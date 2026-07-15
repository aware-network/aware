from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from importlib import import_module

import pytest

from _skill_runtime_test_paths import (
    REPO_ROOT,
    prepend_repo_paths,
    register_skill_module_plugins,
)


def _prepend_skill_contract_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    prepend_repo_paths(
        monkeypatch,
        (
            "workspaces/aware_network/modules/skill/ontology/runtime/python",
            "workspaces/aware_kernel/modules/code/ontology/runtime/python",
            "workspaces/aware_network/modules/skill/ontology/structure/python/orm_runtime",
            "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
        ),
    )


@contextmanager
def _isolated_module_plugin_registry() -> Iterator[None]:
    from aware_code.module_plugin_registry import AwareModulePluginRegistry

    AwareModulePluginRegistry.clear()
    try:
        yield
    finally:
        AwareModulePluginRegistry.clear()


def test_skill_module_manifest_declares_semantic_contract_plugin() -> None:
    from aware_code.module_manifest.loader import load_aware_module_spec

    spec = load_aware_module_spec(
        toml_path=(
            REPO_ROOT / "workspaces/aware_network/modules/skill/aware.module.toml"
        )
    )

    assert tuple(
        (package.id, package.kind, package.manifest, package.visibility)
        for package in spec.packages
    ) == (
        ("ontology", "ontology", "ontology/aware.ontology.toml", "module"),
        ("runtime", "runtime", "ontology/runtime/python/pyproject.toml", "module"),
        ("skill_api", "api", "apis/skill/aware.api.toml", "module"),
        ("skill_service", "service", "services/skill/aware.service.toml", "module"),
        ("skill_sdk", "sdk", "sdks/skill/aware/aware.sdk.toml", "module"),
    )
    assert spec.packages[0].semantic_contract is None
    assert spec.packages[1].semantic_contract is not None
    assert (
        spec.packages[1].semantic_contract.role,
        spec.packages[1].semantic_contract.contract,
        spec.packages[1].semantic_contract.provider_key,
        spec.packages[1].semantic_contract.module,
        spec.packages[1].semantic_contract.owns_manifest_kinds,
        spec.packages[1].semantic_contract.capabilities,
        spec.packages[1].semantic_contract.bindings,
    ) == (
        "aware_skill.provider",
        "aware.semantic_provider",
        "aware_skill",
        "aware_skill.semantic_contract",
        ("aware_skill_toml",),
        ("semantic_analysis", "diagnostics", "semantic_tokens", "materialize"),
        (),
    )
    assert tuple(
        (
            plugin.kind,
            plugin.provider_key,
            plugin.semantic_contract_module,
            plugin.capability_contract_module,
            plugin.capability_execution_module,
        )
        for plugin in spec.plugins
    ) == (
        (
            "code.module_plugin",
            "aware_skill",
            None,
            "aware_skill.language_service_capability_metadata",
            "aware_skill.language_service_capabilities",
        ),
    )
    assert tuple(
        (policy.capability, policy.workspace_fallback)
        for policy in spec.plugins[0].capability_policy
    ) == (("diagnostics", True), ("semantic_tokens", True))


def test_skill_semantic_contract_declares_scoped_provider_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_contract_runtime(monkeypatch)

    semantic_contract_module = import_module("aware_skill.semantic_contract")
    contract = semantic_contract_module.AWARE_MODULE_SEMANTIC_CONTRACT
    assert contract.provider_key == "aware_skill"
    assert contract.semantic_scope_keys == ("aware_skill.semantic_scope",)
    assert tuple(
        (
            role.role,
            role.contract,
            role.package_kind,
            role.capabilities,
            role.owns_manifest_kinds,
        )
        for role in contract.package_roles
    ) == (
        (
            "aware_skill.provider",
            "aware.semantic_provider",
            "runtime",
            ("semantic_analysis", "diagnostics", "semantic_tokens", "materialize"),
            ("aware_skill_toml",),
        ),
    )
    assert {
        (item.capability, item.semantic_owner)
        for item in contract.capability_participation
    } >= {
        ("semantic_analysis", "aware_skill.skill_config"),
        ("materialize", "aware_skill.provider"),
        ("diagnostics", "aware_skill.skill_config"),
        ("diagnostics", "aware_skill.api"),
        ("diagnostics", "aware_skill.endpoint"),
        ("diagnostics", "aware_skill.step"),
        ("semantic_tokens", "aware_skill.skill_config"),
        ("semantic_tokens", "aware_skill.api"),
        ("semantic_tokens", "aware_skill.endpoint"),
        ("semantic_tokens", "aware_skill.step"),
    }
    assert tuple(
        (
            item.capability,
            item.semantic_owner,
            item.callable_module,
            item.callable_name,
        )
        for item in contract.capability_execution_policy
        if item.capability in {"semantic_analysis", "materialize"}
    ) == (
        (
            "semantic_analysis",
            "aware_skill.skill_config",
            None,
            "_skill_semantic_analysis_provider",
        ),
        (
            "materialize",
            "aware_skill.provider",
            "aware_skill.materialization.workspace_provider",
            "materialize",
        ),
    )
    assert tuple(
        (lane.lane_key, lane.semantic_owner, lane.grammar_rules)
        for lane in contract.syntax_lanes
    ) == (
        ("aware_skill.skill_config", "aware_skill.skill_config", ("skill_def",)),
        ("aware_skill.api", "aware_skill.api", ("skill_api_decl",)),
        ("aware_skill.endpoint", "aware_skill.endpoint", ("skill_endpoint_def",)),
        ("aware_skill.step", "aware_skill.step", ("skill_step_def",)),
    )


