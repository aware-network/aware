# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_code_service_dto.code.features.generated_materialization_delta import (
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    FingerprintCodeGeneratedMaterializationDeltaResponse,
    NormalizeCodeGeneratedMaterializationDeltaRequest,
    NormalizeCodeGeneratedMaterializationDeltaResponse,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
    ValidateCodeGeneratedMaterializationDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaResponse,
)
from aware_code_service_dto.code.features.grammar_anchor_binding import (
    ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ResolveCodeGrammarAnchorBindingEvidenceResponse,
    ValidateCodeGrammarAnchorBindingRequest,
    ValidateCodeGrammarAnchorBindingResponse,
)
from aware_code_service_dto.code.features.grammar_anchor_render_delta import (
    ResolveCodeGrammarAnchorRenderDeltaRequest,
    ResolveCodeGrammarAnchorRenderDeltaResponse,
)
from aware_code_service_dto.code.features.grammar_profile import (
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
)
from aware_code_service_dto.code.features.package_delta import (
    FingerprintCodePackageDeltaRequest,
    FingerprintCodePackageDeltaResponse,
    NormalizeCodePackageDeltaRequest,
    NormalizeCodePackageDeltaResponse,
)
from aware_code_service_dto.code.features.package_layout import (
    DescribeCodePackageLayoutRequest,
    DescribeCodePackageLayoutResponse,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    ValidateCodePackageLayoutRequest,
    ValidateCodePackageLayoutResponse,
)
from aware_code_service_dto.code.features.section_delta import (
    FingerprintCodeSectionDeltaRequest,
    FingerprintCodeSectionDeltaResponse,
    NormalizeCodeSectionDeltaRequest,
    NormalizeCodeSectionDeltaResponse,
    ResolveCodeSectionDeltaPackageDeltaRequest,
    ResolveCodeSectionDeltaPackageDeltaResponse,
    ResolveCodeSegmentRenderPolicyRequest,
    ResolveCodeSegmentRenderPolicyResponse,
    ValidateCodeSectionDeltaRequest,
    ValidateCodeSectionDeltaResponse,
)
from aware_code_service_dto.code.features.semantic_analysis import (
    PreviewCodeSemanticAnalysisPackageDeltaRequest,
    PreviewCodeSemanticAnalysisPackageDeltaResponse,
)
from aware_code_service_dto.code.features.semantic_contract import (
    DescribeCodeSemanticContractRequest,
    DescribeCodeSemanticContractResponse,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
    NormalizeCodeSemanticContractRequest,
    NormalizeCodeSemanticContractResponse,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
    ValidateCodeSemanticContractRequest,
    ValidateCodeSemanticContractResponse,
)
from aware_code_service_dto.code.features.semantic_source_meaning import (
    ResolveCodeSemanticSourceDeltaMeaningRequest,
    ResolveCodeSemanticSourceDeltaMeaningResponse,
    ResolveCodeSemanticSourceMeaningRequest,
    ResolveCodeSemanticSourceMeaningResponse,
)
from aware_code_service_dto.code.features.semantic_workflow_coverage import (
    ResolveCodeSemanticWorkflowCoverageRequest,
    ResolveCodeSemanticWorkflowCoverageResponse,
)
from aware_code_service_dto.code.features.source_ownership import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
)
from aware_code_service_dto.code.features.source_projection import (
    FingerprintCodeSourceProjectionRequest,
    FingerprintCodeSourceProjectionResponse,
    NormalizeCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionResponse,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ResolveCodeSourceProjectionPackageDeltaResponse,
    ValidateCodeSourceProjectionRequest,
    ValidateCodeSourceProjectionResponse,
)

API_PACKAGE_NAME: Final[str] = "code-service-api"
API_FQN_PREFIX: Final[str] = "aware_code_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_code_service_api"


@dataclass(frozen=True, slots=True)
class ServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str
    request_type_ref: str
    response_type_ref: str


class ServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceProtocolExecution(Protocol):
    pass


ServiceProtocolExecutionFactory: TypeAlias = Callable[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]

ServiceProtocolInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], Awaitable[object | None]
]

ServiceProtocolStreamInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], AsyncIterator[object]
]


def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    required_fields = [name for name, field in model_cls.model_fields.items() if field.is_required()]
    if len(required_fields) == 1:
        field_name = required_fields[0]
        if isinstance(payload, dict) and field_name in payload:
            return payload
        return {field_name: payload}
    return payload


@dataclass(frozen=True, slots=True)
class ServiceProtocolEndpointBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ServiceProtocolExecutionFactory | None
    stream_invoke: ServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]
    invoke: ServiceProtocolInvoker


async def invoke_code__generated_materialization_delta__fingerprint(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> FingerprintCodeGeneratedMaterializationDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = FingerprintCodeGeneratedMaterializationDeltaRequest.model_validate(request)
    return await typed_handler.code.generated_materialization_delta.fingerprint(typed_request)


CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.fingerprint"
)
CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF,
        api_name="code",
        capability_name="generated_materialization_delta",
        endpoint_name="fingerprint",
        request_type_ref="aware_code_service_dto.code.FingerprintCodeGeneratedMaterializationDeltaRequest",
        response_type_ref="aware_code_service_dto.code.FingerprintCodeGeneratedMaterializationDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__generated_materialization_delta__fingerprint,
    )
)


async def invoke_code__generated_materialization_delta__normalize(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NormalizeCodeGeneratedMaterializationDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = NormalizeCodeGeneratedMaterializationDeltaRequest.model_validate(request)
    return await typed_handler.code.generated_materialization_delta.normalize(typed_request)


CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.normalize"
)
CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF,
        api_name="code",
        capability_name="generated_materialization_delta",
        endpoint_name="normalize",
        request_type_ref="aware_code_service_dto.code.NormalizeCodeGeneratedMaterializationDeltaRequest",
        response_type_ref="aware_code_service_dto.code.NormalizeCodeGeneratedMaterializationDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__generated_materialization_delta__normalize,
    )
)


async def invoke_code__generated_materialization_delta__resolve_package_delta(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeGeneratedMaterializationPackageDeltaRequest.model_validate(request)
    return await typed_handler.code.generated_materialization_delta.resolve_package_delta(typed_request)


CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.resolve_package_delta"
)
CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
        api_name="code",
        capability_name="generated_materialization_delta",
        endpoint_name="resolve_package_delta",
        request_type_ref="aware_code_service_dto.code.ResolveCodeGeneratedMaterializationPackageDeltaRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeGeneratedMaterializationPackageDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__generated_materialization_delta__resolve_package_delta,
    )
)


