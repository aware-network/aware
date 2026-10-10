"""Real Workspace observations; Code source validator is an explicit unit fixture."""

from dataclasses import fields, replace

import pytest
from aware_code_semantic_contract_runtime import ContentDigest
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.semantic_issuer_factory import (
    WorkspaceSourcePlanningSemanticIssuerRuntime,
)
from test_observed_semantic_issuers import expectation, setup


class CodeValidatorFixture:
    def __init__(self, context, expected):
        self.context, self.expected, self.calls = context, expected, 0

    def validate_retained_semantic_operation_context(self, context, *, expected):
        assert context is self.context
        for field in fields(expected):
            actual, original = (
                getattr(expected, field.name),
                getattr(self.expected, field.name),
            )
            assert (
                (actual is original)
                if field.name
                in {
                    "runtime",
                    "generation_identity",
                    "operation_identity",
                    "selected_provider_registration",
                }
                else (actual == original)
            )
        self.calls += 1


@pytest.mark.parametrize(
    "change",
    [None, "foreign", "digest", "package", "inventory", "source", "close", "validator"],
)
async def test_original_target_issuer(tmp_path, change, monkeypatch):
    async with setup(tmp_path) as (
        root,
        _,
        observation,
        membership,
        retained,
        consumer,
        _,
    ):
        issuer = WorkspaceSourcePlanningSemanticIssuerRuntime._assemble(
            observation_runtime=observation,
            membership_runtime=membership,
            observation=retained,
        )
        try:
            expected = expectation(issuer, membership, consumer)
            context = object()
            validator = CodeValidatorFixture(context, expected)
            issuer._bind_original_code_validator(validator)
            _, inventory = issuer.issue_source_planning_pair(
                consumer, context=context, expected=expected
            )
            target = issuer._records[inventory].targets[0]
            proposed = RetainedTargetExpectation(
                expected, target.context.source_identity_digest, target.context.package
            )
            handle = issuer.select_dependency_target_admission(
                inventory_admission=inventory, expected=proposed
            )
            assert handle is target.membership
            issuer.validate_dependency_target_admission(
                handle, inventory_admission=inventory, expected=proposed
            )
            assert validator.calls >= 4
            if change is None:
                return
            if change == "foreign":
                handle = consumer
            elif change == "digest":
                proposed = replace(
                    proposed,
                    target_source_identity_digest=ContentDigest.of_bytes(b"foreign"),
                )
            elif change == "package":
                proposed = replace(
                    proposed,
                    target_package=replace(
                        proposed.target_package, package_ref="foreign"
                    ),
                )
            elif change == "inventory":
                inventory = object()
            elif change == "source":
                (root / "target/aware.example.toml").write_bytes(b"changed")
            elif change == "close":
                issuer.close()
            else:
                monkeypatch.setattr(
                    validator,
                    "validate_retained_semantic_operation_context",
                    lambda *a, **k: None,
                )
            with pytest.raises(SourceObservationUnavailable):
                issuer.validate_dependency_target_admission(
                    handle, inventory_admission=inventory, expected=proposed
                )
        finally:
            issuer.close()


class DemandValidatorFixture:
    """Only unit mechanics; positive bootstrap authentication is not claimed."""

    def __init__(self, operation, expected):
        self.operation, self.expected = operation, expected
        self.calls = 0
        self.hook = None

    def validate_retained_dependency_operation(self, operation, *, expected):
        assert operation is self.operation
        assert expected is self.expected
        self.calls += 1
        if self.hook:
            return self.hook(self.calls)


