# VoxCore — VS-01 Low-Level Design

**Document:** `07_VoxCore_VS01_LLD.md`  
**Version:** VS-01 — First End-to-End Vertical Slice  
**Status:** Implementation Blueprint / Freeze Candidate  
**Authority:** Derived from the Frozen V1 HLD, architecture constraints, and progressive vertical-slice methodology.

---

## 1. Purpose

This document is the **implementation-level design** for VS-01.

The Frozen HLD defines what VoxCore is and the permanent architectural boundaries. This document defines **how VS-01 will actually be implemented and proven**.

The intended relationship is:

```text
Frozen HLD
    ↓
VS-01 Requirements
    ↓
VS-01 Contracts
    ↓
VS-01 Algorithms
    ↓
VS-01 Implementation
    ↓
VS-01 Tests
    ↓
VS-01 Verification
    ↓
Completion Gate
    ↓
VS-01 Frozen
```

An implementation should be a mechanical realization of this document. If implementation requires an architectural or implementation-critical decision not covered here, the coding agent must stop, record the ambiguity, report it back to Human developer and suggest possible solution to resolve it, and do not update the LLD - before continuing.

---

# 2. VS-01 Goal

VS-01 must prove the complete fundamental VoxCore execution loop:

```text
User
 ↓
Developer Frontend
 ↓
Python Client SDK
 ↓
Network
 ↓
VoxCore Core
 ↓
Environment
 ↓
Google ADK Agent
 ↓
Dynamic ADK Toolset
 ↓
Deterministic Router
 ↓
Network
 ↓
Developer SDK
 ↓
Developer Function
 ↓
Result
 ↓
VoxCore Core
 ↓
ADK
 ↓
Goal Check / Replan
 ↓
Voice / UI Response
 ↓
User
```

The slice must demonstrate all of the following:

1. Three independent codebases run as separate processes.
2. The Developer Application installs the SDK as a package.
3. The SDK performs function registration/introspection.
4. Core receives developer capability metadata without importing SDK or developer code.
5. Core constructs a project/session environment.
6. Core exposes capabilities dynamically to Google ADK.
7. The Core agent contains no developer-specific hardcoded tools.
8. The model can choose among multiple client and server capabilities.
9. Core deterministically routes the selected capability.
10. The actual developer function executes in the correct developer process.
11. Results return through the network boundary.
12. ADK receives structured tool results.
13. The agent can continue planning after a tool result.
14. Tool execution failure produces structured recovery behavior.
15. A real frontend visibly demonstrates client-side tool execution.
16. Voice interaction is exercised through the selected native live/voice path.
17. Automated tests and deterministic acceptance scenarios prove the slice.
18. A human manually verifies the real running system.
19. The completion gate provides objective evidence for every requirement.

---

# 3. Permanent Codebase Boundary

The repository contains three permanently independent codebases:

```text
Voxcore_Mark_1/
├── developer_app/
│   ├── frontend/
│   └── backend/
│
├── sdk/
│   └── src/
│       └── voxcore_sdk/
│
└── core/
    └── src/
        └── voxcore_core/
```

They are three separate software systems.

## 3.1 Dependency Rules

Allowed:

```text
developer_app
      │
      └── installed dependency ──► sdk

developer_app
      │
      └──────── network ─────────► core

sdk
      │
      └──────── network ─────────► core
```

Forbidden:

```text
developer_app ──import──► core
core ──import──► developer_app

core ──import──► sdk
sdk ──import──► core

sdk ──import──► developer_app
developer_app ──import──► sdk source tree
```

The Developer Application consumes the SDK as an installed package. It must not import files using paths such as:

```python
from ../../sdk.src...
```

or otherwise reach into SDK source directories.

Each codebase has its own dependency configuration and isolated environment. Shared dependencies are independently installed.

No shared `common/`, `shared/`, or cross-codebase package is permitted.

---

# 4. VS-01 Technology Stack

This is the implementation stack for this slice.

## 4.1 Core

| Responsibility | Technology |
|---|---|
| Agent/orchestration | Google ADK |
| Core HTTP server | FastAPI |
| WebSocket server | FastAPI/Starlette WebSocket |
| Data contracts | Pydantic v2 |
| Configuration | `pydantic-settings` |
| Async execution | Python `asyncio` |
| Outbound HTTP | HTTPX |
| Package/environment | `uv` + `pyproject.toml` |
| Tests | pytest + pytest-asyncio/AnyIO |
| Static analysis | Ruff + mypy/pyright |
| Logging | Python standard `logging` |
| Browser E2E | Playwright |

## 4.2 SDK

| Responsibility | Technology |
|---|---|
| Language | Python |
| Contracts | Pydantic v2 |
| Async runtime | `asyncio` |
| HTTP | HTTPX |
| WebSocket client | Python WebSocket client compatible with the selected browser/runtime boundary |
| Package management | `uv` + `pyproject.toml` |
| Tests | pytest |

## 4.3 Developer Backend

Python and the same general Python service stack used by the SDK/Core where required.

It remains a separate dependency environment.

## 4.4 Developer Frontend

The first slice intentionally uses a **Python-capable browser runtime** so the Client SDK can be exercised without creating an official JavaScript VoxCore SDK.

The exact browser runtime is an implementation-critical spike:

```text
Python source
     ↓
browser Python runtime
     ↓
browser
     ↓
VoxCore Client SDK
```

The preferred VS-01 direction is Pyodide/PyScript-class browser Python execution.

The selected runtime must prove:

- Python code executes in the browser;
- the Python Client SDK can execute there;
- browser WebSocket communication can be performed;
- registered frontend Python functions execute in the browser;
- results can return to Core.

No handwritten JavaScript application SDK is permitted as a substitute.

If the selected Python browser runtime cannot satisfy these requirements, the implementation must stop and record the technical limitation before changing the architecture.

---

# 5. Why These Technologies

VS-01 deliberately uses mature infrastructure rather than implementing infrastructure primitives manually.

