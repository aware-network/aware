from __future__ import annotations

from uuid import uuid4

from aware_meta.graph.config.index_orm import ObjectConfigGraphORMIndex
from aware_orm.models.orm_model import ORMModel


def test_object_config_graph_orm_index_len_counts_indexed_classes() -> None:
    class ExampleOrmModel(ORMModel):
        pass

    index = ObjectConfigGraphORMIndex(
        orm_model_type_by_class_config_id={uuid4(): ExampleOrmModel}
    )

    assert len(index) == 1
