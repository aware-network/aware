from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


class ObjectProjectionGraphORMIndex(BaseModel):
    """Index ORM model types by ObjectProjectionGraph membership (ClassConfig-bound)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    opgs_by_id: dict[UUID, ObjectProjectionGraph] = Field(default_factory=dict)
    opg_ids_by_class_config_id: dict[UUID, list[UUID]] = Field(default_factory=dict)
    class_config_ids_by_opg_id: dict[UUID, list[UUID]] = Field(default_factory=dict)
    orm_model_types_by_projection_id: dict[UUID, list[type[ORMModel]]] = Field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.opgs_by_id)


def index_orm_models_by_projection(
    ocg: ObjectConfigGraph,
) -> ObjectProjectionGraphORMIndex:
    """Index ORM models by projection id using canonical ClassConfig bindings."""
    if not ORMModelRegistry.is_initialized():
        raise ValueError("ORM registry is not initialized")

    opgs_by_id: dict[UUID, ObjectProjectionGraph] = {}
    opg_ids_by_class_config_id: dict[UUID, list[UUID]] = {}
    class_config_ids_by_opg_id: dict[UUID, list[UUID]] = {}
    orm_model_types_by_projection_id: dict[UUID, list[type[ORMModel]]] = {}

    for opg in ocg.object_projection_graphs:
        opgs_by_id[opg.id] = opg

        cc_ids: set[UUID] = set()
        for node in opg.object_projection_graph_nodes:
            cc_ids.add(node.class_config_id)
            opg_ids_by_class_config_id.setdefault(node.class_config_id, []).append(opg.id)

        ordered_cc_ids = sorted(cc_ids, key=lambda cid: str(cid))
        class_config_ids_by_opg_id[opg.id] = ordered_cc_ids

    for opg_id, class_config_ids in class_config_ids_by_opg_id.items():
        orm_classes: list[type[ORMModel]] = []
        for class_config_id in class_config_ids:
            orm_class = ORMModelRegistry.get_class_by_class_config_id(class_config_id)
            if orm_class is None:
                raise ValueError(f"ORM model not found for ClassConfig {class_config_id}")
            orm_classes.append(orm_class)
        orm_model_types_by_projection_id[opg_id] = orm_classes

    return ObjectProjectionGraphORMIndex(
        opgs_by_id=opgs_by_id,
        opg_ids_by_class_config_id=opg_ids_by_class_config_id,
        class_config_ids_by_opg_id=class_config_ids_by_opg_id,
        orm_model_types_by_projection_id=orm_model_types_by_projection_id,
    )


__all__ = [
    "ObjectProjectionGraphORMIndex",
    "index_orm_models_by_projection",
]
