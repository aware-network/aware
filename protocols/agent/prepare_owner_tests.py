"""Export pinned owner tests, separately from the consumer dependency closure."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = "728831f6636a611a8baac61dbc258ed563a0e466"
BASE = "workspaces/aware_coordination/modules/workflow/"
GROUPS = {
    "provider": [BASE + "sdks/issue/filesystem_adapter/python/tests/test_provider.py"],
    "cli": [BASE + "sdks/issue/cli/python/tests/test_cli.py"],
    "sdk": [BASE + "sdks/issue/python/tests/test_issue_sdk_operation.py"],
    "state": [BASE + "libs/issue_operational_runtime/tests/" + n for n in ("conftest.py", "test_state_machine.py")],
    "commit": ["workspaces/aware_workspace/modules/workspace/libs/workspace_operator/python/tests/test_commit.py"],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for group, paths in GROUPS.items():
        for source in paths:
            data = subprocess.check_output(["git", "show", PIN + ":" + source], cwd=args.source_repository)
            target = args.output / group / Path(source).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            records.append({"source_path": source, "test_path": target.relative_to(args.output).as_posix(), "sha256": hashlib.sha256(data).hexdigest()})
    (args.output / "manifest.json").write_text(json.dumps({"source_revision": PIN, "tests": records}, indent=2) + "\n")


if __name__ == "__main__":
    main()
