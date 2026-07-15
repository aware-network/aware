from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.organization.organization_enums import OrganizationMemberRole
from aware_identity_ontology.organization.organization_member import OrganizationMember

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Identity Runtime
from aware_identity.context import current_actor_id, current_branch_id
from aware_identity_ontology.stable_ids import (
    stable_organization_id,
    stable_organization_member_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_organization(
    organization_id: UUID, identity_id: UUID, role: OrganizationMemberRole
) -> OrganizationMember:
    """
    Construct a organization member
    TODO: CLARIFY ROLES must come via Role-Actor ACL.
    WARNING: This table must evolve towards a proper ROLE over ORGANIZATION
    """

    # --- AWARE: LOGIC START create_via_organization
    organization_id = organization_id if isinstance(organization_id, UUID) else UUID(str(organization_id))
    identity_id = identity_id if isinstance(identity_id, UUID) else UUID(str(identity_id))
    actor_id = current_actor_id()
    expected_organization_id = stable_organization_id(actor_id=actor_id)
    if organization_id != expected_organization_id:
        raise ValueError(
            "forbidden: OrganizationMember.create requires caller to be the organization actor (anti-claim): "
            f"organization_id={organization_id} expected_organization_id={expected_organization_id} actor_id={actor_id}"
        )

    actual_branch_id = current_branch_id()
    if actual_branch_id != organization_id:
        raise ValueError(
            "forbidden: OrganizationMember.create requires branch_id to match organization_id: "
            f"branch_id={actual_branch_id} organization_id={organization_id}"
        )

    member_id = stable_organization_member_id(
        organization_id=organization_id,
        identity_id=identity_id,
    )
    return OrganizationMember(
        id=member_id,
        organization_id=organization_id,
        identity_id=identity_id,
        role=role,
    )
    # --- AWARE: LOGIC END create_via_organization
