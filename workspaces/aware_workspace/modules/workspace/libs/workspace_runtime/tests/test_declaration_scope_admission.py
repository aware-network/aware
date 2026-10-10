"""Original declaration and selected-source Code consumer conformance."""

import os
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.contracts import ContentDigest
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
    CodeRetainedDependencyScopeClosureV3,
    CodeSelectedPackageSourceBinding,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    decode_retained_declaration_scope,
    decode_selected_package_source_binding,
    encode_retained_declaration_scope,
    encode_selected_package_source_binding,
)
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspaceDeclarationScope,
    WorkspaceDeclarationScopeRuntime,
    WorkspaceSelectedPackageSource,
)
from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeUnavailable
from aware_workspace_runtime.source_observation import WorkspaceSourceObservationRuntime
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from test_source_exclusion import parent
from test_source_observation import runtime


@asynccontextmanager
async def fixture(tmp_path):
    async with runtime(tmp_path) as (borrowed, session, store, package):
        root = package.parent
        (root / "aware.repo.toml").write_text(
            'aware_repo=1\n[repo]\nhandle="demo"\nworkspaces_dir="workspaces"\n'
            '[[workspaces]]\nhandle="Kernel"\npath="kernel"\n'
            '[[workspaces]]\nhandle="Network"\npath="network"\n'
        )
        for handle in ("Kernel", "Network"):
            workspace = root / "workspaces" / handle.lower()
            module = workspace / "modules/main"
            owner = module / "package"
            owner.mkdir(parents=True)
            (owner / "aware.example.toml").write_bytes(handle.encode())
            (owner / "body.bin").write_bytes(handle.encode() + b" body")
            module_body = (
                'aware=1\n[module]\n[[packages]]\nid="example"\nkind="example"\n'
                'manifest="package/aware.example.toml"\nvisibility="module"\n'
            )
            if handle == "Network":
                module_body += (
                    '[[packages]]\nid="nested"\nkind="example"\n'
                    'manifest="package/child/aware.example.toml"\n'
                    'visibility="module"\n'
                )
                child = owner / "child"
                child.mkdir()
                (child / "aware.example.toml").write_bytes(b"nested")
            (module / "aware.module.toml").write_text(module_body)
            workspace_body = (
                f'aware=2\n[workspace]\nhandle="{handle}"\n'
                '[[workspace.modules]]\nid="main"\npath="modules/main"\n'
            )
            if handle == "Kernel":
                workspace_body += (
                    '[[workspace.code_semantic_contract_profile_packages]]\n'
                    'profile_key="kernel.default"\n'
                    'profile_package_ref="workspace://Kernel#kernel.default"\n'
                )
                profile = workspace / "semantic_contract/profiles/kernel.default"
                profile.mkdir(parents=True)
                (profile / "aware.semantic_contract_profile.toml").write_bytes(b"profile")
            else:
                workspace_body += (
                    '[[workspace.dependencies]]\nid="Kernel"\nkind="workspace"\n'
                    'source="workspace://Kernel"\nchannel="local"\n'
                    'revision="workspace-revision:local"\n'
                    '[[workspace.dependencies.code_semantic_contract_profile_packages]]\n'
                    'profile_package_ref="workspace://Kernel#kernel.default"\n'
                    'profile_key="kernel.default"\n'
                    'semantic_contract_provider_keys=["aware_code"]\n'
                )
            (workspace / "aware.workspace.toml").write_text(workspace_body)
        parent_runtime, _, _, exclusion = parent()
        observer = WorkspaceSourceObservationRuntime(
            session=session, store=store, exclusion=exclusion
        )
        issuer = WorkspaceDeclarationScopeRuntime(observation_runtime=observer)
        observation = observer.observe_declarations()
        expectation = CodeDeclarationScopeExpectation(
            store.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
        )
        try:
            yield root, parent_runtime, observer, issuer, observation, expectation
        finally:
            issuer.close()
            observer.close()
            parent_runtime.close()


