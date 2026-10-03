# VoxCore — Architecture Design V1

> **Status:** Version 1 — Architecture Baseline | ***`FROZEN`***  
> **Purpose:** Authoritative design reference for subsequent Low-Level Design (LLD), prototype implementation, and future architectural refinement.

---

# 1. Document Purpose

This document defines the Version 1 architecture of **VoxCore**, an open-source, multi-tenant orchestration infrastructure for embedding real-time conversational Voice AI into developer applications.

The document establishes:

- system boundaries
- primary components
- component responsibilities
- ownership boundaries
- execution boundaries
- agent vs deterministic responsibilities
- client-side vs server-side capability execution
- session and project isolation
- runtime orchestration
- voice/orchestration separation
- SDK responsibilities
- developer application responsibilities
- data ownership
- security and reliability principles
- sandbox and policy-refinement responsibilities
- architectural invariants
- unresolved implementation-level decisions

This document intentionally does **not** define:

- exact class structures
- database schemas
- REST/WebSocket message schemas
- exact package structures
- exact ADK agent topology
- exact model/API versions
- exact deployment infrastructure
- detailed retry algorithms
- detailed authentication protocols
- detailed persistence mechanisms

Those belong to the Low-Level Design and implementation phases.

The purpose of this document is to establish a stable architectural foundation from which those details can be derived.

---

# 2. Architecture Status

VoxCore V1 is a **finished-product architecture baseline**, not an MVP architecture.

The prototype implementation may implement only a representative vertical slice of this architecture. The prototype must not redefine the product architecture merely because only a subset is implemented.

Architectural decisions use the following status terminology:

| Status | Meaning |
|---|---|
| **Established** | Directly required by the project requirements or already fixed by project direction. |
| **Proposed** | Architectural decision selected for V1 because it provides a suitable structure, but may still be revised if LLD investigation disproves an assumption. |
| **Pseudofrozen** | Agreed for V1 and should be treated as the current architecture unless a downstream technical constraint requires revision. |
| **Open** | Intentionally unresolved and must be decided during LLD or implementation research. |

---

# 3. System Vision

VoxCore is a developer-facing infrastructure layer that allows an existing application to gain a highly capable conversational Voice AI interface without requiring the developer to independently build:

- real-time voice infrastructure
- conversational orchestration
- multi-step tool planning
- client/server capability routing
- session management
- voice interaction management
- deterministic execution infrastructure
- conversational latency masking
- recovery behavior
- sandbox-based policy refinement

The developer remains the owner of:

- application UI
- application frontend
- application backend
- business logic
- business data
- actual capability implementations
- external services
- persistent user data
- long-term conversation storage

VoxCore provides the infrastructure that connects conversational intelligence with those developer-owned capabilities.

---

# 4. Core Architectural Principles

## 4.1 Google ADK Is the Core Agentic Framework

The VoxCore backend agentic/orchestration layer MUST use **Google ADK**.

LangChain, LangGraph, or another orchestration framework is not part of the core architecture.

Google ADK provides the agent/tool execution abstraction used by VoxCore.

---

## 4.2 Deterministic First

LLMs and agents are used where flexible reasoning is actually required.

They are responsible for:

- understanding user intent
- understanding the user's ultimate goal
- reasoning
- dynamic planning
- selecting capabilities
- deciding execution order
- interpreting results
- adapting plans
- conversational behavior

Deterministic code is responsible for operations that can be performed reliably without an LLM.

This principle does **not** mean that the agent should be rigid or incapable of learning from execution outcomes.

The Core Agentic Runtime is expected to use the current session's context, previous actions, capability results, failures, and other relevant execution history to improve its next decision.

This is **execution-time adaptation** and is part of normal agentic behavior. It changes the agent's current plan or strategy; it does not automatically modify persistent project policy.

Examples include:

- authentication
- authorization
- API-key validation
- session lookup
- project lookup
- configuration validation
- schema validation
- serialization
- routing
- transport handling
- correlation
- duplicate prevention
- timeout handling
- deterministic error classification
- connection management
- capability registration
- execution dispatch

The system MUST NOT use an agent to perform a task that ordinary deterministic code can reliably perform.

---

## 4.3 ADK Owns Agent Tool Invocation

The agent MUST NOT be treated as a source of natural-language instructions that VoxCore later parses to discover tool calls.

VoxCore MUST NOT depend on:

- regex parsing of model responses
- natural-language inspection to detect tool calls
- heuristic inference of whether a tool was requested
- custom post-processing of conversational output to determine tool invocation

Instead:

```text
Model
  ↓
structured tool/function call
  ↓
Google ADK tool execution lifecycle
  ↓
registered ADK tool
  ↓
VoxCore deterministic execution layer
```

The ADK tool abstraction is the boundary through which VoxCore receives an already-selected capability invocation.

This is a foundational architectural invariant.

---

## 4.4 Unified Capability Execution

Client-side and server-side developer capabilities follow the same conceptual execution model.

A capability is exposed to the agent as an individual ADK tool.

The capability contains or is associated with metadata describing its execution location.

Conceptually:

```text
Capability
├── name
├── description
├── input schema
├── output schema
├── execution location
└── execution/policy metadata
```

Execution location is infrastructure metadata.

The agent does not need to implement different reasoning logic for:

```text
client capability
server capability
```

Instead:

```text
Agent
  ↓
ADK Tool
  ↓
Deterministic Execution Router
  ↓
┌─────────────────┐
│ client          │ server
│                 │  
Client SDK        Server SDK
│                 │
Developer         Developer
Frontend          Backend
```

---

## 4.5 Generic / Black-Box Orchestration

The core agentic runtime MUST remain generic.

It MUST NOT contain hardcoded business logic such as:

```text
if developer == X:
    call tool A

if application == Y:
    call tool B
```

Developer-specific behavior comes from the dynamically constructed project environment:

- instructions
- personality
- policies
- autonomy configuration
- registered capabilities
- capability schemas
- execution locations
- workflows
- developer-provided context

The same core runtime must be capable of operating different projects without modifying its implementation for each project.

---

## 4.6 Perceive → Plan → Execute → Check

VoxCore is not intended to be a simple:

```text
user request → tool → result
```

router.

The core orchestration model is:

```text
PERCEIVE
    ↓
PLAN
    ↓
EXECUTE
    ↓
CHECK
    ↓
complete?
 ┌──┴──┐
yes    no
 ↓      ↓
respond replan/recover
```

The runtime must be able to:

- understand the user's ultimate goal
- break complex goals into multiple actions
- execute independent capabilities in parallel where appropriate
- execute dependent actions sequentially
- interpret capability results
- determine whether the goal has been achieved
- recover from failures
- modify the execution strategy when necessary

The exact internal ADK agent topology remains an implementation decision.

---

## 4.7 Execution-Time Learning vs Policy Refinement

VoxCore explicitly distinguishes between two different forms of adaptation.

**Execution-time learning / self-correction** happens while an agent is solving the current task.

The agent may use:

- previous actions in the current session
- previous capability results
- observed failures
- tool errors
- intermediate state
- conversation context
- the current goal
- approved project policies and constraints

to avoid repeating an unsuccessful approach and to choose a better strategy.

For example:

```text
Attempt A
    ↓
failure
    ↓
understand what happened
    ↓
use execution history / context
    ↓
change plan
    ↓
Attempt B
```

This behavior is expected in production.

It is temporary, task-oriented adaptation. It does not mean the agent is rewriting the project's persistent business rules.

**Policy refinement** is different.

Policy refinement concerns the business rules, constraints, requirements, and operating expectations that define how an agent should work for a particular developer application.

Policy refinement is a developer-controlled configuration activity that may occur in the sandbox or in a live production project.

A developer may observe that the agent misunderstands a business constraint or that the project's business behavior has not been expressed clearly enough. The developer can then refine the relevant policy, test it again, and approve the resulting configuration for future runtime use.

Therefore:

```text
Runtime self-correction
    → "What should I do differently now?"
    → agentic
    → production
    → current task / session

Policy refinement
    → "What business rule or constraint should I understand differently?"
    → developer-controlled
    → sandbox or production
    → developer-controlled configuration lifecycle
    → activated runtime configuration
```

The production agent may recover, replan, and learn from its current execution history, but it does not autonomously convert those experiences into persistent business policy.

---

# 5. System Boundary

VoxCore consists of infrastructure operated by VoxCore and SDKs integrated into the developer application.

The developer application itself is outside the VoxCore backend boundary.

