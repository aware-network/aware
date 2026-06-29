from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_instance_graph_identity_id,
    stable_object_projection_graph_identity_id,
)
from aware_meta.graph.instance.identity import (
    synthesize_object_instance_graph_identity,
)
from aware_meta.graph.projection.identity import (
    synthesize_object_projection_graph_identity,
)


def test_synthesize_object_projection_graph_identity_is_parent_scoped() -> None:
    ocgi_key = "aware_meta"
    ocgi = ObjectConfigGraphIdentity(
        id=stable_object_config_graph_identity_id(key=ocgi_key),
        key=ocgi_key,
        label=f"ocg:{ocgi_key}",
    )
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=uuid4(),
        name="environment",
        projection_hash="sha256:test:environment",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )

    opgi = synthesize_object_projection_graph_identity(
        object_config_graph_identity=ocgi,
        object_projection_graph=opg,
    )

    assert opgi.id == stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi.id,
        object_projection_graph_id=opg.id,
    )
    assert opgi.object_config_graph_identity_id == ocgi.id
    assert opgi.object_projection_graph_id == opg.id
    assert opgi.object_projection_graph is opg


def test_synthesize_object_instance_graph_identity_is_parent_scoped() -> None:
    ocgi_key = "aware_meta"
    ocgi = ObjectConfigGraphIdentity(
        id=stable_object_config_graph_identity_id(key=ocgi_key),
        key=ocgi_key,
        label=f"ocg:{ocgi_key}",
    )
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=uuid4(),
        name="environment",
        projection_hash="sha256:test:environment",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )
    opgi = synthesize_object_projection_graph_identity(
        object_config_graph_identity=ocgi,
        object_projection_graph=opg,
    )

    root_class_instance = ClassInstance(
        id=uuid4(),
        object_instance_graph_id=uuid4(),
        class_config_id=uuid4(),
        source_object_id=uuid4(),
    )
    oig = ObjectInstanceGraph(
        id=uuid4(),
        object_projection_graph_id=opg.id,
        key="environment-main",
        name="Environment Main",
        description=None,
        hash="",
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )

    oigi = synthesize_object_instance_graph_identity(
        object_projection_graph_identity=opgi,
        object_instance_graph=oig,
    )

    assert oigi.id == stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=oig.id,
    )
    assert oigi.object_projection_graph_identity_id == opgi.id
    assert oigi.object_instance_graph_id == oig.id
    assert oigi.object_instance_graph is oig
