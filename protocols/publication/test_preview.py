"""Public-byte and acquisition-wrapper proofs, not substitute domain evaluation."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import tarfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("preview_install", ROOT / "protocols/install.py")
assert SPEC and SPEC.loader
INSTALL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALL)


def synthetic_archive(items: list[tuple[str, bytes, bytes]]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data, kind in items:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(data) if kind == tarfile.REGTYPE else 0
            if kind == tarfile.SYMTYPE:
                info.linkname = "/outside"
            archive.addfile(info, io.BytesIO(data) if info.isfile() else None)
    return output.getvalue()


class PreviewTests(unittest.TestCase):
    def readme_fixture(self, root):
        receipt = json.loads((ROOT / "protocols/publication/receipt.json").read_bytes())
        names = set(receipt["outputs"]) | {
            "protocols/install.py", "protocols/publication/export_preview.py",
            "protocols/publication/source_layout.py", "protocols/publication/source-layout.json",
            "protocols/publication/README.md.in", "protocols/publication/receipt.json",
        }
        for name in names:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        return receipt

    def test_readme_only_refresh_preserves_all_other_outputs(self):
        with tempfile.TemporaryDirectory(prefix="aware-readme-projection-") as raw:
            root = Path(raw)
            receipt = self.readme_fixture(root)
            template = root / "protocols/publication/README.md.in"
            template.write_bytes(template.read_bytes() + b"\nTest-only projection marker.\n")
            before = {name: (root / name).read_bytes() for name in receipt["outputs"] if name != "README.md"}
            subprocess.run([sys.executable, "-B", str(root / "protocols/publication/export_preview.py"),
                            "--envelope", str(root / "protocols/distributions" / INSTALL.ARCHIVE),
                            "--refresh-readme-only"], check=True, capture_output=True)
            self.assertEqual((root / "README.md").read_bytes(), template.read_bytes())
            self.assertEqual(before, {name: (root / name).read_bytes() for name in before})
            updated = json.loads((root / "protocols/publication/receipt.json").read_bytes())
            self.assertEqual({name: row for name, row in receipt["outputs"].items() if name != "README.md"},
                             {name: row for name, row in updated["outputs"].items() if name != "README.md"})

    def test_readme_only_refresh_refuses_drift_before_any_write(self):
        with tempfile.TemporaryDirectory(prefix="aware-readme-refusal-") as raw:
            root = Path(raw)
            receipt = self.readme_fixture(root)
            name = next(name for name in receipt["outputs"] if name != "README.md" and name.endswith(".py"))
            (root / name).write_bytes(b"Test-only unexpected source bytes.\n")
            before = {name: (root / name).read_bytes() for name in receipt["outputs"]}
            old_receipt = (root / "protocols/publication/receipt.json").read_bytes()
            result = subprocess.run([sys.executable, "-B", str(root / "protocols/publication/export_preview.py"),
                                     "--envelope", str(root / "protocols/distributions" / INSTALL.ARCHIVE),
                                     "--refresh-readme-only"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("readme_refresh_other_output_mismatch", result.stderr)
            self.assertEqual(before, {name: (root / name).read_bytes() for name in before})
            self.assertEqual(old_receipt, (root / "protocols/publication/receipt.json").read_bytes())

    def test_public_bootstrap_is_explicitly_aligned_with_selected_contract(self):
        release = json.loads((ROOT / "protocols/agent/release.json").read_bytes())
        bootstrap = json.loads((ROOT / ".aware/agent-bootstrap.json").read_bytes())
        self.assertEqual(release["agent_contract"], {"ref": bootstrap["contract_ref"], "version": bootstrap["version"]})
        source = ROOT / ("protocols/contracts/agent-fs/v" + bootstrap["version"])
        authored = json.loads((source / "contract.json").read_bytes())
        for name, relative in authored["files"].items():
            self.assertEqual(hashlib.sha256((source / relative).read_bytes()).hexdigest(), bootstrap["template_sha256"][name])
        for name, digest in bootstrap["rendered_sha256"].items():
            if name == "docs/alignment/CURRENT.md":
                self.assertEqual(digest, hashlib.sha256((source / "docs/alignment/CURRENT.md").read_bytes()).hexdigest())
                self.assertIn("approved authored amendment", (ROOT / name).read_text())
            else:
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)

    def test_exact_outer_and_nested_checksums(self):
        _, files = INSTALL.verified_archive(
            (ROOT / "protocols/distributions" / INSTALL.ARCHIVE).read_bytes(), INSTALL.ENVELOPE_SHA256)
        self.assertEqual(len(files), 76)
        _, source = INSTALL.verified_archive(files["sources/aware-goal-fs-source-capsule-v2.tar.gz"],
                                              INSTALL.SOURCE_SHA256)
        self.assertEqual(len(source), 104)
        _, payload = INSTALL.verified_archive(files["payload/aware-goal-native-fs-v2-linux_x86_64-py312.tar.gz"],
                                               INSTALL.PAYLOAD_SHA256)
        wheels = {name: data for name, data in payload.items() if name.endswith(".whl")}
        self.assertEqual(len(wheels), 13)
        self.assertEqual(sum(name.startswith("wheelhouse/aware_") for name in wheels), 7)
        for name, content in wheels.items():
            with zipfile.ZipFile(io.BytesIO(content)) as wheel:
                self.assertFalse(any("benchmarks" in part.split("/") for part in wheel.namelist()))
                self.assertFalse(any(part.endswith("direct_url.json") for part in wheel.namelist()))

    def test_publication_receipt_matches_outputs_and_generator(self):
        self.assertEqual(
            (ROOT / "README.md").read_bytes(),
            (ROOT / "protocols/publication/README.md.in").read_bytes(),
            "README template drift would revert the selected consumer instructions",
        )
        receipt = json.loads((ROOT / "protocols/publication/receipt.json").read_text())
        self.assertEqual(len(receipt["outputs"]), 106)
        for name, record in receipt["outputs"].items():
            data = (ROOT / name).read_bytes()
            self.assertEqual(len(data), record["bytes"], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"], name)
        generator = (ROOT / receipt["generator"]).read_bytes()
        self.assertEqual(hashlib.sha256(generator).hexdigest(), receipt["generator_sha256"])

    def test_source_capsule_is_exact_public_source(self):
        manifest = json.loads((ROOT / "protocols/publication/goal-source-capsule/manifest.json").read_text())
        self.assertEqual(len(manifest["aware_wheel_source"]), 70)
        for record in manifest["aware_wheel_source"]:
            path = ROOT / record["source_path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])

    def test_digest_tampering_refused(self):
        with self.assertRaisesRegex(ValueError, "archive_digest_mismatch"):
            INSTALL.verified_archive(b"wrong", INSTALL.ENVELOPE_SHA256)

    def test_traversal_refused(self):
        data = synthetic_archive([("root/../escape", b"x", tarfile.REGTYPE)])
        with self.assertRaisesRegex(ValueError, "unsafe_archive_path"):
            INSTALL.verified_archive(data, hashlib.sha256(data).hexdigest())

    def test_absolute_path_refused(self):
        data = synthetic_archive([("/absolute", b"x", tarfile.REGTYPE)])
        with self.assertRaisesRegex(ValueError, "unsafe_archive_path"):
            INSTALL.verified_archive(data, hashlib.sha256(data).hexdigest())

    def test_duplicate_member_refused(self):
        data = synthetic_archive([("root/a", b"x", tarfile.REGTYPE), ("root/a", b"x", tarfile.REGTYPE)])
        with self.assertRaisesRegex(ValueError, "duplicate_archive_member"):
            INSTALL.verified_archive(data, hashlib.sha256(data).hexdigest())

    def test_link_refused(self):
        data = synthetic_archive([("root/link", b"", tarfile.SYMTYPE)])
        with self.assertRaisesRegex(ValueError, "unsupported_or_duplicate"):
            INSTALL.verified_archive(data, hashlib.sha256(data).hexdigest())

    def test_multiple_roots_refused(self):
        data = synthetic_archive([("root/a", b"a", tarfile.REGTYPE), ("other/b", b"b", tarfile.REGTYPE)])
        with self.assertRaisesRegex(ValueError, "single_root"):
            INSTALL.verified_archive(data, hashlib.sha256(data).hexdigest())

    def test_missing_checksum_coverage_refused(self):
        data = synthetic_archive([("root/a", b"a", tarfile.REGTYPE),
                                  ("root/SHA256SUMS", b"", tarfile.REGTYPE)])
        with self.assertRaisesRegex(ValueError, "incomplete_checksum_coverage"):
            INSTALL.verified_archive(data, hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
