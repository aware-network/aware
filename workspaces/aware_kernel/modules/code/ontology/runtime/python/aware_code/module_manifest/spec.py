"""Module spec models for `aware.module.toml` (non-ORM, strict, deterministic)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AwareModuleRuntimeSpec:
    handler_modules: tuple[str, ...] = ()
    project_name: str | None = None
    import_root: str | None = None


@dataclass(frozen=True, slots=True)
class AwareModulePluginCapabilityPolicySpec:
    capability: str
    workspace_activation: str = "owner"
    workspace_fallback: bool = False


@dataclass(frozen=True, slots=True)
class AwareModulePluginSpec:
    """Generic plugin declaration for module-owned requirements.

    v0: used to declare DB requirements (e.g. Postgres extensions) and
    module-owned code/LSP execution plugins.

    This is intentionally generic so new plugin kinds can be introduced without
    changing the environment runtime packages. Only the environment-artifacts
    pipeline (build-time) needs to understand how to aggregate/emit artifacts
    for specific plugin kinds.
    """

    kind: str
    name: str | None = None
    module: str | None = None
    provider_key: str | None = None
    capability_contract_module: str | None = None
    capability_execution_module: str | None = None
    semantic_contract_module: str | None = None
    code_package_materialization_contract_module: str | None = None
    capability_policy: tuple[AwareModulePluginCapabilityPolicySpec, ...] = ()
    required: bool = True


@dataclass(frozen=True, slots=True)
class AwareModuleServiceSpec:
    """Service export declaration by app surface.

    Services are module-owned boundary adapters. The environment compiler
    consumes this rail to emit deterministic service mounts into runtime
    composition manifests.
    """

    surface: str
    provider_modules: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True, slots=True)
class AwareModulePackageSpec:
    id: str
    kind: str
    manifest: str
    aware_toml_path: str
    visibility: str = "module"
    semantic_contract: "AwareModulePackageSemanticContractSpec | None" = None
    semantic_bindings: tuple["AwareModulePackageSemanticBindingSpec", ...] = ()
    # When true for an API package, allows the package to reference its own module ontology
    # at `.aware` level for mirroring/copying types into the DTO OCG (no language-level deps).
    mirrors_ontology: bool = False


@dataclass(frozen=True, slots=True)
class AwareModulePackageSemanticContractBindingSpec:
    capability: str
    module: str
    callable: str


@dataclass(frozen=True, slots=True)
class AwareModulePackageSemanticContractSpec:
    role: str
    contract: str
    provider_key: str
    module: str
    owns_manifest_kinds: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    bindings: tuple[AwareModulePackageSemanticContractBindingSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class AwareModulePackageSemanticBindingSpec:
    role: str
    contract: str
    binding_module: str | None = None
    capabilities: tuple[str, ...] = ()
    callable_name: str | None = None


@dataclass(frozen=True, slots=True)
class AwareModuleSpec:
    aware: int
    structure_root: str = "structure"
    runtime_root: str = "runtime"
    representation_root: str = "representation"
    # Stable-id ownership mode for ontology Aware renderer.
    # - authored: emit `stable_ids.generated.toml` (parity rail).
    # - compiler: emit canonical `stable_ids.toml` (compiler-owned artifact).
    stable_ids_ownership: str = "authored"
    # Stable-id parity gate for the Aware renderer output.
    # Applies to `stable_ids.generated.toml` (authored mode) or `stable_ids.toml`
    # (compiler mode).
    # - off: skip parity validation
    # - warn: emit warnings on drift
    # - error: fail materialization on drift
    stable_ids_parity_policy: str = "warn"
    # Stable-id derivation policy.
    # - class_strict: class keys required for graph_ref classes; constructor fallback disallowed.
    stable_ids_resolution_policy: str = "class_strict"
    # FunctionImpl ownership mode for runtime-handlers materialization.
    # - authored: manual/dev-owned runtime_handlers rail.
    # - compiler: FunctionImpl-aware compiler-owned runtime_handlers rail.
    function_impl_ownership: str = "authored"
    # FunctionImpl parity policy for runtime-handlers.
    # - off: do not gate on FunctionImpl fallback warnings
    # - warn: surface FunctionImpl fallback warnings
    # - error: fail materialization when FunctionImpl fallback warnings exist
    function_impl_parity_policy: str = "off"
    runtime: AwareModuleRuntimeSpec | None = None
    services: tuple[AwareModuleServiceSpec, ...] = ()
    plugins: tuple[AwareModulePluginSpec, ...] = ()
    packages: tuple[AwareModulePackageSpec, ...] = ()


__all__ = [
    "AwareModulePluginCapabilityPolicySpec",
    "AwareModulePluginSpec",
    "AwareModuleServiceSpec",
    "AwareModuleSpec",
    "AwareModulePackageSpec",
    "AwareModulePackageSemanticBindingSpec",
    "AwareModulePackageSemanticContractBindingSpec",
    "AwareModulePackageSemanticContractSpec",
    "AwareModuleRuntimeSpec",
]