```text
                         DEVELOPER APPLICATION
                 ┌────────────────────────────────┐
                 │                                │
                 │          Frontend              │
                 │             │                  │
                 │        Client SDK              │
                 │                                │
                 │                                │
                 │          Backend               │
                 │             │                  │
                 │        Server SDK              │
                 │                                │
                 └─────────────┬──────────────────┘
                               │
                         Network Boundary
                               │
                               ▼
                    ┌──────────────────────┐
                    │       VOXCORE        │
                    │                      │
                    │ Environment          │
                    │ Initializer          │
                    │                      │
                    │ Core Agentic         │
                    │ Runtime              │
                    │                      │
                    │ Deterministic        │
                    │ Infrastructure       │
                    │                      │
                    │ Voice Agent Runtime  │
                    └──────────────────────┘
```

---

# 6. Primary Components

VoxCore V1 contains five primary architectural components.

```text
1. VoxCore SDK
2. Environment Initializer
3. Core Agentic Runtime
4. Deterministic Infrastructure
5. Voice Agent Runtime
```

These are the primary architectural components.

The following are **not** separate top-level components:

- MCP
- individual tools
- capability registry
- router
- session manager
- authentication service
- policy engine
- workflow engine
- toolset
- database
- cache
- WebSocket handler
- transport adapter
- ADK sub-agent
- planner
- evaluator
- retry handler

These are implementation mechanisms or internal responsibilities belonging to one of the five primary components.

This keeps the architecture intentionally compact.

---

# 7. Developer Application

The Developer Application is outside VoxCore's internal runtime.

It is the application being enhanced with VoxCore.

It consists conceptually of:

```text
Developer Application
├── Frontend
│   └── VoxCore Client SDK
│
├── Backend
│   └── VoxCore Server SDK
│
├── Business Logic
├── Business Data
├── UI
└── External Services
```

## Developer Application Owns

The developer owns:

- frontend UI
- backend application
- business logic
- business data
- databases
- external APIs
- actual capability implementations
- long-term user data
- persistent conversation storage
- application-specific authorization decisions where applicable

VoxCore must not become the system of record for developer business data.

---

# 8. Component 1 — VoxCore SDK

The VoxCore SDK is the primary developer integration interface.

The SDK is not merely a thin wrapper around a network API.

It provides the application-side infrastructure required to connect a developer application to VoxCore.

The SDK is divided into:

```text
VoxCore SDK
├── Client SDK
│   ├── JavaScript
│   └── Python
│
└── Server SDK
    ├── JavaScript
    └── Python
```

Python and JavaScript are independently supported on both client and server sides.

A developer is not required to use the same language on both sides.

For example:

```text
React Frontend
    ↓
JavaScript Client SDK

Python Backend
    ↓
Python Server SDK
```

is a supported architecture.

---

# 9. Client SDK

The Client SDK runs inside the developer's frontend environment.

Typical environments include:

- browser applications
- web applications
- frontend JavaScript applications
- other supported client environments in future implementations

## Client SDK Responsibilities

The Client SDK is responsible for:

- VoxCore client connection
- session integration
- voice/audio communication
- event communication
- capability registration
- client capability execution
- returning capability results
- returning capability errors
- connection lifecycle
- reconnection
- temporary network recovery
- browser/application integration

---

## 9.1 Client Capability Registration

A developer can register a frontend capability with the Client SDK.

Conceptually:

```text
Developer Function
      ↓
Client SDK Registration
      ↓
Capability Metadata
      ↓
VoxCore Session
      ↓
Agent Environment
      ↓
ADK Tool
```

The developer provides enough information for VoxCore to expose the capability to the agent.

The registration contract should include, at minimum:

- capability name
- description
- input schema
- output schema
- execution location

The exact API is an LLD concern.

---

## 9.2 Client Capability Execution

When the agent selects a client capability:

```text
ADK
 ↓
Client ADK Tool
 ↓
Deterministic Router
 ↓
Client Session Channel
 ↓
Client SDK
 ↓
Developer Function
```

The Client SDK executes the actual developer function.

The VoxCore backend does not execute browser business logic.

---

## 9.3 Client Results

After the frontend capability executes:

```text
Developer Function
 ↓
Client SDK
 ↓
VoxCore Client Channel
 ↓
Deterministic Infrastructure
 ↓
ADK Tool Result
 ↓
Core Agentic Runtime
```

The result is returned as structured data.

The agent can then:

- interpret the result
- determine whether the goal was completed
- continue planning
- execute another capability
- communicate the final result

---

# 10. Server SDK

The Server SDK runs inside the developer's backend environment.

It provides the developer-side infrastructure necessary for VoxCore to invoke backend capabilities.

## Server SDK Responsibilities

The Server SDK is responsible for:

- server capability registration
- capability metadata
- schema extraction or registration
- authenticated connection to VoxCore
- invocation handling
- dispatching to developer functions
- input validation
- result serialization
- result validation
- error normalization
- lifecycle management
- correlation identifiers
- duplicate invocation protection where required

The Server SDK must not contain business logic owned by the developer.

It acts as the execution boundary between VoxCore and developer-owned backend functions.

---

# 11. Component 2 — Environment Initializer

The Environment Initializer runs inside VoxCore.

Its purpose is to construct the project-specific runtime environment required by the generic agent.

The core principle is:

```text
Generic Agent
      +
Project Environment
      =
Specialized Runtime Behavior
```

The agent implementation itself remains generic.

---

## 11.1 Environment Inputs

At session initialization, the Environment Initializer obtains or receives validated information including:

- developer identity
- project identity
- session identity
- project configuration
- instructions
- personality configuration
- autonomy configuration
- guardrails
- policies / business rules / operating constraints
- workflow definitions
- capability definitions
- capability descriptions
- capability schemas
- capability execution locations
- developer-provided session context

Policies in this environment represent developer-defined business rules, constraints, requirements, and operating expectations. They provide boundaries and business semantics for agentic judgment; they are not intended to replace the agent's reasoning or prescribe every individual decision.
---

## 11.2 Environment Construction

The initializer:

1. resolves the project/session
2. loads applicable configuration
3. loads registered capability metadata
4. loads policies and autonomy boundaries
5. loads developer-provided context
6. validates configuration
7. validates capability metadata
8. constructs the runtime environment
9. exposes the resulting environment to the Core Agentic Runtime

All deterministic validation must happen in deterministic infrastructure.

The initializer should not require an agent to perform configuration retrieval or validation.

---

## 11.3 Environment Boundary

The Project Runtime Environment is **not** a copy of the developer application.

VoxCore must not copy the developer's entire source codebase into the agent runtime.

Instead, the environment contains the operational representation required by the agent, such as:

```text
instructions
policies / business rules / operating constraints
capabilities
schemas
execution locations
workflows
context
autonomy rules
```

The developer application remains the owner of actual business implementation and data.

The policies in this environment are approved project configuration. The agent can reason within those constraints, but normal production execution does not rewrite them as a result of an execution failure.
---

# 12. Component 3 — Core Agentic Runtime

The Core Agentic Runtime is the primary reasoning and orchestration engine.

It is implemented using Google ADK.

Its responsibility is to transform conversational intent into a reliable multi-step execution process.

---

# 13. Core Agentic Runtime Responsibilities

The runtime is responsible for:

- understanding user intent
- understanding the user's ultimate goal
- reasoning
- planning
- selecting capabilities
- multi-step orchestration
- sequential execution
- parallel execution where appropriate
- dependency handling
- result interpretation
- completion checking
- replanning
- recovery
- dynamic strategy adaptation
- execution-time self-correction using current context and execution history
- avoiding repetition of known unsuccessful approaches within the active task/session
- respecting project autonomy constraints
- reasoning within approved business policies and constraints

The runtime is therefore expected to be intelligent and adaptive during execution. A failure does not automatically mean that a new policy must be created. The normal first response to an execution failure is for the agent to understand the result and determine whether the current task can be completed through a different strategy.

Persistent policy changes belong to the developer-controlled policy lifecycle described later in this document. This lifecycle may be used in sandbox or production; the production agent itself must not autonomously mutate persistent policy.
---

# 14. Tool Representation in ADK

Each developer capability must be represented to the Core Agentic Runtime as an individual ADK tool.

For example:

```text
get_cart()
add_item()
verify_payment()
highlight_missing_forms()
open_checkout()
```

The runtime should not expose one generic meta-tool such as:

```text
execute_capability(name, arguments)
```

