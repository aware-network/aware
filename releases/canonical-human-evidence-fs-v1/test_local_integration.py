"""Maintainer accounting plus retained-installation reads; never install here."""

import ast
import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIOR = ROOT / "releases/canonical-refusal-successor-fs-v1/test_local_integration.py"
PRIOR_SHA = "b2c47206babe628074d04728c25149faebf28d116eb7d86a8920c96bc7b47fc1"
raw = PRIOR.read_bytes()
if PRIOR.is_symlink() or hashlib.sha256(raw).hexdigest() != PRIOR_SHA:
    raise ValueError("original_integration_test_required")

# Explicit maintainer receiving: coordinates/cardinalities change, seven
# original accounting methods remain. Replace the fresh-install method with a
# separately named retained-installation proof; do not relabel it as fresh.
source = raw.decode()
for before, after in (
    (
        "3667bed1396f67763176e0c78788661a30de5ecd",
        "591303349dbcd2762c55e1b4fd477de453581be5",
    ),
    (
        "2377067bb1f8f2400701c4d4ffb91920a8da71ce7df12ca1425fa2081958ed94",
        "19f6571e52fcfe512147ab03baae0a3a82da9c4f9f8190f9107d18ef64d2131a",
    ),
    (
        "e96946272b7812e833d41370ec5bfbba722f2f6f91720f994abcf9f407c975f7",
        "55790f137bf751a3500accd0fe064fd16305b677808a0d4cf7ac4f5e6d216272",
    ),
    (
        "34c3c9d16d5bec1aba75add5ce03e55d32b25c828da78e878288b19453d6a51c",
        "edf602d26547e39c13de452f23179faa3c186eaf4e99d3701294cd32be9e3e35",
    ),
    ("canonical-refusal-successor", "canonical-human-evidence"),
    ("canonical-reviewed-workflow", "canonical-refusal-successor"),
    (
        "03eb59691cfa1aa1e01e95a7c2727eb3d093ac28e5bd26ae7073416bb61f01b2",
        "e96946272b7812e833d41370ec5bfbba722f2f6f91720f994abcf9f407c975f7",
    ),
    (
        "899b2ef4beabf074fbdf7ea5980d4eaea1967ef4318b3ebc772814ee84b54727",
        "34c3c9d16d5bec1aba75add5ce03e55d32b25c828da78e878288b19453d6a51c",
    ),
):
    if before not in source:
        raise ValueError("original_receiving_coordinate_required")
    source = source.replace(before, after)
tree = ast.parse(source, filename=str(PRIOR))
classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
assert len(classes) == 1 and classes[0].name == "Integration"
removed = [
    node
    for node in classes[0].body
    if isinstance(node, ast.FunctionDef)
    and node.name == "test_fresh_offline_hidden_install_and_refusals"
]
assert len(removed) == 1
classes[0].body.remove(removed[0])
runner = tree.body.pop()
assert (
    isinstance(runner, ast.If) and ast.unparse(runner.test) == "__name__ == '__main__'"
)


class Counts(ast.NodeTransformer):
    def visit_Constant(self, node):
        if type(node.value) is int and node.value in {1627, 88, 92}:
            node.value = {1627: 1662, 88: 35, 92: 39}[node.value]
        return node


tree = ast.fix_missing_locations(Counts().visit(tree))
exec(compile(tree, str(PRIOR), "exec"), globals())  # noqa: S102 -- hash-pinned seven accounting tests only
Integration = globals()["Integration"]


def retained_installation_reads(self):
    candidate = Path(os.environ["AWARE_HUMAN_INTEGRATION_CANDIDATE"])
    scratch = Path(os.environ["AWARE_HUMAN_INTEGRATION_REPLAY_ROOT"])
    self.assertTrue(scratch.is_dir() and not scratch.is_symlink())
    self.assertEqual(scratch.stat().st_mode & 0o777, 0o700)
    installed = candidate / "build/environment"
    receipt = json.loads((candidate / "build/receipt.json").read_bytes())
    self.assertEqual(receipt["archive_sha256"], globals()["PAYLOAD_SHA"])
    expected = json.loads((candidate / "build/installed-account.json").read_bytes())
    self.assertEqual(len(expected["packages"]), 42)
    prefix = [
        "/usr/bin/bwrap",
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
        "--bind",
        str(scratch),
        str(scratch),
        "--ro-bind",
        str(installed),
        str(installed),
        "--dev",
        "/dev",
        "--proc",
        "/proc",
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
        "--chdir",
        str(scratch),
        "--",
    ]
    ledger = []

    def run(args, expected_exit=0):
        ordinal = len(ledger)
        begin = scratch / f"{ordinal:02d}.begin.json"
        with begin.open("x") as stream:
            json.dump({"argv": args, "automatic_retry": False}, stream)
        result = subprocess.run(
            [*prefix, *args], capture_output=True, text=True, timeout=60, check=False
        )
        (scratch / f"{ordinal:02d}.stdout").write_text(result.stdout)
        (scratch / f"{ordinal:02d}.stderr").write_text(result.stderr)
        ledger.append({"argv": args, "exit": result.returncode})
        (scratch / "commands.json").write_text(json.dumps(ledger, indent=2) + "\n")
        self.assertEqual(
            result.returncode, expected_exit, result.stdout + result.stderr
        )
        return result

    for parts in (
        (),
        ("init",),
        ("issue",),
        ("protocol",),
        ("spec",),
        ("workspace",),
        ("workspace", "review"),
        ("workspace", "review", "prepare"),
        ("workspace", "review", "show"),
        ("workspace", "review", "scope"),
        ("workspace", "review", "apply"),
        ("workspace", "review", "evidence"),
        ("spec", "present-receipt"),
    ):
        run([str(installed / "bin/aware"), *parts, "--help"])
    code = "import importlib.metadata as m,json,sys; expected=json.loads(sys.argv[1]); actual={k:m.version(k) for k in expected}; assert actual==expected; print(json.dumps(actual,sort_keys=True))"
    versions = json.loads(
        run(
            [
                str(installed / "bin/python"),
                "-I",
                "-B",
                "-c",
                code,
                json.dumps(expected["packages"]),
            ]
        ).stdout
    )
    run([str(installed / "bin/python"), "-I", "-B", "-m", "pip", "check"])
    missing = scratch / "missing-identity"
    refused = json.loads(
        run(
            [
                str(installed / "bin/aware"),
                "init",
                "--repo-root",
                str(missing),
                "--create-repository",
            ],
            2,
        ).stdout
    )
    self.assertEqual(refused["effect"], "none")
    self.assertFalse(missing.exists())
    origins = json.loads((candidate / "build/installed-origins.json").read_bytes())[
        "modules"
    ]
    self.assertEqual(len(origins), 137)
    for row in origins.values():
        path = Path(row["path"]).resolve()
        self.assertTrue(path.is_relative_to(installed.resolve()))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"])
    (scratch / "retained-installation.json").write_text(
        json.dumps(
            {
                "payload_sha256": receipt["archive_sha256"],
                "versions": versions,
                "installed_origins_rechecked": len(origins),
                "commands": len(ledger),
                "new_installation": False,
                "customer_workflow_replayed": False,
                "missing_identity_effect": refused["effect"],
            },
            indent=2,
        )
        + "\n"
    )


Integration.test_retained_installation_reads = retained_installation_reads

if __name__ == "__main__":
    unittest.main()
