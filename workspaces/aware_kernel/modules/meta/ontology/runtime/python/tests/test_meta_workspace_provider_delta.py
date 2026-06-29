from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from _meta_runtime_test_paths import META_RUNTIME_ROOT, REPO_ROOT

_REPO_ROOT = REPO_ROOT
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_META_RUNTIME_ROOT_STR = str(META_RUNTIME_ROOT)
if _META_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _META_RUNTIME_ROOT_STR)

from aware_code.semantic_materialization import (  # noqa: E402
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY,
    SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY,
    SemanticProviderDeltaRequest,
)
from aware_code.types import JsonArray  # noqa: E402
from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: E402
from aware_meta.materialization import workspace_provider  # noqa: E402
from aware_meta.materialization.deltas import service as provider_delta  # noqa: E402
from aware_meta.materialization.deltas.execution import (  # noqa: E402
    _provider_delta_oig_commit_receipt,
)
from aware_meta.materialization.deltas.ontology_execution.service import (  # noqa: E402
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.attribute.config.deltas.ontology_execution import (  # noqa: E402
    ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF,
    CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
    FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
)
from aware_meta.function.impl.deltas.ontology_execution import (  # noqa: E402
    FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
    FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
    FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
)
from aware_meta.materialization.runtime_delta import (  # noqa: E402
    MetaOcgRuntimeDeltaTransformRequest,
    build_meta_ocg_runtime_delta_transform,
)
from aware_meta.manifest.spec import AwareTomlNamespaceMappingSpec  # noqa: E402
from aware_meta.runtime.package_index import (  # noqa: E402
    MetaRuntimePackageIndexEntry,
    build_meta_runtime_package_projection_index,
    load_meta_runtime_package_projection_index,
)
from aware_meta.runtime.invocation_engine import (  # noqa: E402
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.materialization.semantic_function_call_resolution import (  # noqa: E402
    META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
    META_OCG_CREATE_NODE_FUNCTION_REF,
)
from aware_meta.semantic_contract import (  # noqa: E402
    META_GRAPH_RUNTIME_CONTEXT_KEY,
    META_MATERIALIZATION_CAPABILITY_METADATA,
    META_MATERIALIZATION_DELTA_ADAPTER_METADATA,
    META_OBJECT_CONFIG_GRAPH_OWNER,
)
from aware_meta.semantic_analysis import MetaOcgSemanticAnalysisResult  # noqa: E402
from aware_meta_ontology.attribute.attribute import Attribute  # noqa: E402
from aware_meta_ontology.attribute.attribute_config import AttributeConfig  # noqa: E402
from aware_meta_ontology.attribute.attribute_value import AttributeValue  # noqa: E402
from aware_meta_ontology.class_.class_instance import ClassInstance  # noqa: E402
from aware_meta_ontology.class_.class_instance_attribute import (  # noqa: E402
    ClassInstanceAttribute,
)
from aware_meta_ontology.class_.class_instance_relationship import (  # noqa: E402
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_config import ClassConfig  # noqa: E402
from aware_meta_ontology.class_.class_config_relationship import (  # noqa: E402
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (  # noqa: E402
    ClassConfigRelationshipType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (  # noqa: E402
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.config.object_config_graph import (  # noqa: E402
    ObjectConfigGraph,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (  # noqa: E402
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (  # noqa: E402
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (  # noqa: E402
    ObjectProjectionGraph,
)
from aware_workspace.features.semantic_materialization.delta_contract import (  # noqa: E402
    WorkspaceSemanticMaterializationProviderDeltaRequest,
    build_workspace_semantic_materialization_provider_delta_request_bundle,
    classify_workspace_semantic_materialization_provider_delta_request,
    dry_run_workspace_semantic_materialization_provider_delta_adapter_contract,
    plan_workspace_semantic_materialization_provider_delta_adapter,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")


def _provider_delta_context_graph() -> ObjectConfigGraph:
    graph_id = uuid4()
    class_config = ClassConfig(
        class_fqn="aware_meta.ObjectConfigGraphPackage",
        name="ObjectConfigGraphPackage",
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="Meta Provider Delta Context Graph",
        hash="sha256:test:meta-provider-delta-context",
        fqn_prefix="aware_meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=graph_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_config.class_fqn,
                class_config=class_config,
            )
        ],
        object_projection_graphs=[
            ObjectProjectionGraph(
                object_config_graph_id=graph_id,
                language=CodeLanguage.aware,
                name="ObjectConfigGraphPackage",
                projection_hash="sha256:test:ObjectConfigGraphPackage",
            )
        ],
    )


def _home_namespace_mappings() -> tuple[AwareTomlNamespaceMappingSpec, ...]:
    return (
        AwareTomlNamespaceMappingSpec(
            path="home/**/*.aware",
            namespace="default.home",
        ),
    )


def _aware_toml_namespace_lines() -> list[str]:
    return [
        "[build.namespace]",
        '"home/**/*.aware" = "default.home"',
        "",
    ]


def _write_meta_delta_fixture(workspace_root: Path) -> Path:
    manifest_path = workspace_root / "aware.toml"
    _write(
        manifest_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                *_aware_toml_namespace_lines(),
            ]
        ),
    )
    _write(
        workspace_root / "aware" / "home" / "model.aware",
        "\n".join(
            [
                "enum RoomState {",
                "    ready",
                "    offline",
                "}",
                "",
                "class Door {",
                "    label String",
                "}",
                "",
                "class Room {",
                "    name String",
                "    state RoomState?",
                "    doors Door[]",
                "",
                "    fn create construct (",
                "        name String key",
                "    ) -> Room {",
                '        """',
                "        Create deterministic room.",
                '        """',
                "    }",
                "}",
                "",
            ]
        ),
    )
    return manifest_path


def _write_meta_attribute_update_delta_fixture(workspace_root: Path) -> Path:
    manifest_path = workspace_root / "aware.toml"
    _write(
        manifest_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                *_aware_toml_namespace_lines(),
            ]
        ),
    )
    _write(
        workspace_root / "aware" / "home" / "model.aware",
        "\n".join(
            [
                "class Room {",
                "    name Int",
                "}",
                "",
            ]
        ),
    )
    return manifest_path


def _provider_delta_request(
    *,
    manifest_path: Path,
    change_kind: str = "update",
    include_baseline_refs: bool = False,
    include_code_package_delta: bool = True,
    include_code_delta_content: bool = True,
    code_delta_content_text: str | None = None,
) -> WorkspaceSemanticMaterializationProviderDeltaRequest:
    source_relative_path = "aware/home/model.aware"
    source_text = (
        code_delta_content_text
        if code_delta_content_text is not None
        else (manifest_path.parent / source_relative_path).read_text(encoding="utf-8")
    )
    payload: dict[str, object] = {
        "package": {
            "package_name": "demo-ontology",
            "workspace_manifest_kind": "aware_toml",
            "manifest_path": manifest_path.as_posix(),
            "source_code_package_id": "source-code-package-id",
        },
        "semantic_contract": {
            "module": "aware_meta.semantic_contract",
            "provider_key": "aware_meta",
            "role": "aware_meta.provider",
            "name": "aware.semantic_provider",
        },
        "current_delta_fingerprint": "sha256:current",
        "delta_cause_hints": {
            "changed_path_count": 1,
            "source_owned_path_count": 1,
            "generated_fallout_path_count": 0,
            "changed_path_classifications": {"source_owned": 1},
            "top_changed_path_limit": 8,
            "top_changed_paths": [
                {
                    "path": "aware/home/model.aware",
                    "change_kind": change_kind,
                    "classification": "source_owned",
                    "package_relative_path": "aware/home/model.aware",
                    "language": "aware",
                    "is_structural": True,
                }
            ],
            "current_delta_fingerprint_available": True,
            "previous_delta_fingerprint_available": True,
        },
    }
    if include_code_package_delta:
        delta_path: dict[str, object] = {
            "relative_path": source_relative_path,
            "kind": change_kind,
            "language": "aware",
            "is_structural": True,
            "path_role": "authored_source",
        }
        if include_code_delta_content and change_kind != "delete":
            delta_path["content_text"] = source_text
        payload["code_package_delta"] = {
            "package_name": "demo-ontology",
            "package_root": ".",
            "sources_root": "aware",
            "manifest_relative_path": manifest_path.name,
            "authority_kind": "local_fs_view",
            "source_revision_id": "test-current",
            "paths": [delta_path],
        }
    if include_baseline_refs:
        payload["baseline_ref"] = _baseline_ref_payload(
            manifest_path=manifest_path,
        )
        payload["previous_materialization_evidence"] = {
            "available": True,
            "evidence_source": "reused_workspace_materialization_receipt",
            "commit_refs": {
                "source_object_instance_graph_commit_id": "source-oig-commit",
                "semantic_object_instance_graph_commit_id": (
                    "semantic-package-oig-commit"
                ),
                "semantic_root_object_instance_graph_commit_id": (
                    "semantic-root-oig-commit"
                ),
            },
        }
    return WorkspaceSemanticMaterializationProviderDeltaRequest.model_validate(payload)


def _baseline_ref_payload(*, manifest_path: Path) -> dict[str, object]:
    return {
        "workspace_revision_id": "workspace-revision-id",
        "workspace_materialization_id": "workspace-materialization-id",
        "workspace_materialization_index": 3,
        "revision_code_package_id": "revision-code-package-id",
        "source_code_package_id": "source-code-package-id",
        "source_object_instance_graph_commit_id": "source-oig-commit",
        "revision_code_package_object_instance_graph_commit_id": "source-oig-commit",
        "semantic_package_commit_id": "semantic-package-commit-id",
        "semantic_owner_module": "aware_meta",
        "semantic_package_kind": "object_config_graph_package",
        "semantic_package_id": "semantic-package-id",
        "semantic_package_name": "demo-ontology",
        "semantic_contract_module": "aware_meta.semantic_contract",
        "semantic_contract_name": "aware.semantic_provider",
        "semantic_contract_role": "aware_meta.provider",
        "semantic_contract_provider_key": "aware_meta",
        "semantic_projection_name": "ObjectConfigGraphPackage",
        "semantic_branch_id": "semantic-branch-id",
        "semantic_object_instance_graph_commit_id": "semantic-package-oig-commit",
        "semantic_root_kind": "object_config_graph",
        "semantic_root_id": "semantic-root-id",
        "semantic_root_object_instance_graph_commit_id": "semantic-root-oig-commit",
        "manifest_path": manifest_path.as_posix(),
        "manifest_toml_path": manifest_path.as_posix(),
    }


def _baseline_semantic_object_index_payload() -> dict[str, dict[str, object]]:
    return {
        "ocg_package:demo-ontology": {
            "object_id": "baseline-package-object-id",
            "object_kind": "object_config_graph_package",
            "source_refs": ("aware.toml",),
        },
        "ocg:aware_demo": {
            "object_id": "baseline-graph-object-id",
            "object_kind": "object_config_graph",
            "source_refs": ("home/model.aware",),
        },
        "ocg:aware_demo/node:aware_demo.default.home.Room": {
            "object_id": "baseline-room-class-object-id",
            "object_kind": "class",
            "source_refs": ("home/model.aware",),
        },
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name": {
            "object_id": "baseline-room-name-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": "ocg:aware_demo/node:aware_demo.default.home.Room",
            "attribute_name": "name",
            "source_refs": ("home/model.aware",),
        },
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:state": {
            "object_id": "baseline-room-state-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": "ocg:aware_demo/node:aware_demo.default.home.Room",
            "attribute_name": "state",
            "source_refs": ("home/model.aware",),
        },
    }


def _attribute_update_current_runtime_index(
    *,
    request: WorkspaceSemanticMaterializationProviderDeltaRequest,
) -> dict[str, dict[str, object]]:
    transform = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=request.code_package_delta,
            current_delta_fingerprint=request.current_delta_fingerprint,
            namespace_mappings=_home_namespace_mappings(),
            baseline_semantic_object_index={
                "ocg:aware_demo": {
                    "object_id": str(_test_uuid("seed-baseline-graph")),
                    "object_kind": "object_config_graph",
                },
            },
        )
    )
    assert transform.status == "runtime_delta_transform_ready"
    return {
        str(key): {str(item_key): item_value for item_key, item_value in value.items()}
        for key, value in transform.current_runtime_semantic_object_index.items()
    }


def _baseline_semantic_object_index_for_attribute_update(
    *,
    current_index: Mapping[str, Mapping[str, object]],
    attribute_semantic_key: str,
) -> dict[str, dict[str, object]]:
    baseline_index: dict[str, dict[str, object]] = {}
    for semantic_key, current_entry in current_index.items():
        entry = {str(key): item for key, item in current_entry.items()}
        entry["object_id"] = str(_test_uuid(f"baseline-object:{semantic_key}"))
        entry["object_kind"] = str(
            entry.get("object_kind") or entry.get("ontology_subject_kind")
        )
        if semantic_key == attribute_semantic_key:
            entry["semantic_fingerprint"] = (
                "sha256:test:baseline-before-attribute-type-update"
            )
            entry["attribute_signature"] = {
                "name": "name",
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
                "kind": "primitive",
                "primitive_base_type": "string",
                "is_required": True,
                "is_public": True,
                "position": 0,
            }
        baseline_index[semantic_key] = entry
    return baseline_index


def _test_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:test:meta-provider-delta:{key}")


class _RecordingProviderDeltaOntologyRuntime:
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
            or _test_uuid(f"ontology-runtime-root:{invocation_index}"),
            graph_hash_pre=f"sha256:test:pre:{invocation_index}",
            graph_hash_post=f"sha256:test:post:{invocation_index}",
            changes=JsonArray([]),
            function_call_id=_test_uuid(
                f"ontology-runtime-function-call:{invocation_index}"
            ),
            function_call_response_id=_test_uuid(
                f"ontology-runtime-function-response:{invocation_index}"
            ),
            commit_id=_test_uuid(f"ontology-runtime-commit:{invocation_index}"),
            object_instance_graph_commit_id=_test_uuid(
                f"ontology-runtime-oig-commit:{invocation_index}"
            ),
        )
        self.receipts.append(receipt)
        return receipt


