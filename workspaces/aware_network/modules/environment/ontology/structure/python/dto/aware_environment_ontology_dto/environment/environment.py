from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology_dto.environment.environment_ontology import EnvironmentOntology
    from aware_environment_ontology_dto.environment.environment_profile import EnvironmentProfile
    from aware_environment_ontology_dto.environment.environment_session import EnvironmentSession
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class Environment(BaseModel):
    # Relationships
    config: EnvironmentConfig | None = Field(
        default=None,
        description="Canonical composition truth bound to this runtime environment.\nContract:\n- Required runtime binder input.\n- Owned by Environment through `EnvironmentConfig`; `Environment` binds it.\n- Not part of `Environment` class-key identity in this cut.",
    )
    image: StorageBlob | None = Field(
        default=None,
        description="Optional territory image override for this environment.\nFallback guidance:\n- If unset, UI should resolve through the caller-selected Experience/profile\nsurface, not through Environment-owned profile selection.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    profiles: list[EnvironmentProfile] = Field(
        default_factory=list,
        description="Concrete Environment-applied profiles.\nContract:\n- Reusable OS topology lives in EnvironmentProfileConfig.\n- Applied profiles own runtime Process/Thread provenance.\n- Environment does not point at Experience profiles for canonical boot.",
    )
    sessions: list[EnvironmentSession] = Field(
        default_factory=list,
        description="Runtime Environment sessions.\nContract:\n- Environment owns concrete shared session wrappers.\n- Identity owns actor membership through the linked Identity Session.\n- Profiles remain Process/Thread provenance; sessions resolve threads\nthrough EnvironmentSessionThread pins and may cross applied profiles.",
    )
    ontologies: list[EnvironmentOntology] = Field(
        default_factory=list,
        description="Ontology authorities available to this runtime Environment.\nContract:\n- Environment selects Ontology instances through this portal only.\n- ObjectInstanceGraphIdentity inventory remains owned by Ontology.\n- Environment must not point directly at Meta ObjectInstanceGraph/OIGI\nmembership.",
    )

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
