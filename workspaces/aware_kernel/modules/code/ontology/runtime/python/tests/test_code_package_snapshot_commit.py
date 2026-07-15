from __future__ import annotations

import json
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code.package import snapshot_commit, snapshot_index, snapshot_source_text
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_plan import CodeContentPlan, CodeSectionPlan
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.package.code_package_artifact import CodePackageArtifactRef
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_meta.graph.instance.commit.state_snapshot_segments import (
    commit_state_witness_cursor_summary_payload,
)
from aware_meta.graph.instance.commit.state_witness import (
    COMMIT_STATE_WITNESS_CURSOR_SCHEMA,
    CommitStateWitnessCursorChunkSummary,
    CommitStateWitnessCursorSummary,
    compute_commit_state_witness_cursor_hash,
)


def test_snapshot_introspection_derives_association_code_id() -> None:
    code_package = CodePackage.model_construct(id=uuid4())
    code = Code.model_construct(id=uuid4())
    package_code = CodePackageCode.model_construct(id=uuid4(), code=code)

    source = snapshot_commit._code_package_snapshot_introspection_source(
        source=package_code,
        code_package=code_package,
        code_package_config_id=uuid4(),
        surface="runtime",
    )

    assert source.try_field_value("code_id") == (True, code.id)


def test_cursor_snapshot_index_hit_requires_backing_segment_metadata(
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    class SnapshotStore:
        def snapshot_state_class_segment_index_metadata(self, **kwargs):
            calls.append(dict(kwargs))
            return object()

    chunk = CommitStateWitnessCursorChunkSummary(
        index=0,
        first_segment_key="class:00000000-0000-0000-0000-000000000001",
        last_segment_key="class:00000000-0000-0000-0000-000000000001",
        segment_count=1,
        row_count=3,
        digest="chunk-digest",
    )
    cursor_hash = compute_commit_state_witness_cursor_hash((chunk,))
    summary = CommitStateWitnessCursorSummary(
        schema=COMMIT_STATE_WITNESS_CURSOR_SCHEMA,
        state_hash=None,
        legacy_witness_hash=None,
        cursor_hash=cursor_hash,
        row_count=3,
        segment_count=1,
        chunk_size=64,
        chunks=(chunk,),
    )
    payload = {
        "graph_hash_post": cursor_hash,
        "state_snapshot": {
            "state_snapshot_kind": "class_segment_index",
            "state_snapshot_graph_hash": cursor_hash,
            "state_snapshot_graph_hash_source": "witness_cursor_hash",
            "state_snapshot_witness_cursor": (
                commit_state_witness_cursor_summary_payload(summary)
            ),
            "state_snapshot_row_count": 3,
            "state_snapshot_segment_count": 1,
        },
    }

    monkeypatch.setattr(
        snapshot_commit,
        "FSSnapshotStore",
        lambda: SnapshotStore(),
    )

    branch_id = uuid4()
    commit_id = uuid4()
    assert snapshot_commit._code_package_text_snapshot_state_snapshot_index_hit(
        payload=payload,
        branch_id=branch_id,
        projection_hash="projection",
        commit_id=commit_id,
    )
    assert calls == [
        {
            "branch_id": branch_id,
            "projection_hash": "projection",
            "commit_id": commit_id,
            "expected_graph_hash": cursor_hash,
        }
    ]

    class MissingSnapshotStore:
        def snapshot_state_class_segment_index_metadata(self, **_kwargs):
            return None

    monkeypatch.setattr(
        snapshot_commit,
        "FSSnapshotStore",
        lambda: MissingSnapshotStore(),
    )
    assert not snapshot_commit._code_package_text_snapshot_state_snapshot_index_hit(
        payload=payload,
        branch_id=branch_id,
        projection_hash="projection",
        commit_id=commit_id,
    )


@pytest.mark.asyncio
async def test_exact_head_snapshot_state_requires_matching_healthy_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_code.package import snapshot_health

    code_package_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    observed: dict[str, object] = {}

    async def _load_evidence(
        **kwargs: object,
    ) -> snapshot_health.CodePackageSelectedSnapshotHealthEvidence | None:
        observed.update(kwargs)
        if kwargs["expected_head_commit_id"] != head_commit_id:
            return None
        return snapshot_health.CodePackageSelectedSnapshotHealthEvidence(
            code_package_id=code_package_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
            graph_hash_post="sha256:graph",
            snapshot_fingerprint="sha256:snapshot",
            source_snapshot_fingerprint="sha256:source",
            artifact_state_index={},
            required_relative_paths=tuple(kwargs["required_relative_paths"]),
        )

    monkeypatch.setattr(
        snapshot_health,
        "load_code_package_selected_snapshot_health_evidence",
        _load_evidence,
    )

    assert await snapshot_commit.has_code_package_text_snapshot_state_at_head(
        branch_id=uuid4(),
        projection_hash="code-package",
        code_package_id=code_package_id,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    assert observed["expected_head_commit_id"] == head_commit_id
    assert await snapshot_commit.has_code_package_text_snapshot_state_at_head(
        branch_id=uuid4(),
        projection_hash="code-package",
        code_package_id=code_package_id,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        required_relative_paths=("pyproject.toml",),
    )

    assert not await snapshot_commit.has_code_package_text_snapshot_state_at_head(
        branch_id=uuid4(),
        projection_hash="code-package",
        code_package_id=code_package_id,
        head_commit_id=uuid4(),
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )


@pytest.mark.asyncio
async def test_noop_snapshot_index_result_uses_supplied_payload(monkeypatch) -> None:
    def raising_index_hit(**_kwargs):
        raise AssertionError("full snapshot index reader was called")

    monkeypatch.setattr(
        snapshot_commit,
        "_code_package_text_snapshot_index_hit",
        raising_index_hit,
    )

    class SnapshotStore:
        def snapshot_state_class_segment_index_metadata(self, **_kwargs):
            return object()

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", SnapshotStore)

    code_package_id = uuid4()
    code_package_config_id = uuid4()
    domain_oig_id = uuid4()
    head_commit_id = uuid4()
    oig_commit_id = uuid4()
    chunk = CommitStateWitnessCursorChunkSummary(
        index=0,
        first_segment_key="class:00000000-0000-0000-0000-000000000001",
        last_segment_key="class:00000000-0000-0000-0000-000000000001",
        segment_count=1,
        row_count=3,
        digest="chunk-digest",
    )
    cursor_hash = compute_commit_state_witness_cursor_hash((chunk,))
    summary = CommitStateWitnessCursorSummary(
        schema=COMMIT_STATE_WITNESS_CURSOR_SCHEMA,
        state_hash=None,
        legacy_witness_hash=None,
        cursor_hash=cursor_hash,
        row_count=3,
        segment_count=1,
        chunk_size=64,
        chunks=(chunk,),
    )
    payload = {
        "v": snapshot_commit._CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
        "snapshot_fingerprint": "snapshot-fingerprint",
        "source_snapshot_fingerprint": "source-fingerprint",
        "code_package_id": str(code_package_id),
        "commit_id": str(head_commit_id),
        "head_commit_id": str(head_commit_id),
        "object_instance_graph_commit_id": str(oig_commit_id),
        "object_instance_graph_id": str(domain_oig_id),
        "graph_hash_post": cursor_hash,
        "object_count": 3,
        "change_count": 0,
        "state_snapshot": {
            "state_snapshot_kind": "class_segment_index",
            "state_snapshot_graph_hash": cursor_hash,
            "state_snapshot_graph_hash_source": "witness_cursor_hash",
            "state_snapshot_witness_cursor": (
                commit_state_witness_cursor_summary_payload(summary)
            ),
            "state_snapshot_row_count": 3,
            "state_snapshot_segment_count": 1,
        },
    }

    result = await snapshot_commit._code_package_text_snapshot_index_noop_result(
        store=SimpleNamespace(),
        branch_id=uuid4(),
        projection_hash="projection",
        code_package_id=code_package_id,
        code_package_config_id=code_package_config_id,
        package_name="aware-test-package",
        language=CodeLanguage.python,
        surface="runtime",
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root="generated/aware-test-package",
        sources_root="generated/aware-test-package/aware_test_package",
        fqn_prefix="aware_test_package",
        domain_oig_id=domain_oig_id,
        snapshot_fingerprint="snapshot-fingerprint",
        snapshot_index_payload=payload,
    )

    assert result is not None
    assert result.commit_id == head_commit_id
    assert result.object_instance_graph_commit_id == oig_commit_id
    assert result.object_count == 3
    assert result.change_count == 0


@pytest.mark.asyncio
async def test_snapshot_index_section_bundle_loads_only_when_requested(
    tmp_path,
) -> None:
    class FakeStore:
        def __init__(self, aware_root, head):
            self.aware_root = aware_root
            self._head = head

        async def head(self, *, branch_id, projection_hash):
            assert branch_id == expected_branch_id
            assert projection_hash == expected_projection_hash
            return self._head

    expected_branch_id = uuid4()
    expected_projection_hash = "projection"
    code_package_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    object_instance_graph_id = uuid4()
    graph_hash_post = "sha256:graph"
    head = {
        "commit_id": str(head_commit_id),
        "graph_hash_post": graph_hash_post,
        "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
        "object_instance_graph_id": str(object_instance_graph_id),
    }
    store = FakeStore(tmp_path, head)
    artifact_state_index = {
        "schema": snapshot_commit.CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
        "code_package_id": str(code_package_id),
        "artifact_count": 0,
        "artifacts": [],
        "signature_hash": "sha256:artifacts",
    }
    source_path_object_id = uuid4()
    source_object_state_index = {
        "schema": snapshot_commit.CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
        "object_count": 2,
        "objects": [
            {
                "source_object_id": str(code_package_id),
                "class_config_id": str(uuid4()),
                "class_instance_id": str(uuid4()),
                "signature_hash": "sha256:root",
            },
            {
                "source_object_id": str(source_path_object_id),
                "class_config_id": str(uuid4()),
                "class_instance_id": str(uuid4()),
                "signature_hash": "sha256:path",
            },
        ],
        "path_source_object_index": [
            {
                "relative_path": "aware_test_package/module.py",
                "source_object_ids": [str(source_path_object_id)],
            }
        ],
    }
    source_text_hash_index = {
        "schema": "aware.code.package.source_text_hash_index.v1",
        "source_text_count": 0,
        "unparsed_text_count": 0,
        "source_texts": [],
        "unparsed_texts": [],
        "signature_hash": "sha256:text",
    }

    snapshot_index.write_code_package_text_snapshot_index(
        store=store,
        branch_id=expected_branch_id,
        projection_hash=expected_projection_hash,
        code_package_id=code_package_id,
        snapshot_fingerprint="snapshot",
        source_snapshot_fingerprint="source",
        commit_id=head_commit_id,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash_post,
        object_count=3,
        change_count=0,
        artifact_state_index=artifact_state_index,
        state_snapshot_metadata={"state_snapshot_kind": "class_segment_index"},
        source_object_state_index=source_object_state_index,
        source_text_hash_index=source_text_hash_index,
    )

    _head, root_payload = (
        await snapshot_index.load_current_code_package_text_snapshot_index_payload_with_head(
            store=store,
            branch_id=expected_branch_id,
            projection_hash=expected_projection_hash,
            code_package_id=code_package_id,
            include_sections=False,
        )
    )

    assert root_payload is not None
    assert "section_bundle_ref" in root_payload
    assert "artifact_state_index" not in root_payload
    assert "source_object_state_index" not in root_payload
    assert "source_text_hash_index" not in root_payload

    _head, sectioned_payload = (
        await snapshot_index.load_current_code_package_text_snapshot_index_payload_with_head(
            store=store,
            branch_id=expected_branch_id,
            projection_hash=expected_projection_hash,
            code_package_id=code_package_id,
            include_sections=True,
        )
    )

    assert sectioned_payload is not None
    assert sectioned_payload["artifact_state_index"] == artifact_state_index
    assert sectioned_payload["source_object_state_index"]["schema"] == (
        source_object_state_index["schema"]
    )
    assert sectioned_payload["source_object_state_index"]["object_count"] == 2
    assert {
        UUID(str(row["source_object_id"]))
        for row in sectioned_payload["source_object_state_index"]["objects"]
    } == {code_package_id, source_path_object_id}
    assert (
        sectioned_payload["source_object_state_index"]["path_source_object_index"]
        == source_object_state_index["path_source_object_index"]
    )
    assert sectioned_payload["source_text_hash_index"] == source_text_hash_index

    _head, sectioned_without_source_payload = (
        await snapshot_index.load_current_code_package_text_snapshot_index_payload_with_head(
            store=store,
            branch_id=expected_branch_id,
            projection_hash=expected_projection_hash,
            code_package_id=code_package_id,
            include_sections=True,
            include_source_object_index=False,
        )
    )

    assert sectioned_without_source_payload is not None
    assert "source_object_state_index" not in sectioned_without_source_payload
    assert isinstance(
        sectioned_without_source_payload["source_object_state_index_ref"],
        dict,
    )
    selected_source_object_index = snapshot_index.load_code_package_text_snapshot_source_object_state_index_selected(
        store=store,
        branch_id=expected_branch_id,
        projection_hash=expected_projection_hash,
        code_package_id=code_package_id,
        snapshot_index_payload=sectioned_without_source_payload,
        relative_paths=frozenset({"aware_test_package/module.py"}),
    )
    assert selected_source_object_index is not None
    assert selected_source_object_index["schema"] == (
        snapshot_commit.CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA
    )
    assert selected_source_object_index["object_count"] == 2
    assert {
        UUID(str(row["source_object_id"]))
        for row in selected_source_object_index["objects"]
    } == {code_package_id, source_path_object_id}


@pytest.mark.asyncio
async def test_snapshot_index_rejects_payload_when_head_commit_record_missing(
    tmp_path,
) -> None:
    class FakeStore:
        def __init__(self, aware_root, head):
            self.aware_root = aware_root
            self._head = head

        async def head(self, *, branch_id, projection_hash):
            assert branch_id == expected_branch_id
            assert projection_hash == expected_projection_hash
            return self._head

        async def get_commit_record(self, *, branch_id, projection_hash, commit_id):
            assert branch_id == expected_branch_id
            assert projection_hash == expected_projection_hash
            assert commit_id == head_commit_id
            return None

    expected_branch_id = uuid4()
    expected_projection_hash = "projection"
    code_package_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    object_instance_graph_id = uuid4()
    graph_hash_post = "sha256:graph"
    head = {
        "commit_id": str(head_commit_id),
        "graph_hash_post": graph_hash_post,
        "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
        "object_instance_graph_id": str(object_instance_graph_id),
    }
    store = FakeStore(tmp_path, head)

    snapshot_index.write_code_package_text_snapshot_index(
        store=store,
        branch_id=expected_branch_id,
        projection_hash=expected_projection_hash,
        code_package_id=code_package_id,
        snapshot_fingerprint="snapshot",
        source_snapshot_fingerprint="source",
        commit_id=head_commit_id,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash_post,
        object_count=0,
        change_count=0,
        artifact_state_index={
            "schema": snapshot_commit.CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
            "code_package_id": str(code_package_id),
            "artifact_count": 0,
            "artifacts": [],
        },
        state_snapshot_metadata={"state_snapshot_kind": "class_segment_index"},
        source_object_state_index={
            "schema": snapshot_commit.CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
            "object_count": 0,
            "objects": [],
        },
        source_text_hash_index={
            "schema": "aware.code.package.source_text_hash_index.v1",
            "source_text_count": 0,
            "unparsed_text_count": 0,
            "source_texts": [],
            "unparsed_texts": [],
        },
    )

    _head, payload = (
        await snapshot_index.load_current_code_package_text_snapshot_index_payload_with_head(
            store=store,
            branch_id=expected_branch_id,
            projection_hash=expected_projection_hash,
            code_package_id=code_package_id,
            include_sections=False,
        )
    )

    assert payload is None


@pytest.mark.asyncio
async def test_snapshot_index_uses_commit_health_without_body_hydration() -> None:
    from types import SimpleNamespace

    branch_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_id = uuid4()
    head = {
        "commit_id": str(head_commit_id),
        "graph_hash_post": "sha256:graph",
        "object_instance_graph_id": str(object_instance_graph_id),
    }

    class FakeStore:
        async def get_commit_health_metadata(self, **kwargs: object):
            assert kwargs["commit_id"] == head_commit_id
            return SimpleNamespace(
                commit_id=head_commit_id,
                graph_hash_post="sha256:graph",
                object_instance_graph_id=object_instance_graph_id,
            )

        async def get_commit_record(self, **_kwargs: object):
            raise AssertionError("commit body was hydrated")

    assert await snapshot_index._snapshot_index_head_commit_record_readable(
        store=FakeStore(),  # type: ignore[arg-type]
        branch_id=branch_id,
        projection_hash="projection",
        head=head,
    )


@pytest.mark.asyncio
async def test_snapshot_commit_head_guard_rejects_missing_commit_record() -> None:
    class FakeStore:
        async def get_commit_record(self, *, branch_id, projection_hash, commit_id):
            assert branch_id == expected_branch_id
            assert projection_hash == expected_projection_hash
            assert commit_id == head_commit_id
            return None

    expected_branch_id = uuid4()
    expected_projection_hash = "projection"
    head_commit_id = uuid4()

    assert not await snapshot_commit._code_package_text_snapshot_head_commit_record_readable(
        store=FakeStore(),
        branch_id=expected_branch_id,
        projection_hash=expected_projection_hash,
        head={"commit_id": str(head_commit_id)},
    )


@pytest.mark.asyncio
async def test_noop_snapshot_index_payload_miss_skips_full_reader(monkeypatch) -> None:
    def raising_index_hit(**_kwargs):
        raise AssertionError("full snapshot index reader was called")

    monkeypatch.setattr(
        snapshot_commit,
        "_code_package_text_snapshot_index_hit",
        raising_index_hit,
    )

    result = await snapshot_commit._code_package_text_snapshot_index_noop_result(
        store=SimpleNamespace(),
        branch_id=uuid4(),
        projection_hash="projection",
        code_package_id=uuid4(),
        code_package_config_id=uuid4(),
        package_name="aware-test-package",
        language=CodeLanguage.python,
        surface="runtime",
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root="generated/aware-test-package",
        sources_root="generated/aware-test-package/aware_test_package",
        fqn_prefix="aware_test_package",
        domain_oig_id=uuid4(),
        snapshot_fingerprint="current-fingerprint",
        snapshot_index_payload={
            "v": snapshot_commit._CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
            "snapshot_fingerprint": "previous-fingerprint",
        },
    )

    assert result is None


@pytest.mark.asyncio
async def test_source_object_state_index_is_changed_text_scoped() -> None:
    code_package_id = uuid4()
    code_package_config_id = uuid4()
    domain_oig_id = uuid4()

    _seed_package, seed_objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'seed'\n",
                "aware_test_package/other.py": "VALUE = 'same'\n",
            },
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
        )
    )
    _update_package, update_objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'updated'\n",
                "aware_test_package/other.py": "VALUE = 'same'\n",
            },
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
        )
    )

    seed_states = snapshot_commit._code_package_source_object_states_by_source_id(
        domain_oig_id=domain_oig_id,
        objects_by_id=seed_objects_by_id,
    )
    update_states = snapshot_commit._code_package_source_object_states_by_source_id(
        domain_oig_id=domain_oig_id,
        objects_by_id=update_objects_by_id,
    )
    changed_source_ids = {
        source_object_id
        for source_object_id, update_state in update_states.items()
        if seed_states.get(source_object_id) != update_state
    }

    assert len(changed_source_ids) == 1
    changed_object = update_objects_by_id[next(iter(changed_source_ids))]
    assert changed_object.__class__.__name__ == "ContentPartText"


