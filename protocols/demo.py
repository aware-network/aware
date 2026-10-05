#!/usr/bin/env python3
"""Read the committed synthetic preview fixture through the installed CLI."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

GOAL_PATH = "protocols/examples/read-only/goals/2026/10/05/goal-2026-10-05-reader-demo.md"
GOAL_TAG = "goal/2026-10-05/reader-demo"


def snapshot(root: Path) -> dict[str, str]:
    result = {}
    for key, arguments in (("head", ["rev-parse", "HEAD"]),
                           ("status", ["status", "--porcelain=v1"]),
                           ("index_path", ["rev-parse", "--git-path", "index"])):
        result[key] = subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()
    index = Path(result.pop("index_path"))
    if not index.is_absolute():
        index = root / index
    result["index_sha256"] = hashlib.sha256(index.read_bytes()).hexdigest()
    result["goal_sha256"] = hashlib.sha256((root / GOAL_PATH).read_bytes()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    cli = args.cli.expanduser().resolve(strict=True)
    output = Path(tempfile.mkdtemp(prefix="aware-goal-preview-receipts-"))
    environment = {key: value for key, value in os.environ.items()
                   if key in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"}}
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    common = ["--repository-root", str(root), "--manifest-path",
              str(root / "protocols/examples/read-only/aware.protocol.toml")]
    before = snapshot(root)

    def invoke(name: str, arguments: list[str]) -> dict:
        completed = subprocess.run([str(cli), *arguments], cwd=root, env=environment,
                                   capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout)
        (output / name).write_text(completed.stdout, encoding="utf-8")
        return json.loads(completed.stdout)

    invoke("request.json", [*common, "--discover-goal-path", GOAL_PATH,
                            "--lane-key", "demo", "--phase-key", "read"])
    eligibility = invoke("eligibility.json", [*common, "--request-file", str(output / "request.json")])
    invoke("direction.json", ["observe_phase_direction", *common, "--goal-path", GOAL_PATH,
                              "--goal-tag", GOAL_TAG, "--lane-key", "demo", "--phase-key", "read"])
    currentness = invoke("currentness.json", ["verify_phase_direction_currentness", *common,
                                             "--goal-path", GOAL_PATH, "--receipt-file",
                                             str(output / "direction.json")])
    if snapshot(root) != before:
        raise RuntimeError("demo_changed_repository_state")
    print(json.dumps({"fixture": "synthetic-not-customer-authority",
                      "eligibility": eligibility["eligibility"],
                      "currentness": currentness.get("status", "current"),
                      "repository_unchanged": True, "receipts": str(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
