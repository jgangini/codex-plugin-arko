"""Build a reviewable local plugin zip, excluding caches and dependencies."""

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
plugin = ROOT / "plugins/arko"
sys.path.insert(0, str(plugin / "skills/arko/scripts"))
from arko_lib.scaffold import source_files  # noqa: E402

manifest = json.loads((plugin / "plugin.json").read_text())
version = manifest["version"]
assert manifest["name"] == "arko"
assert isinstance(version, str) and re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version)
assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
assert (plugin / "skills/arko/SKILL.md").is_file()
catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
assert (ROOT / catalog["plugins"][0]["source"]["path"]).resolve() == plugin.resolve()
output = ROOT / f"artifacts/arko-{version}.zip"
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(source_files(plugin)):
        archive.write(path, "arko/" + path.relative_to(plugin).as_posix())
digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(".zip.sha256").write_text(digest + "  " + output.name + "\n")
print(f"{output}: {output.stat().st_size} bytes; SHA256 {digest}")
