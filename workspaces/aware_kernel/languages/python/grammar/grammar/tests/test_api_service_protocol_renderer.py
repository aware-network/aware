from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_utils.string_transform import to_snake_case

_REPO_ROOT = Path(__file__).resolve().parents[5]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
)  # noqa: E402
from aware_meta.test_support import (
    make_function_attribute_edge,
    make_function_config,
)  # noqa: E402
from aware_meta.test_support import test_function_attribute_owner_key  # noqa: E402
from aware_api_runtime.ir import (  # noqa: E402
    build_api_compile_plan,
    emit_api_runtime_artifacts,
)
from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
from aware_api_runtime.models import ProjectionOwnedClassTruth  # noqa: E402
from aware_api_runtime.packages import (  # noqa: E402
    ApiProductRuntimeArtifactRef,
    ApiServiceProtocolRenderTarget,
    build_api_service_protocol_lowering_handoff,
    build_api_service_protocol_plan,
    build_api_service_protocol_render_inputs,
    build_api_service_protocol_render_job,
)
from aware_api_runtime.packages.materialization import (
    _load_profile_inputs,
)  # noqa: E402
from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: E402
    collect_api_dependency_class_config_ids_from_graphs,
)
from python_grammar.renderer_api_service_protocol import (  # noqa: E402
    API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION,
    API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME,
    PythonApiServiceProtocolRendererLanguage,
)


@dataclass
class _ServiceProtocolLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_home_story_protocol"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("models") / f"{to_snake_case(class_config.name)}.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("models") / f"{to_snake_case(enum_config.name)}.py"

    def get_function_file_path(self, function_config) -> Path:  # pragma: no cover
        return Path("models") / "functions.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        return ".".join(part for part in parts if part).strip(".")


def _write_api_toml(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "home-story-api"',
                'fqn_prefix = "aware_home_story_api"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_api_type_package(root: Path) -> None:
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
                "    fn lock(",
                "        force Bool = false",
                "    ) -> Bool {",
                '        """Lock this door."""',
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

    package_root = root / "apis" / "types" / "home"
    (package_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-api"',
                'fqn_prefix = "aware_home_api"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_home_api"',
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
                "class LockDoor {",
                "    label String",
                "}",
                "",
                "class LockDoorResult {",
                "    accepted Boolean",
                "}",
                "",
                "class DoorSnapshot {",
                "    label String",
                "    is_locked Boolean",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware" / "door" / "keys.aware").write_text(
        "\n".join(
            [
                "class DoorDevice {",
                "    device_id String",
                "    provider String",
                "    door_label String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_api_source(root: Path) -> None:
    _write_api_type_package(root)
    bindings = root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "home.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
                "    capability lock_door {",
                '        """Lock the front door."""',
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                '            """Lock command."""',
                "            response aware_home_api.door.LockDoorResult;",
                "            stream server {",
                '                """Server push state."""',
                "                event snapshot aware_home_api.door.DoorSnapshot;",
                "            }",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability lock_door {",
                "            function lock aware_home.home.Door.lock;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _projection_truth() -> dict[str, dict[str, ProjectionOwnedClassTruth]]:
    return {
        "aware_home.Home": {
            "Home": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Home",
                attributes=frozenset({"doors"}),
                identity_key_attributes=frozenset({"name"}),
                relationship_targets=(("doors", "Door"),),
            ),
            "Door": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Door",
                attributes=frozenset({"label", "is_locked"}),
                identity_key_attributes=frozenset({"label"}),
            ),
        }
    }


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive, child_links=[]
    )


def _attribute(
    *, owner_key: str, name: str, descriptor: AttributeTypeDescriptor
) -> AttributeConfig:
    return make_attribute_config(
        owner_key=owner_key,
        name=name,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        default_value=None,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _class(*, fqn: str, name: str, attributes: list[AttributeConfig]) -> ClassConfig:
    class_config = ClassConfig(
        class_fqn=fqn,
        name=name,
        is_base=True,
        class_config_attribute_configs=[],
    )
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=attribute,
            name=attribute.name,
            position=position,
        )
        for position, attribute in enumerate(attributes)
    ]
    return class_config


def _class_node(*, graph_id, class_config: ClassConfig) -> ObjectConfigGraphNode:
    return ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_config.class_fqn,
        class_config=class_config,
        object_config_graph_id=graph_id,
    )


def _graph(*, fqn_prefix: str, classes: list[ClassConfig]) -> ObjectConfigGraph:
    graph_id = uuid4()
    return ObjectConfigGraph(
        id=graph_id,
        name="home_api_types",
        hash="sha256:home_api_types",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=class_config)
            for class_config in classes
        ],
    )