async def invoke_code__generated_materialization_delta__validate(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateCodeGeneratedMaterializationDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ValidateCodeGeneratedMaterializationDeltaRequest.model_validate(request)
    return await typed_handler.code.generated_materialization_delta.validate(typed_request)


CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.validate"
)
CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF,
        api_name="code",
        capability_name="generated_materialization_delta",
        endpoint_name="validate",
        request_type_ref="aware_code_service_dto.code.ValidateCodeGeneratedMaterializationDeltaRequest",
        response_type_ref="aware_code_service_dto.code.ValidateCodeGeneratedMaterializationDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__generated_materialization_delta__validate,
    )
)


async def invoke_code__grammar_anchor_binding__resolve_evidence(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeGrammarAnchorBindingEvidenceResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeGrammarAnchorBindingEvidenceRequest.model_validate(request)
    return await typed_handler.code.grammar_anchor_binding.resolve_evidence(typed_request)


CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF: Final[str] = "code.grammar_anchor_binding.resolve_evidence"
CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF,
        api_name="code",
        capability_name="grammar_anchor_binding",
        endpoint_name="resolve_evidence",
        request_type_ref="aware_code_service_dto.code.ResolveCodeGrammarAnchorBindingEvidenceRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeGrammarAnchorBindingEvidenceResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__grammar_anchor_binding__resolve_evidence,
    )
)


async def invoke_code__grammar_anchor_binding__validate(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateCodeGrammarAnchorBindingResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ValidateCodeGrammarAnchorBindingRequest.model_validate(request)
    return await typed_handler.code.grammar_anchor_binding.validate(typed_request)


CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF: Final[str] = "code.grammar_anchor_binding.validate"
CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF,
        api_name="code",
        capability_name="grammar_anchor_binding",
        endpoint_name="validate",
        request_type_ref="aware_code_service_dto.code.ValidateCodeGrammarAnchorBindingRequest",
        response_type_ref="aware_code_service_dto.code.ValidateCodeGrammarAnchorBindingResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__grammar_anchor_binding__validate,
    )
)


async def invoke_code__grammar_anchor_render_delta__resolve_delta(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeGrammarAnchorRenderDeltaRequest.model_validate(request)
    return await typed_handler.code.grammar_anchor_render_delta.resolve_delta(typed_request)


CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF: Final[str] = (
    "code.grammar_anchor_render_delta.resolve_delta"
)
CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF,
        api_name="code",
        capability_name="grammar_anchor_render_delta",
        endpoint_name="resolve_delta",
        request_type_ref="aware_code_service_dto.code.ResolveCodeGrammarAnchorRenderDeltaRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeGrammarAnchorRenderDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__grammar_anchor_render_delta__resolve_delta,
    )
)


async def invoke_code__grammar_profile__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeGrammarProfileResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeGrammarProfileRequest.model_validate(request)
    return await typed_handler.code.grammar_profile.resolve(typed_request)


CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF: Final[str] = "code.grammar_profile.resolve"
CODE__GRAMMAR_PROFILE__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF,
    api_name="code",
    capability_name="grammar_profile",
    endpoint_name="resolve",
    request_type_ref="aware_code_service_dto.code.ResolveCodeGrammarProfileRequest",
    response_type_ref="aware_code_service_dto.code.ResolveCodeGrammarProfileResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__grammar_profile__resolve,
)


async def invoke_code__package_delta__fingerprint(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> FingerprintCodePackageDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = FingerprintCodePackageDeltaRequest.model_validate(request)
    return await typed_handler.code.package_delta.fingerprint(typed_request)


CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF: Final[str] = "code.package_delta.fingerprint"
CODE__PACKAGE_DELTA__FINGERPRINT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF,
        api_name="code",
        capability_name="package_delta",
        endpoint_name="fingerprint",
        request_type_ref="aware_code_service_dto.code.FingerprintCodePackageDeltaRequest",
        response_type_ref="aware_code_service_dto.code.FingerprintCodePackageDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__package_delta__fingerprint,
    )
)


async def invoke_code__package_delta__normalize(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NormalizeCodePackageDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = NormalizeCodePackageDeltaRequest.model_validate(request)
    return await typed_handler.code.package_delta.normalize(typed_request)


CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF: Final[str] = "code.package_delta.normalize"
CODE__PACKAGE_DELTA__NORMALIZE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF,
    api_name="code",
    capability_name="package_delta",
    endpoint_name="normalize",
    request_type_ref="aware_code_service_dto.code.NormalizeCodePackageDeltaRequest",
    response_type_ref="aware_code_service_dto.code.NormalizeCodePackageDeltaResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__package_delta__normalize,
)


async def invoke_code__package_layout__describe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeCodePackageLayoutResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = DescribeCodePackageLayoutRequest.model_validate(request)
    return await typed_handler.code.package_layout.describe(typed_request)


CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF: Final[str] = "code.package_layout.describe"
CODE__PACKAGE_LAYOUT__DESCRIBE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF,
    api_name="code",
    capability_name="package_layout",
    endpoint_name="describe",
    request_type_ref="aware_code_service_dto.code.DescribeCodePackageLayoutRequest",
    response_type_ref="aware_code_service_dto.code.DescribeCodePackageLayoutResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__package_layout__describe,
)


async def invoke_code__package_layout__discover(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DiscoverCodePackageLayoutsResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = DiscoverCodePackageLayoutsRequest.model_validate(request)
    return await typed_handler.code.package_layout.discover(typed_request)


CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF: Final[str] = "code.package_layout.discover"
CODE__PACKAGE_LAYOUT__DISCOVER_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF,
    api_name="code",
    capability_name="package_layout",
    endpoint_name="discover",
    request_type_ref="aware_code_service_dto.code.DiscoverCodePackageLayoutsRequest",
    response_type_ref="aware_code_service_dto.code.DiscoverCodePackageLayoutsResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__package_layout__discover,
)


async def invoke_code__package_layout__validate(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateCodePackageLayoutResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ValidateCodePackageLayoutRequest.model_validate(request)
    return await typed_handler.code.package_layout.validate(typed_request)


CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF: Final[str] = "code.package_layout.validate"
CODE__PACKAGE_LAYOUT__VALIDATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF,
    api_name="code",
    capability_name="package_layout",
    endpoint_name="validate",
    request_type_ref="aware_code_service_dto.code.ValidateCodePackageLayoutRequest",
    response_type_ref="aware_code_service_dto.code.ValidateCodePackageLayoutResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__package_layout__validate,
)


async def invoke_code__section_delta__fingerprint(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> FingerprintCodeSectionDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = FingerprintCodeSectionDeltaRequest.model_validate(request)
    return await typed_handler.code.section_delta.fingerprint(typed_request)


CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF: Final[str] = "code.section_delta.fingerprint"
CODE__SECTION_DELTA__FINGERPRINT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF,
        api_name="code",
        capability_name="section_delta",
        endpoint_name="fingerprint",
        request_type_ref="aware_code_service_dto.code.FingerprintCodeSectionDeltaRequest",
        response_type_ref="aware_code_service_dto.code.FingerprintCodeSectionDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__section_delta__fingerprint,
    )
)


