"""Private feasibility only; no installed/source-authority qualification."""
import pytest
from aware_workspace_runtime import SourceObservationUnavailable
from test_declaration_scope_admission import fixture

CONSUMER = "workspaces/network/aware.workspace.toml"

def unrelated(root):
    p = root / "aware.repo.toml"
    p.write_text(p.read_text() + '\n[[workspaces]]\nhandle="Archive"\npath="archive"\n')
    p = root / "workspaces/archive/modules/main/package"
    p.mkdir(parents=True)
    (p / "aware.example.toml").write_bytes(b"archive")
    (p.parent / "aware.module.toml").write_text('aware=1\n[module]\n[[packages]]\nid="example"\nkind="example"\nmanifest="package/aware.example.toml"\nvisibility="module"\n')
    (p.parents[2] / "aware.workspace.toml").write_text('aware=2\n[workspace]\nhandle="Archive"\n[[workspace.modules]]\nid="main"\npath="modules/main"\n')

async def test_distinct_subject_keeps_headers_all_reachable_packages_and_same_code_bodies(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expected):
        unrelated(root)
        full = observer.observe_declarations()
        scoped = observer.observe_declarations(consumer_scope_key=CONSUMER)
        a = observer.declaration_evidence(full)
        b = observer.declaration_evidence(scoped)
        assert a.policy_ref == "declared-repository-structure.v1"
        assert b.policy_ref == "declared-consumer-structure.v1:" + CONSUMER
        paths = {x.relative_path for x in b.bodies}
        assert "workspaces/archive/aware.workspace.toml" in paths
        assert "workspaces/archive/modules/main/aware.module.toml" not in paths
        assert len(b.bodies) < len(a.bodies)
        for scope in ("kernel", "network"):
            assert f"workspaces/{scope}/modules/main/aware.module.toml" in paths
        full_scope = issuer.capture_declaration_scope(observation=full, consumer_scope_key=CONSUMER, expectation=expected)
        scoped_scope = issuer.capture_declaration_scope(observation=scoped, consumer_scope_key=CONSUMER, expectation=expected)
        first, second = issuer.read_declaration_scope(full_scope), issuer.read_declaration_scope(scoped_scope)
        assert [x.scope_key for x in first.scopes] == [x.scope_key for x in second.scopes]
        assert first.repository_manifest == second.repository_manifest
        assert first.edges == second.edges
        assert first.local_profiles == second.local_profiles
        assert first.profile_associations == second.profile_associations
        for left, right in zip(first.scopes, second.scopes, strict=True):
            assert left.projection.workspace_manifest == right.projection.workspace_manifest
            assert left.projection.modules == right.projection.modules
            assert left.projection.packages == right.projection.packages
        observer.revalidate_declarations(scoped)

@pytest.mark.parametrize("path", ("aware.repo.toml", "workspaces/archive/aware.workspace.toml", "workspaces/network/aware.workspace.toml", "workspaces/kernel/modules/main/aware.module.toml", "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml", "workspaces/network/modules/main/package/aware.example.toml"))
async def test_each_admitted_namespace_import_or_descendant_change_rejects(tmp_path, path):
    async with fixture(tmp_path) as (root, _, observer, _, _, _):
        unrelated(root)
        scoped = observer.observe_declarations(consumer_scope_key=CONSUMER)
        p = root / path
        p.write_bytes(p.read_bytes() + b"\n# changed\n")
        with pytest.raises(SourceObservationUnavailable):
            observer.revalidate_declarations(scoped)

async def test_unobserved_descendant_never_claims_full_repo_or_selected_membership(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, _, _, _):
        unrelated(root)
        full = observer.observe_declarations()
        scoped = observer.observe_declarations(consumer_scope_key=CONSUMER)
        p = root / "workspaces/archive/modules/main/package/aware.example.toml"
        p.write_bytes(b"changed")
        observer.revalidate_declarations(scoped)
        with pytest.raises(SourceObservationUnavailable):
            observer.revalidate_declarations(full)
        with pytest.raises(SourceObservationUnavailable):
            observer.observe_selected_package(declaration=scoped, workspace_manifest_path="workspaces/archive/aware.workspace.toml", module_id="main", package_id="example")

async def test_other_consumer_cannot_relabel_scoped_observation(tmp_path):
    async with fixture(tmp_path) as (_, _, observer, issuer, _, expected):
        scoped = observer.observe_declarations(consumer_scope_key=CONSUMER)
        with pytest.raises(SourceObservationUnavailable, match="consumer_policy"):
            issuer.capture_declaration_scope(observation=scoped, consumer_scope_key="workspaces/kernel/aware.workspace.toml", expectation=expected)


