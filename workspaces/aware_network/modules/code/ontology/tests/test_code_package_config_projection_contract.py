from __future__ import annotations

from pathlib import Path

from _code_ontology_test_paths import source_text


def _source(path: str) -> str:
    return source_text(path)


def test_kernel_code_package_config_projection_portals_to_code_package() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/"
        "code_package_config_projection.aware"
    )

    assert "projection CodePackageConfig" in source
    assert "root aware_code.package.CodePackageConfig" in source
    assert "aware_code.package.CodePackageConfig::inputs" in source
    assert "aware_code.package.CodePackageConfig::outputs" in source
    assert "aware_code.package.CodePackageConfig::runtime_contexts" in source
    assert "aware_code.package.CodePackageConfig::packages CodePackage" in source
    assert "CodePackageConfig::packages" in source
    assert "portal-backed concrete package instances" in source

    assert "CodePackage::codes" not in source
    assert "CodePackageCode::code" not in source
    assert "CodePackage::tests" not in source


def test_kernel_code_package_projection_remains_package_owned_surface() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/"
        "code_package_projection.aware"
    )

    assert "projection CodePackage" in source
    assert "root aware_code.package.CodePackage" in source
    assert "aware_code.package.CodePackage::codes" in source
    assert "aware_code.package.CodePackageCode::code" in source
    assert "aware_code.package.CodePackage::tests" in source


def test_kernel_code_package_config_owns_package_contract_vocabulary() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/"
        "code_package_config.aware"
    )

    assert "packages CodePackage[]" in source
    assert "instances CodePackage[]" not in source
    assert "inputs CodePackageConfigInput[]" in source
    assert "outputs CodePackageConfigOutput[]" in source
    assert "runtime_contexts CodePackageConfigRuntimeContext[]" in source
    assert "manifest_kind String" in source
    assert "manifest_filename String" in source
    assert "default_surface String?" in source
    assert "materialization_capability String?" in source
    assert "workspace_manifest_kind" not in source
    assert "JsonObject" not in source
    assert "JsonArray" not in source


def test_kernel_code_package_is_config_scoped_child() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/"
        "code_package.aware"
    )

    assert "manifest_kind" not in source
    assert "ann package.CodePackage identity contained" in source
    assert "ann package.CodePackage identity standalone" not in source
    assert "Identity is config-scoped" in source
    assert (
        "Semantic package kind and manifest-kind truth live on CodePackageConfig"
        in source
    )


def test_kernel_code_package_config_contract_uses_typed_rows() -> None:
    enum_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/"
        "code_package_enums.aware"
    )
    input_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/"
        "code_package_config_input.aware"
    )
    output_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/"
        "code_package_config_output.aware"
    )
    runtime_context_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/"
        "code_package_config_runtime_context.aware"
    )

    assert "enum CodePackageConfigInputKind" in enum_source
    assert "enum CodePackageConfigOutputKind" in enum_source
    assert "enum CodePackageConfigRuntimeContextKind" in enum_source
    assert "kind CodePackageConfigInputKind" in input_source
    assert "kind CodePackageConfigOutputKind" in output_source
    assert "kind CodePackageConfigRuntimeContextKind" in runtime_context_source

    for source in (input_source, output_source, runtime_context_source):
        assert (
            "Workspace owns" in source
            or "Workspace-owned" in source
            or "outside Code" in source
        )
        assert "JsonObject" not in source
        assert "JsonArray" not in source
