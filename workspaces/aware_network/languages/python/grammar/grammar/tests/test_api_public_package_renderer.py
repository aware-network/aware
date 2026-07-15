from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from uuid import uuid4

from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.schemas import (
    API_PUBLIC_PACKAGE_KIND,
    API_PUBLIC_PACKAGE_RENDERER_PROFILE,
    MaterializationSource,
)
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
from aware_api_runtime.interface.builder import (  # noqa: E402
    build_api_interface_spec,
    emit_api_interface_spec_artifact,
)
from aware_api_runtime.invocation.builder import (  # noqa: E402
    build_api_invocation_manifest,
    emit_api_invocation_manifest_artifact,
)
from aware_api_runtime.models import (  # noqa: E402
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityEndpointResponseConfigOwnership,
    APICapabilityEndpointStreamConfigOwnership,
    APICapabilityEndpointStreamEventConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.packages import (  # noqa: E402
    ApiProductBackendHandoff,
    ApiPublicPackageRenderTarget,
    ApiPublicPackageApiPlan,
    ApiPublicPackageCapabilityPlan,
    ApiPublicPackageEndpointPlan,
    ApiPublicPackagePlan,
    ApiPublicPackageRequestPlan,
    ApiPublicPackageResponsePlan,
    ApiPublicPackageStreamEventPlan,
    ApiPublicPackageStreamPlan,
    build_api_public_package_dto_graph,
    build_api_public_package_lowering_handoff,
    build_api_public_package_render_inputs,
    build_api_public_package_render_job,
    emit_api_public_package_plan_artifact,
)
from aware_api_runtime.packages.materialization import (
    _load_profile_inputs,
)  # noqa: E402
from python_grammar.renderer_api_public_package import (  # noqa: E402
    PythonApiPublicPackageBindingsRendererLanguage,
    PythonApiPublicPackageClientRendererLanguage,
)
from python_grammar.renderer import PythonRenderer  # noqa: E402
from python_grammar.renderer_policy import PythonRenderPolicy  # noqa: E402


@dataclass
class _PublicPackageLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_home_story_sdk"

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


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive, child_links=[]
    )


def _attribute(
    *,
    owner_key: str,
    name: str,
    descriptor: AttributeTypeDescriptor,
    description: str | None = None,
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
        description=description,
    )


