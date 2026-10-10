"""Real source resources and explicit borrowed-parent lifetime proofs."""

import asyncio

import pytest
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from test_observed_semantic_issuers import setup


async def test_fixed_assembly_preserves_original_resources_and_closes_only_owned(
    tmp_path,
):
    async with setup(tmp_path) as (_, session, observer, membership, retained, _, _):
        with composition._compose_direct_workspace_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            assert resources.observation_runtime is not observer
            assert resources.membership_runtime is not membership
            issuer = resources.semantic_issuer
            assert issuer._observation_runtime is resources.observation_runtime
            assert issuer._membership_runtime is resources.membership_runtime
            assert issuer._observation is resources.observation
            assert not hasattr(issuer, "issue_isolated_pair")
            with pytest.raises(SourceObservationUnavailable):
                issuer.issue_source_planning_pair(None, context=None, expected=None)
            projection = resources.scope_adapter.read_complete_scope_projection(
                resources.scope_snapshot
            )
            assert [p.package_id for p in projection.packages] == [
                "demo",
                "provider",
                "target",
            ]
            resources.scope_adapter.validate_complete_scope_projection(
                resources.scope_snapshot, projection_digest=projection.projection_digest
            )
        with pytest.raises(SourceObservationUnavailable):
            resources.scope_adapter.validate_complete_scope_projection(
                resources.scope_snapshot
            )
        assert session.authority_admitted
        assert issuer._closed
        observer.revalidate(retained)  # Borrowed session and shared store still work.


@pytest.mark.parametrize("failure", [RuntimeError, asyncio.CancelledError])
async def test_body_failure_and_cancellation_unwind(tmp_path, failure):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        with pytest.raises(failure):
            with composition._compose_direct_workspace_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                raise failure("body failed")
        with pytest.raises(SourceObservationUnavailable):
            resources.observation_runtime.revalidate(resources.observation)
        assert resources.semantic_issuer._closed
        observer.revalidate(retained)


async def test_all_cleanups_attempted_and_primary_error_preserved(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        calls = []
        original = composition.WorkspaceCompleteScopeObservationRuntime.close

        def failing_close(owner):
            calls.append("scope")
            original(owner)
            raise RuntimeError("cleanup failed")

        monkeypatch.setattr(
            composition.WorkspaceCompleteScopeObservationRuntime, "close", failing_close
        )
        with pytest.raises(BaseExceptionGroup) as caught:
            with composition._compose_direct_workspace_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                raise asyncio.CancelledError("cancelled")
        assert calls == ["scope"]
        assert isinstance(caught.value.exceptions[0], asyncio.CancelledError)
        assert str(caught.value.exceptions[1]) == "cleanup failed"
        with pytest.raises(SourceObservationUnavailable):
            resources.observation_runtime.revalidate(resources.observation)
        observer.revalidate(retained)


async def test_partial_capture_failure_closes_observation(tmp_path, monkeypatch):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        closed = []
        original = composition.WorkspaceSourceObservationRuntime.close

        def track(owner):
            closed.append(owner)
            original(owner)

        monkeypatch.setattr(
            composition.WorkspaceSourceObservationRuntime, "close", track
        )
        with pytest.raises(Exception):
            with composition._compose_direct_workspace_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="absent.workspace.toml",
            ):
                pytest.fail("missing Workspace scope admitted")
        assert len(closed) == 1 and closed[0] is not observer
        observer.revalidate(retained)


async def test_cleanup_uses_retained_method_not_late_replacement(tmp_path, monkeypatch):
    async with setup(tmp_path) as (_, session, observer, _, _, _, _):
        with composition._compose_direct_workspace_sources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as resources:
            monkeypatch.setattr(resources.observation_runtime, "close", lambda: None)
            monkeypatch.setattr(resources.semantic_issuer, "close", lambda: None)
        assert resources.semantic_issuer._closed
        with pytest.raises(SourceObservationUnavailable):
            resources.observation_runtime.revalidate(resources.observation)


