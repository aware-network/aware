"""Program registry entries embedded in environment manifests."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProgramRegistryEntry(BaseModel):
    """Deterministic `program_ref` registry entry."""

    ref: str = Field(..., description="Program ref: '<module_id>:<program_name>'")
    module_id: str = Field(..., description="Owning module id")
    program_name: str = Field(..., description="Program declaration name")
    program_path: str = Field(
        ...,
        description="Repo-relative path to the `.aware` program source file",
    )
    content_hash: str = Field(
        ...,
        description="Deterministic content hash of the program source (sha256:<hex>)",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Declared package dependencies for this program",
    )
    required_symbols: list[str] = Field(
        default_factory=list,
        description="Required `plan.*` symbols expected by the program",
    )
    optional_symbols: list[str] = Field(
        default_factory=list,
        description="Optional `plan.*` symbols accepted by the program",
    )
    invocation_plan_path: str | None = Field(
        default=None,
        description=(
            "Repo-relative path to compile-emitted InvocationPlan artifact JSON "
            "for runtime execution."
        ),
    )
    invocation_plan_hash: str | None = Field(
        default=None,
        description="Deterministic hash of invocation plan artifact (sha256:<hex>).",
    )
    program_config_plan_path: str | None = Field(
        default=None,
        description=(
            "Repo-relative path to compile-emitted ProgramConfigPlan artifact JSON "
            "(graph-oriented program contract payload)."
        ),
    )
    program_config_plan_hash: str | None = Field(
        default=None,
        description="Deterministic hash of ProgramConfigPlan artifact (sha256:<hex>).",
    )
    program_apply_calls_path: str | None = Field(
        default=None,
        description=(
            "Repo-relative path to compile-emitted program apply-call artifact JSON "
            "(graph-first canonical call intents)."
        ),
    )
    program_apply_calls_hash: str | None = Field(
        default=None,
        description="Deterministic hash of program apply-calls artifact (sha256:<hex>).",
    )


__all__ = ["ProgramRegistryEntry"]
