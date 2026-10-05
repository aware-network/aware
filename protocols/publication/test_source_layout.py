"""Neutral source boundary and immutable-candidate accounting, not new authority."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = json.loads((ROOT / "protocols/publication/source-layout.json").read_bytes())


class SourceLayoutTests(unittest.TestCase):
    def test_exact_relocated_inventory(self):
        self.assertEqual(len(LAYOUT["moves"]), 187)
        destinations = [m["path"] for m in LAYOUT["moves"]]
        self.assertEqual(len(destinations), len(set(destinations)))
        for item in LAYOUT["moves"]:
            path = ROOT / item["path"]
            self.assertFalse(path.is_symlink())
            data = path.read_bytes()
            self.assertEqual(len(data), item["bytes"], item["path"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"], item["path"])
            self.assertFalse((ROOT / item["previous_path"]).exists(), item["previous_path"])
        for item in LAYOUT.get("additions", []):
            data = (ROOT / item["path"]).read_bytes()
            self.assertEqual(len(data), item["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])

    def test_only_provenance_link_readmes_changed(self):
        changed = [m for m in LAYOUT["moves"] if not m["byte_identical"]]
        provenance = json.loads((ROOT / "protocols/agent/source-provenance.json").read_bytes())
        amendments = set(provenance.get("owner_adoption", {}).get("public_changed_paths", []))
        historical_readmes = {m["path"] for m in changed if m["path"].endswith("/README.md")}
        self.assertEqual(len(historical_readmes), 6)
        self.assertEqual({m["path"] for m in changed}, historical_readmes | amendments)
        for item in LAYOUT["moves"]:
            if not item["path"].endswith("/README.md") and item["path"] not in amendments:
                self.assertEqual(item["sha256"], item["previous_sha256"], item["path"])

    def test_workspace_files_are_allowlisted(self):
        admitted = {m["path"] for m in LAYOUT["moves"] if m["path"].startswith("workspaces/")}
        admitted.update(m["path"] for m in LAYOUT.get("additions", []))
        actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "workspaces").rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts}
        self.assertEqual(actual, admitted | {"workspaces/README.md"})

    def test_no_retired_internal_surface_is_restored(self):
        forbidden = {"ontology", "apis", "services", "dto", "orm", "experience", "aware.repo.toml", "aware.module.toml"}
        for path in (ROOT / "workspaces").rglob("*"):
            self.assertFalse(forbidden.intersection(path.relative_to(ROOT).parts), str(path))
        self.assertFalse((ROOT / "aware.repo.toml").exists())
        self.assertFalse((ROOT / ".aware/workspace").exists())
        self.assertFalse((ROOT / ".aware/repository").exists())

    def test_sixteen_neutral_projects_are_explicit(self):
        projects = list((ROOT / "workspaces").rglob("pyproject.toml"))
        self.assertEqual(len(projects), 16)
        names = [tomllib.loads(p.read_text())["project"]["name"] for p in projects]
        self.assertEqual(len(set(names)), 16)
        for project in LAYOUT["agent_projects"].values():
            self.assertTrue((ROOT / project / "pyproject.toml").is_file())

    def test_python_sources_still_parse(self):
        for path in (ROOT / "workspaces").rglob("*.py"):
            ast.parse(path.read_bytes(), filename=str(path))

    def test_historical_builder_and_candidate_are_unchanged(self):
        archive = ROOT / "protocols/agent/distribution/aware-agent-fs-0.1.0a3-linux_x86_64-py312.tar.gz"
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), "4af072afaea666480009c03721c9846d122f61d7160fb1511329463762222a1c")
        self.assertEqual(hashlib.sha256((ROOT / "protocols/publication/builders/agent-0.1.0a3.py").read_bytes()).hexdigest(), "796e7ade8bdb2aa6b633ae9a07339b07b18e8b9888eb5160e2157f912333eb4e")

    def test_current_builder_refuses_immutable_overwrite_before_source_mutation(self):
        version = tomllib.loads((ROOT / LAYOUT["agent_projects"]["aware_agent_cli"] / "pyproject.toml").read_text())["project"]["version"]
        if not (ROOT / ("protocols/agent/distribution/aware-agent-fs-" + version + "-linux_x86_64-py312.tar.gz")).exists():
            self.assertEqual(version, "0.1.0a5")
            self.assertEqual(json.loads((ROOT / "protocols/agent/release.json").read_bytes())["version"], "0.1.0a4")
            return  # a5 preparation does not promote the a4 selection
        paths = [ROOT / m["path"] for m in LAYOUT["moves"]]
        before = [p.read_bytes() for p in paths]
        result = subprocess.run([sys.executable, "-B", str(ROOT / "protocols/agent/build_bundle.py"),
                                 "--registry-wheelhouse", "/not-used-by-this-refusal"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable_candidate_exists", result.stderr)
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_original_preparation_and_agent_source_matches_installed_archive(self):
        spec = importlib.util.spec_from_file_location("layout_install", ROOT / "protocols/install.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        release = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        _, files = module.verified_archive((ROOT / "protocols/agent" / release["archive"]).read_bytes(), release["archive_sha256"])
        for item in LAYOUT["moves"]:
            if item["previous_path"].startswith("protocols/agent/source/") and item["byte_identical"]:
                archive_path = item["previous_path"].removeprefix("protocols/agent/")
                self.assertEqual((ROOT / item["path"]).read_bytes(), files[archive_path], item["path"])

    def test_undeclared_projection_and_parent_paths_refused(self):
        spec = importlib.util.spec_from_file_location("tested_source_layout", ROOT / "protocols/publication/source_layout.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaisesRegex(ValueError, "source_coordinate_not_admitted"):
            module.current_path("protocols/source/private-extra.py")
        with self.assertRaisesRegex(ValueError, "layout_path_invalid"):
            module.relative("../outside")


if __name__ == "__main__":
    unittest.main()
