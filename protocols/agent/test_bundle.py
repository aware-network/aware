"""Candidate-bound archive, source, notice and dependency accounting."""
import email
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
import zipfile

from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("prior_install", ROOT.parent / "install.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = json.loads((ROOT / "release.json").read_bytes())
        _, cls.files = VERIFIER.verified_archive((ROOT / cls.release["archive"]).read_bytes(), cls.release["archive_sha256"])
        cls.wheels = {}
        for name, data in cls.files.items():
            if not name.startswith("wheelhouse/") or not name.endswith(".whl"):
                continue
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                metadata = email.message_from_bytes(archive.read(next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))))
                cls.wheels[canonicalize_name(metadata["Name"])] = (metadata, data)

    def test_exact_wheel_and_source_pins(self):
        self.assertEqual(len(self.wheels), 22)
        self.assertEqual(self.release["version"], self.wheels["aware-agent-cli"][0]["Version"])
        self.assertEqual(self.release["root_requirement"], "aware-agent-cli==" + self.release["version"])
        for record in self.release["wheels"]:
            self.assertEqual(hashlib.sha256(self.files["wheelhouse/" + record["filename"]]).hexdigest(), record["sha256"])
        self.assertEqual(hashlib.sha256((ROOT / "build_bundle.py").read_bytes()).hexdigest(), self.release["builder_sha256"])
        provenance = json.loads(self.files["source-provenance.json"])
        self.assertEqual(len(provenance["files"]), 33)
        self.assertEqual(sum(r["disposition"] == "curated export facade" for r in provenance["files"]), 3)
        for record in provenance["files"]:
            module = record["package"].replace("-", "_")
            relative = record["source_path"].split("/" + module + "/", 1)[1]
            data = self.files["source/" + module + "/" + module + "/" + relative]
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["shipped_sha256"])
            with zipfile.ZipFile(io.BytesIO(self.wheels[record["package"]][1])) as archive:
                self.assertEqual(data, archive.read(module + "/" + relative))
            if record["disposition"] == "byte-identical owner implementation":
                self.assertEqual(record["source_sha256"], record["shipped_sha256"])

    def test_dependency_closure_is_reachable_and_satisfied(self):
        pending, reached, checks = ["aware-agent-cli"], set(), 0
        while pending:
            name = pending.pop()
            if name in reached:
                continue
            reached.add(name)
            metadata = self.wheels[name][0]
            for value in metadata.get_all("Requires-Dist", []):
                requirement = Requirement(value)
                if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                    continue
                dependency = canonicalize_name(requirement.name)
                self.assertIn(dependency, self.wheels)
                self.assertFalse(requirement.url)
                self.assertIn(self.wheels[dependency][0]["Version"], requirement.specifier)
                checks += 1
                pending.append(dependency)
        self.assertEqual(reached, self.wheels.keys())
        self.assertGreaterEqual(checks, 20)

    def test_excluded_surfaces_are_physically_absent(self):
        prohibited = {"aware_local_service_runtime", "aware_workflow", "aware_issue_service_api", "aware_issue_service_dto", "aware_ontology", "aware_orm", "aware_experience", "participant.py"}
        for _, data in self.wheels.values():
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for member in archive.namelist():
                    self.assertFalse(prohibited.intersection(member.split("/")), member)
                    self.assertNotIn("benchmarks", member.split("/"))
                    self.assertFalse(member.endswith("direct_url.json"))

    def test_aware_legal_files_are_in_wheel(self):
        for name, (metadata, data) in self.wheels.items():
            if not name.startswith("aware-"):
                continue
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                legal = [n for n in archive.namelist() if ".dist-info/licenses/" in n]
                self.assertTrue(any(n.endswith("LICENSE") for n in legal), name)
                self.assertTrue(any(n.endswith("NOTICE") for n in legal), name)
                self.assertIn("Apache", metadata.get("License-Expression", "") + metadata.get("License", ""))

    def test_complete_publisher_candidate_notice_inputs(self):
        manifest = json.loads(self.files["notices/pydantic-core/manifest.json"])
        self.assertEqual(len(manifest["components"]), 103)
        self.assertEqual(sum(len(c["legal_files"]) for c in manifest["components"]), 185)
        self.assertEqual(manifest["wheel_sha256"], hashlib.sha256(self.wheels["pydantic-core"][1]).hexdigest())
        for component in manifest["components"]:
            for notice in component["legal_files"]:
                data = self.files["notices/pydantic-core/" + notice["path"]]
                self.assertEqual(len(data), notice["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), notice["sha256"])

    def test_no_aware_private_paths_in_bounded_text_scan(self):
        for name, data in self.files.items():
            if name.endswith((".json", ".md", ".py", ".toml", ".txt")):
                self.assertNotIn(b"/home/aware/", data, name)
                self.assertNotIn(b"/home/luis/", data, name)

    def test_contract_assets_and_identity_match_authored_inputs(self):
        source = ROOT.parent / "contracts/agent-fs/v1.1.0"
        metadata = json.loads((source / "contract.json").read_bytes())
        self.assertEqual(self.release["agent_contract"], {"ref": metadata["contract_ref"], "version": metadata["version"]})
        with zipfile.ZipFile(io.BytesIO(self.wheels["aware-agent-cli"][1])) as archive:
            for relative in ["contract.json", *metadata["files"].values()]:
                self.assertEqual(archive.read("aware_agent_cli/templates/agent-fs-v1/" + relative), (source / relative).read_bytes())

    def test_preparation_sources_and_wheels_match_without_new_domain_engine(self):
        provenance = json.loads(self.files["source-provenance.json"])
        for path, expected in provenance["public_authored_preparation"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)
            self.assertEqual((ROOT / path).read_bytes(), self.files[path])
        for name in ["aware-repository-sdk", "aware-repository-fs-adapter"]:
            module = name.replace("-", "_")
            source = (ROOT / "source" / module / module / "__init__.py").read_bytes()
            with zipfile.ZipFile(io.BytesIO(self.wheels[name][1])) as archive:
                self.assertEqual(source, archive.read(module + "/__init__.py"))
        self.assertEqual(self.release["preparation_operation"], "repository_sdk.prepare_repository")


if __name__ == "__main__":
    unittest.main()