FastAPI provides HTTP/WebSocket application infrastructure. FastAPI documents native WebSocket endpoints and WebSocket testing through `TestClient`. citeturn0search4turn0search0

HTTPX provides the asynchronous HTTP client boundary used by Python services and integration tests. FastAPI's testing documentation uses HTTPX for asynchronous API testing. citeturn0search2turn0search7

Google ADK remains the only agentic framework. The agent/tool layer must not be replaced by a custom orchestration framework. Current Google ADK tooling documentation also treats Python functions as first-class tools and uses their docstrings as tool descriptions. citeturn1search1

Docker, Redis, Kafka, Celery, databases, OpenTelemetry, and similar infrastructure are intentionally deferred because VS-01 does not require them.

---

# 6. Runtime Topology

During development:

```text
┌──────────────────────────┐
│ Developer Frontend       │
│ Python browser runtime   │
│ Python Client SDK        │
└────────────┬─────────────┘
             │
             │ WebSocket
             ▼
┌──────────────────────────┐
│ VoxCore Core             │
│                          │
│ FastAPI                  │
│ Environment              │
│ ADK Agent                │
│ Dynamic Toolset          │
│ Deterministic Router     │
└────────────┬─────────────┘
             │
             │ HTTP/WebSocket
             ▼
┌──────────────────────────┐
│ Developer Backend        │
│ Python Server SDK        │
│ Dummy Business Logic     │
│ Fake APIs                │
└──────────────────────────┘
```

Each runs independently.

Example development allocation:

```text
Developer Frontend: localhost:<frontend-port>
Developer Backend:  localhost:<backend-port>
VoxCore Core:       localhost:<core-port>
```

The exact port numbers are configuration values, not protocol semantics.

The production topology changes hostnames and deployment infrastructure, not the architectural boundary.

---

# 7. Component Responsibilities

## 7.1 Developer Frontend

Responsible for:

- UI;
- user interaction;
- voice/browser interaction;
- Client SDK initialization;
- client capability registration;
- executing client capabilities;
- displaying execution state;
- returning client capability results.

It must not contain VoxCore Core logic.

## 7.2 Developer Backend

Responsible for:

- backend application;
- Server SDK initialization;
- server capability registration;
- fake business/API implementations;
- simulated latency/failure;
- executing server capabilities.

It must not contain Core orchestration logic.

## 7.3 SDK

Responsible for:

- registration;
- introspection;
- transport;
- capability invocation;
- function execution;
- result normalization;
- connection lifecycle.

It does not reason about user intent.

## 7.4 Core

Responsible for:

- environment construction;
- ADK agent execution;
- dynamic tool exposure;
- deterministic routing;
- invocation lifecycle;
- session state;
- result propagation;
- execution failure classification.

Core does not contain developer business logic.

---

# 8. Capability Data Model

The canonical capability model is:

```text
CapabilityDefinition
├── protocol_version: string
├── capability_id: string
├── name: string
├── description: string
├── location: CLIENT | SERVER
├── input_schema: JSON Schema
├── output_schema: JSON Schema
└── metadata_version: integer
```

### Identity

`capability_id` must be unique within a project.

The recommended deterministic identity is:

```text
<project_id>:<location>:<capability_name>
```

The exact encoding must be centralized in the SDK/Core contract implementation.

A capability name alone is not sufficient to identify a cross-project capability.

---

# 9. Capability Registration Algorithm

The SDK registration API is intentionally small:

```python
voxcore.tool(function)
```

The decorator/registration function performs:

```text
REGISTER(function)
    1. Verify function is callable.
    2. Read function name.
    3. Read docstring.
    4. Inspect signature.
    5. Verify every required parameter has a supported type annotation.
    6. Verify return annotation exists.
    7. Generate input schema.
    8. Generate output schema.
    9. Determine execution location from the SDK context:
          Client SDK → CLIENT
          Server SDK → SERVER
   10. Generate capability_id.
   11. Construct immutable CapabilityDefinition.
   12. Store function + definition in local registry.
   13. Reject duplicate capability_id.
   14. Return the original function/decorator-compatible object.
```

The developer does not manually repeat the function schema.

Example:

```python
@voxcore.tool
async def verify_insurance(patient_id: str) -> InsuranceResult:
    """Verify the patient's insurance information."""
    ...
```

The SDK derives the capability metadata.

---

# 10. Registration Validation Contract

Registration fails before the capability is published if:

- function is not callable;
- docstring is absent/empty;
- a parameter lacks a usable type annotation;
- return type is absent;
- a type cannot be converted into the supported schema;
- capability identity collides with another registered capability.

Registration warnings may be emitted for non-critical metadata conditions, but the agent must never receive an invalid capability schema.

---

# 11. SDK Package Contract

The developer application interacts with only public SDK symbols.

Internal SDK modules are not part of the developer contract.

The SDK must expose a small public surface conceptually equivalent to:

```text
voxcore
├── Client
├── Server
├── tool
├── session primitives
└── public contract types where required
```

Exact names may be finalized during implementation, but the principle is fixed:

> The dummy application should look like an ordinary external developer consuming an SDK.

---

# 12. Wire Protocol Envelope

Every network message uses a common envelope:

```json
{
  "protocol_version": "1",
  "message_type": "...",
  "message_id": "...",
  "project_id": "...",
  "session_id": "...",
  "timestamp": "...",
  "payload": {}
}
```

## Required properties

| Field | Requirement |
|---|---|
| `protocol_version` | identifies wire contract |
| `message_type` | deterministic message discriminator |
| `message_id` | unique message identifier |
| `project_id` | tenant/project boundary |
| `session_id` | active conversation boundary |
| `timestamp` | message creation time |
| `payload` | message-specific validated data |

Unknown message types are rejected.

Unknown protocol versions are rejected unless an explicit compatibility rule exists.

---

# 13. Registration Message Contract

Developer SDK → Core:

