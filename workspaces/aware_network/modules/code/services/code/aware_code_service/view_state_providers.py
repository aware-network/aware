from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aware_code_service_dto.code.features.package_layout import (
    CodePackageLayoutContract,
    DiscoverCodePackageLayoutsResponse,
)
from aware_code_service_dto.code.features.semantic_source_meaning import (
    CodeSemanticSourceMeaningSource,
    ResolveCodeSemanticSourceMeaningResponse,
)
from aware_code_service_dto.code.features.view_state import (
    CodeEditorViewStateV1,
    CodeViewStateCode as CodePackageSelectorCodeV1,
    CodeViewStatePackage as CodePackageSelectorPackageV1,
    CodeViewStateSourceRef as CodeSourceRefV1,
    CodePackageSelectorViewStateV1,
    ResolveCodeEditorViewResponse,
    ResolveCodePackageSelectorViewResponse,
)
from aware_service_runtime.api_ingress.view_fulfillment import (
    ServiceApiViewFulfillmentPlan,
)

CODE_PACKAGE_SELECTOR_API_VIEW_REF = "code.package_selector"
CODE_EDITOR_API_VIEW_REF = "code.editor"
CODE_PACKAGE_SELECTOR_PROJECTION_VIEW_KEY = "codes.selector.v1"
CODE_EDITOR_PROJECTION_VIEW_KEY = "codes.editor.v1"
CODE_PACKAGE_SELECTOR_PROVIDER_REF = (
    "aware_code_service.view_state_providers.code_package_selector_view_state"
)
CODE_EDITOR_PROVIDER_REF = (
    "aware_code_service.view_state_providers.code_editor_view_state"
)


class CodeServiceViewFulfillmentEvidenceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_kind: str = Field(default="code_service")
    service_id: str | None = Field(default=None)
    api_view_id: str | None = Field(default=None)
    service_operation_config_api_view_id: str | None = Field(default=None)
    service_operation_config_id: str | None = Field(default=None)
    service_config_api_id: str | None = Field(default=None)
    provider_kind: str | None = Field(default=None)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class CodePackageSelectorV1ServiceProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    response: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | Mapping[str, Any]
        | None
    ) = None
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    codes: list[Mapping[str, Any]] = Field(default_factory=list)
    fulfillment: CodeServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] = Field(
        default_factory=CodeServiceViewFulfillmentEvidenceV1
    )
    provenance: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class CodeEditorV1ServiceProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    response: (
        ResolveCodeSemanticSourceMeaningResponse
        | ResolveCodeEditorViewResponse
        | Mapping[str, Any]
        | None
    ) = None
    sources: list[CodeSemanticSourceMeaningSource | Mapping[str, Any]] = Field(
        default_factory=list
    )
    selected_source_key: str | None = Field(default=None)
    selected_section_key: str | None = Field(default=None)
    section_anchors: list[Mapping[str, Any]] = Field(default_factory=list)
    materialization: Mapping[str, Any] | None = Field(default=None)
    fulfillment: CodeServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] = Field(
        default_factory=CodeServiceViewFulfillmentEvidenceV1
    )
    provenance: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


def code_package_selector_view_state_from_response(
    response: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | Mapping[str, Any]
        | None
    ),
    *,
    selected_package_key: str | None = None,
    selected_code_key: str | None = None,
    codes: Sequence[Mapping[str, Any]] = (),
    fulfillment_plan: ServiceApiViewFulfillmentPlan | None = None,
    fulfillment: CodeServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> CodePackageSelectorViewStateV1:
    if fulfillment_plan is not None and fulfillment is not None:
        raise ValueError("Pass either fulfillment_plan or fulfillment, not both.")
    return code_package_selector_view_state_from_input(
        CodePackageSelectorV1ServiceProviderInput(
            response=response,
            selected_package_key=selected_package_key,
            selected_code_key=selected_code_key,
            codes=list(codes),
            fulfillment=(
                _fulfillment_evidence_from_plan(fulfillment_plan)
                if fulfillment_plan is not None
                else _fulfillment_evidence(fulfillment)
            ),
            provenance=dict(provenance or {}),
        )
    )


