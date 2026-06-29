"""ORM-owned class resolution boundary.

Consumers may pass a producer/runtime index, but ORM owns the lookup order and
artifact mechanics. The index is treated as a generic class-config lookup; this
module intentionally has no Meta/Ontology imports.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import import_module
from importlib.resources import files
from typing import Protocol, Self
from uuid import UUID

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry

from .models_manifest import ModelsManifest
from .package_artifacts import DEFAULT_ARTIFACTS_DIR, PYTHON_MODELS_MANIFEST_FILENAME


class ORMClassConfigReference(Protocol):
    """Producer-neutral class reference consumed by ORM class resolution.

    Meta may pass ontology ClassConfig objects, generated package producers may
    pass DTO mirrors, and tests may pass simple refs. ORM only needs the
    canonical Python class FQN keyed by ClassConfig id.
    """

    class_fqn: str | None


@dataclass(frozen=True, slots=True)
class ORMClassResolutionIndex:
    """Explicit ORM boundary index for resolving ClassConfig ids to model classes."""

    class_fqn_by_class_config_id: Mapping[UUID, str]
    package_prefixes: tuple[str, ...] = ()

    @classmethod
    def from_class_configs_by_id(
        cls,
        class_configs_by_id: Mapping[UUID, ORMClassConfigReference],
        *,
        package_prefixes: Iterable[str] = (),
    ) -> Self:
        return cls(
            class_fqn_by_class_config_id={
                class_config_id: class_fqn
                for class_config_id, class_config in class_configs_by_id.items()
                if isinstance((class_fqn := class_config.class_fqn), str)
                and bool(class_fqn)
            },
            package_prefixes=tuple(
                prefix
                for prefix in package_prefixes
                if isinstance(prefix, str) and prefix
            ),
        )

    def class_fqn_for_config_id(self, class_config_id: UUID) -> str | None:
        return self.class_fqn_by_class_config_id.get(class_config_id)


def resolve_orm_class(
    *,
    class_config_id: UUID,
    class_resolution_index: ORMClassResolutionIndex | None = None,
    class_fqn: str | None = None,
    package_prefixes: Iterable[str] | None = None,
) -> type[ORMModel] | None:
    """Resolve an ORM model class from ORM registry/artifact state.

    Lookup order:
    1. Installed native graph binding (`class_config_id -> model class`).
    2. Exact class FQN registered in ORM.
    3. Embedded package `python.models.json` manifests for generated model
       packages. This fallback resolves by canonical aware class FQN when class
       ids change during namespace/stable-id migrations.
    """

    orm_class = ORMModelRegistry.get_class_by_class_config_id(class_config_id)
    if orm_class is not None:
        return orm_class

    candidate_fqns = _candidate_class_fqns(
        class_config_id=class_config_id,
        class_resolution_index=class_resolution_index,
        class_fqn=class_fqn,
    )
    for candidate_fqn in candidate_fqns:
        orm_class = ORMModelRegistry.get_class_by_fqn(candidate_fqn)
        if _is_orm_model_class(orm_class):
            return orm_class

    return _resolve_orm_class_from_python_models_manifest(
        class_config_id=class_config_id,
        package_prefixes=_merged_package_prefixes(
            class_resolution_index=class_resolution_index,
            package_prefixes=package_prefixes,
        ),
        candidate_fqns=candidate_fqns,
    )


def _candidate_class_fqns(
    *,
    class_config_id: UUID,
    class_resolution_index: ORMClassResolutionIndex | None,
    class_fqn: str | None,
) -> tuple[str, ...]:
    fqns: list[str] = []
    if isinstance(class_fqn, str) and class_fqn:
        fqns.append(class_fqn)

    indexed_fqn = (
        class_resolution_index.class_fqn_for_config_id(class_config_id)
        if class_resolution_index is not None
        else None
    )
    if isinstance(indexed_fqn, str) and indexed_fqn:
        fqns.append(indexed_fqn)

    return tuple(dict.fromkeys(fqns))


def _merged_package_prefixes(
    *,
    class_resolution_index: ORMClassResolutionIndex | None,
    package_prefixes: Iterable[str] | None,
) -> tuple[str, ...]:
    prefixes: list[str] = []
    if class_resolution_index is not None:
        prefixes.extend(class_resolution_index.package_prefixes)
    if package_prefixes is not None:
        prefixes.extend(package_prefixes)
    return tuple(dict.fromkeys(prefix for prefix in prefixes if prefix))


def _resolve_orm_class_from_python_models_manifest(
    *,
    class_config_id: UUID,
    package_prefixes: Iterable[str] | None,
    candidate_fqns: Iterable[str],
) -> type[ORMModel] | None:
    for package_prefix in _candidate_model_package_prefixes(
        package_prefixes=package_prefixes,
        candidate_fqns=candidate_fqns,
    ):
        try:
            package = import_module(package_prefix)
            manifest_path = files(package).joinpath(
                DEFAULT_ARTIFACTS_DIR,
                PYTHON_MODELS_MANIFEST_FILENAME,
            )
            if not manifest_path.is_file():
                continue
            manifest = ModelsManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
        except Exception:
            continue

        for entry in manifest.classes:
            if entry.class_config_id != class_config_id and (
                entry.aware_class_ref not in candidate_fqns
            ):
                continue
            try:
                module = import_module(entry.module)
            except Exception:
                continue
            orm_class = getattr(module, entry.name, None)
            if _is_orm_model_class(orm_class):
                return orm_class
    return None


def _candidate_model_package_prefixes(
    *,
    package_prefixes: Iterable[str] | None,
    candidate_fqns: Iterable[str],
) -> tuple[str, ...]:
    prefixes: set[str] = set()
    if package_prefixes is not None:
        prefixes.update(
            prefix for prefix in package_prefixes if isinstance(prefix, str) and prefix
        )

    for fqn in ORMModelRegistry.get_all_fqn_to_class():
        module_name, _, _class_name = fqn.rpartition(".")
        if not module_name:
            continue
        package_prefix, _, _rest = module_name.partition(".")
        if package_prefix:
            prefixes.add(package_prefix)

    for fqn in candidate_fqns:
        package_prefix, _, _rest = fqn.partition(".")
        if package_prefix:
            prefixes.add(package_prefix)
            if package_prefix.startswith("aware_") and not package_prefix.endswith(
                "_ontology"
            ):
                prefixes.add(f"{package_prefix}_ontology")

    return tuple(sorted(prefixes))


def _is_orm_model_class(value: object) -> bool:
    return isinstance(value, type) and issubclass(value, ORMModel)


__all__ = [
    "ORMClassConfigReference",
    "ORMClassResolutionIndex",
    "resolve_orm_class",
]
