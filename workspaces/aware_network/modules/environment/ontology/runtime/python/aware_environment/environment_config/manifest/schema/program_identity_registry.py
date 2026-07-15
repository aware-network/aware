"""Program identity registry artifact schema.

Compile-emitted identity-contract truth for program lowering/runtime rails:
- constructor identity keys (`FunctionConfigAttributeConfig.is_identity_key`)
- projection/branch identity contracts (future bind-resolution slices)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProgramObjectIdentityContract(BaseModel):
    """Class-authored identity contract for one class in one module scope."""

    scope: str = Field(
        ...,
        description="Normalized identity scope (`module::<module_id>`).",
    )
    module_id: str = Field(..., description="Canonical module id.")
    class_name: str = Field(..., description="Class name owning the identity contract.")
    source_name: str = Field(
        ...,
        description="Source evidence label for the emitted identity contract.",
    )
    identity_keys: list[str] = Field(
        default_factory=list,
        description="Ordered class-authored stable-id input keys.",
    )
    namespace: str = Field(
        ...,
        description="Stable-id namespace token (for example `NS_EXPERIENCE`).",
    )
    stable_id_key: str = Field(
        default="primary",
        description="Stable-id key variant (v0 fixed to `primary`).",
    )
    stable_id_target: str = Field(
        ...,
        description=(
            "Program callable target used by Type.id sugar "
            "(for example `experience.stable_program_config_id`)."
        ),
    )
    source: str = Field(
        default="class_identity",
        description="Contract source descriptor.",
    )


class ProgramProjectionBranchIdentityContract(BaseModel):
    """Projection/branch identity contract (reserved for bind derivation slices)."""

    scope: str = Field(
        ...,
        description="Normalized projection scope (`projection::<...>`).",
    )
    projection: str = Field(..., description="Projection identifier.")
    branch: str = Field(..., description="Branch key identifier.")
    identity_key: str = Field(
        ...,
        description="Port resolver argument that represents branch identity input.",
    )


class ProgramIdentityRegistry(BaseModel):
    """Compile-emitted identity-contract registry."""

    version: str = Field(
        default="1.0", description="Program identity registry schema version."
    )
    object_identity_contracts: list[ProgramObjectIdentityContract] = Field(
        default_factory=list,
        description="Constructor identity contracts indexed by class/module scope.",
    )
    projection_branch_contracts: list[ProgramProjectionBranchIdentityContract] = Field(
        default_factory=list,
        description="Projection branch identity contracts for bind resolution.",
    )


__all__ = [
    "ProgramIdentityRegistry",
    "ProgramObjectIdentityContract",
    "ProgramProjectionBranchIdentityContract",
]