@pytest.mark.asyncio
async def test_source_object_signature_fast_fields_match_generic() -> None:
    for (
        cls,
        field_names,
    ) in snapshot_commit._CODE_PACKAGE_SOURCE_SIGNATURE_FIELD_NAMES_BY_CLASS.items():
        assert field_names == tuple(
            name
            for name in sorted(str(item) for item in cls.model_fields)
            if name != "id"
        )

    _package, objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(
            code_package_id=uuid4(),
            code_package_config_id=uuid4(),
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'seed'\n",
            },
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
        )
    )

    for source_object in objects_by_id.values():
        if (
            source_object.__class__
            not in snapshot_commit._CODE_PACKAGE_SOURCE_SIGNATURE_FIELD_NAMES_BY_CLASS
        ):
            continue
        assert snapshot_commit._code_package_source_object_signature_fields(
            source_object,
        ) == snapshot_commit._code_package_source_object_signature_fields_generic(
            source_object,
        )


@pytest.mark.asyncio
async def test_input_source_object_states_match_full_object_states() -> None:
    code_package_id = uuid4()
    code_package_config_id = uuid4()
    domain_oig_id = uuid4()
    content_plan = CodeContentPlan(
        language=CodeLanguage.python,
        content_text="def value() -> int:\n    return 1\n",
        section_plans=[
            CodeSectionPlan(
                section_key="function:value",
                section_type=CodeSectionType.function,
                qualname="value",
                identity_hash="sha256:value",
                byte_start=0,
                byte_end=32,
                metadata={"kind": "function"},
            )
        ],
    )
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package_id,
        output_key="python.runtime",
        artifact_key="runtime/module.py",
        artifact_family="python",
        artifact_role="runtime_file",
        required_for=["workspace_revision"],
        producer_key="aware_python.runtime",
        relative_path="aware_test_package/module.py",
        digest="sha256:module",
    )
    plans_by_relative_path = (
        snapshot_commit._code_package_snapshot_plans_by_relative_path(
            language=CodeLanguage.python,
            source_texts_by_relative_path={},
            source_plans_by_relative_path={
                "aware_test_package/module.py": content_plan,
            },
            unparsed_texts_by_relative_path={},
        )
    )

    _package, objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={
                "aware_test_package/module.py": content_plan,
            },
            unparsed_texts_by_relative_path={},
            path_roles_by_relative_path={},
            code_package_artifact_refs=(artifact_ref,),
            plans_by_relative_path=plans_by_relative_path,
        )
    )

    object_states = snapshot_commit._code_package_source_object_states_by_source_id(
        domain_oig_id=domain_oig_id,
        objects_by_id=objects_by_id,
    )
    input_states = (
        snapshot_commit._code_package_source_object_states_from_snapshot_inputs(
            domain_oig_id=domain_oig_id,
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            plans_by_relative_path=plans_by_relative_path,
            path_roles_by_relative_path={},
            code_package_artifact_refs=(artifact_ref,),
        )
    )

    assert input_states == object_states


