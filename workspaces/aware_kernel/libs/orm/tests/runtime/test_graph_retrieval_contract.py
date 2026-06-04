from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import Field

from aware_orm.models.query_mixin import QueryMixin


class Profile(QueryMixin):
    name: str | None = None


class User(QueryMixin):
    name: str | None = None
    profiles: list[Profile] = Field(default_factory=list)


class IdentityMapSession:
    def __init__(self) -> None:
        self._branch_id = uuid4()
        self._objects: dict[tuple[type, UUID], QueryMixin] = {}

    def imap_get(self, cls, obj_id):  # type: ignore[no-untyped-def]
        return self._objects.get((cls, obj_id))

    def imap_add(self, instance):  # type: ignore[no-untyped-def]
        self._objects[(type(instance), instance.id)] = instance


def test_graph_hydration_reuses_nested_identity_map_instances(monkeypatch) -> None:
    session = IdentityMapSession()
    monkeypatch.setattr("aware_orm.session.current_session_ctx.current_session", lambda: session)

    profile_id = uuid4()
    cached_profile = Profile(id=profile_id, name="cached")
    session.imap_add(cached_profile)

    user = User._hydrate_object_graph(
        {
            "id": str(uuid4()),
            "name": "Ada",
            "profiles": [
                {
                    "id": str(profile_id),
                    "name": "hydrated",
                }
            ],
        }
    )

    assert user is not None
    assert user.profiles[0] is cached_profile
    assert cached_profile.name == "hydrated"
    assert session.imap_get(Profile, profile_id) is cached_profile
    assert session.imap_get(User, user.id) is user
