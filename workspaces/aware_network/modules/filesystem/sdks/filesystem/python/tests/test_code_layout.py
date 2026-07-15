from __future__ import annotations

from pathlib import Path

import pytest
from aware_code_service_dto.code.features.package_layout import (
    CodePackageLayoutContract,
)
from aware_code_service_dto.code.features.package_layout import (
    CodePackageLayoutPathRole,
)
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract
from aware_file_system_sdk import (
    FileSystemSdkError,
    build_code_layout_classifier,
    classify_code_layout_paths,
)


def test_layout_classifier_uses_code_path_roles_and_provider_hints() -> None:
    layout = CodePackageLayoutContract(
        package_name="demo",
        package_root="packages/demo",
        sources_root="src",
        generated_roots=[".aware"],
        manifest_relative_path="aware.toml",
        path_roles=[
            CodePackageLayoutPathRole(
                role=CodePackagePathRole.authored_source,
                include_patterns=["**/*.py", "pyproject.toml"],
                exclude_patterns=["src/generated/**", ".aware/**"],
                semantic_owner_hints=["runtime_owner"],
            ),
            CodePackageLayoutPathRole(
                role=CodePackagePathRole.generated_code,
                include_patterns=["src/generated/**"],
                semantic_owner_hints=["renderer_owner"],
            ),
            CodePackageLayoutPathRole(
                role=CodePackagePathRole.generated_metadata,
                include_patterns=[".aware/**"],
            ),
        ],
    )
    semantic_contract = CodeSemanticContract(provider_key="aware_code")

    result = classify_code_layout_paths(
        layout_contract=layout,
        semantic_contract=semantic_contract,
        paths=[
            "packages/demo/src/main.py",
            "packages/demo/src/generated/runtime.py",
            "packages/demo/.aware/manifest.json",
            "packages/demo/pyproject.toml",
        ],
    )

    by_path = {
        item.root_relative_path: item
        for item in result.classifications
    }
    authored = by_path["packages/demo/src/main.py"]
    generated = by_path["packages/demo/src/generated/runtime.py"]
    metadata = by_path["packages/demo/.aware/manifest.json"]
    pyproject = by_path["packages/demo/pyproject.toml"]

    assert authored.role == CodePackagePathRole.authored_source
    assert authored.source == "path_role"
    assert authored.package_relative_path == "src/main.py"
    assert authored.matched_include_pattern == "**/*.py"
    assert authored.semantic_owner_hints == ("runtime_owner", "aware_code")

    assert generated.role == CodePackagePathRole.generated_code
    assert generated.matched_include_pattern == "src/generated/**"
    assert generated.semantic_owner_hints == ("renderer_owner", "aware_code")

    assert metadata.role == CodePackagePathRole.generated_metadata
    assert metadata.semantic_owner_hints == ("aware_code",)

    assert pyproject.role_value == "authored_source"
    assert result.evidence["code_api_dto_package"] == "aware_code_service_api"
    assert result.evidence["semantic_contract_provider_key"] == "aware_code"
    assert result.evidence["role_counts"] == {
        "authored_source": 2,
        "generated_code": 1,
        "generated_metadata": 1,
    }


def test_layout_classifier_handles_package_relative_paths_and_fallbacks() -> None:
    layout = CodePackageLayoutContract(
        package_name="demo",
        package_root="packages/demo",
        sources_root="src",
        generated_roots=["build"],
        manifest_relative_path="aware.toml",
    )
    classifier = build_code_layout_classifier(
        layout_contract=layout,
        semantic_contract=CodeSemanticContract(provider_key="aware_code"),
    )

    source = classifier.classify_path(
        "src/module.aware",
        path_scope="package_relative",
    )
    manifest = classifier.classify_path(
        "aware.toml",
        path_scope="package_relative",
    )
    generated = classifier.classify_path(
        "build/package.json",
        path_scope="package_relative",
    )

    assert source.root_relative_path == "packages/demo/src/module.aware"
    assert source.role == CodePackagePathRole.authored_source
    assert source.source == "sources_root"
    assert source.semantic_owner_hints == ("aware_code",)

    assert manifest.root_relative_path == "packages/demo/aware.toml"
    assert manifest.role == CodePackagePathRole.generated_manifest
    assert manifest.source == "manifest_relative_path"

    assert generated.root_relative_path == "packages/demo/build/package.json"
    assert generated.role == CodePackagePathRole.generated_metadata
    assert generated.source == "generated_root"
    assert generated.generated_root == "packages/demo/build"


def test_layout_classifier_reports_outside_package_and_rejects_escapes() -> None:
    layout = CodePackageLayoutContract(
        package_name="demo",
        package_root="packages/demo",
    )
    classifier = build_code_layout_classifier(layout_contract=layout)

    outside = classifier.classify_path("other/main.py")

    assert outside.source == "outside_package"
    assert outside.role is None
    assert outside.package_relative_path is None

    with pytest.raises(FileSystemSdkError, match="escapes"):
        _ = classifier.classify_path("../outside.py")


def test_filesystem_sdk_import_boundary_excludes_workspace_runtime_service() -> None:
    package_dir = Path(__file__).parents[1] / "aware_file_system_sdk"
    forbidden_snippets = (
        "aware_workspace",
        "from aware_file_system_service ",
        "import aware_file_system_service",
        "from aware_code_service ",
        "import aware_code_service",
    )

    offenders: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            if snippet in text:
                offenders.append(f"{path.name}: {snippet}")

    assert offenders == []
