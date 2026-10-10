
from contextlib import asynccontextmanager

import pytest
from aware_code_semantic_contract_runtime import CodeSemanticCandidateListing
from aware_workspace_runtime import (
    FileSystemIndexObservationProvider,
    SourceObservationUnavailable,
    WorkspaceObservedPackageMembershipRuntime,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSession,
    WorkspaceSourceObservationRuntime,
)
from aware_workspace_runtime.composition import (
    LocalCheckoutWorkspaceCompositionProvider,
    RetainedWorkspaceCompositionProvider,
    WorkspaceCompositionFailure,
)
from test_repository_delta_retention_client import retained


@asynccontextmanager
async def fixture(tmp_path, root_package=False):
    root = tmp_path / "repository"
    root.mkdir()
    (root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle="demo"'
        '\n[[workspace.modules]]\nid="main"\npath="."\n'
    )
    manifest = "aware.example.toml" if root_package else "package/aware.example.toml"
    (root / "aware.module.toml").write_text(
        f'aware = 1\n[module]\n[[packages]]\nid="demo"\nkind="example"'
        f'\nmanifest="{manifest}"\nvisibility="module"\n'
    )
    package = root if root_package else root / "package"
    package.mkdir(exist_ok=True)
    (package / "aware.example.toml").write_bytes(b"opaque owner manifest")
    (package / "unselected.bin").write_bytes(b"unfiltered")
    binding = WorkspaceRepositoryBinding(root)
    session = WorkspaceRepositoryObservationSession(
        binding=binding, provider=FileSystemIndexObservationProvider(binding=binding)
    )
    await session.start(background=False)
    store = retained(
        repository_binding_ref=binding.binding_key, state_root=tmp_path / "state"
    )
    observation = WorkspaceSourceObservationRuntime(session=session, store=store)
    membership = WorkspaceObservedPackageMembershipRuntime(
        observation_runtime=observation
    )
    try:
        yield root, session, observation, membership
    finally:
        membership.close()
        observation.close()
        await session.stop()


def admit(observation, membership):
    retained = observation.observe(root_relative_path=".")
    return retained, membership.admit(
        observation=retained,
        workspace_manifest_path="aware.workspace.toml",
        module_id="main",
        package_id="demo",
    )


@pytest.mark.parametrize("root_package", [False, True])
async def test_membership_from_retained_declarations_and_shared_candidates(
    tmp_path, root_package
):
    async with fixture(tmp_path, root_package) as (root, _, observation, membership):
        _, handle = admit(observation, membership)
        value = membership.evidence(handle)
        assert type(value.candidate_listing) is CodeSemanticCandidateListing
        assert (
            value.source_identity_digest
            == value.candidate_listing.source_identity_digest
        )
        assert value.package_root == ("." if root_package else "package")
        assert (
            membership.read(handle, relative_path="aware.example.toml")
            == b"opaque owner manifest"
        )
        assert "unselected.bin" in [
            c.relative_path for c in value.candidate_listing.candidates
        ]
        membership.revalidate(handle)
        legacy = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        assert (
            legacy["repository"]["workspaces"][0]["modules"][0]["packages"][0][
                "package_root"
            ]
            == value.package_root
        )