def _provider_delta_ontology_invocation_runtime_context() -> SimpleNamespace:
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
    index = SimpleNamespace(
        class_configs_by_id={
            _test_uuid("AttributeConfig.class"): _class_config(
                name="AttributeConfig",
                function_links=(attribute_update_primitive,),
            ),
            _test_uuid("ClassConfig.class"): _class_config(
                name="ClassConfig",
                function_links=(
                    class_remove_attribute_config,
                    class_create_relationship,
                    class_remove_relationship_config,
                ),
            ),
            _test_uuid("ClassConfigAttributeConfig.class"): _class_config(
                name="ClassConfigAttributeConfig",
                function_links=(class_attribute_membership_update_config,),
            ),
            _test_uuid("ClassConfigRelationship.class"): _class_config(
                name="ClassConfigRelationship",
                function_links=(relationship_update_config,),
            ),
            _test_uuid("ClassConfigFunctionConfig.class"): _class_config(
                name="ClassConfigFunctionConfig",
                function_links=(class_function_membership_update_config,),
            ),
            _test_uuid("FunctionConfig.class"): _class_config(
                name="FunctionConfig",
                function_links=(
                    function_update_config,
                    function_remove_attribute_config,
                ),
            ),
            _test_uuid("FunctionConfigAttributeConfig.class"): _class_config(
                name="FunctionConfigAttributeConfig",
                function_links=(function_attribute_membership_update_config,),
            ),
            _test_uuid("FunctionImpl.class"): _class_config(
                name="FunctionImpl",
                function_links=(
                    function_impl_create_instruction,
                    function_impl_remove_instruction,
                ),
            ),
            _test_uuid("FunctionImplInstruction.class"): _class_config(
                name="FunctionImplInstruction",
                function_links=(
                    instruction_create_value_source,
                    instruction_attach_set,
                ),
            ),
            _test_uuid("FunctionImplValueSource.class"): _class_config(
                name="FunctionImplValueSource",
                function_links=(value_source_update_function_input,),
            ),
            _test_uuid("FunctionImplInstructionSet.class"): _class_config(
                name="FunctionImplInstructionSet",
                function_links=(instruction_set_update_assignment,),
            ),
        },
        opg_by_id={},
        opg_by_hash={},
    )
    return SimpleNamespace(index=index)


def _class_config(
    *,
    name: str,
    function_links: tuple[SimpleNamespace, ...],
) -> SimpleNamespace:
    return SimpleNamespace(
        id=_test_uuid(f"{name}.class"),
        name=name,
        class_fqn=f"aware_meta.{name}",
        class_config_function_configs=function_links,
    )


def _function_link(*, owner: str, name: str) -> SimpleNamespace:
    function_id = _test_uuid(f"{owner}.{name}.function")
    return SimpleNamespace(
        id=_test_uuid(f"{owner}.{name}.link"),
        function_config_id=function_id,
        function_config=SimpleNamespace(
            id=function_id,
            owner_key=f"aware_meta.{owner}",
            name=name,
        ),
    )


def _baseline_oig_from_semantic_objects(
    *,
    include_layouts: bool = True,
    include_function_impl_source_ref: bool = True,
) -> ObjectInstanceGraph:
    oig_id = _test_uuid("baseline-oig")
    room_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_key = (
        "aware_demo.default.home.Room:doors:one_to_many:" "aware_demo.default.home.Door"
    )
    function_impl_attrs: dict[str, object] = {
        "key": "default",
        "kind": "instruction_body",
        "instruction_count": 0,
    }
    if include_function_impl_source_ref:
        function_impl_attrs["relative_path"] = "home/model.aware"
    class_instances: list[ClassInstance] = [
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-package-object-id",
            class_config_name="ObjectConfigGraphPackage",
            attrs={
                "package_name": "demo-ontology",
            },
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-graph-object-id",
            class_config_name="ObjectConfigGraph",
            attrs={
                "fqn_prefix": "aware_demo",
            },
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-room-class-object-id",
            class_config_name="ObjectConfigGraphNode",
            attrs={
                "graph_semantic_key": "ocg:aware_demo",
                "node_key": "aware_demo.default.home.Room",
                "node_type": "class",
                "name": "String",
                "state": "RoomState?",
            },
            attribute_ids={
                "name": "baseline-room-name-attribute-object-id",
                "state": "baseline-room-state-attribute-object-id",
            },
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-room-state-enum-object-id",
            class_config_name="ObjectConfigGraphNode",
            attrs={
                "graph_semantic_key": "ocg:aware_demo",
                "node_key": "aware_demo.default.home.RoomState",
                "node_type": "enum",
            },
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-room-door-relationship-object-id",
            class_config_name="ObjectConfigGraphNode",
            attrs={
                "graph_semantic_key": "ocg:aware_demo",
                "node_key": relationship_key,
                "node_type": "relationship",
            },
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-room-create-function-object-id",
            class_config_name="ObjectConfigGraphNode",
            attrs={
                "graph_semantic_key": "ocg:aware_demo",
                "node_key": "aware_demo.default.home.Room.create",
                "node_type": "function",
            },
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-room-create-function-impl-object-id",
            class_config_name="FunctionImpl",
            attrs=function_impl_attrs,
        ),
        _oig_class_instance(
            oig_id=oig_id,
            object_id="baseline-room-capacity-attribute-config-object-id",
            class_config_name="AttributeConfig",
            attrs={
                "owner_semantic_key": room_semantic_key,
                "name": "capacity",
            },
        ),
    ]
    relationships: list[ClassInstanceRelationship] = [
        _oig_relationship(
            oig_id=oig_id,
            object_id="baseline-room-door-relationship-link-id",
            relationship_id="baseline-relationship-config-id",
            relationship_key=relationship_key,
            source_class_instance_id="baseline-room-class-object-id",
            target_class_instance_id="baseline-door-class-object-id",
        ),
        _oig_relationship(
            oig_id=oig_id,
            object_id="baseline-room-create-function-impl-link-id",
            relationship_id="baseline-function-impl-relationship-id",
            relationship_key="function_impl",
            source_class_instance_id="baseline-room-create-function-object-id",
            target_class_instance_id="baseline-room-create-function-impl-object-id",
        ),
    ]
    if include_layouts:
        class_instances.append(
            _oig_class_instance(
                oig_id=oig_id,
                object_id="baseline-room-layout-object-id",
                class_config_name="ObjectConfigGraphNodeLayout",
                attrs={
                    "layout_kind": "aware",
                    "relative_path": "home/model.aware",
                    "source_position": 12,
                },
            )
        )
        relationships.append(
            _oig_relationship(
                oig_id=oig_id,
                object_id="baseline-room-layout-link-id",
                relationship_id="baseline-layout-relationship-id",
                relationship_key=None,
                source_class_instance_id="baseline-room-class-object-id",
                target_class_instance_id="baseline-room-layout-object-id",
            )
        )
    return ObjectInstanceGraph.model_construct(
        id=oig_id,
        object_projection_graph_id=_test_uuid("baseline-opg"),
        root_class_instance_id=class_instances[0].id,
        root_class_instance=class_instances[0],
        key="baseline-oig",
        name="Baseline OIG",
        description="typed baseline fixture",
        hash="sha256:test:baseline-oig",
        class_instances=class_instances,
        class_instance_relationships=relationships,
    )


def _oig_class_instance(
    *,
    oig_id: UUID,
    object_id: str,
    class_config_name: str,
    attrs: Mapping[str, object],
    attribute_ids: Mapping[str, str] | None = None,
) -> ClassInstance:
    class_instance_id = _test_uuid(object_id)
    class_config_id = _test_uuid(f"{class_config_name}:class-config-id")
    attributes = tuple(
        _oig_attribute(
            class_instance_id=class_instance_id,
            name=name,
            value=value,
            attribute_id=(attribute_ids or {}).get(
                name,
                f"{object_id}:{name}:attribute-id",
            ),
        )
        for name, value in attrs.items()
    )
    return ClassInstance.model_construct(
        id=class_instance_id,
        object_instance_graph_id=oig_id,
        source_object_id=_test_uuid(f"source:{object_id}"),
        class_config_id=class_config_id,
        class_config=ClassConfig.model_construct(
            id=class_config_id,
            class_fqn=f"aware_meta.{class_config_name}",
            name=class_config_name,
        ),
        class_instance_attributes=[
            ClassInstanceAttribute.model_construct(
                id=_test_uuid(f"{attribute.id}:edge"),
                class_instance_id=class_instance_id,
                attribute_id=attribute.id,
                attribute=attribute,
            )
            for attribute in attributes
        ],
    )


def _oig_attribute(
    *,
    class_instance_id: UUID,
    name: str,
    value: object,
    attribute_id: str,
) -> Attribute:
    attribute_config_id = _test_uuid(f"{name}:attribute-config-id")
    return Attribute.model_construct(
        id=_test_uuid(attribute_id),
        owner_key=_test_uuid(f"owner:{class_instance_id}"),
        attribute_config_id=attribute_config_id,
        attribute_config=AttributeConfig.model_construct(
            id=attribute_config_id,
            owner_key=str(class_instance_id),
            name=name,
            type_descriptor_id=_test_uuid(f"{name}:type-descriptor-id"),
        ),
        value_root=AttributeValue.model_construct(
            id=_test_uuid(f"{attribute_id}:value-root"),
            type_descriptor_id=_test_uuid(f"{name}:type-descriptor-id"),
            primitive_value=value,
        ),
    )


def _oig_relationship(
    *,
    oig_id: UUID,
    object_id: str,
    relationship_id: str,
    relationship_key: str | None,
    source_class_instance_id: str,
    target_class_instance_id: str,
) -> ClassInstanceRelationship:
    relationship_uuid = _test_uuid(relationship_id)
    return ClassInstanceRelationship.model_construct(
        id=_test_uuid(object_id),
        object_instance_graph_id=oig_id,
        class_config_relationship_id=relationship_uuid,
        class_config_relationship=(
            ClassConfigRelationship.model_construct(
                id=relationship_uuid,
                relationship_key=relationship_key,
                relationship_type=ClassConfigRelationshipType.one_to_many,
                forward_required=False,
                class_config_id=_test_uuid("relationship-source-class-config-id"),
                target_class_config_id=_test_uuid(
                    "relationship-target-class-config-id"
                ),
            )
            if relationship_key is not None
            else None
        ),
        source_class_instance_id=_test_uuid(source_class_instance_id),
        target_class_instance_id=_test_uuid(target_class_instance_id),
    )


def _meta_provider_descriptor() -> dict[str, object]:
    return {
        "provider_key": "aware_meta",
        "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
        "callable_module": "aware_meta.materialization.workspace_provider",
        "callable_name": "materialize",
        "metadata": META_MATERIALIZATION_CAPABILITY_METADATA,
    }


