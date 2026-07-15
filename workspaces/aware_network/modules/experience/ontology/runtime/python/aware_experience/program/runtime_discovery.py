from __future__ import annotations

from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    CapabilityFunction,
    CapabilityObject,
    DescribeEnvironmentOPG,
    DescribeEnvironmentOPGConstructor,
)


def _node_type_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "").strip()


def _is_class_node(node: object) -> bool:
    return _node_type_value(getattr(node, "type", None)) == "class"


def _is_function_node(node: object) -> bool:
    return _node_type_value(getattr(node, "type", None)) == "function"


def _ocg_nodes(index: object) -> tuple[object, ...]:
    ocg = getattr(index, "ocg", None)
    return tuple(getattr(ocg, "object_config_graph_nodes", ()) or ())


def _opgs(index: object) -> tuple[object, ...]:
    opg_by_id = getattr(index, "opg_by_id", None)
    if isinstance(opg_by_id, dict):
        return tuple(opg_by_id.values())
    ocg = getattr(index, "ocg", None)
    return tuple(getattr(ocg, "object_projection_graphs", ()) or ())


def build_program_describe_environment_opgs(
    *,
    index: object,
) -> list[DescribeEnvironmentOPG]:
    edge_to_function_id: dict[UUID, UUID] = {}
    for node in _ocg_nodes(index):
        if not _is_class_node(node):
            continue
        class_config = getattr(node, "class_config", None)
        if class_config is None:
            continue
        for link in getattr(class_config, "class_config_function_configs", ()) or ():
            function_config = getattr(link, "function_config", None)
            function_id = getattr(function_config, "id", None)
            edge_id = getattr(link, "id", None)
            if edge_id is not None and function_id is not None:
                edge_to_function_id[edge_id] = function_id

    descriptors: list[DescribeEnvironmentOPG] = []
    for opg in _opgs(index):
        constructors: list[DescribeEnvironmentOPGConstructor] = []
        for constructor in (
            getattr(opg, "object_projection_graph_constructors", ()) or ()
        ):
            function_edge_id = getattr(constructor, "function_constructor_id", None)
            function_id = (
                edge_to_function_id.get(function_edge_id)
                if function_edge_id is not None
                else None
            )
            if function_id is None:
                continue

            root_class_config_id = None
            root_node_id = getattr(constructor, "root_node_id", None)
            if root_node_id is not None:
                for node in getattr(opg, "object_projection_graph_nodes", ()) or ():
                    if getattr(node, "id", None) == root_node_id:
                        root_class_config_id = getattr(node, "class_config_id", None)
                        break

            constructors.append(
                DescribeEnvironmentOPGConstructor(
                    function_id=function_id,
                    root_class_config_id=root_class_config_id,
                )
            )

        descriptors.append(
            DescribeEnvironmentOPG(
                id=getattr(opg, "id", None),
                projection_hash=getattr(opg, "projection_hash", None),
                name=getattr(opg, "name", None),
                description=getattr(opg, "description", None),
                supports_virtual_build=getattr(opg, "supports_virtual_build", None),
                constructors=constructors,
            )
        )

    descriptors.sort(key=lambda item: item.projection_hash or "")
    return descriptors


def build_program_capability_functions(
    *,
    index: object,
) -> list[CapabilityFunction]:
    by_id: dict[UUID, CapabilityFunction] = {}
    for node in _ocg_nodes(index):
        if _is_function_node(node):
            function_config = getattr(node, "function_config", None)
            capability = (
                _capability_function_from_config(
                    function_config,
                    is_constructor=False,
                )
                if function_config is not None
                else None
            )
            if capability is not None:
                by_id[capability.id] = capability
            continue

        if not _is_class_node(node):
            continue
        class_config = getattr(node, "class_config", None)
        if class_config is None:
            continue
        for link in getattr(class_config, "class_config_function_configs", ()) or ():
            if not bool(getattr(link, "is_public", False)):
                continue
            function_config = getattr(link, "function_config", None)
            capability = (
                _capability_function_from_config(
                    function_config,
                    is_constructor=bool(getattr(link, "is_constructor", False)),
                )
                if function_config is not None
                else None
            )
            if capability is None:
                continue
            existing = by_id.get(capability.id)
            if existing is not None and existing.is_constructor:
                continue
            by_id[capability.id] = capability
    return sorted(by_id.values(), key=lambda item: item.name or "")


def build_program_capability_objects(
    *,
    index: object,
) -> list[CapabilityObject]:
    objects: list[CapabilityObject] = []
    for node in _ocg_nodes(index):
        if not _is_class_node(node):
            continue
        class_config = getattr(node, "class_config", None)
        if class_config is None:
            continue
        class_id = getattr(class_config, "id", None)
        class_name = getattr(class_config, "name", None)
        if class_id is None or not class_name:
            continue
        links = list(getattr(class_config, "class_config_function_configs", ()) or ())
        links.sort(
            key=lambda item: (
                getattr(item, "position", None)
                if getattr(item, "position", None) is not None
                else 10_000
            )
        )
        functions: list[CapabilityFunction] = []
        for link in links:
            if not bool(getattr(link, "is_public", False)):
                continue
            function_config = getattr(link, "function_config", None)
            capability = (
                _capability_function_from_config(
                    function_config,
                    is_constructor=bool(getattr(link, "is_constructor", False)),
                )
                if function_config is not None
                else None
            )
            if capability is not None:
                functions.append(capability)
        objects.append(
            CapabilityObject(
                id=class_id,
                name=class_name,
                description=getattr(class_config, "description", None),
                functions=functions,
            )
        )
    return sorted(objects, key=lambda item: item.name or "")


def _capability_function_from_config(
    function_config: object,
    *,
    is_constructor: bool = False,
) -> CapabilityFunction | None:
    function_id = getattr(function_config, "id", None)
    name = getattr(function_config, "name", None)
    if function_id is None or not name:
        return None
    return CapabilityFunction(
        id=function_id,
        name=name,
        summary=getattr(function_config, "description", None),
        role_id=None,
        is_constructor=is_constructor,
        inputs=[],
        outputs=[],
        arguments=[],
    )


__all__ = [
    "build_program_capability_functions",
    "build_program_capability_objects",
    "build_program_describe_environment_opgs",
]