def code_package_selector_view_state_from_input(
    provider_input: CodePackageSelectorV1ServiceProviderInput | Mapping[str, Any],
) -> CodePackageSelectorViewStateV1:
    typed_input = CodePackageSelectorV1ServiceProviderInput.model_validate(
        provider_input
    )
    response = _typed_selector_response(typed_input.response)
    packages = _selector_packages(response)
    codes = _selector_codes(response=response, explicit_codes=typed_input.codes)
    return CodePackageSelectorViewStateV1(
        status=_selector_status(response=response, package_count=len(packages)),
        source_mode=_selector_source_mode(response),
        selected_package_key=typed_input.selected_package_key
        or _optional_text(getattr(response, "selected_package_key", None)),
        selected_code_key=typed_input.selected_code_key
        or _optional_text(getattr(response, "selected_code_key", None)),
        packages=packages,
        codes=codes,
        summary=_count_summary(
            packages, singular="Code package", plural="Code packages"
        ),
        error=_optional_text(getattr(response, "error", None)),
        provenance=_provenance_payload(
            provider_ref=CODE_PACKAGE_SELECTOR_PROVIDER_REF,
            api_view_ref=CODE_PACKAGE_SELECTOR_API_VIEW_REF,
            projection_view_key=CODE_PACKAGE_SELECTOR_PROJECTION_VIEW_KEY,
            fulfillment=_fulfillment_evidence(typed_input.fulfillment),
            provenance=typed_input.provenance,
            counts={"package_count": len(packages), "code_count": len(codes)},
        ),
    )


def code_package_selector_view_state(
    *,
    provider_input: CodePackageSelectorV1ServiceProviderInput | Mapping[str, Any],
) -> CodePackageSelectorViewStateV1:
    return code_package_selector_view_state_from_input(provider_input)


setattr(
    code_package_selector_view_state,
    "provider_input_resolver",
    CodePackageSelectorV1ServiceProviderInput.model_validate,
)


def code_editor_view_state_from_response(
    response: (
        ResolveCodeSemanticSourceMeaningResponse
        | ResolveCodeEditorViewResponse
        | Mapping[str, Any]
        | None
    ),
    *,
    sources: Sequence[CodeSemanticSourceMeaningSource | Mapping[str, Any]] = (),
    selected_source_key: str | None = None,
    selected_section_key: str | None = None,
    section_anchors: Sequence[Mapping[str, Any]] = (),
    materialization: Mapping[str, Any] | None = None,
    fulfillment_plan: ServiceApiViewFulfillmentPlan | None = None,
    fulfillment: CodeServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> CodeEditorViewStateV1:
    if fulfillment_plan is not None and fulfillment is not None:
        raise ValueError("Pass either fulfillment_plan or fulfillment, not both.")
    return code_editor_view_state_from_input(
        CodeEditorV1ServiceProviderInput(
            response=response,
            sources=list(sources),
            selected_source_key=selected_source_key,
            selected_section_key=selected_section_key,
            section_anchors=list(section_anchors),
            materialization=materialization,
            fulfillment=(
                _fulfillment_evidence_from_plan(fulfillment_plan)
                if fulfillment_plan is not None
                else _fulfillment_evidence(fulfillment)
            ),
            provenance=dict(provenance or {}),
        )
    )


def code_editor_view_state_from_input(
    provider_input: CodeEditorV1ServiceProviderInput | Mapping[str, Any],
) -> CodeEditorViewStateV1:
    typed_input = CodeEditorV1ServiceProviderInput.model_validate(provider_input)
    response = _typed_editor_response(typed_input.response)
    source = _selected_source(
        sources=typed_input.sources,
        selected_source_key=typed_input.selected_source_key,
    )
    source_ref = _source_ref_from_editor_response(response)
    semantic_events = _model_payloads(getattr(response, "semantic_events", ()))
    semantic_deltas = _model_payloads(getattr(response, "semantic_deltas", ()))
    diagnostics = [str(item) for item in getattr(response, "diagnostics", ()) or ()]
    section_anchors = _section_anchors_from_editor_response(
        response=response,
        explicit_section_anchors=typed_input.section_anchors,
    )
    return CodeEditorViewStateV1(
        status=_editor_status(response=response, source=source),
        source_ref=source_ref or _source_ref(source),
        source_text=_optional_source_text(
            getattr(response, "source_text", None)
            if source_ref is not None
            else getattr(source, "source_text", None)
        ),
        selected_section_key=typed_input.selected_section_key
        or _optional_text(getattr(response, "selected_section_key", None)),
        section_anchors=section_anchors,
        semantic_events=semantic_events,
        semantic_deltas=semantic_deltas,
        diagnostics=diagnostics,
        materialization=(
            dict(typed_input.materialization)
            if typed_input.materialization is not None
            else None
        ),
        summary=_optional_text(getattr(response, "summary", None))
        or _editor_summary(source=source, semantic_events=semantic_events),
        error=_optional_text(getattr(response, "error", None)),
        provenance=_provenance_payload(
            provider_ref=CODE_EDITOR_PROVIDER_REF,
            api_view_ref=CODE_EDITOR_API_VIEW_REF,
            projection_view_key=CODE_EDITOR_PROJECTION_VIEW_KEY,
            fulfillment=_fulfillment_evidence(typed_input.fulfillment),
            provenance=typed_input.provenance,
            counts={
                "source_count": len(typed_input.sources),
                "semantic_event_count": len(semantic_events),
                "semantic_delta_count": len(semantic_deltas),
            },
        ),
    )


def code_editor_view_state(
    *,
    provider_input: CodeEditorV1ServiceProviderInput | Mapping[str, Any],
) -> CodeEditorViewStateV1:
    return code_editor_view_state_from_input(provider_input)


setattr(
    code_editor_view_state,
    "provider_input_resolver",
    CodeEditorV1ServiceProviderInput.model_validate,
)


def _typed_selector_response(
    value: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | Mapping[str, Any]
        | None
    ),
) -> DiscoverCodePackageLayoutsResponse | ResolveCodePackageSelectorViewResponse | None:
    if value is None:
        return None
    if isinstance(
        value,
        (DiscoverCodePackageLayoutsResponse, ResolveCodePackageSelectorViewResponse),
    ):
        return value
    if isinstance(value, Mapping):
        if (
            value.get("operation") == "resolve_code_package_selector_view"
            or "packages" in value
        ):
            return ResolveCodePackageSelectorViewResponse.model_validate(value)
        return DiscoverCodePackageLayoutsResponse.model_validate(value)
    return None


