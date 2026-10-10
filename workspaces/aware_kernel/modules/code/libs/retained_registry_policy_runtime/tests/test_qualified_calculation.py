"""Qualified source-policy composition without host or live provider authority."""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_retained_registry_policy_runtime.qualified_calculation import (
    calculate_qualified_registry_policy as calculate,
    propose_qualified_declared_provider_candidates,
    propose_qualified_execution_providers,
    validate_qualified_execution_provider_catalog,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    DependencyScopeEntry,
    DependencyScopeRestriction,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeModule,
    CodeRetainedScopePackage,
)
from test_calculation import _catalog
from test_calculation import _body, _digest
from test_calculation import fixture as local_fixture
from test_profile_membership import fixture as closure_fixture


def fixture():
    closure = closure_fixture()
    consumer = closure.scopes[0]
    model = consumer.projection.modules[0]
    raw = model.manifest.body.replace(b"aware = 2", b"aware = 3", 1)
    raw = raw.replace(
        b'value={module_id="demo", package_id="provider", registration_key="demo"}',
        b'value={scope={kind="dependency", workspace_handle="target"}, module_id="demo", package_id="provider", registration_key="demo"}',
    )
    raw = raw.replace(b'value="home"', b'value="consumer_home"').replace(
        b'value=["home"]', b'value=["consumer_home"]'
    )
    module = replace(
        model,
        manifest=replace(
            model.manifest, body=raw, content_digest=ContentDigest.of_bytes(raw)
        ),
    )
    packages = tuple(
        replace(
            p,
            source_identity_digest=ContentDigest.of_bytes(
                b"consumer:" + p.package_id.encode()
            ),
        )
        for p in consumer.projection.packages
    )
    consumer = replace(
        consumer,
        projection=replace(consumer.projection, modules=(module,), packages=packages),
    )
    return replace(closure, scopes=(consumer, closure.scopes[1])), local_fixture()[1]


def change_consumer(closure, before, after):
    c = closure.scopes[0]
    m = c.projection.modules[0]
    raw = m.manifest.body.replace(before, after)
    assert raw != m.manifest.body
    m = replace(
        m,
        manifest=replace(
            m.manifest, body=raw, content_digest=ContentDigest.of_bytes(raw)
        ),
    )
    return replace(
        closure,
        scopes=(
            replace(c, projection=replace(c.projection, modules=(m,))),
            closure.scopes[1],
        ),
    )


def test_imported_registration_and_local_target_on_same_grant_rail():
    closure, catalog = fixture()
    result = calculate(closure, catalog)
    assert result.declaration_scope_digest == closure.closure_digest
    assert len(result.grants) == 2
    assert len({g.registration_declaration_digest for g in result.grants}) == 1
    assert {g.namespace for g in result.grants} == {"home", "consumer_home"}
    assert calculate(closure, catalog) == result


def test_selected_execution_provider_is_derived_per_original_package():
    closure, catalog = fixture()
    selected = tuple(
        package.source_identity_digest
        for scope in closure.scopes
        for package in scope.projection.packages
        if package.package_id == "home"
    )
    result = propose_qualified_execution_providers(closure, selected)
    assert tuple(item.source_identity_digest for item in result) == selected
    assert tuple(item.provider_key for item in result) == ("demo", "demo")
    assert all(
        item.registration_declaration_digest == result[0].registration_declaration_digest
        for item in result
    )
    validate_qualified_execution_provider_catalog(closure, catalog, result)


def test_declared_provider_candidates_include_all_occurrences_without_catalog():
    closure, _ = fixture()
    candidates = propose_qualified_declared_provider_candidates(closure)
    assert tuple(item.provider_key for item in candidates) == ("demo",)
    assert len(candidates[0].source_identity_digests) == 2
    assert len(set(candidates[0].source_identity_digests)) == 2
    assert len(set(candidates[0].registration_declaration_digests)) == 1
    # This input step remains valid when a source-only relationship target has
    # no executable catalog entry or locally installed factory.
    assert propose_qualified_declared_provider_candidates(closure) == candidates


