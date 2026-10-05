"""Public-byte and acquisition-wrapper proofs, not substitute domain evaluation."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
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
        receipt = json.loads((ROOT / "protocols/publication/receipt.json").read_text())
        self.assertEqual(len(receipt["outputs"]), 107)
        for name, record in receipt["outputs"].items():
            data = (ROOT / name).read_bytes()
            self.assertEqual(len(data), record["bytes"], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"], name)
        generator = (ROOT / receipt["generator"]).read_bytes()
        self.assertEqual(hashlib.sha256(generator).hexdigest(), receipt["generator_sha256"])

    def test_source_capsule_is_exact_public_source(self):
        manifest = json.loads((ROOT / "protocols/source/manifest.json").read_text())
        self.assertEqual(len(manifest["aware_wheel_source"]), 70)
        for record in manifest["aware_wheel_source"]:
            path = ROOT / "protocols/source/source/aware" / record["source_path"]
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