```json
{
  "protocol_version": "1",
  "message_type": "capability.register",
  "message_id": "...",
  "project_id": "...",
  "session_id": null,
  "timestamp": "...",
  "payload": {
    "capability": {
      "capability_id": "...",
      "name": "...",
      "description": "...",
      "location": "CLIENT",
      "input_schema": {},
      "output_schema": {},
      "metadata_version": 1
    }
  }
}
```

Registration is project-scoped, not user-session business logic.

---

# 14. Invocation Message Contract

Core → SDK:

```json
{
  "protocol_version": "1",
  "message_type": "capability.invoke",
  "message_id": "...",
  "project_id": "...",
  "session_id": "...",
  "timestamp": "...",
  "payload": {
    "invocation_id": "...",
    "capability_id": "...",
    "arguments": {},
    "attempt": 1
  }
}
```

The receiving SDK must validate:

1. protocol version;
2. message type;
3. project identity;
4. session identity where applicable;
5. capability existence;
6. capability location;
7. argument schema;
8. invocation ID.

Only then may the developer function execute.

---

# 15. Result Message Contract

SDK → Core:

```json
{
  "protocol_version": "1",
  "message_type": "capability.result",
  "message_id": "...",
  "project_id": "...",
  "session_id": "...",
  "timestamp": "...",
  "payload": {
    "invocation_id": "...",
    "status": "success",
    "result": {},
    "error": null,
    "attempt": 1
  }
}
```

Failure:

```json
{
  "protocol_version": "1",
  "message_type": "capability.result",
  "message_id": "...",
  "project_id": "...",
  "session_id": "...",
  "timestamp": "...",
  "payload": {
    "invocation_id": "...",
    "status": "error",
    "result": null,
    "error": {
      "code": "CAPABILITY_EXECUTION_FAILED",
      "message": "Capability execution failed.",
      "retryable": false
    },
    "attempt": 1
  }
}
```

Raw exceptions, tracebacks, filesystem paths, credentials, and infrastructure details must not cross the boundary.

---

# 16. Error Contract

All deterministic errors use:

```text
Error
├── code
├── message
├── retryable
└── details (optional, structured and non-sensitive)
```

VS-01 minimum error codes:

```text
INVALID_MESSAGE
UNSUPPORTED_PROTOCOL_VERSION
PROJECT_NOT_FOUND
SESSION_NOT_FOUND
CAPABILITY_NOT_FOUND
CAPABILITY_LOCATION_MISMATCH
INVALID_ARGUMENTS
INVALID_RESULT
DUPLICATE_INVOCATION
INVOCATION_TIMEOUT
CONNECTION_UNAVAILABLE
CAPABILITY_EXECUTION_FAILED
CAPABILITY_NOT_READY
INTERNAL_RUNTIME_ERROR
```

The `code` is for software.

The `message` is for controlled diagnostics.

The voice layer must not read technical error codes to the user.

---

# 17. Session State Model

VS-01 uses in-memory active session state.

```text
Session
├── project_id
├── session_id
├── status
├── created_at
├── last_activity_at
├── capability_snapshot
├── active_invocations
└── recent_invocation_results
```

Session states:

```text
CREATING
   ↓
ACTIVE
   ↓
RECONNECTING
   ↓
ACTIVE
   ↓
CLOSING
   ↓
CLOSED
```

A closed session cannot accept new capability invocations.

---

# 18. Environment Construction Algorithm

```text
CREATE_SESSION(project_id, session_id, context)

1. Validate project_id.
2. Validate session_id format.
3. Resolve project configuration.
4. Resolve currently registered capabilities for project.
5. Validate every capability definition.
6. Build immutable capability snapshot.
7. Load project instructions/configuration.
8. Apply session-provided context.
9. Validate autonomy/guardrail configuration.
10. Construct RuntimeEnvironment.
11. Create ADK session/runtime binding.
12. Associate session with environment.
13. Return session-ready state.
```

No LLM call occurs during steps 1–10.

---

# 19. Runtime Environment

```text
RuntimeEnvironment
├── project_id
├── session_id
├── instructions
├── autonomy_constraints
├── capability_snapshot
└── session_context
```

The environment is the source used by the dynamic ADK toolset.

The agent itself remains generic.

---

# 20. ADK Agent Design

The Core must use Google ADK as the agentic framework.

The intended structure is:

```python
root_agent = Agent(
    name="voxcore_agent",
    model=MODEL,
    instruction=CORE_INSTRUCTION,
    planner=PLANNER,
    tools=[voxcore_toolset],
)
```

The exact imports/API must be confirmed against the pinned `google-adk` version before implementation freeze.

The following is prohibited:

```python
tools=[
    verify_insurance,
    check_doctor_availability,
    book_appointment,
    highlight_missing_forms,
]
```

The agent must remain developer-agnostic.

---

# 21. Dynamic ADK Toolset Algorithm

Use ADK's native dynamic toolset mechanism rather than a custom tool registry injected into a custom agent framework.

Conceptual algorithm:

```text
GET_TOOLS(runtime_context)

1. Read project/session identity from runtime context.
2. Resolve RuntimeEnvironment.
3. Obtain capability snapshot.
4. For each capability:
      a. create an ADK-compatible tool representation;
      b. preserve capability name;
      c. preserve description;
      d. preserve input schema;
      e. bind execution callback to capability_id only;
      f. do not bind developer business function directly into Core.
5. Return individual ADK tools.
```

Each capability appears as a first-class ADK tool.

The callback for a tool performs only:

```text
tool callback
    ↓
construct invocation
    ↓
deterministic router
    ↓
network dispatch
    ↓
wait for result
    ↓
return structured result to ADK
```

It must not contain capability-specific business logic.

---

# 22. ADK Technical Spike

Before freezing the ADK implementation, prove these exact behaviors:

### S1 — Toolset acceptance

`Agent` accepts the selected ADK toolset mechanism.

### S2 — Dynamic resolution

ADK requests tools from the toolset using runtime context.

### S3 — Per-session capability set