unless a future technical requirement proves that such a mechanism is necessary.

The preferred architecture is:

```text
ADK
├── get_cart
├── add_item
├── verify_payment
├── highlight_missing_forms
└── open_checkout
```

This allows the agent/model to reason over meaningful capability descriptions and schemas directly.

---

# 15. Tool Invocation Boundary

The invocation lifecycle is:

```text
User
 ↓
Voice / Conversation Layer
 ↓
Core Agentic Runtime
 ↓
Model reasoning
 ↓
Structured tool call
 ↓
Google ADK
 ↓
Registered ADK Tool
 ↓
Deterministic Execution Router
 ↓
Destination
```

The important architectural rule is:

> The model decides **which capability to invoke** through the ADK tool mechanism. Deterministic infrastructure decides **where and how that already-selected capability executes**.

This prevents the deterministic infrastructure from becoming a second reasoning engine.

---

# 16. Unified Capability Execution Model

Every capability has an execution location.

```text
execution_location = client
```

or:

```text
execution_location = server
```

The same execution architecture is used for both.

```text
                   ADK Tool Call
                         │
                         ▼
                Deterministic Router
                         │
              ┌──────────┴──────────┐
              │                     │
           CLIENT                 SERVER
              │                     │
              ▼                     ▼
        Client SDK              Server SDK
              │                     │
              ▼                     ▼
        Developer               Developer
         Frontend                Backend
```

This is the **Federated Tool Boundary**.

---

# 17. Client-Side Capability Path

```text
Core Agentic Runtime
        ↓
ADK Client Tool
        ↓
Deterministic Execution Router
        ↓
Active Session Resolution
        ↓
Client Execution Channel
        ↓
Client SDK
        ↓
Developer Frontend Function
        ↓
Result
        ↓
Client SDK
        ↓
VoxCore
        ↓
ADK Tool Result
        ↓
Core Agentic Runtime
```

The frontend function is executed only by the developer application.

VoxCore routes the invocation but does not execute frontend application logic.

---

# 18. Server-Side Capability Path

```text
Core Agentic Runtime
        ↓
ADK Server Tool
        ↓
Deterministic Execution Router
        ↓
Project/Server Resolution
        ↓
Server SDK
        ↓
Developer Backend Function
        ↓
Result
        ↓
Server SDK
        ↓
VoxCore
        ↓
ADK Tool Result
        ↓
Core Agentic Runtime
```

The developer backend remains responsible for actual business logic.

---

# 19. MCP Position in VoxCore

MCP is **not required as the core VoxCore developer-capability execution mechanism in V1**.

The primary architecture is:

```text
ADK Tool
   ↓
VoxCore Deterministic Router
   ↓
Client SDK / Server SDK
   ↓
Developer Application
```

MCP may still be supported in the future as:

- an interoperability mechanism
- an external integration mechanism
- an optional developer integration path
- a mechanism for connecting VoxCore to third-party MCP servers

However, MCP must not be introduced merely to solve a problem that VoxCore can already solve using its own SDK and deterministic routing infrastructure.

This decision intentionally reduces unnecessary protocol and lifecycle complexity.

---

# 20. Why MCP Is Not a Required Internal Dependency

VoxCore controls:

- the Core Agentic Runtime
- the deterministic routing infrastructure
- the Client SDK
- the Server SDK
- the developer integration contract

Therefore VoxCore does not inherently need a second tool protocol between its own infrastructure and its own SDKs.

Using ADK tools directly provides:

- direct integration with the ADK execution lifecycle
- direct structured tool calls
- unified client/server capability handling
- deterministic routing
- lower implementation complexity
- fewer protocol layers
- simpler debugging
- fewer lifecycle concerns

MCP remains valuable where interoperability requires it, but it is not a mandatory internal abstraction.

---

# 21. No Model-Response Parsing

The following architecture is explicitly prohibited:

```text
Model response
    ↓
parse text
    ↓
detect tool name
    ↓
extract arguments
    ↓
route manually
```

The correct architecture is:

```text
Model
    ↓
structured tool call
    ↓
ADK
    ↓
registered tool
    ↓
deterministic router
```

This is one of the most important implementation invariants of VoxCore.

---

# 22. Component 4 — Deterministic Infrastructure

Deterministic Infrastructure contains the non-agentic runtime mechanisms required to make VoxCore reliable.

It is intentionally broad.

It is not a separate intelligent system.

It provides infrastructure around the Core Agentic Runtime.

---

# 23. Deterministic Infrastructure Responsibilities

The component includes responsibilities such as:

### Security

- API-key validation
- authentication
- authorization
- project identity resolution
- session identity validation
- capability authorization
- project isolation

### Configuration

- configuration loading
- schema validation
- configuration validation
- capability metadata validation
- policy validation

### Capability Execution

- capability lookup
- execution-location resolution
- routing
- invocation dispatch
- correlation
- result validation
- serialization

### Session Infrastructure

- session creation
- session lifecycle
- session state
- temporary state retention
- reconnect handling
- session recovery
- connection association

### Transport

- client communication
- server communication
- WebSocket or equivalent client transport
- authenticated server transport
- message validation
- protocol handling

### Reliability

- timeout handling
- error normalization
- safe retry
- duplicate prevention
- idempotency mechanisms where required
- connection recovery

### Cross-Cutting Infrastructure

Potential responsibilities include:

- rate limiting
- quotas
- observability
- tracing
- metrics
- secret management
- runtime isolation

These remain implementation-level infrastructure concerns and are not separate top-level architecture components.

---

# 24. Deterministic Router

The deterministic router is an internal capability of Deterministic Infrastructure.

Its responsibility is not to decide what the user wants.

Its responsibility is to route an already-selected capability.

Conceptually:

```text
ADK Tool Invocation
        ↓
Validate invocation
        ↓
Resolve capability
        ↓
Resolve project
        ↓
Resolve session
        ↓
Resolve execution location
        ↓
Authorize
        ↓
Dispatch
```

For example:

```text
open_checkout
execution_location = client
session = S123
project = P42
```

becomes:

```text
P42 + S123 + open_checkout
        ↓
Client SDK associated with S123
```

Whereas:

```text
get_cart
execution_location = server
project = P42
```

becomes:

```text
P42 + get_cart
        ↓
Server SDK associated with P42
```

---

# 25. Routing Must Be Deterministic

The router must not use an LLM to determine:

- where a tool exists
- which project owns a tool
- which session owns a client
- whether a capability is client-side or server-side
- whether an API key is valid
- whether arguments satisfy a schema

Those are deterministic facts.

---

# 26. Schema Validation

Input and output validation must be deterministic.

Conceptually:

```text
Agent
 ↓
Tool Call
 ↓
Input Schema Validation
 ↓
Execution
 ↓
Output Schema Validation
 ↓
ADK Tool Result
```

Invalid data must not be silently passed through.

The exact schema technology is an LLD decision.

---

# 27. Error Handling

Technical errors must be normalized by deterministic infrastructure before being exposed to the agent/voice layer.

Examples include:

- malformed arguments
- invalid schema
- authentication failure
- authorization failure
- unavailable developer backend
- timeout
- network failure
- connection loss
- developer function exception
- invalid developer result

The system must preserve enough structured information for the agentic runtime to reason about recovery while preventing raw infrastructure details from being unnecessarily exposed to the user.

---

# 28. Retry Policy

Retries must be deterministic and capability-aware.

The system must not blindly retry every operation.

For example:

```text
read operation
    → potentially retryable

idempotent operation
    → potentially retryable

non-idempotent side-effect
    → retry only with appropriate protection
```

The exact retry policy belongs to LLD.

The architecture requires that retry behavior be safe and deterministic.

---

# 29. Correlation and Duplicate Prevention

Distributed execution can result in:

- duplicated messages
- connection retries
- delayed responses
- client reconnects
- server reconnects

Therefore capability invocations should have a correlation identity.

Conceptually:

```text
project_id
session_id
invocation_id
capability_id
```

The exact identifier model belongs to LLD.

The architectural requirement is that VoxCore be able to distinguish:

```text
new invocation
duplicate invocation
late result
unknown result
```

where required.

---

# 30. Component 5 — Voice Agent Runtime

The Voice Agent Runtime is the conversational interface between the user and the system.

It is deliberately separated from backend orchestration.

The voice layer uses a native Speech-to-Speech / multimodal architecture rather than a mandatory:

```text
ASR → LLM → TTS
```

pipeline.

