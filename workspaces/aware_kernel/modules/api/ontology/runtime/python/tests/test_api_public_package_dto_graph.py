from __future__ import annotations

from pathlib import Path
import sys
from uuid import UUID, uuid4

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: E402
from aware_meta_ontology.attribute.attribute_config import AttributeConfig  # noqa: E402
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)  # noqa: E402
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)  # noqa: E402
from aware_meta_ontology.annotation.code_section_annotation_discriminate import (  # noqa: E402
    CodeSectionAnnotationDiscriminate,
)
from aware_meta_ontology.class_.class_config import ClassConfig  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph_annotation import (  # noqa: E402
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (  # noqa: E402
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)  # noqa: E402

from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
)  # noqa: E402

from aware_api_runtime.packages import (
    build_api_public_package_dto_graph,
)  # noqa: E402
from aware_api_runtime.packages.models import (  # noqa: E402
    ApiProductBackendHandoff,
    ApiPublicPackageApiPlan,
    ApiPublicPackageCapabilityPlan,
    ApiPublicPackageEndpointPlan,
    ApiPublicPackagePlan,
    ApiPublicPackageRequestPlan,
    ApiPublicPackageResponsePlan,
    ApiPublicPackageStreamEventPlan,
    ApiPublicPackageStreamPlan,
)
from aware_meta.materialization.schemas import (  # noqa: E402
    API_PUBLIC_PACKAGE_KIND,
    API_PUBLIC_PACKAGE_RENDERER_PROFILE,
    MaterializationSource,
)


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive, child_links=[]
    )


def _class_desc(*, class_config: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=class_config.id,
        child_links=[],
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


def _class(
    *,
    fqn: str,
    name: str,
    attributes: list[AttributeConfig],
    parent_class: ClassConfig | None = None,
) -> ClassConfig:
    class_config = ClassConfig(
        class_fqn=fqn,
        name=name,
        is_base=parent_class is None,
        class_config_attribute_configs=[],
        parent_class=parent_class,
        parent_class_id=parent_class.id if parent_class is not None else None,
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


def _class_node(*, graph_id: UUID, class_config: ClassConfig) -> ObjectConfigGraphNode:
    return ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_config.class_fqn,
        class_config=class_config,
        object_config_graph_id=graph_id,
    )


def _graph(
    *,
    fqn_prefix: str,
    classes: list[ClassConfig],
    annotations: list[ObjectConfigGraphAnnotation] | None = None,
) -> ObjectConfigGraph:
    graph_id = uuid4()
    copied_annotations: list[ObjectConfigGraphAnnotation] = []
    for annotation in annotations or []:
        copied = annotation.model_copy(deep=True)
        copied.object_config_graph_id = graph_id
        copied_annotations.append(copied)
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
        object_config_graph_annotations=copied_annotations,
    )


