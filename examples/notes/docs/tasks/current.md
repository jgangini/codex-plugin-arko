# Current task — notes priority

- Source: repository `docs/acceptance.md` (from this file: `../../../../docs/acceptance.md`), criterion 3; app owner requested optional
  integer priority 1..5 while preserving existing title-only clients.
- Status: priority implementation and acceptance checks passed on 2026-11-03;
  see the evidence below for scope and remaining limits. No product deployment requested.
- Decision: default 3, strict integer, server is authoritative. TS types come from
  OpenAPI; HTML min/max improve feedback but do not replace server checks.
- Relevant files: run `python tools/arko.py context notes --root .`; schemas,
  service, API, core auth, React api/View and tests are linked by that output.
- Last verification: 2026-11-03, `arch-postflight.ps1 -Docker`; see
  `../../../../docs/validation.md` for dated command evidence;
  rerun after edits. Notes themselves do not establish freshness.
- Next action: inspect context and contract, run check; if extending priority,
  update Python field, generated types, React form and boundary tests together.
- Pending: durable storage and production identity require separate requirements.
- Resume question: explain why an unauthenticated request differs from another
  authenticated owner's read; preserve owner success and other-owner 404.
