"""
SQL renderer (full-file materialization) for ObjectConfigGraphs.

Postgres-first, with a small dialect interface so we can add SQLite later without
splitting the pipeline into multiple renderers.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_index import (
    CodeSectionAnnotationIndex,
)
from aware_meta_ontology.annotation.code_section_annotation_storage import (
    CodeSectionAnnotationStorage,
)
from aware_meta_ontology.annotation.code_section_annotation_storage_enums import (
    CodeSectionAnnotationStorageOperation,
)
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_config_overlay import EnumConfigOverlay
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import (
    AttributeConfigOverlay,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

# Code Runtime
from aware_code.section.comment.assembler import assemble_comment
from aware_code.section.comment.segments import CodeSectionCommentSegment
from aware_code.section.spec import SectionSpec
from aware_code.section.writer import CodeSectionWriter

# Aware Meta
from aware_meta.attribute.config.type_descriptor_helpers import (
    resolve_type_info,
    AttributeTypeInfo,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    build_renderer_empty_code,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# Utils
from aware_utils.string_transform import to_snake_case
from typing_extensions import override

# SQL Grammar
from sql_grammar.renderers.postgres_dialect import PostgresDialect
from sql_grammar.renderers.dialect import SQLDialect
from sql_grammar.renderers.sqlite_dialect import SqliteDialect
from sql_grammar.migrations.postgres_ddl import (
    stable_index_name_for_storage as _stable_index_name_for_storage,
)
from sql_grammar.renderer_policy import SQLRenderPolicy


@dataclass(frozen=True)
class SQLStorageIndexSpec:
    view_id: UUID
    member_names: tuple[str, ...]
    unique: bool = False
    name: str | None = None


@dataclass(frozen=True)
class SQLPhysicalStorageIndexSpec:
    name: str
    columns: tuple[str, ...]
    unique: bool = False


@dataclass(frozen=True)
class SQLTableSchemaSpec:
    table_name: str
    columns: tuple[str, ...]
    json_columns: tuple[str, ...] = ()
    storage_indexes: tuple[SQLPhysicalStorageIndexSpec, ...] = ()


class SQLRenderer(ObjectConfigGraphRendererLanguage):
    """Full-file SQL renderer (DDL) for Postgres-first outputs."""

    def __init__(
        self,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        dialect: SQLDialect | None = None,
    ) -> None:
        self._dialect: SQLDialect = dialect or PostgresDialect()
        self._db_enforced_relationship_ids: set[UUID] | None = None
        self._index_views_by_class_id: dict[UUID, list[SQLStorageIndexSpec]] = {}
        self._spec_comment: SectionSpec | None = None
        self.policy = SQLRenderPolicy.projection_default()
        super().__init__(layout_strategy)

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    @property
    @override
    def indent(self) -> int:
        return 2

    @property
    @override
    def comment_prefix(self) -> str:
        return "--"

    @override
    def set_policy(self, policy: object | None) -> None:
        if policy is None:
            self.policy = SQLRenderPolicy.projection_default()
            return
        if not isinstance(policy, SQLRenderPolicy):
            raise TypeError(f"Unexpected policy for {type(self).__name__}: {type(policy).__name__}")
        self.policy = policy

    @override
    def define_assemblers(self) -> None:
        self._spec_comment = SectionSpec(
            section_type=CodeSectionType.comment,
            assemble=lambda code_section, segments, _nested: assemble_comment(
                code_section=code_section,
                segments=segments,
            ),
        )

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.sql,
            renderer_key=type(self).__name__,
        )

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._db_enforced_relationship_ids = self._compute_db_enforced_relationship_ids(graph)
        self._index_views_by_class_id = self._index_index_annotations_by_class_id(graph)

    @override
    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        # We render a full file as a single "comment section" payload to keep the
        # CodeSectionWriter contract satisfied without inventing SQL segment types yet.
        enums: list[EnumConfig] = []
        classes: list[ClassConfig] = []

        # Relationships may be present as meta_objects, but we rely on runtime-attached
        # `ClassConfig.class_config_relationships` for FK mapping.
        for obj in meta_objects:
            if isinstance(obj, EnumConfig):
                enums.append(obj)
            elif isinstance(obj, ClassConfig):
                # Inline values are wire/payload types, not persistent ORM entities.
                #
                # SQL DDL outputs must only include persistent graph_ref classes; inline_value classes
                # are represented as JSON payloads inside persistent tables when needed.
                if obj.value_mode == ClassValueMode.graph_ref:
                    classes.append(obj)

        enums.sort(key=lambda e: e.name)
        classes.sort(key=lambda c: c.name)

        ddl: list[str] = []
        ddl.append("-- coverage:ignore-file\n")
        ddl.append("-- GENERATED CODE - DO NOT MODIFY BY HAND\n\n")

        for e in enums:
            ddl.append(self._emit_enum(e))
            ddl.append("\n")

        # Build a best-effort class lookup (includes external classes if provided by renderer).
        class_lookup: dict[UUID, ClassConfig] = {}
        # Materialize stage populates this for cross-OCG imports.
        if class_to_class_config_map:
            class_lookup.update(class_to_class_config_map)
        for c in classes:
            _ = class_lookup.setdefault(c.id, c)

        for c in classes:
            ddl.append(self._emit_table(c, class_lookup=class_lookup))
            ddl.append(self._emit_indexes_for_table(c))
            ddl.append("\n")

        body = "".join(ddl).rstrip() + "\n"

        spec_comment = self._spec_comment
        if spec_comment is None:
            raise RuntimeError("SQL renderer assembler spec is not initialized")
        with writer.start_section(spec_comment, qualname="sql_file") as scope:
            _ = scope.token(body, CodeSectionCommentSegment.CONTENT.value)

    # ------------------------------------------------------------------
    # DDL emitters
    # ------------------------------------------------------------------

    def _table_name(self, cls: ClassConfig) -> str:
        name = self._dialect.table_name(cls)
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.class_, cls.id)
        if overlay is not None and isinstance(overlay, ClassConfigOverlay) and overlay.rendered_name:
            name = overlay.rendered_name
        return name

    def _enum_type_name(self, enum: EnumConfig) -> str:
        name = self._dialect.enum_type_name(enum)
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.enum, enum.id)
        if overlay is not None and isinstance(overlay, EnumConfigOverlay) and overlay.rendered_name:
            name = overlay.rendered_name
        return name

    def _column_name(self, attr: AttributeConfig) -> str:
        name = attr.name
        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr.id)
        if overlay is not None and isinstance(overlay, AttributeConfigOverlay) and overlay.rendered_name:
            name = overlay.rendered_name
        return name

    def _emit_enum(self, enum: EnumConfig) -> str:
        type_name = self._enum_type_name(enum)
        values: list[str] = []
        for opt in enum.enum_options:
            values.append(opt.value)
        return self._dialect.emit_enum(type_name, values)

    def _emit_table(self, cls: ClassConfig, *, class_lookup: dict[UUID, ClassConfig]) -> str:
        table = self._table_name(cls)

        # Build FK target lookup: fk_attr_id -> target ClassConfig (best-effort, may be external)
        fk_targets: dict[UUID, ClassConfig] = {}
        fk_enforced_attr_ids: set[UUID] = set()
        for rel in cls.class_config_relationships or []:
            self._index_fk_targets_for_class(
                cls,
                rel,
                fk_targets,
                fk_enforced_attr_ids,
                class_lookup=class_lookup,
            )

        # Deterministic attribute order uses link.position (runtime transformer normalized).
        links = sorted(
            cls.class_config_attribute_configs,
            key=lambda acc: (acc.position, acc.attribute_config.name),
        )

        # Categorize physical columns for readability:
        # - PRIMARY KEY: attrs with AttributeConfig.is_primary == True (table-level PK constraint emitted)
        # - RELATIONSHIPS: FK columns (those that have an FK target via relationship role metadata;
        #   lane-scoped composite FK constraints emitted)
        # - ATTRIBUTES: everything else
        pk_cols: list[str] = []
        relationship_cols: list[str] = []
        attribute_cols: list[str] = []
        pk_col_names: list[str] = []
        fk_constraints: list[str] = []
        semantic_identity_col_names: list[str] = []

        for link in links:
            attr = link.attribute_config
            info = resolve_type_info(attr)
            col_name = self._column_name(attr)
            col_ident = self._dialect.quote_ident(col_name)

            is_json_column = self._should_emit_json_column(attr, info)

            if is_json_column:
                col_type = self._dialect.type_for_json()
            else:
                # Only physical scalar columns: primitive + enum.
                if info.kind not in (
                    AttributeTypeDescriptorKind.primitive,
                    AttributeTypeDescriptorKind.enum,
                ):
                    continue

                if info.kind == AttributeTypeDescriptorKind.enum and info.enum_config is not None:
                    col_type = self._dialect.type_for_enum(self._enum_type_name(info.enum_config))
                else:
                    col_type = self._dialect.type_for_attribute(attr)
                if info.is_collection:
                    col_type = self._dialect.array_of(col_type)
            parts = [col_ident, col_type]

            # NOT NULL for required primitives (but allow nullable descriptors too)
            is_required = bool(attr.is_required) and not info.nullable
            if is_required:
                parts.append("NOT NULL")

            # UNIQUE constraint
            is_lane_scope_key = self.policy.emit_lane_scoped_foreign_keys and col_name in {
                "branch_id",
                "projection_hash",
            }
            is_semantic_identity_key = bool(attr.is_primary) and col_name != "id" and not is_lane_scope_key
            if is_semantic_identity_key:
                semantic_identity_col_names.append(col_ident)
            should_emit_unique = bool(attr.is_unique)
            if is_semantic_identity_key and not self.policy.emit_semantic_identity_unique_columns:
                should_emit_unique = False
            if not is_json_column and should_emit_unique and col_name != "id" and not info.is_collection:
                parts.append("UNIQUE")

            # FK reference
            target = fk_targets.get(attr.id)
            if not is_json_column and target is not None and attr.id in fk_enforced_attr_ids:
                if self.policy.emit_lane_scoped_foreign_keys:
                    # Lane-scoped FK: reuse the owning row's (branch_id, projection_hash) and
                    # reference the target row's composite key.
                    #
                    # This keeps projections branch-aware without duplicating scope columns.
                    scope_cols = [
                        self._dialect.quote_ident("branch_id"),
                        self._dialect.quote_ident("projection_hash"),
                    ]
                    fk_cols = [*scope_cols, col_ident]
                    ref_cols = [*scope_cols, self._dialect.quote_ident("id")]
                else:
                    fk_cols = [col_ident]
                    ref_cols = [self._dialect.quote_ident("id")]
                ref_table = self._table_name(target)
                fk_constraints.append(
                    f"  FOREIGN KEY ({', '.join(fk_cols)}) REFERENCES {ref_table}({', '.join(ref_cols)})"
                )

            col_line = "  " + " ".join(parts)

            # Categorize based on primary key and FK target mapping (role metadata).
            if bool(attr.is_primary) and (
                col_name == "id" or is_lane_scope_key or self.policy.emit_semantic_identity_primary_keys
            ):
                pk_cols.append(col_line)
                pk_col_names.append(col_ident)
            elif target is not None:
                relationship_cols.append(col_line)
            else:
                attribute_cols.append(col_line)

        # Emit with comment group headers without breaking comma placement.
        items: list[tuple[str, str]] = []
        if pk_cols:
            items.append(("comment", "  -- PRIMARY KEY"))
            for c in pk_cols:
                items.append(("item", c))
        if relationship_cols:
            items.append(("comment", "  -- RELATIONSHIPS"))
            for c in relationship_cols:
                items.append(("item", c))
        if attribute_cols:
            items.append(("comment", "  -- ATTRIBUTES"))
            for c in attribute_cols:
                items.append(("item", c))

        # Table-level constraints (primary key + lane-scoped foreign keys).
        constraints: list[str] = []
        if pk_col_names:
            constraints.append(f"  PRIMARY KEY ({', '.join(pk_col_names)})")
        unique_col_names = self._semantic_identity_unique_col_names(
            cls,
            semantic_identity_col_names=semantic_identity_col_names,
        )
        if unique_col_names:
            constraints.append(f"  UNIQUE ({', '.join(unique_col_names)})")
        constraints.extend(fk_constraints)
        if constraints:
            items.append(("comment", "  -- CONSTRAINTS"))
            for c in constraints:
                items.append(("item", c))

        item_indices = [i for i, (k, _v) in enumerate(items) if k == "item"]
        last_item_index = item_indices[-1] if item_indices else None

        rendered_lines: list[str] = []
        for idx, (kind, text) in enumerate(items):
            if kind == "comment":
                rendered_lines.append(text)
                continue
            # Column/constraint line: add comma unless it's the last emitted item in the table.
            if last_item_index is not None and idx != last_item_index:
                rendered_lines.append(f"{text},")
            else:
                rendered_lines.append(text)

        body = "\n".join(rendered_lines)
        return f"CREATE TABLE {table} (\n{body}\n);\n"

    # ------------------------------------------------------------------
    # Index annotations (v0)
    # ------------------------------------------------------------------

    def _stable_index_name(
        self,
        *,
        table_name: str,
        column_names: tuple[str, ...],
        unique: bool = False,
        annotation_name: str | None = None,
    ) -> str:
        return _stable_index_name_for_storage(
            table_name=table_name,
            column_names=column_names,
            unique=unique,
            annotation_name=annotation_name,
            prefix="uidx" if unique else "idx",
        )

    def _index_index_annotations_by_class_id(self, graph: ObjectConfigGraph) -> dict[UUID, list[SQLStorageIndexSpec]]:
        """
        Best-effort map of INDEX annotation views -> owning class_config_id.

        Note:
        - SQL-derived graphs do not always include full source namespace metadata.
        - v0 resolves by `class_name` and requires it to be unique within the graph.
        """
        class_by_name: dict[str, list[ClassConfig]] = {}
        for node in graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
                continue
            class_by_name.setdefault(node.class_config.name, []).append(node.class_config)

        out: dict[UUID, list[SQLStorageIndexSpec]] = {}
        storage_annotation_kind = getattr(ObjectConfigGraphAnnotationKind, "storage", None)
        for ann in graph.object_config_graph_annotations:
            index_view = getattr(ann, "code_section_annotation_index", None)
            storage_view = getattr(ann, "code_section_annotation_storage", None)
            view: CodeSectionAnnotationIndex | CodeSectionAnnotationStorage | None
            unique = False
            name: str | None = None
            if ann.kind == ObjectConfigGraphAnnotationKind.index and index_view is not None:
                if not isinstance(index_view, CodeSectionAnnotationIndex):
                    continue
                view = index_view
            elif (
                storage_annotation_kind is not None and ann.kind == storage_annotation_kind and storage_view is not None
            ):
                if not isinstance(storage_view, CodeSectionAnnotationStorage):
                    continue
                view = storage_view
                unique = storage_view.operation == CodeSectionAnnotationStorageOperation.unique
                name = storage_view.name
            else:
                continue
            class_name = str(view.class_name).strip()
            if not class_name:
                continue
            hits = class_by_name.get(class_name) or []
            if not hits:
                raise ValueError(f"INDEX annotation targets unknown class: {class_name!r}")
            if len(hits) != 1:
                raise ValueError(f"INDEX annotation class_name is ambiguous: {class_name!r}")
            out.setdefault(hits[0].id, []).append(
                SQLStorageIndexSpec(
                    view_id=view.id,
                    member_names=tuple(str(m or "").strip() for m in view.member_names if str(m or "").strip()),
                    unique=unique,
                    name=name,
                )
            )

        for _, views in out.items():
            views.sort(key=lambda v: str(v.view_id))
        return out

    def _emit_indexes_for_table(self, cls: ClassConfig) -> str:
        storage_indexes = self._storage_indexes_for_table(cls)
        if not storage_indexes:
            return ""

        table = self._table_name(cls)
        statements: list[str] = []
        for storage_index in storage_indexes:
            cols = ", ".join(self._dialect.quote_ident(c) for c in storage_index.columns)
            unique_token = "UNIQUE " if storage_index.unique else ""
            statements.append(
                f"CREATE {unique_token}INDEX {self._dialect.quote_ident(storage_index.name)} "
                f"ON {self._dialect.quote_ident(table)} ({cols});\n"
            )

        if not statements:
            return ""
        return "\n" + "".join(statements)

    def describe_table_schema(self, cls: ClassConfig) -> SQLTableSchemaSpec:
        columns: list[str] = []
        json_columns: list[str] = []
        links = sorted(
            cls.class_config_attribute_configs,
            key=lambda acc: (acc.position, acc.attribute_config.name),
        )
        for link in links:
            attr = link.attribute_config
            info = resolve_type_info(attr)
            col_name = self._column_name(attr)
            is_json_column = self._should_emit_json_column(attr, info)
            if is_json_column:
                columns.append(col_name)
                json_columns.append(col_name)
                continue
            if info.kind not in (
                AttributeTypeDescriptorKind.primitive,
                AttributeTypeDescriptorKind.enum,
            ):
                continue
            columns.append(col_name)
        return SQLTableSchemaSpec(
            table_name=self._table_name(cls),
            columns=tuple(columns),
            json_columns=tuple(json_columns),
            storage_indexes=self._storage_indexes_for_table(cls),
        )

    def _storage_indexes_for_table(self, cls: ClassConfig) -> tuple[SQLPhysicalStorageIndexSpec, ...]:
        views = self._index_views_by_class_id.get(cls.id) or []
        if not views:
            return ()

        table = self._table_name(cls)
        attr_by_name: dict[str, AttributeConfig] = {}
        for link in cls.class_config_attribute_configs:
            attr_cfg = link.attribute_config
            if not attr_cfg.name.strip():
                continue
            attr_by_name[attr_cfg.name] = attr_cfg

        storage_indexes: list[SQLPhysicalStorageIndexSpec] = []
        seen_keys: set[tuple[str, ...]] = set()
        for view in views:
            raw_members = view.member_names
            members = [m.strip() for m in raw_members]
            if not members:
                raise ValueError(f"INDEX annotation has no member_names for class {cls.name}")

            col_names: list[str] = []
            if self.policy.emit_lane_scoped_indexes:
                # Prefix projection indexes with lane scope columns.
                col_names.extend(["branch_id", "projection_hash"])

            for m in members:
                attr = attr_by_name.get(m)
                if attr is not None:
                    info = resolve_type_info(attr)
                    if info.is_collection:
                        raise ValueError(f"INDEX annotation member is a collection: {cls.name}.{m}")
                    if self._should_emit_json_column(attr, info):
                        raise ValueError(f"INDEX annotation member is JSON-backed (unsupported v0): {cls.name}.{m}")
                    if info.kind in (
                        AttributeTypeDescriptorKind.primitive,
                        AttributeTypeDescriptorKind.enum,
                    ):
                        col_names.append(self._column_name(attr))
                        continue

                # Relationship pointer -> FK column (member_name_id).
                fk_name = f"{to_snake_case(m)}_id"
                fk_attr = attr_by_name.get(fk_name)
                if fk_attr is None:
                    raise ValueError(
                        f"INDEX annotation member cannot be resolved to a SQL column: {cls.name}.{m} "
                        + f"(expected attribute {m!r} or FK attr {fk_name!r})"
                    )
                col_names.append(self._column_name(fk_attr))

            key = tuple(col_names)
            if key in seen_keys:
                raise ValueError(f"Duplicate physical INDEX definition for {cls.name}: {key}")
            seen_keys.add(key)

            storage_indexes.append(
                SQLPhysicalStorageIndexSpec(
                    name=self._stable_index_name(
                        table_name=table,
                        column_names=key,
                        unique=view.unique,
                        annotation_name=view.name,
                    ),
                    columns=key,
                    unique=view.unique,
                )
            )
        return tuple(
            sorted(
                storage_indexes,
                key=lambda index: (
                    index.columns,
                    0 if index.unique else 1,
                    index.name,
                ),
            )
        )

    def _descriptor_has_kind(
        self,
        desc: AttributeTypeDescriptor,
        kind: AttributeTypeDescriptorKind,
        _seen: set[UUID] | None = None,
    ) -> bool:
        if desc.kind == kind:
            return True
        seen = _seen if _seen is not None else set()
        if desc.id in seen:
            return False
        seen.add(desc.id)
        try:
            return self._descriptor_child_has_kind(desc, kind, seen)
        finally:
            seen.remove(desc.id)

    def _descriptor_child_has_kind(
        self,
        desc: AttributeTypeDescriptor,
        kind: AttributeTypeDescriptorKind,
        seen: set[UUID],
    ) -> bool:
        for link in desc.child_links:
            child = link.child
            if self._descriptor_has_kind(child, kind, seen):
                return True
        return False

    def _should_emit_json_column(self, attr: AttributeConfig, info: AttributeTypeInfo) -> bool:
        if (
            info.kind == AttributeTypeDescriptorKind.primitive
            and info.primitive_config is not None
            and info.primitive_config.primitive_type.base_type == CodePrimitiveBaseType.json
        ):
            return True

        # Dict[...] attributes are stored as JSON blobs for persistence.
        if self._descriptor_has_kind(attr.type_descriptor, AttributeTypeDescriptorKind.mapping):
            return True

        # Inline values are wire/payload shapes; persistent tables store them as JSON.
        if (
            info.kind == AttributeTypeDescriptorKind.class_
            and info.class_config is not None
            and info.class_config.value_mode == ClassValueMode.inline_value
        ):
            return True

        return False

    def _semantic_identity_unique_col_names(
        self,
        cls: ClassConfig,
        *,
        semantic_identity_col_names: list[str],
    ) -> list[str]:
        if not self.policy.emit_semantic_identity_unique_constraints:
            return []
        if not semantic_identity_col_names:
            return []

        scope_cols: list[str] = []
        if self.policy.emit_lane_scoped_foreign_keys:
            scope_cols.extend(
                [
                    self._dialect.quote_ident("branch_id"),
                    self._dialect.quote_ident("projection_hash"),
                ]
            )

        owner_scope_cols = self._parent_scope_fk_col_names(cls)
        return list(dict.fromkeys([*scope_cols, *owner_scope_cols, *semantic_identity_col_names]))

    def _parent_scope_fk_col_names(self, cls: ClassConfig) -> list[str]:
        """
        Return FK columns that scope a child row under an owning parent collection.

        A `.aware` collection such as `Parent.children Child[]` materializes as a
        reverse FK on `Child`. That FK participates in the child's semantic
        identity even though it is not an authored `key` attribute on `Child`.
        Ordinary forward references, for example `Member.org Organization`, are
        not parent scopes and must not weaken global semantic-key uniqueness.
        """
        attr_by_id: dict[UUID, AttributeConfig] = {
            link.attribute_config.id: link.attribute_config
            for link in cls.class_config_attribute_configs
            if link.attribute_config is not None
        }
        cols: list[str] = []
        for rel in cls.class_config_relationships or []:
            if rel.relationship_type != ClassConfigRelationshipType.one_to_many:
                continue
            for rel_attr in rel.class_config_relationship_attributes:
                if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                    continue
                if rel_attr.direction != ClassConfigRelationshipDirection.reverse:
                    continue
                attr = attr_by_id.get(rel_attr.attribute_config_id)
                if attr is None:
                    continue
                cols.append(self._dialect.quote_ident(self._column_name(attr)))
        return cols

    def _index_fk_targets_for_class(
        self,
        owner_class: ClassConfig,
        rel: ClassConfigRelationship,
        fk_targets: dict[UUID, ClassConfig],
        fk_enforced_attr_ids: set[UUID],
        *,
        class_lookup: dict[UUID, ClassConfig],
    ) -> None:
        """
        Populate fk_targets for FK attributes that live on `owner_class`.

        Direction rules:
        - FORWARD FK attribute references relationship.target_class_config_id
        - REVERSE FK attribute references relationship.class_config_id (source)
        """
        # Gather attribute IDs present on owner_class for quick membership checks
        owner_attr_ids: set[UUID] = set()
        for acc in owner_class.class_config_attribute_configs:
            owner_attr_ids.add(acc.attribute_config.id)

        for ra in rel.class_config_relationship_attributes:
            if ra.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            if ra.attribute_config_id not in owner_attr_ids:
                continue

            # Pick target class id by direction.
            #
            # Important nuance:
            # - For non-association FKs (FK owner is one endpoint class), direction maps:
            #     FORWARD -> references rel.target_class_config_id
            #     REVERSE -> references rel.class_config_id
            # - For association/join-table FKs (FKs live on association class),
            #   the runtime transformer encodes:
            #     FORWARD -> source FK (references rel.class_config_id)
            #     REVERSE -> target FK (references rel.target_class_config_id)
            assoc_edge = rel.class_config_relationship_association_edge
            is_assoc_owner = assoc_edge is not None and assoc_edge.class_config_id == owner_class.id
            if is_assoc_owner:
                target_id = (
                    rel.class_config_id
                    if ra.direction == ClassConfigRelationshipDirection.forward
                    else rel.target_class_config_id
                )
            else:
                target_id = (
                    rel.target_class_config_id
                    if ra.direction == ClassConfigRelationshipDirection.forward
                    else rel.class_config_id
                )

            target_cls = class_lookup.get(target_id)
            if target_cls is not None:
                fk_targets[ra.attribute_config_id] = target_cls
                if self._should_emit_fk_constraint(rel):
                    fk_enforced_attr_ids.add(ra.attribute_config_id)

    def _should_emit_fk_constraint(self, rel: ClassConfigRelationship) -> bool:
        enforced = self._db_enforced_relationship_ids
        if enforced is None:
            return True
        return rel.id in enforced

    def _compute_db_enforced_relationship_ids(self, graph: ObjectConfigGraph) -> set[UUID] | None:
        """
        Decide which relationships should emit DB-level FK constraints for this graph.

        Canonical model:
        - FK-role metadata is kept for projection plan compilation (OIG -> SQL).
        - FK constraint enforcement is a DDL concern and must not be encoded by deleting FK-role metadata.
        """
        opgs = list(graph.object_projection_graphs or [])
        if not opgs:
            try:
                from aware_meta.graph.config.handlers import (
                    build_object_projection_graphs,
                )

                opgs = build_object_projection_graphs(graph)
            except Exception:
                opgs = []
        if not opgs:
            # No declared projection frontier lens => legacy behavior (emit constraints for all FKs).
            return None

        relationships: list[ClassConfigRelationship] = []
        for node in graph.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
                relationships.append(node.class_config_relationship)

        # Only enforce DB-level FK constraints when both endpoint classes are materialized
        # by this graph. This prevents module-local schemas from enforcing constraints to
        # external classes that are not part of the bundle's projection plans.
        local_class_ids: set[UUID] = set()
        for node in graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_:
                continue
            cc = node.class_config
            if cc is None:
                continue
            local_class_ids.add(cc.id)

        canonical_id_by_relationship_id: dict[UUID, UUID] = {}
        for rel in relationships:
            canonical_id_by_relationship_id[rel.id] = rel.reified_from_relationship_id or rel.id

        opg_by_id: dict[UUID, ObjectProjectionGraph] = {opg.id: opg for opg in opgs}
        opg_ids_by_class_id: dict[UUID, list[UUID]] = {}
        member_class_ids_by_opg_id: dict[UUID, set[UUID]] = {}
        for opg in opgs:
            opg_id = opg.id
            member_ids: set[UUID] = set()
            for opg_node in opg.object_projection_graph_nodes:
                class_id = opg_node.class_config_id
                if class_id not in local_class_ids:
                    continue
                opg_ids_by_class_id.setdefault(class_id, []).append(opg_id)
                member_ids.add(class_id)
            member_class_ids_by_opg_id[opg_id] = member_ids

        # v0 deterministic "home" OPG per class.
        home_opg_id_by_class_id: dict[UUID, UUID] = {}
        for class_id, opg_ids in opg_ids_by_class_id.items():
            unique_ids = sorted(set(opg_ids), key=str)
            if not unique_ids:
                continue
            if len(unique_ids) == 1:
                home_opg_id_by_class_id[class_id] = unique_ids[0]
                continue
            candidates: list[tuple[str, str, str, UUID]] = []
            for oid in unique_ids:
                opg_entry = opg_by_id.get(oid)
                if opg_entry is None:
                    continue
                proj_hash = opg_entry.projection_hash
                name = opg_entry.name
                candidates.append((proj_hash, name, str(oid), oid))
            candidates.sort()
            home_opg_id_by_class_id[class_id] = candidates[0][3] if candidates else unique_ids[0]

        included_canonical_rel_ids_by_opg_id: dict[UUID, set[UUID]] = {}
        for opg in opgs:
            opg_id = opg.id
            rel_ids: set[UUID] = set()
            for edge in opg.object_projection_graph_edges:
                rel_id = edge.class_config_relationship_id
                canonical_rel_id = canonical_id_by_relationship_id.get(rel_id, rel_id)
                rel_ids.add(canonical_rel_id)
            included_canonical_rel_ids_by_opg_id[opg_id] = rel_ids

        enforced_relationship_ids: set[UUID] = set()
        for rel in relationships:

            fk_owner_class_id: UUID | None
            if rel.relationship_type == ClassConfigRelationshipType.one_to_many:
                fk_owner_class_id = rel.target_class_config_id
            elif rel.relationship_type in {
                ClassConfigRelationshipType.many_to_one,
                ClassConfigRelationshipType.one_to_one,
            }:
                fk_owner_class_id = rel.class_config_id
            else:
                fk_owner_class_id = rel.class_config_id

            home_opg_id = home_opg_id_by_class_id.get(fk_owner_class_id)
            if home_opg_id is None:
                continue

            # Portal rule: endpoints must be members of the FK-owner class' home OPG.
            members = member_class_ids_by_opg_id.get(home_opg_id) or set()
            if rel.class_config_id not in members or rel.target_class_config_id not in members:
                continue

            included = included_canonical_rel_ids_by_opg_id.get(home_opg_id)
            if not included:
                continue
            canonical_id = canonical_id_by_relationship_id.get(rel.id, rel.id)
            if canonical_id in included:
                enforced_relationship_ids.add(rel.id)

        return enforced_relationship_ids


class SqliteSQLRenderer(SQLRenderer):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        super().__init__(layout_strategy=layout_strategy, dialect=SqliteDialect())


__all__ = [
    "SQLDialect",
    "PostgresDialect",
    "SqliteDialect",
    "SQLRenderer",
    "SqliteSQLRenderer",
]
