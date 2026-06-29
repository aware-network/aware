from __future__ import annotations

from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
import sys
from types import ModuleType
from typing import Iterator

import pytest

import aware_code.module_plugin_registry as module_plugin_registry
from aware_code.language_service_capability_contract import (
    LanguageServiceModuleCapabilityContract,
)
from aware_code.language_service_execution_contract import (
    LanguageServiceModuleCapabilityExecutionContract,
)
from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor,
)
from aware_code.code_module_contract import CodeModuleContract
from aware_code.module_code_package_materialization_contract import (
    ModuleCodePackageMaterializationContract,
)
from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticArtifactLeafOwnershipDescriptor,
    ModuleSemanticContract,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
    ModuleSemanticMaterializationInputDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticPackageRoleDescriptor,
)
from aware_code.module_plugin import (
    AwareModulePackageContract,
    AwareModulePackageSemanticContract,
    AwareModulePackageSemanticContractBinding,
    AwareModulePlugin,
)
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
)
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor
from aware_code.semantic_package.registry import SemanticPackageRegistry
from aware_code.semantic_scope.registry import SemanticScopeRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.language_service.capability_provider_bootstrap import (
    ensure_builtin_language_service_capability_providers_registered,
)
from aware_code.language_service.features.diagnostics_capabilities import (
    clear_diagnostics_capability_providers,
    get_registered_diagnostics_capability_descriptors,
)
from aware_code.language_service.features.semantic_tokens_capabilities import (
    clear_semantic_tokens_capability_providers,
    get_registered_semantic_tokens_capability_descriptors,
)


@contextmanager
def _isolated_module_plugin_registry() -> Iterator[None]:
    AwareModulePluginRegistry.clear()
    try:
        yield
    finally:
        AwareModulePluginRegistry.clear()


def _prepend_skill_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[4]
    monkeypatch.syspath_prepend(str(repo_root / "modules" / "skill" / "runtime"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[8]


def test_module_plugin_registry_registers_idempotently() -> None:
    plugin = AwareModulePlugin(provider_key="fake")
    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.register(plugin)
        AwareModulePluginRegistry.register(plugin)

        assert AwareModulePluginRegistry.get_provider_keys() == ("fake",)
        assert AwareModulePluginRegistry.get("fake") is plugin


def test_module_plugin_registry_bootstraps_plugins_from_explicit_repo_root(
    tmp_path: Path,
) -> None:
    bad_repo_root = tmp_path / "bad"
    bad_module_root = bad_repo_root / "modules" / "demo"
    bad_module_root.mkdir(parents=True)
    (bad_module_root / "aware.module.toml").write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "runtime"',
                "",
                "[[plugins]]",
                'kind = "code.module_plugin"',
                'provider_key = "aware_demo"',
                'semantic_contract_module = "missing_demo_runtime.semantic_contract"',
                "",
                "[[packages]]",
                'id = "runtime"',
                'kind = "runtime"',
                'manifest = "runtime/pyproject.toml"',
                'visibility = "module"',
                "",
            )
        ),
        encoding="utf-8",
    )

    good_repo_root = tmp_path / "good"
    good_module_root = good_repo_root / "modules" / "demo"
    good_runtime_root = good_module_root / "runtime"
    good_package = good_runtime_root / "aware_demo_runtime"
    good_package.mkdir(parents=True)
    (good_module_root / "aware.module.toml").write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "runtime"',
                "",
                "[[plugins]]",
                'kind = "code.module_plugin"',
                'provider_key = "aware_demo"',
                'semantic_contract_module = "aware_demo_runtime.semantic_contract"',
                "",
                "[[packages]]",
                'id = "runtime"',
                'kind = "runtime"',
                'manifest = "runtime/pyproject.toml"',
                'visibility = "module"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (good_package / "__init__.py").write_text("", encoding="utf-8")
    (good_package / "semantic_contract.py").write_text(
        "\n".join(
            (
                "from aware_code.module_semantic_contract import ModuleSemanticContract",
                "",
                "AWARE_MODULE_SEMANTIC_CONTRACT = ModuleSemanticContract(",
                '    provider_key="aware_demo",',
                ")",
                "",
            )
        ),
        encoding="utf-8",
    )

    runtime_root_text = good_runtime_root.resolve().as_posix()
    with _isolated_module_plugin_registry():
        try:
            AwareModulePluginRegistry.ensure_module_plugins_registered_from_repo_root(
                repo_root=bad_repo_root,
            )
            assert (
                AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                    "aware_demo"
                )
                == "missing_demo_runtime.semantic_contract"
            )
            assert (
                AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
                    "aware_demo"
                )
                is None
            )

            AwareModulePluginRegistry.ensure_module_plugins_registered_from_repo_root(
                repo_root=good_repo_root,
                replace_existing=True,
            )

            assert (
                AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                    "aware_demo"
                )
                == "aware_demo_runtime.semantic_contract"
            )
            contract = (
                AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
                    "aware_demo"
                )
            )
            assert contract is not None
            assert contract.provider_key == "aware_demo"
            assert runtime_root_text in sys.path
        finally:
            while runtime_root_text in sys.path:
                sys.path.remove(runtime_root_text)
            sys.modules.pop("aware_demo_runtime.semantic_contract", None)
            sys.modules.pop("aware_demo_runtime", None)


