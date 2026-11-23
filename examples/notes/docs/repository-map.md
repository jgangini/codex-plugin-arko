# Repository map

Read `docs/standard.md` for shared engineering rules and
`docs/profiles/fastapi-react.md` for this implementation. Architecture decisions:
`docs/decisions/0001-profile.md`. Current work and sources: `docs/tasks/current.md`.

Locate a feature with `python tools/arko.py context notes --root .`.
The feature registry and applied version are in `.arko/project.json`. Use the
source code to confirm imports and runtime dependencies.

Run `python tools/arko.py check --root .` after setup. Review contract changes
before approving a new baseline.
