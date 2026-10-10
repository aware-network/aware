"""Graph checks over portable evidence only; no original issuer qualification."""
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime.qualified_scope import (
    qualified_package_index,
    validate_selected_scope_graph,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    CodeRetainedDependencyScopeClosure,
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeEntry,
    DependencyScopeRestriction,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
    CodeRetainedScopePackage,
    CodeRetainedScopeProjection,
)


def fixture():
    def body(path):
        return CodeRetainedScopeBody(path, path, ContentDigest.of_bytes(b"x"), b"x")
    projection = CodeRetainedScopeProjection("repo", ContentDigest.of_bytes(b"obs"), body("aware.workspace.toml"),
        (CodeRetainedScopeModule("same", body("m/aware.module.toml")),),
        (CodeRetainedScopePackage("same", "package", "code", "m/aware.module.toml", "m/p", "aware.toml",
                                 ContentDigest.of_bytes(b"source"), body("m/p/aware.toml")),))
    scopes = tuple(DependencyScopeEntry(k, k, projection) for k in ("a", "b"))
    tag = lambda v: DependencyScopeRestriction("present", v)
    edge = DependencyScopeEdge("a", "b", DependencyScopeDeclaration("aware.workspace.toml", projection.workspace_manifest.content_digest, 0, 0),
        "b", "workspace", "workspace://b", tag("local"), tag("workspace-revision:local"),
        "workspace://b#default", tag("default"), tag(("provider",)))
    return CodeRetainedDependencyScopeClosure("a", scopes, (edge,))


def test_qualified_index_preserves_same_names_and_identical_bytes():
    index = qualified_package_index(fixture())
    assert set(index) == {("a", "same", "package"), ("b", "same", "package")}


@pytest.mark.parametrize("field", ["channel", "revision", "profile_key", "semantic_contract_provider_keys"])
@pytest.mark.parametrize("state", ["absent", "unavailable"])
def test_missing_restriction_never_grants(field, state):
    c = fixture()
    edge = replace(c.edges[0], **{field: DependencyScopeRestriction(state)})
    with pytest.raises(ContractViolation): validate_selected_scope_graph(replace(c, edges=(edge,)))


@pytest.mark.parametrize("field,value", [
    ("dependency_kind", "external"), ("dependency_source", "workspace://foreign"),
    ("profile_package_ref", "workspace://b#other"),
    ("channel", DependencyScopeRestriction("present", "remote")),
    ("revision", DependencyScopeRestriction("present", "pinned")),
    ("semantic_contract_provider_keys", DependencyScopeRestriction("present", ())),
])
def test_unsupported_or_substituted_selector_refuses(field, value):
    c = fixture()
    with pytest.raises(ContractViolation):
        validate_selected_scope_graph(replace(c, edges=(replace(c.edges[0], **{field: value}),)))


def test_cycles_unreachable_and_ambiguous_handles_refuse():
    c = fixture()
    reverse = replace(c.edges[0], declaring_scope_key="b", target_scope_key="a", dependency_id="a",
                      dependency_source="workspace://a", profile_package_ref="workspace://a#default")
    with pytest.raises(ContractViolation, match="cycle"):
        validate_selected_scope_graph(replace(c, edges=c.edges + (reverse,)))
    with pytest.raises(ContractViolation, match="unreachable"):
        validate_selected_scope_graph(replace(c, edges=()))
    with pytest.raises(ContractViolation, match="ambiguous"):
        validate_selected_scope_graph(replace(c, scopes=(c.scopes[0], replace(c.scopes[1], workspace_handle="a"))))