@pytest.mark.asyncio
async def test_partial_snapshot_object_build_keeps_topology_only() -> None:
    code_package_id = uuid4()
    code_package_config_id = uuid4()
    domain_oig_id = uuid4()
    seed_plans = snapshot_commit._code_package_snapshot_plans_by_relative_path(
        language=CodeLanguage.python,
        source_texts_by_relative_path={},
        source_plans_by_relative_path={},
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'seed'\n",
            "aware_test_package/other.py": "VALUE = 'same'\n",
        },
    )
    update_plans = snapshot_commit._code_package_snapshot_plans_by_relative_path(
        language=CodeLanguage.python,
        source_texts_by_relative_path={},
        source_plans_by_relative_path={},
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'updated'\n",
            "aware_test_package/other.py": "VALUE = 'same'\n",
        },
    )
    _full_update_package, full_update_objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'updated'\n",
                "aware_test_package/other.py": "VALUE = 'same'\n",
            },
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
            plans_by_relative_path=update_plans,
        )
    )
    seed_states = (
        snapshot_commit._code_package_source_object_states_from_snapshot_inputs(
            domain_oig_id=domain_oig_id,
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            plans_by_relative_path=seed_plans,
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
        )
    )
    update_states = (
        snapshot_commit._code_package_source_object_states_from_snapshot_inputs(
            domain_oig_id=domain_oig_id,
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            plans_by_relative_path=update_plans,
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
        )
    )
    changed_source_object_ids = {
        source_object_id
        for source_object_id, update_state in update_states.items()
        if seed_states.get(source_object_id) != update_state
    }
    changed_source_object_ids.add(code_package_id)

    partial_package, partial_objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-test-package",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root="generated/aware-test-package",
            sources_root="generated/aware-test-package/aware_test_package",
            fqn_prefix="aware_test_package",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'updated'\n",
                "aware_test_package/other.py": "VALUE = 'same'\n",
            },
            path_roles_by_relative_path={},
            code_package_artifact_refs=(),
            plans_by_relative_path=update_plans,
            full_source_object_ids=frozenset(changed_source_object_ids),
        )
    )

    assert len(changed_source_object_ids) == 2
    assert len(partial_objects_by_id) == 2
    assert set(partial_objects_by_id) == changed_source_object_ids
    assert len(partial_objects_by_id) < len(full_update_objects_by_id)
    assert len(partial_package.code_package_codes) == 2
    assert all(item.code is not None for item in partial_package.code_package_codes)


