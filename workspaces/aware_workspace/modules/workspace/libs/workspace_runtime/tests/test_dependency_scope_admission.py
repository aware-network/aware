
from test_repository_delta_retention_client import retained

"""Original retained profile associations; no Code operation or live policy proof."""

import copy
import os
from contextlib import asynccontextmanager

import aware_workspace_runtime.code_scope_adapter as scope_adapter_module
import aware_workspace_runtime.complete_scope_observation as scope_observation
import pytest
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    decode_dependency_scope_closure_v2,
    encode_dependency_scope_closure_v2,
)
from aware_workspace_runtime import (
    FileSystemIndexObservationProvider,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSession,
)
from aware_workspace_runtime.code_scope_adapter import WorkspaceCodeScopeAdapter
from aware_workspace_runtime.command_lifetime import (
    WorkspaceCommandLifetimeRuntime,
    WorkspaceCommandLifetimeUnavailable,
)
from aware_workspace_runtime.complete_scope_observation import (
    WorkspaceCompleteScopeObservationRuntime,
)
from aware_workspace_runtime.composition import (
    LocalCheckoutWorkspaceCompositionProvider,
    RetainedWorkspaceCompositionProvider,
    WorkspaceCompositionFailure,
)
from aware_workspace_runtime.dependency_scope_adapter import (
    WorkspaceCodeDependencyScopeAdapter,
)
from aware_workspace_runtime.dependency_scope_admission import (
    WorkspaceDependencyScopeRuntime,
    WorkspaceRetainedDependencySource,
)
from aware_workspace_runtime.observed_membership import (
    WorkspaceObservedPackageMembershipRuntime,
)
from aware_workspace_runtime.source_exclusion import WorkspaceSourceExclusion
from aware_workspace_runtime.source_observation import WorkspaceSourceObservationRuntime
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable


def dependency(target="Target", key="arbitrary.profile", identifier="provider_source"):
    return f'''
[[workspace.dependencies]]
id="{identifier}"
kind="workspace"
source="workspace://{target}"
channel="local"
revision="workspace-revision:local"
[[workspace.dependencies.code_semantic_contract_profile_packages]]
profile_package_ref="workspace://{target}#{key}"
profile_key="{key}"
semantic_contract_provider_keys=["demo"]
'''


@asynccontextmanager
async def fixture(tmp_path, mutate=None):
    root = tmp_path / "repository"
    root.mkdir()
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\n[[workspaces]]\nhandle="Consumer"\npath="consumer"\n[[workspaces]]\nhandle="Target"\npath="target"\n'
    )
    for folder, handle in (("consumer", "Consumer"), ("target", "Target")):
        module = root / folder / "modules/main"
        module.mkdir(parents=True)
        (root / folder / "aware.workspace.toml").write_text(
            f'aware={1 if folder == "consumer" else 2}\n'
            f'[workspace]\nhandle="{handle}"\n'
            '[[workspace.modules]]\nid="main"\npath="modules/main"\n'
            + (
                dependency()
                if folder == "consumer"
                else '[[workspace.code_semantic_contract_profile_packages]]\n'
                'profile_key="arbitrary.profile"\n'
                'profile_package_ref="workspace://Target#arbitrary.profile"\n'
            )
        )
        (module / "aware.module.toml").write_text(
            'aware=3\n[[packages]]\nid="same"\nkind="code"\nmanifest="pyproject.toml"\n'
        )
        (module / "pyproject.toml").write_bytes(b'[project]\nname="opaque"\n')
    profile = (
        root
        / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
    )
    profile.parent.mkdir(parents=True)
    profile.write_text(
        'aware_semantic_contract_profile=1\n[profile]\nkey="arbitrary.profile"\npackage_key="independent.package"\n[[providers]]\nmodule_id="main"\nprovider_key="demo"\n'
    )
    if mutate:
        mutate(root)
    binding = WorkspaceRepositoryBinding(root)
    session = WorkspaceRepositoryObservationSession(
        binding=binding, provider=FileSystemIndexObservationProvider(binding=binding)
    )
    await session.start(background=False)
    store = retained(
        repository_binding_ref=binding.binding_key, state_root=tmp_path / "state"
    )
    lifetime = WorkspaceCommandLifetimeRuntime()
    parent = lifetime._retain_direct_invocation_parent()
    expected = DirectInvocationExpectation(
        lifetime.invocation_identity, lifetime.epoch_identity, os.getpid()
    )
    exclusion = WorkspaceSourceExclusion(
        runtime=lifetime, parent=parent, expected=expected
    )
    observer = WorkspaceSourceObservationRuntime(
        session=session, store=store, exclusion=exclusion
    )
    members = WorkspaceObservedPackageMembershipRuntime(
        observation_runtime=observer, exclusion=exclusion
    )
    scopes = WorkspaceCompleteScopeObservationRuntime(
        observation_runtime=observer, membership_runtime=members, exclusion=exclusion
    )
    owner = WorkspaceDependencyScopeRuntime(
        observation_runtime=observer, scope_runtime=scopes
    )
    observation = observer.observe(root_relative_path=".")
    try:
        yield root, owner, observation, observer, scopes, lifetime
    finally:
        owner.close()
        scopes.close()
        members.close()
        observer.close()
        lifetime.close()
        await session.stop()


