from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.organization.organization_enums import OrganizationMemberRole
from aware_identity_ontology.organization.organization import Organization
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


async def create(actor_id: UUID) -> Organization:
    """
    Construct a Organization - Identity resolves profile
    """

    # --- AWARE: LOGIC START create
    actor_id = actor_id if isinstance(actor_id, UUID) else UUID(str(actor_id))
    actual_actor_id = current_actor_id()
    if actual_actor_id != actor_id:
        raise ValueError(
            "forbidden: Organization.create requires actor_id to match caller (anti-claim): "
            f"actor_id={actor_id} actual_actor_id={actual_actor_id}"
        )

    organization_id = stable_organization_id(actor_id=actor_id)

    actual_branch_id = current_branch_id()
    if actual_branch_id != organization_id:
        raise ValueError(
            "forbidden: Organization.create requires branch_id to match stable Organization.id: "
            f"branch_id={actual_branch_id} expected={organization_id}"
        )

    return Organization(id=organization_id, actor_id=actor_id)
    # --- AWARE: LOGIC END create


async def create_member(
    organization: Organization, identity_id: UUID, role: OrganizationMemberRole
) -> OrganizationMember:
    """
    Create a member at an organization
    """

    # --- AWARE: LOGIC START create_member
    if organization.id is None:
        raise ValueError("Organization.create_member requires organization.id")
    organization_id = organization.id if isinstance(organization.id, UUID) else UUID(str(organization.id))
    identity_id = identity_id if isinstance(identity_id, UUID) else UUID(str(identity_id))

    member_id = stable_organization_member_id(
        organization_id=organization_id,
        identity_id=identity_id,
    )
    for existing in organization.members:
        if existing.id == member_id:
            if existing.role != role:
                existing.role = role
            return existing

    member = await OrganizationMember.create_via_organization(
        organization_id=organization_id,
        identity_id=identity_id,
        role=role,
    )
    organization.members.append(member)
    return member
    # --- AWARE: LOGIC END create_member
