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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor import Actor
    from aware_identity_ontology.organization.organization_member import OrganizationMember


class Organization(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    members: list[OrganizationMember] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Organization.actor")

    @classmethod
    async def create(cls, actor_id: UUID) -> Organization:
        """Construct a Organization - Identity resolves profile"""

        payload = {"actor_id": actor_id}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Organization):
            return value
        return Organization.validate_invocation_value(value)

    async def create_member(self, identity_id: UUID, role: OrganizationMemberRole) -> OrganizationMember:
        """Create a member at an organization"""

        payload = {"identity_id": identity_id, "role": role}
        result = await invoke_instance(orm_model=self, function_name="create_member", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.organization.organization_member import OrganizationMember

        if isinstance(value, OrganizationMember):
            return value
        return OrganizationMember.validate_invocation_value(value)


class OrganizationCreateInput(BaseModel):
    actor_id: UUID


class OrganizationCreateOutput(BaseModel):
    value: Organization


class OrganizationCreateMemberInput(BaseModel):
    identity_id: UUID
    role: OrganizationMemberRole


class OrganizationCreateMemberOutput(BaseModel):
    value: OrganizationMember


FUNCTIONS = {
    "Organization": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Construct a Organization - Identity resolves profile",
                "is_constructor": True,
            },
            "input": OrganizationCreateInput,
            "output": OrganizationCreateOutput,
        },
        "create_member": {
            "canonical": {
                "name": "create_member",
                "description": "Create a member at an organization",
                "is_constructor": False,
            },
            "input": OrganizationCreateMemberInput,
            "output": OrganizationCreateMemberOutput,
        },
    },
}

__all__ = [
    "Organization",
    "OrganizationCreateInput",
    "OrganizationCreateOutput",
    "OrganizationCreateMemberInput",
    "OrganizationCreateMemberOutput",
    "FUNCTIONS",
]
