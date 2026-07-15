from __future__ import annotations

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[8]
_NETWORK_NODE_SOURCE = (
    _REPO_ROOT / "workspaces/aware_network/modules/network/ontology/structure/aware/network/network_node.aware"
)
_NETWORK_NODE_PROJECTION = (
    _REPO_ROOT
    / "workspaces/aware_network/modules/network/ontology/structure/aware/network/network_node_projection.aware"
)
_GENERATED_NETWORK_NODE = (
    _REPO_ROOT
    / "workspaces/aware_network/modules/network/ontology/structure/python/orm_runtime/aware_network_ontology/network/network_node.py"
)
_GENERATED_NETWORK_NODE_ORM = (
    _REPO_ROOT / "workspaces/aware_network/modules/network/ontology/structure/python/orm_models/"
    "aware_network_ontology_orm_models/network/network_node.py"
)


def test_network_node_declares_system_actor_portal_source_contract() -> None:
    source = _NETWORK_NODE_SOURCE.read_text(encoding="utf-8")
    projection = _NETWORK_NODE_PROJECTION.read_text(encoding="utf-8")

    assert "system_actor aware_identity.actor.Actor?" in source
    assert "Node bootstrap/self-registration is never actorless." in source
    assert "system_actor_id UUID? = null" in source
    assert "network.NetworkNode::system_actor aware_identity.Identity" in projection


def test_network_node_system_actor_portal_materializes_to_python_models() -> None:
    generated_network_node = _GENERATED_NETWORK_NODE.read_text(encoding="utf-8")
    generated_network_node_orm = _GENERATED_NETWORK_NODE_ORM.read_text(
        encoding="utf-8",
    )

    for generated in (generated_network_node, generated_network_node_orm):
        assert "system_actor: Actor | None = Field(" in generated
        assert "exclude=True" in generated
        assert "Node bootstrap/self-registration is never actorless." in generated
        assert "system_actor_id: UUID | None = Field(" in generated
        assert 'description="Foreign key for NetworkNode.system_actor"' in generated

    assert "system_actor_id: UUID | None = None" in generated_network_node
    assert "system_actor_id: UUID | None = Field(default=None)" in (generated_network_node)