async def invoke_code__section_delta__normalize(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NormalizeCodeSectionDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = NormalizeCodeSectionDeltaRequest.model_validate(request)
    return await typed_handler.code.section_delta.normalize(typed_request)


CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF: Final[str] = "code.section_delta.normalize"
CODE__SECTION_DELTA__NORMALIZE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF,
    api_name="code",
    capability_name="section_delta",
    endpoint_name="normalize",
    request_type_ref="aware_code_service_dto.code.NormalizeCodeSectionDeltaRequest",
    response_type_ref="aware_code_service_dto.code.NormalizeCodeSectionDeltaResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__section_delta__normalize,
)


async def invoke_code__section_delta__resolve_package_delta(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSectionDeltaPackageDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSectionDeltaPackageDeltaRequest.model_validate(request)
    return await typed_handler.code.section_delta.resolve_package_delta(typed_request)


CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = "code.section_delta.resolve_package_delta"
CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
        api_name="code",
        capability_name="section_delta",
        endpoint_name="resolve_package_delta",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSectionDeltaPackageDeltaRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSectionDeltaPackageDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__section_delta__resolve_package_delta,
    )
)


async def invoke_code__section_delta__resolve_render_policy(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSegmentRenderPolicyResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSegmentRenderPolicyRequest.model_validate(request)
    return await typed_handler.code.section_delta.resolve_render_policy(typed_request)


CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF: Final[str] = "code.section_delta.resolve_render_policy"
CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF,
        api_name="code",
        capability_name="section_delta",
        endpoint_name="resolve_render_policy",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSegmentRenderPolicyRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSegmentRenderPolicyResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__section_delta__resolve_render_policy,
    )
)


async def invoke_code__section_delta__validate(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateCodeSectionDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ValidateCodeSectionDeltaRequest.model_validate(request)
    return await typed_handler.code.section_delta.validate(typed_request)


CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF: Final[str] = "code.section_delta.validate"
CODE__SECTION_DELTA__VALIDATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF,
    api_name="code",
    capability_name="section_delta",
    endpoint_name="validate",
    request_type_ref="aware_code_service_dto.code.ValidateCodeSectionDeltaRequest",
    response_type_ref="aware_code_service_dto.code.ValidateCodeSectionDeltaResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_code__section_delta__validate,
)


async def invoke_code__semantic_analysis__preview_package_delta(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = PreviewCodeSemanticAnalysisPackageDeltaRequest.model_validate(request)
    return await typed_handler.code.semantic_analysis.preview_package_delta(typed_request)


CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = "code.semantic_analysis.preview_package_delta"
CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_analysis",
        endpoint_name="preview_package_delta",
        request_type_ref="aware_code_service_dto.code.PreviewCodeSemanticAnalysisPackageDeltaRequest",
        response_type_ref="aware_code_service_dto.code.PreviewCodeSemanticAnalysisPackageDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_analysis__preview_package_delta,
    )
)


async def invoke_code__semantic_contract__describe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeCodeSemanticContractResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = DescribeCodeSemanticContractRequest.model_validate(request)
    return await typed_handler.code.semantic_contract.describe(typed_request)


CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF: Final[str] = "code.semantic_contract.describe"
CODE__SEMANTIC_CONTRACT__DESCRIBE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_contract",
        endpoint_name="describe",
        request_type_ref="aware_code_service_dto.code.DescribeCodeSemanticContractRequest",
        response_type_ref="aware_code_service_dto.code.DescribeCodeSemanticContractResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_contract__describe,
    )
)


async def invoke_code__semantic_contract__find_manifest_resolution(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> FindCodeSemanticManifestResolutionResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = FindCodeSemanticManifestResolutionRequest.model_validate(request)
    return await typed_handler.code.semantic_contract.find_manifest_resolution(typed_request)


CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF: Final[str] = (
    "code.semantic_contract.find_manifest_resolution"
)
CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_contract",
        endpoint_name="find_manifest_resolution",
        request_type_ref="aware_code_service_dto.code.FindCodeSemanticManifestResolutionRequest",
        response_type_ref="aware_code_service_dto.code.FindCodeSemanticManifestResolutionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_contract__find_manifest_resolution,
    )
)


async def invoke_code__semantic_contract__normalize(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NormalizeCodeSemanticContractResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = NormalizeCodeSemanticContractRequest.model_validate(request)
    return await typed_handler.code.semantic_contract.normalize(typed_request)


CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF: Final[str] = "code.semantic_contract.normalize"
CODE__SEMANTIC_CONTRACT__NORMALIZE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_contract",
        endpoint_name="normalize",
        request_type_ref="aware_code_service_dto.code.NormalizeCodeSemanticContractRequest",
        response_type_ref="aware_code_service_dto.code.NormalizeCodeSemanticContractResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_contract__normalize,
    )
)


async def invoke_code__semantic_contract__resolve_semantic_scope(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSemanticScopeResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSemanticScopeRequest.model_validate(request)
    return await typed_handler.code.semantic_contract.resolve_semantic_scope(typed_request)


CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF: Final[str] = (
    "code.semantic_contract.resolve_semantic_scope"
)
CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_contract",
        endpoint_name="resolve_semantic_scope",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSemanticScopeRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSemanticScopeResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_contract__resolve_semantic_scope,
    )
)


async def invoke_code__semantic_contract__validate(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateCodeSemanticContractResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ValidateCodeSemanticContractRequest.model_validate(request)
    return await typed_handler.code.semantic_contract.validate(typed_request)


CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF: Final[str] = "code.semantic_contract.validate"
CODE__SEMANTIC_CONTRACT__VALIDATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_contract",
        endpoint_name="validate",
        request_type_ref="aware_code_service_dto.code.ValidateCodeSemanticContractRequest",
        response_type_ref="aware_code_service_dto.code.ValidateCodeSemanticContractResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_contract__validate,
    )
)


async def invoke_code__semantic_source_meaning__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSemanticSourceMeaningResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSemanticSourceMeaningRequest.model_validate(request)
    return await typed_handler.code.semantic_source_meaning.resolve(typed_request)


CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF: Final[str] = "code.semantic_source_meaning.resolve"
CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_source_meaning",
        endpoint_name="resolve",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSemanticSourceMeaningRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSemanticSourceMeaningResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_source_meaning__resolve,
    )
)


async def invoke_code__semantic_source_meaning__resolve_delta(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSemanticSourceDeltaMeaningResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSemanticSourceDeltaMeaningRequest.model_validate(request)
    return await typed_handler.code.semantic_source_meaning.resolve_delta(typed_request)


CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF: Final[str] = "code.semantic_source_meaning.resolve_delta"
CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_source_meaning",
        endpoint_name="resolve_delta",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSemanticSourceDeltaMeaningRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSemanticSourceDeltaMeaningResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_source_meaning__resolve_delta,
    )
)


