from __future__ import annotations

import sys
from typing import cast

from _meta_runtime_test_paths import META_RUNTIME_ROOT, REPO_ROOT

_REPO_ROOT = REPO_ROOT
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_META_RUNTIME_ROOT_STR = str(META_RUNTIME_ROOT)
if _META_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _META_RUNTIME_ROOT_STR)

from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: E402
from aware_code_ontology.code.code_plan import (  # noqa: E402
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta.materialization.runtime_delta import (  # noqa: E402
    META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION,
    MetaOcgRuntimeDeltaTransformRequest,
    build_meta_ocg_runtime_delta_transform,
)


def test_runtime_delta_transform_requires_content_backed_code_delta() -> None:
    delta = CodePackageDelta(
        package_name="demo-ontology",
        manifest_relative_path="aware.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/home/model.aware",
                kind=CodePackageDeltaKind.update,
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                }
            },
        )
    )
    payload = result.evidence_payload()

    assert payload["contract_version"] == (
        META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION
    )
    assert payload["status"] == "runtime_delta_transform_blocked"
    assert payload["reason"] == (
        "meta_ocg_runtime_delta_requires_content_backed_code_package_delta"
    )
    assert payload["blockers"] == ("path_content_missing:aware/home/model.aware",)
    assert payload["path_count"] == 1
    path_evidence = cast(
        tuple[dict[str, object], ...],
        payload["path_evidence"],
    )[0]
    assert path_evidence["has_content_text"] is False
    assert path_evidence["has_content_plan"] is False
    assert payload["full_rebuild_oracle_used"] is False
    assert payload["current_runtime_semantic_object_index_available"] is False


def test_runtime_delta_transform_builds_runtime_index_for_primitive_class() -> None:
    delta = CodePackageDelta(
        package_name="demo-ontology",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/home/model.aware",
                kind=CodePackageDeltaKind.update,
                content_text="class Room { name String }",
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                }
            },
        )
    )
    payload = result.evidence_payload()

    assert payload["status"] == "runtime_delta_transform_ready"
    assert payload["reason"] == "meta_ocg_runtime_delta_transform_ready"
    assert payload["blockers"] == ()
    path_evidence = cast(
        tuple[dict[str, object], ...],
        payload["path_evidence"],
    )[0]
    assert path_evidence["has_content_text"] is True
    assert path_evidence["content_text_size_bytes"] == len(
        "class Room { name String }".encode("utf-8")
    )
    assert payload["baseline_semantic_object_index_count"] == 1
    assert payload["changed_runtime_source_refs"] == ("home/model.aware",)
    assert payload["deleted_runtime_source_refs"] == ()
    current_index = cast(
        dict[str, dict[str, object]],
        payload["current_runtime_semantic_object_index"],
    )
    assert payload["current_runtime_semantic_object_index_available"] is True
    assert payload["namespace_mapping_count"] == 0
    assert payload["current_runtime_semantic_object_index_keys"] == (
        "ocg:aware_demo",
        "ocg:aware_demo/node:aware_demo.home.Room",
        "ocg:aware_demo/node:aware_demo.home.Room/attribute:name",
        "ocg_package:demo-ontology",
    )
    assert payload["runtime_ocg_delta_count"] == 4
    assert current_index["ocg:aware_demo"]["object_kind"] == "object_config_graph"
    room = current_index["ocg:aware_demo/node:aware_demo.home.Room"]
    assert room["object_kind"] == "class"
    assert room["node_type"] == "class"
    assert room["source_refs"] == ("home/model.aware",)
    attribute = current_index[
        "ocg:aware_demo/node:aware_demo.home.Room/attribute:name"
    ]
    assert attribute["object_kind"] == "attribute"
    assert attribute["parent_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.home.Room"
    )
    signature = cast(dict[str, object], attribute["attribute_signature"])
    assert signature["primitive_signature"] == "string"
    assert signature["primitive_base_type"] == "string"
    assert isinstance(attribute["semantic_fingerprint"], str)


