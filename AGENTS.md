# VoxCore Project Rules & Grounding

## 1. Open-Ended Deep Documentation Grounding
You are implementing the highly complex VoxCore architecture. You are strictly forbidden from guessing Python, Node.js, FastAPI, Google ADK syntax, or any other framwork/library we will be using in our this project and you must not rely on outdated legacy paradigms.

Before generating any code or implementation plans, you MUST perform Deep Research:
1. **Search:** Use the `search` tool via the DuckDuckGo MCP to find the official, latest documentation and advanced guides for the specific framework you are about to implement.
2. **Read the Docs:** Use the `fetch_content` tool to scrape and read the actual documentation pages, focusing on advanced features, complex capabilities, and best practices.
3. **Analyze Capabilities:** Discover which specific features of the framework (e.g., advanced async patterns, unique routing paradigms, or specific Google ADK workflow configurations) will best serve VoxCore's complex requirements.
4. **Output the Strategy:** Before writing code, output a structured summary detailing the specific, verified syntax you found and the advanced framework capabilities you intend to utilize to achieve the project's true potential.

Do not artificially limit your search. Explore the documentation fully. Any implementation attempted without this deep MCP research phase will be rejected.

## 2. Project Architecture & Constraints
You must strictly adhere to the rules, constraints, and methodologies defined in the following project documents. Do not deviate from these guidelines:

* **Project Overview:** @docs/01_voxcore_project_overview.md
* **User Journey:** @docs/02_voxcore_user_journey.md
* **Hard Constraints (MUST READ):** @[VoxCore Constraints](./docs/03_voxcore_architecture_constraints.md)
* **Architectural HLD:** @docs/04_HLD_voxcore_architectural_design.md
* **Development Methodology:** @docs/05_Progressive_vertical_slice_Development_with_incremental_LLD.md
* **Git Strategy:** @docs/06_voxcore_development_workflow_and_git_strategy.md