async def invoke_code__semantic_workflow_coverage__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSemanticWorkflowCoverageResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSemanticWorkflowCoverageRequest.model_validate(request)
    return await typed_handler.code.semantic_workflow_coverage.resolve(typed_request)


CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF: Final[str] = "code.semantic_workflow_coverage.resolve"
CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF,
        api_name="code",
        capability_name="semantic_workflow_coverage",
        endpoint_name="resolve",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSemanticWorkflowCoverageRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSemanticWorkflowCoverageResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__semantic_workflow_coverage__resolve,
    )
)


async def invoke_code__source_ownership__classify(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ClassifyCodeSourceOwnershipResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ClassifyCodeSourceOwnershipRequest.model_validate(request)
    return await typed_handler.code.source_ownership.classify(typed_request)


CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF: Final[str] = "code.source_ownership.classify"
CODE__SOURCE_OWNERSHIP__CLASSIFY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF,
        api_name="code",
        capability_name="source_ownership",
        endpoint_name="classify",
        request_type_ref="aware_code_service_dto.code.ClassifyCodeSourceOwnershipRequest",
        response_type_ref="aware_code_service_dto.code.ClassifyCodeSourceOwnershipResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__source_ownership__classify,
    )
)


async def invoke_code__source_projection__fingerprint(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> FingerprintCodeSourceProjectionResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = FingerprintCodeSourceProjectionRequest.model_validate(request)
    return await typed_handler.code.source_projection.fingerprint(typed_request)


CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF: Final[str] = "code.source_projection.fingerprint"
CODE__SOURCE_PROJECTION__FINGERPRINT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF,
        api_name="code",
        capability_name="source_projection",
        endpoint_name="fingerprint",
        request_type_ref="aware_code_service_dto.code.FingerprintCodeSourceProjectionRequest",
        response_type_ref="aware_code_service_dto.code.FingerprintCodeSourceProjectionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__source_projection__fingerprint,
    )
)


async def invoke_code__source_projection__normalize(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NormalizeCodeSourceProjectionResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = NormalizeCodeSourceProjectionRequest.model_validate(request)
    return await typed_handler.code.source_projection.normalize(typed_request)


CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF: Final[str] = "code.source_projection.normalize"
CODE__SOURCE_PROJECTION__NORMALIZE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF,
        api_name="code",
        capability_name="source_projection",
        endpoint_name="normalize",
        request_type_ref="aware_code_service_dto.code.NormalizeCodeSourceProjectionRequest",
        response_type_ref="aware_code_service_dto.code.NormalizeCodeSourceProjectionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__source_projection__normalize,
    )
)


async def invoke_code__source_projection__resolve_package_delta(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodeSourceProjectionPackageDeltaResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ResolveCodeSourceProjectionPackageDeltaRequest.model_validate(request)
    return await typed_handler.code.source_projection.resolve_package_delta(typed_request)


CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = "code.source_projection.resolve_package_delta"
CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
        api_name="code",
        capability_name="source_projection",
        endpoint_name="resolve_package_delta",
        request_type_ref="aware_code_service_dto.code.ResolveCodeSourceProjectionPackageDeltaRequest",
        response_type_ref="aware_code_service_dto.code.ResolveCodeSourceProjectionPackageDeltaResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__source_projection__resolve_package_delta,
    )
)


async def invoke_code__source_projection__validate(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateCodeSourceProjectionResponse:
    typed_handler = cast(AwareCodeServiceProtocol, handler)
    typed_request = ValidateCodeSourceProjectionRequest.model_validate(request)
    return await typed_handler.code.source_projection.validate(typed_request)


CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF: Final[str] = "code.source_projection.validate"
CODE__SOURCE_PROJECTION__VALIDATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF,
        api_name="code",
        capability_name="source_projection",
        endpoint_name="validate",
        request_type_ref="aware_code_service_dto.code.ValidateCodeSourceProjectionRequest",
        response_type_ref="aware_code_service_dto.code.ValidateCodeSourceProjectionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_code__source_projection__validate,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF: CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_PROTOCOL_BINDING,
    CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF: CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_PROTOCOL_BINDING,
    CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING,
    CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF: CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_PROTOCOL_BINDING,
    CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF: CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_PROTOCOL_BINDING,
    CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF: CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_PROTOCOL_BINDING,
    CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF: CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_PROTOCOL_BINDING,
    CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF: CODE__GRAMMAR_PROFILE__RESOLVE_PROTOCOL_BINDING,
    CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF: CODE__PACKAGE_DELTA__FINGERPRINT_PROTOCOL_BINDING,
    CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF: CODE__PACKAGE_DELTA__NORMALIZE_PROTOCOL_BINDING,
    CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF: CODE__PACKAGE_LAYOUT__DESCRIBE_PROTOCOL_BINDING,
    CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF: CODE__PACKAGE_LAYOUT__DISCOVER_PROTOCOL_BINDING,
    CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF: CODE__PACKAGE_LAYOUT__VALIDATE_PROTOCOL_BINDING,
    CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF: CODE__SECTION_DELTA__FINGERPRINT_PROTOCOL_BINDING,
    CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF: CODE__SECTION_DELTA__NORMALIZE_PROTOCOL_BINDING,
    CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING,
    CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF: CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_PROTOCOL_BINDING,
    CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF: CODE__SECTION_DELTA__VALIDATE_PROTOCOL_BINDING,
    CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF: CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_PROTOCOL_BINDING,
    CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF: CODE__SEMANTIC_CONTRACT__DESCRIBE_PROTOCOL_BINDING,
    CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF: CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_PROTOCOL_BINDING,
    CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF: CODE__SEMANTIC_CONTRACT__NORMALIZE_PROTOCOL_BINDING,
    CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF: CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_PROTOCOL_BINDING,
    CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF: CODE__SEMANTIC_CONTRACT__VALIDATE_PROTOCOL_BINDING,
    CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF: CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_PROTOCOL_BINDING,
    CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF: CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_PROTOCOL_BINDING,
    CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF: CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_PROTOCOL_BINDING,
    CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF: CODE__SOURCE_OWNERSHIP__CLASSIFY_PROTOCOL_BINDING,
    CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF: CODE__SOURCE_PROJECTION__FINGERPRINT_PROTOCOL_BINDING,
    CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF: CODE__SOURCE_PROJECTION__NORMALIZE_PROTOCOL_BINDING,
    CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING,
    CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF: CODE__SOURCE_PROJECTION__VALIDATE_PROTOCOL_BINDING,
}


