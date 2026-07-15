from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.credential.credential_profile_enums import CredentialSecretResolverKind

# Types
from aware_types import JsonObject


class CredentialSecretMaterialRef(BaseModel):
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
