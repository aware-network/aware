from __future__ import annotations

from types import SimpleNamespace

from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticWorkflowDescriptor,
    ModuleSemanticWorkflowInstructionDescriptor,
)
from aware_meta.semantic_workflow_closure import (
    META_FUNCTION_IMPL_COVERAGE_PROOF_REF,
    META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED,
    META_SEMANTIC_WORKFLOW_CLOSURE_READY,
    MetaSemanticWorkflowClosureCatalog,
    resolve_meta_semantic_workflow_closure,
)
from aware_service_runtime.semantic_contract import AWARE_SERVICE_SEMANTIC_CONTRACT


API_ONTOLOGY_FEATURE_REFS = (
    "aware_api.Api",
    "aware_api.ApiCapability",
    "aware_api.ApiCapabilityEndpoint",
)

SERVICE_ONTOLOGY_FEATURE_REFS = (
    "aware_service.ServiceConfig",
    "aware_service.ServiceOperationConfig",
    "aware_service.ServiceOperationConfigApiEndpoint",
    "aware_api.ApiCapabilityEndpoint",
)

API_GRAPH_BINDING_REFS = (
    "aware_api.api_def",
    "aware_api.api_capability_def",
    "aware_api.api_capability_endpoint_def",
)

SERVICE_GRAPH_BINDING_REFS = (
    "aware_service.service_def",
    "aware_service.service_operation_def",
    "aware_service.service_operation_endpoint_def",
)

PROJECTION_REFS = (
    "Api",
    "ApiPackage",
    "CodePackage",
    "CodePackageConfig",
    "ServicePackage",
)

PROOF_REFS = (
    "api_service_protocol.hash",
    "workspace.semantic_materialization.receipt",
    "meta.function_call.proof",
)

DIAGNOSTIC_REFS = (
    "code.grammar_profile.resolve",
    "meta.semantic_diagnostics",
)


def _complete_catalog() -> MetaSemanticWorkflowClosureCatalog:
    return MetaSemanticWorkflowClosureCatalog(
        ontology_feature_refs=(
            *API_ONTOLOGY_FEATURE_REFS,
            *SERVICE_ONTOLOGY_FEATURE_REFS,
        ),
        graph_binding_refs=(
            *API_GRAPH_BINDING_REFS,
            *SERVICE_GRAPH_BINDING_REFS,
        ),
        typed_operation_feature_refs=(
            *API_ONTOLOGY_FEATURE_REFS,
            *SERVICE_ONTOLOGY_FEATURE_REFS,
        ),
        native_function_feature_refs=SERVICE_ONTOLOGY_FEATURE_REFS,
        projection_refs=PROJECTION_REFS,
        proof_refs=PROOF_REFS,
        diagnostic_refs=DIAGNOSTIC_REFS,
    )


def test_meta_workflow_closure_marks_api_service_contracts_ready() -> None:
    result = resolve_meta_semantic_workflow_closure(
        semantic_contracts=(
            AWARE_API_SEMANTIC_CONTRACT,
            AWARE_SERVICE_SEMANTIC_CONTRACT,
        ),
        catalog=_complete_catalog(),
        provider_keys=("aware_api", "aware_service"),
    )

    assert result.ready is True
    assert result.status == META_SEMANTIC_WORKFLOW_CLOSURE_READY
    assert result.provider_count == 2
    assert result.workflow_count == 2
    assert result.ready_workflow_count == 2
    assert result.blocked_workflow_count == 0
    assert result.diagnostics == ()

    entries = {entry.workflow_key: entry for entry in result.entries}
    api_entry = entries["external-api-service.api"]
    service_entry = entries["external-api-service.service"]
    assert api_entry.required_projection_refs == (
        "Api",
        "ApiPackage",
        "CodePackage",
    )
    assert service_entry.required_projection_refs == (
        "ServicePackage",
        "ApiPackage",
        "CodePackage",
        "CodePackageConfig",
    )
    assert "meta.function_call.proof" in service_entry.expected_proof_refs
    assert service_entry.native_function_feature_refs == SERVICE_ONTOLOGY_FEATURE_REFS


def test_meta_workflow_closure_blocks_missing_api_closure_refs() -> None:
    result = resolve_meta_semantic_workflow_closure(
        semantic_contracts=(AWARE_API_SEMANTIC_CONTRACT,),
        catalog=MetaSemanticWorkflowClosureCatalog(
            ontology_feature_refs=("aware_api.Api",),
            graph_binding_refs=("aware_api.api_def",),
            typed_operation_feature_refs=("aware_api.Api",),
            projection_refs=("Api",),
            proof_refs=("api_service_protocol.hash",),
            diagnostic_refs=("meta.semantic_diagnostics",),
        ),
        provider_keys=("aware_api",),
    )

    assert result.ready is False
    assert result.status == META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED
    assert result.workflow_count == 1
    entry = result.entries[0]
    assert entry.ready is False
    assert entry.status == META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED

    codes = {diagnostic.code for diagnostic in result.diagnostics}
    assert codes >= {
        "aware_meta.workflow_closure.ontology_feature_ref_missing",
        "aware_meta.workflow_closure.graph_binding_ref_missing",
        "aware_meta.workflow_closure.typed_operation_missing",
        "aware_meta.workflow_closure.projection_ref_missing",
        "aware_meta.workflow_closure.proof_ref_missing",
        "aware_meta.workflow_closure.diagnostic_ref_missing",
    }
    assert "ontology_feature:aware_api.ApiCapabilityEndpoint" in entry.blocker_refs
    assert "projection:ApiPackage" in entry.blocker_refs


