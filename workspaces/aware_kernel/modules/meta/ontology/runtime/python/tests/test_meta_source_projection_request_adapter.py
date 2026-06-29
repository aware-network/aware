from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from aware_code.parse.sections import collect_top_level_section_identity_descriptors
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_sdk import (
    AwareCodeSdk,
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionRef,
    CodeSegmentRef,
    FingerprintCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionRequest,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ValidateCodeSourceProjectionRequest,
)
from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
)
from aware_meta.materialization.deltas.source_projection import (
    META_SOURCE_PROJECTION_PRODUCT_INTENT,
    META_SOURCE_PROJECTION_PROVIDER_KEY,
    code_source_projection_request_from_meta_change_report,
    code_source_projection_result_from_meta_section_delta_entries,
)


def _service_backed_code_sdk() -> AwareCodeSdk:
    code_service = pytest.importorskip("aware_code_service")
    return AwareCodeSdk(
        api_client=cast(Any, code_service.build_local_code_service_api_client())
    )


def test_meta_source_projection_request_adapter_maps_change_report_to_code_dto() -> (
    None
):
    projection = code_source_projection_request_from_meta_change_report(
        _ready_change_report(),
        package_name="home-ontology",
        package_root=".",
        sources_root="home",
        target_language="python",
        source_refs=("home/tv_channel.aware",),
    )

    assert projection.provider_key == META_SOURCE_PROJECTION_PROVIDER_KEY
    assert projection.semantic_owner == "aware_meta.ocg"
    assert projection.product_intent == META_SOURCE_PROJECTION_PRODUCT_INTENT
    assert projection.package_name == "home-ontology"
    assert projection.package_root == "."
    assert projection.sources_root == "home"
    assert projection.target_language == "python"
    assert projection.source_refs == ["home/tv_channel.aware"]
    assert len(projection.events) == 1
    assert len(projection.action_bindings) == 1

    event = projection.events[0]
    assert event.event_key == "aware_meta.provider_delta.world_change.attribute.update"
    assert event.semantic_key == "graph:home.Home/node:home.Device/attribute:name"
    assert event.verb == "update"
    assert event.subject_type == "attribute"
    assert event.payload is not None
    assert event.payload["ontology_subject_kind"] == "attribute"

    action = projection.action_bindings[0]
    assert action.event_key == event.event_key
    assert action.action_type == "source_projection"
    assert action.policy_key == "aware_meta.ocg.source_projection.attribute.update"
    assert action.product_intent == META_SOURCE_PROJECTION_PRODUCT_INTENT


@pytest.mark.asyncio
async def test_meta_source_projection_request_validates_through_code_sdk() -> None:
    sdk = _service_backed_code_sdk()
    projection = code_source_projection_request_from_meta_change_report(
        _ready_change_report(),
        package_name="home-ontology",
        package_root=".",
        sources_root="home",
    )

    valid_response = await sdk.validate_source_projection(
        ValidateCodeSourceProjectionRequest(projection=projection)
    )
    normalized_response = await sdk.normalize_source_projection(
        NormalizeCodeSourceProjectionRequest(projection=projection)
    )
    fingerprint_response = await sdk.fingerprint_source_projection(
        FingerprintCodeSourceProjectionRequest(projection=projection)
    )

    assert valid_response.success is True
    assert valid_response.valid is True
    assert valid_response.event_count == 1
    assert valid_response.action_count == 1
    assert normalized_response.success is True
    assert normalized_response.projection is not None
    assert normalized_response.projection.events[0].event_key == (
        "aware_meta.provider_delta.world_change.attribute.update"
    )
    assert fingerprint_response.success is True
    assert fingerprint_response.fingerprint is not None
    assert fingerprint_response.event_count == 1


def test_meta_source_projection_request_blocks_unready_change_report() -> None:
    blocked_report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_blocked",
            "reason": "missing_baseline",
            "dirty_entry_count": 0,
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_blocked",
            "reason": "blocked",
            "typed_operations": (),
        },
    )

    with pytest.raises(ValueError, match="requires a ready semantic change report"):
        code_source_projection_request_from_meta_change_report(blocked_report)


