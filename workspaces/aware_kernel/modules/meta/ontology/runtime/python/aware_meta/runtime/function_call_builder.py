"""Meta-owned FunctionCall envelope builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID, uuid4

from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.value_resolvers import (
    default_meta_class_instance_resolver,
    default_meta_enum_option_resolver,
    parse_meta_default_value,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_call_argument import FunctionCallArgument
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.instance.object_instance_graph_lane import (
    ObjectInstanceGraphLane,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_identity_id,
    stable_function_call_id,
)


def resolve_meta_function_config(
    *,
    index: MetaGraphRuntimeIndex,
    function_id: UUID,
) -> FunctionConfig:
    """Resolve a FunctionConfig from Meta indexed graph truth."""

    for node in index.ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.function:
            continue
        function_config = node.function_config
        if function_config is not None and function_config.id == function_id:
            return function_config

    for node in index.ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        class_config = node.class_config
        if class_config is None:
            continue
        for link in class_config.class_config_function_configs:
            if link.function_config.id == function_id:
                return link.function_config

    raise ValueError(f"FunctionConfig not found in Meta OCG: {function_id}")


def build_meta_function_call(
    *,
    index: MetaGraphRuntimeIndex,
    object_id: UUID,
    function_id: UUID,
    args: Sequence[object],
    kwargs: Mapping[str, object],
    domain_oig_lane: ObjectInstanceGraphLane | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    base_commit: ObjectInstanceGraphCommit | None = None,
    call_key: UUID | None = None,
    expected_graph_hash_pre: str | None = None,
) -> FunctionCall:
    """Build a deterministic Meta FunctionCall envelope."""

    function_config = resolve_meta_function_config(
        index=index,
        function_id=function_id,
    )
    lane_id = (
        domain_oig_lane.id
        if domain_oig_lane is not None and domain_oig_lane.id is not None
        else uuid4()
    )
    resolved_call_key = call_key or uuid4()
    function_call_id = stable_function_call_id(
        object_instance_graph_lane_id=lane_id,
        function_config_id=function_id,
        call_key=resolved_call_key,
    )
    target_identity_id = None
    if object_instance_graph_identity_id is not None:
        target_identity_id = stable_class_instance_identity_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_id=object_id,
        )

    payload: dict[str, object | None] = {
        "id": function_call_id,
        "object_instance_graph_lane_id": lane_id,
        "call_key": resolved_call_key,
        "function_config": function_config,
        "function_config_id": function_id,
        "base_commit": base_commit,
        "base_commit_id": base_commit.id if base_commit is not None else None,
        "graph_hash_pre": expected_graph_hash_pre,
        "function_call_arguments": [],
    }
    if "target_class_instance_identity_id" in FunctionCall.model_fields:
        payload["target_class_instance_identity_id"] = target_identity_id
    elif "target_class_instance_id" in FunctionCall.model_fields:
        payload["target_class_instance_id"] = object_id

    function_call = FunctionCall(**payload)
    function_call.function_call_arguments = _build_meta_function_call_arguments(
        index=index,
        function_call=function_call,
        function_config=function_config,
        args=args,
        kwargs=kwargs,
    )
    return function_call


def _build_meta_function_call_arguments(
    *,
    index: MetaGraphRuntimeIndex,
    function_call: FunctionCall,
    function_config: FunctionConfig,
    args: Sequence[object],
    kwargs: Mapping[str, object],
) -> list[FunctionCallArgument]:
    inputs = [
        edge
        for edge in (function_config.function_config_attribute_configs or [])
        if edge.type == FunctionAttributeType.input
    ]
    inputs.sort(key=lambda edge: edge.position)

    positions = [edge.position for edge in inputs]
    if len(set(positions)) != len(positions):
        raise ValueError("FunctionConfig has duplicate input argument positions")

    max_position = max(positions) if positions else -1
    if len(args) > max_position + 1:
        raise ValueError(
            f"Too many positional args (got {len(args)}, expected <= "
            f"{max_position + 1})"
        )

    resolved: list[object | None] = list(args)
    while len(resolved) <= max_position:
        resolved.append(None)

    if kwargs:
        name_to_position = {
            edge.attribute_config.name: edge.position
            for edge in inputs
        }
        unknown = [key for key in kwargs if key not in name_to_position]
        if unknown:
            raise ValueError(
                f"Unknown kwargs for function {function_config.name}: {unknown}"
            )
        for key, value in kwargs.items():
            resolved[name_to_position[key]] = value

    call_arguments: list[FunctionCallArgument] = []
    for edge in inputs:
        position = edge.position
        attribute_config = edge.attribute_config
        value = resolved[position]
        if value is None:
            if attribute_config.default_value is not None:
                value = parse_meta_default_value(attribute_config.default_value)
            elif not attribute_config.is_required:
                continue
            else:
                raise ValueError(
                    "Missing required argument "
                    f"{attribute_config.name!r} for function {function_config.name}"
                )

        attribute = build_attribute(
            owner_key=function_call.id,
            attribute_config=attribute_config,
            value=value,
            class_configs_by_id=index.class_configs_by_id,
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=default_meta_class_instance_resolver,
        )
        call_arguments.append(
            FunctionCallArgument(
                position=position,
                attribute=attribute,
                attribute_id=attribute.id,
                function_call_id=function_call.id,
            )
        )
    return call_arguments


__all__ = ["build_meta_function_call", "resolve_meta_function_config"]
