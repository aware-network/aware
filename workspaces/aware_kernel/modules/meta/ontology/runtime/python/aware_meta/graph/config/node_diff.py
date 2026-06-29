from __future__ import annotations
from typing import Any
from uuid import UUID
import hashlib
import json

# Code Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphNodeDelta,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)

# History Ontology
from aware_history_ontology.change.change_enums import ChangeType

from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)


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


def _prefix_from_namespace(*, fqn_prefix: str, namespace: str) -> str:
    namespace = namespace.strip()
    return f"{fqn_prefix}.{namespace}" if namespace else fqn_prefix


def _node_fingerprint(
    node: ObjectConfigGraphNode, *, ctx: dict[str, Any] | None = None
) -> str:
    """
    Deterministic node fingerprint for `ObjectConfigGraphNodeDelta` inference.

    This intentionally mirrors the compiler session fingerprint (semantic fields only, stable ordering).
    """

    def _safe_json(value: Any) -> str:
        try:
            return json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
        except Exception:
            try:
                return str(value)
            except Exception:
                return ""

    def _enum_sig(enum_id: UUID | None, *, ctx: dict[str, Any]) -> str:
        if enum_id is None:
            return ""
        enum_fqn_by_id = ctx.get("enum_fqn_by_id") or {}
        return str(enum_fqn_by_id.get(enum_id) or f"external:{enum_id}")

    def _class_sig(class_id: UUID | None, *, ctx: dict[str, Any]) -> str:
        if class_id is None:
            return ""
        class_fqn_by_id = ctx.get("class_fqn_by_id") or {}
        return str(class_fqn_by_id.get(class_id) or f"external:{class_id}")

    def _primitive_type_sig(
        prim: CodePrimitiveType, *, ctx: dict[str, Any], seen: set[UUID]
    ) -> str:
        if prim is None:
            return ""
        prim_id = prim.id
        if prim_id is not None:
            try:
                prim_uuid = UUID(str(prim_id))
                if prim_uuid in seen:
                    return f"cycle:{prim_uuid}"
                seen.add(prim_uuid)
            except Exception:
                pass

        base_type = prim.base_type
        base = base_type.value if base_type is not None else ""
        constraints_sig = ""
        constraints = prim.constraints
        if constraints is not None:
            constraints_sig = _safe_json(constraints)

        prims_by_id = ctx.get("primitive_types_by_id") or {}

        def _nested_sig(field_name: str) -> str:
            nested = getattr(prim, field_name, None)
            if nested is not None:
                return _primitive_type_sig(nested, ctx=ctx, seen=seen)
            nested_id = getattr(prim, f"{field_name}_id", None)
            if nested_id is None:
                return ""
            nested_obj = prims_by_id.get(nested_id)
            if nested_obj is not None:
                return _primitive_type_sig(nested_obj, ctx=ctx, seen=seen)
            return str(nested_id)

        item = _nested_sig("item_type")
        key = _nested_sig("key_type")
        value = _nested_sig("value_type")

        def _edge_sigs(edge_list_name: str, edge_type_field: str) -> str:
            out: list[str] = []
            for edge in getattr(prim, edge_list_name, []) or []:
                pos = edge.position
                target = getattr(edge, edge_type_field, None)
                target_id = getattr(edge, f"{edge_type_field}_id", None)
                if target is None and target_id is not None:
                    target = prims_by_id.get(target_id)
                out.append(
                    "|".join(
                        [
                            "" if pos is None else str(pos),
                            _primitive_type_sig(target, ctx=ctx, seen=seen),
                        ]
                    )
                )
            return ",".join(sorted(out))

        elements = _edge_sigs("code_primitive_type_element_types", "element_type")
        unions = _edge_sigs("code_primitive_type_union_types", "union_type")

        return (
            f"{base}"
            f":c={constraints_sig}"
            f":item={item}"
            f":key={key}"
            f":value={value}"
            f":elements=[{elements}]"
            f":unions=[{unions}]"
        )

    def _type_descriptor_sig(
        desc: AttributeTypeDescriptor, *, ctx: dict[str, Any], seen: set[UUID]
    ) -> str:
        if desc is None:
            return "none"
        desc_id = desc.id
        if desc_id is not None:
            try:
                desc_uuid = UUID(str(desc_id))
                if desc_uuid in seen:
                    return f"cycle:{desc_uuid}"
                seen.add(desc_uuid)
            except Exception:
                pass

        kind = desc.kind
        kind_val = kind.value if kind is not None else str(kind or "")

        # Primitive descriptor: include primitive type semantics where available.
        if kind_val == "primitive":
            prim_cfg = desc.primitive_config
            if prim_cfg is None:
                # Be lenient: some minimal graphs omit primitive_config wiring. Keep the signature
                # deterministic without forcing callers to fully hydrate descriptor graphs.
                return f"{kind_val}:missing:{desc_id}"
            prim = prim_cfg.primitive_type
            prim_seen: set[UUID] = set()
            prim_sig = _primitive_type_sig(prim, ctx=ctx, seen=prim_seen)
            return f"{kind_val}:{prim_sig}"

        # Enum descriptor: include enum name/FQN when resolvable.
        if kind_val == "enum":
            return f"{kind_val}:{_enum_sig(desc.enum_config_id, ctx=ctx)}"

        # Class descriptor: include class name/FQN when resolvable.
        if kind_val == "class":
            return f"{kind_val}:{_class_sig(desc.class_config_id, ctx=ctx)}"

        collection_kind = desc.collection_kind
        collection_val = collection_kind.value if collection_kind is not None else ""

        # Composite descriptors: include collection kind + ordered child signatures.
        child_entries: list[str] = []
        for link in sorted(
            (desc.child_links or []),
            key=lambda l: (
                l.role.value if l.role is not None else "",
                l.position is None,
                l.position or 0,
            ),
        ):
            role = link.role.value if link.role is not None else ""
            pos = link.position
            pos_sig = "" if pos is None else str(pos)
            child_entries.append(
                f"{role}:{pos_sig}:{_type_descriptor_sig(link.child, ctx=ctx, seen=seen)}"
            )
        children_sig = ",".join(child_entries)
        return f"{kind_val}:{collection_val}[{children_sig}]"

    def _function_signature(fn: FunctionConfig, *, ctx: dict[str, Any]) -> str:
        verb = (fn.verb or "").strip().lower()
        kind = fn.kind.value if fn.kind is not None else ""
        is_async = "1" if bool(fn.is_async) else "0"

        inputs: list[tuple[int, str]] = []
        outputs: list[tuple[int, str]] = []
        for edge in fn.function_config_attribute_configs or []:
            edge_type = edge.type
            edge_type_val = edge_type.value if edge_type is not None else ""
            pos = int(edge.position or 0)
            ac = edge.attribute_config
            name = (ac.name or "").strip() if ac is not None else ""
            if edge_type_val == "input":
                inputs.append((pos, name))
            elif edge_type_val == "output":
                outputs.append((pos, name))

        inputs_sorted = ",".join(
            f"{pos}:{name}" for pos, name in sorted(inputs, key=lambda v: (v[0], v[1]))
        )
        outputs_sorted = ",".join(
            f"{pos}:{name}" for pos, name in sorted(outputs, key=lambda v: (v[0], v[1]))
        )
        return f"kind={kind}:verb={verb}:async={is_async}:in={inputs_sorted}:out={outputs_sorted}"

    ctx = ctx or {}

    node_loc = ""
    try:
        memberships = (ctx.get("node_memberships_by_node_id") or {}).get(node.id) or ()
        node_loc = "|".join(f"{d}.{s}" for d, s in memberships if d or s)
    except Exception:
        node_loc = ""

    ann_by_entity = ctx.get("annotation_sigs_by_entity_id") or {}
    proj_by_entity = ctx.get("projection_sigs_by_entity_id") or {}
    mirror_by_entity = ctx.get("mirror_sigs_by_entity_id") or {}
    global_ann = ctx.get("global_annotation_sigs") or ()
    global_proj = ctx.get("global_projection_sigs") or ()
    global_mirrors = ctx.get("global_mirror_sigs") or ()

    if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
        cc = node.class_config
        class_parts: list[str] = [
            f"fqn_prefix={ctx.get('graph_fqn_prefix') or ''}",
            f"loc={node_loc}",
            f"class={cc.name}",
            f"is_base={cc.is_base}",
            f"parent={_class_sig(cc.parent_class_id, ctx=ctx) if cc.parent_class_id is not None else ''}",
        ]
        anns = ann_by_entity.get(cc.id) or []
        projs = proj_by_entity.get(cc.id) or []
        mirrors = mirror_by_entity.get(cc.id) or []
        if anns:
            class_parts.append("ann=" + ",".join(sorted(anns)))
        if projs:
            class_parts.append("proj=" + ",".join(sorted(projs)))
        if mirrors:
            class_parts.append("mirrors=" + ",".join(sorted(mirrors)))
        if global_ann:
            class_parts.append("ann_global=" + ",".join(sorted(global_ann)))
        if global_proj:
            class_parts.append("proj_global=" + ",".join(sorted(global_proj)))
        if global_mirrors:
            class_parts.append("mirrors_global=" + ",".join(sorted(global_mirrors)))

        attrs: list[str] = []
        for link in sorted(
            cc.class_config_attribute_configs or [], key=lambda a: a.position
        ):
            ac = link.attribute_config
            if ac is None:
                attrs.append(
                    "|".join(
                        [
                            str(link.position),
                            f"unresolved:{link.attribute_config_id}",
                        ]
                    )
                )
                continue
            td_sig = _type_descriptor_sig(
                ac.type_descriptor,
                ctx=ctx,
                seen=set(),
            )
            default = "" if ac.default_value is None else str(ac.default_value)
            attrs.append(
                "|".join(
                    [
                        str(link.position),
                        ac.name,
                        f"type={td_sig}",
                        f"default={default}",
                        f"req={int(bool(ac.is_required))}",
                        f"uniq={int(bool(ac.is_unique))}",
                        f"pk={int(bool(ac.is_primary))}",
                        f"pub={int(bool(ac.is_public))}",
                        f"excl={int(bool(ac.exclude_serialization))}",
                        f"virt={int(bool(ac.is_virtual))}",
                    ]
                )
            )
        funcs: list[str] = []
        for link in sorted(cc.class_config_function_configs, key=lambda f: f.position):
            fc = link.function_config
            ctor = "1" if bool(link.is_constructor) else "0"
            pub = "1" if bool(link.is_public) else "0"
            sig = _function_signature(fc, ctx=ctx)
            funcs.append(
                "|".join(
                    [
                        str(link.position),
                        f"ctor={ctor}",
                        f"pub={pub}",
                        fc.name,
                        sig,
                    ]
                )
            )
        class_parts.append("attrs=" + ",".join(attrs))
        class_parts.append("funcs=" + ",".join(funcs))
        return hashlib.sha256("\n".join(class_parts).encode("utf-8")).hexdigest()

    if node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
        ec = node.enum_config
        enum_parts: list[str] = [
            f"fqn_prefix={ctx.get('graph_fqn_prefix') or ''}",
            f"loc={node_loc}",
        ]
        anns = ann_by_entity.get(ec.id) or []
        mirrors = mirror_by_entity.get(ec.id) or []
        if anns:
            enum_parts.append("ann=" + ",".join(sorted(anns)))
        if mirrors:
            enum_parts.append("mirrors=" + ",".join(sorted(mirrors)))
        if global_ann:
            enum_parts.append("ann_global=" + ",".join(sorted(global_ann)))
        if global_mirrors:
            enum_parts.append("mirrors_global=" + ",".join(sorted(global_mirrors)))

        options: list[str] = []
        for opt in sorted(ec.enum_options or [], key=lambda o: (o.position, o.value)):
            options.append(
                "|".join(
                    [
                        str(opt.position),
                        opt.value,
                        opt.label or "",
                        opt.description or "",
                    ]
                )
            )
        enum_parts.extend([ec.name, ec.description or "", "opts=" + ",".join(options)])
        return hashlib.sha256("\n".join(enum_parts).encode("utf-8")).hexdigest()

    if (
        node.type == ObjectConfigGraphNodeType.function
        and node.function_config is not None
    ):
        fn = node.function_config
        function_parts: list[str] = [
            f"fqn_prefix={ctx.get('graph_fqn_prefix') or ''}",
            f"loc={node_loc}",
        ]
        anns = ann_by_entity.get(fn.id) or []
        mirrors = mirror_by_entity.get(fn.id) or []
        if anns:
            function_parts.append("ann=" + ",".join(sorted(anns)))
        if mirrors:
            function_parts.append("mirrors=" + ",".join(sorted(mirrors)))
        if global_ann:
            function_parts.append("ann_global=" + ",".join(sorted(global_ann)))
        if global_mirrors:
            function_parts.append("mirrors_global=" + ",".join(sorted(global_mirrors)))

        payload = "\n".join(
            [
                fn.name,
                fn.description or "",
                _function_signature(fn, ctx=ctx),
            ]
        )
        function_parts.append(payload)
        return hashlib.sha256("\n".join(function_parts).encode("utf-8")).hexdigest()

    if (
        node.type == ObjectConfigGraphNodeType.relationship
        and node.class_config_relationship is not None
    ):
        rel = node.class_config_relationship
        relationship_parts: list[str] = [
            f"fqn_prefix={ctx.get('graph_fqn_prefix') or ''}",
            f"loc={node_loc}",
        ]
        anns = ann_by_entity.get(rel.id) or []
        mirrors = mirror_by_entity.get(rel.id) or []
        if anns:
            relationship_parts.append("ann=" + ",".join(sorted(anns)))
        if mirrors:
            relationship_parts.append("mirrors=" + ",".join(sorted(mirrors)))
        if global_ann:
            relationship_parts.append("ann_global=" + ",".join(sorted(global_ann)))
        if global_mirrors:
            relationship_parts.append(
                "mirrors_global=" + ",".join(sorted(global_mirrors))
            )

        src = _class_sig(rel.class_config_id, ctx=ctx)
        tgt = _class_sig(rel.target_class_config_id, ctx=ctx)
        assoc = rel.class_config_relationship_association_edge
        assoc_sig = ""
        if assoc is not None:
            assoc_sig = "|".join(
                [
                    _class_sig(assoc.class_config_id, ctx=ctx),
                    (
                        assoc.forward_loading_strategy.value
                        if assoc.forward_loading_strategy is not None
                        else ""
                    ),
                    (
                        assoc.reverse_loading_strategy.value
                        if assoc.reverse_loading_strategy is not None
                        else ""
                    ),
                ]
            )

        attr_sig_by_id = ctx.get("attribute_sig_by_id") or {}
        class_rel_attrs: list[str] = []
        for ra in rel.class_config_relationship_attributes or []:
            direction = ra.direction.value if ra.direction is not None else ""
            role = ra.role.value if ra.role is not None else ""
            aid = ra.attribute_config_id
            a_sig = str(attr_sig_by_id.get(aid) or f"external:{aid}")
            class_rel_attrs.append(f"{direction}:{role}:{a_sig}")
        class_rel_attrs = sorted(class_rel_attrs)

        payload = "\n".join(
            [
                f"{src}->{tgt}",
                (
                    rel.relationship_type.value
                    if rel.relationship_type is not None
                    else ""
                ),
                f"req={int(bool(rel.forward_required))}",
                (
                    rel.forward_loading_strategy.value
                    if rel.forward_loading_strategy is not None
                    else ""
                ),
                (
                    rel.reverse_loading_strategy.value
                    if rel.reverse_loading_strategy is not None
                    else ""
                ),
                (rel.reified_role.value if rel.reified_role is not None else ""),
                "assoc=" + assoc_sig,
                "attrs=" + "|".join(class_rel_attrs),
            ]
        )
        relationship_parts.append(payload)
        return hashlib.sha256("\n".join(relationship_parts).encode("utf-8")).hexdigest()

    raise ValueError(f"Unsupported OCG node type for fingerprint: {node.type}")


