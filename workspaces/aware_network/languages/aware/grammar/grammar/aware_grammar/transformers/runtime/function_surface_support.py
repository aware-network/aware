"""Concrete runtime support owner for function-surface lowering."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from aware_meta.attribute.config.type_descriptor_builder import ensure_stable_descriptor_tree_ids
from aware_meta.function.impl.builder import (
    apply_function_impl_kind,
    build_function_impl_from_body,
    build_function_invocation_plan_from_body,
    build_function_invocation_plan_from_impl,
    clone_function_impl_from_template,
)
from aware_meta.graph.config.namespace.builder import build_namespace_bundle_from_ocg_topology
from aware_meta.graph.config.package.constants import deterministic_uuid
from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_class_relationship_attribute_id,
    stable_function_config_attribute_config_id,
    stable_function_config_id,
    stable_function_config_invocation_id,
    stable_function_impl_instruction_invoke_attribute_config_id,
    stable_join_id,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode
from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)
from aware_meta_ontology.function.function_config_invocation import (
    FunctionConfigInvocation,
)
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
)
from aware_meta_ontology.function.function_impl_instruction_invoke import (
    FunctionImplInstructionInvoke,
)
from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
    FunctionImplInstructionInvokeAttributeConfig,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_types import JsonObject
from aware_utils.string_transform import to_snake_case

from aware_grammar.transformers.runtime.clone_support import clone_attribute_config_for_runtime_function
from aware_grammar.transformers.runtime.support import RuntimeTransformSupport

type FkOwnerIndex = dict[
    tuple[UUID, UUID],
    tuple[tuple[ClassConfigRelationshipAttribute, AttributeConfig], ...],
]


@dataclass(slots=True)
class RuntimeFunctionSurfaceSupport:
    """Own runtime invocation truth and `_via_*` constructor closure."""

    support: RuntimeTransformSupport

    def materialize_path_scoped_constructors(
        self,
        *,
        source_graph: ObjectConfigGraph,
        class_configs: list[ClassConfig],
        function_configs: list[FunctionConfig],
        relationships: list[ClassConfigRelationship],
    ) -> None:
        """Lower nested constructor propagation into path-scoped runtime constructors."""

        if not class_configs:
            return

        class_by_id: dict[UUID, ClassConfig] = {cls.id: cls for cls in class_configs}
        function_by_id: dict[UUID, FunctionConfig] = {}
        function_owner_by_id: dict[UUID, ClassConfig] = {}
        source_function_by_id: dict[UUID, FunctionConfig] = {}
        source_function_by_code_section_id: dict[UUID, FunctionConfig] = {}
        relationship_by_id: dict[UUID, ClassConfigRelationship] = {rel.id: rel for rel in relationships}

        for ocg_rel in source_graph.object_config_graph_relationships:
            for rel in ocg_rel.class_config_relationships:
                if rel.id not in relationship_by_id:
                    relationship_by_id[rel.id] = rel
        for cls in class_configs:
            for rel in cls.class_config_relationships:
                if rel.id not in relationship_by_id:
                    relationship_by_id[rel.id] = rel

        for node in source_graph.object_config_graph_nodes:
            source_cls = node.class_config
            if source_cls is None:
                continue
            for link in source_cls.class_config_function_configs:
                fn = link.function_config
                source_function_by_id[fn.id] = fn
                if fn.code_section_function_id is not None:
                    if fn.code_section_function_id not in source_function_by_code_section_id:
                        source_function_by_code_section_id[fn.code_section_function_id] = fn

        for cls in class_configs:
            for link in cls.class_config_function_configs:
                fn = link.function_config
                function_by_id[fn.id] = fn
                function_owner_by_id[fn.id] = cls

        constructor_function_ids: set[UUID] = {
            link.function_config_id
            for cls in class_configs
            for link in cls.class_config_function_configs
            if link.is_constructor and link.function_config_id is not None
        }

        fk_attrs_by_relationship_and_owner_class = self._index_foreign_keys_by_relationship_owner_class(
            class_configs=class_configs,
            relationships=list(relationship_by_id.values()),
        )
        class_fqn_by_id = self._resolve_class_fqn_by_id(source_graph=source_graph, class_configs=class_configs)
        existing_names_by_class_id: dict[UUID, set[str]] = {
            cls.id: {link.function_config.name for link in cls.class_config_function_configs} for cls in class_configs
        }

        path_constructor_by_key: dict[tuple[UUID, UUID, tuple[UUID, ...]], FunctionConfig] = {}
        synthetic_functions_by_class: dict[UUID, list[FunctionConfig]] = {}
        synthetic_functions: list[FunctionConfig] = []
        template_constructor_ids: set[UUID] = set()

        ordered_owner_classes = sorted(class_configs, key=lambda cls: (cls.name, str(cls.id)))
        pending_owner_functions_by_class: dict[UUID, list[FunctionConfig]] = {}
        next_owner_function_index_by_class: dict[UUID, int] = {}
        for owner_cls in ordered_owner_classes:
            owner_links = sorted(
                owner_cls.class_config_function_configs,
                key=lambda link: (
                    link.position,
                    link.function_config.name,
                    str(link.function_config_id),
                ),
            )
            pending_owner_functions_by_class[owner_cls.id] = [link.function_config for link in owner_links]
            next_owner_function_index_by_class[owner_cls.id] = 0

        progressed = True
        while progressed:
            progressed = False
            for owner_cls in ordered_owner_classes:
                pending_owner_functions = pending_owner_functions_by_class.setdefault(owner_cls.id, [])
                next_index = next_owner_function_index_by_class.setdefault(owner_cls.id, 0)
                while next_index < len(pending_owner_functions):
                    owner_fn = pending_owner_functions[next_index]
                    next_index += 1
                    progressed = True
                    invocations = sorted(owner_fn.invocations, key=lambda inv: (inv.position, str(inv.id)))
                    for invocation in invocations:
                        kind = invocation.kind.value.strip().lower()
                        if kind != FunctionInvocationKind.construct.value:
                            continue

                        relationship_id = invocation.class_config_relationship_id
                        if relationship_id is None and invocation.class_config_relationship is not None:
                            relationship_id = invocation.class_config_relationship.id
                        if relationship_id is None:
                            continue

                        relationship = relationship_by_id.get(relationship_id)
                        if relationship is None:
                            raise ValueError(
                                "path-constructor propagation relationship id is missing from canonical relationship set "
                                + f"(invocation_id={invocation.id}, relationship_id={relationship_id})"
                            )

                        target_fn = invocation.target_function_config
                        if target_fn is None:
                            target_fn = function_by_id.get(invocation.target_function_config_id)
                        if target_fn is None:
                            target_fn = next(
                                (fn for fn in function_configs if fn.id == invocation.target_function_config_id),
                                None,
                            )
                        if target_fn is None:
                            continue

                        canonical_target_fn = target_fn
                        target_code_section_id = target_fn.code_section_function_id
                        if target_code_section_id is not None:
                            canonical_target_fn = source_function_by_code_section_id.get(
                                target_code_section_id,
                                target_fn,
                            )

                        if canonical_target_fn.id not in constructor_function_ids:
                            continue

                        target_cls = function_owner_by_id.get(canonical_target_fn.id)
                        if target_cls is None:
                            target_cls = function_owner_by_id.get(target_fn.id)
                        if target_cls is None:
                            continue
                        # Standalone identity keeps a semantic public constructor surface.
                        # The caller's invocation metadata and runtime propagation scope still
                        # carry the containment/path rail, but we do not surface that path as a
                        # generated public `_via_*` constructor on the standalone target class.
                        if self.support.class_identity_mode(cls=target_cls) is ClassIdentityMode.standalone:
                            continue

                        template_constructor_ids.add(canonical_target_fn.id)

                        path_rel_ids = (relationship.id,)
                        key = (canonical_target_fn.id, owner_cls.id, path_rel_ids)
                        synthetic_fn = path_constructor_by_key.get(key)
                        if synthetic_fn is None:
                            target_owner_fqn = class_fqn_by_id.get(target_cls.id)
                            if target_owner_fqn is None:
                                raise ValueError(
                                    "Cannot lower path constructor without class namespace mapping: "
                                    + f"class={target_cls.name} class_id={target_cls.id}"
                                )

                            path_tokens = self._invocation_path_tokens(
                                invocation=invocation,
                                relationship=relationship,
                            )
                            path_name = self._path_constructor_name(
                                base_name=target_fn.name,
                                owner_class=owner_cls,
                            )
                            used_names = existing_names_by_class_id.setdefault(target_cls.id, set())
                            if path_name in used_names:
                                collision_name = self._path_constructor_collision_name(
                                    base_name=target_fn.name,
                                    owner_class=owner_cls,
                                    receiver_path_tokens=path_tokens,
                                )
                                if collision_name not in used_names:
                                    path_name = collision_name
                                else:
                                    suffix = deterministic_uuid(
                                        f"runtime_path_constructor:{target_fn.id}:{owner_cls.id}:{path_rel_ids}"
                                    ).hex[:8]
                                    path_name = f"{collision_name}_{suffix}"

                            canonical_relationship = (
                                relationship_by_id.get(relationship.reified_from_relationship_id)
                                if relationship.reified_from_relationship_id is not None
                                else None
                            )
                            parent_fk_attr = self._resolve_parent_fk_attribute_for_path(
                                target_class=target_cls,
                                owner_class=owner_cls,
                                relationship=relationship,
                                canonical_relationship=canonical_relationship,
                                fk_attrs_by_relationship_and_owner_class=fk_attrs_by_relationship_and_owner_class,
                            )
                            if any(
                                link.attribute_config_id == parent_fk_attr.id
                                for link in target_cls.class_config_attribute_configs
                            ):
                                self.support.mark_class_attribute_identity_key(
                                    cls=target_cls,
                                    attribute_config_id=parent_fk_attr.id,
                                )

                            synthetic_fn = self._build_path_constructor_function(
                                target_function=canonical_target_fn,
                                source_function=source_function_by_id.get(canonical_target_fn.id),
                                target_class=target_cls,
                                target_owner_fqn=target_owner_fqn,
                                path_function_name=path_name,
                                parent_fk_attribute=parent_fk_attr,
                            )
                            used_names.add(path_name)
                            path_constructor_by_key[key] = synthetic_fn
                            synthetic_functions.append(synthetic_fn)
                            synthetic_functions_by_class.setdefault(target_cls.id, []).append(synthetic_fn)
                            function_by_id[synthetic_fn.id] = synthetic_fn
                            function_owner_by_id[synthetic_fn.id] = target_cls
                            constructor_function_ids.add(synthetic_fn.id)
                            pending_owner_functions_by_class.setdefault(target_cls.id, []).append(synthetic_fn)
                            if target_cls.id not in next_owner_function_index_by_class:
                                next_owner_function_index_by_class[target_cls.id] = 0

                        self._retarget_invocation_to_function(
                            invocation=invocation,
                            target_function=synthetic_fn,
                        )
                        self._retarget_function_impl_invokes(
                            owner_function=owner_fn,
                            original_target_function=target_fn,
                            original_target_function_id=target_fn.id,
                            relationship_id=invocation.class_config_relationship_id,
                            target_function=synthetic_fn,
                        )
                next_owner_function_index_by_class[owner_cls.id] = next_index

        if not synthetic_functions:
            return

        for class_id, class_synthetic_fns in sorted(
            synthetic_functions_by_class.items(),
            key=lambda item: (class_by_id[item[0]].name, str(item[0])),
        ):
            cls = class_by_id[class_id]
            max_position = max((link.position for link in cls.class_config_function_configs), default=-1)
            next_position = max_position + 1
            for fn in sorted(class_synthetic_fns, key=lambda function: (function.name, str(function.id))):
                cls.class_config_function_configs.append(
                    ClassConfigFunctionConfig(
                        id=stable_join_id(
                            join_kind="class_fn",
                            left_id=cls.id,
                            right_id=fn.id,
                        ),
                        class_config_id=cls.id,
                        function_config=fn,
                        function_config_id=fn.id,
                        is_public=True,
                        is_constructor=True,
                        position=next_position,
                    )
                )
                next_position += 1

        existing_function_ids = {fn.id for fn in function_configs}
        for fn in sorted(synthetic_functions, key=lambda function: (function.name, str(function.id))):
            if fn.id in existing_function_ids:
                continue
            function_configs.append(fn)
            existing_function_ids.add(fn.id)

        if template_constructor_ids:
            for cls in class_configs:
                cls.class_config_function_configs = [
                    link
                    for link in cls.class_config_function_configs
                    if link.function_config_id not in template_constructor_ids
                ]
            function_configs[:] = [fn for fn in function_configs if fn.id not in template_constructor_ids]

    def complete_runtime_function_resolution(
        self,
        *,
        class_configs: list[ClassConfig],
        replace_existing_body_lowering: bool = False,
    ) -> None:
        """Complete FunctionImpl and invocation lowering once runtime topology is honest."""

        ordered_classes = sorted(class_configs, key=lambda cls: (cls.name, str(cls.id)))
        for cls in ordered_classes:
            ordered_functions = sorted(
                cls.class_config_function_configs,
                key=lambda link: (
                    link.position,
                    link.function_config.name,
                    str(link.function_config_id),
                ),
            )
            for fn_link in ordered_functions:
                fn = fn_link.function_config
                body_backed = fn.code_section_function is not None and fn.code_section_function.body_segment is not None

                if body_backed and (replace_existing_body_lowering or fn.function_impl is None):
                    fn.function_impl = build_function_impl_from_body(
                        function_config=fn,
                        owner_class_config=cls,
                        fail_on_unresolved=True,
                        is_constructor=bool(fn_link.is_constructor),
                    )

                if body_backed and replace_existing_body_lowering:
                    fn.invocations.clear()

                if fn.function_impl is not None:
                    apply_function_impl_kind(
                        function_config=fn,
                        function_impl=fn.function_impl,
                        is_constructor=bool(fn_link.is_constructor),
                    )

                if fn.invocations:
                    continue

                if body_backed:
                    fn.invocations = build_function_invocation_plan_from_body(
                        function_config=fn,
                        owner_class_config=cls,
                        fail_on_unresolved=True,
                    )
                    if fn.invocations:
                        continue

                if fn.function_impl is None:
                    continue

                fn.invocations = build_function_invocation_plan_from_impl(
                    function_config=fn,
                    function_impl=fn.function_impl,
                    capture_name_by_sequence={},
                )

    def _resolve_class_fqn_by_id(
        self,
        *,
        source_graph: ObjectConfigGraph,
        class_configs: Sequence[ClassConfig],
    ) -> dict[UUID, str]:
        """Resolve class FQNs from topology first, then code provenance."""

        out: dict[UUID, str] = {}
        class_by_id = {cls.id: cls for cls in class_configs}

        topo_bundle = build_namespace_bundle_from_ocg_topology(ocg=source_graph)
        for class_id, namespace in topo_bundle.namespace_by_class_config_id.items():
            cls = class_by_id.get(class_id)
            if cls is None:
                continue
            out[class_id] = namespace.fqn(cls.name)

        namespace_by_code_id = self.support.namespace_by_code_id
        for cls in class_configs:
            if cls.id in out:
                continue
            code_section_class = cls.code_section_class
            if code_section_class is None or namespace_by_code_id is None:
                continue
            namespace = namespace_by_code_id.get(code_section_class.code_section.code_id)
            if namespace is None:
                continue
            out[cls.id] = namespace.fqn(cls.name)

        return out

    def _path_constructor_name(
        self,
        *,
        base_name: str,
        owner_class: ClassConfig,
    ) -> str:
        owner_token = to_snake_case(owner_class.name)
        suffix = owner_token.strip("_") or "path"
        return f"{base_name}_via_{suffix}"

    def _path_constructor_collision_name(
        self,
        *,
        base_name: str,
        owner_class: ClassConfig,
        receiver_path_tokens: Sequence[str],
    ) -> str:
        base = self._path_constructor_name(
            base_name=base_name,
            owner_class=owner_class,
        )
        path_tokens = [to_snake_case(token).strip("_") for token in receiver_path_tokens if token]
        path_tokens = [token for token in path_tokens if token]
        if not path_tokens:
            return base
        return f"{base}_{'_'.join(path_tokens)}"

    def _invocation_path_tokens(
        self,
        *,
        invocation: FunctionConfigInvocation,
        relationship: ClassConfigRelationship | None = None,
    ) -> list[str]:
        rel = relationship or invocation.class_config_relationship
        if rel is None:
            return []
        member = self._forward_reference_member_name(rel)
        if member is None:
            return []
        return [member]

    def _forward_reference_member_name(self, relationship: ClassConfigRelationship) -> str | None:
        for rel_attr in relationship.class_config_relationship_attributes:
            if (
                rel_attr.direction == ClassConfigRelationshipDirection.forward
                and rel_attr.role == ClassConfigRelationshipAttributeRole.reference
                and rel_attr.attribute_config is not None
                and rel_attr.attribute_config.name
            ):
                return rel_attr.attribute_config.name
        return None

    def _resolve_parent_fk_attribute_for_path(
        self,
        *,
        target_class: ClassConfig,
        owner_class: ClassConfig,
        relationship: ClassConfigRelationship,
        canonical_relationship: ClassConfigRelationship | None = None,
        fk_attrs_by_relationship_and_owner_class: FkOwnerIndex,
    ) -> AttributeConfig:
        key = (relationship.id, target_class.id)
        candidates = fk_attrs_by_relationship_and_owner_class.get(key, ())
        if not candidates:
            synthesized = self._materialize_reified_association_target_parent_fk_for_path(
                target_class=target_class,
                owner_class=owner_class,
                relationship=relationship,
                canonical_relationship=canonical_relationship,
                fk_attrs_by_relationship_and_owner_class=fk_attrs_by_relationship_and_owner_class,
            )
            if synthesized is not None:
                candidates = fk_attrs_by_relationship_and_owner_class.get(key, ())
        if not candidates:
            raise ValueError(
                "no-guess propagation foreign key resolution failed: relationship has no synthesized FK for target class "
                + f"(relationship_id={relationship.id}, owner_class={owner_class.name!r}, target_class={target_class.name!r}). "
                + "Ensure containment rails synthesize child-owned parent FK anchors and do not declare propagation FK fields in .aware."
            )
        if len(candidates) > 1:
            expected_direction = self._relationship_direction_for_owner(
                relationship=relationship,
                owner_class=owner_class,
            )
            if expected_direction is not None:
                directional_candidates = tuple(
                    candidate for candidate in candidates if candidate[0].direction == expected_direction
                )
                if len(directional_candidates) == 1:
                    candidates = directional_candidates
                elif len(directional_candidates) > 1:
                    candidate_names = ", ".join(sorted(attr.name for (_, attr) in directional_candidates if attr.name))
                    raise ValueError(
                        "no-guess propagation foreign key resolution failed: relationship maps to multiple owner-side FK candidates "
                        + f"(relationship_id={relationship.id}, owner_class={owner_class.name!r}, target_class={target_class.name!r}, "
                        + f"expected_direction={expected_direction.value!r}, candidates=[{candidate_names}])."
                    )
        if not candidates:
            raise ValueError(
                "no-guess propagation foreign key resolution failed: relationship has no FK candidates "
                + f"(relationship_id={relationship.id}, owner_class={owner_class.name!r}, target_class={target_class.name!r}). "
                + "Ensure FK synthesis from relationship contracts completed and do not declare propagation FK fields in .aware."
            )
        _, parent_fk_attr = candidates[0]
        if parent_fk_attr.code_section_attribute is not None:
            raise ValueError(
                "no-guess propagation foreign key resolution failed: propagation FK must be transformer-synthesized, "
                + "found authored attribute in source contract "
                + f"(relationship_id={relationship.id}, owner_class={owner_class.name!r}, target_class={target_class.name!r}, "
                + f"attribute={parent_fk_attr.name!r})."
            )
        return parent_fk_attr

    def _materialize_reified_association_target_parent_fk_for_path(
        self,
        *,
        target_class: ClassConfig,
        owner_class: ClassConfig,
        relationship: ClassConfigRelationship,
        canonical_relationship: ClassConfigRelationship | None,
        fk_attrs_by_relationship_and_owner_class: FkOwnerIndex,
    ) -> AttributeConfig | None:
        if relationship.reified_role != ClassConfigRelationshipReifiedRole.association_to_target:
            return None
        if owner_class.id != relationship.class_config_id:
            return None
        if target_class.id != relationship.target_class_config_id:
            return None

        attr_name = f"{to_snake_case(owner_class.name)}_id"
        existing_link = next(
            (
                link
                for link in target_class.class_config_attribute_configs
                if link.attribute_config.name == attr_name
            ),
            None,
        )
        if existing_link is not None and existing_link.attribute_config.code_section_attribute is not None:
            raise ValueError(
                "no-guess propagation foreign key resolution failed: runtime association target propagation "
                + "requires a transformer-synthesized FK anchor, found authored attribute in source contract "
                + f"(relationship_id={relationship.id}, owner_class={owner_class.name!r}, "
                + f"target_class={target_class.name!r}, attribute={attr_name!r})."
            )

        if existing_link is None:
            parent_fk_attr = AttributeConfig(
                owner_key=self.support.attribute_owner_key(target_class),
                name=self.support.validate_unique(target_class, attr_name),
                description=f"Propagation FK to {owner_class.name}",
                is_public=False,
                is_required=bool(relationship.forward_required),
                is_unique=relationship.relationship_type == ClassConfigRelationshipType.one_to_one,
                is_virtual=False,
                type_descriptor=self.support.build_uuid_primitive_descriptor(None),
            )
            self.support.attach_attribute(target_class, parent_fk_attr)
            existing_link = next(
                (
                    link
                    for link in target_class.class_config_attribute_configs
                    if link.attribute_config.id == parent_fk_attr.id
                ),
                None,
            )
        else:
            parent_fk_attr = existing_link.attribute_config

        existing_rel_attr = next(
            (
                rel_attr
                for rel_attr in relationship.class_config_relationship_attributes
                if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
                and rel_attr.direction == ClassConfigRelationshipDirection.reverse
                and rel_attr.attribute_config_id == parent_fk_attr.id
            ),
            None,
        )
        if existing_rel_attr is None:
            existing_rel_attr = ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=relationship.id,
                    attribute_config_id=parent_fk_attr.id,
                    direction=ClassConfigRelationshipDirection.reverse.value,
                    role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                ),
                class_config_relationship_id=relationship.id,
                attribute_config_id=parent_fk_attr.id,
                attribute_config=parent_fk_attr,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            )
            relationship.class_config_relationship_attributes.append(existing_rel_attr)

        self._retire_reified_association_target_owner_fk(
            owner_class=owner_class,
            relationship=relationship,
            canonical_relationship=canonical_relationship,
            fk_attrs_by_relationship_and_owner_class=fk_attrs_by_relationship_and_owner_class,
        )

        key = (relationship.id, target_class.id)
        bucket = list(fk_attrs_by_relationship_and_owner_class.get(key, ()))
        if all(existing_attr.id != parent_fk_attr.id for (_, existing_attr) in bucket):
            bucket.append((existing_rel_attr, parent_fk_attr))
            fk_attrs_by_relationship_and_owner_class[key] = tuple(bucket)

        return parent_fk_attr

    def _retire_reified_association_target_owner_fk(
        self,
        *,
        owner_class: ClassConfig,
        relationship: ClassConfigRelationship,
        canonical_relationship: ClassConfigRelationship | None,
        fk_attrs_by_relationship_and_owner_class: FkOwnerIndex,
    ) -> None:
        if relationship.reified_role != ClassConfigRelationshipReifiedRole.association_to_target:
            return

        owner_key = (relationship.id, owner_class.id)
        owner_candidates = fk_attrs_by_relationship_and_owner_class.get(owner_key, ())
        if not owner_candidates:
            return

        stale_attr_ids: set[UUID] = set()
        for rel_attr, attr in owner_candidates:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            if rel_attr.direction != ClassConfigRelationshipDirection.forward:
                continue
            if attr.code_section_attribute is not None:
                raise ValueError(
                    "runtime association target propagation must retire only transformer-synthesized "
                    + "edge-owned target FKs, found authored attribute in source contract "
                    + f"(relationship_id={relationship.id}, owner_class={owner_class.name!r}, "
                    + f"attribute={attr.name!r})."
                )
            stale_attr_ids.add(attr.id)

        if not stale_attr_ids:
            return

        relationship.class_config_relationship_attributes = [
            rel_attr
            for rel_attr in relationship.class_config_relationship_attributes
            if not (
                rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
                and rel_attr.direction == ClassConfigRelationshipDirection.forward
                and rel_attr.attribute_config_id in stale_attr_ids
            )
        ]
        if canonical_relationship is not None:
            canonical_relationship.class_config_relationship_attributes = [
                rel_attr
                for rel_attr in canonical_relationship.class_config_relationship_attributes
                if not (
                    rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
                    and rel_attr.direction == ClassConfigRelationshipDirection.reverse
                    and rel_attr.attribute_config_id in stale_attr_ids
                )
            ]

        owner_class.class_config_attribute_configs = [
            link for link in owner_class.class_config_attribute_configs if link.attribute_config_id not in stale_attr_ids
        ]
        _ = fk_attrs_by_relationship_and_owner_class.pop(owner_key, None)
        if canonical_relationship is not None:
            _ = fk_attrs_by_relationship_and_owner_class.pop((canonical_relationship.id, owner_class.id), None)

    def _relationship_direction_for_owner(
        self,
        *,
        relationship: ClassConfigRelationship,
        owner_class: ClassConfig,
    ) -> ClassConfigRelationshipDirection | None:
        if owner_class.id == relationship.class_config_id:
            return ClassConfigRelationshipDirection.forward
        if owner_class.id == relationship.target_class_config_id:
            return ClassConfigRelationshipDirection.reverse
        return None

    def _index_foreign_keys_by_relationship_owner_class(
        self,
        *,
        class_configs: list[ClassConfig],
        relationships: list[ClassConfigRelationship],
    ) -> FkOwnerIndex:
        owner_class_by_attr_id: dict[UUID, ClassConfig] = {}
        attr_by_id: dict[UUID, AttributeConfig] = {}
        for cls in class_configs:
            for link in cls.class_config_attribute_configs:
                attr = link.attribute_config
                owner_class_by_attr_id[attr.id] = cls
                attr_by_id[attr.id] = attr

        index: dict[tuple[UUID, UUID], list[tuple[ClassConfigRelationshipAttribute, AttributeConfig]]] = {}
        for relationship in relationships:
            for rel_attr in relationship.class_config_relationship_attributes:
                if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                    continue
                owner_cls = owner_class_by_attr_id.get(rel_attr.attribute_config_id)
                attr = attr_by_id.get(rel_attr.attribute_config_id)
                if owner_cls is None or attr is None:
                    continue
                key = (relationship.id, owner_cls.id)
                bucket = index.setdefault(key, [])
                if all(existing_attr.id != attr.id for (_, existing_attr) in bucket):
                    bucket.append((rel_attr, attr))

        return {key: tuple(attrs) for key, attrs in index.items()}

    def _build_path_constructor_function(
        self,
        *,
        target_function: FunctionConfig,
        source_function: FunctionConfig | None,
        target_class: ClassConfig,
        target_owner_fqn: str,
        path_function_name: str,
        parent_fk_attribute: AttributeConfig,
    ) -> FunctionConfig:
        function_kind = target_function.kind.value
        source_code_section_function = (
            source_function.code_section_function if source_function is not None else target_function.code_section_function
        )
        source_code_section_function_id = (
            source_function.code_section_function_id
            if source_function is not None
            else target_function.code_section_function_id
        )
        path_function = FunctionConfig(
            id=stable_function_config_id(
                owner_key=target_owner_fqn,
                name=path_function_name,
                kind=function_kind,
            ),
            owner_key=target_owner_fqn,
            name=path_function_name,
            description=target_function.description,
            is_async=target_function.is_async,
            kind=target_function.kind,
            verb=target_function.verb,
            code_section_function_id=source_code_section_function_id,
            code_section_function=source_code_section_function,
        )

        source_edges = sorted(
            (edge for edge in target_function.function_config_attribute_configs),
            key=lambda edge: (
                edge.type.value,
                edge.position,
                edge.attribute_config.name,
            ),
        )
        source_inputs = [edge for edge in source_edges if edge.type == FunctionAttributeType.input]
        source_outputs = [edge for edge in source_edges if edge.type == FunctionAttributeType.output]

        parent_name = parent_fk_attribute.name
        input_position = 0
        parent_path_input = self._append_cloned_function_attribute(
            owner_fqn=target_owner_fqn,
            function_name=path_function_name,
            function_config=path_function,
            source_attribute=parent_fk_attribute,
            function_attribute_type=FunctionAttributeType.input,
            position=input_position,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        )
        parent_path_input.attribute_config.is_required = True
        parent_path_input.attribute_config.default_value = None
        input_position += 1

        for edge in source_inputs:
            attr = edge.attribute_config
            if attr.name == parent_name:
                continue
            edge_is_identity_key = bool(edge.is_identity_key) or bool(attr.is_primary)
            _ = self._append_cloned_function_attribute(
                owner_fqn=target_owner_fqn,
                function_name=path_function_name,
                function_config=path_function,
                source_attribute=attr,
                function_attribute_type=FunctionAttributeType.input,
                position=input_position,
                is_identity_key=edge_is_identity_key,
                identity_key_origin=self._resolve_identity_key_origin(
                    edge=edge,
                    is_identity_key=edge_is_identity_key,
                ),
            )
            input_position += 1

        output_position = 0
        for edge in source_outputs:
            attr = edge.attribute_config
            edge_is_identity_key = bool(edge.is_identity_key) or bool(attr.is_primary)
            _ = self._append_cloned_function_attribute(
                owner_fqn=target_owner_fqn,
                function_name=path_function_name,
                function_config=path_function,
                source_attribute=attr,
                function_attribute_type=FunctionAttributeType.output,
                position=output_position,
                is_identity_key=edge_is_identity_key,
                identity_key_origin=self._resolve_identity_key_origin(
                    edge=edge,
                    is_identity_key=edge_is_identity_key,
                ),
            )
            output_position += 1

        template_function = source_function or target_function
        function_impl = clone_function_impl_from_template(
            function_config=path_function,
            template_function=template_function,
            is_constructor=True,
        )
        if function_impl is None:
            function_impl = build_function_impl_from_body(
                function_config=path_function,
                owner_class_config=target_class,
                fail_on_unresolved=False,
                is_constructor=True,
            )
        if function_impl is not None:
            path_function.function_impl = function_impl
            capture_name_by_sequence = {
                invocation.position: invocation.capture_name for invocation in template_function.invocations
            }
            path_function.invocations = build_function_invocation_plan_from_impl(
                function_config=path_function,
                function_impl=function_impl,
                capture_name_by_sequence=capture_name_by_sequence,
            )

        return path_function

    def _resolve_identity_key_origin(
        self,
        *,
        edge: FunctionConfigAttributeConfig,
        is_identity_key: bool,
    ) -> FunctionIdentityKeyOrigin:
        if not is_identity_key:
            return FunctionIdentityKeyOrigin.standalone
        raw_origin = edge.identity_key_origin
        origin_value = raw_origin.value.strip().casefold()
        if origin_value in {"", FunctionIdentityKeyOrigin.standalone.value}:
            return FunctionIdentityKeyOrigin.standalone
        if origin_value == FunctionIdentityKeyOrigin.propagated_parent.value:
            return FunctionIdentityKeyOrigin.propagated_parent
        raise ValueError(
            "Unknown FunctionConfigAttributeConfig.identity_key_origin " + f"(edge_id={edge.id}, value={raw_origin!r})"
        )

    def _append_cloned_function_attribute(
        self,
        *,
        owner_fqn: str,
        function_name: str,
        function_config: FunctionConfig,
        source_attribute: AttributeConfig,
        function_attribute_type: FunctionAttributeType,
        position: int,
        is_identity_key: bool,
        identity_key_origin: FunctionIdentityKeyOrigin,
    ) -> FunctionConfigAttributeConfig:
        io_owner_fqn = f"{owner_fqn}.{function_name}::{function_attribute_type.value}"
        attr_clone = clone_attribute_config_for_runtime_function(source_attribute=source_attribute)
        attr_clone.owner_key = io_owner_fqn
        attr_clone.id = stable_attribute_config_id(
            owner_key=io_owner_fqn,
            name=attr_clone.name,
        )
        attr_clone.is_primary = bool(is_identity_key)
        attr_clone.type_descriptor = ensure_stable_descriptor_tree_ids(attr_clone.type_descriptor)
        attr_clone.type_descriptor_id = attr_clone.type_descriptor.id

        link = FunctionConfigAttributeConfig(
            id=stable_function_config_attribute_config_id(
                function_config_id=function_config.id,
                name=attr_clone.name,
                type=function_attribute_type.value,
            ),
            function_config_id=function_config.id,
            attribute_config=attr_clone,
            attribute_config_id=attr_clone.id,
            name=attr_clone.name,
            position=position,
            type=function_attribute_type,
            is_identity_key=is_identity_key,
            identity_key_origin=identity_key_origin,
        )
        function_config.function_config_attribute_configs.append(link)
        return link

    def _retarget_invocation_to_function(
        self,
        *,
        invocation: FunctionConfigInvocation,
        target_function: FunctionConfig,
    ) -> None:
        invocation.target_function_config_id = target_function.id
        invocation.target_function_config = target_function

        invocation_kind = invocation.kind.value.strip().lower()
        relationship_fingerprint = (
            str(invocation.class_config_relationship_id)
            if invocation.class_config_relationship_id is not None
            else "owner"
        )
        invocation.id = stable_function_config_invocation_id(
            function_config_id=invocation.function_config_id,
            position=invocation.position,
            kind=invocation_kind,
            target_function_config_id=target_function.id,
            relationship_fingerprint=relationship_fingerprint,
        )

    def _retarget_function_impl_invokes(
        self,
        *,
        owner_function: FunctionConfig,
        original_target_function: FunctionConfig,
        original_target_function_id: UUID,
        relationship_id: UUID | None,
        target_function: FunctionConfig,
    ) -> None:
        function_impl = owner_function.function_impl
        if function_impl is None:
            return
        for instruction in function_impl.instructions:
            payload = instruction.instruction_invoke
            if payload is None:
                continue
            payload_kind = payload.kind.value.strip().lower()
            if payload_kind != FunctionInvocationKind.construct.value:
                continue
            if payload.class_config_relationship_id != relationship_id:
                continue
            if payload.target_function_config_id != original_target_function_id:
                continue
            payload.target_function_config_id = target_function.id
            payload.target_function_config = target_function
            self._retarget_function_impl_invoke_attribute_configs(
                invoke_payload=payload,
                original_target_function=original_target_function,
                target_function=target_function,
            )

    def _retarget_function_impl_invoke_attribute_configs(
        self,
        *,
        invoke_payload: FunctionImplInstructionInvoke,
        original_target_function: FunctionConfig,
        target_function: FunctionConfig,
    ) -> None:
        """Remap invoke bindings when construct invokes retarget to path constructors."""

        original_input_name_by_attr_id: dict[UUID, str] = {}
        for edge in original_target_function.function_config_attribute_configs:
            if edge.type != FunctionAttributeType.input:
                continue
            original_input_name_by_attr_id[edge.attribute_config.id] = edge.attribute_config.name

        target_input_by_name: dict[str, FunctionConfigAttributeConfig] = {}
        for edge in target_function.function_config_attribute_configs:
            if edge.type != FunctionAttributeType.input:
                continue
            target_input_by_name[edge.attribute_config.name] = edge

        remapped_bindings: list[FunctionImplInstructionInvokeAttributeConfig] = []
        assigned_attribute_config_ids: set[UUID] = set()
        for binding in invoke_payload.attribute_configs:
            binding_attr = binding.attribute_config
            input_name = binding_attr.name if binding_attr is not None else None
            if not input_name:
                input_name = original_input_name_by_attr_id.get(binding.attribute_config_id)
            if not input_name and isinstance(binding.value_expr, dict):
                value_kind = str(binding.value_expr.get("kind", "")).strip().lower()
                value_name = str(binding.value_expr.get("name", "")).strip()
                if value_kind == "reference" and value_name in target_input_by_name:
                    input_name = value_name
            if not input_name:
                continue
            target_edge = target_input_by_name.get(input_name)
            if target_edge is None:
                continue
            target_attr_id = target_edge.attribute_config_id
            target_attr = target_edge.attribute_config
            if target_attr_id is None or target_attr is None:
                raise ValueError(
                    "path-constructor FunctionImpl retarget found target input without AttributeConfig "
                    + f"(invoke_id={invoke_payload.id}, input={input_name!r})"
                )
            if target_attr_id in assigned_attribute_config_ids:
                raise ValueError(
                    "duplicate FunctionImpl invoke binding after path-constructor retarget "
                    + f"(invoke_id={invoke_payload.id}, input={input_name!r}, "
                    + f"attribute_config_id={target_attr_id})"
                )
            binding.id = stable_function_impl_instruction_invoke_attribute_config_id(
                function_impl_instruction_invoke_id=invoke_payload.id,
                attribute_config_id=target_attr_id,
            )
            binding.function_impl_instruction_invoke_id = invoke_payload.id
            binding.attribute_config_id = target_attr_id
            binding.attribute_config = target_attr
            binding.position = target_edge.position
            remapped_bindings.append(binding)
            assigned_attribute_config_ids.add(target_attr_id)

        for edge in target_function.function_config_attribute_configs:
            if edge.type != FunctionAttributeType.input:
                continue
            edge_attr_id = edge.attribute_config_id
            edge_attr = edge.attribute_config
            if edge_attr_id is None or edge_attr is None:
                raise ValueError(
                    "path-constructor FunctionImpl retarget found target input without AttributeConfig "
                    + f"(invoke_id={invoke_payload.id}, function={target_function.name!r})"
                )
            if edge_attr_id in assigned_attribute_config_ids:
                continue
            if edge.identity_key_origin != FunctionIdentityKeyOrigin.propagated_parent:
                continue
            binding_id = stable_function_impl_instruction_invoke_attribute_config_id(
                function_impl_instruction_invoke_id=invoke_payload.id,
                attribute_config_id=edge_attr_id,
            )
            value_expr = JsonObject({"kind": "self_id"})
            remapped_bindings.append(
                FunctionImplInstructionInvokeAttributeConfig(
                    id=binding_id,
                    function_impl_instruction_invoke_id=invoke_payload.id,
                    attribute_config_id=edge_attr_id,
                    attribute_config=edge_attr,
                    value_expr=value_expr,
                    position=edge.position,
                )
            )
            assigned_attribute_config_ids.add(edge_attr_id)

        remapped_bindings.sort(
            key=lambda binding: (
                binding.position if binding.position is not None else 1_000_000,
                str(binding.id),
            )
        )
        invoke_payload.attribute_configs = remapped_bindings


__all__ = ["RuntimeFunctionSurfaceSupport"]