def test_resolved_semantic_capability_provider_preserves_participation_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = "fake_semantic_materialization_provider"
    module = ModuleType(module_name)

    def _materialize(**_: object) -> None:
        return None

    module.materialize = _materialize  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, module_name, module)
    plugin = AwareModulePlugin(provider_key="fake")
    delta_adapter = {
        "callable_module": module_name,
        "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
        "request_contract_version": (
            "aware.workspace.semantic-materialization.provider-delta-request.v1"
        ),
        "result_contract_version": (
            "aware.workspace.semantic-materialization.provider-delta-result.v1"
        ),
    }

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.register(plugin)
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                capability_participation=(
                    CapabilityParticipationDescriptor(
                        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
                        semantic_owner="fake.provider",
                        metadata={
                            SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: (
                                delta_adapter
                            ),
                        },
                    ),
                ),
                capability_execution_policy=(
                    ModuleCapabilityExecutionPolicyDescriptor(
                        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
                        semantic_owner="fake.provider",
                        callable_module=module_name,
                        callable_name="materialize",
                    ),
                ),
            )
        )

        resolved = AwareModulePluginRegistry.resolve_semantic_capability_provider(
            provider_key="fake",
            capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        )

    assert resolved is not None
    assert resolved.metadata == {
        SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: delta_adapter,
    }


def test_code_module_contract_validates_package_semantic_contract_roles() -> None:
    plugin = AwareModulePlugin(
        provider_key="fake",
        packages=(
            AwareModulePackageContract(
                id="ontology",
                kind="ontology",
                manifest="structure/ontology/aware.toml",
                semantic_contract=AwareModulePackageSemanticContract(
                    role="fake.ontology",
                    contract="aware.ontology",
                    provider_key="fake",
                    module="fake.semantic_contract",
                ),
            ),
        ),
    )
    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.register(plugin)
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                package_roles=(
                    ModuleSemanticPackageRoleDescriptor(
                        role="fake.ontology",
                        contract="aware.ontology",
                        package_kind="ontology",
                    ),
                ),
            )
        )

        contract = AwareModulePluginRegistry.code_module_contract_for_provider_key(
            "fake"
        )

        assert contract is not None
        assert contract.packages[0].semantic_contract is not None
        assert contract.packages[0].semantic_contract.role == "fake.ontology"


def test_code_module_contract_rejects_unknown_package_semantic_contract_role() -> None:
    plugin = AwareModulePlugin(
        provider_key="fake",
        packages=(
            AwareModulePackageContract(
                id="ontology",
                kind="ontology",
                manifest="structure/ontology/aware.toml",
                semantic_contract=AwareModulePackageSemanticContract(
                    role="fake.ontology",
                    contract="aware.ontology",
                    provider_key="fake",
                    module="fake.semantic_contract",
                ),
            ),
        ),
    )
    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.register(plugin)
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(provider_key="fake")
        )

        with pytest.raises(ValueError, match="does not declare that package role"):
            AwareModulePluginRegistry.code_module_contract_for_provider_key("fake")


def test_code_module_contract_rejects_disallowed_package_semantic_contract_capability() -> (
    None
):
    plugin = AwareModulePlugin(
        provider_key="fake",
        packages=(
            AwareModulePackageContract(
                id="ontology",
                kind="ontology",
                manifest="structure/ontology/aware.toml",
                semantic_contract=AwareModulePackageSemanticContract(
                    role="fake.ontology",
                    contract="aware.ontology",
                    provider_key="fake",
                    module="fake.semantic_contract",
                    bindings=(
                        AwareModulePackageSemanticContractBinding(
                            capability="diagnostics",
                            module="fake.binding",
                            callable="diagnostics",
                        ),
                    ),
                ),
            ),
        ),
    )
    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.register(plugin)
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                package_roles=(
                    ModuleSemanticPackageRoleDescriptor(
                        role="fake.ontology",
                        contract="aware.ontology",
                        package_kind="ontology",
                    ),
                ),
            )
        )

        with pytest.raises(ValueError, match="is not allowed"):
            AwareModulePluginRegistry.code_module_contract_for_provider_key("fake")


def test_module_semantic_contract_filters_artifact_leaf_ownership_descriptors() -> None:
    descriptor = ModuleSemanticArtifactLeafOwnershipDescriptor(
        semantic_owner="fake.provider",
        owner_manifest_kinds=("aware_fake_toml",),
        artifact_manifest_kinds=("pyproject_toml",),
        callable_module="fake.artifacts",
        callable_name="claim_artifact_leaf",
    )
    contract = ModuleSemanticContract(
        provider_key="fake",
        artifact_leaf_ownership=(descriptor,),
    )

    assert contract.artifact_leaf_ownership_for(
        semantic_owner="fake.provider",
        owner_manifest_kind="aware_fake_toml",
        artifact_manifest_kind="pyproject_toml",
    ) == (descriptor,)
    assert (
        contract.artifact_leaf_ownership_for(
            semantic_owner="fake.provider",
            owner_manifest_kind="aware_fake_toml",
            artifact_manifest_kind="pubspec_yaml",
        )
        == ()
    )


def test_module_semantic_contract_filters_materialization_artifact_output_descriptors() -> (
    None
):
    descriptor = ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner="fake.provider",
        producer_key="fake.semantic_materialization",
        output_key="runtime.index.graphsql",
        artifact_family="runtime_index",
        artifact_role="runtime",
        output_kind="sqlite",
        package_output_key="runtime.index",
        artifact_relpath=".aware/runtime/index/graphsql.sqlite",
        manifest_relpath=".aware/runtime/index/graphsql.manifest.json",
        media_type="application/vnd.aware.runtime-index+sqlite",
        runtime_contract_version="aware.runtime.index.v1",
        required_for=("runtime.index", "deployment"),
        provider_payload={"declared_by": "fake"},
    )
    contract = ModuleSemanticContract(
        provider_key="fake",
        materialization_artifact_outputs=(descriptor,),
    )

    assert contract.materialization_artifact_outputs_for(
        semantic_owner="fake.provider",
        producer_key="fake.semantic_materialization",
        artifact_family="runtime_index",
        required_for="runtime.index",
    ) == (descriptor,)
    assert (
        contract.materialization_artifact_outputs_for(
            semantic_owner="fake.provider",
            producer_key="fake.semantic_materialization",
            artifact_family="runtime_index",
            required_for="servicehost.bootstrap",
        )
        == ()
    )


