from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from aware_code_sdk import (
    AwareCodeSdk,
    CodeSegmentContentDomain,
    ResolveCodeSegmentRenderPolicyRequest,
    ResolveCodeSourceProjectionPackageDeltaRequest,
)
from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
)
from aware_meta.materialization.deltas.source_projection import (
    code_source_projection_request_from_meta_change_report,
    code_source_projection_result_from_meta_feature_results,
    provider_delta_source_projection_stage,
    source_projection_feature_results_from_meta_typed_operations,
)


def _service_backed_code_sdk() -> AwareCodeSdk:
    code_service = pytest.importorskip("aware_code_service")
    return AwareCodeSdk(
        api_client=cast(Any, code_service.build_local_code_service_api_client())
    )


@pytest.mark.asyncio
async def test_meta_attribute_type_source_projection_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=("class TvChannel {\n" "    selected_channel Int?\n" "}\n"),
    )
    report, projection, result = _meta_source_projection_bundle(
        operation=_attribute_type_operation(),
        package_root=tmp_path,
    )
    entry = result.delta_set.entries[0] if result.delta_set is not None else None

    assert report["available"] is True
    assert entry is not None
    assert entry.before_hash is None
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "type"
    assert entry.segment_ref.byte_start is None
    assert entry.segment_ref.byte_end is None
    assert entry.segment_ref.before_segment_hash == _digest("Int?")

    sdk = _service_backed_code_sdk()
    policy_response = await sdk.resolve_segment_render_policy(
        ResolveCodeSegmentRenderPolicyRequest(
            language="aware",
            section_type="function",
            segment_name="description_comment",
        )
    )
    response = await sdk.resolve_source_projection_package_delta(
        ResolveCodeSourceProjectionPackageDeltaRequest(
            projection=projection,
            result=result,
        )
    )

    assert policy_response.success is True
    assert policy_response.resolved is True
    assert policy_response.policy_count == 1
    assert policy_response.policies[0].content_text_domain is (
        CodeSegmentContentDomain.semantic_segment_value
    )
    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "class TvChannel {\n" "    selected_channel String?\n" "}\n"
    )


@pytest.mark.asyncio
async def test_meta_attribute_default_value_source_projection_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=("class TvChannel {\n" "    selected_channel Int = 7\n" "}\n"),
    )
    report, projection, result = _meta_source_projection_bundle(
        operation=_attribute_default_value_operation(),
        package_root=tmp_path,
    )
    entry = result.delta_set.entries[0] if result.delta_set is not None else None

    assert report["available"] is True
    assert entry is not None
    assert entry.before_hash is None
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "default_value"
    assert entry.segment_ref.byte_start is None
    assert entry.segment_ref.byte_end is None
    assert entry.segment_ref.before_segment_hash == _digest("7")

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "class TvChannel {\n" "    selected_channel Int = 11\n" "}\n"
    )


@pytest.mark.asyncio
async def test_meta_function_description_source_projection_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=(
            "class TvChannel {\n"
            "    fn rename(display_name String) -> TvChannel {\n"
            '        """Rename the channel display label for humans and assistants."""\n'
            "    }\n"
            "}\n"
        ),
    )
    report, projection, result = _meta_source_projection_bundle(
        operation=_function_description_operation(),
        package_root=tmp_path,
    )
    entry = result.delta_set.entries[0] if result.delta_set is not None else None

    assert report["available"] is True
    assert entry is not None
    assert entry.before_hash is None
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "description_comment"
    assert entry.segment_ref.byte_start is None
    assert entry.segment_ref.byte_end is None
    assert entry.segment_ref.before_segment_hash == _digest(
        "Rename the channel display label for humans and assistants."
    )

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "class TvChannel {\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        '        """Rename the channel display label and keep assistant-facing media '
        'context synchronized."""\n'
        "    }\n"
        "}\n"
    )