def test_declared_provider_candidates_reject_one_key_with_two_declarations():
    closure, _ = fixture()
    closure = change_consumer(
        closure,
        b'scope={kind="dependency", workspace_handle="target"}',
        b'scope={kind="local"}',
    )
    consumer, target = closure.scopes
    module = target.projection.modules[0]
    body = module.manifest.body.replace(
        b'supported_languages = ["aware"]',
        b'supported_languages = ["python"]',
        1,
    )
    assert body != module.manifest.body
    module = replace(
        module,
        manifest=replace(
            module.manifest,
            body=body,
            content_digest=ContentDigest.of_bytes(body),
        ),
    )
    target = replace(
        target,
        projection=replace(target.projection, modules=(module,)),
    )
    with pytest.raises(ContractViolation, match="incompatible registration"):
        propose_qualified_declared_provider_candidates(
            replace(closure, scopes=(consumer, target))
        )


def test_declared_provider_candidates_cover_two_unrelated_owner_keys():
    scope, _ = local_fixture()
    original = scope.modules[0]
    second_body = original.manifest.body.replace(b"demo", b"other")
    second_body = second_body.replace(b'value="home"', b'value="other_home"')
    second_body = second_body.replace(b'value=["home"]', b'value=["other_home"]')
    second_module = CodeRetainedScopeModule(
        "other", _body("other/aware.module.toml", second_body)
    )
    second_packages = tuple(
        CodeRetainedScopePackage(
            "other",
            package.package_id,
            package.package_kind,
            second_module.manifest.relative_path,
            f"other/{package.package_id}",
            package.manifest_relative_path.replace("demo", "other"),
            _digest(f"other:{package.package_id}"),
            _body(
                f"other/{package.package_id}/"
                f"{package.manifest_relative_path.replace('demo', 'other')}",
                package.manifest.body,
            ),
        )
        for package in scope.packages
    )
    projection = replace(
        scope,
        modules=(original, second_module),
        packages=(*scope.packages, *second_packages),
    )
    closure = CodeRetainedDependencyScopeClosureV2(
        "consumer", (DependencyScopeEntry("consumer", "consumer", projection),), (), ()
    )
    candidates = propose_qualified_declared_provider_candidates(closure)
    assert tuple(item.provider_key for item in candidates) == ("demo", "other")
    assert all(len(item.source_identity_digests) == 1 for item in candidates)


def test_duplicate_qualified_source_occurrence_refuses_pool_proposal():
    closure, _ = fixture()
    consumer, target = closure.scopes
    duplicate = replace(
        consumer.projection.packages[0],
        source_identity_digest=target.projection.packages[0].source_identity_digest,
    )
    consumer = replace(
        consumer,
        projection=replace(
            consumer.projection,
            packages=(duplicate, *consumer.projection.packages[1:]),
        ),
    )
    with pytest.raises(ContractViolation, match="policy grants.*unique"):
        propose_qualified_declared_provider_candidates(
            replace(closure, scopes=(consumer, target))
        )


def test_execution_proposal_refuses_missing_duplicate_and_unexecutable_selection():
    closure, catalog = fixture()
    selected = closure.scopes[0].projection.packages[0].source_identity_digest
    with pytest.raises(ContractViolation, match="duplicate"):
        propose_qualified_execution_providers(closure, (selected, selected))
    with pytest.raises(ContractViolation, match="unique selected"):
        propose_qualified_execution_providers(closure, (ContentDigest.of_bytes(b"foreign"),))
    with pytest.raises(ContractViolation, match="catalog"):
        validate_qualified_execution_provider_catalog(
            closure,
            _catalog(),
            propose_qualified_execution_providers(closure, (selected,)),
        )


