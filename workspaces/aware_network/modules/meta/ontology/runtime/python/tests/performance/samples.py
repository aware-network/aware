from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import (
    CodePrimitiveBaseType,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
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
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

_SAMPLE_NAMESPACE = "aware:meta:performance:sample"


@dataclass(frozen=True, slots=True)
class MetaPerformanceGraphBundle:
    source_graph: ObjectConfigGraph
    dependency_graphs: tuple[ObjectConfigGraph, ...]


def meta_performance_sample_package_root() -> Path:
    return Path(__file__).resolve().parent / "sample_packages" / "meta_perf_lab"


def build_meta_performance_graph_bundle(
    *,
    source_class_count: int = 8,
    dependency_graph_count: int = 3,
    dependency_class_count: int = 4,
) -> MetaPerformanceGraphBundle:
    return MetaPerformanceGraphBundle(
        source_graph=build_meta_performance_runtime_graph(
            fqn_prefix="aware_meta_perf_lab",
            graph_name="meta_perf_lab",
            class_count=source_class_count,
            attributes_per_class=4,
            include_relationships=True,
        ),
        dependency_graphs=tuple(
            build_meta_performance_runtime_graph(
                fqn_prefix=f"aware_meta_perf_dep_{index}",
                graph_name=f"meta_perf_dep_{index}",
                class_count=dependency_class_count,
                attributes_per_class=3,
                include_relationships=True,
            )
            for index in range(dependency_graph_count)
        ),
    )


def build_meta_performance_runtime_graph(
    *,
    fqn_prefix: str = "aware_meta_perf_lab",
    graph_name: str = "meta_perf_lab",
    class_count: int = 8,
    attributes_per_class: int = 4,
    include_relationships: bool = True,
) -> ObjectConfigGraph:
    if class_count < 1:
        raise ValueError("class_count must be at least 1")
    if attributes_per_class < 1:
        raise ValueError("attributes_per_class must be at least 1")

    graph_id = _sample_uuid(f"graph:{fqn_prefix}:{graph_name}")
    classes = tuple(
        _sample_class(
            graph_id=graph_id,
            fqn_prefix=fqn_prefix,
            class_index=class_index,
            attributes_per_class=attributes_per_class,
        )
        for class_index in range(class_count)
    )
    if include_relationships and len(classes) > 1:
        for index, class_config in enumerate(classes[:-1]):
            target = classes[index + 1]
            attr = _class_ref_attr(
                owner=class_config,
                target=target,
                name=f"next_entity_{index:02d}",
            )
            class_config.class_config_attribute_configs.append(
                ClassConfigAttributeConfig(
                    id=_sample_uuid(f"{class_config.class_fqn}:edge_attr:{index}"),
                    class_config_id=class_config.id,
                    attribute_config=attr,
                    attribute_config_id=attr.id,
                    position=len(class_config.class_config_attribute_configs),
                )
            )
            class_config.class_config_relationships.append(
                _relationship_for_attr(
                    source=class_config,
                    target=target,
                    attr=attr,
                    key=f"{class_config.name}.next_entity_{index:02d}",
                )
            )

    return ObjectConfigGraph(
        id=graph_id,
        name=graph_name,
        hash=(
            f"{graph_name}:classes={class_count}:attrs={attributes_per_class}:"
            f"relationships={include_relationships}"
        ),
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                id=_sample_uuid(f"node:{class_config.class_fqn}"),
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_config.class_fqn,
                class_config=class_config,
                object_config_graph_id=graph_id,
            )
            for class_config in classes
        ],
    )


def _sample_class(
    *,
    graph_id: UUID,
    fqn_prefix: str,
    class_index: int,
    attributes_per_class: int,
) -> ClassConfig:
    class_name = f"PerfEntity{class_index:02d}"
    class_fqn = f"{fqn_prefix}.default.lab.{class_name}"
    class_config = ClassConfig(
        id=_sample_uuid(f"class:{class_fqn}"),
        class_fqn=class_fqn,
        name=class_name,
        description=f"Meta performance sample class {class_index}.",
        is_base=True,
    )
    class_config.class_config_attribute_configs = [
        _primitive_attribute_edge(
            owner=class_config,
            name=f"value_{attr_index:02d}",
            base_type=(
                CodePrimitiveBaseType.string
                if attr_index % 2 == 0
                else CodePrimitiveBaseType.float
            ),
            position=attr_index,
        )
        for attr_index in range(attributes_per_class)
    ]
    class_config.class_config_function_configs = [
        _function_edge(
            owner=class_config,
            name="describe",
            position=0,
            description="Describe this performance sample entity.",
        )
    ]
    _ = graph_id
    return class_config