async def test_batch_admission_reuses_one_retained_composition_scan(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (root, _, observation, membership):
        module = root / "aware.module.toml"
        module.write_text(
            module.read_text()
            + '\n[[packages]]\nid="second"\nkind="example"'
            '\nmanifest="second/aware.example.toml"\n'
        )
        (root / "second").mkdir()
        (root / "second/aware.example.toml").write_bytes(b"second body")
        retained = observation.observe(root_relative_path=".")
        calls = []
        original = RetainedWorkspaceCompositionProvider.describe_retained

        def describe(provider, **kwargs):
            calls.append(1)
            return original(provider, **kwargs)

        monkeypatch.setattr(
            RetainedWorkspaceCompositionProvider, "describe_retained", describe
        )
        handles = membership.admit_many(
            observation=retained,
            workspace_manifest_path="aware.workspace.toml",
            selections=(("main", "demo"), ("main", "second")),
        )
        assert len(handles) == 2
        assert len(set(handles)) == 2
        assert calls == [1]
        assert [membership.evidence(h).package_id for h in handles] == [
            "demo",
            "second",
        ]


async def test_batch_admission_rejects_duplicate_selection(tmp_path):
    async with fixture(tmp_path) as (_, _, observation, membership):
        retained = observation.observe(root_relative_path=".")
        with pytest.raises(SourceObservationUnavailable, match="duplicate"):
            membership.admit_many(
                observation=retained,
                workspace_manifest_path="aware.workspace.toml",
                selections=(("main", "demo"), ("main", "demo")),
            )


@pytest.mark.parametrize(
    "change", ["declaration", "source", "addition", "missing", "restart"]
)
async def test_membership_revalidation_uses_nominal_runtime(tmp_path, change):
    async with fixture(tmp_path) as (root, session, observation, membership):
        _, handle = admit(observation, membership)
        if change == "declaration":
            (root / "aware.module.toml").write_text("aware = 1\n[module]\n")
        elif change == "source":
            (root / "package/unselected.bin").write_bytes(b"changed")
        elif change == "addition":
            (root / "package/new.txt").write_bytes(b"new")
        elif change == "missing":
            (root / "package/aware.example.toml").unlink()
        else:
            await session.stop()
            await session.start(background=False)
        with pytest.raises(SourceObservationUnavailable):
            membership.revalidate(handle)


async def test_stale_declarations_cannot_issue_membership(tmp_path):
    async with fixture(tmp_path) as (root, _, observation, membership):
        retained = observation.observe(root_relative_path=".")
        (root / "aware.module.toml").write_text("aware = 1\n[module]\n")
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            membership.admit(
                observation=retained,
                workspace_manifest_path="aware.workspace.toml",
                module_id="main",
                package_id="demo",
            )


@pytest.mark.parametrize(
    "change", ["unknown", "duplicate", "alias", "overlap", "schema", "manifest"]
)
async def test_inexact_declarations_refuse(tmp_path, change):
    async with fixture(tmp_path) as (root, _, observation, membership):
        module = root / "aware.module.toml"
        if change == "duplicate":
            module.write_text(
                module.read_text() + '\n[[packages]]\nid="demo"\nkind="example"'
                '\nmanifest="package/aware.example.toml"\n'
            )
        elif change == "alias":
            module.write_text(
                module.read_text() + '\n[[packages]]\nid="other"\nkind="example"'
                '\nmanifest="package/aware.example.toml"\n'
            )
        elif change == "overlap":
            (root / "package/nested").mkdir()
            (root / "package/nested/manifest").write_bytes(b"other")
            module.write_text(
                module.read_text() + '\n[[packages]]\nid="other"\nkind="example"'
                '\nmanifest="package/nested/manifest"\n'
            )
        elif change == "schema":
            module.write_text(module.read_text().replace("aware = 1", "aware = true"))
        elif change == "manifest":
            (root / "package/aware.example.toml").unlink()
        retained = observation.observe(root_relative_path=".")
        with pytest.raises((SourceObservationUnavailable, WorkspaceCompositionFailure)):
            membership.admit(
                observation=retained,
                workspace_manifest_path="aware.workspace.toml",
                module_id="main",
                package_id="unknown" if change == "unknown" else "demo",
            )


async def test_foreign_handles_and_detached_evidence_do_not_issue_authority(tmp_path):
    async with fixture(tmp_path) as (_, _, observation, membership):
        retained, handle = admit(observation, membership)
        evidence = membership.evidence(handle)
        object.__setattr__(evidence, "package_root", ".")
        assert membership.evidence(handle).package_root == "package"
        other = WorkspaceObservedPackageMembershipRuntime(
            observation_runtime=observation
        )
        try:
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                other.revalidate(handle)
        finally:
            other.close()
        with pytest.raises(SourceObservationUnavailable):
            membership.read(handle, relative_path="../aware.module.toml")
        observation.release(retained)
        with pytest.raises(SourceObservationUnavailable):
            membership.evidence(handle)


async def test_repository_declaration_chain_and_handle_mismatch(tmp_path):
    async with fixture(tmp_path) as (root, _, observation, membership):
        (root / "aware.repo.toml").write_text(
            'aware_repo = 1\n[repo]\nhandle="repo"\n'
            '[[workspaces]]\nhandle="demo"\npath="."\n'
        )
        _, handle = admit(observation, membership)
        membership.revalidate(handle)
        (root / "aware.repo.toml").write_text(
            'aware_repo = 1\n[repo]\nhandle="repo"\n'
            '[[workspaces]]\nhandle="wrong"\npath="."\n'
        )
        with pytest.raises(SourceObservationUnavailable, match="handle_mismatch"):
            admit(observation, membership)


async def test_no_live_declaration_fallback_and_direct_nominal_revalidation(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (root, _, observation, membership):
        retained = observation.observe(root_relative_path=".")
        from pathlib import Path

        original_read = Path.read_bytes

        def forbidden(path):
            if path == root or root in path.parents:
                raise AssertionError("live parser read attempted")
            return original_read(path)

        with monkeypatch.context() as patch:
            patch.setattr(Path, "read_bytes", forbidden)
            # Allow retained-store reads; forbid live declaration reads.
            handle = membership.admit(
                observation=retained,
                workspace_manifest_path="aware.workspace.toml",
                module_id="main",
                package_id="demo",
            )
        calls = []
        original = observation.revalidate

        def revalidate(value):
            calls.append(value)
            return original(value)

        with monkeypatch.context() as patch:
            patch.setattr(observation, "revalidate", revalidate)
            membership.revalidate(handle)
        assert calls == [retained]


@pytest.mark.parametrize('root_package', [False, True])
async def test_declaring_module_uses_original_scope_and_revalidation(
    tmp_path, monkeypatch, root_package
):
    async with fixture(tmp_path, root_package) as (root, _, observation, membership):
        retained, handle = admit(observation, membership)
        expected = (root / 'aware.module.toml').read_bytes()
        calls = []
        original = observation.revalidate

        def revalidate(actual):
            assert actual is retained
            calls.append(actual)
            return original(actual)

        monkeypatch.setattr(observation, 'revalidate', revalidate)
        assert membership.read_declaring_module(handle) == expected
        assert calls == [retained]
        if not root_package:
            with pytest.raises(SourceObservationUnavailable):
                membership.read(handle, relative_path='aware.module.toml')


@pytest.mark.parametrize(
    'change', ['module', 'source', 'addition', 'release', 'restart']
)
async def test_declaring_module_refuses_invalidated_observation(tmp_path, change):
    async with fixture(tmp_path) as (root, session, observation, membership):
        _, handle = admit(observation, membership)
        if change == 'module':
            (root / 'aware.module.toml').write_bytes(b'aware = 2\n')
        elif change == 'source':
            (root / 'package/unselected.bin').write_bytes(b'changed')
        elif change == 'addition':
            (root / 'new.bin').write_bytes(b'new')
        elif change == 'release':
            membership.release(handle)
        else:
            await session.stop()
            await session.start(background=False)
        with pytest.raises(SourceObservationUnavailable):
            membership.read_declaring_module(handle)


async def test_declaring_module_rejects_foreign_membership(tmp_path):
    async with fixture(tmp_path) as (_, _, observation, membership):
        _, handle = admit(observation, membership)
        other = WorkspaceObservedPackageMembershipRuntime(
            observation_runtime=observation
        )
        try:
            with pytest.raises(SourceObservationUnavailable):
                other.read_declaring_module(handle)
        finally:
            other.close()
