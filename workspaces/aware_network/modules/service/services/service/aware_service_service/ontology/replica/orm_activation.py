from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module, invalidate_caches
from pathlib import Path
import re
from uuid import UUID

from aware_orm.models.base_model import BaseORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.models_manifest import ClassModelEntry, ModelsManifest
from aware_orm.runtime.package_artifacts import (
    DEFAULT_ARTIFACTS_DIR,
    PYTHON_MODELS_MANIFEST_FILENAME,
)
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata, register_sql_metadata

from .orm_package_paths import (
    OntologyPackageRequirement,
    ResolvedOntologyOrmPackagePath,
    expose_required_service_ontology_orm_package_paths,
)


SERVICE_ONTOLOGY_REPLICA_SQL_SCHEMA = "service_ontology_replica"


@dataclass(frozen=True, slots=True)
class ActivatedServiceOntologyReplicaOrmPackage:
    package_name: str
    fqn_prefix: str
    import_root: str
    path: Path
    model_count: int
    metadata_count: int


@dataclass(frozen=True, slots=True)
class ServiceOntologyReplicaOrmPackageActivation:
    resolved_paths: tuple[ResolvedOntologyOrmPackagePath, ...]
    packages: tuple[ActivatedServiceOntologyReplicaOrmPackage, ...]

    @property
    def metadata_count(self) -> int:
        return sum(package.metadata_count for package in self.packages)


def activate_service_ontology_replica_orm_packages(
    paths: Iterable[ResolvedOntologyOrmPackagePath],
) -> ServiceOntologyReplicaOrmPackageActivation:
    """Install Service replica read metadata for generated ontology ORM packages."""

    resolved_paths = tuple(paths)
    class_config_bindings = dict(ORMModelRegistry._class_config_id_to_model)
    try:
        activated = tuple(
            _activate_service_ontology_replica_orm_package(path=path)
            for path in resolved_paths
        )
    finally:
        ORMModelRegistry._class_config_id_to_model.clear()
        ORMModelRegistry._class_config_id_to_model.update(class_config_bindings)
    return ServiceOntologyReplicaOrmPackageActivation(
        resolved_paths=resolved_paths,
        packages=activated,
    )


@contextmanager
def activate_required_service_ontology_replica_orm_packages(
    *,
    repo_root: Path,
    ontology_packages: Iterable[OntologyPackageRequirement],
) -> Iterator[ServiceOntologyReplicaOrmPackageActivation]:
    with expose_required_service_ontology_orm_package_paths(
        repo_root=repo_root,
        ontology_packages=ontology_packages,
    ) as resolved_paths:
        yield activate_service_ontology_replica_orm_packages(resolved_paths)


def _activate_service_ontology_replica_orm_package(
    *,
    path: ResolvedOntologyOrmPackagePath,
) -> ActivatedServiceOntologyReplicaOrmPackage:
    invalidate_caches()
    import_module(path.import_root)
    manifest = _load_models_manifest(import_root=path.import_root)
    metadata_count = 0
    for entry in manifest.classes:
        model_class = _import_model_class(entry=entry)
        installed = _install_service_replica_sql_metadata(
            model_class=model_class,
            entry=entry,
        )
        if installed:
            metadata_count += 1
    return ActivatedServiceOntologyReplicaOrmPackage(
        package_name=path.package_name,
        fqn_prefix=path.fqn_prefix,
        import_root=path.import_root,
        path=path.path,
        model_count=len(manifest.classes),
        metadata_count=metadata_count,
    )


def _load_models_manifest(*, import_root: str) -> ModelsManifest:
    package = import_module(import_root)
    from importlib.resources import files

    manifest_path = files(package).joinpath(
        DEFAULT_ARTIFACTS_DIR,
        PYTHON_MODELS_MANIFEST_FILENAME,
    )
    if not manifest_path.is_file():
        raise RuntimeError(
            "Service ontology replica ORM activation requires generated package "
            f"models manifest: package={import_root!r} artifact="
            f"{DEFAULT_ARTIFACTS_DIR}/{PYTHON_MODELS_MANIFEST_FILENAME}."
        )
    return ModelsManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))


def _import_model_class(*, entry: ClassModelEntry) -> type:
    module = import_module(entry.module)
    model_class = getattr(module, entry.name, None)
    if not isinstance(model_class, type):
        raise RuntimeError(
            "Service ontology replica ORM activation could not import generated "
            f"model class: {entry.module}.{entry.name}."
        )
    return model_class


def _install_service_replica_sql_metadata(
    *,
    model_class: type,
    entry: ClassModelEntry,
) -> bool:
    if not issubclass(model_class, BaseORMModel):
        return False

    class_config_id = _bound_class_config_id(model_class=model_class)
    if class_config_id is None:
        raise RuntimeError(
            "Service ontology replica ORM activation requires generated model "
            f"ClassConfig binding before metadata install: {_class_fqn(model_class)!r}."
        )
    if class_config_id != entry.class_config_id:
        raise RuntimeError(
            "Service ontology replica ORM activation resolved a generated model "
            "ClassConfig id that does not match python.models.json: "
            f"class={_class_fqn(model_class)!r} expected={entry.class_config_id} "
            f"actual={class_config_id}."
        )

    attributes = _replica_persisted_attributes(model_class=model_class)
    metadata = SQLRuntimeMetadata(
        class_config_id=class_config_id,
        table_schema=SERVICE_ONTOLOGY_REPLICA_SQL_SCHEMA,
        table_name=_replica_virtual_table_name(class_fqn=_class_fqn(model_class)),
        column_by_attribute={attribute: attribute for attribute in attributes},
        persisted_attributes=frozenset(attributes),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )
    setattr(model_class, "_sql_runtime_metadata", metadata)
    register_sql_metadata(
        metadata,
        class_fqn=_class_fqn(model_class),
    )
    return True


def _bound_class_config_id(*, model_class: type) -> UUID | None:
    get_class_config = getattr(model_class, "get_class_config", None)
    if not callable(get_class_config):
        return None
    class_config = get_class_config()
    class_config_id = getattr(class_config, "id", None)
    return class_config_id if isinstance(class_config_id, UUID) else None


def _replica_persisted_attributes(*, model_class: type) -> tuple[str, ...]:
    attributes = {"id", "branch_id", "projection_hash"}
    model_fields = getattr(model_class, "model_fields", {}) or {}
    if isinstance(model_fields, dict):
        for name, field in model_fields.items():
            if not isinstance(name, str) or not name.strip():
                continue
            if name.startswith("_"):
                continue
            if getattr(field, "exclude", None) is True:
                continue
            attributes.add(name)
    return tuple(sorted(attributes))


def _replica_virtual_table_name(*, class_fqn: str) -> str:
    table_name = re.sub(r"[^A-Za-z0-9_]+", "_", class_fqn).strip("_").lower()
    if not table_name:
        raise RuntimeError(
            "Service ontology replica ORM activation could not derive a virtual "
            f"table name from class FQN: {class_fqn!r}."
        )
    return table_name


def _class_fqn(model_class: type) -> str:
    get_registry_key = getattr(model_class, "get_registry_key", None)
    if callable(get_registry_key):
        value = get_registry_key()
        if isinstance(value, str) and value.strip():
            return value
    return f"{model_class.__module__}.{model_class.__name__}"


__all__ = [
    "ActivatedServiceOntologyReplicaOrmPackage",
    "SERVICE_ONTOLOGY_REPLICA_SQL_SCHEMA",
    "ServiceOntologyReplicaOrmPackageActivation",
    "activate_required_service_ontology_replica_orm_packages",
    "activate_service_ontology_replica_orm_packages",
]