def _typed_editor_response(
    value: (
        ResolveCodeSemanticSourceMeaningResponse
        | ResolveCodeEditorViewResponse
        | Mapping[str, Any]
        | None
    ),
) -> ResolveCodeSemanticSourceMeaningResponse | ResolveCodeEditorViewResponse | None:
    if value is None:
        return None
    if isinstance(
        value, (ResolveCodeSemanticSourceMeaningResponse, ResolveCodeEditorViewResponse)
    ):
        return value
    if isinstance(value, Mapping):
        if (
            value.get("operation") == "resolve_code_editor_view"
            or "source_ref" in value
        ):
            return ResolveCodeEditorViewResponse.model_validate(value)
        return ResolveCodeSemanticSourceMeaningResponse.model_validate(value)
    return None


def _selector_packages(
    response: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | None
    ),
) -> list[CodePackageSelectorPackageV1]:
    if isinstance(response, ResolveCodePackageSelectorViewResponse):
        return [
            _selector_package_from_mapping(_model_payload(package) or {})
            for package in response.packages
        ]
    contracts = (
        getattr(response, "layout_contracts", ()) if response is not None else ()
    )
    return [_selector_package(contract) for contract in contracts or ()]


def _selector_package(
    contract: CodePackageLayoutContract,
) -> CodePackageSelectorPackageV1:
    metadata = _mapping_payload(getattr(contract, "metadata", None))
    manifest_path = _optional_text(getattr(contract, "manifest_path", None))
    manifest_path = manifest_path or _optional_text(
        getattr(contract, "manifest_relative_path", None)
    )
    package_name = _optional_text(getattr(contract, "package_name", None))
    selector_key = manifest_path or package_name or "code-package"
    return CodePackageSelectorPackageV1(
        selector_key=selector_key,
        code_package_name=package_name,
        package_root=_optional_text(getattr(contract, "package_root", None)),
        manifest_path=manifest_path,
        package_fqn=_optional_text(getattr(contract, "package_fqn", None))
        or _optional_text(metadata.get("package_fqn")),
        provider_key=_optional_text(getattr(contract, "provider_key", None))
        or _optional_text(metadata.get("provider_key")),
        metadata=metadata,
    )