def test_skill_code_module_contract_registers_provider_execution_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_contract_runtime(monkeypatch)

    from aware_code.code_module_contract import CodeModuleContract
    from aware_code.module_plugin_registry import AwareModulePluginRegistry
    from aware_code.module_semantic_contract import ModuleSemanticContract

    with _isolated_module_plugin_registry():
        register_skill_module_plugins(AwareModulePluginRegistry)

        assert (
            AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                "aware_skill"
            )
            == "aware_skill.semantic_contract"
        )
        assert (
            AwareModulePluginRegistry.capability_execution_module_for_provider_key(
                "aware_skill"
            )
            == "aware_skill.language_service_capabilities"
        )
        assert "aware_skill" in (
            AwareModulePluginRegistry.workspace_fallback_provider_keys_for_capability(
                capability="semantic_tokens",
            )
        )

        code_module_contract = (
            AwareModulePluginRegistry.code_module_contract_for_provider_key(
                "aware_skill"
            )
        )
        assert isinstance(code_module_contract, CodeModuleContract)
        assert code_module_contract.provider_key == "aware_skill"
        assert code_module_contract.capability_contract_module == (
            "aware_skill.language_service_capability_metadata"
        )
        assert code_module_contract.capability_execution_module == (
            "aware_skill.language_service_capabilities"
        )
        assert tuple(
            (policy.capability, policy.workspace_fallback)
            for policy in code_module_contract.capability_policy
        ) == (("diagnostics", True), ("semantic_tokens", True))
        assert tuple(
            (item.capability, item.provider_key)
            for item in code_module_contract.language_service_provider_descriptors
            if item.capability == "semantic_analysis"
        ) == (("semantic_analysis", "aware_skill.skill_config"),)
        assert tuple(
            (
                package.id,
                package.kind,
                package.manifest,
                package.visibility,
                package.semantic_contract,
            )
            for package in code_module_contract.packages
        ) == (
            (
                "ontology",
                "ontology",
                "ontology/aware.ontology.toml",
                "module",
                None,
            ),
            (
                "runtime",
                "runtime",
                "ontology/runtime/python/pyproject.toml",
                "module",
                code_module_contract.packages[1].semantic_contract,
            ),
            (
                "skill_api",
                "api",
                "apis/skill/aware.api.toml",
                "module",
                None,
            ),
            (
                "skill_service",
                "service",
                "services/skill/aware.service.toml",
                "module",
                None,
            ),
            (
                "skill_sdk",
                "sdk",
                "sdks/skill/aware/aware.sdk.toml",
                "module",
                None,
            ),
        )
        assert code_module_contract.packages[1].semantic_contract is not None
        assert (
            code_module_contract.packages[1].semantic_contract.role,
            code_module_contract.packages[1].semantic_contract.contract,
            code_module_contract.packages[1].semantic_contract.provider_key,
            code_module_contract.packages[1].semantic_contract.module,
            code_module_contract.packages[1].semantic_contract.bindings,
        ) == (
            "aware_skill.provider",
            "aware.semantic_provider",
            "aware_skill",
            "aware_skill.semantic_contract",
            (),
        )
        assert isinstance(
            code_module_contract.semantic_contract,
            ModuleSemanticContract,
        )
        assert code_module_contract.semantic_contract.provider_key == "aware_skill"
        assert tuple(
            role.role for role in code_module_contract.semantic_contract.package_roles
        ) == ("aware_skill.provider",)
        assert tuple(
            lane.lane_key
            for lane in code_module_contract.semantic_contract.syntax_lanes
        ) == (
            "aware_skill.skill_config",
            "aware_skill.api",
            "aware_skill.endpoint",
            "aware_skill.step",
        )
        semantic_analysis_provider = (
            AwareModulePluginRegistry.language_service_capability_provider(
                capability="semantic_analysis",
                provider_key="aware_skill.skill_config",
            )
        )
        assert callable(semantic_analysis_provider)
        materializer = AwareModulePluginRegistry.resolve_semantic_capability_provider(
            provider_key="aware_skill",
            capability="materialize",
        )
        assert materializer is not None
        assert materializer.semantic_owner == "aware_skill.provider"
        assert materializer.callable_module == (
            "aware_skill.materialization.workspace_provider"
        )
        assert materializer.callable_name == "materialize"
