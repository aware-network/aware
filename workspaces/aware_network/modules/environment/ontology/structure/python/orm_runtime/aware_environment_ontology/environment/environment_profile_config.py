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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology.environment.environment_profile_actor_config import EnvironmentProfileActorConfig
    from aware_environment_ontology.environment.environment_provider import EnvironmentProvider
    from aware_environment_ontology.process.process_config import ProcessConfig
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class EnvironmentProfileConfig(ORMModel):
    """
    Reusable Environment OS topology profile config.
    Contract:
    - Parent constructor is EnvironmentConfig.
    - Stable Environment topology config lives here, not in Experience and not
    under a concrete Environment instance.
    - ProcessConfig and ThreadConfig are reusable config parents.
    - EnvironmentProfile applies this config under a concrete Environment and
    owns concrete Process/Thread provenance.
    - EnvironmentSessionConfig lives at EnvironmentConfig scope; profile config
    can be referenced from session config defaults but never owns sessions.
    - Experiences attach later as approved providers through provider grants.
    """

    # Relationships
    process_configs: list[ProcessConfig] = Field(default_factory=list)
    providers: list[EnvironmentProvider] = Field(default_factory=list)
    actor_configs: list[EnvironmentProfileActorConfig] = Field(default_factory=list)
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional profile image used as the default for territory surfaces.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    environment_config: EnvironmentConfig | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentConfig.profile_configs"
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(
        default=None, description="Canonical environment-level narrative used by Environment selection and AI context."
    )
    key: str = Field(description="Stable profile key (recommended: `os.default`, `desktop.story`, etc).")
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.profile_configs")
    image_id: UUID | None = Field(default=None, description="Foreign key for EnvironmentProfileConfig.image")

    async def create_process_config(
        self,
        type: str,
        key: str,
        title: str | None = None,
        description: str | None = None,
        shape: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ProcessConfig:
        """
        Create a ProcessConfig under this EnvironmentProfileConfig.

        Contract:
        - Deterministic identity is EnvironmentProfileConfig-scoped using `key`.
        - Mutates only profile config membership.
        - Runtime Process instances are constructed under EnvironmentProfile.
        """

        payload = {
            "type": type,
            "key": key,
            "title": title,
            "description": description,
            "shape": shape,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="create_process_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.process.process_config import ProcessConfig

        if isinstance(value, ProcessConfig):
            return value
        return ProcessConfig.validate_invocation_value(value)

    async def register_provider(
        self,
        provider_key: str,
        provider_kind: str = "provider",
        contract_ref: str | None = None,
        selection_policy: str = "contract_required",
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProvider:
        """
        Register a provider-neutral slot for this EnvironmentProfileConfig.

        Contract:
        - Does not reference Experience or Service implementation classes.
        - Provider identity remains a contract key until an Experience binds to it.
        """

        payload = {
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "contract_ref": contract_ref,
            "selection_policy": selection_policy,
            "status": status,
            "title": title,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="register_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_provider import EnvironmentProvider

        if isinstance(value, EnvironmentProvider):
            return value
        return EnvironmentProvider.validate_invocation_value(value)

    async def add_actor_config(
        self,
        actor_config_id: UUID,
        policy_key: str = "admit",
        requirement_kind: str = "environment_actor_config",
        access_scope: str = "profile",
        status: str = "active",
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProfileActorConfig:
        """
        Declare one ActorConfig as eligible for EnvironmentProfileConfig admission.

        Contract:
        - Environment profile config owns eligibility policy for shared OS entrance.
        - Identity owns ActorConfig, RoleConfig, Role / ActorRole materialization.
        - Actors are not embedded here; admission services later translate this
          policy into Identity role assignment requests.
        """

        payload = {
            "actor_config_id": actor_config_id,
            "policy_key": policy_key,
            "requirement_kind": requirement_kind,
            "access_scope": access_scope,
            "status": status,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="add_actor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_profile_actor_config import (
            EnvironmentProfileActorConfig,
        )

        if isinstance(value, EnvironmentProfileActorConfig):
            return value
        return EnvironmentProfileActorConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_config(
        cls,
        environment_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
    ) -> EnvironmentProfileConfig:
        """
        Construct one reusable EnvironmentProfileConfig.

        Contract:
        - Stable identity is EnvironmentConfig path + `key`.
        - Parent EnvironmentConfig is propagated by containment.
        - This profile config is OS topology config, not an Experience profile
          and not a concrete Environment instance profile.
        """

        payload = {
            "environment_config_id": environment_config_id,
            "key": key,
            "title": title,
            "description": description,
            "narrative": narrative,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProfileConfig):
            return value
        return EnvironmentProfileConfig.validate_invocation_value(value)


class EnvironmentProfileConfigCreateProcessConfigInput(BaseModel):
    type: str
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    shape: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentProfileConfigCreateProcessConfigOutput(BaseModel):
    value: ProcessConfig


class EnvironmentProfileConfigRegisterProviderInput(BaseModel):
    provider_key: str
    provider_kind: str = Field(default="provider")
    contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProfileConfigRegisterProviderOutput(BaseModel):
    value: EnvironmentProvider


class EnvironmentProfileConfigAddActorConfigInput(BaseModel):
    actor_config_id: UUID
    policy_key: str = Field(default="admit")
    requirement_kind: str = Field(default="environment_actor_config")
    access_scope: str = Field(default="profile")
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProfileConfigAddActorConfigOutput(BaseModel):
    value: EnvironmentProfileActorConfig


class EnvironmentProfileConfigBuildViaEnvironmentConfigInput(BaseModel):
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.profile_configs")
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)


class EnvironmentProfileConfigBuildViaEnvironmentConfigOutput(BaseModel):
    value: EnvironmentProfileConfig


FUNCTIONS = {
    "EnvironmentProfileConfig": {
        "create_process_config": {
            "canonical": {
                "name": "create_process_config",
                "description": "Create a ProcessConfig under this EnvironmentProfileConfig.\n\nContract:\n- Deterministic identity is EnvironmentProfileConfig-scoped using `key`.\n- Mutates only profile config membership.\n- Runtime Process instances are constructed under EnvironmentProfile.",
                "is_constructor": False,
            },
            "input": EnvironmentProfileConfigCreateProcessConfigInput,
            "output": EnvironmentProfileConfigCreateProcessConfigOutput,
        },
        "register_provider": {
            "canonical": {
                "name": "register_provider",
                "description": "Register a provider-neutral slot for this EnvironmentProfileConfig.\n\nContract:\n- Does not reference Experience or Service implementation classes.\n- Provider identity remains a contract key until an Experience binds to it.",
                "is_constructor": False,
            },
            "input": EnvironmentProfileConfigRegisterProviderInput,
            "output": EnvironmentProfileConfigRegisterProviderOutput,
        },
        "add_actor_config": {
            "canonical": {
                "name": "add_actor_config",
                "description": "Declare one ActorConfig as eligible for EnvironmentProfileConfig admission.\n\nContract:\n- Environment profile config owns eligibility policy for shared OS entrance.\n- Identity owns ActorConfig, RoleConfig, Role / ActorRole materialization.\n- Actors are not embedded here; admission services later translate this\n  policy into Identity role assignment requests.",
                "is_constructor": False,
            },
            "input": EnvironmentProfileConfigAddActorConfigInput,
            "output": EnvironmentProfileConfigAddActorConfigOutput,
        },
        "build_via_environment_config": {
            "canonical": {
                "name": "build_via_environment_config",
                "description": "Construct one reusable EnvironmentProfileConfig.\n\nContract:\n- Stable identity is EnvironmentConfig path + `key`.\n- Parent EnvironmentConfig is propagated by containment.\n- This profile config is OS topology config, not an Experience profile\n  and not a concrete Environment instance profile.",
                "is_constructor": True,
            },
            "input": EnvironmentProfileConfigBuildViaEnvironmentConfigInput,
            "output": EnvironmentProfileConfigBuildViaEnvironmentConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentProfileConfig",
    "EnvironmentProfileConfigCreateProcessConfigInput",
    "EnvironmentProfileConfigCreateProcessConfigOutput",
    "EnvironmentProfileConfigRegisterProviderInput",
    "EnvironmentProfileConfigRegisterProviderOutput",
    "EnvironmentProfileConfigAddActorConfigInput",
    "EnvironmentProfileConfigAddActorConfigOutput",
    "EnvironmentProfileConfigBuildViaEnvironmentConfigInput",
    "EnvironmentProfileConfigBuildViaEnvironmentConfigOutput",
    "FUNCTIONS",
]
