# VoxCore: Architectural Constraints & Requirements

This document serves as the absolute baseline for the new VoxCore architecture. It does not dictate *how* the system will be built, but strictly defines the *constraints and rules* that the final design must adhere to.

---

## 1. Framework & Core Engine Constraints
*   **Must Use Google ADK:** The backend orchestration layer must be built exclusively using Google ADK (Agent Development Kit). Frameworks like LangGraph or LangChain are strictly prohibited to maintain simpler syntax, better default interfaces, and seamless translation from design to code.
*   **Native V2V / Multi-Modal Engine:** The conversational frontend must utilize a native Speech-to-Speech (Omni) model (e.g., Gemini Multimodal Live API via the free tier, or open-weights like Llama-Omni). Traditional cascaded pipelines (ASR -> LLM -> TTS) are deprecated.

## 2. The "Deterministic First" Rule
*   **Strict Agent Limitations:** LLMs and Agents are highly flexible but prone to hallucination and latency. They must *only* be used for natural conversation, complex reasoning, and dynamic planning.
*   **Code over AI:** Any task that can be executed using deterministic programming (e.g., validating JSON schemas, catching HTTP 500 errors, dispatching a payload to a Webhook) **MUST** be written in pure deterministic code (Python). We will not use agents blindly for tasks that a simple Python script can do faster and without error. This ensures the infrastructure remains robust and unbreakable.

## 3. Asynchronous Conversational Engagement
*   **Decoupled Voice Layer:** The conversational agent (Gemini Live) must run completely asynchronously from the backend orchestration layer.
*   **Latency Masking (Silent Injection):** The backend must communicate with the conversational agent via silent system updates. If a background tool takes 10 seconds, the conversational agent must stall naturally (e.g., *"Just give me a second while I pull that up..."*) to ensure the user never experiences dead air.
*   **Graceful Error Reporting:** Technical errors (e.g., JSON failures, API timeouts) must never be spoken to the user. The conversational agent must mask these with natural human tactics (e.g., *"The system is taking a bit longer than usual"*, or for fatal errors, *"I'm sorry, that system seems to be down right now"*).

## 4. The Orchestration Loop
*   **Perceive -> Plan -> Execute -> Check:** The ADK backend cannot be a simple "trigger tool" router. It must perceive the user's ultimate goal, generate a multi-step execution plan, run tools (in parallel when independent, sequentially when dependent), and evaluate if the goal was achieved before responding.
*   **Universal Black-Box Design:** The orchestrator must not contain any hardcoded logic specific to a developer's application. It must dynamically read the developer's registered tools and prompts at runtime and act as a generic engine processing that fuel.
*   **Federated Tool Boundary (Client vs. Server):** The orchestration engine must natively understand where a tool exists. It must reliably route execution signals to the user's frontend (Client UI Control / Reverse MCP) or to the developer's backend (Server Webhooks) without crossing or executing logic in the wrong environment.
*   **Configurable Autonomy (Guardrails):** The orchestrator must enforce strict boundaries based on developer configuration. If an agent is assigned a narrow, specific task, the engine must prevent the agent from planning orchestrations outside that constrained scope.

## 5. Adaptability & Self-Correction
*   **Policy Generation:** If the system fails due to an agent's poor reasoning (e.g., passing a wrong parameter type), it must reflect on the failure, understand what went wrong, and generate a dynamic "Policy" (rule) to ensure it never makes that mistake again.
*   **Developer Sandbox:** The architecture must support a training window where developers can simulate conversations, review the agent's orchestration plans, and provide manual feedback to generate highly robust policies *before* the agent is deployed to real users.

## 6. Multi-Tenancy & Privacy
*   **Strict Isolation:** Developer projects must be entirely isolated. Tools and personas must be bound dynamically per WebSocket session based on the developer's API key.
*   **Robust Stateless Memory:** To protect privacy, the agent must completely forget the user when a session truly ends. However, the architecture must retain active session state securely to seamlessly handle temporary network drops or slow internet without disrupting the user's flow.
*   **Data Egress & Ingress (Transcript Management):** Because VoxCore does not hoard chat histories, the architecture must expose egress APIs/channels to stream conversation transcripts *back* to the developer's infrastructure for them to store. It must also expose ingress APIs allowing developers to inject prior user context the moment a session boots.

## 7. Codebase Boundaries & Dependency Isolation
*   **Three Permanent Pillars:** The repository houses three strictly independent projects: `developer_app/` (the client's custom application logic), `sdk/` (the installed external package connecting the app to VoxCore), and `core/` (the runtime orchestration service).
*   **Zero Source-Code Coupling:** These three codebases must never share common source directories, and no codebase may import files from another via relative internal paths.
*   **Strict Dependency Isolation:** All dependencies across these three codebases are strictly isolated.<br>
*for example :-* Even if `sdk` and `developer_app` require the exact same third-party package, they must each install it independently in their own dedicated virtual environments. There is no shared root dependency configuration.
*   **SDK Installation Model:** The `developer_app` must consume the `sdk` strictly as an installed external package boundary, mimicking how an external developer uses a production SDK.
*   **Network Isolation:** To prevent monolith bleed during local development, `developer_app` and `core` must communicate exclusively via runtime network protocols (HTTP/WebSocket) over separate processes, exactly as they would in production. Localhost is a deployment location, not a bypass mechanism.
