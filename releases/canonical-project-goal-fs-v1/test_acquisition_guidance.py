"""Acquisition routing, exact wrapper pins, history and retained installation reads."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_ACQUISITION_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-project-goal-fs-v1"
BASELINE = "55de18317dcb77ed879b36aaeed43691ce4d3342"
SOFTWARE = "704b5943931fcac23bcc748a574e112d20884017"
WRAPPER_SHA = "3d6da7b29caf09f83a795f85fc05126192b6eeb12d957d7224429b945b58376d"
CURRENT = {
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/workspace/RESOURCE-RELEASES.md",
    "protocols/issues/README.md",
    "protocols/issues/OBSERVATION-INPUT.md",
    "protocols/workspace/ACTION-OBSERVATION.md",
    "protocols/EXISTING-REPOSITORY.md",
    "protocols/PROJECT-GOAL.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-project-goal-fs-v1/README.md",
    "protocols/specification/README.md",
    "protocols/FIRST-USEFUL-TASK.md",
}
ISSUE = "docs/issues/2026/10/20/fb-2026-10-20-project-goal-acquisition-guidance-v0.md"
SCOPE = CURRENT | {
    ISSUE,
    "releases/SELECTED.json",
    *[
        "releases/canonical-project-goal-fs-v1/" + name
        for name in (
            "ACQUISITION-INSTRUCTIONS.json",
            "ACQUISITION-STATUS.md",
            "test_acquisition_guidance.py",
        )
    ],
}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def prior():
    path = RELEASE / "test_public_status.py"
    if (
        hashlib.sha256(path.read_bytes()).hexdigest()
        != "24337168c0c60197f71bce8976e4155d3dcffbd5a10da16285137dbd317d6180"
    ):
        raise ValueError("original_status_receiver_required")
    spec = importlib.util.spec_from_file_location("acquisition_original_status", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_current(body):
    if (
        "For a fresh installation, acquire corrected revision `" + BASELINE + "`"
        not in body
    ):
        raise ValueError("corrected_acquisition_revision_required")
    if (
        "`"
        + SOFTWARE
        + "`; that is historical software provenance, not a fresh-install target."
        not in body
    ):
        raise ValueError("separate_software_provenance_required")
    if (
        "Acquire that exact revision" in body
        or "Acquire exact revision `" + SOFTWARE in body
    ):
        raise ValueError("broken_acquisition_instruction")


class AcquisitionGuidance(unittest.TestCase):
    def test_exact_successor_pins_and_original_negative_controls(self):
        before = json.loads((RELEASE / "PUBLIC-INSTRUCTIONS.json").read_bytes())
        record = json.loads((RELEASE / "ACQUISITION-INSTRUCTIONS.json").read_bytes())
        self.assertEqual(
            set(record["files"]), set(before["files"]) | {"protocols/install.py"}
        )
        self.assertEqual(len(record["files"]), 25)
        bodies = {n: (ROOT / n).read_bytes() for n in record["files"]}
        helper = prior().freeze().original().helper()
        helper.INSTRUCTIONS = set(before["files"]) | {"protocols/install.py"}
        helper.verify_instructions(record["files"], bodies)
        bodies["protocols/install.py"] += b"\n"
        with self.assertRaisesRegex(ValueError, "instruction_bytes_changed"):
            helper.verify_instructions(record["files"], bodies)
        bodies.pop("protocols/install.py")
        with self.assertRaisesRegex(ValueError, "exact_instruction_set_required"):
            helper.verify_instructions(record["files"], bodies)
        self.assertEqual(record["files"]["protocols/install.py"]["sha256"], WRAPPER_SHA)

    def test_no_current_acquisition_points_back_to_broken_installer(self):
        for name in CURRENT:
            body = (ROOT / name).read_text()
            verify_current(body)
            for changed in (
                body.replace(BASELINE, SOFTWARE),
                body + "\nAcquire that exact revision.\n",
                body.replace(
                    "historical software provenance", "fresh installation proof"
                ),
            ):
                with self.assertRaises(ValueError):
                    verify_current(changed)
        task = (ROOT / "protocols/FIRST-USEFUL-TASK.md").read_text()
        for suffix in (
            "README.md",
            "protocols/INIT.md",
            "releases/canonical-project-goal-fs-v1/README.md",
        ):
            self.assertNotIn(
                "https://github.com/aware-network/aware/blob/"
                + SOFTWARE
                + "/"
                + suffix,
                task,
            )
        self.assertIn(
            "../README.md#acquire-and-install-the-exact-delivered-revision", task
        )

    def test_exact_scope_conservation_and_modes(self):
        baseline = {}
        for row in git("ls-tree", "-rz", BASELINE).split(b"\0"):
            if not row:
                continue
            meta, name = row.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            self.assertEqual(kind, "blob")
            baseline[name.decode()] = (mode, oid)
        actual = {
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(ROOT).parts
        }
        self.assertEqual(actual, set(baseline) | SCOPE)
        changed = actual - set(baseline)
        for name, (mode, oid) in baseline.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(bool(path.stat().st_mode & 0o111), mode == "100755", name)
            before = git("cat-file", "blob", oid)
            if path.read_bytes() != before:
                changed.add(name)
            if name not in SCOPE:
                self.assertEqual(path.read_bytes(), before, name)
        self.assertEqual(changed, SCOPE)
        self.assertEqual(
            (len(baseline), len(actual), len(set(baseline) - SCOPE)), (2311, 2315, 2293)
        )
        section = (
            (ROOT / ISSUE)
            .read_text()
            .split("## Ownership Scope", 1)[1]
            .split("##", 1)[0]
        )
        self.assertEqual(
            set(re.findall(r"^- `([^`]+)`$", section, re.MULTILINE)), SCOPE
        )

    def test_pointer_and_record_separate_acquisition_from_software(self):
        current = json.loads((ROOT / "releases/SELECTED.json").read_bytes())
        before = json.loads(git("show", BASELINE + ":releases/SELECTED.json"))
        record = json.loads((RELEASE / "ACQUISITION-INSTRUCTIONS.json").read_bytes())
        for data in (current, record):
            self.assertEqual(data["acquisition_revision"], BASELINE)
            self.assertEqual(data["installer_correction_revision"], BASELINE)
            self.assertEqual(data["published_software_revision"], SOFTWARE)
            self.assertFalse(data["instruction_alignment_publication_authorized"])
            self.assertTrue(data["whole_envelope_required"])
        self.assertEqual(current["published_revision"], BASELINE)
        self.assertEqual(
            current["instruction_record"],
            "canonical-project-goal-fs-v1/ACQUISITION-INSTRUCTIONS.json",
        )
        for key in (
            "published_revision",
            "published_software_revision",
            "installer_correction_revision",
            "acquisition_revision",
            "instruction_record",
            "instruction_status",
            "instruction_alignment_publication_authorized",
        ):
            current.pop(key, None)
            before.pop(key, None)
        self.assertEqual(current, before)
        self.assertNotIn("packages", current)

    def test_unchanged_commands_wrapper_and_historical_records(self):
        for name in CURRENT | {"protocols/install.py"}:
            before = git("show", BASELINE + ":" + name)
            after = (ROOT / name).read_bytes()
            blocks = lambda b: re.findall(
                rb"```(?:sh|bash|python)\n(.*?)```", b, re.DOTALL
            )
            self.assertEqual(blocks(after), blocks(before), name)
        for name in (
            "INSTRUCTIONS.json",
            "PUBLIC-INSTRUCTIONS.json",
            "INSTRUCTION-FREEZE.md",
            "PUBLIC-STATUS.md",
            "INSTALLER-CORRECTION.md",
            "test_public_status.py",
            "test_instruction_freeze.py",
            "test_public_installer.py",
        ):
            self.assertEqual(
                (RELEASE / name).read_bytes(),
                git(
                    "show", BASELINE + ":releases/canonical-project-goal-fs-v1/" + name
                ),
            )
        self.assertEqual(
            hashlib.sha256((ROOT / "protocols/install.py").read_bytes()).hexdigest(),
            WRAPPER_SHA,
        )

    def test_local_links_and_shell_syntax(self):
        helper = prior().freeze().original().helper()
        for name in CURRENT | {
            "releases/canonical-project-goal-fs-v1/ACQUISITION-STATUS.md"
        }:
            path = ROOT / name
            body = path.read_text()
            for link in re.findall(r"\]\(([^)]+)\)", body):
                helper.verify_local_link(path, link)
            for language, block in re.findall(
                r"```(sh|bash)\n(.*?)```", body, re.DOTALL
            ):
                run = subprocess.run(
                    ["/bin/" + language, "-n"],
                    input=block.encode(),
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(run.returncode, 0, run.stderr)

    def test_frozen_blocker_and_capability_limits_remain_explicit(self):
        note = (RELEASE / "ACQUISITION-STATUS.md").read_text()
        for phrase in (
            "not a fresh-install target",
            "all predecessor releases stay unchanged",
            "U/V/R/ProjectGoalU remain unrun",
            "nine legal gaps",
            "thirteen findings",
            "not work authority",
            "no automatic retry",
            "separate exact-range publication authorization",
        ):
            self.assertIn(phrase, note)
        goal = " ".join((ROOT / "protocols/PROJECT-GOAL.md").read_text().split())
        for phrase in (
            "not work authority",
            "not a clean matrix PASS",
            "not a clean single 34-case replay",
        ):
            self.assertIn(phrase, goal)

    def test_retained_corrected_environment_readonly(self):
        proof = Path(
            os.environ.get(
                "AWARE_CORRECTED_INSTALL_PROOF_ROOT",
                "/tmp/aware-project-goal-layout.12MwymXH/installer-correction/installed-proof",
            )
        )
        self.assertTrue((proof / "environment/bin/python").exists())
        code = "import importlib.metadata as m,json,subprocess; d={x.metadata['Name']:x.version for x in m.distributions()}; assert len(d)==50 and d['aware-agent-cli']=='0.2.0a16' and d['aware-issue-cli']=='0.8.4'; p=subprocess.run(['/tmp/proof/environment/bin/python','-I','-B','-m','pip','check'],capture_output=True,text=True); assert p.returncode==0,p.stderr; h=subprocess.run(['/tmp/proof/environment/bin/aware','init','--help'],capture_output=True,text=True); assert h.returncode==0,h.stderr; print(json.dumps({'payload_distributions':49,'pip_separate':True,'pip_check':p.stdout.strip(),'init_help_exit':h.returncode}))"
        run = subprocess.run(
            [
                "bwrap",
                "--die-with-parent",
                "--unshare-net",
                "--ro-bind",
                "/",
                "/",
                "--tmpfs",
                "/home",
                "--tmpfs",
                "/root",
                "--tmpfs",
                "/tmp",
                "--ro-bind",
                str(proof),
                "/tmp/proof",
                "--dev",
                "/dev",
                "--proc",
                "/proc",
                "--clearenv",
                "--setenv",
                "PATH",
                "/usr/bin:/bin",
                "--chdir",
                "/tmp/proof",
                "--",
                "/tmp/proof/environment/bin/python",
                "-I",
                "-B",
                "-c",
                code,
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["payload_distributions"], 49)


if __name__ == "__main__":
    unittest.main()
