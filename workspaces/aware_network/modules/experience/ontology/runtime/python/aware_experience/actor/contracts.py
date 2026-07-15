from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict

from aware_experience.compiler.models import ExperienceActorRoleContract

_TModel = TypeVar("_TModel", bound=BaseModel)


class _BindingsRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    class_fqn: str | None = None


class _BindingsManifest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    bindings: tuple[_BindingsRow, ...] = ()


class _EnvironmentManifestArtifact(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    file: str


class _EnvironmentManifestCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    bindings: _EnvironmentManifestArtifact | None = None


class _CompositionModuleRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    manifest_path: str


class _CompositionManifestCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    modules: tuple[_CompositionModuleRow, ...] = ()


def load_actor_role_contract(
    *,
    composition_manifest_path: Path,
    repo_root: Path,
) -> ExperienceActorRoleContract | None:
    return load_actor_role_contract_from_runtime_manifests(
        environment_runtime_manifest_paths=_manifest_paths_from_composition_manifest(
            composition_manifest_path=composition_manifest_path,
            repo_root=repo_root,
        ),
        repo_root=repo_root,
    )


def load_actor_role_contract_from_runtime_manifests(
    *,
    environment_runtime_manifest_paths: Sequence[Path],
    repo_root: Path,
) -> ExperienceActorRoleContract | None:
    actor_configs_by_prefix: dict[str, str] = {}
    role_configs_by_prefix: dict[str, str] = {}
    for class_fqn in _iter_runtime_binding_class_fqns(
        environment_runtime_manifest_paths=environment_runtime_manifest_paths,
        repo_root=repo_root,
    ):
        actor_prefix = _contract_package_prefix(
            class_fqn=class_fqn,
            suffix=".actor.actor_config.ActorConfig",
        )
        if actor_prefix is not None:
            _record_unique_contract_class(
                classes_by_prefix=actor_configs_by_prefix,
                package_prefix=actor_prefix,
                class_fqn=class_fqn,
                label="ActorConfig",
            )
            continue
        role_prefix = _contract_package_prefix(
            class_fqn=class_fqn,
            suffix=".role.role_config.RoleConfig",
        )
        if role_prefix is not None:
            _record_unique_contract_class(
                classes_by_prefix=role_configs_by_prefix,
                package_prefix=role_prefix,
                class_fqn=class_fqn,
                label="RoleConfig",
            )
    if not actor_configs_by_prefix and not role_configs_by_prefix:
        return None

    contract_prefixes = tuple(
        sorted(set(actor_configs_by_prefix).intersection(role_configs_by_prefix))
    )
    if len(contract_prefixes) == 1:
        contract_prefix = contract_prefixes[0]
        return ExperienceActorRoleContract(
            actor_config_class_fqn=actor_configs_by_prefix[contract_prefix],
            role_config_class_fqn=role_configs_by_prefix[contract_prefix],
        )

    if not contract_prefixes:
        raise ValueError(
            "Incomplete actor-role contract in composition: both ActorConfig and RoleConfig classes are required"
        )
    raise ValueError(
        "Ambiguous actor-role contract across composition: "
        + f"package_prefixes={contract_prefixes!r}"
    )


def _contract_package_prefix(*, class_fqn: str, suffix: str) -> str | None:
    if not class_fqn.endswith(suffix):
        return None
    return class_fqn[: -len(suffix)]


def _record_unique_contract_class(
    *,
    classes_by_prefix: dict[str, str],
    package_prefix: str,
    class_fqn: str,
    label: str,
) -> None:
    prior = classes_by_prefix.get(package_prefix)
    if prior is not None and prior != class_fqn:
        raise ValueError(
            f"Ambiguous {label} contract for package prefix {package_prefix!r}: "
            + f"{prior!r} vs {class_fqn!r}"
        )
    classes_by_prefix[package_prefix] = class_fqn


def _iter_composed_binding_class_fqns(
    *,
    composition_manifest_path: Path,
    repo_root: Path,
) -> tuple[str, ...]:
    return _iter_runtime_binding_class_fqns(
        environment_runtime_manifest_paths=_manifest_paths_from_composition_manifest(
            composition_manifest_path=composition_manifest_path,
            repo_root=repo_root,
        ),
        repo_root=repo_root,
    )


def _iter_runtime_binding_class_fqns(
    *,
    environment_runtime_manifest_paths: Sequence[Path],
    repo_root: Path,
) -> tuple[str, ...]:
    repo_root = repo_root.resolve()
    if not environment_runtime_manifest_paths:
        return ()

    class_fqns: list[str] = []
    for idx, module_manifest_path in enumerate(environment_runtime_manifest_paths):
        module_manifest_path = _resolve_runtime_manifest_path(
            module_manifest_path=module_manifest_path,
            repo_root=repo_root,
            module_idx=idx,
        )
        module_manifest = _load_json_model(
            module_manifest_path, _EnvironmentManifestCompat
        )
        module_runtime_dir = module_manifest_path.parent
        bindings = module_manifest.bindings
        if bindings is None:
            continue
        bindings_relpath = bindings.file.strip()
        if not bindings_relpath:
            continue
        bindings_path = (module_runtime_dir / bindings_relpath).resolve()
        _assert_within(
            base=module_runtime_dir, candidate=bindings_path, label="bindings path"
        )
        if not bindings_path.exists():
            continue
        bindings_payload = _load_json_model(bindings_path, _BindingsManifest)
        for row in bindings_payload.bindings:
            class_fqn = (row.class_fqn or "").strip()
            if class_fqn:
                class_fqns.append(class_fqn)
    return tuple(class_fqns)


def _manifest_paths_from_composition_manifest(
    *,
    composition_manifest_path: Path,
    repo_root: Path,
) -> tuple[Path, ...]:
    composition_path = composition_manifest_path.resolve()
    repo_root = repo_root.resolve()
    if not composition_path.exists():
        raise FileNotFoundError(
            f"Environment composition manifest not found: {composition_path}"
        )
    composition = _load_json_model(composition_path, _CompositionManifestCompat)
    if not composition.modules:
        return ()

    manifest_paths: list[Path] = []
    for idx, module_row in enumerate(composition.modules):
        manifest_path_raw = module_row.manifest_path.strip()
        if not manifest_path_raw:
            raise ValueError(
                f"Invalid module entry at {composition_path} modules[{idx}]: manifest_path must be non-empty string"
            )
        module_manifest_path = _resolve_manifest_path(
            manifest_path_raw=manifest_path_raw,
            repo_root=repo_root,
            composition_path=composition_path,
            module_idx=idx,
        )
        manifest_paths.append(module_manifest_path)
    return tuple(manifest_paths)


def _resolve_runtime_manifest_path(
    *, module_manifest_path: Path, repo_root: Path, module_idx: int
) -> Path:
    if not module_manifest_path.is_absolute():
        resolved = (repo_root / module_manifest_path).resolve()
    else:
        resolved = module_manifest_path.resolve()
    _assert_within(base=repo_root, candidate=resolved, label="module manifest path")
    if not resolved.exists():
        raise FileNotFoundError(
            "Environment module manifest not found: "
            + f"{resolved} (runtime_manifests[{module_idx}])"
        )
    return resolved


def _resolve_manifest_path(
    *,
    manifest_path_raw: str,
    repo_root: Path,
    composition_path: Path,
    module_idx: int,
) -> Path:
    module_manifest_path = Path(manifest_path_raw)
    if not module_manifest_path.is_absolute():
        module_manifest_path = (repo_root / module_manifest_path).resolve()
    else:
        module_manifest_path = module_manifest_path.resolve()
    _assert_within(
        base=repo_root, candidate=module_manifest_path, label="module manifest path"
    )
    if not module_manifest_path.exists():
        raise FileNotFoundError(
            "Environment module manifest not found: "
            + f"{module_manifest_path} (composition={composition_path} modules[{module_idx}])"
        )
    return module_manifest_path


def _load_json_model(path: Path, model_type: type[_TModel]) -> _TModel:
    raw_text = path.read_text(encoding="utf-8")
    try:
        return model_type.model_validate_json(raw_text)
    except Exception as exc:
        raise ValueError(
            f"Invalid {model_type.__name__} payload at {path}: {exc}"
        ) from exc


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "load_actor_role_contract",
    "load_actor_role_contract_from_runtime_manifests",
]
