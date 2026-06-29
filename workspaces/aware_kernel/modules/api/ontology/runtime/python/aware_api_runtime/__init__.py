from __future__ import annotations

from importlib import import_module
from typing import cast

_EXPORTS: dict[str, tuple[str, str]] = {
    "load_api_ownership_from_sources": (
        "aware_api_runtime.source",
        "load_api_ownership_from_sources",
    ),
    "APICompileResult": ("aware_api_runtime.compile", "APICompileResult"),
    "compile_api_workspace": ("aware_api_runtime.compile", "compile_api_workspace"),
    "APICompilePlan": ("aware_api_runtime.ir", "APICompilePlan"),
    "APICompilePlanArtifact": ("aware_api_runtime.ir", "APICompilePlanArtifact"),
    "build_api_compile_plan": ("aware_api_runtime.ir", "build_api_compile_plan"),
    "emit_api_compile_plan_artifact": (
        "aware_api_runtime.ir",
        "emit_api_compile_plan_artifact",
    ),
    "APIOntologyApiOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyApiOperation",
    ),
    "APIOntologyCapabilityOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyCapabilityOperation",
    ),
    "APIOntologyCapabilityEndpointOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyCapabilityEndpointOperation",
    ),
    "APIOntologyCapabilityEndpointFunctionOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyCapabilityEndpointFunctionOperation",
    ),
    "APIOntologyGraphOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyGraphOperation",
    ),
    "APIOntologyGraphFunctionOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyGraphFunctionOperation",
    ),
    "APIOntologyGraphProjectionOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyGraphProjectionOperation",
    ),
    "APIOntologyGraphProjectionContractOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyGraphProjectionContractOperation",
    ),
    "APIOntologyGraphCapabilityOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyGraphCapabilityOperation",
    ),
    "APIOntologyGraphCapabilityFunctionOperation": (
        "aware_api_runtime.ontology_graph.ontology",
        "APIOntologyGraphCapabilityFunctionOperation",
    ),
    "APIOntologyPlan": ("aware_api_runtime.ontology_graph.ontology", "APIOntologyPlan"),
    "decode_api_ontology_plan_payload": (
        "aware_api_runtime.ontology_graph.ontology",
        "decode_api_ontology_plan_payload",
    ),
    "load_api_compile_plan_payloads": (
        "aware_api_runtime.compile_materialization.service",
        "load_api_compile_plan_payloads",
    ),
    "materialize_api_compile_plan_ontology": (
        "aware_api_runtime.compile_materialization.service",
        "materialize_api_compile_plan_ontology",
    ),
    "ApiCallMaterializationResult": (
        "aware_api_runtime.invocation.materialization",
        "ApiCallMaterializationResult",
    ),
    "ApiCallOutcomeMaterializationResult": (
        "aware_api_runtime.invocation.materialization",
        "ApiCallOutcomeMaterializationResult",
    ),
    "materialize_api_call": (
        "aware_api_runtime.invocation.materialization",
        "materialize_api_call",
    ),
    "materialize_api_call_outcome": (
        "aware_api_runtime.invocation.materialization",
        "materialize_api_call_outcome",
    ),
    "APICapabilityEndpointOwnership": (
        "aware_api_runtime.models",
        "APICapabilityEndpointOwnership",
    ),
    "APICapabilityEndpointFunctionOwnership": (
        "aware_api_runtime.models",
        "APICapabilityEndpointFunctionOwnership",
    ),
    "APICapabilityOwnership": ("aware_api_runtime.models", "APICapabilityOwnership"),
    "APIGraphCapabilityFunctionOwnership": (
        "aware_api_runtime.models",
        "APIGraphCapabilityFunctionOwnership",
    ),
    "APIGraphCapabilityOwnership": (
        "aware_api_runtime.models",
        "APIGraphCapabilityOwnership",
    ),
    "APIGraphOwnership": ("aware_api_runtime.models", "APIGraphOwnership"),
    "APIGraphProjectionContractOwnership": (
        "aware_api_runtime.models",
        "APIGraphProjectionContractOwnership",
    ),
    "APIGraphProjectionOwnership": (
        "aware_api_runtime.models",
        "APIGraphProjectionOwnership",
    ),
    "APIOwnership": ("aware_api_runtime.models", "APIOwnership"),
    "ProjectionOwnedClassTruth": (
        "aware_api_runtime.models",
        "ProjectionOwnedClassTruth",
    ),
    "ApiInvocationIR": ("aware_api_runtime.invocation", "ApiInvocationIR"),
    "ApiInvocationDispatchResult": (
        "aware_api_runtime.invocation",
        "ApiInvocationDispatchResult",
    ),
    "ApiInvocationManifestEndpointBinding": (
        "aware_api_runtime.invocation",
        "ApiInvocationManifestEndpointBinding",
    ),
    "ApiInvocationRuntimeProtocol": (
        "aware_api_runtime.invocation",
        "ApiInvocationRuntimeProtocol",
    ),
    "MaterializedApiCallBinding": (
        "aware_api_runtime.invocation",
        "MaterializedApiCallBinding",
    ),
    "ResolvedApiInvocationEnvelope": (
        "aware_api_runtime.invocation",
        "ResolvedApiInvocationEnvelope",
    ),
    "build_api_invocation_resolution_index": (
        "aware_api_runtime.invocation",
        "build_api_invocation_resolution_index",
    ),
    "build_resolved_api_invocation_envelope": (
        "aware_api_runtime.invocation",
        "build_resolved_api_invocation_envelope",
    ),
    "resolve_api_invocation_ir": (
        "aware_api_runtime.invocation",
        "resolve_api_invocation_ir",
    ),
    "resolve_api_invocation_ir_from_manifest": (
        "aware_api_runtime.invocation",
        "resolve_api_invocation_ir_from_manifest",
    ),
    "resolve_api_invocation_manifest_endpoint": (
        "aware_api_runtime.invocation",
        "resolve_api_invocation_manifest_endpoint",
    ),
    "resolve_api_invocation_request_class_config_id": (
        "aware_api_runtime.invocation",
        "resolve_api_invocation_request_class_config_id",
    ),
    "dispatch_api_invocation": (
        "aware_api_runtime.invocation",
        "dispatch_api_invocation",
    ),
    "dispatch_api_invocation_from_manifest": (
        "aware_api_runtime.invocation",
        "dispatch_api_invocation_from_manifest",
    ),
    "ApiRuntimePackageRef": (
        "aware_api_runtime.package_ref_resolution",
        "ApiRuntimePackageRef",
    ),
    "ResolvedApiRuntimePackageRef": (
        "aware_api_runtime.package_ref_resolution",
        "ResolvedApiRuntimePackageRef",
    ),
    "build_api_invocation_manifest_from_api_package": (
        "aware_api_runtime.package_ref_resolution",
        "build_api_invocation_manifest_from_api_package",
    ),
    "build_api_runtime_package_binding_from_objects": (
        "aware_api_runtime.package_ref_resolution",
        "build_api_runtime_package_binding_from_objects",
    ),
    "resolve_api_runtime_package_ref": (
        "aware_api_runtime.package_ref_resolution",
        "resolve_api_runtime_package_ref",
    ),
    "validate_api_runtime_package_ref": (
        "aware_api_runtime.package_ref_resolution",
        "validate_api_runtime_package_ref",
    ),
    "ApiServiceProtocolEndpointBinding": (
        "aware_api_runtime.service_protocol",
        "ApiServiceProtocolEndpointBinding",
    ),
    "ApiServiceDispatchPlan": (
        "aware_api_runtime.service_protocol",
        "ApiServiceDispatchPlan",
    ),
    "DecodedApiServiceProtocolRequest": (
        "aware_api_runtime.service_protocol",
        "DecodedApiServiceProtocolRequest",
    ),
    "build_api_service_dispatch_plan": (
        "aware_api_runtime.service_protocol",
        "build_api_service_dispatch_plan",
    ),
    "LoadedApiServiceProtocolPackage": (
        "aware_api_runtime.service_protocol",
        "LoadedApiServiceProtocolPackage",
    ),
    "RematerializedApiCall": (
        "aware_api_runtime.service_protocol",
        "RematerializedApiCall",
    ),
    "decode_committed_api_call_request": (
        "aware_api_runtime.service_protocol",
        "decode_committed_api_call_request",
    ),
    "decode_inline_value_instance_to_mapping_strict": (
        "aware_api_runtime.service_protocol",
        "decode_inline_value_instance_to_mapping_strict",
    ),
    "load_api_service_protocol_package": (
        "aware_api_runtime.service_protocol",
        "load_api_service_protocol_package",
    ),
    "rematerialize_committed_api_call": (
        "aware_api_runtime.service_protocol",
        "rematerialize_committed_api_call",
    ),
    "APIWorkspace": ("aware_api_runtime.workspace", "APIWorkspace"),
    "APIWorkspaceSnapshot": (
        "aware_api_runtime.workspace",
        "APIWorkspaceSnapshot",
    ),
    "ensure_api_dependency_runtime_artifacts": (
        "aware_api_runtime.dependencies.runtime_resolution",
        "ensure_api_dependency_runtime_artifacts",
    ),
    "resolve_api_runtime_semantic_artifacts": (
        "aware_api_runtime.dependencies.runtime_resolution",
        "resolve_api_runtime_semantic_artifacts",
    ),
    "load_api_dependency_class_config_ids": (
        "aware_api_runtime.dependencies.runtime_resolution",
        "load_api_dependency_class_config_ids",
    ),
    "resolve_api_workspace_runtime_manifest": (
        "aware_api_runtime.dependencies.runtime_resolution",
        "resolve_api_workspace_runtime_manifest",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = export
    module = import_module(module_name)
    value = cast(object, getattr(module, attr_name))
    globals()[name] = value
    return value
