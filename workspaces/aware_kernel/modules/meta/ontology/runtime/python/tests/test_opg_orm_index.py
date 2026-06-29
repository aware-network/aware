from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.projection.index_orm import ObjectProjectionGraphORMIndex
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


def test_object_projection_graph_orm_index_len_counts_indexed_projections() -> None:
    opg = ObjectProjectionGraph(
        id=uuid4(),
        name="home",
        projection_hash="sha256:home",
        language=CodeLanguage.aware,
        object_config_graph_id=uuid4(),
    )

    index = ObjectProjectionGraphORMIndex(opgs_by_id={opg.id: opg})

    assert len(index) == 1
