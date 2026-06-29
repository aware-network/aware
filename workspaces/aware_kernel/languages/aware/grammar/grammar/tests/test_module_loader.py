from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from aware_grammar.module.loader import AwareModuleTomlError, load_aware_module_spec


def _write_module_toml(*, tmp_path, body: str):
    toml_path = tmp_path / "aware.module.toml"
    toml_path.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    return toml_path


def test_repo_aware_module_manifests_do_not_use_legacy_package_semantic_bindings() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    offenders = tuple(
        sorted(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / "modules").glob("**/aware.module.toml")
            if "[[packages.semantic_bindings]]" in path.read_text(encoding="utf-8")
        )
    )

    assert offenders == ()


def test_repo_aware_module_manifests_do_not_use_legacy_aware_toml_path() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    offenders = tuple(
        sorted(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / "modules").glob("**/aware.module.toml")
            if "aware_toml_path" in path.read_text(encoding="utf-8")
        )
    )

    assert offenders == ()


def test_repo_aware_module_manifests_do_not_use_plugin_semantic_provider_modules() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    offenders = tuple(
        sorted(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / "modules").glob("**/aware.module.toml")
            if (
                "semantic_package_module" in path.read_text(encoding="utf-8")
                or "semantic_scope_module" in path.read_text(encoding="utf-8")
            )
        )
    )

    assert offenders == ()