class CodeGeneratedMaterializationDeltaCapabilityServiceProtocol(Protocol):

    async def fingerprint(
        self, request: FingerprintCodeGeneratedMaterializationDeltaRequest
    ) -> FingerprintCodeGeneratedMaterializationDeltaResponse: ...

    async def normalize(
        self, request: NormalizeCodeGeneratedMaterializationDeltaRequest
    ) -> NormalizeCodeGeneratedMaterializationDeltaResponse: ...

    async def resolve_package_delta(
        self, request: ResolveCodeGeneratedMaterializationPackageDeltaRequest
    ) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse: ...

    async def validate(
        self, request: ValidateCodeGeneratedMaterializationDeltaRequest
    ) -> ValidateCodeGeneratedMaterializationDeltaResponse: ...


class CodeGrammarAnchorBindingCapabilityServiceProtocol(Protocol):

    async def resolve_evidence(
        self, request: ResolveCodeGrammarAnchorBindingEvidenceRequest
    ) -> ResolveCodeGrammarAnchorBindingEvidenceResponse: ...

    async def validate(
        self, request: ValidateCodeGrammarAnchorBindingRequest
    ) -> ValidateCodeGrammarAnchorBindingResponse: ...


class CodeGrammarAnchorRenderDeltaCapabilityServiceProtocol(Protocol):

    async def resolve_delta(
        self, request: ResolveCodeGrammarAnchorRenderDeltaRequest
    ) -> ResolveCodeGrammarAnchorRenderDeltaResponse: ...


class CodeGrammarProfileCapabilityServiceProtocol(Protocol):

    async def resolve(self, request: ResolveCodeGrammarProfileRequest) -> ResolveCodeGrammarProfileResponse: ...


class CodePackageDeltaCapabilityServiceProtocol(Protocol):

    async def fingerprint(self, request: FingerprintCodePackageDeltaRequest) -> FingerprintCodePackageDeltaResponse: ...

    async def normalize(self, request: NormalizeCodePackageDeltaRequest) -> NormalizeCodePackageDeltaResponse: ...


class CodePackageLayoutCapabilityServiceProtocol(Protocol):

    async def describe(self, request: DescribeCodePackageLayoutRequest) -> DescribeCodePackageLayoutResponse: ...

    async def discover(self, request: DiscoverCodePackageLayoutsRequest) -> DiscoverCodePackageLayoutsResponse: ...

    async def validate(self, request: ValidateCodePackageLayoutRequest) -> ValidateCodePackageLayoutResponse: ...


class CodeSectionDeltaCapabilityServiceProtocol(Protocol):

    async def fingerprint(self, request: FingerprintCodeSectionDeltaRequest) -> FingerprintCodeSectionDeltaResponse: ...

    async def normalize(self, request: NormalizeCodeSectionDeltaRequest) -> NormalizeCodeSectionDeltaResponse: ...

    async def resolve_package_delta(
        self, request: ResolveCodeSectionDeltaPackageDeltaRequest
    ) -> ResolveCodeSectionDeltaPackageDeltaResponse: ...

    async def resolve_render_policy(
        self, request: ResolveCodeSegmentRenderPolicyRequest
    ) -> ResolveCodeSegmentRenderPolicyResponse: ...

    async def validate(self, request: ValidateCodeSectionDeltaRequest) -> ValidateCodeSectionDeltaResponse: ...


