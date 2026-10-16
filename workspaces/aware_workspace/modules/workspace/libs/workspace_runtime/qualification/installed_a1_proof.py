"""Test-free installed A1 SDK/Agent qualification in a disposable repository."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import traceback
import weakref
from pathlib import Path
from typing import Any


def sha(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def observe(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): sha(p.read_bytes())
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def record(path: Path, value: dict[str, Any]) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def run(args: list[str], log: Path, expected: int) -> dict[str, Any]:
    record(log, {"stage": "command_begin", "argv": args})
    try:
        result = subprocess.run(args, capture_output=True, timeout=30, check=False)
    except subprocess.TimeoutExpired as error:
        record(
            log,
            {
                "stage": "command_timeout",
                "argv": args,
                "stdout": (error.stdout or b"").decode(errors="replace"),
                "stderr": (error.stderr or b"").decode(errors="replace"),
                "effects": "unknown",
                "retry_authorized": False,
            },
        )
        raise
    record(
        log,
        {
            "stage": "command_result",
            "argv": args,
            "exit": result.returncode,
            "stdout": result.stdout.decode(errors="replace"),
            "stderr": result.stderr.decode(errors="replace"),
        },
    )
    assert result.returncode == expected, result.stderr.decode(errors="replace")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--installed-root", type=Path, required=True)
    parser.add_argument("--expected-execution", required=True)
    args = parser.parse_args()
    fixture, installed = args.fixture, args.installed_root
    root, log = fixture / "repository", fixture / "commands.jsonl"
    assert root.is_dir() and installed.is_dir() and not log.exists()
    assert "codex-" + os.environ["CODEX_THREAD_ID"] == args.expected_execution
    assert not os.environ.get("CLAUDE_CODE_SESSION_ID")
    assert Path(sys.prefix) == installed
    assert not any("/aware-dev/" in p for p in sys.path)
    aware = str(installed / "bin/aware")
    issue_tag = "fb/2026-10-14/installed-a1-proof"
    issue_path = "docs/issues/2026/10/14/fb-2026-10-14-installed-a1-proof.md"
    common = [
        "--repository-root",
        str(root),
        "--issue-ref",
        issue_tag,
        "--protocol-source",
        "aware.protocol.toml",
    ]
    actor = [
        "--actor-ref",
        args.expected_execution,
        "--actor-evidence-ref",
        "declared:human-directed-fixture",
    ]
    outcome: dict[str, Any] = {
        "status": "incomplete",
        "execution": args.expected_execution,
        "retry_authorized": False,
    }
    before = observe(root)
    held_clients = []
    disposal_attempted = set()
    try:
        # Issue creation/lifecycle use the installed family's original supplier.
        run(
            [
                aware,
                "issue",
                "ensure-snapshot",
                *common,
                *actor,
                "--client-intent-id",
                "intent:issue-create",
                "--title",
                "Installed A1 proof",
                "--priority",
                "P1",
                "--owner-ref",
                args.expected_execution,
            ],
            log,
            0,
        )
        assert (root / issue_path).is_file()
        run(
            [
                aware,
                "issue",
                "start-progress",
                *common,
                *actor,
                "--client-intent-id",
                "intent:issue-start",
                "--expected-source-sha256",
                sha((root / issue_path).read_bytes()),
            ],
            log,
            0,
        )

        from aware_issue_fs_adapter import FilesystemIssueOperationProvider
        from aware_issue_sdk import IssueBindScopePathsRequest, IssueSdkOperationClient
        from aware_issue_sdk.workspace_setup_admission import (
            IssueWorkspaceSetupAdmissionClient,
        )
        from aware_issue_sdk.workspace_setup_admission_values import (
            IssueWorkspaceSetupRequest,
        )
        from aware_workspace_command.architecture_setup_a1_command_values import (
            WorkspaceSetupA1CommandEvidence,
            command_value_from_payload,
        )
        from aware_workspace_sdk.architecture_setup import (
            ArchitectureSetupError,
            ArchitectureSetupRequest,
            WorkspaceSetupClient,
        )
        from aware_workspace_sdk.architecture_setup_admission import (
            observe_original_setup_plan,
        )
        from aware_workspace_sdk.architecture_setup_admission_codec import (
            setup_value_to_payload,
        )

        operations = IssueSdkOperationClient(
            provider=FilesystemIssueOperationProvider(
                repository_root=str(root), protocol_source_ref="aware.protocol.toml"
            )
        )

        def bind(paths, intent):
            result = operations.bind_issue_scope_paths(
                IssueBindScopePathsRequest(
                    issue_ref=issue_tag,
                    expected_source_sha256=sha((root / issue_path).read_bytes()),
                    client_intent_id=intent,
                    actor_ref=args.expected_execution,
                    actor_evidence_ref="declared:human-directed-fixture",
                    scope_paths=tuple(sorted(set(paths))),
                )
            )
            record(log, {"stage": "original_issue_scope", "result": result.to_wire()})
            assert str(result.outcome) in ("applied", "unchanged")

        def footprint(binding):
            return sorted(
                {
                    p
                    for step in binding.ordered_effects
                    for p in (step.primary_path, *step.auxiliary_paths)
                }
            )

        results = []

        def agent(operation, extra):
            original = [
                aware,
                "workspace",
                "setup",
                operation,
                "--repository-root",
                str(root),
                *extra,
                "--governed",
                "--issue-ref",
                issue_path,
                "--authority-manifest",
                "aware.protocol.toml",
                "--client-intent-id",
                "intent:agent-" + operation,
                "--json",
            ]
            initial = observe(root)
            preview = command_value_from_payload(
                WorkspaceSetupA1CommandEvidence, run(original, log, 0)
            )
            assert observe(root) == initial and preview.issue_observation is None
            assert preview.workspace_observation is not None
            assert preview.workspace_observation.binding is not None
            bind(
                footprint(preview.workspace_observation.binding),
                "intent:scope-" + operation,
            )
            reviewed = command_value_from_payload(
                WorkspaceSetupA1CommandEvidence, run(original, log, 0)
            )
            assert reviewed.command_status == "preview_completed"
            assert reviewed.workspace_observation is not None
            assert reviewed.workspace_observation.binding is not None
            guards = reviewed.review_guards
            apply = [
                *original,
                "--apply",
                "--issue-source-sha256",
                guards.issue_source_sha256,
                "--authority-manifest-sha256",
                guards.authority_manifest_sha256,
                "--expected-plan-sha256",
                guards.plan_sha256,
            ]
            for path in tuple(
                row.path
                for row in reviewed.workspace_observation.binding.file_transitions
            ):
                apply += ["--allowed-path", path]
            done = command_value_from_payload(
                WorkspaceSetupA1CommandEvidence, run(apply, log, 0)
            )
            assert done.command_status == "apply_completed" and done.completion_verified
            assert done.issue_observation is not None
            assert done.workspace_observation is not None
            assert done.workspace_observation.binding is not None
            assert done.plan_cleanup is not None and done.admission_cleanup is not None
            assert done.client_cleanup.issue is not None
            assert done.client_cleanup.workspace is not None
            assert done.workspace_result is not None
            assert done.issue_observation.consumption_ref
            assert (
                done.issue_observation.verified_effect_ordinal
                == len(done.workspace_observation.binding.ordered_effects) - 1
            )
            assert (
                done.plan_cleanup.release
                == done.admission_cleanup.outcome
                == "confirmed"
            )
            assert (
                done.client_cleanup.issue.outcome
                == done.client_cleanup.workspace.outcome
                == "confirmed"
            )
            assert done.ledger_complete and not done.authorizes_retry
            settled = observe(root)
            refused = command_value_from_payload(
                WorkspaceSetupA1CommandEvidence, run(apply, log, 2)
            )
            assert observe(root) == settled and not refused.completion_verified
            assert refused.workspace_result is None and not refused.authorizes_retry
            results.append(
                {
                    "operation": operation,
                    "written_paths": list(
                        done.workspace_result.original_receipt.written_paths
                    ),
                    "consumption_ref": done.issue_observation.consumption_ref,
                    "last_verified_ordinal": done.issue_observation.verified_effect_ordinal,
                    "replay_refused": True,
                    "cleanup": "confirmed",
                }
            )

        agent(
            "repository", ["--name", "installed-example", "--license-expression", "MIT"]
        )
        agent("workspace", ["--name", "application"])
        agent("module", ["--workspace", "application", "--name", "greeting"])

        # Public SDK creation uses the same live original supplier join.
        descriptor_before = len(tuple(Path("/proc/self/fd").iterdir()))
        workspace = WorkspaceSetupClient.filesystem(repository_root=root)
        held_clients.append(("workspace", workspace))
        issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
            repository_root=root,
            execution_id=args.expected_execution,
            authority_manifest_locator="aware.protocol.toml",
        )
        held_clients.append(("issue", issuer))
        request = ArchitectureSetupRequest(
            "python_package",
            name="client",
            workspace="application",
            module="greeting",
            distribution="installed-example-client",
            import_root="installed_example_client",
            path="libs/client/python",
            owner="module",
        )
        plan = workspace.prepare_setup(
            request, expected_plan_sha256=workspace.preview(request).plan_sha256
        )
        binding = observe_original_setup_plan(plan).binding
        bind(footprint(binding), "intent:sdk-scope")
        sources = issuer.observe_authority_sources(issue_ref=issue_path)
        issue_plan = issuer.prepare_setup_admission(
            IssueWorkspaceSetupRequest(
                issue_path,
                sources.issue_source.content_sha256,
                None,
                None,
                "intent:sdk-package",
                "workspace_setup_a1_v1",
                sources.authority_manifest_source.content_sha256,
            ),
            workspace_plan=plan,
            expected_binding=binding,
        )
        admission = workspace.enroll_setup_admission(
            plan, issue_admission=issuer.admit_setup(issue_plan)
        )
        try:
            result = workspace.observe_setup_result(
                workspace.apply_setup_plan(plan, admission=admission)
            )
            record(
                log, {"stage": "sdk_result", "result": setup_value_to_payload(result)}
            )
            assert result.release == "unknown" and result.ledger_complete
            assert result.original_receipt.status == "succeeded"
            successful = observe(root)
            try:
                workspace.apply_setup_plan(plan, admission=admission)
            except ArchitectureSetupError:
                pass
            else:
                raise AssertionError("original admission replay accepted")
            assert observe(root) == successful
        finally:
            assert workspace.release_setup_plan(plan).release == "confirmed"
            assert issuer.release_setup_admission(issue_plan).outcome == "confirmed"
            disposal_attempted.add("issue")
            issue_cleanup = issuer.release_client()
            disposal_attempted.add("workspace")
            workspace_cleanup = workspace.release_client()
            assert issue_cleanup.outcome == workspace_cleanup.outcome == "confirmed"
        # Cleanup has its own original receipt; it cannot rewrite the historical
        # execution result into a stronger release claim.
        assert result.release == "unknown"
        record(
            log,
            {
                "stage": "sdk_cleanup",
                "issue": issue_cleanup.outcome,
                "workspace": workspace_cleanup.outcome,
            },
        )
        held_clients.clear()
        refs = weakref.ref(workspace), weakref.ref(issuer)
        del workspace, issuer, plan, issue_plan, admission
        gc.collect()
        assert all(ref() is None for ref in refs)
        assert len(tuple(Path("/proc/self/fd").iterdir())) == descriptor_before
        results.append(
            {
                "operation": "sdk_python_package",
                "written_paths": list(result.original_receipt.written_paths),
                "replay_refused": True,
                "client_collection": True,
                "descriptor_cleanup": True,
            }
        )

        agent("align", [])
        # Genuine source currentness refusal with old guards; no guard refresh.
        original = [
            aware,
            "workspace",
            "setup",
            "python-package",
            "--repository-root",
            str(root),
            "--owner",
            "repository",
            "--name",
            "stale",
            "--distribution",
            "installed-stale",
            "--import-root",
            "installed_stale",
            "--governed",
            "--issue-ref",
            issue_path,
            "--authority-manifest",
            "aware.protocol.toml",
            "--client-intent-id",
            "intent:stale",
            "--json",
        ]
        preview = command_value_from_payload(
            WorkspaceSetupA1CommandEvidence, run(original, log, 0)
        )
        assert preview.workspace_observation is not None
        assert preview.workspace_observation.binding is not None
        bind(footprint(preview.workspace_observation.binding), "intent:stale-scope")
        reviewed = command_value_from_payload(
            WorkspaceSetupA1CommandEvidence, run(original, log, 0)
        )
        assert reviewed.workspace_observation is not None
        assert reviewed.workspace_observation.binding is not None
        changed = (
            root / "aware.protocol.toml"
        ).read_bytes() + b"\n# disposable observed drift\n"
        (root / "aware.protocol.toml").write_bytes(changed)
        initial = observe(root)
        apply = [
            *original,
            "--apply",
            "--issue-source-sha256",
            reviewed.review_guards.issue_source_sha256,
            "--authority-manifest-sha256",
            reviewed.review_guards.authority_manifest_sha256,
            "--expected-plan-sha256",
            reviewed.review_guards.plan_sha256,
        ]
        for path in tuple(
            row.path for row in reviewed.workspace_observation.binding.file_transitions
        ):
            apply += ["--allowed-path", path]
        refused = command_value_from_payload(
            WorkspaceSetupA1CommandEvidence, run(apply, log, 2)
        )
        assert (
            observe(root) == initial
            and refused.workspace_result is None
            and not refused.authorizes_retry
        )
        assert not tuple(root.rglob(".aware-cas-*"))

        origins = {}
        for name, module in sorted(sys.modules.items()):
            file = getattr(module, "__file__", None)
            if name.startswith("aware_") and file:
                path = Path(file).resolve()
                assert path.is_relative_to(installed), (name, file)
                origins[name] = {"path": str(path), "sha256": sha(path.read_bytes())}
        versions = {
            d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
        }
        assert (
            not {
                "aware-orm",
                "aware-local-service-runtime",
                "aware-sdk-runtime",
                "tree-sitter-aware",
            }
            & versions.keys()
        )
        outcome.update(
            status="complete",
            operations=results,
            origins=origins,
            versions=versions,
            stale_refused=True,
            scratch_absent=True,
            no_a2=True,
            before=before,
            after=observe(root),
            generated_operations=False,
        )
    except BaseException as error:
        outcome.update(
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
            after=observe(root),
        )
        raise
    finally:
        # Independent original cleanup begins at construction, including a
        # failed preview/preparation. Never repeat an uncertain disposal.
        for owner, client in reversed(held_clients):
            if owner in disposal_attempted:
                continue
            disposal_attempted.add(owner)
            try:
                cleanup = client.release_client()
                record(
                    log,
                    {
                        "stage": "client_cleanup",
                        "owner": owner,
                        "outcome": cleanup.outcome,
                    },
                )
            except BaseException as error:  # noqa: BLE001 -- settle independent cleanup after cancellation without retry
                record(
                    log,
                    {
                        "stage": "client_cleanup",
                        "owner": owner,
                        "outcome": "unknown",
                        "error_type": type(error).__name__,
                    },
                )
        record(fixture / "outcome.jsonl", outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
