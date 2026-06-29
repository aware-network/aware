from dataclasses import dataclass
import json
import time
from typing import Iterable
from uuid import UUID

# Aware Kernel Graph Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Aware Kernel Meta
from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.attribute.instance.value.builder import (
    ClassInstanceResolver,
    EnumOptionResolver,
    UnionSelection,
)
from aware_meta.class_.instance.handlers import link_attribute
from aware_meta.graph.config.stable_ids import stable_class_instance_id

# Aware ORM
from aware_orm.models.introspection import ModelIntrospection
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks


class ClassInstanceBuildError(ValueError):
    pass


@dataclass(slots=True)
class ClassInstanceBuildProfile:
    plan_attributes_s: float = 0.0
    materialize_attributes_s: float = 0.0
    attr_links_total: int = 0
    duplicate_attribute_links_skipped: int = 0
    relationship_attribute_ids_total: int = 0
    required_fk_attribute_ids_total: int = 0
    attributes_built: int = 0
    virtual_attributes_skipped: int = 0
    relationship_attributes_skipped: int = 0
    optional_attributes_omitted: int = 0
    default_values_used: int = 0


def build_class_instance(
    *,
    object_instance_graph_id: UUID,
    class_config: ClassConfig,
    class_configs_by_id: dict[UUID, ClassConfig] | None = None,
    source: ModelIntrospection,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
    relationship_attribute_config_ids: Iterable[UUID] | None = None,
    include_relationship_attribute_config_ids: Iterable[UUID] | None = None,
    build_profile: ClassInstanceBuildProfile | None = None,
) -> ClassInstance:
    """
    Build a canonical ClassInstance from a ClassConfig and a source payload.

    This builder is intentionally scoped to "data attributes" only:
    - Attributes are built via descriptor-driven AttributeValue trees (`Attribute.value_root`).
    - Relationships are *not* built here; they will be modeled separately as ClassInstanceRelationship.
    """
    if not isinstance(source, ModelIntrospection):
        raise ClassInstanceBuildError(
            f"Invalid source type {type(source)!r}: expected a ModelIntrospection implementation "
            f"(e.g., BaseORMModel or MappingModelSource)."
        )

    with disable_change_tracking_hooks():
        # Canonical ClassInstances are pure in-memory artifacts; avoid implicit
        # session binding side effects.
        with disable_autobind():
            class_instance = ClassInstance(
                id=stable_class_instance_id(
                    object_instance_graph_id=object_instance_graph_id,
                    class_config_id=class_config.id,
                    source_object_id=source.id,
                ),
                object_instance_graph_id=object_instance_graph_id,
                class_config_id=class_config.id,
                source_object_id=source.id,
                class_config=class_config,
            )

    # Deterministic attribute order: by ClassConfigAttributeConfig.position then name.
    plan_started_at = time.perf_counter() if build_profile is not None else 0.0
    relationship_attribute_ids = _relationship_attribute_config_ids(class_config)
    required_fk_attribute_ids = _required_fk_attribute_config_ids(class_config)
    if relationship_attribute_config_ids is not None:
        relationship_attribute_ids |= set(relationship_attribute_config_ids)
    if include_relationship_attribute_config_ids is not None:
        # Portals (cross-OPG relationships) can require keeping select relationship-bound
        # attributes (e.g. `<ref>_id`) in the OIG snapshot so lane routing can be
        # derived deterministically from the commit rail.
        relationship_attribute_ids -= set(include_relationship_attribute_config_ids)
    raw_attr_links = sorted(
        class_config.class_config_attribute_configs,
        key=lambda link: (
            link.position,
            link.attribute_config.name if link.attribute_config else "",
        ),
    )
    attr_links = _dedupe_attribute_links(raw_attr_links)
    if build_profile is not None:
        build_profile.plan_attributes_s += time.perf_counter() - plan_started_at
        build_profile.relationship_attribute_ids_total += len(
            relationship_attribute_ids
        )
        build_profile.required_fk_attribute_ids_total += len(required_fk_attribute_ids)
        build_profile.attr_links_total += len(raw_attr_links)
        build_profile.duplicate_attribute_links_skipped += len(raw_attr_links) - len(
            attr_links
        )

    materialize_started_at = time.perf_counter() if build_profile is not None else 0.0
    with disable_change_tracking_hooks():
        for link in attr_links:
            attr_cfg = link.attribute_config
            if attr_cfg is None:
                continue
            if attr_cfg.is_virtual:
                # Virtual attributes are derived/projection-only (e.g. association-edge views like
                # `Repository.contents`) and must not be serialized into ClassInstance.attributes.
                if build_profile is not None:
                    build_profile.virtual_attributes_skipped += 1
                continue
            if attr_cfg.id in relationship_attribute_ids:
                # Relationship attributes are modeled separately as ClassInstanceRelationship.
                if build_profile is not None:
                    build_profile.relationship_attributes_skipped += 1
                continue

            found, raw_value = source.try_attribute_value(attr_cfg)

            if not found:
                if attr_cfg.default_value is not None:
                    raw_value = _parse_default_value(attr_cfg)
                    if build_profile is not None:
                        build_profile.default_values_used += 1
                elif attr_cfg.is_required or attr_cfg.id in required_fk_attribute_ids:
                    raise ClassInstanceBuildError(
                        f"Missing required attribute '{attr_cfg.name}'"
                    )
                else:
                    # Optional and no default → omit the Attribute instance.
                    if build_profile is not None:
                        build_profile.optional_attributes_omitted += 1
                    continue

            union = union_selections.get(attr_cfg.name) if union_selections else None
            attribute = build_attribute(
                owner_key=source.id,
                attribute_config=attr_cfg,
                value=raw_value,
                class_configs_by_id=class_configs_by_id,
                enum_option_resolver=enum_option_resolver,
                class_instance_resolver=class_instance_resolver,
                union=union,
            )
            _ = link_attribute(class_instance, attribute)
            if build_profile is not None:
                build_profile.attributes_built += 1

    if build_profile is not None:
        build_profile.materialize_attributes_s += (
            time.perf_counter() - materialize_started_at
        )

    return class_instance