class CodeSemanticAnalysisCapabilityServiceProtocol(Protocol):

    async def preview_package_delta(
        self, request: PreviewCodeSemanticAnalysisPackageDeltaRequest
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse: ...


class CodeSemanticContractCapabilityServiceProtocol(Protocol):

    async def describe(self, request: DescribeCodeSemanticContractRequest) -> DescribeCodeSemanticContractResponse: ...

    async def find_manifest_resolution(
        self, request: FindCodeSemanticManifestResolutionRequest
    ) -> FindCodeSemanticManifestResolutionResponse: ...

    async def normalize(
        self, request: NormalizeCodeSemanticContractRequest
    ) -> NormalizeCodeSemanticContractResponse: ...

    async def resolve_semantic_scope(
        self, request: ResolveCodeSemanticScopeRequest
    ) -> ResolveCodeSemanticScopeResponse: ...

    async def validate(self, request: ValidateCodeSemanticContractRequest) -> ValidateCodeSemanticContractResponse: ...


class CodeSemanticSourceMeaningCapabilityServiceProtocol(Protocol):

    async def resolve(
        self, request: ResolveCodeSemanticSourceMeaningRequest
    ) -> ResolveCodeSemanticSourceMeaningResponse: ...

    async def resolve_delta(
        self, request: ResolveCodeSemanticSourceDeltaMeaningRequest
    ) -> ResolveCodeSemanticSourceDeltaMeaningResponse: ...


class CodeSemanticWorkflowCoverageCapabilityServiceProtocol(Protocol):

    async def resolve(
        self, request: ResolveCodeSemanticWorkflowCoverageRequest
    ) -> ResolveCodeSemanticWorkflowCoverageResponse: ...


class CodeSourceOwnershipCapabilityServiceProtocol(Protocol):

    async def classify(self, request: ClassifyCodeSourceOwnershipRequest) -> ClassifyCodeSourceOwnershipResponse: ...


class CodeSourceProjectionCapabilityServiceProtocol(Protocol):

    async def fingerprint(
        self, request: FingerprintCodeSourceProjectionRequest
    ) -> FingerprintCodeSourceProjectionResponse: ...

    async def normalize(
        self, request: NormalizeCodeSourceProjectionRequest
    ) -> NormalizeCodeSourceProjectionResponse: ...

    async def resolve_package_delta(
        self, request: ResolveCodeSourceProjectionPackageDeltaRequest
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse: ...

    async def validate(self, request: ValidateCodeSourceProjectionRequest) -> ValidateCodeSourceProjectionResponse: ...


class CodeApiServiceProtocol(Protocol):
    generated_materialization_delta: CodeGeneratedMaterializationDeltaCapabilityServiceProtocol
    grammar_anchor_binding: CodeGrammarAnchorBindingCapabilityServiceProtocol
    grammar_anchor_render_delta: CodeGrammarAnchorRenderDeltaCapabilityServiceProtocol
    grammar_profile: CodeGrammarProfileCapabilityServiceProtocol
    package_delta: CodePackageDeltaCapabilityServiceProtocol
    package_layout: CodePackageLayoutCapabilityServiceProtocol
    section_delta: CodeSectionDeltaCapabilityServiceProtocol
    semantic_analysis: CodeSemanticAnalysisCapabilityServiceProtocol
    semantic_contract: CodeSemanticContractCapabilityServiceProtocol
    semantic_source_meaning: CodeSemanticSourceMeaningCapabilityServiceProtocol
    semantic_workflow_coverage: CodeSemanticWorkflowCoverageCapabilityServiceProtocol
    source_ownership: CodeSourceOwnershipCapabilityServiceProtocol
    source_projection: CodeSourceProjectionCapabilityServiceProtocol


class AwareCodeServiceProtocol(Protocol):
    code: CodeApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:32554323d35a820edfb2a16244b568bbc8aeb79fb01fdde14afffabc443245ad",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 115,'
    '  "sections": ['
    "    {"
    '      "line_count": 28,'
    '      "rendered_text_digest": "sha256:4e131c06b87a53706cde11cc45a0a65c594e8cf75e960871b0e4c7c668323b91",'
    '      "section_key": "api.service_protocol.module_prelude",'
    '      "section_kind": "service_protocol_module_prelude",'
    '      "section_order": 0'
    "    },"
    "    {"
    '      "line_count": 59,'
    '      "rendered_text_digest": "sha256:4b2f83676760964f04df5a2dfd6a8153e0c286051f2d85dd83b8e2e933b411d7",'
    '      "section_key": "api.service_protocol.runtime_support",'
    '      "section_kind": "service_protocol_runtime_support",'
    '      "section_order": 1'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.generated_materialization_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.generated_materialization_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.generated_materialization_delta.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.generated_materialization_delta.validate",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.grammar_anchor_binding.resolve_evidence",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.grammar_anchor_binding.validate",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.grammar_anchor_render_delta.resolve_delta",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.grammar_profile.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.package_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.package_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.package_layout.describe",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.package_layout.discover",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.package_layout.validate",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.section_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.section_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.section_delta.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.section_delta.resolve_render_policy",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.section_delta.validate",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_analysis.preview_package_delta",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_contract.describe",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_contract.find_manifest_resolution",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_contract.normalize",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_contract.resolve_semantic_scope",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_contract.validate",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_source_meaning.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_source_meaning.resolve_delta",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.semantic_workflow_coverage.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.source_ownership.classify",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.source_projection.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.source_projection.normalize",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.source_projection.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:code.source_projection.validate",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:afdfa6ad1f80c819d4f9eadbb48fb91934ce7ea0173ad4e2b7a2a2f17399d8c7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.generated_materialization_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:cf01e0d006b75d1b2a5ecdd2b30c74eba39077a109c636f088a8e65c4f32c954",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.generated_materialization_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ba884a979d0572607c56a68c8d14d47a7985e5774767af8f0fd09dfdfce7faed",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.generated_materialization_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a7e3c9910458ea25816493b5808a4a81b09ec7cb07a2dac4b6479ed12d876ed9",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.generated_materialization_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ae9404d210199f1914141985cc293a032d45e0f8a25a65f614d1c9217ea4eb04",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.generated_materialization_delta.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:845c9db5a7e821e9e4e5df4e5c554eed4adb54eb96ec1c98557636bc2bad154c",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.generated_materialization_delta.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ae42221a07d7b5eda2388470cc0119a6c9fa2946c4cad0e7ad32c2b0f1662b47",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.generated_materialization_delta.validate",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:187166b0e26f208a838b3bac39a9fbd573d1b138e8cd7d9a2c068bbc92aac45e",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.generated_materialization_delta.validate",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:48255abda4339c5c1cce8280b6ccb999d5c9740238adb3f8389163956bf1baf0",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.grammar_anchor_binding.resolve_evidence",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:022523d628d3eea9e052d328d792db748e0b4aba8bf8c1ab4f67b304c45030c9",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.grammar_anchor_binding.resolve_evidence",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:dd591546cfd13f6ca4aace3f432691bb08004fc07f8ed5245bc00b0751823ba2",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.grammar_anchor_binding.validate",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c88017512409d0b9ef0c515f45a1bc1ccaff96abb837f0c1376c85878cffda99",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.grammar_anchor_binding.validate",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f85811c38d0c6e6613af164159e4b2e0666b83bb9cd01f79c7536a93e1be84c2",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.grammar_anchor_render_delta.resolve_delta",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:931e94110e38f33987ebc6a11b68144ae7e3fef4aeaf62809d0e417787055397",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.grammar_anchor_render_delta.resolve_delta",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:201e7921d50cdde2b982ca9792daaabc11d3ec5a9d93e6cc4e9981be009c72b6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.grammar_profile.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:11b8c14df8760ae2ead69389aa431ab9f070aba07fdc4ef2be6c62fd736e4409",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.grammar_profile.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4c859784f30e50c8d2997b34e482090f7d41565e919f6f5674f5db2e7b96e3a7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.package_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0c02c4f66235f2a38ba306a1dafe855c75eee63a6cc65a5e3819675de1ab2ea8",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.package_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5be3f5c5c8a9e0537ac18a258b066629c24004c3e38611f9c73ea14d3f64dae1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.package_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d7207d170300284e4d813cf908b3ad482ff47f3a267b899d40849b52343518f1",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.package_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2f3b1c508579ccb48565f040a322bf8407b3d0ef29a6b71afe08063cb5226780",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.package_layout.describe",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6ab29445fd520c9917562b0cd584d568ef45bba393996bf6d74fe2c4d7cff00a",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.package_layout.describe",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:789ee45a88636e1efb96af9e74c0c15d549d45cea470a4d868975cc220ad2d5d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.package_layout.discover",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:9ac359ca21d0bbfb4a59a5f795217c760eaa22bd749822271735288402bc7ca1",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.package_layout.discover",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d8c0ee52ea2f7995f51b00eeb627736bb454a63df9509af3dbae5bcfddc687ee",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.package_layout.validate",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d6f831d3c0c01fa52b68b3cc8aa91f06ac1c2e3afd6fc3ba6052c54319a2c733",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.package_layout.validate",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b4dc227f94122911dd66e25c162045745dc3c9483586e5cab853a22ad61bb7cb",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.section_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:279f1979da884ab6bf0c51ea8c767c1f95ccd18f133188e001bbe5b64e28d545",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.section_delta.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 61'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ee8ec4fa2273e646e403ef35e3b66017cac0e933c3a01591141537c9467729dd",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.section_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 62'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:25845593fb8b08ced6d1e88bdd0f0e85f3450b724423b3f29a1c514a6075492a",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.section_delta.normalize",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 63'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b83a075346b6ca7eb694c4321059d2ac82619dd6ca8175187f424dc0bbc20147",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.section_delta.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 64'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:445e1bb99b95f267e6dcd99470ca8273f5a07657f2896616c40d4e5eff688b0b",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.section_delta.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 65'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:13043bc7d23dc9ec9b258a8b852e363aaa6f33aad3f1049f676aec6ca580acee",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.section_delta.resolve_render_policy",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 66'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b2007b68eb1a94f74376be371d18cc58d88839c8841eacfeb6ca192be6187d4f",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.section_delta.resolve_render_policy",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 67'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:453020e123c550083feecebe493e40ee5c9748a6ed09677fa45c8421ce423ee6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.section_delta.validate",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 68'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:3bdf4d4ed765c9524d00901699334d863a3a544a7cf49a4d5186dd8f33892047",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.section_delta.validate",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 69'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9983e7b4dd5cc7ae12c40d948f313c1d4b9ca9f69b35170c9749d044560fc230",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_analysis.preview_package_delta",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 70'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8de2791f4765b06ad9f34dfd4cff95011944c8fb780a45198d06baf092a8217c",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_analysis.preview_package_delta",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 71'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f7b07fa5b77af01fe4b27f14968462f30ef38e7cfda0469d0d91a1643e0dc814",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_contract.describe",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 72'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:ddb34be4f216811c8e140fbb0eba5892d32b1b34910c064edd80bdbaa04249bb",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_contract.describe",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 73'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:3c9c42e1174218aaf4f986e23a493691f9bbf42d41cf32d1b4456a599d8c45c1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_contract.find_manifest_resolution",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 74'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:12d1877a814028697c3619e4030b4a2b3b69a9d0563245d2ebe73ef79b90f6e2",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_contract.find_manifest_resolution",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 75'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:616830348dd1bdc4ce2339ca654b0910821d2fc230268f65f5b89f06293f2818",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_contract.normalize",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 76'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:59e2e30d55c1c0992c0f3815484d5f23606f99508d20cd17ee994217bdebbc77",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_contract.normalize",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 77'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9dc45597b428a98e24c50d941f169fae23c4eee0bd541c9e8e70d2a7259bee33",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_contract.resolve_semantic_scope",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 78'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:63edcaf46767cd349b2deddffa8e9ce714ce858b08c87fdfb677e0363213b3b2",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_contract.resolve_semantic_scope",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 79'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b350bad8f799e4d817f0eeb952817e97c7463426ab6bb3fa7e23a34dc8593da3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_contract.validate",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 80'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:00c63f8b882d4a976353f79cc535f0657a0b44c7d3740c6724f6986d8e40800a",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_contract.validate",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 81'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0cc858be51ce39436b9525112defc509e69181feea6ff535699f7ae9b55bb3b3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_source_meaning.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 82'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0a1f10b5a5cb4b8ba36053ba7f93134ea08858a514985d535a0f62a96b3b6d14",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_source_meaning.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 83'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:8bf104745b2503e60383a40bd3dcd46ae28033ea7c0204c98007baccb40490fe",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_source_meaning.resolve_delta",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 84'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:98fe05171a0dde488fc8d7301a75a3bad7d01286fade08c1435d739b1b138458",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_source_meaning.resolve_delta",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 85'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:08bc76c8c7b1ac1a7713ae672fe3ae3220cef418fb3f448165955b42d0655e50",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.semantic_workflow_coverage.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 86'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a142ba3ffa95522ac3d79e7d8e0bb2779516a1c10470807d1130fc8bf450d6f4",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.semantic_workflow_coverage.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 87'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:beaaf6456f9c9241409428b7fe0b8763a7bdb977dce67efbf868227010de321f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.source_ownership.classify",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 88'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:27607d2953f3d0f752d73820cfb1e83ba2a5df01893be342cbd5d0086cdc28d8",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.source_ownership.classify",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 89'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:feb5110b95f48c30f75ac76c06879ebdb63dd8c40d7e9acd16e723ddedef963e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.source_projection.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 90'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:36e89af774599aa1f0ff5d1317b4f1edd6757f95f0dfc00e2a4cf59b35c6967b",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.source_projection.fingerprint",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 91'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f5fbea48b547229516dae2e2a2f163966eb883f555677213e3529575e40600c9",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.source_projection.normalize",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 92'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:477df69257d0ba3933f68f3cb61dc10f45530b650440ea4ed450c35dc6d847dc",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.source_projection.normalize",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 93'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:285385970e3035117b932470ef974dd716b611c1ac122031eba39740491a986c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.source_projection.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 94'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:db08c64be77c9ef972976e305c8c959b6f3d710ff6918b6d08f8798a961fadf8",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.source_projection.resolve_package_delta",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 95'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:314415d6d9f24aecb024cc29401abcf586d33f75cbf16a999ad3e3a27e6ff8f0",'
    '      "section_key": "api.service_protocol.endpoint_invoker:code.source_projection.validate",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 96'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:dbeace35587740d11c53599c7834519f2f8a2c5f8fb077f9e683f905f992bf2d",'
    '      "section_key": "api.service_protocol.endpoint_binding:code.source_projection.validate",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 97'
    "    },"
    "    {"
    '      "line_count": 35,'
    '      "rendered_text_digest": "sha256:241fea136af9ec70a5da244581445a882e115d4c7c53c0b6679953723f7c8899",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 98'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:fd1f1881061a9a37e460998696f93dabefedcbbfab2415d9aeb8006d3858fab1",'
    '      "section_key": "api.service_protocol.capability_protocol:code.generated_materialization_delta",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 99'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:68a9b39c23fc826a4315aaadddc2054257742902599c8c0210d079be1014955f",'
    '      "section_key": "api.service_protocol.capability_protocol:code.grammar_anchor_binding",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 100'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:7c4bc7687f37f09f13fa711163a24bf9f90c4a7a76083f1e9e9733adc213ea44",'
    '      "section_key": "api.service_protocol.capability_protocol:code.grammar_anchor_render_delta",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 101'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:865df8647514b2d13da8cff778b9235b43f6c7ef8d4526dcbfa28277326ba38e",'
    '      "section_key": "api.service_protocol.capability_protocol:code.grammar_profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 102'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:a63a797d9166b1c6e008d67dd734037559b1f36b3eae02471f40735a4c799998",'
    '      "section_key": "api.service_protocol.capability_protocol:code.package_delta",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 103'
    "    },"
    "    {"
    '      "line_count": 8,'
    '      "rendered_text_digest": "sha256:ce876bc7d5419649e38e8252d79b31561da10f9b2315e302d394726a1559c669",'
    '      "section_key": "api.service_protocol.capability_protocol:code.package_layout",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 104'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:e3283b05555bf34e8b8c4e345efef1e126ae579475036ea9fd7511455f6aca75",'
    '      "section_key": "api.service_protocol.capability_protocol:code.section_delta",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 105'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:75962bff1c96d021a472673c54dda4cc6a508e3794300a48ca5c967641452a85",'
    '      "section_key": "api.service_protocol.capability_protocol:code.semantic_analysis",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 106'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:ae6ef242929e6452fd137ce389c68e0bce660fca0ee565648e9c2229f5a65109",'
    '      "section_key": "api.service_protocol.capability_protocol:code.semantic_contract",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 107'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:e70797a400066c136053c67c0134a2bb59133858af794d0e251df62016c0abd1",'
    '      "section_key": "api.service_protocol.capability_protocol:code.semantic_source_meaning",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 108'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1659fbbe2c0462c99b9b98cb8c1e47d95c2df180bc23164919602b564c74bdc6",'
    '      "section_key": "api.service_protocol.capability_protocol:code.semantic_workflow_coverage",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 109'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:4bf4fed7f405a0b3b0fc96fd76237a506f70899484b49399af0fd4d6fb8622d6",'
    '      "section_key": "api.service_protocol.capability_protocol:code.source_ownership",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 110'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:d84960d04ca50120448082d487a3c22838d32d700cbbfd4dcd2e3ed0dded9c81",'
    '      "section_key": "api.service_protocol.capability_protocol:code.source_projection",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 111'
    "    },"
    "    {"
    '      "line_count": 15,'
    '      "rendered_text_digest": "sha256:7f63a25382ffa1779b10aba392e2d84f838fa099068e0f83d7f176f5d8fcc344",'
    '      "section_key": "api.service_protocol.api_protocol:code",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 112'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:1904c4533576308caea3b57cc4306b03718e2f7e7e272a385fceb60d9e920207",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 113'
    "    },"
    "    {"
    '      "line_count": 125,'
    '      "rendered_text_digest": "sha256:f5c9a39bc8938d54f3c21889f9d71ed432afd2318ef67252f51f58762d5c0771",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 114'
    "    }"
    "  ],"
    '  "target_relpath": "protocols.py",'
    '  "text_digest_algorithm": "sha256"'
    "}"
)

__all__ = [
    "API_FQN_PREFIX",
    "API_PACKAGE_NAME",
    "ENDPOINT_BINDINGS",
    "PUBLIC_PACKAGE_IMPORT_ROOT",
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON",
    "ServiceProtocolExecutionBackend",
    "ServiceProtocolExecutionFactory",
    "ServiceProtocolEndpointBinding",
    "ServiceProtocolFulfillmentBinding",
    "ServiceProtocolInvoker",
    "ServiceProtocolStreamInvoker",
    "AwareCodeServiceProtocol",
    "CodeApiServiceProtocol",
    "CodeGeneratedMaterializationDeltaCapabilityServiceProtocol",
    "CodeGrammarAnchorBindingCapabilityServiceProtocol",
    "CodeGrammarAnchorRenderDeltaCapabilityServiceProtocol",
    "CodeGrammarProfileCapabilityServiceProtocol",
    "CodePackageDeltaCapabilityServiceProtocol",
    "CodePackageLayoutCapabilityServiceProtocol",
    "CodeSectionDeltaCapabilityServiceProtocol",
    "CodeSemanticAnalysisCapabilityServiceProtocol",
    "CodeSemanticContractCapabilityServiceProtocol",
    "CodeSemanticSourceMeaningCapabilityServiceProtocol",
    "CodeSemanticWorkflowCoverageCapabilityServiceProtocol",
    "CodeSourceOwnershipCapabilityServiceProtocol",
    "CodeSourceProjectionCapabilityServiceProtocol",
    "CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_PROTOCOL_BINDING",
    "invoke_code__generated_materialization_delta__fingerprint",
    "CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_PROTOCOL_BINDING",
    "invoke_code__generated_materialization_delta__normalize",
    "CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING",
    "invoke_code__generated_materialization_delta__resolve_package_delta",
    "CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_PROTOCOL_BINDING",
    "invoke_code__generated_materialization_delta__validate",
    "CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF",
    "CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_PROTOCOL_BINDING",
    "invoke_code__grammar_anchor_binding__resolve_evidence",
    "CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF",
    "CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_PROTOCOL_BINDING",
    "invoke_code__grammar_anchor_binding__validate",
    "CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF",
    "CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_PROTOCOL_BINDING",
    "invoke_code__grammar_anchor_render_delta__resolve_delta",
    "CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF",
    "CODE__GRAMMAR_PROFILE__RESOLVE_PROTOCOL_BINDING",
    "invoke_code__grammar_profile__resolve",
    "CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF",
    "CODE__PACKAGE_DELTA__FINGERPRINT_PROTOCOL_BINDING",
    "invoke_code__package_delta__fingerprint",
    "CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF",
    "CODE__PACKAGE_DELTA__NORMALIZE_PROTOCOL_BINDING",
    "invoke_code__package_delta__normalize",
    "CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF",
    "CODE__PACKAGE_LAYOUT__DESCRIBE_PROTOCOL_BINDING",
    "invoke_code__package_layout__describe",
    "CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF",
    "CODE__PACKAGE_LAYOUT__DISCOVER_PROTOCOL_BINDING",
    "invoke_code__package_layout__discover",
    "CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF",
    "CODE__PACKAGE_LAYOUT__VALIDATE_PROTOCOL_BINDING",
    "invoke_code__package_layout__validate",
    "CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF",
    "CODE__SECTION_DELTA__FINGERPRINT_PROTOCOL_BINDING",
    "invoke_code__section_delta__fingerprint",
    "CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF",
    "CODE__SECTION_DELTA__NORMALIZE_PROTOCOL_BINDING",
    "invoke_code__section_delta__normalize",
    "CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING",
    "invoke_code__section_delta__resolve_package_delta",
    "CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF",
    "CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_PROTOCOL_BINDING",
    "invoke_code__section_delta__resolve_render_policy",
    "CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF",
    "CODE__SECTION_DELTA__VALIDATE_PROTOCOL_BINDING",
    "invoke_code__section_delta__validate",
    "CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_PROTOCOL_BINDING",
    "invoke_code__semantic_analysis__preview_package_delta",
    "CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__DESCRIBE_PROTOCOL_BINDING",
    "invoke_code__semantic_contract__describe",
    "CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_PROTOCOL_BINDING",
    "invoke_code__semantic_contract__find_manifest_resolution",
    "CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__NORMALIZE_PROTOCOL_BINDING",
    "invoke_code__semantic_contract__normalize",
    "CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_PROTOCOL_BINDING",
    "invoke_code__semantic_contract__resolve_semantic_scope",
    "CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__VALIDATE_PROTOCOL_BINDING",
    "invoke_code__semantic_contract__validate",
    "CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF",
    "CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_PROTOCOL_BINDING",
    "invoke_code__semantic_source_meaning__resolve",
    "CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF",
    "CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_PROTOCOL_BINDING",
    "invoke_code__semantic_source_meaning__resolve_delta",
    "CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF",
    "CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_PROTOCOL_BINDING",
    "invoke_code__semantic_workflow_coverage__resolve",
    "CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF",
    "CODE__SOURCE_OWNERSHIP__CLASSIFY_PROTOCOL_BINDING",
    "invoke_code__source_ownership__classify",
    "CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__FINGERPRINT_PROTOCOL_BINDING",
    "invoke_code__source_projection__fingerprint",
    "CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__NORMALIZE_PROTOCOL_BINDING",
    "invoke_code__source_projection__normalize",
    "CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_PROTOCOL_BINDING",
    "invoke_code__source_projection__resolve_package_delta",
    "CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__VALIDATE_PROTOCOL_BINDING",
    "invoke_code__source_projection__validate",
]
