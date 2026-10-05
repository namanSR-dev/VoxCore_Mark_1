import asyncio
import json
import uuid
import inspect
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional

from pydantic import ValidationError

from .models import (
    MessageEnvelope, 
    RegisterPayload, 
    InvokePayload, 
    ResultPayload, 
    ErrorDetail
)
from .registry import create_capability_definition

# PyScript & Pyodide Browser Imports
# When running in a browser, we cannot use Python's standard `websockets` package 
# because standard raw sockets are blocked by browser security models.
# Instead, we use the `js` module provided by Pyodide to access the browser's 
# native `window.WebSocket` API directly.
try:
    import js
    from pyodide.ffi import create_proxy
except ImportError:
    # Fallback for environments without pyodide/browser (e.g., if a developer 
    # accidentally runs the Client SDK in a normal terminal)
    js = None
    create_proxy = None


class VoxCoreClient:
    """
    The main entry point for the VoxCore Client SDK.
    Secures the connection using the Publishable Key and registers frontend UI capabilities.
    Designed specifically to execute inside a user's browser via PyScript.
    """
    
    def __init__(self, public_key: str, core_endpoint: str = "ws://localhost:8001/ws"):
        # Security sanity check: Client SDKs should only be initialized with Publishable Keys
        if not public_key.startswith("pk_"):
            print("WARNING: public_key does not start with 'pk_'. Ensure you are using the Publishable Key on the frontend.")
            
        self.public_key = public_key
        
        # Unlike the Server SDK which passes the Secret Key via HTTP Headers, 
        # browser WebSockets (window.WebSocket) do not allow setting custom Authorization headers.
        # Therefore, we append the public publishable key as a URL query parameter.
        sep = "&" if "?" in core_endpoint else "?"
        self.core_endpoint = f"{core_endpoint}{sep}public_key={self.public_key}"
        
        # For VS01 dummy setup
        self.project_id = "dev_dummy_01" 
        
        # Internal registry mapping capability_id -> the actual Python/JS function in memory
        self._tools: Dict[str, Callable] = {}
        
        # Holds the active browser WebSocket connection
        self._ws = None

    def tool(self, func: Optional[Callable] = None, *, location: str = "CLIENT") -> Callable:
        """
        Decorator to register a frontend JavaScript/PyScript function as a capability.
        
        Usage:
            @voxcore.tool
            async def highlight_element(element_id: str): ...
            
        Because this decorator is an instance method of `VoxCoreClient`, it implicitly 
        tags the function with `location="CLIENT"`. The Orchestrator knows this tool 
        only exists in the user's browser.
        """
        def decorator(f: Callable) -> Callable:
            # 1. Inspect function and create the schema definition
            capability = create_capability_definition(f, location, self.project_id)
            
            # 2. Prevent duplicate registrations
            if capability.capability_id in self._tools:
                raise ValueError(f"Capability '{capability.capability_id}' is already registered.")
                
            # 3. Store the actual executable function in our local browser memory registry
            self._tools[capability.capability_id] = f
            return f

        if func:
            return decorator(func)
        return decorator

    def _create_envelope(self, message_type: str, payload: dict, session_id: Optional[str] = None) -> str:
        """
        Creates a standardized wire protocol envelope.
        Every message sent to the Orchestrator is wrapped in this JSON envelope.
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

    def _send_registrations(self):
        """
        Iterates over all functions tagged with @voxcore.tool and sends their 
        generated schemas to the Orchestrator to teach the AI what UI controls are available.
        """
        if not self._ws:
            return
            
        for capability_id, func in self._tools.items():
            cap_def = create_capability_definition(func, "CLIENT", self.project_id)
            payload = RegisterPayload(capability=cap_def)
            msg = self._create_envelope("capability.register", payload.model_dump())
            self._ws.send(msg)
            print(f"[VoxCoreClient] Registered frontend UI capability: {cap_def.name}")

    async def _handle_invoke(self, envelope: MessageEnvelope):
        """
        Triggered when the Orchestrator's AI decides to call a UI-level tool.
        This function finds the requested UI tool, executes it in the browser, and sends the result back.
        """
        try:
            invoke_payload = InvokePayload(**envelope.payload)
        except ValidationError as e:
            print(f"[VoxCoreClient] Invalid invoke payload: {e}")
            return
            
        cap_id = invoke_payload.capability_id
        inv_id = invoke_payload.invocation_id
        
        # Security Check: We cannot execute backend tools here. We only execute registered frontend tools.
        if cap_id not in self._tools:
            error_result = ResultPayload(
                invocation_id=inv_id,
                status="error",
                error=ErrorDetail(
                    code="CAPABILITY_NOT_FOUND",
                    message=f"Capability '{cap_id}' not found on this client.",
                    retryable=False
                )
            )
            msg = self._create_envelope("capability.result", error_result.model_dump(), envelope.session_id)
            if self._ws:
                self._ws.send(msg)
            return

        func = self._tools[cap_id]
        kwargs = invoke_payload.arguments
        
        try:
            print(f"[VoxCoreClient] Executing {cap_id} with args {kwargs}")
            
            # Execute the UI function (e.g., navigating to a page, highlighting a form)
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
                
            success_result = ResultPayload(
                invocation_id=inv_id,
                status="success",
                result=result
            )
        except Exception as e:
            # Catch UI execution errors and report them back gracefully
            print(f"[VoxCoreClient] Execution failed for {cap_id}: {str(e)}")
            success_result = ResultPayload(
                invocation_id=inv_id,
                status="error",
                error=ErrorDetail(
                    code="CAPABILITY_EXECUTION_FAILED",
                    message=str(e),
                    retryable=False
                )
            )
            
        if self._ws:
            msg = self._create_envelope("capability.result", success_result.model_dump(), envelope.session_id)
            self._ws.send(msg)

    def start(self):
        """
        Connects to the VoxCore Orchestrator using the browser's native WebSocket API.
        This establishes the persistent voice and control session.
        """
        if not js:
            raise RuntimeError("VoxCoreClient is designed to run in a browser (PyScript). `js` module not found.")

        print(f"[VoxCoreClient] Connecting to {self.core_endpoint}...")
        
        # Access the browser's native JavaScript window.WebSocket object
        self._ws = js.WebSocket.new(self.core_endpoint)
        
        # ---------------------------------------------------------------------
        # Event Callbacks
        # Pyodide requires Python functions to be wrapped with `create_proxy` 
        # before they can be assigned to JavaScript event handlers (like onopen).
        # ---------------------------------------------------------------------
        
        def on_open(event):
            print("[VoxCoreClient] Connected successfully. Connection secured via Publishable Key.")
            self._send_registrations()
            
        def on_message(event):
            try:
                # event.data contains the JSON string sent from the Orchestrator
                data = json.loads(event.data)
                envelope = MessageEnvelope(**data)
                
                if envelope.message_type == "capability.invoke":
                    # Fire off the execution asynchronously so the UI thread doesn't freeze
                    asyncio.create_task(self._handle_invoke(envelope))
                else:
                    print(f"[VoxCoreClient] Unhandled message type: {envelope.message_type}")
            except Exception as e:
                print(f"[VoxCoreClient] Error processing message: {e}")

        def on_error(event):
            print("[VoxCoreClient] WebSocket error encountered.")

        def on_close(event):
            print("[VoxCoreClient] Connection closed.")
            self._ws = None

        # Bind the Python callbacks to the JavaScript WebSocket events
        self._ws.onopen = create_proxy(on_open)
        self._ws.onmessage = create_proxy(on_message)
        self._ws.onerror = create_proxy(on_error)
        self._ws.onclose = create_proxy(on_close)
