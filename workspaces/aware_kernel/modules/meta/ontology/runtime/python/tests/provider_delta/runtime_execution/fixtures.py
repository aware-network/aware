from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from aware_code.types import JsonArray
from aware_meta.runtime.invocation_engine import (
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)

from ..fixtures import provider_delta_uuid


@dataclass(frozen=True)
class ProviderDeltaRuntimeExecutionContext:
    branch_id: UUID
    actor_id: UUID
    baseline_domain_commit_id: UUID
    baseline_oig_commit_id: UUID
    baseline_root_domain_commit_id: UUID
    baseline_root_oig_commit_id: UUID
    baseline_root_oig_id: UUID
    baseline_root_oigi_id: UUID
    package_projection_hash: str
    root_projection_hash: str
    runtime: RecordingProviderDeltaOntologyRuntime
    graph_runtime_context: SimpleNamespace
    request: SimpleNamespace
    baseline_dirty_preflight: dict[str, object]


class RecordingProviderDeltaOntologyRuntime:
    def __init__(self) -> None:
        self.requests: list[MetaGraphInvokeFunctionInput] = []
        self.receipts: list[MetaGraphCommitReceipt] = []

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        self.requests.append(request)
        invocation_index = len(self.requests)
        receipt = MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"invocation_index": invocation_index},
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=request.target_object_id
            or provider_delta_uuid(f"ontology-runtime-root:{invocation_index}"),
            graph_hash_pre=f"sha256:test:pre:{invocation_index}",
            graph_hash_post=f"sha256:test:post:{invocation_index}",
            changes=JsonArray([]),
            function_call_id=provider_delta_uuid(
                f"ontology-runtime-function-call:{invocation_index}"
            ),
            function_call_response_id=provider_delta_uuid(
                f"ontology-runtime-function-response:{invocation_index}"
            ),
            commit_id=provider_delta_uuid(
                f"ontology-runtime-commit:{invocation_index}"
            ),
            object_instance_graph_commit_id=provider_delta_uuid(
                f"ontology-runtime-oig-commit:{invocation_index}"
            ),
        )
        self.receipts.append(receipt)
        return receipt