def test_module_semantic_contract_filters_materialization_input_descriptors() -> None:
    descriptor = ModuleSemanticMaterializationInputDescriptor(
        semantic_owner="fake.provider",
        input_key="fake.compile_plan",
        input_kind="compile_plan",
        artifact_family="fake_compile_plan",
        artifact_role="compile_plan",
        package_family="fake",
        semantic_kind="fake_package",
        runtime_contract_version="aware.fake.compile_plan.v1",
        callable_module="fake.materialization.provider",
        callable_name="materialize",
        provider_payload={"declared_by": "fake"},
    )
    contract = ModuleSemanticContract(
        provider_key="fake",
        materialization_inputs=(descriptor,),
    )

    assert contract.materialization_inputs_for(
        semantic_owner="fake.provider",
        input_key="fake.compile_plan",
        input_kind="compile_plan",
        artifact_family="fake_compile_plan",
        package_family="fake",
        semantic_kind="fake_package",
    ) == (descriptor,)
    assert (
        contract.materialization_inputs_for(
            semantic_owner="fake.provider",
            input_key="other.compile_plan",
        )
        == ()
    )


def test_module_semantic_contract_filters_code_package_delta_output_descriptors() -> (
    None
):
    descriptor = ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor(
        semantic_owner="fake.provider",
        producer_key="fake.semantic_materialization",
        output_key="fake.generated_code_deltas",
        package_output_key="fake.generated_package",
        runtime_contract_version="aware.fake.code-delta.v1",
        required_for=("workspace_revision", "local_checkout"),
        provider_payload={"declared_by": "fake"},
    )
    contract = ModuleSemanticContract(
        provider_key="fake",
        materialization_code_package_delta_outputs=(descriptor,),
    )

    assert contract.materialization_code_package_delta_outputs_for(
        semantic_owner="fake.provider",
        producer_key="fake.semantic_materialization",
        output_key="fake.generated_code_deltas",
        authority_kind="semantic_materialization",
        required_for="workspace_revision",
    ) == (descriptor,)
    assert (
        contract.materialization_code_package_delta_outputs_for(
            semantic_owner="fake.provider",
            producer_key="fake.semantic_materialization",
            required_for="deployment_artifact",
        )
        == ()
    )


def test_module_semantic_contract_filters_materialization_package_output_descriptors() -> (
    None
):
    descriptor = ModuleSemanticMaterializationPackageOutputDescriptor(
        semantic_owner="fake.provider",
        producer_key="fake.view_target",
        output_key="fake.generated_target_package",
        target_provider_key="aware_target",
        target_semantic_owner="aware_target.provider",
        target_input_key="aware_target.compile_plan",
        target_package_family="target",
        target_semantic_kind="target_package",
        input_artifact_producer_key="fake.view_target",
        input_artifact_output_key="fake.target_compile_plan",
        input_artifact_family="target_compile_plan",
        runtime_contract_version="aware.target.compile_plan.v1",
        required_for=("workspace.semantic_materialization",),
        provider_payload={"declared_by": "fake"},
    )
    contract = ModuleSemanticContract(
        provider_key="fake",
        materialization_package_outputs=(descriptor,),
    )

    assert contract.materialization_package_outputs_for(
        semantic_owner="fake.provider",
        producer_key="fake.view_target",
        output_key="fake.generated_target_package",
        target_provider_key="aware_target",
        target_input_key="aware_target.compile_plan",
        required_for="workspace.semantic_materialization",
    ) == (descriptor,)
    assert (
        contract.materialization_package_outputs_for(
            semantic_owner="fake.provider",
            target_provider_key="aware_other",
            required_for="workspace.semantic_materialization",
        )
        == ()
    )


def test_module_plugin_registry_resolves_materialization_artifact_outputs_without_provider_import() -> (
    None
):
    descriptor = ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner="fake.provider",
        producer_key="fake.semantic_materialization",
        output_key="runtime.index.graphsql",
        artifact_family="runtime_index",
        required_for=("runtime.index",),
    )

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                materialization_artifact_outputs=(descriptor,),
            )
        )

        assert AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
            provider_key="fake",
            semantic_owner="fake.provider",
            producer_key="fake.semantic_materialization",
            required_for="runtime.index",
        ) == (
            descriptor,
        )
        assert (
            AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
                provider_key="fake",
                semantic_owner="fake.provider",
                producer_key="other",
                required_for="runtime.index",
            )
            == ()
        )


def test_module_plugin_registry_resolves_materialization_inputs_without_provider_import() -> (
    None
):
    descriptor = ModuleSemanticMaterializationInputDescriptor(
        semantic_owner="fake.provider",
        input_key="fake.compile_plan",
        input_kind="compile_plan",
        artifact_family="fake_compile_plan",
        package_family="fake",
        semantic_kind="fake_package",
    )

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                materialization_inputs=(descriptor,),
            )
        )

        assert (
            AwareModulePluginRegistry.semantic_materialization_inputs_for_provider_key(
                provider_key="fake",
                semantic_owner="fake.provider",
                input_key="fake.compile_plan",
                input_kind="compile_plan",
                artifact_family="fake_compile_plan",
            )
            == (descriptor,)
        )
        assert (
            AwareModulePluginRegistry.semantic_materialization_inputs_for_provider_key(
                provider_key="fake",
                semantic_owner="fake.provider",
                input_key="other.compile_plan",
            )
            == ()
        )