def _accessible_graph() -> ObjectConfigGraph:
    request = _class(
        fqn="aware_home_api.door.LockDoor",
        name="LockDoor",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoor",
                name="label",
                descriptor=_primitive_desc(),
            )
        ],
    )
    response = _class(
        fqn="aware_home_api.door.LockDoorResult",
        name="LockDoorResult",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoorResult",
                name="accepted",
                descriptor=_primitive_desc(),
            )
        ],
    )
    snapshot = _class(
        fqn="aware_home_api.door.DoorSnapshot",
        name="DoorSnapshot",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.DoorSnapshot",
                name="is_locked",
                descriptor=_primitive_desc(),
            )
        ],
    )
    door = _class(
        fqn="aware_home.home.Door",
        name="Door",
        attributes=[
            _attribute(
                owner_key="aware_home.home.Door",
                name="label",
                descriptor=_primitive_desc(),
            )
        ],
    )
    lock_function = make_function_config(
        owner_key=str(door.class_fqn),
        name="lock",
        kind=FunctionKind.instance,
        is_async=True,
    )
    dry_run_attribute = _attribute(
        owner_key=test_function_attribute_owner_key(
            function_owner_key=str(door.class_fqn),
            function_name="lock",
            type=FunctionAttributeType.input,
        ),
        name="dry_run",
        descriptor=_primitive_desc(),
    )
    accepted_attribute = _attribute(
        owner_key=test_function_attribute_owner_key(
            function_owner_key=str(door.class_fqn),
            function_name="lock",
            type=FunctionAttributeType.output,
        ),
        name="accepted",
        descriptor=_primitive_desc(),
    )
    lock_function.function_config_attribute_configs = [
        make_function_attribute_edge(
            function_config_id=lock_function.id,
            attribute_config=dry_run_attribute,
            name=dry_run_attribute.name,
            type=FunctionAttributeType.input,
            position=0,
        ),
        make_function_attribute_edge(
            function_config_id=lock_function.id,
            attribute_config=accepted_attribute,
            name=accepted_attribute.name,
            type=FunctionAttributeType.output,
            position=1,
        ),
    ]
    door.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=door.id,
            function_config_id=lock_function.id,
            function_config=lock_function,
            position=0,
            is_public=True,
        )
    ]
    return _graph(
        fqn_prefix="aware_home_api",
        classes=[request, response, snapshot, door],
    )


def _build_product_b(tmp_path: Path) -> tuple[ObjectConfigGraph, dict[str, object]]:
    root = tmp_path.resolve()
    toml_path = _write_api_toml(root)
    _write_api_source(root)
    graph = _accessible_graph()

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    compile_plan = build_api_compile_plan(
        snapshot=result.snapshot,
        projection_truth_by_name=_projection_truth(),
        dependency_class_config_ids=collect_api_dependency_class_config_ids_from_graphs(
            accessible_graphs=(graph,),
        ),
    )
    runtime_artifacts = emit_api_runtime_artifacts(
        plan=compile_plan,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )
    service_plan = build_api_service_protocol_plan(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        api_ontology=compile_plan.api_ontology,
    )
    external_python_type_index_artifact = _write_external_python_type_index_artifact(
        runtime_root=root / "runtime"
    )
    handoff = build_api_service_protocol_lowering_handoff(
        plan=service_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
        service_protocol_plan_artifact=runtime_artifacts.service_protocol_plan,
        extra_runtime_artifacts=(external_python_type_index_artifact,),
    )
    render_job = build_api_service_protocol_render_job(
        handoff=handoff,
        target=ApiServiceProtocolRenderTarget(
            target_language=CodeLanguage.python,
            source_aware_toml_path=toml_path,
            target_output_dir=root / "render" / "python",
            package_root=root / "sdk" / "python",
            package_name="aware_home_story_protocol",
            import_root="aware_home_story_protocol",
            description="Generated Product B test package.",
        ),
    )
    render_job = build_api_service_protocol_render_inputs(render_job=render_job)
    payloads = _load_profile_inputs(
        aware_root=root,
        materialization_config=render_job.materialization_config,
    )
    return graph, payloads


def _write_external_python_type_index_artifact(
    *, runtime_root: Path
) -> ApiProductRuntimeArtifactRef:
    runtime_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "language": "python",
        "classes": {
            "demo-door-id": {
                "module": "aware_home_ontology.home.door",
                "name": "Door",
            }
        },
        "enums": {},
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()
    artifact_path = runtime_root / "api.external_python_type_index.json"
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return ApiProductRuntimeArtifactRef(
        kind="api.external_python_type_index",
        relpath="runtime/api.external_python_type_index.json",
        hash_sha256=digest,
    )


def _external_python_type_index_payload(
    *, graph: ObjectConfigGraph
) -> dict[str, object]:
    door_class = next(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
        and node.class_config.class_fqn == "aware_home.home.Door"
    )
    assert door_class is not None
    return {
        "language": "python",
        "classes": {
            str(door_class.id): {
                "module": "aware_home_ontology.home.door",
                "name": "Door",
            }
        },
        "enums": {},
    }


