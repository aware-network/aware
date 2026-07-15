"""
Runtime IR -> Dart lowering transformer.

Dart materializations are intended to be *flat data models* (Freezed-style) rather
than relying on inheritance. The runtime IR supports parent classes (e.g. Aware
`augment`) to express shared field sets; without lowering, those inherited fields
are lost in Dart output because renderers are emit-only.

This transformer keeps renderers honest by materializing inherited attributes
into each derived `ClassConfig` before rendering.
"""

from uuid import UUID

from typing_extensions import override

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_code_ontology.primitive.code_primitive_enums import (
    CodePrimitiveBaseType,
)
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer, ObjectConfigGraphTransformerPolicy
from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_attribute_config_id,
)
from aware_meta.fqn_resolver import NamespacePath

from dart_grammar.transformer_policy import DartTransformPolicy


class RuntimeToDartTransformer(ObjectConfigGraphTransformer):
    """
    Lower runtime IR into a Dart-ready graph.

    Current scope:
    - Flatten parent_class attributes into derived classes (single inheritance chain).
    """

    def __init__(
        self,
        *,
        namespace_by_code_id: dict[UUID, NamespacePath] | None = None,
        policy: DartTransformPolicy | None = None,
        external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
    ) -> None:
        self.namespace_by_code_id: dict[UUID, NamespacePath] = namespace_by_code_id or {}
        self.policy: DartTransformPolicy = policy or DartTransformPolicy.orm_default()
        self._external_graphs_by_id: dict[UUID, ObjectConfigGraph] = external_graphs_by_id or {}

    @override
    def set_policy(self, policy: ObjectConfigGraphTransformerPolicy) -> None:
        if policy is None:
            self.policy = DartTransformPolicy.orm_default()
            return
        if not isinstance(policy, DartTransformPolicy):
            raise TypeError(f"Unexpected policy for {type(self).__name__}: {type(policy).__name__}")
        self.policy = policy

    @override
    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: type[CodePrimitiveType] | None = None,
    ) -> ObjectConfigGraph:
        _ = code_primitive_type
        class_configs: list[ClassConfig] = []
        for node in object_config_graph.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                class_configs.append(node.class_config)

        class_by_id: dict[UUID, ClassConfig] = {cls.id: cls for cls in class_configs}

        # Snapshot original membership edges so lowering is stable regardless of iteration order.
        original_attr_edges_by_class_id: dict[UUID, list[ClassConfigAttributeConfig]] = {
            cls.id: cls.class_config_attribute_configs for cls in class_configs
        }

        for cls in class_configs:
            flattened = self._flatten_class_attributes(
                cls,
                class_by_id=class_by_id,
                original_attr_edges_by_class_id=original_attr_edges_by_class_id,
            )
            cls.class_config_attribute_configs = flattened

        if not self.policy.emit_non_opg_constructors:
            self._drop_internal_constructors(object_config_graph, class_configs)

        if self.policy.emit_orm_base_fields:
            self._ensure_dart_base_columns(class_configs)

        return object_config_graph

    def _drop_internal_constructors(self, ocg: ObjectConfigGraph, class_configs: list[ClassConfig]) -> None:
        """
        Remove constructor functions from Dart materialization unless they are registered
        as OPG constructors (virtual builds) on at least one ObjectProjectionGraph.

        Rationale:
        - Wire API only supports `call_target=INSTANCE` and `call_target=OPG_CONSTRUCTOR`.
        - Non-root constructors are runtime-internal building blocks invoked via propagation
          from an existing object (inside an in-process call chain), not as top-level API calls.
        - Dart should not emit network-callable wrappers for functions that cannot be routed.
        """

        allowed_constructor_link_ids: set[UUID] = set()
        for opg in ocg.object_projection_graphs or []:
            for ctor in opg.object_projection_graph_constructors or []:
                allowed_constructor_link_ids.add(ctor.function_constructor_id)

        dropped_constructor_function_ids: set[UUID] = set()
        for cls in class_configs:
            if not cls.class_config_function_configs:
                continue
            filtered: list[ClassConfigFunctionConfig] = []
            for link in cls.class_config_function_configs:
                if not link.is_constructor:
                    filtered.append(link)
                    continue
                if link.id in allowed_constructor_link_ids:
                    filtered.append(link)
                else:
                    if link.function_config_id is not None:
                        dropped_constructor_function_ids.add(link.function_config_id)
                    else:
                        dropped_constructor_function_ids.add(link.function_config.id)
            cls.class_config_function_configs = filtered

        if not dropped_constructor_function_ids:
            return

        # Keep graph node membership aligned with class membership policy:
        # constructors filtered from all class rails must not remain as standalone
        # function nodes in Dart materialization.
        ocg.object_config_graph_nodes = [
            node
            for node in ocg.object_config_graph_nodes
            if not (
                node.type == ObjectConfigGraphNodeType.function
                and node.function_config is not None
                and node.function_config.id in dropped_constructor_function_ids
            )
        ]

    def _ensure_dart_base_columns(self, class_configs: list[ClassConfig]) -> None:
        """
        Dart materializations are flat (no inheritance), so we synthesize ORM base fields
        that exist implicitly in Python ORMModel/BaseORMModel:
        - id (uuid, primary)

        Controlled by `DartTransformPolicy.emit_orm_base_fields` (ORM on, API off).
        """

        for cls in class_configs:
            if cls.value_mode == ClassValueMode.inline_value:
                continue
            by_name: dict[str, AttributeConfig] = {}
            for acc in cls.class_config_attribute_configs:
                attr = acc.attribute_config
                by_name[attr.name] = attr

            id_attr = by_name.get("id")
            if id_attr is None:
                id_attr = self._uuid_attr(
                    owner_key=cls.class_fqn,
                    name="id",
                    required=True,
                    unique=True,
                    key=f"dart_base:{cls.id}:id",
                    is_primary=True,
                )
                cls.class_config_attribute_configs.append(
                    ClassConfigAttributeConfig(
                        id=stable_class_config_attribute_config_id(
                            class_config_id=cls.id,
                            attribute_config_id=id_attr.id,
                        ),
                        class_config_id=cls.id,
                        attribute_config=id_attr,
                        attribute_config_id=id_attr.id,
                        name=id_attr.name,
                        position=-30,
                    )
                )
            else:
                id_attr.is_primary = True
                id_attr.is_required = True

    def _uuid_attr(
        self,
        *,
        owner_key: str,
        name: str,
        required: bool,
        unique: bool,
        key: str,
        is_primary: bool = False,
    ) -> AttributeConfig:
        prim_type = CodePrimitiveType(
            signature=CodePrimitiveBaseType.uuid.value,
            base_type=CodePrimitiveBaseType.uuid,
            constraints=None,
        )
        prim = PrimitiveConfig(primitive_type=prim_type, primitive_type_id=prim_type.id)
        desc = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
            primitive_config=prim,
            primitive_config_id=prim.id,
        )
        return AttributeConfig(
            id=stable_attribute_config_id(owner_key=owner_key, name=name),
            owner_key=owner_key,
            name=name,
            is_primary=is_primary,
            is_public=True,
            is_required=required,
            is_unique=unique,
            is_virtual=True,
            type_descriptor=desc,
        )

    def _flatten_class_attributes(
        self,
        cls: ClassConfig,
        *,
        class_by_id: dict[UUID, ClassConfig],
        original_attr_edges_by_class_id: dict[UUID, list[ClassConfigAttributeConfig]],
    ) -> list[ClassConfigAttributeConfig]:
        """
        Return a new `ClassConfigAttributeConfig[]` list for `cls` that includes
        all inherited attribute configs, with child overrides winning by attribute name.
        """

        lineage = self._ancestor_chain(cls, class_by_id=class_by_id)

        # attribute_name -> ("own"|"inherited", edge)
        selected: dict[str, tuple[str, ClassConfigAttributeConfig]] = {}

        # Add ancestors first (furthest -> closest), so closer ancestors override.
        for ancestor in lineage:
            for edge in original_attr_edges_by_class_id.get(ancestor.id, []):
                attr = edge.attribute_config
                selected[attr.name] = ("inherited", edge)

        # Add own last so the current class wins.
        for edge in original_attr_edges_by_class_id.get(cls.id, []):
            attr = edge.attribute_config
            selected[attr.name] = ("own", edge)

        flattened_edges: list[ClassConfigAttributeConfig] = []
        for _, (kind, edge) in selected.items():
            if kind == "own":
                flattened_edges.append(edge)
                continue

            attr = edge.attribute_config
            flattened_edges.append(
                ClassConfigAttributeConfig(
                    id=stable_class_config_attribute_config_id(
                        class_config_id=cls.id,
                        attribute_config_id=attr.id,
                    ),
                    class_config_id=cls.id,
                    attribute_config=attr,
                    attribute_config_id=attr.id,
                    name=attr.name,
                    position=edge.position,
                )
            )

        return flattened_edges

    def _ancestor_chain(self, cls: ClassConfig, *, class_by_id: dict[UUID, ClassConfig]) -> list[ClassConfig]:
        """
        Return the ancestor chain (root-first, excluding `cls`).
        """

        seen: set[UUID] = set()
        chain: list[ClassConfig] = []

        parent = self._resolve_parent(cls, class_by_id=class_by_id)
        while parent is not None:
            if parent.id in seen:
                raise ValueError(f"Cyclic parent_class chain detected at class_config_id={parent.id}")
            seen.add(parent.id)
            chain.append(parent)
            parent = self._resolve_parent(parent, class_by_id=class_by_id)

        chain.reverse()
        return chain

    def _resolve_parent(self, cls: ClassConfig, *, class_by_id: dict[UUID, ClassConfig]) -> ClassConfig | None:
        if cls.parent_class is not None:
            return cls.parent_class
        if cls.parent_class_id is not None:
            return class_by_id.get(cls.parent_class_id)
        return None


__all__ = ["RuntimeToDartTransformer"]
