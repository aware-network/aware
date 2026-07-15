from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry

from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta.graph.config.model_bootstrap import (
    get_object_config_graph_node_class_config_id,
)


class ObjectConfigGraphORMIndex(BaseModel):
    """Canonical OCG→ORM index (ClassConfig-bound).

    Runtime resolves ORM model classes using canonical `ClassConfig.id` bindings
    (not legacy ObjectConfig IDs).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    orm_model_type_by_class_config_id: dict[UUID, type[ORMModel]]

    def __len__(self) -> int:
        return len(self.orm_model_type_by_class_config_id)


def index_ocg_orm_by_class_config_id(
    ocg: ObjectConfigGraph,
) -> ObjectConfigGraphORMIndex:
    """Index ORM model classes for every graph_ref ClassConfig present in an OCG.

    Inline-value classes are value objects (Pydantic-only) and are intentionally not bound
    as ORM models, so they are excluded from this index.
    """
    if not ORMModelRegistry.is_initialized():
        raise ValueError("ORM registry is not initialized")

    orm_model_type_by_class_config_id: dict[UUID, type[ORMModel]] = {}
    for node in ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        class_config_id = get_object_config_graph_node_class_config_id(node)
        if class_config_id is None:
            continue
        if node.class_config is not None and node.class_config.value_mode == ClassValueMode.inline_value:
            continue
        orm_class = ORMModelRegistry.get_class_by_class_config_id(class_config_id)
        if orm_class is None:
            raise ValueError(f"ORM model not found for ClassConfig {class_config_id}")
        orm_model_type_by_class_config_id[class_config_id] = orm_class

    return ObjectConfigGraphORMIndex(
        orm_model_type_by_class_config_id=orm_model_type_by_class_config_id,
    )


__all__ = [
    "ObjectConfigGraphORMIndex",
    "index_ocg_orm_by_class_config_id",
]
