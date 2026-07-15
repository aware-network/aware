from __future__ import annotations

from uuid import UUID

from aware_identity_ontology_orm_models.identity.identity import (
    Identity as IdentityOrmModel,
)


async def read_identity_from_identity_replica(*, identity_id: UUID) -> object | None:
    return await IdentityOrmModel.by_id(identity_id)


__all__ = ["read_identity_from_identity_replica"]