def test_module_plugin_registry_resolves_code_package_delta_outputs_without_provider_import() -> (
    None
):
    descriptor = ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor(
        semantic_owner="fake.provider",
        producer_key="fake.semantic_materialization",
        output_key="fake.generated_code_deltas",
        required_for=("workspace_revision",),
    )

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                materialization_code_package_delta_outputs=(descriptor,),
            )
        )

        assert AwareModulePluginRegistry.semantic_materialization_code_package_delta_outputs_for_provider_key(
            provider_key="fake",
            semantic_owner="fake.provider",
            producer_key="fake.semantic_materialization",
            required_for="workspace_revision",
        ) == (
            descriptor,
        )
        assert (
            AwareModulePluginRegistry.semantic_materialization_code_package_delta_outputs_for_provider_key(
                provider_key="fake",
                semantic_owner="fake.provider",
                producer_key="other",
                required_for="workspace_revision",
            )
            == ()
        )


def test_module_plugin_registry_resolves_materialization_package_outputs_without_provider_import() -> (
    None
):
    descriptor = ModuleSemanticMaterializationPackageOutputDescriptor(
        semantic_owner="fake.provider",
        producer_key="fake.view_target",
        output_key="fake.generated_target_package",
        target_provider_key="aware_target",
        target_input_key="aware_target.compile_plan",
        required_for=("workspace.semantic_materialization",),
    )

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry._module_semantic_contracts["fake"] = (  # noqa: SLF001
            ModuleSemanticContract(
                provider_key="fake",
                materialization_package_outputs=(descriptor,),
            )
        )

        assert AwareModulePluginRegistry.semantic_materialization_package_outputs_for_provider_key(
            provider_key="fake",
            semantic_owner="fake.provider",
            producer_key="fake.view_target",
            target_provider_key="aware_target",
            target_input_key="aware_target.compile_plan",
            required_for="workspace.semantic_materialization",
        ) == (
            descriptor,
        )
        assert (
            AwareModulePluginRegistry.semantic_materialization_package_outputs_for_provider_key(
                provider_key="fake",
                semantic_owner="fake.provider",
                target_provider_key="aware_other",
                required_for="workspace.semantic_materialization",
            )
            == ()
        )


def test_module_plugin_registry_loads_builtin_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)
    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()

        assert AwareModulePluginRegistry.get_provider_keys() == (
            "aware_grammar",
            "aware_code",
            "aware_workspace",
        )
        assert (
            AwareModulePluginRegistry.capability_contract_module_for_provider_key(
                "aware_grammar"
            )
            == "aware_grammar.language_service_capability_metadata"
        )
        assert (
            AwareModulePluginRegistry.capability_execution_module_for_provider_key(
                "aware_grammar"
            )
            == "aware_grammar.language_service_capabilities"
        )
        assert (
            AwareModulePluginRegistry.code_package_materialization_contract_module_for_provider_key(
                "aware_grammar"
            )
            == "aware_grammar.code_package_materialization_contract"
        )
        assert (
            AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                "aware_grammar"
            )
            == "aware_grammar.semantic_contract"
        )
        assert (
            AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                "aware_code"
            )
            == "aware_code.semantic_contract"
        )
        assert (
            AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                "aware_workspace"
            )
            == "aware_workspace.semantic_contract"
        )

        language_contract_for_provider = (
            AwareModulePluginRegistry.language_service_capability_contract_for_provider_key
        )
        language_execution_contract_for_provider = (
            AwareModulePluginRegistry.language_service_capability_execution_contract_for_provider_key
        )
        code_materialization_contract_for_provider = (
            AwareModulePluginRegistry.module_code_package_materialization_contract_for_provider_key
        )
        aware_grammar_contract = language_contract_for_provider("aware_grammar")
        aware_grammar_execution_contract = language_execution_contract_for_provider(
            "aware_grammar"
        )
        aware_grammar_materialization_contract = (
            code_materialization_contract_for_provider("aware_grammar")
        )
        aware_grammar_code_module_contract = (
            AwareModulePluginRegistry.code_module_contract_for_provider_key(
                "aware_grammar"
            )
        )

        assert isinstance(
            aware_grammar_contract, LanguageServiceModuleCapabilityContract
        )
        assert aware_grammar_contract.contract_module == (
            "aware_grammar.language_service_capability_metadata"
        )
        assert tuple(
            item.semantic_owner for item in aware_grammar_contract.capability_metadata
        ) == ("aware_grammar.lexical",)
        assert tuple(
            item.workspace_activation
            for item in aware_grammar_contract.capability_metadata
        ) == ("always",)
        assert isinstance(
            aware_grammar_execution_contract,
            LanguageServiceModuleCapabilityExecutionContract,
        )
        assert aware_grammar_execution_contract.execution_module == (
            "aware_grammar.language_service_capabilities"
        )
        assert tuple(
            (item.capability, item.provider_key, item.callable_name)
            for item in aware_grammar_execution_contract.execution_entrypoints
        ) == (
            ("semantic_tokens", "aware_grammar.lexical", "_lexical_provider"),
        )
        assert isinstance(
            aware_grammar_materialization_contract,
            ModuleCodePackageMaterializationContract,
        )
        assert isinstance(aware_grammar_code_module_contract, CodeModuleContract)
        assert aware_grammar_code_module_contract.provider_key == "aware_grammar"
        assert aware_grammar_code_module_contract.semantic_contract_module == (
            "aware_grammar.semantic_contract"
        )
        assert aware_grammar_code_module_contract.capability_execution_module == (
            "aware_grammar.language_service_capabilities"
        )
        assert (
            aware_grammar_code_module_contract.code_package_materialization_contract
            is aware_grammar_materialization_contract
        )
        assert aware_grammar_code_module_contract.workspace_fallback_for(
            capability="semantic_tokens"
        )
        assert tuple(
            item.surface
            for item in aware_grammar_code_module_contract.package_materializations_for(
                surface="runtime"
            )
        ) == ("runtime",)
        assert aware_grammar_code_module_contract.packages == ()
        assert AwareModulePluginRegistry.get_capability_execution_module_paths() == (
            "aware_code.language_service_capabilities",
            "aware_grammar.language_service_capabilities",
        )
        assert AwareModulePluginRegistry.get_semantic_contract_module_paths() == (
            "aware_code.semantic_contract",
            "aware_grammar.semantic_contract",
            "aware_workspace.semantic_contract",
        )
        assert AwareModulePluginRegistry.get_code_package_materialization_contract_module_paths() == (
            "aware_grammar.code_package_materialization_contract",
        )
        assert (
            AwareModulePluginRegistry.workspace_fallback_provider_keys_for_capability(
                capability="semantic_tokens"
            )
            == ("aware_code", "aware_grammar")
        )
        assert callable(
            AwareModulePluginRegistry.language_service_capability_provider(
                capability="semantic_tokens",
                provider_key="aware_grammar.lexical",
            )
        )


