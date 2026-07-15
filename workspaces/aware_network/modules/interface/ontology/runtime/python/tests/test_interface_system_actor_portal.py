from __future__ import annotations

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[8]
_INTERFACE_SOURCE = _REPO_ROOT / "workspaces/aware_network/modules/interface/ontology/structure/aware/interface/interface.aware"
_INTERFACE_PROJECTION = _REPO_ROOT / "workspaces/aware_network/modules/interface/ontology/structure/aware/interface_projection.aware"
_GENERATED_INTERFACE = (
    _REPO_ROOT
    / "workspaces/aware_network/modules/interface/ontology/structure/python/orm_runtime/aware_interface_ontology/interface/interface.py"
)
_GENERATED_INTERFACE_ORM = (
    _REPO_ROOT / "workspaces/aware_network/modules/interface/ontology/structure/python/orm_models/"
    "aware_interface_ontology_orm_models/interface/interface.py"
)


def test_interface_declares_system_actor_portal_source_contract() -> None:
    source = _INTERFACE_SOURCE.read_text(encoding="utf-8")
    projection = _INTERFACE_PROJECTION.read_text(encoding="utf-8")

    assert "system_actor aware_identity.actor.Actor?" in source
    assert "Interface bootstrap/admission actions are never actorless." in source
    assert "interface.Interface::system_actor aware_identity.Identity" in projection


def test_interface_system_actor_portal_materializes_to_python_models() -> None:
    generated_interface = _GENERATED_INTERFACE.read_text(encoding="utf-8")
    generated_interface_orm = _GENERATED_INTERFACE_ORM.read_text(encoding="utf-8")

    for generated in (generated_interface, generated_interface_orm):
        assert "system_actor: Actor | None = Field(" in generated
        assert "exclude=True" in generated
        assert "Interface bootstrap/admission actions are never actorless." in generated
        assert "system_actor_id: UUID | None = Field(" in generated
        assert 'description="Foreign key for Interface.system_actor"' in generated