def test_changed_path_source_state_reuses_unchanged_path_states() -> None:
    code_package_id = uuid4()
    code_package_config_id = uuid4()
    domain_oig_id = uuid4()
    common_kwargs = {
        "domain_oig_id": domain_oig_id,
        "code_package_id": code_package_id,
        "code_package_config_id": code_package_config_id,
        "package_name": "aware-test-package",
        "language": CodeLanguage.python,
        "surface": "runtime",
        "manifest_kind": "pyproject_toml",
        "manifest_relative_path": "pyproject.toml",
        "package_root": "generated/aware-test-package",
        "sources_root": "generated/aware-test-package/aware_test_package",
        "fqn_prefix": "aware_test_package",
        "path_roles_by_relative_path": {},
        "code_package_artifact_refs": (),
    }
    seed_plans = snapshot_commit._code_package_snapshot_plans_by_relative_path(
        language=CodeLanguage.python,
        source_texts_by_relative_path={},
        source_plans_by_relative_path={},
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'seed'\n",
            "aware_test_package/other.py": "VALUE = 'same'\n",
        },
    )
    update_plans = snapshot_commit._code_package_snapshot_plans_by_relative_path(
        language=CodeLanguage.python,
        source_texts_by_relative_path={},
        source_plans_by_relative_path={},
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'updated'\n",
            "aware_test_package/other.py": "VALUE = 'same'\n",
        },
    )
    seed_build = (
        snapshot_commit._code_package_source_object_state_build_from_snapshot_inputs(
            **common_kwargs,
            plans_by_relative_path=seed_plans,
        )
    )
    update_build = (
        snapshot_commit._code_package_source_object_state_build_from_snapshot_inputs(
            **common_kwargs,
            plans_by_relative_path=update_plans,
        )
    )
    previous_index = (
        snapshot_commit._code_package_source_object_state_index_from_states(
            seed_build.states_by_id.values(),
            source_object_path_index=seed_build.path_source_object_ids,
        )
    )
    assert "signature_hash" not in previous_index
    assert (
        snapshot_commit._code_package_source_object_states_from_index_payload(
            {"source_object_state_index": previous_index},
        )
        == seed_build.states_by_id
    )
    assert (
        snapshot_commit._code_package_source_object_path_index_from_index_payload(
            {"source_object_state_index": previous_index},
        )
        == seed_build.path_source_object_ids
    )
    previous_source_index_view = (
        snapshot_commit._code_package_source_object_raw_index_view_from_index_payload(
            {"source_object_state_index": previous_index},
        )
    )
    assert previous_source_index_view is not None

    merged = (
        snapshot_commit._code_package_changed_path_source_state_from_snapshot_inputs(
            **common_kwargs,
            plans_by_relative_path=update_plans,
            changed_relative_paths=frozenset(("aware_test_package/module.py",)),
            previous_source_index_view=previous_source_index_view,
        )
    )

    assert merged is not None
    assert merged.source_object_path_index == update_build.path_source_object_ids
    assert merged.source_object_state_index["schema"] == (
        snapshot_commit.CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA
    )
    assert merged.source_object_state_index["base_schema"] == (
        snapshot_commit.CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA
    )
    assert merged.source_object_state_index["object_count"] == len(
        update_build.states_by_id,
    )
    assert merged.source_object_state_index["changed_object_count"] == len(
        merged.changed_source_object_ids,
    )
    assert merged.source_object_state_index["changed_path_count"] == 1
    assert (
        snapshot_commit._code_package_source_object_states_from_index_payload(
            {"source_object_state_index": merged.source_object_state_index},
        )
        is None
    )
    overlay_raw_view = (
        snapshot_commit._code_package_source_object_raw_index_view_from_index_payload(
            {"source_object_state_index": merged.source_object_state_index},
        )
    )
    assert overlay_raw_view is not None
    assert overlay_raw_view.partial is True
    assert overlay_raw_view.object_count == len(update_build.states_by_id)
    assert set(overlay_raw_view.path_source_object_ids) == {
        "aware_test_package/module.py",
    }
    overlay_source_object_ids = {
        UUID(str(row["source_object_id"])) for row in overlay_raw_view.object_rows
    }
    assert set(merged.changed_source_object_ids) <= overlay_source_object_ids
    assert (
        set(overlay_raw_view.path_source_object_ids["aware_test_package/module.py"])
        <= overlay_source_object_ids
    )
    assert len(overlay_raw_view.object_rows) < len(update_build.states_by_id)
    overlay_reuse = (
        snapshot_commit._code_package_changed_path_source_state_from_snapshot_inputs(
            **common_kwargs,
            plans_by_relative_path=update_plans,
            changed_relative_paths=frozenset(("aware_test_package/module.py",)),
            previous_source_index_view=overlay_raw_view,
        )
    )
    assert overlay_reuse is not None
    assert overlay_reuse.source_object_count == len(update_build.states_by_id)
    assert merged.source_object_count == len(update_build.states_by_id)
    assert merged.build_relationship_topology is False
    assert code_package_id in merged.changed_source_object_ids
    assert code_package_id in merged.changed_source_states_by_id
    unchanged_path_ids = set(
        update_build.path_source_object_ids["aware_test_package/other.py"],
    )
    assert not (unchanged_path_ids & set(merged.changed_source_object_ids))
    assert not (unchanged_path_ids & set(merged.changed_source_states_by_id))