async def test_original_association_retains_distinct_scopes_and_profile_bytes(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        handle = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        adapter = WorkspaceCodeDependencyScopeAdapter(runtime=owner)
        projection = adapter.read_preliminary_dependency_scope_projection(handle)
        assert [s.workspace_handle for s in projection.scopes] == ["Consumer", "Target"]
        assert [s.projection.packages[0].package_id for s in projection.scopes] == [
            "same",
            "same",
        ]
        assert len(projection.edges) == len(projection.profile_associations) == 1
        association = projection.profile_associations[0]
        assert association.declaration == projection.edges[0].declaration
        assert (
            association.manifest.relative_path
            == "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
        )
        assert b"independent.package" in association.manifest.body
        encoded = encode_dependency_scope_closure_v2(projection)
        assert decode_dependency_scope_closure_v2(encoded) == projection
        with pytest.raises(SourceObservationUnavailable):
            adapter.read_dependency_scope_closure(handle, expected=None)
        for copier in (copy.copy, copy.deepcopy):
            with pytest.raises(TypeError):
                copier(handle)
        with pytest.raises(SourceObservationUnavailable):
            owner.read_preliminary_closure(
                object.__new__(WorkspaceRetainedDependencySource)
            )


async def test_local_profile_v2_live_and_retained_composition_agree(tmp_path):
    async with fixture(tmp_path) as (root, _, observation, observer, _, _):
        live = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        retained = RetainedWorkspaceCompositionProvider().describe_retained(
            observation_runtime=observer, observation=observation
        )
        assert live == retained
        assert live["root_kind"] == "repository"


async def test_batch_scope_projection_matches_individual_projection(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        snapshots = tuple(snapshot for _, _, snapshot, _ in owner._records[source].scopes)
        adapter = WorkspaceCodeScopeAdapter(scope_runtime=owner._scope)
        batch = adapter.read_complete_scope_projections(snapshots)
        individual = tuple(
            adapter.read_complete_scope_projection(snapshot) for snapshot in snapshots
        )
        assert batch == individual


@pytest.mark.parametrize(
    "change",
    ["target_v1", "missing_declaration", "wrong_ref", "duplicate", "missing_body"],
)
async def test_import_requires_original_local_profile_publication(tmp_path, change):
    def mutate(root):
        manifest = root / "target/aware.workspace.toml"
        body = manifest.read_text()
        declaration = (
            '[[workspace.code_semantic_contract_profile_packages]]\n'
            'profile_key="arbitrary.profile"\n'
            'profile_package_ref="workspace://Target#arbitrary.profile"\n'
        )
        if change == "target_v1":
            body = body.replace("aware=2", "aware=1")
        elif change == "missing_declaration":
            body = body.replace(declaration, "")
        elif change == "wrong_ref":
            body = body.replace("workspace://Target#", "workspace://Other#")
        elif change == "duplicate":
            body += declaration
        else:
            (
                root
                / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
            ).unlink()
        manifest.write_text(body)

    async with fixture(tmp_path, mutate) as (_, owner, observation, _, _, _):
        with pytest.raises((SourceObservationUnavailable, WorkspaceCompositionFailure)):
            owner.capture(
                observation=observation,
                consumer_scope_key="consumer/aware.workspace.toml",
            )
        assert not owner._records


async def test_batch_scope_projection_final_validation_catches_mutation(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (root, owner, observation, _, _, _):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        snapshots = tuple(snapshot for _, _, snapshot, _ in owner._records[source].scopes)
        adapter = WorkspaceCodeScopeAdapter(scope_runtime=owner._scope)
        original_body = scope_adapter_module._body
        mutated = False

        def mutate_during_projection(coordinate, body):
            nonlocal mutated
            result = original_body(coordinate, body)
            if not mutated:
                mutated = True
                (root / "target/pyproject.toml").write_bytes(
                    b"changed during batch projection"
                )
            return result

        monkeypatch.setattr(scope_adapter_module, "_body", mutate_during_projection)
        with pytest.raises(SourceObservationUnavailable):
            adapter.read_complete_scope_projections(snapshots)


@pytest.mark.parametrize(
    "change",
    ["status", "handle", "profile_missing", "provider_empty", "revision", "cycle"],
)
async def test_invalid_original_selection_refuses_and_unwinds(tmp_path, change):
    def mutate(root):
        path = root / "consumer/aware.workspace.toml"
        text = path.read_text()
        if change == "status":
            text += '\nstatus="inactive"\n'
        elif change == "handle":
            text = text.replace('handle="Consumer"', 'handle=" Consumer"')
        elif change == "profile_missing":
            text = text.replace("arbitrary.profile", "missing.profile")
        elif change == "provider_empty":
            text = text.replace('["demo"]', "[]")
        elif change == "revision":
            text = text.replace("workspace-revision:local", "invented-revision")
        else:
            target = root / "target/aware.workspace.toml"
            target.write_text(target.read_text() + dependency("Consumer"))
        path.write_text(text)

    async with fixture(tmp_path, mutate) as (_, owner, observation, _, scopes, _):
        with pytest.raises((SourceObservationUnavailable, ValueError)):
            owner.capture(
                observation=observation,
                consumer_scope_key="consumer/aware.workspace.toml",
            )
        assert not owner._records and not scopes._records


@pytest.mark.parametrize(
    "change",
    ["comment", "consumer", "root_release", "scope_release", "parent_close", "method"],
)
async def test_original_evidence_revalidated_on_every_read(
    tmp_path, change, monkeypatch
):
    async with fixture(tmp_path) as (
        root,
        owner,
        observation,
        observer,
        scopes,
        lifetime,
    ):
        handle = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        if change in ("comment", "consumer"):
            path = root / (
                "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
                if change == "comment"
                else "consumer/aware.workspace.toml"
            )
            path.write_text(path.read_text() + "\n# changed original bytes\n")
        elif change == "root_release":
            observer.release(observation)
        elif change == "scope_release":
            # Retire via the source owner so its owned cleanup is not repeated.
            owner.release(handle)
        elif change == "parent_close":
            lifetime.close()
        else:
            with monkeypatch.context() as patch:
                patch.setattr(observer, "read", lambda *a, **k: b"substitute")
                with pytest.raises(SourceObservationUnavailable):
                    owner.read_preliminary_closure(handle)
            del observer.read
            return
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            owner.read_preliminary_closure(handle)


async def test_repeated_profile_body_preserves_each_declaration(tmp_path):
    def mutate(root):
        path = root / "consumer/aware.workspace.toml"
        path.write_text(path.read_text() + dependency(identifier="second_selection"))

    async with fixture(tmp_path, mutate) as (
        _,
        owner,
        observation,
        observer,
        scopes,
        _,
    ):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        value = owner.read_preliminary_closure(source)
        first, second = value.profile_associations
        assert first.declaration != second.declaration
        assert first.manifest.body_ref == second.manifest.body_ref
        assert first.manifest.body == second.manifest.body
        digest = value.closure_digest
        object.__setattr__(first.manifest, "body", b"caller mutation")
        fresh = owner.read_preliminary_closure(source)
        assert fresh.closure_digest == digest
        assert fresh.profile_associations[0].manifest.body != b"caller mutation"
        owner.release(source)
        assert not scopes._records
        observer.revalidate(observation)  # borrowed observation remains usable


async def test_read_uses_captured_selection_after_source_revalidation(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )

        def unexpected_selection(*args, **kwargs):
            raise AssertionError("retained selection should be reused")

        monkeypatch.setattr(owner, "_selection", unexpected_selection)
        projection = owner.read_preliminary_closure(source)
        assert [scope.workspace_handle for scope in projection.scopes] == [
            "Consumer",
            "Target",
        ]


async def test_partial_capture_closure_retires_owned_scopes(tmp_path, monkeypatch):
    async with fixture(tmp_path) as (_, owner, observation, _, scopes, lifetime):
        original = owner._project

        def close_after_projection(*args, **kwargs):
            result = original(*args, **kwargs)
            lifetime.close()
            return result

        monkeypatch.setattr(owner, "_project", close_after_projection)
        with pytest.raises(WorkspaceCommandLifetimeUnavailable):
            owner.capture(
                observation=observation,
                consumer_scope_key="consumer/aware.workspace.toml",
            )
        assert not owner._records and not scopes._records


def test_optional_workspace_performance_probe_records_without_authority_input():
    events = []

    class Probe:
        def record(self, **event):
            events.append(event)

    token = scope_observation.set_performance_probe(Probe())
    try:
        scope_observation._performance_count("workspace.test_counter", amount=3)
        with scope_observation._performance_phase("workspace.test_phase"):
            pass
    finally:
        scope_observation.reset_performance_probe(token)

    assert {event["kind"] for event in events} == {
        "counter",
        "phase_start",
        "phase_end",
    }
    assert {event["name"] for event in events} == {
        "workspace.test_counter",
        "workspace.test_phase",
    }
    assert next(event for event in events if event["kind"] == "counter")["amount"] == 3
