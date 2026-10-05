"""An agent entrance to canonical filesystem Issue operations, not another engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from aware_issue_cli.main import main as issue_main
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueSdkOperationClient, IssueEnsureSnapshotRequest, IssueBindScopePathsRequest,
    IssueStartProgressRequest, IssueReadProjectionResolveRequest,
    IssueReadProjectionResolveOutcome, IssueMutationOutcome,
)
from aware_protocol_fs_adapter import admit_protocol_manifest, resolve_repository_path_at_use

MANIFEST = '''aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = ".aware/agent-protocol.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "docs/issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
'''

CONTRACT = '''# Aware filesystem agent contract

Use the installed `aware` command. The customer chooses this filesystem profile;
there is no service authority or automatic service fallback.

Identify your real harness execution before work. Codex uses codex-$CODEX_THREAD_ID;
Claude Code uses claude_code-$CLAUDE_CODE_SESSION_ID. If there is no unambiguous
stable execution identity, stay read-only. Never borrow another execution's id.

Open one explicitly chosen Issue with exact scope through `aware issue open`.
Modify only its authored sources under customer approval. Do not manually edit
Issue authority, ownership, lifecycle or evidence; use the installed operations.
Observe the latest digest before every write. Commit explicit owned paths with
`aware repository commit --dry-run`, then the identical apply. Do not use raw
git add/commit to bypass the governed publication entrance.

Preserve unrelated staged and unstaged work. Tests and publication receipts are
evidence, not Goal acceptance. Close through the SDK-backed command with the
actual implementation receipt. For replacement, the current owner blocks the
Issue, transfers it to the exact new execution, and that execution observes and
resumes it. A transcript, cache, title or cwd never grants ownership.

This local profile checks declared identity/ownership, not authenticated actor
identity or sandbox isolation. A process with filesystem permissions can bypass
the tools. Service/API authentication is a later explicitly admitted authority.
Goal creation/approval, effectful pursuit, dispatch and hosted service are absent.
'''


def initialize(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="aware init")
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args(arguments)
    root = args.repository_root.resolve(strict=True)
    actual = Path(subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
    if root != actual:
        raise ValueError("select_exact_git_repository_root")
    targets = []
    for name, text in (("aware.protocol.toml", MANIFEST), (".aware/agent-protocol.md", CONTRACT)):
        result = resolve_repository_path_at_use(repository_root=root, relative_path=name,
                                                field_name="bootstrap." + name)
        if result.path is None:
            raise ValueError("bootstrap_target_unresolvable:" + ",".join(result.diagnostics))
        if (root / name).exists() or (root / name).is_symlink():
            raise ValueError("bootstrap_target_exists:" + name)
        targets.append((root / name, text))
    for path, text in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
    admitted = admit_protocol_manifest(repository_root=root, manifest_path=root / "aware.protocol.toml")
    if admitted.filesystem_profile is None:
        raise ValueError("bootstrap_admission_refused:" + ",".join(admitted.diagnostics))
    print(json.dumps({"outcome": "initialized", "profile": "aware.collaboration.fs_v1",
                      "created": ["aware.protocol.toml", ".aware/agent-protocol.md"],
                      "authority_mode": "filesystem", "goal_capability": "unavailable"}, sort_keys=True))
    return 0


def open_issue(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="aware issue open")
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--protocol-source", default="aware.protocol.toml")
    parser.add_argument("--issue-ref", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--priority", default="P1")
    parser.add_argument("--scope-path", action="append", required=True)
    parser.add_argument("--client-intent-id", required=True)
    parser.add_argument("--actor-ref", required=True)
    parser.add_argument("--actor-evidence-ref", required=True)
    parser.add_argument("--goal-ref", default="TBD")
    args = parser.parse_args(arguments)
    client = IssueSdkOperationClient(provider=FilesystemIssueOperationProvider(
        repository_root=args.repository_root, protocol_source_ref=args.protocol_source))
    before = client.resolve_read_projection(IssueReadProjectionResolveRequest(issue_ref=args.issue_ref))
    if before.outcome is not IssueReadProjectionResolveOutcome.ABSENT:
        print(json.dumps({"outcome": "refused", "diagnostics": ["open_requires_absent_issue"],
                          "observation": before.to_wire()}, sort_keys=True))
        return 2
    evidence = dict(issue_ref=args.issue_ref, actor_ref=args.actor_ref, actor_evidence_ref=args.actor_evidence_ref)
    receipts = []

    def retain(result):
        receipts.append(result.to_wire())
        return result.outcome in {IssueMutationOutcome.APPLIED, IssueMutationOutcome.IDEMPOTENT}

    ensured = client.ensure_issue_snapshot(IssueEnsureSnapshotRequest(
        **evidence, client_intent_id=args.client_intent_id + ":ensure", title=args.title,
        priority=args.priority, owner_ref=args.actor_ref, goal_ref=args.goal_ref,
        source_description="Customer-directed work through aware issue open"))
    if retain(ensured) and ensured.projection is not None:
        scope = tuple(dict.fromkeys([*args.scope_path, ensured.projection.source_path]))
        bound = client.bind_issue_scope_paths(IssueBindScopePathsRequest(
            **evidence, client_intent_id=args.client_intent_id + ":scope",
            expected_source_sha256=ensured.source_sha256_after, scope_paths=scope))
        if retain(bound):
            started = client.start_issue_progress(IssueStartProgressRequest(
                **evidence, client_intent_id=args.client_intent_id + ":start",
                expected_source_sha256=bound.source_sha256_after))
            success = retain(started)
            print(json.dumps({"outcome": "opened" if success else "incomplete",
                              "receipts": receipts, "atomic": False}, sort_keys=True))
            return 0 if success else 2
    print(json.dumps({"outcome": "incomplete", "receipts": receipts, "atomic": False}, sort_keys=True))
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args and args[0] == "init":
            return initialize(args[1:])
        if args[:2] == ["issue", "open"]:
            return open_issue(args[2:])
        if args and args[0] == "issue":
            return issue_main(args[1:])
        if args[:2] == ["repository", "commit"]:
            return issue_main(["commit-workspace", *args[2:]])
        parser = argparse.ArgumentParser(prog="aware", description="Agent-first, filesystem-only Issue workflow.")
        parser.add_argument("--version", action="version", version="aware-agent-cli 0.1.0a1")
        parser.epilog = "Commands: init; issue open; issue <canonical Issue CLI command>; repository commit"
        parser.parse_args(args)
        parser.print_help()
        return 0
    except (ValueError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(json.dumps({"outcome": "error", "diagnostics": [str(error)]}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
