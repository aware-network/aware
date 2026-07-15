from __future__ import annotations

import asyncio
from typing import Any, cast

from aware_code_sdk import (
    AwareCodeSdk,
    CodeLanguage,
    CodePackageLayoutContract,
    CodePackageManifestContract,
    CodeSdkDiscoveryFile,
    CodeSdkPackageLayoutBinding,
    CodeSdkSemanticContractCatalog,
    DiscoverCodePackageLayoutsResponse,
    source_ownership_package_binding_from_layout_contract,
)


def test_code_sdk_package_layout_provider_discovers_manifest_layout() -> None:
    sdk = AwareCodeSdk.local(
        catalog=CodeSdkSemanticContractCatalog(
            package_layouts=(
                CodePackageLayoutContract(
                    package_name="aware-demo",
                    package_root="packages/demo",
                    sources_root="packages/demo/src",
                    surface="runtime",
                    manifest_relative_path="packages/demo/pyproject.toml",
                    manifest=CodePackageManifestContract(
                        manifest_kind="pyproject_toml",
                        manifest_relative_path="packages/demo/pyproject.toml",
                        language=CodeLanguage.python,
                    ),
                    generated_roots=["packages/demo/.aware"],
                ),
            ),
        )
    )

    response = sdk.package_layout_provider().discover_package_layouts(
        manifest_paths=("packages/demo/pyproject.toml",)
    )

    assert response.success is True
    assert response.diagnostics == []
    assert len(response.layout_contracts) == 1
    assert response.layout_contracts[0].package_name == "aware-demo"


def test_code_sdk_package_layout_provider_requires_declared_manifest_layout() -> None:
    sdk = AwareCodeSdk.local(catalog=CodeSdkSemanticContractCatalog())

    response = sdk.package_layout_provider().discover_package_layouts(
        manifest_paths=("packages/demo/pyproject.toml",),
    )

    assert response.success is False
    assert response.layout_contracts == []
    assert response.diagnostics == [
        "Code SDK package layout catalog has no declared layout contract "
        "for manifest path: packages/demo/pyproject.toml"
    ]


def test_code_sdk_package_layout_provider_discovers_observed_file_layout() -> None:
    class _RecordingPackageLayout:
        def __init__(self) -> None:
            self.files: tuple[CodeSdkDiscoveryFile, ...] | None = None

        async def discover_package_layouts_for_files(
            self,
            *,
            workspace_root: str = ".",
            files=(),
        ) -> DiscoverCodePackageLayoutsResponse:
            _ = workspace_root
            self.files = tuple(files)
            return DiscoverCodePackageLayoutsResponse(
                success=True,
                layout_contracts=[],
                diagnostics=[],
            )

    package_layout = _RecordingPackageLayout()
    api_client = type(
        "ApiClient",
        (),
        {
            "code": type(
                "CodeClient",
                (),
                {"package_layout": package_layout},
            )()
        },
    )()
    provider = AwareCodeSdk(
        api_client=cast(Any, api_client)
    ).async_package_layout_provider()

    result = asyncio.run(
        provider.discover_package_layouts_for_files(
            workspace_root=".",
            files=(CodeSdkDiscoveryFile(relative_path="packages/demo/src/main.py"),),
        )
    )

    assert result.success is True
    assert package_layout.files == (
        CodeSdkDiscoveryFile(relative_path="packages/demo/src/main.py"),
    )


def test_code_sdk_layout_contract_maps_to_source_ownership_binding() -> None:
    layout = CodePackageLayoutContract(
        package_name="aware-demo",
        package_root="packages/demo",
        sources_root="packages/demo/src",
        surface="runtime",
        manifest_relative_path="packages/demo/pyproject.toml",
        manifest=CodePackageManifestContract(
            manifest_kind="pyproject_toml",
            manifest_relative_path="packages/demo/pyproject.toml",
            language=CodeLanguage.python,
        ),
        generated_roots=["packages/demo/.aware"],
    )

    binding = source_ownership_package_binding_from_layout_contract(layout)

    assert binding.package_name == "aware-demo"
    assert binding.package_root == "packages/demo"
    assert binding.sources_root == "packages/demo/src"
    assert binding.manifest_relative_path == "packages/demo/pyproject.toml"
    assert binding.language == "python"
    assert binding.manifest_kind == "pyproject_toml"
    assert binding.surface == "runtime"
    assert binding.generated_roots == ["packages/demo/.aware"]


def test_code_sdk_layout_binding_keeps_coordinates_typed() -> None:
    catalog = CodeSdkSemanticContractCatalog(
        package_layouts=(
            CodeSdkPackageLayoutBinding(
                package_name="aware-demo",
                package_fqn="aware.demo",
                fqn_prefix="aware_demo",
                package_root="packages/demo",
                manifest_kind="pyproject_toml",
                manifest_relative_path="packages/demo/pyproject.toml",
                language=CodeLanguage.python,
            ),
        ),
    )

    layout = catalog.layout_contract(package_fqn="aware.demo")

    assert layout is not None
    assert layout.package_fqn == "aware.demo"
    assert layout.fqn_prefix == "aware_demo"
    assert layout.metadata == {"source": "aware_code_sdk.local_semantic_contract"}
