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
from aware_identity_ontology.role.role_enums import AccessLevelType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.role.role_config_class_config import RoleConfigClassConfig
    from aware_identity_ontology.role.role_config_class_config_relationship import RoleConfigClassConfigRelationship
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship


class RoleConfig(ORMModel):
    # Relationships
    role_config_class_configs: list[RoleConfigClassConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    # Edges
    role_config_class_config_relationships: list[RoleConfigClassConfigRelationship] = Field(
        default_factory=list, exclude=True, description="Edge association helper for class_config_relationships"
    )

    @property
    def class_config_relationships(self) -> list[ClassConfigRelationship]:
        return [
            edge.class_config_relationship
            for edge in self.role_config_class_config_relationships
            if edge.class_config_relationship is not None
        ]

    @classmethod
    async def create(cls, name: str, description: str | None = None) -> RoleConfig:
        """
        Create a RoleConfig (policy root) inside the `role_config` projection.

        Contract (v0):
        - Policy creation is commit-backed (no transport-only RoleConfigs).
        - `name` is the canonical key (runtime derives a stable id from it).
        - Idempotent by name: creating the same RoleConfig twice returns the existing instance.
        """

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RoleConfig):
            return value
        return RoleConfig.validate_invocation_value(value)

    async def upsert_class_config_policy(
        self, class_config_id: UUID, access_level: AccessLevelType
    ) -> RoleConfigClassConfig:
        """
        Upsert a class-level policy edge for a given meta ClassConfig.

        Notes:
        - `class_config_id` refers to `aware_meta.class.ClassConfig` via the `role_config` →
        `object_config_graph` portal.
        - Function-level policy is modeled on `RoleConfigClassConfigFunctionConfig`.
        """

        payload = {"class_config_id": class_config_id, "access_level": access_level}
        result = await invoke_instance(orm_model=self, function_name="upsert_class_config_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.role.role_config_class_config import RoleConfigClassConfig

        if isinstance(value, RoleConfigClassConfig):
            return value
        return RoleConfigClassConfig.validate_invocation_value(value)


class RoleConfigCreateInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class RoleConfigCreateOutput(BaseModel):
    value: RoleConfig


class RoleConfigUpsertClassConfigPolicyInput(BaseModel):
    class_config_id: UUID
    access_level: AccessLevelType


class RoleConfigUpsertClassConfigPolicyOutput(BaseModel):
    value: RoleConfigClassConfig


FUNCTIONS = {
    "RoleConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create a RoleConfig (policy root) inside the `role_config` projection.\n\nContract (v0):\n- Policy creation is commit-backed (no transport-only RoleConfigs).\n- `name` is the canonical key (runtime derives a stable id from it).\n- Idempotent by name: creating the same RoleConfig twice returns the existing instance.",
                "is_constructor": True,
            },
            "input": RoleConfigCreateInput,
            "output": RoleConfigCreateOutput,
        },
        "upsert_class_config_policy": {
            "canonical": {
                "name": "upsert_class_config_policy",
                "description": "Upsert a class-level policy edge for a given meta ClassConfig.\n\nNotes:\n- `class_config_id` refers to `aware_meta.class.ClassConfig` via the `role_config` → `object_config_graph` portal.\n- Function-level policy is modeled on `RoleConfigClassConfigFunctionConfig`.",
                "is_constructor": False,
            },
            "input": RoleConfigUpsertClassConfigPolicyInput,
            "output": RoleConfigUpsertClassConfigPolicyOutput,
        },
    },
}

__all__ = [
    "RoleConfig",
    "RoleConfigCreateInput",
    "RoleConfigCreateOutput",
    "RoleConfigUpsertClassConfigPolicyInput",
    "RoleConfigUpsertClassConfigPolicyOutput",
    "FUNCTIONS",
]
