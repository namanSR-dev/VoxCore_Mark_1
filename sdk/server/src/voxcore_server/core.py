import asyncio
import json
import uuid
import inspect
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional

import websockets
from pydantic import ValidationError

from .models import (
    MessageEnvelope, 
    RegisterPayload, 
    InvokePayload, 
    ResultPayload, 
    ErrorDetail
)
from .registry import create_capability_definition


class VoxCoreServer:
    """
    The main entry point for the VoxCore Server SDK.
    Secures the connection using the Secret API Key and registers backend capabilities.
    """
    
    def __init__(self, api_key: str, core_endpoint: str = "ws://localhost:8001/ws"):
        # Security sanity check: Server SDKs should only be initialized with Secret Keys
        if not api_key.startswith("sk_"):
            print("WARNING: api_key does not start with 'sk_'. Ensure you are using the Secret Key on the server.")
        
        self.api_key = api_key
        self.core_endpoint = core_endpoint
        
        # For VS01, we hardcode the project ID for the dummy app.
        # In a production environment, the Orchestrator will securely resolve the project ID 
        # from the provided `api_key` payload.
        self.project_id = "dev_dummy_01" 
        
        # Internal registry mapping capability_id -> the actual Python function in memory
        self._tools: Dict[str, Callable] = {}
        
        # Holds the active WebSocket connection to the VoxCore Orchestrator
        self._connection: Optional[websockets.WebSocketClientProtocol] = None

    def tool(self, func: Optional[Callable] = None, *, location: str = "SERVER") -> Callable:
        """
        Decorator to register a Python function as a VoxCore tool.
        
        Usage:
            @voxcore.tool
            async def my_function(arg1: str): ...
            
        Because this decorator is an instance method of `VoxCoreServer`, it implicitly 
        tags the function with `location="SERVER"` without the developer having to specify it.
        """
        def decorator(f: Callable) -> Callable:
            # 1. Inspect function and create the schema definition
            capability = create_capability_definition(f, location, self.project_id)
            
            # 2. Prevent duplicate registrations which would confuse the AI
            if capability.capability_id in self._tools:
                raise ValueError(f"Capability '{capability.capability_id}' is already registered.")
                
            # 3. Store the actual executable function in our local memory registry
            self._tools[capability.capability_id] = f
            
            # We return the unmodified function so the developer can still call it normally in their code
            return f

        # Allows the decorator to be used with or without parentheses
        if func:
            return decorator(func)
        return decorator

    def _create_envelope(self, message_type: str, payload: dict, session_id: Optional[str] = None) -> str:
        """
        Creates a standardized wire protocol envelope.
        Every message sent between the SDK and the Orchestrator is wrapped in this 
        predictable JSON envelope to ensure deterministic routing and tracing.
        """
        envelope = MessageEnvelope(
            message_type=message_type,
            message_id=str(uuid.uuid4()),
            project_id=self.project_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload
        )
        return envelope.model_dump_json()

    async def _send_registrations(self):
        """
        Iterates over all functions tagged with @voxcore.tool and sends their 
        generated schemas to the Orchestrator. This essentially "teaches" the AI 
        what backend tools are currently available.
        """
        if not self._connection:
            return
            
        for capability_id, func in self._tools.items():
            cap_def = create_capability_definition(func, "SERVER", self.project_id)
            payload = RegisterPayload(capability=cap_def)
            
            # Wrap the registration payload in the wire protocol envelope
            msg = self._create_envelope(
                message_type="capability.register",
                payload=payload.model_dump()
            )
            await self._connection.send(msg)
            print(f"[VoxCoreServer] Registered backend capability: {cap_def.name}")

    async def _handle_invoke(self, envelope: MessageEnvelope):
        """
        Triggered when the Orchestrator's AI decides to call a backend tool.
        This function finds the requested tool, executes it, and sends the result back.
        """
        try:
            # Validate the incoming payload against our Pydantic contract
            invoke_payload = InvokePayload(**envelope.payload)
        except ValidationError as e:
            print(f"[VoxCoreServer] Invalid invoke payload from Core: {e}")
            return
            
        cap_id = invoke_payload.capability_id
        inv_id = invoke_payload.invocation_id
        
        # Security/Sanity Check: Does this SDK actually possess the requested tool?
        if cap_id not in self._tools:
            error_result = ResultPayload(
                invocation_id=inv_id,
                status="error",
                error=ErrorDetail(
                    code="CAPABILITY_NOT_FOUND",
                    message=f"Capability '{cap_id}' not found on this server.",
                    retryable=False
                )
            )
            msg = self._create_envelope("capability.result", error_result.model_dump(), envelope.session_id)
            if self._connection:
                await self._connection.send(msg)
            return

        # Retrieve the actual Python function from our local registry
        func = self._tools[cap_id]
        
        # Extract the LLM-generated arguments
        kwargs = invoke_payload.arguments
        
        try:
            print(f"[VoxCoreServer] Executing {cap_id} with args {kwargs}")
            
            # Execute the developer's function dynamically
            # We support both modern `async` functions and traditional synchronous functions
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
                
            # If successful, wrap the developer's returned dictionary in a success payload
            success_result = ResultPayload(
                invocation_id=inv_id,
                status="success",
                result=result
            )
            
        except Exception as e:
            # If the developer's code crashes, catch the error and send a graceful failure 
            # message back to the Orchestrator so the AI can handle the failure without crashing.
            print(f"[VoxCoreServer] Execution failed for {cap_id}: {str(e)}")
            success_result = ResultPayload(
                invocation_id=inv_id,
                status="error",
                error=ErrorDetail(
                    code="CAPABILITY_EXECUTION_FAILED",
                    message=str(e),
                    retryable=False
                )
            )
            
        # Send the final result back to the Orchestrator
        if self._connection:
            msg = self._create_envelope("capability.result", success_result.model_dump(), envelope.session_id)
            await self._connection.send(msg)

    async def start(self):
        """
        Establishes a persistent, asynchronous WebSocket connection to the 
        VoxCore Orchestrator and begins listening for tool execution commands.
        """
        # Pass the Secret Key in the Authorization header to authenticate the server
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        print(f"[VoxCoreServer] Connecting to {self.core_endpoint}...")
        async with websockets.connect(self.core_endpoint, additional_headers=headers) as ws:
            self._connection = ws
            print("[VoxCoreServer] Connected successfully. Connection secured via Secret Key.")
            
            # 1. Immediately inform the Orchestrator of all available backend tools
            await self._send_registrations()
            
            # 2. Enter an infinite loop, listening for incoming messages from the Orchestrator
            async for message in ws:
                try:
                    data = json.loads(message)
                    envelope = MessageEnvelope(**data)
                    
                    if envelope.message_type == "capability.invoke":
                        # We use `asyncio.create_task` so that if a developer's tool takes 
                        # 10 seconds to execute, it doesn't block the SDK from receiving 
                        # other messages from the Orchestrator.
                        asyncio.create_task(self._handle_invoke(envelope))
                    else:
                        print(f"[VoxCoreServer] Unhandled message type: {envelope.message_type}")
                        
                except Exception as e:
                    print(f"[VoxCoreServer] Error processing message: {e}")