def _node_delta(
    *, change_type: ChangeType, node: ObjectConfigGraphNode
) -> ObjectConfigGraphNodeDelta:
    entity_id: UUID
    if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
        entity_id = node.class_config.id
    elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
        entity_id = node.enum_config.id
    elif (
        node.type == ObjectConfigGraphNodeType.function
        and node.function_config is not None
    ):
        entity_id = node.function_config.id
    elif (
        node.type == ObjectConfigGraphNodeType.relationship
        and node.class_config_relationship is not None
    ):
        entity_id = node.class_config_relationship.id
    else:
        raise ValueError(f"Unsupported OCG node type for delta: {node.type}")

    return ObjectConfigGraphNodeDelta(
        change_type=change_type,
        node_type=node.type,
        node_id=node.id,
        entity_id=entity_id,
        payload=None,
        entity_fqn=None,
        source_relative_path=None,
        notes=None,
    )


def diff_object_config_graph_nodes(
    *, before: ObjectConfigGraph, after: ObjectConfigGraph
) -> list[ObjectConfigGraphNodeDelta]:
    def _build_ctx(ocg: ObjectConfigGraph) -> dict[str, Any]:
        # Build a best-effort context so node fingerprints change when the *graph hash* changes
        # due to non-node semantics (namespaces/annotations/mirrors).
        nodes_by_id: dict[UUID, ObjectConfigGraphNode] = {
            n.id: n for n in ocg.object_config_graph_nodes if n.id is not None
        }

        namespace_bundle = build_namespace_bundle_from_ocg_topology(ocg=ocg)

        class_entity_by_key: dict[tuple[str, str], UUID] = {}
        enum_entity_by_key: dict[tuple[str, str], UUID] = {}
        function_entity_by_key: dict[tuple[str, str], UUID] = {}
        class_fqn_by_id: dict[UUID, str] = {}
        enum_fqn_by_id: dict[UUID, str] = {}
        function_fqn_by_id: dict[UUID, str] = {}
        attribute_sig_by_id: dict[UUID, str] = {}

        for node in nodes_by_id.values():
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                cc = node.class_config
                ns = namespace_bundle.namespace_for_class(cc.id)
                if ns is not None:
                    class_entity_by_key[(ns.namespace, cc.name)] = cc.id
                    class_fqn_by_id[cc.id] = _class_fqn_from_namespace(
                        fqn_prefix=ns.package,
                        namespace=ns.namespace,
                        class_name=cc.name,
                    )
                else:
                    class_fqn_by_id[cc.id] = cc.name
                for link in cc.class_config_attribute_configs:
                    ac = link.attribute_config
                    if ac is None:
                        attribute_sig_by_id[link.attribute_config_id] = (
                            f"{class_fqn_by_id[cc.id]}::unresolved:{link.attribute_config_id}"
                        )
                        continue
                    attribute_sig_by_id[ac.id] = f"{class_fqn_by_id[cc.id]}::{ac.name}"

            elif (
                node.type == ObjectConfigGraphNodeType.enum
                and node.enum_config is not None
            ):
                ec = node.enum_config
                ns = namespace_bundle.namespace_for_enum(ec.id)
                if ns is not None:
                    enum_entity_by_key[(ns.namespace, ec.name)] = ec.id
                    enum_fqn_by_id[ec.id] = _class_fqn_from_namespace(
                        fqn_prefix=ns.package,
                        namespace=ns.namespace,
                        class_name=ec.name,
                    )
                else:
                    enum_fqn_by_id[ec.id] = ec.name

            elif (
                node.type == ObjectConfigGraphNodeType.function
                and node.function_config is not None
            ):
                fc = node.function_config
                ns = namespace_bundle.namespace_for_function(fc.id)
                if ns is not None:
                    function_entity_by_key[(ns.namespace, fc.name)] = fc.id
                    function_fqn_by_id[fc.id] = _class_fqn_from_namespace(
                        fqn_prefix=ns.package,
                        namespace=ns.namespace,
                        class_name=fc.name,
                    )
                else:
                    function_fqn_by_id[fc.id] = fc.name

        # Collect primitive types (best-effort) so type descriptor fingerprints can recurse
        # through nested CodePrimitiveType ids when those objects are present in the graph.
        primitive_types_by_id: dict[UUID, Any] = {}

        def _collect_primitive_types_from_desc(desc: AttributeTypeDescriptor) -> None:
            if desc is None:
                return
            try:
                kind = desc.kind.value
            except Exception:
                kind = ""
            if kind == "primitive":
                prim_cfg = desc.primitive_config
                prim = prim_cfg.primitive_type if prim_cfg is not None else None
                pid = prim.id if prim is not None else None
                if pid is not None:
                    try:
                        primitive_types_by_id[UUID(str(pid))] = prim
                    except Exception:
                        pass
            for link in desc.child_links:
                _collect_primitive_types_from_desc(link.child)

        def _collect_from_attribute_config(ac: Any) -> None:
            if ac is None:
                return
            _collect_primitive_types_from_desc(ac.type_descriptor)

        for node in nodes_by_id.values():
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                for link in node.class_config.class_config_attribute_configs or []:
                    _collect_from_attribute_config(link.attribute_config)
                for link in node.class_config.class_config_function_configs or []:
                    fn = link.function_config
                    if fn is None:
                        continue
                    for edge in fn.function_config_attribute_configs or []:
                        _collect_from_attribute_config(edge.attribute_config)
            elif (
                node.type == ObjectConfigGraphNodeType.function
                and node.function_config is not None
            ):
                for edge in (
                    node.function_config.function_config_attribute_configs or []
                ):
                    _collect_from_attribute_config(edge.attribute_config)

        annotation_sigs_by_entity_id: dict[UUID, list[str]] = {}
        global_annotation_sigs: list[str] = []
        for ann in ocg.object_config_graph_annotations or []:
            kind = ann.kind
            sig = ""
            target_entity_id: UUID | None = None

            if (
                ObjectConfigGraphAnnotationKind is not None
                and kind == ObjectConfigGraphAnnotationKind.load
                and ann.code_section_annotation_load is not None
            ):
                v = ann.code_section_annotation_load
                namespace = _namespace_required(v, context="LOAD annotation diff")
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=namespace,
                    class_name=v.class_name,
                )
                edge = v.edge_name or ""
                fwd = v.forward_strategy.value if v.forward_strategy is not None else ""
                rev = v.reverse_strategy.value if v.reverse_strategy is not None else ""
                sig = f"ann:load:{target}::{v.attribute_name}::edge={edge}:fwd={fwd}:rev={rev}"
                target_entity_id = class_entity_by_key.get(
                    (namespace, v.class_name)
                )

            elif (
                ObjectConfigGraphAnnotationKind is not None
                and kind == ObjectConfigGraphAnnotationKind.overlay
                and ann.code_section_annotation_overlay is not None
            ):
                v = ann.code_section_annotation_overlay
                namespace = _namespace_required(v, context="OVERLAY annotation diff")
                base = _prefix_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=namespace,
                )
                entity_val = (
                    v.entity.value
                    if CodeSectionAnnotationOverlayEntity is not None
                    and isinstance(v.entity, CodeSectionAnnotationOverlayEntity)
                    else str(v.entity)
                )
                lang = v.language.value
                member = v.class_name or v.enum_name or ""
                if (
                    CodeSectionAnnotationOverlayEntity is not None
                    and v.entity == CodeSectionAnnotationOverlayEntity.attribute
                ):
                    member = f"{v.class_name}::{v.attribute_name or ''}"
                elif (
                    CodeSectionAnnotationOverlayEntity is not None
                    and v.entity == CodeSectionAnnotationOverlayEntity.function
                ):
                    member = f"{v.class_name}::{v.function_name or ''}"
                elif (
                    CodeSectionAnnotationOverlayEntity is not None
                    and v.entity == CodeSectionAnnotationOverlayEntity.enum_option
                ):
                    member = f"{v.enum_name}::{v.enum_option_name or ''}"
                rename = v.rename or ""
                wire = v.wire_name or ""
                sig = f"ann:overlay:{lang}:{entity_val}:{base}:{member}:rename={rename}:wire={wire}"

                if (
                    CodeSectionAnnotationOverlayEntity is not None
                    and v.entity
                    in (
                        CodeSectionAnnotationOverlayEntity.enum,
                        CodeSectionAnnotationOverlayEntity.enum_option,
                    )
                    and v.enum_name
                ):
                    target_entity_id = enum_entity_by_key.get(
                        (namespace, v.enum_name)
                    )
                elif v.class_name:
                    target_entity_id = class_entity_by_key.get(
                        (namespace, v.class_name)
                    )
                elif v.function_name:
                    target_entity_id = function_entity_by_key.get(
                        (namespace, v.function_name)
                    )

            elif (
                ObjectConfigGraphAnnotationKind is not None
                and kind == ObjectConfigGraphAnnotationKind.discriminate
                and ann.code_section_annotation_discriminate is not None
            ):
                v = ann.code_section_annotation_discriminate
                namespace = _namespace_required(
                    v,
                    context="DISCRIMINATE annotation diff",
                )
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=namespace,
                    class_name=v.class_name,
                )
                mode = (v.mode or "").strip().lower()
                tag = (v.tag_value or "").strip()
                sig = f"ann:discriminate:{target}::{v.attribute_name}:mode={mode}:tag={tag}"
                target_entity_id = class_entity_by_key.get(
                    (namespace, v.class_name)
                )

            elif (
                ObjectConfigGraphAnnotationKind is not None
                and kind == ObjectConfigGraphAnnotationKind.oneof
                and ann.code_section_annotation_oneof is not None
            ):
                v = ann.code_section_annotation_oneof
                namespace = _namespace_required(v, context="ONEOF annotation diff")
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=namespace,
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
                sig = f"ann:oneof:{target}:mode={mode}:attrs={attrs}"
                target_entity_id = class_entity_by_key.get(
                    (namespace, v.class_name)
                )

            elif (
                ObjectConfigGraphAnnotationKind is not None
                and kind == ObjectConfigGraphAnnotationKind.identity
                and ann.code_section_annotation_identity is not None
            ):
                v = ann.code_section_annotation_identity
                namespace = _namespace_required(v, context="IDENTITY annotation diff")
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=namespace,
                    class_name=v.class_name,
                )
                mode = (
                    str(getattr(v.mode, "value", v.mode) or "contained").strip().lower()
                )
                sig = f"ann:identity:{target}:mode={mode}"
                target_entity_id = class_entity_by_key.get(
                    (namespace, v.class_name)
                )

            elif (
                ObjectConfigGraphAnnotationKind is not None
                and kind == ObjectConfigGraphAnnotationKind.reference
                and ann.code_section_annotation_reference is not None
            ):
                v = ann.code_section_annotation_reference
                namespace = _namespace_required(v, context="REFERENCE annotation diff")
                target = _class_fqn_from_namespace(
                    fqn_prefix=v.fqn_prefix,
                    namespace=namespace,
                    class_name=v.class_name,
                )
                mode = (
                    v.mode.value
                    if CodeSectionAnnotationReferenceMode is not None
                    and isinstance(v.mode, CodeSectionAnnotationReferenceMode)
                    else str(v.mode)
                )
                tgt_base = ""
                target_namespace = _namespace_optional(
                    v,
                    attr="target_namespace",
                    context="REFERENCE annotation target diff",
                )
                if v.target_fqn_prefix and target_namespace and v.target_class_name:
                    tgt_base = _class_fqn_from_namespace(
                        fqn_prefix=v.target_fqn_prefix,
                        namespace=target_namespace,
                        class_name=v.target_class_name,
                    )
                tgt_attr = v.target_attribute_name or ""
                sig = f"ann:reference:{mode}:{target}::{v.attribute_name}:target={tgt_base}::{tgt_attr}"
                target_entity_id = class_entity_by_key.get(
                    (namespace, v.class_name)
                )

            else:
                sig = f"ann:unknown:{str(kind)}"

            if not sig:
                continue
            if target_entity_id is not None:
                annotation_sigs_by_entity_id.setdefault(target_entity_id, []).append(
                    sig
                )
            else:
                global_annotation_sigs.append(sig)

        for sigs in annotation_sigs_by_entity_id.values():
            sigs.sort()
        global_annotation_sigs = sorted(set(global_annotation_sigs))

        projection_sigs_by_entity_id: dict[UUID, list[str]] = {}
        global_projection_sigs: list[str] = []
        for decl in ocg.object_projection_graph_declarations or []:
            projection_name = (decl.projection_name or "").strip()
            if not projection_name:
                continue

            meta_payload = ""
            try:
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
            except Exception:
                meta_payload = ""
            decl_sig = f"opg_decl:{projection_name}:{meta_payload}"

            # Prefer attaching declaration metadata to the local root class (when present)
            # so a projection-only change doesn't churn every node delta.
            root_binding = next(
                (
                    b
                    for b in (decl.object_projection_graph_bindings or [])
                    if b.attribute_name is None
                    and not (b.target_projection_name or "").strip()
                ),
                None,
            )
            if (
                root_binding is not None
                and (root_binding.fqn_prefix or "").strip()
                == (ocg.fqn_prefix or "").strip()
            ):
                root_entity_id = class_entity_by_key.get(
                    (
                        _namespace_required(
                            root_binding,
                            context="Projection root binding diff",
                        ),
                        root_binding.class_name,
                    )
                )
                if root_entity_id is not None:
                    projection_sigs_by_entity_id.setdefault(root_entity_id, []).append(
                        decl_sig
                    )
                else:
                    global_projection_sigs.append(decl_sig)
            else:
                global_projection_sigs.append(decl_sig)

            for b in decl.object_projection_graph_bindings or []:
                namespace = _namespace_required(b, context="Projection binding diff")
                target = _class_fqn_from_namespace(
                    fqn_prefix=b.fqn_prefix,
                    namespace=namespace,
                    class_name=b.class_name,
                )
                attr = b.attribute_name or ""
                portal = (b.target_projection_name or "").strip()
                side = (b.side or "").strip().lower()
                bind_sig = f"opg_bind:{projection_name}:{target}:attr={attr}:portal={portal}:side={side}"

                if (b.fqn_prefix or "").strip() == (ocg.fqn_prefix or "").strip():
                    entity_id = class_entity_by_key.get(
                        (namespace, b.class_name)
                    )
                    if entity_id is not None:
                        projection_sigs_by_entity_id.setdefault(entity_id, []).append(
                            bind_sig
                        )
                        continue

                global_projection_sigs.append(bind_sig)

        for sigs in projection_sigs_by_entity_id.values():
            sigs.sort()
        global_projection_sigs = sorted(set(global_projection_sigs))

        mirror_sigs_by_entity_id: dict[UUID, list[str]] = {}
        global_mirror_sigs: list[str] = []
        for mirror in ocg.object_config_graph_mirrors or []:
            kind = mirror.target_kind
            kind_val = kind.value if kind is not None else ""
            base = _prefix_from_namespace(
                fqn_prefix=mirror.fqn_prefix,
                namespace=_namespace_required(mirror, context="Mirror diff"),
            )
            target_text = mirror.target_text or ""
            sig = f"mirror:{kind_val}:{base}:{target_text}"
            entity_id = mirror.class_config_id or mirror.enum_config_id
            if entity_id is None:
                global_mirror_sigs.append(sig)
            else:
                try:
                    mirror_sigs_by_entity_id.setdefault(
                        UUID(str(entity_id)), []
                    ).append(sig)
                except Exception:
                    global_mirror_sigs.append(sig)

        for sigs in mirror_sigs_by_entity_id.values():
            sigs.sort()
        global_mirror_sigs = sorted(set(global_mirror_sigs))

        return {
            "graph_fqn_prefix": (ocg.fqn_prefix or "").strip(),
            "node_memberships_by_node_id": node_memberships_by_node_id,
            "class_fqn_by_id": class_fqn_by_id,
            "enum_fqn_by_id": enum_fqn_by_id,
            "function_fqn_by_id": function_fqn_by_id,
            "attribute_sig_by_id": attribute_sig_by_id,
            "annotation_sigs_by_entity_id": annotation_sigs_by_entity_id,
            "global_annotation_sigs": global_annotation_sigs,
            "projection_sigs_by_entity_id": projection_sigs_by_entity_id,
            "global_projection_sigs": global_projection_sigs,
            "mirror_sigs_by_entity_id": mirror_sigs_by_entity_id,
            "global_mirror_sigs": global_mirror_sigs,
            "primitive_types_by_id": primitive_types_by_id,
        }

    before_ctx = _build_ctx(before)
    after_ctx = _build_ctx(after)

    before_nodes_by_id: dict[UUID, ObjectConfigGraphNode] = {
        n.id: n for n in before.object_config_graph_nodes if n.id is not None
    }
    after_nodes_by_id: dict[UUID, ObjectConfigGraphNode] = {
        n.id: n for n in after.object_config_graph_nodes if n.id is not None
    }

    deltas: list[ObjectConfigGraphNodeDelta] = []
    before_ids = set(before_nodes_by_id.keys())
    after_ids = set(after_nodes_by_id.keys())

    for node_id in sorted(before_ids - after_ids, key=str):
        deltas.append(
            _node_delta(change_type=ChangeType.delete, node=before_nodes_by_id[node_id])
        )

    for node_id in sorted(after_ids - before_ids, key=str):
        deltas.append(
            _node_delta(change_type=ChangeType.create, node=after_nodes_by_id[node_id])
        )

    for node_id in sorted(before_ids & after_ids, key=str):
        old = before_nodes_by_id[node_id]
        new = after_nodes_by_id[node_id]
        if _node_fingerprint(old, ctx=before_ctx) != _node_fingerprint(
            new, ctx=after_ctx
        ):
            deltas.append(_node_delta(change_type=ChangeType.update, node=new))

    return deltas
