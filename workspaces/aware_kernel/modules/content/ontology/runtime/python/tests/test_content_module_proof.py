from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_content.handlers._generated import meta_handlers as content_meta_handlers
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    META_SYSTEM_ACTOR_ID,
    MetaGraphCallTarget,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphInvokeFunctionInput,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    SourceObjectId,
    run_meta_runtime_proof,
)
from aware_storage.handlers._generated import meta_handlers as storage_meta_handlers

_TESTS_ROOT = Path(__file__).resolve().parent
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[5]
CONTENT_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
)


CONTENT_CLASS_FQN = "aware_content.default.content.Content"
CONTENT_PART_TEXT_CLASS_FQN = "aware_content.default.part.ContentPartText"

_CONTENT_META_HANDLERS_ANY: Any = content_meta_handlers
_CONTENT_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _CONTENT_META_HANDLERS_ANY,
)
_CONTENT_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _CONTENT_META_HANDLERS_ANY,
)
_STORAGE_META_HANDLERS_ANY: Any = storage_meta_handlers
_STORAGE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _STORAGE_META_HANDLERS_ANY,
)
_STORAGE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _STORAGE_META_HANDLERS_ANY,
)


def _build_content_meta_runtime(*, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=CONTENT_PACKAGE_MANIFEST_PATHS,
        workspace_root=KERNEL_WORKSPACE_ROOT,
        aware_root=aware_root,
        handler_modules=(
            _STORAGE_META_HANDLER_MODULE,
            _CONTENT_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _STORAGE_META_BOOTSTRAP_MODULE,
            _CONTENT_META_BOOTSTRAP_MODULE,
        ),
    )
    assert runtime.context is not None
    return runtime


def _lane_with_branch(lane: LaneIds, branch_id: UUID) -> LaneIds:
    return LaneIds(
        environment_id=lane.environment_id,
        process_id=lane.process_id,
        thread_id=lane.thread_id,
        branch_id=branch_id,
        actor_id=lane.actor_id,
    )


def _resolve_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_fqn: str,
    function_name: str,
) -> UUID:
    matches: list[UUID] = []
    for class_config in index.class_configs_by_id.values():
        if class_config.class_fqn != class_fqn:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                matches.append(function_config.id)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise AssertionError(
            "FunctionConfig not found in Meta graph index: "
            f"class_fqn={class_fqn!r} function_name={function_name!r}"
        )
    raise AssertionError(
        "FunctionConfig is ambiguous in Meta graph index: "
        f"class_fqn={class_fqn!r} function_name={function_name!r} "
        f"matches={matches}"
    )


async def _class_instance_id_for_source_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    source_object_id: UUID,
) -> UUID:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head and head.get("commit_id") and head.get("object_instance_graph_id")
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    for instance in oig.class_instances:
        if instance.source_object_id == source_object_id and instance.id is not None:
            return instance.id
    raise AssertionError(
        "Source object was not found in committed Content lane: "
        f"source_object_id={source_object_id}"
    )


async def _invoke_content_part_text_patch(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    branch_id: UUID,
    projection_hash: str,
    source_object_id: UUID,
    patch: Mapping[str, object],
):
    context = runtime.context
    assert context is not None
    target_object_id = await _class_instance_id_for_source_object(
        index=context.index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        source_object_id=source_object_id,
    )
    return await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=context.index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=_resolve_function_id(
                index=context.index,
                class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                function_name="apply_editor_patch",
            ),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphCallTarget.instance,
            target_object_id=target_object_id,
            object_projection_graph_id=None,
            args=JsonArray([_jsonify_value(patch)]),
            kwargs=JsonObject({}),
            commit=True,
            publish=False,
        )
    )


def _jsonify_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return value


def _ids_by_class_name(assertions) -> dict[str, list[UUID]]:  # noqa: ANN001
    class_name_by_id = {
        cc_id: cc.name for cc_id, cc in assertions._class_configs_by_id.items()
    }
    ids_by_class_name: dict[str, list[UUID]] = {}
    for ci in assertions.oig.class_instances:
        object_id = ci.source_object_id or ci.id
        if object_id is None:
            continue
        name = class_name_by_id.get(ci.class_config_id)
        if not name:
            continue
        ids_by_class_name.setdefault(name, []).append(UUID(str(object_id)))
    return ids_by_class_name