The exact model and provider are an implementation decision and must be validated against the available Google/ADK/voice infrastructure before being frozen.

---

# 31. Voice Runtime Responsibilities

The Voice Agent Runtime is responsible for:

- natural conversation
- voice input/output
- conversational pacing
- natural responses
- conversational context required for the active interaction
- latency masking
- natural progress communication
- natural error communication
- presenting completed results
- maintaining conversational engagement

It does not own business orchestration.

---

# 32. Voice Runtime Is Asynchronous

The voice layer operates asynchronously from backend orchestration.

Conceptually:

```text
User
 ↓
Voice Runtime
      ║
      ║ asynchronous communication
      ▼
Core Agentic Runtime
      ↓
Plan
      ↓
Execute
      ↓
Check
```

The voice layer can continue engaging naturally while backend operations execute.

---

# 33. Silent System Updates

Backend orchestration communicates internal state to the voice layer through system-level updates that are not exposed as raw technical messages to the user.

For example:

```text
Backend:
"Capability execution is taking longer than expected."
```

must not necessarily become:

```text
"HTTP 504 from developer API."
```

Instead, the conversational layer can naturally communicate:

> “Give me a second while I pull that up.”

The exact system-update protocol belongs to LLD.

The architectural requirement is that backend technical state and user-facing conversational language remain separate.

---

# 34. Error Communication

Technical errors must not be directly spoken to the user.

For example:

```text
HTTP 500
JSONDecodeError
TimeoutError
ConnectionReset
```

are internal system states.

The voice runtime should receive structured information sufficient to produce an appropriate conversational response.

Example:

```text
internal:
developer_backend_unavailable

voice interpretation:
"I’m sorry, that system seems to be unavailable right now."
```

The exact mapping belongs to the runtime implementation.

---

# 35. Complete Runtime Flow

A normal interaction conceptually follows:

```text
User speaks
    ↓
Developer Application
    ↓
Client SDK
    ↓
Voice Connection
    ↓
Voice Agent Runtime
    ↓
Core Agentic Runtime
    ↓
PERCEIVE
    ↓
PLAN
    ↓
EXECUTE
    ↓
Deterministic Tool Routing
    ↓
Developer Capability
    ↓
Tool Result
    ↓
CHECK
    ↓
Goal complete?
   ┌───────┴───────┐
   │               │
  Yes              No
   │               │
   │          Replan/Recover
   │               │
   │               └──────→ EXECUTE
   ↓
Voice Agent Runtime
    ↓
Developer Application
    ↓
User
```

---

# 36. Parallel and Sequential Execution

The agentic runtime must support both:

### Sequential execution

```text
A
 ↓
B
 ↓
C
```

when B depends on A and C depends on B.

### Parallel execution

```text
        ┌── B ──┐
A ──────┤       ├──── D
        └── C ──┘
```

when B and C are independent.

The decision of whether operations are independent is an agentic planning responsibility.

The actual concurrency mechanism is deterministic infrastructure.

---

# 37. Goal Checking

Tool execution is not automatically equivalent to task completion.

After execution, the agentic runtime must evaluate whether the user's ultimate goal has been achieved.

For example:

```text
User:
"Update my insurance, show missing forms, and book the earliest appointment."

Possible execution:

verify_insurance()
       ↓
highlight_missing_forms()
       ↓
check_availability()
       ↓
book_appointment()
```

The runtime must check whether all required outcomes have been achieved.

If not:

```text
CHECK
 ↓
REPLAN
 ↓
EXECUTE
```

---

# 38. Environment and Agent Relationship

The Environment Initializer prepares the context in which the generic agent operates.

```text
Project Configuration
        +
Capabilities
        +
Policies
        +
Autonomy
        +
Context
        ↓
Project Runtime Environment
        ↓
Generic ADK Agent
```

The runtime therefore does not require developer-specific code.

---

# 39. Configurable Autonomy

Developers control how much autonomy the agent has.

The environment can define constraints such as:

```text
Allowed capabilities
Allowed workflows
Allowed actions
Restricted actions
Approval requirements
Execution boundaries
```

The Core Agentic Runtime must respect these constraints.

Policies and autonomy settings constrain the agent's decision space; they do not replace the agent's reasoning.

The agent remains responsible for deciding how to achieve the user's goal within the approved business constraints.

For example, a policy may require approval above a certain transaction amount. The policy establishes the business constraint; the agent still reasons about whether approval is needed, what information must be gathered, and which available capability should be used.

A narrow project configuration must not be bypassed simply because the model finds another possible action.
---

# 40. Project Isolation

VoxCore is multi-tenant.

Every project must be isolated.

Project-specific:

- instructions
- personality
- policies
- capabilities
- schemas
- autonomy settings
- context
- sessions

must never accidentally cross project boundaries.

Conceptually:

```text
Project A
 ├── Environment A
 ├── Capabilities A
 └── Sessions A

Project B
 ├── Environment B
 ├── Capabilities B
 └── Sessions B
```

No runtime operation may accidentally resolve Project A's resources for Project B.

---

# 41. Session Binding

Tools and runtime behavior are dynamically bound to the active session.

Conceptually:

```text
Developer API Key
      ↓
Project
      ↓
Session
      ↓
Client Connection
      ↓
Project Runtime Environment
      ↓
Capabilities
```

For client capabilities, session identity is particularly important because the same developer backend may serve many browser clients simultaneously.

Example:

```text
Developer Backend
      │
      ├── Session A → Browser A
      ├── Session B → Browser B
      └── Session C → Browser C
```

A client capability invocation must reach the correct active session.

---

# 42. Session Recovery

VoxCore does not retain permanent end-user memory as part of its normal operating model.

However, active session state may be retained temporarily to survive:

- network interruptions
- temporary disconnections
- reconnects
- short-lived infrastructure failures

The purpose is continuity of the active interaction, not permanent user-memory storage.

---

# 43. Permanent User Memory

VoxCore does not become the permanent system of record for end-user conversational history.

Long-term user data remains developer-owned.

If a developer wants persistent history or personalization, the developer can:

- store the transcript
- store user context
- retrieve prior information
- inject context when a new session starts

---

# 44. Context Ingress

At session initialization, the developer may provide context required by the agent.

Conceptually:

```text
Developer Backend
       ↓
Session Context
       ↓
VoxCore
       ↓
Environment Initializer
       ↓
Agent Runtime
```

This enables personalized interactions without requiring VoxCore to permanently store the user's historical data.

---

# 45. Transcript Egress

Conversation transcripts should be made available to the developer.

Conceptually:

```text
Voice Conversation
       ↓
VoxCore
       ↓
Transcript Events
       ↓
Developer Infrastructure
       ↓
Developer Storage
```

The developer remains responsible for long-term storage and retention policies.

---

# 46. Security Boundary

Security is deterministic infrastructure.

The agent must not be responsible for:

- authenticating developers
- validating API keys
- authorizing projects
- validating session ownership
- enforcing tenant isolation
- validating capability access

The security boundary must execute before the relevant operation reaches developer-owned infrastructure.

---

# 47. Data Ownership

The ownership model is:

| Data / Responsibility | Owner |
|---|---|
| Business data | Developer |
| Business database | Developer |
| Business logic | Developer |
| Frontend application | Developer |
| Backend application | Developer |
| Actual capability implementation | Developer |
| Long-term transcript storage | Developer |
| Project configuration | VoxCore / developer configuration boundary |
| Active session state | VoxCore |
| Agent runtime state | VoxCore during active execution |
| Permanent end-user memory | Not owned by VoxCore |

The exact persistence model for VoxCore-controlled project configuration and active state is an LLD concern.

---

# 48. Sandbox

VoxCore includes a sandbox concept for developers to test and refine agent behavior. The sandbox is an important validation environment, but policy refinement is not restricted to the sandbox; authorized developers may also refine and activate policy while a project is live in production.

The sandbox should use the same fundamental architectural components as production.

It should not become an unrelated second orchestration implementation.

Conceptually:

```text
Sandbox
   ↓
Environment Initializer
   ↓
Core Agentic Runtime
   ↓
Deterministic Infrastructure
   ↓
Voice/Conversation Interface
```

The primary difference is the developer-controlled testing and feedback environment.

The sandbox is one controlled place where a developer can inspect agent behavior, identify business-behavior mismatches, refine project policies, and validate configuration. Equivalent developer-controlled policy refinement may also occur while the project is already live in production.

The sandbox is **not** intended to make the production agent dependent on an autonomous persistent learning loop.

