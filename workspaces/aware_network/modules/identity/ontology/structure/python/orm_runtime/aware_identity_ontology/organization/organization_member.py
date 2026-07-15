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
from aware_identity_ontology.organization.organization_enums import OrganizationMemberRole

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_identity_ontology.identity.identity import Identity


class OrganizationMember(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)

    # Attributes
    role: OrganizationMemberRole

    # Foreign Keys
    organization_id: UUID = Field(description="Foreign key for Organization.members")
    identity_id: UUID = Field(description="Foreign key for OrganizationMember.identity")

    @classmethod
    async def create_via_organization(
        cls, organization_id: UUID, identity_id: UUID, role: OrganizationMemberRole
    ) -> OrganizationMember:
        """
        Construct a organization member
        TODO: CLARIFY ROLES must come via Role-Actor ACL.
        WARNING: This table must evolve towards a proper ROLE over ORGANIZATION
        """

        payload = {"organization_id": organization_id, "identity_id": identity_id, "role": role}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_organization", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, OrganizationMember):
            return value
        return OrganizationMember.validate_invocation_value(value)


class OrganizationMemberCreateViaOrganizationInput(BaseModel):
    organization_id: UUID = Field(description="Foreign key for Organization.members")
    identity_id: UUID
    role: OrganizationMemberRole


class OrganizationMemberCreateViaOrganizationOutput(BaseModel):
    value: OrganizationMember


FUNCTIONS = {
    "OrganizationMember": {
        "create_via_organization": {
            "canonical": {
                "name": "create_via_organization",
                "description": "Construct a organization member\nTODO: CLARIFY ROLES must come via Role-Actor ACL.\nWARNING: This table must evolve towards a proper ROLE over ORGANIZATION",
                "is_constructor": True,
            },
            "input": OrganizationMemberCreateViaOrganizationInput,
            "output": OrganizationMemberCreateViaOrganizationOutput,
        },
    },
}

__all__ = [
    "OrganizationMember",
    "OrganizationMemberCreateViaOrganizationInput",
    "OrganizationMemberCreateViaOrganizationOutput",
    "FUNCTIONS",
]
