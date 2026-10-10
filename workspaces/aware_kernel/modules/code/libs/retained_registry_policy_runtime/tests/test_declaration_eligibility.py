"""V3 declaration eligibility is complete but never source authority."""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
    calculate_declaration_eligibility,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDeclarationPackage,
    CodeRetainedDeclarationScopeEntry,
    CodeRetainedDeclarationScopeProjection,
    CodeRetainedDependencyScopeClosureV3,
    CodeRetainedLocalProfilePublication,
)

from test_calculation import _body
from test_qualified_calculation import change_consumer, fixture as old_fixture


def fixture():
    old, _ = old_fixture()

    def retained(body):
        # The v2 fixture reused a path-based ref after mutating module bytes.
        # V3 correctly requires each ref to identify one exact retained body.
        return replace(body, body_ref="body:" + body.content_digest.value)

    scopes = []
    for scope in old.scopes:
        projection = scope.projection
        packages = tuple(
            CodeRetainedDeclarationPackage(
                package.module_id,
                package.package_id,
                package.package_kind,
                package.module_manifest_path,
                package.package_root,
                package.manifest_relative_path,
                retained(package.manifest),
            )
            for package in projection.packages
        )
        scopes.append(
            CodeRetainedDeclarationScopeEntry(
                scope.scope_key,
                scope.workspace_handle,
                CodeRetainedDeclarationScopeProjection(
                    "repo",
                    projection.observation_digest,
                    retained(projection.workspace_manifest),
                    tuple(
                        replace(module, manifest=retained(module.manifest))
                        for module in projection.modules
                    ),
                    packages,
                ),
            )
        )
    associations = tuple(
        replace(association, manifest=retained(association.manifest))
        for association in old.profile_associations
    )
    profiles = tuple(
        CodeRetainedLocalProfilePublication(
            edge.target_scope_key,
            edge.profile_key.value,
            association.manifest,
        )
        for edge, association in zip(
            old.edges, associations, strict=True
        )
    )
    return CodeRetainedDependencyScopeClosureV3(
        old.consumer_scope_key,
        "repo",
        _body("aware.repo.toml", b"repository"),
        tuple(scopes),
        old.edges,
        profiles,
        associations,
    )


def test_complete_v3_eligibility_has_no_source_grants():
    closure = fixture()
    result = calculate_declaration_eligibility(closure)
    assert result.closure_digest == closure.closure_digest
    assert len(result.packages) == 2
    assert {row.namespace for row in result.packages} == {
        "home", "consumer_home"
    }
    assert len({row.registration_declaration_digest for row in result.packages}) == 1
    assert all(not hasattr(row, "source_identity_digest") for row in result.packages)
    assert calculate_declaration_eligibility(closure) == result


def test_v3_eligibility_rejects_conflicting_assignments():
    closure = fixture()
    consumer = closure.scopes[0]
    module = consumer.projection.modules[0]
    raw = module.manifest.body.replace(
        b'value="consumer_home"', b'value="home"'
    )
    raw = raw.replace(b'value=["consumer_home"]', b'value=["home"]')
    assert raw != module.manifest.body
    module = replace(
        module,
        manifest=replace(
            module.manifest,
            body=raw,
            content_digest=ContentDigest.of_bytes(raw),
        ),
    )
    consumer = replace(
        consumer,
        projection=replace(consumer.projection, modules=(module,)),
    )
    with pytest.raises(ContractViolation, match="conflicting declaration assignment"):
        calculate_declaration_eligibility(
            replace(closure, scopes=(consumer, closure.scopes[1]))
        )


def test_v3_eligibility_keeps_imported_profile_and_direct_edge_checks():
    closure = fixture()
    with pytest.raises(ContractViolation):
        calculate_declaration_eligibility(replace(closure, edges=()))
    profile = closure.local_profiles[0]
    changed_body = profile.manifest.body.replace(
        b'key = "custom.profile"', b'key = "other.profile"'
    )
    changed = _body(profile.manifest.relative_path, changed_body)
    with pytest.raises(ContractViolation):
        calculate_declaration_eligibility(
            replace(
                closure,
                local_profiles=(replace(profile, manifest=changed),),
                profile_associations=(
                    replace(closure.profile_associations[0], manifest=changed),
                ),
            )
        )


def test_v2_closure_is_not_v3_eligibility():
    old, _ = old_fixture()
    with pytest.raises(TypeError, match="declaration-only"):
        calculate_declaration_eligibility(old)
