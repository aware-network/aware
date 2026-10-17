"""Status-only checks reuse retained installed inputs; never build or install."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_STATUS_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-refusal-successor-fs-v1"
BASELINE = "afa2d7116a296b5585ed7acac158eede2c447d5b"
HISTORICAL_SHA = "89ea44d36f24126622aa2e338ec5a29dc69ef4036984f7e3bb2b88e275949f8b"
FREEZE_TEST_SHA = "2f1bf0f10ad8dbb0c108cabe449b367d653a336960ca50abd0ae33aabe72b271"
SCOPE = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/specification/README.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    "releases/canonical-refusal-successor-fs-v1/README.md",
    "releases/canonical-refusal-successor-fs-v1/PUBLIC-INSTRUCTIONS.json",
    "releases/canonical-refusal-successor-fs-v1/PUBLIC-STATUS.md",
    "releases/canonical-refusal-successor-fs-v1/test_public_status.py",
    "docs/issues/2026/10/18/fb-2026-10-18-canonical-refusal-successor-public-status-v0.md",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def accepted_freeze():
    path = RELEASE / "test_instruction_freeze.py"
    if sha(path.read_bytes()) != FREEZE_TEST_SHA:
        raise ValueError("accepted_freeze_proof_changed")
    spec = importlib.util.spec_from_file_location("accepted_draft_freeze", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def successor_record():
    """Print-only pin derivation; never writes instructions or selects packages."""
    historical = (RELEASE / "INSTRUCTIONS.json").read_bytes()
    if sha(historical) != HISTORICAL_SHA:
        raise ValueError("historical_instruction_record_changed")
    record = json.loads(historical)
    record.update(
        status="status_alignment_review_pending",
        baseline_revision=BASELINE,
        published_software_revision=BASELINE,
        historical_instruction_sha256=HISTORICAL_SHA,
        public_delivery_authorized=True,
        instruction_alignment_publication_authorized=False,
    )
    record["files"] = {
        name: {"bytes": len(body), "sha256": sha(body)}
        for name, body in (
            (name, (ROOT / name).read_bytes()) for name in record["files"]
        )
    }
    return record


def verify_delivery_status(text):
    normalized = " ".join(text.lower().split())
    if BASELINE not in text:
        raise ValueError("published_revision_missing")
    for stale in (
        "public delivery is not yet authorized",
        "public delivery remains unauthorized",
        "not yet publicly delivered",
        "prepared successor is unselected",
        "prepared, unselected successor",
        "prepared refusal successor is unselected",
        "prepared, unselected refusal successor",
        "instructions remain draft",
        "pending independent freeze review",
        "local freeze remains pending independent review",
        "not publicly delivered",
        "unchanged public main",
        "frozen locally pending independent",
        "frozen locally, pending independent",
        "locally frozen instructions, pending independent",
        "this local status alignment remains unpublished",
        "this local status/instruction alignment remains unpublished",
    ):
        if stale in normalized:
            raise ValueError("stale_delivery_status:" + stale)


class PublicStatus(unittest.TestCase):
    def test_historical_record_and_exact_successor_pins(self):
        self.assertEqual(
            (RELEASE / "INSTRUCTIONS.json").read_bytes(),
            git(
                "show",
                BASELINE
                + ":releases/canonical-refusal-successor-fs-v1/INSTRUCTIONS.json",
            ),
        )
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(record, successor_record())
        freeze = accepted_freeze()
        bodies = {name: (ROOT / name).read_bytes() for name in record["files"]}
        freeze.helper().verify_instructions(record["files"], bodies)
        bodies["README.md"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            freeze.helper().verify_instructions(record["files"], bodies)

    def test_exact_scope_unaffected_bytes_and_modes(self):
        baseline = {}
        for line in git("ls-tree", "-r", BASELINE).decode().splitlines():
            meta, name = line.split("\t")
            mode, kind, oid = meta.split()
            self.assertEqual(kind, "blob")
            baseline[name] = (mode, oid)
        actual = {
            str(path.relative_to(ROOT))
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(ROOT).parts
        }
        self.assertEqual(actual, set(baseline) | SCOPE)
        changed = actual - set(baseline)
        for name, (mode, oid) in baseline.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            original = git("cat-file", "blob", oid)
            if path.read_bytes() != original:
                changed.add(name)
            if name not in SCOPE:
                self.assertEqual(path.read_bytes(), original, name)
        self.assertEqual(changed, SCOPE)
        self.assertEqual(len(baseline), 1638)
        self.assertEqual(len(actual), 1642)
        self.assertEqual(len(set(baseline) - SCOPE), 1629)

    def test_unchanged_candidate_carriage_and_sole_selector(self):
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        self.assertEqual(current["published_revision"], BASELINE)
        self.assertTrue(current["public_delivery_authorized"])
        self.assertFalse(current["instruction_alignment_publication_authorized"])
        self.assertEqual(
            current["instruction_status"], "status_alignment_review_pending"
        )
        self.assertEqual(
            current["instruction_record"],
            "canonical-refusal-successor-fs-v1/PUBLIC-INSTRUCTIONS.json",
        )
        for key in (
            "selection_kind",
            "instruction_status",
            "instruction_record",
            "public_delivery_authorized",
            "published_revision",
            "instruction_alignment_publication_authorized",
        ):
            current.pop(key, None)
            before.pop(key, None)
        self.assertEqual(current, before)
        self.assertEqual(current["canonical_profile"], "portable_protocols")
        self.assertFalse(current["detached_wheels_accepted"])
        self.assertFalse(current["contributor_selection_changed"])
        self.assertFalse(current["unassisted_onboarding_proven"])
        self.assertTrue(current["workspace_agent_mount_admitted"])
        self.assertEqual(
            current["workspace_mount_profile"],
            "bounded-reviewed-repository-manifest-a1",
        )
        self.assertTrue(current["init_supplies_configuration_not_admission"])
        self.assertFalse(current["a2_admitted"])
        self.assertFalse(current["tree_completion_admitted"])
        self.assertNotIn("packages", current)
        freeze = accepted_freeze()
        freeze.helper().original_test().Integration.test_whole_envelope_and_unsuppressed_findings(
            self
        )

    def test_operation_blocks_and_example_are_unchanged(self):
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        for name in record["files"]:
            before = git("show", BASELINE + ":" + name)
            current = (ROOT / name).read_bytes()
            if name.endswith(".py"):
                self.assertEqual(current, before, name)
            else:
                blocks = lambda body: re.findall(
                    rb"```(?:sh|bash|python)\n(.*?)```", body, re.DOTALL
                )
                self.assertEqual(blocks(current), blocks(before), name)
        workflow = (ROOT / "protocols/WORKFLOW.md").read_text()
        for phrase in (
            "prospective_only",
            "completion_verified=false",
            "fresh Protocol admission",
            "absolute input paths",
            "never silent guard refresh",
            "not an atomic transaction",
            "live publication capability",
            "no draft-input custody",
            "preserve every remaining argument and reviewed guard",
            "no subsequent Issue/input observation",
            "not Issue eligibility",
            "docs/specs/json-checker/aware.spec.toml",
            "docs/specs/aware.spec.toml",
        ):
            self.assertIn(phrase, " ".join(workflow.split()))
        self.assertIn("unassisted", (ROOT / "README.md").read_text())
        workspace = (ROOT / "protocols/workspace/REVIEWED-SETUP.md").read_text()
        for phrase in (
            "--accept-reviewed-effect-scope",
            "--accept-reviewed-final-files",
            "Init supplies the Protocol configuration",
            "without another configuration step",
            "release uncertainty remains unknown",
        ):
            self.assertIn(phrase, " ".join(workspace.split()))
        marker = "## Inputs and configuration"
        self.assertEqual(
            workspace.split(marker, 1)[1],
            git("show", BASELINE + ":protocols/workspace/REVIEWED-SETUP.md")
            .decode()
            .split(marker, 1)[1],
        )
        self.assertEqual(
            (ROOT / "protocols/issues/FIRST-ISSUE.md").read_bytes(),
            git("show", BASELINE + ":protocols/issues/FIRST-ISSUE.md"),
        )

    def test_status_matches_observed_delivery_without_new_authority(self):
        for name in (
            "README.md",
            "protocols/WORKFLOW.md",
            "protocols/specification/README.md",
            "protocols/workspace/README.md",
            "protocols/workspace/REVIEWED-SETUP.md",
            "docs/alignment/CURRENT.md",
            "releases/README.md",
            "releases/canonical-refusal-successor-fs-v1/README.md",
        ):
            text = (ROOT / name).read_text()
            verify_delivery_status(text)
            original = git("show", BASELINE + ":" + name).decode()
            with self.assertRaisesRegex(ValueError, "stale_delivery_status"):
                verify_delivery_status(original + "\n" + BASELINE)
            with self.assertRaisesRegex(ValueError, "published_revision_missing"):
                verify_delivery_status(text.replace(BASELINE, "unknown_revision"))
            for stale in (
                "Public delivery is not yet authorized.",
                "Not publicly delivered.",
                "Use unchanged public main.",
                "Frozen locally, pending independent review.",
                "Locally frozen instructions, pending independent review.",
                "This local status alignment remains unpublished.",
                "This local status/instruction alignment remains unpublished.",
            ):
                with (
                    self.subTest(name=name, stale=stale),
                    self.assertRaisesRegex(ValueError, "stale_delivery_status"),
                ):
                    verify_delivery_status(text + "\n" + stale)
        record = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        self.assertFalse(record["instruction_alignment_publication_authorized"])
        self.assertFalse(record["unassisted_onboarding_proven"])
        ledger = (RELEASE / "PUBLIC-STATUS.md").read_text()
        self.assertIn("independent status-alignment review remains next", ledger)
        self.assertIn("No additional public push or U/V/R execution", ledger)
        self.assertIn("Whole-envelope delivery remains required", ledger)
        self.assertIn("not a live remote-status assertion", ledger)
        self.assertIn("not live remote state or", ledger)

    def test_links_fragments_and_shell_syntax(self):
        freeze = accepted_freeze()
        freeze.Instructions.test_local_links_and_install_blocks_are_valid(self)
        for name in (
            "docs/alignment/CURRENT.md",
            "releases/canonical-refusal-successor-fs-v1/PUBLIC-STATUS.md",
        ):
            source = ROOT / name
            for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                freeze.helper().verify_local_link(source, link)

    def test_original_executable_install_guards(self):
        accepted_freeze().Instructions.test_documented_install_guards_refuse_existing_targets(
            self
        )

    def test_retained_installation_and_thirteen_help_entrances(self):
        """Use only the explicit held installation, never the installer helper."""
        retained = Path(os.environ["AWARE_STATUS_RETAINED_INSTALL_ROOT"])
        scratch = Path(os.environ["AWARE_STATUS_PROOF_ROOT"])
        self.assertTrue(retained.is_dir() and not retained.is_symlink())
        self.assertTrue(scratch.is_dir() and not scratch.is_symlink())
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        self.assertNotEqual(retained.resolve(), scratch.resolve())
        receipt_body = (retained / "installed-receipt.json").read_bytes()
        self.assertEqual(
            sha(receipt_body),
            "b0acd9efb420491a3bace24623a2a2cfa2f3a1d6bb1ea80e8dc1d4a4ae014806",
        )
        receipt = json.loads(receipt_body)
        self.assertEqual(
            receipt["installation"]["packet_sha256"], accepted_freeze().ENVELOPE_SHA
        )
        self.assertEqual(
            receipt["installation"]["payload_sha256"], accepted_freeze().PAYLOAD_SHA
        )
        source = Path(receipt["installation"]["retained_source_and_notices"]) / "source"
        self.assertTrue(source.is_relative_to(retained))
        prefix = [
            "/usr/bin/bwrap",
            "--die-with-parent",
            "--unshare-net",
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--tmpfs",
            "/home",
            "--tmpfs",
            "/root",
            "--tmpfs",
            "/tmp",
            "--ro-bind",
            str(retained),
            str(retained),
            "--bind",
            str(scratch),
            str(scratch),
            "--ro-bind",
            str(ROOT),
            "/mnt",
            "--tmpfs",
            "/mnt/workspaces",
            "--tmpfs",
            str(source),
            "--clearenv",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--setenv",
            "TMPDIR",
            str(scratch),
            "--setenv",
            "PYTHONDONTWRITEBYTECODE",
            "1",
            "--chdir",
            str(scratch),
            "--",
        ]
        commands = []

        def run(arguments):
            result = subprocess.run(
                prefix + arguments,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            commands.append(
                {
                    "argv": arguments,
                    "exit": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            (scratch / "retained-commands.json").write_text(
                json.dumps(commands, indent=2) + "\n"
            )
            self.assertEqual(
                result.returncode, 0, (arguments, result.stdout, result.stderr)
            )
            return result

        python = str(retained / "env/bin/python")
        aware = str(retained / "env/bin/aware")
        metadata = run(
            [
                python,
                "-I",
                "-B",
                "-c",
                (
                    "import importlib.metadata as m,json; "
                    "ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; "
                    "assert not any(d.read_text('direct_url.json') for d in ds); "
                    "print(json.dumps({d.metadata['Name']:d.version for d in ds}))"
                ),
            ]
        )
        versions = json.loads(metadata.stdout)
        self.assertEqual(versions, receipt["versions"])
        self.assertEqual(len(versions), 42)
        run([python, "-I", "-B", "-m", "pip", "check"])
        operations = [
            ("init",),
            ("issue", "ensure-snapshot"),
            ("issue", "bind-scope"),
            ("issue", "start-progress"),
            ("issue", "publish-close"),
            ("protocol", "admit"),
            ("protocol", "setup-specification"),
            ("spec", "observe"),
            ("spec", "create-draft"),
            ("spec", "prepare-draft"),
            ("spec", "present-receipt"),
            ("workspace", "review"),
            ("workspace", "review", "apply"),
        ]
        for operation in operations:
            run([aware, *operation, "--help"])
        (scratch / "retained-smoke.json").write_text(
            json.dumps(
                {
                    "packages": len(versions),
                    "dependency_check": "passed",
                    "editable_or_direct_url": False,
                    "help_entrances": len(operations),
                    "command_captures": len(commands),
                    "historical_install_receipt_sha256": sha(receipt_body),
                    "retained_installation": str(retained),
                    "retained_mount_read_only": True,
                    "fresh_installation": False,
                    "installer_invoked": False,
                    "workflow_or_customer_operation": False,
                    "build_or_clone_created": False,
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    if "--print-instruction-record" in sys.argv:
        print(json.dumps(successor_record(), indent=2) + "\n", end="")
    else:
        unittest.main()
