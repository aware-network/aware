from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_workspace_operator.bridge.adapters.compiler_service_remote import (
    CompilerServiceRemoteAdapter,
)
from aware_workspace_operator.bridge.adapters.upgrade_service_remote import (
    CompilerUpgradeRemoteAdapter,
)
from aware_workspace_operator.bridge.adapters.defaults import (
    InMemoryEvidenceAdapter,
    PassthroughWorkspaceDeltaAdapter,
)
from aware_workspace_operator.bridge.models import (
    WorkspaceBridgeCycleRequest,
)
from aware_workspace_operator.bridge.orchestrator import WorkspaceBridgeOrchestrator


@dataclass(frozen=True, slots=True)
class _SyntheticPreflightReport:
    relationship: str
    integrity_ok: bool


def _preflight_synthetic_ocg_lane_upgrade(
    *,
    lane_json_path: Path,
    aware_root: Path,
) -> _SyntheticPreflightReport:
    lane = json.loads(lane_json_path.read_text(encoding="utf-8"))
    branch_id = UUID(str(lane["branch_id"]))
    projection_hash = str(lane["projection_hash"])
    head_commit_id = UUID(str(lane["head_commit_id"]))
    lane_dir = aware_root / ".aware" / "oig" / str(branch_id) / projection_hash
    head_path = lane_dir / "HEAD.json"
    commits_dir = lane_dir / "commits"
    migrations_root = lane_json_path.parent.parent

    integrity_ok = head_path.is_file()
    current_head_commit_id: UUID | None = None
    if integrity_ok:
        head = json.loads(head_path.read_text(encoding="utf-8"))
        current_head_commit_id = UUID(str(head["commit_id"]))
        integrity_ok = current_head_commit_id == head_commit_id

    for entry in lane.get("commits", []):
        commit_id = UUID(str(entry["commit_id"]))
        commit_path = commits_dir / f"{commit_id}.json"
        delta_file = entry.get("delta_file")
        delta_path = migrations_root / str(delta_file) if delta_file else None
        if not commit_path.is_file() or delta_path is None or not delta_path.is_file():
            integrity_ok = False
            continue

        commit_payload = json.loads(commit_path.read_text(encoding="utf-8"))
        parents = commit_payload.get("commit", {}).get("commit_parents", [])
        actual_parent = None
        if parents:
            actual_parent = str(parents[0].get("parent_commit_id"))
        expected_parent = entry.get("parent_commit_id")
        if actual_parent != expected_parent:
            integrity_ok = False
        if commit_payload.get("graph_hash_post") != entry.get("graph_hash_post"):
            integrity_ok = False

    return _SyntheticPreflightReport(
        relationship=(
            "up_to_date"
            if current_head_commit_id == head_commit_id
            else "needs_migration"
        ),
        integrity_ok=integrity_ok,
    )


