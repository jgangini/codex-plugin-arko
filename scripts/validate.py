"""One validation route. --docker adds local builds and HTTP smoke tests."""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "plugins/arko/skills/arko/scripts/arko.py"
EXAMPLE = ROOT / "examples/notes"
RECORDS = []


def run(label, command, cwd=ROOT, expected=0):
    start = time.monotonic()
    resolved = [shutil.which(str(command[0])) or str(command[0]), *map(str, command[1:])]
    result = subprocess.run(
        resolved, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    record = {
        "label": label,
        "command": list(map(str, command)),
        "cwd": str(cwd),
        "seconds": round(time.monotonic() - start, 3),
        "exit_code": result.returncode,
        "expected": expected,
        "output": result.stdout + result.stderr,
    }
    RECORDS.append(record)
    print(f"{label}: exit={result.returncode}, {record['seconds']}s", flush=True)
    if (expected == 0 and result.returncode != 0) or (expected == "failure" and result.returncode == 0):
        raise RuntimeError(record["output"])
    return record["output"]


def cli(label, operation, root, *args):
    return run(label, [sys.executable, CLI, operation, "--root", root, *args])


def mount_feature(root, name):
    main = root / "backend/app/main.py"
    text = main.read_text(encoding="utf-8")
    marker = "# Mount feature routers here, before the optional static root."
    text = text.replace(
        "from pathlib import Path\n",
        "from pathlib import Path\n"
        f"from app.features.{name}.api import create_router as {name}_router\n"
        f"from app.features.{name}.service import Store as {name}_store\n",
        1,
    )
    text = text.replace(marker, f"{marker}\napp.include_router({name}_router({name}_store()))", 1)
    main.write_text(text, encoding="utf-8")


def fresh_application(cache):
    with tempfile.TemporaryDirectory(dir=cache, prefix="fresh-") as folder:
        root = Path(folder) / "app"
        run("init backend-only", [sys.executable, CLI, "init", root])
        cli("setup backend-only", "setup", root)
        cli("check backend-only", "check", root)
        cli("add feature", "add-feature", root, "tasks")
        manifest = root / ".arko/project.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["features"]["tasks"]["public_routes"] = ["POST /api/tasks", "GET /api/tasks/{item_id}"]
        manifest.write_text(json.dumps(data), encoding="utf-8")
        main = root / "backend/app/main.py"
        without_router = main.read_text(encoding="utf-8")
        mount_feature(root, "tasks")
        run(
            "format composition imports",
            ["uv", "run", "--locked", "ruff", "check", "backend/app/main.py", "--fix"],
            root,
        )
        cli("add React later", "frontend", root)
        cli("setup combined", "setup", root)
        cli("export new contract", "contract", root)
        cli(
            "accept fixture contract",
            "accept-contract",
            root,
            "--reason",
            "Acceptance fixture: new tasks endpoints",
        )
        cli("check fresh full stack", "check", root)
        # Keep the published schema identical so schema drift alone cannot catch the missing router.
        main.write_text(
            "import json\n" + without_router
            + "\napp.openapi = lambda: json.loads(Path('contracts/openapi.json').read_text(encoding='utf-8'))\n",
            encoding="utf-8",
        )
        for operation, args in (("check", []), ("contract", []), ("accept-contract", ["--reason", "fixture"])):
            output = run(
                f"{operation} rejects unmounted public routes",
                [sys.executable, CLI, operation, "--root", root, *args],
                expected="failure",
            )
            assert "public route POST /api/tasks is not mounted in app.main:app" in output, output
            assert "public route GET /api/tasks/{item_id} is not mounted in app.main:app" in output, output
        data = json.loads(manifest.read_text(encoding="utf-8"))
        del data["features"]["tasks"]["public_routes"]
        manifest.write_text(json.dumps(data), encoding="utf-8")
        output = run(
            "check protects approved routes without declarations",
            [sys.executable, CLI, "check", "--root", root],
            expected="failure",
        )
        assert "approved OpenAPI: public route POST /api/tasks is not mounted in app.main:app" in output, output
        assert "approved OpenAPI: public route GET /api/tasks/{item_id} is not mounted" in output, output

        main.write_text(without_router, encoding="utf-8")
        cli("export honest candidate for intentional retirement", "contract", root)
        output = run(
            "check rejects retirement before review",
            [sys.executable, CLI, "check", "--root", root],
            expected="failure",
        )
        assert "approved OpenAPI: public route POST /api/tasks is not mounted" in output, output
        cli("accept reviewed intentional retirement", "accept-contract", root, "--reason", "Fixture retirement")
        approved = json.loads((root / "contracts/baseline.json").read_text(encoding="utf-8"))
        assert "/api/tasks" not in approved["paths"] and "/api/tasks/{item_id}" not in approved["paths"]


def fixture_openapi(label, root):
    code = (
        "import json, sys; sys.path.insert(0, 'backend'); "
        "from app.main import app; print(json.dumps(app.openapi()))"
    )
    return json.loads(run(label, [sys.executable, "-B", "-c", code], root))


def verify_schema_extension(label, root, baseline, name):
    baseline_path = root / "contracts/baseline.json"
    approved_bytes = baseline_path.read_bytes()
    cli(f"{label}: generate second feature", "add-feature", root, name)
    schema = root / f"backend/app/features/{name}/schemas.py"
    source = schema.read_text(encoding="utf-8")
    assert "    title: str" in source
    schema.write_text(source.replace("    title: str", "    label: str\n    title: str", 1), encoding="utf-8")
    mount_feature(root, name)
    current = fixture_openapi(f"{label}: export with distinct second schema", root)
    for path, operation in baseline["paths"].items():
        assert current["paths"].get(path) == operation, f"{label}: contract changed for {path}"
    components = current["components"]["schemas"]
    for key, component in baseline["components"]["schemas"].items():
        assert components.get(key) == component, f"{label}: component changed for {key}"
    post = current["paths"][f"/api/{name}"]["post"]
    assert post["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        f"#/components/schemas/CreateItem_{name}"
    )
    assert post["responses"]["201"]["content"]["application/json"]["schema"]["$ref"] == (
        f"#/components/schemas/Item_{name}"
    )
    assert components[f"CreateItem_{name}"]["properties"]["label"]["type"] == "string"
    assert baseline_path.read_bytes() == approved_bytes, f"{label}: approved baseline was rewritten"
    RECORDS.append({"label": f"{label}: preserve approved schemas and operation references", "result": "pass"})


def schema_stability(cache):
    with tempfile.TemporaryDirectory(dir=cache, prefix="schema-stability-") as folder:
        root = Path(folder) / "generated"
        run("schema stability: init application", [sys.executable, CLI, "init", root])
        cli("schema stability: generate first feature", "add-feature", root, "line_items")
        mount_feature(root, "line_items")
        baseline = fixture_openapi("schema stability: export first feature", root)
        (root / "contracts/baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
        verify_schema_extension("generated templates", root, baseline, "line__items")
        assert {"CreateItem_line_items", "Item_line_items"} <= baseline["components"]["schemas"].keys()

        root = Path(folder) / "notes"
        for directory in ("backend", ".arko", "contracts"):
            shutil.copytree(EXAMPLE / directory, root / directory, ignore=shutil.ignore_patterns("__pycache__"))
        baseline = json.loads((root / "contracts/baseline.json").read_text(encoding="utf-8"))
        assert fixture_openapi("Notes: export approved example", root) == baseline
        proposal = cli("Notes: review schema template upgrade", "upgrade", root)
        assert any(
            line.startswith("backend/app/features/notes/schemas.py: CUSTOMIZED")
            and "preserve approved OpenAPI names" in line
            for line in proposal.splitlines()
        )
        verify_schema_extension("Notes", root, baseline, "reminders")
        assert {"CreateItem", "Item"} <= baseline["components"]["schemas"].keys()


def approval_integrity(cache):
    with tempfile.TemporaryDirectory(dir=cache, prefix="notes-approval-") as folder:
        root = Path(folder)
        for directory in ("backend", ".arko", "contracts", "frontend"):
            shutil.copytree(
                EXAMPLE / directory,
                root / directory,
                ignore=shutil.ignore_patterns("__pycache__", "node_modules", "dist"),
            )
        for name in ("pyproject.toml", "uv.lock", ".python-version"):
            shutil.copy2(EXAMPLE / name, root / name)
        cli("Notes approval fixture: setup", "setup", root)
        baseline = root / "contracts/baseline.json"
        log = root / "contracts/acceptance.json"
        prior_approval = log.read_bytes()
        changed = baseline.read_bytes() + b"\n"
        baseline.write_bytes(changed)
        output = run(
            "Notes: reject baseline edited without approval",
            [sys.executable, CLI, "check", "--root", root],
            expected="failure",
        )
        assert "baseline.json does not match the latest approval" in output, output
        assert baseline.read_bytes() == changed and log.read_bytes() == prior_approval
        cli("Notes: approve unchanged API explicitly", "accept-contract", root, "--reason", "Regression fixture review")
        assert log.read_bytes() != prior_approval
        cli("Notes: verify explicitly approved baseline", "check", root)


def mutations(cache):
    with tempfile.TemporaryDirectory(dir=cache, prefix="mutation-") as folder:
        root = Path(folder)
        shutil.copytree(EXAMPLE / "backend", root / "backend", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(EXAMPLE / "pyproject.toml", root / "pyproject.toml")
        service = root / "backend/app/features/notes/service.py"
        original = service.read_text()
        service.write_text(original.replace("entry is None or entry[0] != actor", "entry is None"))
        output = run(
            "authorization mutation caught",
            [sys.executable, "-m", "pytest", "backend/tests/test_notes.py", "-q"],
            root,
            "failure",
        )
        assert "test_owner_and_validation" in output and "200 == 404" in output, output
        service.write_text(original)
        schemas = root / "backend/app/features/notes/schemas.py"
        schemas.write_text(schemas.read_text().replace("ge=1", "ge=0"))
        output = run(
            "validation mutation caught",
            [sys.executable, "-m", "pytest", "backend/tests/test_priority.py", "-q"],
            root,
            "failure",
        )
        assert "test_priority_rejected" in output and "201 == 422" in output, output
    frontend = EXAMPLE / "frontend"
    with tempfile.TemporaryDirectory(dir=cache, prefix="ts-boundary-") as folder:
        root = Path(folder)
        (root / "frontend/src/shared").mkdir(parents=True)
        (root / "frontend/src/shared/bad.ts").write_text('import "../features/notes/api";\n')
        (root / ".arko").mkdir()
        shutil.copy2(EXAMPLE / ".arko/project.json", root / ".arko/project.json")
        shutil.copy2(frontend / "tsconfig.json", root / "frontend/tsconfig.json")
        output = run(
            "frontend architecture mutation caught",
            ["node", frontend / "scripts/boundaries.mjs"],
            root / "frontend",
            "failure",
        )
        assert "shared imports feature" in output, output
    with tempfile.TemporaryDirectory(dir=cache, prefix="ts-contract-") as folder:
        probe = Path(folder) / "probe.ts"
        types = (frontend / "src/shared/api.generated.ts").as_posix()
        probe.write_text(
            f'import type {{ paths }} from "{types}";\n'
            'const body: paths["/api/notes"]["post"]["requestBody"]["content"]["application/json"] = {title: 42};\n'
        )
        output = run(
            "TS consumer incompatible field caught",
            [
                "node",
                frontend / "node_modules/typescript/bin/tsc",
                "--noEmit",
                "--strict",
                "--skipLibCheck",
                "--moduleResolution",
                "bundler",
                "--module",
                "esnext",
                "--target",
                "es2022",
                probe,
            ],
            expected="failure",
        )
        assert "not assignable to type 'string'" in output, output


def wait_http(url, child=None):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if child is not None and child.poll() is not None:
            raise RuntimeError("Dev coordinator exited before HTTP readiness")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return response.status, response.read().decode()
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"HTTP did not become ready: {url}")


def dev_checks(cache):
    # Reserved ports are probed before starting; never terminate unrelated servers.
    for port in (8000, 5173):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))
    sys.path.insert(0, str(CLI.parent))
    from arko_lib.runtime import stop_process

    flags = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with (cache / "dev.log").open("w") as log:
        child = subprocess.Popen(
            [sys.executable, str(CLI), "dev", "--root", str(EXAMPLE)], stdout=log, stderr=log, **flags
        )
        try:
            assert wait_http("http://127.0.0.1:8000/api/health", child)[0] == 200
            assert wait_http("http://127.0.0.1:5173", child)[0] == 200
            RECORDS.append({"label": "dev backend + frontend HTTP", "result": "pass"})
        finally:
            stop_process(child)
    with tempfile.TemporaryDirectory(dir=cache, prefix="dev-failure-") as folder:
        root = Path(folder)
        (root / ".arko").mkdir()
        data = json.loads((EXAMPLE / ".arko/project.json").read_text())
        data["frontend"] = False
        (root / ".arko/project.json").write_text(json.dumps(data))
        for name in ("pyproject.toml", "uv.lock"):
            shutil.copy2(EXAMPLE / name, root / name)
        (root / "backend/app").mkdir(parents=True)
        (root / "backend/app/main.py").write_text('raise RuntimeError("intentional-startup-failure")\n')
        cli("setup failing ASGI fixture", "setup", root)
        started = time.monotonic()
        result = subprocess.run(
            [sys.executable, str(CLI), "dev", "--root", str(root)], capture_output=True, text=True, timeout=20
        )
        assert result.returncode != 0 and "intentional-startup-failure" in result.stderr
        RECORDS.append(
            {
                "label": "dev propagates ASGI startup failure",
                "exit_code": result.returncode,
                "seconds": round(time.monotonic() - started, 3),
                "result": "pass",
            }
        )


