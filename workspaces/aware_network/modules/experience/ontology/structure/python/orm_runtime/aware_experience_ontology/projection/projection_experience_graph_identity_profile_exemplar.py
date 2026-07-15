from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ProjectionExperienceGraphIdentityProfileExemplar(ORMModel):
    """
    One commit-backed exemplar row for a graph-identity profile.
    Contract:
    - Image bytes are uploaded out-of-band (data-plane).
    - Commits reference StorageBlob metadata only.
    - Future content/location specialization may aggregate on top of this row.
    """

    # Relationships
    image: StorageBlob | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    label: str | None = Field(default=None)
    prompt_hint: str | None = Field(default=None)
    note: str | None = Field(default=None)
    is_primary: bool = Field(default=False)

    # Foreign Keys
    projection_experience_graph_identity_profile_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityProfile.exemplars"
    )
    image_id: UUID | None = Field(
        default=None, description="Foreign key for ProjectionExperienceGraphIdentityProfileExemplar.image"
    )

    @classmethod
    async def build_via_projection_experience_graph_identity_profile(
        cls,
        projection_experience_graph_identity_profile_id: UUID,
        key: str,
        label: str | None = None,
        prompt_hint: str | None = None,
        note: str | None = None,
        is_primary: bool = False,
        image_id: UUID | None = None,
    ) -> ProjectionExperienceGraphIdentityProfileExemplar:
        """Construct one exemplar row under a ProjectionExperienceGraphIdentityProfile."""

        payload = {
            "projection_experience_graph_identity_profile_id": projection_experience_graph_identity_profile_id,
            "key": key,
            "label": label,
            "prompt_hint": prompt_hint,
            "note": note,
            "is_primary": is_primary,
            "image_id": image_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_graph_identity_profile", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceGraphIdentityProfileExemplar):
            return value
        return ProjectionExperienceGraphIdentityProfileExemplar.validate_invocation_value(value)


class ProjectionExperienceGraphIdentityProfileExemplarBuildViaProjectionExperienceGraphIdentityProfileInput(BaseModel):
    projection_experience_graph_identity_profile_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityProfile.exemplars"
    )
    key: str
    label: str | None = Field(default=None)
    prompt_hint: str | None = Field(default=None)
    note: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    image_id: UUID | None = Field(default=None)


class ProjectionExperienceGraphIdentityProfileExemplarBuildViaProjectionExperienceGraphIdentityProfileOutput(BaseModel):
    value: ProjectionExperienceGraphIdentityProfileExemplar


FUNCTIONS = {
    "ProjectionExperienceGraphIdentityProfileExemplar": {
        "build_via_projection_experience_graph_identity_profile": {
            "canonical": {
                "name": "build_via_projection_experience_graph_identity_profile",
                "description": "Construct one exemplar row under a ProjectionExperienceGraphIdentityProfile.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceGraphIdentityProfileExemplarBuildViaProjectionExperienceGraphIdentityProfileInput,
            "output": ProjectionExperienceGraphIdentityProfileExemplarBuildViaProjectionExperienceGraphIdentityProfileOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceGraphIdentityProfileExemplar",
    "ProjectionExperienceGraphIdentityProfileExemplarBuildViaProjectionExperienceGraphIdentityProfileInput",
    "ProjectionExperienceGraphIdentityProfileExemplarBuildViaProjectionExperienceGraphIdentityProfileOutput",
    "FUNCTIONS",
]