Two sessions with different capability snapshots receive different tool sets without rebuilding developer-specific agent code.

### S4 — Schema correctness

Generated tools preserve:

- name;
- description;
- parameter names;
- parameter types;
- required/optional status.

### S5 — Invocation

The model can select a dynamically returned tool.

### S6 — Async execution

The tool can await an external network operation and return a structured result.

### S7 — Error propagation

A tool execution error reaches the ADK execution lifecycle without requiring model-text parsing.

### S8 — Planning

The selected ADK planner can execute multiple tools when the task requires multiple capabilities.

### S9 — Live runtime

The selected ADK live/voice path can coexist with tool execution.

A failure in any spike item blocks implementation of the corresponding main component.

---

# 23. Deterministic Router Algorithm

The router receives a **selected capability**, never a natural-language request.

```text
ROUTE(invocation)

1. Validate envelope.
2. Validate project_id.
3. Resolve session.
4. Resolve capability_id from session snapshot.
5. Compare registered capability location with destination.
6. Validate invocation arguments against input_schema.
7. Generate/validate invocation identity.
8. Check duplicate/previous result state.
9. Create active invocation record.
10. Select transport destination using registered location:
       CLIENT → client session channel
       SERVER → developer server channel
11. Dispatch invocation.
12. Wait for result or timeout.
13. Validate returned invocation_id.
14. Validate result against output_schema.
15. Store result state.
16. Return structured result to ADK.
```

The router never:

- chooses the tool;
- interprets user intent;
- infers location from arguments;
- modifies developer business data;
- executes developer functions locally.

---

# 24. Client Routing Algorithm

```text
ADK selected client_tool
        ↓
router validates capability
        ↓
router confirms location == CLIENT
        ↓
create invocation_id
        ↓
send capability.invoke over client WebSocket
        ↓
client SDK receives message
        ↓
client SDK validates message
        ↓
client SDK resolves local capability
        ↓
execute developer function
        ↓
validate returned value
        ↓
construct capability.result
        ↓
send result to Core
        ↓
Core validates/correlates result
        ↓
ADK receives tool result
```

---

# 25. Server Routing Algorithm

```text
ADK selected server_tool
        ↓
router validates capability
        ↓
router confirms location == SERVER
        ↓
create invocation_id
        ↓
send capability.invoke to developer backend
        ↓
server SDK validates message
        ↓
server SDK resolves local capability
        ↓
execute developer function
        ↓
validate returned value
        ↓
construct capability.result
        ↓
send result to Core
        ↓
Core validates/correlates result
        ↓
ADK receives tool result
```

---

# 26. Duplicate Protection Algorithm

```text
RECEIVE_INVOCATION(invocation_id)

1. Look up invocation_id.
2. If state == COMPLETED:
       return stored result.
3. If state == RUNNING:
       do not execute a second copy.
       attach/reuse result lifecycle.
4. If unknown:
       create RUNNING record.
       execute exactly once.
5. Store terminal result.
```

This applies independently inside the receiving SDK runtime.

---

# 27. Timeout Algorithm

For each invocation:

```text
dispatch
  ↓
start monotonic deadline
  ↓
await result
  ├── result arrives before deadline → success/failure result
  └── deadline expires
          ↓
      mark timeout
          ↓
      do not fabricate success
          ↓
      return retryable structured error where policy permits
```

A timeout does not prove that the remote function did not execute.

Therefore a timed-out non-idempotent operation must not automatically be executed again.

---

# 28. Retry Algorithm

VS-01 uses conservative retry behavior.

```text
result failure
    ↓
is retryable?
    ├── no → return failure to ADK
    └── yes
          ↓
is operation safely retryable?
          ├── no → return failure to ADK
          └── yes
                ↓
             retry
```

Retry count is deterministic and bounded.

The agent may decide to attempt an alternative strategy after receiving the failure.

The infrastructure must not repeatedly retry indefinitely.

---

# 29. Agent Execution Algorithm

The Core execution cycle is:

```text
HANDLE_USER_TURN(input)

1. Receive user input.
2. Attach input to active session.
3. Provide current environment to ADK.
4. Run ADK agent.
5. If ADK produces normal conversational output:
       deliver output.
6. If ADK produces structured tool call:
       execute selected ADK tool.
7. Receive tool result.
8. Return result to ADK.
9. Allow ADK to interpret result.
10. If goal is incomplete:
        ADK may select another tool / replan.
11. If goal is complete:
        produce final response.
12. Return final response through voice/UI channel.
```

No custom:

```text
if user_contains("insurance"):
```

or similar intent parser is allowed.

---

# 30. Multi-Tool Verification Scenario

The primary deterministic orchestration scenario is:

> "Verify my insurance and show me the missing forms."

Expected capability set:

```text
CLIENT
    highlight_missing_forms
    show_patient_banner

SERVER
    verify_insurance
    check_doctor_availability
```

Expected execution:

```text
User request
      ↓
ADK understands goal
      ↓
select verify_insurance
      ↓
SERVER invocation
      ↓
developer backend executes
      ↓
insurance result
      ↓
ADK interprets result
      ↓
select highlight_missing_forms
      ↓
CLIENT invocation
      ↓
developer frontend executes
      ↓
frontend visibly changes state
      ↓
client result
      ↓
ADK checks goal
      ↓
final response
```

The exact order above is the expected test behavior for this deterministic test scenario.

The implementation must not hardcode that order. The test verifies that ADK produces the required behavior from the capability descriptions and user goal.

---

# 31. Additional Planning Scenario

A second scenario must require server-only multi-step execution:

> "Check the earliest available doctor appointment and tell me the earliest option."

Expected:

```text
check_doctor_availability
        ↓
result
        ↓
goal check
        ↓
final response
```

A multi-step variant may add another capability if the planner requires it.

The purpose is to demonstrate that the Core can expose and select multiple capabilities rather than being implemented around one special tool.

---

# 32. Failure Scenario

Configure the dummy backend:

```text
verify_insurance
    simulated delay
    simulated failure
```

User:

> "Verify my insurance."

Expected:

```text
User input
    ↓
ADK selects verify_insurance
    ↓
router dispatches
    ↓
dummy backend delays
    ↓
dummy backend returns controlled failure
    ↓
SDK creates structured error
    ↓
Core correlates invocation
    ↓
ADK receives tool failure
    ↓
agent decides recovery
    ↓
natural response
```

Forbidden result:

```text
"CAPABILITY_EXECUTION_FAILED"
```

spoken directly to the user.

---

# 33. Developer Fake API Algorithm

The dummy backend must simulate latency without external APIs.

```python
async def fake_operation(...):
    await asyncio.sleep(configured_delay)

    if configured_failure:
        raise ControlledFakeFailure(...)

    return deterministic_fake_result(...)
```

The fake API must be deterministic enough for tests to assert exact results.

The fake API must not be used to implement Core behavior.

---

# 34. Frontend Capability Algorithm

A frontend capability follows:

```text
register function
      ↓
SDK introspects function
      ↓
SDK publishes metadata
      ↓
Core exposes capability to ADK
      ↓
ADK selects tool
      ↓
Core sends invocation
      ↓
browser SDK receives invocation
      ↓
lookup capability_id
      ↓
validate arguments
      ↓
execute Python frontend function
      ↓
update visible UI state
      ↓
construct result
      ↓
send result
```

The UI update must be observable by a human.

---

# 35. Voice Runtime Contract

The voice layer is separate from orchestration.

It must provide:

```text
voice input → session input
session output → voice response
```

The orchestration runtime provides structured execution state.

The voice runtime converts execution state and final results into natural interaction.

The first slice must use the selected native live/voice model path rather than implementing a mandatory ASR → LLM → TTS pipeline.

The exact voice model/API remains a spike decision until verified.

---

# 36. Connection Lifecycle

Client:

```text
DISCONNECTED
   ↓
CONNECTING
   ↓
CONNECTED
   ↓
RECONNECTING
   ↓
CONNECTED
   ↓
CLOSING
   ↓
DISCONNECTED
```

On reconnect:

```text
client reconnects
    ↓
provides project_id/session_id
    ↓
Core validates active session
    ↓
Core restores channel association
    ↓
client resumes normal operation
```

A reconnect must not create an unrelated session unless the original session has been explicitly closed.

---

# 37. Contract Completeness Review

The VS-01 contracts must cover five categories.

### Identity

- project ID;
- session ID;
- capability ID;
- invocation ID;
- message ID;
- protocol version.

### Capability

- name;
- description;
- location;
- input schema;
- output schema;
- metadata version.

### Invocation

- target capability;
- arguments;
- attempt;
- lifecycle;
- correlation.

### Result

- status;
- result;
- error;
- retryability;
- correlation.

### Lifecycle

- registration;
- session creation;
- connection;
- invocation;
- completion;
- failure;
- timeout;
- duplicate;
- reconnection.

If a newly discovered VS-01 message cannot fit these contracts without inventing a new semantic concept, the LLD must be updated before implementation continues.

---

# 38. Test Architecture

Testing is divided into five levels.

```text
Level 1 — Unit
        ↓
Level 2 — Contract
        ↓
Level 3 — Component Integration
        ↓
Level 4 — End-to-End Process Test
        ↓
Level 5 — Human Browser/Voice Verification
```

Every level has a different purpose.

---

# 39. Level 1 — Unit Tests

## SDK

Must test:

- valid registration;
- missing docstring;
- missing parameter annotation;
- missing return annotation;
- unsupported annotation;
- duplicate capability;
- schema generation;
- result serialization;
- error normalization;
- duplicate invocation handling.

## Core

Must test:

- environment construction;
- project lookup;
- session lookup;
- capability lookup;
- location validation;
- argument validation;
- result validation;
- invocation ID generation;
- timeout;
- retry classification;
- duplicate result handling.

---

# 40. Level 2 — Contract Tests

Contract tests prove that independently implemented boundaries agree.

### Capability contract

Given:

```python
async def verify_insurance(patient_id: str) -> InsuranceResult:
    """Verify insurance information."""
```

assert that the SDK-generated capability contains:

```text
name == verify_insurance
description == expected docstring
patient_id == string input
return schema == InsuranceResult schema
location == SERVER
```

### Invocation contract

Given a valid invocation, assert:

```text
protocol_version valid
message_type == capability.invoke
project_id preserved
session_id preserved
invocation_id preserved
capability_id preserved
arguments preserved
```

### Result contract

Assert:

```text
success → status=success, result!=null, error=null
failure → status=error, result=null, error!=null
```

### Negative contract tests

Verify malformed messages are rejected without developer-function execution.

---

# 41. Level 3 — Component Integration Tests

Use real component implementations but keep the test inside one process where appropriate.

Examples:

1. Core + real ADK + dynamic toolset.
2. SDK + registered functions.
3. Core + SDK transport adapter.
4. FastAPI WebSocket endpoint + SDK client.

FastAPI supports testing WebSocket endpoints using `TestClient`, while async application behavior can be tested through HTTPX/AnyIO. citeturn0search0turn0search7

These tests prove component correctness but do not replace process-boundary tests.

---

# 42. Level 4 — Full Process Integration Tests

Start:

```text
Process A: Developer Frontend
Process B: Developer Backend
Process C: VoxCore Core
```

Use actual network communication.

The test harness must not import business functions from another process.

Minimum process tests:

| Test | Expected |
|---|---|
| Core starts alone | PASS |
| Backend starts without Core | PASS |
| Frontend starts without Core | PASS |
| SDK installs into developer app | PASS |
| Frontend connects to Core | PASS |
| Backend connects to Core | PASS |
| Client invocation round trip | PASS |
| Server invocation round trip | PASS |
| Multi-tool round trip | PASS |
| Controlled failure round trip | PASS |
| Reconnect | PASS |
| Duplicate invocation | exactly one function execution |