class _StubUpgradeBackend:
    def __init__(self, *, aware_root: Path, runtime_dir: Path) -> None:
        self._aware_root = aware_root
        self._runtime_dir = runtime_dir
        self._branch_id = UUID("11111111-1111-1111-1111-111111111111")
        self._projection_hash = "sha256:test:opg"
        self._head_commit_id: UUID | None = None
        self._head_hash: str | None = None

    def build_upgrade_service_response(self) -> dict[str, object]:
        previous = self._head_commit_id
        next_commit = uuid4()
        graph_hash_pre = self._head_hash
        graph_hash_post = f"sha256:test:{next_commit}"

        self._write_delta_file(commit_id=next_commit)
        self._write_lane_json(
            head_commit_id=next_commit,
            parent_commit_id=previous,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
        )
        self._write_commit_store(
            head_commit_id=next_commit,
            parent_commit_id=previous,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
        )
        self._head_commit_id = next_commit
        self._head_hash = graph_hash_post

        report = _preflight_synthetic_ocg_lane_upgrade(
            lane_json_path=self._runtime_dir / "migrations" / "ocg" / "lane.json",
            aware_root=self._aware_root,
        )
        return {
            "environment_operation": {
                "response": {
                    "service_operation": {
                        "service": "compiler",
                        "operation": "apply_upgrade",
                        "upgrade_result": {
                            "previous_head_commit_id": (
                                str(previous) if previous is not None else None
                            ),
                            "current_head_commit_id": str(next_commit),
                            "lane_head_advanced": previous != next_commit,
                            "preflight_status": (
                                "ok" if report.integrity_ok else "failed"
                            ),
                            "preflight_relationship": report.relationship,
                            "preflight_integrity_ok": report.integrity_ok,
                        },
                    }
                }
            }
        }

    def _write_delta_file(self, *, commit_id: UUID) -> None:
        path = self._runtime_dir / "migrations" / "ocg" / "deltas" / f"{commit_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    def _write_lane_json(
        self,
        *,
        head_commit_id: UUID,
        parent_commit_id: UUID | None,
        graph_hash_pre: str | None,
        graph_hash_post: str,
    ) -> None:
        lane_json_path = self._runtime_dir / "migrations" / "ocg" / "lane.json"
        lane_json_path.parent.mkdir(parents=True, exist_ok=True)
        lane_json_path.write_text(
            json.dumps(
                {
                    "v": 1,
                    "opg_name": "ObjectConfigGraph",
                    "branch_id": str(self._branch_id),
                    "projection_hash": self._projection_hash,
                    "head_commit_id": str(head_commit_id),
                    "commits": [
                        {
                            "commit_id": str(head_commit_id),
                            "parent_commit_id": (
                                str(parent_commit_id)
                                if parent_commit_id is not None
                                else None
                            ),
                            "graph_hash_pre": graph_hash_pre,
                            "graph_hash_post": graph_hash_post,
                            "delta_file": f"ocg/deltas/{head_commit_id}.json",
                            "sql_file": f"sql/commits/{head_commit_id}.sql",
                        }
                    ],
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

    def _write_commit_store(
        self,
        *,
        head_commit_id: UUID,
        parent_commit_id: UUID | None,
        graph_hash_pre: str | None,
        graph_hash_post: str,
    ) -> None:
        lane_dir = (
            self._aware_root
            / ".aware"
            / "oig"
            / str(self._branch_id)
            / self._projection_hash
        )
        commits_dir = lane_dir / "commits"
        commits_dir.mkdir(parents=True, exist_ok=True)
        (commits_dir / f"{head_commit_id}.json").write_text(
            json.dumps(
                {
                    "commit": {
                        "id": str(head_commit_id),
                        "commit_parents": (
                            [{"parent_commit_id": str(parent_commit_id)}]
                            if parent_commit_id is not None
                            else []
                        ),
                    },
                    "graph_hash_pre": graph_hash_pre,
                    "graph_hash_post": graph_hash_post,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        (lane_dir / "HEAD.json").write_text(
            json.dumps(
                {
                    "commit_id": str(head_commit_id),
                    "graph_hash_post": graph_hash_post,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )


@pytest.mark.asyncio
async def test_workspace_bridge_cycle_remote_delta_to_preflight_green(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "bundle" / ".aware" / "environment" / "runtime"
    aware_root = tmp_path / "aware_root"
    repo_root = tmp_path / "remote_workspace"
    aware_root.mkdir(parents=True, exist_ok=True)
    repo_root.mkdir(parents=True, exist_ok=True)

    session_id = uuid4()
    upgrade_backend = _StubUpgradeBackend(
        aware_root=aware_root, runtime_dir=runtime_dir
    )

    async def _request_fn(payload: dict[str, object]) -> dict[str, object]:
        operation = str(payload.get("operation", ""))
        if operation == "open_session":
            return {
                "service": "compiler",
                "operation": "open_session",
                "session_id": str(session_id),
                "repo_root": str(repo_root),
                "lane": "main",
                "language_id": "aware",
                "update_id": 1,
                "code_package_delta": {"operations": []},
                "object_config_graph_delta": None,
            }
        if operation == "apply_code_package_delta":
            return {
                "service": "compiler",
                "operation": "apply_code_package_delta",
                "session_id": str(session_id),
                "repo_root": str(repo_root),
                "lane": "main",
                "language_id": "aware",
                "update_id": 2,
                "code_package_delta": payload.get("code_package_delta"),
                "object_config_graph_delta": {
                    "graph_hash_pre": "sha256:test:pre",
                    "graph_hash_post": "sha256:test:post",
                    "node_deltas": [{"change": "update"}],
                },
            }
        if operation == "close_session":
            return {
                "service": "compiler",
                "operation": "close_session",
                "session_id": str(session_id),
                "repo_root": str(repo_root),
                "lane": "main",
                "language_id": "aware",
            }
        if operation == "apply_upgrade":
            return upgrade_backend.build_upgrade_service_response()
        raise AssertionError(f"Unexpected operation: {operation}")

    compiler_adapter = CompilerServiceRemoteAdapter(request_fn=_request_fn)
    upgrade_adapter = CompilerUpgradeRemoteAdapter(request_fn=_request_fn)
    evidence = InMemoryEvidenceAdapter()
    orchestrator = WorkspaceBridgeOrchestrator(
        workspace_delta_port=PassthroughWorkspaceDeltaAdapter(),
        compiler_session_port=compiler_adapter,
        upgrade_port=upgrade_adapter,
        evidence_port=evidence,
    )

    cycle = await orchestrator.run_cycle(
        request=WorkspaceBridgeCycleRequest(
            repo_root=str(repo_root),
            lane="main",
            language_id="aware",
            code_package_delta={
                "workspace_root": str(repo_root),
                "operations": [
                    {
                        "create": {
                            "path": "domains/demo/model.aware",
                            "content_text": "class Demo {\n    name String\n}\n",
                            "content_hash": "sha256:test:file",
                        }
                    }
                ],
            },
            close_session=True,
        )
    )

    assert cycle.session_id == session_id
    assert cycle.object_config_graph_delta_present is True
    assert cycle.lane_head_advanced is True
    assert cycle.preflight_status == "ok"
    assert cycle.preflight_relationship == "up_to_date"
    assert cycle.preflight_integrity_ok is True
    assert cycle.evidence_count >= 5
