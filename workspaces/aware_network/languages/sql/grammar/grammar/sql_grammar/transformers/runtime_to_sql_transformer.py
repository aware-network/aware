"""
Runtime IR -> SQL lowering transformer.

This transformer exists to keep SQL materialization honest:
- Runtime IR remains the SSOT for FK/edge/runtime semantics.
- SQL may require additional *DDL-only* artifacts (e.g. join tables).

Postgres-first.
"""

from __future__ import annotations

from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_association import (
    ClassConfigRelationshipAssociation,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
from aware_meta.graph.config.package.constants import deterministic_uuid
from aware_meta.graph.config.namespace_index import build_namespace_index
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.relationship_analysis import (
    analyze_relationships,
    index_fk_override_annotations,
    resolve_fk_override,
)
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
    GeneratedObjectConfigGraphNodeIntent,
    GeneratedObjectConfigGraphNodeFilePolicy,
)

from aware_utils.string_transform import singularize, to_pascal_case, to_snake_case
from typing_extensions import override

from sql_grammar.transformer_policy import SQLTransformPolicy


class RuntimeToSQLTransformer(ObjectConfigGraphTransformer):
    """
    Lower a runtime IR graph into a SQL-ready graph.

    Current scope (v1):
    - Synthesize join-table association classes for pure MANY_TO_MANY relationships
      that have no explicit association edge in SSOT.
    - Synthesize join-table association classes for cross-package ONE_TO_MANY relationships
      where the FK would otherwise live on an external (dependency) class.
    """

    def __init__(
        self,
        *,
        namespace_by_code_id: dict[UUID, NamespacePath] | None = None,
        external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
    ):
        self.namespace_by_code_id: dict[UUID, NamespacePath] = namespace_by_code_id or {}
        self._generated_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
        self._external_graphs_by_id: dict[UUID, ObjectConfigGraph] = external_graphs_by_id or {}
        self.policy = SQLTransformPolicy.projection_default()

    @override
    def set_policy(self, policy: object | None) -> None:
        if policy is None:
            self.policy = SQLTransformPolicy.projection_default()
            return
        if not isinstance(policy, SQLTransformPolicy):
            raise TypeError(f"Unexpected policy for {type(self).__name__}: {type(policy).__name__}")
        self.policy = policy

    @override
    def get_generated_ocg_node_manifest(self) -> GeneratedObjectConfigGraphNodeManifest | None:
        return self._generated_manifest

    @override
    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: type[CodePrimitiveType] | None = None,
    ) -> ObjectConfigGraph:
        _ = code_primitive_type
        # Collect generated join classes keyed by class_config_id, then resolve to node ids
        # after building the final SQL OCG.
        join_anchor_class_id_by_join_class_id: dict[UUID, UUID] = {}
        # Build meta-time namespaces keyed by class_config_id from OCG topology.
        # This avoids any dependency on code_id/code_sections and supports synthetic classes.
        ns_by_class_id: dict[UUID, NamespacePath] = {}
        ns_by_enum_id: dict[UUID, NamespacePath] = {}
        ns_by_fn_id: dict[UUID, NamespacePath] = {}
        ns_idx = build_namespace_index(object_config_graph)
        for node in object_config_graph.object_config_graph_nodes:
            ns = ns_idx.node_namespace_by_node_id.get(node.id)
            if ns is None:
                continue
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                ns_by_class_id[node.class_config.id] = ns
            elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
                ns_by_enum_id[node.enum_config.id] = ns
            elif node.type == ObjectConfigGraphNodeType.function and node.function_config is not None:
                ns_by_fn_id[node.function_config.id] = ns

        # Collect nodes
        class_configs: list[ClassConfig] = []
        enum_configs: list[EnumConfig] = []
        function_configs: list[FunctionConfig] = []
        relationships: list[ClassConfigRelationship] = []

        for node in object_config_graph.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                class_configs.append(node.class_config)
            elif node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
                relationships.append(node.class_config_relationship)
            elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
                enum_configs.append(node.enum_config)
            elif node.type == ObjectConfigGraphNodeType.function and node.function_config is not None:
                function_configs.append(node.function_config)

        class_by_id = {c.id: c for c in class_configs}
        local_class_ids = set(class_by_id.keys())

        overrides_by_key = index_fk_override_annotations(object_config_graph)
        analyses_by_relationship_id = {
            analysis.relationship.id: analysis
            for analysis in analyze_relationships(
                object_config_graph,
                namespace_by_code_id=self.namespace_by_code_id,
                external_graphs_by_id=self._external_graphs_by_id,
            )
        }
        nullable_fk_override_by_relationship_id: dict[UUID, bool] = {}
        for rel_id, analysis in analyses_by_relationship_id.items():
            override = resolve_fk_override(analysis, overrides_by_key=overrides_by_key)
            nullable_fk_override_by_relationship_id[rel_id] = bool(override is not None and override.nullable)

        # External class lookup for cross-OCG relationship lowering.
        external_class_by_id: dict[UUID, ClassConfig] = {}
        for ocg_rel in object_config_graph.object_config_graph_relationships or []:
            tgt = ocg_rel.target_object_config_graph
            if tgt is None:
                tgt = self._external_graphs_by_id.get(ocg_rel.target_object_config_graph_id)
            if tgt is None:
                continue
            for n in tgt.object_config_graph_nodes:
                if n.type != ObjectConfigGraphNodeType.class_ or n.class_config is None:
                    continue
                _ = external_class_by_id.setdefault(n.class_config.id, n.class_config)

        # Unified relationship stream (local RELATIONSHIP nodes + detached cross-OCG relationships).
        all_relationships: list[ClassConfigRelationship] = list(relationships)
        seen_rel_ids = {r.id for r in all_relationships}
        for ocg_rel in object_config_graph.object_config_graph_relationships or []:
            for rel in ocg_rel.class_config_relationships or []:
                if rel.id in seen_rel_ids:
                    continue
                all_relationships.append(rel)
                seen_rel_ids.add(rel.id)

        join_class_name_by_relationship_id = self._plan_synthetic_join_class_names(
            relationships=all_relationships,
            class_by_id=class_by_id,
            local_class_ids=local_class_ids,
            external_class_by_id=external_class_by_id,
        )

        # Add synthetic join classes for MANY_TO_MANY without association class.
        for rel in all_relationships:
            if rel.relationship_type != ClassConfigRelationshipType.many_to_many:
                continue
            if rel.class_config_relationship_association_edge is not None:
                continue
            src = class_by_id.get(rel.class_config_id)
            tgt = class_by_id.get(rel.target_class_config_id) or external_class_by_id.get(rel.target_class_config_id)
            if src is None or tgt is None:
                continue

            # Assign namespace deterministically for synthetic class: use the relationship source class namespace.
            join_namespace = ns_by_class_id.get(src.id)
            if join_namespace is None:
                tgt_ns = ns_by_class_id.get(tgt.id)
                if tgt_ns is None:
                    raise ValueError(
                        "Cannot assign namespace for synthetic join class: "
                        + f"missing namespace for both endpoints (src={src.id}, tgt={tgt.id})."
                    )
                join_namespace = tgt_ns
            join_cls = self._build_join_class_for_relationship(
                rel=rel,
                source=src,
                target=tgt,
                join_namespace=join_namespace,
                join_name=join_class_name_by_relationship_id.get(rel.id),
            )
            class_configs.append(join_cls)
            class_by_id[join_cls.id] = join_cls
            ns_by_class_id[join_cls.id] = join_namespace

            # Explicit contract: this join class was synthesized by the transformer.
            # Placement policy: own file, anchored next to the canonical source class container.
            join_anchor_class_id_by_join_class_id[join_cls.id] = src.id

            # Attach as association edge
            rel.class_config_relationship_association_edge = ClassConfigRelationshipAssociation(
                class_config_id=join_cls.id,
                class_config_relationship_id=rel.id,
            )

            # Ensure relationship attributes include the association FK attrs so SQL renderer can
            # discover FK constraints from runtime relationship metadata.
            # (We only add if absent.)
            existing_attr_ids = {ra.attribute_config_id for ra in rel.class_config_relationship_attributes}
            src_fk_name = f"{to_snake_case(src.name)}_id"
            tgt_fk_name = f"{to_snake_case(tgt.name)}_id"
            for acc in join_cls.class_config_attribute_configs:
                attr = acc.attribute_config
                if attr is None:
                    continue
                if attr.id in existing_attr_ids:
                    continue
                if attr.name == src_fk_name:
                    direction = ClassConfigRelationshipDirection.forward
                elif attr.name == tgt_fk_name:
                    direction = ClassConfigRelationshipDirection.reverse
                else:
                    continue
                rel.class_config_relationship_attributes.append(
                    ClassConfigRelationshipAttribute(
                        class_config_relationship_id=rel.id,
                        attribute_config_id=attr.id,
                        direction=direction,
                        role=ClassConfigRelationshipAttributeRole.foreign_key,
                    )
                )

        # Add synthetic join classes for cross-package ONE_TO_MANY where FK ownership is external.
        #
        # Contract:
        # - We never mutate dependency packages (external classes) to add FK columns.
        # - Therefore, when a ONE_TO_MANY would place an FK on an external target class, we
        #   represent it as a local join table in SQL.
        for rel in all_relationships:
            if rel.relationship_type != ClassConfigRelationshipType.one_to_many:
                continue
            if rel.class_config_relationship_association_edge is not None:
                continue
            # ONE_TO_MANY: FK would live on the target class; if target is local, runtime IR can synthesize it.
            if rel.target_class_config_id in local_class_ids:
                continue
            # If the relationship already has FK metadata (e.g. explicit `reference bind`), do not synthesize a join.
            if any(
                ra.role == ClassConfigRelationshipAttributeRole.foreign_key
                for ra in (rel.class_config_relationship_attributes or [])
            ):
                continue

            src = class_by_id.get(rel.class_config_id)
            tgt = external_class_by_id.get(rel.target_class_config_id)
            if src is None or tgt is None:
                continue

            # Assign namespace deterministically for synthetic class: use the relationship source class namespace.
            src_ns = ns_by_class_id.get(src.id)
            if src_ns is None:
                raise ValueError(
                    "Cannot assign namespace for synthetic join class: "
                    + f"missing namespace for source class (src={src.id})."
                )
            join_cls = self._build_join_class_for_relationship(
                rel=rel,
                source=src,
                target=tgt,
                join_namespace=src_ns,
                join_name=join_class_name_by_relationship_id.get(rel.id),
            )
            if join_cls.id in class_by_id:
                continue
            class_configs.append(join_cls)
            class_by_id[join_cls.id] = join_cls
            ns_by_class_id[join_cls.id] = src_ns

            # Placement policy: own file, anchored next to the canonical source class container.
            join_anchor_class_id_by_join_class_id[join_cls.id] = src.id

            # Attach as association edge
            rel.class_config_relationship_association_edge = ClassConfigRelationshipAssociation(
                class_config_id=join_cls.id,
                class_config_relationship_id=rel.id,
            )

            # Ensure relationship attributes include the association FK attrs so SQL renderer can
            # discover FK constraints from runtime relationship metadata.
            existing_attr_ids = {ra.attribute_config_id for ra in rel.class_config_relationship_attributes}
            src_fk_name = f"{to_snake_case(src.name)}_id"
            tgt_fk_name = f"{to_snake_case(tgt.name)}_id"
            for acc in join_cls.class_config_attribute_configs:
                attr = acc.attribute_config
                if attr is None:
                    continue
                if attr.id in existing_attr_ids:
                    continue
                if attr.name == src_fk_name:
                    direction = ClassConfigRelationshipDirection.forward
                elif attr.name == tgt_fk_name:
                    direction = ClassConfigRelationshipDirection.reverse
                else:
                    continue
                rel.class_config_relationship_attributes.append(
                    ClassConfigRelationshipAttribute(
                        class_config_relationship_id=rel.id,
                        attribute_config_id=attr.id,
                        direction=direction,
                        role=ClassConfigRelationshipAttributeRole.foreign_key,
                    )
                )

        # Apply canonical DB requiredness to FK columns for SQL materialization.
        # Runtime IR may have mutated FK requiredness for ergonomics; SQL must not depend on that.
        #
        # Important:
        # SQL rendering relies on `ClassConfig.class_config_relationships` (runtime-attached) to
        # discover FK constraints. Ensure we unify relationship identity so transformer mutations
        # (frontier stripping, requiredness) apply to the same relationship objects the renderer reads.
        all_relationships_by_id: dict[UUID, ClassConfigRelationship] = {r.id: r for r in all_relationships}
        for cls in class_configs:
            if not cls.class_config_relationships:
                continue
            unified: list[ClassConfigRelationship] = []
            for rel in cls.class_config_relationships:
                canonical = all_relationships_by_id.get(rel.id)
                if canonical is None:
                    all_relationships_by_id[rel.id] = rel
                    canonical = rel
                unified.append(canonical)
            cls.class_config_relationships = unified

        self._apply_db_requiredness(
            relationships=list(all_relationships_by_id.values()),
            class_by_id=class_by_id,
            nullable_fk_override_by_relationship_id=nullable_fk_override_by_relationship_id,
        )

        # Materialize SQL-standard base columns as real AttributeConfigs (renderer must be emit-only):
        # - id (PRIMARY KEY)
        self._ensure_sql_base_columns(
            class_configs,
            emit_lane_scope_columns=self.policy.emit_lane_scope_columns,
        )

        # Build new graph (language=SQL).
        #
        # NOTE: `build_object_config_graph` intentionally does not accept overlays.
        # We preserve overlays by copying them onto the built graph afterward so
        # materialization can still apply overlay-driven renames (reserved keywords, etc).
        namespace_bundle = ObjectConfigGraphNamespaceBundle(
            namespace_by_class_config_id=ns_by_class_id,
            namespace_by_enum_config_id=ns_by_enum_id,
            namespace_by_function_config_id=ns_by_fn_id,
        )

        sql_graph = build_object_config_graph(
            language=CodeLanguage.sql,
            name=object_config_graph.name,
            description=object_config_graph.description,
            fqn_prefix=object_config_graph.fqn_prefix,
            class_configs=class_configs,
            class_config_relationships=sorted(all_relationships_by_id.values(), key=lambda r: str(r.id)),
            enum_configs=enum_configs,
            function_configs=function_configs,
            namespace_bundle=namespace_bundle,
            object_config_graph_annotations=list(object_config_graph.object_config_graph_annotations),
            object_projection_graph_declarations=list(object_config_graph.object_projection_graph_declarations),
            source_graph=object_config_graph,
        )
        sql_graph.object_config_graph_overlays = list(object_config_graph.object_config_graph_overlays)
        # Preserve frontier lens on SQL graphs. Rebuilding OPGs from declarations can fail on
        # SQL-only topology may lack full source namespace provenance, so copy runtime OPG instances.
        sql_graph.object_projection_graphs = [
            opg.model_copy(deep=False) for opg in (object_config_graph.object_projection_graphs or [])
        ]

        # Resolve class_config_id -> node_id for both the join and its anchor, then build a node-based manifest.
        node_id_by_class_id: dict[UUID, UUID] = {}
        for n in sql_graph.object_config_graph_nodes:
            if n.type == ObjectConfigGraphNodeType.class_ and n.class_config is not None:
                node_id_by_class_id[n.class_config.id] = n.id

        intents_by_node_id: dict[UUID, GeneratedObjectConfigGraphNodeIntent] = {}
        for join_class_id, anchor_class_id in join_anchor_class_id_by_join_class_id.items():
            join_node_id = node_id_by_class_id.get(join_class_id)
            anchor_node_id = node_id_by_class_id.get(anchor_class_id)
            if join_node_id is None:
                continue
            intents_by_node_id[join_node_id] = GeneratedObjectConfigGraphNodeIntent(
                node_id=join_node_id,
                node_type=ObjectConfigGraphNodeType.class_,
                anchor_node_id=anchor_node_id,
                file_policy=GeneratedObjectConfigGraphNodeFilePolicy.OWN_FILE,
            )

        self._generated_manifest = GeneratedObjectConfigGraphNodeManifest(intents_by_node_id=intents_by_node_id)
        return sql_graph

    # ------------------------------------------------------------------
    # SQL base columns (PK + timestamps)
    # ------------------------------------------------------------------

    def _ensure_sql_base_columns(
        self,
        class_configs: list[ClassConfig],
        *,
        emit_lane_scope_columns: bool = True,
    ) -> None:
        for cls in class_configs:
            # Index by name for idempotence.
            by_name: dict[str, AttributeConfig] = {}
            for acc in cls.class_config_attribute_configs:
                attr = acc.attribute_config
                if attr is None:
                    continue
                by_name[attr.name] = attr

            if emit_lane_scope_columns:
                # Ensure branch_id exists (lane scope).
                branch_attr = by_name.get("branch_id")
                if branch_attr is None:
                    branch_attr = self._uuid_attr(
                        owner_key=cls.class_fqn,
                        name="branch_id",
                        required=True,
                        unique=False,
                        key=f"sql_base:{cls.id}:branch_id",
                        is_primary=True,
                    )
                    # Branch scoping is a DB/index concern, not SSOT object state.
                    branch_attr.is_virtual = True
                    cls.class_config_attribute_configs.append(
                        ClassConfigAttributeConfig(
                            class_config_id=cls.id,
                            attribute_config=branch_attr,
                            name=branch_attr.name,
                            position=-50,
                        )
                    )
                else:
                    branch_attr.is_primary = True
                    branch_attr.is_required = True
                    branch_attr.is_virtual = True

                # Ensure projection_hash exists (lane scope).
                projection_hash_attr = by_name.get("projection_hash")
                if projection_hash_attr is None:
                    projection_hash_attr = self._string_attr(
                        owner_key=cls.class_fqn,
                        name="projection_hash",
                        required=True,
                        unique=False,
                        key=f"sql_base:{cls.id}:projection_hash",
                        is_primary=True,
                    )
                    # Projection hash scoping is a DB/index concern, not SSOT object state.
                    projection_hash_attr.is_virtual = True
                    cls.class_config_attribute_configs.append(
                        ClassConfigAttributeConfig(
                            class_config_id=cls.id,
                            attribute_config=projection_hash_attr,
                            name=projection_hash_attr.name,
                            position=-40,
                        )
                    )
                else:
                    projection_hash_attr.is_primary = True
                    projection_hash_attr.is_required = True
                    projection_hash_attr.is_virtual = True

            # Ensure id exists and is the primary key.
            id_attr = by_name.get("id")
            if id_attr is None:
                id_attr = self._uuid_attr(
                    owner_key=cls.class_fqn,
                    name="id",
                    required=True,
                    unique=True,
                    key=f"sql_base:{cls.id}:id",
                    is_primary=True,
                )
                cls.class_config_attribute_configs.append(
                    ClassConfigAttributeConfig(
                        class_config_id=cls.id,
                        attribute_config=id_attr,
                        name=id_attr.name,
                        position=-30,
                    )
                )
            else:
                id_attr.is_primary = True
                id_attr.is_required = True

    def _apply_db_requiredness(
        self,
        *,
        relationships: list[ClassConfigRelationship],
        class_by_id: dict[UUID, ClassConfig],
        nullable_fk_override_by_relationship_id: dict[UUID, bool] | None = None,
    ) -> None:
        # Helper: set requiredness for FK attrs that belong to a specific class.
        def set_fk_requiredness(owner: ClassConfig, fk_attr_ids: set[UUID], required: bool) -> None:
            for acc in owner.class_config_attribute_configs:
                attr = acc.attribute_config
                if attr is None:
                    continue
                if attr.id in fk_attr_ids:
                    attr.is_required = required

        for rel in relationships:
            # DB truth is derived from canonical relationships only.
            if rel.reified_from_relationship_id is not None:
                continue
            fk_attr_ids = {
                ra.attribute_config_id
                for ra in rel.class_config_relationship_attributes
                if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
            }
            if not fk_attr_ids:
                continue

            nullable_override = bool(
                nullable_fk_override_by_relationship_id and nullable_fk_override_by_relationship_id.get(rel.id, False)
            )
            assoc_id = None
            if rel.class_config_relationship_association_edge is not None:
                assoc_id = rel.class_config_relationship_association_edge.class_config_id
            if assoc_id:
                # Join-table/association FKs are DB truth: both endpoints must be NOT NULL by default.
                assoc_cls = class_by_id.get(assoc_id)
                if assoc_cls is not None:
                    set_fk_requiredness(assoc_cls, fk_attr_ids, not nullable_override)
                continue

            if rel.relationship_type in {
                ClassConfigRelationshipType.many_to_one,
                ClassConfigRelationshipType.one_to_one,
            }:
                owner_cls = class_by_id.get(rel.class_config_id)
                if owner_cls is None:
                    continue
                set_fk_requiredness(
                    owner_cls,
                    fk_attr_ids,
                    bool(rel.forward_required) and not nullable_override,
                )
            elif rel.relationship_type == ClassConfigRelationshipType.one_to_many:
                owner_cls = class_by_id.get(rel.target_class_config_id)
                if owner_cls is None:
                    continue
                set_fk_requiredness(
                    owner_cls,
                    fk_attr_ids,
                    bool(rel.forward_required) and not nullable_override,
                )

    # ------------------------------------------------------------------
    # Join table synthesis
    # ------------------------------------------------------------------

    def _plan_synthetic_join_class_names(
        self,
        *,
        relationships: list[ClassConfigRelationship],
        class_by_id: dict[UUID, ClassConfig],
        local_class_ids: set[UUID],
        external_class_by_id: dict[UUID, ClassConfig],
    ) -> dict[UUID, str]:
        candidates: list[tuple[ClassConfigRelationship, ClassConfig, ClassConfig, str]] = []
        for rel in relationships:
            endpoints = self._synthetic_join_endpoints(
                rel=rel,
                class_by_id=class_by_id,
                local_class_ids=local_class_ids,
                external_class_by_id=external_class_by_id,
            )
            if endpoints is None:
                continue
            source, target = endpoints
            candidates.append((rel, source, target, self._default_join_class_name(source=source, target=target)))

        relationship_ids_by_default_name: dict[str, list[UUID]] = {}
        for rel, _source, _target, default_name in candidates:
            relationship_ids_by_default_name.setdefault(default_name, []).append(rel.id)

        planned: dict[UUID, str] = {}
        for rel, source, target, default_name in candidates:
            rel_ids = relationship_ids_by_default_name[default_name]
            if len(rel_ids) == 1:
                planned[rel.id] = default_name
            else:
                planned[rel.id] = self._relationship_scoped_join_class_name(rel=rel, source=source, target=target)
        return planned

    def _synthetic_join_endpoints(
        self,
        *,
        rel: ClassConfigRelationship,
        class_by_id: dict[UUID, ClassConfig],
        local_class_ids: set[UUID],
        external_class_by_id: dict[UUID, ClassConfig],
    ) -> tuple[ClassConfig, ClassConfig] | None:
        if rel.class_config_relationship_association_edge is not None:
            return None

        if rel.relationship_type == ClassConfigRelationshipType.many_to_many:
            src = class_by_id.get(rel.class_config_id)
            tgt = class_by_id.get(rel.target_class_config_id) or external_class_by_id.get(rel.target_class_config_id)
            if src is None or tgt is None:
                return None
            return src, tgt

        if rel.relationship_type != ClassConfigRelationshipType.one_to_many:
            return None
        if rel.target_class_config_id in local_class_ids:
            return None
        if any(
            ra.role == ClassConfigRelationshipAttributeRole.foreign_key
            for ra in (rel.class_config_relationship_attributes or [])
        ):
            return None

        src = class_by_id.get(rel.class_config_id)
        tgt = external_class_by_id.get(rel.target_class_config_id)
        if src is None or tgt is None:
            return None
        return src, tgt

    @staticmethod
    def _default_join_class_name(*, source: ClassConfig, target: ClassConfig) -> str:
        return f"{source.name}{target.name}Join"

    @staticmethod
    def _relationship_scoped_join_class_name(
        *,
        rel: ClassConfigRelationship,
        source: ClassConfig,
        target: ClassConfig,
    ) -> str:
        relationship_key = str(rel.relationship_key or "").strip()
        member_name = singularize(relationship_key) if relationship_key else target.name
        member_token = to_pascal_case(member_name) or target.name
        if not member_token.casefold().endswith(target.name.casefold()):
            member_token = f"{member_token}{target.name}"
        return f"{source.name}{member_token}Join"

    def _build_join_class_for_relationship(
        self,
        *,
        rel: ClassConfigRelationship,
        source: ClassConfig,
        target: ClassConfig,
        join_namespace: NamespacePath,
        join_name: str | None = None,
    ) -> ClassConfig:
        # Stable ID contract for SQL-synthesized join tables:
        # Relationship IDs are now deterministic, so we *could* key this off `rel.id`.
        # We still prefer a natural key here so SQL join-table identity remains stable even
        # if the relationship-id derivation scheme evolves later.
        #
        # Natural key components:
        # - endpoints (source/target class_config_id)
        # - the declaring relationship attribute (REFERENCE attribute_config_id) when present
        #
        # This also avoids collisions for multiple M2M edges between the same pair.
        ref_attr_id: UUID | None = None
        for ra in rel.class_config_relationship_attributes or []:
            if ra.role == ClassConfigRelationshipAttributeRole.reference:
                ref_attr_id = ra.attribute_config_id
                break
        a = str(min(source.id, target.id))
        b = str(max(source.id, target.id))
        suffix = str(ref_attr_id) if ref_attr_id is not None else "no_ref"
        join_key = f"sql_join:{a}:{b}:{suffix}"
        join_id = deterministic_uuid(join_key)
        join_name = join_name or self._default_join_class_name(source=source, target=target)
        join_class_fqn = join_namespace.fqn(join_name)

        cls = ClassConfig(
            id=join_id,
            class_fqn=join_class_fqn,
            name=join_name,
            description=f"SQL join table for {source.name} <-> {target.name}",
            is_base=True,
        )

        # Add id + two FK uuid columns
        id_attr = self._uuid_attr(
            owner_key=cls.class_fqn,
            name="id",
            required=True,
            unique=True,
            key=f"{join_key}:id",
            is_primary=True,
        )
        src_fk = self._uuid_attr(
            owner_key=cls.class_fqn,
            name=f"{to_snake_case(source.name)}_id",
            required=True,
            unique=False,
            key=f"{join_key}:src",
        )
        tgt_fk = self._uuid_attr(
            owner_key=cls.class_fqn,
            name=f"{to_snake_case(target.name)}_id",
            required=True,
            unique=False,
            key=f"{join_key}:tgt",
        )

        cls.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                class_config_id=cls.id,
                attribute_config=id_attr,
                name=id_attr.name,
                position=0,
            )
        )
        cls.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                class_config_id=cls.id,
                attribute_config=src_fk,
                name=src_fk.name,
                position=1,
            )
        )
        cls.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                class_config_id=cls.id,
                attribute_config=tgt_fk,
                name=tgt_fk.name,
                position=2,
            )
        )

        return cls

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
        attr_id = deterministic_uuid(f"{key}:attr")
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
            id=attr_id,
            owner_key=owner_key,
            name=name,
            is_primary=is_primary,
            is_public=False,
            is_required=required,
            is_unique=unique,
            is_virtual=False,
            type_descriptor=desc,
        )

    def _string_attr(
        self,
        *,
        owner_key: str,
        name: str,
        required: bool,
        unique: bool,
        key: str,
        is_primary: bool = False,
    ) -> AttributeConfig:
        attr_id = deterministic_uuid(f"{key}:attr")
        prim_type = CodePrimitiveType(
            signature=CodePrimitiveBaseType.string.value,
            base_type=CodePrimitiveBaseType.string,
            constraints=None,
        )
        prim = PrimitiveConfig(primitive_type=prim_type, primitive_type_id=prim_type.id)
        desc = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
            primitive_config=prim,
            primitive_config_id=prim.id,
        )
        return AttributeConfig(
            id=attr_id,
            owner_key=owner_key,
            name=name,
            is_primary=is_primary,
            is_public=False,
            is_required=required,
            is_unique=unique,
            is_virtual=False,
            type_descriptor=desc,
        )

    def _datetime_attr(self, *, owner_key: str, name: str, required: bool, unique: bool, key: str) -> AttributeConfig:
        attr_id = deterministic_uuid(f"{key}:attr")
        prim_type = CodePrimitiveType(
            signature=CodePrimitiveBaseType.datetime.value,
            base_type=CodePrimitiveBaseType.datetime,
            constraints=None,
        )
        prim = PrimitiveConfig(primitive_type=prim_type, primitive_type_id=prim_type.id)
        desc = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
            primitive_config=prim,
            primitive_config_id=prim.id,
        )
        return AttributeConfig(
            id=attr_id,
            owner_key=owner_key,
            name=name,
            is_primary=False,
            is_public=False,
            is_required=required,
            is_unique=unique,
            is_virtual=False,
            type_descriptor=desc,
        )


__all__ = ["RuntimeToSQLTransformer"]