def _class(
    *,
    fqn: str,
    name: str,
    attributes: list[AttributeConfig],
    description: str | None = None,
) -> ClassConfig:
    class_config = ClassConfig(
        class_fqn=fqn,
        name=name,
        is_base=True,
        description=description,
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


def _api_ownership() -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="home_devices",
            source_path="apis/bindings/home.apis.aware",
            capabilities=(
                APICapabilityOwnership(
                    name="lock_door",
                    description="Lock the front door.",
                    source_path="apis/bindings/home.apis.aware",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="lock_door",
                            description="Lock command.",
                            source_path="apis/bindings/home.apis.aware",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref="aware_home_api.door.LockDoor",
                                source_path="apis/types/home/aware/door/endpoints.aware",
                                description="Lock request.",
                                response_config=APICapabilityEndpointResponseConfigOwnership(
                                    class_ref="aware_home_api.door.LockDoorResult",
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                    description="Lock result.",
                                ),
                                stream_config=APICapabilityEndpointStreamConfigOwnership(
                                    stream_mode="server",
                                    source_path="apis/bindings/home.apis.aware",
                                    description="Server push state.",
                                    event_configs=(
                                        APICapabilityEndpointStreamEventConfigOwnership(
                                            kind="snapshot",
                                            class_ref="aware_home_api.door.DoorSnapshot",
                                            source_path="apis/types/home/aware/door/endpoints.aware",
                                            description="Snapshot event.",
                                        ),
                                    ),
                                ),
                            ),
                            functions=(
                                APICapabilityEndpointFunctionOwnership(
                                    name="lock",
                                    graph_target="aware_home",
                                    graph_capability_function_name="lock",
                                    source_path="apis/bindings/home.apis.aware",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            graphs=(),
        ),
    )


def _public_plan() -> ApiPublicPackagePlan:
    return ApiPublicPackagePlan(
        schema_version=1,
        package_name="home-story-api",
        fqn_prefix="aware_home_story_api",
        backend_handoff=ApiProductBackendHandoff(
            materialization_source=MaterializationSource.api,
            aware_package_kind=API_PUBLIC_PACKAGE_KIND,
            expected_renderer_profile=API_PUBLIC_PACKAGE_RENDERER_PROFILE,
        ),
        apis=(
            ApiPublicPackageApiPlan(
                name="home_devices",
                description=None,
                source_path="apis/bindings/home.apis.aware",
                capabilities=(
                    ApiPublicPackageCapabilityPlan(
                        api_name="home_devices",
                        name="lock_door",
                        description="Lock the front door.",
                        source_path="apis/bindings/home.apis.aware",
                        endpoints=(
                            ApiPublicPackageEndpointPlan(
                                api_name="home_devices",
                                capability_name="lock_door",
                                name="lock_door",
                                discriminant="home_devices.lock_door.lock_door",
                                description="Lock command.",
                                source_path="apis/bindings/home.apis.aware",
                                request=ApiPublicPackageRequestPlan(
                                    class_ref="aware_home_api.door.LockDoor",
                                    description="Lock request.",
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                ),
                                response=ApiPublicPackageResponsePlan(
                                    class_ref="aware_home_api.door.LockDoorResult",
                                    description="Lock result.",
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                ),
                                stream=ApiPublicPackageStreamPlan(
                                    stream_mode="server",
                                    description="Server push state.",
                                    source_path="apis/bindings/home.apis.aware",
                                    events=(
                                        ApiPublicPackageStreamEventPlan(
                                            kind="snapshot",
                                            class_ref="aware_home_api.door.DoorSnapshot",
                                            description="Snapshot event.",
                                            source_path="apis/types/home/aware/door/endpoints.aware",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _accessible_graph() -> ObjectConfigGraph:
    request = _class(
        fqn="aware_home_api.door.LockDoor",
        name="LockDoor",
        description="Generated Product A request DTO.",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoor",
                name="label",
                descriptor=_primitive_desc(),
                description="Product B label detail.",
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
    return _graph(
        fqn_prefix="aware_home_api",
        classes=[request, response, snapshot],
    )


def _build_product_a(tmp_path: Path) -> tuple[ObjectConfigGraph, dict[str, object]]:
    repo_root = tmp_path.resolve()
    runtime_package_dir = repo_root / "runtime"
    source_toml_path = repo_root / "aware.api.toml"
    source_toml_path.write_text("aware_api = 1\n", encoding="utf-8")

    api_ownership = _api_ownership()
    public_plan = _public_plan()
    interface_spec = build_api_interface_spec(
        package_name="home-story-api",
        fqn_prefix="aware_home_story_api",
        api_ownership=api_ownership,
    )
    invocation_manifest = build_api_invocation_manifest(
        package_name="home-story-api",
        fqn_prefix="aware_home_story_api",
        api_ownership=api_ownership,
    )

    interface_artifact = emit_api_interface_spec_artifact(
        spec=interface_spec,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    invocation_artifact = emit_api_invocation_manifest_artifact(
        manifest=invocation_manifest,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    public_plan_artifact = emit_api_public_package_plan_artifact(
        plan=public_plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )

    handoff = build_api_public_package_lowering_handoff(
        plan=public_plan,
        interface_spec_artifact=interface_artifact,
        invocation_manifest_artifact=invocation_artifact,
        public_package_plan_artifact=public_plan_artifact,
    )
    render_job = build_api_public_package_render_job(
        handoff=handoff,
        target=ApiPublicPackageRenderTarget(
            target_language=CodeLanguage.python,
            source_aware_toml_path=source_toml_path,
            target_output_dir=repo_root / "render" / "python",
            package_root=repo_root / "sdk" / "python",
            package_name="aware_home_story_sdk",
            import_root="aware_home_story_sdk",
            description="Generated Product A test package.",
        ),
    )
    render_job = build_api_public_package_render_inputs(render_job=render_job)

    dto_graph = build_api_public_package_dto_graph(
        plan=public_plan,
        accessible_graphs=(_accessible_graph(),),
    )
    payloads = _load_profile_inputs(
        aware_root=repo_root,
        materialization_config=render_job.materialization_config,
    )
    return dto_graph, payloads


def test_api_public_package_support_renderers_emit_bindings_and_client(
    tmp_path: Path,
) -> None:
    dto_graph, payloads = _build_product_a(tmp_path)
    layout = _PublicPackageLayout(
        base_dir=tmp_path / "render", import_root="aware_home_story_sdk"
    )
    layout.bind_graph(dto_graph)

    bindings_renderer = PythonApiPublicPackageBindingsRendererLanguage(
        layout_strategy=layout
    )
    bindings_renderer.bind_profile_inputs(payloads)
    bindings_renderer.bind_object_config_graph(dto_graph)
    bindings_code = bindings_renderer.create_empty_code()
    with CodeSectionWriter(
        bindings_code, CodeSectionBuilderIndex(), indent_size=bindings_renderer.indent
    ) as writer:
        bindings_renderer.emit_file([], writer)
    bindings_text = bindings_code.content_part_text.inline_text or ""

    assert "API_INTERFACE_SPEC" in bindings_text
    assert "API_INVOCATION_MANIFEST" in bindings_text
    assert "HOME_DEVICES__LOCK_DOOR__LOCK_DOOR_ENDPOINT_REF" in bindings_text
    assert (
        "'python_model_ref': 'aware_home_story_sdk.models.lock_door.LockDoor'"
        in bindings_text
    )
    assert (
        "'python_model_ref': "
        "'aware_home_story_sdk.models.lock_door_result.LockDoorResult'"
    ) in bindings_text
    assert (
        "'python_model_ref': "
        "'aware_home_story_sdk.models.door_snapshot.DoorSnapshot'"
    ) in bindings_text

    client_renderer = PythonApiPublicPackageClientRendererLanguage(
        layout_strategy=layout
    )
    client_renderer.bind_profile_inputs(payloads)
    client_renderer.bind_object_config_graph(dto_graph)
    client_code = client_renderer.create_empty_code()
    with CodeSectionWriter(
        client_code, CodeSectionBuilderIndex(), indent_size=client_renderer.indent
    ) as writer:
        client_renderer.emit_file([], writer)
    client_text = client_code.content_part_text.inline_text or ""

    assert "from aware_api import AwareApiEndpointInvoker" in client_text
    assert "from typing import AsyncIterator, cast" in client_text
    assert "from .models.lock_door import LockDoor" in client_text
    assert "from .models.lock_door_result import LockDoorResult" in client_text
    assert "from .models.door_snapshot import DoorSnapshot" in client_text
    assert "HomeDevicesLockDoorLockDoorStreamEvent = DoorSnapshot" in client_text
    assert "class AwareHomeStorySdkClient:" in client_text
    assert "class HomeDevicesLockDoorCapabilityClient:" in client_text
    assert "def __init__(self, client: AwareApiEndpointInvoker) -> None:" in client_text
    assert (
        "async def lock_door(self, request: LockDoor) -> LockDoorResult:" in client_text
    )
    assert (
        "async def stream_lock_door(self, request: LockDoor) -> "
        "AsyncIterator[HomeDevicesLockDoorLockDoorStreamEvent]:"
    ) in client_text
    assert "endpoint_ref=HOME_DEVICES__LOCK_DOOR__LOCK_DOOR_ENDPOINT_REF" in client_text
    assert "async for event in self._client.stream_api_endpoint(" in client_text


def test_api_public_package_model_renderer_scrubs_internal_product_labels(
    tmp_path: Path,
) -> None:
    dto_graph, payloads = _build_product_a(tmp_path)
    layout = _PublicPackageLayout(
        base_dir=tmp_path / "render", import_root="aware_home_story_sdk"
    )
    layout.bind_graph(dto_graph)
    lock_door = next(
        node.class_config
        for node in dto_graph.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "LockDoor"
    )

    renderer = PythonRenderer(
        layout_strategy=layout, policy=PythonRenderPolicy.api_default()
    )
    renderer.bind_profile_inputs(payloads)
    renderer.bind_object_config_graph(dto_graph)
    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code, CodeSectionBuilderIndex(), indent_size=renderer.indent
    ) as writer:
        renderer.emit_file([lock_door], writer)
    text = code.content_part_text.inline_text or ""

    assert "Generated API client request DTO." in text
    assert 'description="service protocol label detail."' in text
    assert "Product A" not in text
    assert "Product B" not in text