@pytest.mark.parametrize(
    "change",
    [
        None,
        "unbound",
        "rebind",
        "foreign_operation",
        "foreign_inventory",
        "wrong_source",
        "method",
        "result",
        "changed_during_validation",
        "close",
    ],
)
async def test_demand_inventory_binding(tmp_path, change, monkeypatch):
    from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
        RetainedDependencyResolutionExpectation,
    )

    async with setup(tmp_path) as (
        root,
        _,
        observation,
        membership,
        retained,
        consumer,
        _,
    ):
        issuer = WorkspaceSourcePlanningSemanticIssuerRuntime._assemble(
            observation_runtime=observation,
            membership_runtime=membership,
            observation=retained,
        )
        try:
            source = expectation(issuer, membership, consumer)
            context = object()
            issuer._bind_original_code_validator(CodeValidatorFixture(context, source))
            _, inventory = issuer.issue_source_planning_pair(
                consumer,
                context=context,
                expected=source,
            )
            operation = object()
            # These portable fields are deliberately placeholders: the unit tests
            # only nominal handoff mechanics, never demand semantic validity.
            expected = RetainedDependencyResolutionExpectation(
                object(),
                object(),
                operation,
                source,
                None,
                None,
                None,
                None,
                None,
                None,
            )
            validator = DemandValidatorFixture(operation, expected)
            if change != "unbound":
                issuer._bind_original_dependency_validator(validator)
            if change == "rebind":
                with pytest.raises(SourceObservationUnavailable):
                    issuer._bind_original_dependency_validator(validator)
                return
            if change == "foreign_operation":
                operation = object()
            elif change == "foreign_inventory":
                inventory = object()
            elif change == "wrong_source":
                expected = replace(
                    expected,
                    source_planning=replace(source, operation_identity=object()),
                )
                validator.expected = expected
            elif change == "method":
                monkeypatch.setattr(
                    validator,
                    "validate_retained_dependency_operation",
                    lambda *a, **k: None,
                )
            elif change == "result":
                validator.hook = lambda _: True
            elif change == "changed_during_validation":

                def change_source(count):
                    if count == 2:
                        (root / "target/aware.example.toml").write_bytes(b"changed")

                validator.hook = change_source
            elif change == "close":
                issuer.close()
            if change is not None:
                with pytest.raises((SourceObservationUnavailable, AssertionError)):
                    issuer._validate_dependency_inventory(
                        operation, inventory, expected=expected
                    )
                return
            record = issuer._validate_dependency_inventory(
                operation, inventory, expected=expected
            )
            assert record is issuer._records[inventory]
            assert validator.calls == 2
        finally:
            issuer.close()


@pytest.mark.parametrize(
    "change",
    [
        None,
        "unbound",
        "rebind",
        "same_validator",
        "planning_handle",
        "wrong_entrance",
        "replay",
        "method",
        "source",
        "close",
        "foreign_context",
    ],
)
async def test_separate_authority_stage_issuer(tmp_path, change, monkeypatch):
    """Real source evidence, explicit validator fixtures; no bootstrap claim."""
    async with setup(tmp_path) as (
        root,
        _,
        observation,
        membership,
        retained,
        consumer,
        _,
    ):
        issuer = WorkspaceSourcePlanningSemanticIssuerRuntime._assemble(
            observation_runtime=observation,
            membership_runtime=membership,
            observation=retained,
        )
        try:
            planning = expectation(issuer, membership, consumer)
            planning_context = object()
            planning_validator = CodeValidatorFixture(planning_context, planning)
            issuer._bind_original_code_validator(planning_validator)
            p_package, p_inventory = issuer.issue_source_planning_pair(
                consumer, context=planning_context, expected=planning
            )
            authority = replace(
                planning,
                stage="authority_derivation",
                runtime=object(),
                operation_identity=object(),
                selected_provider_registration=object(),
            )
            context = object()
            validator = CodeValidatorFixture(context, authority)
            if change == "same_validator":
                with pytest.raises(SourceObservationUnavailable):
                    issuer._bind_original_authority_validator(planning_validator)
                return
            if change != "unbound":
                issuer._bind_original_authority_validator(validator)
            if change == "rebind":
                with pytest.raises(SourceObservationUnavailable):
                    issuer._bind_original_authority_validator(validator)
                return
            if change == "wrong_entrance":
                with pytest.raises(SourceObservationUnavailable):
                    issuer.issue_source_planning_pair(
                        consumer, context=context, expected=authority
                    )
                with pytest.raises(SourceObservationUnavailable):
                    issuer.issue_authority_pair(
                        consumer, context=planning_context, expected=planning
                    )
                return
            if change == "unbound":
                with pytest.raises(SourceObservationUnavailable):
                    issuer.issue_authority_pair(
                        consumer, context=context, expected=authority
                    )
                return
            if change == "foreign_context":
                with pytest.raises(AssertionError):
                    issuer.issue_authority_pair(
                        consumer, context=object(), expected=authority
                    )
                return
            package, inventory = issuer.issue_authority_pair(
                consumer, context=context, expected=authority
            )
            assert package is not p_package and inventory is not p_inventory
            assert issuer._validator is planning_validator
            issuer.validate_package_context_admission(package, expected=authority)
            issuer.validate_declaration_inventory_admission(
                inventory, expected=authority
            )
            issuer.validate_package_context_admission(p_package, expected=planning)
            issuer.validate_declaration_inventory_admission(
                p_inventory, expected=planning
            )
            if change is None:
                return
            if change == "replay":
                with pytest.raises(SourceObservationUnavailable):
                    issuer.issue_authority_pair(
                        consumer, context=context, expected=authority
                    )
                return
            if change == "planning_handle":
                with pytest.raises(AssertionError):
                    issuer.validate_package_context_admission(
                        p_package, expected=authority
                    )
                return
            if change == "method":
                monkeypatch.setattr(
                    validator,
                    "validate_retained_semantic_operation_context",
                    lambda *a, **k: None,
                )
            elif change == "source":
                (root / "target/aware.example.toml").write_bytes(b"changed")
            elif change == "close":
                issuer.close()
            with pytest.raises(SourceObservationUnavailable):
                issuer.validate_package_context_admission(package, expected=authority)
            with pytest.raises(SourceObservationUnavailable):
                issuer.validate_declaration_inventory_admission(
                    inventory, expected=authority
                )
        finally:
            issuer.close()