async def test_issuer_cleanup_precedes_sources_and_failure_keeps_unwinding(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        calls = []
        original = composition.WorkspaceSourcePlanningSemanticIssuerRuntime.close

        def failing_close(issuer):
            # The original source resources must still be live during issuer close.
            issuer._observation_runtime.revalidate(issuer._observation)
            calls.append("issuer")
            original(issuer)
            raise RuntimeError("issuer cleanup failed")

        monkeypatch.setattr(
            composition.WorkspaceSourcePlanningSemanticIssuerRuntime,
            "close",
            failing_close,
        )
        with pytest.raises(RuntimeError, match="issuer cleanup failed"):
            with composition._compose_direct_workspace_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                pass
        assert calls == ["issuer"]
        assert resources.semantic_issuer._closed
        with pytest.raises(SourceObservationUnavailable):
            resources.scope_adapter.validate_complete_scope_projection(
                resources.scope_snapshot
            )
        observer.revalidate(retained)


@pytest.mark.parametrize("failure", [None, RuntimeError, asyncio.CancelledError])
async def test_command_parent_revokes_before_source_cleanup(
    tmp_path, monkeypatch, failure
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        events = []
        original_parent_close = composition.WorkspaceCommandLifetimeRuntime.close
        original_source_close = (
            composition.WorkspaceSourcePlanningSemanticIssuerRuntime.close
        )

        def close_parent(owner):
            events.append("parent")
            original_parent_close(owner)

        def close_source(owner):
            events.append("issuer")
            original_source_close(owner)

        monkeypatch.setattr(
            composition.WorkspaceCommandLifetimeRuntime, "close", close_parent
        )
        monkeypatch.setattr(
            composition.WorkspaceSourcePlanningSemanticIssuerRuntime,
            "close",
            close_source,
        )

        def run():
            with composition._compose_direct_workspace_command_resources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                assert resources.lifetime_runtime._lifetime is None
                assert resources.invocation_parent is not None
                if failure:
                    raise failure("command failed")
            return resources

        if failure:
            with pytest.raises(failure):
                run()
        else:
            resources = run()
            assert resources.lifetime_runtime._closed
            assert resources.sources.semantic_issuer._closed
        assert events == ["parent", "issuer"]
        observer.revalidate(retained)


async def test_command_partial_source_failure_revokes_unexposed_parent(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        closed = []
        original = composition.WorkspaceCommandLifetimeRuntime.close

        def close(owner):
            assert owner._lifetime is None
            original(owner)
            closed.append(owner)

        monkeypatch.setattr(composition.WorkspaceCommandLifetimeRuntime, "close", close)
        with pytest.raises(Exception):
            with composition._compose_direct_workspace_command_resources(
                session=session,
                store=observer._store,
                workspace_manifest_path="absent.workspace.toml",
            ):
                pytest.fail("partial assembly exposed")
        assert len(closed) == 1 and closed[0]._closed
        observer.revalidate(retained)


async def test_command_cleanup_preserves_body_and_revocation_failures(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        original = composition.WorkspaceCommandLifetimeRuntime.close
        calls = []

        def close(owner):
            calls.append(owner)
            original(owner)
            raise RuntimeError("revocation cleanup failed")

        monkeypatch.setattr(composition.WorkspaceCommandLifetimeRuntime, "close", close)
        with pytest.raises(BaseExceptionGroup) as caught:
            with composition._compose_direct_workspace_command_resources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                raise asyncio.CancelledError("body cancelled")
        assert len(calls) == 1
        assert isinstance(caught.value.exceptions[0], asyncio.CancelledError)
        assert str(caught.value.exceptions[1]) == "revocation cleanup failed"
        assert resources.sources.semantic_issuer._closed
        observer.revalidate(retained)


async def test_fixed_command_retains_host_and_attempts_every_cleanup(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        events = []
        parent_close = composition.WorkspaceCommandLifetimeRuntime.close
        host_close = composition.WorkspaceSemanticCatalogHost.close
        source_close = composition.WorkspaceSourcePlanningSemanticIssuerRuntime.close

        def close_parent(owner):
            events.append("parent")
            parent_close(owner)

        def close_host(host):
            events.append("host")
            host_close(host)
            raise RuntimeError("host cleanup failed")

        def close_source(owner):
            events.append("source")
            source_close(owner)

        monkeypatch.setattr(
            composition.WorkspaceCommandLifetimeRuntime, "close", close_parent
        )
        monkeypatch.setattr(
            composition.WorkspaceSemanticCatalogHost, "close", close_host
        )
        monkeypatch.setattr(
            composition.WorkspaceSourcePlanningSemanticIssuerRuntime,
            "close",
            close_source,
        )
        with pytest.raises(RuntimeError, match="host cleanup failed"):
            with composition._compose_direct_workspace_command_resources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                host = resources.catalog_host
                assert host._command_parent.owner is resources.lifetime_runtime
                assert host._command_parent.parent is resources.invocation_parent
                host.validate_catalog_parent()
        assert events == ["parent", "host", "source"]
        assert resources.lifetime_runtime._closed
        assert resources.sources.semantic_issuer._closed
        assert host._phase == "closed"
        observer.revalidate(retained)


async def test_fixed_command_publishes_original_pair_and_revokes_it(tmp_path):
    from test_semantic_catalog_host import admit, command_setup

    fixture_owner, _, _, fixture_host, code, workspace = command_setup()
    try:
        async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
            with composition._compose_direct_workspace_command_resources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                host = resources.catalog_host
                result = admit(host, code, lambda: workspace)
                expected = host.read_initial_publication()
                epoch = host.read_initial_epoch()
                assert (
                    host.read_code_catalog_for_epoch(epoch, expected=expected)
                    is result.code_admission
                )
                assert (
                    expected.invocation.invocation_identity
                    is resources.lifetime_runtime.invocation_identity
                )
            with pytest.raises(Exception):
                result.code.validate_catalog()
            with pytest.raises(Exception):
                _ = result.workspace.catalog
            observer.revalidate(retained)
    finally:
        fixture_host.close()
        fixture_owner.close()


@pytest.mark.parametrize("change", [None, "source", "pending"])
async def test_original_command_epoch_tracks_real_policy(tmp_path, monkeypatch, change):
    import os
    from dataclasses import replace

    from aware_code_retained_registry_policy_runtime import direct_host as direct
    from aware_code_retained_registry_policy_runtime.calculation import (
        calculate_registry_policy,
    )
    from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
        _bind_direct_policy_epoch,
    )
    from aware_code_retained_registry_policy_runtime.epoch_participation import (
        _assemble_code_epoch_participation,
    )
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticContractRuntime,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
        CatalogPublicationExpectation,
    )
    from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
        RESOURCE_ROLES,
        DirectCommandExpectedContext,
        DirectCommandResourceBinding,
    )
    from aware_workspace_runtime import (
        WorkspaceSemanticMaterializationMembershipCatalog,
    )
    from test_calculation import fixture as code_fixture
    from test_direct_policy_conformance import (
        IsolatedFactory,
        NoExecutionCodec,
        NoExecutionProvider,
    )
    from test_materialization_catalog import _execution_closure
    from test_observed_membership import fixture as repository_fixture

    scope, catalog = code_fixture()
    async with repository_fixture(tmp_path) as (root, session, observer, _):
        (root / "aware.workspace.toml").write_text(
            'aware=1\n[workspace]\nhandle="demo"\n[[workspace.modules]]\nid="demo"\npath="demo"\n'
        )
        for body in [scope.modules[0].manifest, *(p.manifest for p in scope.packages)]:
            path = root / body.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body.body)
        with composition._compose_direct_workspace_command_resources(
            session=session,
            store=observer._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as command:
            owner, joint, sources = (
                command.lifetime_runtime,
                command.catalog_host,
                command.sources,
            )
            providers, planners = _execution_closure(catalog)
            membership = WorkspaceSemanticMaterializationMembershipCatalog.create(
                catalog_ref="fixture.empty",
                catalog_generation=1,
                entries=(),
            )
            pair = joint.admit_catalogs(
                code_catalog=catalog,
                workspace_catalog_reader=lambda: membership,
                provider_executable_bindings=providers,
                dependency_planner_bindings=planners,
            )
            profile = catalog.entries[0].profile_declaration
            runtime = SemanticContractRuntime(
                profile,
                {p.provider_key: NoExecutionProvider(p) for p in profile.providers},
                {
                    c: NoExecutionCodec(c)
                    for c in SemanticContractRuntime._profile_body_contracts(profile)
                },
            )
            # Only this origin supplier remains a fixture. It makes no application trust claim.
            factory = IsolatedFactory(owner)
            resources = dict(
                catalog=pair.code_admission,
                code_runtime=runtime,
                composition_factory=factory,
                lifetime_runtime=owner,
                membership_runtime=sources.membership_runtime,
                observation_runtime=sources.observation_runtime,
                policy_producer=calculate_registry_policy,
                repository_store=observer._store,
                scope_adapter=sources.scope_adapter,
                scope_runtime=sources.scope_runtime,
                semantic_issuer=sources.semantic_issuer,
            )
            digest = ContentDigest.of_bytes(b"isolated-policy-epoch-conformance")
            expected = DirectCommandExpectedContext(
                owner.invocation_identity,
                owner.epoch_identity,
                os.getpid(),
                runtime,
                pair.code_admission,
                SemanticImplementationCoordinate("fixture-composition", digest),
                SemanticConfigurationCoordinate("fixture-composition", digest),
                SemanticImplementationCoordinate("fixture-policy", digest),
                SemanticConfigurationCoordinate("fixture-policy", digest),
                tuple(
                    DirectCommandResourceBinding(role, resources[role], "borrowed")
                    for role in RESOURCE_ROLES
                ),
            )
            lifetime = owner.bind_command_lifetime(expected=expected)
            factory.expected = expected
            bootstrap = direct._assemble_direct_command_bootstrap(
                lifetime=lifetime, expected=expected
            )
            host = direct.register_direct_workspace_origin(bootstrap, lifetime)
            epoch_expected = joint.read_initial_publication()
            epoch = joint.read_initial_epoch()
            parent = command.invocation_parent
            invocation = epoch_expected.invocation
            guard = owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
            try:
                participant = _assemble_code_epoch_participation(
                    owner=owner,
                    parent=parent,
                    invocation=invocation,
                    epoch_owner=joint,
                    guard=guard,
                )
                _bind_direct_policy_epoch(
                    host, participant, epoch, expected=epoch_expected, guard=guard
                )
            finally:
                owner.release_catalog_epoch_exclusion(guard)
            successor = CatalogPublicationExpectation(
                object(),
                epoch_expected,
                replace(epoch_expected, publication_identity=object()),
                digest,
            )
            calculation = direct.calculate_registry_policy
            seen = []

            def during(scope_value, catalog_value):
                assert owner._guard is None
                guard = owner.acquire_catalog_epoch_exclusion(
                    parent, expected=invocation
                )
                try:
                    with pytest.raises(Exception, match="active or unresolved"):
                        participant.validate_catalog_publication_exclusion(
                            guard, expected=successor
                        )
                    seen.append(True)
                finally:
                    owner.release_catalog_epoch_exclusion(guard)
                if change == "source":
                    (root / "demo/home/aware.demo.toml").write_bytes(b"changed")
                return calculation(scope_value, catalog_value)

            monkeypatch.setattr(direct, "calculate_registry_policy", during)
            try:
                if change == "source":
                    with pytest.raises(Exception):
                        direct.produce_registry_policy(host, sources.scope_snapshot)
                    assert seen == [True]
                else:
                    policy = direct.produce_registry_policy(
                        host, sources.scope_snapshot
                    )
                    assert (
                        len(
                            direct.validate_admitted_registry_policy(
                                host, policy
                            ).grants
                        )
                        == 1
                    )
                    assert seen == [True]
                    guard = owner.acquire_catalog_epoch_exclusion(
                        parent, expected=invocation
                    )
                    try:
                        participant.validate_catalog_publication_exclusion(
                            guard, expected=successor
                        )
                        if change == "pending":
                            use = participant._begin_epoch_use(
                                guard, epoch, expected=epoch_expected
                            )
                            with pytest.raises(Exception, match="active or unresolved"):
                                participant.validate_catalog_publication_exclusion(
                                    guard, expected=successor
                                )
                            participant._abandon_unstarted_epoch_use(guard, use)
                    finally:
                        owner.release_catalog_epoch_exclusion(guard)
            finally:
                # Real tracked host requires the live original parent during close.
                direct.close_direct_validation_host(host)
            with pytest.raises(Exception):
                direct.produce_registry_policy(host, sources.scope_snapshot)


@pytest.fixture(scope="module")
def real_environment_factory():
    from aware_code_semantic_contract_runtime import selected_provider
    from aware_environment_semantic_contract_runtime_provider import (
        construct_environment_stage_factory_product,
    )

    return selected_provider._admit_selected_provider_factory(
        factory_ref="test.workspace.real-environment-stage-assembly",
        provider_key="aware_environment",
        selection_factory=construct_environment_stage_factory_product,
    )


@pytest.mark.parametrize("failure", [None, RuntimeError, asyncio.CancelledError])
async def test_real_stage_pair_original_resources_and_cleanup(
    tmp_path, real_environment_factory, failure
):
    from aware_code_semantic_contract_runtime import ContractViolation
    from aware_code_semantic_contract_runtime.stage_contribution import (
        read_selected_provider_stage_contribution,
    )

    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        captured = []

        def run():
            with composition._compose_direct_workspace_staged_command_resources(
                factory_admission=real_environment_factory,
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as resources:
                captured.append(resources)
                stages = read_selected_provider_stage_contribution(
                    resources.contribution
                )
                assert [s.stage for s in stages] == [
                    "source_planning",
                    "authority_derivation",
                ]
                assert stages[0].runtime is not stages[1].runtime
                for actual, retained_stage in zip(
                    stages, resources.stage_runtime_bindings, strict=True
                ):
                    assert actual.runtime is retained_stage.runtime
                    assert actual.registration is retained_stage.registration
                assert resources.command.lifetime_runtime._lifetime is None
                if failure:
                    raise failure("staged body failed")

        if failure:
            with pytest.raises(failure):
                run()
        else:
            run()
        assert captured[0].command.lifetime_runtime._closed
        with pytest.raises(ContractViolation):
            read_selected_provider_stage_contribution(captured[0].contribution)
        observer.revalidate(retained)


@pytest.fixture(scope="module")
def real_sdk_factory():
    from aware_code_semantic_contract_runtime import selected_provider
    from aware_sdk_contract_runtime_provider import (
        construct_sdk_stage_factory_product,
    )

    return selected_provider._admit_selected_provider_factory(
        factory_ref="test.workspace.real-sdk-stage-assembly",
        provider_key="aware_sdk",
        selection_factory=construct_sdk_stage_factory_product,
    )


@pytest.mark.parametrize("failure", [None, RuntimeError, asyncio.CancelledError])
async def test_real_sdk_stage_pair_uses_original_workspace_assembly(
    tmp_path, real_sdk_factory, failure
):
    from aware_code_semantic_contract_runtime import ContractViolation
    from aware_code_semantic_contract_runtime.stage_contribution import (
        read_selected_provider_stage_contribution,
    )
    from aware_sdk_contract_runtime_provider.catalog_contribution import (
        build_sdk_catalog_contribution,
    )

    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        captured = []

        def run():
            with composition._compose_direct_workspace_staged_command_resources(
                factory_admission=real_sdk_factory,
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as staged:
                captured.append(staged)
                stages = read_selected_provider_stage_contribution(staged.contribution)
                assert tuple(stage.stage for stage in stages) == (
                    "source_planning",
                    "authority_derivation",
                )
                assert stages[0].runtime is not stages[1].runtime
                for stage, retained_stage in zip(
                    stages, staged.stage_runtime_bindings, strict=True
                ):
                    assert stage.runtime is retained_stage.runtime
                    assert stage.registration is retained_stage.registration
                catalog = build_sdk_catalog_contribution(staged.contribution)
                assert {
                    entry.profile_declaration.profile_ref for entry in catalog.entries
                } == {
                    "aware.sdk.source-planning",
                    "aware.sdk.package-authority",
                }
                if failure:
                    raise failure("SDK staged body failed")

        if failure:
            with pytest.raises(failure):
                run()
        else:
            run()
        assert captured[0].command.lifetime_runtime._closed
        with pytest.raises(ContractViolation):
            read_selected_provider_stage_contribution(captured[0].contribution)
        observer.revalidate(retained)


async def test_stage_pair_closed_after_source_capture_failure(
    tmp_path, monkeypatch, real_environment_factory
):
    from aware_code_semantic_contract_runtime import ContractViolation
    from aware_code_semantic_contract_runtime.stage_contribution import (
        read_selected_provider_stage_contribution,
    )

    captured = []
    original = composition.issue_selected_provider_stage_contribution

    def issue(factory):
        result = original(factory)
        captured.append(result)
        return result

    monkeypatch.setattr(
        composition, "issue_selected_provider_stage_contribution", issue
    )
    async with setup(tmp_path) as (_, session, observer, _, retained, _, _):
        with pytest.raises(Exception):
            with composition._compose_direct_workspace_staged_command_resources(
                factory_admission=real_environment_factory,
                session=session,
                store=observer._store,
                workspace_manifest_path="absent.workspace.toml",
            ):
                pytest.fail("partial assembly exposed")
        assert len(captured) == 1
        with pytest.raises(ContractViolation):
            read_selected_provider_stage_contribution(captured[0])
        observer.revalidate(retained)


@pytest.mark.parametrize(
    "change", [None, "replay", "source", "stage", "forged", "validator", "gate"]
)
async def test_original_two_stage_origin_product(
    tmp_path, real_environment_factory, change, monkeypatch
):
    from dataclasses import replace

    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from test_semantic_catalog_host import admit, command_setup

    fixture_owner, _, _, fixture_host, code, workspace = command_setup()
    digest = ContentDigest.of_bytes(b"fixture-coordinates-no-bootstrap-authority")
    coords = dict(
        composition_implementation=SemanticImplementationCoordinate(
            "fixture-composition", digest
        ),
        composition_configuration=SemanticConfigurationCoordinate(
            "fixture-composition", digest
        ),
        policy_implementation=SemanticImplementationCoordinate(
            "fixture-policy", digest
        ),
        policy_configuration=SemanticConfigurationCoordinate("fixture-policy", digest),
    )
    try:
        async with setup(tmp_path) as (root, session, observer, _, retained, _, _):
            with composition._compose_direct_workspace_staged_command_resources(
                factory_admission=real_environment_factory,
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as staged:
                admit(staged.command.catalog_host, code, lambda: workspace)
                if change == "forged":
                    with pytest.raises(RuntimeError, match="foreign.*retired"):
                        composition._assemble_direct_workspace_origin_factory(
                            replace(staged), **coords
                        )
                    return
                factory = composition._assemble_direct_workspace_origin_factory(
                    staged, **coords
                )
                lifetime = factory._lifetime
                if change == "gate":
                    from aware_code_retained_registry_policy_runtime import direct_host

                    with pytest.raises(
                        Exception, match="unique live stage catalog entry required"
                    ):
                        direct_host._assemble_direct_command_bootstrap(
                            lifetime=lifetime, expected=factory._expected
                        )
                    assert not factory._used
                elif change == "validator":
                    monkeypatch.setattr(
                        staged.command.sources.scope_adapter,
                        "validate_complete_scope_projection",
                        lambda *a, **k: None,
                    )
                    with pytest.raises(RuntimeError, match="dependency substituted"):
                        factory.create_direct_semantic_origin(lifetime)
                elif change == "source":
                    (root / "aware.workspace.toml").write_bytes(b"changed")
                    with pytest.raises(Exception):
                        factory.create_direct_semantic_origin(lifetime)
                elif change == "stage":
                    object.__setattr__(
                        factory._expected.stage_runtime_bindings[1],
                        "registration",
                        object(),
                    )
                    with pytest.raises(Exception):
                        factory.create_direct_semantic_origin(lifetime)
                else:
                    product = factory.create_direct_semantic_origin(lifetime)
                    assert product.lifetime is lifetime
                    assert product.expected is factory._expected
                    assert len(product.expected.stage_runtime_bindings) == 2
                    assert (
                        product.expected.runtime
                        is staged.stage_runtime_bindings[0].runtime
                    )
                    assert {b.role: b.resource for b in product.expected.resources}[
                        "composition_factory"
                    ] is factory
                    if change == "replay":
                        with pytest.raises(RuntimeError, match="consumed"):
                            factory.create_direct_semantic_origin(lifetime)
                if change not in ("stage", "source"):
                    observer.revalidate(retained)
            with pytest.raises(Exception):
                factory.create_direct_semantic_origin(lifetime)
    finally:
        fixture_host.close()
        fixture_owner.close()


# Qualified fixed composition uses original source resources and the real
# Environment stage/catalog supplier. Fixture factory authorization and build
# coordinates do not qualify installed bootstrap or selected execution.
def qualified_repository(root):
    from aware_environment_semantic_contract_runtime_provider.authority_stage import (
        environment_authority_profile,
    )
    from aware_environment_semantic_contract_runtime_provider.planning_stage import (
        environment_planning_profile,
    )
    from owner_fixtures import MANIFEST
    from test_calculation import HEADER

    text = HEADER.replace("aware = 2", "aware = 3", 1)
    text = text.replace('provider_key = "demo"', 'provider_key = "aware_environment"')
    text = text.replace("demo_toml", "aware_environment_toml").replace(
        "aware.demo.toml", "aware.environment.toml"
    )
    text = text.replace(
        'semantic_package_family = "demo"', 'semantic_package_family = "environment"'
    )
    text = text.replace(
        'semantic_package_kind = "demo_package"',
        'semantic_package_kind = "environment_config_package"\ndeclared_package_kinds = ["environment"]',
    )
    text = text.replace(
        'role = "demo", name = "demo"',
        'role = "aware_environment.environment_config.provider", name = "aware.semantic_provider"',
    )
    text = text.replace(
        'coordinate = "contract:demo"',
        'coordinate = "aware_environment.semantic_contract"',
    )
    text = text.replace(
        'code_package_surface = { state = "absent" }',
        'code_package_surface = { state = "present", value = "environment" }',
    )
    text = text.replace('kind = "demo"', 'kind = "environment"')
    for stage, profile in [
        ("authority", environment_authority_profile()),
        ("planning", environment_planning_profile()),
    ]:
        text = text.replace(
            'profile_ref="demo.' + stage + '"',
            'profile_ref="' + profile.profile_ref + '"',
        )
        text = text.replace(
            '"sha256:' + "a" * 64 + '"', '"' + profile.digest.to_wire() + '"', 1
        )
    text = (
        text[: text.index("dependency_targets =")]
        + 'dependency_targets = {state="present", value=[]}\n'
    )
    provider, occurrence = text.split('[[packages]]\nid = "home"', 1)
    occurrence = 'aware = 3\n[[packages]]\nid = "home"' + occurrence
    occurrence = occurrence.replace(
        'module_id="demo"',
        'scope={kind="dependency", workspace_handle="Target"}, module_id="main"',
    )
    (root / "consumer/modules/main/aware.module.toml").write_text(occurrence)
    (root / "target/modules/main/aware.module.toml").write_text(provider)
    for folder in ("consumer/modules/main/home", "target/modules/main/provider"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "consumer/modules/main/home/aware.environment.toml").write_bytes(MANIFEST)
    (root / "target/modules/main/provider/pyproject.toml").write_bytes(
        b'[project]\nname="provider"\n'
    )
    p = root / "consumer/aware.workspace.toml"
    p.write_text(p.read_text().replace('["demo"]', '["aware_environment"]'))
    p = (
        root
        / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
    )
    p.write_text(
        p.read_text().replace('provider_key="demo"', 'provider_key="aware_environment"')
    )


def qualified_sdk_repository(root):
    """Retained v3 test scope; no repository declaration or installed trust."""
    from pathlib import Path

    from aware_environment_semantic_contract_runtime_provider.authority_stage import (
        environment_authority_profile,
    )
    from aware_environment_semantic_contract_runtime_provider.planning_stage import (
        environment_planning_profile,
    )
    from aware_sdk_contract_runtime_provider.authority_stage import (
        sdk_package_authority_profile,
    )
    from aware_sdk_contract_runtime_provider.planning_stage import (
        sdk_planning_profile,
    )

    qualified_repository(root)
    provider = root / "target/modules/main/aware.module.toml"
    consumer = root / "consumer/modules/main/aware.module.toml"
    for path in (provider, consumer):
        body = path.read_text()
        body = body.replace("aware_environment", "aware_sdk")
        body = body.replace(
            "aware_sdk.environment_config.provider", "aware_sdk.provider"
        )
        body = body.replace(
            'name = "aware.semantic_provider"', 'name = "sdk_definition"'
        )
        body = body.replace(
            'coordinate = "aware_sdk.semantic_contract"',
            'coordinate = "code.semantic-contract:aware_sdk.provider"',
        )
        body = body.replace(
            'code_package_surface = { state = "present", value = "environment" }',
            'code_package_surface = { state = "absent" }',
        )
        body = body.replace("aware.environment.toml", "aware.sdk.toml")
        body = body.replace("environment_config_package", "sdk")
        body = body.replace(
            'declared_package_kinds = ["environment"]',
            'declared_package_kinds = ["sdk"]',
        )
        body = body.replace(
            'semantic_package_family = "environment"',
            'semantic_package_family = "public"',
        )
        body = body.replace('kind = "environment"', 'kind = "sdk"')
        body = body.replace('value = "environment"', 'value = "sdk"')
        body = body.replace('value="1.0"', 'value="1"')
        body = body.replace('value="home-demo"', 'value="aware-dev-sdk"')
        if path is consumer:
            body = body.replace(
                'namespace = {state="present", value="home"}',
                'namespace = {state="present", value="aware_dev_sdk"}',
            ).replace(
                'owned_roots = {state="present", value=["home"]}',
                'owned_roots = {state="present", value=["aware_dev_sdk"]}',
            )
        for predecessor, profile in (
            (environment_authority_profile(), sdk_package_authority_profile()),
            (environment_planning_profile(), sdk_planning_profile()),
        ):
            body = body.replace(
                'profile_ref="' + predecessor.profile_ref + '"',
                'profile_ref="' + profile.profile_ref + '"',
            )
            body = body.replace(predecessor.digest.to_wire(), profile.digest.to_wire())
        path.write_text(body)
    old = root / "consumer/modules/main/home/aware.environment.toml"
    old.unlink()
    sdk_manifest = (
        Path(__file__).resolve().parents[7]
        / "workspaces/aware_dev/modules/dev/sdks/aware_dev/aware/aware.sdk.toml"
    )
    (root / "consumer/modules/main/home/aware.sdk.toml").write_bytes(
        sdk_manifest.read_bytes()
    )
    workspace = root / "consumer/aware.workspace.toml"
    workspace.write_text(
        workspace.read_text().replace("aware_environment", "aware_sdk")
    )
    profile = (
        root
        / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
    )
    profile.write_text(profile.read_text().replace("aware_environment", "aware_sdk"))


_SDK_TARGETS = (
    ("api_package", "dev-service-api", "dev_service_api", "api"),
    ("sdk_package", "agent-sdk", "agent_sdk", "sdk"),
    ("sdk_package", "economy-sdk", "economy_sdk", "sdk"),
    ("sdk_package", "identity-sdk", "identity_sdk", "sdk"),
    ("sdk_package", "workspace-sdk", "workspace_sdk", "sdk"),
)


def qualified_sdk_five_target_repository(root):
    """Test-only v3 targets; target result execution is not claimed."""
    qualified_sdk_repository(root)
    consumer_path = root / "consumer/modules/main/aware.module.toml"
    consumer = consumer_path.read_text()
    mappings = ",".join(
        '{dependency_kind="' + kind + '",dependency_ref="' + name + '",'
        'targets=[{scope={kind="dependency",workspace_handle="Target"},'
        'module_id="main",package_id="' + package_id + '"}],constraints=[]}'
        for kind, name, package_id, _ in _SDK_TARGETS
    )
    consumer_path.write_text(
        consumer.replace(
            'dependency_targets = {state="present", value=[]}',
            'dependency_targets = {state="present", value=[' + mappings + "]}",
        )
    )
    target_path = root / "target/modules/main/aware.module.toml"
    target = target_path.read_text()
    target += """
[[plugins]]
kind="code.module_plugin"
provider_key="fixture_api"
[[packages]]
id="fixture_api_provider"
kind="code"
manifest="fixture_api_provider/pyproject.toml"
[packages.semantic_contract]
role="fixture_api.provider"
contract="aware.semantic_provider"
provider_key="fixture_api"
module="fixture_api.provider"
owns_manifest_kinds=["aware_api_toml"]
capabilities=["materialize"]
[[packages.semantic_contract.registrations]]
key="api"
manifest_contract_kind="aware_api_toml"
manifest_filename="aware.api.toml"
semantic_package_family="public"
semantic_package_kind="api"
declared_package_kinds=["api"]
semantic_contract={role="fixture_api.provider",name="aware.semantic_provider",provider_key="fixture_api",coordinate="fixture_api.semantic_contract"}
supported_languages=["aware"]
code_package_surface={state="absent"}
profiles=[
 {stage="authority_derivation",profile_ref="fixture.api.authority",profile_version="1",profile_digest="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
 {stage="source_planning",profile_ref="fixture.api.planning",profile_version="1",profile_digest="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
]
"""
    provider_root = root / "target/modules/main/fixture_api_provider"
    provider_root.mkdir()
    (provider_root / "pyproject.toml").write_text('[project]\nname="fixture-api"\n')
    for _, name, package_id, kind in _SDK_TARGETS:
        filename = "aware.api.toml" if kind == "api" else "aware.sdk.toml"
        provider = "fixture_api_provider" if kind == "api" else "provider"
        registration = "api" if kind == "api" else "demo"
        target += f'''
[[packages]]
id="{package_id}"
kind="{kind}"
manifest="{package_id}/{filename}"
[packages.semantic_admission]
registration={{state="present",value={{scope={{kind="local"}},module_id="main",package_id="{provider}",registration_key="{registration}"}}}}
semantic_version={{state="present",value="1"}}
semantic_package_name={{state="present",value="{name}"}}
code_package_name={{state="present",value="{package_id}_code"}}
source_code_package_id={{state="absent"}}
configuration={{state="absent"}}
namespace={{state="present",value="{package_id}"}}
owned_roots={{state="present",value=["{package_id}"]}}
dependency_targets={{state="present",value=[]}}
'''
        package_root = root / "target/modules/main" / package_id
        package_root.mkdir()
        body = (
            'aware_api=1\n[api]\npackage_name="dev-service-api"\n'
            if kind == "api"
            else f'aware_sdk=1\n[sdk]\npackage_name="{name}"\nfqn_prefix="{package_id}"\n[build]\n'
        )
        (package_root / filename).write_text(body)
    target_path.write_text(target)


@pytest.mark.parametrize("change", [None, "profile", "manifest"])
async def test_sdk_qualified_host_uses_retained_cross_workspace_profile(
    tmp_path, real_sdk_factory, change
):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime.stage_policy_binding import (
        validate_stage_policy_occurrence,
    )
    from aware_code_semantic_contract_runtime import (
        CodeSemanticContractCatalog,
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_sdk_contract_runtime_provider.catalog_contribution import (
        build_sdk_catalog_contribution,
    )
    from aware_workspace_runtime import (
        WorkspaceSemanticMaterializationMembershipCatalog,
    )
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_sdk_repository) as (
        root,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_sdk_factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            qualified=True,
        ) as staged:
            contribution = build_sdk_catalog_contribution(staged.contribution)
            catalog = CodeSemanticContractCatalog.create(
                catalog_ref="fixture.sdk",
                catalog_generation=1,
                entries=contribution.entries,
            )
            membership = WorkspaceSemanticMaterializationMembershipCatalog.create(
                catalog_ref="fixture.empty", catalog_generation=1, entries=()
            )
            binding = contribution.entries[0]
            staged.command.catalog_host.admit_catalogs(
                code_catalog=catalog,
                workspace_catalog_reader=lambda: membership,
                provider_executable_bindings=contribution.executables,
                dependency_planner_bindings=(
                    (
                        binding.dependency_planner_implementation,
                        binding.dependency_planner_configuration,
                        contribution.planner,
                    ),
                ),
            )
            digest = ContentDigest.of_bytes(b"fixture SDK composition coordinates")
            coords = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.composition", digest
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.composition", digest
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.policy", digest
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.policy", digest
                ),
            )
            with composition._compose_direct_workspace_policy_host(
                staged, **coords
            ) as host:
                source = staged.command.sources.scope_snapshot
                runtime = staged.command.sources.scope_runtime
                policy = code.produce_registry_policy(host, source)
                closure = runtime.read_preliminary_closure(source)
                sdk_package = next(
                    package
                    for scope in closure.scopes
                    if scope.workspace_handle == "Consumer"
                    for package in scope.projection.packages
                    if package.package_id == "home"
                )
                assert sdk_package.package_kind == "sdk"
                validate_stage_policy_occurrence(
                    host, policy, sdk_package.source_identity_digest
                )
                if change == "profile":
                    profile = (
                        root
                        / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
                    )
                    profile.write_text(profile.read_text() + "\n# changed\n")
                elif change == "manifest":
                    manifest = root / "consumer/modules/main/home/aware.sdk.toml"
                    manifest.write_bytes(manifest.read_bytes() + b"\n# changed\n")
                if change:
                    with pytest.raises(
                        SourceObservationUnavailable, match="observed_root_changed"
                    ):
                        validate_stage_policy_occurrence(
                            host, policy, sdk_package.source_identity_digest
                        )


@pytest.mark.parametrize("change", [None, "target_body", "target_declaration"])
async def test_sdk_five_direct_targets_are_original_workspace_inventory(
    tmp_path, change
):
    from aware_sdk_contract_runtime_provider.sdk_manifest import (
        plan_sdk_dependencies,
    )
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            qualified=True,
        ) as command:
            membership = command.sources.membership_runtime
            member = membership.admit(
                observation=command.sources.observation,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            )
            try:
                context, inventory = command.sources.semantic_issuer.inspect_inputs(
                    member
                )
                manifest = (
                    root / "consumer/modules/main/home/aware.sdk.toml"
                ).read_bytes()
                plan = plan_sdk_dependencies(manifest, context, inventory)
                assert len(plan.dependencies) == 5
                assert {
                    (item.dependency_kind, item.dependency_ref)
                    for item in plan.dependencies
                } == {(kind, name) for kind, name, _, _ in _SDK_TARGETS}
                if change == "target_body":
                    target = root / "target/modules/main/agent_sdk/aware.sdk.toml"
                    target.write_bytes(target.read_bytes() + b"\n# changed\n")
                elif change == "target_declaration":
                    target = root / "target/modules/main/aware.module.toml"
                    target.write_text(target.read_text() + "\n# changed\n")
                if change:
                    with pytest.raises(
                        SourceObservationUnavailable, match="observed_root_changed"
                    ):
                        command.sources.semantic_issuer.inspect_inputs(member)
            finally:
                membership.release(member)


@pytest.mark.parametrize(
    "change", [None, "target_before", "target_after", "target_after_resolution"]
)
async def test_sdk_five_targets_join_original_code_selected_planning(
    tmp_path, real_sdk_factory, change
):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime import (
        operation_context as contexts,
    )
    from aware_code_retained_registry_policy_runtime import (
        planning_completion,
    )
    from aware_code_retained_registry_policy_runtime import (
        planning_execution as planning,
    )
    from aware_code_retained_registry_policy_runtime.operation_derivation import (
        RetainedSourcePlanningRequest,
    )
    from aware_code_retained_registry_policy_runtime.retained_input_admission import (
        assemble_retained_input_admission_origin,
    )
    from aware_code_semantic_contract_runtime import (
        CodePortableSemanticContract,
        CodeSemanticContractCatalog,
        ContentDigest,
        ContractViolation,
        SemanticBody,
        SemanticConfigurationCoordinate,
        SemanticContractInvocation,
        SemanticImplementationCoordinate,
        SemanticValueCoordinate,
        TypedEmptyCoordinate,
        selected_provider,
    )
    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        DependencyPlanningInputCodec,
        retained_projection_body,
    )
    from aware_code_semantic_contract_runtime.retained_input_projections import (
        CodeSemanticRegistryPackageInput,
    )
    from aware_code_semantic_contract_runtime.semantic_candidates import (
        semantic_candidate_listing_body,
    )
    from aware_sdk_contract_runtime_provider.catalog_contribution import (
        build_sdk_catalog_contribution,
    )
    from aware_sdk_contract_runtime_provider.planning_stage import (
        BINDING,
        MANIFEST_SOURCE_REF,
        MEANING_ROLE,
        SdkManifestMeaningCodec,
        sdk_planning_body_codec_bindings,
    )
    from aware_workspace_runtime import (
        WorkspaceSemanticMaterializationMembershipCatalog,
    )
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_sdk_factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            qualified=True,
        ) as staged:
            contribution = build_sdk_catalog_contribution(staged.contribution)
            catalog = CodeSemanticContractCatalog.create(
                catalog_ref="fixture.sdk.five-targets",
                catalog_generation=1,
                entries=contribution.entries,
            )
            membership_catalog = (
                WorkspaceSemanticMaterializationMembershipCatalog.create(
                    catalog_ref="fixture.empty", catalog_generation=1, entries=()
                )
            )
            binding = contribution.entries[0]
            pair = staged.command.catalog_host.admit_catalogs(
                code_catalog=catalog,
                workspace_catalog_reader=lambda: membership_catalog,
                provider_executable_bindings=contribution.executables,
                dependency_planner_bindings=(
                    (
                        binding.dependency_planner_implementation,
                        binding.dependency_planner_configuration,
                        contribution.planner,
                    ),
                ),
            )
            digest = ContentDigest.of_bytes(b"fixture SDK five-target composition")
            coordinates = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.composition", digest
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.composition", digest
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.policy", digest
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.policy", digest
                ),
            )
            with composition._compose_direct_workspace_policy_host(
                staged, **coordinates
            ) as host:
                scope = staged.command.sources.scope_snapshot
                policy = code.produce_registry_policy(host, scope)
                stage = next(
                    item
                    for item in staged.stage_runtime_bindings
                    if item.stage == "source_planning"
                )
                member = staged.command.sources.membership_runtime.admit(
                    observation=staged.command.sources.observation,
                    workspace_manifest_path="consumer/aware.workspace.toml",
                    module_id="main",
                    package_id="home",
                )
                try:
                    issuer = staged.command.sources.semantic_issuer
                    package_context, inventory = issuer.inspect_inputs(member)
                    evidence = staged.command.sources.membership_runtime.evidence(
                        member
                    )
                    grant = next(
                        item
                        for item in code.validate_admitted_registry_policy(
                            host, policy
                        ).grants
                        if item.source_identity_digest
                        == package_context.source_identity_digest
                    )
                    registry = CodeSemanticRegistryPackageInput(
                        "aware_sdk_toml",
                        "aware.sdk.toml",
                        "aware_sdk",
                        "public",
                        "sdk",
                        CodePortableSemanticContract(
                            "aware_sdk.provider",
                            "sdk_definition",
                            "aware_sdk",
                            "code.semantic-contract:aware_sdk.provider",
                        ),
                        ("aware",),
                        None,
                        grant.namespace,
                        grant.owned_roots,
                        stage.runtime.profile.profile_ref,
                        stage.runtime.profile.version,
                        stage.runtime.profile.digest,
                        BINDING,
                    )
                    closure = (
                        staged.command.sources.scope_runtime.read_preliminary_closure(
                            scope
                        )
                    )
                    package = next(
                        package
                        for item in closure.scopes
                        if item.workspace_handle == "Consumer"
                        for package in item.projection.packages
                        if package.package_id == "home"
                    )
                    manifest = package.manifest.body
                    manifest_body = SemanticBody(
                        SemanticValueCoordinate(
                            "manifest_source",
                            MANIFEST_SOURCE_REF,
                            "fixture:sdk-retained-manifest",
                            ContentDigest.of_bytes(manifest),
                            len(manifest),
                        ),
                        manifest,
                    )
                    request = RetainedSourcePlanningRequest(
                        manifest_body,
                        semantic_candidate_listing_body(evidence.candidate_listing),
                        retained_projection_body(registry),
                        retained_projection_body(package_context),
                        retained_projection_body(inventory),
                    )
                    context = contexts.begin_source_planning_operation(
                        host, policy, stage.registration, request
                    )
                    expected = contexts.source_planning_expectation(host, context)
                    package_admission, inventory_admission = (
                        issuer.issue_source_planning_pair(
                            member, context=context, expected=expected
                        )
                    )
                    origin = assemble_retained_input_admission_origin(host)
                    registry_admission = origin.issue_registry_package_admission(
                        context, package_admission
                    )
                    joined = origin.join(
                        context,
                        registry_admission,
                        package_admission,
                        inventory_admission,
                    )
                    origin.validate(joined)
                    planning_origin = planning.bind_planning_execution_origin(
                        host, stage.registration, terminal_mode="runtime_completion"
                    )
                    bodies = tuple(
                        sorted(
                            (
                                request.manifest_source,
                                request.candidate_listing,
                                request.registry_package,
                                request.package_context,
                                request.declaration_inventory,
                            ),
                            key=lambda body: body.coordinate.role,
                        )
                    )
                    profile = stage.runtime.profile
                    invocation = SemanticContractInvocation(
                        invocation_ref="fixture:sdk-five-target-planning",
                        idempotency_key="fixture:sdk-five-target-planning",
                        profile_ref=profile.profile_ref,
                        profile_digest=profile.digest,
                        target_package=package_context.package,
                        operation_kind="materialize",
                        inputs=tuple(body.coordinate for body in bodies),
                        predecessor=TypedEmptyCoordinate(
                            profile.providers[0].result_role.contract
                        ),
                        dependencies=(),
                        body_codec_bindings=sdk_planning_body_codec_bindings(),
                        provider_bindings=(BINDING,),
                        requested_output_roles=(MEANING_ROLE,),
                    )
                    closure = selected_provider.SelectedProviderInvocationClosure(
                        invocation, bodies
                    )
                    target = root / "target/modules/main/agent_sdk/aware.sdk.toml"
                    if change == "target_before":
                        target.write_bytes(target.read_bytes() + b"\n# changed\n")
                        with pytest.raises(
                            (ContractViolation, SourceObservationUnavailable)
                        ):
                            selected_provider.issue_selected_provider_execution(
                                stage.runtime,
                                stage.registration,
                                closure,
                                operation_context=context,
                            )
                        return
                    admitted = selected_provider.issue_selected_provider_execution(
                        stage.runtime,
                        stage.registration,
                        closure,
                        operation_context=context,
                    )
                    result = selected_provider.execute_selected_provider(
                        stage.runtime, admitted
                    )
                    assert stage.runtime.owns_completion(result)
                    assert result.result.transition is not None
                    plan = DependencyPlanningInputCodec().decode(
                        result.body_for(result.result.transition.result).canonical_body
                    )
                    assert len(plan.dependencies) == 5
                    assert {
                        (item.dependency_kind, item.dependency_ref)
                        for item in plan.dependencies
                    } == {(kind, name) for kind, name, _, _ in _SDK_TARGETS}
                    meaning_output = result.result.outputs[0].output
                    meaning = SdkManifestMeaningCodec().decode(
                        planning_completion.retained_planning_output_body(
                            planning_origin, context, meaning_output
                        ).canonical_body
                    )
                    assert meaning.sdk.package_name == "aware-dev-sdk"
                    with pytest.raises(ContractViolation):
                        selected_provider.execute_selected_provider(
                            stage.runtime, admitted
                        )
                    if change == "target_after":
                        target.write_bytes(target.read_bytes() + b"\n# changed\n")
                        with pytest.raises(
                            (ContractViolation, SourceObservationUnavailable)
                        ):
                            origin.validate(joined)
                        return
                    origin.validate(joined)
                    from aware_code_retained_registry_policy_runtime import (
                        dependency_operation_validator as demand_validation,
                        retained_demand_operation as demand_runtime,
                    )
                    from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
                        retained_planning_dependency_source,
                    )
                    from aware_code_semantic_contract_runtime import (
                        CodeSemanticMaterializationIntent,
                        CodeSemanticPackagePlanningContext,
                        CodeSemanticRequiredResultProduct,
                    )
                    from aware_code_semantic_contract_runtime.dependency_input_codec import (
                        SemanticDependencyProductInputCodec,
                    )

                    source = retained_planning_dependency_source(
                        planning_origin, context
                    )
                    authority_binding = next(
                        entry
                        for entry in contribution.entries
                        if entry.profile_declaration.profile_ref
                        != stage.runtime.profile.profile_ref
                    )
                    authority_result = next(
                        product
                        for product in authority_binding.result_product_contracts
                        if product.role == "package_authority"
                    )
                    intent = CodeSemanticMaterializationIntent.create(
                        operation_kind="materialize",
                        requested_semantic_root_refs=grant.owned_roots,
                        requested_terminal_output_roles=(authority_result.role,),
                        semantic_configuration_coordinate=None,
                    )
                    selected = CodeSemanticPackagePlanningContext.create(
                        package=package_context.package,
                        package_family=registry.semantic_package_family,
                        package_role=registry.semantic_contract.role,
                        manifest_contract=MANIFEST_SOURCE_REF,
                        code_intent=intent,
                        required_result_products=(
                            CodeSemanticRequiredResultProduct.create(
                                role=authority_result.role,
                                contract=authority_result.contract,
                            ),
                        ),
                        required_semantic_provider_keys=(),
                    )
                    operation = await demand_runtime.execute_retained_dependency_demand(
                        source, context=selected
                    )
                    demand_validator = (
                        demand_validation.retained_dependency_operation_validator(host)
                    )
                    assert issuer._dependency_validator is demand_validator
                    assert (
                        issuer._dependency_resolution.resolver._admission
                        is pair.code_admission
                    )
                    resolution_expected = demand_validator.expectation(operation)
                    assert resolution_expected.demand_set.demands == ()
                    resolution, _fulfillment, products = (
                        issuer.issue_empty_dependency_products(
                            operation,
                            inventory_admission=inventory_admission,
                            expected=resolution_expected,
                        )
                    )
                    assert (
                        len(
                            issuer._dependency_resolution.records[
                                resolution
                            ].relationships
                        )
                        == 5
                    )
                    assert issuer._dependency_resolution.records[resolution].targets == ()
                    product_value = SemanticDependencyProductInputCodec().decode(
                        products.canonical_body
                    )
                    assert product_value.products == ()
                    assert len(product_value.declared_dependencies) == 5
                    if change == "target_after_resolution":
                        target.write_bytes(target.read_bytes() + b"\n# changed\n")
                        with pytest.raises(
                            (ContractViolation, SourceObservationUnavailable)
                        ):
                            issuer.validate_dependency_resolution_admission(
                                resolution, expected=resolution_expected
                            )
                        return
                    issuer.validate_dependency_resolution_admission(
                        resolution, expected=resolution_expected
                    )
                finally:
                    staged.command.sources.membership_runtime.release(member)