---

# 43. Level 5 — Human Verification

Automated tests cannot prove that the user experience actually works.

A human must:

1. start Core;
2. start Developer Backend;
3. start Developer Frontend;
4. open the real browser UI;
5. establish a session;
6. perform the required voice/user interaction;
7. observe the frontend;
8. observe the backend execution;
9. verify the final response.

The verifier must record evidence for each acceptance scenario.

---

# 44. Deterministic Acceptance Test Matrix

This matrix is the actual VS-01 behavioral specification.

## AT-01 — System Startup

**Setup**

All three codebases are independently installed.

**Action**

Start frontend, backend, and Core.

**Expected**

```text
frontend process → running
backend process  → running
core process     → running
```

No cross-codebase import error occurs.

**Pass condition:** all three services start independently.

---

## AT-02 — SDK Installation Boundary

**Action**

Install SDK into the Developer Application environment.

**Expected**

Developer code imports only the SDK's public API.

**Pass condition:**

No source-path import into `sdk/src`.

---

## AT-03 — Capability Registration

**Action**

Register:

```text
highlight_missing_forms
show_patient_banner
verify_insurance
check_doctor_availability
```

**Expected**

Core receives four valid capability definitions.

**Pass condition:**

Four capabilities appear in the project capability snapshot with correct locations.

---

## AT-04 — Dynamic Tool Exposure

**Action**

Start two project/session environments with different capability sets.

**Expected**

Session A receives only its configured capabilities.

Session B receives only its configured capabilities.

**Pass condition:**

No cross-session capability leakage.

---

## AT-05 — No Hardcoded Tools

**Action**

Add a new dummy capability without changing Core agent source.

**Expected**

After registration and new session initialization, the new capability becomes available to the agent.

**Pass condition:**

No Core agent source modification is required.

This is a critical architectural test.

---

## AT-06 — Client Invocation

**Input**

> "Show me the missing forms."

**Expected**

```text
ADK
 → highlight_missing_forms
 → CLIENT route
 → frontend function
 → visible UI state change
 → result
 → ADK
 → final response
```

**Pass condition:**

The actual browser UI changes and the returned result is correlated with the correct invocation.

---

## AT-07 — Server Invocation

**Input**

> "Verify my insurance."

**Expected**

```text
ADK
 → verify_insurance
 → SERVER route
 → backend function
 → fake API result
 → Core
 → ADK
 → final response
```

**Pass condition:**

Backend execution occurs and frontend/Core never directly executes the backend function.

---

## AT-08 — Multi-Step Client + Server Task

**Input**

> "Verify my insurance and show me the missing forms."

**Expected behavior**

1. Agent identifies both goals.
2. Agent selects required capabilities.
3. Server capability executes.
4. Result returns.
5. Agent continues/replans.
6. Client capability executes.
7. Browser visibly changes.
8. Client result returns.
9. Agent checks goal.
10. Final response is produced.

**Pass condition:**

All required events occur and both capability executions are correlated to the same session.

---

## AT-09 — Delayed Backend Operation

Configure:

```text
verify_insurance delay = 3 seconds
```

**Input**

> "Verify my insurance."

**Expected**

Backend waits approximately configured delay.

Core does not prematurely report success.

The voice/UI layer remains responsive according to the selected live interaction design.

**Pass condition:**

No false completion occurs before the tool result.

---

## AT-10 — Controlled Backend Failure

Configure:

```text
verify_insurance = failure
```

**Input**

> "Verify my insurance."

**Expected**

```text
backend failure
 → SDK structured error
 → Core correlation
 → ADK tool failure
 → natural recovery/failure response
```

**Pass condition:**

No raw traceback or infrastructure error code is spoken/displayed as the user-facing response.

---

## AT-11 — Duplicate Invocation

Send the same `invocation_id` twice.

**Expected**

Developer function executes once.

**Pass condition:**

Execution counter == 1.

---

## AT-12 — Timeout

Configure the fake backend delay beyond the invocation timeout.

**Expected**

Core returns a deterministic timeout state.

**Pass condition:**

No fabricated success result.

No infinite retry.

---

## AT-13 — Reconnect

1. Start session.
2. Establish connection.
3. Interrupt frontend connection.
4. Reconnect using the same session identity.
5. Submit another request.

**Expected**

The request is processed in the same active session.

**Pass condition:**

Session identity remains unchanged and the new request succeeds.

---

## AT-14 — Project Isolation

Create:

```text
Project A:
tool_a

Project B:
tool_b
```

**Action**

Run a session for Project A.

**Expected**

`tool_b` is unavailable.

**Pass condition:**

Cross-project capability invocation is rejected deterministically.

---

## AT-15 — Manual Browser Verification

Human verifier performs:

```text
voice/user request
    ↓
agent response
    ↓
client capability
    ↓
visible UI change
    ↓
server capability
    ↓
visible/observable result
    ↓
final response
```

**Pass condition:**

The behavior is observed in the real application, not inferred from test logs.

---

# 45. Trace/Event Verification

The Core must make enough structured execution information available to tests to prove ordering.

At minimum, each execution event must identify:

```text
event_type
timestamp
project_id
session_id
invocation_id (when applicable)
capability_id (when applicable)
```

VS-01 test event types:

```text
SESSION_CREATED
CAPABILITY_REGISTERED
USER_INPUT_RECEIVED
TOOL_SELECTED
INVOCATION_CREATED
INVOCATION_DISPATCHED
INVOCATION_RECEIVED
CAPABILITY_STARTED
CAPABILITY_COMPLETED
CAPABILITY_FAILED
RESULT_RECEIVED
TOOL_RESULT_RETURNED
GOAL_CHECKED
FINAL_RESPONSE
CONNECTION_LOST
CONNECTION_RESTORED
```

Tests must assert event ordering.

Example:

```text
TOOL_SELECTED
    <
INVOCATION_CREATED
    <
INVOCATION_DISPATCHED
    <
CAPABILITY_STARTED
    <
CAPABILITY_COMPLETED
    <
RESULT_RECEIVED
    <
TOOL_RESULT_RETURNED
```

This is stronger than asserting only the final response.

---

# 46. Execution Evidence

Every end-to-end acceptance test should produce:

```text
Test ID
Scenario
Input
Expected tool sequence
Observed tool sequence
Expected final state
Observed final state
Relevant invocation IDs
Pass/Fail
```

For manual tests additionally record:

```text
Browser result
Visible UI result
Voice result
Developer backend observation
```

A final textual answer from the agent is not sufficient proof that a tool executed.

---

# 47. Automated Agent Evaluation

Where possible, agent tests should evaluate both:

### Outcome

Did the correct final state occur?

### Trace

Did the expected capability sequence occur?

Example:

```text
Expected:
verify_insurance
highlight_missing_forms

Observed:
verify_insurance
highlight_missing_forms

Outcome:
frontend missing-form state == expected
```

If the model produces an alternate valid execution order, the test may accept that order only if the scenario's dependencies allow it.

For dependent operations, ordering is mandatory.

For independent operations, concurrency/order must be specified as an allowed set rather than an arbitrary exact sequence.

---

# 48. Concurrency Verification

VS-01 must prove that independent capabilities can execute concurrently when ADK chooses parallel execution and the runtime permits it.

Use two fake operations:

```text
tool_a = 2 seconds
tool_b = 2 seconds
```

If both are independent and executed in parallel:

```text
elapsed time ≈ 2 seconds + overhead
```

not:

```text
≈ 4 seconds
```

The test must not use a fragile exact timing assertion.

Instead assert:

```text
tool_a started before tool_b completed
tool_b started before tool_a completed
both completed
```

and use a generous timing bound only as a secondary regression signal.

---

# 49. Security/Boundary Verification

Tests must prove:

### Wrong project

```text
Project A session
→ Project B capability
→ reject
```

### Wrong location

```text
CLIENT capability
→ SERVER destination
→ reject
```

### Invalid arguments

```text
missing required parameter
→ reject
→ developer function not executed
```

### Invalid result

```text
developer returns schema-invalid value
→ SDK/Core rejects result
→ invalid result never reaches agent as successful data
```

### Malformed message

```text
invalid envelope
→ reject
→ no capability execution
```

---

# 50. Regression Requirements

VS-01 is the first implementation slice, so its complete acceptance suite becomes the regression baseline.

After VS-01 is frozen:

```text
VS-02
  +
VS-01 regression suite
```

Future slices must not silently break:

- capability registration;
- capability schema;
- invocation correlation;
- client/server routing;
- project/session isolation;
- duplicate protection;
- session lifecycle;
- dynamic tool exposure.

---

# 51. Requirement-to-Proof Matrix

| Requirement | Implementation | Proof |
|---|---|---|
| Three isolated codebases | separate projects/envs | isolation tests |
| SDK installed by developer app | package installation | AT-02 |
| No Core/SDK imports | dependency boundary | source scan |
| Dynamic tools | ADK toolset | S4/S5 + AT-05 |
| No hardcoded developer tools | generic agent | AT-05 |
| Multiple tools | 4+ capabilities | AT-03/04 |
| Client routing | WebSocket client path | AT-06 |
| Server routing | server path | AT-07 |
| Multi-step planning | ADK + tool results | AT-08 |
| Goal checking | post-result agent turn | AT-08 |
| Failure recovery | structured errors | AT-10 |
| Timeout | deterministic timeout | AT-12 |
| Duplicate protection | invocation registry | AT-11 |
| Reconnection | session lifecycle | AT-13 |
| Project isolation | project/session validation | AT-14 |
| Real frontend verification | browser | AT-15 |
| Voice interaction | live/voice runtime | manual voice test |
| No raw technical errors | error normalization | AT-10 |
| Async execution | asyncio + async transports | unit/integration |
| Independent processes | separate servers | Level 4 |

---

# 52. Completion Gate

VS-01 may be declared **COMPLETE** only if every gate below is satisfied.

## Gate A — Repository Integrity

- [ ] Three codebases remain separate.
- [ ] Each has its own dependency environment.
- [ ] No forbidden imports exist.
- [ ] SDK is consumed as an installed package.
- [ ] No shared runtime code exists between codebases.

**Evidence:** dependency manifests, import scan, successful independent startup.

---

## Gate B — Core Runtime

- [ ] Core starts independently.
- [ ] Environment construction passes.
- [ ] Session creation passes.
- [ ] Generic ADK agent passes.
- [ ] Dynamic toolset passes.
- [ ] Multiple capabilities appear as individual ADK tools.
- [ ] No developer-specific tool names exist in agent implementation.

**Evidence:** unit tests + ADK spike + source inspection.

---

## Gate C — Protocol Contracts

- [ ] Registration contract passes.
- [ ] Invocation contract passes.
- [ ] Result contract passes.
- [ ] Error contract passes.
- [ ] Protocol version validation passes.
- [ ] Project/session/invocation IDs are preserved end-to-end.
- [ ] Invalid messages are rejected.

**Evidence:** contract-test suite.

---

## Gate D — Federated Execution

- [ ] Client capability executes only in frontend.
- [ ] Server capability executes only in backend.
- [ ] Core never directly calls developer business functions.
- [ ] Results return through the network boundary.
- [ ] Client and server capabilities can coexist in one session.

**Evidence:** process-level integration tests.

---

## Gate E — Agentic Behavior

- [ ] Agent can select among multiple capabilities.
- [ ] Agent can execute a single capability.
- [ ] Agent can execute a multi-step task.
- [ ] Agent receives tool results.
- [ ] Agent can continue after a result.
- [ ] Agent performs goal checking.
- [ ] Agent can recover from a controlled tool failure.
- [ ] No model-response parsing is used.

**Evidence:** AT-06 through AT-10 + ADK trace assertions.