def test_snapshot_plan_index_can_be_changed_path_scoped() -> None:
    plans = snapshot_commit._code_package_snapshot_plans_by_relative_path(
        language=CodeLanguage.python,
        source_texts_by_relative_path={},
        source_plans_by_relative_path={},
        unparsed_texts_by_relative_path={
            "pkg/changed.py": "VALUE = 'updated'\n",
            "pkg/unchanged.py": "VALUE = 'same'\n",
        },
        include_relative_paths=frozenset(("pkg/changed.py",)),
    )

    assert tuple(plans) == ("pkg/changed.py",)
    assert plans["pkg/changed.py"].content_text == "VALUE = 'updated'\n"


def test_snapshot_plan_index_scoped_mode_still_rejects_duplicate_paths() -> None:
    with pytest.raises(RuntimeError, match="duplicate parsed/unparsed path"):
        snapshot_commit._code_package_snapshot_plans_by_relative_path(
            language=CodeLanguage.python,
            source_texts_by_relative_path={},
            source_plans_by_relative_path={
                "pkg/unchanged.py": CodeContentPlan(
                    language=CodeLanguage.python.value,
                    content_text="VALUE = 'same'\n",
                    section_plans=[],
                ),
            },
            unparsed_texts_by_relative_path={
                "pkg/changed.py": "VALUE = 'updated'\n",
                "pkg/unchanged.py": "VALUE = 'same'\n",
            },
            include_relative_paths=frozenset(("pkg/changed.py",)),
        )


def test_direct_relationship_context_reuses_runtime_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_commit._clear_code_package_direct_relationship_context_cache_for_tests()
    call_counts = {
        "relationship_attrs": 0,
        "include_attrs": 0,
        "relationship_configs": 0,
    }

    def _relationship_attrs(**_kwargs: object) -> dict[object, set[object]]:
        call_counts["relationship_attrs"] += 1
        return {}

    def _include_attrs(**_kwargs: object) -> dict[object, set[object]]:
        call_counts["include_attrs"] += 1
        return {}

    def _relationship_configs(**_kwargs: object) -> dict[object, object]:
        call_counts["relationship_configs"] += 1
        return {}

    monkeypatch.setattr(
        snapshot_commit,
        "build_relationship_attribute_config_ids_by_class_config_id",
        _relationship_attrs,
    )
    monkeypatch.setattr(
        snapshot_commit,
        "build_include_relationship_attribute_config_ids_by_class_config_id",
        _include_attrs,
    )
    monkeypatch.setattr(
        snapshot_commit,
        "_code_package_relationship_configs_by_key",
        _relationship_configs,
    )

    index = SimpleNamespace(
        ocg=SimpleNamespace(id=uuid4()),
        class_configs_by_id={},
    )
    opg = SimpleNamespace(id=uuid4())

    first = snapshot_commit._code_package_direct_relationship_context(
        index=index,
        opg=opg,
    )
    second = snapshot_commit._code_package_direct_relationship_context(
        index=index,
        opg=opg,
    )

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert first.relationship_configs_by_key == second.relationship_configs_by_key
    assert call_counts == {
        "relationship_attrs": 1,
        "include_attrs": 1,
        "relationship_configs": 1,
    }


