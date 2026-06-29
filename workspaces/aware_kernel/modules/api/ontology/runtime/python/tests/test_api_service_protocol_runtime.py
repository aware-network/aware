from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.class_.inline_value_instance.builder import (
    build_inline_value_instance_from_mapping,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from _api_runtime_test_paths import (
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    REPO_ROOT,
)

from api_runtime_fixture_artifacts import (
    write_ontology_dependency_runtime_artifacts,
    write_python_models_manifest_for_refs,
)
from aware_api_runtime.compile import compile_api_workspace
from aware_api_runtime.invocation import (
    build_resolved_api_invocation_envelope,
    resolve_api_invocation_ir,
)
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_api_runtime.models import (
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization import materialize_api_call
from aware_api_runtime.service_protocol import (
    build_api_service_dispatch_plan,
    build_api_service_dispatch_plan_from_materialized_call,
    decode_inline_value_instance_to_mapping_strict,
    decode_committed_api_call_request,
    load_api_service_protocol_package,
)
from aware_api_runtime.service_protocol.runtime import (
    ApiServiceProtocolEndpointBinding,
    LoadedApiServiceProtocolPackage,
    _decode_attribute_value_strict,
    _projection_target_matches,
    _request_class_configs_by_id_for_decode,
    _resolve_request_model_class,
)


_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)


@dataclass(frozen=True, slots=True)
class ApiMetaRuntimeLane:
    branch_id: UUID
    actor_id: UUID | None = None


def _api_ownership_for_runtime(*, request_class_ref: str) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="openai",
            source_path="runtime-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="door",
                    source_path="runtime-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="open",
                            source_path="runtime-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="runtime-proof",
                            ),
                            functions=(
                                APICapabilityEndpointFunctionOwnership(
                                    name="open",
                                    graph_target="aware_home",
                                    graph_capability_function_name="open",
                                    source_path="runtime-proof",
                                ),
                            ),
                            description="Open the API proof door.",
                        ),
                    ),
                    description="Door operations",
                ),
            ),
            graphs=(),
        ),
    )


def _api_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PACKAGE_MANIFEST_PATHS


def _api_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PYTHON_ROOTS


def _prepend_api_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _api_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_api_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_api_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_API_META_HANDLER_MODULE,),
        bootstrap_modules=(_API_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _pydantic_class_config_by_name(*, package_prefix: str, name: str) -> ClassConfig:
    from aware_utils.pydantic.class_config_registry import (
        iter_pydantic_package_class_config_payloads,
        register_pydantic_package_class_configs,
    )

    register_pydantic_package_class_configs(package_prefix=package_prefix)
    for entry in iter_pydantic_package_class_config_payloads(
        package_prefix=package_prefix,
    ):
        class_config = ClassConfig.model_validate(entry.payload)
        if class_config.name == name:
            return class_config
    raise AssertionError(f"Missing ClassConfig {package_prefix}.{name}")


def test_projection_target_match_preserves_authored_projection_identity() -> None:
    assert _projection_target_matches(
        projection_name="FocusScope", target="aware_attention.FocusScope"
    )
    assert not _projection_target_matches(
        projection_name="FocusScope", target="aware_attention.FocusScopeProjection"
    )
    assert not _projection_target_matches(
        projection_name="FocusScope", target="aware_attention.focus_scope"
    )


def test_resolve_request_model_class_uses_service_protocol_dto_ref(
    tmp_path: Path,
) -> None:
    public_root = tmp_path / "public"
    protocol_root = tmp_path / "protocol"
    public_package = public_root / "proof_public_api"
    protocol_package = protocol_root / "proof_public_protocol"
    dto_package = protocol_root / "proof_dto"
    public_package.mkdir(parents=True)
    protocol_package.mkdir(parents=True)
    dto_package.mkdir(parents=True)
    (public_package / "__init__.py").write_text("", encoding="utf-8")
    (protocol_package / "__init__.py").write_text("", encoding="utf-8")
    (dto_package / "__init__.py").write_text("", encoding="utf-8")
    (dto_package / "requests.py").write_text(
        "\n".join(
            [
                "from pydantic import BaseModel",
                "",
                "class ProofRequest(BaseModel):",
                "    value: str",
            ]
        ),
        encoding="utf-8",
    )
    (protocol_package / "protocols.py").write_text(
        "from proof_dto.requests import ProofRequest\n",
        encoding="utf-8",
    )

    loaded_package = LoadedApiServiceProtocolPackage(
        runtime_package_dir=tmp_path,
        public_package_root=public_root,
        service_protocol_package_root=protocol_root,
        public_package_import_root="proof_public_api",
        service_protocol_import_root="proof_public_protocol",
        endpoint_bindings={},
        runtime_fulfillment_bindings={},
    )
    endpoint_binding = ApiServiceProtocolEndpointBinding(
        endpoint_ref="proof.fetch",
        request_type_ref="proof_dto.ProofRequest",
        response_type_ref=None,
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=lambda _handler, _request, _execution=None: None,
    )

    resolved = _resolve_request_model_class(
        loaded_package=loaded_package,
        endpoint_binding=endpoint_binding,
    )

    assert resolved.__name__ == "ProofRequest"
    assert issubclass(resolved, BaseModel)


def test_service_protocol_decode_includes_registered_nested_dto_class_configs() -> None:
    from aware_utils.pydantic.class_config_registry import (
        iter_pydantic_package_class_config_payloads,
        register_pydantic_package_class_configs,
    )

    register_pydantic_package_class_configs(
        package_prefix="aware_workspace_service_dto"
    )
    register_pydantic_package_class_configs(package_prefix="aware_code_service_dto")
    request_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_workspace_service_dto",
        name="WorkspaceMaterializeRequest",
    )
    code_package_delta_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_code_service_dto",
        name="CodePackageDelta",
    )

    class_configs_by_id = _request_class_configs_by_id_for_decode(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        request_class_config=request_class_config,
        request_type_ref="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
    )

    assert request_class_config.id is not None
    assert code_package_delta_class_config.id is not None
    assert class_configs_by_id[request_class_config.id] == request_class_config
    assert class_configs_by_id[code_package_delta_class_config.id].value_mode == (
        ClassValueMode.inline_value
    )
    assert tuple(
        entry
        for entry in iter_pydantic_package_class_config_payloads(
            package_prefix="aware_code_service_dto"
        )
        if entry.class_config_id == str(code_package_delta_class_config.id)
    )


