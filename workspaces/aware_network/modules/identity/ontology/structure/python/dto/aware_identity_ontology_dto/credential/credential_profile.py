from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.credential.credential_profile_enums import (
    CredentialKind,
    CredentialProfileStatus,
    CredentialTargetKind,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.credential.credential_grant import CredentialGrant
    from aware_identity_ontology_dto.credential.credential_readiness_receipt import CredentialReadinessReceipt
    from aware_identity_ontology_dto.credential.credential_secret_material_ref import CredentialSecretMaterialRef
    from aware_identity_ontology_dto.credential.credential_usage_receipt import CredentialUsageReceipt


class CredentialProfile(BaseModel):
    """
    Identity-owned credential authority for API keys, publish credentials, and
    external auth rails.
    Contract:
    - This is the public credential/API key model for Identity.
    - Secret material is represented only through CredentialSecretMaterialRef.
    - A profile is contained by Identity; organizations are Identity instances.
    - Parent identity context is propagated by construct traversal.
    """

    # Relationships
    secret_material_refs: list[CredentialSecretMaterialRef] = Field(default_factory=list)
    grants: list[CredentialGrant] = Field(default_factory=list)
    readiness_receipts: list[CredentialReadinessReceipt] = Field(default_factory=list)
    usage_receipts: list[CredentialUsageReceipt] = Field(default_factory=list)

    # Attributes
    profile_key: str
    target_kind: CredentialTargetKind = Field(default=CredentialTargetKind.aware_api)
    credential_kind: CredentialKind = Field(default=CredentialKind.api_key)
    status: CredentialProfileStatus = Field(default=CredentialProfileStatus.planned)
    display_name: str | None = Field(default=None)
    target_name: str | None = Field(default=None)
    issuer: str | None = Field(default=None)
    audience: str | None = Field(default=None)
    external_subject: str | None = Field(default=None)
    created_at_utc: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    revoked_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)