@pytest.mark.asyncio
async def test_meta_class_description_source_projection_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=(
            "/// Old display contract.\n"
            "class TvChannel {\n"
            "    selected_channel Int\n"
            "}\n"
        ),
    )
    report, projection, result = _meta_source_projection_bundle(
        operation=_class_description_operation(),
        package_root=tmp_path,
    )
    entry = result.delta_set.entries[0] if result.delta_set is not None else None

    assert report["available"] is True
    assert entry is not None
    assert entry.before_hash is None
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "description_comment"
    assert entry.segment_ref.byte_start is None
    assert entry.segment_ref.byte_end is None
    assert entry.segment_ref.before_segment_hash == _digest("Old display contract.")

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "/// Describes a media channel available to the home assistant.\n"
        "class TvChannel {\n"
        "    selected_channel Int\n"
        "}\n"
    )


@pytest.mark.asyncio
async def test_meta_relationship_load_policy_source_projection_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=(
            "class RemoteControl {\n" "    selected_channel TvChannel\n" "}\n"
        ),
    )
    report, projection, result = _meta_source_projection_bundle(
        operation=_relationship_load_policy_operation(),
        package_root=tmp_path,
    )
    entry = result.delta_set.entries[0] if result.delta_set is not None else None

    assert report["available"] is True
    assert entry is not None
    assert getattr(entry.operation, "value", entry.operation) == (
        "insert_after_section"
    )
    assert entry.section_ref.section_type == "class"
    assert entry.section_ref.qualname == "RemoteControl"
    assert entry.segment_ref is None
    assert entry.content_text is not None
    assert entry.content_text == (
        "\nann home.RemoteControl::selected_channel load forward eager"
    )
    assert entry.after_hash == _digest(entry.content_text)

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "class RemoteControl {\n"
        "    selected_channel TvChannel\n"
        "}\n"
        "ann home.RemoteControl::selected_channel load forward eager\n"
    )


def test_meta_class_description_source_projection_blocks_without_baseline_segment(
    tmp_path: Path,
) -> None:
    operation = _class_description_operation()
    baseline = cast(dict[str, object], operation["baseline"])
    baseline_object = cast(dict[str, object], baseline["object"])
    baseline_signature = dict(
        cast(dict[str, object], baseline_object["class_signature"]),
    )
    baseline_signature["description"] = None
    baseline_object["class_signature"] = baseline_signature

    _, _, result = _meta_source_projection_bundle(
        operation=operation,
        package_root=tmp_path,
        require_projected=False,
    )

    assert result.projected is False
    assert result.delta_set is None
    assert result.skipped_events
    assert result.skipped_events[0].reason == (
        "meta_source_projection_class_config_description_requires_renderable_segment"
    )
    assert result.skipped_events[0].metadata["missing_evidence_fields"] == [
        "baseline_description",
    ]


@pytest.mark.asyncio
async def test_meta_function_signature_source_projection_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=(
            "class TvChannel {\n"
            "    fn rename(display_name String) -> TvChannel {\n"
            "    }\n"
            "}\n"
        ),
    )
    report, projection, result = _meta_source_projection_bundle(
        operation=_function_signature_operation(),
        package_root=tmp_path,
    )
    entry = result.delta_set.entries[0] if result.delta_set is not None else None

    assert report["available"] is True
    assert entry is not None
    assert entry.before_hash is None
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "signature"
    assert entry.segment_ref.byte_start is None
    assert entry.segment_ref.byte_end is None
    assert entry.segment_ref.before_segment_hash == (
        _digest("(display_name String) -> TvChannel")
    )

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "class TvChannel {\n"
        "    fn rename(label String) -> TvChannel {\n"
        "    }\n"
        "}\n"
    )


