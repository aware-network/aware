from __future__ import annotations

from _code_runtime_test_paths import source_text


def _source(path: str) -> str:
    return source_text(path)


def test_code_package_config_projection_portals_to_code_package() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/code_package_config_projection.aware"
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


def test_code_package_projection_remains_package_owned_surface() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/code_package_projection.aware"
    )

    assert "projection CodePackage" in source
    assert "root aware_code.package.CodePackage" in source
    assert "aware_code.package.CodePackage::codes" in source
    assert "aware_code.package.CodePackageCode::code" in source
    assert "aware_code.package.CodePackage::artifacts" in source
    assert "aware_code.package.CodePackage::tests" in source