def test_write_code_package_text_snapshot_index_skips_existing_parse(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SimpleNamespace(aware_root=tmp_path)
    branch_id = uuid4()
    projection_hash = "CodePackage"
    code_package_id = uuid4()
    path = snapshot_index.code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    def _unexpected_read(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("snapshot-index writes must not parse existing JSON")

    monkeypatch.setattr(
        snapshot_index,
        "read_json_object_or_none",
        _unexpected_read,
    )

    commit_id = uuid4()
    snapshot_index.write_code_package_text_snapshot_index(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        snapshot_fingerprint="fingerprint:all",
        source_snapshot_fingerprint="fingerprint:source",
        commit_id=commit_id,
        head_commit_id=commit_id,
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_id=uuid4(),
        graph_hash_post="hash:post",
        object_count=1,
        change_count=1,
        artifact_state_index={"schema": "test.artifacts"},
        state_snapshot_metadata={"state_snapshot_payload_sha256": "sha256:payload"},
        source_object_state_index={"schema": "test.source"},
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["commit_id"] == str(commit_id)
    assert payload["snapshot_fingerprint"] == "fingerprint:all"


def test_artifact_state_index_delta_reuses_unchanged_rows() -> None:
    code_package_id = uuid4()

    def _artifact_ref(relative_path: str, digest: str) -> CodePackageArtifactRef:
        return CodePackageArtifactRef(
            code_package_id=code_package_id,
            output_key="python.runtime",
            artifact_key=relative_path,
            artifact_family="python",
            artifact_role="runtime_file",
            required_for=["workspace_revision"],
            producer_key="aware_python.runtime",
            relative_path=relative_path,
            digest=digest,
        )

    previous_refs = (
        _artifact_ref("aware_test_package/module.py", "sha256:module-old"),
        _artifact_ref("aware_test_package/other.py", "sha256:other"),
    )
    current_refs = (
        _artifact_ref("aware_test_package/module.py", "sha256:module-new"),
        _artifact_ref("aware_test_package/other.py", "sha256:other"),
    )
    previous_index = snapshot_commit._code_package_artifact_state_index_from_refs(
        code_package_id=code_package_id,
        code_package_artifact_refs=previous_refs,
    )
    full_current_index = snapshot_commit._code_package_artifact_state_index_from_refs(
        code_package_id=code_package_id,
        code_package_artifact_refs=current_refs,
    )

    delta_index = snapshot_commit._code_package_artifact_state_index_from_refs_delta(
        code_package_id=code_package_id,
        code_package_artifact_refs=current_refs,
        previous_snapshot_index_payload={"artifact_state_index": previous_index},
        changed_relative_paths=frozenset({"aware_test_package/module.py"}),
    )

    assert delta_index == full_current_index
    assert previous_index["signature_hash"] != full_current_index["signature_hash"]
    previous_rows = {row["relative_path"]: row for row in previous_index["artifacts"]}
    delta_rows = {row["relative_path"]: row for row in delta_index["artifacts"]}
    assert (
        delta_rows["aware_test_package/other.py"]
        == previous_rows["aware_test_package/other.py"]
    )
    assert delta_rows["aware_test_package/module.py"]["digest"] == "sha256:module-new"


def test_artifact_state_index_delta_falls_back_on_mismatched_paths() -> None:
    code_package_id = uuid4()
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package_id,
        output_key="python.runtime",
        artifact_key="aware_test_package/module.py",
        artifact_family="python",
        artifact_role="runtime_file",
        producer_key="aware_python.runtime",
        relative_path="aware_test_package/module.py",
        digest="sha256:module",
    )
    previous_index = snapshot_commit._code_package_artifact_state_index_from_refs(
        code_package_id=code_package_id,
        code_package_artifact_refs=(artifact_ref,),
    )

    assert (
        snapshot_commit._code_package_artifact_state_index_from_refs_delta(
            code_package_id=code_package_id,
            code_package_artifact_refs=(artifact_ref,),
            previous_snapshot_index_payload={"artifact_state_index": previous_index},
            changed_relative_paths=frozenset({"aware_test_package/missing.py"}),
        )
        is None
    )


def test_source_snapshot_fingerprint_delta_reuses_unchanged_text_hashes() -> None:
    code_package_config_id = uuid4()
    common_kwargs = {
        "code_package_config_id": code_package_config_id,
        "package_name": "aware-test-package",
        "language": CodeLanguage.python,
        "surface": "runtime",
        "manifest_kind": "pyproject_toml",
        "manifest_relative_path": "pyproject.toml",
        "package_root": "generated/aware-test-package",
        "sources_root": "generated/aware-test-package/aware_test_package",
        "fqn_prefix": "aware_test_package",
        "source_texts_by_relative_path": {},
        "source_plans_by_relative_path": {},
        "path_roles_by_relative_path": {},
    }
    seed = snapshot_source_text.code_package_text_source_snapshot_fingerprint_result(
        **common_kwargs,
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'seed'\n",
            "aware_test_package/other.py": "VALUE = 'same'\n",
        },
        previous_snapshot_index_payload=None,
        changed_relative_paths=frozenset(),
    )
    full_current = (
        snapshot_source_text.code_package_text_source_snapshot_fingerprint_result(
            **common_kwargs,
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'updated'\n",
                "aware_test_package/other.py": "VALUE = 'same'\n",
            },
            previous_snapshot_index_payload=None,
            changed_relative_paths=frozenset(),
        )
    )
    delta_current = (
        snapshot_source_text.code_package_text_source_snapshot_fingerprint_result(
            **common_kwargs,
            unparsed_texts_by_relative_path={
                "aware_test_package/module.py": "VALUE = 'updated'\n",
                "aware_test_package/other.py": "VALUE = 'same'\n",
            },
            previous_snapshot_index_payload={
                "source_text_hash_index": seed.source_text_hash_index,
            },
            changed_relative_paths=frozenset({"aware_test_package/module.py"}),
        )
    )

    assert delta_current.delta_hit is True
    assert (
        delta_current.source_snapshot_fingerprint
        == full_current.source_snapshot_fingerprint
    )
    seed_unparsed_rows = snapshot_source_text._source_text_hash_rows_by_path(
        seed.source_text_hash_index["unparsed_texts"],
    )
    delta_unparsed_rows = snapshot_source_text._source_text_hash_rows_by_path(
        delta_current.source_text_hash_index["unparsed_texts"],
    )
    assert seed_unparsed_rows is not None
    assert delta_unparsed_rows is not None
    assert (
        delta_unparsed_rows["aware_test_package/other.py"]
        == seed_unparsed_rows["aware_test_package/other.py"]
    )
    assert (
        delta_unparsed_rows["aware_test_package/module.py"]
        != seed_unparsed_rows["aware_test_package/module.py"]
    )


def test_source_snapshot_fingerprint_uses_hash_index_signature() -> None:
    code_package_config_id = uuid4()
    common_kwargs = {
        "package_name": "aware-test-package",
        "code_package_config_id": code_package_config_id,
        "language": CodeLanguage.python,
        "surface": "runtime",
        "manifest_kind": "pyproject_toml",
        "manifest_relative_path": "pyproject.toml",
        "package_root": "generated/aware-test-package",
        "sources_root": "generated/aware-test-package/aware_test_package",
        "fqn_prefix": "aware_test_package",
        "source_plans_by_relative_path": {},
        "path_roles_by_relative_path": {},
    }
    full_index = snapshot_source_text.code_package_source_text_hash_index_from_inputs(
        source_texts_by_relative_path={},
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'same'\n",
        },
    )
    signature_index = {
        "schema": full_index["schema"],
        "source_text_count": full_index["source_text_count"],
        "unparsed_text_count": full_index["unparsed_text_count"],
        "signature_hash": full_index["signature_hash"],
    }

    assert snapshot_source_text.code_package_text_source_snapshot_fingerprint_from_hash_index(
        **common_kwargs,
        source_text_hash_index=full_index,
    ) == snapshot_source_text.code_package_text_source_snapshot_fingerprint_from_hash_index(
        **common_kwargs,
        source_text_hash_index=signature_index,
    )


