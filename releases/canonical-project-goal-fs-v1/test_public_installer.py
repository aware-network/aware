"""Actual envelope lookup regressions; stop before retention or installation."""

import hashlib
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(
    os.environ.get("AWARE_INSTALLER_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-project-goal-fs-v1"
ENVELOPE_SHA = "edaab985f57541928effb038c825fa3af6ec6afbffda45249099a64bf1120898"
PAYLOAD_SHA = "f5b5062aeefec2db2ce660e533342ef9b0df59b9ef7a1b02661d467239da4522"
OLD = b'"payload/aware-canonical-neutral-fs-internal-v1.tar.gz"'
NEW = b'"payload/aware-canonical-project-goal-fs-internal-v1.tar.gz"'
BEFORE_SHA = "292d46aec43dd421662b211304755f9354296ef583a02354274c9a77efc24c04"


class BeforeRetention(RuntimeError):
    pass


def wrapper(body=None):
    path = ROOT / "protocols/install.py"
    module = types.ModuleType("public_installer_regression")
    module.__file__ = str(path)
    source = path.read_bytes() if body is None else body
    if hashlib.sha256(source.replace(NEW, OLD)).hexdigest() != BEFORE_SHA:
        raise ValueError("exact_original_or_corrected_installer_required")
    exec(  # noqa: S102 -- exact pinned original or single-coordinate correction only
        compile(source, str(path), "exec"),
        module.__dict__,
    )
    return module


def verifier():
    path = RELEASE / "archive_verifier.py"
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9"
    )
    spec = importlib.util.spec_from_file_location("public_archive_regression", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actual_outer():
    return verifier().verified_archive(
        (
            RELEASE / "canonical-project-goal-source-notice-review-v1.tar.gz"
        ).read_bytes(),
        ENVELOPE_SHA,
    )


class PublicInstaller(unittest.TestCase):
    def invoke_before_retention(self, module, expected):
        target = ROOT / "__installer_regression_target_must_stay_absent__"
        self.assertFalse(target.exists() or target.is_symlink())
        with (
            patch.object(module.subprocess, "check_output", return_value="3.12\n"),
            patch.object(
                sys,
                "argv",
                [
                    "install.py",
                    "--python-executable",
                    "/usr/bin/python3.12",
                    "--venv",
                    str(target),
                ],
            ),
            patch.object(
                module.tempfile, "mkdtemp", side_effect=BeforeRetention
            ) as retention,
            patch.object(
                module.subprocess,
                "run",
                side_effect=AssertionError("installer_must_not_dispatch_in_regression"),
            ) as dispatch,
            self.assertRaises(expected),
        ):
            module.main()
        self.assertEqual(retention.call_count, int(expected is BeforeRetention))
        dispatch.assert_not_called()
        self.assertFalse(target.exists() or target.is_symlink())

    def test_actual_outer_and_inner_validation_reach_retention_boundary(self):
        self.invoke_before_retention(wrapper(), BeforeRetention)

    def test_original_wrong_member_reproduces_keyerror_before_retention(self):
        body = (ROOT / "protocols/install.py").read_bytes()
        self.assertEqual(body.count(NEW), 1)
        self.invoke_before_retention(wrapper(body.replace(NEW, OLD)), KeyError)

    def test_missing_exact_member_has_no_search_or_fallback(self):
        module = wrapper()
        root, outer = actual_outer()
        outer = dict(outer)
        payload = outer.pop(NEW.decode().strip('"'))
        outer[OLD.decode().strip('"')] = payload
        real = module.load_verifier(ROOT / "protocols")
        with (
            patch.object(module, "load_verifier", return_value=real),
            patch.object(real, "verified_archive", return_value=(root, outer)),
        ):
            self.invoke_before_retention(module, KeyError)

    def test_changed_whole_envelope_refuses(self):
        body = (
            RELEASE / "canonical-project-goal-source-notice-review-v1.tar.gz"
        ).read_bytes()
        with self.assertRaisesRegex(ValueError, "archive_digest_mismatch"):
            verifier().verified_archive(body + b"changed", ENVELOPE_SHA)

    def test_changed_inner_payload_refuses(self):
        _, outer = actual_outer()
        with self.assertRaisesRegex(ValueError, "archive_digest_mismatch"):
            verifier().verified_archive(
                outer[NEW.decode().strip('"')] + b"changed", PAYLOAD_SHA
            )

    def test_existing_destination_refuses(self):
        with self.assertRaisesRegex(ValueError, "installation_target_must_be_new"):
            wrapper().new_target(ROOT)

    def test_missing_parent_refuses(self):
        with self.assertRaisesRegex(ValueError, "existing_regular_parent_required"):
            wrapper().new_target(ROOT / "__missing_installer_parent__" / "environment")

    def test_dangling_symlink_destination_refuses(self):
        with tempfile.TemporaryDirectory(prefix="aware-installer-guard-") as directory:
            target = Path(directory) / "target"
            target.symlink_to("missing")
            with self.assertRaisesRegex(ValueError, "installation_target_must_be_new"):
                wrapper().new_target(target)

    def test_only_exact_payload_coordinate_changes(self):
        body = (ROOT / "protocols/install.py").read_bytes()
        self.assertEqual(body.count(NEW), 1)
        self.assertNotIn(OLD, body)
        self.assertEqual(hashlib.sha256(body.replace(NEW, OLD)).hexdigest(), BEFORE_SHA)


if __name__ == "__main__":
    unittest.main()