async def test_v3_real_sdk_source_authority_joins_original_five_targets(
    tmp_path, real_sdk_factory
):
    from aware_code_retained_registry_policy_runtime import (
        authority_execution,
        authority_operation_context,
        dependency_operation_validator,
        planning_execution,
        retained_demand_operation,
        successor_epoch,
    )
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
        assemble_dependency_admission_consumer,
    )
    from aware_code_retained_registry_policy_runtime.catalog_completion_transfer import (
        bind_catalog_completion_transfer_runtime,
    )
    from aware_code_retained_registry_policy_runtime.operation_context import (
        begin_source_planning_operation,
        source_planning_expectation,
    )
    from aware_code_retained_registry_policy_runtime.operation_derivation import (
        RetainedSourcePlanningRequest,
    )
    from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
        retained_planning_dependency_source,
    )
    from aware_code_retained_registry_policy_runtime.retained_input_admission import (
        assemble_retained_input_admission_origin,
    )
    from aware_code_semantic_contract_runtime import (
        CodePortableSemanticContract,
        CodeSemanticMaterializationIntent,
        CodeSemanticPackagePlanningContext,
        CodeSemanticRequiredResultProduct,
        ContentDigest,
        SemanticBody,
        SemanticConfigurationCoordinate,
        SemanticContractInvocation,
        SemanticImplementationCoordinate,
        SemanticValueCoordinate,
        TypedEmptyCoordinate,
        selected_provider,
    )
    from aware_code_semantic_contract_runtime.package_authority_body_codec import (
        PackageAuthorityBodyCodec,
    )
    from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
        CatalogCompletionTransferExpectation,
        EpochSemanticOperationExpectation,
    )
    from aware_code_semantic_contract_runtime.product_contribution import (
        read_selected_provider_product_catalog_contribution,
    )
    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        retained_projection_body,
    )
    from aware_code_semantic_contract_runtime.retained_input_projections import (
        CodeSemanticRegistryPackageInput,
    )
    from aware_code_semantic_contract_runtime.semantic_candidates import (
        semantic_candidate_listing_body,
    )
    from aware_local_service_runtime import InMemoryLocalOperationalStateStore
    from aware_sdk_contract_runtime_provider.catalog_contribution import (
        build_sdk_catalog_contribution,
    )
    from aware_sdk_contract_runtime_provider import (
        SDK_DEFINITION_PROVIDER_KEY,
        SDK_GRAPH_PRODUCT_FACTORY_REF,
        construct_sdk_graph_product_factory_product,
    )
    from aware_sdk_contract_runtime_provider.planning_stage import (
        BINDING,
        MANIFEST_SOURCE_REF,
        MEANING_ROLE,
        sdk_planning_body_codec_bindings,
    )
    from aware_workspace_runtime import WorkspaceSemanticMaterializationMembershipCatalog
    from aware_workspace_runtime.semantic_materialization_publication import (
        WorkspaceSemanticMaterializationPublisher,
    )
    from aware_workspace_runtime.source_admission_catalog import (
        capture_v3_graph_source_correspondence,
        derive_owner_defined_catalog_entry,
    )
    from test_dependency_scope_admission import fixture as sources
    from test_materialization_declaration_selection import _selection
    from test_semantic_materialization_publication import _BodyStore, _runtime

    real_sdk_graph_product_factory = selected_provider._admit_selected_provider_factory(
        factory_ref=SDK_GRAPH_PRODUCT_FACTORY_REF,
        provider_key=SDK_DEFINITION_PROVIDER_KEY,
        selection_factory=construct_sdk_graph_product_factory_product,
    )

    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        _, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_sdk_factory,
            product_factory_admissions=(real_sdk_graph_product_factory,),
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as staged:
            contribution = build_sdk_catalog_contribution(staged.contribution)
            composition._admit_direct_workspace_selected_provider_catalogs(staged)
            catalog = staged.command.catalog_host._result.code.catalog
            binding = contribution.entries[0]
            product_catalog = read_selected_provider_product_catalog_contribution(
                staged.product_contributions[0]
            )
            digest = ContentDigest.of_bytes(b"fixture SDK v3 authority")
            coordinates = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.v3.composition", digest
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.v3.composition", digest
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.v3.policy", digest
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.v3.policy", digest
                ),
            )
            with composition._compose_direct_workspace_policy_host(
                staged, **coordinates
            ) as host:
                with composition._compose_direct_workspace_selected_materialization_roots(
                    staged.command, selection=_selection("package", "aware-dev-sdk")
                ) as roots:
                    assert len(roots) == 1
                    root, selected = roots[0]
                    issuer = staged.command.sources.declaration_scope_runtime
                    policy = code.produce_registry_policy(host, selected)
                    package, inventory = issuer.inspect_inputs(selected)
                    selected_source = issuer.read_selected_package_source(selected)
                    grant = next(
                        item
                        for item in code.validate_admitted_registry_policy(
                            host, policy
                        ).grants
                        if item.source_identity_digest == package.source_identity_digest
                    )
                    source_record = issuer._selected_record(selected)
                    manifest = staged.command.sources.observation_runtime.read_selected_package(
                        source_record.observation,
                        relative_path=package.manifest_relative_path,
                    )
                    stage = staged.stage_runtime_bindings[0]
                    registry = CodeSemanticRegistryPackageInput(
                        "aware_sdk_toml", "aware.sdk.toml", "aware_sdk", "public", "sdk",
                        CodePortableSemanticContract(
                            "aware_sdk.provider", "sdk_definition", "aware_sdk",
                            "code.semantic-contract:aware_sdk.provider",
                        ),
                        ("aware",), None, grant.namespace, grant.owned_roots,
                        stage.runtime.profile.profile_ref,
                        stage.runtime.profile.version,
                        stage.runtime.profile.digest,
                        BINDING,
                    )
                    manifest_body = SemanticBody(
                        SemanticValueCoordinate(
                            "manifest_source", MANIFEST_SOURCE_REF,
                            "fixture:sdk-v3-manifest", ContentDigest.of_bytes(manifest),
                            len(manifest),
                        ),
                        manifest,
                    )
                    request = RetainedSourcePlanningRequest(
                        manifest_body,
                        semantic_candidate_listing_body(selected_source.candidates),
                        retained_projection_body(registry),
                        retained_projection_body(package),
                        retained_projection_body(inventory),
                    )
                    context = begin_source_planning_operation(
                        host, policy, stage.registration, request
                    )
                    expected = source_planning_expectation(host, context)
                    package_admission, inventory_admission = issuer.issue_source_planning_pair(
                        selected, context=context, expected=expected
                    )
                    origin = assemble_retained_input_admission_origin(host)
                    registry_admission = origin.issue_registry_package_admission(
                        context, package_admission
                    )
                    origin.validate(origin.join(
                        context, registry_admission, package_admission, inventory_admission
                    ))
                    planning_origin = planning_execution.bind_planning_execution_origin(
                        host, stage.registration, terminal_mode="runtime_completion"
                    )
                    bodies = tuple(sorted((
                        request.manifest_source, request.candidate_listing,
                        request.registry_package, request.package_context,
                        request.declaration_inventory,
                    ), key=lambda body: body.coordinate.role))
                    profile = stage.runtime.profile
                    invocation = SemanticContractInvocation(
                        invocation_ref="fixture:sdk-v3-planning",
                        idempotency_key="fixture:sdk-v3-planning",
                        profile_ref=profile.profile_ref,
                        profile_digest=profile.digest,
                        target_package=package.package,
                        operation_kind="materialize",
                        inputs=tuple(body.coordinate for body in bodies),
                        predecessor=TypedEmptyCoordinate(
                            profile.providers[0].result_role.contract
                        ),
                        dependencies=(),
                        body_codec_bindings=sdk_planning_body_codec_bindings(),
                        provider_bindings=(BINDING,),
                        requested_output_roles=(MEANING_ROLE,),
                    )
                    admitted = selected_provider.issue_selected_provider_execution(
                        stage.runtime, stage.registration,
                        selected_provider.SelectedProviderInvocationClosure(invocation, bodies),
                        operation_context=context,
                    )
                    selected_provider.execute_selected_provider(stage.runtime, admitted)
                    planning_source = retained_planning_dependency_source(
                        planning_origin, context
                    )
                    authority_binding = next(
                        entry for entry in contribution.entries
                        if entry.profile_declaration.profile_ref != profile.profile_ref
                    )
                    authority_product = next(
                        item for item in authority_binding.result_product_contracts
                        if item.role == "package_authority"
                    )
                    intent = CodeSemanticMaterializationIntent.create(
                        operation_kind="materialize",
                        requested_semantic_root_refs=grant.owned_roots,
                        requested_terminal_output_roles=(authority_product.role,),
                        semantic_configuration_coordinate=None,
                    )
                    target = CodeSemanticPackagePlanningContext.create(
                        package=package.package,
                        package_family="public",
                        package_role="aware_sdk.provider",
                        manifest_contract=MANIFEST_SOURCE_REF,
                        code_intent=intent,
                        required_result_products=(
                            CodeSemanticRequiredResultProduct.create(
                                role=authority_product.role,
                                contract=authority_product.contract,
                            ),
                        ),
                        required_semantic_provider_keys=(),
                    )
                    operation = await retained_demand_operation.execute_retained_dependency_demand(
                        planning_source, context=target
                    )
                    demand_validator = dependency_operation_validator.retained_dependency_operation_validator(host)
                    resolution_expected = demand_validator.expectation(operation)
                    assert resolution_expected.demand_set.demands == ()
                    resolution, fulfillment, product_body = issuer.issue_empty_dependency_products(
                        operation,
                        inventory_admission=inventory_admission,
                        expected=resolution_expected,
                    )
                    assert len(issuer._dependency_resolution.records[resolution].relationships) == 5
                    admitted_products = assemble_dependency_admission_consumer(
                        host
                    ).admit_dependency_products(
                        operation, resolution, fulfillment, body=product_body
                    )
                    authority_context = authority_operation_context.begin_authority_operation(
                        host, admitted_products
                    )
                    authority_expected = authority_operation_context.authority_operation_expectation(
                        host, authority_context
                    )
                    authority_package, authority_inventory = issuer.issue_authority_pair(
                        selected, context=authority_context, expected=authority_expected
                    )
                    authority_registry = origin.issue_registry_package_admission(
                        authority_context, authority_package
                    )
                    origin.validate(origin.join(
                        authority_context, authority_registry,
                        authority_package, authority_inventory,
                    ))
                    publisher = WorkspaceSemanticMaterializationPublisher(
                        runtime=_runtime(),
                        state_store=InMemoryLocalOperationalStateStore(),
                        body_store=_BodyStore(),
                    )
                    with composition._compose_direct_workspace_authority_predecessor_issuer(
                        staged, host, publisher=publisher
                    ) as predecessor_issuer:
                        authority_stage = staged.stage_runtime_bindings[1]
                        result_contract = authority_stage.runtime.profile.providers[0].result_role.contract
                        execution_identity = object()
                        predecessor_admission = predecessor_issuer.issue_authority_predecessor(
                            authority_context,
                            authority_expected=authority_expected,
                            execution_identity=execution_identity,
                            result_contract=result_contract,
                        )
                        retained_predecessor = authority_execution.retain_authority_predecessor(
                            predecessor_issuer, predecessor_admission,
                            authority_context=authority_context,
                            authority_expected=authority_expected,
                            execution_identity=execution_identity,
                            result_contract=result_contract,
                        )
                        authority_execution.bind_authority_execution_origin(
                            host, authority_stage.registration
                        )
                        closure = authority_execution.prepare_authority_execution(
                            authority_context, retained_predecessor
                        )
                        authority_run = selected_provider.issue_selected_provider_execution(
                            authority_stage.runtime, authority_stage.registration,
                            closure, operation_context=authority_context,
                        )
                        selected_provider.execute_selected_provider(
                            authority_stage.runtime, authority_run
                        )
                        completion = authority_execution.read_authority_completion(
                            authority_context
                        )
                        assert authority_stage.runtime.owns_completion(completion)
                        assert completion.result.transition is not None
                        result_coordinate = completion.result.transition.result
                        authority = PackageAuthorityBodyCodec().decode(
                            completion.body_for(result_coordinate).canonical_body
                        )
                        assert authority.semantic_package.name == "aware-dev-sdk"
                        assert len(authority.direct_dependency_package_refs) == 5
                        source_admission = staged.command.sources.source_admission_runtime.issue(
                            root, selected, authority_package, authority_inventory,
                            context=authority_context,
                            expected=authority_expected,
                            completion=completion,
                        )
                        inspection = staged.command.sources.source_admission_runtime.inspect(
                            source_admission
                        )
                        assert (
                            inspection.package_authority.canonical_bytes()
                            == authority.canonical_bytes()
                        )
                        from aware_code_retained_registry_policy_runtime.selected_catalog_eligibility import (
                            issue_selected_product_catalog_eligibility,
                        )

                        product_policy = code.produce_registry_policy(host, selected)
                        product_eligibility = issue_selected_product_catalog_eligibility(
                            host, product_policy,
                            staged.product_runtime_bindings[0].registration,
                        )
                        entry = derive_owner_defined_catalog_entry(
                            staged.command.sources.source_admission_runtime,
                            source_admission,
                            product_eligibilities=(product_eligibility,),
                        )
                        correspondence = capture_v3_graph_source_correspondence(
                            staged.command.sources.source_admission_runtime,
                            source_admission,
                            entry,
                            product_eligibilities=(product_eligibility,),
                        )
                        owner_plan = planning_source.read_dependencies(package.package)
                        successor = WorkspaceSemanticMaterializationMembershipCatalog.create(
                            catalog_ref="fixture.sdk.v3-successor",
                            catalog_generation=2,
                            entries=(entry,),
                        )
                        catalog_host = staged.command.catalog_host
                        predecessor_publication = catalog_host.read_initial_publication()
                        preparation, publication = catalog_host.prepare_successor_catalogs(
                            code_catalog=catalog,
                            workspace_catalog_reader=lambda: successor,
                            provider_executable_bindings=(
                                *contribution.executables,
                                *product_catalog.executables,
                            ),
                            dependency_planner_bindings=(
                                (
                                    binding.dependency_planner_implementation,
                                    binding.dependency_planner_configuration,
                                    contribution.planner,
                                ),
                                (
                                    product_catalog.entries[0].dependency_planner_implementation,
                                    product_catalog.entries[0].dependency_planner_configuration,
                                    product_catalog.planner,
                                ),
                            ),
                            source_correspondences=(correspondence,),
                        )
                        transfer_runtime = bind_catalog_completion_transfer_runtime(host)
                        transfer_expected = CatalogCompletionTransferExpectation(
                            EpochSemanticOperationExpectation(
                                authority_expected, predecessor_publication
                            ),
                            publication,
                        )
                        transfer = transfer_runtime.prepare_catalog_completion_transfer(
                            authority_context,
                            completion,
                            preparation,
                            expected=transfer_expected,
                        )
                        published = catalog_host.publish_successor_catalogs(
                            preparation,
                            transfer,
                            publication_expected=publication,
                            transfer_expected=transfer_expected,
                            transfer_runtime=transfer_runtime,
                        )
                        assert published.workspace.catalog == successor
                        assert (
                            product_catalog.entries[0].profile_declaration.profile_ref
                            in entry.allowed_profile_refs
                        )
                        assert "sdk_code_package_delta" in (
                            entry.participation_policy.allowed_terminal_output_roles
                        )
                        successor_epoch.adopt_committed_successor_epoch(
                            host, transfer_runtime, transfer, expected=transfer_expected
                        )
                        correspondence.validate(entry, owner_plan)
                        current_epoch = catalog_host.read_initial_epoch()
                        current_publication = catalog_host.read_initial_publication()
                        with composition._compose_direct_workspace_selected_materialization_roots(
                            staged.command,
                            selection=_selection("package", "aware-dev-sdk"),
                        ) as selected_roots:
                            root_plans = composition._compose_direct_workspace_selected_root_code_plans(
                                staged,
                                host,
                                epoch=current_epoch,
                                expected_epoch=current_publication,
                                selection=_selection("package", "aware-dev-sdk"),
                                bound_roots=selected_roots,
                            )
                            from aware_code_retained_registry_policy_runtime.selected_root_intent import (
                                derive_selected_product_root_intent,
                            )
                            product_policy = code.produce_registry_policy(
                                host, selected_roots[0][1]
                            )
                            product_intent, product, provider_key = derive_selected_product_root_intent(
                                host, product_policy,
                                requested_role="sdk_code_package_delta",
                                selected_product_registration=(
                                    staged.product_runtime_bindings[0].registration
                                ),
                            )
                            assert product_intent.requested_terminal_output_roles == (
                                "sdk_code_package_delta",
                            )
                            assert product.role == "sdk_code_package_delta"
                            assert provider_key == SDK_DEFINITION_PROVIDER_KEY
                            product_root_plans = composition._compose_direct_workspace_selected_root_code_plans(
                                staged,
                                host,
                                epoch=current_epoch,
                                expected_epoch=current_publication,
                                selection=_selection("package", "aware-dev-sdk"),
                                bound_roots=selected_roots,
                                selected_product_roots=((
                                    package.package.package_ref,
                                    "sdk_code_package_delta",
                                    staged.product_runtime_bindings[0].registration,
                                ),),
                            )
                            assert product_root_plans[0].required_semantic_provider_keys == (
                                SDK_DEFINITION_PROVIDER_KEY,
                            )
                        assert len(root_plans) == 1
                        assert root_plans[0].code_intent.requested_terminal_output_roles == (
                            "package_authority",
                        )
                        assert "sdk_code_package_delta" in {
                            product.role
                            for product in product_catalog.entries[0].result_product_contracts
                        }


