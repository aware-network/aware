from __future__ import annotations

from collections.abc import Mapping, Sequence

from aware_sdk_runtime.features.contracts import (
    SdkOperationCatalogFeatureContext,
    SdkOperationCatalogFeaturePayloadUpdate,
    SdkOperationCatalogFeatureProvider,
    SdkOperationCatalogFeatureResult,
)


DELTA_EVENT_POLICY_FEATURE_KEY = "delta_event_policy"
SDK_DELTA_EVENT_POLICY_CONTRACT = "aware.sdk_delta_event_policy.v0"
SDK_DELTA_EVENT_POLICY_SOURCE = "aware_sdk_runtime.features.delta_event_policy"

_CODE_SECTION_SEGMENT_AUTHORITY = "aware_code.section_segment_registry"


def build_delta_event_policy_feature_result(
    context: SdkOperationCatalogFeatureContext,
) -> SdkOperationCatalogFeatureResult:
    operations = _operation_payloads(context.catalog_payload)
    method_updates: list[SdkOperationCatalogFeaturePayloadUpdate] = []
    operation_updates: list[SdkOperationCatalogFeaturePayloadUpdate] = []
    surface_policy_refs_by_surface_ref: dict[str, set[str]] = {}
    policy_ref_by_operation_ref: dict[str, str] = {}

    for operation in operations:
        operation_ref = _required_text(operation.get("operation_ref"))
        policy = _policy_for_operation(operation)
        policy_ref = _required_text(policy["policy_ref"])
        policy_ref_by_operation_ref[operation_ref] = policy_ref
        operation_updates.append(
            SdkOperationCatalogFeaturePayloadUpdate(
                target_ref=operation_ref,
                fields={"delta_event_policy": policy},
            )
        )
        for method in _surface_method_payloads(operation):
            method_ref = _required_text(method.get("method_ref"))
            surface_ref = _required_text(method.get("surface_ref"))
            surface_policy_refs_by_surface_ref.setdefault(surface_ref, set()).add(
                policy_ref
            )
            method_updates.append(
                SdkOperationCatalogFeaturePayloadUpdate(
                    target_ref=method_ref,
                    fields={"delta_event_policy_ref": policy_ref},
                )
            )

    for surface in _surface_payloads(context.catalog_payload):
        surface_ref = _required_text(surface.get("surface_ref"))
        for method in _surface_method_payloads(surface):
            operation_ref = _required_text(method.get("operation_ref"))
            policy_ref = policy_ref_by_operation_ref.get(operation_ref)
            if policy_ref is not None:
                surface_policy_refs_by_surface_ref.setdefault(surface_ref, set()).add(
                    policy_ref
                )
                method_updates.append(
                    SdkOperationCatalogFeaturePayloadUpdate(
                        target_ref=_required_text(method.get("method_ref")),
                        fields={"delta_event_policy_ref": policy_ref},
                    )
                )

    surface_updates = tuple(
        SdkOperationCatalogFeaturePayloadUpdate(
            target_ref=surface_ref,
            fields={
                "delta_event_policy_refs": sorted(
                    surface_policy_refs_by_surface_ref[surface_ref]
                )
            },
        )
        for surface_ref in sorted(surface_policy_refs_by_surface_ref)
    )

    return SdkOperationCatalogFeatureResult(
        feature_key=DELTA_EVENT_POLICY_FEATURE_KEY,
        catalog_fields={
            "catalog_features": [
                {
                    "feature_key": DELTA_EVENT_POLICY_FEATURE_KEY,
                    "contract": SDK_DELTA_EVENT_POLICY_CONTRACT,
                    "source": SDK_DELTA_EVENT_POLICY_SOURCE,
                },
            ],
            "feature_contracts": {
                DELTA_EVENT_POLICY_FEATURE_KEY: SDK_DELTA_EVENT_POLICY_CONTRACT,
            },
        },
        operation_fields=tuple(operation_updates),
        surface_fields=surface_updates,
        surface_method_fields=tuple(method_updates),
    )


SDK_DELTA_EVENT_POLICY_FEATURE_PROVIDER = SdkOperationCatalogFeatureProvider(
    feature_key=DELTA_EVENT_POLICY_FEATURE_KEY,
    catalog_builder=build_delta_event_policy_feature_result,
)


def _policy_for_operation(operation: Mapping[str, object]) -> dict[str, object]:
    operation_ref = _required_text(operation.get("operation_ref"))
    role = _operation_role(operation)
    policy = _policy_parts_for_role(role)
    return {
        "contract": SDK_DELTA_EVENT_POLICY_CONTRACT,
        "feature_key": DELTA_EVENT_POLICY_FEATURE_KEY,
        "policy_source": SDK_DELTA_EVENT_POLICY_SOURCE,
        "policy_ref": f"{operation_ref}.delta_event_policy",
        "operation_role": role,
        "delta_policy_ref": policy["delta_policy_ref"],
        "semantic_event_policy_ref": policy["semantic_event_policy_ref"],
        "source_projection_policy_ref": policy["source_projection_policy_ref"],
        "filesystem_policy_ref": policy["filesystem_policy_ref"],
        "surface_method_refs": sorted(
            _required_text(method.get("method_ref"))
            for method in _surface_method_payloads(operation)
        ),
        "code_capability_requirements": list(
            _code_capability_requirements(
                source_projection_policy_ref=_required_text(
                    policy["source_projection_policy_ref"]
                ),
            )
        ),
        "renderer_owned": False,
    }


