from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class CodeTestFramework(ORMModel):
    """
    Canonical test framework identity.
    Framework is intentionally an object instead of an enum so languages and
    installations can later attach compatibility/capability contracts.
    """

    # Attributes
    name: str
    title: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, title: str | None = None) -> CodeTestFramework:
        """Create deterministic test framework identity by canonical framework name."""

        payload = {"name": name, "title": title}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeTestFramework):
            return value
        return CodeTestFramework.validate_invocation_value(value)


class CodeTestFrameworkBuildInput(BaseModel):
    name: str
    title: str | None = Field(default=None)


class CodeTestFrameworkBuildOutput(BaseModel):
    value: CodeTestFramework


FUNCTIONS = {
    "CodeTestFramework": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create deterministic test framework identity by canonical framework name.",
                "is_constructor": True,
            },
            "input": CodeTestFrameworkBuildInput,
            "output": CodeTestFrameworkBuildOutput,
        },
    },
}

__all__ = [
    "CodeTestFramework",
    "CodeTestFrameworkBuildInput",
    "CodeTestFrameworkBuildOutput",
    "FUNCTIONS",
]