@pytest.mark.asyncio
async def test_meta_provider_stage_anchors_relative_code_delta_package_root(
    tmp_path: Path,
) -> None:
    manifest_path = (
        tmp_path / "modules" / "home" / "structure" / "ontology" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    (manifest_path.parent / "aware" / "home").mkdir(parents=True)
    (manifest_path.parent / "aware" / "home" / "tv_channel.aware").write_text(
        "class TvChannel {\n" "    selected_channel Int?\n" "}\n",
        encoding="utf-8",
    )
    typed_operation_plan = _typed_operation_plan(_attribute_type_operation())
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    stage = provider_delta_source_projection_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=manifest_path,
        current_delta_fingerprint="sha256:test",
        provider_delta_semantic_change_report=report,
        provider_delta_typed_operation_plan=typed_operation_plan,
        code_package_delta={
            "package_root": "structure/ontology",
            "sources_root": "aware",
            "paths": [
                {
                    "relative_path": "aware/home/tv_channel.aware",
                    "language": "aware",
                }
            ],
        },
    )
    projection = cast(dict[str, object], stage["projection"])
    result = cast(dict[str, object], stage["result"])

    assert stage["ready"] is True
    assert projection["package_root"] == manifest_path.parent.resolve().as_posix()
    assert projection["sources_root"] == "aware"
    assert projection["source_refs"] == [
        "aware/home/tv_channel.aware",
        "home/tv_channel.aware",
    ]
    delta_set = cast(dict[str, object], result["delta_set"])
    entries = cast(list[object], delta_set["entries"])
    entry = cast(dict[str, object], entries[0])
    section_ref = cast(dict[str, object], entry["section_ref"])
    assert section_ref["relative_path"] == "home/tv_channel.aware"

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "home/tv_channel.aware"
    assert response.package_delta.paths[0].content_text == (
        "class TvChannel {\n" "    selected_channel String?\n" "}\n"
    )


@pytest.mark.asyncio
async def test_meta_blocked_source_projection_result_does_not_resolve_through_code_sdk(
    tmp_path: Path,
) -> None:
    _write_home_source(
        tmp_path=tmp_path,
        source_text=("class TvChannel {\n" "    selected_channel Int = 7\n" "}\n"),
    )
    operation = _attribute_default_value_operation()
    current = cast(dict[str, object], operation["current"])
    signature = dict(cast(dict[str, object], current["attribute_signature"]))
    signature["default_value"] = None
    current["attribute_signature"] = signature
    report, projection, result = _meta_source_projection_bundle(
        operation=operation,
        package_root=tmp_path,
        require_projected=False,
    )

    assert report["available"] is True
    assert result.projected is False
    assert result.delta_set is None
    assert result.skipped_events
    assert result.skipped_events[0].reason == (
        "meta_source_projection_attribute_config_default_value_requires_renderable_default_value"
    )

    response = await _resolve_with_code_sdk(projection=projection, result=result)

    assert response.success is False
    assert response.resolved is False
    assert response.package_delta is None
    assert response.path_count == 0
    assert response.diagnostics == [
        "result.delta_set is required for source_projection package-delta resolution."
    ]


async def _resolve_with_code_sdk(*, projection: Any, result: Any) -> Any:
    sdk = _service_backed_code_sdk()
    return await sdk.resolve_source_projection_package_delta(
        ResolveCodeSourceProjectionPackageDeltaRequest(
            projection=projection,
            result=result,
        )
    )


def _meta_source_projection_bundle(
    *,
    operation: dict[str, object],
    package_root: Path,
    require_projected: bool = True,
) -> tuple[Any, Any, Any]:
    typed_operation_plan = _typed_operation_plan(operation)
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    projection = code_source_projection_request_from_meta_change_report(
        report,
        package_name="home-ontology",
        package_root=str(package_root),
        target_language="aware",
    )
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan,
        package_name=projection.package_name,
        target_language=projection.target_language,
    )
    result = code_source_projection_result_from_meta_feature_results(
        report,
        projection=projection,
        feature_results=feature_results,
        require_projected=require_projected,
    )
    return report, projection, result