def _style_id_for_spec(spec: Mapping[str, object | None]) -> UUID:
    spec_key = json.dumps(
        {
            "background_color": spec.get("background_color"),
            "block_semantic_type": spec.get("block_semantic_type"),
            "bold": bool(spec.get("bold") or False),
            "color": spec.get("color"),
            "font_family": spec.get("font_family"),
            "font_size": spec.get("font_size"),
            "italic": bool(spec.get("italic") or False),
            "underline": bool(spec.get("underline") or False),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return uuid5(NAMESPACE_URL, f"aware:content:text-style:v1:{spec_key}")


@pytest.mark.asyncio
async def test_content_create_content_seeds_text_part_with_parent_edge_fk(
    tmp_path: Path,
) -> None:
    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/content/env/create"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/content/process/create"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/content/thread/create"),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_content_meta_runtime(
            aware_root=aware_root,
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CONTENT_CLASS_FQN,
                    function_name="create_content",
                    kwargs={"seed_inline_text": "Keep answers crisp."},
                )
            ],
        )

    assert result.root_object_id is not None
    assertions.expect_root(result.root_object_id)
    ids = _ids_by_class_name(assertions)
    assert len(ids.get("ContentPartContent", [])) == 1
    assert len(ids.get("ContentPart", [])) == 1
    assert len(ids.get("ContentPartText", [])) == 1
    part_content_id = ids["ContentPartContent"][0]
    part_id = ids["ContentPart"][0]
    text_id = ids["ContentPartText"][0]
    assertions.expect_edge(
        source_id=result.root_object_id,
        target_id=part_content_id,
        relationship_name="content_part_contents",
    )
    assertions.expect_edge(
        source_id=part_content_id,
        target_id=part_id,
        relationship_name="content_part",
    )
    assertions.expect_primitive(
        instance_id=text_id,
        field_name="inline_text",
        expected="Keep answers crisp.",
    )


@pytest.mark.asyncio
async def test_content_apply_editor_patch_segments_and_styles(tmp_path: Path) -> None:
    import aware_content_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/content/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/content/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/content/thread"),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_content_meta_runtime(
            aware_root=aware_root,
        )

        create_res, create_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CONTENT_CLASS_FQN,
                    function_name="create_content",
                )
            ],
        )
        assert create_res.root_object_id is not None
        root_id = create_res.root_object_id
        create_assertions.expect_root(root_id)
        create_assertions.expect_instance(root_id)

        ids = _ids_by_class_name(create_assertions)
        assert len(ids.get("ContentPartText", [])) == 1
        text_id = ids["ContentPartText"][0]

        text_after = "Hello 🌍"
        earth_start = len("Hello ".encode("utf-8"))
        earth_end = earth_start + len("🌍".encode("utf-8"))

        segment_earth = uuid5(NAMESPACE_URL, "aware://tests/content/segment/earth")
        segment_hello = uuid5(NAMESPACE_URL, "aware://tests/content/segment/hello")
        segment_prefix = uuid5(NAMESPACE_URL, "aware://tests/content/segment/prefix")

        red_style_spec = {
            "font_family": None,
            "font_size": None,
            "bold": True,
            "italic": False,
            "underline": False,
            "color": "#ff0000",
            "background_color": None,
            "block_semantic_type": "paragraph",
        }
        green_style_spec = {
            "font_family": None,
            "font_size": None,
            "bold": False,
            "italic": False,
            "underline": False,
            "color": "#00ff00",
            "background_color": None,
            "block_semantic_type": "paragraph",
        }

        patch_1 = {
            "text_after": text_after,
            "segment_ops": [
                {
                    "upsert": {
                        "segment_id": str(segment_earth),
                        "byte_start": earth_start,
                        "byte_end": earth_end,
                        "parent_id": None,
                        "style": red_style_spec,
                    }
                }
            ],
        }
        patch_2 = {
            "segment_ops": [
                {
                    "upsert": {
                        "segment_id": str(segment_hello),
                        "byte_start": 0,
                        "byte_end": len("Hello".encode("utf-8")),
                        "parent_id": None,
                        "style": red_style_spec,
                    }
                }
            ]
        }
        patch_3 = {
            "segment_ops": [
                {
                    "upsert": {
                        "segment_id": str(segment_prefix),
                        "byte_start": 0,
                        "byte_end": len("Hello ".encode("utf-8")),
                        "parent_id": None,
                        "style": green_style_spec,
                    }
                }
            ]
        }

        lane_after_create = _lane_with_branch(lane, create_res.branch_id)
        patch_res, patch_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_after_create,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_1],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_2],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_3],
                ),
            ],
        )
        assert patch_res.root_object_id is not None

        patch_assertions.expect_instance(text_id)
        patch_assertions.expect_primitive(
            instance_id=text_id, field_name="inline_text", expected=text_after
        )

        ids = _ids_by_class_name(patch_assertions)
        assert set(ids.get("ContentPartTextSegment", [])) == {
            segment_earth,
            segment_hello,
            segment_prefix,
        }

        red_style_id = _style_id_for_spec(red_style_spec)
        green_style_id = _style_id_for_spec(green_style_spec)
        assert set(ids.get("ContentPartTextStyle", [])) == {
            red_style_id,
            green_style_id,
        }

        patch_assertions.expect_primitive(
            instance_id=segment_earth, field_name="byte_start", expected=earth_start
        )
        patch_assertions.expect_primitive(
            instance_id=segment_earth, field_name="byte_end", expected=earth_end
        )
        patch_assertions.expect_primitive(
            instance_id=red_style_id, field_name="color", expected="#ff0000"
        )
        patch_assertions.expect_primitive(
            instance_id=red_style_id, field_name="bold", expected=True
        )
        patch_assertions.expect_primitive(
            instance_id=green_style_id, field_name="color", expected="#00ff00"
        )

        for seg_id in (segment_earth, segment_hello, segment_prefix):
            patch_assertions.expect_instance(seg_id)
            patch_assertions.expect_edge(source_id=text_id, target_id=seg_id)

        patch_assertions.expect_edge(source_id=segment_earth, target_id=red_style_id)
        patch_assertions.expect_edge(source_id=segment_hello, target_id=red_style_id)
        patch_assertions.expect_edge(source_id=segment_prefix, target_id=green_style_id)