def qualified_target_repository(root):
    from test_current_head_two_stage_host import qualified_repository

    qualified_repository(root)
    consumer_path = root / "consumer/modules/main/aware.module.toml"
    consumer = consumer_path.read_text()
    target = consumer.replace("aware = 3\n", "", 1).replace("home", "base")
    target = target.replace(
        'scope={kind="dependency", workspace_handle="Target"}', 'scope={kind="local"}'
    )
    target_path = root / "target/modules/main/aware.module.toml"
    target_path.write_text(target_path.read_text() + "\n" + target)
    base = root / "target/modules/main/base"
    base.mkdir()
    original = (root / "consumer/modules/main/home/aware.environment.toml").read_bytes()
    (base / "aware.environment.toml").write_bytes(original.replace(b"home", b"base"))
    consumer_path.write_text(
        consumer.replace(
            'dependency_targets = {state="present", value=[]}',
            'dependency_targets = {state="present", value=[{dependency_kind="environment",dependency_ref="base",targets=[{scope={kind="dependency",workspace_handle="Target"},module_id="main",package_id="base"}],constraints=[]}]}',
        )
    )


@pytest.mark.parametrize(
    "change",
    [
        None,
        "profile",
        "target",
        "edge",
        "retire",
        "reader",
        "foreign_target",
        "replay",
        "cross_stage",
        "imported_v2",
    ],
)
async def test_qualified_original_issuer_both_stages(tmp_path, change, monkeypatch):
    """Original qualified sources and fixed assembly; Code validators are fixtures."""
    from aware_workspace_runtime import direct_command_composition as composition
    from test_dependency_scope_admission import fixture as sources

    def fixture_repository(root):
        qualified_target_repository(root)
        if change == "imported_v2":
            path = root / "target/modules/main/aware.module.toml"
            path.write_text(
                path.read_text()
                .replace("aware = 3", "aware = 2", 1)
                .replace('scope={kind="local"}, ', "")
            )

    async with sources(tmp_path, fixture_repository) as (
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
            resources = command.sources
            issuer = resources.semantic_issuer
            membership = resources.membership_runtime
            consumer = membership.admit(
                observation=resources.observation,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            )
            try:
                planning = expectation(issuer, membership, consumer)
                context = object()
                issuer._bind_original_code_validator(
                    CodeValidatorFixture(context, planning)
                )
                authority = replace(
                    planning,
                    stage="authority_derivation",
                    operation_identity=object(),
                    runtime=object(),
                    selected_provider_registration=object(),
                )
                authority_context = object()
                issuer._bind_original_authority_validator(
                    CodeValidatorFixture(authority_context, authority)
                )
                pp, pi = issuer.issue_source_planning_pair(
                    consumer, context=context, expected=planning
                )
                ap, ai = issuer.issue_authority_pair(
                    consumer, context=authority_context, expected=authority
                )
                assert pp is not ap and pi is not ai
                target = issuer._records[pi].targets[0]
                evidence = membership.evidence(target.membership)
                assert evidence.workspace_manifest_path == "target/aware.workspace.toml"
                assert evidence.package_id == "base"
                assert target.context.package.package_kind == "environment"
                proposed = RetainedTargetExpectation(
                    planning,
                    target.context.source_identity_digest,
                    target.context.package,
                )
                selected = issuer.select_dependency_target_admission(
                    inventory_admission=pi, expected=proposed
                )
                assert selected is target.membership
                for package, inventory, expected in (
                    (pp, pi, planning),
                    (ap, ai, authority),
                ):
                    issuer.validate_package_context_admission(
                        package, expected=expected
                    )
                    issuer.validate_declaration_inventory_admission(
                        inventory, expected=expected
                    )
                if change in (None, "imported_v2"):
                    return
                if change == "foreign_target":
                    with pytest.raises(
                        SourceObservationUnavailable, match="foreign_dependency_target"
                    ):
                        issuer.validate_dependency_target_admission(
                            consumer, inventory_admission=pi, expected=proposed
                        )
                    return
                if change == "replay":
                    for entrance, ctx, exp in (
                        (issuer.issue_source_planning_pair, context, planning),
                        (issuer.issue_authority_pair, authority_context, authority),
                    ):
                        with pytest.raises(
                            SourceObservationUnavailable, match="replay"
                        ):
                            entrance(consumer, context=ctx, expected=exp)
                    return
                if change == "cross_stage":
                    with pytest.raises(AssertionError):
                        issuer.validate_package_context_admission(
                            pp, expected=authority
                        )
                    return
                if change == "profile":
                    path = (
                        root
                        / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
                    )
                elif change == "target":
                    path = root / "target/modules/main/base/aware.environment.toml"
                elif change == "edge":
                    path = root / "consumer/aware.workspace.toml"
                elif change == "retire":
                    resources.scope_runtime.release(resources.scope_snapshot)
                elif change == "reader":
                    monkeypatch.setattr(
                        resources.scope_runtime,
                        "read_preliminary_closure",
                        lambda *a: None,
                    )
                if change in ("profile", "target", "edge"):
                    path.write_bytes(path.read_bytes() + b"\n# changed\n")
                for package, inventory, expected in (
                    (pp, pi, planning),
                    (ap, ai, authority),
                ):
                    with pytest.raises(SourceObservationUnavailable):
                        issuer.validate_package_context_admission(
                            package, expected=expected
                        )
                    with pytest.raises(SourceObservationUnavailable):
                        issuer.validate_declaration_inventory_admission(
                            inventory, expected=expected
                        )
            finally:
                membership.release(consumer)


@pytest.mark.parametrize(
    "change",
    ["unbound", "foreign_source", "missing_edge", "profile_excluded", "target_missing"],
)
async def test_qualified_issuer_refuses_unadmitted_sources(tmp_path, change):
    from aware_code_semantic_contract_runtime import ContractViolation
    from aware_workspace_runtime import direct_command_composition as composition
    from test_dependency_scope_admission import fixture as sources

    def mutate(root):
        qualified_target_repository(root)
        if change == "missing_edge":
            path = root / "consumer/modules/main/aware.module.toml"
            path.write_text(
                path.read_text().replace(
                    'workspace_handle="Target"},module_id="main",package_id="base"',
                    'workspace_handle="Consumer"},module_id="main",package_id="base"',
                )
            )
        elif change == "target_missing":
            path = root / "consumer/modules/main/aware.module.toml"
            path.write_text(
                path.read_text().replace('package_id="base"', 'package_id="missing"')
            )
        elif change == "profile_excluded":
            path = (
                root
                / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
            )
            path.write_text(
                path.read_text().replace(
                    'provider_key="aware_environment"', 'provider_key="another"'
                )
            )

    async with sources(tmp_path, mutate) as (_, _, foreign_source, borrowed, _, _):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            qualified=True,
        ) as command:
            r = command.sources
            member = r.membership_runtime.admit(
                observation=r.observation,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            )
            isolated = WorkspaceSourcePlanningSemanticIssuerRuntime._assemble(
                observation_runtime=r.observation_runtime,
                membership_runtime=r.membership_runtime,
                observation=r.observation,
            )
            try:
                if change == "foreign_source":
                    with pytest.raises(SourceObservationUnavailable):
                        isolated._bind_original_dependency_source(
                            r.scope_runtime, foreign_source
                        )
                else:
                    issuer = isolated if change == "unbound" else r.semantic_issuer
                    with pytest.raises(
                        (SourceObservationUnavailable, ContractViolation)
                    ):
                        issuer.inspect_inputs(member)
            finally:
                isolated.close()
                r.membership_runtime.release(member)


