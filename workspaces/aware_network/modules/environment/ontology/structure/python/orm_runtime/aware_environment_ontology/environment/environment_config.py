from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology.environment.environment_config_ontology_config import (
        EnvironmentConfigOntologyConfig,
    )
    from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology.environment.environment_session_config import EnvironmentSessionConfig


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

    @classmethod
    async def build(
        cls,
        handle: str,
        title: str,
        canonical_language: CodeLanguage,
        languages: list[CodeLanguage],
        description: str | None = None,
        is_kernel: bool = False,
    ) -> EnvironmentConfig:
        """
        Build one EnvironmentConfig for a deterministic module/environment handle.

        Contract:
        - `handle` is the identity key used by compiler-owned stable IDs.
        - EnvironmentConfig does not own repository, ownership, or raw Meta OCG
          composition truth.
        - OCG resolution is reachable only through attached OntologyConfig roots.
        """

        payload = {
            "handle": handle,
            "title": title,
            "canonical_language": canonical_language,
            "languages": languages,
            "description": description,
            "is_kernel": is_kernel,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentConfig):
            return value
        return EnvironmentConfig.validate_invocation_value(value)

    async def attach_ontology_config(
        self, name: str, fqn_prefix: str, ontology_config_object_instance_graph_commit_id: UUID | None = None
    ) -> EnvironmentConfigOntologyConfig:
        """
        Attach one ontology config requirement to this environment config.

        Contract:
        - Parent `EnvironmentConfig` scope is injected by propagation.
        - Target OntologyConfig identity is resolved from `(name, fqn_prefix)`.
        - The optional OIG commit pin is exact OntologyConfig replay truth.
        - EnvironmentConfig never resolves ObjectConfigGraph directly; it goes
          through `OntologyConfig.object_config_graph`.
        """

        payload = {
            "name": name,
            "fqn_prefix": fqn_prefix,
            "ontology_config_object_instance_graph_commit_id": ontology_config_object_instance_graph_commit_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_ontology_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_config_ontology_config import (
            EnvironmentConfigOntologyConfig,
        )

        if isinstance(value, EnvironmentConfigOntologyConfig):
            return value
        return EnvironmentConfigOntologyConfig.validate_invocation_value(value)

    async def add_profile_config(
        self, key: str, title: str | None = None, description: str | None = None, narrative: str | None = None
    ) -> EnvironmentProfileConfig:
        """
        Declare one Environment-level profile config.

        Contract:
        - EnvironmentConfig owns reusable profile topology for this
          Environment composition.
        - Stable identity is EnvironmentConfig path + `key`.
        - EnvironmentProfileConfig remains topology/config truth only; runtime
          EnvironmentProfile instances are Environment-owned.
        """

        payload = {"key": key, "title": title, "description": description, "narrative": narrative}
        result = await invoke_instance(orm_model=self, function_name="add_profile_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig

        if isinstance(value, EnvironmentProfileConfig):
            return value
        return EnvironmentProfileConfig.validate_invocation_value(value)

    async def add_session_config(
        self,
        key: str,
        identity_session_config_id: UUID,
        default_profile_config_id: UUID | None = None,
        default_process_config_id: UUID | None = None,
        default_thread_config_id: UUID | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSessionConfig:
        """
        Declare one Environment-level session config.

        Contract:
        - EnvironmentConfig owns reusable session defaults for this Environment
          composition.
        - Identity owns reusable SessionConfig policy and concrete membership.
        - Optional default profile/process/thread config portals are bootstrap
          defaults only; runtime session/thread resolution remains
          EnvironmentSession-owned.
        """

        payload = {
            "key": key,
            "identity_session_config_id": identity_session_config_id,
            "default_profile_config_id": default_profile_config_id,
            "default_process_config_id": default_process_config_id,
            "default_thread_config_id": default_thread_config_id,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="add_session_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_session_config import EnvironmentSessionConfig

        if isinstance(value, EnvironmentSessionConfig):
            return value
        return EnvironmentSessionConfig.validate_invocation_value(value)


class EnvironmentConfigBuildInput(BaseModel):
    handle: str
    title: str
    canonical_language: CodeLanguage
    languages: list[CodeLanguage] = Field(default_factory=list)
    description: str | None = Field(default=None)
    is_kernel: bool = Field(default=False)


class EnvironmentConfigBuildOutput(BaseModel):
    value: EnvironmentConfig


class EnvironmentConfigAttachOntologyConfigInput(BaseModel):
    name: str
    fqn_prefix: str
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(default=None)


class EnvironmentConfigAttachOntologyConfigOutput(BaseModel):
    value: EnvironmentConfigOntologyConfig


class EnvironmentConfigAddProfileConfigInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)


class EnvironmentConfigAddProfileConfigOutput(BaseModel):
    value: EnvironmentProfileConfig


class EnvironmentConfigAddSessionConfigInput(BaseModel):
    key: str
    identity_session_config_id: UUID
    default_profile_config_id: UUID | None = Field(default=None)
    default_process_config_id: UUID | None = Field(default=None)
    default_thread_config_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentConfigAddSessionConfigOutput(BaseModel):
    value: EnvironmentSessionConfig


FUNCTIONS = {
    "EnvironmentConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Build one EnvironmentConfig for a deterministic module/environment handle.\n\nContract:\n- `handle` is the identity key used by compiler-owned stable IDs.\n- EnvironmentConfig does not own repository, ownership, or raw Meta OCG\n  composition truth.\n- OCG resolution is reachable only through attached OntologyConfig roots.",
                "is_constructor": True,
            },
            "input": EnvironmentConfigBuildInput,
            "output": EnvironmentConfigBuildOutput,
        },
        "attach_ontology_config": {
            "canonical": {
                "name": "attach_ontology_config",
                "description": "Attach one ontology config requirement to this environment config.\n\nContract:\n- Parent `EnvironmentConfig` scope is injected by propagation.\n- Target OntologyConfig identity is resolved from `(name, fqn_prefix)`.\n- The optional OIG commit pin is exact OntologyConfig replay truth.\n- EnvironmentConfig never resolves ObjectConfigGraph directly; it goes\n  through `OntologyConfig.object_config_graph`.",
                "is_constructor": False,
            },
            "input": EnvironmentConfigAttachOntologyConfigInput,
            "output": EnvironmentConfigAttachOntologyConfigOutput,
        },
        "add_profile_config": {
            "canonical": {
                "name": "add_profile_config",
                "description": "Declare one Environment-level profile config.\n\nContract:\n- EnvironmentConfig owns reusable profile topology for this\n  Environment composition.\n- Stable identity is EnvironmentConfig path + `key`.\n- EnvironmentProfileConfig remains topology/config truth only; runtime\n  EnvironmentProfile instances are Environment-owned.",
                "is_constructor": False,
            },
            "input": EnvironmentConfigAddProfileConfigInput,
            "output": EnvironmentConfigAddProfileConfigOutput,
        },
        "add_session_config": {
            "canonical": {
                "name": "add_session_config",
                "description": "Declare one Environment-level session config.\n\nContract:\n- EnvironmentConfig owns reusable session defaults for this Environment\n  composition.\n- Identity owns reusable SessionConfig policy and concrete membership.\n- Optional default profile/process/thread config portals are bootstrap\n  defaults only; runtime session/thread resolution remains\n  EnvironmentSession-owned.",
                "is_constructor": False,
            },
            "input": EnvironmentConfigAddSessionConfigInput,
            "output": EnvironmentConfigAddSessionConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentConfig",
    "EnvironmentConfigBuildInput",
    "EnvironmentConfigBuildOutput",
    "EnvironmentConfigAttachOntologyConfigInput",
    "EnvironmentConfigAttachOntologyConfigOutput",
    "EnvironmentConfigAddProfileConfigInput",
    "EnvironmentConfigAddProfileConfigOutput",
    "EnvironmentConfigAddSessionConfigInput",
    "EnvironmentConfigAddSessionConfigOutput",
    "FUNCTIONS",
]