def test_service_protocol_decode_prefers_package_snapshot_over_runtime_index_conflict() -> (
    None
):
    request_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_workspace_service_dto",
        name="WorkspaceMaterializeRequest",
    )
    code_package_delta_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_code_service_dto",
        name="CodePackageDelta",
    )
    assert code_package_delta_class_config.id is not None
    stale_runtime_nested_class_config = ClassConfig(
        id=code_package_delta_class_config.id,
        class_config_attribute_configs=(
            code_package_delta_class_config.class_config_attribute_configs
        ),
        class_config_function_configs=(),
        class_config_relationships=(),
        class_fqn=code_package_delta_class_config.class_fqn,
        name=code_package_delta_class_config.name,
        value_mode=ClassValueMode.graph_ref,
    )

    class_configs_by_id = _request_class_configs_by_id_for_decode(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={
                    code_package_delta_class_config.id: (
                        stale_runtime_nested_class_config
                    ),
                },
            ),
        ),
        request_class_config=request_class_config,
        request_type_ref="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
    )

    assert class_configs_by_id[code_package_delta_class_config.id].value_mode == (
        ClassValueMode.inline_value
    )


def test_decode_inline_value_instance_to_mapping_includes_parent_class_id_attributes() -> (
    None
):
    base_cc = ClassConfig(
        name="ConversationServiceRequest",
        class_fqn="aware_test_api.ConversationServiceRequest",
        value_mode=ClassValueMode.inline_value,
    )
    child_cc = ClassConfig(
        name="CreateConversationSpaceRequest",
        class_fqn="aware_test_api.CreateConversationSpaceRequest",
        value_mode=ClassValueMode.inline_value,
        parent_class_id=base_cc.id,
    )

    base_operation_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    base_operation_cfg = AttributeConfig(
        owner_key=base_cc.class_fqn,
        name="operation",
        is_required=True,
        type_descriptor=base_operation_desc,
        type_descriptor_id=base_operation_desc.id,
    )
    request_id_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    request_id_cfg = AttributeConfig(
        owner_key=base_cc.class_fqn,
        name="request_id",
        type_descriptor=request_id_desc,
        type_descriptor_id=request_id_desc.id,
    )
    child_operation_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_operation_cfg = AttributeConfig(
        owner_key=child_cc.class_fqn,
        name="operation",
        is_required=True,
        type_descriptor=child_operation_desc,
        type_descriptor_id=child_operation_desc.id,
    )
    title_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    title_cfg = AttributeConfig(
        owner_key=child_cc.class_fqn,
        name="title",
        type_descriptor=title_desc,
        type_descriptor_id=title_desc.id,
    )
    base_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=base_cc.id,
            attribute_config=base_operation_cfg,
            attribute_config_id=base_operation_cfg.id,
            name=base_operation_cfg.name,
            position=0,
        ),
        ClassConfigAttributeConfig(
            class_config_id=base_cc.id,
            attribute_config=request_id_cfg,
            attribute_config_id=request_id_cfg.id,
            name=request_id_cfg.name,
            position=1,
        ),
    ]
    child_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=child_cc.id,
            attribute_config=child_operation_cfg,
            attribute_config_id=child_operation_cfg.id,
            name=child_operation_cfg.name,
            position=0,
        ),
        ClassConfigAttributeConfig(
            class_config_id=child_cc.id,
            attribute_config=title_cfg,
            attribute_config_id=title_cfg.id,
            name=title_cfg.name,
            position=1,
        ),
    ]

    request_id = uuid4()
    class_configs_by_id = {base_cc.id: base_cc, child_cc.id: child_cc}
    instance = build_inline_value_instance_from_mapping(
        owner_key=uuid4(),
        class_config=child_cc,
        values={
            "operation": "create_conversation_space",
            "request_id": request_id,
            "title": "Conversation local dogfood",
        },
        class_configs_by_id=class_configs_by_id,
    )

    payload = decode_inline_value_instance_to_mapping_strict(
        inline_value_instance=instance,
        class_config=child_cc,
        class_configs_by_id=class_configs_by_id,
    )

    assert payload == {
        "operation": "create_conversation_space",
        "request_id": str(request_id),
        "title": "Conversation local dogfood",
    }


def _sample_value_for_primitive(base_type: CodePrimitiveBaseType) -> object | None:
    if base_type == CodePrimitiveBaseType.string:
        return "front-door"
    if base_type == CodePrimitiveBaseType.boolean:
        return True
    if base_type == CodePrimitiveBaseType.integer:
        return 7
    if base_type == CodePrimitiveBaseType.float:
        return 1.5
    if base_type == CodePrimitiveBaseType.uuid:
        return uuid4()
    return None


def _aware_type_for_primitive(base_type: CodePrimitiveBaseType) -> str:
    if base_type == CodePrimitiveBaseType.string:
        return "String"
    if base_type == CodePrimitiveBaseType.boolean:
        return "Bool"
    if base_type == CodePrimitiveBaseType.integer:
        return "Int"
    if base_type == CodePrimitiveBaseType.float:
        return "Float"
    if base_type == CodePrimitiveBaseType.uuid:
        return "UUID"
    raise AssertionError(
        f"Unsupported primitive base type for proof workspace: {base_type!r}"
    )


def _expected_decoded_payload_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    return value


def test_decode_attribute_value_strict_resolves_enum_option_id_via_descriptor() -> None:
    enum_cfg = EnumConfig(
        name="IdentityType",
        enum_fqn="aware_identity.IdentityType",
        enum_options=[],
    )
    human = EnumOption(value="human", label="Human", enum_config_id=enum_cfg.id)
    enum_cfg.enum_options = [human]
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=enum_cfg,
        enum_config_id=enum_cfg.id,
    )
    value = AttributeValue(
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
        enum_option_id=human.id,
    )

    assert (
        _decode_attribute_value_strict(
            value,
            descriptor=descriptor,
            class_configs_by_id=None,
        )
        == "human"
    )


