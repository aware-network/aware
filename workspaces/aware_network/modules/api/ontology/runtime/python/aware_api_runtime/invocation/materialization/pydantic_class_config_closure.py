from __future__ import annotations

from collections.abc import Iterable, Mapping
from importlib import import_module
from types import UnionType
from typing import Any, get_args, get_origin
from uuid import UUID

from pydantic import BaseModel

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_utils.pydantic.class_config_registry import (
    get_registered_class_config_payload,
    iter_pydantic_package_class_config_payloads,
    register_pydantic_package_class_configs,
)


def pydantic_class_configs_by_id_for_ref(
    *,
    base_class_configs_by_id: Mapping[UUID, ClassConfig],
    root_class_config: ClassConfig | None,
    class_ref: str | None,
) -> dict[UUID, ClassConfig]:
    class_configs_by_id = dict(base_class_configs_by_id)
    if root_class_config is not None and root_class_config.id is not None:
        class_configs_by_id[root_class_config.id] = root_class_config

    package_prefixes = set(_package_prefixes_from_class_ref(class_ref=class_ref))
    model_cls = _resolve_pydantic_model_class_from_class_ref(class_ref=class_ref)
    if model_cls is not None:
        package_prefixes.update(_pydantic_model_package_prefixes(model_cls))

    for package_prefix in sorted(package_prefixes):
        register_pydantic_package_class_configs(package_prefix=package_prefix)
        for entry in iter_pydantic_package_class_config_payloads(
            package_prefix=package_prefix,
        ):
            class_config = ClassConfig.model_validate(entry.payload)
            if class_config.id is None:
                continue
            class_configs_by_id[class_config.id] = class_config

    return _close_descriptor_referenced_class_configs(
        class_configs_by_id=class_configs_by_id,
    )


def _package_prefixes_from_class_ref(*, class_ref: str | None) -> tuple[str, ...]:
    if not class_ref:
        return ()
    package_prefix = class_ref.split(".", 1)[0].strip()
    return (package_prefix,) if package_prefix else ()


def _resolve_pydantic_model_class_from_class_ref(
    *,
    class_ref: str | None,
) -> type[BaseModel] | None:
    if not class_ref or "." not in class_ref:
        return None
    module_ref, _, class_name = class_ref.rpartition(".")
    if not module_ref or not class_name:
        return None
    try:
        module = import_module(module_ref)
    except Exception:
        return None
    candidate = getattr(module, class_name, None)
    if isinstance(candidate, type) and issubclass(candidate, BaseModel):
        return candidate
    return None


def _pydantic_model_package_prefixes(model_cls: type[BaseModel]) -> tuple[str, ...]:
    prefixes: set[str] = set()
    seen_models: set[type[BaseModel]] = set()
    pending = [model_cls]
    while pending:
        current = pending.pop()
        if current in seen_models:
            continue
        seen_models.add(current)
        package_prefix = current.__module__.split(".", 1)[0].strip()
        if package_prefix:
            prefixes.add(package_prefix)
        try:
            current.model_rebuild()
        except Exception:
            pass
        for field in current.model_fields.values():
            for nested_model in _pydantic_model_classes_from_annotation(
                field.annotation,
            ):
                if nested_model not in seen_models:
                    pending.append(nested_model)
    return tuple(sorted(prefixes))


def _pydantic_model_classes_from_annotation(
    annotation: object,
) -> Iterable[type[BaseModel]]:
    if annotation is None or annotation is Any:
        return ()
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return (annotation,)
        return ()
    origin = get_origin(annotation)
    if origin is None:
        return ()
    args = tuple(
        arg
        for arg in get_args(annotation)
        if arg is not None and arg is not type(None) and arg is not Ellipsis
    )
    if origin is UnionType:
        nested: list[type[BaseModel]] = []
        for arg in args:
            nested.extend(_pydantic_model_classes_from_annotation(arg))
        return tuple(nested)
    nested_models: list[type[BaseModel]] = []
    for arg in args:
        nested_models.extend(_pydantic_model_classes_from_annotation(arg))
    return tuple(nested_models)


def _close_descriptor_referenced_class_configs(
    *,
    class_configs_by_id: dict[UUID, ClassConfig],
) -> dict[UUID, ClassConfig]:
    changed = True
    while changed:
        changed = False
        missing_ids: set[UUID] = set()
        for class_config in tuple(class_configs_by_id.values()):
            missing_ids.update(
                class_config_id
                for class_config_id in _descriptor_class_config_ids(
                    class_config=class_config,
                )
                if class_config_id not in class_configs_by_id
            )
        for class_config_id in missing_ids:
            payload = get_registered_class_config_payload(
                class_config_id=str(class_config_id),
            )
            if payload is None:
                continue
            class_config = ClassConfig.model_validate(payload)
            if class_config.id is None or class_config.id in class_configs_by_id:
                continue
            class_configs_by_id[class_config.id] = class_config
            changed = True
    return class_configs_by_id


def _descriptor_class_config_ids(*, class_config: ClassConfig) -> tuple[UUID, ...]:
    class_config_ids: list[UUID] = []
    for link in class_config.class_config_attribute_configs or ():
        attribute_config = link.attribute_config
        if attribute_config is None or attribute_config.type_descriptor is None:
            continue
        class_config_ids.extend(
            _descriptor_tree_class_config_ids(attribute_config.type_descriptor)
        )
    return tuple(class_config_ids)


def _descriptor_tree_class_config_ids(
    descriptor: AttributeTypeDescriptor,
) -> tuple[UUID, ...]:
    class_config_ids: list[UUID] = []
    if (
        descriptor.kind == AttributeTypeDescriptorKind.class_
        and descriptor.class_config_id is not None
    ):
        class_config_ids.append(descriptor.class_config_id)
    for link in descriptor.child_links or ():
        child = link.child
        if child is None:
            continue
        class_config_ids.extend(_descriptor_tree_class_config_ids(child))
    return tuple(class_config_ids)


__all__ = ["pydantic_class_configs_by_id_for_ref"]
