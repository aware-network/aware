from __future__ import annotations

from uuid import UUID, uuid5

# Stable global namespace for roles
NS_AWARE = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
NS_ROLE = uuid5(NS_AWARE, "role")


class RoleCatalog:
    _name_to_id: dict[str, UUID] = {}

    @classmethod
    def register(cls, role_key: str) -> UUID:
        rid = uuid5(NS_ROLE, role_key)
        cls._name_to_id.setdefault(role_key, rid)
        return rid

    @classmethod
    def resolve(cls, role_key: str) -> UUID:
        existing = cls._name_to_id.get(role_key)
        if existing is not None:
            return existing
        return cls.register(role_key)