def provider_delta_ontology_invocation_runtime_context(
    *,
    root_projection_hash: str,
    package_projection_hash: str,
) -> SimpleNamespace:
    function_impl_create_instruction = _function_link(
        owner="FunctionImpl",
        name="create_instruction",
    )
    function_impl_remove_instruction = _function_link(
        owner="FunctionImpl",
        name="remove_instruction",
    )
    instruction_create_value_source = _function_link(
        owner="FunctionImplInstruction",
        name="create_value_source",
    )
    instruction_attach_set = _function_link(
        owner="FunctionImplInstruction",
        name="attach_set",
    )
    value_source_update_function_input = _function_link(
        owner="FunctionImplValueSource",
        name="update_function_input_ref",
    )
    instruction_set_update_assignment = _function_link(
        owner="FunctionImplInstructionSet",
        name="update_assignment",
    )
    attribute_update_primitive = _function_link(
        owner="AttributeConfig",
        name="update_primitive",
    )
    class_attribute_membership_update_config = _function_link(
        owner="ClassConfigAttributeConfig",
        name="update_config",
    )
    function_attribute_membership_update_config = _function_link(
        owner="FunctionConfigAttributeConfig",
        name="update_config",
    )
    class_remove_attribute_config = _function_link(
        owner="ClassConfig",
        name="remove_attribute_config",
    )
    class_create_relationship = _function_link(
        owner="ClassConfig",
        name="create_relationship",
    )
    class_remove_relationship_config = _function_link(
        owner="ClassConfig",
        name="remove_relationship_config",
    )
    relationship_update_config = _function_link(
        owner="ClassConfigRelationship",
        name="update_config",
    )
    class_function_membership_update_config = _function_link(
        owner="ClassConfigFunctionConfig",
        name="update_config",
    )
    function_update_config = _function_link(
        owner="FunctionConfig",
        name="update_config",
    )
    function_remove_attribute_config = _function_link(
        owner="FunctionConfig",
        name="remove_attribute_config",
    )
    function_add_primitive_attribute_config = _function_link(
        owner="FunctionConfig",
        name="add_primitive_attribute_config",
    )
    index = SimpleNamespace(
        class_configs_by_id={
            provider_delta_uuid("AttributeConfig.class"): _class_config(
                name="AttributeConfig",
                function_links=(attribute_update_primitive,),
            ),
            provider_delta_uuid("ClassConfig.class"): _class_config(
                name="ClassConfig",
                function_links=(
                    class_remove_attribute_config,
                    class_create_relationship,
                    class_remove_relationship_config,
                ),
            ),
            provider_delta_uuid("ClassConfigAttributeConfig.class"): _class_config(
                name="ClassConfigAttributeConfig",
                function_links=(class_attribute_membership_update_config,),
            ),
            provider_delta_uuid("ClassConfigRelationship.class"): _class_config(
                name="ClassConfigRelationship",
                function_links=(relationship_update_config,),
            ),
            provider_delta_uuid("ClassConfigFunctionConfig.class"): _class_config(
                name="ClassConfigFunctionConfig",
                function_links=(class_function_membership_update_config,),
            ),
            provider_delta_uuid("FunctionConfig.class"): _class_config(
                name="FunctionConfig",
                function_links=(
                    function_update_config,
                    function_remove_attribute_config,
                    function_add_primitive_attribute_config,
                ),
            ),
            provider_delta_uuid("FunctionConfigAttributeConfig.class"): _class_config(
                name="FunctionConfigAttributeConfig",
                function_links=(function_attribute_membership_update_config,),
            ),
            provider_delta_uuid("FunctionImpl.class"): _class_config(
                name="FunctionImpl",
                function_links=(
                    function_impl_create_instruction,
                    function_impl_remove_instruction,
                ),
            ),
            provider_delta_uuid("FunctionImplInstruction.class"): _class_config(
                name="FunctionImplInstruction",
                function_links=(
                    instruction_create_value_source,
                    instruction_attach_set,
                ),
            ),
            provider_delta_uuid("FunctionImplValueSource.class"): _class_config(
                name="FunctionImplValueSource",
                function_links=(value_source_update_function_input,),
            ),
            provider_delta_uuid("FunctionImplInstructionSet.class"): _class_config(
                name="FunctionImplInstructionSet",
                function_links=(instruction_set_update_assignment,),
            ),
        },
        opg_by_id={},
        opg_by_hash={},
    )
    return SimpleNamespace(
        index=index,
        projection_hash_by_name={
            "ObjectConfigGraph": root_projection_hash,
            "ObjectConfigGraphPackage": package_projection_hash,
        },
    )