Production execution remains adaptive at the task/session level through context, execution history, results, and replanning.
---

# 49. Sandbox Responsibilities

The sandbox should support:

- simulated conversations
- testing different user requests
- observing orchestration behavior
- reviewing execution plans
- observing capability calls
- observing failures
- inspecting relevant execution history
- providing manual developer feedback
- refining business policies and constraints
- validating autonomy boundaries
- comparing behavior before and after a policy refinement
- approving a configuration for activation in the applicable runtime environment

The developer remains the authority for deciding whether a refined policy accurately represents the intended business behavior.
---

# 50. Policy Refinement

Policy refinement exists so that the agent can better understand and operate within the developer's business.

A policy represents developer-defined business logic at the level of rules, constraints, requirements, conditions, approvals, prohibitions, and other operating expectations that should guide agentic decisions.

A policy is therefore **not** a replacement for agent judgment.

For example:

```text
Policy:
Refunds above ₹10,000 require approval.

Agentic judgment:
- determine whether the user's request is a refund
- inspect the relevant order
- determine the refund amount
- determine whether approval is required
- gather required information
- choose the appropriate capability
- decide what to do if an execution step fails
```

The policy constrains the decision space. The agent remains responsible for reasoning within that space.

Policy refinement is a **developer-controlled configuration process that may occur in sandbox or production**.

A typical refinement loop is:

```text
Developer
   ↓
Sandbox Conversation
   ↓
Observe Agent Behavior
   ↓
Identify Business-Behavior Mismatch
   ↓
Developer Feedback
   ↓
Policy Generation / Refinement Assistance
   ↓
Developer Review
   ↓
Policy Validation / Versioning
   ↓
Developer Approval
   ↓
Future Runtime Environment
```

Agentic assistance may be used inside the sandbox to analyze the observed behavior or propose a policy refinement. Such a proposal is not automatically active.

A policy becomes part of the project's approved runtime configuration only through the developer-controlled approval/configuration process.

### Policy Refinement Is Not Production Self-Learning

The production agent must **not** automatically turn an execution mistake into a persistent policy.

For example:

```text
Production execution
    ↓
agent makes mistake
    ↓
agent understands failure
    ↓
agent changes current plan
    ↓
agent tries a different approach
```

is valid.

But:

```text
Production execution
    ↓
agent makes mistake
    ↓
agent invents persistent policy
    ↓
policy automatically becomes active
```

is not the V1 architecture.

The first flow is execution-time self-correction.

The second flow is autonomous policy mutation and is explicitly outside the production architecture.

If a recurring behavior indicates that the project's business rules were incomplete, ambiguous, or incorrectly represented, that observation can become input to a developer-controlled policy refinement cycle. The refinement may be performed in sandbox or directly against the live project configuration, subject to validation and approval.

Policy storage, validation, versioning, approval, and activation are deterministic configuration responsibilities.

The exact sandbox/policy-assistance topology remains an LLD decision.

### 50.1 Live Production Policy Evolution

Business policies are expected to evolve after deployment. VoxCore therefore supports developer-controlled policy modification while an application is already connected to VoxCore and serving real users in production.

The policy lifecycle is:

```text
Developer / Authorized Business Owner
                ↓
        Modify Policy Definition
                ↓
       Deterministic Validation
                ↓
        Version / Review / Approve
                ↓
       Activate Policy Version
                ↓
       Applicable Runtime Environments
```

A production deployment does not make the policy immutable. Policy changes must not require redeploying the entire agentic runtime merely because a business rule, constraint, requirement, approval condition, or operating expectation changed.

The production agent may continue executing with the currently applicable policy while a developer prepares a new version. The exact semantics for whether an already-running session or task immediately adopts a newly activated policy version, remains pinned to its starting version, or switches at a defined safe boundary are intentionally left to LLD.

At minimum, the production policy lifecycle must provide a controlled mechanism for:

- policy editing
- validation
- versioning
- developer authorization / approval
- activation
- rollback or deactivation where required
- consistent propagation to applicable runtime environments

The critical architectural boundary is **developer-controlled versus autonomous**, not **pre-production versus production**.

```text
Runtime experience
    → changes the agent's current strategy

Developer-approved policy change
    → changes the agent's future operating constraints
```

The production agent may suggest or surface evidence for a policy improvement, but it must not autonomously turn that observation into an active persistent policy.
---

# 51. Failure Classification

Failures should be distinguished between at least three broad categories.

## 51.1 Infrastructure / Execution Failure

Examples:

- network timeout
- malformed response
- authentication failure
- unavailable service
- invalid schema
- transport failure
- developer function exception

These are primarily deterministic infrastructure concerns.

The infrastructure should catch, classify, and normalize these failures before returning the relevant structured result to the agent.

---

## 51.2 Reasoning / Planning Failure

Examples:

- incorrect execution order
- unnecessary capability selection
- incomplete plan
- wrong reasoning about dependencies
- failure to achieve the stated goal
- repeating an unsuccessful approach when the relevant failure information is already available

These are agentic concerns.

The expected production response is **self-correction**:

```text
failure / unexpected result
        ↓
understand what happened
        ↓
use context + execution history
        ↓
change strategy
        ↓
replan
        ↓
execute again when appropriate
        ↓
check
```

This is normal runtime behavior and does not by itself modify persistent policy.

---

## 51.3 Business-Policy / Configuration Mismatch

A different class of issue occurs when the agent's behavior is technically coherent but does not match the developer's intended business behavior.

Examples:

- a business rule was not expressed clearly enough
- a required business condition is missing from project configuration
- an approval boundary is incomplete
- a business exception was not represented
- the agent follows a reasonable interpretation that is nevertheless wrong for the developer's business

These issues are candidates for **sandbox policy refinement**.

They are not automatically converted into persistent policies during production execution.

This distinction prevents the system from treating every failure as either an infrastructure problem or an instruction to permanently change the agent.
---

# 52. Voice and Orchestration Separation

The Voice Agent Runtime and Core Agentic Runtime are separate responsibilities.

The Voice Runtime handles:

```text
conversation
voice
pacing
user-facing communication
```

The Core Agentic Runtime handles:

```text
reasoning
planning
capability selection
execution coordination
goal checking
recovery
execution-time self-correction
```

Neither component should silently absorb the other's responsibilities.

The Core Agentic Runtime may adapt its current execution strategy based on context and prior results, but persistent business-policy refinement remains outside normal production execution.
---

# 53. Control Plane and Runtime Plane

The architecture can be understood as two logical planes without introducing additional top-level components.

## Control / Configuration Responsibilities

These include:

- project configuration
- instructions
- policies / business rules
- autonomy
- capability registration
- schemas
- workflow definitions
- sandbox feedback
- policy refinement
- policy validation
- policy versioning
- developer approval / activation

These are primarily consumed by the Environment Initializer.

Policy refinement is a **developer-controlled configuration activity** that may occur before deployment or while the project is live in production. The control plane may contain tooling that assists developers in generating or editing policy, but production runtime execution does not autonomously mutate this configuration.

## Runtime Responsibilities

These include:

- sessions
- active environment
- agent execution
- capability invocation
- routing
- voice interaction
- results
- recovery
- execution-time learning from current context/history
- replanning

The runtime may adapt its current behavior without changing the persistent control-plane policy.

The two planes are logically distinct but do not need to become separate top-level architectural components.
---

# 54. Execution Responsibility Matrix

| Responsibility | Agentic Runtime | Deterministic Infrastructure | Client SDK | Server SDK | Voice Runtime | Developer App |
|---|---:|---:|---:|---:|---:|---:|
| Understand user intent | ✓ | | | | ✓ conversationally | |
| Plan multi-step task | ✓ | | | | | |
| Select capability | ✓ / ADK | | | | | |
| Tool invocation lifecycle | ADK | | | | | |
| Route capability | | ✓ | | | | |
| Validate schema | | ✓ | ✓ | ✓ | | |
| Authenticate | | ✓ | | | | |
| Project isolation | | ✓ | | | | |
| Client capability execution | | routing | ✓ | | | ✓ implementation |
| Server capability execution | | routing | | ✓ | | ✓ implementation |
| Business logic | | | | | | ✓ |
| Business data | | | | | | ✓ |
| Voice conversation | | | | | ✓ | |
| Goal completion check | ✓ | | | | | |
| Runtime self-correction | ✓ | | | | | |
| Retry mechanics | | ✓ | ✓ where applicable | ✓ where applicable | | |
| Long-term transcript storage | | | | | | ✓ |
| Active session recovery | | ✓ | ✓ | ✓ | ✓ | |
| Sandbox behavior analysis | ✓ / agentic assistance | validation / storage | | | | ✓ developer review |
| Policy refinement | assistance / proposal | validation / versioning / activation | | | | ✓ authority / approval |
| Policy enforcement | reasoning within policy | ✓ configuration / authorization enforcement | | | | |
| UI manipulation | | route | ✓ | | | ✓ |
| API/database execution | | route | | ✓ | | ✓ |