def test_module_plugin_registry_unions_capability_available_provider_keys_with_overlays() -> (
    None
):
    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()

        available_provider_keys = AwareModulePluginRegistry.get_language_service_capability_available_provider_keys(
            capability="semantic_tokens",
            module_provider_keys=("aware_grammar",),
            overlay_provider_keys=("test.semantic.overlay",),
        )

        assert available_provider_keys == (
            "aware_grammar.lexical",
            "test.semantic.overlay",
        )


def test_module_plugin_registry_resolves_capability_providers_with_overlay_override() -> (
    None
):
    def _overlay_provider(_collector) -> None:
        return None

    def _overlay_override(_collector) -> None:
        return None

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()

        resolved = (
            AwareModulePluginRegistry.resolve_language_service_capability_providers(
                capability="semantic_tokens",
                provider_keys=(
                    "test.semantic.overlay",
                    "aware_grammar.lexical",
                    "test.semantic.overlay",
                    "aware_code.section",
                    "missing.provider",
                ),
                overlay_providers={
                    "test.semantic.overlay": _overlay_provider,
                    "aware_grammar.lexical": _overlay_override,
                },
            )
        )

        assert tuple(provider_key for provider_key, _provider in resolved) == (
            "test.semantic.overlay",
            "aware_grammar.lexical",
            "aware_code.section",
        )
        assert resolved[0][1] is _overlay_provider
        assert resolved[1][1] is _overlay_override


def test_module_plugin_registry_resolves_descriptor_aware_execution_providers() -> None:
    def _overlay_provider(_collector) -> None:
        return None

    overlay_descriptor = LanguageServiceProviderDescriptor(
        capability="semantic_tokens",
        provider_key="test.semantic.overlay",
        semantic_owner="test.semantic.overlay",
        priority=5,
        workspace_activation="always",
    )

    with _isolated_module_plugin_registry():
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()

        resolved = AwareModulePluginRegistry.resolve_language_service_capability_execution_providers(
            capability="semantic_tokens",
            module_provider_keys=("aware_grammar", "aware_code"),
            overlay_descriptors=(overlay_descriptor,),
            overlay_providers={"test.semantic.overlay": _overlay_provider},
            descriptor_filter=lambda descriptor: descriptor.provider_key
            != "aware_code.section",
        )

        assert tuple(item.descriptor.provider_key for item in resolved) == (
            "test.semantic.overlay",
            "aware_grammar.lexical",
        )
        assert resolved[0].descriptor is overlay_descriptor
        assert resolved[0].provider is _overlay_provider
        assert resolved[1].descriptor.provider_key == "aware_grammar.lexical"
        assert resolved[
            1
        ].provider is AwareModulePluginRegistry.language_service_capability_provider(
            capability="semantic_tokens",
            provider_key="aware_grammar.lexical",
        )


def test_module_plugin_registry_loads_builtin_language_plugins(monkeypatch) -> None:
    real_import_module = module_plugin_registry.import_module

    def _fake_import_module(module_name: str):
        if module_name.startswith("dart_grammar."):
            raise ModuleNotFoundError(module_name)
        return real_import_module(module_name)

    monkeypatch.setattr(module_plugin_registry, "import_module", _fake_import_module)

    with _isolated_module_plugin_registry():
        code_plugins = AwareModulePluginRegistry.get_builtin_code_language_plugins()
        meta_plugins = AwareModulePluginRegistry.get_builtin_meta_language_plugins()

        assert [plugin.language for plugin in code_plugins] == [
            CodeLanguage.aware,
            CodeLanguage.sql,
            CodeLanguage.python,
        ]
        assert [getattr(plugin, "language") for plugin in meta_plugins] == [
            CodeLanguage.aware,
            CodeLanguage.sql,
            CodeLanguage.python,
        ]