def publish_profile(root, scope):
    p = root / f"workspaces/{scope.lower()}/aware.workspace.toml"
    p.write_text(p.read_text() + f'\n[[workspace.code_semantic_contract_profile_packages]]\nprofile_key="{scope.lower()}.default"\nprofile_package_ref="workspace://{scope}#{scope.lower()}.default"\n')
    q = p.parent / f"semantic_contract/profiles/{scope.lower()}.default/aware.semantic_contract_profile.toml"
    q.parent.mkdir(parents=True)
    q.write_bytes(b"profile")


def import_profile(root, source, target):
    p = root / f"workspaces/{source.lower()}/aware.workspace.toml"
    p.write_text(p.read_text() + f'\n[[workspace.dependencies]]\nid="{target}"\nkind="workspace"\nsource="workspace://{target}"\nchannel="local"\nrevision="workspace-revision:local"\n[[workspace.dependencies.code_semantic_contract_profile_packages]]\nprofile_package_ref="workspace://{target}#{target.lower()}.default"\nprofile_key="{target.lower()}.default"\nsemantic_contract_provider_keys=["aware_code"]\n')


@pytest.mark.parametrize("cyclic", (False, True))
async def test_transitive_and_cyclic_imports_keep_every_reachable_descendant(tmp_path, cyclic):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expected):
        unrelated(root)
        publish_profile(root, "Archive")
        import_profile(root, "Kernel", "Archive")
        if cyclic:
            import_profile(root, "Archive", "Kernel")
        scoped = observer.observe_declarations(consumer_scope_key=CONSUMER)
        evidence = observer.declaration_evidence(scoped)
        paths = {x.relative_path for x in evidence.bodies}
        assert "workspaces/archive/modules/main/aware.module.toml" in paths
        assert "workspaces/archive/modules/main/package/aware.example.toml" in paths
        handle = issuer.capture_declaration_scope(observation=scoped, consumer_scope_key=CONSUMER, expectation=expected)
        closure = issuer.read_declaration_scope(handle)
        assert {x.scope_key for x in closure.scopes} == {f"workspaces/{s}/aware.workspace.toml" for s in ("archive", "kernel", "network")}
        assert len(closure.edges) == (3 if cyclic else 2)


@pytest.mark.parametrize("mode", ("default", "explicit_full", "consumer"))
async def test_original_composition_defaults_stay_full_and_opt_in_is_explicit(tmp_path, mode):
    from aware_workspace_runtime import direct_command_composition as composition

    async with fixture(tmp_path) as (root, _, observer, _, _, _):
        unrelated(root)
        kwargs = {} if mode == "default" else {"consumer_bound": mode == "consumer"}
        with composition._compose_direct_workspace_declaration_sources(session=observer._session, store=observer._store, workspace_manifest_path=CONSUMER, exclusion=observer._exclusion, **kwargs) as sources:
            evidence = sources.observation_runtime.declaration_evidence(sources.declaration_observation)
            assert evidence.policy_ref.startswith("declared-consumer-structure.v1:") == (mode == "consumer")
            assert any(x.relative_path == "workspaces/archive/modules/main/aware.module.toml" for x in evidence.bodies) == (mode != "consumer")


@pytest.mark.parametrize("mode", ("alias", "missing_header", "unknown_consumer"))
async def test_namespace_or_consumer_cannot_be_inferred(tmp_path, mode):
    async with fixture(tmp_path) as (root, _, observer, _, _, _):
        unrelated(root)
        consumer = CONSUMER
        if mode == "alias":
            p = root / "aware.repo.toml"
            p.write_text(p.read_text().replace('handle="Archive"', 'handle="Alias"'))
        elif mode == "missing_header":
            (root / "workspaces/archive/aware.workspace.toml").unlink()
        else:
            consumer = "workspaces/unknown/aware.workspace.toml"
        with pytest.raises(SourceObservationUnavailable):
            observer.observe_declarations(consumer_scope_key=consumer)


