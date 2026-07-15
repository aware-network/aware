from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any, Callable, Iterable, Mapping
from uuid import UUID

from aware_node_operator.kernel_ops.legacy_api_models import (
    FunctionCallRequest,
    FunctionDescriptor,
    ObjectDescriptor,
)

from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_identity_id,
    stable_organization_id,
    stable_organization_member_id,
)

from aware_agent.stable_ids import (
    stable_agent_id,
    stable_agent_process_inference_model_id,
    stable_agent_process_id,
    stable_agent_process_thread_id,
    stable_inference_deployment_id,
    stable_inference_model_id,
    stable_inference_region_id,
    stable_inference_service_config_id,
    stable_inference_service_id,
)

from aware_economy.stable_ids import (
    stable_finance_entity_id,
    stable_smart_contract_config_id,
    stable_smart_contract_id,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_id,
    stable_service_id,
)

from aware_node_operator.kernel_ops.seed_keys import (
    load_seed_keypairs,
    resolve_seed_keypair,
)
from aware_node_operator.kernel_ops.seed_deterministic import (
    build_seed_agent_profile_request,
    economy_wallet_seed,
)


def _legacy_api_unavailable() -> RuntimeError:
    return RuntimeError(
        "Kernel seed program apply requires the retired legacy `aware_api.client` rail. "
        "The helper is quarantined under `aware-node-operator`; use the SDK/API "
        "service rail for live product paths."
    )


try:
    from aware_api.client import AwareApiClient, AwareApiConfig
    from aware_api.context import AwareApiContext
except ImportError:

    class AwareApiConfig:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise _legacy_api_unavailable()

    class AwareApiContext:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise _legacy_api_unavailable()

    class AwareApiClient:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise _legacy_api_unavailable()


from aware_experience.program.language import (
    InvocationPlan,
    PlanCall,
    PlanExpr,
    PlanInput,
    PlanInvoke,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanSymbolRef,
    compile_invocation_plans,
)
from aware_experience.program.language.stdlib import (
    stable_ns_url,
    stable_uuid5,
)
from aware_meta_ontology.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_id,
    stable_function_config_id,
)
from aware_meta.graph.config.stable_ids import stable_class_relationship_id
from aware_experience.program.loader import load_aware_programs_toml_spec


@dataclass(frozen=True, slots=True)
class BootContext:
    environment_id: UUID
    process_id: UUID
    thread_id: UUID


@dataclass(frozen=True, slots=True)
class OpgRef:
    opg_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class PendingLaneActivation:
    branch_id: UUID
    opg_name: str
    require_head: bool
    skip_if_head: bool


class SeedProgramError(RuntimeError):
    pass


_REPO_ROOT_ENV_VARS = (
    "AWARE_NODE_OPERATOR_REPO_ROOT",
    "AWARE_NODE_REPO_ROOT",
    "AWARE_REPO_ROOT",
    "AWARE_REPOSITORY_ROOT",
)


@dataclass(frozen=True, slots=True)
class ProgramAssetRef:
    module_id: str
    program_name: str

    @classmethod
    def parse(cls, raw: str) -> "ProgramAssetRef":
        text = (raw or "").strip()
        if not text:
            raise SeedProgramError("Program ref is empty")
        if ":" not in text:
            raise SeedProgramError(
                f"Invalid program ref {text!r}; expected '<module_id>:<program_name>'"
            )
        module_id, program_name = text.split(":", 1)
        module_id = module_id.strip()
        program_name = program_name.strip()
        if not module_id or not program_name:
            raise SeedProgramError(
                f"Invalid program ref {text!r}; expected '<module_id>:<program_name>'"
            )
        return cls(module_id=module_id, program_name=program_name)

    @property
    def value(self) -> str:
        return f"{self.module_id}:{self.program_name}"


@dataclass(frozen=True, slots=True)
class SeedProgramRegistryEntry:
    ref: str
    module_id: str
    program_name: str
    source_path: Path
    required_symbols: tuple[str, ...]
    optional_symbols: tuple[str, ...]


def _normalize_node_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    suffix = "/interface/network_node"
    trimmed = endpoint.rstrip("/")
    if trimmed.endswith(suffix):
        trimmed = trimmed[: -len(suffix)]
    return trimmed.rstrip("/")


def _resolve_node_endpoint(*, override: str | None = None) -> str:
    if override and override.strip():
        return _normalize_node_endpoint(override)
    endpoint = os.getenv("AWARE_NODE_WS_URL")
    if endpoint:
        return _normalize_node_endpoint(endpoint)
    base = os.getenv("AWARE_NODE_BASE_URL")
    if base:
        if base.startswith("http://"):
            return _normalize_node_endpoint("ws://" + base[len("http://") :])
        if base.startswith("https://"):
            return _normalize_node_endpoint("wss://" + base[len("https://") :])
        return _normalize_node_endpoint(base)
    raise SeedProgramError(
        "Missing node endpoint. Set AWARE_NODE_WS_URL/AWARE_NODE_BASE_URL or pass --endpoint."
    )


async def _resolve_boot_context(*, client: AwareApiClient) -> BootContext:
    boot = await client.get_boot_environment_descriptor()
    if boot.status != "ready" or boot.descriptor is None:
        raise SeedProgramError(
            f"Boot environment is not ready: status={boot.status} error={boot.error}"
        )
    env_id = boot.descriptor.boot_environment_id
    process_id = boot.descriptor.process_id
    thread_id = boot.descriptor.thread_id
    if process_id is None or thread_id is None:
        raise SeedProgramError(
            "Boot environment descriptor missing process_id/thread_id "
            f"(process_id={process_id} thread_id={thread_id})"
        )
    return BootContext(
        environment_id=env_id,
        process_id=process_id,
        thread_id=thread_id,
    )


def _lower_key(value: str) -> str:
    return (value or "").strip().casefold()


def _tokenize(value: str) -> list[str]:
    raw = (value or "").strip().casefold()
    if not raw:
        return []
    return [token for token in re.split(r"[^0-9a-zA-Z]+", raw) if token]


def _split_call_target(target: str) -> tuple[str, str]:
    raw = (target or "").strip()
    if not raw or "." not in raw:
        raise SeedProgramError(f"Invalid call target: {target!r}")
    owner, fn = raw.rsplit(".", 1)
    owner = owner.strip()
    fn = fn.strip()
    if not owner or not fn:
        raise SeedProgramError(f"Invalid call target: {target!r}")
    return owner, fn


def _compile_program_by_ref(*, src: str, program_name: str) -> InvocationPlan:
    plans = compile_invocation_plans(src)
    if not plans:
        raise SeedProgramError("No program declarations found in source")
    matches = [plan for plan in plans if plan.name == program_name]
    if not matches:
        available = sorted({plan.name for plan in plans})
        raise SeedProgramError(
            f"Program not found in source: {program_name!r} (available={available})"
        )
    if len(matches) > 1:
        raise SeedProgramError(f"Ambiguous program declaration name: {program_name!r}")
    return matches[0]


