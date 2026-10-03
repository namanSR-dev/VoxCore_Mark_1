# VoxCore (Mark 1)

> **Status:** Architecture & design phase  
> **Implementation:** In progress  
> **Documentation:** Architecture baseline frozen  

**Voice AI can talk. But making it reliably *do* things inside somebody else's application is a very different problem.**

What happens when you give an AI control over real application infrastructure? Natural-language intelligence is powerful—but infrastructure cannot afford to behave like a probabilistic guessing machine.

VoxCore is an open-source orchestration infrastructure designed to solve this exact systems engineering problem. 

**VoxCore ≠ chatbot application.**  
**VoxCore = orchestration infrastructure.**

It provides the bridge between real-time conversational AI (powered by Google ADK and native Voice-to-Voice models) and your application's actual business logic.

---

## What does this actually enable?

If VoxCore succeeds, what can a developer build that is difficult today?

By safely connecting AI reasoning to your specific frontend and backend capabilities, VoxCore enables:

- **Complex Application Control:** *"Update my insurance to BlueCross, show me the forms I need to sign on my screen, and book the earliest slot."*
- **Voice-Enabled SaaS Workflows:** *"Pull up the Q3 revenue report, filter for enterprise clients, and export it to my dashboard."*
- **Autonomous Support Operations:** *"Check the database for the user's shipping status, verbally explain the delay, and trigger a frontend notification with a tracking link."*

---

## What makes VoxCore different?

If you want to understand the engineering behind VoxCore, you have to look at its boundaries. Here are the four architectural decisions the entire system is built around.

### 01 — AI where reasoning belongs. Deterministic infrastructure where reliability matters.
An AI can decide that a user's password needs to be reset. But the AI should not be writing the SQL query or handling the HTTP 500 error if the database times out.

In VoxCore, the model reasons. The infrastructure does not guess. All operational logic, routing, transport, authentication, and error handling are strictly managed by deterministic Python code. 

→ [Explore the Architectural Constraints](docs/03_voxcore_architecture_constraints.md)

### 02 — One capability model across client + server
An AI can decide it needs to `highlight_missing_forms`. But that function doesn't live inside VoxCore's backend. It lives inside the developer's frontend browser. 

So how does a backend orchestration engine safely execute a function inside someone else's frontend? 

The model chooses the capability. VoxCore chooses where it runs.

```text
                 ADK Tool
                    │
                    ▼
          Deterministic Router
             /           \
            /             \
       CLIENT            SERVER
          │                 │
     Client SDK        Server SDK
          │                 │
     Developer         Developer
      Frontend           Backend
```

→ [See the Federated Tool Boundary in the HLD](docs/04_HLD_voxcore_architectural_design.md)

### 03 — Perceive → Plan → Execute → Check
VoxCore is not a simplistic `user request → tool → result` router. Real-world tasks require multi-step orchestration.

```text
User request
     ↓
  PERCEIVE
     ↓
    PLAN
     ↓
  EXECUTE
     ↓
   CHECK
     ↓
 Complete?
 ↙       ↘
Yes       No
 ↓         ↓
Respond   Replan
```

→ [Discover how the orchestration loop works](docs/04_HLD_voxcore_architectural_design.md)

### 04 — Runtime adaptation without uncontrolled policy mutation
What happens when the agent makes a mistake—and who is allowed to turn that mistake into a permanent rule?

VoxCore makes a deliberate distinction between:
- **Runtime self-correction:** *"What should I do differently right now to fix this failed API call?"* (Agentic behavior)
- **Policy refinement:** *"What business rule or constraint should I understand differently forever?"* (Developer-controlled configuration)

→ [Read the complete User Journey to see this in action](docs/02_voxcore_user_journey.md)

---

## How this is being built

**VoxCore is currently being built from a frozen architectural baseline.**

How can a single developer realistically build an infrastructure layer this complex? By not building massive, untested horizontal layers. 

VoxCore relies on **Progressive Vertical-Slice Development**. The architecture is being built incrementally, and each version must be verified before becoming the foundation for the next.

```text
Architecture Baseline
        │
        ▼
     V0 🚧 (Upcoming)
        │
        ▼
     V1
        │
        ▼
     V2
        │
        ▼
        .
        .
        .
        ▼
   VoxCore
```

Every version requires strict testing, verification, and a completion gate to prove that the architecture works before moving forward.

→ [Examine the Progressive Development Methodology](docs/05_Progressive_vertical_slice_Development_with_incremental_LLD.md)

---

## Inside VoxCore: The Learning Path

If you want to disappear into the engineering and understand how this system actually works, follow the trail. 

*Understand the story → understand the constraints → dive into architecture.*

| Document | Question it answers |
|---|---|
| [Project Overview](docs/01_voxcore_project_overview.md) | **What is VoxCore trying to accomplish?** |
| [User Journey](docs/02_voxcore_user_journey.md) | **What does using VoxCore actually feel like?** |
| [Constraints](docs/03_voxcore_architecture_constraints.md) | **What rules must the architecture obey?** |
| [HLD](docs/04_HLD_voxcore_architectural_design.md) | **How does the system actually work?** |
| [Progressive Development](docs/05_Progressive_vertical_slice_Development_with_incremental_LLD.md) | **How will such a large system be built safely?** |
| [Development Workflow](docs/06_voxcore_development_workflow_and_git_strategy.md) | **How is the AI engineering process controlled?** |
