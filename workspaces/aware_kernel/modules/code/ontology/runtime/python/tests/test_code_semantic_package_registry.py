from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

import aware_code.language_service_capability_metadata as code_lsp_metadata
import aware_code.semantic_contract as code_semantic_contract
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_code_ontology.code.code_enums import CodeLanguage


@contextmanager
def _isolated_semantic_registry() -> Iterator[None]:
    SemanticPackageRegistry.clear()
    try:
        yield
    finally:
        SemanticPackageRegistry.clear()


class _FakeSemanticProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "fake_semantic_family"

    def resolve(
        self,
        code_package: CodePackageInfo,
    ) -> tuple[SemanticPackageDescriptor, ...]:
        manifest_kind = code_package.metadata.get("manifest_kind")
        package_kind = code_package.metadata.get("package_kind")
        if manifest_kind != "aware_toml" or package_kind != "ontology":
            return ()
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="fake",
                semantic_kind="fake_package",
                package_name=f"{code_package.name}-semantic",
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={"source_package_name": code_package.name},
            ),
        )


class _BrokenProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "broken_provider"

    def resolve(
        self,
        code_package: CodePackageInfo,
    ) -> tuple[SemanticPackageDescriptor, ...]:
        raise RuntimeError(f"boom:{code_package.name}")


def _code_package_info() -> CodePackageInfo:
    return CodePackageInfo(
        name="demo-ontology",
        root_path=Path("modules/demo/structure/ontology"),
        manifest_path=Path("modules/demo/structure/ontology/aware.toml"),
        language=CodeLanguage.aware,
        metadata={"manifest_kind": "aware_toml", "package_kind": "ontology"},
    )


def test_semantic_package_registry_registers_idempotently() -> None:
    provider = _FakeSemanticProvider()
    with _isolated_semantic_registry():
        SemanticPackageRegistry.register(provider)
        SemanticPackageRegistry.register(provider)

        assert SemanticPackageRegistry.get_provider_keys() == ("fake_semantic_family",)
        assert SemanticPackageRegistry.get("fake_semantic_family") is provider


def test_semantic_package_registry_fails_closed_for_missing_provider() -> None:
    with _isolated_semantic_registry():
        with pytest.raises(KeyError, match="No semantic package provider registered"):
            SemanticPackageRegistry.get("missing")


def test_semantic_package_registry_enriches_code_packages_with_fake_provider() -> None:
    with _isolated_semantic_registry():
        SemanticPackageRegistry.register(_FakeSemanticProvider())
        enriched = SemanticPackageRegistry.enrich_code_package(_code_package_info())

    descriptor = enriched.semantic_packages[0]
    assert descriptor.provider_key == "fake_semantic_family"
    assert descriptor.family == "fake"
    assert descriptor.semantic_kind == "fake_package"
    assert descriptor.package_name == "demo-ontology-semantic"
    assert (
        descriptor.manifest_relative_path
        == "modules/demo/structure/ontology/aware.toml"
    )
    assert descriptor.metadata["source_package_name"] == "demo-ontology"


def test_semantic_package_registry_ignores_provider_failures() -> None:
    with _isolated_semantic_registry():
        SemanticPackageRegistry.register(_FakeSemanticProvider())
        SemanticPackageRegistry.register(_BrokenProvider())
        enriched = SemanticPackageRegistry.enrich_code_package(_code_package_info())

    assert [item.provider_key for item in enriched.semantic_packages] == [
        "fake_semantic_family"
    ]


def test_builtin_code_semantic_provider_is_registered_without_higher_modules() -> None:
    AwareModulePluginRegistry.clear()
    try:
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()
        contract = AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
            "aware_code"
        )

        assert contract is code_semantic_contract.AWARE_CODE_SEMANTIC_CONTRACT
        assert "aware_code" in AwareModulePluginRegistry.get_provider_keys()
        assert AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
            "aware_missing"
        ) is None
    finally:
        AwareModulePluginRegistry.clear()


def test_code_language_service_metadata_is_projected_from_semantic_contract() -> None:
    contract = code_semantic_contract.AWARE_CODE_SEMANTIC_CONTRACT
    capability_metadata = code_lsp_metadata.CODE_CAPABILITY_METADATA
    participation_by_key = {
        (descriptor.capability, descriptor.semantic_owner): descriptor
        for descriptor in contract.capability_participation
    }
    execution_policy_by_key = {
        (descriptor.capability, descriptor.semantic_owner): descriptor
        for descriptor in contract.capability_execution_policy
    }

    assert {
        (descriptor.capability, descriptor.semantic_owner)
        for descriptor in capability_metadata
    } == set(participation_by_key)

    for descriptor in capability_metadata:
        key = (descriptor.capability, descriptor.semantic_owner)
        participation = participation_by_key[key]
        execution_policy = execution_policy_by_key.get(key)

        assert descriptor.default_enabled == participation.default_enabled
        assert descriptor.required_semantic_scope_keys == (
            execution_policy.required_semantic_scope_keys
            if execution_policy is not None
            else ()
        )
        assert descriptor.priority == (
            execution_policy.priority if execution_policy is not None else 100
        )
        assert descriptor.applies_when == (
            execution_policy.applies_when if execution_policy is not None else "always"
        )


def test_code_semantic_contract_declares_raw_code_package_materialization() -> None:
    contract = code_semantic_contract.AWARE_CODE_SEMANTIC_CONTRACT

    assert contract.provider_key == "aware_code"
    assert {
        (item.capability, item.semantic_owner)
        for item in contract.capability_participation
    } >= {
        ("semantic_tokens", code_semantic_contract.CODE_SECTION_OWNER),
        ("materialize", code_semantic_contract.CODE_PROVIDER_OWNER),
    }
    role = contract.package_role_for(role=code_semantic_contract.CODE_PROVIDER_OWNER)
    assert role is not None
    assert role.contract == "aware.semantic_provider"
    assert role.owns_manifest_kinds == ("pyproject_toml", "setup_py", "pubspec_yaml")
    materialization_policy = [
        item
        for item in contract.capability_execution_policy
        if item.capability == "materialize"
        and item.semantic_owner == code_semantic_contract.CODE_PROVIDER_OWNER
    ]
    assert tuple(
        (item.callable_module, item.callable_name) for item in materialization_policy
    ) == (("aware_code.materialization.workspace_provider", "materialize"),)
    assert tuple(
        (
            item.semantic_owner,
            item.lane_projection_name,
            item.required_projection_names,
        )
        for item in contract.materialization_runtime
    ) == (
        (
            code_semantic_contract.CODE_PROVIDER_OWNER,
            "CodePackage",
            ("CodePackage",),
        ),
    )
