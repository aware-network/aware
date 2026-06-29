from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_file_system.config import FilterConfig
from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageSpec,
    ObjectConfigGraphPackageStrategy,
)
from aware_meta.language_plugin import (
    MetaLanguagePackageStrategyConfigurationRequest,
    MetaLanguagePlugin,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization import (
    LanguageMaterializationPackageBuildRequest,
    build_language_materialization_packages,
)
from aware_meta.materialization import language_service as language_service_module
from aware_meta.materialization.language_service import (
    LanguagePluginMaterializationRequest,
)


class _RecordingPackageStrategy(ObjectConfigGraphPackageStrategy):
    def build_into(
        self,
        *,
        output_root: Path,
        rendered_files: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> list[Path]:
        _ = spec
        out = output_root / "artifact.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        rendered_payload = "\n".join(
            path.read_text(encoding="utf-8").strip() for path in rendered_files
        )
        self._write_text_if_changed(out, f"{rendered_payload}\n")
        return [out]


@pytest.fixture
def isolated_meta_language_plugin_registry() -> Iterator[None]:
    saved_plugins = dict(MetaLanguagePluginRegistry._plugins)
    saved_supported = set(MetaLanguagePluginRegistry._supported_languages)
    saved_file_filters = dict(MetaLanguagePluginRegistry._file_filter_overrides)
    saved_structural_filter_overrides = dict(
        MetaLanguagePluginRegistry._structural_filter_overrides
    )
    MetaLanguagePluginRegistry.clear()
    try:
        yield
    finally:
        MetaLanguagePluginRegistry.clear()
        MetaLanguagePluginRegistry._plugins.update(saved_plugins)
        MetaLanguagePluginRegistry._supported_languages.update(saved_supported)
        MetaLanguagePluginRegistry._file_filter_overrides.update(saved_file_filters)
        MetaLanguagePluginRegistry._structural_filter_overrides.update(
            saved_structural_filter_overrides
        )


def test_language_materialization_package_runner_uses_plugin_configurator(
    tmp_path: Path,
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    base_dir = tmp_path / "render"
    target_output_dir = tmp_path / "package"
    rendered_file = base_dir / "model.txt"
    rendered_file.parent.mkdir(parents=True, exist_ok=True)
    rendered_file.write_text("rendered", encoding="utf-8")
    strategies: list[_RecordingPackageStrategy] = []
    configuration_requests: list[MetaLanguagePackageStrategyConfigurationRequest] = []

    def factory(path: Path) -> _RecordingPackageStrategy:
        strategy = _RecordingPackageStrategy(path)
        strategies.append(strategy)
        return strategy

    def configure(
        request: MetaLanguagePackageStrategyConfigurationRequest,
    ) -> None:
        configuration_requests.append(request)
        request.strategy.set_policy(
            cast(Any, {"source": request.materialization_source})
        )

    MetaLanguagePluginRegistry.register(
        MetaLanguagePlugin(
            language=CodeLanguage.sql,
            file_filter_config_factory=lambda: FilterConfig.model_validate({}),
            code_plugin=cast(Any, object()),
            surgical_renderers={},
            package_strategy_factory=factory,
            package_strategy_configurator=configure,
        )
    )

    result = build_language_materialization_packages(
        LanguageMaterializationPackageBuildRequest(
            target_language_plugin_id=CodeLanguage.sql,
            layout_base_dir=base_dir,
            target_output_dir=target_output_dir,
            rendered_files=(rendered_file,),
            package_specs=(
                ObjectConfigGraphPackageSpec(
                    name="demo",
                    package_name="demo",
                ),
            ),
            materialization_source="api",
            renderer_profile="api_runtime",
            package_kind="api_public_package",
        )
    )

    assert len(result.package_results) == 1
    package_result = result.package_results[0]
    assert package_result.name == "demo"
    assert package_result.output_root == target_output_dir.resolve()
    assert package_result.files == [target_output_dir.resolve() / "artifact.txt"]
    assert package_result.changed_files == [
        target_output_dir.resolve() / "artifact.txt"
    ]
    assert (target_output_dir / "artifact.txt").read_text(encoding="utf-8") == (
        "rendered\n"
    )
    assert len(configuration_requests) == 1
    assert configuration_requests[0].materialization_source == "api"
    assert configuration_requests[0].renderer_profile == "api_runtime"
    assert strategies[0].policy == {"source": "api"}
    assert result.metrics["package_strategy_available"] is True
    assert result.metrics["changed_file_count"] == 1

    second = build_language_materialization_packages(
        LanguageMaterializationPackageBuildRequest(
            target_language_plugin_id=CodeLanguage.sql,
            layout_base_dir=base_dir,
            target_output_dir=target_output_dir,
            rendered_files=(rendered_file,),
            package_specs=(
                ObjectConfigGraphPackageSpec(
                    name="demo",
                    package_name="demo",
                ),
            ),
            materialization_source="api",
            renderer_profile="api_runtime",
            package_kind="api_public_package",
        )
    )

    assert second.package_results[0].files == [
        target_output_dir.resolve() / "artifact.txt"
    ]
    assert second.package_results[0].changed_files == []
    assert second.metrics["changed_file_count"] == 0


def test_python_packaged_language_file_path_strips_import_root_prefix(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "package"
    request = LanguagePluginMaterializationRequest(
        source_graph=cast(Any, object()),
        target_language_plugin_id=CodeLanguage.python,
    )

    packaged_path = (
        language_service_module._packaged_language_file_path(  # noqa: SLF001
            request=request,
            output_root=output_root,
            import_root="aware_storage_ontology_dto",
            relative_path=Path("aware_storage_ontology_dto/blob/storage_blob.py"),
        )
    )

    assert packaged_path == (
        output_root / "aware_storage_ontology_dto" / "blob" / "storage_blob.py"
    )


def test_prune_stale_packaged_language_files_removes_nested_import_root(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "package"
    import_root = "aware_storage_ontology_dto"
    live_file = output_root / import_root / "blob" / "storage_blob.py"
    live_init = output_root / import_root / "__init__.py"
    stale_file = output_root / import_root / import_root / "blob" / "storage_blob.py"
    for path, text in (
        (live_file, "class StorageBlob: ...\n"),
        (live_init, ""),
        (stale_file, "class StorageBlobOld: ...\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    removed_paths = (
        language_service_module._prune_stale_packaged_language_files(  # noqa: SLF001
            output_root=output_root,
            import_root=import_root,
            current_files=(live_file, live_init),
        )
    )

    assert removed_paths == (
        Path(import_root) / import_root / "blob" / "storage_blob.py",
    )
    assert live_file.is_file()
    assert live_init.is_file()
    assert not stale_file.exists()
    assert not (output_root / import_root / import_root).exists()


def test_prune_stale_unpacked_sql_files_reports_delete_refs(tmp_path: Path) -> None:
    output_root = tmp_path / "sql"
    live_file = output_root / "environment" / "environment_experience_profile.sql"
    stale_file = output_root / "actor" / "actor_config.sql"
    metadata_file = output_root / "_aware" / "ocg.node_paths.sql.json"
    for path, text in (
        (live_file, "CREATE TABLE environment_experience_profile (id UUID);\n"),
        (stale_file, "CREATE TABLE actor_config (id UUID);\n"),
        (metadata_file, "{}\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    request = LanguagePluginMaterializationRequest(
        source_graph=cast(Any, object()),
        target_language_plugin_id=CodeLanguage.sql,
        output_root=output_root,
        import_root="aware_experience_ontology",
        materialization_source="ontology",
    )
    generated_file = language_service_module.LanguageMaterializationGeneratedFile(
        path=Path("environment/environment_experience_profile.sql"),
        output_kind="source_code",
        producer_step="render",
        sha256="0" * 64,
        size_bytes=live_file.stat().st_size,
    )

    removed_paths = (
        language_service_module._prune_stale_unpacked_language_files(  # noqa: SLF001
            request=request,
            generated_files=(generated_file,),
        )
    )
    package_outputs = language_service_module._build_package_outputs(  # noqa: SLF001
        request=request,
        generated_files=(generated_file,),
        deleted_file_refs=removed_paths,
    )

    assert removed_paths == (Path("actor/actor_config.sql"),)
    assert live_file.is_file()
    assert metadata_file.is_file()
    assert not stale_file.exists()
    assert not (output_root / "actor").exists()
    assert len(package_outputs) == 1
    assert package_outputs[0].deleted_file_refs == removed_paths


def test_legacy_packaged_language_deleted_file_refs_cover_python_layout_migration() -> (
    None
):
    import_root = "aware_storage_ontology_dto"
    request = LanguagePluginMaterializationRequest(
        source_graph=cast(Any, object()),
        target_language_plugin_id=CodeLanguage.python,
        import_root=import_root,
        materialization_source="ontology_dto",
    )

    refs = language_service_module._legacy_packaged_language_deleted_file_refs(  # noqa: SLF001
        request=request,
        generated_files=(
            language_service_module.LanguageMaterializationGeneratedFile(
                path=Path(import_root) / "blob" / "storage_blob.py",
                output_kind="source_code",
                producer_step="render",
                sha256="0" * 64,
                size_bytes=1,
            ),
            language_service_module.LanguageMaterializationGeneratedFile(
                path=Path(import_root) / "_aware" / "orm.graph.binding.msgpack",
                output_kind="generated_metadata",
                producer_step="plugin_declared_output",
                sha256="1" * 64,
                size_bytes=1,
            ),
        ),
    )

    assert refs == (
        Path(import_root) / "_aware" / "ocg.binding.snapshot.msgpack",
        Path(import_root) / import_root / "blob" / "storage_blob.py",
    )


def test_build_package_outputs_does_not_delete_current_generated_file(
    tmp_path: Path,
) -> None:
    import_root = "aware_storage_ontology"
    current_ref = Path(import_root) / "_aware" / "orm.graph.binding.msgpack"
    request = LanguagePluginMaterializationRequest(
        source_graph=cast(Any, object()),
        target_language_plugin_id=CodeLanguage.python,
        output_root=tmp_path / "package",
        import_root=import_root,
        materialization_source="ontology",
    )

    outputs = language_service_module._build_package_outputs(  # noqa: SLF001
        request=request,
        generated_files=(
            language_service_module.LanguageMaterializationGeneratedFile(
                path=current_ref,
                output_kind="generated_metadata",
                producer_step="plugin_declared_output",
                sha256="1" * 64,
                size_bytes=1,
            ),
        ),
        deleted_file_refs=(current_ref,),
    )

    assert len(outputs) == 1
    assert outputs[0].deleted_file_refs == (
        Path(import_root) / "_aware" / "ocg.binding.snapshot.msgpack",
    )
