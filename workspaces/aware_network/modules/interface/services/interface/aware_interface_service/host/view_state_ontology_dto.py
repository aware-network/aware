from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import NoneType, UnionType
from typing import TypeVar, Union, cast, get_args, get_origin
from uuid import UUID

from aware_types import JsonObject, JsonValue


_T = TypeVar("_T")


class InterfaceViewStateOntologyDtoError(RuntimeError):
    pass


def materialize_latest_ontology(
    *,
    model: type[_T],
    result: object,
    assets: object,
) -> _T | None:
    materialized = getattr(result, "materialized_lane", None)
    graph = getattr(materialized, "graph", None)
    if graph is None:
        return None
    resolver = _OntologyDtoGraphResolver(graph=graph, assets=assets)
    return resolver.materialize_latest(model)


def raw_ontology_deltas_for_result(result: object) -> tuple[JsonObject, ...]:
    materialized = getattr(result, "materialized_lane", None)
    if materialized is None:
        return tuple(
            _json_object(
                {
                    "commit_id": str(commit_id),
                    "kind": "object_instance_graph_commit_ref",
                    "payload": {},
                }
            )
            for commit_id in getattr(result, "fetched_commit_ids", ()) or ()
        )

    commit_id = getattr(result, "head_commit_id", None)
    out: list[JsonObject] = []
    last_semantics = getattr(materialized, "last_semantics", None)
    if isinstance(last_semantics, Mapping):
        out.append(
            _json_object(
                {
                    "commit_id": str(commit_id or ""),
                    "kind": "object_instance_graph_commit_semantics",
                    "payload": _json_object(last_semantics),
                }
            )
        )
    last_change_tree = getattr(materialized, "last_change_tree", None)
    to_dict = getattr(last_change_tree, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            out.append(
                _json_object(
                    {
                        "commit_id": str(commit_id or ""),
                        "kind": "object_instance_graph_change_tree",
                        "payload": _json_object(payload),
                    }
                )
            )
    if not out:
        out.extend(
            _json_object(
                {
                    "commit_id": str(applied_commit_id),
                    "kind": "object_instance_graph_commit_ref",
                    "payload": {},
                }
            )
            for applied_commit_id in getattr(materialized, "applied_commit_ids", ()) or ()
        )
    return tuple(out)


class _OntologyDtoGraphResolver:
    def __init__(self, *, graph: object, assets: object) -> None:
        self._graph = graph
        self._instances_by_id = {
            str(getattr(instance, "id", "")): instance
            for instance in getattr(graph, "class_instances", ()) or ()
            if getattr(instance, "id", None) is not None
        }
        self._relationships = tuple(
            getattr(graph, "class_instance_relationships", ()) or ()
        )
        self._class_configs_by_id = _class_configs_by_id(assets)
        self._relationship_configs_by_id = _relationship_configs_by_id(assets)

    def materialize_latest(self, model: type[_T]) -> _T | None:
        root_instance = self._root_instance()
        if root_instance is None:
            return None
        return self.materialize_model(
            model=model,
            instance=root_instance,
            visiting=frozenset(),
        )

    def materialize_model(
        self,
        *,
        model: type[_T],
        instance: object,
        visiting: frozenset[tuple[str, str]],
    ) -> _T:
        class_config = self._class_config_for_instance(instance)
        if class_config is None:
            raise InterfaceViewStateOntologyDtoError(
                "Cannot materialize ontology DTO without class config: "
                + f"model={_model_name(model)!r} instance_id={getattr(instance, 'id', None)!r}"
            )
        if not _class_config_matches_model(class_config, model):
            raise InterfaceViewStateOntologyDtoError(
                "Ontology DTO model does not match materialized class instance: "
                + f"model={_model_name(model)!r} class_fqn={getattr(class_config, 'class_fqn', None)!r}"
            )

        visit_key = (str(getattr(instance, "id", "")), _model_name(model))
        if visit_key in visiting:
            return _validate_model(model, {})
        next_visiting = frozenset((*visiting, visit_key))

        payload: dict[str, object] = {}
        model_fields = getattr(model, "model_fields", {})
        for field_name, field in model_fields.items():
            annotation = getattr(field, "annotation", None)
            related_model = _related_model_from_annotation(annotation)
            if related_model is not None:
                related_value = self._relationship_value(
                    instance=instance,
                    field_name=field_name,
                    related_model=related_model.model,
                    collection=related_model.collection,
                    visiting=next_visiting,
                )
                if related_value is not None:
                    payload[field_name] = related_value
                continue

            attribute_value = self._attribute_value(
                class_config=class_config,
                instance=instance,
                field_name=field_name,
            )
            if attribute_value is not _MISSING:
                payload[field_name] = attribute_value

        return _validate_model(model, payload)

    def _root_instance(self) -> object | None:
        root_instance = getattr(self._graph, "root_class_instance", None)
        if root_instance is not None:
            return root_instance
        root_id = getattr(self._graph, "root_class_instance_id", None)
        if root_id is None:
            return None
        return self._instances_by_id.get(str(root_id))

    def _class_config_for_instance(self, instance: object) -> object | None:
        class_config = getattr(instance, "class_config", None)
        if class_config is not None:
            return class_config
        class_config_id = getattr(instance, "class_config_id", None)
        if class_config_id is None:
            return None
        return self._class_configs_by_id.get(str(class_config_id))

    def _attribute_value(
        self,
        *,
        class_config: object,
        instance: object,
        field_name: str,
    ) -> object:
        attribute_config_id = _attribute_config_id_for_field(
            class_config=class_config,
            field_name=field_name,
        )
        if attribute_config_id is None:
            return _MISSING
        for edge in getattr(instance, "class_instance_attributes", ()) or ():
            attribute = getattr(edge, "attribute", None)
            if attribute is None:
                continue
            if str(getattr(attribute, "attribute_config_id", "")) != attribute_config_id:
                continue
            return _attribute_value_payload(getattr(attribute, "value_root", None))
        return _MISSING

    def _relationship_value(
        self,
        *,
        instance: object,
        field_name: str,
        related_model: type[object],
        collection: bool,
        visiting: frozenset[tuple[str, str]],
    ) -> object | None:
        instance_id = str(getattr(instance, "id", ""))
        related_payloads: list[object] = []
        for relationship in self._relationships:
            if str(getattr(relationship, "source_class_instance_id", "")) != instance_id:
                continue
            relationship_config = self._relationship_config_for_instance_relationship(
                relationship
            )
            if not _relationship_config_matches_field(
                relationship_config=relationship_config,
                field_name=field_name,
            ):
                continue
            target_id = str(getattr(relationship, "target_class_instance_id", ""))
            target_instance = self._instances_by_id.get(target_id)
            if target_instance is None:
                continue
            related_payloads.append(
                self.materialize_model(
                    model=related_model,
                    instance=target_instance,
                    visiting=visiting,
                )
            )
        if collection:
            return related_payloads
        return related_payloads[0] if related_payloads else None

    def _relationship_config_for_instance_relationship(
        self,
        relationship: object,
    ) -> object | None:
        relationship_config = getattr(relationship, "class_config_relationship", None)
        if relationship_config is not None:
            return relationship_config
        relationship_config_id = getattr(relationship, "class_config_relationship_id", None)
        if relationship_config_id is None:
            return None
        return self._relationship_configs_by_id.get(str(relationship_config_id))


@dataclass(frozen=True, slots=True)
class _RelatedModel:
    model: type[object]
    collection: bool


class _Missing:
    pass


_MISSING = _Missing()


def _class_configs_by_id(assets: object) -> dict[str, object]:
    out: dict[str, object] = {}
    ocg = getattr(assets, "ocg", None)
    for node in getattr(ocg, "object_config_graph_nodes", ()) or ():
        class_config = getattr(node, "class_config", None)
        class_config_id = getattr(class_config, "id", None)
        if class_config_id is not None:
            out[str(class_config_id)] = class_config
    return out


def _relationship_configs_by_id(assets: object) -> dict[str, object]:
    out: dict[str, object] = {}
    for class_config in _class_configs_by_id(assets).values():
        for relationship_config in getattr(class_config, "class_config_relationships", ()) or ():
            relationship_config_id = getattr(relationship_config, "id", None)
            if relationship_config_id is not None:
                out[str(relationship_config_id)] = relationship_config
    ocg = getattr(assets, "ocg", None)
    for node in getattr(ocg, "object_config_graph_nodes", ()) or ():
        relationship_config = getattr(node, "class_config_relationship", None)
        relationship_config_id = getattr(relationship_config, "id", None)
        if relationship_config_id is not None:
            out[str(relationship_config_id)] = relationship_config
    return out


def _class_config_matches_model(class_config: object, model: type[object]) -> bool:
    model_name = _model_name(model)
    if getattr(class_config, "name", None) == model_name:
        return True
    class_fqn = str(getattr(class_config, "class_fqn", "") or "")
    return class_fqn.endswith(f".{model_name}") or class_fqn.endswith(f"::{model_name}")


def _model_name(model: type[object]) -> str:
    return str(getattr(model, "__name__", model.__class__.__name__))


def _validate_model(model: type[_T], payload: Mapping[str, object]) -> _T:
    model_validate = getattr(model, "model_validate", None)
    if not callable(model_validate):
        raise InterfaceViewStateOntologyDtoError(
            "Ontology DTO model is missing pydantic model_validate: "
            + f"model={_model_name(model)!r}"
        )
    return cast(_T, model_validate(payload))


def _related_model_from_annotation(annotation: object) -> _RelatedModel | None:
    if _is_model_type(annotation):
        return _RelatedModel(model=cast(type[object], annotation), collection=False)

    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (list, Sequence) and args:
        item = _non_none_arg(args)
        if _is_model_type(item):
            return _RelatedModel(model=cast(type[object], item), collection=True)
    if origin in (UnionType, Union):
        item = _non_none_arg(args)
        if _is_model_type(item):
            return _RelatedModel(model=cast(type[object], item), collection=False)
        item_origin = get_origin(item)
        item_args = get_args(item)
        if item_origin in (list, Sequence) and item_args:
            list_item = _non_none_arg(item_args)
            if _is_model_type(list_item):
                return _RelatedModel(
                    model=cast(type[object], list_item),
                    collection=True,
                )
    return None


def _non_none_arg(args: tuple[object, ...]) -> object:
    for arg in args:
        if arg is not NoneType:
            return arg
    return args[0] if args else object


def _is_model_type(value: object) -> bool:
    return isinstance(value, type) and callable(getattr(value, "model_validate", None))


def _attribute_config_id_for_field(
    *,
    class_config: object,
    field_name: str,
) -> str | None:
    for edge in getattr(class_config, "class_config_attribute_configs", ()) or ():
        attribute_config = getattr(edge, "attribute_config", None)
        if getattr(attribute_config, "name", None) != field_name:
            continue
        attribute_config_id = getattr(attribute_config, "id", None)
        if attribute_config_id is None:
            attribute_config_id = getattr(edge, "attribute_config_id", None)
        return str(attribute_config_id) if attribute_config_id is not None else None
    return None


def _attribute_value_payload(value_root: object | None) -> object:
    if value_root is None:
        return None
    primitive_value = getattr(value_root, "primitive_value", None)
    if isinstance(primitive_value, Mapping):
        if "value" in primitive_value:
            return primitive_value["value"]
        return dict(primitive_value)
    enum_option = getattr(value_root, "enum_option", None)
    enum_value = getattr(enum_option, "value", None)
    if enum_value is not None:
        return enum_value
    child_links = list(getattr(value_root, "child_links", ()) or ())
    if child_links:
        child_links.sort(
            key=lambda link: (
                _optional_sort_int(getattr(link, "position", None)),
                str(getattr(link, "identity_key", "") or ""),
            )
        )
        return [
            _attribute_value_payload(getattr(link, "child", None))
            for link in child_links
        ]
    inline_value = getattr(value_root, "inline_value_instance", None)
    if inline_value is not None:
        return _inline_value_payload(inline_value)
    return None


def _inline_value_payload(inline_value: object) -> dict[str, object]:
    payload: dict[str, object] = {}
    for edge in getattr(inline_value, "inline_value_instance_attributes", ()) or ():
        attribute = getattr(edge, "attribute", None)
        attribute_config = getattr(attribute, "attribute_config", None)
        name = getattr(attribute_config, "name", None)
        if name is None:
            continue
        payload[str(name)] = _attribute_value_payload(
            getattr(attribute, "value_root", None)
        )
    return payload


def _optional_sort_int(value: object) -> int:
    if isinstance(value, int):
        return value
    return 1_000_000_000


def _relationship_config_matches_field(
    *,
    relationship_config: object | None,
    field_name: str,
) -> bool:
    if relationship_config is None:
        return False
    if getattr(relationship_config, "relationship_key", None) == field_name:
        return True
    for relationship_attribute in (
        getattr(relationship_config, "class_config_relationship_attributes", ()) or ()
    ):
        attribute_config = getattr(relationship_attribute, "attribute_config", None)
        if getattr(attribute_config, "name", None) == field_name:
            return True
    return False


def _json_object(raw: Mapping[object, object]) -> JsonObject:
    return JsonObject(
        {
            str(key): _json_value(value)
            for key, value in raw.items()
            if value is not None
        }
    )


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return cast(JsonValue, _json_object(value))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json", exclude_none=True)
        if isinstance(dumped, Mapping):
            return cast(JsonValue, _json_object(dumped))
        return _json_value(dumped)
    return str(value)


__all__ = [
    "InterfaceViewStateOntologyDtoError",
    "materialize_latest_ontology",
    "raw_ontology_deltas_for_result",
]
