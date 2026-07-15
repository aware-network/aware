from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_config_ontology_config import (
        EnvironmentConfigOntologyConfig,
    )
    from aware_environment_ontology_orm_models.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_orm_models.environment.environment_session_config import EnvironmentSessionConfig


class EnvironmentConfig(ORMModel):
    # Relationships
    ontology_configs: list[EnvironmentConfigOntologyConfig] = Field(default_factory=list)
    profile_configs: list[EnvironmentProfileConfig] = Field(
        default_factory=list,
        description="Reusable Environment profile topology templates.\nContract:\n- EnvironmentConfig owns profile config vocabulary for this Environment\ncomposition.\n- EnvironmentProfileConfig owns Process/Thread/provider/actor topology.\n- Runtime EnvironmentProfile instances are Environment-owned, not\nconfig-owned.",
    )
    session_configs: list[EnvironmentSessionConfig] = Field(
        default_factory=list,
        description="Reusable Environment session templates.\nContract:\n- EnvironmentConfig owns session config vocabulary for this Environment\ncomposition.\n- EnvironmentSessionConfig may point at default profile/process/thread\ntopology, but it does not own runtime EnvironmentSession instances.",
    )

    # Attributes
    canonical_language: CodeLanguage
    description: str | None = Field(default=None)
    handle: str
    is_kernel: bool = Field(default=False)
    languages: list[CodeLanguage] = Field(default_factory=list)
    title: str
