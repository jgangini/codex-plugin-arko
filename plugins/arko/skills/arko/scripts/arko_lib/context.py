import ast
from pathlib import Path

from .io import digest, inside, project
from .scaffold import feature_files


def python_imports(
    path: Path, root: Path, *, dynamic_import_lines: list[int] | None = None
) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = list(path.relative_to(root / "backend").with_suffix("").parts[:-1])
    result = []
    import_functions = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            import_functions.update(
                alias.asname or alias.name for alias in node.names if alias.name == "import_module"
            )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = package[: len(package) - node.level + 1] if node.level else []
            module = ".".join([*prefix, *([node.module] if node.module else [])])
            result.extend(f"{module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name)
            and node.func.id in import_functions
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
        ):
            if dynamic_import_lines is None:
                raise ValueError(f"Dynamic Python import needs explicit analysis: {path}")
            dynamic_import_lines.append(node.lineno)
    return sorted(set(result))


def audit(root: Path) -> list[str]:
    data = project(root)
    features = data["features"]
    errors = []
    for name, entry in features.items():
        actual, declared = set(feature_files(root, name)), set(entry["files"])
        errors.extend(f"{name}: stale/unregistered path {p}" for p in sorted(actual ^ declared))
        for p in declared:
            inside(root, p)
        for dep in entry["depends_on"]:
            if dep not in features or dep == name:
                errors.append(f"{name}: invalid dependency {dep}")
    for tree in ("backend/app/features", "frontend/src/features"):
        for folder in inside(root, tree).glob("*"):
            if folder.is_dir() and folder.name != "__pycache__" and folder.name not in features:
                errors.append(f"Unregistered feature: {folder.name}")
    for path in (root / "backend/app").rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        parts = path.relative_to(root / "backend/app").parts
        owner = parts[1] if len(parts) > 2 and parts[0] == "features" else None
        for target in python_imports(path, root):
            if parts[0] == "core" and target.startswith("app.features"):
                errors.append(f"{relative}: core cannot import features ({target})")
            if path.stem in {"service", "schemas"} and (
                target.startswith(("fastapi", "starlette")) or ".api" in target.split("app")[-1]
            ):
                errors.append(f"{relative}: domain/schema cannot import transport ({target})")
            if path.stem == "schemas" and ".service" in target:
                errors.append(f"{relative}: schema cannot import service ({target})")
            if owner and target.startswith("app.features."):
                tokens = target.split(".")
                other = tokens[2]
                if other != owner and (
                    other not in features[owner]["depends_on"] or len(tokens) < 4 or tokens[3] != "schemas"
                ):
                    errors.append(f"{relative}: forbidden feature dependency {target}")
    return errors


def context(root: Path, name: str) -> dict:
    data = project(root)
    features = data["features"]
    if name not in features:
        raise ValueError(f"Unknown feature: {name}")
    selected = {name}
    while True:
        expanded = selected | {dep for f in selected for dep in features[f]["depends_on"]}
        expanded |= {f for f, entry in features.items() if set(entry["depends_on"]) & selected}
        if expanded == selected:
            break
        if expanded - features.keys():
            raise ValueError("Map contains unknown dependencies")
        selected = expanded
    files = {p for f in selected for p in feature_files(root, f)}
    for shared in ("backend/app/core", "backend/tests", "frontend/src/shared", "contracts", "docs"):
        files.update(
            p.relative_to(root).as_posix()
            for p in (root / shared).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        )
    files |= {"backend/app/main.py", "AGENTS.md", ".arko/project.json"}
    if data["frontend"]:
        files.add("frontend/src/App.tsx")
    records = []
    for relative in sorted(files):
        path = inside(root, relative)
        if not path.exists():
            continue
        record = {"path": relative, "sha256": digest(path)}
        if path.suffix == ".py":
            import_lines = [] if path.is_relative_to(root / "backend/tests") else None
            record["imports"] = python_imports(path, root, dynamic_import_lines=import_lines)
            if import_lines:
                record["dynamic_import_lines"] = sorted(set(import_lines))
            record["symbols"] = [
                {"name": n.name, "line": n.lineno}
                for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            ]
        records.append(record)
    return {
        "feature": name,
        "related_features": sorted(selected),
        "files": records,
        "problems": audit(root),
        "task": (root / "docs/tasks/current.md").read_text(encoding="utf-8"),
        "limits": "Declared dependency closure + Python AST; no runtime proof. TS AST checked by check. "
        "Inspect external consumers, dependency injection, config and undeclared calls; expand as needed.",
    }