def test_module_plugin_registry_loads_module_plugins_from_manifests(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "aware.repo.toml").write_text(
        "\n".join(
            (
                "aware_repo = 1",
                "",
                "[repo]",
                'handle = "aware-test"',
                'workspaces_dir = "workspaces"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "workspaces").mkdir()
    module_root = tmp_path / "modules" / "demo"
    module_root.mkdir(parents=True)
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[[plugins]]",
                'kind = "code.module_plugin"',
                'provider_key = "aware_demo"',
                (
                    "capability_contract_module = "
                    '"aware_demo_runtime.language_service_capability_metadata"'
                ),
                (
                    "capability_execution_module = "
                    '"aware_demo_runtime.language_service_capabilities"'
                ),
                (
                    "code_package_materialization_contract_module = "
                    '"aware_demo_runtime.code_package_materialization_contract"'
                ),
                "",
                "[[plugins.capability_policy]]",
                'capability = "semantic_tokens"',
                'workspace_activation = "always"',
                "workspace_fallback = true",
                "",
                "[[packages]]",
                'aware_toml_path = "structure/ontology/aware.toml"',
                "",
                "[packages.semantic_contract]",
                'role = "demo.ontology"',
                'contract = "aware.ontology"',
                'provider_key = "aware_demo"',
                'module = "aware_demo_runtime.semantic_contract"',
                "",
                "[[packages.semantic_contract.bindings]]",
                'capability = "diagnostics"',
                'module = "aware_demo_runtime.ontology_binding"',
                'callable = "diagnostics"',
                "",
                "[[packages.semantic_contract.bindings]]",
                'capability = "semantic_tokens"',
                'module = "aware_demo_runtime.ontology_binding"',
                'callable = "semantic_tokens"',
                "",
                "[[packages]]",
                'id = "demo_api"',
                'kind = "api"',
                'manifest = "apis/demo/aware.api.toml"',
                'visibility = "public"',
                "",
                "[[packages]]",
                'id = "runtime"',
                'kind = "runtime"',
                'manifest = "runtime/pyproject.toml"',
                'visibility = "module"',
                "",
                "[packages.semantic_contract]",
                'role = "aware_demo.provider"',
                'contract = "aware.semantic_provider"',
                'provider_key = "aware_demo"',
                'module = "aware_demo_runtime.semantic_contract"',
                'owns_manifest_kinds = ["aware_demo_toml"]',
                'capabilities = ["diagnostics", "semantic_tokens", "materialize"]',
                "",
            )
        ),
        encoding="utf-8",
    )

    plugin_package = tmp_path / "aware_demo_runtime"
    plugin_package.mkdir()
    (plugin_package / "__init__.py").write_text("", encoding="utf-8")
    (plugin_package / "semantic_package.py").write_text(
        "\n".join(
            (
                "from aware_code.semantic_package import SemanticPackageProvider, SemanticPackageRegistry",
                "",
                "class _DemoSemanticPackageProvider(SemanticPackageProvider):",
                "    @property",
                "    def provider_key(self) -> str:",
                '        return "aware_demo"',
                "",
                "    def resolve(self, code_package):",
                "        del code_package",
                "        return ()",
                "",
                "def register_semantic_package_providers() -> None:",
                "    SemanticPackageRegistry.register(_DemoSemanticPackageProvider())",
                "",
            )
        ),
        encoding="utf-8",
    )
    (plugin_package / "semantic_scope.py").write_text(
        "\n".join(
            (
                "from aware_code.semantic_scope import SemanticScopeProvider, SemanticScopeRegistry",
                "",
                "class _DemoSemanticScopeProvider(SemanticScopeProvider):",
                "    @property",
                "    def provider_key(self) -> str:",
                '        return "aware_demo"',
                "",
                "    @property",
                "    def scope_keys(self) -> tuple[str, ...]:",
                '        return ("aware_demo.scope",)',
                "",
                "    def resolve(self, code_package, *, workspace_root):",
                "        del code_package",
                "        del workspace_root",
                "        return ()",
                "",
                "def register_semantic_scope_providers() -> None:",
                "    SemanticScopeRegistry.register(_DemoSemanticScopeProvider())",
                "",
            )
        ),
        encoding="utf-8",
    )
    (plugin_package / "semantic_contract.py").write_text(
        "\n".join(
            (
                (
                    "from aware_code.module_semantic_contract import "
                    "ModuleCapabilityExecutionPolicyDescriptor, "
                    "ModuleSemanticContract, "
                    "ModuleSemanticPackageRoleDescriptor"
                ),
                (
                    "from aware_code.semantic_package.schemas import "
                    "CapabilityParticipationDescriptor"
                ),
                "",
                "AWARE_MODULE_SEMANTIC_CONTRACT = ModuleSemanticContract(",
                '    provider_key="aware_demo",',
                '    semantic_scope_keys=("aware_demo.scope",),',
                "    capability_participation=(",
                "        CapabilityParticipationDescriptor(",
                '            capability="semantic_tokens",',
                '            semantic_owner="aware_demo.surface",',
                "        ),",
                "    ),",
                "    capability_execution_policy=(",
                "        ModuleCapabilityExecutionPolicyDescriptor(",
                '            capability="semantic_tokens",',
                '            semantic_owner="aware_demo.surface",',
                '            callable_name="_demo_surface_provider",',
                "        ),",
                "    ),",
                "    package_roles=(",
                "        ModuleSemanticPackageRoleDescriptor(",
                '            role="demo.ontology",',
                '            contract="aware.ontology",',
                '            package_kind="ontology",',
                '            capabilities=("diagnostics", "semantic_tokens"),',
                "        ),",
                "        ModuleSemanticPackageRoleDescriptor(",
                '            role="aware_demo.provider",',
                '            contract="aware.semantic_provider",',
                '            package_kind="runtime",',
                '            capabilities=("diagnostics", "semantic_tokens", "materialize"),',
                '            owns_manifest_kinds=("aware_demo_toml",),',
                "        ),",
                "    ),",
                ")",
                "",
            )
        ),
        encoding="utf-8",
    )
    (plugin_package / "code_package_materialization_contract.py").write_text(
        "\n".join(
            (
                (
                    "from aware_code.module_code_package_materialization_contract import "
                    "ModuleCodePackageMaterializationContract, "
                    "ModuleCodePackageMaterializationDescriptor"
                ),
                "",
                "AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT = (",
                "    ModuleCodePackageMaterializationContract(",
                '        provider_key="aware_demo",',
                "        package_materializations=(",
                "            ModuleCodePackageMaterializationDescriptor(",
                '                surface="runtime",',
                '                language="python",',
                '                manager="uv",',
                '                distribution_name="aware-demo",',
                '                import_root="aware_demo_runtime",',
                '                package_root_relpath="modules/demo/runtime",',
                '                manifest_relpath="modules/demo/runtime/pyproject.toml",',
                "            ),",
                "        ),",
                "    )",
                ")",
                "",
            )
        ),
        encoding="utf-8",
    )
    (plugin_package / "language_service_capability_metadata.py").write_text(
        "\n".join(
            (
                (
                    "from aware_code.language_service_capability_contract import "
                    "build_language_service_capability_metadata_from_semantic_contract"
                ),
                "from aware_demo_runtime.semantic_contract import AWARE_MODULE_SEMANTIC_CONTRACT",
                "",
                "AWARE_DEMO_CAPABILITY_METADATA = (",
                "    build_language_service_capability_metadata_from_semantic_contract(",
                "        AWARE_MODULE_SEMANTIC_CONTRACT,",
                "    )",
                ")",
                "",
            )
        ),
        encoding="utf-8",
    )
    (plugin_package / "language_service_capabilities.py").write_text(
        "\n".join(
            (
                "def _demo_surface_provider(_collector):",
                "    return None",
                "",
            )
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("AWARE_REPO_ROOT", str(tmp_path))
    monkeypatch.syspath_prepend(str(tmp_path))

    with _isolated_module_plugin_registry():
        SemanticPackageRegistry.clear()
        SemanticScopeRegistry.clear()
        try:
            AwareModulePluginRegistry.ensure_module_plugins_registered_from_repo_root(
                repo_root=tmp_path,
            )

            assert AwareModulePluginRegistry.get_provider_keys() == (
                "aware_grammar",
                "aware_code",
                "aware_workspace",
                "aware_demo",
            )
            assert (
                AwareModulePluginRegistry.capability_contract_module_for_provider_key(
                    "aware_demo"
                )
                == "aware_demo_runtime.language_service_capability_metadata"
            )
            assert (
                AwareModulePluginRegistry.capability_execution_module_for_provider_key(
                    "aware_demo"
                )
                == "aware_demo_runtime.language_service_capabilities"
            )
            assert (
                AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
                    "aware_demo"
                )
                == "aware_demo_runtime.semantic_contract"
            )
            assert (
                AwareModulePluginRegistry.code_package_materialization_contract_module_for_provider_key(
                    "aware_demo"
                )
                == "aware_demo_runtime.code_package_materialization_contract"
            )
            assert (
                AwareModulePluginRegistry.get_capability_execution_module_paths()
                == (
                    "aware_code.language_service_capabilities",
                    "aware_demo_runtime.language_service_capabilities",
                    "aware_grammar.language_service_capabilities",
                )
            )
            assert AwareModulePluginRegistry.get_capability_contract_module_paths() == (
                "aware_code.language_service_capability_metadata",
                "aware_demo_runtime.language_service_capability_metadata",
                "aware_grammar.language_service_capability_metadata",
            )
            assert AwareModulePluginRegistry.get_semantic_contract_module_paths() == (
                "aware_code.semantic_contract",
                "aware_demo_runtime.semantic_contract",
                "aware_grammar.semantic_contract",
                "aware_workspace.semantic_contract",
            )
            assert AwareModulePluginRegistry.get_code_package_materialization_contract_module_paths() == (
                "aware_demo_runtime.code_package_materialization_contract",
                "aware_grammar.code_package_materialization_contract",
            )
            language_contract_for_provider = (
                AwareModulePluginRegistry.language_service_capability_contract_for_provider_key
            )
            language_execution_contract_for_provider = (
                AwareModulePluginRegistry.language_service_capability_execution_contract_for_provider_key
            )
            code_materialization_contract_for_provider = (
                AwareModulePluginRegistry.module_code_package_materialization_contract_for_provider_key
            )
            contract = language_contract_for_provider("aware_demo")
            semantic_contract = (
                AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
                    "aware_demo"
                )
            )
            materialization_contract = code_materialization_contract_for_provider(
                "aware_demo"
            )
            assert isinstance(contract, LanguageServiceModuleCapabilityContract)
            assert contract.provider_key == "aware_demo"
            assert contract.contract_module == (
                "aware_demo_runtime.language_service_capability_metadata"
            )
            assert isinstance(semantic_contract, ModuleSemanticContract)
            assert semantic_contract.provider_key == "aware_demo"
            assert semantic_contract.semantic_scope_keys == ("aware_demo.scope",)
            assert isinstance(
                materialization_contract,
                ModuleCodePackageMaterializationContract,
            )
            assert materialization_contract.provider_key == "aware_demo"
            assert tuple(
                item.surface
                for item in materialization_contract.package_materializations
            ) == ("runtime",)
            assert tuple(
                item.semantic_owner for item in contract.capability_metadata
            ) == ("aware_demo.surface",)
            assert tuple(
                item.workspace_activation for item in contract.capability_metadata
            ) == ("always",)
            assert tuple(
                item.provider_key
                for item in AwareModulePluginRegistry.get_language_service_provider_descriptors(
                    provider_keys=("aware_demo",)
                )
            ) == ("aware_demo.surface",)
            execution_contract = language_execution_contract_for_provider("aware_demo")
            assert isinstance(
                execution_contract,
                LanguageServiceModuleCapabilityExecutionContract,
            )
            assert tuple(
                (item.capability, item.provider_key, item.callable_name)
                for item in execution_contract.execution_entrypoints
            ) == (
                ("semantic_tokens", "aware_demo.surface", "_demo_surface_provider"),
            )
            assert AwareModulePluginRegistry.workspace_fallback_provider_keys_for_capability(
                capability="semantic_tokens"
            ) == (
                "aware_code",
                "aware_demo",
                "aware_grammar",
            )
            assert callable(
                AwareModulePluginRegistry.language_service_capability_provider(
                    capability="semantic_tokens",
                    provider_key="aware_demo.surface",
                )
            )
            assert tuple(
                item.provider_key
                for item in AwareModulePluginRegistry.get_module_semantic_contracts()
            ) == ("aware_code", "aware_demo", "aware_grammar", "aware_workspace")
            assert tuple(
                item.provider_key
                for item in AwareModulePluginRegistry.get_module_code_package_materialization_contracts()
            ) == ("aware_demo", "aware_grammar")
            code_module_contract = (
                AwareModulePluginRegistry.code_module_contract_for_provider_key(
                    "aware_demo"
                )
            )
            assert isinstance(code_module_contract, CodeModuleContract)
            assert code_module_contract.provider_key == "aware_demo"
            assert code_module_contract.semantic_contract is semantic_contract
            assert tuple(
                (
                    package.id,
                    package.kind,
                    package.manifest,
                    package.visibility,
                    (
                        (
                            package.semantic_contract.role,
                            package.semantic_contract.contract,
                            package.semantic_contract.provider_key,
                            package.semantic_contract.module,
                            tuple(
                                (
                                    binding.capability,
                                    binding.module,
                                    binding.callable,
                                )
                                for binding in package.semantic_contract.bindings
                            ),
                        )
                        if package.semantic_contract is not None
                        else None
                    ),
                    tuple(
                        (
                            binding.role,
                            binding.contract,
                            binding.binding_module,
                            binding.capabilities,
                            binding.callable_name,
                        )
                        for binding in package.semantic_bindings
                    ),
                    package.mirrors_ontology,
                )
                for package in code_module_contract.packages
            ) == (
                (
                    "ontology",
                    "ontology",
                    "structure/ontology/aware.toml",
                    "module",
                    (
                        "demo.ontology",
                        "aware.ontology",
                        "aware_demo",
                        "aware_demo_runtime.semantic_contract",
                        (
                            (
                                "diagnostics",
                                "aware_demo_runtime.ontology_binding",
                                "diagnostics",
                            ),
                            (
                                "semantic_tokens",
                                "aware_demo_runtime.ontology_binding",
                                "semantic_tokens",
                            ),
                        ),
                    ),
                    (),
                    False,
                ),
                (
                    "demo_api",
                    "api",
                    "apis/demo/aware.api.toml",
                    "public",
                    None,
                    (),
                    False,
                ),
                (
                    "runtime",
                    "runtime",
                    "runtime/pyproject.toml",
                    "module",
                    (
                        "aware_demo.provider",
                        "aware.semantic_provider",
                        "aware_demo",
                        "aware_demo_runtime.semantic_contract",
                        (),
                    ),
                    (),
                    False,
                ),
            )
            assert tuple(
                package.id
                for package in code_module_contract.packages_for_kind(kind="api")
            ) == ("demo_api",)
            assert (
                code_module_contract.code_package_materialization_contract
                is materialization_contract
            )
            assert code_module_contract.workspace_fallback_for(
                capability="semantic_tokens"
            )
            assert tuple(
                item.provider_key
                for item in code_module_contract.language_service_provider_descriptors
            ) == ("aware_demo.surface",)
            assert tuple(
                item.provider_key
                for item in AwareModulePluginRegistry.get_code_module_contracts()
            ) == ("aware_code", "aware_demo", "aware_grammar", "aware_workspace")

            SemanticPackageRegistry.ensure_builtin_providers_registered()
            SemanticScopeRegistry.ensure_builtin_providers_registered()
            assert SemanticPackageRegistry.get_provider_keys() == (
                "aware_code",
                "aware_demo",
                "aware_workspace",
            )
            assert SemanticScopeRegistry.get_provider_keys() == ("aware_demo",)
        finally:
            SemanticPackageRegistry.clear()
            SemanticScopeRegistry.clear()


