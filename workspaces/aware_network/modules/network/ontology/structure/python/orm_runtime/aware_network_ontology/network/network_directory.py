from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class NetworkDirectory(ORMModel):
    # Attributes
    name: str = Field(default="default")

    @classmethod
    async def bootstrap(cls, name: str = "default") -> NetworkDirectory:
        """
        Bootstrap the Network-owned directory/read-model root.

        Contract:
        - This root is the stable Network-owned directory lane for territory-wide discovery.
        - Durable discovery facts remain committed on `NetworkNode`, `NetworkNodePeer`,
          `NetworkNodeService`, and `NetworkNodeEnvironment`.
        - Reads must derive from committed Network state or service-owned read models,
          not ontology read functions.
        """

        payload = {"name": name}
        result = await invoke_constructor(orm_class=cls, function_name="bootstrap", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkDirectory):
            return value
        return NetworkDirectory.validate_invocation_value(value)


class NetworkDirectoryBootstrapInput(BaseModel):
    name: str = Field(default="default")


class NetworkDirectoryBootstrapOutput(BaseModel):
    value: NetworkDirectory


FUNCTIONS = {
    "NetworkDirectory": {
        "bootstrap": {
            "canonical": {
                "name": "bootstrap",
                "description": "Bootstrap the Network-owned directory/read-model root.\n\nContract:\n- This root is the stable Network-owned directory lane for territory-wide discovery.\n- Durable discovery facts remain committed on `NetworkNode`, `NetworkNodePeer`,\n  `NetworkNodeService`, and `NetworkNodeEnvironment`.\n- Reads must derive from committed Network state or service-owned read models,\n  not ontology read functions.",
                "is_constructor": True,
            },
            "input": NetworkDirectoryBootstrapInput,
            "output": NetworkDirectoryBootstrapOutput,
        },
    },
}

__all__ = [
    "NetworkDirectory",
    "NetworkDirectoryBootstrapInput",
    "NetworkDirectoryBootstrapOutput",
    "FUNCTIONS",
]