def _primitive_attribute_edge(
    *,
    owner: ClassConfig,
    name: str,
    base_type: CodePrimitiveBaseType,
    position: int,
) -> ClassConfigAttributeConfig:
    descriptor = _primitive_descriptor(f"{owner.class_fqn}:attr:{name}", base_type)
    attr = AttributeConfig(
        id=_sample_uuid(f"attr:{owner.class_fqn}:{name}"),
        owner_key=owner.class_fqn,
        name=name,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )
    return ClassConfigAttributeConfig(
        id=_sample_uuid(f"attr_edge:{owner.class_fqn}:{name}"),
        class_config_id=owner.id,
        attribute_config=attr,
        attribute_config_id=attr.id,
        position=position,
    )


def _function_edge(
    *,
    owner: ClassConfig,
    name: str,
    position: int,
    description: str,
) -> ClassConfigFunctionConfig:
    function = FunctionConfig(
        id=_sample_uuid(f"function:{owner.class_fqn}:{name}"),
        owner_key=owner.class_fqn,
        name=name,
        description=description,
        kind=FunctionKind.instance,
    )
    input_attr = AttributeConfig(
        id=_sample_uuid(f"function_attr:{owner.class_fqn}:{name}:format"),
        owner_key=(f"{owner.class_fqn}.{name}::{FunctionAttributeType.input.value}"),
        name="format",
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_descriptor(
            f"{owner.class_fqn}:{name}:format",
            CodePrimitiveBaseType.string,
        ),
    )
    function.function_config_attribute_configs = [
        FunctionConfigAttributeConfig(
            id=_sample_uuid(f"function_attr_edge:{owner.class_fqn}:{name}:format"),
            function_config_id=function.id,
            attribute_config=input_attr,
            attribute_config_id=input_attr.id,
            name=input_attr.name,
            type=FunctionAttributeType.input,
            position=0,
        )
    ]
    return ClassConfigFunctionConfig(
        id=_sample_uuid(f"function_edge:{owner.class_fqn}:{name}"),
        class_config_id=owner.id,
        function_config=function,
        function_config_id=function.id,
        is_public=True,
        is_constructor=False,
        position=position,
    )


def _class_ref_attr(
    *,
    owner: ClassConfig,
    target: ClassConfig,
    name: str,
) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(
        id=_sample_uuid(f"type:class:{owner.class_fqn}:{name}"),
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )
    return AttributeConfig(
        id=_sample_uuid(f"attr:{owner.class_fqn}:{name}"),
        owner_key=owner.class_fqn,
        name=name,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _relationship_for_attr(
    *,
    source: ClassConfig,
    target: ClassConfig,
    attr: AttributeConfig,
    key: str,
) -> ClassConfigRelationship:
    relationship = ClassConfigRelationship(
        id=_sample_uuid(f"relationship:{source.class_fqn}:{key}"),
        class_config_id=source.id,
        target_class_config_id=target.id,
        relationship_key=key,
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.lazy,
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            id=_sample_uuid(f"relationship_attr:{source.class_fqn}:{key}"),
            class_config_relationship_id=relationship.id,
            attribute_config_id=attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    return relationship


def _primitive_descriptor(
    key: str,
    base_type: CodePrimitiveBaseType,
) -> AttributeTypeDescriptor:
    primitive_type = build_code_primitive_type(base_type=base_type)
    primitive_config = PrimitiveConfig(
        id=_sample_uuid(f"primitive_config:{key}:{base_type.value}"),
        primitive_type=primitive_type,
        primitive_type_id=primitive_type.id,
    )
    return AttributeTypeDescriptor(
        id=_sample_uuid(f"type:primitive:{key}:{base_type.value}"),
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )


def _sample_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_SAMPLE_NAMESPACE}:{key}")


__all__ = [
    "MetaPerformanceGraphBundle",
    "build_meta_performance_graph_bundle",
    "build_meta_performance_runtime_graph",
    "meta_performance_sample_package_root",
]
