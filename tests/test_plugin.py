import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/arko/skills/arko/scripts"
sys.path.insert(0, str(SCRIPTS))
from arko_lib import scaffold  # noqa: E402
from arko_lib.approval import approved_baseline, record_approval  # noqa: E402
from arko_lib.context import audit, context  # noqa: E402
from arko_lib.contracts import compatible, declared_public_routes, json_equal  # noqa: E402
from arko_lib.io import inside, project, read_json, write_json  # noqa: E402


class PluginTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / ".cache/tests"
        cache.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=cache)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "app"
        scaffold.init(self.root, False)

    def test_init_writes_repository_map_as_agents_md(self):
        template = scaffold.TEMPLATES / "base/agent-instructions.md"
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), template.read_bytes())
        self.assertFalse((self.root / template.name).exists())

    def test_init_does_not_overwrite(self):
        path = self.root / "AGENTS.md"
        path.write_text("custom", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "empty"):
            scaffold.init(self.root, True)
        self.assertEqual(path.read_text(), "custom")

    def test_scaffold_source_files_ignore_binary_cache(self):
        fixture = self.root / "source"
        cache = fixture / ".ruff_cache" / "version"
        cache.mkdir(parents=True)
        (cache / "binary-cache").write_bytes(b"\xff")
        (fixture / "model.pyc").write_bytes(b"\xff")
        (fixture / "model.py").write_text("answer = 42\n")
        self.assertEqual(list(scaffold.source_files(fixture)), [fixture / "model.py"])

    def test_initial_baseline_has_a_matching_approval(self):
        self.assertEqual(approved_baseline(self.root), read_json(self.root / "contracts/baseline.json"))

    def test_approval_verification_requires_latest_valid_record(self):
        log = self.root / "contracts/acceptance.json"
        baseline = self.root / "contracts/baseline.json"
        original = baseline.read_bytes()
        matching = read_json(log)["reviews"][0]

        write_json(log, {"reviews": [matching, {**matching, "sha256": "0" * 64}]})
        with self.assertRaisesRegex(ValueError, "does not match the latest approval"):
            approved_baseline(self.root)

        log.unlink()
        with self.assertRaisesRegex(ValueError, "Missing contract approval"):
            approved_baseline(self.root)
        write_json(log, {"reviews": ["invalid entry"]})
        with self.assertRaisesRegex(ValueError, "Invalid latest contract approval"):
            approved_baseline(self.root)

        write_json(log, {"reviews": "invalid log"})
        with self.assertRaisesRegex(ValueError, "Invalid contract approval log"):
            record_approval(self.root, {"openapi": "3.1.0"}, "Test replacement")
        self.assertEqual(baseline.read_bytes(), original)

    def test_backend_then_frontend_preserves_customization(self):
        scaffold.add_feature(self.root, "notes")
        custom = self.root / "backend/app/features/notes/service.py"
        custom.write_text(custom.read_text() + "\n# local extension\n", encoding="utf-8")
        previous = custom.read_bytes()
        scaffold.add_frontend(self.root)
        self.assertEqual(previous, custom.read_bytes())
        self.assertTrue((self.root / "frontend/src/features/notes/api.ts").exists())
        self.assertEqual(audit(self.root), [])

    def test_frontend_collision_is_preflighted(self):
        target = self.root / "frontend/src/App.tsx"
        target.parent.mkdir(parents=True)
        target.write_text("custom")
        with self.assertRaises(ValueError):
            scaffold.add_frontend(self.root)
        self.assertFalse((self.root / "frontend/package.json").exists())
        self.assertFalse(project(self.root)["frontend"])

    def test_invalid_paths_and_identifiers(self):
        for name in ("../escape", "class", "Bad-Name", "a/b"):
            with self.assertRaises(ValueError):
                scaffold.add_feature(self.root, name)
        with self.assertRaises(ValueError):
            inside(self.root, "../escape")

    def test_context_closes_declared_dependencies_and_consumers(self):
        for name in ("notes", "users", "reports"):
            scaffold.add_feature(self.root, name)
        data = project(self.root)
        data["features"]["notes"]["depends_on"] = ["users"]
        data["features"]["reports"]["depends_on"] = ["notes"]
        write_json(self.root / ".arko/project.json", data)
        result = context(self.root, "notes")
        self.assertEqual(result["related_features"], ["notes", "reports", "users"])
        paths = {p["path"] for p in result["files"]}
        self.assertIn("backend/app/core/auth.py", paths)
        self.assertIn("backend/tests/test_notes.py", paths)
        self.assertTrue(all("sha256" in p for p in result["files"]))

    def test_context_reports_dynamic_test_imports_in_cli_output(self):
        scaffold.add_feature(self.root, "notes")
        relative = "backend/tests/test_notes.py"
        (self.root / relative).write_text(
            "from importlib import import_module as load\n"
            "from pathlib import Path\n\n"
            "def test_notes():\n"
            "    load('fixture')\n"
            "    __import__('another_fixture')\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(self.root / "tools/arko.py"), "context", "notes", "--root", str(self.root)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        entry = next(item for item in data["files"] if item["path"] == relative)
        self.assertEqual(entry["imports"], ["importlib.import_module", "pathlib.Path"])
        self.assertEqual(entry["symbols"], [{"name": "test_notes", "line": 4}])
        self.assertEqual(entry["dynamic_import_lines"], [5, 6])
        self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(data["problems"], [])

    def test_map_detects_new_and_deleted_files(self):
        scaffold.add_feature(self.root, "notes")
        feature = self.root / "backend/app/features/notes"
        (feature / "service.py").unlink()
        (feature / "new.py").write_text("x = 1\n")
        errors = "\n".join(audit(self.root))
        self.assertIn("service.py", errors)
        self.assertIn("new.py", errors)

    def test_architecture_rejects_transport_and_cross_feature_imports(self):
        for name in ("notes", "users"):
            scaffold.add_feature(self.root, name)
        path = self.root / "backend/app/features/notes/service.py"
        path.write_text("from fastapi import HTTPException\nfrom ..users.service import Store\n")
        errors = "\n".join(audit(self.root))
        self.assertIn("domain/schema", errors)
        self.assertIn("forbidden feature", errors)

    def test_core_cannot_import_feature(self):
        scaffold.add_feature(self.root, "notes")
        (self.root / "backend/app/core/auth.py").write_text("from app.features.notes import schemas\n")
        self.assertIn("core cannot", "\n".join(audit(self.root)))

    def test_dynamic_import_fails_closed(self):
        (self.root / "backend/app/core/auth.py").write_text("__import__('app.features.notes')\n")
        with self.assertRaisesRegex(ValueError, "Dynamic"):
            audit(self.root)
        (self.root / "backend/app/core/auth.py").write_text(
            "from importlib import import_module as load\nload('app.features.notes')\n"
        )
        with self.assertRaisesRegex(ValueError, "Dynamic"):
            audit(self.root)

    def test_upgrade_is_readonly_and_marks_customization(self):
        scaffold.add_feature(self.root, "notes")
        service = self.root / "backend/app/features/notes/service.py"
        service.write_text("# custom service\n")
        path = self.root / "AGENTS.md"
        path.write_text("my rules\n")
        proposal = scaffold.upgrade(self.root)
        self.assertIn("CUSTOMIZED", proposal)
        self.assertIn("backend/app/features/notes/service.py", proposal)
        self.assertIn("backend/app/features/notes/service.py", project(self.root)["managed"])
        self.assertIn("+", proposal)
        self.assertEqual(path.read_text(), "my rules\n")

    def test_resume_from_fresh_process(self):
        scaffold.add_feature(self.root, "notes")
        state = "Source: ticket-12\nPending: preserve owner checks\nNext: add priority 1..5\n"
        (self.root / "docs/tasks/current.md").write_text(state)
        result = subprocess.run(
            [sys.executable, str(self.root / "tools/arko.py"), "context", "notes", "--root", str(self.root)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(result.stdout)["task"], state)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.old = {
            "paths": {"/api/notes": {"post": {"responses": {"201": {"description": "ok"}}}}},
            "components": {
                "schemas": {
                    "Note": {
                        "type": "object",
                        "required": ["title"],
                        "properties": {"title": {"type": "string"}},
                    }
                }
            },
        }

    def test_removed_path_and_type_change_fail(self):
        new = copy.deepcopy(self.old)
        del new["paths"]["/api/notes"]
        self.assertTrue(compatible(self.old, new))
        new = copy.deepcopy(self.old)
        new["components"]["schemas"]["Note"]["properties"]["title"]["type"] = "integer"
        self.assertTrue(compatible(self.old, new))

    def test_property_named_title_is_not_metadata(self):
        new = copy.deepcopy(self.old)
        del new["components"]["schemas"]["Note"]["properties"]["title"]
        self.assertTrue(compatible(self.old, new))

    def test_required_field_added_fails(self):
        new = copy.deepcopy(self.old)
        new["components"]["schemas"]["Note"]["required"].append("priority")
        self.assertTrue(compatible(self.old, new))

    def test_optional_field_and_endpoint_addition(self):
        new = copy.deepcopy(self.old)
        new["components"]["schemas"]["Note"]["properties"]["priority"] = {"type": "integer"}
        new["paths"]["/api/other"] = {"get": {}}
        self.assertEqual(compatible(self.old, new), [])

    def test_security_removal_fails(self):
        old = copy.deepcopy(self.old)
        old["paths"]["/api/notes"]["post"]["security"] = [{"HTTPBearer": []}]
        self.assertTrue(compatible(old, self.old))

    def test_contract_audit_detects_new_property_in_closed_response(self):
        schema = {"type": "object", "additionalProperties": False, "properties": {"id": {"type": "integer"}}}
        response = self.old["paths"]["/api/notes"]["post"]["responses"]["201"]
        response["content"] = {"application/json": {"schema": schema}}
        new = copy.deepcopy(self.old)
        revision = new["paths"]["/api/notes"]["post"]["responses"]["201"]["content"]["application/json"]["schema"]
        revision["properties"]["label"] = {"type": "string"}
        self.assertTrue(any("closed schema" in error and ".properties.label" in error
                            for error in compatible(self.old, new)))
        schema["additionalProperties"] = revision["additionalProperties"] = True
        self.assertEqual(compatible(self.old, new), [])

    def test_contract_audit_distinguishes_boolean_from_number_in_enum(self):
        old = {"enum": [True]}
        self.assertTrue(compatible(old, {"enum": [1]}))
        self.assertFalse(json_equal(old, {"enum": [1]}))
        self.assertEqual(compatible({"enum": [1]}, {"enum": [1.0]}), [])

    def test_contract_audit_allows_new_method_on_existing_path(self):
        new = copy.deepcopy(self.old)
        new["paths"]["/api/notes"]["get"] = {"responses": {"200": {"description": "ok"}}}
        self.assertEqual(compatible(self.old, new), [])

    def test_closed_schema_uses_response_references_without_blocking_request_only_additions(self):
        closed = {"additionalProperties": False, "properties": {"id": {"type": "integer"}}}
        self.old["components"] = {
            "schemas": {"Request": copy.deepcopy(closed), "Result": copy.deepcopy(closed)},
            "responses": {"Created": {
                "description": "ok",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Result"}}},
            }},
        }
        operation = self.old["paths"]["/api/notes"]["post"]
        operation["requestBody"] = {
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Request"}}},
        }
        operation["responses"]["201"] = {"$ref": "#/components/responses/Created"}
        new = copy.deepcopy(self.old)
        new["components"]["schemas"]["Request"]["properties"]["label"] = {"type": "string"}
        self.assertEqual(compatible(self.old, new), [])
        new["components"]["schemas"]["Result"]["properties"]["label"] = {"type": "string"}
        self.assertEqual(
            compatible(self.old, new),
            ["$.components.schemas.Result.properties.label: new property in a closed schema requires review"],
        )

    def test_public_routes_are_explicit_and_validated(self):
        features = {
            "legacy": {},
            "draft": {"public_routes": []},
            "ready": {"public_routes": ["GET /api/items/{id}", "POST /api/items"]},
        }
        self.assertEqual(
            declared_public_routes(features),
            [("ready", "GET", "/api/items/{id}"), ("ready", "POST", "/api/items")],
        )
        for invalid in ("GET /api/items", ["get /api/items"], ["GET /api/items?x=1"], [None]):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "ready:"):
                declared_public_routes({"ready": {"public_routes": invalid}})


if __name__ == "__main__":
    unittest.main()