def test_api_service_protocol_renderer_emits_protocol_surface_without_dto_family(
    tmp_path: Path,
) -> None:
    graph, payloads = _build_product_b(tmp_path)
    payloads["api.external_python_type_index"] = _external_python_type_index_payload(
        graph=graph
    )
    layout = _ServiceProtocolLayout(
        base_dir=tmp_path / "render", import_root="aware_home_story_protocol"
    )
    layout.bind_graph(graph)

    renderer = PythonApiServiceProtocolRendererLanguage(layout_strategy=layout)
    renderer.bind_profile_inputs(payloads)
    renderer.bind_object_config_graph(graph)
    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code, CodeSectionBuilderIndex(), indent_size=renderer.indent
    ) as writer:
        renderer.emit_file([], writer)
    text = code.content_part_text.inline_text or ""
    sections = renderer.render_sections()
    section_by_key = {section.section_key: section for section in sections}

    assert text == "\n".join(line for section in sections for line in section.lines)
    assert section_by_key["api.service_protocol.module_prelude"].section_kind == (
        "service_protocol_module_prelude"
    )
    assert (
        section_by_key[
            "api.service_protocol.endpoint_execution:home_devices.lock_door.lock_door"
        ].section_kind
        == "service_protocol_endpoint_execution"
    )
    assert (
        section_by_key[
            "api.service_protocol.endpoint_invoker:home_devices.lock_door.lock_door"
        ].section_kind
        == "service_protocol_endpoint_invoker"
    )
    assert (
        section_by_key[
            "api.service_protocol.endpoint_binding:home_devices.lock_door.lock_door"
        ].section_kind
        == "service_protocol_endpoint_binding"
    )
    assert section_by_key["api.service_protocol.root_protocol"].section_kind == (
        "service_protocol_root_protocol"
    )
    assert (
        section_by_key["api.service_protocol.section_text_manifest"].section_kind
        == "service_protocol_section_text_manifest"
    )
    assert (
        API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME
        in section_by_key["api.service_protocol.__all__"].text
    )
    manifest = renderer.render_section_text_manifest()
    assert manifest["contract_version"] == (
        API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION
    )
    sections_payload = manifest["sections"]
    assert isinstance(sections_payload, list)
    manifest_entries = {
        str(entry["section_key"]): entry
        for entry in sections_payload
        if isinstance(entry, dict)
    }
    assert (
        manifest_entries[
            "api.service_protocol.endpoint_invoker:home_devices.lock_door.lock_door"
        ]["rendered_text_digest"]
        == section_by_key[
            "api.service_protocol.endpoint_invoker:home_devices.lock_door.lock_door"
        ].rendered_text_digest
    )
    manifest_json = _module_string_constant(
        module_text=text,
        constant_name=API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME,
    )
    assert json.loads(manifest_json) == manifest
    assert (
        "invoke_home_devices__lock_door__lock_door"
        in section_by_key[
            "api.service_protocol.endpoint_invoker:home_devices.lock_door.lock_door"
        ].text
    )
    assert (
        "HOME_DEVICES__LOCK_DOOR__LOCK_DOOR_PROTOCOL_BINDING"
        in section_by_key[
            "api.service_protocol.endpoint_binding:home_devices.lock_door.lock_door"
        ].text
    )

    assert "from aware_home_story_api.models.lock_door import LockDoor" in text
    assert (
        "from aware_home_story_api.models.lock_door_result import LockDoorResult"
        in text
    )
    assert "from aware_home_story_api.models.door_snapshot import DoorSnapshot" in text
    assert "PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = 'aware_home_story_api'" in text
    assert "HOME_DEVICES__LOCK_DOOR__LOCK_DOOR_PROTOCOL_BINDING" in text
    assert "class ServiceProtocolExecutionBackend(Protocol):" in text
    assert (
        "def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:"
        in text
    )
    assert (
        "async def invoke_home_devices__lock_door__lock_door(handler: object, request: BaseModel, "
        "execution: ServiceProtocolExecution | None = None) -> LockDoorResult:"
    ) in text
    assert "invoke=invoke_home_devices__lock_door__lock_door," in text
    assert "build_execution=build_home_devices__lock_door__lock_door_execution," in text
    assert "class HomeDevicesLockDoorCapabilityServiceProtocol(Protocol):" in text
    assert (
        "async def lock_door(self, request: LockDoor, execution: HomeDevicesLockDoorLockDoorExecution) "
        "-> LockDoorResult: ..."
    ) in text
    assert (
        "def stream_lock_door(self, request: LockDoor, execution: HomeDevicesLockDoorLockDoorExecution) -> "
        "AsyncIterator[HomeDevicesLockDoorLockDoorStreamEvent]: ..."
    ) in text
    assert (
        "class _HomeDevicesLockDoorLockDoorExecutionImpl(HomeDevicesLockDoorLockDoorExecution):"
        in text
    )
    assert "def build_home_devices__lock_door__lock_door_execution(" in text
    assert "class AwareHomeStoryServiceProtocol(Protocol):" in text
    assert "home_devices: HomeDevicesApiServiceProtocol" in text


def _module_string_constant(*, module_text: str, constant_name: str) -> str:
    tree = ast.parse(module_text)
    for node in tree.body:
        value_node: ast.expr | None = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == constant_name:
                value_node = node.value
        elif isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == constant_name
                for target in node.targets
            ):
                value_node = node.value
        if value_node is None:
            continue
        value = ast.literal_eval(value_node)
        assert isinstance(value, str)
        return value
    raise AssertionError(f"Missing module constant {constant_name!r}")