def test_load_aware_module_spec_parses_code_module_plugin(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        capability_contract_module = "aware_demo_runtime.language_service_capability_metadata"
        capability_execution_module = "aware_demo_runtime.language_service_capabilities"
        semantic_contract_module = "aware_demo_runtime.semantic_contract"
        code_package_materialization_contract_module = "aware_demo_runtime.code_package_materialization_contract"

        [[plugins.capability_policy]]
        capability = "semantic_tokens"
        workspace_activation = "always"
        workspace_fallback = true

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    assert len(spec.plugins) == 1
    plugin = spec.plugins[0]
    assert plugin.kind == "code.module_plugin"
    assert plugin.provider_key == "aware_demo"
    assert plugin.module is None
    assert (
        plugin.capability_contract_module
        == "aware_demo_runtime.language_service_capability_metadata"
    )
    assert plugin.capability_execution_module == "aware_demo_runtime.language_service_capabilities"
    assert plugin.semantic_contract_module == "aware_demo_runtime.semantic_contract"
    assert (
        plugin.code_package_materialization_contract_module
        == "aware_demo_runtime.code_package_materialization_contract"
    )
    assert tuple(
        (policy.capability, policy.workspace_activation, policy.workspace_fallback)
        for policy in plugin.capability_policy
    ) == (("semantic_tokens", "always", True),)
    assert plugin.name is None
    assert plugin.required is True


def test_load_aware_module_spec_normalizes_legacy_package_shape(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    assert len(spec.packages) == 1
    package = spec.packages[0]
    assert package.id == "ontology"
    assert package.kind == "ontology"
    assert package.manifest == "structure/ontology/aware.toml"
    assert package.aware_toml_path == "structure/ontology/aware.toml"
    assert package.visibility == "module"


def test_load_aware_module_spec_parses_normalized_package_shape(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[packages]]
        id = "home_ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"
        visibility = "public"

        [[packages.semantic_bindings]]
        role = "demo.ontology"
        contract = "aware.ontology"
        binding_module = "aware_demo_runtime.ontology_binding"
        capabilities = ["diagnostics", "semantic_tokens"]
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    assert len(spec.packages) == 1
    package = spec.packages[0]
    assert package.id == "home_ontology"
    assert package.kind == "ontology"
    assert package.manifest == "structure/ontology/aware.toml"
    assert package.aware_toml_path == "structure/ontology/aware.toml"
    assert package.visibility == "public"
    assert tuple(
        (
            binding.role,
            binding.contract,
            binding.binding_module,
            binding.capabilities,
            binding.callable_name,
        )
        for binding in package.semantic_bindings
    ) == (
        (
            "demo.ontology",
            "aware.ontology",
            "aware_demo_runtime.ontology_binding",
            ("diagnostics", "semantic_tokens"),
            None,
        ),
    )


def test_load_aware_module_spec_parses_package_semantic_contract(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        semantic_contract_module = "aware_demo_runtime.semantic_contract"

        [[packages]]
        id = "home_ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"

        [packages.semantic_contract]
        role = "demo.ontology"
        contract = "aware.ontology"
        provider_key = "aware_demo"
        module = "aware_demo_runtime.semantic_contract"

        [[packages.semantic_contract.bindings]]
        capability = "diagnostics"
        module = "aware_demo_runtime.ontology_binding"
        callable = "diagnostics"

        [[packages.semantic_contract.bindings]]
        capability = "semantic_tokens"
        module = "aware_demo_runtime.ontology_binding"
        callable = "semantic_tokens"
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    package = spec.packages[0]
    assert package.semantic_contract is not None
    assert (
        package.semantic_contract.role,
        package.semantic_contract.contract,
        package.semantic_contract.provider_key,
        package.semantic_contract.module,
    ) == (
        "demo.ontology",
        "aware.ontology",
        "aware_demo",
        "aware_demo_runtime.semantic_contract",
    )
    assert tuple(
        (binding.capability, binding.module, binding.callable)
        for binding in package.semantic_contract.bindings
    ) == (
        ("diagnostics", "aware_demo_runtime.ontology_binding", "diagnostics"),
        ("semantic_tokens", "aware_demo_runtime.ontology_binding", "semantic_tokens"),
    )
    assert package.semantic_bindings == ()


def test_load_aware_module_spec_parses_package_semantic_provider_contract(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"

        [[packages]]
        id = "runtime"
        kind = "runtime"
        manifest = "runtime/pyproject.toml"

        [packages.semantic_contract]
        role = "aware_demo.provider"
        contract = "aware.semantic_provider"
        provider_key = "aware_demo"
        module = "aware_demo_runtime.semantic_contract"
        owns_manifest_kinds = ["aware_demo_toml", "aware_demo_toml"]
        capabilities = ["diagnostics", "semantic_tokens", "materialize"]
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    package = spec.packages[0]
    assert package.semantic_contract is not None
    assert (
        package.semantic_contract.role,
        package.semantic_contract.contract,
        package.semantic_contract.provider_key,
        package.semantic_contract.module,
        package.semantic_contract.owns_manifest_kinds,
        package.semantic_contract.capabilities,
    ) == (
        "aware_demo.provider",
        "aware.semantic_provider",
        "aware_demo",
        "aware_demo_runtime.semantic_contract",
        ("aware_demo_toml",),
        ("diagnostics", "semantic_tokens", "materialize"),
    )


def test_load_aware_module_spec_rejects_package_semantic_contract_without_registered_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[packages]]
        id = "home_ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"

        [packages.semantic_contract]
        role = "demo.ontology"
        contract = "aware.ontology"
        provider_key = "aware_demo"
        module = "aware_demo_runtime.semantic_contract"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="must reference a registered code.module_plugin",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_mixed_package_semantic_contract_rails(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        semantic_contract_module = "aware_demo_runtime.semantic_contract"

        [[packages]]
        id = "home_ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"

        [packages.semantic_contract]
        role = "demo.ontology"
        contract = "aware.ontology"
        provider_key = "aware_demo"
        module = "aware_demo_runtime.semantic_contract"

        [[packages.semantic_bindings]]
        role = "demo.ontology"
        contract = "aware.ontology"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="cannot mix semantic_contract with legacy semantic_bindings",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_duplicate_package_semantic_binding_role(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[packages]]
        id = "home_ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"

        [[packages.semantic_bindings]]
        role = "demo.ontology"
        contract = "aware.ontology"

        [[packages.semantic_bindings]]
        role = "demo.ontology"
        contract = "aware.other"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="duplicate semantic binding role 'demo.ontology'",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_mixed_package_shapes(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        id = "home_ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="cannot mix legacy aware_toml_path with id/kind/manifest",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_accepts_legacy_module_wrapper_mode(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        module = "aware_demo_runtime.module_plugin"
        semantic_contract_module = "aware_demo_runtime.semantic_contract"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    assert len(spec.plugins) == 1
    plugin = spec.plugins[0]
    assert plugin.kind == "code.module_plugin"
    assert plugin.module == "aware_demo_runtime.module_plugin"
    assert plugin.provider_key is None
    assert plugin.capability_contract_module is None
    assert plugin.capability_execution_module is None
    assert plugin.semantic_contract_module == "aware_demo_runtime.semantic_contract"
    assert plugin.capability_policy == ()


def test_load_aware_module_spec_accepts_semantic_contract_only_provider_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        semantic_contract_module = "aware_demo_runtime.semantic_contract"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    spec = load_aware_module_spec(toml_path=toml_path)

    assert len(spec.plugins) == 1
    plugin = spec.plugins[0]
    assert plugin.provider_key == "aware_demo"
    assert plugin.semantic_contract_module == "aware_demo_runtime.semantic_contract"
    assert plugin.capability_contract_module is None
    assert plugin.capability_execution_module is None
    assert plugin.code_package_materialization_contract_module is None


def test_load_aware_module_spec_requires_module_or_provider_key_for_code_module_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\] must set either module or provider_key when kind='code.module_plugin'",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_name_for_code_module_plugin(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        name = "AWARE_MODULE_PLUGIN"
        module = "aware_demo_runtime.module_plugin"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\]\\.name is not allowed when kind='code.module_plugin'",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_invalid_python_module_for_code_module_plugin(tmp_path) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        module = "aware-demo-runtime.module_plugin"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\]\\.module must match",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_mixed_module_and_provider_key_for_code_module_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        module = "aware_demo_runtime.module_plugin"
        provider_key = "aware_demo"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="cannot set both module and provider_key",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_invalid_capability_contract_module_for_code_module_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        capability_contract_module = "aware-demo-runtime.language_service_capability_metadata"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\]\\.capability_contract_module must match",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_invalid_capability_execution_module_for_code_module_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        capability_execution_module = "aware-demo-runtime.language_service_capabilities"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\]\\.capability_execution_module must match",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_invalid_semantic_contract_module_for_code_module_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        semantic_contract_module = "aware-demo-runtime.semantic_contract"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\]\\.semantic_contract_module must match",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_invalid_provider_key_for_code_module_plugin(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware-demo"
        capability_contract_module = "aware_demo_runtime.language_service_capability_metadata"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="plugins\\[0\\]\\.provider_key must match",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_workspace_policy_in_legacy_module_wrapper_mode(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        module = "aware_demo_runtime.module_plugin"

        [[plugins.capability_policy]]
        capability = "semantic_tokens"
        workspace_activation = "always"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="cannot declare capability_policy in legacy module wrapper mode",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_invalid_workspace_activation_in_capability_policy(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        capability_contract_module = "aware_demo_runtime.language_service_capability_metadata"

        [[plugins.capability_policy]]
        capability = "semantic_tokens"
        workspace_activation = "global"

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="workspace_activation must be one of: always, owner",
    ):
        load_aware_module_spec(toml_path=toml_path)


def test_load_aware_module_spec_rejects_duplicate_capability_policy_entries(
    tmp_path,
) -> None:
    toml_path = _write_module_toml(
        tmp_path=tmp_path,
        body="""
        aware = 1

        [[plugins]]
        kind = "code.module_plugin"
        provider_key = "aware_demo"
        capability_contract_module = "aware_demo_runtime.language_service_capability_metadata"

        [[plugins.capability_policy]]
        capability = "semantic_tokens"

        [[plugins.capability_policy]]
        capability = "semantic_tokens"
        workspace_fallback = true

        [[packages]]
        aware_toml_path = "structure/ontology/aware.toml"
        """,
    )

    with pytest.raises(
        AwareModuleTomlError,
        match="declares duplicate capability 'semantic_tokens'",
    ):
        load_aware_module_spec(toml_path=toml_path)
