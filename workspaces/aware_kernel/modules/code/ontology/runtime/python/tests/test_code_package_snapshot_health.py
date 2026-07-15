from __future__ import annotations

from uuid import uuid4

import pytest

from aware_code.package import snapshot_health
from aware_code.package.snapshot_contract import (
    CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
)


@pytest.mark.asyncio
async def test_selected_health_loads_only_required_source_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code_package_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    source_object_id = uuid4()
    observed: dict[str, object] = {}
    payload = {
        "code_package_id": str(code_package_id),
        "head_commit_id": str(head_commit_id),
        "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
        "graph_hash_post": "sha256:graph",
        "snapshot_fingerprint": "sha256:snapshot",
        "source_snapshot_fingerprint": "sha256:source",
        "artifact_state_index": {
            "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
            "code_package_id": str(code_package_id),
        },
        "source_text_hash_index": {
            "source_texts": [],
            "unparsed_texts": [{"relative_path": "pyproject.toml"}],
        },
        "source_object_state_index_ref": {"schema": "selected"},
    }

    async def _load_with_head(**kwargs: object):
        observed.update(kwargs)
        return {}, payload

    def _load_selected(**kwargs: object):
        observed["selected_relative_paths"] = kwargs["relative_paths"]
        return {
            "objects": [{"source_object_id": str(source_object_id)}],
            "path_source_object_index": [
                {
                    "relative_path": "pyproject.toml",
                    "source_object_ids": [str(source_object_id)],
                }
            ],
        }

    monkeypatch.setattr(
        snapshot_health,
        "load_current_code_package_text_snapshot_index_payload_with_head",
        _load_with_head,
    )
    monkeypatch.setattr(
        snapshot_health,
        "load_code_package_text_snapshot_source_object_state_index_selected",
        _load_selected,
    )
    monkeypatch.setattr(
        snapshot_health,
        "_snapshot_state_witness_is_healthy",
        lambda **_kwargs: True,
    )

    evidence = (
        await snapshot_health.load_code_package_selected_snapshot_health_evidence(
            branch_id=uuid4(),
            projection_hash="code-package",
            code_package_id=code_package_id,
            expected_head_commit_id=head_commit_id,
            expected_object_instance_graph_commit_id=object_instance_graph_commit_id,
            required_relative_paths=("pyproject.toml",),
            store=object(),  # type: ignore[arg-type]
        )
    )

    assert evidence is not None
    assert evidence.artifact_state_index["code_package_id"] == str(code_package_id)
    assert observed["include_source_object_index"] is False
    assert observed["selected_relative_paths"] == frozenset({"pyproject.toml"})


@pytest.mark.asyncio
async def test_selected_health_fails_closed_for_missing_required_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code_package_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()

    async def _load_with_head(**_kwargs: object):
        return {}, {
            "code_package_id": str(code_package_id),
            "head_commit_id": str(head_commit_id),
            "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
            "graph_hash_post": "sha256:graph",
            "artifact_state_index": {
                "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
                "code_package_id": str(code_package_id),
            },
            "source_text_hash_index": {
                "source_texts": [],
                "unparsed_texts": [],
            },
        }

    monkeypatch.setattr(
        snapshot_health,
        "load_current_code_package_text_snapshot_index_payload_with_head",
        _load_with_head,
    )
    monkeypatch.setattr(
        snapshot_health,
        "_snapshot_state_witness_is_healthy",
        lambda **_kwargs: True,
    )

    assert (
        await snapshot_health.load_code_package_selected_snapshot_health_evidence(
            branch_id=uuid4(),
            projection_hash="code-package",
            code_package_id=code_package_id,
            required_relative_paths=("pyproject.toml",),
            store=object(),  # type: ignore[arg-type]
        )
        is None
    )