def build_provider_delta_runtime_execution_context(
    *,
    workspace_root: Path,
    key: str,
) -> ProviderDeltaRuntimeExecutionContext:
    branch_id = provider_delta_uuid(f"{key}-branch")
    actor_id = provider_delta_uuid(f"{key}-actor")
    baseline_domain_commit_id = provider_delta_uuid(f"{key}-baseline-domain-head")
    baseline_oig_commit_id = provider_delta_uuid(f"{key}-baseline-oig-head")
    baseline_root_domain_commit_id = provider_delta_uuid(
        f"{key}-baseline-root-domain-head"
    )
    baseline_root_oig_commit_id = provider_delta_uuid(f"{key}-baseline-root-oig-head")
    baseline_root_oig_id = provider_delta_uuid(f"{key}-baseline-root-oig")
    baseline_root_oigi_id = provider_delta_uuid(f"{key}-baseline-root-oigi")
    package_projection_hash = "sha256:test:ObjectConfigGraphPackage"
    root_projection_hash = "sha256:test:ObjectConfigGraph"
    runtime = RecordingProviderDeltaOntologyRuntime()
    graph_runtime_context = provider_delta_ontology_invocation_runtime_context(
        root_projection_hash=root_projection_hash,
        package_projection_hash=package_projection_hash,
    )
    write_root_oig_head_context(
        workspace_root=workspace_root,
        branch_id=branch_id,
        root_projection_hash=root_projection_hash,
        root_domain_commit_id=baseline_root_domain_commit_id,
        root_oig_commit_id=baseline_root_oig_commit_id,
        root_oig_id=baseline_root_oig_id,
        root_oigi_id=baseline_root_oigi_id,
    )
    request = SimpleNamespace(
        execute_provider_delta_materialization=True,
        context={
            "runtime": runtime,
            "aware_meta.graph_runtime_context": graph_runtime_context,
        },
        workspace_root=str(workspace_root),
        provider_delta_author_id=str(actor_id),
        semantic_branch_id=str(branch_id),
        semantic_projection_hash=package_projection_hash,
        baseline_semantic_object_instance_graph_commit_id=str(baseline_oig_commit_id),
        baseline_semantic_root_object_instance_graph_commit_id=(
            str(baseline_root_oig_commit_id)
        ),
        semantic_package_commit_id=str(baseline_domain_commit_id),
    )
    baseline_dirty_preflight: dict[str, object] = {
        "status": "baseline_commit_refs_available",
        "commit_backed_baseline_available": True,
        "baseline_ref_available": True,
        "baseline_ref_hydrator_ready": True,
        "baseline_hydration_preflight": {
            "status": "baseline_hydrated",
            "semantic_branch_id": str(branch_id),
            "semantic_projection_hash": package_projection_hash,
            "semantic_object_instance_graph_commit_id": str(baseline_oig_commit_id),
            "semantic_root_object_instance_graph_commit_id": (
                str(baseline_root_oig_commit_id)
            ),
            "details": {
                "materializer_metadata": {
                    "domain_commit_id": str(baseline_domain_commit_id),
                },
            },
        },
    }
    return ProviderDeltaRuntimeExecutionContext(
        branch_id=branch_id,
        actor_id=actor_id,
        baseline_domain_commit_id=baseline_domain_commit_id,
        baseline_oig_commit_id=baseline_oig_commit_id,
        baseline_root_domain_commit_id=baseline_root_domain_commit_id,
        baseline_root_oig_commit_id=baseline_root_oig_commit_id,
        baseline_root_oig_id=baseline_root_oig_id,
        baseline_root_oigi_id=baseline_root_oigi_id,
        package_projection_hash=package_projection_hash,
        root_projection_hash=root_projection_hash,
        runtime=runtime,
        graph_runtime_context=graph_runtime_context,
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
    )


def write_root_oig_head_context(
    *,
    workspace_root: Path,
    branch_id: UUID,
    root_projection_hash: str,
    root_domain_commit_id: UUID,
    root_oig_commit_id: UUID,
    root_oig_id: UUID,
    root_oigi_id: UUID,
) -> None:
    root_oig_commit_index_path = (
        workspace_root
        / ".aware"
        / "oig"
        / str(branch_id)
        / root_projection_hash
        / "indexes"
        / "object_instance_graph_commits"
        / f"{root_oig_commit_id}.json"
    )
    root_oig_commit_index_path.parent.mkdir(parents=True)
    root_oig_commit_index_path.write_text(
        json.dumps(
            {
                "v": 1,
                "branch_id": str(branch_id),
                "projection_hash": root_projection_hash,
                "object_instance_graph_commit_id": str(root_oig_commit_id),
                "domain_commit_id": str(root_domain_commit_id),
            }
        ),
        encoding="utf-8",
    )
    root_head_path = (
        workspace_root
        / ".aware"
        / "oig"
        / str(branch_id)
        / root_projection_hash
        / "HEAD.json"
    )
    root_head_path.write_text(
        json.dumps(
            {
                "v": 1,
                "commit_id": str(root_domain_commit_id),
                "object_instance_graph_commit_id": str(root_oig_commit_id),
                "object_instance_graph_id": str(root_oig_id),
                "object_instance_graph_identity_id": str(root_oigi_id),
            }
        ),
        encoding="utf-8",
    )


def _class_config(
    *,
    name: str,
    function_links: tuple[SimpleNamespace, ...],
) -> SimpleNamespace:
    return SimpleNamespace(
        id=provider_delta_uuid(f"{name}.class"),
        name=name,
        class_fqn=f"aware_meta.{name}",
        class_config_function_configs=function_links,
    )


def _function_link(*, owner: str, name: str) -> SimpleNamespace:
    function_id = provider_delta_uuid(f"{owner}.{name}.function")
    return SimpleNamespace(
        id=provider_delta_uuid(f"{owner}.{name}.link"),
        function_config_id=function_id,
        function_config=SimpleNamespace(
            id=function_id,
            owner_key=f"aware_meta.{owner}",
            name=name,
        ),
    )
