from __future__ import annotations

from dataclasses import dataclass
import sys

from aware_code.package.semantic_binding import (
    package_semantic_binding_callable_name,
    package_semantic_binding_provider_descriptors,
    package_semantic_binding_provider_map,
    package_semantic_contract_provider_descriptors,
    package_semantic_contract_provider_map,
    resolve_package_semantic_binding_providers,
    resolve_package_semantic_contract_providers,
)


@dataclass(frozen=True, slots=True)
class _Binding:
    role: str
    contract: str
    binding_module: str | None
    capabilities: tuple[str, ...]
    callable_name: str | None = None


@dataclass(frozen=True, slots=True)
class _ContractBinding:
    capability: str
    module: str
    callable: str


@dataclass(frozen=True, slots=True)
class _Contract:
    role: str
    contract: str
    provider_key: str
    module: str
    bindings: tuple[_ContractBinding, ...]


def test_package_semantic_contract_resolves_provider_from_module_runtime_root(tmp_path):
    runtime_root = tmp_path / "modules" / "home" / "runtime"
    package_root = runtime_root / "demo_home_contract_binding"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "language_service_binding.py").write_text(
        "\n".join(
            (
                "def custom_diagnostics(context):",
                "    return [{'message': 'contract binding active'}]",
                "",
                "def semantic_tokens(collector):",
                "    collector.append('home-token')",
            )
        ),
        encoding="utf-8",
    )

    contract = _Contract(
        role="home.ontology",
        contract="aware.ontology",
        provider_key="home",
        module="demo_home_contract_binding.semantic_contract",
        bindings=(
            _ContractBinding(
                capability="diagnostics",
                module="demo_home_contract_binding.language_service_binding",
                callable="custom_diagnostics",
            ),
            _ContractBinding(
                capability="semantic_tokens",
                module="demo_home_contract_binding.language_service_binding",
                callable="semantic_tokens",
            ),
        ),
    )

    resolved = resolve_package_semantic_contract_providers(
        capability="diagnostics",
        workspace_root=tmp_path,
        module_root_relative_path="modules/home",
        semantic_contract=contract,
        provider_keys=("home.ontology",),
    )

    assert len(resolved) == 1
    assert resolved[0].provider_key == "home.ontology"
    assert resolved[0].semantic_owner == "home.ontology"
    assert resolved[0].contract == "aware.ontology"
    assert resolved[0].binding_module == (
        "demo_home_contract_binding.language_service_binding"
    )
    assert resolved[0].callable_name == "custom_diagnostics"
    assert resolved[0].module_runtime_root == runtime_root.resolve()
    assert resolved[0].provider(None) == [{"message": "contract binding active"}]
    assert runtime_root.as_posix() not in sys.path


def test_package_semantic_contract_provider_descriptors_are_code_owned() -> None:
    contract = _Contract(
        role="home.ontology",
        contract="aware.ontology",
        provider_key="home",
        module="aware_home.semantic_contract",
        bindings=(
            _ContractBinding(
                capability="diagnostics",
                module="aware_home.language_service_binding",
                callable="diagnostics",
            ),
        ),
    )

    descriptors = package_semantic_contract_provider_descriptors(
        capability="diagnostics",
        semantic_contract=contract,
    )

    assert len(descriptors) == 1
    assert descriptors[0].capability == "diagnostics"
    assert descriptors[0].provider_key == "home.ontology"
    assert descriptors[0].semantic_owner == "home.ontology"
    assert descriptors[0].module_provider_key == "home"
    assert descriptors[0].priority == 25
    assert descriptors[0].workspace_activation == "owner"
    assert (
        package_semantic_contract_provider_descriptors(
            capability="hover",
            semantic_contract=contract,
        )
        == ()
    )


def test_package_semantic_binding_resolves_provider_from_module_runtime_root(tmp_path):
    runtime_root = tmp_path / "modules" / "home" / "runtime"
    package_root = runtime_root / "demo_home_binding"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "language_service_binding.py").write_text(
        "\n".join(
            (
                "def diagnostics(context):",
                "    return [{'message': 'home binding active'}]",
                "",
                "def semantic_tokens(collector):",
                "    collector.append('home-token')",
            )
        ),
        encoding="utf-8",
    )

    binding = _Binding(
        role="home.ontology",
        contract="aware.ontology",
        binding_module="demo_home_binding.language_service_binding",
        capabilities=("diagnostics", "semantic_tokens"),
    )

    resolved = resolve_package_semantic_binding_providers(
        capability="diagnostics",
        workspace_root=tmp_path,
        module_root_relative_path="modules/home",
        semantic_bindings=(binding,),
        provider_keys=("home.ontology",),
    )

    assert len(resolved) == 1
    assert resolved[0].provider_key == "home.ontology"
    assert resolved[0].semantic_owner == "home.ontology"
    assert resolved[0].contract == "aware.ontology"
    assert resolved[0].binding_module == "demo_home_binding.language_service_binding"
    assert resolved[0].callable_name == "diagnostics"
    assert resolved[0].module_runtime_root == runtime_root.resolve()
    assert resolved[0].provider(None) == [{"message": "home binding active"}]
    assert runtime_root.as_posix() not in sys.path