The matrix intentionally separates **runtime self-correction** from **policy refinement**. The former is an agentic production responsibility; the latter is a developer-controlled configuration lifecycle.
---

# 55. Complete Architecture

```text
                              END USER
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │  DEVELOPER FRONTEND   │
                     │                        │
                     │     Client SDK         │
                     └────────────┬───────────┘
                                  │
                         Voice / Client Channel
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                             VOXCORE                                 │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    VOICE AGENT RUNTIME                        │  │
│  │                                                               │  │
│  │  Native V2V / Multimodal Conversation                         │  │
│  │  Natural pacing / progress / user-facing communication        │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                      │
│                    asynchronous updates                             │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    CORE AGENTIC RUNTIME                       │  │
│  │                                                               │  │
│  │                     Google ADK                                │  │
│  │                                                               │  │
│  │        PERCEIVE → PLAN → EXECUTE → CHECK                     │  │
│  │                                                               │  │
│  │        reasoning / planning / tool selection                  │  │
│  │        multi-step orchestration / recovery                    │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                      │
│                         ADK Tool Call                               │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                 DETERMINISTIC INFRASTRUCTURE                  │  │
│  │                                                               │  │
│  │  Auth / Validation / Session / Routing / Transport            │  │
│  │  Schema Validation / Errors / Retry / Correlation              │  │
│  │  Project Isolation / Capability Dispatch                       │  │
│  └───────────────┬───────────────────────────────┬───────────────┘  │
│                  │                               │                  │
│             CLIENT TOOL                     SERVER TOOL             │
│                  │                               │                  │
└──────────────────┼───────────────────────────────┼──────────────────┘
                   │                               │
                   ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐
          │   Client SDK    │             │   Server SDK    │
          └────────┬────────┘             └────────┬────────┘
                   │                               │
                   ▼                               ▼
          Developer Frontend              Developer Backend
                   │                               │
                   ▼                               ▼
            Client Function                 Server Function
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                              Result / Error
                                   │
                                   ▼
                            VoxCore Runtime
```

---

# 56. Environment Initialization in the Architecture

Before normal agent execution:

```text
Developer Session Request
        ↓
Deterministic Authentication
        ↓
Project Resolution
        ↓
Session Resolution
        ↓
Environment Initializer
        ↓
Load Project Configuration
        ↓
Load Instructions
        ↓
Load Policies
        ↓
Load Autonomy
        ↓
Load Capabilities
        ↓
Load Schemas
        ↓
Load Execution Locations
        ↓
Load Session Context
        ↓
Validate
        ↓
Construct Runtime Environment
        ↓
Core Agentic Runtime
```

No LLM should be required to perform these bootstrap operations.

---

# 57. Developer Capability Lifecycle

The conceptual lifecycle of a capability is:

```text
Developer Function
        ↓
SDK Registration
        ↓
Capability Metadata
        ↓
Validation
        ↓
Project Capability Set
        ↓
Session Environment
        ↓
ADK Tool
        ↓
Agent Selection
        ↓
ADK Invocation
        ↓
Deterministic Routing
        ↓
Client SDK / Server SDK
        ↓
Developer Function
        ↓
Result Validation
        ↓
ADK Tool Result
        ↓
Agent
```

This lifecycle applies to both client and server capabilities.

---

# 58. Capability Registration vs Capability Execution

These are intentionally separate concerns.

### Registration

Answers:

> What capabilities exist?

### Execution

Answers:

> Execute this already-selected capability in the correct location.

The registration system must not perform business execution.

The execution router must not discover capabilities through business logic.

---

# 59. SDK as the Developer Contract

The SDK is the main contract between the developer application and VoxCore.

The developer should not need to understand:

- internal ADK architecture
- internal agent topology
- internal orchestration logic
- internal session implementation
- internal routing implementation
- internal voice runtime
- internal persistence

The SDK abstracts those mechanisms.

---

# 60. Internal vs External Responsibility

The following principle applies:

```text
Developer Application
    owns application behavior

VoxCore SDK
    owns developer integration mechanics

VoxCore Deterministic Infrastructure
    owns reliable execution mechanics

VoxCore Agentic Runtime
    owns reasoning and orchestration

VoxCore Voice Runtime
    owns natural conversation
```

No layer should unnecessarily absorb another layer's responsibility.

---

# 61. Observability

Observability is a cross-cutting infrastructure responsibility.

The architecture should support tracing of:

- session
- user interaction
- agent execution
- plan
- capability invocation
- capability result
- retries
- failures
- latency
- voice/orchestration events

Observability must not require exposing sensitive business data beyond the configured boundaries.

Exact logging, metrics, and tracing technology remain LLD decisions.

---

# 62. Security Principles

VoxCore should follow these architectural security principles:

1. Every project is isolated.
2. Every session is explicitly associated with a project.
3. Client capability execution is bound to the correct session.
4. Server capability execution is bound to the correct project/developer backend.
5. Developer authentication is deterministic.
6. Capability authorization is deterministic.
7. Developer business data remains developer-owned.
8. VoxCore does not require copying the developer source codebase.
9. Raw secrets must not be exposed to the agent unnecessarily.
10. Agent reasoning must not bypass deterministic security controls.

---

# 63. No Business Logic in VoxCore

VoxCore must remain application-agnostic.

For example, VoxCore may know:

```text
verify_insurance
execution_location = server
```

but must not contain:

```python
if insurance_provider == "BlueCross":
    ...
```

That belongs to the developer application.

Similarly, VoxCore may know:

```text
highlight_missing_forms
execution_location = client
```

but the actual UI manipulation belongs to the developer frontend.

---

# 64. Latency Model

VoxCore is designed for asynchronous execution.

The user should not experience unnecessary dead air while backend operations execute.

The architecture therefore separates:

```text
conversation latency
```

from:

```text
business execution latency
```

The Voice Runtime can remain conversational while the Core Agentic Runtime performs longer-running work.

---

# 65. Long-Running Capability Execution

A capability may take significantly longer than the voice interaction's natural response time.

The architecture must support:

```text
Voice Runtime
       │
       │ progress / silent updates
       ▼
Core Agentic Runtime
       │
       │ long-running execution
       ▼
Developer Capability
```

The exact asynchronous execution contract is an LLD concern.

---

# 66. Failure Recovery Model

The general recovery model is:

```text
Capability Failure / Unexpected Result
            ↓
Deterministic Error Classification
            ↓
Structured Result Returned to Agent
            ↓
Agent Evaluates What Happened
            ↓
Use Current Context + Execution History
            ↓
Can Recover?
       ┌────┴────┐
      yes        no
       │          │
    replan     final failure
       │          │
    execute     voice response
       │
     CHECK
```

The agent is expected to learn from the current execution and avoid blindly repeating an approach that has already failed.

For example, if an invocation fails because the chosen parameters were invalid, the agent may use the structured failure and previous attempt information to correct the parameters or choose another capability.

This is **execution-time self-correction**, not persistent policy learning.

Deterministic infrastructure catches and classifies technical failures.

The agent decides what to do next when reasoning is required.

If the failure instead reveals that the project's business rules were incomplete or ambiguous, that observation may later be used by the developer in the sandbox to refine policy. It does not automatically mutate production policy.
---

# 67. Architectural Separation of Concerns

VoxCore follows this separation:

```text
                FLEXIBLE / INTELLIGENT
                         │
                         ▼
              Core Agentic Runtime
                         │
                         │
              structured decisions
                         │
                         ▼
                DETERMINISTIC
                         │
                         ▼
          Routing / Security / Validation
                         │
                         ▼
                 DEVELOPER SDK
                         │
                         ▼
              DEVELOPER APPLICATION
```

The more mechanically predictable an operation is, the lower it should sit in this stack.

---

# 68. What the Agent Must Never Be Responsible For

The agent must not be the authority for:

- authentication
- authorization
- API-key verification
- project resolution
- session ownership
- schema validation
- serialization
- transport protocol handling
- routing based on execution location
- duplicate prevention
- low-level retries
- tenant isolation

The agent can reason about the consequences of these operations, but deterministic infrastructure remains authoritative.

---

# 69. What the Developer Must Never Need to Implement

VoxCore should abstract away:

- voice streaming infrastructure
- conversational model connection management
- agent orchestration infrastructure
- client/server capability routing
- session lifecycle
- VoxCore transport protocol
- execution correlation
- deterministic validation
- low-level recovery mechanics

The developer should focus on the application and its capabilities.

---

# 70. What VoxCore Must Never Own

VoxCore should not become the owner of:

- developer business logic
- developer business databases
- developer UI
- developer external service implementations
- long-term end-user records
- application-specific workflows hidden inside platform code

VoxCore provides infrastructure and orchestration.

---

# 71. Architecture Invariants

The following are mandatory architectural invariants for V1.

### Invariant 1 — ADK

The core agentic runtime uses Google ADK.

### Invariant 2 — No Model Output Parsing

Tool calls are never discovered through natural-language response parsing.

### Invariant 3 — First-Class Tools

Developer capabilities are exposed to the agent as individual ADK tools.

### Invariant 4 — Deterministic Routing

Execution location is resolved deterministically.

### Invariant 5 — Developer Ownership

Actual business capability implementation remains inside the developer application.

### Invariant 6 — Generic Runtime

The agentic runtime contains no developer-specific business logic.

### Invariant 7 — Deterministic First

Mechanical operations are implemented using deterministic code.

### Invariant 8 — Client/Server Isolation

Client capabilities execute in the developer frontend.

Server capabilities execute in the developer backend.

### Invariant 9 — Project Isolation

Project configuration and capabilities cannot cross tenant boundaries.

### Invariant 10 — Temporary Session State

Active session state may be retained for recovery, but VoxCore does not become permanent end-user memory.

### Invariant 11 — Asynchronous Voice

Voice interaction remains decoupled from backend execution.

### Invariant 12 — Natural Error Handling

Raw technical errors are not directly exposed to the user through voice.

### Invariant 13 — Goal-Oriented Orchestration

The runtime follows:

```text
Perceive → Plan → Execute → Check
```

rather than simple trigger-to-tool routing.

### Invariant 14 — SDK as Primary Developer Interface

Client and Server SDKs are the primary developer integration mechanism.

### Invariant 15 — MCP Is Optional

MCP is not a required dependency for the core VoxCore developer-capability execution path.

### Invariant 16 — Runtime Self-Correction

The production agent may learn from the current session's context, previous actions, results, failures, and execution history. It may change its current plan or strategy to avoid repeating mistakes.

### Invariant 17 — No Autonomous Persistent Policy Mutation

Production execution must not automatically create, rewrite, or activate persistent project policies based on runtime mistakes or experience.

### Invariant 18 — Developer-Controlled Policy Refinement

Policy refinement is a developer-controlled configuration activity that may occur in sandbox or production. The developer or authorized business owner controls approval and activation; the production agent cannot autonomously persist policy changes.

### Invariant 19 — Policy Constrains, Agent Reasons

Policies express business rules, constraints, requirements, and operating expectations. They constrain the agent's decision space but do not replace agentic judgment.

### Invariant 20 — Recovery Is Not Policy Learning

Runtime recovery and replanning for the current task are separate from persistent policy refinement.

### Invariant 21 — Approved Configuration Boundary

Only developer-approved policy/configuration changes become part of the future runtime environment.
---

# 72. Open Architectural / LLD Decisions

The following are intentionally unresolved.

## 72.1 Exact ADK Tool Implementation

Determine whether the implementation should primarily use:

- custom `BaseTool`
- custom `BaseToolset`
- dynamically generated tools
- another native ADK tool abstraction

The architecture only requires that developer capabilities become first-class ADK tools.

---

## 72.2 Exact ADK Agent Topology

Determine whether the final implementation uses:

- one primary ADK agent
- multiple ADK agents
- workflow agents
- sub-agents
- specialized evaluator/recovery agents

The architecture does not require a specific internal topology.

---

## 72.3 Exact Voice Model/API

The project requires native V2V/multimodal conversation.

The exact Google/ADK model and API combination must be verified before implementation.

---

## 72.4 Client Transport

Determine the exact protocol used between:

```text
VoxCore ↔ Client SDK
```

The architecture requires a persistent/recoverable client communication mechanism but does not mandate a specific protocol in V1.

---

## 72.5 Server Transport

Determine the exact protocol used between:

```text
VoxCore ↔ Server SDK
```

The transport must support:

- authenticated invocation
- structured arguments
- structured results
- errors
- correlation
- appropriate lifecycle handling

---

## 72.6 Capability Registration Storage

Determine where capability metadata is stored and how it is retrieved.

---

## 72.7 Project Configuration Storage

Determine the persistence mechanism for:

- project configuration
- policies
- capabilities
- autonomy settings
- instructions

---

## 72.8 Active Session State

Determine:

- in-memory vs distributed state
- expiration
- reconnect window
- horizontal scaling
- session ownership
- recovery semantics

---

## 72.9 Retry Semantics

Define exact retry rules based on:

- idempotency
- operation type
- error category
- developer capability metadata

---

## 72.10 Policy Refinement / Assistance Architecture

Determine:

- whether sandbox policy assistance is performed by a dedicated ADK agent
- whether policy analysis is part of the sandbox runtime or a separate workflow
- what evidence from sandbox conversations is supplied to the assistance mechanism
- how proposed policies are represented
- how policies are validated
- how policies are versioned
- how developer review and approval work
- how approved policies become active for future runtime environments

The architectural requirement is already established:

```text
Sandbox observation
    ↓
optional agentic assistance / proposal
    ↓
developer review
    ↓
validation + versioning
    ↓
developer approval
    ↓
future runtime configuration
```

Automatic production activation of a policy generated from runtime experience is outside the V1 architecture. Developer-controlled activation of an explicitly reviewed policy change in production is supported by the architecture.
---

## 72.11 Live Policy Activation Semantics

Determine the exact semantics for live policy updates, including:

- whether new sessions immediately use the newly activated version
- whether active sessions are pinned to their starting policy version
- whether an active task may finish under its current version
- atomic activation semantics
- distributed consistency across runtime instances
- rollback behavior
- policy version visibility in execution traces

The architecture requires live developer-controlled policy evolution but intentionally leaves these lifecycle semantics to LLD.

---

## 72.12 Sandbox Architecture

Determine how sandbox execution is isolated from production projects and sessions while still using the same core runtime architecture.

---

## 72.13 Observability

Determine the exact tracing, logging, metrics, and debugging architecture.

---

# 73. Implementation Direction

The future implementation should derive directly from this architecture.

The recommended implementation sequence is:

```text
Architecture V1
      ↓
LLD
      ↓
Core Contracts
      ↓
SDK Contracts
      ↓
ADK Tool Integration
      ↓
Deterministic Execution Router
      ↓
Client Execution
      ↓
Server Execution
      ↓
Session Infrastructure
      ↓
Voice Runtime
      ↓
Sandbox / Policy Refinement
      ↓
Production Hardening
```

The prototype should implement a representative vertical slice rather than creating a separate simplified architecture.

---

# 74. Representative Prototype Vertical Slice

A prototype can demonstrate the architecture through a scenario containing:

1. Developer project initialization
2. Client SDK connection
3. Server SDK connection
4. Project environment construction
5. Native voice interaction
6. Agent reasoning
7. Multi-step planning
8. Client capability invocation
9. Server capability invocation
10. Deterministic routing
11. Tool result propagation
12. Goal completion checking
13. Natural voice response
14. One failure/recovery path
15. Session reconnection or recovery

The prototype does not need to implement every production feature, but the implemented features should fit the V1 architecture.

---

# 75. Example End-to-End Scenario

Consider a developer application with:

```text
Server:
    verify_insurance()
    check_doctor_availability()
    book_appointment()

Client:
    highlight_missing_forms()
```

A user says:

> “Update my insurance, show me which forms I still need, and book the earliest available appointment.”

The architecture handles this as follows.

## Step 1 — Session

```text
User
 ↓
Developer Application
 ↓
Client SDK
 ↓
VoxCore
```

The session is authenticated and associated with the developer project.

---

## Step 2 — Environment

The Environment Initializer loads:

```text
instructions
policies
autonomy
verify_insurance
check_doctor_availability
book_appointment
highlight_missing_forms
```

