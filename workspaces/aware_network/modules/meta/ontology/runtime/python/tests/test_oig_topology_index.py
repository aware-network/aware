from __future__ import annotations

from uuid import uuid4

from aware_meta.graph.support.index import build_index

from aware_meta_ontology import _bootstrap_models
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

from aware_meta.graph.instance.member import ObjectInstanceGraphMember
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind
from aware_meta.graph.instance.topology import ObjectInstanceGraphTopology
from aware_meta.test_support import make_class_config, test_class_fqn


def _build_minimal_oig() -> ObjectInstanceGraph:
    """Construct a minimal ObjectInstanceGraph suitable for topology/index tests."""
    _bootstrap_models()
    graph_id = uuid4()
    # Class config / instance (use model_construct to avoid forward-ref validation noise)
    cls_cfg = make_class_config(
        "User",
        class_fqn=test_class_fqn("User"),
        description=None,
        parent_class_id=None,
    )

    cls_inst = ClassInstance(
        object_instance_graph_id=graph_id,
        class_config=cls_cfg,
        class_config_id=cls_cfg.id,
        source_object_id=uuid4(),
    )

    # Relationship: simple self-edge for testing
    rel = ClassInstanceRelationship(
        object_instance_graph_id=graph_id,
        class_config_relationship_id=uuid4(),
        source_class_instance_id=cls_inst.id,
        target_class_instance_id=cls_inst.id,
    )

    graph = ObjectInstanceGraph(
        key="test-graph",
        root_class_instance=cls_inst,
        class_instances=[cls_inst],
        class_instance_relationships=[rel],
        description="Test graph",
        hash="0",
        name="TestGraph",
        id=graph_id,
        object_projection_graph_id=uuid4(),
        root_class_instance_id=cls_inst.id,
    )
    return graph


def test_oig_topology_and_index_paths():
    _bootstrap_models()
    graph = _build_minimal_oig()

    root_member = ObjectInstanceGraphMember(object_instance_graph=graph)
    topology = ObjectInstanceGraphTopology()

    index = build_index(root_member, topology)
    paths = index.get_all_paths()

    # Collect a simple view: {segment_tuple: (entity_type_name, kind)}
    simplified = {
        path: (type(entity).__name__, kind) for path, (entity, kind) in paths.items()
    }

    # Root path (canonical: graph identity is by id, not name)
    root_path = (f"graph:{graph.id}",)
    assert root_path in simplified
    root_entity_name, root_kind = simplified[root_path]
    assert root_entity_name == "ObjectInstanceGraphMember"
    assert root_kind == ObjectInstanceGraphMemberKind.object_instance_graph

    # There should be at least one ClassInstanceMember and one Relationship member indexed
    instance_paths = [
        (p, info) for p, info in simplified.items() if info[0] == "ClassInstanceMember"
    ]
    assert instance_paths, "Expected at least one ClassInstanceMember in index"

    relationship_paths = [
        (p, info)
        for p, info in simplified.items()
        if info[0] == "ClassInstanceRelationshipMember"
    ]
    assert relationship_paths, "Expected ClassInstanceRelationshipMember in index"

    # Instance path should be rooted under the graph path
    inst_path, (inst_name, inst_kind) = instance_paths[0]
    assert inst_path[0] == root_path[0]
    assert inst_kind == ObjectInstanceGraphMemberKind.class_instance

    # Relationship path should be rooted under the graph path and use the expected kind
    rel_path, (rel_name, rel_kind) = relationship_paths[0]
    assert rel_path[0] == root_path[0]
    assert rel_kind == ObjectInstanceGraphMemberKind.relationship_instance
