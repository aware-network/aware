from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.credential.credential_profile_enums import CredentialSecretResolverKind

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class CredentialSecretMaterialRef(ORMModel):
    """
    Reference to secret material held outside canonical commits.
    Contract:
    - Secret values are never stored here.
    - `secret_name` is the resolver key, not the secret value.
    - `fingerprint_sha256` may record a digest of the external material when the
    resolver can calculate one without exposing the material.
    """

    # Attributes
    secret_ref_key: str
    resolver_kind: CredentialSecretResolverKind
    secret_name: str
    locator: str | None = Field(default=None)
    username_hint: str | None = Field(default=None)
    material_hint: str | None = Field(default=None)
    fingerprint_sha256: str | None = Field(default=None)
    created_at_utc: str | None = Field(default=None)
    rotated_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)

    # Foreign Keys
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.secret_material_refs")
