from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class CodeSemanticContractRuntimeImport(BaseModel):
    # Attributes
    capabilities: list[str] = Field(default_factory=list)
    import_role: str = Field(default="semantic_contract")
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    provider_key: str
    required: bool = Field(default=True)
    semantic_contract_module: str
    status: str = Field(default="active")