def test_source_snapshot_fingerprint_delta_falls_back_on_mismatched_paths() -> None:
    code_package_config_id = uuid4()
    common_kwargs = {
        "code_package_config_id": code_package_config_id,
        "package_name": "aware-test-package",
        "language": CodeLanguage.python,
        "surface": "runtime",
        "manifest_kind": "pyproject_toml",
        "manifest_relative_path": "pyproject.toml",
        "package_root": "generated/aware-test-package",
        "sources_root": "generated/aware-test-package/aware_test_package",
        "fqn_prefix": "aware_test_package",
        "source_texts_by_relative_path": {},
        "source_plans_by_relative_path": {},
        "path_roles_by_relative_path": {},
    }
    seed = snapshot_source_text.code_package_text_source_snapshot_fingerprint_result(
        **common_kwargs,
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'seed'\n",
        },
        previous_snapshot_index_payload=None,
        changed_relative_paths=frozenset(),
    )
    current = snapshot_source_text.code_package_text_source_snapshot_fingerprint_result(
        **common_kwargs,
        unparsed_texts_by_relative_path={
            "aware_test_package/module.py": "VALUE = 'updated'\n",
        },
        previous_snapshot_index_payload={
            "source_text_hash_index": seed.source_text_hash_index,
        },
        changed_relative_paths=frozenset({"aware_test_package/missing.py"}),
    )

    assert current.delta_hit is False


def test_product_witness_desired_state_uses_witness_cursor_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        snapshot_commit,
        "_CODE_PACKAGE_STATE_ROW_MAP_MIN_SOURCE_OBJECT_COUNT",
        1,
    )
    graph_id = uuid4()
    class_config_id = uuid4()
    source_object_id = uuid4()
    class_instance_id = uuid4()
    state_index = snapshot_commit.CommitStateIndex(
        rows=(
            snapshot_commit.CommitStateRow(
                kind="NODE",
                key=str(class_config_id),
                value=str(class_instance_id),
            ),
        ),
    )
    root_class_instance = snapshot_commit.ClassInstance.model_construct(
        id=class_instance_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
        class_instance_attributes=[],
    )
    desired_state = snapshot_commit._CodePackageDesiredState(
        object_instance_graph_id=graph_id,
        graph_hash=state_index.compute_hash(),
        state_index=state_index,
        root_metadata=snapshot_commit.ObjectInstanceGraphCommitRootMetadata(
            object_instance_graph_key="branch",
            object_instance_graph_name="name",
            object_instance_graph_description=None,
            root_class_config_id=class_config_id,
            root_source_object_id=source_object_id,
        ),
        root_class_instance=root_class_instance,
        class_instances=(root_class_instance,),
        class_instance_payloads=(),
        class_instances_by_id={class_instance_id: root_class_instance},
        class_instance_relationships=(),
        relationships_by_key={},
        graph_meta={"hash": state_index.compute_hash()},
        source_object_state_index={},
    )

    result = snapshot_commit._code_package_witness_desired_state_for_product(
        desired_state,
    )

    assert result.graph_hash_source == "witness_cursor_hash"
    assert result.post_witness_ref is not None
    assert result.post_witness_cursor_summary is not None
    assert result.graph_hash == result.post_witness_cursor_summary.cursor_hash
    assert result.post_witness_cursor_chunks
    assert result.graph_meta["hash"] == result.graph_hash

    assert (
        snapshot_commit._code_package_witness_desired_state_for_product(result)
        is result
    )


def test_segmented_pre_state_evidence_preserves_witness_cursor_hash() -> None:
    chunk = CommitStateWitnessCursorChunkSummary(
        index=0,
        first_segment_key="class:00000000-0000-0000-0000-000000000001",
        last_segment_key="class:00000000-0000-0000-0000-000000000001",
        segment_count=1,
        row_count=3,
        digest="chunk-digest",
    )
    cursor_hash = compute_commit_state_witness_cursor_hash((chunk,))
    summary = CommitStateWitnessCursorSummary(
        schema=COMMIT_STATE_WITNESS_CURSOR_SCHEMA,
        state_hash=None,
        legacy_witness_hash=None,
        cursor_hash=cursor_hash,
        row_count=3,
        segment_count=1,
        chunk_size=64,
        chunks=(chunk,),
    )

    evidence = snapshot_commit._code_package_snapshot_state_pre_state_evidence(
        state_payload={
            "schema": "aware.oig.snapshot_state_class_segment_index.v3",
            "graph_hash_source": "witness_cursor_hash",
            "state_witness_cursor": commit_state_witness_cursor_summary_payload(
                summary
            ),
        },
        state_hash="state-hash",
        row_count=3,
        head_commit_id=uuid4(),
    )

    assert evidence.graph_hash_source == "witness_cursor_hash"
    assert evidence.witness_cursor_hash == cursor_hash
    assert evidence.state_hash is None
    assert evidence.row_count == 3


def test_large_state_hash_head_requires_one_witness_migration() -> None:
    commit_id = uuid4()
    graph_hash = "state-hash"

    assert snapshot_commit._code_package_head_requires_witness_migration(
        head={
            "commit_id": str(commit_id),
            "graph_hash_source": "state_hash",
            "graph_hash_post": graph_hash,
        },
        snapshot_index_payload={"object_count": 500},
    )
    assert not snapshot_commit._code_package_head_requires_witness_migration(
        head={
            "commit_id": str(commit_id),
            "graph_hash_source": "state_hash",
            "graph_hash_post": graph_hash,
        },
        snapshot_index_payload={
            "object_count": 500,
            "state_snapshot": {
                "state_snapshot_kind": "class_segment_index",
                "state_snapshot_graph_hash": graph_hash,
            },
        },
    )
    assert not snapshot_commit._code_package_head_requires_witness_migration(
        head={
            "commit_id": str(commit_id),
            "graph_hash_source": "witness_cursor_hash",
        },
        snapshot_index_payload={"object_count": 500},
    )
    assert not snapshot_commit._code_package_head_requires_witness_migration(
        head={
            "commit_id": str(commit_id),
            "graph_hash_source": "state_hash",
        },
        snapshot_index_payload={"object_count": 499},
    )


def test_legacy_head_without_snapshot_index_skips_witness_migration() -> None:
    assert not snapshot_commit._code_package_head_requires_witness_migration(
        head={
            "commit_id": str(uuid4()),
            "graph_hash_source": "state_hash",
        },
        snapshot_index_payload=None,
    )


def test_snapshot_state_index_hit_accepts_class_segment_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    calls: list[object] = []

    class _Store:
        def snapshot_state_class_segment_index_metadata(
            self,
            **kwargs: object,
        ) -> object:
            calls.append(kwargs)
            assert kwargs["branch_id"] == branch_id
            assert kwargs["projection_hash"] == "CodePackage"
            assert kwargs["commit_id"] == commit_id
            assert kwargs["expected_graph_hash"] == "sha256:witness"
            return object()

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", _Store)

    assert snapshot_commit._code_package_text_snapshot_state_snapshot_index_hit(
        payload={
            "graph_hash_post": "sha256:witness",
            "state_snapshot": {
                "state_snapshot_kind": "class_segment_index",
                "state_snapshot_graph_hash": "sha256:witness",
            },
        },
        branch_id=branch_id,
        projection_hash="CodePackage",
        commit_id=commit_id,
    )
    assert len(calls) == 1


