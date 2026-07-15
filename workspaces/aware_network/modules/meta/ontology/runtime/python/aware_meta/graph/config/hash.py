import hashlib
import json
from uuid import UUID

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror import (
    ObjectConfigGraphMirror,
)
from aware_meta_ontology.graph.config.object_config_graph_binding import (
    ObjectConfigGraphBinding,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

# Aware Meta
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle


def _namespace_required(value: object, *, context: str) -> str:
    namespace = getattr(value, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError(f"{context} requires namespace")
    return namespace.strip()


def _namespace_optional(value: object, *, attr: str, context: str) -> str:
    namespace = getattr(value, attr, None)
    if namespace is None:
        return ""
    if not isinstance(namespace, str):
        raise ValueError(f"{context} requires {attr} to be a namespace string")
    return namespace.strip()


def _class_fqn_from_namespace(
    *,
    fqn_prefix: str,
    namespace: str,
    class_name: str,
) -> str:
    namespace = namespace.strip()
    if not namespace:
        return f"{fqn_prefix}.{class_name}"
    return f"{fqn_prefix}.{namespace}.{class_name}"


def compute_object_config_graph_hash(
    language: CodeLanguage,
    fqn_prefix: str,
    namespace_bundle: ObjectConfigGraphNamespaceBundle,
    class_configs: list[ClassConfig],
    enum_configs: list[EnumConfig],
    function_configs: list[FunctionConfig],
    class_config_relationships: list[ClassConfigRelationship] | None = None,
    object_config_graph_annotations: list[ObjectConfigGraphAnnotation] | None = None,
    object_projection_graph_declarations: (
        list[ObjectProjectionGraphDeclaration] | None
    ) = None,
    object_config_graph_bindings: list[ObjectConfigGraphBinding] | None = None,
    object_config_graph_mirrors: list[ObjectConfigGraphMirror] | None = None,
    node_layouts_by_node_key: (
        dict[tuple[str, str], list[ObjectConfigGraphNodeLayout]] | None
    ) = None,
    *,
    include_layout: bool = False,
) -> str:
    """
    Deterministic hash for the ObjectConfigGraph topology (stable across runs).

    Avoids UUIDs; uses names + relationship signatures. Layout metadata can be
    optionally included for materialization identity.
    """
    entries: list[str] = []

    # Build stable FQN maps
    class_id_to_fqn: dict[UUID, str] = {}
    enum_id_to_name: dict[UUID, str] = {e.id: e.name for e in enum_configs}

    def _function_signature(function_config: FunctionConfig) -> str:
        verb = (function_config.verb or "").strip().lower()
        kind = function_config.kind.value
        is_async = "1" if function_config.is_async else "0"

        inputs: list[tuple[int, str]] = []
        outputs: list[tuple[int, str]] = []
        for edge in function_config.function_config_attribute_configs or []:
            name = (
                edge.attribute_config.name if edge.attribute_config is not None else ""
            )
            if edge.type == FunctionAttributeType.input:
                inputs.append((edge.position, name))
            elif edge.type == FunctionAttributeType.output:
                outputs.append((edge.position, name))

        inputs_sorted = ",".join(
            f"{pos}:{name}" for pos, name in sorted(inputs, key=lambda v: (v[0], v[1]))
        )
        outputs_sorted = ",".join(
            f"{pos}:{name}" for pos, name in sorted(outputs, key=lambda v: (v[0], v[1]))
        )
        return f"kind={kind}:verb={verb}:async={is_async}:in={inputs_sorted}:out={outputs_sorted}"

    def _class_fqn(class_config: ClassConfig) -> str:
        ns = namespace_bundle.namespace_for_class(class_config.id)
        if ns is None:
            raise ValueError(
                f"ClassConfig {class_config.id} missing namespace in ObjectConfigGraphNamespaceBundle "
                f"(class={class_config.name})"
            )
        return ns.fqn(class_config.name)

    for cc in class_configs:
        class_id_to_fqn[cc.id] = _class_fqn(cc)

    def _primitive_type_sig(
        prim: CodePrimitiveType,
        _seen: set[int] | None = None,
    ) -> str:
        """Deterministic signature for primitive types (avoid UUID/id fields)."""
        seen = _seen if _seen is not None else set()
        primitive_identity = id(prim)
        if primitive_identity in seen:
            return f"{prim.base_type.value}:cycle"
        seen.add(primitive_identity)
        base = prim.base_type.value
        try:
            constraints = prim.constraints
            constraints_sig = ""
            if constraints is not None:
                constraints_sig = json.dumps(
                    constraints,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
            # Primitive types can be nested, but for hashing we only need deterministic semantic shape.
            # Include nested parts if present.
            item = (
                _primitive_type_sig(prim.item_type, seen)
                if prim.item_type is not None
                else ""
            )
            key = (
                _primitive_type_sig(prim.key_type, seen)
                if prim.key_type is not None
                else ""
            )
            value = (
                _primitive_type_sig(prim.value_type, seen)
                if prim.value_type is not None
                else ""
            )
            elements = ",".join(
                _primitive_type_sig(x, seen) for x in (prim.element_types or [])
            )
            unions = ",".join(
                _primitive_type_sig(x, seen) for x in (prim.union_types or [])
            )
            return (
                f"{base}"
                f":c={constraints_sig}"
                f":item={item}"
                f":key={key}"
                f":value={value}"
                f":elements=[{elements}]"
                f":unions=[{unions}]"
            )
        finally:
            seen.remove(primitive_identity)

    def _type_descriptor_sig(
        desc: AttributeTypeDescriptor | None,
        _seen: set[UUID] | None = None,
    ) -> str:
        """Deterministic signature for AttributeTypeDescriptor (avoid UUID/id fields)."""
        if desc is None:
            return "none"
        kind = desc.kind.value
        seen = _seen if _seen is not None else set()
        if desc.id in seen:
            collection_kind = ""
            if desc.collection_kind is not None:
                collection_kind = desc.collection_kind.value
            return f"{kind}:{collection_kind}[cycle]"
        seen.add(desc.id)

        try:
            if (
                desc.kind == AttributeTypeDescriptorKind.primitive
                and desc.primitive_config is not None
            ):
                prim = desc.primitive_config.primitive_type
                prim_sig = _primitive_type_sig(prim) if prim is not None else ""
                return f"{kind}:{prim_sig}"

            if (
                desc.kind == AttributeTypeDescriptorKind.enum
                and desc.enum_config_id is not None
            ):
                enum_name = enum_id_to_name.get(desc.enum_config_id, "")
                return f"{kind}:{enum_name or f'external:{desc.enum_config_id}'}"

            if (
                desc.kind == AttributeTypeDescriptorKind.class_
                and desc.class_config_id is not None
            ):
                cls_fqn = class_id_to_fqn.get(desc.class_config_id)
                return f"{kind}:{cls_fqn or f'external:{desc.class_config_id}'}"

            # Composite descriptors: include collection kind + ordered child signatures.
            collection_kind = ""
            if desc.collection_kind is not None:
                ck = desc.collection_kind
                collection_kind = ck.value

            child_entries: list[str] = []
            for link in sorted(
                (desc.child_links or []),
                key=lambda child_link: (
                    child_link.role.value,
                    child_link.position is None,
                    child_link.position or 0,
                ),
            ):
                role = link.role.value
                pos = "" if link.position is None else str(link.position)
                child_entries.append(
                    f"{role}:{pos}:{_type_descriptor_sig(link.child, seen)}"
                )
            children_sig = ",".join(child_entries)
            return f"{kind}:{collection_kind}[{children_sig}]"
        finally:
            seen.remove(desc.id)

    def _parent_fqn(child_cls: ClassConfig) -> str:
        parent_id = child_cls.parent_class_id
        if parent_id is None:
            raise ValueError(f"ClassConfig {child_cls.id} missing parent class id")
        # Parent may be external (cross-OCG augment). In that case, the parent is not part of the
        # current graph's class set, but the parent_id is still a stable meta ID and must
        # participate in the hash deterministically.
        parent_fqn = class_id_to_fqn.get(parent_id)
        if parent_fqn is not None:
            return parent_fqn
        return f"external:{parent_id}"

    for cc in sorted(class_configs, key=lambda c: class_id_to_fqn[c.id]):
        cc_fqn = class_id_to_fqn[cc.id]
        is_base = cc.parent_class_id is None
        cls_info = f"cls:{cc_fqn}:is_base={is_base}"
        if not is_base:
            cls_info += f":parent={_parent_fqn(cc)}"
        entries.append(cls_info)
        for acc in sorted(cc.class_config_attribute_configs, key=lambda a: a.position):
            attr = acc.attribute_config
            if attr is None:
                entries.append(
                    f"attr:{cc_fqn}:unresolved:{acc.attribute_config_id}:{acc.position}"
                )
                continue
            # AttributeConfig semantics are part of the OCG identity: changes here MUST invalidate
            # downstream caches/materializations (SQL schema, bindings, runtime transforms).
            req = "1" if attr.is_required else "0"
            uniq = "1" if attr.is_unique else "0"
            pk = "1" if attr.is_primary else "0"
            virt = "1" if attr.is_virtual else "0"
            pub = "1" if attr.is_public else "0"
            excl = "1" if attr.exclude_serialization else "0"
            default = "" if attr.default_value is None else str(attr.default_value)
            type_sig = _type_descriptor_sig(attr.type_descriptor)
            entries.append(
                f"attr:{cc_fqn}:{attr.name}:{acc.position}"
                f":pk={pk}:req={req}:uniq={uniq}:virt={virt}:pub={pub}:excl={excl}:default={default}"
                f":type={type_sig}"
            )
        for fcc in sorted(cc.class_config_function_configs, key=lambda f: f.position):
            ctor = "1" if fcc.is_constructor else "0"
            sig = _function_signature(fcc.function_config)
            entries.append(
                f"fn:{cc_fqn}:{fcc.function_config.name}:{fcc.position}:ctor={ctor}:{sig}"
            )

    # Build stable AttributeConfig id -> signature map for relationship hashing.
    # (Avoids UUIDs; uses the class FQN + attribute name.)
    attr_id_to_sig: dict[UUID, str] = {}
    for cc in class_configs:
        cc_fqn = class_id_to_fqn[cc.id]
        for acc in cc.class_config_attribute_configs:
            attr = acc.attribute_config
            if attr is None:
                if acc.attribute_config_id is not None:
                    attr_id_to_sig[acc.attribute_config_id] = (
                        f"{cc_fqn}::unresolved:{acc.attribute_config_id}"
                    )
                continue
            attr_id_to_sig[attr.id] = f"{cc_fqn}::{attr.name}"
    # Relationships (SSOT: ClassConfigRelationship)
    if class_config_relationships:
        rel_entries: list[str] = []
        for rel in class_config_relationships:
            src_fqn = class_id_to_fqn.get(rel.class_config_id, "")
            tgt_fqn = class_id_to_fqn.get(rel.target_class_config_id, "")
            assoc_fqn = ""
            if (
                rel.class_config_relationship_association_edge is not None
                and rel.class_config_relationship_association_edge.class_config_id
                is not None
            ):
                assoc_fqn = class_id_to_fqn.get(
                    rel.class_config_relationship_association_edge.class_config_id, ""
                )
            fwd = (
                rel.forward_loading_strategy.value
                if rel.forward_loading_strategy is not None
                else ""
            )
            rev = (
                rel.reverse_loading_strategy.value
                if rel.reverse_loading_strategy is not None
                else ""
            )
            req = "1" if rel.forward_required else "0"
            # Relationship attributes (representation) are part of the relationship signature.
            # Deterministic: sort by (direction, role, attr_sig).
            attr_sigs: list[str] = []
            for ra in rel.class_config_relationship_attributes:
                a_sig = attr_id_to_sig.get(ra.attribute_config_id, "")
                attr_sigs.append(f"{ra.direction.value}:{ra.role.value}:{a_sig}")
            attr_sigs = sorted(attr_sigs)
            rel_entries.append(
                f"rel:{src_fqn}->{tgt_fqn}:{rel.relationship_type.value}"
                f":assoc={assoc_fqn}:req={req}:fwd={fwd}:rev={rev}:attrs={'|'.join(attr_sigs)}"
            )
        for line in sorted(rel_entries):
            entries.append(line)

    for e in sorted(enum_configs, key=lambda e: ((e.enum_fqn or "").strip(), e.name)):
        enum_payload = {
            "description": (e.description or "").strip(),
            "enum_fqn": (e.enum_fqn or "").strip(),
            "name": e.name,
            "options": [
                {
                    "description": (opt.description or "").strip(),
                    "label": (opt.label or "").strip(),
                    "position": opt.position,
                    "value": opt.value,
                }
                for opt in sorted(
                    e.enum_options or [],
                    key=lambda opt: (
                        opt.position,
                        opt.value,
                        (opt.label or "").strip(),
                        (opt.description or "").strip(),
                    ),
                )
            ],
        }
        entries.append(
            "enum:"
            + json.dumps(
                enum_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
        )

    for f in sorted(function_configs, key=lambda f: f.name):
        entries.append(f"gfn:{f.name}:{_function_signature(f)}")

    if object_config_graph_bindings:

        def _binding_class_fqn(
            class_config: ClassConfig | None, class_id: UUID | None = None
        ) -> str:
            if class_config is not None:
                explicit = (getattr(class_config, "class_fqn", None) or "").strip()
                if explicit:
                    return explicit
                local = class_id_to_fqn.get(class_config.id)
                if local:
                    return local
                if class_id is not None and class_id in class_id_to_fqn:
                    return class_id_to_fqn[class_id]
                return f"external:{class_config.id}"
            if class_id is not None and class_id in class_id_to_fqn:
                return class_id_to_fqn[class_id]
            return f"external:{class_id}"

        binding_entries: list[str] = []
        for binding in object_config_graph_bindings:
            target_graph_prefix = ""
            if binding.target_object_config_graph is not None:
                target_graph_prefix = (
                    binding.target_object_config_graph.fqn_prefix or ""
                ).strip()
            if (
                not target_graph_prefix
                and binding.target_object_config_graph_id is not None
            ):
                target_graph_prefix = (
                    f"external:{binding.target_object_config_graph_id}"
                )
            binding_entries.append(f"binding:{fqn_prefix}->{target_graph_prefix}")

            for binding_class in sorted(
                binding.object_config_graph_binding_classes or [],
                key=lambda item: (
                    item.name or "",
                    _binding_class_fqn(item.source_class, item.source_class_id),
                    _binding_class_fqn(item.target_class, item.target_class_id),
                    (
                        item.target_attribute.attribute_config.name
                        if item.target_attribute is not None
                        and item.target_attribute.attribute_config is not None
                        else ""
                    ),
                ),
            ):
                source_fqn = _binding_class_fqn(
                    binding_class.source_class, binding_class.source_class_id
                )
                target_fqn = _binding_class_fqn(
                    binding_class.target_class, binding_class.target_class_id
                )
                source_attr = ""
                if (
                    binding_class.source_attr is not None
                    and binding_class.source_attr.attribute_config is not None
                ):
                    source_attr = binding_class.source_attr.attribute_config.name
                target_attr = ""
                if (
                    binding_class.target_attribute is not None
                    and binding_class.target_attribute.attribute_config is not None
                ):
                    target_attr = binding_class.target_attribute.attribute_config.name
                binding_entries.append(
                    "binding_map:"
                    + f"{target_graph_prefix}:{binding_class.name}:{source_fqn}:{source_attr}"
                    + f"->{target_fqn}.{target_attr}:description="
                    + f"{(binding_class.description or '').strip()}"
                )
        for line in sorted(binding_entries):
            entries.append(line)

    # Layout metadata (canonical .aware or other layouts) is part of the materialization identity.
    if include_layout and node_layouts_by_node_key:
        layout_entries: list[str] = []

        for (kind, node_key), layouts in node_layouts_by_node_key.items():
            if not layouts:
                continue
            for layout in layouts:
                layout_kind = layout.layout_kind or ""
                rel_path = layout.relative_path or ""
                pos = (
                    ""
                    if layout.source_position is None
                    else str(layout.source_position)
                )
                layout_entries.append(
                    f"layout:{kind}:{node_key}:{layout_kind}:{rel_path}:{pos}"
                )

        for line in sorted(layout_entries):
            entries.append(line)

    # Annotations are semantic (loading/overlay), so they are part of the graph hash.
    if object_config_graph_annotations:
        ann_entries: list[str] = []
        for ann in object_config_graph_annotations:
            kind = ann.kind
            if (
                kind == ObjectConfigGraphAnnotationKind.load
                and ann.code_section_annotation_load is not None
            ):
                v = ann.code_section_annotation_load
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=_namespace_required(v, context="LOAD annotation hash"),
                    class_name=v.class_name,
                )
                edge = v.edge_name or ""
                fwd = v.forward_strategy.value if v.forward_strategy is not None else ""
                rev = v.reverse_strategy.value if v.reverse_strategy is not None else ""
                ann_entries.append(
                    f"ann:load:{target}::{v.attribute_name}::edge={edge}:fwd={fwd}:rev={rev}"
                )
            elif (
                kind == ObjectConfigGraphAnnotationKind.overlay
                and ann.code_section_annotation_overlay is not None
            ):
                v = ann.code_section_annotation_overlay
                overlay_namespace = _namespace_required(
                    v,
                    context="OVERLAY annotation hash",
                )
                base = (
                    f"{v.fqn_prefix}.{overlay_namespace}"
                    if overlay_namespace
                    else v.fqn_prefix
                )
                entity = (
                    v.entity.value
                    if isinstance(v.entity, CodeSectionAnnotationOverlayEntity)
                    else str(v.entity)
                )
                lang = v.language.value
                member = v.class_name or v.enum_name or ""
                if v.entity == CodeSectionAnnotationOverlayEntity.attribute:
                    member = f"{v.class_name}::{v.attribute_name or ''}"
                elif v.entity == CodeSectionAnnotationOverlayEntity.function:
                    member = f"{v.class_name}::{v.function_name or ''}"
                elif v.entity == CodeSectionAnnotationOverlayEntity.enum_option:
                    member = f"{v.enum_name}::{v.enum_option_name or ''}"
                rename = v.rename or ""
                wire = v.wire_name or ""
                ann_entries.append(
                    f"ann:overlay:{lang}:{entity}:{base}:{member}:rename={rename}:wire={wire}"
                )
            elif (
                kind == ObjectConfigGraphAnnotationKind.discriminate
                and ann.code_section_annotation_discriminate is not None
            ):
                v = ann.code_section_annotation_discriminate
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=_namespace_required(
                        v,
                        context="DISCRIMINATE annotation hash",
                    ),
                    class_name=v.class_name,
                )
                mode = (v.mode or "").strip().lower()
                tag = (v.tag_value or "").strip()
                ann_entries.append(
                    f"ann:discriminate:{target}::{v.attribute_name}:mode={mode}:tag={tag}"
                )
            elif (
                kind == ObjectConfigGraphAnnotationKind.oneof
                and ann.code_section_annotation_oneof is not None
            ):
                v = ann.code_section_annotation_oneof
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=_namespace_required(v, context="ONEOF annotation hash"),
                    class_name=v.class_name,
                )
                mode = (
                    str(getattr(v.mode, "value", v.mode) or "validation")
                    .strip()
                    .lower()
                )
                attrs = ",".join(
                    [a for a in (v.attribute_names or []) if (a or "").strip()]
                )
                ann_entries.append(f"ann:oneof:{target}:mode={mode}:attrs={attrs}")
            elif (
                kind == ObjectConfigGraphAnnotationKind.identity
                and ann.code_section_annotation_identity is not None
            ):
                v = ann.code_section_annotation_identity
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=_namespace_required(v, context="IDENTITY annotation hash"),
                    class_name=v.class_name,
                )
                mode = (
                    str(getattr(v.mode, "value", v.mode) or "contained").strip().lower()
                )
                ann_entries.append(f"ann:identity:{target}:mode={mode}")
            elif (
                kind == ObjectConfigGraphAnnotationKind.reference
                and ann.code_section_annotation_reference is not None
            ):
                v = ann.code_section_annotation_reference
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=_namespace_required(v, context="REFERENCE annotation hash"),
                    class_name=v.class_name,
                )
                mode = (
                    v.mode.value
                    if isinstance(v.mode, CodeSectionAnnotationReferenceMode)
                    else str(v.mode)
                )
                tgt_base = ""
                target_namespace = _namespace_optional(
                    v,
                    attr="target_namespace",
                    context="REFERENCE annotation target hash",
                )
                if v.target_fqn_prefix and target_namespace and v.target_class_name:
                    tgt_base = _class_fqn_from_namespace(
                        fqn_prefix=v.target_fqn_prefix,
                        namespace=target_namespace,
                        class_name=v.target_class_name,
                    )
                tgt_attr = v.target_attribute_name or ""
                ann_entries.append(
                    f"ann:reference:{mode}:{target}::{v.attribute_name}:target={tgt_base}::{tgt_attr}"
                )
            else:
                # Unknown or malformed annotation => include minimal signature so hash changes.
                ann_entries.append(f"ann:unknown:{str(kind)}")

        for line in sorted(ann_entries):
            entries.append(line)

    # Projection declarations are semantic (projection membership/portal SSOT), so they are part of the graph hash.
    if object_projection_graph_declarations:
        decl_entries: list[str] = []
        for decl in sorted(
            object_projection_graph_declarations,
            key=lambda d: (
                (d.projection_name or "").strip(),
                (d.key or "").strip(),
                str(d.id),
            ),
        ):
            projection_name = (decl.projection_name or "").strip()
            if not projection_name:
                continue

            meta_payload = json.dumps(
                {
                    "label": decl.label,
                    "description": decl.description,
                    "is_branchable": bool(decl.is_branchable),
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            decl_entries.append(f"opg_decl:{projection_name}:{meta_payload}")

            bindings = sorted(
                decl.object_projection_graph_bindings or [],
                key=lambda b: (
                    b.fqn_prefix,
                    _namespace_required(b, context="Projection binding hash"),
                    b.class_name,
                    b.attribute_name or "",
                    (b.target_projection_name or "").strip(),
                    (b.side or "").strip().lower(),
                ),
            )
            for b in bindings:
                target = _class_fqn_from_namespace(
                    fqn_prefix=b.fqn_prefix,
                    namespace=_namespace_required(
                        b,
                        context="Projection binding hash",
                    ),
                    class_name=b.class_name,
                )
                attr = b.attribute_name or ""
                portal = (b.target_projection_name or "").strip()
                side = (b.side or "").strip().lower()
                decl_entries.append(
                    f"opg_bind:{projection_name}:{target}:attr={attr}:portal={portal}:side={side}"
                )

        for line in sorted(decl_entries):
            entries.append(line)

    # Mirrors are semantic (DTO surface selection), so they are part of the graph hash.
    if object_config_graph_mirrors:
        mirror_entries: list[str] = []
        for mirror in object_config_graph_mirrors:
            kind = mirror.target_kind
            mirror_namespace = _namespace_required(mirror, context="Mirror hash")
            base = (
                f"{mirror.fqn_prefix}.{mirror_namespace}"
                if mirror_namespace
                else mirror.fqn_prefix
            )
            target_text = mirror.target_text or ""
            mirror_entries.append(
                f"mirror:{kind.value if kind is not None else ''}:{base}:{target_text}"
            )
            if include_layout and mirror.relative_path:
                mirror_entries.append(
                    "mirror-layout:"
                    f"{base}:{target_text}:"
                    f"{mirror.layout_kind}:{mirror.relative_path}:{mirror.source_position or ''}"
                )

        for line in sorted(mirror_entries):
            entries.append(line)

    hasher = hashlib.sha256()
    hasher.update(str(language.value).encode())
    hasher.update(b"\n")
    hasher.update(fqn_prefix.encode())
    hasher.update(b"\n")
    for line in entries:
        hasher.update(line.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()