def test_runtime_delta_transform_derives_layout_namespace_without_mappings() -> None:
    delta = CodePackageDelta(
        package_name="demo-ontology",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/home/model.aware",
                kind=CodePackageDeltaKind.update,
                content_text="class Room { name String }",
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                }
            },
        )
    )
    payload = result.evidence_payload()

    assert payload["status"] == "runtime_delta_transform_ready"
    assert payload["reason"] == "meta_ocg_runtime_delta_transform_ready"
    assert payload["blockers"] == ()
    assert payload["namespace_mapping_count"] == 0
    assert "ocg:aware_demo/node:aware_demo.home.Room" in (
        payload["current_runtime_semantic_object_index_keys"]
    )


def test_runtime_delta_transform_strips_workspace_qualified_aware_source_root() -> (
    None
):
    delta = CodePackageDelta(
        package_name="demo-ontology",
        sources_root="modules/demo/ontology/structure/aware",
        manifest_relative_path="modules/demo/ontology/aware.ontology.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/content/model.aware",
                kind=CodePackageDeltaKind.update,
                content_text="class Room { name String }",
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                }
            },
        )
    )
    payload = result.evidence_payload()

    assert payload["status"] == "runtime_delta_transform_ready"
    assert payload["changed_runtime_source_refs"] == ("content/model.aware",)
    assert "ocg:aware_demo/node:aware_demo.content.Room" in (
        payload["current_runtime_semantic_object_index_keys"]
    )


def test_runtime_delta_transform_indexes_function_and_relationship_subjects() -> None:
    delta = CodePackageDelta(
        package_name="demo-ontology",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/home/model.aware",
                kind=CodePackageDeltaKind.update,
                content_text="\n".join(
                    [
                        "class Room {",
                        "    name String",
                        "",
                        "    fn rename(new_name String) -> Room {",
                        '        """',
                        "        Rename the room for humans and assistants.",
                        '        """',
                        "        set name = new_name",
                        "    }",
                        "}",
                        "",
                        "class Door {",
                        "    label String",
                        "}",
                        "",
                        "class House {",
                        "    doors Door[]",
                        "}",
                    ]
                ),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                }
            },
        )
    )
    payload = result.evidence_payload()

    function_key = "ocg:aware_demo/node:aware_demo.home.Room.rename"
    function_impl_key = f"{function_key}/function_impl:default"
    relationship_key = (
        "ocg:aware_demo/node:aware_demo.home.House:doors:one_to_many:"
        "aware_demo.home.Door"
    )
    collection_attribute_key = (
        "ocg:aware_demo/node:aware_demo.home.House/attribute:doors"
    )
    current_index = cast(
        dict[str, dict[str, object]],
        payload["current_runtime_semantic_object_index"],
    )

    assert payload["status"] == "runtime_delta_transform_ready"
    assert payload["blockers"] == ()
    assert function_key in current_index
    assert function_impl_key in current_index
    assert relationship_key in current_index
    assert collection_attribute_key in current_index

    function = current_index[function_key]
    assert function["object_kind"] == "function"
    assert function["parent_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.home.Room"
    )
    assert function["function_name"] == "rename"
    assert function["source_refs"] == ("home/model.aware",)
    function_signature = cast(dict[str, object], function["function_signature"])
    assert function_signature["kind"] == "instance"
    assert function_signature["owner_key"] == "aware_demo.home.Room"
    assert function_signature["description"] == (
        "Rename the room for humans and assistants."
    )
    inputs = cast(tuple[dict[str, object], ...], function_signature["inputs"])
    outputs = cast(tuple[dict[str, object], ...], function_signature["outputs"])
    assert inputs[0]["name"] == "new_name"
    assert inputs[0]["primitive_base_type"] == "string"
    assert outputs[0]["kind"] == "class"
    assert outputs[0]["class_fqn"] == "aware_demo.home.Room"

    function_impl = current_index[function_impl_key]
    assert function_impl["object_kind"] == "function_impl"
    assert function_impl["parent_semantic_key"] == function_key
    assert function_impl["owner_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.home.Room"
    )
    assert function_impl["function_name"] == "rename"
    assert function_impl["function_impl_key"] == "default"
    assert function_impl["source_refs"] == ("home/model.aware",)
    function_impl_signature = cast(
        dict[str, object],
        function_impl["function_impl_signature"],
    )
    assert function_impl_signature["kind"] == "instruction_body"
    assert function_impl_signature["instruction_count"] == 1
    assert function_impl_signature["instruction_summaries"] == ("set name = new_name",)
    instructions = cast(
        tuple[dict[str, object], ...],
        function_impl_signature["instructions"],
    )
    assert instructions[0]["type"] == "set"
    set_payload = cast(dict[str, object], instructions[0]["set"])
    assert set_payload["target_attribute_name"] == "name"
    value_source = cast(dict[str, object], set_payload["value_source"])
    assert value_source["kind"] == "function_input_ref"
    assert value_source["source_function_input_name"] == "new_name"

    relationship = current_index[relationship_key]
    assert relationship["object_kind"] == "relationship"
    assert relationship["node_type"] == "relationship"
    assert relationship["relationship_key"] == "doors"
    assert relationship["relationship_type"] == "one_to_many"
    assert relationship["source_refs"] == ("home/model.aware",)
    relationship_signature = cast(
        dict[str, object],
        relationship["relationship_signature"],
    )
    assert relationship_signature["relationship_key"] == "doors"
    assert relationship_signature["relationship_type"] == "one_to_many"
    assert relationship_signature["identity_rail"] == "reference"
    assert relationship_signature["forward_required"] is True

    collection_attribute = current_index[collection_attribute_key]
    collection_signature = cast(
        dict[str, object],
        collection_attribute["attribute_signature"],
    )
    assert collection_signature["kind"] == "collection"
    assert collection_signature["collection_kind"] == "list"
    child_links = cast(
        tuple[dict[str, object], ...],
        collection_signature["child_links"],
    )
    assert cast(dict[str, object], child_links[0]["child"])["kind"] == "class"
    assert cast(dict[str, object], child_links[0]["child"])["class_fqn"] == (
        "aware_demo.home.Door"
    )