def test_meta_workflow_closure_blocks_missing_service_native_function_refs() -> None:
    complete = _complete_catalog()
    catalog = MetaSemanticWorkflowClosureCatalog(
        ontology_feature_refs=complete.ontology_feature_refs,
        graph_binding_refs=complete.graph_binding_refs,
        typed_operation_feature_refs=complete.typed_operation_feature_refs,
        native_function_feature_refs=(),
        projection_refs=complete.projection_refs,
        proof_refs=complete.proof_refs,
        diagnostic_refs=complete.diagnostic_refs,
    )

    result = resolve_meta_semantic_workflow_closure(
        semantic_contracts=(AWARE_SERVICE_SEMANTIC_CONTRACT,),
        catalog=catalog,
        provider_keys=("aware_service",),
    )

    assert result.ready is False
    assert result.status == META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED
    codes = {diagnostic.code for diagnostic in result.diagnostics}
    assert codes == {"aware_meta.workflow_closure.native_function_missing"}
    assert (
        "native_function_feature:aware_service.ServiceOperationConfigApiEndpoint"
        in result.entries[0].blocker_refs
    )


def test_meta_workflow_closure_accepts_native_function_impl_coverage() -> None:
    result = resolve_meta_semantic_workflow_closure(
        semantic_contracts=(_function_impl_coverage_contract(),),
        catalog=MetaSemanticWorkflowClosureCatalog(
            ontology_feature_refs=("aware_demo.Widget",),
            typed_operation_feature_refs=("aware_demo.Widget",),
            native_function_feature_refs=("aware_demo.Widget",),
            proof_refs=(META_FUNCTION_IMPL_COVERAGE_PROOF_REF,),
        ),
        provider_keys=("aware_demo",),
    )

    assert result.ready is True
    assert result.status == META_SEMANTIC_WORKFLOW_CLOSURE_READY
    entry = result.entries[0]
    assert entry.native_function_feature_refs == ("aware_demo.Widget",)
    assert entry.runtime_handler_delegation_feature_refs == ()
    assert entry.function_impl_coverage_feature_refs == ("aware_demo.Widget",)


def test_meta_workflow_closure_accepts_runtime_handler_delegation_coverage() -> None:
    result = resolve_meta_semantic_workflow_closure(
        semantic_contracts=(_function_impl_coverage_contract(),),
        catalog=MetaSemanticWorkflowClosureCatalog(
            ontology_feature_refs=("aware_demo.Widget",),
            typed_operation_feature_refs=("aware_demo.Widget",),
            runtime_handler_delegation_feature_refs=("aware_demo.Widget",),
            proof_refs=(META_FUNCTION_IMPL_COVERAGE_PROOF_REF,),
        ),
        provider_keys=("aware_demo",),
    )

    assert result.ready is True
    assert result.status == META_SEMANTIC_WORKFLOW_CLOSURE_READY
    entry = result.entries[0]
    assert entry.native_function_feature_refs == ()
    assert entry.runtime_handler_delegation_feature_refs == ("aware_demo.Widget",)
    assert entry.function_impl_coverage_feature_refs == ("aware_demo.Widget",)


def test_meta_workflow_closure_blocks_missing_function_impl_coverage() -> None:
    result = resolve_meta_semantic_workflow_closure(
        semantic_contracts=(_function_impl_coverage_contract(),),
        catalog=MetaSemanticWorkflowClosureCatalog(
            ontology_feature_refs=("aware_demo.Widget",),
            typed_operation_feature_refs=("aware_demo.Widget",),
            proof_refs=(META_FUNCTION_IMPL_COVERAGE_PROOF_REF,),
        ),
        provider_keys=("aware_demo",),
    )

    assert result.ready is False
    assert result.status == META_SEMANTIC_WORKFLOW_CLOSURE_BLOCKED
    codes = {diagnostic.code for diagnostic in result.diagnostics}
    assert codes == {"aware_meta.workflow_closure.function_impl_coverage_missing"}
    assert (
        "function_impl_coverage_feature:aware_demo.Widget"
        in result.entries[0].blocker_refs
    )


def test_meta_workflow_closure_catalog_derives_ocg_ontology_feature_refs() -> None:
    graph = SimpleNamespace(
        fqn_prefix="aware_api",
        object_config_graph_nodes=(
            SimpleNamespace(
                class_config=SimpleNamespace(
                    name="ApiCapabilityEndpoint",
                    class_fqn=(
                        "aware_api_ontology.api.api_capability_endpoint."
                        "ApiCapabilityEndpoint"
                    ),
                )
            ),
        ),
    )

    catalog = MetaSemanticWorkflowClosureCatalog.from_object_config_graphs(
        object_config_graphs=(graph,)
    )

    assert "aware_api.ApiCapabilityEndpoint" in catalog.ontology_feature_refs
    assert (
        "aware_api_ontology.api.api_capability_endpoint.ApiCapabilityEndpoint"
        in catalog.ontology_feature_refs
    )


def _function_impl_coverage_contract() -> ModuleSemanticContract:
    return ModuleSemanticContract(
        provider_key="aware_demo",
        semantic_workflows=(
            ModuleSemanticWorkflowDescriptor(
                workflow_key="demo.ontology",
                semantic_owner="aware_demo.provider",
                stage_keys=("semantic.demo.verify_runtime_coverage",),
                instructions=(
                    ModuleSemanticWorkflowInstructionDescriptor(
                        instruction_key="demo.coverage",
                        title="Verify coverage",
                        body="Verify native or runtime handler coverage.",
                    ),
                ),
                ontology_feature_refs=("aware_demo.Widget",),
                expected_proof_refs=(META_FUNCTION_IMPL_COVERAGE_PROOF_REF,),
            ),
        ),
    )
