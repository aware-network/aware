"""Maintainer integration proof; no new participant runner or domain engine."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-initializer-fs-v1"
BASELINE = "f760ac28066191e50ba12d249928c0fd553f79b4"
LAYOUT_SHA = "31ffd2ea0c41d76a01e7bec728640ba2e18f0e48fd0913d724a01d300b52b2a1"
ENVELOPE_SHA = "5f0edebe568d1cfd8a06a33e6122cd4e0d3dd68f764058b1aa098456cc2df13c"
PAYLOAD_SHA = "2d812c489485ee187cf45fca012fffdfda5fcdf93d60495a02b843f94e4a8b68"
ISSUE = "docs/issues/2026/10/10/fb-2026-10-10-canonical-initializer-public-integration-v0.md"
EXTRAS = {
    ISSUE,
    *[
        "releases/canonical-initializer-fs-v1/" + name
        for name in (
            "LAYOUT-REVIEW.json",
            "INTEGRATION-PLAN.json",
            "LOCAL-INTEGRATION.md",
            "test_local_integration.py",
        )
    ],
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((RELEASE / "LAYOUT-REVIEW.json").read_bytes())
        cls.plan = json.loads((RELEASE / "INTEGRATION-PLAN.json").read_bytes())

    def test_accepted_layout_and_exact_file_set(self):
        self.assertEqual(sha((RELEASE / "LAYOUT-REVIEW.json").read_bytes()), LAYOUT_SHA)
        actual = set()
        for parent, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d != ".git"]
            for name in files:
                path = Path(parent) / name
                self.assertFalse(path.is_symlink())
                actual.add(str(path.relative_to(ROOT)))
        self.assertEqual(actual, set(self.layout["files"]) | EXTRAS)
        self.assertEqual(len(self.layout["files"]), 1086)
        for name, row in self.layout["files"].items():
            path = ROOT / name
            self.assertEqual(sha(path.read_bytes()), row["sha256"], name)
            self.assertEqual(path.stat().st_size, row["bytes"], name)
            self.assertEqual(
                bool(path.stat().st_mode & 0o111),
                bool(int(row["mode"], 8) & 0o111),
                name,
            )

    def test_exact_retirement_and_pinned_history(self):
        self.assertEqual(self.plan["baseline_revision"], BASELINE)
        self.assertEqual(self.plan["layout_sha256"], LAYOUT_SHA)
        self.assertEqual(len(self.plan["changes"]), 5019)
        self.assertEqual(len(self.plan["publication_paths"]), 5024)
        self.assertEqual(len(self.plan["scope_paths"]), 7384)
        baseline = git("ls-tree", "-r", "--name-only", BASELINE).decode().splitlines()
        self.assertEqual(set(baseline), set(self.layout["baseline_dispositions"]))
        for name, row in self.plan["changes"].items():
            if row["after_sha256"] is None:
                self.assertFalse((ROOT / name).exists(), name)
        for name in self.plan["empty_directory_retirement_candidates"]:
            if name in {"docs/issues/2026", "docs/issues/2026/10"}:
                self.assertEqual(
                    {
                        str(p.relative_to(ROOT))
                        for p in (ROOT / name).rglob("*")
                        if p.is_file()
                    },
                    {ISSUE},
                )
            else:
                self.assertFalse((ROOT / name).exists(), name)

    def test_publication_batches_do_not_claim_atomicity(self):
        flat = [p for b in self.plan["publication_batches"] for p in b]
        self.assertEqual(set(flat), set(self.plan["publication_paths"]))
        self.assertEqual(len(flat), len(set(flat)))
        self.assertEqual(flat[0], ISSUE)
        self.assertFalse(self.plan["atomic_publication"])
        self.assertTrue(
            all(
                sum(len(p.encode()) + 2 for p in b) <= 48000
                for b in self.plan["publication_batches"]
            )
        )
        for key in ("instruction_freeze", "public_selection", "push_authorized"):
            self.assertFalse(self.plan[key])

    def test_original_bootstrap_and_contributor_authority(self):
        names = [
            p
            for p in self.layout["baseline_dispositions"]
            if p in {"AGENTS.md", "aware.protocol.toml"}
            or p.startswith(
                (".aware/", "docs/agents/", "protocols/contracts/agent-fs/v1.2.1/")
            )
        ]
        for name in names:
            self.assertEqual(
                (ROOT / name).read_bytes(), git("show", BASELINE + ":" + name), name
            )
        self.assertIn(
            "not a compatibility migration", (ROOT / "CONTRIBUTING.md").read_text()
        )

    def test_single_profile_source_and_no_expanded_previews(self):
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        self.assertEqual(index["canonical_profile"], "portable_protocols")
        self.assertEqual(len(index["files"]), 1023)
        self.assertEqual(len(mapping), 1023)
        self.assertEqual(len(list(ROOT.glob("workspaces/**/pyproject.toml"))), 26)
        self.assertFalse((ROOT / "workspaces/previews").exists())
        self.assertFalse((ROOT / "protocols/collaboration/previews").exists())

    def test_whole_envelope_and_every_attachment(self):
        path = RELEASE / "archive_verifier.py"
        spec = importlib.util.spec_from_file_location("integration_verifier", path)
        assert spec and spec.loader
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        archive = RELEASE / "canonical-initializer-source-notice-review-v1.tar.gz"
        self.assertEqual(sha(archive.read_bytes()), ENVELOPE_SHA)
        _, members = verifier.verified_archive(archive.read_bytes(), ENVELOPE_SHA)
        delivery = json.loads((RELEASE / "DELIVERY-MAP.json").read_bytes())
        self.assertEqual(set(delivery), set(members))
        self.assertEqual(len(members), 1358)
        for name, row in delivery.items():
            self.assertEqual(sha(members[name]), row["sha256"], name)
        for name in (
            "LICENSE",
            "NOTICE",
            "SOURCE-INDEX.json",
            "NOTICE-BINDINGS.json",
            "CONTENT-AUDIT.json",
        ):
            self.assertEqual((RELEASE / name).read_bytes(), members[name])
        self.assertEqual(len(json.loads(members["CONTENT-AUDIT.json"])["findings"]), 12)
        self.assertEqual(
            sum(
                not r["detected_legal_file_paths"]
                for r in json.loads(members["NOTICE-BINDINGS.json"])[
                    "aware_package_legal_inventory"
                ]
            ),
            6,
        )

    def test_guidance_distinguishes_prospective_inputs_and_runtime(self):
        self.assertIn("not two\nadmitted plans", (ROOT / "README.md").read_text())
        init = (ROOT / "protocols/INITIALIZATION.md").read_text()
        self.assertIn("prospective_only", init)
        self.assertIn("completion_verified=false", init)
        self.assertIn("detached wheels", (RELEASE / "README.md").read_text())

    def test_fresh_offline_hidden_install_and_refusals(self):
        scratch = Path(os.environ["AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT"])
        self.assertTrue(scratch.is_dir() and not scratch.is_symlink())
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        target = scratch / "env"
        self.assertFalse(target.exists() or target.is_symlink())
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
            "--bind",
            str(scratch),
            str(scratch),
            "--ro-bind",
            str(ROOT),
            "/mnt",
            "--clearenv",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "HOME",
            str(scratch),
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--setenv",
            "TMPDIR",
            str(scratch),
            "--chdir",
            "/mnt",
            "--",
        ]

        def run(args, expected=0):
            result = subprocess.run(
                prefix + args, capture_output=True, text=True, timeout=120, check=False
            )
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            return result

        command = [
            "/usr/bin/python3.12",
            "protocols/install.py",
            "--python-executable",
            "/usr/bin/python3.12",
            "--venv",
            str(target),
        ]
        installed = run(command)
        (scratch / "installation.stdout").write_text(installed.stdout)
        receipt = json.loads(installed.stdout.splitlines()[-1])
        self.assertEqual(receipt["packet_sha256"], ENVELOPE_SHA)
        self.assertEqual(receipt["payload_sha256"], PAYLOAD_SHA)
        retained = Path(receipt["retained_source_and_notices"])
        for name in ("LICENSE", "NOTICE", "source/THIRD_PARTY_NOTICES.md"):
            self.assertTrue((retained / name).is_file())
        for args in (
            ["--help"],
            ["init", "--help"],
            ["issue", "--help"],
            ["protocol", "--help"],
            ["spec", "--help"],
        ):
            run([str(target / "bin/aware"), *args])
        refusal = json.loads(
            run(
                [
                    str(target / "bin/aware"),
                    "init",
                    "--repo-root",
                    str(scratch / "repo"),
                    "--create-repository",
                ],
                2,
            ).stdout
        )
        self.assertEqual(
            refusal["preflight_error"]["diagnostics"],
            ["unambiguous_provider_execution_required"],
        )
        self.assertEqual(refusal["effect"], "none")
        self.assertFalse((scratch / "repo").exists())
        packages = json.loads(
            run(
                [
                    str(target / "bin/python"),
                    "-I",
                    "-c",
                    "import importlib.metadata as m,json; ds=[d for d in m.distributions() if d.metadata['Name']!='pip']; assert not any(d.read_text('direct_url.json') for d in ds); print(json.dumps({d.metadata['Name']:d.version for d in ds},sort_keys=True))",
                ]
            ).stdout
        )
        self.assertEqual(len(packages), 40)
        path = RELEASE / "archive_verifier.py"
        spec = importlib.util.spec_from_file_location("install_verifier", path)
        assert spec and spec.loader
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        _, outer = verifier.verified_archive(
            (
                RELEASE / "canonical-initializer-source-notice-review-v1.tar.gz"
            ).read_bytes(),
            ENVELOPE_SHA,
        )
        _, inner = verifier.verified_archive(
            outer["payload/aware-canonical-neutral-fs-internal-v1.tar.gz"], PAYLOAD_SHA
        )
        lock = json.loads(inner["consumer-lock.json"])
        norm = lambda s: re.sub(r"[-_.]+", "-", s).lower()
        self.assertEqual(
            {norm(n): v for n, v in packages.items()},
            {norm(r["name"]): r["version"] for r in lock["packages"]},
        )
        run([str(target / "bin/python"), "-I", "-m", "pip", "check"])
        self.assertIn("installation_target_must_be_new", run(command, 2).stderr)
        self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
        (scratch / "installed-receipt.json").write_text(
            json.dumps(
                {
                    "installation": receipt,
                    "versions": packages,
                    "missing_harness_effect": refusal["effect"],
                    "domain_matrix_replayed": False,
                },
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