@pytest.mark.parametrize("stage", ["source_planning", "authority_derivation"])
async def test_qualified_issuer_last_validator_source_change(tmp_path, stage):
    from aware_workspace_runtime import direct_command_composition as composition
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_target_repository) as (
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
            r = command.sources
            issuer = r.semantic_issuer
            member = r.membership_runtime.admit(
                observation=r.observation,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            )
            try:
                expected = replace(
                    expectation(issuer, r.membership_runtime, member), stage=stage
                )
                context = object()

                class ChangingValidator(CodeValidatorFixture):
                    def validate_retained_semantic_operation_context(
                        self, context, *, expected
                    ):
                        super().validate_retained_semantic_operation_context(
                            context, expected=expected
                        )
                        if self.calls == 2:
                            path = (
                                root / "target/modules/main/base/aware.environment.toml"
                            )
                            path.write_bytes(
                                path.read_bytes()
                                + b"\n# changed during final validator\n"
                            )

                validator = ChangingValidator(context, expected)
                if stage == "source_planning":
                    issuer._bind_original_code_validator(validator)
                    entrance = issuer.issue_source_planning_pair
                else:
                    issuer._bind_original_code_validator(
                        CodeValidatorFixture(
                            object(), replace(expected, stage="source_planning")
                        )
                    )
                    issuer._bind_original_authority_validator(validator)
                    entrance = issuer.issue_authority_pair
                with pytest.raises(SourceObservationUnavailable):
                    entrance(member, context=context, expected=expected)
                assert not issuer._records
            finally:
                r.membership_runtime.release(member)