---

## Gate F — Reliability

- [ ] Timeout behavior passes.
- [ ] Duplicate invocation behavior passes.
- [ ] Retry classification passes.
- [ ] Reconnection passes.
- [ ] No infinite retry exists.
- [ ] No false success is produced after timeout.

**Evidence:** AT-11 through AT-13.

---

## Gate G — Isolation/Security

- [ ] Cross-project capability invocation is rejected.
- [ ] Wrong-location execution is rejected.
- [ ] Invalid arguments do not execute developer functions.
- [ ] Invalid results do not become successful tool results.
- [ ] Raw exceptions do not cross the wire.

**Evidence:** boundary/security test suite.

---

## Gate H — Real Application

- [ ] Frontend runs in the real browser.
- [ ] Backend runs as a separate process.
- [ ] Core runs as a separate process.
- [ ] SDK is installed into the developer application.
- [ ] Real user input reaches Core.
- [ ] Real client capability changes browser state.
- [ ] Real server capability executes backend code.
- [ ] Real results return to the agent.
- [ ] Final response reaches the user.

**Evidence:** recorded manual verification checklist.

---

## Gate I — Voice

- [ ] Native/live voice path works.
- [ ] User can provide a real voice turn.
- [ ] Agent produces a voice response.
- [ ] Tool execution can occur during the voice interaction.
- [ ] Technical errors are not spoken verbatim.

**Evidence:** manual voice acceptance test.

---

## Gate J — Test Suite

All must pass:

```text
SDK unit tests
Core unit tests
Contract tests
ADK integration tests
Transport tests
Process integration tests
End-to-end tests
Failure/recovery tests
Isolation tests
Browser tests
Manual acceptance tests
Voice acceptance test
```

No known failing test may be waived merely because the happy path works.

---

# 53. Mandatory Manual Acceptance Script

The final human verification must execute this exact sequence.

### Step 1 — Start

Start:

```text
Core
Developer Backend
Developer Frontend
```

Verify all three are independent processes.

### Step 2 — Connect

Open the browser.

Verify the frontend establishes the VoxCore session.

### Step 3 — Client capability

Say/type:

> "Show me the missing forms."

Verify:

```text
agent receives request
→ client tool selected
→ invocation sent
→ frontend function executes
→ UI changes
→ result returns
→ final response
```

### Step 4 — Server capability

Say/type:

> "Verify my insurance."

Verify:

```text
agent
→ server tool
→ backend
→ fake API
→ result
→ agent
→ response
```

### Step 5 — Multi-step

Say/type:

> "Verify my insurance and show me the missing forms."

Verify the complete multi-step execution trace.

### Step 6 — Delay

Configure a visible artificial delay.

Repeat the server operation.

Verify that the result does not arrive before the configured delay.

### Step 7 — Failure

Configure the fake API to fail.

Repeat.

Verify:

```text
structured failure
→ agent recovery/natural response
```

and not a raw technical error.

### Step 8 — Reconnect

Disconnect/reconnect the frontend.

Submit another request.

Verify the session remains valid.

### Step 9 — Voice

Repeat a supported scenario using actual voice.

Verify the voice path and capability execution.

A human must mark each step:

```text
PASS / FAIL
```

with the observed evidence.

---

# 54. Implementation Order

The coding agent must implement in this order:

```text
Phase 0
Repository/dependency boundary validation
        ↓
Phase 1
ADK dynamic-tool spike
        ↓
Phase 2
Python-browser runtime spike
        ↓
Phase 3
SDK contracts + registration
        ↓
Phase 4
Core contracts + environment/session
        ↓
Phase 5
Dynamic ADK toolset
        ↓
Phase 6
Deterministic router
        ↓
Phase 7
Server SDK + backend execution
        ↓
Phase 8
Client SDK + frontend execution
        ↓
Phase 9
Multi-tool orchestration
        ↓
Phase 10
Voice/live path
        ↓
Phase 11
Automated test suite
        ↓
Phase 12
Full-process E2E
        ↓
Phase 13
Manual browser + voice verification
        ↓
Phase 14
Completion Gate
        ↓
VS-01 FROZEN
```

At each phase:

```text
Implement
  ↓
Test
  ↓
Verify
  ↓
Only then continue
```

---

# 55. Implementation Stop Conditions

The coding agent must stop rather than guessing if:

- ADK behavior differs from the assumed API;
- dynamic tool generation cannot preserve schemas;
- Python browser execution cannot perform the required client boundary;
- a wire contract is insufficient;
- a capability cannot be deterministically identified;
- an operation's retry safety is ambiguous;
- a session/reconnection behavior is ambiguous;
- voice/live tool execution differs materially from the expected lifecycle;
- a test cannot deterministically distinguish pass from failure.

The agent must report the specific uncertainty and proposed resolution.

It must not silently invent an architectural workaround.

---

# 56. VS-01 Frozen Boundary

After completion, VS-01 freezes these implementation contracts:

```text
Developer Application
        ↕
      SDK API
        ↕
 Capability Contract
        ↕
 Invocation Contract
        ↕
 Result/Error Contract
        ↕
 Network Protocol
        ↕
 Core Session/Environment
        ↕
 Dynamic ADK Toolset
        ↕
 Deterministic Router
```

Future slices may extend these contracts, but they must not silently invalidate them.

---

# 57. Final Implementation Principle

The objective is not:

> "The application seems to work."

The objective is:

> **Every important architectural claim made by VS-01 has a corresponding implementation mechanism, deterministic contract, automated test, runtime trace, and/or human acceptance procedure capable of proving that claim.**

The slice is frozen only when the evidence demonstrates:

```text
Correct Architecture
        +
Correct Contracts
        +
Correct Implementation
        +
Correct Runtime Behavior
        +
Correct Failure Behavior
        +
Correct Isolation
        +
Correct User-Facing Behavior
        +
Passing Regression Suite
        =
VS-01 Proven
```

Only then does VS-02 begin.
