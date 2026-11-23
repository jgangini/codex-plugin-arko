---
name: arko
description: Use Arko to scaffold and maintain FastAPI applications with optional React, locate and verify features, or guide native Rust desktop application design, implementation and validation with Cargo.
---

Choose the workflow from the requested application and the project's own stack.
For native Rust desktop applications, read [the Rust desktop guide](references/rust-desktop.md).
Use the project's Cargo toolchain and tests for that workflow. For FastAPI
applications, use the workflow below.

## FastAPI applications

Use the packaged CLI at `scripts/arko.py` relative to this skill. Resolve its
absolute path from this file; commands below are Python scripts, not native Codex
commands. Read [the workflow](references/workflow.md) for command details.
Read [research and tradeoffs](references/research.md) when reconsidering the profile.

In an existing application read its AGENTS.md, `.arko/project.json`, relevant ADRs
and `docs/tasks/current.md`. The repository's requirements and current code govern
the task. Get feature context with the CLI, then inspect callers and tests. The
map is a starting point: expand exploration when imports, shared state, runtime
dispatch or uncertainty suggest other dependencies. Never impose a file/token cap.

Keep the common standard separate from the selected technical profile. Do not add
a framework, design system, screen, database or LLM provider without a task need.
Complement existing design tools, Semble and Graphify; do not reindex their corpora.

Run the relevant baseline before changes. After edits, update feature maps and
task state, export OpenAPI and generate TS types when needed, then run `check`.
Never repair a failed compatibility check by silently accepting a new baseline.
Explain intentional breaking changes and review the contract diff first.

Record sources, verification date, pending work and actual checks in repository
artifacts. Summarize limitations: static discovery is not complete runtime analysis;
the starter token and in-memory example are not production identity or storage.
Report unavailable checks explicitly. Updating the standard generates a proposal;
review and apply it without overwriting custom files.