async def _compile_api_workspace_in_thread(
    *,
    toml_path: Path,
    repo_root: Path,
    materialize_service_protocol: bool = False,
    dependency_graph_mode: str = "meta_runtime",
):
    return await asyncio.to_thread(
        compile_api_workspace,
        toml_path=toml_path,
        repo_root=repo_root,
        materialize_service_protocol=materialize_service_protocol,
        dependency_graph_mode=dependency_graph_mode,
        kernel_repo_root=REPO_ROOT,
    )


def _select_runtime_function_config_id(runtime_index: MetaGraphRuntimeIndex) -> UUID:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        for function_link in sorted(
            class_config.class_config_function_configs,
            key=lambda item: (item.position, str(item.id)),
        ):
            if function_link.function_config_id is not None:
                return function_link.function_config_id
    raise AssertionError(
        "Expected one runtime ClassConfigFunctionConfig for API service protocol proof"
    )


def _load_planned_runtime_function_target(
    runtime_package_dir: Path,
    *,
    endpoint_ref: str,
    fulfillment_name: str,
    graph_target: str,
    graph_capability_function_name: str,
    function_name: str,
) -> str:
    payload = json.loads(
        (runtime_package_dir / "api.service_protocol_plan.json").read_text(
            encoding="utf-8"
        )
    )
    apis = payload.get("apis", [])
    assert isinstance(apis, list)
    matches: list[str] = []
    for api in apis:
        assert isinstance(api, dict)
        capabilities = api.get("capabilities", [])
        assert isinstance(capabilities, list)
        for capability in capabilities:
            assert isinstance(capability, dict)
            endpoints = capability.get("endpoints", [])
            assert isinstance(endpoints, list)
            for endpoint in endpoints:
                assert isinstance(endpoint, dict)
                if endpoint.get("endpoint_ref") != endpoint_ref:
                    continue
                fulfillment_bindings = endpoint.get("fulfillment_bindings", [])
                assert isinstance(fulfillment_bindings, list)
                for binding in fulfillment_bindings:
                    assert isinstance(binding, dict)
                    if binding.get("name") != fulfillment_name:
                        continue
                    if binding.get("graph_target") != graph_target:
                        continue
                    if (
                        binding.get("graph_capability_function_name")
                        != graph_capability_function_name
                    ):
                        continue
                    runtime_target = binding.get("graph_function_runtime_target")
                    assert isinstance(runtime_target, str)
                    assert runtime_target.rsplit(".", 1)[-1] == function_name
                    matches.append(runtime_target)
    unique_matches = tuple(dict.fromkeys(matches))
    assert len(unique_matches) == 1
    return unique_matches[0]


def _select_runtime_inline_request_contract(
    runtime_index,
) -> tuple[ClassConfig, str, CodePrimitiveBaseType, object]:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        if class_config.value_mode != ClassValueMode.inline_value:
            continue
        attribute_links = [
            link
            for link in sorted(
                class_config.class_config_attribute_configs,
                key=lambda item: item.position,
            )
            if link.attribute_config is not None
            and not link.attribute_config.is_virtual
        ]
        if len(attribute_links) != 1:
            continue
        attribute_config = attribute_links[0].attribute_config
        if attribute_config is None or not attribute_config.name:
            continue
        type_info = resolve_type_info(attribute_config)
        if (
            type_info.kind.value != "primitive"
            or type_info.is_collection
            or type_info.primitive_config is None
        ):
            continue
        primitive_type = CodePrimitiveType.model_validate(
            type_info.primitive_config.primitive_type
        )
        sample_value = _sample_value_for_primitive(primitive_type.base_type)
        if sample_value is None:
            continue
        return (
            class_config,
            attribute_config.name,
            primitive_type.base_type,
            sample_value,
        )

    raise AssertionError(
        "Expected one compiled inline_value ClassConfig with a single supported primitive attribute"
    )


