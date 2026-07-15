from __future__ import annotations

# Third-party
from pydantic import BaseModel

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class WalletPrivate(ORMModel):
    # Attributes
    private_key_encrypted: str

    @classmethod
    async def build(cls, private_key_encrypted: str) -> WalletPrivate:
        """
        Creates a wallet private/custody record.

        Receipt: WalletPrivate (opaque custody handle or encrypted key reference).

        Fail-closed:
        - production-visible `dev:` private-key material is rejected.
        """

        payload = {"private_key_encrypted": private_key_encrypted}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WalletPrivate):
            return value
        return WalletPrivate.validate_invocation_value(value)


class WalletPrivateBuildInput(BaseModel):
    private_key_encrypted: str


class WalletPrivateBuildOutput(BaseModel):
    value: WalletPrivate


FUNCTIONS = {
    "WalletPrivate": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a wallet private/custody record.\n\nReceipt: WalletPrivate (opaque custody handle or encrypted key reference).\n\nFail-closed:\n- production-visible `dev:` private-key material is rejected.",
                "is_constructor": True,
            },
            "input": WalletPrivateBuildInput,
            "output": WalletPrivateBuildOutput,
        },
    },
}

__all__ = [
    "WalletPrivate",
    "WalletPrivateBuildInput",
    "WalletPrivateBuildOutput",
    "FUNCTIONS",
]
