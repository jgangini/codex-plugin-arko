import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .approval import approved_baseline, record_approval
from .context import audit
from .contracts import compatible, declared_public_routes, json_equal, openapi_routes
from .io import project, read_json, write_json


def run(command: list[str], root: Path, capture: bool = False) -> str:
    executable = shutil.which(command[0])
    if executable is None:
        raise ValueError(f"Required executable not found: {command[0]}")
    result = subprocess.run(
        [executable, *command[1:]], cwd=root, check=True, text=True, encoding="utf-8", capture_output=capture
    )
    return result.stdout if capture else ""


def python(root: Path, *args: str, capture: bool = False) -> str:
    return run(["uv", "run", "--locked", "python", *args], root, capture)


def export_schema(root: Path) -> dict:
    return _export_schema(root, approved_baseline(root))


def _export_schema(root: Path, approved: dict | None) -> dict:
    expected = declared_public_routes(project(root)["features"])
    # This executes trusted project code, just like tests. Never run on unknown repos implicitly.
    raw = python(
        root,
        "-c",
        """\
import json
import sys

sys.path.insert(0, "backend")
from app.main import app
from fastapi.openapi.utils import get_openapi

# Inspect the composed routes even when the project overrides app.openapi().
generated = get_openapi(title=app.title, version=app.version, routes=app.routes)
paths = {path: list(item) for path, item in generated["paths"].items()}
print(json.dumps([app.openapi(), {"paths": paths}]))
""",
        capture=True,
    )
    schema, generated_paths = json.loads(raw)
    mounted = openapi_routes(generated_paths)
    exported = openapi_routes(schema)
    required = dict.fromkeys(exported, "OpenAPI export")
    if approved is not None:
        required.update(dict.fromkeys(openapi_routes(approved), "approved OpenAPI"))
    required.update({(method, path): feature for feature, method, path in expected})
    errors = []
    for (method, path), source in sorted(required.items()):
        if (method, path) not in mounted:
            errors.append(f"{source}: public route {method} {path} is not mounted in app.main:app")
        elif (method, path) not in exported:
            errors.append(f"{source}: public route {method} {path} is missing from the OpenAPI export")
    if errors:
        raise ValueError("\n".join(errors))
    return schema


def contract(root: Path) -> None:
    data = project(root)
    write_json(root / "contracts/openapi.json", _export_schema(root, None))
    if data["frontend"]:
        run(["npm", "run", "generate"], root / "frontend")


def accept(root: Path, reason: str) -> None:
    if not reason.strip():
        raise ValueError("A review reason is required")
    current = _export_schema(root, None)
    if not json_equal(current, read_json(root / "contracts/openapi.json")):
        raise ValueError("Export current contract first")
    record_approval(root, current, reason)


def setup(root: Path) -> None:
    data = project(root)
    run(["uv", "sync", "--locked"], root)
    if data["frontend"]:
        run(["npm", "ci", "--ignore-scripts"], root / "frontend")


def check(root: Path) -> None:
    data = project(root)
    errors = audit(root)
    if errors:
        raise ValueError("\n".join(errors))
    approved = approved_baseline(root)
    current = _export_schema(root, approved)
    if not json_equal(current, read_json(root / "contracts/openapi.json")):
        raise ValueError("OpenAPI export is stale; run contract and review the diff")
    errors = compatible(approved, current)
    if errors:
        raise ValueError("Contract requires compatibility review:\n" + "\n".join(errors))
    run(["uv", "run", "--locked", "ruff", "check", "backend"], root)
    run(["uv", "run", "--locked", "mypy", "backend/app"], root)
    run(["uv", "run", "--locked", "pytest", "-q"], root)
    if data["frontend"]:
        frontend = root / "frontend"
        cache = root / ".cache"
        cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="arko-types-", dir=cache) as temporary:
            output = Path(temporary) / "api.ts"
            run(
                [
                    "node",
                    "node_modules/openapi-typescript/bin/cli.js",
                    "../contracts/openapi.json",
                    "-o",
                    str(output),
                ],
                frontend,
            )
            if output.read_bytes() != (frontend / "src/shared/api.generated.ts").read_bytes():
                raise ValueError("Generated TS types are stale; run contract")
        run(["npm", "run", "check"], frontend)
    print("Arko checks passed")


def stop_process(child: subprocess.Popen) -> None:
    if child.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True)
    else:
        os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(child.pid, signal.SIGKILL)
        child.kill()
        child.wait()


def dev(root: Path) -> int:
    data = project(root)
    commands = [
        (
            root,
            [
                "uv",
                "run",
                "--locked",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "backend",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
        )
    ]
    if data["frontend"]:
        commands.append((root / "frontend", ["node", "node_modules/vite/bin/vite.js", "--host", "127.0.0.1"]))
    children = []
    try:
        for cwd, command in commands:
            executable = shutil.which(command[0])
            if executable is None:
                raise ValueError(f"Missing executable: {command[0]}")
            flags = (
                {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                if os.name == "nt"
                else {"start_new_session": True}
            )
            children.append(subprocess.Popen([executable, *command[1:]], cwd=cwd, **flags))
        while all(child.poll() is None for child in children):
            time.sleep(0.2)
        return next((c.returncode or 1 for c in children if c.poll() is not None), 1)
    except KeyboardInterrupt:
        return 130
    finally:
        for child in children:
            stop_process(child)


def docker(root: Path, tag: str) -> None:
    import re

    if not re.fullmatch(r"[a-z0-9][a-z0-9._/-]*(?::[a-zA-Z0-9._-]+)?", tag):
        raise ValueError("Invalid Docker tag")
    data = project(root)
    filename = "Dockerfile.web" if data["frontend"] else "Dockerfile"
    run(["docker", "build", "-f", filename, "-t", tag, "."], root)
