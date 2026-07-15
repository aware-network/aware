"""
ACL repository for the network node.

Provides helpers to resolve which roles and object instances are accessible
to a given identity, including delegated role grants, using the ORM APIs so the
underlying persistence backend (DB or filesystem) remains transparent.

# !! TODO: MOVE TO ACL PROPERLY - COMMON AT AWARE IDENTITY PACKAGE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional
from uuid import UUID

from aware_identity_ontology.actor.actor_role import ActorRole
from aware_identity_ontology.role.role import Role
from aware_orm.filters import EqFilter, InFilter


@dataclass(frozen=True)
class IdentityRoleEntry:
    identity_role: ActorRole

    @property
    def id(self) -> UUID:
        return self.identity_role.id

    @property
    def identity_id(self) -> UUID:
        return self.identity_role.identity_id  # type: ignore[return-value]

    @property
    def role_id(self) -> UUID:
        return self.identity_role.role_id  # type: ignore[return-value]


@dataclass(frozen=True)
class RoleGrantEntry:
    grant: Role

    @property
    def id(self) -> UUID:
        return self.grant.id

    @property
    def grantee_identity_role_id(self) -> Optional[UUID]:
        return self.grant.grantee_role_id

    @property
    def granter_identity_role_id(self) -> Optional[UUID]:
        return self.grant.granter_role_id

    @property
    def expires_at(self) -> Optional[datetime]:
        return self.grant.expires_at


class NetworkAclRepository:
    """Utility repository that resolves identity roles, role coverage, and grants."""

    def __init__(self, reference_time: Optional[datetime] = None):
        self.reference_time = reference_time or datetime.now(timezone.utc)

    async def list_actor_roles(self, actor_id: UUID) -> list[IdentityRoleEntry]:
        roles = (
            await ActorRole.query()
            .where(EqFilter(column="actor_id", value=str(actor_id)))
            .all()
        )
        return [IdentityRoleEntry(role) for role in roles]

    async def list_actor_roles_by_id(
        self, actor_role_ids: Iterable[UUID]
    ) -> list[IdentityRoleEntry]:
        ids = [str(rid) for rid in actor_role_ids]
        if not ids:
            return []
        roles = await ActorRole.query().where(InFilter(column="id", values=ids)).all()
        return [IdentityRoleEntry(role) for role in roles]

    async def list_role_object_instances(
        self, role_ids: Iterable[UUID]
    ) -> dict[UUID, set[UUID]]:
        ids = [str(rid) for rid in role_ids]
        if not ids:
            return {}
        roles = await Role.query().where(InFilter(column="role_id", values=ids)).all()
        # !! TODO: Clarify how to get from JOIN as is not materialized at Python -> we want the Join RoleClassInstance.
        coverage: dict[UUID, set[UUID]] = {}
        for role in roles:
            for class_instance in role.class_instances:
                coverage.setdefault(role.id, set()).add(class_instance.id)
        return coverage

    async def resolve_actor_access(self, actor_id: UUID) -> dict[str, set[UUID]]:
        """
        Resolve object instance coverage for an identity, including delegated roles.

        Returns a dict with keys:
            - actor_role_ids: set of UUIDs
            - delegated_role_ids: set of UUIDs
            - accessible_class_instance_ids: set of UUIDs
        """
        direct_roles = await self.list_actor_roles(actor_id)
        actor_role_ids = {entry.id for entry in direct_roles}
        direct_role_ids = {entry.role_id for entry in direct_roles}

        coverage = await self.list_role_object_instances(direct_role_ids)
        accessible_class_instance_ids = {
            obj for objs in coverage.values() for obj in objs
        }

        # !! TODO: ENABLE FUTURE
        # delegated_role_ids = self.fetch_delegated_roles(identity_role_ids)
        delegated_role_ids = set()

        return {
            "actor_role_ids": actor_role_ids,
            "delegated_role_ids": delegated_role_ids,
            "accessible_class_instance_ids": accessible_class_instance_ids,
        }

    async def fetch_delegated_roles(
        self, actor_role_ids: Iterable[UUID]
    ) -> list[RoleGrantEntry]:
        delegated_class_instance_ids = set()
        # Fetch delegated roles
        active_grants = await self.list_active_role_grants(actor_role_ids)
        delegated_actor_role_ids = {
            grant.granter_actor_role_id
            for grant in active_grants
            if grant.granter_actor_role_id
        }

        if delegated_actor_role_ids:
            delegated_roles = await self.list_actor_roles_by_id(
                delegated_actor_role_ids
            )
            delegated_actor_role_ids = {entry.role_id for entry in delegated_roles}
            if delegated_actor_role_ids:
                delegated_coverage = await self.list_role_object_instances(
                    delegated_actor_role_ids
                )
                for class_instances in delegated_coverage.values():
                    for class_instance in class_instances:
                        delegated_class_instance_ids.add(class_instance)
            else:
                return []
        else:
            return []
        return delegated_class_instance_ids

    # async def list_active_role_grants(self, identity_role_ids: Iterable[UUID]) -> list[RoleGrantEntry]:
    #     ids = [str(rid) for rid in identity_role_ids]
    #     if not ids:
    #         return []
    #     filters = [InFilter(column="grantee_identity_role_id", values=ids)]
    #     grants = await Role.query().where(*filters).all()
    #     active: list[RoleGrantEntry] = []
    #     for grant in grants:
    #         expires_at = grant.expires_at
    #         if expires_at and expires_at <= self.reference_time:
    #             continue
    #         active.append(RoleGrantEntry(grant))
    #     return active
