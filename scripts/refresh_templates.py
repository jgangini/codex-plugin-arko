"""Maintainer operation: refresh locked dependencies and base contract assets."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/arko/skills/arko/scripts"
sys.path.insert(0, str(SCRIPTS))
from arko_lib.scaffold import TEMPLATES, init  # noqa: E402

example = ROOT / "examples/notes"
for source, target in (
    (example / "uv.lock", TEMPLATES / "base/uv.lock"),
    (example / "frontend/package-lock.json", TEMPLATES / "frontend/frontend/package-lock.json"),
):
    target.write_bytes(source.read_bytes())
cache = ROOT / ".cache"
cache.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=cache) as folder:
    app = Path(folder) / "app"
    init(app, True)
    code = "import sys,json; sys.path.insert(0,'backend'); from app.main import app; print(json.dumps(app.openapi()))"
    schema = json.loads(subprocess.check_output([sys.executable, "-c", code], cwd=app, text=True))
    contracts = TEMPLATES / "base/contracts"
    contracts.mkdir(exist_ok=True)
    for name in ("baseline.json", "openapi.json"):
        (contracts / name).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    executable = example / "frontend/node_modules/openapi-typescript/bin/cli.js"
    subprocess.run(
        [
            "node",
            str(executable),
            str(contracts / "openapi.json"),
            "-o",
            str(TEMPLATES / "frontend/frontend/src/shared/api.generated.ts"),
        ],
        check=True,
    )
