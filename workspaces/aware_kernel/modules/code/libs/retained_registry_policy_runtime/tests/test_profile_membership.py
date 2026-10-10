"""Original authority is deliberately absent from these portable proofs."""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime.profile_membership import (
    resolve_profile_memberships,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeEntry,
    DependencyScopeRestriction,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
    DependencyScopeProfileAssociation,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
)
from test_calculation import fixture as scope_fixture

PROFILE = b"""aware_semantic_contract_profile = 1
[profile]
key = "custom.profile"
package_key = "independent.package"
[[providers]]
module_id = "demo"
provider_key = "demo"
required = false
[[providers]]
module_id = "unavailable"
provider_key = "not_selected"
status = "inactive"
"""


def fixture(profile=PROFILE):
    scope, _ = scope_fixture()
    scopes = (
        DependencyScopeEntry("consumer", "consumer", scope),
        DependencyScopeEntry("target", "target", scope),
    )
    tag = lambda v: DependencyScopeRestriction("present", v)
    edge = DependencyScopeEdge(
        "consumer",
        "target",
        DependencyScopeDeclaration(
            scope.workspace_manifest.relative_path,
            scope.workspace_manifest.content_digest,
            0,
            0,
        ),
        "target",
        "workspace",
        "workspace://target",
        tag("local"),
        tag("workspace-revision:local"),
        "workspace://target#custom.profile",
        tag("custom.profile"),
        tag(("demo",)),
    )
    body = CodeRetainedScopeBody(
        "semantic_contract/profiles/custom.profile/aware.semantic_contract_profile.toml",
        "profile",
        ContentDigest.of_bytes(profile),
        profile,
    )
    association = DependencyScopeProfileAssociation(
        "consumer", edge.declaration, "target", body
    )
    return CodeRetainedDependencyScopeClosureV2(
        "consumer", scopes, (edge,), (association,)
    )


def test_arbitrary_key_and_complete_meaning_without_result_catalog():
    closure = fixture()
    result = resolve_profile_memberships(closure)
    assert len(result) == 1 and len(result[0].members) == 1
    assert result[0].closure_digest == closure.closure_digest
    assert result[0].meaning.profile.package_key == "independent.package"
    assert len(result[0].meaning.providers) == 2
    assert result[0].members[0].package.package_id == "provider"
    assert result[0].members[0].member.required is False
    assert resolve_profile_memberships(closure) == result


@pytest.mark.parametrize(
    "before,after",
    [
        (b"= 1", b"= true"),
        (b'key = "custom.profile"', b'key = "other.profile"'),
        (
            b'package_key = "independent.package"',
            b'package_key = "independent.package"\nstatus="inactive"',
        ),
        (b'module_id = "demo"', b'module_id = "foreign"'),
        (b'provider_key = "demo"', b'provider_key = "foreign"'),
        (b"required = false", b'required = false\nstatus="inactive"'),
    ],
)
def test_missing_inactive_or_substituted_profile_refuses(before, after):
    with pytest.raises(ContractViolation):
        resolve_profile_memberships(fixture(PROFILE.replace(before, after, 1)))


def test_requested_inactive_optional_member_cannot_satisfy():
    value = fixture()
    edge = replace(
        value.edges[0],
        semantic_contract_provider_keys=DependencyScopeRestriction(
            "present", ("not_selected",)
        ),
    )
    with pytest.raises(ContractViolation):
        resolve_profile_memberships(replace(value, edges=(edge,)))


def test_comment_change_binds_new_source_digest():
    a = resolve_profile_memberships(fixture())[0]
    b = resolve_profile_memberships(fixture(b"# comment\n" + PROFILE))[0]
    assert a.meaning == b.meaning and a.members == b.members
    assert a.closure_digest != b.closure_digest


def test_separate_occurrences_are_not_merged():
    value = fixture()
    edge = value.edges[0]
    a = value.profile_associations[0]
    d = replace(edge.declaration, profile_package_index=1)
    result = resolve_profile_memberships(
        replace(
            value,
            edges=(edge, replace(edge, declaration=d)),
            profile_associations=(a, replace(a, declaration=d)),
        )
    )
    assert len(result) == 2 and result[0].edge != result[1].edge


def test_noncanonical_or_incomplete_target_packages_refuse():
    value = fixture()
    scope = value.scopes[1]
    projected = replace(scope.projection, packages=scope.projection.packages[:1])
    with pytest.raises(ContractViolation):
        resolve_profile_memberships(
            replace(
                value, scopes=(value.scopes[0], replace(scope, projection=projected))
            )
        )


def test_v1_module_is_not_promoted():
    value = fixture()
    scope = value.scopes[1]
    m = scope.projection.modules[0]
    raw = b'aware=1\n[[packages]]\nid="home"\nkind="sdk"\nmanifest="home/aware.demo.toml"\n'
    module = replace(
        m,
        manifest=replace(
            m.manifest, body=raw, content_digest=ContentDigest.of_bytes(raw)
        ),
    )
    projected = replace(scope.projection, modules=(module,))
    with pytest.raises(ContractViolation):
        resolve_profile_memberships(
            replace(
                value, scopes=(value.scopes[0], replace(scope, projection=projected))
            )
        )