@pytest.mark.asyncio
async def test_content_apply_editor_patch_detach_segment(tmp_path: Path) -> None:
    import aware_content_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/content/detach/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/content/detach/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/content/detach/thread"),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_content_meta_runtime(
            aware_root=aware_root,
        )

        create_res, create_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CONTENT_CLASS_FQN,
                    function_name="create_content",
                )
            ],
        )
        assert create_res.root_object_id is not None
        text_id = _ids_by_class_name(create_assertions)["ContentPartText"][0]

        segment_id = uuid5(NAMESPACE_URL, "aware://tests/content/detach/segment")
        red_style_spec = {
            "font_family": None,
            "font_size": None,
            "bold": True,
            "italic": False,
            "underline": False,
            "color": "#ff0000",
            "background_color": None,
            "block_semantic_type": "paragraph",
        }
        patch_upsert = {
            "text_after": "Hello",
            "segment_ops": [
                {
                    "upsert": {
                        "segment_id": str(segment_id),
                        "byte_start": 0,
                        "byte_end": len("Hello".encode("utf-8")),
                        "parent_id": None,
                        "style": red_style_spec,
                    }
                }
            ],
        }
        patch_detach = {"segment_ops": [{"detach": {"segment_id": str(segment_id)}}]}

        lane_after_create = _lane_with_branch(lane, create_res.branch_id)

        _, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_after_create,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_upsert],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_detach],
                ),
            ],
        )

        ids = _ids_by_class_name(assertions)
        assert ids.get("ContentPartTextSegment", []) == []
        assert ids.get("ContentPartTextStyle", []) == []

        rel_pairs = {
            (rel.source_class_instance_id, rel.target_class_instance_id)
            for rel in assertions.oig.class_instance_relationships
        }
        assert (text_id, segment_id) not in rel_pairs
        assert (segment_id, text_id) not in rel_pairs
        red_style_id = _style_id_for_spec(red_style_spec)
        assert (segment_id, red_style_id) not in rel_pairs
        assert (red_style_id, segment_id) not in rel_pairs