def _selector_package_from_mapping(
    value: Mapping[str, Any],
) -> CodePackageSelectorPackageV1:
    selector_key = _optional_text(value.get("selector_key"))
    package_name = _optional_text(value.get("code_package_name")) or _optional_text(
        value.get("package_name")
    )
    manifest_path = _optional_text(value.get("manifest_path"))
    return CodePackageSelectorPackageV1(
        selector_key=selector_key or manifest_path or package_name or "code-package",
        code_package_id=_optional_text(value.get("code_package_id")),
        code_package_name=package_name,
        package_root=_optional_text(value.get("package_root")),
        manifest_path=manifest_path,
        package_fqn=_optional_text(value.get("package_fqn")),
        provider_key=_optional_text(value.get("provider_key")),
        metadata=_mapping_payload(value.get("metadata")),
    )


def _selector_codes(
    *,
    response: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | None
    ),
    explicit_codes: Sequence[Mapping[str, Any]],
) -> list[CodePackageSelectorCodeV1]:
    if isinstance(response, ResolveCodePackageSelectorViewResponse):
        return [_selector_code(_model_payload(code) or {}) for code in response.codes]
    return [_selector_code(item) for item in explicit_codes]


def _selector_code(value: Mapping[str, Any]) -> CodePackageSelectorCodeV1:
    selector_key = _optional_text(value.get("selector_key")) or _optional_text(
        value.get("relative_path")
    )
    return CodePackageSelectorCodeV1(
        selector_key=selector_key or "code",
        code_id=_optional_text(value.get("code_id")),
        code_package_code_id=_optional_text(value.get("code_package_code_id")),
        code_package_id=_optional_text(value.get("code_package_id")),
        relative_path=_optional_text(value.get("relative_path")),
        language=_optional_text(value.get("language")),
        source_hash=_optional_text(value.get("source_hash")),
        label=_optional_text(value.get("label")),
        metadata=_mapping_payload(value.get("metadata")),
    )


def _selected_source(
    *,
    sources: Sequence[CodeSemanticSourceMeaningSource | Mapping[str, Any]],
    selected_source_key: str | None,
) -> CodeSemanticSourceMeaningSource | None:
    typed_sources = [
        (
            source
            if isinstance(source, CodeSemanticSourceMeaningSource)
            else CodeSemanticSourceMeaningSource.model_validate(source)
        )
        for source in sources
    ]
    if not typed_sources:
        return None
    if selected_source_key is None:
        return typed_sources[0]
    for source in typed_sources:
        if source.source_key == selected_source_key:
            return source
    return typed_sources[0]


def _source_ref(
    source: CodeSemanticSourceMeaningSource | None,
) -> CodeSourceRefV1 | None:
    if source is None:
        return None
    return CodeSourceRefV1(
        source_key=source.source_key,
        relative_path=source.relative_path,
        language=source.language,
        source_hash=source.before_hash,
        metadata=_mapping_payload(source.metadata),
    )


def _source_ref_from_editor_response(
    response: (
        ResolveCodeSemanticSourceMeaningResponse | ResolveCodeEditorViewResponse | None
    ),
) -> CodeSourceRefV1 | None:
    if not isinstance(response, ResolveCodeEditorViewResponse):
        return None
    payload = _model_payload(response.source_ref)
    if payload is None:
        return None
    return CodeSourceRefV1(
        source_key=_optional_text(payload.get("source_key")) or "code-source",
        code_id=_optional_text(payload.get("code_id")),
        code_package_id=_optional_text(payload.get("code_package_id")),
        code_package_code_id=_optional_text(payload.get("code_package_code_id")),
        package_name=_optional_text(payload.get("package_name")),
        relative_path=_optional_text(payload.get("relative_path")),
        language=_optional_text(payload.get("language")),
        source_hash=_optional_text(payload.get("source_hash")),
        metadata=_mapping_payload(payload.get("metadata")),
    )


