from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from aware_service_runtime.implementation_package import (
    _raise_if_api_request_model_dropped_payload_fields,
)


class _StaleWorkspaceCommitRequest(BaseModel):
    operation: str = Field(default="commit")
    workspace_root: str
    message: str
    persist_source_commit: bool = Field(default=True)


class _FreshWorkspaceCommitRequest(_StaleWorkspaceCommitRequest):
    commit_source_kind: str = Field(default="source_change")
    workspace_materialization_id: str | None = Field(default=None)
    verified_path_count: int | None = Field(default=None)


class _WorkspaceBranchPublishRequest(BaseModel):
    operation: str = Field(default="branch_publish")
    workspace_root: str
    authority_root: str | None = Field(default=None)
    candidate_workspace_revision_id: str


def test_service_api_dispatch_guard_rejects_stale_request_model() -> None:
    payload = {
        "operation": "commit",
        "workspace_root": "/tmp/aware_kernel",
        "message": "Seal genesis materialization",
        "persist_source_commit": False,
        "commit_source_kind": "verified_materialization",
        "workspace_materialization_id": "workspace-materialization:test",
        "verified_path_count": 48,
    }

    request_object = _StaleWorkspaceCommitRequest.model_validate(payload)

    with pytest.raises(RuntimeError) as exc_info:
        _raise_if_api_request_model_dropped_payload_fields(
            endpoint_ref="workspace.commit",
            request_type_ref="aware.workspace.WorkspaceCommitRequest",
            request_model_cls=_StaleWorkspaceCommitRequest,
            request_payload=payload,
            request_object=request_object,
        )

    message = str(exc_info.value)
    assert "changed caller payload fields" in message
    assert "commit_source_kind" in message
    assert "workspace_materialization_id" in message
    assert "verified_path_count" in message


def test_service_api_dispatch_guard_rejects_changed_request_value() -> None:
    payload = {
        "operation": "branch_publish",
        "workspace_root": "/tmp/aware_kernel",
        "authority_root": "/tmp/aware_authority",
        "candidate_workspace_revision_id": "workspace-revision:test",
    }
    request_object = _WorkspaceBranchPublishRequest.model_validate(
        {
            "operation": "branch_publish",
            "workspace_root": "/tmp/aware_kernel",
            "candidate_workspace_revision_id": "workspace-revision:test",
        }
    )

    with pytest.raises(RuntimeError) as exc_info:
        _raise_if_api_request_model_dropped_payload_fields(
            endpoint_ref="workspace.branch.publish",
            request_type_ref="aware.workspace.WorkspaceBranchPublishRequest",
            request_model_cls=_WorkspaceBranchPublishRequest,
            request_payload=payload,
            request_object=request_object,
        )

    message = str(exc_info.value)
    assert "changed caller payload fields" in message
    assert "authority_root" in message
    assert "changed_fields=('authority_root',)" in message


def test_service_api_dispatch_guard_accepts_current_request_model() -> None:
    payload = {
        "operation": "commit",
        "workspace_root": "/tmp/aware_kernel",
        "message": "Seal genesis materialization",
        "persist_source_commit": False,
        "commit_source_kind": "verified_materialization",
        "workspace_materialization_id": "workspace-materialization:test",
        "verified_path_count": 48,
    }
    request_object = _FreshWorkspaceCommitRequest.model_validate(payload)

    _raise_if_api_request_model_dropped_payload_fields(
        endpoint_ref="workspace.commit",
        request_type_ref="aware.workspace.WorkspaceCommitRequest",
        request_model_cls=_FreshWorkspaceCommitRequest,
        request_payload=payload,
        request_object=request_object,
    )