async def test_real_nested_profile_import_and_selected_source(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, observed, expected):
        handle = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        closure = issuer.read_declaration_scope(handle)
        assert type(closure) is CodeRetainedDependencyScopeClosureV3
        assert decode_retained_declaration_scope(
            encode_retained_declaration_scope(closure)
        ) == closure
        assert len(closure.scopes) == 2 and len(closure.edges) == 1
        assert closure.repository_manifest.relative_path == "aware.repo.toml"
        assert closure.local_profiles[0].manifest.relative_path == (
            "workspaces/kernel/semantic_contract/profiles/kernel.default/"
            "aware.semantic_contract_profile.toml"
        )
        assert closure.profile_associations[0].manifest is closure.local_profiles[0].manifest
        issuer.validate_declaration_scope(
            handle, expectation=expected, closure_digest=closure.closure_digest
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main",
            package_id="example",
        )
        source = issuer.bind_selected_package_source(
            declaration=handle, selected=selected
        )
        value = issuer.read_selected_package_source(source)
        assert type(value) is CodeSelectedPackageSourceBinding
        assert observer.selected_package_evidence(selected).excluded_nested_roots == (
            "child",
        )
        assert decode_selected_package_source_binding(
            encode_selected_package_source_binding(value)
        ) == value
        assert [c.relative_path for c in value.candidates.candidates] == [
            "aware.example.toml", "body.bin"
        ]
        assert value.expectation.closure_digest == closure.closure_digest
        issuer.validate_selected_package_source(
            source,
            expectation=value.expectation,
            binding_digest=value.binding_digest,
        )
        (root / "workspaces/network/modules/main/package/body.bin").write_bytes(b"changed")
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            issuer.validate_selected_package_source(
                source, expectation=value.expectation
            )
        issuer.release_selected_package_source(source)
        issuer.release_declaration_scope(handle)


async def test_wrong_expectation_foreign_handle_and_profile_change_refuse(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, observed, expected):
        handle = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        closure = issuer.read_declaration_scope(handle)
        with pytest.raises(SourceObservationUnavailable, match="expectation"):
            issuer.validate_declaration_scope(
                handle, expectation=replace(expected, operation_identity="other")
            )
        with pytest.raises(SourceObservationUnavailable, match="digest"):
            issuer.validate_declaration_scope(
                handle, expectation=expected,
                closure_digest=ContentDigest.of_bytes(b"substitute"),
            )
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            issuer.read_declaration_scope(object.__new__(WorkspaceDeclarationScope))
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(
            declaration=handle, selected=selected
        )
        binding = issuer.read_selected_package_source(source)
        with pytest.raises(SourceObservationUnavailable, match="expectation"):
            issuer.validate_selected_package_source(
                source,
                expectation=replace(binding.expectation, package_id="other"),
            )
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            issuer.read_selected_package_source(object.__new__(WorkspaceSelectedPackageSource))
        profile = (
            root / "workspaces/kernel/semantic_contract/profiles/kernel.default/"
            "aware.semantic_contract_profile.toml"
        )
        profile.write_bytes(b"changed profile")
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_declaration_scope(
                handle, expectation=expected, closure_digest=closure.closure_digest
            )
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_selected_package_source(
                source, expectation=binding.expectation
            )


async def test_original_reader_substitution_and_parent_close_revoke(tmp_path, monkeypatch):
    async with fixture(tmp_path) as (_, parent_runtime, observer, issuer, observed, expected):
        handle = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        with monkeypatch.context() as patch:
            patch.setattr(observer, "read_declarations", lambda _: ())
            with pytest.raises(SourceObservationUnavailable, match="reader_origin"):
                issuer.read_declaration_scope(handle)
        delattr(observer, "read_declarations")
        issuer.read_declaration_scope(handle)
        parent_runtime.close()
        with pytest.raises(WorkspaceCommandLifetimeUnavailable):
            issuer.read_declaration_scope(handle)
        issuer.release_declaration_scope(handle)


async def test_foreign_issuer_and_context_cannot_rebind_source(tmp_path):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        with pytest.raises(SourceObservationUnavailable, match="context"):
            issuer.capture_declaration_scope(
                observation=observed,
                consumer_scope_key="workspaces/network/aware.workspace.toml",
                expectation=replace(expected, process_id=os.getpid() + 1),
            )
        handle = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        other = WorkspaceDeclarationScopeRuntime(observation_runtime=observer)
        try:
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                other.read_declaration_scope(handle)
        finally:
            other.close()