def _section_anchors_from_editor_response(
    *,
    response: (
        ResolveCodeSemanticSourceMeaningResponse | ResolveCodeEditorViewResponse | None
    ),
    explicit_section_anchors: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    if isinstance(response, ResolveCodeEditorViewResponse):
        return [_model_payload(anchor) or {} for anchor in response.section_anchors]
    return list(explicit_section_anchors)


def _selector_status(
    *,
    response: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | None
    ),
    package_count: int,
) -> str:
    if response is None:
        return "waiting"
    if getattr(response, "success", False) is not True:
        return "error"
    status = (
        _optional_text(getattr(response, "status", None))
        if isinstance(response, ResolveCodePackageSelectorViewResponse)
        else None
    )
    if status is not None:
        return status
    return "ready" if package_count else "empty"


def _selector_source_mode(
    response: (
        DiscoverCodePackageLayoutsResponse
        | ResolveCodePackageSelectorViewResponse
        | None
    ),
) -> str:
    return _optional_text(getattr(response, "source_kind", None)) or "code_service"


def _editor_status(
    *,
    response: (
        ResolveCodeSemanticSourceMeaningResponse | ResolveCodeEditorViewResponse | None
    ),
    source: CodeSemanticSourceMeaningSource | None,
) -> str:
    if response is not None and getattr(response, "success", False) is not True:
        return "error"
    status = (
        _optional_text(getattr(response, "status", None))
        if isinstance(response, ResolveCodeEditorViewResponse)
        else None
    )
    if status is not None:
        return status
    if source is None:
        return "waiting"
    return "ready"


def _count_summary(items: Sequence[object], *, singular: str, plural: str) -> str:
    count = len(items)
    label = singular if count == 1 else plural
    return f"{count} {label}."


def _editor_summary(
    *,
    source: CodeSemanticSourceMeaningSource | None,
    semantic_events: Sequence[Mapping[str, Any]],
) -> str:
    if source is None:
        return "No Code source selected."
    event_count = len(semantic_events)
    return f"{source.source_key}: {event_count} semantic events."


def _fulfillment_evidence(
    value: CodeServiceViewFulfillmentEvidenceV1 | Mapping[str, Any] | None,
) -> CodeServiceViewFulfillmentEvidenceV1:
    if isinstance(value, CodeServiceViewFulfillmentEvidenceV1):
        return value
    return CodeServiceViewFulfillmentEvidenceV1.model_validate(value or {})


def _fulfillment_evidence_from_plan(
    plan: ServiceApiViewFulfillmentPlan,
) -> CodeServiceViewFulfillmentEvidenceV1:
    return CodeServiceViewFulfillmentEvidenceV1(
        service_id=_optional_text(plan.service_id),
        api_view_id=_optional_text(plan.api_view_id),
        service_operation_config_api_view_id=_optional_text(
            plan.service_operation_config_api_view_id
        ),
        service_operation_config_id=_optional_text(plan.service_operation_config_id),
        service_config_api_id=_optional_text(plan.service_config_api_id),
        provider_kind=_optional_text(plan.provider_kind),
    )


def _provenance_payload(
    *,
    provider_ref: str,
    api_view_ref: str,
    projection_view_key: str,
    fulfillment: CodeServiceViewFulfillmentEvidenceV1,
    provenance: Mapping[str, Any],
    counts: Mapping[str, int],
) -> dict[str, Any]:
    return {
        "source_kind": "code_service",
        "state_provider_ref": provider_ref,
        "api_view_ref": api_view_ref,
        "projection_view_key": projection_view_key,
        **fulfillment.to_json(),
        **dict(provenance),
        **dict(counts),
    }


def _model_payload(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return None


def _model_payloads(values: object) -> list[dict[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return []
    payloads: list[dict[str, Any]] = []
    for value in values:
        payload = _model_payload(value)
        if payload is not None:
            payloads.append(payload)
    return payloads


def _mapping_payload(value: object) -> dict[str, Any]:
    payload = _model_payload(value)
    return payload or {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_source_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = [
    "CODE_EDITOR_PROVIDER_REF",
    "CODE_PACKAGE_SELECTOR_PROVIDER_REF",
    "CodeEditorV1ServiceProviderInput",
    "CodePackageSelectorV1ServiceProviderInput",
    "CodeServiceViewFulfillmentEvidenceV1",
    "code_editor_view_state",
    "code_editor_view_state_from_input",
    "code_editor_view_state_from_response",
    "code_package_selector_view_state",
    "code_package_selector_view_state_from_input",
    "code_package_selector_view_state_from_response",
]