along with schemas and execution locations.

---

## Step 3 — Perceive

The agent determines that the user has requested multiple related outcomes.

---

## Step 4 — Plan

The agent generates an appropriate plan.

For example:

```text
verify insurance
       ↓
check availability
       ↓
book appointment

highlight missing forms
```

The exact plan depends on the registered capability descriptions and policies.

---

## Step 5 — Execute

The agent invokes:

```text
verify_insurance()
```

ADK invokes the corresponding tool.

The deterministic router identifies:

```text
location = server
```

and routes it to the Server SDK.

---

## Step 6 — Client Execution

The agent invokes:

```text
highlight_missing_forms()
```

ADK invokes the client capability.

The deterministic router identifies:

```text
location = client
session = current session
```

and sends the invocation through the Client SDK.

The browser executes the actual UI function.

---

## Step 7 — Continue Planning

The agent receives the results and determines whether it can proceed.

It may invoke:

```text
check_doctor_availability()
```

and then:

```text
book_appointment()
```

---

## Step 8 — Failure

Suppose the booking API returns a temporary server failure.

Deterministic infrastructure:

```text
detects error
classifies error
returns structured failure
```

The agent receives the failure and determines whether another strategy is appropriate.

The voice layer receives a silent/system-level status update rather than raw technical details.

---

## Step 9 — Check

The agent evaluates whether all requested outcomes have been completed.

Only when the required goal is satisfied does it produce the final conversational response.

---

# 76. Architectural Summary

VoxCore V1 can be reduced to five primary components:

```text
┌───────────────────────────────────────────────────────┐
│                    VOXCORE SDK                        │
│                                                       │
│   Client SDK                    Server SDK            │
│   JS / Python                   JS / Python           │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│              ENVIRONMENT INITIALIZER                  │
│                                                       │
│  Project config / policies / capabilities / context  │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│              CORE AGENTIC RUNTIME                     │
│                                                       │
│                   Google ADK                          │
│                                                       │
│        PERCEIVE → PLAN → EXECUTE → CHECK             │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│            DETERMINISTIC INFRASTRUCTURE               │
│                                                       │
│  Security / Validation / Session / Routing /         │
│  Transport / Errors / Retry / Correlation / Isolation│
└───────────────────────┬───────────────────────────────┘
                        │
               ┌────────┴────────┐
               ▼                 ▼
          Client SDK         Server SDK
               │                 │
               ▼                 ▼
          Frontend            Backend
```

Alongside the agentic runtime:

```text
┌───────────────────────────────────────────────────────┐
│                VOICE AGENT RUNTIME                    │
│                                                       │
│  Native V2V / conversation / pacing / latency         │
│  masking / natural error and progress communication  │
└───────────────────────────────────────────────────────┘
```

---

# 77. Final Architectural Principle

The central architectural idea of VoxCore V1 is:

```text
                     USER INTENT
                          │
                          ▼
                  VOICE AGENT RUNTIME
                          │
                          ▼
                  CORE AGENTIC RUNTIME
                          │
                     Google ADK
                          │
                   structured tool call
                          │
                          ▼
               DETERMINISTIC ROUTER
                          │
                 ┌────────┴────────┐
                 │                 │
              CLIENT             SERVER
                 │                 │
                 ▼                 ▼
            Client SDK         Server SDK
                 │                 │
                 ▼                 ▼
            Developer          Developer
            Frontend           Backend
```

The responsibility boundary is therefore:

> **The agent decides what should happen within the approved business constraints.  
> The agent may learn from current execution outcomes and change its plan when necessary.  
> Deterministic infrastructure decides how and where a selected capability executes.  
> The SDK executes the developer-side capability.  
> The developer application owns the actual business logic.  
> The developer controls persistent policy refinement through the sandbox.  
> The voice runtime makes the entire process conversational and natural.**

The foundational behavioral distinction is:

> **Runtime experience changes the agent's current strategy; developer-approved policy changes the agent's future operating constraints.**

This is the foundational architecture of VoxCore V1.

---

# 78. V1 Architectural Decision Record

### Decision

Use Google ADK as the core agentic framework and expose developer capabilities as individual ADK tools.

### Decision

Do not parse model responses to discover tool calls.

### Decision

Use a deterministic execution router to resolve capability destination.

### Decision

Support two execution locations:

```text
client
server
```

### Decision

Use Client SDK and Server SDK as the primary developer-side execution interfaces.

### Decision

Keep actual capability implementations inside the developer application.

### Decision

Keep deterministic infrastructure separate from agentic reasoning.

### Decision

Keep the Voice Agent Runtime asynchronous and separate from business orchestration.

### Decision

Do not make MCP a mandatory internal execution layer.

### Decision

Keep MCP available as a possible future interoperability mechanism rather than a core architectural dependency.

### Decision

Maintain strict project and session isolation.

### Decision

Do not make VoxCore the permanent owner of end-user memory or business data.

### Decision

Allow the production agent to learn from execution outcomes through current context, session history, tool results, failures, and replanning.

### Decision

Treat runtime self-correction as task/session-level adaptation rather than persistent policy modification.

### Decision

Treat policies as developer-defined business rules, constraints, requirements, and operating expectations that guide agentic decisions.

### Decision

Keep policy refinement developer-controlled, while allowing it in both sandbox and live production projects.

### Decision

Allow agentic assistance to propose policy refinements where appropriate, but require developer review, deterministic validation, versioning, and controlled activation before a change becomes active runtime configuration.

### Decision

Do not allow production runtime experience to autonomously mutate or activate persistent project policies. Developer-controlled policy updates may be activated while the project is live in production.
---

# 79. V1 Status

The following is considered **pseudofrozen for Version 1**:

```text
Five primary components
        ↓
VoxCore SDK
Environment Initializer
Core Agentic Runtime
Deterministic Infrastructure
Voice Agent Runtime
```

The following is also pseudofrozen:

```text
Google ADK
        ↓
individual ADK capabilities/tools
        ↓
deterministic execution routing
        ↓
Client SDK / Server SDK
        ↓
Developer Application
```

The following behavior boundary is also pseudofrozen:

```text
Production Runtime
    ↓
agent learns from current execution context/history
    ↓
agent replans and recovers when appropriate
    ↓
no autonomous persistent policy mutation

Developer Policy Lifecycle
    ├── Sandbox
    │     ↓
    │  observe / test / refine / validate
    │
    └── Production
          ↓
       observe business change
          ↓
       modify / validate / version
          ↓
       developer-controlled activation

Both paths update persistent policy only through the developer-controlled configuration lifecycle.
```

The following remains open until LLD:

```text
Exact ADK tool implementation
Exact ADK agent topology
Exact voice model/API
Client transport
Server transport
Session persistence
Capability registry implementation
Project configuration persistence
Retry/idempotency mechanism
Policy generation implementation
Sandbox implementation
Observability implementation
Deployment topology
```

Any LLD decision that conflicts with a V1 architectural invariant must either:

1. be redesigned to preserve the invariant, or
2. explicitly trigger an architecture review and revision of this document.

---

# 80. End State

The intended end state of VoxCore is a generic infrastructure platform where a developer can integrate their existing application through the SDK and provide:

```text
Project Configuration
+
Instructions
+
Policies
+
Capabilities
+
Context
```

while VoxCore provides:

```text
Voice
+
Reasoning
+
Planning
+
Orchestration
+
Capability Routing
+
Session Infrastructure
+
Deterministic Reliability
+
Conversational Execution
```

without taking ownership of the developer's:

```text
Business Logic
Business Data
Frontend
Backend
Persistent User Data
```

The intended behavioral model is equally important:

```text
Production Agent
    ↓
uses approved business policies
    ↓
reasons freely within those constraints
    ↓
learns from current execution outcomes
    ↓
avoids repeating mistakes
    ↓
replans / recovers when possible
    ↓
does not automatically rewrite persistent policy

Developer Policy Lifecycle
    ├── Sandbox → observes, tests, refines, validates
    └── Production → observes live business changes, refines, validates, activates
                         ↓
                  applicable runtime environments use the approved configuration
```

The architecture is intentionally designed so that the **agentic layer is flexible, adaptive, and capable of self-correction**, while the **business-policy layer remains explicit, versioned, and developer-controlled throughout the project lifecycle**. Policies may evolve while the project is live in production, but the production agent cannot autonomously persist or activate policy changes. The infrastructure surrounding both remains deterministic, isolated, and reliable.