def _resolve_existing_repo_root(raw_root: str | Path, *, source: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    if not root.exists():
        raise SeedProgramError(f"{source} does not exist: {root}")
    if not root.is_dir():
        raise SeedProgramError(f"{source} is not a directory: {root}")
    return root


def _resolve_repo_root_from_env() -> Path | None:
    for env_name in _REPO_ROOT_ENV_VARS:
        raw_root = os.getenv(env_name)
        if raw_root and raw_root.strip():
            return _resolve_existing_repo_root(raw_root, source=env_name)
    return None


def _iter_path_ancestors(path: Path) -> Iterable[Path]:
    yield path
    yield from path.parents


def _repo_root_from_program_manifest(manifest_path: Path) -> Path:
    for ancestor in _iter_path_ancestors(manifest_path.parent):
        if ancestor.name in {"configs", "modules"}:
            return ancestor.parent.resolve()
    raise SeedProgramError(
        "Program manifest is not under a recognized semantic root "
        f"(`configs` or `modules`): {manifest_path}"
    )


def _resolve_repo_root_from_program_path(program_path: Path) -> Path:
    resolved_program_path = program_path.expanduser().resolve()
    for ancestor in _iter_path_ancestors(resolved_program_path.parent):
        manifest_path = ancestor / "aware.programs.toml"
        if manifest_path.is_file():
            return _repo_root_from_program_manifest(manifest_path)
    raise SeedProgramError(
        "Cannot resolve repository root from program path. Pass `repo_root`, set "
        f"one of {', '.join(_REPO_ROOT_ENV_VARS)}, or place the program under an "
        f"`aware.programs.toml` semantic package: {resolved_program_path}"
    )


def _resolve_repo_root(
    *,
    program_path: Path,
    repo_root: str | Path | None = None,
) -> Path:
    if repo_root is not None and str(repo_root).strip():
        return _resolve_existing_repo_root(repo_root, source="repo_root")

    env_root = _resolve_repo_root_from_env()
    if env_root is not None:
        return env_root

    return _resolve_repo_root_from_program_path(program_path)


def _iter_program_manifests(*, repo_root: Path) -> Iterable[Path]:
    seeds_manifest = repo_root / "configs" / "seeds" / "aware.programs.toml"
    if seeds_manifest.exists():
        yield seeds_manifest

    modules_root = repo_root / "modules"
    if not modules_root.exists():
        return
    for module_dir in sorted(modules_root.iterdir(), key=lambda p: p.name):
        if not module_dir.is_dir():
            continue
        # Canonical module-owned programs live under experience packages.
        experience_root = module_dir / "experience"
        if experience_root.exists() and experience_root.is_dir():
            for experience_toml in sorted(
                experience_root.glob("**/aware.experience.toml")
            ):
                manifest_path = experience_toml.parent / "aware.programs.toml"
                if manifest_path.exists():
                    yield manifest_path

        # Legacy fallback for modules not yet migrated to experience packages.
        manifest_path = module_dir / "programs" / "aware.programs.toml"
        if manifest_path.exists():
            yield manifest_path


def _load_program_registry(*, repo_root: Path) -> dict[str, SeedProgramRegistryEntry]:
    entries: dict[str, SeedProgramRegistryEntry] = {}
    for manifest_path in _iter_program_manifests(repo_root=repo_root):
        try:
            spec = load_aware_programs_toml_spec(toml_path=manifest_path)
        except ValueError as exc:
            raise SeedProgramError(
                f"Invalid aware.programs.toml at {manifest_path}: {exc}"
            ) from exc

        programs_root = manifest_path.parent
        for row in list(spec.programs):
            parsed = ProgramAssetRef.parse(row.ref)
            source_path = (programs_root / row.path).resolve()
            if repo_root != source_path and repo_root not in source_path.parents:
                raise SeedProgramError(
                    "Program manifest path escapes repo root: "
                    f"manifest={manifest_path} path={row.path!r}"
                )
            if not source_path.exists():
                raise SeedProgramError(
                    "Program manifest source path not found: "
                    f"manifest={manifest_path} path={row.path!r}"
                )
            if not source_path.is_file():
                raise SeedProgramError(
                    "Program manifest source path is not a file: "
                    f"manifest={manifest_path} path={row.path!r}"
                )

            ref = parsed.value
            if ref in entries:
                prev = entries[ref]
                raise SeedProgramError(
                    "Duplicate program ref across manifests: "
                    f"{ref!r} (first={prev.source_path} second={source_path})"
                )

            entries[ref] = SeedProgramRegistryEntry(
                ref=ref,
                module_id=parsed.module_id,
                program_name=parsed.program_name,
                source_path=source_path,
                required_symbols=tuple(
                    (sym or "").strip()
                    for sym in list(row.required_symbols or [])
                    if (sym or "").strip()
                ),
                optional_symbols=tuple(
                    (sym or "").strip()
                    for sym in list(row.optional_symbols or [])
                    if (sym or "").strip()
                ),
            )

    return entries


def _validate_required_symbols(
    *,
    required_symbols: Iterable[str],
    provided_symbols: dict[str, object] | None,
    boot: BootContext | None,
    actor_id: UUID | None,
    context: str,
    program_ref: str,
) -> None:
    required = sorted(
        {(sym or "").strip() for sym in required_symbols if (sym or "").strip()}
    )
    if not required:
        return

    symbols = dict(provided_symbols or {})
    missing: list[str] = []
    for symbol in required:
        if symbol in symbols:
            continue
        if symbol == "plan.actor_id" and actor_id is not None:
            continue
        if symbol == "plan.environment_id" and boot is not None:
            continue
        if symbol == "plan.process_id" and boot is not None:
            continue
        if symbol == "plan.thread_id" and boot is not None:
            continue
        missing.append(symbol)

    if missing:
        raise SeedProgramError(
            f"{context} missing required symbols for {program_ref}: {missing}"
        )


def _resolve_profile_path(
    *,
    program_path: Path,
    profile_path: str | None,
) -> Path | None:
    if profile_path is not None and profile_path.strip():
        resolved = Path(profile_path).expanduser().resolve()
        if not resolved.exists():
            raise SeedProgramError(f"Kernel seed profile not found: {resolved}")
        return resolved

    env_path = os.getenv("AWARE_KERNEL_SEED_PROFILE")
    if env_path and env_path.strip():
        resolved = Path(env_path).expanduser().resolve()
        if not resolved.exists():
            raise SeedProgramError(
                f"Kernel seed profile from AWARE_KERNEL_SEED_PROFILE not found: {resolved}"
            )
        return resolved

    default_path = program_path.with_suffix(".profile.toml")
    if default_path.exists():
        return default_path.resolve()
    return None


def _flatten_profile_symbols(
    value: dict[str, Any],
    *,
    prefix: str = "",
) -> dict[str, object]:
    out: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        if not key:
            raise SeedProgramError("Kernel seed profile symbols contain an empty key")
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(raw_value, dict):
            out.update(_flatten_profile_symbols(raw_value, prefix=full_key))
            continue
        if not _is_supported_profile_symbol_value(raw_value):
            raise SeedProgramError(
                "Kernel seed profile symbol has unsupported value type: "
                f"{full_key} ({type(raw_value).__name__})"
            )
        out[full_key] = raw_value
    return out


def _is_supported_profile_symbol_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, list):
        return all(_is_supported_profile_symbol_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(k, str) and _is_supported_profile_symbol_value(v)
            for k, v in value.items()
        )
    return False


def _load_profile_symbols(*, profile_path: Path | None) -> dict[str, object]:
    if profile_path is None:
        return {}
    raw = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SeedProgramError(
            f"Kernel seed profile root must be a TOML table: {profile_path}"
        )
    aware = raw.get("aware")
    if aware != 1:
        raise SeedProgramError(
            f"Kernel seed profile must set aware = 1: {profile_path}"
        )

    symbols_raw = raw.get("symbols")
    if not isinstance(symbols_raw, dict):
        raise SeedProgramError(
            f"Kernel seed profile missing [symbols] table: {profile_path}"
        )

    symbols = _flatten_profile_symbols(symbols_raw)
    if not symbols:
        raise SeedProgramError(
            f"Kernel seed profile [symbols] must contain at least one symbol: {profile_path}"
        )
    return symbols


def _eval_symbol(name: str, symbols: dict[str, object]) -> object:
    key = (name or "").strip()
    if key in symbols:
        return symbols[key]
    # Default: treat as a symbolic literal (enum/value name).
    return key


def _get_call_arg(
    call: PlanCall, *, name: str, default: object | None = None
) -> object | None:
    for arg in call.args:
        if arg.name == name:
            return arg.value
    return default