def stage_request(
    package,
    stage,
    *,
    package_coordinate=None,
    package_context=None,
    declaration_inventory=None,
    candidate_listing=None,
):
    from dataclasses import replace

    from aware_code_retained_registry_policy_runtime.operation_derivation import (
        RetainedSourcePlanningRequest,
    )
    from aware_code_semantic_contract_runtime import SemanticPackageCoordinate
    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        retained_projection_body,
    )
    from aware_code_semantic_contract_runtime.semantic_candidates import (
        CodeSemanticCandidate,
        CodeSemanticCandidateListing,
        semantic_candidate_listing_body,
    )
    from aware_environment_semantic_contract_runtime_provider import (
        authority_stage,
        planning_stage,
    )
    from aware_environment_semantic_contract_runtime_provider.body_codecs import (
        environment_manifest_source_body,
    )
    from test_authority_derivation import arguments

    args, _ = arguments(package.manifest.body)
    coordinate = package_coordinate or SemanticPackageCoordinate(
        "fixture:home", package.package_kind, package.manifest.content_digest
    )
    context = package_context or replace(
        args["package_context"],
        package=coordinate,
        source_identity_digest=package.source_identity_digest,
        manifest_relative_path=package.manifest_relative_path,
    )
    registry = replace(
        args["registry_package"],
        fqn_prefix="home",
        owned_semantic_root_refs=("home",),
        profile_ref=stage.runtime.profile.profile_ref,
        profile_version=stage.runtime.profile.version,
        profile_digest=stage.runtime.profile.digest,
        binding=(
            planning_stage.BINDING
            if stage.stage == "source_planning"
            else authority_stage.BINDING
        ),
    )
    inventory = declaration_inventory or replace(
        args["declaration_inventory"],
        package=coordinate,
        source_identity_digest=package.source_identity_digest,
        entries=(),
    )
    candidates = candidate_listing or CodeSemanticCandidateListing(
        package.source_identity_digest,
        (
            CodeSemanticCandidate(
                package.manifest_relative_path, package.manifest.content_digest
            ),
        ),
    )
    return RetainedSourcePlanningRequest(
        environment_manifest_source_body(package.manifest.body),
        semantic_candidate_listing_body(candidates),
        retained_projection_body(registry),
        retained_projection_body(context),
        retained_projection_body(inventory),
    )


