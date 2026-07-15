from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import (
    CredentialKind,
    CredentialProfileStatus,
    CredentialTargetKind,
)
from aware_identity_ontology.identity.identity_enums import IdentityType
from aware_identity_ontology.identity.identity_pattern_enums import IdentityPatternType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor import Actor
    from aware_identity_ontology.credential.credential_profile import CredentialProfile
    from aware_identity_ontology.human.human import Human
    from aware_identity_ontology.identity.create_profile_request import CreateProfileRequest
    from aware_identity_ontology.identity.identity_pattern import IdentityPattern
    from aware_identity_ontology.identity.identity_profile import IdentityProfile
    from aware_identity_ontology.organization.organization import Organization


class Identity(ORMModel):
    # Relationships
    human: Human | None = Field(default=None, exclude=True)
    organization: Organization | None = Field(default=None, exclude=True)
    identity_patterns: list[IdentityPattern] = Field(default_factory=list, exclude=True)
    identity_profile: IdentityProfile | None = Field(default=None, exclude=True)
    credential_profiles: list[CredentialProfile] = Field(default_factory=list, exclude=True)

    # Attributes
    public_key: str
    type: IdentityType

    # Foreign Keys
    human_id: UUID | None = Field(default=None, description="Foreign key for Identity.human")
    organization_id: UUID | None = Field(default=None, description="Foreign key for Identity.organization")
    identity_profile_id: UUID | None = Field(default=None, description="Foreign key for Identity.identity_profile")

    @classmethod
    async def signup(cls, public_key: str, type: IdentityType = IdentityType.human) -> Identity:
        """
        Canonical identity signup (v0).

        This is the first end-to-end identity mutation:
        `.aware` → runtime handler → OIG delta → OIG commit → UI materialization.

        Notes:
        - Signup is a state mutation and must always be commit-backed (no transport-only identity creation).
        - The public key is the canonical identity anchor (human + AI).
        """

        payload = {"public_key": public_key, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="signup", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Identity):
            return value
        return Identity.validate_invocation_value(value)

    @classmethod
    async def signup_via_profile(
        cls, public_key: str, create_profile_request: CreateProfileRequest, type: IdentityType = IdentityType.human
    ) -> Identity:
        """
        Creates identity and profile in a single commit (canonical onboarding).

        Contract:
        - public_key is device-generated; runtime canonicalizes and derives stable ids.
        - idempotent by public key (stable Identity.id).
        - profile handle is unique (stable IdentityProfile.id).
        """

        payload = {"public_key": public_key, "create_profile_request": create_profile_request, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="signup_via_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Identity):
            return value
        return Identity.validate_invocation_value(value)

    async def create_profile(
        self,
        public_handle: str,
        display_name: str,
        full_name: str,
        country_code: str,
        language_code: str,
        bio: str | None = None,
        image_id: UUID | None = None,
    ) -> IdentityProfile:
        """
        Creates and links a profile to this Identity (v0).

        Runtime invariants:
        - Mutate-self-only: this handler may only mutate the Identity instance.
        - Profile creation must occur via the IdentityProfile constructor handler (propagation).
        """

        payload = {
            "public_handle": public_handle,
            "display_name": display_name,
            "full_name": full_name,
            "country_code": country_code,
            "language_code": language_code,
            "bio": bio,
            "image_id": image_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.identity.identity_profile import IdentityProfile

        if isinstance(value, IdentityProfile):
            return value
        return IdentityProfile.validate_invocation_value(value)

    async def ensure_actor(self, key: str = "default") -> Actor:
        """
        Ensure an Actor instance exists for this Identity.

        Contract:
        - `IdentityType.agent` may own multiple keyed actors (deterministic by key).
        - `IdentityType.human`/`organization`/`system` remain 1:1 and only allow `key=default`.
        - Returns existing actor when the deterministic id already exists.
        """

        payload = {"key": key}
        result = await invoke_instance(orm_model=self, function_name="ensure_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.actor.actor import Actor

        if isinstance(value, Actor):
            return value
        return Actor.validate_invocation_value(value)

    async def create_credential_profile(
        self,
        profile_key: str,
        target_kind: CredentialTargetKind = CredentialTargetKind.aware_api,
        credential_kind: CredentialKind = CredentialKind.api_key,
        status: CredentialProfileStatus = CredentialProfileStatus.planned,
        display_name: str | None = None,
        target_name: str | None = None,
        issuer: str | None = None,
        audience: str | None = None,
        external_subject: str | None = None,
        created_at_utc: str | None = None,
        updated_at_utc: str | None = None,
        expires_at_utc: str | None = None,
        revoked_at_utc: str | None = None,
        metadata: JsonObject | None = None,
    ) -> CredentialProfile:
        """
        Create one Identity-owned credential profile.

        Contract:
        - Parent Identity context is propagated by traversal.
        - Organizations use Identity.type=organization on this same rail.
        - Secret values are never stored on this object.
        - Secret material is resolved through profile-owned refs.
        """

        payload = {
            "profile_key": profile_key,
            "target_kind": target_kind,
            "credential_kind": credential_kind,
            "status": status,
            "display_name": display_name,
            "target_name": target_name,
            "issuer": issuer,
            "audience": audience,
            "external_subject": external_subject,
            "created_at_utc": created_at_utc,
            "updated_at_utc": updated_at_utc,
            "expires_at_utc": expires_at_utc,
            "revoked_at_utc": revoked_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="create_credential_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.credential.credential_profile import CredentialProfile

        if isinstance(value, CredentialProfile):
            return value
        return CredentialProfile.validate_invocation_value(value)

    async def find_relevant_patterns(
        self,
        category: str | None = None,
        pattern_type: IdentityPatternType | None = None,
        min_confidence: float | None = 0.0,
    ) -> None:
        """Experimentally finds relevant patterns for an identity."""

        payload = {"category": category, "pattern_type": pattern_type, "min_confidence": min_confidence}
        await invoke_instance(orm_model=self, function_name="find_relevant_patterns", payload=payload)
        return None


class IdentitySignupInput(BaseModel):
    public_key: str
    type: IdentityType = Field(default=IdentityType.human)


class IdentitySignupOutput(BaseModel):
    value: Identity


class IdentitySignupViaProfileInput(BaseModel):
    public_key: str
    create_profile_request: CreateProfileRequest
    type: IdentityType = Field(default=IdentityType.human)


class IdentitySignupViaProfileOutput(BaseModel):
    value: Identity


class IdentityCreateProfileInput(BaseModel):
    public_handle: str
    display_name: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)
    image_id: UUID | None = Field(default=None)


class IdentityCreateProfileOutput(BaseModel):
    value: IdentityProfile


class IdentityEnsureActorInput(BaseModel):
    key: str = Field(default="default")


class IdentityEnsureActorOutput(BaseModel):
    value: Actor


class IdentityCreateCredentialProfileInput(BaseModel):
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


class IdentityCreateCredentialProfileOutput(BaseModel):
    value: CredentialProfile


class IdentityFindRelevantPatternsInput(BaseModel):
    category: str | None = Field(default=None)
    pattern_type: IdentityPatternType | None = Field(default=None)
    min_confidence: float | None = Field(default=0.0)


class IdentityFindRelevantPatternsOutput(BaseModel):
    pass


FUNCTIONS = {
    "Identity": {
        "signup": {
            "canonical": {
                "name": "signup",
                "description": "Canonical identity signup (v0).\n\nThis is the first end-to-end identity mutation:\n`.aware` → runtime handler → OIG delta → OIG commit → UI materialization.\n\nNotes:\n- Signup is a state mutation and must always be commit-backed (no transport-only identity creation).\n- The public key is the canonical identity anchor (human + AI).",
                "is_constructor": True,
            },
            "input": IdentitySignupInput,
            "output": IdentitySignupOutput,
        },
        "signup_via_profile": {
            "canonical": {
                "name": "signup_via_profile",
                "description": "Creates identity and profile in a single commit (canonical onboarding).\n\nContract:\n- public_key is device-generated; runtime canonicalizes and derives stable ids.\n- idempotent by public key (stable Identity.id).\n- profile handle is unique (stable IdentityProfile.id).",
                "is_constructor": True,
            },
            "input": IdentitySignupViaProfileInput,
            "output": IdentitySignupViaProfileOutput,
        },
        "create_profile": {
            "canonical": {
                "name": "create_profile",
                "description": "Creates and links a profile to this Identity (v0).\n\nRuntime invariants:\n- Mutate-self-only: this handler may only mutate the Identity instance.\n- Profile creation must occur via the IdentityProfile constructor handler (propagation).",
                "is_constructor": False,
            },
            "input": IdentityCreateProfileInput,
            "output": IdentityCreateProfileOutput,
        },
        "ensure_actor": {
            "canonical": {
                "name": "ensure_actor",
                "description": "Ensure an Actor instance exists for this Identity.\n\nContract:\n- `IdentityType.agent` may own multiple keyed actors (deterministic by key).\n- `IdentityType.human`/`organization`/`system` remain 1:1 and only allow `key=default`.\n- Returns existing actor when the deterministic id already exists.",
                "is_constructor": False,
            },
            "input": IdentityEnsureActorInput,
            "output": IdentityEnsureActorOutput,
        },
        "create_credential_profile": {
            "canonical": {
                "name": "create_credential_profile",
                "description": "Create one Identity-owned credential profile.\n\nContract:\n- Parent Identity context is propagated by traversal.\n- Organizations use Identity.type=organization on this same rail.\n- Secret values are never stored on this object.\n- Secret material is resolved through profile-owned refs.",
                "is_constructor": False,
            },
            "input": IdentityCreateCredentialProfileInput,
            "output": IdentityCreateCredentialProfileOutput,
        },
        "find_relevant_patterns": {
            "canonical": {
                "name": "find_relevant_patterns",
                "description": "Experimentally finds relevant patterns for an identity.",
                "is_constructor": False,
            },
            "input": IdentityFindRelevantPatternsInput,
            "output": IdentityFindRelevantPatternsOutput,
        },
    },
}

__all__ = [
    "Identity",
    "IdentitySignupInput",
    "IdentitySignupOutput",
    "IdentitySignupViaProfileInput",
    "IdentitySignupViaProfileOutput",
    "IdentityCreateProfileInput",
    "IdentityCreateProfileOutput",
    "IdentityEnsureActorInput",
    "IdentityEnsureActorOutput",
    "IdentityCreateCredentialProfileInput",
    "IdentityCreateCredentialProfileOutput",
    "IdentityFindRelevantPatternsInput",
    "IdentityFindRelevantPatternsOutput",
    "FUNCTIONS",
]