class KernelSeedProgramExecutor:
    def __init__(
        self,
        *,
        endpoint: str,
        include_economy: bool,
        repo_root: Path,
        program_registry: dict[str, SeedProgramRegistryEntry],
        program_ref_stack: tuple[str, ...] = (),
        boot: BootContext | None = None,
        base_symbols: dict[str, object] | None = None,
        initial_identity_id: UUID | None = None,
        initial_actor_id: UUID | None = None,
        initial_identity_type: str | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._include_economy = include_economy
        self._repo_root = repo_root.resolve()
        self._program_registry = dict(program_registry)
        self._program_ref_stack = tuple(program_ref_stack)

        self._keypairs = load_seed_keypairs()

        self._boot: BootContext | None = boot
        self._base_symbols: dict[str, object] = dict(base_symbols or {})
        self._symbols: dict[str, object] = dict(self._base_symbols)
        self._locals: dict[str, object] = {}
        self._initial_identity_id = initial_identity_id
        self._initial_actor_id = initial_actor_id
        self._initial_identity_type = (
            initial_identity_type or ""
        ).strip().casefold() or None

        # Execution context (mutable)
        self._clients_by_identity: dict[UUID, AwareApiClient] = {}
        self._current_client: AwareApiClient | None = None
        self._current_identity_id: UUID | None = None
        self._current_actor_id: UUID | None = None
        self._current_identity_type: str | None = None

        self._opgs_by_name: dict[str, OpgRef] | None = None
        self._objects_by_name: dict[str, list[ObjectDescriptor]] | None = None
        self._current_lane_branch_id: UUID | None = None
        self._current_lane_opg_name: str | None = None
        self._current_lane_opg: OpgRef | None = None
        self._current_lane_head_commit_id: UUID | None = None
        self._skip_calls_in_lane: bool = False
        self._pending_lane_activation: PendingLaneActivation | None = None

        self._current_object_id: UUID | None = None
        self._active_actor_alias: str | None = None

        self._pure_fns: dict[str, Callable[..., object]] = {
            # Generic stable-id helpers.
            "stable.ns_url": stable_ns_url,
            "stable.uuid5": stable_uuid5,
            # Meta (OCG plane) stable ids.
            "meta.stable_class_config_id": stable_class_config_id,
            "meta.stable_attribute_config_id": stable_attribute_config_id,
            "meta.stable_class_relationship_id": stable_class_relationship_id,
            "meta.stable_function_config_id": stable_function_config_id,
            "meta.resolve_class_config_id": self._fn_meta_resolve_class_config_id,
            "meta.resolve_function_config_id": self._fn_meta_resolve_function_config_id,
            # Identity stable ids.
            "identity.stable_identity_id": self._fn_identity_stable_identity_id,
            "identity.stable_actor_id": stable_actor_id,
            "identity.stable_actor_id_for_key": stable_actor_id,
            "identity.stable_organization_id": stable_organization_id,
            "identity.stable_organization_member_id": stable_organization_member_id,
            # Agent stable ids.
            "agent.stable_agent_id": stable_agent_id,
            "agent.stable_agent_process_id": stable_agent_process_id,
            "agent.stable_agent_process_thread_id": stable_agent_process_thread_id,
            "agent.stable_agent_process_inference_model_id": stable_agent_process_inference_model_id,
            "agent.stable_inference_model_id": stable_inference_model_id,
            "agent.stable_inference_region_id": stable_inference_region_id,
            "agent.stable_inference_deployment_id": stable_inference_deployment_id,
            "agent.stable_inference_service_config_id": stable_inference_service_config_id,
            "agent.stable_inference_service_id": stable_inference_service_id,
            # Economy stable ids.
            "economy.stable_finance_entity_id": stable_finance_entity_id,
            "economy.stable_smart_contract_config_id": stable_smart_contract_config_id,
            "economy.stable_smart_contract_id": stable_smart_contract_id,
            # Service stable ids.
            "service.stable_service_config_id": stable_service_config_id,
            "service.stable_service_id": stable_service_id,
            # Kernel deterministic helpers.
            "kernel.seed_agent_profile_request": self._fn_kernel_seed_agent_profile_request,
            "kernel.symbols": self._fn_kernel_symbols,
            "kernel.list": self._fn_kernel_list,
            "economy.kernel_wallet_address": self._fn_kernel_wallet_address,
            "economy.kernel_wallet_public_key": self._fn_kernel_wallet_public_key,
            "economy.kernel_wallet_private_key_encrypted": self._fn_kernel_wallet_private_key_encrypted,
            "economy.kernel_wallet_id": self._fn_kernel_wallet_id,
        }
        self._dynamic_pure_fn_cache: dict[str, Callable[..., object]] = {}

    async def close(self) -> None:
        for client in self._clients_by_identity.values():
            await client.close()
        self._clients_by_identity.clear()

    # ------------------------------------------------------------------
    # Pure evaluation functions (program expressions)
    # ------------------------------------------------------------------

    def _fn_identity_stable_identity_id(
        self,
        *,
        public_key: str | None = None,
        public_key_bytes: bytes | None = None,
        identity_type_value: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> UUID:
        kind = (identity_type_value or type or "").strip()
        if not kind:
            raise SeedProgramError(
                "identity.stable_identity_id requires `identity_type_value` (alias: `type`)"
            )
        key_bytes = public_key_bytes
        if key_bytes is None:
            if public_key is None:
                raise SeedProgramError(
                    "identity.stable_identity_id requires `public_key` or `public_key_bytes`"
                )
            canonical_public_key, _ = canonicalize_ed25519_public_key(public_key)
        else:
            canonical_public_key = f"ed25519:{key_bytes.hex()}"
        return stable_identity_id(
            public_key=canonical_public_key,
            type=kind,
        )

    def _fn_kernel_seed_agent_profile_request(
        self,
        *,
        label: str,
        identity_id: UUID,
        seed_id: str,
        seed_version: int,
    ) -> dict[str, Any]:
        return build_seed_agent_profile_request(
            label=label,
            identity_id=identity_id,
            spec_id=seed_id,
            spec_version=int(seed_version),
        )

    def _fn_kernel_symbols(self, *args: object, **kwargs: object) -> dict[str, object]:
        out: dict[str, object] = {}
        if args:
            if len(args) % 2 != 0:
                raise SeedProgramError(
                    "kernel.symbols positional args must be alternating key/value pairs"
                )
            for i in range(0, len(args), 2):
                key_raw = str(args[i]).strip()
                if not key_raw:
                    raise SeedProgramError(
                        "kernel.symbols key must be a non-empty string"
                    )
                out[key_raw] = args[i + 1]
        for key, value in kwargs.items():
            rendered = str(key).strip()
            if rendered:
                out[rendered] = value
        return out

    def _fn_kernel_list(self, *args: object) -> list[object]:
        return list(args)

    def _kernel_wallet_seed(self, *, identity_id: UUID):
        return economy_wallet_seed(identity_id=identity_id)

    def _fn_kernel_wallet_address(self, *, identity_id: UUID) -> str:
        return self._kernel_wallet_seed(identity_id=identity_id).address

    def _fn_kernel_wallet_public_key(self, *, identity_id: UUID) -> str:
        return self._kernel_wallet_seed(identity_id=identity_id).public_key

    def _fn_kernel_wallet_private_key_encrypted(self, *, identity_id: UUID) -> str:
        return self._kernel_wallet_seed(identity_id=identity_id).private_key_encrypted

    def _fn_kernel_wallet_id(self, *, identity_id: UUID) -> UUID:
        return self._kernel_wallet_seed(identity_id=identity_id).wallet_id

    def _fn_meta_resolve_class_config_id(self, *, class_name: str) -> UUID:
        if self._objects_by_name is None:
            raise SeedProgramError(
                "meta.resolve_class_config_id requires capability index (set plan.actor before invoking)."
            )
        key = _lower_key(class_name)
        matches = list(self._objects_by_name.get(key, []))
        if not matches:
            available = sorted(self._objects_by_name.keys())
            raise SeedProgramError(
                f"Unknown capability object for class_name={class_name!r} (available={available})"
            )
        if len(matches) > 1:
            ids = sorted(str(obj.id) for obj in matches)
            raise SeedProgramError(
                f"Ambiguous capability object for class_name={class_name!r} (ids={ids})"
            )
        return matches[0].id

    def _fn_meta_resolve_function_config_id(
        self, *, class_name: str, function_name: str
    ) -> UUID:
        if self._objects_by_name is None:
            raise SeedProgramError(
                "meta.resolve_function_config_id requires capability index (set plan.actor before invoking)."
            )
        key = _lower_key(class_name)
        matches = list(self._objects_by_name.get(key, []))
        if not matches:
            available = sorted(self._objects_by_name.keys())
            raise SeedProgramError(
                f"Unknown capability object for class_name={class_name!r} (available={available})"
            )
        if len(matches) > 1:
            ids = sorted(str(obj.id) for obj in matches)
            raise SeedProgramError(
                f"Ambiguous capability object for class_name={class_name!r} (ids={ids})"
            )
        obj = matches[0]
        fn = next(
            (
                f
                for f in list(obj.functions or [])
                if (getattr(f, "name", None) or "") == function_name
            ),
            None,
        )
        if fn is None:
            available = sorted(
                {getattr(f, "name", "") for f in list(obj.functions or [])}
            )
            raise SeedProgramError(
                f"Function not found for class_name={class_name!r} function_name={function_name!r} "
                f"(available={available})"
            )
        return fn.id

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def _try_eval_symbol_strict(self, name: str) -> tuple[bool, object | None]:
        key = (name or "").strip()
        if key in self._symbols:
            return True, self._symbols[key]
        if key == "plan.actor_id" and self._current_actor_id is not None:
            return True, self._current_actor_id
        if key == "plan.identity_id" and self._current_identity_id is not None:
            return True, self._current_identity_id
        if key == "plan.identity_type" and self._current_identity_type is not None:
            return True, self._current_identity_type
        return False, None

    def _try_eval_input_source(self, expr: PlanExpr) -> tuple[bool, object | None]:
        if isinstance(expr, PlanLocalRef):
            if expr.name in self._locals:
                return True, self._locals[expr.name]
            return False, None
        if isinstance(expr, PlanSymbolRef):
            return self._try_eval_symbol_strict(expr.name)
        return True, self._eval_expr(expr)

    def _lookup_local_or_symbol(self, name: str) -> tuple[bool, object | None]:
        key = (name or "").strip()
        if not key:
            return False, None
        if key in self._locals:
            return True, self._locals[key]
        if key in self._symbols:
            return True, self._symbols[key]
        return self._try_eval_symbol_strict(key)

    def _try_resolve_port_projection_node_symbol(
        self,
        *,
        symbol_name: str,
    ) -> tuple[bool, object | None]:
        key = (symbol_name or "").strip()
        if not key:
            return False, None
        if not key.startswith("program.port.") or ".projection_node" not in key:
            return False, None
        if key in self._symbols:
            return True, self._symbols[key]

        prefix, marker, suffix = key.partition(".projection_node")
        if marker != ".projection_node":
            return False, None
        port_ref = prefix
        requested_node_key = suffix.removeprefix(".").strip() if suffix else ""

        resolved = False
        value: object | None = None
        if requested_node_key:
            resolved, value = self._try_resolve_port_node_selector(
                port_ref=port_ref,
                node_key=requested_node_key,
            )
        else:
            resolved, value = self._try_resolve_port_node_selector(
                port_ref=port_ref,
                node_key="main",
            )
        if not resolved and not requested_node_key:
            raw_contract = self._symbols.get(port_ref)
            if not isinstance(raw_contract, Mapping):
                return False, None
            projection_nodes = raw_contract.get("projection_nodes")
            if not isinstance(projection_nodes, Mapping) or len(projection_nodes) != 1:
                return False, None
            only_key = next(iter(projection_nodes.keys()))
            resolved, value = self._try_resolve_port_node_selector(
                port_ref=port_ref,
                node_key=str(only_key),
            )
            if not resolved:
                return False, None
        self._symbols[key] = value
        return True, value

    def _try_resolve_port_node_selector(
        self,
        *,
        port_ref: str,
        node_key: str,
    ) -> tuple[bool, object | None]:
        raw_contract = self._symbols.get(port_ref)
        if not isinstance(raw_contract, Mapping):
            return False, None
        projection_nodes = raw_contract.get("projection_nodes")
        if not isinstance(projection_nodes, Mapping):
            return False, None
        selected_contract = projection_nodes.get(node_key)
        if not isinstance(selected_contract, Mapping):
            return False, None

        raw_keys = selected_contract.get("keys")
        if isinstance(raw_keys, Mapping):
            key_values = list(raw_keys.values())
            if len(key_values) == 1:
                return True, self._eval_expr(key_values[0])
            if len(key_values) > 1:
                return False, None

        return False, None

    def _candidate_actor_stems(self, alias: str) -> tuple[str, ...]:
        key = (alias or "").strip()
        if not key:
            return ()
        tokens = [token for token in key.split("_") if token]
        if not tokens:
            return ()
        ordered: list[str] = []

        def _append(candidate: str) -> None:
            if candidate and candidate not in ordered:
                ordered.append(candidate)

        _append(key)
        n = len(tokens)
        for width in range(n - 1, 0, -1):
            for start in range(0, n - width + 1):
                _append("_".join(tokens[start : start + width]))
        return tuple(ordered)

    async def _ensure_actor_alias_context(
        self,
        *,
        actor_alias: str,
        actor_kind: str,
    ) -> None:
        alias = (actor_alias or "").strip()
        if not alias:
            raise SeedProgramError("Invoke actor alias cannot be empty")
        kind = (actor_kind or "").strip().casefold()
        if not kind:
            raise SeedProgramError(
                f"Invoke actor kind is empty for actor alias {alias!r}"
            )

        if self._active_actor_alias == alias and self._current_client is not None:
            return

        explicit_prefix = f"plan.actor.{alias}."
        explicit_identity_id_found, explicit_identity_id = self._lookup_local_or_symbol(
            f"{explicit_prefix}identity_id"
        )
        explicit_actor_id_found, explicit_actor_id = self._lookup_local_or_symbol(
            f"{explicit_prefix}actor_id"
        )
        explicit_identity_type_found, explicit_identity_type = (
            self._lookup_local_or_symbol(f"{explicit_prefix}identity_type")
        )

        identity_id: UUID | None = None
        actor_id: UUID | None = None
        identity_type: str | None = None
        if explicit_identity_id_found:
            identity_id = self._coerce_uuid(
                value=explicit_identity_id,
                label=f"plan.actor.{alias}.identity_id",
            )
        if explicit_actor_id_found:
            actor_id = self._coerce_uuid(
                value=explicit_actor_id,
                label=f"plan.actor.{alias}.actor_id",
            )
        if explicit_identity_type_found:
            identity_type = str(explicit_identity_type).strip().casefold()

        stems = self._candidate_actor_stems(alias)
        if identity_id is None:
            for stem in stems:
                found, value = self._lookup_local_or_symbol(f"{stem}_identity_id")
                if found:
                    identity_id = self._coerce_uuid(
                        value=value,
                        label=f"actor identity id for alias {alias!r}",
                    )
                    break
        if actor_id is None:
            for stem in stems:
                found, value = self._lookup_local_or_symbol(f"{stem}_actor_id")
                if found:
                    actor_id = self._coerce_uuid(
                        value=value,
                        label=f"actor id for alias {alias!r}",
                    )
                    break

        if identity_id is None:
            found, value = self._lookup_local_or_symbol("identity_id")
            if found:
                identity_id = self._coerce_uuid(
                    value=value,
                    label=f"identity_id for alias {alias!r}",
                )
        if actor_id is None:
            found, value = self._lookup_local_or_symbol("actor_id")
            if found:
                actor_id = self._coerce_uuid(
                    value=value,
                    label=f"actor_id for alias {alias!r}",
                )

        if identity_type is None:
            found, value = self._lookup_local_or_symbol("identity_type_value")
            if found:
                identity_type = str(value).strip().casefold()
        if identity_type is None:
            identity_type = kind

        if (
            (identity_id is None or actor_id is None)
            and self._current_identity_id is not None
            and self._current_actor_id is not None
        ):
            current_kind = (self._current_identity_type or "").strip().casefold()
            identity_id = (
                self._current_identity_id if identity_id is None else identity_id
            )
            actor_id = self._current_actor_id if actor_id is None else actor_id
            if not identity_type:
                identity_type = current_kind or kind

        if identity_id is None or actor_id is None:
            raise SeedProgramError(
                "Unable to resolve actor context for invoke actor alias "
                + f"{alias!r}; expected symbols like "
                + f"`plan.actor.{alias}.identity_id`/`actor_id` or "
                + "derived `<stem>_identity_id` + `<stem>_actor_id` locals"
            )

        await self._set_active_actor(
            identity_id=identity_id,
            actor_id=actor_id,
            identity_type=identity_type,
            overwrite_plan_symbols=True,
        )
        self._active_actor_alias = alias
        await self._ensure_capability_index()

    def _eval_expr(self, expr: PlanExpr) -> object:
        if isinstance(expr, PlanLocalRef):
            if expr.name not in self._locals:
                raise SeedProgramError(f"Undefined local reference: {expr.name!r}")
            return self._locals[expr.name]

        if isinstance(expr, PlanSymbolRef):
            symbol_name = (expr.name or "").strip()
            if symbol_name in self._locals:
                return self._locals[symbol_name]
            return _eval_symbol(expr.name, self._symbols)

        if isinstance(expr, PlanCall):
            fn = self._resolve_pure_fn(expr.target)
            if fn is None:
                available = sorted(self._pure_fns.keys())
                raise SeedProgramError(
                    f"Unsupported pure function call in program: {expr.target!r} (available={available})"
                )
            args, kwargs = self._eval_call_args(expr)
            return fn(*args, **kwargs)

        return expr

    def _eval_object_selector(self, *, expr: PlanExpr, call_target: str) -> object:
        if isinstance(expr, PlanSymbolRef):
            symbol_name = (expr.name or "").strip()
            if not symbol_name:
                raise SeedProgramError(
                    f"inline object selector for {call_target} cannot be empty"
                )
            resolved, value = self._lookup_local_or_symbol(symbol_name)
            if not resolved:
                resolved, value = self._try_resolve_port_projection_node_symbol(
                    symbol_name=symbol_name
                )
            if not resolved:
                current_port_ref = str(
                    self._symbols.get("plan.current_port_ref") or ""
                ).strip()
                if current_port_ref:
                    resolved, value = self._try_resolve_port_node_selector(
                        port_ref=current_port_ref,
                        node_key=symbol_name,
                    )
                    if resolved:
                        self._symbols[symbol_name] = value
            if not resolved:
                raise SeedProgramError(
                    f"inline object selector for {call_target} unresolved symbol: {symbol_name!r}"
                )
            return value
        return self._eval_expr(expr)

    def _resolve_pure_fn(self, target: str) -> Callable[..., object] | None:
        fn = self._pure_fns.get(target)
        if fn is not None:
            return fn

        cached = self._dynamic_pure_fn_cache.get(target)
        if cached is not None:
            return cached

        # Module-owned stable-id functions:
        # - `<module_id>.stable_<fn_name>` in programs
        # - Try generated ontology package first, then runtime package fallback.
        raw = (target or "").strip()
        if "." not in raw:
            return None
        module_id, fn_name = raw.split(".", 1)
        module_id = module_id.strip()
        fn_name = fn_name.strip()
        if not module_id or not fn_name.startswith("stable_"):
            return None
        if not all(ch.isalnum() or ch == "_" for ch in module_id):
            return None

        module_candidates = (
            f"aware_{module_id}_ontology.stable_ids",
            f"aware_{module_id}.stable_ids",
        )
        for module_name in module_candidates:
            try:
                mod = importlib.import_module(module_name)
            except ModuleNotFoundError:
                continue
            attr = getattr(mod, fn_name, None)
            if callable(attr):
                self._dynamic_pure_fn_cache[target] = attr
                return attr

        return None

    def _eval_call_args(self, call: PlanCall) -> tuple[list[object], dict[str, object]]:
        args: list[object] = []
        kwargs: dict[str, object] = {}
        for arg in call.args:
            value = self._eval_expr(arg.value)
            if arg.name is None:
                args.append(value)
            else:
                kwargs[arg.name] = value
        return args, kwargs

    # ------------------------------------------------------------------
    # Directives (program statements)
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_uuid(*, value: object, label: str) -> UUID:
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except Exception as exc:  # noqa: BLE001
            raise SeedProgramError(
                f"{label} must resolve to UUID, got {value!r}"
            ) from exc

    def _apply_input_contract(self, step: PlanInput) -> None:
        resolved, value = self._try_eval_input_source(step.source)
        if not resolved:
            if step.default is not None:
                value = self._eval_expr(step.default)
                resolved = True
            elif step.required:
                raise SeedProgramError(f"Required input unresolved: {step.name!r}")
        if not resolved:
            return
        self._locals[step.name] = value
        self._symbols[step.name] = value

    def _seed_compiled_port_contracts(
        self,
        *,
        ports: tuple[PlanPortContract, ...],
    ) -> None:
        for port in ports:
            key = (port.key or "").strip()
            if not key:
                raise SeedProgramError("Compiled port contract key cannot be empty")
            projection = str(port.projection or "").strip()
            if not projection:
                raise SeedProgramError(
                    f"Compiled port contract projection is required: {key!r}"
                )

            port_ref = f"program.port.{key}"
            node_contracts: dict[str, dict[str, object]] = {}
            for projection_node in port.projection_nodes:
                node_key = (projection_node.key or "").strip()
                if not node_key:
                    raise SeedProgramError(
                        f"Compiled port contract node key cannot be empty: {key!r}"
                    )
                node_ref = str(projection_node.node or "").strip()
                if not node_ref:
                    raise SeedProgramError(
                        f"Compiled port contract node ref is required: {key!r}.{node_key}"
                    )
                node_keys: dict[str, object] = {}
                for node_arg in projection_node.keys:
                    arg_name = (node_arg.name or "").strip()
                    if not arg_name:
                        raise SeedProgramError(
                            f"Compiled port contract node key name cannot be empty: {key!r}.{node_key}"
                        )
                    node_keys[arg_name] = node_arg.value_expr
                node_contracts[node_key] = {
                    "node": node_ref,
                    "keys": node_keys,
                }
            contract: dict[str, object] = {
                "projection": projection,
                "projection_nodes": node_contracts,
            }
            if port.intent:
                contract["intent"] = str(port.intent).strip()

            self._symbols[port_ref] = contract
            self._symbols[f"{port_ref}.projection"] = projection
            for node_key, node_contract in node_contracts.items():
                node_ref_value = node_contract.get("node")
                if isinstance(node_ref_value, str):
                    self._symbols[f"{port_ref}.node.{node_key}.node"] = node_ref_value
                node_keys_value = node_contract.get("keys")
                if isinstance(node_keys_value, dict):
                    for arg_name, arg_expr in node_keys_value.items():
                        self._symbols[f"{port_ref}.node.{node_key}.key.{arg_name}"] = (
                            arg_expr
                        )
            if port.intent:
                self._symbols[f"{port_ref}.intent"] = str(port.intent).strip()

    def _resolve_bind_port_contract(
        self,
        *,
        port_ref: str,
        port_value: object,
    ) -> tuple[UUID, str]:
        contract: dict[str, object]
        if isinstance(port_value, dict):
            contract = dict(port_value)
        else:
            from_symbol = self._symbols.get(port_ref)
            if isinstance(from_symbol, dict):
                contract = dict(from_symbol)
            else:
                contract = {
                    "projection": self._symbols.get(f"{port_ref}.projection"),
                }

        projection = str(contract.get("projection") or "").strip()
        branch_value: object | None = None
        if not projection:
            raise SeedProgramError(
                "bind unresolved port contract; expected projection on declared port"
            )

        port_key = ""
        if port_ref.startswith("program.port."):
            port_key = port_ref.removeprefix("program.port.").strip()
        projection_key = projection.replace(".", "_")
        candidate_symbol_names: tuple[str, ...] = (
            f"plan.{projection_key}_branch_id",
            f"plan.{port_key}_branch_id" if port_key else "",
            "plan.branch_id",
        )
        for symbol_name in candidate_symbol_names:
            if not symbol_name:
                continue
            if symbol_name in self._symbols:
                branch_value = self._symbols[symbol_name]
                break
            resolved, value = self._try_eval_symbol_strict(symbol_name)
            if resolved:
                branch_value = value
                break

        if branch_value is None:
            projection_nodes = contract.get("projection_nodes")
            if isinstance(projection_nodes, Mapping):
                selected_contract: Mapping[str, object] | None = None
                main_contract = projection_nodes.get("main")
                if isinstance(main_contract, Mapping):
                    selected_contract = main_contract
                else:
                    projection_node_key = projection.split(".")[-1].strip()
                    if projection_node_key:
                        projection_contract = projection_nodes.get(projection_node_key)
                        if isinstance(projection_contract, Mapping):
                            selected_contract = projection_contract
                if selected_contract is None and len(projection_nodes) == 1:
                    only_contract = next(iter(projection_nodes.values()))
                    if isinstance(only_contract, Mapping):
                        selected_contract = only_contract

                if selected_contract is not None:
                    node_ref = str(selected_contract.get("node") or "").strip()
                    node_leaf = node_ref.split(".")[-1].strip() if node_ref else ""
                    projection_leaf = projection.split(".")[-1].strip()
                    if node_leaf and projection_leaf and node_leaf == projection_leaf:
                        raw_keys = selected_contract.get("keys")
                        if isinstance(raw_keys, Mapping):
                            key_values = list(raw_keys.values())
                            if len(key_values) == 1:
                                branch_value = key_values[0]

        if (
            branch_value is None
            and self._current_lane_opg_name is not None
            and self._current_lane_branch_id is not None
            and self._current_lane_opg_name.strip() == projection
        ):
            branch_value = self._current_lane_branch_id

        if branch_value is None:
            raise SeedProgramError(
                "bind unresolved branch contract; expected one of "
                + ", ".join(name for name in candidate_symbol_names if name)
            )
        if isinstance(branch_value, PlanLocalRef):
            local_name = (branch_value.name or "").strip()
            if local_name and local_name in self._locals:
                branch_value = self._locals[local_name]
            else:
                branch_value = self._eval_expr(branch_value)
        elif isinstance(branch_value, PlanSymbolRef):
            symbol_name = (branch_value.name or "").strip()
            if symbol_name in self._locals:
                branch_value = self._locals[symbol_name]
            elif symbol_name in self._symbols:
                branch_value = self._symbols[symbol_name]
            else:
                resolved, resolved_value = self._try_eval_symbol_strict(symbol_name)
                if resolved:
                    branch_value = resolved_value
                else:
                    branch_value = self._eval_expr(branch_value)
        elif isinstance(branch_value, PlanCall):
            branch_value = self._eval_expr(branch_value)
        elif isinstance(branch_value, str):
            raw_symbol = branch_value.strip()
            if raw_symbol:
                if raw_symbol in self._locals:
                    branch_value = self._locals[raw_symbol]
                elif raw_symbol in self._symbols:
                    branch_value = self._symbols[raw_symbol]
                else:
                    resolved, resolved_value = self._try_eval_symbol_strict(raw_symbol)
                    if resolved:
                        branch_value = resolved_value

        branch_id = self._coerce_uuid(
            value=branch_value,
            label=f"bind branch id for projection {projection}",
        )
        return branch_id, projection

    async def _ensure_opg_index(self) -> None:
        if self._opgs_by_name is not None:
            return
        if self._current_client is None:
            raise SeedProgramError("plan.lane requires an active actor (plan.actor)")
        desc = await self._current_client.describe_environment_config()
        opgs_by_name: dict[str, OpgRef] = {}
        for opg in list(desc.opgs or []):
            name = (opg.name or "").strip()
            if not name:
                continue
            projection_hash = (opg.projection_hash or "").strip()
            if not projection_hash:
                continue
            opgs_by_name[_lower_key(name)] = OpgRef(
                opg_id=opg.id,
                projection_hash=projection_hash,
            )
        if not opgs_by_name:
            raise SeedProgramError(
                "describe_environment_config returned no resolvable OPGs"
            )
        self._opgs_by_name = opgs_by_name

    async def _ensure_capability_index(self) -> None:
        if self._objects_by_name is not None:
            return
        if self._current_client is None:
            raise SeedProgramError(
                "Function resolution requires an active actor (plan.actor)"
            )
        envelope = await self._current_client.fetch_capabilities(force_refresh=True)
        objects_by_name: dict[str, list[ObjectDescriptor]] = {}
        for obj in list(envelope.objects or []):
            name = (obj.name or "").strip()
            if not name:
                continue
            objects_by_name.setdefault(_lower_key(name), []).append(obj)
        if not objects_by_name:
            raise SeedProgramError(
                "fetch_capabilities returned no resolvable objects; cannot resolve call targets"
            )
        self._objects_by_name = objects_by_name

    async def _ensure_client_for_actor(
        self,
        *,
        identity_id: UUID,
        actor_id: UUID,
        identity_type: str,
    ) -> AwareApiClient:
        if self._boot is None:
            raise SeedProgramError("plan.actor requires boot context to be resolved")
        client = self._clients_by_identity.get(identity_id)
        if client is not None:
            return client

        keypair = resolve_seed_keypair(
            keypairs=self._keypairs,
            identity_id=identity_id,
            identity_type_value=identity_type,
        )
        client = AwareApiClient(
            AwareApiConfig(endpoint=self._endpoint, actor_id=actor_id)
        )
        client.set_context(
            AwareApiContext(
                environment_id=self._boot.environment_id,
                process_id=self._boot.process_id,
                thread_id=self._boot.thread_id,
                branch_id=None,
                projection_hash=None,
            )
        )
        await client.authenticate_identity_session(
            public_key=keypair.public_key,
            private_key=keypair.private_key,
        )
        self._clients_by_identity[identity_id] = client
        return client

    async def _set_active_actor(
        self,
        *,
        identity_id: UUID,
        actor_id: UUID,
        identity_type: str,
        overwrite_plan_symbols: bool = True,
    ) -> None:
        normalized_type = (identity_type or "").strip().casefold()
        if not normalized_type:
            raise SeedProgramError("plan.actor identity_type is empty")
        self._current_identity_id = identity_id
        self._current_actor_id = actor_id
        self._current_identity_type = normalized_type
        if overwrite_plan_symbols:
            self._symbols["plan.identity_id"] = identity_id
            self._symbols["plan.actor_id"] = actor_id
            self._symbols["plan.identity_type"] = normalized_type
        else:
            # Nested program symbols may intentionally shadow inherited actor context.
            self._symbols.setdefault("plan.identity_id", identity_id)
            self._symbols.setdefault("plan.actor_id", actor_id)
            self._symbols.setdefault("plan.identity_type", normalized_type)
        self._current_client = await self._ensure_client_for_actor(
            identity_id=identity_id,
            actor_id=actor_id,
            identity_type=normalized_type,
        )
        if (
            self._current_lane_branch_id is not None
            and self._current_lane_opg_name is not None
        ):
            self._pending_lane_activation = PendingLaneActivation(
                branch_id=self._current_lane_branch_id,
                opg_name=self._current_lane_opg_name,
                require_head=False,
                skip_if_head=False,
            )
            self._current_lane_branch_id = None
            self._current_lane_opg_name = None
            self._current_lane_opg = None
            self._current_lane_head_commit_id = None
            self._skip_calls_in_lane = False
            self._current_object_id = None
        # Describe cache is actor-scoped; force rebuild on actor switch.
        self._opgs_by_name = None
        self._objects_by_name = None

    async def _apply_actor_directive(self, call: PlanCall) -> None:
        if self._boot is None:
            raise SeedProgramError("plan.actor requires boot context to be resolved")
        # Required args (by name).
        raw_identity_id = _get_call_arg(call, name="identity_id")
        raw_actor_id = _get_call_arg(call, name="actor_id")
        raw_identity_type = _get_call_arg(call, name="identity_type")

        if raw_identity_id is None or raw_actor_id is None or raw_identity_type is None:
            raise SeedProgramError(
                "plan.actor requires identity_id, actor_id, identity_type"
            )

        identity_id = UUID(str(self._eval_expr(raw_identity_id)))
        actor_id = UUID(str(self._eval_expr(raw_actor_id)))
        identity_type = str(self._eval_expr(raw_identity_type)).strip().casefold()
        await self._set_active_actor(
            identity_id=identity_id,
            actor_id=actor_id,
            identity_type=identity_type,
            overwrite_plan_symbols=True,
        )
        self._active_actor_alias = None
        await self._ensure_capability_index()

    async def _activate_lane(
        self,
        *,
        branch_id: UUID,
        opg_name: str,
        require_head: bool = False,
        skip_if_head: bool = False,
    ) -> None:
        if self._boot is None:
            raise SeedProgramError(
                "lane activation requires boot context to be resolved"
            )
        if self._current_client is None:
            raise SeedProgramError(
                "lane activation requires an active actor (plan.actor)"
            )

        await self._ensure_opg_index()
        assert self._opgs_by_name is not None
        opg = self._opgs_by_name.get(_lower_key(opg_name))
        if opg is None:
            available = sorted(self._opgs_by_name.keys())
            raise SeedProgramError(
                f"Unknown OPG name in lane activation: {opg_name!r} (available={available})"
            )

        # Economy toggle: allow callers to omit economy lanes by flag.
        if not self._include_economy and _lower_key(opg_name) in {
            "wallet",
            "finance_entity",
            "service_config",
            "service",
            "smart_contract_config",
            "smart_contract",
        }:
            self._current_lane_branch_id = branch_id
            self._current_lane_opg_name = opg_name
            self._current_lane_opg = opg
            self._current_lane_head_commit_id = None
            self._skip_calls_in_lane = True
            self._current_object_id = None
            return

        ctx = self._current_client.get_context()
        self._current_client.set_context(
            AwareApiContext(
                environment_id=ctx.environment_id,
                process_id=ctx.process_id,
                thread_id=ctx.thread_id,
                branch_id=branch_id,
                projection_hash=opg.projection_hash,
            )
        )

        self._current_lane_branch_id = branch_id
        self._current_lane_opg_name = opg_name
        self._current_lane_opg = opg
        self._current_object_id = None

        head = await self._current_client.get_lane_head(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
        )
        self._current_lane_head_commit_id = head.commit_id
        if require_head and head.commit_id is None:
            raise SeedProgramError(
                "Required lane HEAD is missing for bind/lane activation "
                f"(branch_id={branch_id} opg={opg_name!r} projection_hash={opg.projection_hash})"
            )
        self._skip_calls_in_lane = bool(skip_if_head and head.commit_id is not None)

    async def _apply_lane_directive(self, call: PlanCall) -> None:
        raw_branch_id = _get_call_arg(call, name="branch_id")
        raw_opg = _get_call_arg(call, name="opg")
        if raw_branch_id is None or raw_opg is None:
            raise SeedProgramError("plan.lane requires branch_id and opg")

        branch_id = self._coerce_uuid(
            value=self._eval_expr(raw_branch_id),
            label="plan.lane branch_id",
        )
        opg_name = str(self._eval_expr(raw_opg)).strip()
        if not opg_name:
            raise SeedProgramError("plan.lane opg is empty")
        skip_if_head = bool(
            self._eval_expr(
                _get_call_arg(call, name="skip_if_head", default=False) or False
            )
        )
        await self._activate_lane(
            branch_id=branch_id,
            opg_name=opg_name,
            skip_if_head=skip_if_head,
        )

    async def _apply_bind_directive(self, call: PlanCall) -> None:
        raw_port = _get_call_arg(call, name="port")
        if raw_port is None:
            raw_port = _get_call_arg(call, name="port_ref")
        if raw_port is None:
            raw_port = _get_call_arg(call, name="program_config_port")
        if raw_port is None:
            raw_port = _get_call_arg(call, name="program_config_port_ref")
        if raw_port is None:
            raise SeedProgramError(
                "bind requires `port` (aliases: `port_ref`, `program_config_port`, `program_config_port_ref`)"
            )

        raw_view_key = _get_call_arg(call, name="view_key")
        if raw_view_key is None:
            raw_view_key = _get_call_arg(call, name="view")
        if raw_view_key is None:
            raise SeedProgramError("bind requires `view_key` (alias: `view`)")
        view_key = str(self._eval_expr(raw_view_key)).strip()
        if not view_key:
            raise SeedProgramError("bind view_key cannot be empty")

        raw_is_active = _get_call_arg(call, name="is_active", default=True)
        is_active = self._eval_expr(raw_is_active)
        if not isinstance(is_active, bool):
            raise SeedProgramError("bind is_active must be a boolean")

        self._symbols["plan.current_view_key"] = view_key
        if not is_active:
            self._current_lane_branch_id = None
            self._current_lane_opg_name = None
            self._current_lane_opg = None
            self._current_lane_head_commit_id = None
            self._skip_calls_in_lane = False
            self._current_object_id = None
            self._pending_lane_activation = None
            return

        port_value = self._eval_expr(raw_port)
        port_ref = ""
        if isinstance(raw_port, PlanSymbolRef):
            port_ref = (raw_port.name or "").strip()
        elif isinstance(port_value, str):
            port_ref = port_value.strip()
        if not port_ref:
            raise SeedProgramError(
                "bind port must be provided as a symbolic reference (for example `program.port.main`)"
            )

        branch_id, opg_name = self._resolve_bind_port_contract(
            port_ref=port_ref,
            port_value=port_value,
        )
        require_head = bool(
            self._eval_expr(_get_call_arg(call, name="require_head", default=False))
        )
        skip_if_head = bool(
            self._eval_expr(_get_call_arg(call, name="skip_if_head", default=False))
        )
        self._pending_lane_activation = PendingLaneActivation(
            branch_id=branch_id,
            opg_name=opg_name,
            require_head=require_head,
            skip_if_head=skip_if_head,
        )
        if self._current_client is not None:
            pending = self._pending_lane_activation
            assert pending is not None
            await self._activate_lane(
                branch_id=pending.branch_id,
                opg_name=pending.opg_name,
                require_head=pending.require_head,
                skip_if_head=pending.skip_if_head,
            )
            self._pending_lane_activation = None
        self._symbols["plan.current_port_ref"] = port_ref
        self._symbols[f"{port_ref}.branch_id"] = branch_id

    def _apply_object_directive(self, call: PlanCall) -> None:
        raw_object_id = _get_call_arg(call, name="object_id")
        if raw_object_id is None:
            raise SeedProgramError("plan.object requires object_id")
        self._current_object_id = UUID(str(self._eval_expr(raw_object_id)))

    async def _apply_program_ref_directive(self, call: PlanCall) -> None:
        raw_program_ref = _get_call_arg(call, name="program_ref")
        if raw_program_ref is None:
            raise SeedProgramError("plan.apply_program_ref requires program_ref")

        target_ref = str(self._eval_expr(raw_program_ref)).strip()
        if not target_ref:
            raise SeedProgramError("plan.apply_program_ref program_ref is empty")
        if target_ref in self._program_ref_stack:
            chain = " -> ".join([*self._program_ref_stack, target_ref])
            raise SeedProgramError(
                f"Cycle detected in plan.apply_program_ref chain: {chain}"
            )

        parsed_ref = ProgramAssetRef.parse(target_ref)
        entry = self._program_registry.get(parsed_ref.value)
        if entry is None:
            available = sorted(self._program_registry.keys())
            raise SeedProgramError(
                "Program ref not declared in aware.programs.toml registry: "
                f"{parsed_ref.value!r} (available={available})"
            )

        nested_symbols: dict[str, object] = {}
        raw_symbols = _get_call_arg(call, name="symbols", default=None)
        if raw_symbols is not None:
            evaluated = self._eval_expr(raw_symbols)
            if not isinstance(evaluated, dict):
                raise SeedProgramError(
                    "plan.apply_program_ref symbols must evaluate to an object/map"
                )
            nested_symbols = {
                str(k): v for k, v in dict(evaluated).items() if str(k).strip()
            }

        _validate_required_symbols(
            required_symbols=entry.required_symbols,
            provided_symbols=nested_symbols,
            boot=self._boot,
            actor_id=self._current_actor_id,
            context="plan.apply_program_ref",
            program_ref=entry.ref,
        )

        nested_src = entry.source_path.read_text(encoding="utf-8")
        nested_plan = _compile_program_by_ref(
            src=nested_src,
            program_name=entry.program_name,
        )

        nested_executor = KernelSeedProgramExecutor(
            endpoint=self._endpoint,
            include_economy=self._include_economy,
            repo_root=self._repo_root,
            program_registry=self._program_registry,
            program_ref_stack=(*self._program_ref_stack, entry.ref),
            boot=self._boot,
            base_symbols=nested_symbols,
            initial_identity_id=self._current_identity_id,
            initial_actor_id=self._current_actor_id,
            initial_identity_type=self._current_identity_type,
        )
        try:
            await nested_executor.execute(nested_plan)
        finally:
            await nested_executor.close()

    async def _resolve_function_descriptor(
        self, *, owner: str, fn_name: str
    ) -> tuple[ObjectDescriptor, FunctionDescriptor]:
        await self._ensure_capability_index()
        assert self._objects_by_name is not None

        owner_raw = (owner or "").strip()
        object_name = owner_raw.split(".")[-1]
        object_key = _lower_key(object_name)
        matches = list(self._objects_by_name.get(object_key, []))
        if not matches:
            available = sorted(self._objects_by_name.keys())
            raise SeedProgramError(
                f"Unknown capability object: {object_name!r} (available={available})"
            )
        if len(matches) > 1:
            fn_matches = [
                obj
                for obj in matches
                if any(f.name == fn_name for f in list(obj.functions or []))
            ]
            if fn_matches:
                matches = fn_matches

        if len(matches) > 1:
            owner_tokens = _tokenize(" ".join(owner_raw.split(".")[:-1]))
            if owner_tokens:
                scored: list[tuple[int, ObjectDescriptor]] = []
                for obj in matches:
                    obj_tokens = set(
                        _tokenize(obj.name or "") + _tokenize(obj.description or "")
                    )
                    score = sum(1 for token in owner_tokens if token in obj_tokens)
                    if score > 0:
                        scored.append((score, obj))
                if scored:
                    best_score = max(score for score, _ in scored)
                    matches = [obj for score, obj in scored if score == best_score]

        if len(matches) > 1:
            ids = sorted(str(obj.id) for obj in matches)
            raise SeedProgramError(
                "Ambiguous capability object: "
                f"{object_name!r} for owner={owner_raw!r} fn={fn_name!r} (ids={ids})"
            )

        obj = matches[0]
        fn = next(
            (f for f in list(obj.functions or []) if f.name == fn_name),
            None,
        )
        if fn is None:
            available = sorted({f.name for f in list(obj.functions or [])})
            raise SeedProgramError(
                f"Function not found on {object_name}: {fn_name!r} (available={available})"
            )
        return obj, fn

    # ------------------------------------------------------------------
    # Commit-backed invocation
    # ------------------------------------------------------------------

    async def _invoke_call(self, call: PlanCall) -> None:
        if self._pending_lane_activation is not None:
            if self._current_client is None:
                raise SeedProgramError(
                    "Invocation requires an active actor before bind/lane activation"
                )
            pending = self._pending_lane_activation
            await self._activate_lane(
                branch_id=pending.branch_id,
                opg_name=pending.opg_name,
                require_head=pending.require_head,
                skip_if_head=pending.skip_if_head,
            )
            self._pending_lane_activation = None
        if self._skip_calls_in_lane:
            return
        if self._current_client is None or self._current_actor_id is None:
            raise SeedProgramError("Invocation requires an active actor (plan.actor)")
        if self._current_lane_branch_id is None or self._current_lane_opg is None:
            raise SeedProgramError("Invocation requires an active lane (plan.lane)")

        owner, fn_name = _split_call_target(call.target)
        _obj, fn = await self._resolve_function_descriptor(owner=owner, fn_name=fn_name)
        args, kwargs = self._eval_call_args(call)

        is_constructor = fn.is_constructor
        if is_constructor:
            # Skip construct calls when the lane already has a head (idempotent seed apply).
            if self._current_lane_head_commit_id is not None:
                return
            req = FunctionCallRequest(
                call_target="opg_constructor",
                object_id=None,
                object_projection_graph_id=self._current_lane_opg.opg_id,
                function_id=fn.id,
                args=list(args),
                kwargs=dict(kwargs),
                actor_id=self._current_actor_id,
                commit=True,
                publish=False,
            )
        else:
            object_id: UUID | None = None
            if call.object_expr is not None:
                object_value = self._eval_object_selector(
                    expr=call.object_expr,
                    call_target=call.target,
                )
                object_id = self._coerce_uuid(
                    value=object_value,
                    label=f"inline object selector for {call.target}",
                )
            elif self._current_object_id is not None:
                # Backward compatibility for legacy seed plans.
                object_id = self._current_object_id
            if object_id is None:
                raise SeedProgramError(
                    "Instance call requires inline object selector "
                    f"`call <object_id> {call.target}(...)`"
                )
            use_constructor_path = (
                self._current_lane_head_commit_id is None
                and self._current_lane_branch_id is not None
                and object_id == self._current_lane_branch_id
                and fn_name in {"signup", "signup_via_profile"}
            )
            if use_constructor_path:
                req = FunctionCallRequest(
                    call_target="opg_constructor",
                    object_id=None,
                    object_projection_graph_id=self._current_lane_opg.opg_id,
                    function_id=fn.id,
                    args=list(args),
                    kwargs=dict(kwargs),
                    actor_id=self._current_actor_id,
                    commit=True,
                    publish=False,
                )
            else:
                req = FunctionCallRequest(
                    call_target="instance",
                    object_id=object_id,
                    object_projection_graph_id=None,
                    function_id=fn.id,
                    args=list(args),
                    kwargs=dict(kwargs),
                    actor_id=self._current_actor_id,
                    commit=True,
                    publish=False,
                )

        try:
            await self._current_client.invoke_function(req)
        except Exception as exc:  # noqa: BLE001
            lane_branch = self._current_lane_branch_id
            raise SeedProgramError(
                "invoke failed for call target "
                + f"{call.target!r} in branch={lane_branch}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Plan execution
    # ------------------------------------------------------------------

    def _reset_program_state(self) -> None:
        self._symbols = dict(self._base_symbols)
        self._locals.clear()
        self._current_client = None
        self._current_identity_id = self._initial_identity_id
        self._current_actor_id = self._initial_actor_id
        self._current_identity_type = self._initial_identity_type
        self._opgs_by_name = None
        self._objects_by_name = None
        self._current_lane_branch_id = None
        self._current_lane_opg_name = None
        self._current_lane_opg = None
        self._current_lane_head_commit_id = None
        self._skip_calls_in_lane = False
        self._pending_lane_activation = None
        self._current_object_id = None
        self._active_actor_alias = None

    async def execute(self, plan: InvocationPlan) -> None:
        self._reset_program_state()
        # Boot context is fetched once from the node-managed BOOT environment.
        if self._boot is None:
            boot_client = AwareApiClient(
                AwareApiConfig(endpoint=self._endpoint, actor_id=UUID(int=0))
            )
            try:
                self._boot = await _resolve_boot_context(client=boot_client)
            finally:
                await boot_client.close()
        assert self._boot is not None
        self._symbols["boot.environment_id"] = self._boot.environment_id
        self._symbols["boot.process_id"] = self._boot.process_id
        self._symbols["boot.thread_id"] = self._boot.thread_id
        # `plan.*` are canonical executor-provided symbols.
        self._symbols.setdefault("plan.environment_id", self._boot.environment_id)
        self._symbols.setdefault("plan.process_id", self._boot.process_id)
        self._symbols.setdefault("plan.thread_id", self._boot.thread_id)
        self._seed_compiled_port_contracts(ports=plan.ports)
        if (
            self._current_identity_id is not None
            and self._current_actor_id is not None
            and self._current_identity_type is not None
        ):
            await self._set_active_actor(
                identity_id=self._current_identity_id,
                actor_id=self._current_actor_id,
                identity_type=self._current_identity_type,
                overwrite_plan_symbols=False,
            )
            await self._ensure_capability_index()

        actor_kinds_by_alias = {
            (contract.key or "").strip(): (contract.actor or "").strip()
            for contract in plan.actors
            if (contract.key or "").strip()
        }

        for step in plan.steps:
            if isinstance(step, PlanInput):
                self._apply_input_contract(step)
                continue

            if isinstance(step, PlanLet):
                self._locals[step.name] = self._eval_expr(step.value)
                continue

            if isinstance(step, PlanInvoke):
                step_actor = (step.actor or "").strip()
                if step_actor:
                    actor_kind = actor_kinds_by_alias.get(step_actor, "")
                    if not actor_kind:
                        raise SeedProgramError(
                            f"Invoke references undeclared actor alias: {step_actor!r}"
                        )
                    await self._ensure_actor_alias_context(
                        actor_alias=step_actor,
                        actor_kind=actor_kind,
                    )
                # Directives are call statements with reserved targets.
                if step.call.target == "bind":
                    await self._apply_bind_directive(step.call)
                    continue
                if step.call.target == "plan.actor":
                    await self._apply_actor_directive(step.call)
                    continue
                if step.call.target == "plan.lane":
                    await self._apply_lane_directive(step.call)
                    continue
                if step.call.target == "plan.object":
                    self._apply_object_directive(step.call)
                    continue
                if step.call.target == "plan.apply_program_ref":
                    await self._apply_program_ref_directive(step.call)
                    continue

                await self._invoke_call(step.call)
                continue

            raise SeedProgramError(f"Unsupported plan step: {type(step).__name__}")


async def apply_kernel_seed_program(
    *,
    program_path: str,
    repo_root: str | Path | None = None,
    profile_path: str | None = None,
    endpoint: str | None = None,
    include_economy: bool = True,
) -> None:
    """
    Apply a kernel seed expressed as a `.aware program` invocation plan.

    This is the migration target for `seed_apply.py`: program becomes SSOT, and
    the runner interprets it into commit-backed FunctionCalls.
    """

    node_endpoint = _resolve_node_endpoint(override=endpoint)
    source_path = Path(program_path).expanduser().resolve()
    resolved_repo_root = _resolve_repo_root(
        program_path=source_path,
        repo_root=repo_root,
    )
    registry = _load_program_registry(repo_root=resolved_repo_root)
    resolved_profile_path = _resolve_profile_path(
        program_path=source_path,
        profile_path=profile_path,
    )
    profile_symbols = _load_profile_symbols(profile_path=resolved_profile_path)

    src = source_path.read_text(encoding="utf-8")
    plans = compile_invocation_plans(src)
    if not plans:
        raise SeedProgramError(f"No program declarations found in: {program_path}")
    if len(plans) != 1:
        raise SeedProgramError(
            f"Kernel seed program file must contain exactly one program (found={len(plans)})"
        )
    plan = plans[0]

    kernel_entry = registry.get("kernel:KernelSeed")
    if kernel_entry is not None:
        _validate_required_symbols(
            required_symbols=kernel_entry.required_symbols,
            provided_symbols=profile_symbols,
            boot=None,
            actor_id=None,
            context="apply_kernel_seed_program",
            program_ref=kernel_entry.ref,
        )

    exec_ = KernelSeedProgramExecutor(
        endpoint=node_endpoint,
        include_economy=include_economy,
        repo_root=resolved_repo_root,
        program_registry=registry,
        program_ref_stack=("kernel:KernelSeed",),
        base_symbols=profile_symbols,
    )
    try:
        await exec_.execute(plan)
    finally:
        await exec_.close()


__all__ = [
    "KernelSeedProgramExecutor",
    "SeedProgramError",
    "apply_kernel_seed_program",
]
