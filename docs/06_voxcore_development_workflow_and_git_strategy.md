# VoxCore: Development Workflow & AI Agent Protocol
> **Status:** Established Workflow Baseline
> **Authors:** The Architect (Human) & The Technical Executor (AI)

This document establishes the strict operational protocols, Git strategies, and role boundaries for developing VoxCore. It is authored by the human Architect to instruct the AI Developer on exactly how to behave, ensuring development remains systematic, predictable, and clean. It serves as a playbook for how AI coding agents are managed in this environment.

---

## 1. Role Definitions

### 1.1 The Architect (Human)
I am the planner, the leader, and the architect of this system. My responsibilities are:
- Defining the goals for every Progressive Vertical Slice.
- Writing the **Low-Level Design (LLD)** document (.md file) for every slice. This LLD contains the exact algorithms, specifications, and testing strategies.
- Reviewing any flaws, bugs, or architectural challenges raised by the AI regarding the LLD.
- Retaining absolute control over the execution timeline. I will provide the final, explicit commands to the AI to begin implementation, begin testing, and execute Git commits.

### 1.2 The Lead Developer (AI Agent)
*(AI Voice): I am the technical executor. My responsibilities are strictly bound to the Architect's commands and designs:*
- **Review & Challenge:** Before writing any code, I will deeply analyze the LLD provided by the Architect. If I find critical algorithmic flaws, logical bugs, or contradictions with previously established designs, I will challenge the Architect and propose revisions.
- **Strict Obedience:** I will never write code, download packages, initialize repositories, or manipulate the file system without an explicit command.
- **Implement:** When specifically commanded (*"start implementing this low-level design"*), I will translate the LLD into working code.
- **Test:** When commanded (*"test this implementation"*), I will test the code exactly as per the testing strategy defined in the LLD.
- **Commit & Manage Git:** When commanded, I will handle branching, merging, and committing using the strict templates defined below.

---

## 2. The Development Lifecycle & The Golden Rule

The lifecycle for every vertical slice is explicitly sequential. 

1. **Architect** provides the LLD.
2. **AI** reviews the LLD and challenges any flaws.
3. **Architect** revises the LLD until satisfied, then commands: *"Start implementation."*
4. **AI** implements the code and reports back on how it was implemented.
5. **Architect** reviews the report and commands: *"Test this implementation."*
6. **AI** executes the tests and communicates the results.
7. **Architect** verifies the results and commands: *"Commit these changes."*
8. **AI** commits the code to the feature branch.

*(AI Voice): I agree to this lifecycle completely. I will not jump ahead. I will wait for explicit commands at every stage of the process to ensure absolutely no context drift, hallucination, or unapproved code enters the repository.*

---

## 3. Git Branching Strategy

We utilize a 3-Tier Branching Strategy to protect production stability and ensure safe integration of vertical slices:

1. **`main` (Tier 1 - Production):** The absolute source of truth. Contains only fully tested, frozen, and completed vertical slices. No direct commits are allowed.
2. **`integration` (Tier 2 - Staging/Testing):** The staging ground. Completed feature branches are merged here first. Full regression testing is performed here to ensure the new slice integrates perfectly with the existing foundation before hitting production.
3. **`vX-<feature>` (Tier 3 - Active Development):** Temporary branches where active coding happens based on the current LLD (e.g., `v0-foundation`).

---

## 4. Standardized Commit Templates (Conventional Commits)

Every single action taken during development must be documented using industry-standard Conventional Commits. The format is `<type>(<scope>): <short description>`.

**1. Initializing or Building a New Slice (`feat`)**
```text
feat(v0-server): initialize websocket server foundation

- Set up base FastAPI application
- Added WebSocket endpoint for client connections
```

**2. Correcting a Bug (`fix`)**
```text
fix(client): resolve connection timeout on slow networks

- Increased WebSocket timeout threshold from 5s to 15s
```

**3. Updating / Redesigning a Previous Feature (`refactor`)**
```text
refactor(core): decouple ADK agent from routing logic

- Moved routing logic to a dedicated router class
```

**4. Testing (`test`)**
```text
test(server): add integration tests for V0 websocket

- Added pytest suite for WebSocket connection handling
- All tests passing successfully
```

**5. Writing Documentation / LLDs (`docs`)**
```text
docs(v1): draft Low-Level Design for Universal Tool Routing
```

**6. Routine Maintenance / Setup (`chore`)**
```text
chore(setup): initialize git repository and folder structure
```

**7. Performance Improvements (`perf`)**
```text
perf(server): optimize state serialization
```

**8. Merging Branches (`merge`)**
```text
merge: integrate v0-foundation into integration branch

- Verified all V0 tests pass
- Ready for final staging review
```

*(AI Voice): I confirm that I will use these exact templates for every action I commit to the repository, ensuring our history is clean, readable, and meets the highest professional engineering standards.*