@pytest.mark.parametrize(
    "change",
    [
        None,
        "profile",
        "registration",
        "wrong_stage",
        "install_failure",
        "authority_validator_failure",
        "dependency_validator_failure",
        "source_substitution",
    ],
)
async def test_qualified_fixed_source_both_stages(
    tmp_path, real_environment_factory, change, monkeypatch
):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime.operation_derivation import (
        _derive_stage,
    )
    from aware_code_retained_registry_policy_runtime.stage_policy_binding import (
        validate_stage_policy_occurrence,
    )
    from aware_code_semantic_contract_runtime import (
        CodeSemanticContractCatalog,
        ContentDigest,
        ContractViolation,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
        selected_provider,
    )
    from aware_environment_semantic_contract_runtime_provider.catalog_contribution import (
        build_environment_catalog_contribution,
    )
    from aware_workspace_runtime import (
        WorkspaceSemanticMaterializationMembershipCatalog,
    )
    from test_dependency_scope_admission import fixture as sources

    events = []
    holder = {}
    original_code_close = code.close_direct_validation_host
    original_contribution_close = composition.close_selected_provider_stage_contribution
    original_parent_close = composition.WorkspaceCommandLifetimeRuntime.close

    def code_close(host):
        events.append("code")
        assert not holder["command"].lifetime_runtime._closed
        return original_code_close(host)

    def contribution_close(value):
        if "command" in holder:
            events.append("registrations")
            assert not holder["command"].lifetime_runtime._closed
        return original_contribution_close(value)

    def parent_close(owner):
        if "command" in holder and owner is holder["command"].lifetime_runtime:
            events.append("parent")
        return original_parent_close(owner)

    monkeypatch.setattr(code, "close_direct_validation_host", code_close)
    monkeypatch.setattr(
        composition, "close_selected_provider_stage_contribution", contribution_close
    )
    monkeypatch.setattr(
        composition.WorkspaceCommandLifetimeRuntime, "close", parent_close
    )
    if change == "install_failure":

        def fail(*args, **kwargs):
            raise RuntimeError("injected installation failure")

        monkeypatch.setattr(composition, "_install_operation_origin", fail)
    elif change == "authority_validator_failure":
        from aware_code_retained_registry_policy_runtime import (
            authority_operation_context as authority_contexts,
        )

        def fail(_host):
            raise RuntimeError("injected authority validator failure")

        monkeypatch.setattr(authority_contexts, "authority_context_validator", fail)
    elif change == "dependency_validator_failure":
        def fail(_issuer, _validator):
            raise RuntimeError("injected dependency validator failure")

        monkeypatch.setattr(
            composition.WorkspaceSourcePlanningSemanticIssuerRuntime,
            "_bind_original_dependency_validator",
            fail,
        )
    async with sources(tmp_path, qualified_repository) as (
        root,
        _,
        borrowed_source,
        borrowed,
        _,
        _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_environment_factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            qualified=True,
        ) as staged:
            holder["command"] = staged.command
            contribution = build_environment_catalog_contribution(staged.contribution)
            catalog = CodeSemanticContractCatalog.create(
                catalog_ref="fixture.environment",
                catalog_generation=1,
                entries=contribution.entries,
            )
            membership = WorkspaceSemanticMaterializationMembershipCatalog.create(
                catalog_ref="fixture.empty", catalog_generation=1, entries=()
            )
            b = contribution.entries[0]
            pair = staged.command.catalog_host.admit_catalogs(
                code_catalog=catalog,
                workspace_catalog_reader=lambda: membership,
                provider_executable_bindings=contribution.executables,
                dependency_planner_bindings=(
                    (
                        b.dependency_planner_implementation,
                        b.dependency_planner_configuration,
                        contribution.planner,
                    ),
                ),
            )
            digest = ContentDigest.of_bytes(b"fixture build coordinates")
            coords = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "fixture.composition", digest
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "fixture.composition", digest
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "fixture.policy", digest
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "fixture.policy", digest
                ),
            )
            if change == "source_substitution":
                original = staged.command.sources.scope_snapshot
                object.__setattr__(staged.command.sources, "scope_snapshot", object())
                try:
                    with pytest.raises(RuntimeError, match="substituted"):
                        composition._assemble_direct_workspace_origin_factory(
                            staged, **coords
                        )
                finally:
                    object.__setattr__(
                        staged.command.sources, "scope_snapshot", original
                    )
                return
            if change in (
                "install_failure",
                "authority_validator_failure",
                "dependency_validator_failure",
            ):
                message = {
                    "install_failure": "injected installation failure",
                    "authority_validator_failure": "injected authority validator failure",
                    "dependency_validator_failure": "injected dependency validator failure",
                }[change]
                with pytest.raises(RuntimeError, match=message):
                    with composition._compose_direct_workspace_policy_host(
                        staged, **coords
                    ):
                        pytest.fail(
                            "host exposed before original validator installation"
                        )
                assert events == ["code"]
                return
            with composition._compose_direct_workspace_policy_host(
                staged, **coords
            ) as host:
                from aware_code_retained_registry_policy_runtime import (
                    authority_operation_context as authority_contexts,
                )
                from aware_code_retained_registry_policy_runtime import (
                    operation_context as planning_contexts,
                )
                from aware_local_service_runtime import (
                    InMemoryLocalOperationalStateStore,
                )
                from aware_workspace_runtime.semantic_materialization_publication import (
                    WorkspaceSemanticMaterializationPublisher,
                )
                from test_semantic_materialization_publication import (
                    _BodyStore,
                    _runtime,
                )

                predecessor_publisher = WorkspaceSemanticMaterializationPublisher(
                    runtime=_runtime(),
                    state_store=InMemoryLocalOperationalStateStore(),
                    body_store=_BodyStore(),
                )
                with composition._compose_direct_workspace_authority_predecessor_issuer(
                    staged, host, publisher=predecessor_publisher
                ) as predecessor_issuer:
                    assert predecessor_issuer._entrances["authority"][
                        0
                    ] is authority_contexts.authority_context_validator(host)
                    assert predecessor_issuer._catalog_epoch is (
                        staged.command.catalog_host.read_initial_epoch()
                    )
                assert predecessor_issuer._closed

                issuer = staged.command.sources.semantic_issuer
                assert (
                    issuer._validator
                    is planning_contexts.source_planning_context_validator(host)
                )
                assert issuer._authority_validator_binding[
                    0
                ] is authority_contexts.authority_context_validator(host)
                source = staged.command.sources.scope_snapshot
                runtime = staged.command.sources.scope_runtime
                policy = code.produce_registry_policy(host, source)
                closure = runtime.read_preliminary_closure(source)
                package = next(
                    p
                    for scope in closure.scopes
                    if scope.workspace_handle == "Consumer"
                    for p in scope.projection.packages
                    if p.package_id == "home"
                )
                for stage in staged.stage_runtime_bindings:
                    result = _derive_stage(
                        host,
                        policy,
                        stage.registration,
                        stage_request(package, stage),
                        object(),
                        stage=stage.stage,
                    )
                    assert result.runtime is stage.runtime
                    assert result.selected_provider_registration is stage.registration
                if change is None:
                    from aware_code_retained_registry_policy_runtime.retained_input_admission import (
                        assemble_retained_input_admission_origin,
                    )

                    planning = next(
                        stage
                        for stage in staged.stage_runtime_bindings
                        if stage.stage == "source_planning"
                    )
                    member = staged.command.sources.membership_runtime.admit(
                        observation=staged.command.sources.observation,
                        workspace_manifest_path="consumer/aware.workspace.toml",
                        module_id="main",
                        package_id="home",
                    )
                    try:
                        derived_context, derived_inventory = issuer.inspect_inputs(
                            member
                        )
                        derived_candidates = (
                            staged.command.sources.membership_runtime.evidence(
                                member
                            ).candidate_listing
                        )
                        context = planning_contexts.begin_source_planning_operation(
                            host,
                            policy,
                            planning.registration,
                            stage_request(
                                package,
                                planning,
                                package_coordinate=derived_context.package,
                                package_context=derived_context,
                                declaration_inventory=derived_inventory,
                                candidate_listing=derived_candidates,
                            ),
                        )
                        expected = planning_contexts.source_planning_expectation(
                            host, context
                        )
                        assert expected.package == derived_context.package, (
                            expected.package,
                            derived_context.package,
                        )
                        assert (
                            expected.source_identity_digest
                            == derived_context.source_identity_digest
                        ), (
                            expected.source_identity_digest,
                            derived_context.source_identity_digest,
                        )
                        package_admission, inventory_admission = (
                            issuer.issue_source_planning_pair(
                                member, context=context, expected=expected
                            )
                        )
                        origin = assemble_retained_input_admission_origin(host)
                        registry = origin.issue_registry_package_admission(
                            context, package_admission
                        )
                        joined = origin.join(
                            context,
                            registry,
                            package_admission,
                            inventory_admission,
                        )
                        origin.validate(joined)
                    finally:
                        staged.command.sources.membership_runtime.release(member)
                validate_stage_policy_occurrence(
                    host, policy, package.source_identity_digest
                )
                assert not runtime._operation_origin.active
                if change == "profile":
                    p = (
                        root
                        / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
                    )
                    p.write_text(p.read_text() + "\n# changed\n")
                elif change == "registration":
                    st = staged.stage_runtime_bindings[1]
                    selected_provider.close_selected_provider_registration(
                        st.runtime, st.registration
                    )
                if change:
                    for stage in staged.stage_runtime_bindings:
                        registration = (
                            staged.stage_runtime_bindings[
                                1 if stage.stage == "source_planning" else 0
                            ].registration
                            if change == "wrong_stage"
                            else stage.registration
                        )
                        with pytest.raises(Exception):
                            _derive_stage(
                                host,
                                policy,
                                registration,
                                stage_request(package, stage),
                                object(),
                                stage=stage.stage,
                            )
            assert host not in code._HOSTS
            assert not staged.command.lifetime_runtime._closed
        assert staged.command.lifetime_runtime._closed
        assert events == ["code", "registrations", "parent"]
        assert runtime._closed and not runtime._operation_origin.active
        if change is None:
            borrowed.revalidate(borrowed_source)
        with pytest.raises(ContractViolation):
            pair.code.validate_catalog()
