from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class PricingPolicy(ORMModel):
    # Attributes
    description: str | None = Field(default=None)
    fail_closed: bool = Field(default=True)
    name: str
    policy_json: JsonObject = Field(default_factory=JsonObject)
    version: int = Field(default=1)

    @classmethod
    async def build(
        cls,
        name: str,
        version: int = 1,
        description: str | None = None,
        policy_json: JsonObject = {},
        fail_closed: bool = True,
    ) -> PricingPolicy:
        """Creates one Economy-owned pricing policy receipt."""

        payload = {
            "name": name,
            "version": version,
            "description": description,
            "policy_json": policy_json,
            "fail_closed": fail_closed,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PricingPolicy):
            return value
        return PricingPolicy.validate_invocation_value(value)


class PricingPolicyBuildInput(BaseModel):
    name: str
    version: int = Field(default=1)
    description: str | None = Field(default=None)
    policy_json: JsonObject = Field(default_factory=JsonObject)
    fail_closed: bool = Field(default=True)


class PricingPolicyBuildOutput(BaseModel):
    value: PricingPolicy


FUNCTIONS = {
    "PricingPolicy": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates one Economy-owned pricing policy receipt.",
                "is_constructor": True,
            },
            "input": PricingPolicyBuildInput,
            "output": PricingPolicyBuildOutput,
        },
    },
}

__all__ = [
    "PricingPolicy",
    "PricingPolicyBuildInput",
    "PricingPolicyBuildOutput",
    "FUNCTIONS",
]
