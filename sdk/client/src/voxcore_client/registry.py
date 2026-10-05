import inspect
import logging
from typing import Any, Callable, Dict
from pydantic import TypeAdapter

from .models import CapabilityDefinition

def generate_json_schema(func: Callable) -> Dict[str, Any]:
    """
    Analyzes the type hints of a Python function and generates a JSON schema for its arguments.
    
    This is a critical part of VoxCore's magic. It prevents developers from having to 
    manually write JSON Schemas for the LLM. It uses Python's built-in `inspect` 
    module to read the function signature, and Pydantic to convert the Python types 
    into standard JSON Schema format.
    """
    # Grab the function's signature (its parameters and their type annotations)
    sig = inspect.signature(func)
    properties = {}
    required = []

    # Iterate through every parameter in the function
    for name, param in sig.parameters.items():
        # If the developer forgot to add a type hint (e.g., `def my_tool(x):` instead of `def my_tool(x: int):`),
        # we must raise an error because the Orchestrator needs strict types to guide the LLM.
        if param.annotation == inspect.Parameter.empty:
            raise ValueError(f"Parameter '{name}' in '{func.__name__}' is missing a type annotation.")
        
        # We use Pydantic's TypeAdapter to automatically convert the Python type 
        # (like `str`, `int`, or complex Pydantic models) into a JSON schema dict.
        adapter = TypeAdapter(param.annotation)
        schema = adapter.json_schema()
        properties[name] = schema
        
        # If the parameter does not have a default value, it is strictly required by the LLM
        if param.default == inspect.Parameter.empty:
            required.append(name)

    # Return a standard JSON Schema object representing the function's expected inputs
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }

def generate_output_schema(func: Callable) -> Dict[str, Any]:
    """
    Analyzes the return type hint of a function and generates a JSON schema for its output.
    If the return type is missing or vague, it logs a warning instead of crashing, 
    allowing rapid prototyping while nudging the developer toward robust AI chaining.
    """
    sig = inspect.signature(func)
    
    # If no return type is provided, warn the developer and fallback to generic object
    if sig.return_annotation == inspect.Signature.empty:
        logging.warning(
            f"[VoxCore SDK] Tool '{func.__name__}' is missing a return type definition. "
            "The Cognitive Engine will struggle to reliably chain this tool. "
            "Consider returning a strongly typed structured model."
        )
        return {"type": "object", "additionalProperties": True}
    
    if sig.return_annotation in (None, type(None)):
        return {"type": "null"}

    # Warn if the developer is explicitly using a vague type like 'dict' or 'Any'
    if sig.return_annotation is dict or sig.return_annotation is Any:
        logging.warning(
            f"[VoxCore SDK] Tool '{func.__name__}' returns a generic dictionary. "
            "The Cognitive Engine will struggle to reliably chain this tool. "
            "Consider returning a strongly typed structured model."
        )
        return {"type": "object", "additionalProperties": True}

    adapter = TypeAdapter(sig.return_annotation)
    return adapter.json_schema()

def create_capability_definition(
    func: Callable, 
    location: str,
    project_id: str
) -> CapabilityDefinition:
    """
    Inspects a Python function and constructs the formal VoxCore CapabilityDefinition.
    
    This definition acts as the "contract" sent to the VoxCore Orchestrator, 
    telling it what the tool is called, what it does, and what parameters it requires.
    """
    # Ensure the developer actually passed a callable function
    if not callable(func):
        raise ValueError("Provided tool is not callable.")
    
    # The docstring is vital. The VoxCore Orchestrator uses this text as the prompt 
    # to teach the Agent *when* and *how* to use this specific tool.
    docstring = inspect.getdoc(func)
    if not docstring:
        raise ValueError(f"Function '{func.__name__}' must have a docstring to be used as a VoxCore tool.")

    # Automatically generate the input schema from the function's type hints
    input_schema = generate_json_schema(func)
    
    # Automatically generate the output schema from the return type hint
    output_schema = generate_output_schema(func)

    # Generate a deterministic, globally unique ID for this capability 
    # based on the project, the execution environment (Client/Server), and the function name.
    capability_id = f"{project_id}:{location}:{func.__name__}"

    return CapabilityDefinition(
        capability_id=capability_id,
        name=func.__name__,
        description=docstring.strip(),
        location=location,  # type: ignore
        input_schema=input_schema,
        output_schema=output_schema,
        metadata_version=1
    )
