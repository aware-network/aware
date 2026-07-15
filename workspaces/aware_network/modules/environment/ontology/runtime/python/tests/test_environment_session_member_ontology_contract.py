from ._environment_runtime_test_paths import ENVIRONMENT_AWARE


ENVIRONMENT_SOURCE = ENVIRONMENT_AWARE / "environment"
SESSION_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_session_projection.aware"


def test_environment_session_member_ontology_files_are_removed() -> None:
    assert not (ENVIRONMENT_SOURCE / "environment_session_member.aware").exists()
    assert not (
        ENVIRONMENT_SOURCE / "environment_session_member_actor_role.aware"
    ).exists()


def test_environment_session_has_no_member_or_actor_role_relationships() -> None:
    source = (ENVIRONMENT_SOURCE / "environment_session.aware").read_text()
    projection_source = SESSION_PROJECTION_SOURCE.read_text(encoding="utf-8")

    forbidden_tokens = (
        "EnvironmentSessionMember",
        "EnvironmentSessionMemberActorRole",
        "members EnvironmentSessionMember[]",
        "actor_roles EnvironmentSessionMemberActorRole[]",
        "fn join_actor",
    )
    for token in forbidden_tokens:
        assert token not in source
        assert token not in projection_source


def test_environment_session_authority_is_identity_session_portal() -> None:
    source = (ENVIRONMENT_SOURCE / "environment_session.aware").read_text()
    projection_source = SESSION_PROJECTION_SOURCE.read_text(encoding="utf-8")

    assert "identity_session aware_identity.session.Session key" in source
    assert "identity_session_id UUID key" in source
    assert (
        "environment.EnvironmentSession::identity_session aware_identity.Session"
        in projection_source
    )
