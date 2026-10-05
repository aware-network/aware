"""Issue-scoped pinned source adoption, never ordinary customer bootstrap."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

OWNER = "c112eeb065f414f810e3d4d221e20bcb9df38487"
PUBLIC_BASE = "415460aa8118add0fb86601ff2377d6dc96d1d22"
BASE = "workspaces/aware_coordination/modules/workflow/"
ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "aware-issue-sdk": [
        "sdks/issue/python/aware_issue_sdk/operation.py",
        "sdks/issue/python/aware_issue_sdk/local_files.py",
    ],
    "aware-issue-fs-adapter": [
        "sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py"
    ],
    "aware-issue-cli": [
        "sdks/issue/cli/python/aware_issue_cli/main.py",
        "sdks/issue/cli/python/aware_issue_cli/summary.py",
    ],
}
TESTS = {
    "cli/test_cli.py": "sdks/issue/cli/python/tests/test_cli.py",
    "cli/test_summary.py": "sdks/issue/cli/python/tests/test_summary.py",
    "sdk/test_issue_sdk_usability.py": "sdks/issue/python/tests/test_issue_sdk_usability.py",
    "provider/test_provider.py": "sdks/issue/filesystem_adapter/python/tests/test_provider.py",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def committed(repo, revision, path):
    row = subprocess.check_output(["git", "ls-tree", revision, "--", path], cwd=repo)
    if not row.startswith((b"100644 blob ", b"100755 blob ")):
        raise ValueError("committed_regular_source_required:" + path)
    return subprocess.check_output(["git", "show", revision + ":" + path], cwd=repo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-repository", type=Path, required=True)
    args = parser.parse_args()
    selected = {}
    for package, paths in FILES.items():
        for relative in paths:
            path = BASE + relative
            destination = ROOT / path
            if destination.is_symlink():
                raise ValueError("adoption_symlink_refused:" + path)
            data = committed(args.owner_repository, OWNER, path)
            if destination.exists() and destination.read_bytes() not in (
                committed(ROOT, PUBLIC_BASE, path),
                data,
            ):
                raise ValueError("adoption_preimage_changed:" + path)
            selected[path] = (package, data)
    tests = {
        target: committed(args.owner_repository, OWNER, BASE + relative)
        for target, relative in TESTS.items()
    }
    new_contract = ROOT / "protocols/contracts/agent-fs/v1.2.0"
    if new_contract.exists():
        raise ValueError("contract_version_coordinate_exists")
    old_contract = ROOT / "protocols/contracts/agent-fs/v1.1.0"
    contract = json.loads((old_contract / "contract.json").read_bytes())
    assets = {
        relative: (old_contract / relative).read_text()
        for relative in ["contract.json", *contract["files"].values()]
    }
    provenance_path = ROOT / "protocols/agent/source-provenance.json"
    provenance = json.loads(provenance_path.read_bytes())
    rows = {row["source_path"]: row for row in provenance["files"]}
    adopted = []
    for path, (package, data) in selected.items():
        destination = ROOT / path
        previous = digest(destination.read_bytes()) if destination.exists() else None
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        row = rows.get(path)
        if row is None:
            row = {"package": package, "source_path": path}
            provenance["files"].append(row)
        row.update(
            source_revision=OWNER,
            source_sha256=digest(data),
            shipped_sha256=digest(data),
            disposition="byte-identical owner implementation",
        )
        adopted.append(
            {
                "path": path,
                "revision": OWNER,
                "sha256": digest(data),
                "previous_sha256": previous,
            }
        )
    owner_tests = ROOT / "protocols/agent/owner-tests"
    manifest_path = owner_tests / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for target, data in tests.items():
        destination = owner_tests / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        manifest["tests"] = [
            row for row in manifest["tests"] if row["test_path"] != target
        ]
        manifest["tests"].append(
            {
                "source_path": BASE + TESTS[target],
                "test_path": target,
                "source_revision": OWNER,
                "sha256": digest(data),
            }
        )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    previous = provenance["owner_adoption"]
    previous.setdefault("additional_adoptions", []).append(
        {
            "kind": "issue-usability-a5",
            "owner_revision": OWNER,
            "files": adopted,
            "status": "accepted-owner-source-adoption-not-consumer-acceptance",
        }
    )
    changed = set(previous["public_changed_paths"]) | {
        path
        for path in selected
        if path != BASE + "sdks/issue/cli/python/aware_issue_cli/summary.py"
    }
    changed.update(
        BASE + relative
        for relative in (
            "clients/agent/python/aware_agent_cli/main.py",
            "clients/agent/python/pyproject.toml",
            "sdks/issue/python/pyproject.toml",
            "sdks/issue/filesystem_adapter/python/pyproject.toml",
            "sdks/issue/cli/python/pyproject.toml",
        )
    )
    for relative, data in assets.items():
        if relative == "contract.json":
            data = json.dumps(dict(contract, version="1.2.0"), indent=2) + "\n"
        elif relative == "AGENTS.md.in":
            data = data.replace("**1.1.0**", "**1.2.0**").replace(
                "Record the real objective and acceptance through `issue append-update` before\nimplementation.",
                "Supply repeatable `--problem`, `--objective` and `--acceptance` at open.\nThese are durable authored items; acceptance starts unchecked and closure does\nnot automatically check it. Use `append-update` for progress and evidence.",
            )
        elif relative == "docs/agents/operational-work.md":
            data = data.replace(
                "Record objective and acceptance through `issue append-update`.",
                "Supply approved `--problem`, `--objective` and `--acceptance` at open.",
            )
        elif relative == "docs/issues/PROTOCOL.md":
            data += "\n## Initial authored content and opt-in summary\n\nNew `aware issue open` requests require repeatable `--problem`, `--objective`\nand `--acceptance`. They use the same SDK and Markdown owner; no manual record\nedits or automatic acceptance. Narrative updates do not rewrite these items.\nOmitted-content SDK compatibility remains available through lower-level tooling.\n\nUse `--format summary` for concise SDK evidence; JSON remains default. Preserve\nevery constituent receipt on incomplete open. Publication summaries retain\n`operator_ref`, `transaction_mode` and `reference_update`, including refusals.\nCloseout index fields describe that operation only: pending is retained debt,\nunknown is missing evidence, and neither proves a clean current Git index.\n"
        elif relative == "docs/agents/verification-and-handoff.md":
            data += "\nAuthored acceptance remains unchecked unless separately evidenced; Issue\ncloseout does not evaluate it or grant Goal acceptance. Retain actual index\nwarnings: unknown is not clean. Summaries preserve publication owner and\nreference-update state; default JSON remains available.\n"
        destination = new_contract / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(data)
        if data != assets[relative]:
            changed.add(
                BASE
                + "clients/agent/python/aware_agent_cli/templates/agent-fs-v1/"
                + relative
            )
    previous["public_changed_paths"] = sorted(changed)
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    layout_path = ROOT / "protocols/publication/source-layout.json"
    layout = json.loads(layout_path.read_bytes())
    summary_path = BASE + "sdks/issue/cli/python/aware_issue_cli/summary.py"
    layout["additions"] = [
        {
            "path": summary_path,
            "source_revision": OWNER,
            "sha256": digest(selected[summary_path][1]),
            "bytes": len(selected[summary_path][1]),
        }
    ]
    layout_path.write_text(json.dumps(layout, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "owner_revision": OWNER,
                "adopted_files": len(selected),
                "contract_version": "1.2.0",
            }
        )
    )


if __name__ == "__main__":
    main()
