"""Declaration-only Code values and consumer signatures confer no authority."""

import json
import typing
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    decode_dependency_scope_closure_v2,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    DependencyScopeProfileAssociation,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
    CodeRetainedDeclarationPackage,
    CodeRetainedDeclarationScopeEntry,
    CodeRetainedDeclarationScopeProjection,
    CodeRetainedDependencyScopeClosureV3,
    CodeRetainedLocalProfilePublication,
    CodeSelectedPackageSourceBinding,
    CodeSelectedPackageSourceExpectation,
    RetainedDeclarationScopeReader,
    RetainedDeclarationScopeValidator,
    SelectedPackageSourceReader,
    SelectedPackageSourceValidator,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    decode_retained_declaration_scope,
    decode_selected_package_source_binding,
    encode_retained_declaration_scope,
    encode_selected_package_source_binding,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    CodeSemanticCandidate,
    CodeSemanticCandidateListing,
)
from test_dependency_scope_closure import fixture as old_closure


def body(path: str, data: bytes = b"retained bytes") -> CodeRetainedScopeBody:
    return CodeRetainedScopeBody(
        path, "body:" + path, ContentDigest.of_bytes(data), data
    )


def fixture() -> CodeRetainedDependencyScopeClosureV3:
    old = old_closure()
    scopes = []
    for original in old.scopes:
        module = CodeRetainedScopeModule(
            "sdk", body("mods/sdk/aware.module.toml", b"module")
        )
        package = CodeRetainedDeclarationPackage(
            "sdk", "sdk-package", "sdk", module.manifest.relative_path,
            "mods/sdk/package", "aware.sdk.toml",
            body("mods/sdk/package/aware.sdk.toml", b"manifest"),
        )
        projection = CodeRetainedDeclarationScopeProjection(
            "repo", original.projection.observation_digest,
            original.projection.workspace_manifest, (module,), (package,),
        )
        scopes.append(
            CodeRetainedDeclarationScopeEntry(
                original.scope_key, original.workspace_handle, projection
            )
        )
    edge = old.edges[0]
    profile = CodeRetainedLocalProfilePublication(
        edge.target_scope_key, "default",
        body(
            "semantic_contract/profiles/default/aware.semantic_contract_profile.toml",
            b"profile",
        ),
    )
    association = DependencyScopeProfileAssociation(
        edge.declaring_scope_key, edge.declaration,
        edge.target_scope_key, profile.manifest,
    )
    return CodeRetainedDependencyScopeClosureV3(
        old.consumer_scope_key, "repo", body("aware.repo.toml", b"repository"),
        tuple(scopes), old.edges, (profile,), (association,),
    )


def nested_profile_fixture() -> CodeRetainedDependencyScopeClosureV3:
    value = fixture()
    target_path = "workspaces/aware_kernel/aware.workspace.toml"
    profile_path = (
        "workspaces/aware_kernel/semantic_contract/profiles/default/"
        "aware.semantic_contract_profile.toml"
    )
    target = replace(
        value.scopes[1],
        scope_key=target_path,
        projection=replace(
            value.scopes[1].projection,
            workspace_manifest=body(target_path, b"nested Workspace"),
        ),
    )
    edge = replace(value.edges[0], target_scope_key=target_path)
    profile_body = body(profile_path, b"nested profile")
    profile = replace(
        value.local_profiles[0],
        owning_scope_key=target_path,
        manifest=profile_body,
    )
    association = replace(
        value.profile_associations[0],
        target_scope_key=target_path,
        manifest=profile_body,
    )
    return replace(
        value,
        scopes=(value.scopes[0], target),
        edges=(edge,),
        local_profiles=(profile,),
        profile_associations=(association,),
    )


def selected(value: CodeRetainedDependencyScopeClosureV3) -> CodeSelectedPackageSourceBinding:
    package = value.scopes[0].projection.packages[0]
    source = ContentDigest.of_bytes(b"selected complete source")
    context = CodeDeclarationScopeExpectation("repo", "parent", 123, "operation", "epoch")
    expectation = CodeSelectedPackageSourceExpectation(
        context, value.closure_digest, value.scopes[0].scope_key,
        package.module_id, package.package_id, package.manifest_relative_path,
        package.manifest.content_digest, source,
    )
    candidates = CodeSemanticCandidateListing(
        source,
        (CodeSemanticCandidate(package.manifest_relative_path, package.manifest.content_digest),),
    )
    return CodeSelectedPackageSourceBinding(expectation, candidates)


def test_v3_roundtrip_retains_repository_and_local_profile() -> None:
    value = fixture()
    decoded = decode_retained_declaration_scope(encode_retained_declaration_scope(value))
    assert decoded == value and decoded is not value
    assert decoded.repository_manifest.body == b"repository"
    assert decoded.local_profiles[0].manifest.body == b"profile"
    assert "source_identity_digest" not in decoded.scopes[0].projection.packages[0].to_wire()
    with pytest.raises(ContractViolation):
        decode_dependency_scope_closure_v2(encode_retained_declaration_scope(value))


def test_nested_workspace_profile_uses_repository_relative_path() -> None:
    value = nested_profile_fixture()
    assert (
        decode_retained_declaration_scope(encode_retained_declaration_scope(value))
        == value
    )
    assert value.local_profiles[0].manifest.relative_path.startswith(
        "workspaces/aware_kernel/semantic_contract/"
    )


