from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Protocol, cast
from uuid import UUID

from pydantic import BaseModel

from aware_code.types.json import JsonValue
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_call_response_commit import (
    FunctionCallResponseCommit,
)
from aware_meta_ontology.function.function_call_response import FunctionCallResponse
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_function_call_response_commit_id


class OperationLabelIndexSource(Protocol):
    ocg: ObjectConfigGraph
    class_configs_by_id: Mapping[UUID, ClassConfig]


class _FunctionObjectConfigGraphNode(Protocol):
    type: ObjectConfigGraphNodeType
    function_config: FunctionConfig | None


def jsonify_invocation_payload(payload: object) -> JsonValue:
    if payload is None:
        return None
    if isinstance(payload, (str, int, float, bool)):
        return payload
    if isinstance(payload, UUID):
        return str(payload)
    if isinstance(payload, Enum):
        return jsonify_invocation_payload(cast(object, payload.value))
    try:
        from aware_orm.models.orm_model import ORMModel

        if isinstance(payload, ORMModel):
            return jsonify_invocation_payload(payload.model_dump(mode="json"))
    except Exception:
        pass
    if isinstance(payload, BaseModel):
        return jsonify_invocation_payload(payload.model_dump(mode="json"))
    if isinstance(payload, Mapping):
        return {
            str(key): jsonify_invocation_payload(value)
            for key, value in cast(Mapping[object, object], payload).items()
        }
    if isinstance(payload, (list, tuple)):
        sequence = cast(list[object] | tuple[object, ...], payload)
        return [jsonify_invocation_payload(value) for value in sequence]
    return str(payload)


def link_function_call_response_commit(
    *,
    response: FunctionCallResponse | None,
    oig_commit: ObjectInstanceGraphCommit | None,
) -> None:
    """Attach produced OIG commit evidence to a FunctionCallResponse."""
    if response is None or oig_commit is None:
        return
    if response.id is None or oig_commit.id is None:
        return

    response_id = response.id
    oig_commit_id = oig_commit.id
    edges = response.function_call_response_commits
    for edge in edges:
        if edge.object_instance_graph_commit_id == oig_commit_id:
            return

    edges.append(
        FunctionCallResponseCommit(
            id=stable_function_call_response_commit_id(
                function_call_response_id=response_id,
                object_instance_graph_commit_id=oig_commit_id,
            ),
            object_instance_graph_commit=oig_commit,
            object_instance_graph_commit_id=oig_commit_id,
            function_call_response_id=response_id,
            position=len(edges),
        )
    )


def build_invocation_operation_label_index(
    index: OperationLabelIndexSource,
) -> dict[UUID, str]:
    """Build function_id -> operation label lookup from in-memory runtime indexes."""

    function_names_by_id: dict[UUID, str] = {}

    def remember_function(function_config: FunctionConfig | None) -> None:
        if function_config is None:
            return
        function_name = function_config.name.strip()
        if function_name:
            function_names_by_id.setdefault(function_config.id, function_name)

    for node in index.ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.function:
            continue
        remember_function(cast(_FunctionObjectConfigGraphNode, node).function_config)

    class_config_values = tuple(index.class_configs_by_id.values())
    for class_config in class_config_values:
        for link in class_config.class_config_function_configs:
            remember_function(link.function_config)

    labels_by_id: dict[UUID, str] = dict(function_names_by_id)
    class_labels_by_id: dict[UUID, str] = {}
    for class_config in class_config_values:
        class_name = class_config.name.strip()
        for link in class_config.class_config_function_configs:
            function_id = link.function_config_id or link.function_config.id
            function_name = function_names_by_id.get(function_id)
            if not function_name:
                continue
            class_labels_by_id.setdefault(
                function_id,
                f"{class_name}.{function_name}" if class_name else function_name,
            )

    labels_by_id.update(class_labels_by_id)
    return labels_by_id


def resolve_invocation_operation_label(
    *,
    index: OperationLabelIndexSource,
    function_id: UUID,
    label_index: Mapping[UUID, str] | None = None,
) -> str | None:
    labels_by_id = (
        label_index
        if label_index is not None
        else build_invocation_operation_label_index(index)
    )
    return labels_by_id.get(function_id)


__all__ = [
    "build_invocation_operation_label_index",
    "jsonify_invocation_payload",
    "link_function_call_response_commit",
    "OperationLabelIndexSource",
    "resolve_invocation_operation_label",
]