def docker_checks():
    cli("Docker full stack build", "docker", EXAMPLE, "--tag", "arko-notes:validation")
    run(
        "Docker backend build",
        ["docker", "build", "-f", "Dockerfile", "-t", "arko-backend:validation", "."],
        EXAMPLE,
    )
    for image in ("arko-notes:validation", "arko-backend:validation"):
        identifier = run(
            "Docker start " + image, ["docker", "run", "-d", "--rm", "-p", "127.0.0.1::8000", image]
        ).strip()
        try:
            port = run("Docker port", ["docker", "port", identifier, "8000"]).strip().split(":")[-1]
            assert wait_http(f"http://127.0.0.1:{port}/api/health")[0] == 200
            if image.startswith("arko-notes"):
                assert '<div id="root">' in wait_http(f"http://127.0.0.1:{port}")[1]
            user = run("Docker runtime user", ["docker", "exec", identifier, "id", "-u"]).strip()
            assert user == "10001", user
            RECORDS.append({"label": "Docker HTTP and nonroot " + image, "result": "pass"})
        finally:
            run("Docker cleanup own container", ["docker", "stop", identifier])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true")
    args = parser.parse_args()
    cache = ROOT / ".cache/validation"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ["UV_CACHE_DIR"] = str(ROOT / ".cache/uv")
    os.environ["npm_config_cache"] = str(ROOT / ".cache/npm")
    try:
        run("plugin regression tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
        run(
            "plugin lint",
            [
                EXAMPLE / (".venv/Scripts/ruff.exe" if os.name == "nt" else ".venv/bin/ruff"),
                "check",
                "plugins",
                "scripts",
                "tests",
            ],
        )
        cli("example full verification", "check", EXAMPLE)
        fresh_application(cache)
        schema_stability(cache)
        approval_integrity(cache)
        mutations(cache)
        dev_checks(cache)
        if args.docker:
            docker_checks()
        run("package", [sys.executable, ROOT / "scripts/package.py"])
    finally:
        target = ROOT / "artifacts/validation.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(RECORDS, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