def test_language_service_bootstrap_keeps_builtin_execution_contract_driven() -> None:
    clear_diagnostics_capability_providers()
    clear_semantic_tokens_capability_providers()
    with _isolated_module_plugin_registry():
        ensure_builtin_language_service_capability_providers_registered()

        assert AwareModulePluginRegistry.get_provider_keys() == (
            "aware_grammar",
            "aware_code",
            "aware_workspace",
        )
        assert get_registered_diagnostics_capability_descriptors() == ()
        assert get_registered_semantic_tokens_capability_descriptors() == ()
    clear_diagnostics_capability_providers()
    clear_semantic_tokens_capability_providers()


def test_builtin_language_service_capability_modules_do_not_export_legacy_registration_hooks() -> (
    None
):
    capability_modules = (
        "aware_grammar.language_service_capabilities",
        "aware_code.language_service_capabilities",
    )

    for module_name in capability_modules:
        module = import_module(module_name)
        assert (
            getattr(module, "register_language_service_capability_providers", None)
            is None
        )


def test_semantic_package_registry_bootstrap_uses_module_plugin_registry() -> None:
    seen: list[str] = []

    with _isolated_module_plugin_registry():
        SemanticPackageRegistry.clear()
        try:
            AwareModulePluginRegistry.register(
                AwareModulePlugin(
                    provider_key="fake",
                    register_semantic_package_providers=lambda: seen.append(
                        "semantic_package"
                    ),
                )
            )
            AwareModulePluginRegistry._builtin_bootstrap_attempted = True

            SemanticPackageRegistry.ensure_builtin_providers_registered()
        finally:
            SemanticPackageRegistry.clear()

    assert seen == ["semantic_package"]


def test_semantic_scope_registry_bootstrap_uses_module_plugin_registry() -> None:
    seen: list[str] = []

    with _isolated_module_plugin_registry():
        SemanticScopeRegistry.clear()
        try:
            AwareModulePluginRegistry.register(
                AwareModulePlugin(
                    provider_key="fake",
                    register_semantic_scope_providers=lambda: seen.append(
                        "semantic_scope"
                    ),
                )
            )
            AwareModulePluginRegistry._builtin_bootstrap_attempted = True

            SemanticScopeRegistry.ensure_builtin_providers_registered()
        finally:
            SemanticScopeRegistry.clear()

    assert seen == ["semantic_scope"]
