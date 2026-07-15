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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_graph_identity_profile_exemplar import (
        ProjectionExperienceGraphIdentityProfileExemplar,
    )


class ProjectionExperienceGraphIdentityProfile(ORMModel):
    """
    Canonical profile for one ProjectionExperienceGraphIdentity.
    Contract:
    - Owned by one graph occurrence identity, not by generic node identity.
    - Stores review-facing label and deterministic resolution hints for later
    profile-based binding.
    - Remains perception-agnostic: it holds identity-side truth, not observations.
    """

    # Relationships
    exemplars: list[ProjectionExperienceGraphIdentityProfileExemplar] = Field(default_factory=list, exclude=True)

    # Attributes
    review_label: str
    resolution_prompts: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_graph_identity_id: UUID | None = Field(
        default=None,
        description="Foreign key for ProjectionExperienceGraphIdentity.projection_experience_graph_identity_profile",
    )

    async def create_exemplar(
        self,
        key: str,
        label: str | None = None,
        prompt_hint: str | None = None,
        note: str | None = None,
        is_primary: bool = False,
        image_id: UUID | None = None,
    ) -> ProjectionExperienceGraphIdentityProfileExemplar:
        """
        Attach one exemplar row under this graph-identity profile.

        Contract:
        - Exemplar bytes are uploaded out-of-band; commits reference StorageBlob metadata only.
        - Exemplars improve future matching quality but do not redefine graph identity.
        """

        payload = {
            "key": key,
            "label": label,
            "prompt_hint": prompt_hint,
            "note": note,
            "is_primary": is_primary,
            "image_id": image_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_exemplar", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_graph_identity_profile_exemplar import (
            ProjectionExperienceGraphIdentityProfileExemplar,
        )

        if isinstance(value, ProjectionExperienceGraphIdentityProfileExemplar):
            return value
        return ProjectionExperienceGraphIdentityProfileExemplar.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience_graph_identity(
        cls,
        projection_experience_graph_identity_id: UUID,
        review_label: str,
        resolution_prompts: list[str] = [],
        aliases: list[str] = [],
        summary: str | None = None,
        notes: str | None = None,
    ) -> ProjectionExperienceGraphIdentityProfile:
        """
        Construct one canonical graph-identity profile under a ProjectionExperienceGraphIdentity.

        Contract:
        - Parent graph identity is the canonical anchor for this profile.
        - `review_label` is the human-facing label used in review/UI rails.
        - `resolution_prompts` are deterministic matcher hints, not identity by themselves.
        - Richer content/location extensions may evolve later without redefining this core surface.
        """

        payload = {
            "projection_experience_graph_identity_id": projection_experience_graph_identity_id,
            "review_label": review_label,
            "resolution_prompts": resolution_prompts,
            "aliases": aliases,
            "summary": summary,
            "notes": notes,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceGraphIdentityProfile):
            return value
        return ProjectionExperienceGraphIdentityProfile.validate_invocation_value(value)


class ProjectionExperienceGraphIdentityProfileCreateExemplarInput(BaseModel):
    key: str
    label: str | None = Field(default=None)
    prompt_hint: str | None = Field(default=None)
    note: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    image_id: UUID | None = Field(default=None)


class ProjectionExperienceGraphIdentityProfileCreateExemplarOutput(BaseModel):
    value: ProjectionExperienceGraphIdentityProfileExemplar


class ProjectionExperienceGraphIdentityProfileBuildViaProjectionExperienceGraphIdentityInput(BaseModel):
    projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentity.projection_experience_graph_identity_profile"
    )
    review_label: str
    resolution_prompts: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    notes: str | None = Field(default=None)


class ProjectionExperienceGraphIdentityProfileBuildViaProjectionExperienceGraphIdentityOutput(BaseModel):
    value: ProjectionExperienceGraphIdentityProfile


FUNCTIONS = {
    "ProjectionExperienceGraphIdentityProfile": {
        "create_exemplar": {
            "canonical": {
                "name": "create_exemplar",
                "description": "Attach one exemplar row under this graph-identity profile.\n\nContract:\n- Exemplar bytes are uploaded out-of-band; commits reference StorageBlob metadata only.\n- Exemplars improve future matching quality but do not redefine graph identity.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceGraphIdentityProfileCreateExemplarInput,
            "output": ProjectionExperienceGraphIdentityProfileCreateExemplarOutput,
        },
        "build_via_projection_experience_graph_identity": {
            "canonical": {
                "name": "build_via_projection_experience_graph_identity",
                "description": "Construct one canonical graph-identity profile under a ProjectionExperienceGraphIdentity.\n\nContract:\n- Parent graph identity is the canonical anchor for this profile.\n- `review_label` is the human-facing label used in review/UI rails.\n- `resolution_prompts` are deterministic matcher hints, not identity by themselves.\n- Richer content/location extensions may evolve later without redefining this core surface.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceGraphIdentityProfileBuildViaProjectionExperienceGraphIdentityInput,
            "output": ProjectionExperienceGraphIdentityProfileBuildViaProjectionExperienceGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceGraphIdentityProfile",
    "ProjectionExperienceGraphIdentityProfileCreateExemplarInput",
    "ProjectionExperienceGraphIdentityProfileCreateExemplarOutput",
    "ProjectionExperienceGraphIdentityProfileBuildViaProjectionExperienceGraphIdentityInput",
    "ProjectionExperienceGraphIdentityProfileBuildViaProjectionExperienceGraphIdentityOutput",
    "FUNCTIONS",
]
