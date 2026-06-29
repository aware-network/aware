from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# History Ontology
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent

# Meta Ontology
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Meta Runtime
from aware_meta.graph.config.migration_artifacts import (
    ARTIFACT_ROLE_DIALECT_MIGRATION,
    ARTIFACT_ROLE_LANE_INDEX,
    ARTIFACT_ROLE_OCG_DELTA,
    MetaOcgMigrationArtifactError,
    build_ocg_migration_artifact_bundle,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.test_support import make_class_config, make_ocg_node, test_class_fqn


def _meta_class(name: str):
    return make_class_config(
        name,
        class_fqn=test_class_fqn(name),
        class_config_attribute_configs=[],
    )


def _schema_graph() -> tuple[ObjectConfigGraph, UUID]:
    meta_class_config = _meta_class("ClassConfig")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_class_config,
            class_config_id=meta_class_config.id,
            object_config_graph_id=schema_graph.id,
        )
    ]
    return schema_graph, meta_class_config.id


def _test_commit(
    *,
    key: str = "test-commit",
    parent_commit_id: UUID | None = None,
) -> Commit:
    commit = Commit(
        key=key,
        lane_id=uuid4(),
        author_id=uuid4(),
        created_at=datetime.now(UTC),
    )
    if parent_commit_id is not None:
        commit.commit_parents = [
            CommitParent(
                commit_id=commit.id,
                parent_commit_id=parent_commit_id,
            )
        ]
    return commit


def _test_change(*, key: str, type: ChangeType) -> Change:
    return Change(
        key=key,
        created_at=datetime.now(UTC),
        type=type,
        change_deltas=[],
    )


def _test_delta(
    *,
    change: Change,
    position: int,
    kind: ChangeDeltaKind,
    payload: JsonObject,
    property: str | None = None,
) -> ChangeDelta:
    return ChangeDelta(
        change_id=change.id,
        position=position,
        property=property,
        kind=kind,
        payload=payload,
    )


def _make_oig_commit(
    *,
    object_config_graph_id: UUID,
    projection_hash: str,
    graph_hash_pre: str,
    graph_hash_post: str,
    object_instance_graph_changes: list[ObjectInstanceGraphChange],
    parent_commit_id: UUID | None = None,
) -> ObjectInstanceGraphCommit:
    return ObjectInstanceGraphCommit(
        commit=_test_commit(parent_commit_id=parent_commit_id),
        object_instance_graph_changes=object_instance_graph_changes,
        object_instance_graph_key="test-worldline",
        object_instance_graph_name="test worldline",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        projection_hash=projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_identity_id=object_config_graph_id,
        object_instance_graph_id=object_config_graph_id,
    )


def _class_create_change(
    *,
    ocg_id: UUID,
    class_config_id: UUID,
    entity_id: UUID | None = None,
) -> ObjectInstanceGraphChange:
    class_instance_id = entity_id or uuid4()
    change = _test_change(key="class_config:create", type=ChangeType.create)
    change.change_deltas = [
        _test_delta(
            change=change,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(class_config_id)),
        ),
        _test_delta(
            change=change,
            position=1,
            property="name",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value="User"),
        ),
    ]
    ci_change = ClassInstanceChange(
        class_instance_id=class_instance_id,
        change=change,
    )
    return ObjectInstanceGraphChange(
        change=change,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )


async def _append_commit(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> None:
    await store.append(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
        root_object_id=commit.root_source_object_id,
    )


def test_producer_reconstructs_delta_and_writes_stable_artifacts(
    tmp_path: Path,
) -> None:
    async def _run() -> None:
        schema_graph, class_config_id = _schema_graph()
        store = FSCommitStore(root_dir=tmp_path)
        ocg_id = uuid4()
        branch_id = uuid4()
        projection_hash = "sha256:test:opg"
        commit = _make_oig_commit(
            object_config_graph_id=ocg_id,
            projection_hash=projection_hash,
            graph_hash_pre="sha256:test:pre",
            graph_hash_post="sha256:test:post",
            object_instance_graph_changes=[
                _class_create_change(
                    ocg_id=ocg_id,
                    class_config_id=class_config_id,
                )
            ],
        )
        await _append_commit(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )

        output_root = tmp_path / "artifacts"
        bundle = await build_ocg_migration_artifact_bundle(
            store=store,
            schema_graph=schema_graph,
            package_key="aware.test.package",
            object_config_graph_id=ocg_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            output_root=output_root,
        )
        second = await build_ocg_migration_artifact_bundle(
            store=store,
            schema_graph=schema_graph,
            package_key="aware.test.package",
            object_config_graph_id=ocg_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            output_root=output_root,
        )

        assert bundle.status == "ocg_migration_artifacts_ready"
        assert bundle.receipt["artifact_count"] == 3
        assert bundle.receipt["commit_count"] == 1
        assert [artifact.digest for artifact in bundle.artifacts] == [
            artifact.digest for artifact in second.artifacts
        ]
        assert all(
            artifact.path is not None and artifact.path.exists()
            for artifact in bundle.artifacts
        )

        by_role = bundle.artifacts_by_role()
        assert len(by_role[ARTIFACT_ROLE_LANE_INDEX]) == 1
        assert len(by_role[ARTIFACT_ROLE_OCG_DELTA]) == 1
        assert len(by_role[ARTIFACT_ROLE_DIALECT_MIGRATION]) == 1

        delta_artifact = by_role[ARTIFACT_ROLE_OCG_DELTA][0]
        assert delta_artifact.payload["delta_source"] == "oig_commit"
        assert delta_artifact.payload["source_object_instance_graph_id"] == str(ocg_id)
        delta_payload = delta_artifact.payload["object_config_graph_delta"]
        assert isinstance(delta_payload, dict)
        assert delta_payload["graph_hash_pre"] == commit.graph_hash_pre
        assert delta_payload["graph_hash_post"] == commit.graph_hash_post
        assert len(delta_payload["node_deltas"]) == 1

        dialect_artifact = by_role[ARTIFACT_ROLE_DIALECT_MIGRATION][0]
        assert dialect_artifact.payload["migration_kind"] == "unsupported_failfast"
        assert dialect_artifact.payload["node_delta_count"] == 1
        assert "unsupported_reason" in dialect_artifact.payload

        lane_index = bundle.lane_index.payload
        assert lane_index["source_object_instance_graph_id"] == str(ocg_id)
        commits = lane_index["commits"]
        assert isinstance(commits, list)
        assert commits[0]["commit_id"] == str(commit.commit.id)
        assert commits[0]["delta_digest"] == delta_artifact.digest

    asyncio.run(_run())


def test_producer_uses_valid_hint_and_emits_noop_dialect_artifact(
    tmp_path: Path,
) -> None:
    async def _run() -> None:
        schema_graph, _ = _schema_graph()
        store = FSCommitStore(root_dir=tmp_path)
        ocg_id = uuid4()
        branch_id = uuid4()
        projection_hash = "sha256:test:opg"
        commit = _make_oig_commit(
            object_config_graph_id=ocg_id,
            projection_hash=projection_hash,
            graph_hash_pre="sha256:test:pre",
            graph_hash_post="sha256:test:post",
            object_instance_graph_changes=[],
        )
        await _append_commit(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )

        delta = ObjectConfigGraphDelta(
            object_config_graph_id=ocg_id,
            language=CodeLanguage.aware,
            graph_hash_pre=None,
            graph_hash_post=None,
            node_deltas=[],
            warnings=[],
        )
        _ = store.put_ocg_delta_hint(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
            payload={
                "v": 1,
                "branch_id": str(branch_id),
                "projection_hash": projection_hash,
                "commit_id": str(commit.commit.id),
                "ocg_delta": delta.model_dump(
                    mode="json",
                    exclude_none=True,
                    by_alias=True,
                ),
            },
        )

        bundle = await build_ocg_migration_artifact_bundle(
            store=store,
            schema_graph=schema_graph,
            package_key="aware.test.package",
            object_config_graph_id=ocg_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        by_role = bundle.artifacts_by_role()
        assert by_role[ARTIFACT_ROLE_OCG_DELTA][0].payload["delta_source"] == "hint"
        assert (
            by_role[ARTIFACT_ROLE_DIALECT_MIGRATION][0].payload["migration_kind"]
            == "noop"
        )
        delta_payload = by_role[ARTIFACT_ROLE_OCG_DELTA][0].payload[
            "object_config_graph_delta"
        ]
        assert isinstance(delta_payload, dict)
        assert delta_payload["graph_hash_pre"] == commit.graph_hash_pre
        assert delta_payload["graph_hash_post"] == commit.graph_hash_post

    asyncio.run(_run())


def test_producer_fails_closed_on_mismatched_hint(tmp_path: Path) -> None:
    async def _run() -> None:
        schema_graph, _ = _schema_graph()
        store = FSCommitStore(root_dir=tmp_path)
        ocg_id = uuid4()
        branch_id = uuid4()
        projection_hash = "sha256:test:opg"
        commit = _make_oig_commit(
            object_config_graph_id=ocg_id,
            projection_hash=projection_hash,
            graph_hash_pre="sha256:test:pre",
            graph_hash_post="sha256:test:post",
            object_instance_graph_changes=[],
        )
        await _append_commit(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )

        delta = ObjectConfigGraphDelta(
            object_config_graph_id=ocg_id,
            language=CodeLanguage.aware,
            graph_hash_pre=None,
            graph_hash_post=None,
            node_deltas=[],
            warnings=[],
        )
        hint_path = store.ocg_delta_hint_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        hint_path.parent.mkdir(parents=True, exist_ok=True)
        hint_path.write_text(
            json.dumps(
                {
                    "v": 1,
                    "branch_id": str(uuid4()),
                    "projection_hash": projection_hash,
                    "commit_id": str(commit.commit.id),
                    "ocg_delta": delta.model_dump(
                        mode="json",
                        exclude_none=True,
                        by_alias=True,
                    ),
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(MetaOcgMigrationArtifactError, match="branch_id mismatch"):
            await build_ocg_migration_artifact_bundle(
                store=store,
                schema_graph=schema_graph,
                package_key="aware.test.package",
                object_config_graph_id=ocg_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
            )

    asyncio.run(_run())


def test_producer_fails_without_lane_head(tmp_path: Path) -> None:
    async def _run() -> None:
        schema_graph, _ = _schema_graph()
        store = FSCommitStore(root_dir=tmp_path)
        with pytest.raises(MetaOcgMigrationArtifactError, match="without lane HEAD"):
            await build_ocg_migration_artifact_bundle(
                store=store,
                schema_graph=schema_graph,
                package_key="aware.test.package",
                object_config_graph_id=uuid4(),
                branch_id=uuid4(),
                projection_hash="sha256:test:opg",
            )

    asyncio.run(_run())


def test_producer_fails_when_head_references_missing_commit(tmp_path: Path) -> None:
    async def _run() -> None:
        schema_graph, _ = _schema_graph()
        store = FSCommitStore(root_dir=tmp_path)
        branch_id = uuid4()
        projection_hash = "sha256:test:opg"
        missing_commit_id = uuid4()
        lane_dir = tmp_path / ".aware" / "oig" / str(branch_id) / projection_hash
        lane_dir.mkdir(parents=True, exist_ok=True)
        (lane_dir / "HEAD.json").write_text(
            json.dumps(
                {
                    "v": 1,
                    "commit_id": str(missing_commit_id),
                    "graph_hash_post": "sha256:test:post",
                    "object_instance_graph_id": str(uuid4()),
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(MetaOcgMigrationArtifactError, match="missing commit"):
            await build_ocg_migration_artifact_bundle(
                store=store,
                schema_graph=schema_graph,
                package_key="aware.test.package",
                object_config_graph_id=uuid4(),
                branch_id=branch_id,
                projection_hash=projection_hash,
            )

    asyncio.run(_run())


def test_producer_has_no_workspace_or_env_artifacts_dependency() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/config/migration_artifacts.py"
    ).read_text(encoding="utf-8")
    assert "WorkspaceMaterializedArtifactRef" not in source
    assert "aware_workspace" not in source
    assert "environment_artifacts" not in source
