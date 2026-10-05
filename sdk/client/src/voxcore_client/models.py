from pydantic import BaseModel
from typing import Any, Dict, Optional, Literal

class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    details: Optional[Dict[str, Any]] = None

class CapabilityDefinition(BaseModel):
    capability_id: str
    name: str
    description: str
    location: Literal["CLIENT", "SERVER"]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    metadata_version: int = 1

class RegisterPayload(BaseModel):
    capability: CapabilityDefinition

class InvokePayload(BaseModel):
    invocation_id: str
    capability_id: str
    arguments: Dict[str, Any]
    attempt: int = 1

class ResultPayload(BaseModel):
    invocation_id: str
    status: Literal["success", "error"]
    result: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None
    attempt: int = 1

class MessageEnvelope(BaseModel):
    protocol_version: str = "1"
    message_type: str
    message_id: str
    project_id: str
    session_id: Optional[str] = None
    timestamp: str
    payload: Dict[str, Any]