def _descriptor_tree_payload_keys(payload: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(sorted(key for key in payload if "descriptor_tree" in key))


@pytest.mark.asyncio
async def test_meta_provider_delta_adapter_dry_run_contract(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    request = _provider_delta_request(manifest_path=manifest_path)

    assert (
        META_MATERIALIZATION_CAPABILITY_METADATA[
            SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY
        ]
        == META_MATERIALIZATION_DELTA_ADAPTER_METADATA
    )
    assert META_MATERIALIZATION_DELTA_ADAPTER_METADATA["callable_module"] == (
        "aware_meta.materialization.workspace_provider"
    )
    assert META_MATERIALIZATION_DELTA_ADAPTER_METADATA["callable_name"] == (
        SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT
    )
    assert (
        META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY
        ]
        is True
    )
    assert (
        META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY
        ]
        == "ObjectConfigGraphPackage"
    )
    readiness = META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
        SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY
    ]
    assert isinstance(readiness, Mapping)
    assert readiness["readiness_kind"] == "meta_ocg_delta_product_readiness"
    assert readiness["contract_version"] == (
        SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION
    )
    assert readiness["provider_contract_version"] == (
        "aware.meta.ocg-delta-coverage-matrix.v1"
    )
    assert readiness["provider_key"] == "aware_meta"
    assert readiness["default_policy"] == "ready_operations_only"
    assert readiness["fallback_policy"] == "explicit_fallback_required"
    assert readiness["ready_operation_count"] == 12
    assert readiness["render_all_required_operation_count"] == 20
    assert readiness["blocked_operation_count"] == 0
    context_resolvers = META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
        SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY
    ]
    assert isinstance(context_resolvers, tuple)
    assert {
        resolver["context_key"]
        for resolver in context_resolvers
        if isinstance(resolver, Mapping)
    } == {
        META_GRAPH_RUNTIME_CONTEXT_KEY,
    }

    classification = classify_workspace_semantic_materialization_provider_delta_request(
        request=request,
        provider=_meta_provider_descriptor(),
    )
    adapter_plan = plan_workspace_semantic_materialization_provider_delta_adapter(
        request=request,
        classification=classification,
    )
    dry_run = await dry_run_workspace_semantic_materialization_provider_delta_adapter_contract(
        adapter=workspace_provider.materialize_delta,
        request=request,
    )

    assert classification.status == "delta_request_ready"
    assert classification.reason == "provider_declares_delta_adapter"
    assert adapter_plan.status == "ready_non_executing"
    assert adapter_plan.target is not None
    assert adapter_plan.target.callable_name == "materialize_delta"
    assert adapter_plan.adapter_preflight is not None
    assert adapter_plan.adapter_preflight.status == "passed"
    assert dry_run.status == "passed"
    assert dry_run.reason == "adapter_result_contract_valid"
    assert dry_run.adapter_invoked is True
    assert dry_run.result is not None
    assert dry_run.result.status == "succeeded"
    assert dry_run.result.details["production_execution_wired"] is False
    assert (
        dry_run.result.details["baseline_dirty_preflight"]["status"]
        == "baseline_context_missing"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_workspace_bundle_dry_run_invokes_adapter(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    request = _provider_delta_request(manifest_path=manifest_path)
    classification = classify_workspace_semantic_materialization_provider_delta_request(
        request=request,
        provider=_meta_provider_descriptor(),
    )
    adapter_plan = plan_workspace_semantic_materialization_provider_delta_adapter(
        request=request,
        classification=classification,
    )
    bundle = build_workspace_semantic_materialization_provider_delta_request_bundle(
        requests=(request,),
        classifications=(classification,),
        adapter_plans=(adapter_plan,),
    )
    bundle_path = tmp_path / "meta-provider-delta-request-bundle.json"
    _ = bundle_path.write_text(
        json.dumps(bundle.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    from aware_workspace.cli.workspace_command import (  # noqa: WPS433
        _workspace_provider_delta_adapter_dry_run_diagnostics_from_bundle_path,
    )

    diagnostics = (
        await _workspace_provider_delta_adapter_dry_run_diagnostics_from_bundle_path(
            bundle_path=bundle_path,
        )
    )

    diagnostic = diagnostics[0]
    result = cast(dict[str, object], diagnostic["result"])
    details = cast(dict[str, object], result["details"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    commit_ref_contract = cast(dict[str, object], result["commit_ref_contract"])
    assert classification.reason == "provider_declares_delta_adapter"
    assert adapter_plan.status == "ready_non_executing"
    assert diagnostic["provider_delta_request_key"] == (
        request.provider_delta_request_key
    )
    assert diagnostic["dry_run_status"] == "passed"
    assert diagnostic["dry_run_reason"] == "adapter_result_contract_valid"
    assert diagnostic["adapter_invoked"] is True
    assert diagnostic["production_execution_wired"] is False
    assert diagnostic["result_status"] == "succeeded"
    assert result["status"] == "succeeded"
    assert details["production_execution_wired"] is False
    assert operation_plan["plan_kind"] == "meta_ocg_provider_delta_operation_plan"
    assert operation_plan["status"] == "ready_non_executing"
    assert operation_plan["operation_count"] == operation_plan["semantic_delta_count"]
    assert commit_ref_contract["status"] == "missing_durable_refs"
    assert commit_ref_contract["available_fields"] == ["source_code_package_id"]
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    assert preflight["status"] == "baseline_context_missing"


@pytest.mark.asyncio
async def test_meta_provider_delta_workspace_forwards_declared_context(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    request = _provider_delta_request(manifest_path=manifest_path)
    classification = classify_workspace_semantic_materialization_provider_delta_request(
        request=request,
        provider=_meta_provider_descriptor(),
    )
    adapter_plan = plan_workspace_semantic_materialization_provider_delta_adapter(
        request=request,
        classification=classification,
    )
    graph = _provider_delta_context_graph()
    from aware_meta.runtime.graph_context import (  # noqa: WPS433
        build_meta_graph_runtime_index_snapshot,
    )
    from aware_workspace.cli.workspace_command import (  # noqa: WPS433
        _workspace_provider_delta_execution_context,
        _workspace_provider_delta_request_with_operation_execution_context,
    )

    execution_context = await _workspace_provider_delta_execution_context(
        request=request,
        adapter_plan=adapter_plan,
        workspace_root=tmp_path,
        runtime_context={
            "runtime": object(),
            "index": build_meta_graph_runtime_index_snapshot(ocg=graph),
            "actor_id": None,
            "environment_id": uuid4(),
            "process_id": uuid4(),
            "thread_id": uuid4(),
            "branch_id": uuid4(),
        },
    )
    adapter_request = (
        _workspace_provider_delta_request_with_operation_execution_context(
            request=request,
            context={},
            execution_context=execution_context,
        )
    )

    result = await workspace_provider.materialize_delta(request=adapter_request)

    details = cast(dict[str, object], result["details"])
    execution_preflight = cast(
        dict[str, object],
        details["provider_delta_execution_context_preflight"],
    )
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    assert execution_context is not None
    assert result["status"] == "succeeded"
    assert result["fallback_reason"] is None
    assert execution_preflight["status"] == "execution_context_available"
    assert execution_preflight["context_key"] == META_GRAPH_RUNTIME_CONTEXT_KEY
    assert execution_preflight["runtime_graph_count"] == 1
    assert execution_preflight["projection_names"] == ("ObjectConfigGraphPackage",)
    assert execution_preflight["materialization_execution_context_available"] is True
    materialization_context_keys = cast(
        tuple[str, ...],
        execution_preflight["materialization_execution_context_keys"],
    )
    assert META_GRAPH_RUNTIME_CONTEXT_KEY in materialization_context_keys
    assert len(materialization_context_keys) == 1
    assert operation_execution["status"] == "baseline_context_missing"
    assert operation_execution["did_execute"] is False


@pytest.mark.asyncio
async def test_meta_provider_delta_accepts_code_owned_request_contract(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    workspace_request = _provider_delta_request(manifest_path=manifest_path)
    code_request = SemanticProviderDeltaRequest.model_validate(
        workspace_request.model_dump(mode="json")
    )

    result = await workspace_provider.materialize_delta(request=code_request)
    details = cast(dict[str, object], result["details"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )

    assert result["status"] == "succeeded"
    assert head_move_plan["provider_delta_request_key"] == (
        code_request.provider_delta_request_key
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_result_plans_ocg_package_graph_and_nodes(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    request = _provider_delta_request(manifest_path=manifest_path)

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    applied_semantic_keys = cast(tuple[str, ...], result["applied_semantic_keys"])

    assert result["status"] == "succeeded"
    assert result["fallback_reason"] is None
    assert applied_semantic_keys == ()
    assert details["mode"] == "meta_ocg_provider_delta_result_dry_run"
    assert details["production_execution_wired"] is False

    operation_plan = cast(
        dict[str, object],
        details["delta_operation_plan"],
    )
    assert operation_plan["plan_kind"] == "meta_ocg_provider_delta_operation_plan"
    assert operation_plan["status"] == "ready_non_executing"
    assert operation_plan["reason"] == "meta_ocg_provider_delta_operation_plan_ready"
    assert operation_plan["changed_source_files"] == ("home/model.aware",)
    assert operation_plan["affected_object_config_graph_keys"] == ()
    assert operation_plan["required_materializations"] == ()
    assert operation_plan["operation_count"] == 0
    assert operation_plan["semantic_delta_count"] == 0
    assert operation_plan["semantic_function_call_plan_count"] == len(
        cast(tuple[object, ...], operation_plan["semantic_function_call_plans"])
    )
    baseline_dirty_preflight = cast(
        dict[str, object],
        operation_plan["baseline_dirty_preflight"],
    )
    assert baseline_dirty_preflight["status"] == "baseline_context_missing"
    assert baseline_dirty_preflight["commit_backed_baseline_available"] is False
    assert baseline_dirty_preflight["semantic_dirty_diff_available"] is False
    assert operation_plan["semantic_dirty_diff_status"] == (
        "semantic_dirty_diff_blocked"
    )
    assert operation_plan["semantic_dirty_diff_reason"] == (
        "meta_ocg_dirty_diff_requires_commit_backed_baseline"
    )
    assert operation_plan["apply_wired"] is False
    assert operation_plan["would_execute"] is False
    assert operation_plan["would_persist"] is False

    semantic_deltas = cast(
        tuple[dict[str, object], ...],
        operation_plan["semantic_deltas"],
    )
    assert semantic_deltas == ()

    function_refs = [
        cast(dict[str, object], plan)["function_ref"]
        for plan in cast(
            tuple[object, ...],
            operation_plan["semantic_function_call_plans"],
        )
    ]
    assert function_refs == []

    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    assert operation_execution["status"] == "flag_required"
    assert operation_execution["reason"] == (
        "meta_ocg_provider_delta_operation_execution_requires_explicit_flag"
    )
    assert operation_execution["flag_requested"] is False
    assert operation_execution["did_execute"] is False
    assert operation_execution["execution_wired"] is False

    commit_ref_contract = cast(dict[str, object], result["commit_ref_contract"])
    assert commit_ref_contract["contract_version"] == (
        "aware.workspace.semantic-materialization.provider-delta-commit-ref.v1"
    )
    assert commit_ref_contract["status"] == "missing_durable_refs"
    assert commit_ref_contract["reason"] == (
        "meta_ocg_provider_delta_dry_run_does_not_materialize_commits"
    )
    assert commit_ref_contract["available_fields"] == ["source_code_package_id"]
    assert commit_ref_contract["missing_required_fields"] == [
        "source_object_instance_graph_commit_id",
        "semantic_package_id",
        "semantic_branch_id",
        "semantic_object_instance_graph_commit_id",
    ]

    bundle_package = cast(dict[str, object], result["bundle_package"])
    assert bundle_package["package_key"] == "demo-ontology"
    assert bundle_package["package_kind"] == "object_config_graph"
    assert bundle_package["semantic_owner_module"] == "aware_meta"
    assert bundle_package["semantic_package_kind"] == "object_config_graph_package"
    assert bundle_package["semantic_contract_provider_key"] == "aware_meta"
    assert bundle_package["source_code_package_id"] == "source-code-package-id"
    assert bundle_package["commit_ref_contract_status"] == "missing_durable_refs"
    assert result["bundle_packages"] == (bundle_package,)


@pytest.mark.asyncio
async def test_meta_provider_delta_reports_complete_baseline_dirty_preflight(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])

    assert result["status"] == "succeeded"
    assert request.baseline_source_object_instance_graph_commit_id == (
        "source-oig-commit"
    )
    assert request.baseline_semantic_object_instance_graph_commit_id == (
        "semantic-package-oig-commit"
    )
    assert request.baseline_semantic_root_object_instance_graph_commit_id == (
        "semantic-root-oig-commit"
    )
    assert preflight["status"] == "baseline_commit_refs_available"
    assert preflight["commit_backed_baseline_available"] is True
    assert preflight["baseline_ref_available"] is True
    assert preflight["baseline_ref_hydrator_ready"] is True
    assert preflight["baseline_ref_missing_required_fields"] == ()
    assert preflight["semantic_dirty_diff_available"] is False
    assert preflight["semantic_dirty_diff_status"] == "semantic_dirty_diff_blocked"
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])
    assert hydration["status"] == "baseline_hydrator_unavailable"
    assert hydration["reason"] == (
        "meta_ocg_baseline_hydration_requires_runtime_index_or_adapter"
    )
    assert hydration["baseline_identity_source"] == "workspace.baseline_ref"
    assert hydration["hydrator_available"] is False
    assert hydration["would_persist"] is False
    assert hydration["did_persist"] is False
    assert hydration["did_hydrate"] is False
    assert preflight["baseline_commit_refs"] == {
        "baseline_source_object_instance_graph_commit_id": "source-oig-commit",
        "baseline_semantic_object_instance_graph_commit_id": (
            "semantic-package-oig-commit"
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            "semantic-root-oig-commit"
        ),
    }
    baseline_ref = cast(dict[str, object], preflight["baseline_ref"])
    assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
    assert baseline_ref["semantic_projection_name"] == "ObjectConfigGraphPackage"
    assert baseline_ref["semantic_object_instance_graph_commit_id"] == (
        "semantic-package-oig-commit"
    )
    assert baseline_ref["semantic_root_object_instance_graph_commit_id"] == (
        "semantic-root-oig-commit"
    )
    assert operation_plan["baseline_dirty_preflight"] == preflight


@pytest.mark.asyncio
async def test_meta_provider_delta_preserves_structured_baseline_hydrator_block(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> dict[str, object]:
        _ = request
        return {
            "status": "baseline_oig_payload_ref_missing",
            "reason": "workspace_baseline_oig_hydrator_requires_matching_oig_payload_ref_or_local_commit",
            "source": "workspace.semantic_materialization.baseline_oig_hydrator",
            "semantic_projection_hash": "ObjectConfigGraphPackage",
            "details": {
                "expected_branch_id": baseline_ref["semantic_branch_id"],
                "matching_oig_commit_payload_ref_count": 0,
            },
        }

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)

    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    assert hydration["status"] == "baseline_oig_payload_ref_missing"
    assert hydration["source"] == (
        "workspace.semantic_materialization.baseline_oig_hydrator"
    )
    assert hydration["semantic_projection_hash"] == "ObjectConfigGraphPackage"
    assert hydration["did_hydrate"] is False
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == (
        "meta_ocg_dirty_diff_requires_workspace_oig_payload_ref_or_local_commit"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_reports_missing_baseline_ref_when_commits_exist(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(manifest_path=manifest_path)
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence={
            "available": True,
            "evidence_source": "reused_workspace_materialization_receipt",
        },
        baseline_source_object_instance_graph_commit_id="source-oig-commit",
        baseline_semantic_object_instance_graph_commit_id=(
            "semantic-package-oig-commit"
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            "semantic-root-oig-commit"
        ),
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])

    assert preflight["status"] == "baseline_commit_refs_available"
    assert preflight["baseline_ref_available"] is False
    assert preflight["baseline_ref_hydrator_ready"] is False
    assert preflight["semantic_dirty_diff_status"] == "semantic_dirty_diff_blocked"
    assert hydration["status"] == "baseline_ref_missing"
    assert hydration["reason"] == (
        "meta_ocg_baseline_hydration_requires_workspace_baseline_ref"
    )
    assert hydration["did_hydrate"] is False
    assert hydration["would_persist"] is False


@pytest.mark.asyncio
async def test_meta_provider_delta_reports_incomplete_baseline_ref(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    incomplete_ref = _baseline_ref_payload(manifest_path=manifest_path)
    del incomplete_ref["semantic_branch_id"]
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=incomplete_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])
    hydration_details = cast(dict[str, object], hydration["details"])

    assert preflight["status"] == "baseline_commit_refs_available"
    assert preflight["baseline_ref_available"] is True
    assert preflight["baseline_ref_hydrator_ready"] is False
    assert preflight["baseline_ref_missing_required_fields"] == ("semantic_branch_id",)
    assert preflight["semantic_dirty_diff_status"] == "semantic_dirty_diff_blocked"
    assert hydration["status"] == "baseline_ref_incomplete"
    assert hydration_details["missing_required_fields"] == ("semantic_branch_id",)
    assert hydration["did_hydrate"] is False


@pytest.mark.asyncio
async def test_meta_provider_delta_reports_unresolved_baseline_projection(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        index=SimpleNamespace(
            ocg=SimpleNamespace(object_projection_graphs=()),
            opg_by_hash={},
        ),
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])

    assert preflight["status"] == "baseline_commit_refs_available"
    assert preflight["baseline_ref_hydrator_ready"] is True
    assert preflight["semantic_dirty_diff_status"] == "semantic_dirty_diff_blocked"
    assert hydration["status"] == "baseline_projection_unresolved"
    assert hydration["source"] == "meta_runtime_index"
    assert hydration["hydrator_available"] is True
    assert hydration["did_hydrate"] is False
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["available"] is False
    assert dirty_diff["blocked_status"] == "baseline_projection_unresolved"
    assert dirty_diff["blocked_reason"] == (
        "meta_ocg_dirty_diff_requires_resolvable_baseline_projection"
    )
    assert dirty_diff["dirty_entry_count"] == 0
    assert operation_plan["semantic_dirty_diff"] == dirty_diff
    assert operation_plan["semantic_dirty_diff_available"] is False
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    assert head_move_plan["plan_kind"] == "workspace_provider_delta_head_move"
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert head_move_plan["blocked"] is True
    assert head_move_plan["blocked_status"] == "semantic_dirty_diff_blocked"
    assert head_move_plan["planned_operation_count"] == 0
    assert head_move_plan["would_execute"] is False
    assert head_move_plan["would_persist"] is False
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_hydrated_baseline_without_index_blocks_indexed_compare(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[SimpleNamespace, dict[str, object]]:
        _ = request
        _ = baseline_ref
        return (
            SimpleNamespace(
                class_instances=[object(), object(), object()],
                class_instance_relationships=[object()],
            ),
            {"semantic_projection_hash": "projection-hash"},
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])

    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == (
        "meta_ocg_runtime_delta_requires_baseline_semantic_object_index"
    )
    assert dirty_diff["runtime_delta_transform_status"] == (
        "runtime_delta_transform_blocked"
    )
    assert dirty_diff["runtime_delta_transform_reason"] == (
        "meta_ocg_runtime_delta_requires_baseline_semantic_object_index"
    )
    assert dirty_diff["compare_mode"] == "runtime_delta_transform_required"
    assert dirty_diff["did_compare_against_current_delta"] is False
    assert dirty_diff["dirty_entry_count"] == 0
    assert dirty_diff["semantic_dirty_entries"] == ()
    assert dirty_diff["baseline_index_compare_available"] is False
    assert dirty_diff["baseline_index_compare_status"] == (
        "runtime_delta_transform_blocked"
    )
    assert dirty_diff["baseline_semantic_object_index_count"] == 0
    assert operation_plan["baseline_index_compare_available"] is False
    assert operation_plan["baseline_index_compare_status"] == (
        "runtime_delta_transform_blocked"
    )
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert head_move_plan["blocked"] is True
    assert head_move_plan["blocked_status"] == ("semantic_dirty_diff_blocked")
    assert head_move_plan["baseline_hydration_status"] == "baseline_hydrated"
    assert head_move_plan["planned_operation_count"] == 0
    assert head_move_plan["would_execute"] is False
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )
    assert _descriptor_tree_payload_keys(details) == ()
    assert _descriptor_tree_payload_keys(operation_plan) == ()


def test_meta_provider_delta_derives_baseline_semantic_index_from_oig_shape(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    baseline_ref = _baseline_ref_payload(manifest_path=manifest_path)

    index = provider_delta._baseline_semantic_object_index_from_oig(
        oig=_baseline_oig_from_semantic_objects(),
        baseline_ref=baseline_ref,
    )

    relationship_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room:doors:one_to_many:"
        "aware_demo.default.home.Door"
    )
    expected_keys = {
        "ocg_package:demo-ontology",
        "ocg:aware_demo",
        "ocg:aware_demo/node:aware_demo.default.home.Room",
        "ocg:aware_demo/node:aware_demo.default.home.RoomState",
        relationship_key,
        "ocg:aware_demo/node:aware_demo.default.home.Room.create",
        (
            "ocg:aware_demo/node:aware_demo.default.home.Room.create"
            "/function_impl:default"
        ),
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name",
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:state",
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:capacity",
    }
    assert expected_keys.issubset(set(index))
    assert index["ocg_package:demo-ontology"]["object_kind"] == (
        "object_config_graph_package"
    )
    assert index["ocg:aware_demo"]["object_kind"] == "object_config_graph"
    assert (
        index["ocg:aware_demo/node:aware_demo.default.home.Room"]["object_kind"]
        == "class"
    )
    assert index["ocg:aware_demo/node:aware_demo.default.home.Room"]["source_refs"] == (
        "home/model.aware",
    )
    assert (
        index["ocg:aware_demo/node:aware_demo.default.home.RoomState"]["object_kind"]
        == "enum"
    )
    assert index[relationship_key]["object_kind"] == "relationship"
    assert (
        index["ocg:aware_demo/node:aware_demo.default.home.Room.create"]["object_kind"]
        == "function"
    )
    function_impl_entry = index[
        "ocg:aware_demo/node:aware_demo.default.home.Room.create"
        "/function_impl:default"
    ]
    assert function_impl_entry["object_kind"] == "function_impl"
    assert function_impl_entry["parent_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.Room.create"
    )
    assert function_impl_entry["function_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.Room.create"
    )
    assert function_impl_entry["function_name"] == "create"
    assert function_impl_entry["function_impl_key"] == "default"
    assert function_impl_entry["source_refs"] == ("home/model.aware",)
    assert (
        cast(
            Mapping[str, object],
            function_impl_entry["function_impl_signature"],
        )["instruction_count"]
        == 0
    )
    name_entry = index[
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
    ]
    assert name_entry["object_kind"] == "attribute"
    assert name_entry["object_id"] == str(
        _test_uuid("baseline-room-name-attribute-object-id")
    )
    assert name_entry["owner_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.Room"
    )
    assert name_entry["source_refs"] == ("home/model.aware",)
    assert name_entry["object_instance_graph_commit_id"] == (
        "semantic-package-oig-commit"
    )
    assert name_entry["source"] == "object_instance_graph.class_instance_attributes"
    assert (
        index["ocg:aware_demo/node:aware_demo.default.home.Room/attribute:capacity"][
            "source"
        ]
        == "object_instance_graph.class_instances"
    )
    assert index["ocg:aware_demo/node:aware_demo.default.home.Room/attribute:capacity"][
        "source_refs"
    ] == ("home/model.aware",)


@pytest.mark.asyncio
async def test_meta_provider_delta_hydrates_baseline_index_from_oig_shape(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    baseline_oig = _baseline_oig_from_semantic_objects()
    expected_index = provider_delta._baseline_semantic_object_index_from_oig(
        oig=baseline_oig,
        baseline_ref=_baseline_ref_payload(manifest_path=manifest_path),
    )

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            baseline_oig,
            {
                "semantic_projection_hash": "projection-hash",
                "metadata": {"source": "oig-shape-test-hydrator"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])
    hydrated_index = cast(
        dict[str, dict[str, object]],
        hydration["baseline_semantic_object_index"],
    )

    assert hydration["status"] == "baseline_hydrated"
    assert hydration["baseline_semantic_object_index_available"] is True
    assert hydration["baseline_semantic_object_index_count"] == len(expected_index)
    assert hydrated_index == expected_index
    assert hydrated_index["ocg:aware_demo"]["source"] == (
        "object_instance_graph.class_instances"
    )

    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    runtime_delta_transform = cast(
        dict[str, object],
        dirty_diff["runtime_delta_transform"],
    )
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    mutation_plan = cast(
        dict[str, object],
        details["provider_delta_mutation_plan"],
    )

    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == (
        "meta_ocg_runtime_delta_transform_unsupported_semantic_shape"
    )
    assert dirty_diff["baseline_semantic_object_index_available"] is True
    assert dirty_diff["baseline_semantic_object_index_count"] == len(expected_index)
    assert dirty_diff["baseline_index_compare_available"] is False
    assert dirty_diff["baseline_index_compare_status"] == (
        "runtime_delta_transform_blocked"
    )
    assert runtime_delta_transform["status"] == "runtime_delta_transform_blocked"
    runtime_delta_blockers = cast(tuple[str, ...], runtime_delta_transform["blockers"])
    assert any(
        blocker.startswith("unsupported_node_type:enum:")
        for blocker in runtime_delta_blockers
    )
    assert operation_plan["semantic_dirty_diff_status"] == (
        "semantic_dirty_diff_blocked"
    )
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert typed_operation_plan["status"] == "typed_operation_plan_blocked"
    assert mutation_plan["status"] == "mutation_plan_blocked"
    assert _descriptor_tree_payload_keys(details) == ()
    assert _descriptor_tree_payload_keys(operation_plan) == ()


def test_meta_provider_delta_mutation_plan_resolves_function_attribute_receiver() -> (
    None
):
    function_semantic_key = "ocg:aware_demo/node:aware_demo.functions.Sync"
    function_config_id = "11111111-1111-4111-8111-111111111111"
    room_class_config_id = "22222222-2222-4222-8222-222222222222"
    function_operation = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": "aware.meta.ocg.provider-delta-typed-operation.v1",
        "operation_key": f"meta_ocg_provider_delta:create:function:{function_semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.function.create",
        "semantic_key": function_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "function",
        "source_entry_key": "dirty:function",
        "source_delta_key": "delta:function",
        "source_refs": ("functions/sync.aware",),
        "baseline": {},
        "current": {
            "semantic_key": function_semantic_key,
            "object_kind": "function",
            "node_type": "function",
            "node_key": "aware_demo.functions.Sync",
            "entity_id": function_config_id,
            "entity_name": "Sync",
        },
        "ocg_operation": {
            "operation": "ensure_object_config_graph_node",
            "receiver_semantic_key": "ocg:aware_demo",
            "arguments": {
                "node_key": "aware_demo.functions.Sync",
                "node_type": "function",
            },
        },
        "blocked": False,
    }
    attribute_semantic_key = f"{function_semantic_key}/attribute:payload"
    attribute_operation = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": "aware.meta.ocg.provider-delta-typed-operation.v1",
        "operation_key": (
            f"meta_ocg_provider_delta:create:attribute:{attribute_semantic_key}"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": attribute_semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_entry_key": "dirty:function-attribute",
        "source_delta_key": "delta:function",
        "source_refs": ("functions/sync.aware",),
        "baseline": {},
        "current": {
            "semantic_key": attribute_semantic_key,
            "object_kind": "attribute",
            "owner_semantic_key": function_semantic_key,
            "attribute_name": "payload",
            "attribute_signature": {
                "name": "payload",
                "position": 0,
                "function_attribute_type": "input",
                "is_identity_key": True,
                "is_required": True,
                "is_public": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
        },
        "ocg_operation": {
            "operation": "ensure_attribute_config",
            "receiver_semantic_key": function_semantic_key,
            "arguments": {
                "owner_semantic_key": function_semantic_key,
                "name": "payload",
            },
        },
        "blocked": False,
    }
    class_attribute_semantic_key = f"{function_semantic_key}/attribute:room"
    class_attribute_operation = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": "aware.meta.ocg.provider-delta-typed-operation.v1",
        "operation_key": (
            "meta_ocg_provider_delta:create:attribute:"
            f"{class_attribute_semantic_key}"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": class_attribute_semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_entry_key": "dirty:function-class-attribute",
        "source_delta_key": "delta:function",
        "source_refs": ("functions/sync.aware",),
        "baseline": {},
        "current": {
            "semantic_key": class_attribute_semantic_key,
            "object_kind": "attribute",
            "owner_semantic_key": function_semantic_key,
            "attribute_name": "room",
            "attribute_signature": {
                "name": "room",
                "position": 1,
                "function_attribute_type": "output",
                "is_required": False,
                "is_public": True,
                "type_descriptor": {
                    "kind": "class",
                    "class_config_id": room_class_config_id,
                    "target": {
                        "target_kind": "class",
                        "class_config_id": room_class_config_id,
                        "class_fqn": "aware_demo.default.home.Room",
                        "name": "Room",
                    },
                },
            },
        },
        "ocg_operation": {
            "operation": "ensure_attribute_config",
            "receiver_semantic_key": function_semantic_key,
            "arguments": {
                "owner_semantic_key": function_semantic_key,
                "name": "room",
            },
        },
        "blocked": False,
    }
    collection_attribute_semantic_key = f"{function_semantic_key}/attribute:rooms"
    collection_attribute_operation = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": "aware.meta.ocg.provider-delta-typed-operation.v1",
        "operation_key": (
            "meta_ocg_provider_delta:create:attribute:"
            f"{collection_attribute_semantic_key}"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": collection_attribute_semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_entry_key": "dirty:function-collection-attribute",
        "source_delta_key": "delta:function",
        "source_refs": ("functions/sync.aware",),
        "baseline": {},
        "current": {
            "semantic_key": collection_attribute_semantic_key,
            "object_kind": "attribute",
            "owner_semantic_key": function_semantic_key,
            "attribute_name": "rooms",
            "attribute_signature": {
                "name": "rooms",
                "position": 2,
                "function_attribute_type": "output",
                "is_required": False,
                "is_public": True,
                "type_descriptor": {
                    "kind": "collection",
                    "collection_kind": "list",
                    "child_links": (
                        {
                            "role": "element",
                            "position": 0,
                            "child_descriptor": {
                                "kind": "class",
                                "class_config_id": room_class_config_id,
                                "target": {
                                    "target_kind": "class",
                                    "class_config_id": room_class_config_id,
                                    "class_fqn": "aware_demo.default.home.Room",
                                    "name": "Room",
                                },
                            },
                        },
                    ),
                },
            },
        },
        "ocg_operation": {
            "operation": "ensure_attribute_config",
            "receiver_semantic_key": function_semantic_key,
            "arguments": {
                "owner_semantic_key": function_semantic_key,
                "name": "rooms",
            },
        },
        "blocked": False,
    }

    mutation_plan = provider_delta._provider_delta_mutation_plan(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "blocked": False,
            "typed_operation_count": 4,
            "blocked_operation_count": 0,
            "typed_operations": (
                function_operation,
                attribute_operation,
                class_attribute_operation,
                collection_attribute_operation,
            ),
            "blocked_operations": (),
        }
    )

    mutation_steps = tuple(
        cast(
            Sequence[dict[str, object]],
            mutation_plan["mutation_steps"],
        )
    )
    mutation_step_by_key = {step["semantic_key"]: step for step in mutation_steps}
    attribute_step = mutation_step_by_key[attribute_semantic_key]
    assert mutation_plan["status"] == "mutation_plan_ready"
    assert mutation_plan["blocked_mutation_step_count"] == 0
    assert attribute_step["function_ref"] == (
        META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF
    )
    assert attribute_step["receiver_semantic_key"] == function_semantic_key
    assert attribute_step["receiver_source"] == "semantic_node_contained_entity"
    assert attribute_step["receiver_entity_kind"] == "function_config"
    assert attribute_step["receiver_entity_id"] == function_config_id
    assert attribute_step["dependencies"] == (function_semantic_key,)
    arguments = cast(dict[str, object], attribute_step["arguments"])
    assert arguments["name"] == "payload"
    assert arguments["primitive_base_type"] == "string"
    assert arguments["type"] == "input"
    assert arguments["is_identity_key"] is True
    class_attribute_step = mutation_step_by_key[class_attribute_semantic_key]
    assert class_attribute_step["function_ref"] == (
        META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF
    )
    class_arguments = cast(dict[str, object], class_attribute_step["arguments"])
    assert class_arguments["name"] == "room"
    assert class_arguments["type_class_config_id"] == room_class_config_id
    assert class_arguments["type"] == "output"
    class_resolution = cast(
        dict[str, object],
        class_attribute_step["attribute_descriptor_resolution"],
    )
    assert class_resolution["descriptor_kind"] == "class"
    assert class_resolution["method_descriptor_kind"] == "class"
    assert (
        cast(dict[str, object], class_resolution["target"])["class_fqn"]
        == "aware_demo.default.home.Room"
    )
    collection_attribute_step = mutation_step_by_key[collection_attribute_semantic_key]
    assert collection_attribute_step["function_ref"] == (
        provider_delta.META_PROVIDER_DELTA_FUNCTION_CONFIG_ADD_COLLECTION_ATTRIBUTE_FUNCTION_REF
    )
    collection_arguments = cast(
        dict[str, object],
        collection_attribute_step["arguments"],
    )
    assert collection_arguments["name"] == "rooms"
    assert collection_arguments["type"] == "output"
    assert collection_arguments["collection_kind"] == "list"
    assert collection_arguments["element_descriptor_kind"] == "class"
    assert collection_arguments["element_type_class_config_id"] == (
        room_class_config_id
    )
    assert collection_arguments["execution_wired"] is False
    collection_resolution = cast(
        dict[str, object],
        collection_attribute_step["attribute_descriptor_resolution"],
    )
    assert collection_resolution["method_descriptor_kind"] == "collection"
    assert collection_resolution["element_descriptor_kind"] == "class"
    assert collection_resolution["is_collection"] is True
    assert _descriptor_tree_payload_keys(mutation_plan) == ()


def test_meta_provider_delta_mutation_plan_binds_class_attribute_descriptor() -> None:
    owner_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    owner_operation = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": "aware.meta.ocg.provider-delta-typed-operation.v1",
        "operation_key": f"meta_ocg_provider_delta:create:class:{owner_semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.class.create",
        "semantic_key": owner_semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_entry_key": "dirty:class",
        "source_delta_key": "delta:class",
        "source_refs": ("home/model.aware",),
        "baseline": {},
        "current": {
            "semantic_key": owner_semantic_key,
            "object_kind": "class",
            "node_type": "class",
            "node_key": "aware_demo.default.home.Room",
            "entity_id": "room-class-config-id",
            "entity_name": "Room",
        },
        "ocg_operation": {
            "operation": "ensure_object_config_graph_node",
            "receiver_semantic_key": "ocg:aware_demo",
            "arguments": {
                "node_key": "aware_demo.default.home.Room",
                "node_type": "class",
            },
        },
        "blocked": False,
    }
    attribute_semantic_key = f"{owner_semantic_key}/attribute:primaryDoor"
    attribute_operation = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": "aware.meta.ocg.provider-delta-typed-operation.v1",
        "operation_key": (
            f"meta_ocg_provider_delta:create:attribute:{attribute_semantic_key}"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": attribute_semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_entry_key": "dirty:class-attribute",
        "source_delta_key": "delta:class",
        "source_refs": ("home/model.aware",),
        "baseline": {},
        "current": {
            "semantic_key": attribute_semantic_key,
            "object_kind": "attribute",
            "owner_semantic_key": owner_semantic_key,
            "attribute_name": "primaryDoor",
            "attribute_signature": {
                "name": "primaryDoor",
                "position": 2,
                "is_required": False,
                "is_public": True,
                "type_descriptor": {
                    "kind": "class",
                    "class_config_id": "door-class-config-id",
                    "target": {
                        "target_kind": "class",
                        "class_config_id": "door-class-config-id",
                        "class_fqn": "aware_demo.default.home.Door",
                        "name": "Door",
                    },
                },
            },
        },
        "ocg_operation": {
            "operation": "ensure_attribute_config",
            "receiver_semantic_key": owner_semantic_key,
            "arguments": {
                "owner_semantic_key": owner_semantic_key,
                "name": "primaryDoor",
            },
        },
        "blocked": False,
    }

    mutation_plan = provider_delta._provider_delta_mutation_plan(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "blocked": False,
            "typed_operation_count": 2,
            "blocked_operation_count": 0,
            "typed_operations": (owner_operation, attribute_operation),
            "blocked_operations": (),
        }
    )

    mutation_steps = tuple(
        cast(
            Sequence[dict[str, object]],
            mutation_plan["mutation_steps"],
        )
    )
    mutation_step_by_key = {step["semantic_key"]: step for step in mutation_steps}
    attribute_step = mutation_step_by_key[attribute_semantic_key]
    assert mutation_plan["status"] == "mutation_plan_ready"
    assert mutation_plan["blocked_mutation_step_count"] == 0
    assert attribute_step["function_ref"] == (
        META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF
    )
    assert attribute_step["receiver_entity_kind"] == "class_config"
    arguments = cast(dict[str, object], attribute_step["arguments"])
    assert arguments["name"] == "primaryDoor"
    assert arguments["type_class_config_id"] == "door-class-config-id"
    resolution = cast(
        dict[str, object],
        attribute_step["attribute_descriptor_resolution"],
    )
    assert resolution["descriptor_kind"] == "class"
    assert resolution["method_descriptor_kind"] == "class"
    assert (
        cast(dict[str, object], resolution["target"])["class_fqn"]
        == "aware_demo.default.home.Door"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_blocks_path_hints_without_workspace_code_delta(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
        include_code_package_delta=False,
    )
    baseline_oig = _baseline_oig_from_semantic_objects()

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            baseline_oig,
            {
                "semantic_projection_hash": "projection-hash",
                "metadata": {"source": "path-hints-are-diagnostics-test"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    runtime_delta_transform = cast(
        dict[str, object],
        dirty_diff["runtime_delta_transform"],
    )

    assert result["status"] == "succeeded"
    assert details["source_files"] == ()
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == "meta_ocg_runtime_delta_requires_code_package_delta"
    assert dirty_diff["baseline_semantic_object_index_available"] is True
    assert runtime_delta_transform["status"] == "runtime_delta_transform_blocked"
    assert runtime_delta_transform["blockers"] == ("code_package_delta_missing",)


@pytest.mark.asyncio
async def test_meta_provider_delta_dirty_diff_ready_for_simple_runtime_delta(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
        code_delta_content_text="class Room { name String }",
    )
    baseline_index = {
        "ocg_package:demo-ontology": {
            "object_id": "baseline-package-object-id",
            "object_kind": "object_config_graph_package",
        },
        "ocg:aware_demo": {
            "object_id": "baseline-graph-object-id",
            "object_kind": "object_config_graph",
        },
    }

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[SimpleNamespace, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            SimpleNamespace(
                class_instances=[object()], class_instance_relationships=[]
            ),
            {
                "semantic_projection_hash": "projection-hash",
                "baseline_semantic_object_index": baseline_index,
                "metadata": {"source": "simple-runtime-delta-test"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    runtime_delta_transform = cast(
        dict[str, object],
        dirty_diff["runtime_delta_transform"],
    )
    dirty_entries = cast(
        tuple[dict[str, object], ...],
        dirty_diff["semantic_dirty_entries"],
    )
    dirty_by_key = {entry["semantic_key"]: entry for entry in dirty_entries}

    assert result["status"] == "succeeded"
    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert dirty_diff["reason"] == "meta_ocg_dirty_diff_ready"
    assert dirty_diff["compare_mode"] == (
        "hydrated_baseline_index_runtime_delta_transform"
    )
    assert runtime_delta_transform["status"] == "runtime_delta_transform_ready"
    assert runtime_delta_transform["current_runtime_semantic_object_index_keys"] == (
        "ocg:aware_demo",
        "ocg:aware_demo/node:aware_demo.home.Room",
        "ocg:aware_demo/node:aware_demo.home.Room/attribute:name",
        "ocg_package:demo-ontology",
    )
    assert dirty_diff["dirty_entry_count"] == 4
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "create": 2,
        "update": 2,
    }
    assert dirty_by_key["ocg:aware_demo"]["baseline_compare_operation"] == "update"
    assert (
        dirty_by_key["ocg:aware_demo/node:aware_demo.home.Room"][
            "baseline_compare_operation"
        ]
        == "create"
    )
    attribute_entry = dirty_by_key[
        "ocg:aware_demo/node:aware_demo.home.Room/attribute:name"
    ]
    assert attribute_entry["baseline_compare_operation"] == "create"
    assert attribute_entry["parent_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.home.Room"
    )
    assert head_move_plan["status"] == "head_move_plan_ready"
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["blocked_operation_count"] == 0


@pytest.mark.asyncio
async def test_meta_provider_delta_dirty_diff_reports_stale_attribute(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
        code_delta_content_text="class Room { name String }",
    )
    room_key = "ocg:aware_demo/node:aware_demo.home.Room"
    state_key = f"{room_key}/attribute:state"
    baseline_index = {
        "ocg_package:demo-ontology": {
            "object_id": "baseline-package-object-id",
            "object_kind": "object_config_graph_package",
            "source_refs": ("aware.toml",),
        },
        "ocg:aware_demo": {
            "object_id": "baseline-graph-object-id",
            "object_kind": "object_config_graph",
            "source_refs": ("home/model.aware",),
        },
        room_key: {
            "object_id": "baseline-room-class-object-id",
            "object_kind": "class",
            "source_refs": ("home/model.aware",),
        },
        f"{room_key}/attribute:name": {
            "object_id": "baseline-room-name-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": room_key,
            "attribute_name": "name",
            "source_refs": ("home/model.aware",),
        },
        state_key: {
            "object_id": "baseline-room-state-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": room_key,
            "attribute_name": "state",
            "source_refs": ("home/model.aware",),
        },
    }

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[SimpleNamespace, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            SimpleNamespace(
                class_instances=[object()], class_instance_relationships=[]
            ),
            {
                "semantic_projection_hash": "projection-hash",
                "baseline_semantic_object_index": baseline_index,
                "metadata": {"source": "stale-attribute-test"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    dirty_entries = cast(
        tuple[dict[str, object], ...],
        dirty_diff["semantic_dirty_entries"],
    )
    dirty_by_key = {entry["semantic_key"]: entry for entry in dirty_entries}
    typed_operations = cast(
        tuple[dict[str, object], ...],
        typed_operation_plan["typed_operations"],
    )
    typed_by_key = {
        operation["semantic_key"]: operation for operation in typed_operations
    }

    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert dirty_diff["dirty_entry_count"] == 5
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "delete": 1,
        "update": 4,
    }
    assert dirty_diff["stale_semantic_keys"] == (state_key,)
    assert result["stale_semantic_keys"] == (state_key,)
    stale_entry = dirty_by_key[state_key]
    assert stale_entry["baseline_compare_operation"] == "delete"
    assert stale_entry["dirty_operation"] == "attribute_delete"
    assert stale_entry["source_refs"] == ("home/model.aware",)
    assert stale_entry["baseline_object_id"] == (
        "baseline-room-state-attribute-object-id"
    )
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["blocked_operation_count"] == 0
    stale_operation = typed_by_key[state_key]
    stale_ocg_operation = cast(dict[str, object], stale_operation["ocg_operation"])
    assert stale_operation["operation_family"] == "delete"
    assert stale_ocg_operation["operation"] == "delete_attribute_config"
    assert stale_operation["would_execute"] is False


@pytest.mark.asyncio
async def test_meta_provider_delta_dirty_diff_skips_ambiguous_stale_source_refs(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
        code_delta_content_text="class Room { name String }",
    )
    room_key = "ocg:aware_demo/node:aware_demo.home.Room"
    state_key = f"{room_key}/attribute:state"
    broad_source_refs = ("home/model.aware", "home/other.aware")
    baseline_index = {
        "ocg_package:demo-ontology": {
            "object_id": "baseline-package-object-id",
            "object_kind": "object_config_graph_package",
            "source_refs": ("aware.toml",),
        },
        "ocg:aware_demo": {
            "object_id": "baseline-graph-object-id",
            "object_kind": "object_config_graph",
            "source_refs": broad_source_refs,
        },
        room_key: {
            "object_id": "baseline-room-class-object-id",
            "object_kind": "class",
            "source_refs": ("home/model.aware",),
        },
        f"{room_key}/attribute:name": {
            "object_id": "baseline-room-name-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": room_key,
            "attribute_name": "name",
            "source_refs": ("home/model.aware",),
        },
        state_key: {
            "object_id": "baseline-room-state-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": room_key,
            "attribute_name": "state",
            "source_refs": broad_source_refs,
        },
    }

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[SimpleNamespace, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            SimpleNamespace(
                class_instances=[object()], class_instance_relationships=[]
            ),
            {
                "semantic_projection_hash": "projection-hash",
                "baseline_semantic_object_index": baseline_index,
                "metadata": {"source": "ambiguous-source-ref-stale-test"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    dirty_entries = cast(
        tuple[dict[str, object], ...],
        dirty_diff["semantic_dirty_entries"],
    )

    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert dirty_diff["dirty_entry_count"] == 4
    assert dirty_diff["baseline_compare_operation_counts"] == {"update": 4}
    assert dirty_diff["stale_semantic_keys"] == ()
    assert state_key not in {entry["semantic_key"] for entry in dirty_entries}
    assert result["stale_semantic_keys"] == ()


@pytest.mark.asyncio
async def test_meta_provider_delta_hydrates_baseline_via_request_hydrator(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[SimpleNamespace, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            SimpleNamespace(
                class_instances=[object(), object(), object()],
                class_instance_relationships=[object()],
            ),
            {
                "semantic_projection_hash": "projection-hash",
                "baseline_semantic_object_index": (
                    _baseline_semantic_object_index_payload()
                ),
                "metadata": {"source": "test-hydrator"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    hydration = cast(dict[str, object], preflight["baseline_hydration_preflight"])

    assert preflight["status"] == "baseline_commit_refs_available"
    assert preflight["did_hydrate_baseline"] is True
    assert preflight["did_compare_against_current_delta"] is False
    assert preflight["semantic_dirty_diff_available"] is False
    assert preflight["semantic_dirty_diff_status"] == "semantic_dirty_diff_blocked"
    assert preflight["semantic_dirty_diff_reason"] == (
        "meta_ocg_runtime_delta_transform_unsupported_semantic_shape"
    )
    assert hydration["status"] == "baseline_hydrated"
    assert hydration["source"] == "request.baseline_oig_hydrator"
    assert hydration["semantic_branch_id"] == "semantic-branch-id"
    assert hydration["semantic_projection_name"] == "ObjectConfigGraphPackage"
    assert hydration["semantic_projection_hash"] == "projection-hash"
    assert hydration["semantic_package_commit_id"] == "semantic-package-commit-id"
    assert hydration["semantic_object_instance_graph_commit_id"] == (
        "semantic-package-oig-commit"
    )
    assert hydration["semantic_root_object_instance_graph_commit_id"] == (
        "semantic-root-oig-commit"
    )
    assert hydration["object_counts"] == {
        "class_instances": 3,
        "class_instance_relationships": 1,
    }
    assert hydration["baseline_semantic_object_index_available"] is True
    assert hydration["baseline_semantic_object_index_count"] == len(
        _baseline_semantic_object_index_payload()
    )
    payload_index = cast(
        dict[str, dict[str, object]],
        hydration["baseline_semantic_object_index"],
    )
    assert payload_index["ocg:aware_demo"]["source"] == (
        "hydrator_payload.baseline_semantic_object_index"
    )
    assert hydration["class_instance_count"] == 3
    assert hydration["class_instance_relationship_count"] == 1
    assert hydration["would_persist"] is False
    assert hydration["did_persist"] is False
    assert hydration["did_hydrate"] is True
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    runtime_delta_transform = cast(
        dict[str, object],
        dirty_diff["runtime_delta_transform"],
    )
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )

    assert dirty_diff["contract_version"] == "aware.meta.ocg.semantic-dirty-diff.v1"
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == (
        "meta_ocg_runtime_delta_transform_unsupported_semantic_shape"
    )
    assert dirty_diff["available"] is False
    assert dirty_diff["blocked"] is True
    assert dirty_diff["baseline_hydration_status"] == "baseline_hydrated"
    assert dirty_diff["baseline_branch_id"] == "semantic-branch-id"
    assert dirty_diff["baseline_projection_name"] == "ObjectConfigGraphPackage"
    assert dirty_diff["baseline_projection_hash"] == "projection-hash"
    assert dirty_diff["baseline_semantic_object_instance_graph_commit_id"] == (
        "semantic-package-oig-commit"
    )
    assert dirty_diff["baseline_object_counts"] == {
        "class_instances": 3,
        "class_instance_relationships": 1,
    }
    assert dirty_diff["baseline_semantic_object_index_available"] is True
    assert dirty_diff["baseline_semantic_object_index_count"] == len(
        _baseline_semantic_object_index_payload()
    )
    assert dirty_diff["baseline_index_compare_available"] is False
    assert dirty_diff["baseline_index_compare_status"] == (
        "runtime_delta_transform_blocked"
    )
    assert dirty_diff["runtime_delta_transform_status"] == (
        "runtime_delta_transform_blocked"
    )
    runtime_delta_blockers = cast(tuple[str, ...], runtime_delta_transform["blockers"])
    assert any(
        blocker.startswith("unsupported_node_type:enum:")
        for blocker in runtime_delta_blockers
    )
    assert dirty_diff["would_execute"] is False
    assert dirty_diff["would_persist"] is False
    assert dirty_diff["did_persist"] is False
    assert operation_plan["semantic_dirty_diff"] == dirty_diff
    assert operation_plan["semantic_dirty_diff_available"] is False
    assert operation_plan["baseline_index_compare_available"] is False
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )
    assert preflight["semantic_dirty_diff_status"] == "semantic_dirty_diff_blocked"
    assert preflight["baseline_index_compare_available"] is False
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert head_move_plan["blocked"] is True
    return

    dirty_entries = cast(
        tuple[dict[str, object], ...],
        dirty_diff["semantic_dirty_entries"],
    )
    operations = {entry["dirty_operation"] for entry in dirty_entries}
    attribute_names = {
        entry.get("attribute_name")
        for entry in dirty_entries
        if entry["ontology_subject_kind"] == "attribute"
    }
    assert "object_config_graph_package_update" in operations
    assert "object_config_graph_update" in operations
    assert "class_update" in operations
    assert "class_create" in operations
    assert "enum_create" in operations
    assert "relationship_create" in operations
    assert "attribute_update" in operations
    assert "attribute_create" in operations
    assert {"label", "name", "state", "doors"}.issubset(attribute_names)
    matched_entries = {
        entry["semantic_key"]: entry
        for entry in dirty_entries
        if entry["baseline_object_matched"] is True
    }
    assert matched_entries["ocg:aware_demo"]["baseline_object_id"] == (
        "baseline-graph-object-id"
    )
    assert (
        matched_entries[
            "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
        ]["baseline_object_id"]
        == "baseline-room-name-attribute-object-id"
    )
    dirty_entry_kind_counts = cast(
        dict[str, int],
        dirty_diff["dirty_entry_kind_counts"],
    )
    assert dirty_entry_kind_counts["attribute"] >= 4
    assert dirty_entry_kind_counts["class"] == 2
    assert dirty_entry_kind_counts["enum"] == 1
    assert dirty_entry_kind_counts["object_config_graph"] == 1
    assert dirty_entry_kind_counts["object_config_graph_package"] == 1
    assert dirty_entry_kind_counts["relationship"] == 1
    baseline_compare_operation_counts = cast(
        dict[str, int],
        dirty_diff["baseline_compare_operation_counts"],
    )
    assert baseline_compare_operation_counts["update"] >= 4
    assert baseline_compare_operation_counts["create"] >= 4
    assert operation_plan["semantic_dirty_diff"] == dirty_diff
    assert operation_plan["semantic_dirty_diff_available"] is True
    assert operation_plan["baseline_index_compare_available"] is True
    assert operation_plan["baseline_index_compare_status"] == (
        "baseline_index_compared"
    )
    assert operation_plan["semantic_dirty_entry_count"] == len(dirty_entries)
    assert preflight["semantic_dirty_entry_count"] == len(dirty_entries)
    assert preflight["baseline_index_compare_available"] is True
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    planned_operations = tuple(
        cast(
            Sequence[dict[str, object]],
            head_move_plan["planned_operations"],
        )
    )
    assert head_move_plan["contract_version"] == (
        "aware.workspace.semantic-materialization.provider-delta-head-move.v1"
    )
    assert head_move_plan["status"] == "head_move_plan_ready"
    assert head_move_plan["available"] is True
    assert head_move_plan["blocked"] is False
    assert head_move_plan["baseline_index_compare_status"] == (
        "baseline_index_compared"
    )
    assert head_move_plan["dirty_entry_count"] == len(dirty_entries)
    assert head_move_plan["planned_operation_count"] == len(planned_operations)
    assert head_move_plan["planned_operation_count"] == len(dirty_entries)
    assert {operation["operation_family"] for operation in planned_operations} == {
        "create",
        "update",
    }
    assert head_move_plan["would_execute"] is False
    assert head_move_plan["would_persist"] is False
    assert head_move_plan["execution_wired"] is False
    assert operation_plan["provider_delta_head_move_status"] == ("head_move_plan_ready")
    assert operation_plan["provider_delta_head_move_planned_operation_count"] == (
        len(planned_operations)
    )


def test_meta_provider_delta_operation_plan_accepts_function_node_delta() -> None:
    function_delta_key = (
        "aware_meta.object_config_graph_node.upsert:"
        "ocg:aware_demo/node:aware_demo.functions.Sync"
    )
    function_delta = _FakeEvidence(
        {
            "delta_key": function_delta_key,
            "semantic_key": "ocg:aware_demo/node:aware_demo.functions.Sync",
            "verb": "upsert",
            "subject_type": "aware_meta.ObjectConfigGraphNode",
            "source": "aware_meta.semantic_analysis",
            "source_refs": ("functions/sync.aware",),
            "after_payload": {
                "graph_semantic_key": "ocg:aware_demo",
                "node_key": "aware_demo.functions.Sync",
                "node_type": "function",
            },
            "metadata": {
                "semantic_truth_graph": "runtime_ocg",
                "runtime_node_type": "function",
            },
        }
    )
    function_event = _FakeEvidence(
        {
            "event_key": "aware_meta.object_config_graph_node.upserted",
            "semantic_key": "ocg:aware_demo/node:aware_demo.functions.Sync",
            "verb": "upsert",
            "subject_type": "aware_meta.ObjectConfigGraphNode",
            "source": "aware_meta.semantic_analysis",
            "source_refs": ("functions/sync.aware",),
            "delta_keys": (function_delta_key,),
            "payload": {
                "graph_semantic_key": "ocg:aware_demo",
                "node_key": "aware_demo.functions.Sync",
                "node_type": "function",
            },
            "metadata": {
                "semantic_truth_graph": "runtime_ocg",
                "runtime_node_type": "function",
            },
        }
    )
    analysis = cast(
        MetaOcgSemanticAnalysisResult,
        cast(
            object,
            SimpleNamespace(
                change_preview=SimpleNamespace(
                    changed_source_files=("functions/sync.aware",),
                    affected_object_config_graph_keys=("ocg:aware_demo",),
                    affected_node_keys=(
                        "ocg:aware_demo/node:aware_demo.functions.Sync",
                    ),
                    required_materializations=("meta_object_config_graph_plan",),
                    graph_count=1,
                    node_count=1,
                    class_count=0,
                    enum_count=0,
                    function_count=1,
                    relationship_count=0,
                    semantic_deltas=(function_delta,),
                    semantic_events=(function_event,),
                )
            ),
        ),
    )

    function_call_plans = provider_delta._function_call_plans_from_analysis(
        analysis=analysis,
    )
    operation_plan = provider_delta._operation_plan_from_analysis(
        analysis=analysis,
        current_delta_fingerprint="sha256:function",
        function_call_plans=function_call_plans,
    )

    assert operation_plan["function_count"] == 1
    assert operation_plan["operation_count"] == 1
    semantic_deltas = cast(
        tuple[dict[str, object], ...],
        operation_plan["semantic_deltas"],
    )
    semantic_delta_payload = cast(
        dict[str, object], semantic_deltas[0]["after_payload"]
    )
    assert semantic_delta_payload["node_type"] == "function"
    function_call_plan_payloads = cast(
        tuple[dict[str, object], ...],
        operation_plan["semantic_function_call_plans"],
    )
    function_call_plan = function_call_plan_payloads[0]
    assert function_call_plan["function_ref"] == META_OCG_CREATE_NODE_FUNCTION_REF
    assert function_call_plan["arguments"] == {
        "type": "function",
        "node_key": "aware_demo.functions.Sync",
    }
    assert function_call_plan["receiver_semantic_key"] == "ocg:aware_demo"


@pytest.mark.asyncio
async def test_meta_provider_delta_blocks_dirty_diff_for_delete_delta(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    request = _provider_delta_request(
        manifest_path=manifest_path,
        change_kind="delete",
        include_baseline_refs=True,
    )
    baseline_oig = _baseline_oig_from_semantic_objects(
        include_layouts=False,
        include_function_impl_source_ref=False,
    )

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            baseline_oig,
            {
                "semantic_projection_hash": "projection-hash",
                "metadata": {"source": "delete-delta-test"},
            },
        )

    request = SimpleNamespace(
        package=request.package,
        semantic_contract=request.semantic_contract,
        current_delta_fingerprint=request.current_delta_fingerprint,
        delta_cause_hints=request.delta_cause_hints,
        code_package_delta=request.code_package_delta,
        previous_materialization_evidence=request.previous_materialization_evidence,
        baseline_ref=request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    commit_ref_contract = cast(dict[str, object], result["commit_ref_contract"])
    bundle_package = cast(dict[str, object], result["bundle_package"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    runtime_delta_transform = cast(
        dict[str, object],
        dirty_diff["runtime_delta_transform"],
    )

    assert result["status"] == "succeeded"
    assert result["fallback_reason"] is None
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == (
        "meta_ocg_runtime_delta_delete_requires_baseline_source_refs"
    )
    assert runtime_delta_transform["blockers"] == (
        "baseline_source_refs_missing_for_delete_path:home/model.aware",
    )
    assert result["applied_semantic_keys"] == ()
    assert commit_ref_contract["status"] == "missing_durable_refs"
    assert bundle_package["source_code_package_id"] == "source-code-package-id"
    assert details["production_execution_wired"] is False


@pytest.mark.asyncio
async def test_meta_provider_delta_delete_delta_reports_stale_objects(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        change_kind="delete",
        include_baseline_refs=True,
    )
    room_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    function_key = f"{room_key}.rename"
    function_impl_key = f"{function_key}/function_impl:default"
    name_key = f"{room_key}/attribute:name"
    state_key = f"{room_key}/attribute:state"
    baseline_index = {
        "ocg_package:demo-ontology": {
            "object_id": "baseline-package-object-id",
            "object_kind": "object_config_graph_package",
            "source_refs": ("aware.toml",),
        },
        "ocg:aware_demo": {
            "object_id": "baseline-graph-object-id",
            "object_kind": "object_config_graph",
            "source_refs": ("home/model.aware",),
        },
        room_key: {
            "object_id": "baseline-room-class-object-id",
            "object_kind": "class",
            "source_refs": ("home/model.aware",),
        },
        name_key: {
            "object_id": "baseline-room-name-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": room_key,
            "attribute_name": "name",
            "source_refs": ("home/model.aware",),
        },
        state_key: {
            "object_id": "baseline-room-state-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": room_key,
            "attribute_name": "state",
            "source_refs": ("home/model.aware",),
        },
        function_impl_key: {
            "object_id": "baseline-room-rename-function-impl-object-id",
            "object_kind": "function_impl",
            "parent_semantic_key": function_key,
            "owner_semantic_key": room_key,
            "function_semantic_key": function_key,
            "function_name": "rename",
            "function_impl_key": "default",
            "function_impl_kind": "instruction_body",
            "source_refs": ("home/model.aware",),
            "function_impl_signature": {
                "instruction_count": 1,
                "instruction_summaries": ("set name = new_name",),
            },
        },
    }

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[SimpleNamespace, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"
        return (
            SimpleNamespace(
                class_instances=[object()], class_instance_relationships=[]
            ),
            {
                "semantic_projection_hash": "projection-hash",
                "baseline_semantic_object_index": baseline_index,
                "metadata": {"source": "delete-stale-test"},
            },
        )

    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    runtime_delta_transform = cast(
        dict[str, object],
        dirty_diff["runtime_delta_transform"],
    )
    dirty_entries = cast(
        tuple[dict[str, object], ...],
        dirty_diff["semantic_dirty_entries"],
    )
    typed_operations = cast(
        tuple[dict[str, object], ...],
        typed_operation_plan["typed_operations"],
    )

    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert runtime_delta_transform["status"] == "runtime_delta_transform_ready"
    assert runtime_delta_transform["deleted_runtime_source_refs"] == (
        "home/model.aware",
    )
    assert runtime_delta_transform["current_runtime_semantic_object_index"] == {}
    assert dirty_diff["dirty_entry_count"] == 4
    assert dirty_diff["baseline_compare_operation_counts"] == {"delete": 4}
    assert dirty_diff["stale_semantic_keys"] == (
        room_key,
        function_impl_key,
        name_key,
        state_key,
    )
    assert result["stale_semantic_keys"] == (
        room_key,
        function_impl_key,
        name_key,
        state_key,
    )
    assert {entry["dirty_operation"] for entry in dirty_entries} == {
        "attribute_delete",
        "class_delete",
        "function_impl_delete",
    }
    assert head_move_plan["status"] == "head_move_plan_ready"
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert {operation["operation_family"] for operation in typed_operations} == {
        "delete"
    }
    delete_ocg_operations = {
        cast(dict[str, object], operation["ocg_operation"])["operation"]
        for operation in typed_operations
    }
    assert delete_ocg_operations == {
        "delete_attribute_config",
        "delete_function_impl",
        "delete_object_config_graph_node",
    }


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_attribute_update_from_aware_delta(
    tmp_path: Path,
) -> None:
    manifest_path = _write_meta_attribute_update_delta_fixture(tmp_path)
    base_request = _provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name"
    )
    current_index = _attribute_update_current_runtime_index(request=base_request)
    baseline_index = _baseline_semantic_object_index_for_attribute_update(
        current_index=current_index,
        attribute_semantic_key=attribute_semantic_key,
    )
    branch_id = _test_uuid("attribute-update-provider-delta-branch")
    actor_id = _test_uuid("attribute-update-provider-delta-actor")
    package_projection_hash = "sha256:test:ObjectConfigGraphPackage"
    root_projection_hash = "sha256:test:ObjectConfigGraph"
    baseline_domain_commit_id = _test_uuid(
        "attribute-update-provider-delta-baseline-domain-head"
    )
    baseline_package_oig_commit_id = _test_uuid(
        "attribute-update-provider-delta-baseline-package-oig"
    )
    baseline_root_oig_commit_id = _test_uuid(
        "attribute-update-provider-delta-baseline-root-oig"
    )
    next_domain_commit_id = _test_uuid(
        "attribute-update-provider-delta-next-domain-head"
    )
    baseline_ref = {
        **_baseline_ref_payload(manifest_path=manifest_path),
        "semantic_branch_id": str(branch_id),
        "semantic_package_commit_id": str(baseline_domain_commit_id),
        "semantic_object_instance_graph_commit_id": (
            str(baseline_package_oig_commit_id)
        ),
        "semantic_root_object_instance_graph_commit_id": (
            str(baseline_root_oig_commit_id)
        ),
    }
    _ = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(
            MetaRuntimePackageIndexEntry(
                module_id="demo",
                package_name="demo-ontology",
                fqn_prefix="aware_demo",
                manifest_path=manifest_path,
            ),
        ),
    )

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> dict[str, object]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == str(branch_id)
        return {
            "semantic_projection_hash": package_projection_hash,
            "object_counts": {
                "class_instances": len(baseline_index),
                "class_instance_relationships": 0,
            },
            "baseline_semantic_object_index": baseline_index,
            "metadata": {"domain_commit_id": str(baseline_domain_commit_id)},
        }

    runtime = _RecordingProviderDeltaOntologyRuntime()
    graph_runtime_context = _provider_delta_ontology_invocation_runtime_context()
    graph_runtime_context.projection_hash_by_name = {
        "ObjectConfigGraph": root_projection_hash,
        "ObjectConfigGraphPackage": package_projection_hash,
    }
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            baseline_ref["source_object_instance_graph_commit_id"]
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            str(baseline_package_oig_commit_id)
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            str(baseline_root_oig_commit_id)
        ),
        baseline_oig_hydrator=baseline_oig_hydrator,
        execute_provider_delta_materialization=True,
        provider_delta_author_id=str(actor_id),
        semantic_branch_id=str(branch_id),
        semantic_projection_hash=package_projection_hash,
        provider_delta_ontology_head_commit_id=str(baseline_domain_commit_id),
        provider_delta_oig_commit_id=str(next_domain_commit_id),
        workspace_root=str(tmp_path),
        context={
            "runtime": runtime,
            "aware_meta.graph_runtime_context": graph_runtime_context,
        },
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    ontology_execution_plan = cast(
        dict[str, object],
        operation_plan["provider_delta_ontology_execution_plan"],
    )
    capability_matrix = cast(
        dict[str, object],
        details["provider_delta_functioncall_capability_matrix"],
    )
    execute_preflight = cast(
        dict[str, object],
        details["provider_delta_execute_flag_preflight"],
    )
    commit_receipt = cast(
        dict[str, object],
        details["provider_delta_oig_commit_receipt"],
    )
    head_move_applied_receipt = cast(
        dict[str, object],
        details["provider_delta_head_move_applied_receipt"],
    )
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    semantic_commit_evidence = cast(
        dict[str, object],
        details["provider_delta_semantic_commit_evidence"],
    )

    assert result["fallback_reason"] is None
    assert result["status"] == "succeeded"
    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert dirty_diff["baseline_index_compare_status"] == "baseline_index_compared"
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "noop": 3,
        "update": 1,
    }
    dirty_entries = cast(
        Sequence[dict[str, object]],
        dirty_diff["semantic_dirty_entries"],
    )
    attribute_entry = next(
        entry
        for entry in dirty_entries
        if entry["semantic_key"] == attribute_semantic_key
    )
    assert attribute_entry["dirty_operation"] == "attribute_update"
    assert attribute_entry["baseline_object_id"] == (
        baseline_index[attribute_semantic_key]["object_id"]
    )

    typed_operations = cast(
        Sequence[dict[str, object]],
        typed_operation_plan["typed_operations"],
    )
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert len(typed_operations) == 1
    attribute_operation = typed_operations[0]
    assert attribute_operation["semantic_key"] == attribute_semantic_key
    assert attribute_operation["provider_operation_type"] == (
        "meta_ocg.attribute.update"
    )
    assert attribute_operation["readiness_case_key"] == (
        "attribute.update.primitive_type"
    )
    assert attribute_operation["source_projection_policy"] == "segment_ready"
    assert attribute_operation["source_projection_status"] == "ready"
    assert (
        cast(dict[str, object], attribute_operation["baseline"])["object_id"]
        == baseline_index[attribute_semantic_key]["object_id"]
    )

    assert ontology_execution_plan["status"] == "ontology_execution_plan_ready"
    intents = cast(
        Sequence[dict[str, object]],
        ontology_execution_plan["invocation_intents"],
    )
    assert len(intents) == 1
    intent = intents[0]
    assert intent["owner_class_name"] == "AttributeConfig"
    assert intent["function_name"] == "update_primitive"
    assert intent["function_ref"] == ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF
    assert (
        intent["target_object_id"]
        == baseline_index[attribute_semantic_key]["object_id"]
    )
    intent_kwargs = cast(dict[str, object], intent["kwargs"])
    assert intent_kwargs["primitive_base_type"] == "integer"

    assert capability_matrix["coverage_status"] == "all_operations_executable"
    assert capability_matrix["execution_allowed"] is True
    assert execute_preflight["status"] == "execute_flag_preflight_ready"
    assert execute_preflight["blockers"] == ()
    assert commit_receipt["status"] == "execute_flag_commit_applied"
    assert commit_receipt["reason"] == (
        "meta_ocg_provider_delta_ontology_function_call_commit_applied"
    )
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == ("ontology_function_call_execution_applied")
    assert len(runtime.requests) == 1
    assert runtime.requests[0].call_target is MetaGraphCallTarget.instance
    assert runtime.requests[0].target_object_id == UUID(
        str(baseline_index[attribute_semantic_key]["object_id"])
    )
    assert runtime.requests[0].function_id == _test_uuid(
        "AttributeConfig.update_primitive.function"
    )
    assert runtime.requests[0].expected_head_commit_id == baseline_domain_commit_id
    assert runtime.requests[0].kwargs["primitive_base_type"] == "integer"

    assert head_move_applied_receipt["status"] == ("head_move_applied_receipt_ready")
    assert head_move_applied_receipt["dirty_status_after_head_move"] == "clean"
    head_refs = cast(dict[str, object], head_move_applied_receipt["head_refs"])
    assert head_refs["semantic_projection_hash"] == root_projection_hash
    assert cast(dict[str, object], head_refs["details"])["projection_hash"] == (
        root_projection_hash
    )
    assert operation_execution["status"] == "executed"
    assert operation_execution["did_execute"] is True
    assert semantic_commit_evidence["status"] == "semantic_commit_evidence_ready"
    patched_index = load_meta_runtime_package_projection_index(aware_root=tmp_path)
    assert patched_index is not None
    indexed_attribute = patched_index.semantic_objects_by_key[attribute_semantic_key]
    assert (
        str(indexed_attribute.object_id)
        == baseline_index[attribute_semantic_key]["object_id"]
    )
    assert indexed_attribute.runtime_delta_fingerprint == (
        base_request.current_delta_fingerprint
    )
    committed_changes = cast(
        Sequence[dict[str, object]],
        semantic_commit_evidence["committed_semantic_changes"],
    )
    assert len(committed_changes) == 1
    assert committed_changes[0]["semantic_key"] == attribute_semantic_key
    assert committed_changes[0]["change_key"] == (
        "aware_meta.provider_delta.attribute.update.committed"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_ontology_function_call_intents_through_runtime(
    tmp_path: Path,
) -> None:
    branch_id = _test_uuid("provider-delta-ontology-branch")
    actor_id = _test_uuid("provider-delta-ontology-actor")
    baseline_domain_commit_id = _test_uuid(
        "provider-delta-ontology-baseline-domain-head"
    )
    baseline_oig_commit_id = _test_uuid("provider-delta-ontology-baseline-oig-head")
    baseline_root_domain_commit_id = _test_uuid(
        "provider-delta-ontology-baseline-root-domain-head"
    )
    baseline_root_oig_commit_id = _test_uuid(
        "provider-delta-ontology-baseline-root-oig-head"
    )
    baseline_root_oig_id = _test_uuid("provider-delta-ontology-baseline-root-oig")
    baseline_root_oigi_id = _test_uuid("provider-delta-ontology-baseline-root-oigi")
    package_projection_hash = "sha256:test:ObjectConfigGraphPackage"
    root_projection_hash = "sha256:test:ObjectConfigGraph"
    runtime = _RecordingProviderDeltaOntologyRuntime()
    graph_runtime_context = _provider_delta_ontology_invocation_runtime_context()
    graph_runtime_context.projection_hash_by_name = {
        "ObjectConfigGraph": root_projection_hash,
        "ObjectConfigGraphPackage": package_projection_hash,
    }
    root_oig_commit_index_path = (
        tmp_path
        / ".aware"
        / "oig"
        / str(branch_id)
        / root_projection_hash
        / "indexes"
        / "object_instance_graph_commits"
        / f"{baseline_root_oig_commit_id}.json"
    )
    root_oig_commit_index_path.parent.mkdir(parents=True)
    root_oig_commit_index_path.write_text(
        json.dumps(
            {
                "v": 1,
                "branch_id": str(branch_id),
                "projection_hash": root_projection_hash,
                "object_instance_graph_commit_id": str(baseline_root_oig_commit_id),
                "domain_commit_id": str(baseline_root_domain_commit_id),
            }
        ),
        encoding="utf-8",
    )
    root_head_path = (
        tmp_path
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
                "commit_id": str(baseline_root_domain_commit_id),
                "object_instance_graph_commit_id": str(baseline_root_oig_commit_id),
                "object_instance_graph_id": str(baseline_root_oig_id),
                "object_instance_graph_identity_id": str(baseline_root_oigi_id),
            }
        ),
        encoding="utf-8",
    )
    function_impl_id = _test_uuid("provider-delta-function-impl")
    instruction_id = _test_uuid("provider-delta-function-impl-instruction")
    value_source_id = _test_uuid("provider-delta-function-impl-value-source")
    request = SimpleNamespace(
        execute_provider_delta_materialization=True,
        context={
            "runtime": runtime,
            "aware_meta.graph_runtime_context": graph_runtime_context,
        },
        workspace_root=str(tmp_path),
        provider_delta_author_id=str(actor_id),
        semantic_branch_id=str(branch_id),
        semantic_projection_hash=package_projection_hash,
        baseline_semantic_object_instance_graph_commit_id=(str(baseline_oig_commit_id)),
        baseline_semantic_root_object_instance_graph_commit_id=(
            str(baseline_root_oig_commit_id)
        ),
        semantic_package_commit_id=str(baseline_domain_commit_id),
    )
    baseline_dirty_preflight = {
        "status": "baseline_commit_refs_available",
        "commit_backed_baseline_available": True,
        "baseline_ref_available": True,
        "baseline_ref_hydrator_ready": True,
        "baseline_hydration_preflight": {
            "status": "baseline_hydrated",
            "semantic_branch_id": str(branch_id),
            "semantic_projection_hash": package_projection_hash,
            "semantic_object_instance_graph_commit_id": (str(baseline_oig_commit_id)),
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
    ontology_execution_plan = {
        "status": "ontology_execution_plan_ready",
        "reason": "meta_ocg_ontology_execution_plan_ready",
        "invocation_intent_count": 3,
        "invocation_intents": (
            {
                "intent_key": "intent:create-instruction",
                "operation_key": "op:function-impl",
                "semantic_key": "semantic:function-impl",
                "invocation_order": 10,
                "invocation_mode": "instance",
                "owner_class_name": "FunctionImpl",
                "function_name": "create_instruction",
                "function_ref": FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
                "target_object_id": str(function_impl_id),
                "receiver_semantic_key": "semantic:function-impl",
                "result_semantic_key": "semantic:instruction",
                "expected_result_object_id": str(instruction_id),
                "kwargs": {"type": "set", "sequence": 0},
            },
            {
                "intent_key": "intent:build-value-source",
                "operation_key": "op:function-impl",
                "semantic_key": "semantic:function-impl",
                "invocation_order": 20,
                "invocation_mode": "instance",
                "owner_class_name": "FunctionImplInstruction",
                "function_name": "create_value_source",
                "function_ref": FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
                "target_object_id": str(instruction_id),
                "receiver_semantic_key": "semantic:instruction",
                "result_semantic_key": "semantic:value-source",
                "expected_result_object_id": str(value_source_id),
                "kwargs": {
                    "key": "self.capacity",
                    "kind": "function_input_ref",
                },
            },
            {
                "intent_key": "intent:attach-set",
                "operation_key": "op:function-impl",
                "semantic_key": "semantic:function-impl",
                "invocation_order": 30,
                "invocation_mode": "instance",
                "owner_class_name": "FunctionImplInstruction",
                "function_name": "attach_set",
                "function_ref": FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
                "target_object_id": str(instruction_id),
                "receiver_semantic_key": "semantic:instruction",
                "result_semantic_key": "semantic:instruction-set",
                "expected_result_object_id": None,
                "kwargs": {
                    "target_attribute_config_id": str(
                        _test_uuid("capacity-attribute-config")
                    ),
                    "value_source_id": str(value_source_id),
                },
            },
        ),
    }

    commit_receipt = await _provider_delta_oig_commit_receipt(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_mutation_plan={},
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    assert commit_receipt["reason"] == (
        "meta_ocg_provider_delta_ontology_function_call_commit_applied"
    )
    assert commit_receipt["branch_id"] == str(branch_id)
    assert commit_receipt["projection_hash"] == root_projection_hash
    assert commit_receipt["commit_id"] == str(runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        runtime.receipts[-1].object_instance_graph_commit_id
    )
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == ("ontology_function_call_execution_applied")
    assert invocation_receipt["applied_invocation_count"] == 3
    assert len(runtime.requests) == 3
    assert runtime.requests[0].call_target is MetaGraphCallTarget.instance
    assert runtime.requests[0].target_object_id == function_impl_id
    assert runtime.requests[0].domain_projection_hash == root_projection_hash
    assert runtime.requests[0].domain_object_instance_graph_id == baseline_root_oig_id
    assert (
        runtime.requests[0].domain_object_instance_graph_identity_id
        == baseline_root_oigi_id
    )
    assert runtime.requests[0].expected_head_commit_id == baseline_root_domain_commit_id
    assert runtime.requests[1].call_target is MetaGraphCallTarget.instance
    assert runtime.requests[1].target_object_id == instruction_id
    assert runtime.requests[1].expected_head_commit_id == (
        runtime.receipts[0].commit_id
    )
    assert runtime.requests[2].call_target is MetaGraphCallTarget.instance
    assert runtime.requests[2].target_object_id == instruction_id
    assert runtime.requests[2].expected_head_commit_id == (
        runtime.receipts[1].commit_id
    )
    assert tuple(
        request.kwargs.get("kind")
        for request in runtime.requests
        if "kind" in request.kwargs
    ) == ("function_input_ref",)


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_attribute_delete_intents_through_runtime(
    tmp_path: Path,
) -> None:
    branch_id = _test_uuid("provider-delta-attribute-delete-branch")
    actor_id = _test_uuid("provider-delta-attribute-delete-actor")
    baseline_domain_commit_id = _test_uuid(
        "provider-delta-attribute-delete-baseline-domain-head"
    )
    baseline_oig_commit_id = _test_uuid(
        "provider-delta-attribute-delete-baseline-oig-head"
    )
    baseline_root_domain_commit_id = _test_uuid(
        "provider-delta-attribute-delete-baseline-root-domain-head"
    )
    baseline_root_oig_commit_id = _test_uuid(
        "provider-delta-attribute-delete-baseline-root-oig-head"
    )
    baseline_root_oig_id = _test_uuid(
        "provider-delta-attribute-delete-baseline-root-oig"
    )
    baseline_root_oigi_id = _test_uuid(
        "provider-delta-attribute-delete-baseline-root-oigi"
    )
    package_projection_hash = "sha256:test:ObjectConfigGraphPackage"
    root_projection_hash = "sha256:test:ObjectConfigGraph"
    runtime = _RecordingProviderDeltaOntologyRuntime()
    graph_runtime_context = _provider_delta_ontology_invocation_runtime_context()
    graph_runtime_context.projection_hash_by_name = {
        "ObjectConfigGraph": root_projection_hash,
        "ObjectConfigGraphPackage": package_projection_hash,
    }
    root_oig_commit_index_path = (
        tmp_path
        / ".aware"
        / "oig"
        / str(branch_id)
        / root_projection_hash
        / "indexes"
        / "object_instance_graph_commits"
        / f"{baseline_root_oig_commit_id}.json"
    )
    root_oig_commit_index_path.parent.mkdir(parents=True)
    root_oig_commit_index_path.write_text(
        json.dumps(
            {
                "v": 1,
                "branch_id": str(branch_id),
                "projection_hash": root_projection_hash,
                "object_instance_graph_commit_id": str(baseline_root_oig_commit_id),
                "domain_commit_id": str(baseline_root_domain_commit_id),
            }
        ),
        encoding="utf-8",
    )
    root_head_path = (
        tmp_path
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
                "commit_id": str(baseline_root_domain_commit_id),
                "object_instance_graph_commit_id": str(baseline_root_oig_commit_id),
                "object_instance_graph_id": str(baseline_root_oig_id),
                "object_instance_graph_identity_id": str(baseline_root_oigi_id),
            }
        ),
        encoding="utf-8",
    )
    class_config_id = _test_uuid("provider-delta-attribute-delete-class-config")
    function_config_id = _test_uuid("provider-delta-attribute-delete-function-config")
    class_attribute_id = _test_uuid("provider-delta-attribute-delete-class-state")
    function_attribute_id = _test_uuid(
        "provider-delta-attribute-delete-function-payload"
    )
    request = SimpleNamespace(
        execute_provider_delta_materialization=True,
        context={
            "runtime": runtime,
            "aware_meta.graph_runtime_context": graph_runtime_context,
        },
        workspace_root=str(tmp_path),
        provider_delta_author_id=str(actor_id),
        semantic_branch_id=str(branch_id),
        semantic_projection_hash=package_projection_hash,
        baseline_semantic_object_instance_graph_commit_id=(str(baseline_oig_commit_id)),
        baseline_semantic_root_object_instance_graph_commit_id=(
            str(baseline_root_oig_commit_id)
        ),
        semantic_package_commit_id=str(baseline_domain_commit_id),
    )
    baseline_dirty_preflight = {
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
    ontology_execution_plan = {
        "status": "ontology_execution_plan_ready",
        "reason": "meta_ocg_ontology_execution_plan_ready",
        "invocation_intent_count": 2,
        "invocation_intents": (
            {
                "intent_key": "intent:delete-class-attribute",
                "operation_key": "op:delete-class-attribute",
                "semantic_key": "semantic:class-attribute",
                "invocation_order": 10,
                "invocation_mode": "instance",
                "owner_class_name": "ClassConfig",
                "function_name": "remove_attribute_config",
                "function_ref": CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
                "target_object_id": str(class_config_id),
                "receiver_semantic_key": "semantic:class",
                "result_semantic_key": "semantic:class-attribute",
                "expected_result_object_id": str(class_attribute_id),
                "kwargs": {
                    "name": "state",
                    "attribute_config_id": str(class_attribute_id),
                },
            },
            {
                "intent_key": "intent:delete-function-attribute",
                "operation_key": "op:delete-function-attribute",
                "semantic_key": "semantic:function-attribute",
                "invocation_order": 20,
                "invocation_mode": "instance",
                "owner_class_name": "FunctionConfig",
                "function_name": "remove_attribute_config",
                "function_ref": FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
                "target_object_id": str(function_config_id),
                "receiver_semantic_key": "semantic:function",
                "result_semantic_key": "semantic:function-attribute",
                "expected_result_object_id": str(function_attribute_id),
                "kwargs": {
                    "name": "payload",
                    "type": "output",
                    "attribute_config_id": str(function_attribute_id),
                },
            },
        ),
    }

    commit_receipt = await _provider_delta_oig_commit_receipt(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_mutation_plan={},
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    assert commit_receipt["reason"] == (
        "meta_ocg_provider_delta_ontology_function_call_commit_applied"
    )
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 2
    assert len(runtime.requests) == 2

    class_delete_request = runtime.requests[0]
    assert class_delete_request.call_target is MetaGraphCallTarget.instance
    assert class_delete_request.function_id == _test_uuid(
        "ClassConfig.remove_attribute_config.function"
    )
    assert class_delete_request.target_object_id == class_config_id
    assert class_delete_request.expected_head_commit_id == (
        baseline_root_domain_commit_id
    )
    assert class_delete_request.domain_projection_hash == root_projection_hash
    assert class_delete_request.domain_object_instance_graph_id == (
        baseline_root_oig_id
    )
    assert class_delete_request.domain_object_instance_graph_identity_id == (
        baseline_root_oigi_id
    )
    assert class_delete_request.kwargs == {
        "name": "state",
        "attribute_config_id": str(class_attribute_id),
    }

    function_delete_request = runtime.requests[1]
    assert function_delete_request.call_target is MetaGraphCallTarget.instance
    assert function_delete_request.function_id == _test_uuid(
        "FunctionConfig.remove_attribute_config.function"
    )
    assert function_delete_request.target_object_id == function_config_id
    assert function_delete_request.expected_head_commit_id == (
        runtime.receipts[0].commit_id
    )
    assert function_delete_request.expected_graph_hash_pre == (
        runtime.receipts[0].graph_hash_post
    )
    assert function_delete_request.kwargs == {
        "name": "payload",
        "type": "output",
        "attribute_config_id": str(function_attribute_id),
    }
    assert commit_receipt["commit_id"] == str(runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        runtime.receipts[-1].object_instance_graph_commit_id
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_attribute_membership_update_intents_through_runtime(
    tmp_path: Path,
) -> None:
    branch_id = _test_uuid("provider-delta-attribute-membership-update-branch")
    actor_id = _test_uuid("provider-delta-attribute-membership-update-actor")
    baseline_domain_commit_id = _test_uuid(
        "provider-delta-attribute-membership-update-baseline-domain-head"
    )
    baseline_oig_commit_id = _test_uuid(
        "provider-delta-attribute-membership-update-baseline-oig-head"
    )
    baseline_root_domain_commit_id = _test_uuid(
        "provider-delta-attribute-membership-update-baseline-root-domain-head"
    )
    baseline_root_oig_commit_id = _test_uuid(
        "provider-delta-attribute-membership-update-baseline-root-oig-head"
    )
    baseline_root_oig_id = _test_uuid(
        "provider-delta-attribute-membership-update-baseline-root-oig"
    )
    baseline_root_oigi_id = _test_uuid(
        "provider-delta-attribute-membership-update-baseline-root-oigi"
    )
    package_projection_hash = "sha256:test:ObjectConfigGraphPackage"
    root_projection_hash = "sha256:test:ObjectConfigGraph"
    runtime = _RecordingProviderDeltaOntologyRuntime()
    graph_runtime_context = _provider_delta_ontology_invocation_runtime_context()
    graph_runtime_context.projection_hash_by_name = {
        "ObjectConfigGraph": root_projection_hash,
        "ObjectConfigGraphPackage": package_projection_hash,
    }
    root_oig_commit_index_path = (
        tmp_path
        / ".aware"
        / "oig"
        / str(branch_id)
        / root_projection_hash
        / "indexes"
        / "object_instance_graph_commits"
        / f"{baseline_root_oig_commit_id}.json"
    )
    root_oig_commit_index_path.parent.mkdir(parents=True)
    root_oig_commit_index_path.write_text(
        json.dumps(
            {
                "v": 1,
                "branch_id": str(branch_id),
                "projection_hash": root_projection_hash,
                "object_instance_graph_commit_id": str(baseline_root_oig_commit_id),
                "domain_commit_id": str(baseline_root_domain_commit_id),
            }
        ),
        encoding="utf-8",
    )
    root_head_path = (
        tmp_path
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
                "commit_id": str(baseline_root_domain_commit_id),
                "object_instance_graph_commit_id": str(baseline_root_oig_commit_id),
                "object_instance_graph_id": str(baseline_root_oig_id),
                "object_instance_graph_identity_id": str(baseline_root_oigi_id),
            }
        ),
        encoding="utf-8",
    )
    class_edge_id = _test_uuid("provider-delta-class-attribute-membership-update-edge")
    class_config_id = _test_uuid(
        "provider-delta-class-attribute-membership-update-class"
    )
    class_attribute_config_id = _test_uuid(
        "provider-delta-class-attribute-membership-update-attribute"
    )
    function_edge_id = _test_uuid(
        "provider-delta-function-attribute-membership-update-edge"
    )
    function_config_id = _test_uuid(
        "provider-delta-function-attribute-membership-update-function"
    )
    function_attribute_config_id = _test_uuid(
        "provider-delta-function-attribute-membership-update-attribute"
    )
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 2,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:" "class-name"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": (
                    "ocg:aware_demo/node:aware_demo.default.home.Room"
                    "/attribute:name/membership:class_config"
                ),
                "semantic_subject_type": ("aware_meta.ClassConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(class_edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "class_config_attribute_config_id": str(class_edge_id),
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(class_attribute_config_id),
                    },
                },
                "current": {
                    "class_config_attribute_config_id": str(class_edge_id),
                    "class_config_id": str(class_config_id),
                    "attribute_config_id": str(class_attribute_config_id),
                    "attribute_membership_owner_kind": "class",
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "class_config_id": str(class_config_id),
                        "attribute_config_id": str(class_attribute_config_id),
                        "position": 3,
                        "is_identity_key": True,
                    },
                },
            },
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    "function-name"
                ),
                "operation_family": "update",
                "provider_operation_type": ("meta_ocg.attribute_membership.update"),
                "semantic_key": (
                    "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
                    "/attribute:input:name/membership:function_config"
                ),
                "semantic_subject_type": ("aware_meta.FunctionConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(function_edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "function_config_attribute_config_id": str(function_edge_id),
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(function_attribute_config_id),
                    },
                },
                "current": {
                    "function_config_attribute_config_id": str(function_edge_id),
                    "function_config_id": str(function_config_id),
                    "attribute_config_id": str(function_attribute_config_id),
                    "attribute_membership_owner_kind": "function",
                    "attribute_membership_signature": {
                        "owner_kind": "function",
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(function_attribute_config_id),
                        "name": "name",
                        "type": "input",
                        "position": 1,
                        "is_identity_key": True,
                        "identity_key_origin": "propagated_parent",
                    },
                },
            },
        ),
    }
    ontology_execution_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_execution_plan["status"] == "ontology_execution_plan_ready"
    request = SimpleNamespace(
        execute_provider_delta_materialization=True,
        context={
            "runtime": runtime,
            "aware_meta.graph_runtime_context": graph_runtime_context,
        },
        workspace_root=str(tmp_path),
        provider_delta_author_id=str(actor_id),
        semantic_branch_id=str(branch_id),
        semantic_projection_hash=package_projection_hash,
        baseline_semantic_object_instance_graph_commit_id=str(baseline_oig_commit_id),
        baseline_semantic_root_object_instance_graph_commit_id=(
            str(baseline_root_oig_commit_id)
        ),
        semantic_package_commit_id=str(baseline_domain_commit_id),
    )
    baseline_dirty_preflight = {
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

    commit_receipt = await _provider_delta_oig_commit_receipt(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_mutation_plan={},
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 2
    assert len(runtime.requests) == 2
    class_update_request = runtime.requests[0]
    assert class_update_request.call_target is MetaGraphCallTarget.instance
    assert class_update_request.function_id == _test_uuid(
        "ClassConfigAttributeConfig.update_config.function"
    )
    assert class_update_request.target_object_id == class_edge_id
    assert class_update_request.expected_head_commit_id == (
        baseline_root_domain_commit_id
    )
    assert class_update_request.domain_projection_hash == root_projection_hash
    assert class_update_request.domain_object_instance_graph_id == (
        baseline_root_oig_id
    )
    assert class_update_request.domain_object_instance_graph_identity_id == (
        baseline_root_oigi_id
    )
    assert class_update_request.kwargs == {
        "position": 3,
        "is_identity_key": True,
    }
    function_update_request = runtime.requests[1]
    assert function_update_request.call_target is MetaGraphCallTarget.instance
    assert function_update_request.function_id == _test_uuid(
        "FunctionConfigAttributeConfig.update_config.function"
    )
    assert function_update_request.target_object_id == function_edge_id
    assert function_update_request.expected_head_commit_id == (
        runtime.receipts[0].commit_id
    )
    assert function_update_request.expected_graph_hash_pre == (
        runtime.receipts[0].graph_hash_post
    )
    assert function_update_request.kwargs == {
        "position": 1,
        "is_identity_key": True,
        "identity_key_origin": "propagated_parent",
    }
    assert commit_receipt["commit_id"] == str(runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        runtime.receipts[-1].object_instance_graph_commit_id
    )


class _FakeEvidence:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload: dict[str, object] = payload

    def evidence_payload(self) -> dict[str, object]:
        return dict(self._payload)