def _plan() -> ApiPublicPackagePlan:
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
                        description=None,
                        source_path="apis/bindings/home.apis.aware",
                        endpoints=(
                            ApiPublicPackageEndpointPlan(
                                api_name="home_devices",
                                capability_name="lock_door",
                                name="lock_door",
                                discriminant="home_devices.lock_door.lock_door",
                                description=None,
                                source_path="apis/bindings/home.apis.aware",
                                request=ApiPublicPackageRequestPlan(
                                    class_ref="aware_home_api.door.LockDoor",
                                    description=None,
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                ),
                                response=ApiPublicPackageResponsePlan(
                                    class_ref="aware_home_api.door.LockDoorResult",
                                    description=None,
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                ),
                                stream=ApiPublicPackageStreamPlan(
                                    stream_mode="server",
                                    description=None,
                                    source_path="apis/bindings/home.apis.aware",
                                    events=(
                                        ApiPublicPackageStreamEventPlan(
                                            kind="snapshot",
                                            class_ref="aware_home_api.door.DoorSnapshot",
                                            description=None,
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


def test_build_api_public_package_dto_graph_collects_root_and_transitive_classes() -> (
    None
):
    status = _class(
        fqn="aware_home_api.door.DoorStatus",
        name="DoorStatus",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.DoorStatus",
                name="locked",
                descriptor=_primitive_desc(),
            )
        ],
    )
    request = _class(
        fqn="aware_home_api.door.LockDoor",
        name="LockDoor",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoor",
                name="status",
                descriptor=_class_desc(class_config=status),
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
                name="label",
                descriptor=_primitive_desc(),
            )
        ],
    )
    accessible_graph = _graph(
        fqn_prefix="aware_home_api",
        classes=[request, response, snapshot, status],
    )

    dto_graph = build_api_public_package_dto_graph(
        plan=_plan(),
        accessible_graphs=(accessible_graph,),
    )

    assert dto_graph.fqn_prefix == "aware_home_story_api"
    assert dto_graph.name == "home_story_api_public_package_dto"
    assert [node.node_key for node in dto_graph.object_config_graph_nodes] == [
        "aware_home_api.door.DoorSnapshot",
        "aware_home_api.door.DoorStatus",
        "aware_home_api.door.LockDoor",
        "aware_home_api.door.LockDoorResult",
    ]


def test_build_api_public_package_dto_graph_collects_parent_class_chain() -> None:
    request_base = _class(
        fqn="aware_home_api.door.LockDoorEnvelope",
        name="LockDoorEnvelope",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoorEnvelope",
                name="request_id",
                descriptor=_primitive_desc(),
            )
        ],
    )
    request = _class(
        fqn="aware_home_api.door.LockDoor",
        name="LockDoor",
        parent_class=request_base,
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
                name="label",
                descriptor=_primitive_desc(),
            )
        ],
    )
    accessible_graph = _graph(
        fqn_prefix="aware_home_api",
        classes=[request_base, request, response, snapshot],
    )

    dto_graph = build_api_public_package_dto_graph(
        plan=_plan(),
        accessible_graphs=(accessible_graph,),
    )

    assert [node.node_key for node in dto_graph.object_config_graph_nodes] == [
        "aware_home_api.door.DoorSnapshot",
        "aware_home_api.door.LockDoor",
        "aware_home_api.door.LockDoorEnvelope",
        "aware_home_api.door.LockDoorResult",
    ]