async def test_repository_membership_handle_mismatch_refuses_complete_scope(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expected):
        manifest = root / "aware.repo.toml"
        manifest.write_text(manifest.read_text().replace(
            'handle="Network"\npath="network"',
            'handle="network_alias"\npath="network"',
        ))
        observation = observer.observe_declarations()
        with pytest.raises(SourceObservationUnavailable, match="handle_mismatch"):
            issuer.capture_declaration_scope(
                observation=observation,
                consumer_scope_key="workspaces/network/aware.workspace.toml",
                expectation=expected,
            )


async def test_original_handles_check_under_one_existing_parent_guard(tmp_path):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        closure = issuer.read_declaration_scope(declaration)
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(
            declaration=declaration, selected=selected,
        )
        binding = issuer.read_selected_package_source(source)
        issuer.validate_declaration_scope(
            declaration, expectation=expected, closure_digest=closure.closure_digest,
        )
        issuer.validate_selected_package_source(
            source, expectation=binding.expectation,
            binding_digest=binding.binding_digest,
        )
        # A second parent acquisition would reject as nested here.
        with observer._exclusion.mutation() as guard:
            issuer.check_declaration_scope_locked(
                declaration, expectation=expected,
                closure_digest=closure.closure_digest, guard=guard,
            )
            issuer.check_selected_package_source_locked(
                source, expectation=binding.expectation,
                binding_digest=binding.binding_digest, guard=guard,
            )
            with pytest.raises(SourceObservationUnavailable, match="expectation"):
                issuer.check_declaration_scope_locked(
                    declaration,
                    expectation=replace(expected, operation_identity="other"),
                    closure_digest=closure.closure_digest, guard=guard,
                )
            with pytest.raises(SourceObservationUnavailable, match="digest"):
                issuer.check_selected_package_source_locked(
                    source, expectation=binding.expectation,
                    binding_digest=ContentDigest.of_bytes(b"wrong"), guard=guard,
                )
            with pytest.raises(SourceObservationUnavailable, match="expectation"):
                issuer.check_selected_package_source_locked(
                    source,
                    expectation=replace(binding.expectation, package_id="other"),
                    binding_digest=binding.binding_digest, guard=guard,
                )


async def test_guarded_checks_reject_foreign_guard_retirement_and_substitution(
    tmp_path, monkeypatch,
):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        closure = issuer.read_declaration_scope(declaration)
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(
            declaration=declaration, selected=selected,
        )
        binding = issuer.read_selected_package_source(source)
        foreign_parent, _, _, foreign_exclusion = parent()
        try:
            with foreign_exclusion.mutation() as foreign_guard:
                with pytest.raises(WorkspaceCommandLifetimeUnavailable, match="guard"):
                    issuer.check_declaration_scope_locked(
                        declaration, expectation=expected,
                        closure_digest=closure.closure_digest, guard=foreign_guard,
                    )
        finally:
            foreign_parent.close()
        with monkeypatch.context() as patch:
            patch.setattr(observer, "read_declarations", lambda _: ())
            with observer._exclusion.mutation() as guard:
                with pytest.raises(SourceObservationUnavailable, match="reader_origin"):
                    issuer.check_declaration_scope_locked(
                        declaration, expectation=expected,
                        closure_digest=closure.closure_digest, guard=guard,
                    )
        delattr(observer, "read_declarations")
        issuer.release_selected_package_source(source)
        with observer._exclusion.mutation() as guard:
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                issuer.check_selected_package_source_locked(
                    source, expectation=binding.expectation,
                    binding_digest=binding.binding_digest, guard=guard,
                )
        issuer.release_declaration_scope(declaration)
        with observer._exclusion.mutation() as guard:
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                issuer.check_declaration_scope_locked(
                    declaration, expectation=expected,
                    closure_digest=closure.closure_digest, guard=guard,
                )


async def test_guarded_selected_check_requires_original_source_record(tmp_path):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(
            declaration=declaration, selected=selected,
        )
        binding = issuer.read_selected_package_source(source)
        observer.release_selected_package(selected)
        with observer._exclusion.mutation() as guard:
            with pytest.raises(SourceObservationUnavailable, match="expired_selected"):
                issuer.check_selected_package_source_locked(
                    source, expectation=binding.expectation,
                    binding_digest=binding.binding_digest, guard=guard,
                )
