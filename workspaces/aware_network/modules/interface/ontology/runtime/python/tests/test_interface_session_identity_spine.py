from __future__ import annotations

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[8]
_STRUCTURE_ROOT = (
    _REPO_ROOT / "workspaces/aware_network/modules/interface/ontology/structure"
)
_INTERFACE_SESSION_SOURCE = (
    _STRUCTURE_ROOT / "aware/interface/interface_session.aware"
)
_INTERFACE_SOURCE = _STRUCTURE_ROOT / "aware/interface/interface.aware"
_INTERFACE_IDENTITY_SOURCE = _STRUCTURE_ROOT / "aware/interface/interface_identity.aware"
_INTERFACE_SESSION_PROJECTION = (
    _STRUCTURE_ROOT / "aware/interface_session_projection.aware"
)
_INTERFACE_PROJECTION = _STRUCTURE_ROOT / "aware/interface_projection.aware"
_INTERFACE_IDENTITY_NETWORK_NODE_SOURCE = (
    _STRUCTURE_ROOT / "aware/interface/interface_identity_network_node.aware"
)
_REMOVED_NETWORK_BINDING_SOURCE = (
    _STRUCTURE_ROOT / "aware/interface/interface_session_network_binding.aware"
)
_REMOVED_GENERATED_NETWORK_BINDINGS = (
    _STRUCTURE_ROOT
    / "python/dto/aware_interface_ontology_dto/interface/interface_session_network_binding.py",
    _STRUCTURE_ROOT
    / "python/orm_models/aware_interface_ontology_orm_models/interface/interface_session_network_binding.py",
    _STRUCTURE_ROOT
    / "python/orm_runtime/aware_interface_ontology/interface/interface_session_network_binding.py",
    _STRUCTURE_ROOT / "sql/schema/interface/interface_session_network_binding.sql",
    _STRUCTURE_ROOT / "sql/sqlite/interface/interface_session_network_binding.sql",
)
_GENERATED_MODELS = (
    _STRUCTURE_ROOT
    / "python/orm_models/aware_interface_ontology_orm_models/interface/interface_session.py",
    _STRUCTURE_ROOT
    / "python/orm_runtime/aware_interface_ontology/interface/interface_session.py",
    _STRUCTURE_ROOT
    / "python/dto/aware_interface_ontology_dto/interface/interface_session.py",
)
_GENERATED_SQLITE = _STRUCTURE_ROOT / "sql/sqlite/interface/interface_session.sql"
_GENERATED_STABLE_IDS = _STRUCTURE_ROOT / "stable_ids.toml"
_GENERATED_STABLE_ID_MODULES = (
    _STRUCTURE_ROOT
    / "python/orm_models/aware_interface_ontology_orm_models/stable_ids.py",
    _STRUCTURE_ROOT
    / "python/orm_runtime/aware_interface_ontology/stable_ids.py",
    _STRUCTURE_ROOT
    / "python/dto/aware_interface_ontology_dto/stable_ids.py",
)


def test_interface_session_declares_explicit_identity_session_portal() -> None:
    source = _INTERFACE_SESSION_SOURCE.read_text(encoding="utf-8")
    interface_source = _INTERFACE_SOURCE.read_text(encoding="utf-8")
    interface_identity_source = _INTERFACE_IDENTITY_SOURCE.read_text(encoding="utf-8")

    assert "identity_session aware_identity.session.Session key" in source
    assert "Identity Session owns participation, membership, ActorRole evidence" in source
    assert "InterfaceSession owns only renderer/device attachment state." in source
    assert "Many InterfaceSessions may attach to the same Identity Session." in source
    assert "ann interface.InterfaceSession::identity_session load eager" in source
    assert "fn build construct (" in source
    assert "identity_session_id UUID key" in source
    assert "not parented by one InterfaceIdentity" in source
    assert "interface_sessions InterfaceSession[]" not in interface_identity_source
    assert "fn start_session (" in interface_source
    assert "construct interface_sessions.build(" in interface_source
    assert "interface_identity_id" not in interface_source.split("fn start_session (", 1)[1].split(
        "fn set_active_window_navigation_context", 1
    )[0]


def test_interface_session_has_commit_projection_without_transport_state() -> None:
    session_projection = _INTERFACE_SESSION_PROJECTION.read_text(encoding="utf-8")
    interface_projection = _INTERFACE_PROJECTION.read_text(encoding="utf-8")

    assert "projection InterfaceSession" in session_projection
    assert "root interface.InterfaceSession" in session_projection
    assert (
        "interface.InterfaceSession::identity_session aware_identity.Session"
        in session_projection
    )
    assert "observable session" in session_projection
    assert "interface.Interface::interface_sessions InterfaceSession" in interface_projection
    assert "bearer tokens are ephemeral transport state" in session_projection


def test_ephemeral_transport_binding_is_not_interface_ontology() -> None:
    identity_network_node = _INTERFACE_IDENTITY_NETWORK_NODE_SOURCE.read_text(
        encoding="utf-8"
    )
    stable_ids = _GENERATED_STABLE_IDS.read_text(encoding="utf-8")

    assert not _REMOVED_NETWORK_BINDING_SOURCE.exists()
    assert "session_bindings" not in identity_network_node
    assert "InterfaceSessionNetworkBinding" not in identity_network_node
    assert "stable_interface_session_network_binding_id" not in stable_ids
    for path in _REMOVED_GENERATED_NETWORK_BINDINGS:
        assert not path.exists()
    for path in _GENERATED_STABLE_ID_MODULES:
        assert "stable_interface_session_network_binding_id" not in path.read_text(
            encoding="utf-8"
        )


def test_interface_session_identity_portal_materializes_to_python_models() -> None:
    for path in _GENERATED_MODELS:
        generated = path.read_text(encoding="utf-8")

        assert "from aware_identity_ontology" in generated
        assert "session.session import Session" in generated
        assert "identity_session: Session" in generated

        if "dto" not in path.parts:
            assert "identity_session_id: UUID = Field(" in generated
            assert 'description="Foreign key for InterfaceSession.identity_session"' in generated


def test_interface_session_identity_includes_canonical_session() -> None:
    sqlite = _GENERATED_SQLITE.read_text(encoding="utf-8")
    stable_ids = _GENERATED_STABLE_IDS.read_text(encoding="utf-8")

    assert "identity_session_id TEXT NOT NULL" in sqlite
    assert (
        "UNIQUE (branch_id, projection_hash, interface_id, name, identity_session_id)"
    ) in sqlite

    assert (
        'template = "aware:interface_session:{interface_id}:{identity_session_id}:{name_norm}"'
        in stable_ids
    )
    assert (
        'doc = "Compiler-generated from class-attribute identity keys: '
        'interface_id, identity_session_id, name"'
    ) in stable_ids

    for path in _GENERATED_STABLE_ID_MODULES:
        generated = path.read_text(encoding="utf-8")
        assert (
            "def stable_interface_session_id(*, interface_id: UUID, "
            "identity_session_id: UUID, name: str) -> UUID:"
        ) in generated
        assert (
            'f"aware:interface_session:{interface_id}:{identity_session_id}:{name_norm}"'
            in generated
        )