def test_execution_proposal_is_not_a_substitutable_catalog_admission():
    closure, catalog = fixture()
    selected = closure.scopes[0].projection.packages[0].source_identity_digest
    proposal = propose_qualified_execution_providers(closure, (selected,))
    with pytest.raises(ContractViolation, match="proposal changed"):
        validate_qualified_execution_provider_catalog(
            closure, catalog, (replace(proposal[0], provider_key="foreign"),)
        )


def test_local_v2_grants_preserved_in_edge_free_v2_closure():
    scope, catalog = local_fixture()
    old = calculate_registry_policy(scope, catalog)
    entry = closure_fixture().scopes[0]
    closure = CodeRetainedDependencyScopeClosureV2(
        entry.scope_key, (replace(entry, projection=scope),), (), ()
    )
    result = calculate(closure, catalog)
    assert result.grants == old.grants
    assert result.declaration_scope_digest != old.declaration_scope_digest


@pytest.mark.parametrize(
    "before,after",
    [
        (b'workspace_handle="target"', b'workspace_handle="missing"'),
        (b'registration_key="demo"', b'registration_key="missing"'),
        (b'package_id="provider"', b'package_id="missing"'),
    ],
)
def test_qualified_registration_substitution_refuses(before, after):
    closure, catalog = fixture()
    with pytest.raises(ContractViolation):
        calculate(change_consumer(closure, before, after), catalog)


def test_profile_exclusion_refuses_registration():
    closure, catalog = fixture()
    edge = replace(
        closure.edges[0],
        semantic_contract_provider_keys=DependencyScopeRestriction(
            "present", ("not_selected",)
        ),
    )
    with pytest.raises(ContractViolation):
        calculate(replace(closure, edges=(edge,)), catalog)


def test_namespace_conflict_preserves_existing_rejection():
    closure, catalog = fixture()
    closure = change_consumer(closure, b"consumer_home", b"home")
    with pytest.raises(ContractViolation, match="conflicting"):
        calculate(closure, catalog)
    with pytest.raises(ContractViolation, match="conflicting"):
        propose_qualified_declared_provider_candidates(closure)


def test_source_only_targets_need_no_executable_result_catalog():
    closure, _ = fixture()
    assert len(calculate(closure, _catalog()).grants) == 2


def test_qualified_direct_dependency_retains_target_membership():
    closure, catalog = fixture()
    replacement = b'dependency_targets = {state="present", value=[{dependency_kind="module", dependency_ref="target_home", targets=[{scope={kind="dependency",workspace_handle="target"},module_id="demo",package_id="home"}],constraints=[]}]} '
    closure = change_consumer(
        closure, b'dependency_targets = {state="present", value=[]}', replacement
    )
    assert len(calculate(closure, catalog).grants) == 2
    closure = change_consumer(closure, b'package_id="home"', b'package_id="missing"')
    with pytest.raises(ContractViolation):
        calculate(closure, catalog)


def test_transitive_reachability_does_not_authorize_registration():
    value, catalog = fixture()
    edge = value.edges[0]
    a = value.profile_associations[0]
    middle = replace(value.scopes[1], scope_key="middle", workspace_handle="middle")
    first = replace(
        edge,
        target_scope_key="middle",
        dependency_id="middle",
        dependency_source="workspace://middle",
        profile_package_ref="workspace://middle#custom.profile",
    )
    second = replace(edge, declaring_scope_key="middle")
    value = replace(
        value,
        scopes=(value.scopes[0], middle, value.scopes[1]),
        edges=(first, second),
        profile_associations=(
            replace(a, target_scope_key="middle"),
            replace(a, declaring_scope_key="middle"),
        ),
    )
    with pytest.raises(ContractViolation, match="direct declared edge"):
        calculate(value, catalog)


def test_same_named_local_registration_cannot_substitute_imported():
    closure, catalog = fixture()
    expected = calculate(closure, catalog).grants
    changed = change_consumer(
        closure,
        b'semantic_package_kind = "sdk"',
        b'semantic_package_kind = "unselected_local_kind"',
    )
    assert calculate(changed, catalog).grants == expected