def test_snapshot_state_index_hit_rejects_row_state_hash_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Store:
        def has_snapshot_state_rows_file_metadata(self, **_kwargs: object) -> bool:
            raise AssertionError("drifted state hash must fail before file metadata")

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", _Store)

    assert not snapshot_commit._code_package_text_snapshot_state_snapshot_index_hit(
        payload={
            "graph_hash_post": "sha256:commit-state",
            "state_snapshot": {
                "state_snapshot_payload_sha256": "sha256:payload",
                "state_snapshot_state_hash": "sha256:different-state",
                "state_snapshot_file_size": 100,
                "state_snapshot_file_mtime_ns": 200,
                "state_snapshot_file_ctime_ns": 300,
            },
        },
        branch_id=uuid4(),
        projection_hash="CodePackage",
        commit_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_legacy_state_hash_reuse_misses_when_segment_metadata_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Store:
        def snapshot_state_class_segment_index_metadata(
            self,
            **_kwargs: object,
        ) -> None:
            return None

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", _Store)
    source_states = {uuid4(): object() for _ in range(500)}

    result = await snapshot_commit._try_build_code_package_reused_witness_segment_desired_state(
        index=None,
        opg=None,
        branch_id=uuid4(),
        projection_hash="CodePackage",
        head={
            "commit_id": str(uuid4()),
            "graph_hash_post": "state-hash",
            "graph_hash_source": "state_hash",
        },
        previous_snapshot_index_payload=None,
        domain_oig_id=uuid4(),
        code_package=CodePackage.model_construct(id=uuid4()),
        code_package_config_id=uuid4(),
        manifest_kind="ontology",
        surface="runtime",
        objects_by_id={},
        current_source_states_by_id=source_states,
        changed_path_source_state=None,
        current_source_object_path_index=None,
        previous_source_states_by_id=source_states,
        oigi_id=uuid4(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_witness_head_without_reusable_source_state_uses_full_rebuild() -> None:
    result = await snapshot_commit._try_build_code_package_reused_witness_segment_desired_state(
        index=None,
        opg=None,
        branch_id=uuid4(),
        projection_hash="CodePackage",
        head={
            "commit_id": str(uuid4()),
            "graph_hash_post": "witness-hash",
            "graph_hash_source": "witness_cursor_hash",
        },
        previous_snapshot_index_payload=None,
        domain_oig_id=uuid4(),
        code_package=CodePackage.model_construct(id=uuid4()),
        code_package_config_id=uuid4(),
        manifest_kind="pyproject_toml",
        surface="runtime",
        objects_by_id={},
        current_source_states_by_id=None,
        changed_path_source_state=None,
        current_source_object_path_index=None,
        previous_source_states_by_id=None,
        oigi_id=uuid4(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_large_existing_state_snapshot_publishes_missing_segment_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writes: list[dict[str, object]] = []

    class _Store:
        async def get_snapshot_state_rows(self, **_kwargs: object) -> object:
            return {"state_hash": "state-hash"}

        def snapshot_state_class_segment_index_metadata(
            self,
            **_kwargs: object,
        ) -> None:
            return None

        async def put_state_snapshot_rows_from_payloads(
            self,
            **kwargs: object,
        ) -> object:
            writes.append(dict(kwargs))
            return {
                "payload_sha256": "payload-hash",
                "state_hash": "state-hash",
            }

        def snapshot_state_rows_file_metadata(
            self,
            **_kwargs: object,
        ) -> dict[str, object]:
            return {"state_snapshot_file_size": 1}

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", _Store)
    desired_state = SimpleNamespace(
        graph_hash_source="state_hash",
        post_witness_ref=None,
        post_witness_cursor_summary=None,
        previous_commit_id=uuid4(),
        replacement_class_segments=(),
        state_index=SimpleNamespace(node_count=500),
        object_instance_graph_id=uuid4(),
        graph_hash="state-hash",
        graph_meta={},
        class_instance_payloads=({"id": str(uuid4())},),
        class_instances=(),
        class_instance_relationships=(),
    )

    metadata = await snapshot_commit._ensure_code_package_text_snapshot_state_snapshot_from_state_inner(
        branch_id=uuid4(),
        projection_hash="CodePackage",
        commit_id=uuid4(),
        desired_state=desired_state,
    )

    assert metadata["state_snapshot_payload_sha256"] == "payload-hash"
    assert len(writes) == 1
    assert writes[0]["write_state_class_segment_index"] is True


@pytest.mark.asyncio
async def test_snapshot_state_selection_prefers_valid_file_witness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    selection = object()
    calls: list[str] = []

    class _Store:
        async def get_snapshot_state_selection_by_file_witness(
            self,
            **kwargs: object,
        ) -> object:
            calls.append("witness")
            assert kwargs["expected_file_size"] == 100
            assert kwargs["expected_file_mtime_ns"] == 200
            assert kwargs["expected_file_ctime_ns"] == 300
            assert kwargs["expected_payload_sha256"] == "sha256:payload"
            assert kwargs["expected_state_hash"] == "sha256:state"
            return selection

        async def get_snapshot_state_selection(self, **_kwargs: object) -> object:
            raise AssertionError("valid witness should avoid full validation")

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", _Store)

    result = await snapshot_commit._get_code_package_text_snapshot_state_selection(
        branch_id=branch_id,
        projection_hash="CodePackage",
        commit_id=commit_id,
        class_instance_ids=(),
        previous_snapshot_index_payload={
            "state_snapshot": {
                "state_snapshot_file_size": 100,
                "state_snapshot_file_mtime_ns": 200,
                "state_snapshot_file_ctime_ns": 300,
                "state_snapshot_payload_sha256": "sha256:payload",
                "state_snapshot_state_hash": "sha256:state",
            },
        },
        expected_object_instance_graph_id=oig_id,
        expected_graph_hash="sha256:state",
    )

    assert result is selection
    assert calls == ["witness"]


@pytest.mark.asyncio
async def test_snapshot_state_selection_falls_back_without_file_witness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    selection = object()
    calls: list[str] = []

    class _Store:
        async def get_snapshot_state_selection_by_file_witness(
            self,
            **_kwargs: object,
        ) -> object:
            raise AssertionError("missing witness should not call witness path")

        async def get_snapshot_state_selection(self, **kwargs: object) -> object:
            calls.append("full")
            assert kwargs["commit_id"] == commit_id
            assert kwargs["expected_object_instance_graph_id"] == oig_id
            return selection

    monkeypatch.setattr(snapshot_commit, "FSSnapshotStore", _Store)

    result = await snapshot_commit._get_code_package_text_snapshot_state_selection(
        branch_id=branch_id,
        projection_hash="CodePackage",
        commit_id=commit_id,
        class_instance_ids=(),
        previous_snapshot_index_payload={"state_snapshot": {}},
        expected_object_instance_graph_id=oig_id,
        expected_graph_hash="sha256:state",
    )

    assert result is selection
    assert calls == ["full"]