def test_package_semantic_binding_provider_map_filters_by_capability_and_provider_key(
    tmp_path,
):
    runtime_root = tmp_path / "modules" / "home" / "runtime"
    package_root = runtime_root / "demo_home_binding"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "language_service_binding.py").write_text(
        "\n".join(
            (
                "def diagnostics(context):",
                "    return ['diagnostic']",
                "",
                "def semantic_tokens(collector):",
                "    collector.append('token')",
            )
        ),
        encoding="utf-8",
    )

    binding = _Binding(
        role="home.ontology",
        contract="aware.ontology",
        binding_module="demo_home_binding.language_service_binding",
        capabilities=("diagnostics",),
    )

    assert (
        package_semantic_binding_provider_map(
            capability="semantic_tokens",
            workspace_root=tmp_path,
            module_root_relative_path="modules/home",
            semantic_bindings=(binding,),
            provider_keys=("home.ontology",),
        )
        == {}
    )
    assert (
        package_semantic_binding_provider_map(
            capability="diagnostics",
            workspace_root=tmp_path,
            module_root_relative_path="modules/home",
            semantic_bindings=(binding,),
            provider_keys=("other.ontology",),
        )
        == {}
    )


def test_package_semantic_contract_provider_map_filters_by_capability_and_provider_key(
    tmp_path,
):
    runtime_root = tmp_path / "modules" / "home" / "runtime"
    package_root = runtime_root / "demo_home_binding"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "language_service_binding.py").write_text(
        "\n".join(
            (
                "def diagnostics(context):",
                "    return ['diagnostic']",
            )
        ),
        encoding="utf-8",
    )

    contract = _Contract(
        role="home.ontology",
        contract="aware.ontology",
        provider_key="home",
        module="demo_home_binding.semantic_contract",
        bindings=(
            _ContractBinding(
                capability="diagnostics",
                module="demo_home_binding.language_service_binding",
                callable="diagnostics",
            ),
        ),
    )

    assert (
        package_semantic_contract_provider_map(
            capability="semantic_tokens",
            workspace_root=tmp_path,
            module_root_relative_path="modules/home",
            semantic_contract=contract,
            provider_keys=("home.ontology",),
        )
        == {}
    )
    assert (
        package_semantic_contract_provider_map(
            capability="diagnostics",
            workspace_root=tmp_path,
            module_root_relative_path="modules/home",
            semantic_contract=contract,
            provider_keys=("other.ontology",),
        )
        == {}
    )


def test_package_semantic_binding_uses_capability_specific_callable(tmp_path):
    runtime_root = tmp_path / "modules" / "home" / "runtime"
    package_root = runtime_root / "demo_home_custom_binding"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "language_service_binding.py").write_text(
        "\n".join(
            (
                "def custom_diagnostics(context):",
                "    return [{'message': 'custom diagnostics'}]",
            )
        ),
        encoding="utf-8",
    )

    binding = _Binding(
        role="home.ontology",
        contract="aware.ontology",
        binding_module="demo_home_custom_binding.language_service_binding",
        capabilities=("diagnostics",),
        callable_name="custom_diagnostics",
    )

    resolved = resolve_package_semantic_binding_providers(
        capability="diagnostics",
        workspace_root=tmp_path,
        module_root_relative_path="modules/home",
        semantic_bindings=(binding,),
        provider_keys=("home.ontology",),
    )

    assert len(resolved) == 1
    assert resolved[0].callable_name == "custom_diagnostics"
    assert resolved[0].provider(None) == [{"message": "custom diagnostics"}]


def test_package_semantic_binding_provider_descriptors_are_code_owned() -> None:
    diagnostics_binding = _Binding(
        role="home.ontology",
        contract="aware.ontology",
        binding_module="demo_home_binding.language_service_binding",
        capabilities=("diagnostics", "semantic_tokens"),
    )
    declared_only_binding = _Binding(
        role="home.declared_only",
        contract="aware.ontology",
        binding_module=None,
        capabilities=("diagnostics",),
    )

    descriptors = package_semantic_binding_provider_descriptors(
        capability="diagnostics",
        module_provider_key="home",
        semantic_bindings=(declared_only_binding, diagnostics_binding),
    )

    assert len(descriptors) == 1
    assert descriptors[0].capability == "diagnostics"
    assert descriptors[0].provider_key == "home.ontology"
    assert descriptors[0].semantic_owner == "home.ontology"
    assert descriptors[0].module_provider_key == "home"
    assert descriptors[0].priority == 25
    assert descriptors[0].workspace_activation == "owner"
    assert (
        package_semantic_binding_provider_descriptors(
            capability="hover",
            module_provider_key="home",
            semantic_bindings=(diagnostics_binding,),
        )
        == ()
    )


def test_package_semantic_binding_unknown_capability_is_not_executable(tmp_path):
    binding = _Binding(
        role="home.ontology",
        contract="aware.ontology",
        binding_module="demo_home_binding.language_service_binding",
        capabilities=("diagnostics",),
    )

    assert package_semantic_binding_callable_name(capability="hover") is None
    assert (
        resolve_package_semantic_binding_providers(
            capability="hover",
            workspace_root=tmp_path,
            module_root_relative_path="modules/home",
            semantic_bindings=(binding,),
            provider_keys=("home.ontology",),
        )
        == ()
    )