@pytest.mark.asyncio
async def test_meta_source_projection_result_resolves_through_code_sdk(
    tmp_path: Path,
) -> None:
    setup_code_plugins()
    sdk = _service_backed_code_sdk()
    source_text = "def demo():\n    return 1\n"
    target = tmp_path / "demo.py"
    target.write_text(source_text, encoding="utf-8")
    descriptor = next(
        item
        for item in collect_top_level_section_identity_descriptors(
            content=source_text,
            language=CodeLanguage.python,
        )
        if item.section_type is CodeSectionType.function
    )
    byte_start = source_text.index("return 1")
    byte_end = byte_start + len("return 1")
    report = _ready_change_report()
    projection = code_source_projection_request_from_meta_change_report(
        report,
        package_name="home-ontology",
        package_root=str(tmp_path),
        target_language="python",
        source_refs=("demo.py",),
    )
    event = projection.events[0]

    result = code_source_projection_result_from_meta_section_delta_entries(
        report,
        projection=projection,
        delta_entries=(
            CodeSectionDeltaEntry(
                operation=CodeSectionDeltaOperationKind.replace_segment,
                section_ref=CodeSectionRef(
                    package_name=projection.package_name,
                    relative_path="demo.py",
                    language="python",
                    section_type="function",
                    qualname="demo",
                    identity_hash=descriptor.identity_hash,
                    semantic_key=event.semantic_key,
                    source_refs=["demo.py"],
                ),
                segment_ref=CodeSegmentRef(
                    segment_name="body",
                    byte_start=byte_start,
                    byte_end=byte_end,
                    before_segment_hash=_digest("return 1"),
                ),
                content_text="return 2",
                before_hash=_digest(source_text),
                after_hash=_digest("return 2"),
                event_ref=event.event_key,
                semantic_key=event.semantic_key,
                provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
            ),
        ),
    )

    response = await sdk.resolve_source_projection_package_delta(
        ResolveCodeSourceProjectionPackageDeltaRequest(
            projection=projection,
            result=result,
        )
    )

    assert result.projected is True
    assert result.delta_set is not None
    assert result.delta_set.entries[0].event_ref == event.event_key
    assert response.success is True
    assert response.resolved is True
    assert response.diagnostics == []
    assert response.package_delta is not None
    assert response.package_delta.paths[0].relative_path == "demo.py"
    assert response.package_delta.paths[0].content_text == "def demo():\n    return 2\n"


def test_meta_source_projection_result_marks_unprojected_events_skipped() -> None:
    report = _ready_multi_event_report()
    projection = code_source_projection_request_from_meta_change_report(report)
    projected_event = projection.events[0]

    result = code_source_projection_result_from_meta_section_delta_entries(
        report,
        projection=projection,
        delta_entries=(_demo_delta_entry(event_key=projected_event.event_key),),
    )

    assert result.projected is True
    assert result.delta_set is not None
    assert result.delta_set.entries[0].event_ref == projected_event.event_key
    assert len(result.skipped_events) == 1
    assert result.skipped_events[0].event_key == projection.events[1].event_key
    assert result.skipped_events[0].reason == (
        "no CodeSectionDeltaEntry emitted for Meta world change"
    )


def _ready_change_report() -> dict[str, object]:
    return _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "ready",
            "typed_operations": (_attribute_update_operation(),),
            "semantic_object_anchors": (),
            "blocked_operations": (),
        },
    )


def _ready_multi_event_report() -> dict[str, object]:
    return _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 2,
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "ready",
            "typed_operations": (
                _attribute_update_operation(),
                _function_update_operation(),
            ),
            "semantic_object_anchors": (),
            "blocked_operations": (),
        },
    )


def _attribute_update_operation() -> dict[str, object]:
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": "op:attribute:update:name",
        "operation_family": "update",
        "ontology_subject_kind": "attribute",
        "semantic_key": "graph:home.Home/node:home.Device/attribute:name",
        "provider_operation_type": "attribute_update",
        "delta_keys": ("delta:attribute:name",),
        "condition_keys": ("meta.provider_delta.subject_kind.attribute",),
        "baseline": {
            "name": "name",
            "type_descriptor": "Int",
        },
        "current": {
            "name": "name",
            "type_descriptor": "String",
        },
    }


def _function_update_operation() -> dict[str, object]:
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": "op:function:update:demo",
        "operation_family": "update",
        "ontology_subject_kind": "function",
        "semantic_key": "graph:home.Home/node:home.Device/function:demo",
        "provider_operation_type": "function_update",
        "delta_keys": ("delta:function:demo",),
        "condition_keys": ("meta.provider_delta.subject_kind.function",),
        "baseline": {
            "name": "demo",
            "body": "return 1",
        },
        "current": {
            "name": "demo",
            "body": "return 2",
        },
    }


def _demo_delta_entry(*, event_key: str) -> CodeSectionDeltaEntry:
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=CodeSectionRef(
            relative_path="demo.py",
            language="python",
            section_type="function",
            qualname="demo",
        ),
        segment_ref=CodeSegmentRef(
            segment_name="body",
            byte_start=16,
            byte_end=24,
            before_segment_hash=_digest("return 1"),
        ),
        content_text="return 2",
        before_hash=_digest("def demo():\n    return 1\n"),
        after_hash=_digest("return 2"),
        event_ref=event_key,
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
    )


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()