def test_build_api_public_package_dto_graph_preserves_discriminate_annotations_for_selected_classes() -> (
    None
):
    request_base = _class(
        fqn="aware_home_api.door.LockDoorEvent",
        name="LockDoorEvent",
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoorEvent",
                name="kind",
                descriptor=_primitive_desc(),
            )
        ],
    )
    request = _class(
        fqn="aware_home_api.door.LockDoorSnapshot",
        name="LockDoorSnapshot",
        parent_class=request_base,
        attributes=[
            _attribute(
                owner_key="aware_home_api.door.LockDoorSnapshot",
                name="kind",
                descriptor=_primitive_desc(),
            ),
            _attribute(
                owner_key="aware_home_api.door.LockDoorSnapshot",
                name="label",
                descriptor=_primitive_desc(),
            ),
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
    key_annotation = CodeSectionAnnotationDiscriminate(
        fqn_prefix="aware_home_api",
        domain_name="default",
        schema_name="door",
        class_name="LockDoorEvent",
        attribute_name="kind",
        mode="key",
    )
    tag_annotation = CodeSectionAnnotationDiscriminate(
        fqn_prefix="aware_home_api",
        domain_name="default",
        schema_name="door",
        class_name="LockDoorSnapshot",
        attribute_name="kind",
        mode="tag",
        tag_value="snapshot",
        source_position=17,
    )
    accessible_graph = _graph(
        fqn_prefix="aware_home_api",
        classes=[request_base, request, response],
        annotations=[
            ObjectConfigGraphAnnotation(
                kind=ObjectConfigGraphAnnotationKind.discriminate,
                object_config_graph_id=uuid4(),
                code_section_annotation_discriminate=key_annotation,
                code_section_annotation_discriminate_id=key_annotation.id,
            ),
            ObjectConfigGraphAnnotation(
                kind=ObjectConfigGraphAnnotationKind.discriminate,
                object_config_graph_id=uuid4(),
                code_section_annotation_discriminate=tag_annotation,
                code_section_annotation_discriminate_id=tag_annotation.id,
            ),
        ],
    )
    plan = ApiPublicPackagePlan(
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
                        description=None,
                        source_path="apis/bindings/home.apis.aware",
                        endpoints=(
                            ApiPublicPackageEndpointPlan(
                                api_name="home_devices",
                                capability_name="lock_door",
                                name="lock_door",
                                discriminant="home_devices.lock_door.lock_door",
                                description=None,
                                source_path="apis/bindings/home.apis.aware",
                                request=ApiPublicPackageRequestPlan(
                                    class_ref="aware_home_api.door.LockDoorSnapshot",
                                    description=None,
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                ),
                                response=ApiPublicPackageResponsePlan(
                                    class_ref="aware_home_api.door.LockDoorResult",
                                    description=None,
                                    source_path="apis/types/home/aware/door/endpoints.aware",
                                ),
                                stream=None,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    dto_graph = build_api_public_package_dto_graph(
        plan=plan,
        accessible_graphs=(accessible_graph,),
    )

    annotations = list(dto_graph.object_config_graph_annotations)
    assert len(annotations) == 2
    assert {annotation.kind for annotation in annotations} == {
        ObjectConfigGraphAnnotationKind.discriminate,
    }
    assert {
        annotation.code_section_annotation_discriminate.class_name
        for annotation in annotations
        if annotation.code_section_annotation_discriminate is not None
    } == {"LockDoorEvent", "LockDoorSnapshot"}


def test_build_api_public_package_dto_graph_fails_closed_on_missing_class_ref() -> None:
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
    accessible_graph = _graph(
        fqn_prefix="aware_home_api",
        classes=[request],
    )

    try:
        _ = build_api_public_package_dto_graph(
            plan=_plan(),
            accessible_graphs=(accessible_graph,),
        )
    except RuntimeError as exc:
        assert "Could not resolve public API package DTO class ref" in str(exc)
    else:
        raise AssertionError(
            "Expected missing public API package DTO class ref to fail closed."
        )


def test_build_api_public_package_dto_graph_matches_runtime_graph_fqns() -> None:
    accessible_graph = _graph(
        fqn_prefix="aware_home_api",
        classes=[
            _class(
                fqn="aware_home_api.default.door.LockDoor",
                name="LockDoor",
                attributes=[
                    _attribute(
                        owner_key="aware_home_api.default.door.LockDoor",
                        name="label",
                        descriptor=_primitive_desc(),
                    )
                ],
            ),
            _class(
                fqn="aware_home_api.default.door.LockDoorResult",
                name="LockDoorResult",
                attributes=[
                    _attribute(
                        owner_key="aware_home_api.default.door.LockDoorResult",
                        name="accepted",
                        descriptor=_primitive_desc(),
                    )
                ],
            ),
            _class(
                fqn="aware_home_api.default.door.DoorSnapshot",
                name="DoorSnapshot",
                attributes=[
                    _attribute(
                        owner_key="aware_home_api.default.door.DoorSnapshot",
                        name="label",
                        descriptor=_primitive_desc(),
                    )
                ],
            ),
        ],
    )

    dto_graph = build_api_public_package_dto_graph(
        plan=_plan(),
        accessible_graphs=(accessible_graph,),
    )

    assert [node.node_key for node in dto_graph.object_config_graph_nodes] == [
        "aware_home_api.default.door.DoorSnapshot",
        "aware_home_api.default.door.LockDoor",
        "aware_home_api.default.door.LockDoorResult",
    ]
