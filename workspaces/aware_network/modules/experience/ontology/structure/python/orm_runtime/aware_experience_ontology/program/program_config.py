from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramAttributeType,
    ProgramBranchBindingMode,
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
    from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_experience_ontology.program.program_config_attribute_config import ProgramConfigAttributeConfig
    from aware_experience_ontology.program.program_config_input_config import ProgramConfigInputConfig
    from aware_experience_ontology.program.program_config_layout import ProgramConfigLayout
    from aware_experience_ontology.program.program_config_port import ProgramConfigPort


class ProgramConfig(ORMModel):
    """
    Declarative program configuration unit.
    Contract:
    - Stores stable config intent and projection-port bindings.
    - Is graph-agnostic; graph membership is represented by ProgramConfigGraphProgramConfig edges.
    - Does not execute; runtime creates Program instances and Turn receipts.
    """

    # Relationships
    actor_configs: list[ProgramConfigActorConfig] = Field(default_factory=list, exclude=True)
    attribute_configs: list[ProgramConfigAttributeConfig] = Field(default_factory=list, exclude=True)
    input_configs: list[ProgramConfigInputConfig] = Field(default_factory=list, exclude=True)
    ports: list[ProgramConfigPort] = Field(default_factory=list, exclude=True)
    layouts: list[ProgramConfigLayout] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    is_default: bool = Field(default=False)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)

    @classmethod
    async def build(
        cls,
        key: str,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
        intent: str | None = None,
        is_default: bool = False,
    ) -> ProgramConfig:
        """
        Create a deterministic graph-agnostic ProgramConfig.

        Contract:
        - Identity is compiler-derived from stable-id formula using `(key)`.
        - Graph ownership/linkage is represented only by ProgramConfigGraphProgramConfig.
        - Projection-port references are optional but explicit when present.
        """

        payload = {
            "key": key,
            "title": title,
            "description": description,
            "narrative": narrative,
            "intent": intent,
            "is_default": is_default,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfig):
            return value
        return ProgramConfig.validate_invocation_value(value)

    async def add_attribute_config(
        self,
        attribute_config_id: UUID,
        type: ProgramAttributeType = ProgramAttributeType.input,
        position: int | None = None,
        required: bool = True,
        attribute_name: str | None = None,
    ) -> ProgramConfigAttributeConfig:
        """
        Attach one pre-existing typed AttributeConfig contract edge under this ProgramConfig.

        Contract:
        - Represents canonical program I/O schema intent.
        - Idempotent per `(program_config_id, attribute_config_id, type)`.
        - Fails closed when referenced AttributeConfig does not exist.
        """

        payload = {
            "attribute_config_id": attribute_config_id,
            "type": type,
            "position": position,
            "required": required,
            "attribute_name": attribute_name,
        }
        result = await invoke_instance(orm_model=self, function_name="add_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_attribute_config import ProgramConfigAttributeConfig

        if isinstance(value, ProgramConfigAttributeConfig):
            return value
        return ProgramConfigAttributeConfig.validate_invocation_value(value)

    async def create_attribute_config(
        self,
        attribute_config_id: UUID,
        attribute_name: str,
        attribute_type_ref: str = "Any",
        enum_config_id: UUID | None = None,
        class_config_id: UUID | None = None,
        type: ProgramAttributeType = ProgramAttributeType.input,
        position: int | None = None,
        required: bool = True,
    ) -> ProgramConfigAttributeConfig:
        """
        Create AttributeConfig contract truth and attach typed association under this ProgramConfig.

        Contract:
        - Materializes AttributeConfig descriptor chain through canonical facade constructors.
        - Enum/Class contracts are link-only and must reference pre-existing OCG configs.
        - Creates/ensures ProgramConfigAttributeConfig association deterministically.
        """

        payload = {
            "attribute_config_id": attribute_config_id,
            "attribute_name": attribute_name,
            "attribute_type_ref": attribute_type_ref,
            "enum_config_id": enum_config_id,
            "class_config_id": class_config_id,
            "type": type,
            "position": position,
            "required": required,
        }
        result = await invoke_instance(orm_model=self, function_name="create_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_attribute_config import ProgramConfigAttributeConfig

        if isinstance(value, ProgramConfigAttributeConfig):
            return value
        return ProgramConfigAttributeConfig.validate_invocation_value(value)

    async def create_input_config(
        self, name: str, source: str, required: bool = True, default_expr: JsonObject | None = None
    ) -> ProgramConfigInputConfig:
        """Create one deterministic ProgramConfigInputConfig under this ProgramConfig."""

        payload = {"name": name, "source": source, "required": required, "default_expr": default_expr}
        result = await invoke_instance(orm_model=self, function_name="create_input_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_input_config import ProgramConfigInputConfig

        if isinstance(value, ProgramConfigInputConfig):
            return value
        return ProgramConfigInputConfig.validate_invocation_value(value)

    async def create_actor_config(self, actor_config_id: UUID, alias: str) -> ProgramConfigActorConfig:
        """Create one deterministic ProgramConfigActorConfig under this ProgramConfig."""

        payload = {"actor_config_id": actor_config_id, "alias": alias}
        result = await invoke_instance(orm_model=self, function_name="create_actor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig

        if isinstance(value, ProgramConfigActorConfig):
            return value
        return ProgramConfigActorConfig.validate_invocation_value(value)

    async def create_port(
        self,
        projection_id: UUID,
        key: str | None = None,
        intent: str | None = None,
        branch_binding_mode: ProgramBranchBindingMode = ProgramBranchBindingMode.reference,
    ) -> ProgramConfigPort:
        """Create one deterministic ProgramConfigPort under this ProgramConfig."""

        payload = {
            "projection_id": projection_id,
            "key": key,
            "intent": intent,
            "branch_binding_mode": branch_binding_mode,
        }
        result = await invoke_instance(orm_model=self, function_name="create_port", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_port import ProgramConfigPort

        if isinstance(value, ProgramConfigPort):
            return value
        return ProgramConfigPort.validate_invocation_value(value)

    async def create_layout(self, key: str, is_default: bool = False) -> ProgramConfigLayout:
        """Create one deterministic ProgramConfigLayout under this ProgramConfig."""

        payload = {"key": key, "is_default": is_default}
        result = await invoke_instance(orm_model=self, function_name="create_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_layout import ProgramConfigLayout

        if isinstance(value, ProgramConfigLayout):
            return value
        return ProgramConfigLayout.validate_invocation_value(value)


class ProgramConfigBuildInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    is_default: bool = Field(default=False)


class ProgramConfigBuildOutput(BaseModel):
    value: ProgramConfig


class ProgramConfigAddAttributeConfigInput(BaseModel):
    attribute_config_id: UUID
    type: ProgramAttributeType = Field(default=ProgramAttributeType.input)
    position: int | None = Field(default=None)
    required: bool = Field(default=True)
    attribute_name: str | None = Field(default=None)


class ProgramConfigAddAttributeConfigOutput(BaseModel):
    value: ProgramConfigAttributeConfig


class ProgramConfigCreateAttributeConfigInput(BaseModel):
    attribute_config_id: UUID
    attribute_name: str
    attribute_type_ref: str = Field(default="Any")
    enum_config_id: UUID | None = Field(default=None)
    class_config_id: UUID | None = Field(default=None)
    type: ProgramAttributeType = Field(default=ProgramAttributeType.input)
    position: int | None = Field(default=None)
    required: bool = Field(default=True)


class ProgramConfigCreateAttributeConfigOutput(BaseModel):
    value: ProgramConfigAttributeConfig


class ProgramConfigCreateInputConfigInput(BaseModel):
    name: str
    source: str
    required: bool = Field(default=True)
    default_expr: JsonObject | None = Field(default=None)


class ProgramConfigCreateInputConfigOutput(BaseModel):
    value: ProgramConfigInputConfig


class ProgramConfigCreateActorConfigInput(BaseModel):
    actor_config_id: UUID
    alias: str


class ProgramConfigCreateActorConfigOutput(BaseModel):
    value: ProgramConfigActorConfig


class ProgramConfigCreatePortInput(BaseModel):
    projection_id: UUID
    key: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    branch_binding_mode: ProgramBranchBindingMode = Field(default=ProgramBranchBindingMode.reference)


class ProgramConfigCreatePortOutput(BaseModel):
    value: ProgramConfigPort


class ProgramConfigCreateLayoutInput(BaseModel):
    key: str
    is_default: bool = Field(default=False)


class ProgramConfigCreateLayoutOutput(BaseModel):
    value: ProgramConfigLayout


FUNCTIONS = {
    "ProgramConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic graph-agnostic ProgramConfig.\n\nContract:\n- Identity is compiler-derived from stable-id formula using `(key)`.\n- Graph ownership/linkage is represented only by ProgramConfigGraphProgramConfig.\n- Projection-port references are optional but explicit when present.",
                "is_constructor": True,
            },
            "input": ProgramConfigBuildInput,
            "output": ProgramConfigBuildOutput,
        },
        "add_attribute_config": {
            "canonical": {
                "name": "add_attribute_config",
                "description": "Attach one pre-existing typed AttributeConfig contract edge under this ProgramConfig.\n\nContract:\n- Represents canonical program I/O schema intent.\n- Idempotent per `(program_config_id, attribute_config_id, type)`.\n- Fails closed when referenced AttributeConfig does not exist.",
                "is_constructor": False,
            },
            "input": ProgramConfigAddAttributeConfigInput,
            "output": ProgramConfigAddAttributeConfigOutput,
        },
        "create_attribute_config": {
            "canonical": {
                "name": "create_attribute_config",
                "description": "Create AttributeConfig contract truth and attach typed association under this ProgramConfig.\n\nContract:\n- Materializes AttributeConfig descriptor chain through canonical facade constructors.\n- Enum/Class contracts are link-only and must reference pre-existing OCG configs.\n- Creates/ensures ProgramConfigAttributeConfig association deterministically.",
                "is_constructor": False,
            },
            "input": ProgramConfigCreateAttributeConfigInput,
            "output": ProgramConfigCreateAttributeConfigOutput,
        },
        "create_input_config": {
            "canonical": {
                "name": "create_input_config",
                "description": "Create one deterministic ProgramConfigInputConfig under this ProgramConfig.",
                "is_constructor": False,
            },
            "input": ProgramConfigCreateInputConfigInput,
            "output": ProgramConfigCreateInputConfigOutput,
        },
        "create_actor_config": {
            "canonical": {
                "name": "create_actor_config",
                "description": "Create one deterministic ProgramConfigActorConfig under this ProgramConfig.",
                "is_constructor": False,
            },
            "input": ProgramConfigCreateActorConfigInput,
            "output": ProgramConfigCreateActorConfigOutput,
        },
        "create_port": {
            "canonical": {
                "name": "create_port",
                "description": "Create one deterministic ProgramConfigPort under this ProgramConfig.",
                "is_constructor": False,
            },
            "input": ProgramConfigCreatePortInput,
            "output": ProgramConfigCreatePortOutput,
        },
        "create_layout": {
            "canonical": {
                "name": "create_layout",
                "description": "Create one deterministic ProgramConfigLayout under this ProgramConfig.",
                "is_constructor": False,
            },
            "input": ProgramConfigCreateLayoutInput,
            "output": ProgramConfigCreateLayoutOutput,
        },
    },
}

__all__ = [
    "ProgramConfig",
    "ProgramConfigBuildInput",
    "ProgramConfigBuildOutput",
    "ProgramConfigAddAttributeConfigInput",
    "ProgramConfigAddAttributeConfigOutput",
    "ProgramConfigCreateAttributeConfigInput",
    "ProgramConfigCreateAttributeConfigOutput",
    "ProgramConfigCreateInputConfigInput",
    "ProgramConfigCreateInputConfigOutput",
    "ProgramConfigCreateActorConfigInput",
    "ProgramConfigCreateActorConfigOutput",
    "ProgramConfigCreatePortInput",
    "ProgramConfigCreatePortOutput",
    "ProgramConfigCreateLayoutInput",
    "ProgramConfigCreateLayoutOutput",
    "FUNCTIONS",
]