def _write_runtime_api_workspace(
    *,
    root: Path,
    request_attribute_name: str,
    request_attribute_type: str,
) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "proof-api"',
                'fqn_prefix = "aware_proof_api"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-api-types"',
                "",
                "[[semantic_package_exports]]",
                'kind = "api_dto"',
                'package_name = "proof-api-types"',
                'manifest_path = "apis/types/proof/aware.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    package_root = root / "apis" / "types" / "proof"
    (package_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    (ontology_root / "aware" / "home").mkdir(parents=True, exist_ok=True)
    _ = (ontology_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_home"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "home.aware").write_text(
        "\n".join(
            [
                "class Home {",
                "    name String key",
                "    doors Door[]",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String",
                "",
                "    fn open(",
                "        dry_run Bool = false",
                "    ) -> Bool {",
                '        """Open this door."""',
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home_projection.aware").write_text(
        "\n".join(
            [
                "projection Home {",
                "    root home.Home",
                "    home.Home::doors",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _ = (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "proof-api-types"',
                'fqn_prefix = "aware_proof_types"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_proof_types"',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware" / "door" / "endpoints.aware").write_text(
        "\n".join(
            [
                "class OpenRequest {",
                f"    {request_attribute_name} {request_attribute_type}",
                "}",
                "",
                "class OpenResult {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    bindings = root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "proof.apis.aware").write_text(
        "\n".join(
            [
                "api openai {",
                "    capability door {",
                "        endpoint open aware_proof_types.door.OpenRequest {",
                "            response aware_proof_types.door.OpenResult;",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability door {",
                "            function open aware_home.home.Door.open;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_ontology_dependency_runtime_artifacts(
        package_root=ontology_root,
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_refs=("aware_home.home.Home", "aware_home.home.Door"),
        projection_names=("Home",),
    )
    write_python_models_manifest_for_refs(
        package_root=package_root,
        class_refs=(
            "aware_proof_types.door.OpenRequest",
            "aware_proof_types.door.OpenResult",
        ),
    )
    return toml_path


def _write_minimal_service_protocol_package_runtime_package(
    *,
    runtime_root: Path,
    request_type_ref: str = "aware_proof_api.models.open_request.OpenRequest",
    response_type_ref: str | None = None,
    call_target_kind: str | None = "instance",
    exact_output_field_name: str | None = None,
) -> Path:
    public_root = (
        runtime_root / "public_package" / "python" / "package" / "aware_proof_api"
    )
    service_protocol_root = (
        runtime_root
        / "service_protocol"
        / "python"
        / "package"
        / "aware_proof_protocol"
    )
    (public_root / "models").mkdir(parents=True, exist_ok=True)
    service_protocol_root.mkdir(parents=True, exist_ok=True)

    _ = (public_root / "__init__.py").write_text("", encoding="utf-8")
    _ = (public_root / "models" / "__init__.py").write_text("", encoding="utf-8")
    _ = (public_root / "models" / "open_request.py").write_text(
        "\n".join(
            [
                "from pydantic import BaseModel",
                "",
                "class OpenRequest(BaseModel):",
                "    label: str",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (service_protocol_root / "__init__.py").write_text("", encoding="utf-8")
    _ = (service_protocol_root / "protocols.py").write_text(
        "\n".join(
            [
                "from collections.abc import AsyncIterator",
                "from typing import Awaitable, Callable, Protocol, TypeAlias, cast",
                "from dataclasses import dataclass",
                "from pydantic import BaseModel",
                "",
                "class ServiceProtocolExecutionBackend(Protocol):",
                "    async def invoke_fulfillment(",
                "        self,",
                "        *,",
                "        fulfillment_name: str,",
                "        request: BaseModel,",
                "    ) -> object | None: ...",
                "",
                "class ServiceProtocolExecution(Protocol):",
                "    pass",
                "",
                "class OpenExecution(ServiceProtocolExecution, Protocol):",
                "    pass",
                "",
                "ServiceProtocolExecutionFactory: TypeAlias = Callable[",
                "    [ServiceProtocolExecutionBackend],",
                "    ServiceProtocolExecution,",
                "]",
                "ServiceProtocolInvoker: TypeAlias = Callable[",
                "    [object, BaseModel, ServiceProtocolExecution | None],",
                "    Awaitable[object | None],",
                "]",
                "ServiceProtocolStreamInvoker: TypeAlias = Callable[",
                "    [object, BaseModel, ServiceProtocolExecution | None],",
                "    AsyncIterator[object],",
                "]",
                "",
                "async def invoke_openai__door__open(",
                "    handler: object,",
                "    request: BaseModel,",
                "    execution: OpenExecution | None = None,",
                ") -> object | None:",
                "    _ = execution",
                "    return None",
                "",
                "def build_openai__door__open_execution(backend: ServiceProtocolExecutionBackend) -> OpenExecution:",
                "    return cast(OpenExecution, backend)",
                "",
                'PUBLIC_PACKAGE_IMPORT_ROOT = "aware_proof_api"',
                "",
                "@dataclass(frozen=True, slots=True)",
                "class ServiceProtocolEndpointBinding:",
                "    endpoint_ref: str",
                "    request_type_ref: str",
                "    response_type_ref: str | None",
                "    stream_event_type_refs: tuple[str, ...]",
                "    execution_protocol_ref: str | None",
                "    build_execution: ServiceProtocolExecutionFactory | None",
                "    stream_invoke: ServiceProtocolStreamInvoker | None",
                "    fulfillment_bindings: tuple[object, ...]",
                "    invoke: ServiceProtocolInvoker",
                "",
                "ENDPOINT_BINDINGS = {",
                '    "openai.door.open": ServiceProtocolEndpointBinding(',
                '        endpoint_ref="openai.door.open",',
                f'        request_type_ref="{request_type_ref}",',
                f"        response_type_ref={response_type_ref!r},",
                "        stream_event_type_refs=(),",
                '        execution_protocol_ref="aware_proof_protocol.protocols.OpenExecution",',
                "        build_execution=build_openai__door__open_execution,",
                "        stream_invoke=None,",
                "        fulfillment_bindings=(),",
                "        invoke=invoke_openai__door__open,",
                "    ),",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (runtime_root / "api.service_protocol_plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": "proof-api",
                "fqn_prefix": "aware_proof_api",
                "backend_handoff": {
                    "materialization_source": "api",
                    "aware_package_kind": "api_service_protocol",
                    "expected_renderer_profile": "python.api.service_protocol",
                },
                "apis": [
                    {
                        "name": "openai",
                        "description": None,
                        "source_path": "test",
                        "capabilities": [
                            {
                                "api_name": "openai",
                                "name": "door",
                                "description": None,
                                "source_path": "test",
                                "endpoints": [
                                    {
                                        "api_name": "openai",
                                        "capability_name": "door",
                                        "name": "open",
                                        "endpoint_ref": "openai.door.open",
                                        "discriminant": "openai.door.open",
                                        "description": None,
                                        "source_path": "test",
                                        "request": {
                                            "class_ref": request_type_ref.rsplit(
                                                ".", 1
                                            )[0]
                                            + ".OpenRequest",
                                            "description": None,
                                            "source_path": "test",
                                        },
                                        "response": None,
                                        "stream": None,
                                        "fulfillment_bindings": [
                                            {
                                                "name": "open",
                                                "graph_target": "aware_home",
                                                "graph_capability_function_name": "open",
                                                "graph_function_python_ref": "aware_home.home.Door.open",
                                                "graph_function_runtime_target": "aware_home.default.home.Door.open",
                                                "call_target_kind": call_target_kind,
                                                "exact_output_field_name": exact_output_field_name,
                                                "source_path": "test",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_root


def _write_minimal_manifest_backed_service_protocol_package_runtime_package(
    *,
    runtime_root: Path,
    api_package_root: Path,
    request_type_ref: str = "aware_proof_api.models.open_request.OpenRequest",
    response_type_ref: str | None = None,
) -> Path:
    api_toml_path = api_package_root / "aware.api.toml"
    api_package_root.mkdir(parents=True, exist_ok=True)
    runtime_root.mkdir(parents=True, exist_ok=True)
    public_package_root = api_package_root / "python" / "aware_proof_api"
    service_protocol_package_root = api_package_root / "python" / "aware_proof_protocol"
    public_root = public_package_root / "aware_proof_api"
    service_protocol_root = service_protocol_package_root / "aware_proof_protocol"
    _ = api_toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "proof-api"',
                'fqn_prefix = "aware_proof_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "api_ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (public_root / "models").mkdir(parents=True, exist_ok=True)
    service_protocol_root.mkdir(parents=True, exist_ok=True)
    _ = (public_root / "__init__.py").write_text("", encoding="utf-8")
    _ = (public_root / "models" / "__init__.py").write_text("", encoding="utf-8")
    _ = (public_root / "models" / "open_request.py").write_text(
        "\n".join(
            [
                "from pydantic import BaseModel",
                "",
                "class OpenRequest(BaseModel):",
                "    label: str",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (service_protocol_root / "__init__.py").write_text("", encoding="utf-8")
    _ = (service_protocol_root / "protocols.py").write_text(
        "\n".join(
            [
                "from collections.abc import AsyncIterator",
                "from typing import Awaitable, Callable, Protocol, TypeAlias, cast",
                "from dataclasses import dataclass",
                "from pydantic import BaseModel",
                "",
                "class ServiceProtocolExecutionBackend(Protocol):",
                "    async def invoke_fulfillment(",
                "        self,",
                "        *,",
                "        fulfillment_name: str,",
                "        request: BaseModel,",
                "    ) -> object | None: ...",
                "",
                "class ServiceProtocolExecution(Protocol):",
                "    pass",
                "",
                "class OpenExecution(ServiceProtocolExecution, Protocol):",
                "    pass",
                "",
                "ServiceProtocolExecutionFactory: TypeAlias = Callable[",
                "    [ServiceProtocolExecutionBackend],",
                "    ServiceProtocolExecution,",
                "]",
                "ServiceProtocolInvoker: TypeAlias = Callable[",
                "    [object, BaseModel, ServiceProtocolExecution | None],",
                "    Awaitable[object | None],",
                "]",
                "ServiceProtocolStreamInvoker: TypeAlias = Callable[",
                "    [object, BaseModel, ServiceProtocolExecution | None],",
                "    AsyncIterator[object],",
                "]",
                "",
                "async def invoke_openai__door__open(",
                "    handler: object,",
                "    request: BaseModel,",
                "    execution: OpenExecution | None = None,",
                ") -> object | None:",
                "    _ = execution",
                "    return None",
                "",
                "def build_openai__door__open_execution(backend: ServiceProtocolExecutionBackend) -> OpenExecution:",
                "    return cast(OpenExecution, backend)",
                "",
                'PUBLIC_PACKAGE_IMPORT_ROOT = "aware_proof_api"',
                "",
                "@dataclass(frozen=True, slots=True)",
                "class ServiceProtocolEndpointBinding:",
                "    endpoint_ref: str",
                "    request_type_ref: str",
                "    response_type_ref: str | None",
                "    stream_event_type_refs: tuple[str, ...]",
                "    execution_protocol_ref: str | None",
                "    build_execution: ServiceProtocolExecutionFactory | None",
                "    stream_invoke: ServiceProtocolStreamInvoker | None",
                "    fulfillment_bindings: tuple[object, ...]",
                "    invoke: ServiceProtocolInvoker",
                "",
                "ENDPOINT_BINDINGS = {",
                '    "openai.door.open": ServiceProtocolEndpointBinding(',
                '        endpoint_ref="openai.door.open",',
                f'        request_type_ref="{request_type_ref}",',
                f"        response_type_ref={response_type_ref!r},",
                "        stream_event_type_refs=(),",
                '        execution_protocol_ref="aware_proof_protocol.protocols.OpenExecution",',
                "        build_execution=build_openai__door__open_execution,",
                "        stream_invoke=None,",
                "        fulfillment_bindings=(),",
                "        invoke=invoke_openai__door__open,",
                "    ),",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (runtime_root / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "compile_target": "api",
                "api_toml_path": str(api_toml_path.resolve()),
                "api_package_name": "proof-api",
                "api_fqn_prefix": "aware_proof_api",
                "public_package_materialized": True,
                "service_protocol_materialized": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (runtime_root / "api.service_protocol_plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": "proof-api",
                "fqn_prefix": "aware_proof_api",
                "backend_handoff": {
                    "materialization_source": "api",
                    "aware_package_kind": "api_service_protocol",
                    "expected_renderer_profile": "python.api.service_protocol",
                },
                "apis": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_root


def test_load_api_service_protocol_package_uses_symbol_only_endpoint_bindings(
    tmp_path: Path,
) -> None:
    runtime_root = _write_minimal_service_protocol_package_runtime_package(
        runtime_root=tmp_path / "runtime"
    )

    loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)

    assert loaded.public_package_import_root == "aware_proof_api"
    binding = loaded.endpoint_bindings["openai.door.open"]
    assert binding.endpoint_ref == "openai.door.open"
    assert binding.request_type_ref == "aware_proof_api.models.open_request.OpenRequest"
    assert binding.response_type_ref is None
    assert binding.stream_event_type_refs == ()
    assert (
        binding.execution_protocol_ref == "aware_proof_protocol.protocols.OpenExecution"
    )
    assert callable(binding.build_execution)
    assert binding.stream_invoke is None
    assert callable(binding.invoke)
    planned_binding = next(iter(loaded.runtime_fulfillment_bindings.values()))
    assert planned_binding.call_target_kind == "instance"
    assert planned_binding.exact_output_field_name is None


def test_load_api_service_protocol_package_preserves_constructor_metadata_from_plan(
    tmp_path: Path,
) -> None:
    runtime_root = _write_minimal_service_protocol_package_runtime_package(
        runtime_root=tmp_path / "runtime",
        call_target_kind="constructor",
        exact_output_field_name="value",
    )

    loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)

    planned_binding = next(iter(loaded.runtime_fulfillment_bindings.values()))
    assert planned_binding.call_target_kind == "constructor"
    assert planned_binding.exact_output_field_name == "value"


def test_load_api_service_protocol_package_requires_stream_invoke_for_streamed_endpoint(
    tmp_path: Path,
) -> None:
    runtime_root = (
        _write_minimal_manifest_backed_service_protocol_package_runtime_package(
            runtime_root=tmp_path / "runtime",
            api_package_root=tmp_path / "api-package",
        )
    )
    service_protocol_root = (
        tmp_path
        / "api-package"
        / "python"
        / "aware_proof_protocol"
        / "aware_proof_protocol"
    )
    protocols_path = service_protocol_root / "protocols.py"
    protocols_path.write_text(
        "\n".join(
            [
                "from collections.abc import AsyncIterator",
                "from typing import Awaitable, Callable, Protocol, TypeAlias, cast",
                "from dataclasses import dataclass",
                "from pydantic import BaseModel",
                "",
                "class ServiceProtocolExecutionBackend(Protocol):",
                "    async def invoke_fulfillment(",
                "        self,",
                "        *,",
                "        fulfillment_name: str,",
                "        request: BaseModel,",
                "    ) -> object | None: ...",
                "",
                "class ServiceProtocolExecution(Protocol):",
                "    pass",
                "",
                "class OpenExecution(ServiceProtocolExecution, Protocol):",
                "    pass",
                "",
                (
                    "ServiceProtocolExecutionFactory: TypeAlias = Callable"
                    "[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]"
                ),
                (
                    "ServiceProtocolInvoker: TypeAlias = Callable"
                    "[[object, BaseModel, ServiceProtocolExecution | None], "
                    "Awaitable[object | None]]"
                ),
                (
                    "ServiceProtocolStreamInvoker: TypeAlias = Callable"
                    "[[object, BaseModel, ServiceProtocolExecution | None], "
                    "AsyncIterator[object]]"
                ),
                "",
                "async def invoke_openai__door__open(",
                "    handler: object,",
                "    request: BaseModel,",
                "    execution: OpenExecution | None = None,",
                ") -> object | None:",
                "    _ = handler",
                "    _ = request",
                "    _ = execution",
                "    return None",
                "",
                "def stream_invoke_openai__door__open(",
                "    handler: object,",
                "    request: BaseModel,",
                "    execution: OpenExecution | None = None,",
                ") -> AsyncIterator[object]:",
                "    _ = handler",
                "    _ = request",
                "    _ = execution",
                "    async def _empty() -> AsyncIterator[object]:",
                "        if False:",
                "            yield None",
                "    return _empty()",
                "",
                "def build_openai__door__open_execution(backend: ServiceProtocolExecutionBackend) -> OpenExecution:",
                "    return cast(OpenExecution, backend)",
                "",
                'PUBLIC_PACKAGE_IMPORT_ROOT = "aware_proof_api"',
                "",
                "@dataclass(frozen=True, slots=True)",
                "class ServiceProtocolEndpointBinding:",
                "    endpoint_ref: str",
                "    request_type_ref: str",
                "    response_type_ref: str | None",
                "    stream_event_type_refs: tuple[str, ...]",
                "    execution_protocol_ref: str | None",
                "    build_execution: ServiceProtocolExecutionFactory | None",
                "    stream_invoke: ServiceProtocolStreamInvoker | None",
                "    fulfillment_bindings: tuple[object, ...]",
                "    invoke: ServiceProtocolInvoker",
                "",
                "ENDPOINT_BINDINGS = {",
                '    "openai.door.open": ServiceProtocolEndpointBinding(',
                '        endpoint_ref="openai.door.open",',
                '        request_type_ref="aware_proof_api.models.open_request.OpenRequest",',
                "        response_type_ref=None,",
                '        stream_event_type_refs=("aware_proof_api.models.open_request.OpenRequest",),',
                '        execution_protocol_ref="aware_proof_protocol.protocols.OpenExecution",',
                "        build_execution=build_openai__door__open_execution,",
                "        stream_invoke=stream_invoke_openai__door__open,",
                "        fulfillment_bindings=(),",
                "        invoke=invoke_openai__door__open,",
                "    ),",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)

    binding = loaded.endpoint_bindings["openai.door.open"]
    assert binding.stream_event_type_refs == (
        "aware_proof_api.models.open_request.OpenRequest",
    )
    assert callable(binding.stream_invoke)


def test_load_api_service_protocol_package_is_scoped_by_runtime_package_dir(
    tmp_path: Path,
) -> None:
    first_runtime_root = _write_minimal_service_protocol_package_runtime_package(
        runtime_root=tmp_path / "runtime-a",
        request_type_ref="aware_proof_api.models.open_request.OpenRequest",
        response_type_ref=None,
    )
    second_runtime_root = _write_minimal_service_protocol_package_runtime_package(
        runtime_root=tmp_path / "runtime-b",
        request_type_ref="aware_proof_api.models.close_request.CloseRequest",
        response_type_ref="aware_proof_api.models.close_result.CloseResult",
    )

    first_loaded = load_api_service_protocol_package(
        runtime_package_dir=first_runtime_root
    )
    second_loaded = load_api_service_protocol_package(
        runtime_package_dir=second_runtime_root
    )

    first_binding = first_loaded.endpoint_bindings["openai.door.open"]
    second_binding = second_loaded.endpoint_bindings["openai.door.open"]
    assert (
        first_binding.request_type_ref
        == "aware_proof_api.models.open_request.OpenRequest"
    )
    assert first_binding.response_type_ref is None
    assert callable(first_binding.build_execution)
    assert (
        second_binding.request_type_ref
        == "aware_proof_api.models.close_request.CloseRequest"
    )
    assert (
        second_binding.response_type_ref
        == "aware_proof_api.models.close_result.CloseResult"
    )
    assert callable(second_binding.build_execution)


def test_load_api_service_protocol_package_preserves_same_runtime_module_identity(
    tmp_path: Path,
) -> None:
    runtime_root = _write_minimal_service_protocol_package_runtime_package(
        runtime_root=tmp_path / "runtime"
    )

    first_loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)
    first_protocols_module = import_module(
        f"{first_loaded.service_protocol_import_root}.protocols"
    )

    second_loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)
    second_protocols_module = import_module(
        f"{second_loaded.service_protocol_import_root}.protocols"
    )

    assert second_protocols_module is first_protocols_module
    assert (
        second_loaded.endpoint_bindings["openai.door.open"].invoke
        is first_loaded.endpoint_bindings["openai.door.open"].invoke
    )


def test_load_api_service_protocol_package_uses_manifest_backed_package_local_roots(
    tmp_path: Path,
) -> None:
    runtime_root = (
        _write_minimal_manifest_backed_service_protocol_package_runtime_package(
            runtime_root=tmp_path / "runtime",
            api_package_root=tmp_path / "apis" / "proof_api",
        )
    )

    loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)

    assert (
        loaded.public_package_root
        == tmp_path / "apis" / "proof_api" / "python" / "aware_proof_api"
    )
    assert loaded.service_protocol_package_root == (
        tmp_path / "apis" / "proof_api" / "python" / "aware_proof_protocol"
    )
    assert loaded.public_package_import_root == "aware_proof_api"
    assert loaded.service_protocol_import_root == "aware_proof_protocol"
    assert "openai.door.open" in loaded.endpoint_bindings


def test_load_api_service_protocol_package_prefers_runtime_artifact_roots_over_manifest_relpaths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "revision"
    runtime_root = workspace_root / ".aware" / "api" / "runtime" / "proof-api"
    api_package_root = workspace_root / "apis" / "proof_api"
    runtime_root = (
        _write_minimal_manifest_backed_service_protocol_package_runtime_package(
            runtime_root=runtime_root,
            api_package_root=api_package_root,
        )
    )
    manifest_path = runtime_root / "api.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["api_toml_path"] = "/missing/source/apis/proof_api/aware.api.toml"
    manifest["api_toml_relpath"] = "apis/proof_api/aware.api.toml"
    manifest["api_package_root_relpath"] = "apis/proof_api"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _ = _write_minimal_service_protocol_package_runtime_package(
        runtime_root=runtime_root
    )

    loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)

    assert loaded.public_package_root == (
        runtime_root / "public_package" / "python" / "package"
    )
    assert loaded.service_protocol_package_root == (
        runtime_root / "service_protocol" / "python" / "package"
    )
    assert "openai.door.open" in loaded.endpoint_bindings


def test_load_api_service_protocol_package_uses_relocatable_manifest_relpaths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "revision"
    runtime_root = workspace_root / ".aware" / "api" / "runtime" / "proof-api"
    api_package_root = workspace_root / "apis" / "proof_api"
    runtime_root = (
        _write_minimal_manifest_backed_service_protocol_package_runtime_package(
            runtime_root=runtime_root,
            api_package_root=api_package_root,
        )
    )
    manifest_path = runtime_root / "api.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["api_toml_path"] = "/missing/source/apis/proof_api/aware.api.toml"
    manifest["api_toml_relpath"] = "apis/proof_api/aware.api.toml"
    manifest["api_package_root_relpath"] = "apis/proof_api"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = load_api_service_protocol_package(runtime_package_dir=runtime_root)

    assert loaded.public_package_root == (
        workspace_root / "apis" / "proof_api" / "python" / "aware_proof_api"
    )
    assert loaded.service_protocol_package_root == (
        workspace_root / "apis" / "proof_api" / "python" / "aware_proof_protocol"
    )
    assert "openai.door.open" in loaded.endpoint_bindings


@pytest.mark.asyncio
async def test_decode_committed_api_call_request_into_generated_service_protocol_package_request_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        context = runtime.context
        assert context is not None
        runtime_index = context.index
        (
            request_class_config,
            request_attribute_name,
            primitive_base_type,
            request_attribute_value,
        ) = _select_runtime_inline_request_contract(runtime_index)
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )

        workspace_root = tmp_path / "service_protocol_package_workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        toml_path = _write_runtime_api_workspace(
            root=workspace_root,
            request_attribute_name=request_attribute_name,
            request_attribute_type=_aware_type_for_primitive(primitive_base_type),
        )
        compile_result = await _compile_api_workspace_in_thread(
            toml_path=toml_path,
            repo_root=workspace_root,
            materialize_service_protocol=True,
            dependency_graph_mode="meta_runtime",
        )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        assert service_protocol_materialization is not None
        assert compile_result.api_dto_package_materializations
        for dto_result in compile_result.api_dto_package_materializations:
            monkeypatch.syspath_prepend(str(dto_result.package_root))
        runtime_package_dir = service_protocol_materialization.runtime_package_dir

        lane = ApiMetaRuntimeLane(
            branch_id=uuid4(),
        )
        assert request_class_config.id is not None
        snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=lane.branch_id,
            projection_hash=api_projection_hash,
            api_name="openai",
            endpoint_refs=("openai.door.open",),
            endpoint_request_class_config_ids={
                "openai.door.open": request_class_config.id,
            },
            endpoint_fulfillment_names={"openai.door.open": ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        branch_id = lane.branch_id
        assert snapshot.endpoint_ids_by_ref["openai.door.open"]

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="openai.door.open",
            request_payload={request_attribute_name: request_attribute_value},
        )

        materialized = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            source_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            ),
            target_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_call_projection_hash,
            ),
            ir=ir,
        )
        envelope = build_resolved_api_invocation_envelope(
            ir=ir,
            materialized_call=materialized.binding,
        )

        decoded = await decode_committed_api_call_request(
            index=runtime_index,
            envelope=envelope,
            runtime_package_dir=runtime_package_dir,
        )

        assert decoded.endpoint_binding.endpoint_ref == envelope.endpoint_ref
        assert decoded.api_call.id == envelope.api_call_id
        assert decoded.request_class_config.id == request_class_config.id
        assert decoded.request_payload == {
            request_attribute_name: _expected_decoded_payload_value(
                request_attribute_value
            )
        }
        assert type(decoded.request_object).__name__ == "OpenRequest"
        assert (
            decoded.request_object.model_dump()[request_attribute_name]
            == request_attribute_value
        )


@pytest.mark.asyncio
async def test_build_api_service_dispatch_plan_merges_envelope_semantics_with_symbol_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_dispatch",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        context = runtime.context
        assert context is not None
        runtime_index = context.index
        (
            request_class_config,
            request_attribute_name,
            primitive_base_type,
            request_attribute_value,
        ) = _select_runtime_inline_request_contract(runtime_index)
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )

        workspace_root = tmp_path / "dispatch_workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        toml_path = _write_runtime_api_workspace(
            root=workspace_root,
            request_attribute_name=request_attribute_name,
            request_attribute_type=_aware_type_for_primitive(primitive_base_type),
        )
        compile_result = await _compile_api_workspace_in_thread(
            toml_path=toml_path,
            repo_root=workspace_root,
            materialize_service_protocol=True,
            dependency_graph_mode="meta_runtime",
        )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        assert service_protocol_materialization is not None
        assert compile_result.api_dto_package_materializations
        for dto_result in compile_result.api_dto_package_materializations:
            monkeypatch.syspath_prepend(str(dto_result.package_root))
        runtime_package_dir = service_protocol_materialization.runtime_package_dir

        lane = ApiMetaRuntimeLane(
            branch_id=uuid4(),
        )
        assert request_class_config.id is not None
        snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=lane.branch_id,
            projection_hash=api_projection_hash,
            api_name="openai",
            endpoint_refs=("openai.door.open",),
            endpoint_request_class_config_ids={
                "openai.door.open": request_class_config.id,
            },
            endpoint_fulfillment_names={"openai.door.open": ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        branch_id = lane.branch_id
        endpoint_function_id = snapshot.endpoint_function_ids_by_ref[
            "openai.door.open"
        ]["open"]

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="openai.door.open",
            request_payload={request_attribute_name: request_attribute_value},
        )
        materialized = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            source_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            ),
            target_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_call_projection_hash,
            ),
            ir=ir,
        )
        envelope = build_resolved_api_invocation_envelope(
            ir=ir,
            materialized_call=materialized.binding,
        )

        plan = await build_api_service_dispatch_plan(
            index=runtime_index,
            envelope=envelope,
            runtime_package_dir=runtime_package_dir,
        )

        assert plan.endpoint_ref == envelope.endpoint_ref
        assert plan.api_name == envelope.api_name
        assert plan.capability_name == envelope.capability_name
        assert plan.endpoint_name == envelope.endpoint_name
        assert len(plan.fulfillment_bindings) == 1
        assert (
            plan.fulfillment_bindings[0].name == envelope.fulfillment_bindings[0].name
        )
        assert (
            plan.fulfillment_bindings[0].graph_target
            == envelope.fulfillment_bindings[0].graph_target
        )
        assert (
            plan.fulfillment_bindings[0].graph_capability_function_name
            == envelope.fulfillment_bindings[0].graph_capability_function_name
        )
        assert (
            plan.fulfillment_bindings[0].graph_function_python_ref
            == "aware_home.home.Door.open"
        )
        assert plan.fulfillment_bindings[
            0
        ].graph_function_runtime_target == _load_planned_runtime_function_target(
            runtime_package_dir,
            endpoint_ref=envelope.endpoint_ref,
            fulfillment_name=envelope.fulfillment_bindings[0].name,
            graph_target=envelope.fulfillment_bindings[0].graph_target,
            graph_capability_function_name=envelope.fulfillment_bindings[
                0
            ].graph_capability_function_name,
            function_name="open",
        )
        assert (
            plan.fulfillment_bindings[0].api_capability_endpoint_function_id
            == endpoint_function_id
        )
        assert plan.request_type_ref.endswith(".OpenRequest")
        assert plan.execution_protocol_ref is not None
        assert callable(plan.build_execution)
        assert (
            plan.request_object.model_dump()[request_attribute_name]
            == request_attribute_value
        )
        assert callable(plan.invoke)

        import aware_api_runtime.service_protocol.runtime as service_protocol_runtime

        async def _fail_rematerialize_committed_api_call(**_: object) -> None:
            raise AssertionError(
                "materialized dispatch fast path must not re-materialize the committed ApiCall"
            )

        monkeypatch.setattr(
            service_protocol_runtime,
            "rematerialize_committed_api_call",
            _fail_rematerialize_committed_api_call,
        )
        fast_plan = await build_api_service_dispatch_plan_from_materialized_call(
            index=runtime_index,
            envelope=envelope,
            api_call=materialized.api_call,
            request_class_config=materialized.request_class_config,
            runtime_package_dir=runtime_package_dir,
        )

        assert fast_plan.envelope == plan.envelope
        assert fast_plan.endpoint_ref == plan.endpoint_ref
        assert fast_plan.request_object.model_dump() == plan.request_object.model_dump()
        assert fast_plan.fulfillment_bindings == plan.fulfillment_bindings
        assert callable(fast_plan.invoke)

        compact_api_call = materialized.api_call.model_copy(
            update={
                "request_model": InlineValueInstance.model_construct(
                    id=materialized.binding.request_model_id,
                    class_config_id=materialized.binding.request_class_config_id,
                    class_config=materialized.request_class_config,
                    owner_key=materialized.binding.call_key,
                    inline_value_instance_attributes=[],
                )
            }
        )
        compact_plan = await build_api_service_dispatch_plan_from_materialized_call(
            index=runtime_index,
            envelope=envelope,
            api_call=compact_api_call,
            request_class_config=materialized.request_class_config,
            runtime_package_dir=runtime_package_dir,
            request_payload_override={
                request_attribute_name: request_attribute_value,
            },
        )

        assert compact_plan.envelope == plan.envelope
        assert (
            compact_plan.request_object.model_dump() == plan.request_object.model_dump()
        )
