from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity.meta_runtime import IdentityMetaRuntimeLaneBinder
from aware_identity_ontology.identity.create_profile_request import CreateProfileRequest
from aware_identity_ontology.identity.identity import Identity
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_identity_id,
    stable_identity_profile_id,
)


@dataclass(frozen=True, slots=True)
class IdentityAdmissionOperationContext:
    actor_id: UUID


@dataclass(frozen=True, slots=True)
class IdentityAdmissionRuntimeContext:
    lane_binder: IdentityMetaRuntimeLaneBinder


@dataclass(frozen=True, slots=True)
class IdentityAdmissionRuntimeRequest:
    public_key: str
    create_profile_request: CreateProfileRequest


@dataclass(frozen=True, slots=True)
class IdentityAdmissionRuntimeReceipt:
    identity_id: UUID
    actor_id: UUID
    identity_profile_id: UUID
    public_handle: str
    info: str


def resolve_identity_admission_runtime_context(
    *,
    lane_binder: IdentityMetaRuntimeLaneBinder,
) -> IdentityAdmissionRuntimeContext:
    return IdentityAdmissionRuntimeContext(lane_binder=lane_binder)


async def admit_identity_via_profile(
    *,
    runtime_context: IdentityAdmissionRuntimeContext,
    operation_context: IdentityAdmissionOperationContext,
    request: IdentityAdmissionRuntimeRequest,
) -> IdentityAdmissionRuntimeReceipt:
    canonical_public_key, _ = canonicalize_ed25519_public_key(request.public_key)
    identity_id = stable_identity_id(
        public_key=canonical_public_key,
        type=request.create_profile_request.identity_type.value,
    )
    lane = runtime_context.lane_binder.bind(
        projection="Identity",
        branch_id=identity_id,
        actor_id=operation_context.actor_id,
    )
    with lane.activate():
        identity = await Identity.signup_via_profile(
            public_key=canonical_public_key,
            create_profile_request=request.create_profile_request,
            type=request.create_profile_request.identity_type,
        )
    if identity.id != identity_id:
        raise ValueError(
            "identity.signup_via_profile returned an unexpected identity id: "
            + f"expected={identity_id} actual={identity.id}"
        )
    return IdentityAdmissionRuntimeReceipt(
        identity_id=identity_id,
        actor_id=stable_actor_id(identity_id=identity_id),
        identity_profile_id=stable_identity_profile_id(
            public_handle=request.create_profile_request.public_handle
        ),
        public_handle=request.create_profile_request.public_handle,
        info="identity admission completed via signup_via_profile",
    )
