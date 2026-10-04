# VoxCore Security Model & Authentication Architecture

**Document:** `08_voxcore_security_model.md`  
**Status:** Living Document  
**Authority:** Defines the security boundaries, authentication strategies, and threat mitigation models for the VoxCore framework.

---

## 1. The Core Philosophy

VoxCore is an orchestration engine that deeply integrates with a developer's infrastructure to execute code autonomously. Because of this power, **security cannot be an afterthought; it is the foundational constraint.** 

VoxCore's security model is built on three unbreakable principles:
1. **The Dual-Key Architecture:** Absolute separation of client and server privileges.
2. **Execution Boundary Integrity:** The frontend browser can never directly invoke backend tools.
3. **Orthogonal Application Security:** VoxCore secures the *Agentic Voice Layer*; it does not replace or bypass the developer's standard web security (e.g., JWTs, Cookies).

---

## 2. The Dual-Key Architecture (The "Stripe" Model)

Exposing a single, powerful API key in a frontend environment is a critical vulnerability. To mitigate this, VoxCore utilizes a Dual-Key Architecture, mirroring industry gold standards.

### 2.1 The Secret Key (`sk_...`)
*   **Location:** Resides exclusively on the developer's backend server (e.g., in secure environment variables). It is **never** sent to the browser.
*   **Purpose:** Authenticates the `VoxCoreServer` SDK to the VoxCore Orchestrator.
*   **Privileges:** Complete authority. It has full permissions to manage project settings, register Server Tools, and receive server-side tool execution triggers from the Orchestrator.

### 2.2 The Publishable Key (`pk_...`)
*   **Location:** Safe to be hardcoded in frontend JavaScript/PyScript and exposed to the public internet.
*   **Purpose:** Authenticates the `VoxCoreClient` SDK to establish a WebSocket session for a specific user.
*   **Privileges:** Severely restricted. It can only stream audio data and receive Client Tool execution triggers for that specific, sandboxed session. It cannot access project configurations, nor can it inspect or invoke Server Tools.

---

## 3. Execution Boundaries & Tool Triggers

A common security concern in agentic frameworks is that exposing an API key in the frontend might allow a malicious user to hijack the tool execution loop and manipulate backend state. VoxCore's architecture mathematically prevents this.

### The Threat Vector
*What if a malicious user manipulates the Client SDK to trigger a `cancel_appointment` tool?*

### The VoxCore Mitigation
The frontend SDK **never** sends tool execution commands to the backend. The execution loop is strictly top-down from the Orchestrator:
1. The user speaks into the microphone.
2. The **VoxCore Orchestrator** (the brain) decides which tool to call based on the environment state.
3. If the Orchestrator selects a **Server Tool**, it routes the execution command directly to the developer's backend via the secure WebSocket authenticated by the Secret Key. The browser is completely bypassed and completely unaware of the event.
4. If the Orchestrator selects a **Client Tool**, it routes the command to the browser. If an attacker intercepts this, they can only trigger UI changes on their own screen. 

A compromised Publishable Key cannot bleed into backend state manipulation because the routing is physically isolated by the Orchestrator.

---

## 4. State Isolation & Orthogonal App Security

VoxCore must be viewed as an independent layer sitting alongside standard application infrastructure. 

*   **VoxCore Security** secures the pipeline between the User's Microphone, the Orchestrator, and the Developer's SDK.
*   **Developer App Security** (JWTs, OAuth, Session Cookies, CSRF tokens) secures the pipeline between the User's Browser and the Developer's HTTP endpoints.

VoxCore does not bypass standard application security. If a developer has an HTTP `DELETE /api/appointments/123` route, it remains secured by their standard authentication middleware. VoxCore simply provides an alternative, autonomous agentic route that is authenticated by the VoxCore Secret Key.

---

## 5. Living Model

As VoxCore evolves, this document will be updated to address advanced security topologies, including:
*   Multi-tenant data isolation within the Orchestrator.
*   Rate limiting and abuse prevention on the voice streaming endpoints.
*   Developer sandbox boundaries.

*Any architectural decision that compromises the boundaries defined in this document must be immediately rejected.*
