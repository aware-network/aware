"""Compiler for first-class `projection { ... }` declarations.

Contract:
- Projections are a grammar-level construct (not authored as `ann` statements).
- Meta compiler resolves projection roots/edges deterministically via FqnResolver/FqnScope.
- Output is persisted as compiler-owned OCG SSOT:
  - `ObjectProjectionGraphDeclaration` (one per projection)
  - `ObjectProjectionGraphBinding` (root + member + portal bindings)
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

# Code Ontology (projection sections)
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection

# Meta Ontology (declarations)
from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
    ObjectProjectionGraphBinding,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)

# Meta Runtime (FQN resolution)
from aware_meta.fqn_resolver import FqnResolver, FqnScope
from aware_meta.graph.config.stable_ids import (
    ocg_stable_uuid,
)
from aware_meta.graph.projection.declarations import (
    ProjectionDeclaration,
    ProjectionObservableDeclaration,
)


@dataclass(frozen=True, slots=True)
class _ResolvedNamespace:
    fqn_prefix: str
    namespace: str


def _namespace_from_fqn(fqn: str) -> _ResolvedNamespace:
    parts = [p for p in (fqn or "").split(".") if p]
    if len(parts) < 2:
        raise ValueError(f"Invalid class FQN (expected pkg[.namespace].Name): {fqn!r}")
    return _ResolvedNamespace(
        fqn_prefix=parts[0],
        namespace=".".join(parts[1:-1]),
    )


def _resolve_class_namespace_from_type_ref(scope: FqnScope, type_ref: str) -> tuple[_ResolvedNamespace, str]:
    resolved = scope.try_resolve_class_with_fqn(type_ref)
    if resolved is None:
        raise ValueError(f"Class not found for projection target: {type_ref}")
    fqn, cls = resolved
    return _namespace_from_fqn(fqn), cls.name


def _stable_opg_declaration_id(
    *,
    object_config_graph_id: UUID,
    projection_name: str,
) -> UUID:
    return ocg_stable_uuid(f"opg_declaration:{object_config_graph_id}:{projection_name}")


def _stable_opg_binding_id(
    *,
    object_projection_graph_declaration_id: UUID,
    fqn_prefix: str,
    namespace: str,
    class_name: str,
    attribute_name: str | None,
    target_projection_name: str | None,
    side: str | None,
) -> UUID:
    # NOTE: IDs must be stable across compiles to avoid churn in OCG-derived artifacts.
    attr = attribute_name or ""
    portal = target_projection_name or ""
    side_key = (side or "").strip().lower()
    return ocg_stable_uuid(
        "opg_binding:"
        f"{object_projection_graph_declaration_id}:"
        f"{_class_fqn(fqn_prefix=fqn_prefix, namespace=namespace, class_name=class_name)}:"
        f"attr={attr}:portal={portal}:side={side_key}"
    )


def _class_fqn(*, fqn_prefix: str, namespace: str, class_name: str) -> str:
    namespace = (namespace or "").strip()
    if not namespace:
        return f"{fqn_prefix}.{class_name}"
    return f"{fqn_prefix}.{namespace}.{class_name}"


def _build_projection_binding(
    *,
    binding_id: UUID,
    object_projection_graph_declaration_id: UUID,
    namespace: _ResolvedNamespace,
    class_name: str,
    attribute_name: str | None,
    target_projection_name: str | None,
    side: str | None,
) -> ObjectProjectionGraphBinding:
    model_fields = getattr(ObjectProjectionGraphBinding, "model_fields", {})
    if "namespace" in model_fields:
        return ObjectProjectionGraphBinding(
            id=binding_id,
            object_projection_graph_declaration_id=object_projection_graph_declaration_id,
            fqn_prefix=namespace.fqn_prefix,
            namespace=namespace.namespace,
            class_name=class_name,
            attribute_name=attribute_name,
            target_projection_name=target_projection_name,
            side=side,
        )
    binding = ObjectProjectionGraphBinding.model_construct(
        id=binding_id,
        object_projection_graph_declaration_id=object_projection_graph_declaration_id,
        fqn_prefix=namespace.fqn_prefix,
        class_name=class_name,
        attribute_name=attribute_name,
        target_projection_name=target_projection_name,
        side=side,
    )
    object.__setattr__(binding, "namespace", namespace.namespace)
    return binding


def compile_object_config_graph_projections(
    code_section_projections: list[CodeSectionProjection],
    fqn_resolver: FqnResolver,
    object_config_graph_id: UUID,
    *,
    ocg_fqn_prefix: str,
) -> tuple[list[ObjectProjectionGraphDeclaration], dict[str, ProjectionDeclaration]]:
    """Compile CodeSectionProjection entries into OCG projection declarations + observable metadata."""

    projections = sorted(
        [p for p in (code_section_projections or []) if (p.projection_name or "").strip()],
        key=lambda p: (
            str(p.code_section.code_id),
            (p.projection_name or "").strip(),
            (p.name or "").strip(),
        ),
    )

    compiled_by_id: dict[UUID, ObjectProjectionGraphDeclaration] = {}
    declarations_by_name: dict[str, ProjectionDeclaration] = {}

    for proj in projections:
        projection_name = (proj.projection_name or "").strip()
        if not projection_name:
            continue

        if projection_name in declarations_by_name:
            raise ValueError(
                f"Duplicate projection declaration for {projection_name!r}; "
                "projections must be declared once per package"
            )

        scope = fqn_resolver.scope_for_code_id(proj.code_section.code_id)

        root_type_ref = (proj.root_type_ref or "").strip()
        if not root_type_ref:
            raise ValueError(f"Projection {projection_name!r} must declare a root type (e.g. `root schema.Type`)")

        # Observable declarations (parsed from projection `view` sections for now).
        observables: list[ProjectionObservableDeclaration] = []
        seen_observable_keys: set[str] = set()
        for idx, view in enumerate(proj.projection_views or []):
            observable_key = (view.key or "").strip()
            kind = (view.kind or "").strip().lower()
            if not observable_key:
                continue
            if observable_key in seen_observable_keys:
                raise ValueError(f"Projection {projection_name!r} defines observable {observable_key!r} multiple times")
            seen_observable_keys.add(observable_key)
            if kind not in {"construct", "instance"}:
                raise ValueError(
                    f"Projection {projection_name!r} observable {observable_key!r} has invalid kind {view.kind!r}"
                )
            observables.append(
                ProjectionObservableDeclaration(
                    key=observable_key,
                    kind=kind,
                    is_default=bool(view.is_default),
                    description=view.description,
                    position=idx,
                )
            )

        declarations_by_name[projection_name] = ProjectionDeclaration(
            projection_name=projection_name,
            label=proj.label,
            description=proj.description,
            is_branchable=bool(proj.is_branchable),
            observables=tuple(observables),
        )

        decl_id = _stable_opg_declaration_id(
            object_config_graph_id=object_config_graph_id,
            projection_name=projection_name,
        )
        decl_key = f"{ocg_fqn_prefix}:{projection_name}"

        bindings_by_id: dict[UUID, ObjectProjectionGraphBinding] = {}

        # Root membership (class is included and marked as root for selection).
        ns, canonical_class_name = _resolve_class_namespace_from_type_ref(scope, root_type_ref)

        binding_id = _stable_opg_binding_id(
            object_projection_graph_declaration_id=decl_id,
            fqn_prefix=ns.fqn_prefix,
            namespace=ns.namespace,
            class_name=canonical_class_name,
            attribute_name=None,
            target_projection_name=None,
            side=None,
        )
        if binding_id not in bindings_by_id:
            bindings_by_id[binding_id] = _build_projection_binding(
                binding_id=binding_id,
                object_projection_graph_declaration_id=decl_id,
                namespace=ns,
                class_name=canonical_class_name,
                attribute_name=None,
                target_projection_name=None,
                side=None,
            )

        # Edge memberships and portals.
        for edge in proj.projection_edges or []:
            type_ref = (edge.type_ref or "").strip()
            member = (edge.member or "").strip()
            if not type_ref or not member:
                continue

            target_projection_name = (edge.target_projection_ref or "").strip() or None
            ns, canonical_class_name = _resolve_class_namespace_from_type_ref(scope, type_ref)

            binding_id = _stable_opg_binding_id(
                object_projection_graph_declaration_id=decl_id,
                fqn_prefix=ns.fqn_prefix,
                namespace=ns.namespace,
                class_name=canonical_class_name,
                attribute_name=member,
                target_projection_name=target_projection_name,
                side=None,
            )
            if binding_id not in bindings_by_id:
                bindings_by_id[binding_id] = _build_projection_binding(
                    binding_id=binding_id,
                    object_projection_graph_declaration_id=decl_id,
                    namespace=ns,
                    class_name=canonical_class_name,
                    attribute_name=member,
                    target_projection_name=target_projection_name,
                    side=None,
                )

        if decl_id not in compiled_by_id:
            compiled_by_id[decl_id] = ObjectProjectionGraphDeclaration(
                id=decl_id,
                object_config_graph_id=object_config_graph_id,
                key=decl_key,
                projection_name=projection_name,
                label=proj.label,
                description=proj.description,
                is_branchable=bool(proj.is_branchable),
                object_projection_graph_bindings=[bindings_by_id[k] for k in sorted(bindings_by_id, key=str)],
            )

    compiled = [compiled_by_id[k] for k in sorted(compiled_by_id, key=str)]
    return compiled, declarations_by_name