async def test_same_interpreter_can_return_to_full_repository_contract(tmp_path):
    from aware_workspace_runtime.composition import RetainedWorkspaceCompositionProvider

    async with fixture(tmp_path) as (root, _, observer, _, _, _):
        unrelated(root)
        original = observer.observe_declarations()
        bodies = tuple((entry.relative_path, body) for entry, body in observer.read_declarations(original))
        provider = RetainedWorkspaceCompositionProvider()
        scoped = provider.describe_consumer_captured_bodies(bodies, consumer_scope_key=CONSUMER)
        partial = provider.declaration_body_paths(scoped)
        full = provider.describe_captured_bodies(bodies)
        assert full["contract_ref"] != scoped["contract_ref"]
        assert len(provider.declaration_body_paths(full)) > len(partial)


@pytest.mark.parametrize("exact", (False, True))
def test_public_source_continuation_routes_scope_only_for_exact_v3(monkeypatch, exact):
    from contextlib import contextmanager

    from aware_workspace_materialize_transport import (
        WorkspaceMaterializeCommandProposalV2,
        WorkspaceMaterializeCommandProposalV3,
        WorkspaceMaterializeCommandSelectorV2,
    )
    from aware_workspace_runtime import direct_command_composition as composition

    class Stopped(Exception):
        pass

    seen = []

    @contextmanager
    def resource_boundary(**kwargs):
        seen.append(kwargs["consumer_bound"])
        raise Stopped
        yield  # pragma: no cover

    common = {"attempt_ref": "fixture-attempt", "participant_checkout_root": None, "workspace_manifest_name": CONSUMER, "plan_only": True}
    if exact:
        proposal = WorkspaceMaterializeCommandProposalV3.create(**common, package_address=("Network", "main", "example"))
    else:
        proposal = WorkspaceMaterializeCommandProposalV2.create(**common, selectors=(WorkspaceMaterializeCommandSelectorV2.create(selector_kind="workspace", selector_ref="Network"),))
    monkeypatch.setattr(composition, "_compose_direct_workspace_command_resources", resource_boundary)
    with pytest.raises(Stopped), composition._compose_direct_workspace_command_source(session=None, store=None, proposal=proposal):
        pass
    assert seen == [exact]


@pytest.mark.parametrize("failure", (KeyboardInterrupt, RuntimeError))
async def test_interrupted_scoped_interpretation_publishes_no_observation_or_descriptors(tmp_path, monkeypatch, failure):
    from aware_workspace_runtime.composition import RetainedWorkspaceCompositionProvider

    async with fixture(tmp_path) as (root, _, observer, _, observed, _):
        unrelated(root)
        before = len(observer._declarations)
        descriptors = set(__import__("os").listdir("/proc/self/fd"))

        def interrupted(*args, **kwargs):
            raise failure("injected metadata interruption")

        with monkeypatch.context() as patch:
            patch.setattr(RetainedWorkspaceCompositionProvider, "describe_consumer_captured_bodies", interrupted)
            with pytest.raises(failure):
                observer.observe_declarations(consumer_scope_key=CONSUMER)
        assert len(observer._declarations) == before
        assert set(__import__("os").listdir("/proc/self/fd")) == descriptors
        # The original fixture observation predates adding Archive, so retain
        # its handle without incorrectly claiming its physical currentness.
        assert observed in observer._declarations


@pytest.mark.parametrize("reader", ("read_declarations", "declaration_evidence", "revalidate_declarations"))
async def test_original_scoped_owner_reader_substitution_never_dispatches(tmp_path, monkeypatch, reader):
    async with fixture(tmp_path) as (_, _, observer, issuer, _, expected):
        scoped = observer.observe_declarations(consumer_scope_key=CONSUMER)
        handle = issuer.capture_declaration_scope(observation=scoped, consumer_scope_key=CONSUMER, expectation=expected)
        calls = []

        def hostile(*args, **kwargs):
            calls.append(True)
            raise AssertionError("substituted owner reader")

        with monkeypatch.context() as patch:
            patch.setattr(observer, reader, hostile)
            with pytest.raises(SourceObservationUnavailable, match="reader_origin"):
                issuer.validate_declaration_scope(handle, expectation=expected, closure_digest=issuer._declaration_record(handle).digest)
        assert calls == []


async def test_non_boolean_scope_mode_never_dispatches_truth_behavior(tmp_path):
    from aware_workspace_runtime import direct_command_composition as composition

    calls = []

    class Hostile:
        def __bool__(self):
            calls.append(True)
            return True

    async with fixture(tmp_path) as (_, _, observer, _, _, _):
        with pytest.raises(TypeError, match="exact consumer declaration mode"), composition._compose_direct_workspace_declaration_sources(session=observer._session, store=observer._store, workspace_manifest_path=CONSUMER, exclusion=observer._exclusion, consumer_bound=Hostile()):
            pass
        assert calls == []