def _write_home_source(*, tmp_path: Path, source_text: str) -> None:
    source_path = tmp_path / "home" / "tv_channel.aware"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(source_text, encoding="utf-8")


def _typed_operation_plan(
    *typed_operations: dict[str, object],
) -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operations": typed_operations,
        "semantic_object_anchors": (),
        "blocked_operations": (),
    }


def _attribute_type_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel"
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "selected_channel",
        "description": "Selected channel index.",
        "default_value": None,
        "is_required": False,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "integer",
        },
    }
    current_signature = {
        **baseline_signature,
        "description": "Selected channel identifier.",
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "attribute_name": "selected_channel",
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "attribute_name": "selected_channel",
            "owner_key": "aware_demo.default.home.TvChannel",
            "attribute_signature": current_signature,
        },
    }


def _attribute_default_value_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel"
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "selected_channel",
        "description": "Selected channel index.",
        "default_value": "7",
        "is_required": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "integer",
        },
    }
    current_signature = {
        **baseline_signature,
        "default_value": "11",
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "attribute_name": "selected_channel",
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "attribute_name": "selected_channel",
            "owner_key": "aware_demo.default.home.TvChannel",
            "attribute_signature": current_signature,
        },
    }


def _function_description_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": "Rename the channel display label for humans and assistants.",
    }
    current_signature = {
        **baseline_signature,
        "description": (
            "Rename the channel display label and keep assistant-facing media "
            "context synchronized."
        ),
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.function.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "function_name": "rename",
                "owner_semantic_key": (
                    "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                ),
                "function_signature": baseline_signature,
            },
        },
        "current": {
            "function_name": "rename",
            "owner_semantic_key": (
                "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
            ),
            "function_signature": current_signature,
        },
    }


def _class_description_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    baseline_signature = {
        "class_fqn": "aware_demo.default.home.TvChannel",
        "name": "TvChannel",
        "description": "Old display contract.",
        "is_base": False,
        "is_edge": False,
        "value_mode": None,
        "identity_mode": None,
    }
    current_signature = {
        **baseline_signature,
        "description": ("Describes a media channel available to the home assistant."),
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.class.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfig",
        "ontology_subject_kind": "class",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "class_name": "TvChannel",
                "class_key": "aware_demo.default.home.TvChannel",
                "class_signature": baseline_signature,
            },
        },
        "current": {
            "class_name": "TvChannel",
            "class_key": "aware_demo.default.home.TvChannel",
            "class_signature": current_signature,
        },
    }


def _function_signature_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": "Rename the channel display label.",
        "inputs": (
            {
                "name": "display_name",
                "type": "input",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
        ),
        "outputs": (
            {
                "name": "result",
                "type": "output",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "class",
                    "class_fqn": "aware_demo.default.home.TvChannel",
                },
            },
        ),
    }
    current_signature = {
        **baseline_signature,
        "inputs": (
            {
                "name": "label",
                "type": "input",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
        ),
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.function.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "function_name": "rename",
                "owner_semantic_key": (
                    "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                ),
                "function_signature": baseline_signature,
            },
        },
        "current": {
            "function_name": "rename",
            "owner_semantic_key": (
                "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
            ),
            "function_signature": current_signature,
        },
    }


def _relationship_load_policy_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.RemoteControl:"
        "selected_channel:many_to_one:aware_demo.default.home.TvChannel"
    )
    baseline_signature = {
        "relationship_key": "selected_channel",
        "relationship_type": "many_to_one",
        "target_class_fqn": "aware_demo.default.home.TvChannel",
    }
    current_signature = {
        **baseline_signature,
        "forward_loading_strategy": "eager",
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.relationship.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigRelationship",
        "ontology_subject_kind": "relationship",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "relationship_key": "selected_channel",
                "relationship_signature": baseline_signature,
            },
        },
        "current": {
            "relationship_key": "selected_channel",
            "owner_semantic_key": "aware_demo.default.home.RemoteControl",
            "relationship_signature": current_signature,
        },
    }


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()