@pytest.mark.asyncio
async def test_content_apply_editor_patch_detach_segment_after_committed_reload(
    tmp_path: Path,
) -> None:
    import aware_content_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/content/detach-reload/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/content/detach-reload/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/content/detach-reload/thread"),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_detach_reload",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_content_meta_runtime(
            aware_root=aware_root,
        )

        create_res, create_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CONTENT_CLASS_FQN,
                    function_name="create_content",
                )
            ],
        )
        text_id = _ids_by_class_name(create_assertions)["ContentPartText"][0]

        segment_id = uuid5(NAMESPACE_URL, "aware://tests/content/detach-reload/segment")
        patch_upsert = {
            "text_after": "Hello",
            "segment_ops": [
                {
                    "upsert": {
                        "segment_id": str(segment_id),
                        "byte_start": 0,
                        "byte_end": len("Hello".encode("utf-8")),
                        "parent_id": None,
                        "style": {
                            "font_family": None,
                            "font_size": None,
                            "bold": True,
                            "italic": False,
                            "underline": False,
                            "color": "#ff0000",
                            "background_color": None,
                            "block_semantic_type": "paragraph",
                        },
                    }
                }
            ],
        }
        patch_detach = {"segment_ops": [{"detach": {"segment_id": str(segment_id)}}]}

        lane_after_create = _lane_with_branch(lane, create_res.branch_id)
        upsert_res, _ = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_after_create,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_upsert],
                )
            ],
        )

        lane_after_upsert = _lane_with_branch(lane, upsert_res.branch_id)
        _, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_after_upsert,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_detach],
                )
            ],
        )

        ids = _ids_by_class_name(assertions)
        assert ids.get("ContentPartTextSegment", []) == []

        rel_pairs = {
            (rel.source_class_instance_id, rel.target_class_instance_id)
            for rel in assertions.oig.class_instance_relationships
        }
        assert (text_id, segment_id) not in rel_pairs
        assert (segment_id, text_id) not in rel_pairs


@pytest.mark.asyncio
async def test_content_apply_editor_patch_rejects_invalid_segment_ranges(
    tmp_path: Path,
) -> None:
    import aware_content_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/content/invalid/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/content/invalid/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/content/invalid/thread"),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_content_meta_runtime(
            aware_root=aware_root,
        )

        create_res, create_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CONTENT_CLASS_FQN,
                    function_name="create_content",
                )
            ],
        )
        text_id = _ids_by_class_name(create_assertions)["ContentPartText"][0]
        assert create_res.projection_hash

        patch_invalid = {
            "text_after": "Hi",
            "segment_ops": [
                {
                    "upsert": {
                        "segment_id": str(
                            uuid5(
                                NAMESPACE_URL, "aware://tests/content/invalid/segment"
                            )
                        ),
                        "byte_start": 0,
                        "byte_end": 100,
                        "parent_id": None,
                        "style": None,
                    }
                }
            ],
        }

        with pytest.raises(ValueError, match="Invalid segment byte range"):
            await _invoke_content_part_text_patch(
                runtime=runtime,
                lane=lane,
                branch_id=create_res.branch_id,
                projection_hash=create_res.projection_hash,
                source_object_id=text_id,
                patch=patch_invalid,
            )


@pytest.mark.asyncio
async def test_content_apply_editor_patch_text_patches_utf8_bytes(
    tmp_path: Path,
) -> None:
    import aware_content_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/content/patch/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/content/patch/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/content/patch/thread"),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_content_meta_runtime(
            aware_root=aware_root,
        )

        create_res, create_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CONTENT_CLASS_FQN,
                    function_name="create_content",
                )
            ],
        )
        text_id = _ids_by_class_name(create_assertions)["ContentPartText"][0]

        patch_set_text = {"text_after": "Hello"}
        patch_ops = {
            "text_patches": [
                {"op": "replace", "pos": 0, "len": 5, "text": "Hey"},
                {"op": "insert", "pos": 3, "text": "!"},
                {"op": "delete", "pos": 0, "len": 1},
            ]
        }

        lane_after_create = _lane_with_branch(lane, create_res.branch_id)
        _, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_after_create,
            opg_name="Content",
            root_class_fqn=CONTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_set_text],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CONTENT_PART_TEXT_CLASS_FQN,
                    function_name="apply_editor_patch",
                    object_id=SourceObjectId(text_id),
                    args=[patch_ops],
                ),
            ],
        )

        assertions.expect_primitive(
            instance_id=text_id, field_name="inline_text", expected="ey!"
        )