def _dedupe_attribute_links(
    class_config_attribute_configs: Iterable[object],
) -> list[object]:
    links: list[object] = []
    seen_attribute_config_ids: set[UUID] = set()
    for link in class_config_attribute_configs:
        attr_cfg = getattr(link, "attribute_config", None)
        attr_cfg_id = getattr(attr_cfg, "id", None) or getattr(
            link, "attribute_config_id", None
        )
        if attr_cfg_id is None:
            links.append(link)
            continue
        if attr_cfg_id in seen_attribute_config_ids:
            continue
        seen_attribute_config_ids.add(attr_cfg_id)
        links.append(link)
    return links


def _relationship_attribute_config_ids(class_config: ClassConfig) -> set[UUID]:
    ids: set[UUID] = set()
    for rel in class_config.class_config_relationships or []:
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.attribute_config_id is not None:
                ids.add(rel_attr.attribute_config_id)
    return ids


def _required_fk_attribute_config_ids(class_config: ClassConfig) -> set[UUID]:
    """
    Relationship/FK requiredness for commit truth.

    This is intentionally independent from `AttributeConfig.is_required` so language
    serialization ergonomics (optional FK sugar) cannot relax commit invariants.
    """
    owned_attr_ids = {
        link.attribute_config.id
        for link in class_config.class_config_attribute_configs
        if link.attribute_config is not None and link.attribute_config.id is not None
    }
    required_ids: set[UUID] = set()

    for rel in class_config.class_config_relationships or []:
        is_association = rel.class_config_relationship_association_edge is not None
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            attr_id = rel_attr.attribute_config_id
            if attr_id is None or attr_id not in owned_attr_ids:
                continue

            if is_association:
                required_ids.add(attr_id)
                continue

            if bool(rel.forward_required):
                required_ids.add(attr_id)
                continue

    return required_ids


def _parse_default_value(attribute_config: AttributeConfig) -> object:
    default_value = attribute_config.default_value
    if default_value is None:
        raise ClassInstanceBuildError(
            f"Missing default_value for attribute '{attribute_config.name}'"
        )
    try:
        return json.loads(default_value)
    except Exception as e:
        raise ClassInstanceBuildError(
            f"Invalid default_value JSON for attribute '{attribute_config.name}': {default_value}"
        ) from e


__all__ = [
    "ClassInstanceBuildProfile",
    "ClassInstanceBuildError",
    "build_class_instance",
]
