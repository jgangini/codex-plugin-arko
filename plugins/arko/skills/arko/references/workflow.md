# Workflow

`CLI` means `python /absolute/plugin/skills/arko/scripts/arko.py` (Python 3.12+).
Use `CLI --help` for authoritative arguments. Commands do not change the current
application implicitly: always pass `--root /absolute/app`.

- `CLI init /absolute/app [--frontend]`: create an empty base. Refuses nonempty
  directories. No packages installed, Git hooks enabled or global settings changed.
  Records the initial baseline in `contracts/acceptance.json`.
- `CLI add-feature NAME --root APP`: add backend API/service/schema/tests and, when
  present, a React consumer/component/test. Update `backend/app/main.py` to mount
  the generated router and the composition root to display a component as needed.
  When an operation is ready to publish, add it to `features.NAME.public_routes`
  in `.arko/project.json` as `METHOD /path`, such as `GET /api/notes/{item_id}`.
  Use uppercase methods and FastAPI's path parameter names. These declarations
  protect routes before the first contract approval.
  New models use the exact feature identifier in their OpenAPI component names.
  The feature-local Python aliases remain `CreateItem` and `Item`.
  No automatic route discovery or imposed navigation.
- `CLI frontend --root APP`: add React later, including consumers for registered
  features. Existing files cause an error before writes.
- `CLI context NAME --root APP`: current file hashes, symbols, direct dependencies,
  declared transitive dependencies and reverse consumers, shared paths, task state,
  and stale maps. Python files under `backend/tests` keep their static imports and
  symbols even when they use dynamic imports. When present, `dynamic_import_lines`
  lists the source lines to review. Dynamic imports in application code still
  fail the boundary audit. Follow source evidence beyond this starting set.
- `CLI map --root APP`: explicitly refresh registered feature file lists after
  reviewing additions/removals. Never executed by verification.
- `CLI setup --root APP`: `uv sync --locked`, and `npm ci --ignore-scripts` when
  frontend exists. Requires the user's task to authorize dependencies/network.
- `CLI contract --root APP`: export current OpenAPI from trusted application code;
  generate frontend types through installed openapi-typescript. Does not accept.
- `CLI accept-contract --root APP --reason TEXT`: explicitly accept current OpenAPI
  after reviewing changes. Records the reason, timestamp and SHA-256 of the
  accepted bytes in `contracts/acceptance.json`.
- `CLI check --root APP`: one fail-fast route for maps, boundaries, contracts,
  Python lint/types/tests, frontend types/tests/build and generated-type drift.
  Requires the latest approval hash to match `contracts/baseline.json`. For a
  project without an approval record, review the current export and use
  `accept-contract` to record approval. The local log verifies consistency
  between files. Store reviewed changes to both files together in source control.
- `CLI dev --root APP`: local backend (8000) and optional frontend (5173), loopback
  only; first child exit stops the other; Ctrl+C stops both. Setup first. Restart
  after backend edits; reloader subprocess supervision is not implemented in v0.1.
- `CLI docker --root APP [--tag NAME]`: build chosen profile with Docker; no push.
- `CLI upgrade --root APP`: print candidate unified diffs and customization status
  against this installed standard. Does not write or apply anything.
  Merge the vendored template for future features and preserve the model names
  and contract assets already approved for existing features.

Fresh app: setup, run baseline check, add features, mount explicitly, export
contract, inspect diff, accept intentionally, check again. Backend-only needs no
Node. Keep uv.lock and frontend/package-lock.json committed. `docs/tasks/current.md`
is a handoff, not evidence that checks remain valid after changes.

`check`, `contract` and `accept-contract` verify exported and declared operations
against `app.main:app`. `check` also verifies operations in the approved baseline
for existing applications, including manifests without `public_routes`.
For a deliberate retirement, update the application and any declaration, export
the candidate, review the change, then accept it explicitly. This covers schema-visible FastAPI
operations in the main app, including routers included with `include_router`.
HTTP behavior, route precedence and separately mounted apps need their own tests.