def test_nested_workspace_profile_rejects_root_or_foreign_coordinate() -> None:
    value = nested_profile_fixture()
    for path in (
        "semantic_contract/profiles/default/aware.semantic_contract_profile.toml",
        "workspaces/aware_network/semantic_contract/profiles/default/"
        "aware.semantic_contract_profile.toml",
    ):
        substituted = body(path, b"nested profile")
        with pytest.raises(ContractViolation, match="local profile path differs"):
            replace(
                value,
                local_profiles=(replace(value.local_profiles[0], manifest=substituted),),
                profile_associations=(
                    replace(value.profile_associations[0], manifest=substituted),
                ),
            )


def test_nested_workspace_profile_rejects_non_workspace_owner_manifest() -> None:
    value = nested_profile_fixture()
    target = replace(
        value.scopes[1],
        projection=replace(
            value.scopes[1].projection,
            workspace_manifest=body("workspaces/aware_kernel/other.toml"),
        ),
    )
    with pytest.raises(ContractViolation, match="owning Workspace manifest path"):
        replace(value, scopes=(value.scopes[0], target))


def test_repository_and_local_publication_enter_closure_digest() -> None:
    value = fixture()
    changed_repository = replace(value, repository_manifest=body("aware.repo.toml", b"changed"))
    changed_profile = body(
        value.local_profiles[0].manifest.relative_path, b"changed profile"
    )
    changed_local = replace(
        value,
        local_profiles=(replace(value.local_profiles[0], manifest=changed_profile),),
        profile_associations=(replace(value.profile_associations[0], manifest=changed_profile),),
    )
    assert len({value.closure_digest, changed_repository.closure_digest, changed_local.closure_digest}) == 3


def test_unimported_local_profile_still_enters_complete_closure() -> None:
    value = fixture()
    local_only = replace(value, edges=(), profile_associations=())
    assert decode_retained_declaration_scope(encode_retained_declaration_scope(local_only)) == local_only
    assert local_only.local_profiles == value.local_profiles


def test_profile_path_cannot_substitute_package_body_in_same_scope() -> None:
    value = fixture()
    target = value.scopes[1]
    package = target.projection.packages[0]
    local = value.local_profiles[0]
    substituted = replace(
        package,
        package_root="semantic_contract/profiles/default",
        manifest_relative_path="aware.semantic_contract_profile.toml",
        manifest=body(local.manifest.relative_path, b"different package body"),
    )
    target = replace(
        target,
        projection=replace(target.projection, packages=(substituted,)),
    )
    with pytest.raises(ContractViolation):
        replace(value, scopes=(value.scopes[0], target))


@pytest.mark.parametrize("mutation", ["missing", "foreign", "body", "key", "extra"])
def test_import_cannot_publish_or_substitute_target_profile(mutation: str) -> None:
    value = fixture()
    profile = value.local_profiles[0]
    with pytest.raises(ContractViolation):
        if mutation == "missing":
            replace(value, local_profiles=())
        elif mutation == "foreign":
            replace(value, local_profiles=(replace(profile, owning_scope_key=value.consumer_scope_key),))
        elif mutation == "body":
            replace(value, profile_associations=(replace(value.profile_associations[0], manifest=body(profile.manifest.relative_path, b"other")),))
        elif mutation == "key":
            replace(value, local_profiles=(replace(profile, profile_key="different"),))
        else:
            replace(value, local_profiles=value.local_profiles * 2)


def test_selected_binding_requires_real_manifest_candidate_and_source_identity() -> None:
    binding = selected(fixture())
    assert decode_selected_package_source_binding(encode_selected_package_source_binding(binding)) == binding
    assert binding.binding_digest == ContentDigest.of_bytes(encode_selected_package_source_binding(binding))
    with pytest.raises(ContractViolation):
        replace(binding, candidates=replace(binding.candidates, candidates=()))
    with pytest.raises(ContractViolation):
        replace(
            binding,
            candidates=replace(
                binding.candidates,
                source_identity_digest=ContentDigest.of_bytes(b"invented"),
            ),
        )


@pytest.mark.parametrize("mutation", ["extra", "digest", "repository", "local", "whitespace"])
def test_closure_wire_refuses_substitution(mutation: str) -> None:
    raw = encode_retained_declaration_scope(fixture())
    wire = json.loads(raw)
    if mutation == "extra":
        wire["unexpected"] = 1
    elif mutation == "digest":
        wire["closure_digest"] = ContentDigest.of_bytes(b"wrong").value
    elif mutation == "repository":
        wire.pop("repository_manifest")
    elif mutation == "local":
        wire["local_profiles"] = []
    else:
        raw += b"\n"
    if mutation != "whitespace":
        raw = canonical_json_bytes(wire)
    with pytest.raises(ContractViolation):
        decode_retained_declaration_scope(raw)


def test_original_consumer_signatures_are_distinct() -> None:
    assert typing.get_type_hints(RetainedDeclarationScopeReader.read_declaration_scope)["return"] is CodeRetainedDependencyScopeClosureV3
    assert typing.get_type_hints(SelectedPackageSourceReader.read_selected_package_source)["return"] is CodeSelectedPackageSourceBinding
    declaration = typing.get_type_hints(RetainedDeclarationScopeValidator.validate_declaration_scope)
    selected_source = typing.get_type_hints(SelectedPackageSourceValidator.validate_selected_package_source)
    assert declaration["expectation"] is CodeDeclarationScopeExpectation
    assert selected_source["expectation"] is CodeSelectedPackageSourceExpectation
