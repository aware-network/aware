from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from uuid import uuid4

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime import ORMClassResolutionIndex, resolve_orm_class
from aware_orm.runtime.models_manifest import ClassModelEntry, ModelsManifest


class _RegistryBoundModel(ORMModel):
    name: str | None = None


class _FqnResolvedModel(ORMModel):
    name: str | None = None


def test_resolve_orm_class_prefers_class_config_binding() -> None:
    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        ORMModelRegistry.clear_registry()
        class_config_id = uuid4()
        stale_fqn = f"{_FqnResolvedModel.__module__}.{_FqnResolvedModel.__name__}"
        class_config = SimpleNamespace(
            id=class_config_id,
            class_fqn=stale_fqn,
        )

        bound_fqn = ORMModelRegistry.register_class_stub(_RegistryBoundModel)
        ORMModelRegistry.register_class_stub(_FqnResolvedModel)
        assert ORMModelRegistry.attach_class_config(bound_fqn, class_config)

        assert (
            resolve_orm_class(
                class_config_id=class_config_id,
                class_resolution_index=(
                    ORMClassResolutionIndex.from_class_configs_by_id(
                        {class_config_id: class_config},
                    )
                ),
            )
            is _RegistryBoundModel
        )
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def test_resolve_orm_class_uses_index_class_fqn() -> None:
    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        ORMModelRegistry.clear_registry()
        class_config_id = uuid4()
        model_fqn = ORMModelRegistry.register_class_stub(_FqnResolvedModel)
        class_config = SimpleNamespace(
            id=class_config_id,
            class_fqn=model_fqn,
        )

        assert (
            resolve_orm_class(
                class_config_id=class_config_id,
                class_resolution_index=ORMClassResolutionIndex.from_class_configs_by_id(
                    {class_config_id: class_config},
                ),
            )
            is _FqnResolvedModel
        )
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def test_resolve_orm_class_uses_python_models_manifest_fallback(
    tmp_path,
    monkeypatch,
) -> None:
    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        ORMModelRegistry.clear_registry()
        package_root = tmp_path / "aware_resolver_demo"
        aware_root = package_root / "_aware"
        aware_root.mkdir(parents=True)
        (package_root / "__init__.py").write_text("", encoding="utf-8")
        (package_root / "models.py").write_text(
            "from aware_orm.models.orm_model import ORMModel\n\n"
            "class ManifestResolvedModel(ORMModel):\n"
            "    name: str | None = None\n",
            encoding="utf-8",
        )
        class_config_id = uuid4()
        manifest = ModelsManifest(
            language="python",
            classes=[
                ClassModelEntry(
                    class_config_id=class_config_id,
                    module="aware_resolver_demo.models",
                    name="ManifestResolvedModel",
                )
            ],
        )
        (aware_root / "python.models.json").write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )

        monkeypatch.syspath_prepend(str(tmp_path))
        module = import_module("aware_resolver_demo.models")
        model_class = module.ManifestResolvedModel
        ORMModelRegistry.register_class_stub(model_class)

        assert (
            resolve_orm_class(
                class_config_id=class_config_id,
                class_resolution_index=(
                    ORMClassResolutionIndex.from_class_configs_by_id(
                        {
                        class_config_id: SimpleNamespace(
                            id=class_config_id,
                            class_fqn="stale.module.ManifestResolvedModel",
                        )
                        },
                    )
                ),
            )
            is model_class
        )
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)
