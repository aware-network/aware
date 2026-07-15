from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeVar, cast
from uuid import UUID

from pydantic import TypeAdapter

from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_value_decoder import decode_oig_attribute_value
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.class_resolver import (
    ORMClassResolutionIndex,
    resolve_orm_class,
)
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks
from aware_orm.session.session import Session

TModel = TypeVar("TModel", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class _RelationshipBinding:
    field_name: str
    is_collection: bool
    source_class_config_id: UUID


def reify_oig_root_model(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    oig: ObjectInstanceGraph,
    model_type: type[TModel],
    root_id: UUID,
    branch_id: UUID | None = None,
) -> TModel | None:
    """Rebuild an ORM object graph from committed Meta OIG evidence.

    This is a Meta-owned read model reifier for service/package dependency reads.
    It intentionally avoids the legacy runtime function-call executor.
    """

    reifier = _OigModelReifier(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
        preferred_model_types_by_class_config_id=(
            _preferred_model_types_by_class_config_id(
                index=index,
                model_type=model_type,
            )
        ),
    )
    return reifier.reify_root(model_type=model_type, root_id=root_id)


def reify_oig_target_model(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    oig: ObjectInstanceGraph,
    model_type: type[TModel],
    target_class_instance_id: UUID,
    branch_id: UUID | None = None,
) -> TModel | None:
    """Rebuild an ORM model for a committed Meta graph invocation target."""

    reifier = _OigModelReifier(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
        preferred_model_types_by_class_config_id=(
            _preferred_model_types_by_class_config_id(
                index=index,
                model_type=model_type,
            )
        ),
    )
    return reifier.reify_class_instance(
        model_type=model_type,
        class_instance_id=target_class_instance_id,
    )


def reify_oig_session(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    oig: ObjectInstanceGraph,
    branch_id: UUID | None = None,
) -> Session:
    """Rebuild committed OIG participants into a scratch ORM session."""

    session = Session(branch_id=branch_id, skip_db=True)
    reifier = _OigModelReifier(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    with disable_autobind(), disable_change_tracking_hooks():
        instances_by_class_instance_id = reifier._construct_instances()
        reifier._populate_relationships(instances_by_class_instance_id)
    reifier._wrap_reified_list_fields(instances_by_class_instance_id)
    for instance in instances_by_class_instance_id.values():
        session.imap_add(instance)
    return session


def bind_oig_models_to_current_handler_session(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    oig: ObjectInstanceGraph,
    branch_id: UUID | None = None,
) -> int:
    """Hydrate committed OIG participants into the active handler session."""

    reifier = _OigModelReifier(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    with disable_autobind(), disable_change_tracking_hooks():
        instances_by_class_instance_id = reifier._construct_instances()
        reifier._populate_relationships(instances_by_class_instance_id)
    reifier._wrap_reified_list_fields(instances_by_class_instance_id)
    _bind_current_handler_session(instances_by_class_instance_id)
    return len(instances_by_class_instance_id)


def _preferred_model_types_by_class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    model_type: type[TModel],
) -> Mapping[UUID, type[ORMModel]]:
    """Prefer the caller's explicit model type for matching graph classes."""

    preferred_model_type = _semantic_runtime_model_type_for_model_type(model_type)
    if preferred_model_type is None:
        preferred_model_type = model_type

    preferred: dict[UUID, type[ORMModel]] = {}
    class_config = preferred_model_type.get_class_config()
    class_config_id = getattr(class_config, "id", None)
    if (
        isinstance(class_config_id, UUID)
        and class_config_id in index.class_configs_by_id
    ):
        preferred[class_config_id] = preferred_model_type

    candidate_fqns = _candidate_model_type_class_fqns(preferred_model_type)
    for (
        candidate_class_config_id,
        candidate_class_config,
    ) in index.class_configs_by_id.items():
        class_fqn = getattr(candidate_class_config, "class_fqn", None)
        if isinstance(class_fqn, str) and class_fqn in candidate_fqns:
            preferred[candidate_class_config_id] = preferred_model_type

    semantic_prefix = _semantic_package_prefix_for_model_type(preferred_model_type)
    if semantic_prefix is None:
        return preferred
    for (
        candidate_class_config_id,
        candidate_class_config,
    ) in index.class_configs_by_id.items():
        if candidate_class_config_id in preferred:
            continue
        class_fqn = getattr(candidate_class_config, "class_fqn", None)
        if not isinstance(class_fqn, str):
            continue
        if not class_fqn.startswith(f"{semantic_prefix}."):
            continue
        runtime_fqn = _runtime_model_fqn_for_semantic_class_fqn(
            semantic_class_fqn=class_fqn,
            semantic_prefix=semantic_prefix,
        )
        runtime_class = ORMModelRegistry.get_class_by_fqn(runtime_fqn)
        if isinstance(runtime_class, type) and issubclass(runtime_class, ORMModel):
            preferred[candidate_class_config_id] = runtime_class
    return preferred


def _candidate_model_type_class_fqns(model_type: type[ORMModel]) -> tuple[str, ...]:
    module_name = model_type.__module__
    class_name = model_type.__name__
    fqns = [f"{module_name}.{class_name}"]

    for marker in ("_ontology_orm_models.", "_ontology."):
        prefix, found, tail = module_name.partition(marker)
        if not found or not prefix.startswith("aware_"):
            continue
        tokens = [token.removesuffix("_") for token in tail.split(".") if token]
        class_module_token = _camel_to_snake(class_name)
        if tokens and tokens[-1] == class_module_token:
            tokens = tokens[:-1]
        fqns.append(".".join((prefix, *tokens, class_name)))

    return tuple(dict.fromkeys(fqns))


def _semantic_runtime_model_type_for_model_type(
    model_type: type[ORMModel],
) -> type[ORMModel] | None:
    module_name = model_type.__module__
    prefix, found, tail = module_name.partition("_ontology_orm_models.")
    if not found or not prefix.startswith("aware_"):
        return None
    runtime_fqn = ".".join((f"{prefix}_ontology", tail, model_type.__name__))
    runtime_class = ORMModelRegistry.get_class_by_fqn(runtime_fqn)
    if isinstance(runtime_class, type) and issubclass(runtime_class, ORMModel):
        return runtime_class
    return None


def _semantic_package_prefix_for_model_type(
    model_type: type[ORMModel],
) -> str | None:
    module_name = model_type.__module__
    for marker in ("_ontology_orm_models.", "_ontology."):
        prefix, found, _tail = module_name.partition(marker)
        if found and prefix.startswith("aware_"):
            return prefix
    return None


def _runtime_model_fqn_for_semantic_class_fqn(
    *,
    semantic_class_fqn: str,
    semantic_prefix: str,
) -> str:
    tail = semantic_class_fqn.removeprefix(f"{semantic_prefix}.")
    tokens = [token for token in tail.split(".") if token]
    class_name = tokens[-1]
    module_tokens = tokens[:-1]
    class_module_token = _camel_to_snake(class_name)
    return ".".join(
        (
            f"{semantic_prefix}_ontology",
            *module_tokens,
            class_module_token,
            class_name,
        )
    )


def _camel_to_snake(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if index > 0 and char.isupper():
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


@dataclass(slots=True)
class _OigModelReifier:
    index: MetaGraphRuntimeIndex
    opg: ObjectProjectionGraph
    oig: ObjectInstanceGraph
    branch_id: UUID | None = None
    preferred_model_types_by_class_config_id: Mapping[UUID, type[ORMModel]] = field(
        default_factory=dict
    )

    def reify_root(
        self,
        *,
        model_type: type[TModel],
        root_id: UUID,
    ) -> TModel | None:
        with disable_autobind(), disable_change_tracking_hooks():
            instances_by_class_instance_id = self._construct_instances()
            self._populate_relationships(instances_by_class_instance_id)
        self._wrap_reified_list_fields(instances_by_class_instance_id)
        _bind_current_handler_session(instances_by_class_instance_id)

        for instance in instances_by_class_instance_id.values():
            if instance.id == root_id and _model_instance_matches_type(
                instance=instance,
                model_type=model_type,
            ):
                return cast(TModel, instance)
        return None

    def reify_class_instance(
        self,
        *,
        model_type: type[TModel],
        class_instance_id: UUID,
    ) -> TModel | None:
        with disable_autobind(), disable_change_tracking_hooks():
            instances_by_class_instance_id = self._construct_instances()
            self._populate_relationships(instances_by_class_instance_id)
        self._wrap_reified_list_fields(instances_by_class_instance_id)
        _bind_current_handler_session(instances_by_class_instance_id)

        instance = instances_by_class_instance_id.get(class_instance_id)
        if instance is not None and _model_instance_matches_type(
            instance=instance,
            model_type=model_type,
        ):
            return cast(TModel, instance)
        return None

    def _construct_instances(self) -> dict[UUID, ORMModel]:
        derived_fk_values = self._derived_fk_values_by_instance_id()
        instances_by_class_instance_id: dict[UUID, ORMModel] = {}
        class_resolution_index = ORMClassResolutionIndex.from_class_configs_by_id(
            self.index.class_configs_by_id,
        )

        for class_instance in tuple(self.oig.class_instances or ()):
            preferred_orm_class = self.preferred_model_types_by_class_config_id.get(
                class_instance.class_config_id
            )
            resolved_orm_class = resolve_orm_class(
                class_config_id=class_instance.class_config_id,
                class_resolution_index=class_resolution_index,
            )
            if preferred_orm_class is not None and (
                resolved_orm_class is None
                or not _model_class_matches_type(
                    model_class=resolved_orm_class,
                    model_type=preferred_orm_class,
                )
            ):
                orm_class = preferred_orm_class
            else:
                orm_class = resolved_orm_class
            if orm_class is None:
                raise ValueError(
                    "Meta OIG reifier requires ORM bindings for all projection "
                    "members: "
                    f"class_config_id={class_instance.class_config_id} "
                    f"class_instance_id={class_instance.id}"
                )

            source_object_id = _uuid_value(class_instance.source_object_id)
            if source_object_id is None:
                raise ValueError(
                    "Meta OIG reifier requires class instance source_object_id: "
                    f"class_instance_id={class_instance.id}"
                )
            model_data: dict[str, object] = {"id": source_object_id}
            for attribute in tuple(class_instance.attributes or ()):
                attr_cfg = self.index.attribute_configs_by_id.get(
                    attribute.attribute_config_id
                )
                if attr_cfg is None:
                    # Old committed OIGs can carry scalar attributes removed from
                    # the active schema. The current ORM model has no safe field
                    # to bind, so treat the stale attribute as historical payload.
                    continue

                field_name = _orm_field_name_for_config_name(
                    orm_class,
                    attr_cfg.name,
                )
                fields = _model_fields(orm_class)
                if field_name not in fields:
                    continue

                value_root = _value_with_schema_type_descriptors(
                    value=attribute.value_root,
                    expected_descriptor=attr_cfg.type_descriptor,
                )
                if (
                    value_root.type_descriptor.kind
                    == AttributeTypeDescriptorKind.class_
                ):
                    class_config = _resolve_class_value_config(
                        type_descriptor=value_root.type_descriptor,
                        class_configs_by_id=self.index.class_configs_by_id,
                    )
                    if class_config.value_mode != ClassValueMode.inline_value:
                        continue

                decoded_value = decode_oig_attribute_value(
                    value_root,
                    class_configs_by_id=self.index.class_configs_by_id,
                )
                model_data[field_name] = _coerce_field_value(
                    orm_class=orm_class,
                    field_name=field_name,
                    value=decoded_value,
                )

            for fk_field_name, fk_value in derived_fk_values.get(
                class_instance.id,
                {},
            ).items():
                field_name = _orm_field_name_for_config_name(orm_class, fk_field_name)
                if field_name in _model_fields(orm_class):
                    model_data.setdefault(field_name, fk_value)

            orm_model = orm_class.model_construct(
                _fields_set=set(model_data.keys()),
                **model_data,
            )
            orm_model.mark_persisted()
            if self.branch_id is not None:
                orm_model._branch_id = self.branch_id
            orm_model.bind_graph_invocation_target_id(class_instance.id)
            instances_by_class_instance_id[class_instance.id] = orm_model

        return instances_by_class_instance_id

    def _populate_relationships(
        self,
        instances_by_class_instance_id: Mapping[UUID, ORMModel],
    ) -> None:
        rel_bindings = self._relationship_bindings()
        self._reset_relationship_fields(
            rel_bindings=rel_bindings,
            instances_by_class_instance_id=instances_by_class_instance_id,
        )

        for rel_edge in tuple(self.oig.class_instance_relationships or ()):
            binding = rel_bindings.get(rel_edge.class_config_relationship_id)
            if binding is None:
                raise ValueError(
                    "OIG relationship edge is not included in current projection: "
                    f"relationship_id={rel_edge.class_config_relationship_id} "
                    f"object_projection_graph_id={self.opg.id}"
                )

            source = instances_by_class_instance_id.get(
                rel_edge.source_class_instance_id
            )
            target = instances_by_class_instance_id.get(
                rel_edge.target_class_instance_id
            )
            if source is None or target is None:
                # Projection slices can carry relationship edges whose opposite
                # endpoint is not a projected ORM object. FK scalar fields are
                # derived before object relationship binding, so there is no
                # object reference to populate here.
                continue

            field_name = _orm_field_name_for_config_name(
                type(source),
                binding.field_name,
            )
            if field_name not in _model_fields(type(source)):
                continue

            if binding.is_collection:
                current = source.__dict__.get(field_name)
                if not isinstance(current, list):
                    raise TypeError(
                        "Meta OIG reifier expected list relationship field: "
                        f"class={type(source).__module__}.{type(source).__name__} "
                        f"instance_id={source.id} field={field_name} "
                        f"value_type={type(current).__name__}"
                    )
                if not _contains_orm_model(current, target):
                    current.append(target)
            else:
                setattr(source, field_name, target)

    def _relationship_bindings(self) -> dict[UUID, _RelationshipBinding]:
        bindings: dict[UUID, _RelationshipBinding] = {}
        for edge in tuple(self.opg.object_projection_graph_edges or ()):
            rel_id = edge.class_config_relationship_id
            if rel_id in bindings:
                continue
            bindings[rel_id] = self._reference_attr_name_for_relationship(rel_id)
        return bindings

    def _reference_attr_name_for_relationship(
        self,
        rel_id: UUID,
    ) -> _RelationshipBinding:
        rel = self.index.relationships_by_id.get(rel_id)
        if rel is None:
            raise ValueError(f"ClassConfigRelationship not found in OCG: {rel_id}")

        ref_attr_id: UUID | None = None
        for rel_attr in tuple(rel.class_config_relationship_attributes or ()):
            if rel_attr.direction != ClassConfigRelationshipDirection.forward:
                continue
            if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                continue
            ref_attr_id = rel_attr.attribute_config_id
            break
        if ref_attr_id is None:
            raise ValueError(
                "Relationship missing FORWARD REFERENCE attribute: " f"{rel_id}"
            )

        attr_cfg = self.index.attribute_configs_by_id.get(ref_attr_id)
        if attr_cfg is None:
            raise ValueError(
                "AttributeConfig not found for relationship reference: "
                f"rel_id={rel_id} attr_id={ref_attr_id}"
            )

        type_desc = attr_cfg.type_descriptor
        is_collection = (
            type_desc.kind == AttributeTypeDescriptorKind.collection
            and type_desc.collection_kind
            in {AttributeCollectionType.list, AttributeCollectionType.set}
        )
        return _RelationshipBinding(
            field_name=attr_cfg.name,
            is_collection=is_collection,
            source_class_config_id=rel.class_config_id,
        )

    def _reset_relationship_fields(
        self,
        *,
        rel_bindings: Mapping[UUID, _RelationshipBinding],
        instances_by_class_instance_id: Mapping[UUID, ORMModel],
    ) -> None:
        for binding in rel_bindings.values():
            for class_instance in tuple(self.oig.class_instances or ()):
                if class_instance.class_config_id != binding.source_class_config_id:
                    continue
                orm_model = instances_by_class_instance_id.get(class_instance.id)
                if orm_model is None:
                    raise ValueError(
                        "Meta OIG reifier failed to resolve source instance: "
                        f"class_config_id={binding.source_class_config_id} "
                        f"class_instance_id={class_instance.id}"
                    )
                field_name = _orm_field_name_for_config_name(
                    type(orm_model),
                    binding.field_name,
                )
                if field_name not in _model_fields(type(orm_model)):
                    continue
                setattr(orm_model, field_name, [] if binding.is_collection else None)

    def _derived_fk_values_by_instance_id(self) -> dict[UUID, dict[str, UUID]]:
        values_by_instance: dict[UUID, dict[str, UUID]] = {}
        source_object_id_by_instance_id = {
            class_instance.id: _uuid_value(class_instance.source_object_id)
            for class_instance in tuple(self.oig.class_instances or ())
        }
        fk_attribute_config_ids = {
            rel_attr.attribute_config_id
            for rel_edge in tuple(self.oig.class_instance_relationships or ())
            for rel in (
                self.index.relationships_by_id.get(
                    rel_edge.class_config_relationship_id
                ),
            )
            if rel is not None
            for rel_attr in tuple(rel.class_config_relationship_attributes or ())
            if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
        }
        attribute_uuid_values_by_instance_id: dict[UUID, dict[UUID, UUID]] = {}
        for class_instance in tuple(self.oig.class_instances or ()):
            for attribute in tuple(class_instance.attributes or ()):
                if attribute.attribute_config_id not in fk_attribute_config_ids:
                    continue
                uuid_value = _fk_attribute_uuid_value(attribute.value_root)
                if uuid_value is None:
                    continue
                attribute_uuid_values_by_instance_id.setdefault(class_instance.id, {})[
                    attribute.attribute_config_id
                ] = uuid_value

        for rel_edge in tuple(self.oig.class_instance_relationships or ()):
            rel = self.index.relationships_by_id.get(
                rel_edge.class_config_relationship_id
            )
            if rel is None:
                continue
            for rel_attr in tuple(rel.class_config_relationship_attributes or ()):
                if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                    continue
                attr_cfg = self.index.attribute_configs_by_id.get(
                    rel_attr.attribute_config_id
                )
                if attr_cfg is None or not attr_cfg.name:
                    continue
                if rel_attr.direction == ClassConfigRelationshipDirection.forward:
                    owner_instance_id = rel_edge.source_class_instance_id
                    fk_value = source_object_id_by_instance_id.get(
                        rel_edge.target_class_instance_id,
                    )
                else:
                    owner_instance_id = rel_edge.target_class_instance_id
                    fk_value = source_object_id_by_instance_id.get(
                        rel_edge.source_class_instance_id,
                    )
                if fk_value is None:
                    fk_value = attribute_uuid_values_by_instance_id.get(
                        owner_instance_id,
                        {},
                    ).get(rel_attr.attribute_config_id)
                if fk_value is None:
                    raise ValueError(
                        "Meta OIG reifier could not derive relationship foreign "
                        "key from source object id: "
                        f"relationship_id={rel_edge.class_config_relationship_id} "
                        f"direction={rel_attr.direction}"
                    )
                values_by_instance.setdefault(owner_instance_id, {})[
                    attr_cfg.name
                ] = fk_value
        return values_by_instance

    @staticmethod
    def _wrap_reified_list_fields(
        instances_by_class_instance_id: Mapping[UUID, ORMModel],
    ) -> None:
        for instance in instances_by_class_instance_id.values():
            wrap_list_fields = getattr(
                instance,
                "_wrap_list_fields_for_change_collection",
                None,
            )
            if callable(wrap_list_fields):
                wrap_list_fields()


def _resolve_class_value_config(
    *,
    type_descriptor: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig],
) -> ClassConfig:
    class_config = type_descriptor.class_config
    if class_config is None and type_descriptor.class_config_id is not None:
        class_config = class_configs_by_id.get(type_descriptor.class_config_id)
    if class_config is None:
        raise ValueError(
            "CLASS AttributeTypeDescriptor missing class_config during Meta OIG "
            "reification: "
            f"type_descriptor_id={type_descriptor.id} "
            f"class_config_id={type_descriptor.class_config_id}"
        )
    return class_config


def _model_fields(orm_class: type[object]) -> Mapping[str, Any]:
    fields = getattr(orm_class, "model_fields", {})
    if isinstance(fields, Mapping):
        return fields
    return {}


def _orm_field_name_for_config_name(orm_class: type[object], name: str) -> str:
    fields = _model_fields(orm_class)
    if name in fields:
        return name
    for field_name, field_info in fields.items():
        if getattr(field_info, "alias", None) == name:
            return str(field_name)
    return name


def _coerce_field_value(
    *,
    orm_class: type[object],
    field_name: str,
    value: object,
) -> object:
    field_info = _model_fields(orm_class).get(field_name)
    field_type = getattr(field_info, "annotation", None)
    if field_type is None:
        return value
    try:
        return cast(object, TypeAdapter(field_type).validate_python(value))
    except Exception:
        return value


def _value_with_schema_type_descriptors(
    *,
    value: Any,
    expected_descriptor: Any,
) -> Any:
    value_descriptor = getattr(value, "type_descriptor", None)
    if value_descriptor is None or expected_descriptor is None:
        return value
    if getattr(value_descriptor, "id", None) != getattr(
        expected_descriptor, "id", None
    ):
        return value
    if value_descriptor is not expected_descriptor:
        value.type_descriptor = expected_descriptor
    for link in tuple(getattr(value, "child_links", ()) or ()):
        child_value = getattr(link, "child", None)
        child_descriptor = _expected_child_type_descriptor(
            parent_descriptor=expected_descriptor,
            value_link=link,
        )
        if child_value is None or child_descriptor is None:
            continue
        _value_with_schema_type_descriptors(
            value=child_value,
            expected_descriptor=child_descriptor,
        )
    return value


def _expected_child_type_descriptor(
    *,
    parent_descriptor: Any,
    value_link: Any,
) -> Any | None:
    parent_kind = getattr(parent_descriptor, "kind", None)
    role = getattr(value_link, "role", None)
    if parent_kind in {
        AttributeTypeDescriptorKind.collection,
        AttributeTypeDescriptorKind.mapping,
    }:
        for child_link in tuple(getattr(parent_descriptor, "child_links", ()) or ()):
            if getattr(child_link, "role", None) == role:
                return getattr(child_link, "child", None)
        return None

    if parent_kind in {
        AttributeTypeDescriptorKind.tuple,
        AttributeTypeDescriptorKind.union,
    }:
        position = getattr(value_link, "position", None)
        for child_link in tuple(getattr(parent_descriptor, "child_links", ()) or ()):
            if getattr(child_link, "role", None) != role:
                continue
            if role == AttributeTypeDescriptorRole.member and (
                getattr(child_link, "position", None) != position
            ):
                continue
            return getattr(child_link, "child", None)
        return None

    return None


def _uuid_value(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _fk_attribute_uuid_value(value: object) -> UUID | None:
    if value is None:
        return None
    primitive_value = getattr(value, "primitive_value", None)
    uuid_value = _uuid_value(_unwrap_json_envelope(primitive_value))
    if uuid_value is not None:
        return uuid_value
    return _uuid_value(getattr(value, "class_instance_id", None))


def _unwrap_json_envelope(value: object) -> object:
    if isinstance(value, Mapping):
        if set(value.keys()) == {"value"}:
            return value.get("value")
        return value
    return value


def _bind_current_handler_session(
    instances_by_class_instance_id: Mapping[UUID, ORMModel],
) -> None:
    try:
        from aware_meta.runtime.handler_executor.execution_context import (  # noqa: WPS433
            current_meta_graph_handler_execution_context_or_none,
        )
    except Exception:
        return

    context = current_meta_graph_handler_execution_context_or_none()
    if context is None:
        return
    for instance in instances_by_class_instance_id.values():
        context.session.imap_add(instance)


def _contains_orm_model(values: list[object], target: ORMModel) -> bool:
    return any(isinstance(item, ORMModel) and item.id == target.id for item in values)


def _model_instance_matches_type(
    *,
    instance: ORMModel,
    model_type: type[ORMModel],
) -> bool:
    if isinstance(instance, model_type):
        return True
    instance_class_config = type(instance).get_class_config()
    model_class_config = model_type.get_class_config()
    if getattr(instance_class_config, "id", None) is not None and getattr(
        instance_class_config, "id", None
    ) == getattr(model_class_config, "id", None):
        return True
    instance_type = type(instance)
    return (
        instance_type.__module__ == model_type.__module__
        and instance_type.__name__ == model_type.__name__
    )


def _model_class_matches_type(
    *,
    model_class: type[ORMModel],
    model_type: type[ORMModel],
) -> bool:
    if model_class is model_type:
        return True
    return (
        model_class.__module__ == model_type.__module__
        and model_class.__name__ == model_type.__name__
    )


__all__ = [
    "bind_oig_models_to_current_handler_session",
    "reify_oig_root_model",
    "reify_oig_session",
    "reify_oig_target_model",
]