def test_runtime_delta_transform_reports_delete_source_scope() -> None:
    delta = CodePackageDelta(
        package_name="demo-ontology",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/home/model.aware",
                kind=CodePackageDeltaKind.delete,
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                },
                "ocg:aware_demo/node:aware_demo.home.Room": {
                    "semantic_key": "ocg:aware_demo/node:aware_demo.home.Room",
                    "object_id": "baseline-room-class-object-id",
                    "object_kind": "class",
                    "source_refs": ("home/model.aware",),
                },
            },
        )
    )
    payload = result.evidence_payload()

    assert payload["status"] == "runtime_delta_transform_ready"
    assert payload["reason"] == "meta_ocg_runtime_delta_transform_ready"
    assert payload["changed_runtime_source_refs"] == ("home/model.aware",)
    assert payload["deleted_runtime_source_refs"] == ("home/model.aware",)
    assert payload["current_runtime_semantic_object_index"] == {}
    assert payload["runtime_ocg_delta_count"] == 0
    assert payload["full_rebuild_oracle_used"] is False


def test_runtime_delta_transform_blocks_unsupported_semantic_shapes() -> None:
    delta = CodePackageDelta(
        package_name="demo-ontology",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware/home/model.aware",
                kind=CodePackageDeltaKind.update,
                content_text="\n".join(
                    [
                        "enum RoomState { ready }",
                        "class Room { state RoomState? }",
                    ]
                ),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=delta,
            current_delta_fingerprint="sha256:current",
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "semantic_key": "ocg:aware_demo",
                    "object_id": "baseline-graph-object-id",
                    "object_kind": "object_config_graph",
                }
            },
        )
    )
    payload = result.evidence_payload()

    assert payload["status"] == "runtime_delta_transform_blocked"
    assert payload["reason"] == (
        "meta_ocg_runtime_delta_transform_unsupported_semantic_shape"
    )
    blockers = cast(tuple[str, ...], payload["blockers"])
    assert any(
        blocker.startswith("unsupported_node_type:enum:") for blocker in blockers
    )