def _operation_role(operation: Mapping[str, object]) -> str:
    operation_name = _required_text(operation.get("operation_name")).casefold()
    method_family = _optional_text(operation.get("method_family"))
    effect = _required_text(operation.get("effect")).casefold()
    refs = " ".join(
        (
            operation_name,
            " ".join(_text_sequence(operation.get("surface_refs"))),
            " ".join(_text_sequence(operation.get("endpoint_refs"))),
        )
    ).casefold()

    if "materialize" in refs:
        return "materialize_delta"
    if "commit" in refs or "revision" in refs:
        return "commit_revision"
    if "build" in refs:
        return "build_revision"
    if "publish" in refs or "branch" in refs:
        return "publish_branch_head"
    if "delta" in refs or "status" in refs or effect == "read":
        if method_family in {"retrieve", "list", "resolve"} or effect == "read":
            return "observe_status"
    if effect == "write":
        return "mutate"
    if effect == "stream":
        return "stream_events"
    return "observe_status"


def _policy_parts_for_role(role: str) -> dict[str, str]:
    if role == "materialize_delta":
        return {
            "delta_policy_ref": "aware.delta.consume_local_changes",
            "semantic_event_policy_ref": "aware.semantic_event.consume_resolved",
            "source_projection_policy_ref": (
                "code.source_projection.resolve_package_delta"
            ),
            "filesystem_policy_ref": "filesystem.apply_code_package_delta",
        }
    if role == "commit_revision":
        return {
            "delta_policy_ref": "aware.delta.require_materialized_clean_or_verified",
            "semantic_event_policy_ref": "aware.semantic_event.require_receipts",
            "source_projection_policy_ref": "code.source_projection.receipt_only",
            "filesystem_policy_ref": "filesystem.no_apply",
        }
    if role == "build_revision":
        return {
            "delta_policy_ref": "aware.delta.require_verified_revision",
            "semantic_event_policy_ref": "aware.semantic_event.require_receipts",
            "source_projection_policy_ref": "code.source_projection.receipt_only",
            "filesystem_policy_ref": "filesystem.no_apply",
        }
    if role == "publish_branch_head":
        return {
            "delta_policy_ref": "aware.delta.require_committed_revision",
            "semantic_event_policy_ref": "aware.semantic_event.require_receipts",
            "source_projection_policy_ref": "code.source_projection.receipt_only",
            "filesystem_policy_ref": "filesystem.no_apply",
        }
    if role == "stream_events":
        return {
            "delta_policy_ref": "aware.delta.stream",
            "semantic_event_policy_ref": "aware.semantic_event.stream",
            "source_projection_policy_ref": "code.source_projection.observe",
            "filesystem_policy_ref": "filesystem.no_apply",
        }
    if role == "mutate":
        return {
            "delta_policy_ref": "aware.delta.mutate",
            "semantic_event_policy_ref": "aware.semantic_event.receipt_required",
            "source_projection_policy_ref": "code.source_projection.receipt_only",
            "filesystem_policy_ref": "filesystem.no_apply",
        }
    return {
        "delta_policy_ref": "aware.delta.observe",
        "semantic_event_policy_ref": "aware.semantic_event.observe",
        "source_projection_policy_ref": "code.source_projection.observe",
        "filesystem_policy_ref": "filesystem.no_apply",
    }


def _code_capability_requirements(
    *,
    source_projection_policy_ref: str,
) -> tuple[dict[str, object], ...]:
    if source_projection_policy_ref != "code.source_projection.resolve_package_delta":
        return ()
    return (
        {
            "capability_ref": "code.source_projection.resolve_package_delta",
            "authority": _CODE_SECTION_SEGMENT_AUTHORITY,
            "required": True,
        },
        {
            "capability_ref": "code.section_segment_capability_registry",
            "authority": _CODE_SECTION_SEGMENT_AUTHORITY,
            "required": True,
        },
    )


def _operation_payloads(
    catalog_payload: Mapping[str, object]
) -> tuple[Mapping[str, object], ...]:
    return tuple(_mapping_sequence(catalog_payload.get("operations")))


def _surface_payloads(
    catalog_payload: Mapping[str, object]
) -> tuple[Mapping[str, object], ...]:
    return tuple(_mapping_sequence(catalog_payload.get("surfaces")))


def _surface_method_payloads(
    payload: Mapping[str, object]
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        _mapping_sequence(payload.get("surface_methods") or payload.get("methods"))
    )


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _text_sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def _required_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("SDK delta-event policy requires non-empty text.")
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DELTA_EVENT_POLICY_FEATURE_KEY",
    "SDK_DELTA_EVENT_POLICY_CONTRACT",
    "SDK_DELTA_EVENT_POLICY_FEATURE_PROVIDER",
    "build_delta_event_policy_feature_result",
]
