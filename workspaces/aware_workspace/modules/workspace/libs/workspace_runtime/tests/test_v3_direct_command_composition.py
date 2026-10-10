"""One fixed Workspace command owns the original v3 source handles."""

import ast
import asyncio
import hashlib
import os
from dataclasses import replace
from pathlib import Path
from threading import get_ident
from types import SimpleNamespace

import pytest

from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from test_declaration_scope_admission import fixture
from test_materialization_declaration_selection import (
    _author_v3_repository,
    _selection,
)
from test_materialization_graph_coordinator import _executed_fixture, _execution_state
from test_current_head_two_stage_host import (
    real_environment_factory,
    real_sdk_factory,
    qualified_repository,
    qualified_sdk_five_target_repository,
)


# Closed-inlet diagnostic capsule; no constructor, enrollment or positive
# admission is included. Execution waits for the literal footprint review.
_OWNER_ATTACHMENT_COMPOSITION_SHA256 = "40bceff3e809d21480efacc60925c74a231cf54bb2d034b15c57c103199da9de"
_OWNER_ATTACHMENT_CAPSULE_NODES = (
    "_require_installed_selected_owner_inlet",
    "_open_installed_selected_owner_attachment",
    "_attach_installed_selected_owner_lifetime",
    "_capture_installed_selected_owner_cancellation",
    "_read_installed_selected_owner_cancellation",
    "_release_installed_selected_owner_cancellation",
    "_seal_installed_selected_owner_attachment",
)
_OWNER_ATTACHMENT_FACTORY_METHODS = (
    "prepare_selected_owner_lifetime",
    "retain_selected_owner_completion",
    "abort_selected_owner_lifetime",
)


def test_dormant_owner_attachment_capsule_has_no_positive_inlet():
    source_path = Path(__file__).parents[1] / "aware_workspace_runtime/direct_command_composition.py"
    source = source_path.read_bytes()
    assert hashlib.sha256(source).hexdigest() == _OWNER_ATTACHMENT_COMPOSITION_SHA256
    tree = ast.parse(source)
    nodes = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    factory = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "_DirectWorkspaceOriginFactory")
    methods = {node.name: node for node in factory.body if isinstance(node, ast.FunctionDef)}
    selected = [nodes[name] for name in _OWNER_ATTACHMENT_CAPSULE_NODES]
    # Only the three closed methods; none of the original factory constructor,
    # source readers or qualified assembly is executed in this diagnostic class.
    shell = ast.ClassDef(
        name="DiagnosticClosedFactory", bases=[], keywords=[],
        body=[methods[name] for name in _OWNER_ATTACHMENT_FACTORY_METHODS], decorator_list=[],
    )
    capsule = ast.fix_missing_locations(ast.Module(body=[*selected, shell], type_ignores=[]))
    class DiagnosticUnavailable(RuntimeError):
        pass

    namespace = {"SourceObservationUnavailable": DiagnosticUnavailable, "_owner_lifetime": None}
    exec(compile(capsule, str(source_path), "exec"), namespace)  # noqa: S102 - finite reviewed source-only diagnostic capsule

    class Hostile:
        def __getattribute__(self, name):
            raise AssertionError("foreign dispatch")

        def __hash__(self):
            raise AssertionError("foreign hashing")

        def __eq__(self, other):
            raise AssertionError("foreign equality")

    foreign = Hostile()
    diagnostic_factory = namespace["DiagnosticClosedFactory"]()
    invocations = (
        lambda: namespace["_open_installed_selected_owner_attachment"](
            foreign, foreign, foreign, foreign, original_child_delivery=foreign,
            public_contribution=foreign, private_contribution=foreign,
        ),
        lambda: namespace["_attach_installed_selected_owner_lifetime"](foreign, foreign, foreign),
        lambda: namespace["_capture_installed_selected_owner_cancellation"](foreign, foreign, foreign),
        lambda: namespace["_read_installed_selected_owner_cancellation"](foreign, foreign, foreign),
        lambda: namespace["_release_installed_selected_owner_cancellation"](foreign, foreign, foreign),
        lambda: namespace["_seal_installed_selected_owner_attachment"](foreign),
        lambda: diagnostic_factory.prepare_selected_owner_lifetime(foreign, foreign),
        lambda: diagnostic_factory.retain_selected_owner_completion(foreign, foreign, foreign),
        lambda: diagnostic_factory.abort_selected_owner_lifetime(foreign),
    )
    for invoke in invocations:
        with pytest.raises(DiagnosticUnavailable, match="installed_selected_owner_inlet_unavailable"):
            invoke()


def test_original_owner_attachment_receiving_entrances_still_refuse():
    # Separate original-module refusal grade, using this file's existing
    # baseline import closure. It is not part of the isolated capsule route.
    foreign = object()
    calls = (
        lambda: composition._open_installed_selected_owner_attachment(
            foreign, foreign, foreign, foreign, original_child_delivery=foreign,
            public_contribution=foreign, private_contribution=foreign,
        ),
        lambda: composition._attach_installed_selected_owner_lifetime(foreign, foreign, foreign),
        lambda: composition._capture_installed_selected_owner_cancellation(foreign, foreign, foreign),
        lambda: composition._read_installed_selected_owner_cancellation(foreign, foreign, foreign),
        lambda: composition._release_installed_selected_owner_cancellation(foreign, foreign, foreign),
        lambda: composition._seal_installed_selected_owner_attachment(foreign),
    )
    for call in calls:
        with pytest.raises(SourceObservationUnavailable, match="installed_selected_owner_inlet_unavailable"):
            call()


def _qualified_repository_with_unrelated_v1(root):
    qualified_repository(root)
    workspace = root / "consumer/aware.workspace.toml"
    workspace.write_text(
        workspace.read_text()
        + '[[workspace.modules]]\nid="legacy"\npath="modules/legacy"\n'
    )
    legacy = root / "consumer/modules/legacy"
    (legacy / "old").mkdir(parents=True)
    (legacy / "aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="old"\nkind="api"\n'
        'manifest="old/aware.api.toml"\nvisibility="module"\n'
    )
    (legacy / "old/aware.api.toml").write_bytes(b"unrelated v1")


async def test_direct_command_source_admission_uses_original_parent(tmp_path):
    from aware_code_semantic_contract_runtime import ContentDigest
    from aware_workspace_materialize_transport import (
        WorkspaceMaterializeCommandProposalV2,
        WorkspaceMaterializeCommandSelectorV2,
    )
    from test_dependency_scope_admission import fixture as sources

    proposal = WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="workspace-materialize-attempt:source-test",
        participant_checkout_root=str(tmp_path),
        workspace_manifest_name="consumer/aware.workspace.toml",
        selectors=(WorkspaceMaterializeCommandSelectorV2.create(
            selector_kind="package", selector_ref="demo-package"
        ),),
        plan_only=True,
    )
    async with sources(tmp_path) as (_, _, _, borrowed, _, _):
        inspection = composition.admit_direct_workspace_command_source(
            session=borrowed._session,
            store=borrowed._store,
            proposal=proposal,
        )
        assert inspection.attempt_ref == proposal.attempt_ref
        assert inspection.proposal_digest == proposal.proposal_digest
        assert type(inspection.declaration_scope_digest) is ContentDigest
        assert inspection.declaration_scope_digest.value.startswith("sha256:")
        receipt = inspection.operation_receipt
        assert receipt.attempt_ref == proposal.attempt_ref
        assert receipt.proposal_digest == proposal.proposal_digest
        assert receipt.declaration_scope_digest == inspection.declaration_scope_digest.value
        assert receipt.operation_ref != proposal.attempt_ref


async def test_direct_selected_host_composes_original_environment_without_service(
    tmp_path, real_environment_factory
):
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_repository) as (
        _, _, _, borrowed, _, _,
    ):
        digest = ContentDigest.of_bytes(b"direct Workspace host composition")
        implementation = SemanticImplementationCoordinate("fixture.direct.host", digest)
        configuration = SemanticConfigurationCoordinate("fixture.direct.host", digest)
        with composition.compose_direct_workspace_selected_host(
            factory_admission=real_environment_factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            composition_implementation=implementation,
            composition_configuration=configuration,
            policy_implementation=implementation,
            policy_configuration=configuration,
        ) as selected:
            assert selected.catalog_pair is selected.staged.command.catalog_host._result
            assert selected.code_host in code._HOSTS
            assert selected.staged.command.sources.declaration_scope_runtime._planning_validator
            assert selected.staged.command.sources.declaration_scope_runtime._authority_validator
            from aware_workspace_runtime.private_stage_read_admission import _RUNTIMES

            factory = code._HOSTS[selected.code_host].methods["factory"].receiver
            read_runtime = factory._private_stage_read_runtime()
            assert _RUNTIMES[read_runtime].factory() is factory
            with pytest.raises(TypeError, match="command-owned"):
                factory.prepare_private_stage_read_input(object(), object())
        assert selected.code_host not in code._HOSTS
        assert not _RUNTIMES[read_runtime].live


@pytest.mark.parametrize("changed_module", ("main", "legacy"))
async def test_direct_selected_host_admits_exact_v3_source_with_observed_v1(
    tmp_path, real_environment_factory, changed_module
):
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, _qualified_repository_with_unrelated_v1) as (
        root, _, _, borrowed, _, _,
    ):
        digest = ContentDigest.of_bytes(b"mixed Workspace selected host")
        implementation = SemanticImplementationCoordinate("fixture.mixed.host", digest)
        configuration = SemanticConfigurationCoordinate("fixture.mixed.host", digest)
        with composition.compose_direct_workspace_selected_host(
            factory_admission=real_environment_factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            composition_implementation=implementation,
            composition_configuration=configuration,
            policy_implementation=implementation,
            policy_configuration=configuration,
        ) as selected_host:
            command = selected_host.staged.command
            with composition._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            ) as source:
                policy = code.produce_registry_policy(selected_host.code_host, source)
                admitted = code.validate_admitted_registry_policy(
                    selected_host.code_host, policy
                )
                assert len(admitted.grants) == 1
                assert admitted.grants[0].semantic_package_kind == "environment_config_package"
                module = root / f"consumer/modules/{changed_module}/aware.module.toml"
                module.write_text(module.read_text() + "\n# changed\n")
                with pytest.raises(SourceObservationUnavailable):
                    code.validate_admitted_registry_policy(selected_host.code_host, policy)


async def test_selected_provider_key_comes_from_original_imported_profile(
    tmp_path,
):
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_repository) as (
        _, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            selected = composition._resolve_direct_workspace_selected_provider_keys(
                command, selection=_selection("package", "home-demo")
            )
            assert len(selected) == 1
            assert selected[0][0].semantic_package_name == "home-demo"
            assert selected[0][1] == "aware_environment"


async def test_provider_selection_excludes_unrelated_repository_workspace(tmp_path):
    import shutil

    from test_dependency_scope_admission import fixture as sources

    def with_unrelated(root):
        qualified_repository(root)
        shutil.copytree(root / "target", root / "unrelated")
        workspace = root / "unrelated/aware.workspace.toml"
        workspace.write_text(workspace.read_text().replace("Target", "Unrelated"))
        repository = root / "aware.repo.toml"
        repository.write_text(
            repository.read_text()
            + '[[workspaces]]\nhandle="Unrelated"\npath="unrelated"\n'
        )

    async with sources(tmp_path, with_unrelated) as (
        _, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            closure = issuer.read_declaration_scope(command.sources.declaration_scope)
            assert {scope.workspace_handle for scope in closure.scopes} == {
                "Consumer", "Target",
            }
            selected = composition._resolve_direct_workspace_selected_provider_keys(
                command, selection=_selection("package", "home-demo")
            )
            assert selected[0][1] == "aware_environment"
            with pytest.raises(
                SourceObservationUnavailable,
                match="materialization_repository_scope_incomplete",
            ):
                issuer.inspect_materialization_roots(
                    command.sources.declaration_scope,
                    selection=_selection("repository", "demo"),
                )


def test_graph_prior_state_read_is_single_use_and_revalidated(monkeypatch) -> None:
    """A changed retained state invalidates the same live node use."""
    from aware_workspace_runtime import materialization_operation

    session = object.__new__(composition._CommandOwnedGraphNodeSourceSession)
    record = composition._CommandNodeSourceSessionRecord(
        object(), object(), object(), os.getpid(), get_ident()
    )
    composition._COMMAND_NODE_SESSIONS[session] = record
    current = [object()]
    observation = SimpleNamespace(
        package=object(),
        predecessor_head_revision=1,
        predecessor_head_digest=object(),
        stored_package_occurrence=object(),
    )
    monkeypatch.setattr(
        composition, "_validate_command_owned_graph_node_source", lambda *_: None
    )
    monkeypatch.setattr(
        materialization_operation,
        "_graph_node_admission_state",
        lambda _admission: object(),
    )
    monkeypatch.setattr(
        composition, "_original_graph_head_observation", lambda _state: observation
    )
    monkeypatch.setattr(
        composition,
        "_read_graph_prior_output_state",
        lambda _record, _binding: current[0],
    )
    try:
        assert session.read_current_output_state(
            output_role="sdk_code_package_delta",
            output_state_name="aware_dev_sdk",
        ) is current[0]
        session.validate()
        with pytest.raises(RuntimeError, match="already read"):
            session.read_current_output_state(
                output_role="sdk_code_package_delta",
                output_state_name="aware_dev_sdk",
            )
        current[0] = object()
        with pytest.raises(RuntimeError, match="prior output state changed"):
            session.validate()
        with pytest.raises(RuntimeError, match="session is closed"):
            session.validate()
    finally:
        session.close()


def test_graph_node_prepares_original_semantic_input_expectation(monkeypatch) -> None:
    from aware_code_semantic_contract_runtime import (
        ContentDigest, SemanticContractRef, SemanticPackageCoordinate,
        SemanticValueCoordinate,
    )
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputSourceCoordinate,
    )
    from aware_workspace_runtime import materialization_operation

    session = object.__new__(composition._CommandOwnedGraphNodeSourceSession)
    record = composition._CommandNodeSourceSessionRecord(
        object(), object(), object(), os.getpid(), get_ident()
    )
    composition._COMMAND_NODE_SESSIONS[session] = record
    package = SemanticPackageCoordinate(
        "package:fixture", "sdk", ContentDigest.of_bytes(b"package")
    )
    contract = SemanticContractRef(
        "fixture.manifest", "1", ContentDigest.of_bytes(b"contract")
    )
    body = b"fixture manifest"
    source = SemanticInputSourceCoordinate(
        "aware.sdk.toml",
        SemanticValueCoordinate(
            "manifest_source", contract, "source:manifest",
            ContentDigest.of_bytes(body), len(body),
        ),
    )
    admission = object()
    node = SimpleNamespace(
        node_binding=SimpleNamespace(package=package),
        operation_admission=SimpleNamespace(
            request=SimpleNamespace(operation_ref="fixture:graph-operation")
        ),
    )
    checked = []

    class OriginalSource:
        changed = False

        def inspect(self, original):
            assert original is admission
            return SimpleNamespace(
                package=package,
                package_authority=SimpleNamespace(
                    semantic_package=SimpleNamespace(name="aware_dev_sdk")
                ),
            )

        def semantic_input_source_coordinates(
            self, original, *, source_scope, role, contract: object
        ):
            assert original is admission
            assert (source_scope, role) == ("manifest", "manifest_source")
            assert contract is expected_contract
            return (source,)

        def validate_semantic_input_source(self, original, *, expected):
            assert original is admission
            assert expected.operation_identity is session
            assert expected.source_identity is admission
            if self.changed:
                raise RuntimeError("original source changed")
            checked.append(expected)

    expected_contract = contract
    owner = OriginalSource()
    monkeypatch.setattr(
        composition, "_validate_command_owned_graph_node_source", lambda *_: None
    )
    monkeypatch.setattr(
        materialization_operation, "_graph_node_admission_state", lambda _: node
    )
    monkeypatch.setattr(
        composition, "_original_graph_semantic_source", lambda _: (owner, admission)
    )
    try:
        expected = session.prepare_semantic_input_expectation(
            use_ref="fixture:input-use", stage="definition_request",
            source_scope="manifest", role="manifest_source", contract=contract,
        )
        assert checked == [expected]
        assert expected.operation_ref == "fixture:graph-operation"
        assert expected.package_identity.package == package
        assert expected.package_identity.package_name == "aware_dev_sdk"
        assert expected.source_coordinates == (source,)
        assert expected.operation_identity is session
        owner.changed = True
        with pytest.raises(RuntimeError, match="original source changed"):
            session.prepare_semantic_input_expectation(
                use_ref="fixture:changed-use", stage="definition_request",
                source_scope="manifest", role="manifest_source", contract=contract,
            )
        with pytest.raises(RuntimeError, match="session is closed"):
            session.validate()
    finally:
        session.close()


def test_graph_node_retains_original_genesis_lineage_absence(
    tmp_path, monkeypatch
) -> None:
    from aware_code_semantic_contract_runtime import (
        ContentDigest, SemanticPackageCoordinate,
    )
    from aware_code_semantic_contract_runtime.product_contribution import (
        SelectedProviderProductContribution,
    )
    from aware_local_service_runtime import InMemoryLocalOperationalStateStore
    from aware_workspace_runtime import materialization_operation
    from aware_workspace_runtime.materialization_graph_host_composition import (
        WorkspaceMaterializationGraphBacking,
    )
    from aware_workspace_runtime.semantic_materialization_publication import (
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    )
    from test_semantic_materialization_publication import _occurrence

    package = SemanticPackageCoordinate(
        "package:fixture", "sdk", ContentDigest.of_bytes(b"package")
    )
    occurrence = _occurrence()
    state = InMemoryLocalOperationalStateStore()
    backing = WorkspaceMaterializationGraphBacking(
        state_root=tmp_path,
        repository_binding_ref="repository:genesis-test",
        state_store=state,
    )
    runtime = object()
    registration = object()
    admission = object()
    contribution = object.__new__(SelectedProviderProductContribution)
    node = SimpleNamespace(
        operation=SimpleNamespace(
            _publisher=backing.publisher,
            _runtime=runtime,
            _graph_product_registration=registration,
        ),
        node_binding=SimpleNamespace(package=package),
    )
    observation = SimpleNamespace(
        package=package,
        state="missing",
        stored_head_contract=None,
        predecessor_head_revision=None,
        predecessor_head_digest=None,
        stored_package_occurrence=None,
        expected_post_revision=1,
    )
    selected = SimpleNamespace(
        expected=SimpleNamespace(runtime=runtime, registration=registration)
    )

    class OriginalSource:
        def read_publication_package_occurrence(self, original):
            assert original is admission
            return occurrence

        def validate_publication_package_occurrence(self, original, *, occurrence):
            assert original is admission
            assert occurrence == expected_occurrence

    expected_occurrence = occurrence
    source = OriginalSource()
    monkeypatch.setattr(
        composition, "_validate_command_owned_graph_node_source", lambda *_: None
    )
    monkeypatch.setattr(
        materialization_operation, "_graph_node_admission_state", lambda _: node
    )
    monkeypatch.setattr(
        composition, "_original_graph_head_observation", lambda _: observation
    )
    monkeypatch.setattr(
        composition, "_original_graph_semantic_source", lambda _: (source, admission)
    )
    monkeypatch.setattr(
        composition, "read_selected_provider_product_contribution", lambda _: selected
    )
    session = object.__new__(composition._CommandOwnedGraphNodeSourceSession)
    record = composition._CommandNodeSourceSessionRecord(
        object(), object(), object(), os.getpid(), get_ident(),
        publisher=backing.publisher, product_contribution=contribution,
    )
    composition._COMMAND_NODE_SESSIONS[session] = record
    try:
        with pytest.raises(RuntimeError, match="observation unavailable"):
            session.validate_genesis_lineage_absence()
        assert session.observe_genesis_lineage_absence() is None
        assert record.genesis_lineage is not None
        session.validate_genesis_lineage_absence()
        with pytest.raises(RuntimeError, match="observation unavailable"):
            session.observe_genesis_lineage_absence()
        with pytest.raises(RuntimeError, match="session is closed"):
            session.validate()
    finally:
        session.close()

    second = object.__new__(composition._CommandOwnedGraphNodeSourceSession)
    second_record = composition._CommandNodeSourceSessionRecord(
        object(), object(), object(), os.getpid(), get_ident(),
        publisher=backing.publisher, product_contribution=contribution,
    )
    composition._COMMAND_NODE_SESSIONS[second] = second_record
    try:
        second.observe_genesis_lineage_absence()
        state.compare_and_set(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            "package:other", expected_revision=0, value={"other": "head"},
        )
        with pytest.raises(Exception, match="Namespace changed"):
            second.validate()
        with pytest.raises(RuntimeError, match="session is closed"):
            second.validate()
    finally:
        second.close()


@pytest.fixture(scope="module")
def real_sdk_graph_product_factory():
    from aware_code_semantic_contract_runtime import selected_provider
    from aware_sdk_contract_runtime_provider import (
        SDK_DEFINITION_PROVIDER_KEY,
        SDK_GRAPH_PRODUCT_FACTORY_REF,
        construct_sdk_graph_product_factory_product,
    )

    return selected_provider._admit_selected_provider_factory(
        factory_ref=SDK_GRAPH_PRODUCT_FACTORY_REF,
        provider_key=SDK_DEFINITION_PROVIDER_KEY,
        selection_factory=construct_sdk_graph_product_factory_product,
    )


async def test_fixed_command_retains_original_graph_product_with_stage_pair(
    tmp_path, real_sdk_factory, real_sdk_graph_product_factory, monkeypatch,
):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime.product_execution import (
        bind_product_execution_origin,
    )
    from aware_code_semantic_contract_runtime import (
        ContentDigest, ContractViolation,
        SemanticConfigurationCoordinate, SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime.product_contribution import (
        read_selected_provider_product_contribution,
    )
    from test_dependency_scope_admission import fixture as sources

    product = None
    closed_inside_parent = []
    original_close = composition.close_selected_provider_product_contribution

    def close_product(value):
        staged.command.sources.exclusion.check_live()
        closed_inside_parent.append(value)
        original_close(value)

    monkeypatch.setattr(
        composition, "close_selected_provider_product_contribution", close_product
    )
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        _, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_sdk_factory,
            product_factory_admissions=(real_sdk_graph_product_factory,),
            session=borrowed._session, store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as staged:
            assert len(staged.product_contributions) == 1
            product = staged.product_contributions[0]
            original = read_selected_provider_product_contribution(product)
            assert staged.product_runtime_bindings[0].runtime is original.expected.runtime
            assert (
                staged.product_runtime_bindings[0].registration
                is original.expected.registration
            )
            pair = composition._admit_direct_workspace_selected_provider_catalogs(
                staged
            )
            assert len(pair.code.catalog.entries) == 3
            with pytest.raises(ContractViolation, match="already consumed"):
                composition._admit_direct_workspace_selected_provider_catalogs(staged)
            digest = ContentDigest.of_bytes(b"fixture SDK product coordinates")
            coordinates = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.product.composition", digest
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.product.composition", digest
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "fixture.sdk.product.policy", digest
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "fixture.sdk.product.policy", digest
                ),
            )
            with composition._compose_direct_workspace_policy_host(
                staged, **coordinates
            ) as host:
                assert code._state(host).expected.product_runtime_bindings[0].registration \
                    is original.expected.registration
                from aware_local_service_runtime import (
                    InMemoryLocalOperationalStateStore,
                )
                from aware_workspace_runtime.materialization_graph_host_composition import (
                    WorkspaceMaterializationGraphBacking,
                )
                from aware_workspace_runtime.source_admission_catalog import (
                    WorkspaceV3GraphSourceCorrespondence,
                )
                from test_materialization_graph_planner import _composition

                planner, graph_selection, root_plans, *_ = _composition()
                graph_plan = await planner.plan(
                    selection_proposal=graph_selection,
                    requested_root_code_plans=root_plans,
                )
                graph_packages = tuple(sorted(
                    (node.package for node in graph_plan.graph.nodes),
                    key=lambda item: item.package_ref,
                ))
                graph_backing = WorkspaceMaterializationGraphBacking(
                    state_root=tmp_path / "graph-state",
                    repository_binding_ref="repository:fixed-product-test",
                    state_store=InMemoryLocalOperationalStateStore(),
                )
                epoch = staged.command.catalog_host.read_initial_epoch()
                expected = staged.command.catalog_host.read_initial_publication()
                with pytest.raises(
                    RuntimeError,
                    match="complete original graph-node correspondence required",
                ):
                    composition._compose_direct_workspace_current_graph_product_operations(
                        staged,
                        host,
                        plan_result=graph_plan,
                        planning_source=object(),
                        package_closure=graph_packages,
                        source_correspondences=(),
                        epoch=epoch,
                        expected_epoch=expected,
                        backing=graph_backing,
                    )
                forged = tuple(
                    object.__new__(WorkspaceV3GraphSourceCorrespondence)
                    for _ in graph_plan.graph_execution_binding.ordered_node_bindings
                )
                with pytest.raises(RuntimeError, match="foreign_graph_source_correspondence"):
                    composition._compose_direct_workspace_current_graph_product_operations(
                        staged,
                        host,
                        plan_result=graph_plan,
                        planning_source=object(),
                        package_closure=graph_packages,
                        source_correspondences=forged,
                        epoch=epoch,
                        expected_epoch=expected,
                        backing=graph_backing,
                    )
                assert bind_product_execution_origin(
                    host, original.expected.registration
                ) is not None
                from aware_code_semantic_contract_runtime import (
                    SemanticPackageCoordinate,
                )
                initial = staged.command.catalog_host.read_initial_publication()
                initial_epoch = staged.command.catalog_host.read_initial_epoch()
                with pytest.raises(
                    RuntimeError, match="committed successor graph pair required"
                ):
                    composition._compose_successor_graph_node_source_inputs(
                        staged,
                        host,
                        planning_source=object(),
                        package_closure=(SemanticPackageCoordinate(
                            "fixture.package", "environment", digest
                        ),),
                        correspondence=object.__new__(
                            WorkspaceV3GraphSourceCorrespondence
                        ),
                        epoch=initial_epoch,
                        expected_epoch=initial,
                    )
        with pytest.raises(ContractViolation, match="product contribution is unavailable"):
            read_selected_provider_product_contribution(product)
        assert closed_inside_parent == [product]


@pytest.mark.parametrize(
    ("scope", "ref"),
    (
        ("package", "network-example"),
        ("module", "main"),
        ("workspace", "Kernel"),
        ("repository", "demo"),
    ),
)
async def test_v3_root_plan_proposals_bind_original_scope_and_selected_sources(
    tmp_path, scope, ref,
):
    from aware_code_semantic_contract_runtime import (
        CodeSemanticMaterializationIntent,
        CodeSemanticRequiredResultProduct,
        ContentDigest,
        SemanticContractRef,
    )
    from aware_workspace_runtime.materialization_graph_planner import (
        WorkspaceSemanticRootCodePlan,
    )

    contract = SemanticContractRef(
        key="test.root.plan", version="1",
        schema_digest=ContentDigest.of_bytes(b"root plan input only"),
    )

    def plan(package_ref):
        intent = CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=("test.root",),
            requested_terminal_output_roles=("package_authority",),
            semantic_configuration_coordinate=None,
        )
        return WorkspaceSemanticRootCodePlan.create(
            package_ref=package_ref,
            code_intent=intent,
            required_result_products=(CodeSemanticRequiredResultProduct.create(
                role="package_authority", contract=contract,
            ),),
        )

    async with fixture(tmp_path) as (root, _, borrowed, _, _, _):
        _author_v3_repository(root)
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            selection = _selection(scope, ref)
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=selection,
            ) as bound:
                issuer = command.sources.declaration_scope_runtime
                refs = tuple(sorted((
                    issuer.inspect_inputs(source)[0].package.package_ref
                    for _, source in bound
                ), key=str.encode))
                plans = tuple(plan(package_ref) for package_ref in refs)
                composition._validate_direct_workspace_root_plan_closure(
                    command, selection=selection,
                    bound_roots=bound, root_plans=plans,
                )
                graph_selection = composition._derive_direct_workspace_graph_selection(
                    command,
                    selection=selection,
                    bound_roots=bound,
                    root_plans=plans,
                )
                assert graph_selection.proposal_digest != selection.proposal_digest
                assert {(
                    selector.selector_kind,
                    selector.selector_ref,
                ) for selector in graph_selection.selectors} == {
                    ("package", package_ref) for package_ref in refs
                }
                selected_sources = tuple(source for _, source in bound)
                with pytest.raises(RuntimeError, match="complete original graph source"):
                    composition._validate_direct_workspace_graph_source_closure(
                        bound_roots=bound,
                        selected_sources=selected_sources,
                        source_correspondences=(),
                    )
                with pytest.raises(
                    TypeError, match="original v3 graph source correspondence"
                ):
                    composition._validate_direct_workspace_graph_source_closure(
                        bound_roots=bound,
                        selected_sources=selected_sources,
                        source_correspondences=(object(),) * len(selected_sources),
                    )
                with pytest.raises(RuntimeError, match="root plans differ"):
                    composition._validate_direct_workspace_root_plan_closure(
                        command, selection=selection,
                        bound_roots=bound, root_plans=plans[:-1],
                    )
                with pytest.raises(RuntimeError, match="root plans differ"):
                    composition._validate_direct_workspace_root_plan_closure(
                        command, selection=selection,
                        bound_roots=bound,
                        root_plans=(plan("package:foreign@1"), *plans[1:]),
                    )
                if len(bound) > 1:
                    with pytest.raises(
                        RuntimeError, match="duplicate original graph selected source"
                    ):
                        composition._validate_direct_workspace_graph_source_closure(
                            bound_roots=bound,
                            selected_sources=(selected_sources[0],)
                            * len(selected_sources),
                            source_correspondences=(object(),)
                            * len(selected_sources),
                        )
                    with pytest.raises(RuntimeError, match="omit an original root"):
                        composition._validate_direct_workspace_graph_source_closure(
                            bound_roots=bound,
                            selected_sources=selected_sources[1:],
                            source_correspondences=(object(),)
                            * (len(selected_sources) - 1),
                        )
                    with pytest.raises(RuntimeError, match="root plan selection differs"):
                        composition._validate_direct_workspace_root_plan_closure(
                            command, selection=selection,
                            bound_roots=tuple(reversed(bound)), root_plans=plans,
                        )
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                composition._validate_direct_workspace_root_plan_closure(
                    command, selection=selection,
                    bound_roots=bound, root_plans=plans,
                )


async def test_fixed_v3_command_retains_real_declaration_and_selected_source(tmp_path):
    async with fixture(tmp_path) as (_, _, borrowed, _, _, _):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            sources = command.sources
            assert type(sources) is composition._DirectWorkspaceDeclarationSources
            assert sources.observation_runtime is not borrowed
            assert sources.exclusion._runtime is command.lifetime_runtime
            assert sources.exclusion._parent is command.invocation_parent
            closure = sources.declaration_scope_runtime.read_declaration_scope(
                sources.declaration_scope
            )
            sources.declaration_scope_runtime.validate_declaration_scope(
                sources.declaration_scope,
                expectation=sources.expectation,
                closure_digest=closure.closure_digest,
            )
            assert len(closure.scopes) == 2
            with composition._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="workspaces/network/aware.workspace.toml",
                module_id="main",
                package_id="example",
            ) as selected:
                binding = sources.declaration_scope_runtime.read_selected_package_source(
                    selected
                )
                assert binding.expectation.declaration == sources.expectation
                assert binding.expectation.closure_digest == closure.closure_digest
                assert [item.relative_path for item in binding.candidates.candidates] == [
                    "aware.example.toml", "body.bin"
                ]
                with sources.exclusion.mutation() as guard:
                    sources.declaration_scope_runtime.check_declaration_scope_locked(
                        sources.declaration_scope,
                        expectation=sources.expectation,
                        closure_digest=closure.closure_digest,
                        guard=guard,
                    )
                    sources.declaration_scope_runtime.check_selected_package_source_locked(
                        selected,
                        expectation=binding.expectation,
                        binding_digest=binding.binding_digest,
                        guard=guard,
                    )
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                sources.declaration_scope_runtime.read_selected_package_source(selected)
        with pytest.raises(SourceObservationUnavailable):
            sources.declaration_scope_runtime.read_declaration_scope(
                sources.declaration_scope
            )
        assert borrowed._session.authority_admitted


async def test_original_selected_participants_bind_complete_mixed_scope_and_source(
    tmp_path,
):
    from aware_code_semantic_contract_runtime.contracts import ContractViolation
    from aware_code_semantic_contract_runtime.selected_participant_scope import (
        CodeSelectedParticipant,
    )
    from aware_workspace_runtime.declaration_scope_admission import (
        WorkspaceSelectedPackageSource,
    )
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, _qualified_repository_with_unrelated_v1) as (
        root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            declaration = command.sources.declaration_scope
            with composition._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            ) as selected:
                view = composition._read_direct_workspace_selected_participants(
                    command, selected
                )
                assert view.root == CodeSelectedParticipant(
                    "consumer/aware.workspace.toml", "main", "home"
                )
                assert CodeSelectedParticipant(
                    "target/aware.workspace.toml", "main", "provider"
                ) in view.participants
                assert all(item.module_id != "legacy" for item in view.participants)
                assert view.profiles and view.relationships
                issuer.validate_selected_participant_view(
                    declaration, selected, view=view
                )
                with pytest.raises(RuntimeError, match="original v3 command assembly"):
                    composition._read_direct_workspace_selected_participants(
                        replace(command), selected
                    )
                with pytest.raises(SourceObservationUnavailable, match="root_differs"):
                    issuer.validate_selected_participant_view(
                        declaration, selected,
                        view=replace(view, root=CodeSelectedParticipant(
                            "target/aware.workspace.toml", "main", "provider"
                        )),
                    )
                with pytest.raises(ContractViolation, match="selected participant set differs"):
                    issuer.validate_selected_participant_view(
                        declaration, selected,
                        view=replace(view, relationships=()),
                    )
                with pytest.raises(SourceObservationUnavailable, match="foreign"):
                    issuer.validate_selected_participant_view(
                        declaration,
                        object.__new__(WorkspaceSelectedPackageSource),
                        view=view,
                    )
                module = root / "consumer/modules/main/aware.module.toml"
                module.write_text(module.read_text() + "\n# changed\n")
                with pytest.raises(SourceObservationUnavailable):
                    issuer.validate_selected_participant_view(
                        declaration, selected, view=view
                    )


async def test_v3_command_graph_node_session_retains_original_source_runtime(
    tmp_path, monkeypatch
):
    from aware_code_semantic_contract_runtime.selected_provider import (
        SelectedProviderInvocationClosure,
    )
    from aware_workspace_runtime import materialization_operation
    from aware_workspace_runtime.materialization_graph_coordinator import (
        WorkspaceSemanticMaterializationGraphCoordinator,
    )

    async with fixture(tmp_path) as (_, _, borrowed, _, _, _):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            factory = object.__new__(composition._DirectWorkspaceOriginFactory)
            factory._owner = command.lifetime_runtime
            factory._command = command
            factory._joint = command.catalog_host
            composition._ORIGIN_FACTORIES.add(factory)
            _, _, owner, execution, _ = await _executed_fixture(
                owner_override=command.lifetime_runtime
            )
            graph = _execution_state(execution)
            original_prepare = graph.ports.operation_preparer
            admission = object()
            checked_nodes = []

            def check_source(node, *, source_runtime, source_admission):
                assert source_runtime is command.sources.source_admission_runtime
                assert source_admission is admission
                checked_nodes.append(node)

            monkeypatch.setattr(
                materialization_operation,
                "_validate_graph_node_owner_source",
                check_source,
            )

            async def prepare(preparation):
                operation, operation_admission = await original_prepare(preparation)
                original_execute = operation._execute_graph_v2

                async def checked_execute(node):
                    with composition._command_owned_graph_node_source_session(
                        command, node, admission
                    ) as session:
                        session.validate()
                        with pytest.raises(
                            RuntimeError,
                            match="V4 graph prior output state is unavailable",
                        ):
                            session.read_current_output_state(
                                output_role="sdk_code_package_delta",
                                output_state_name="aware_dev_sdk",
                            )
                        with pytest.raises(
                            RuntimeError,
                            match="successor graph semantic source unavailable",
                        ):
                            with session.original_semantic_input_source():
                                pytest.fail("legacy source entered v3 graph input")
                        factory.validate_selected_graph_node_use(session)
                        with pytest.raises(RuntimeError, match="command_guard_foreign"):
                            factory.check_selected_graph_node_use_locked(session)
                        expected = command.sources.exclusion._expected
                        guard = command.lifetime_runtime.acquire_catalog_epoch_exclusion(
                            command.invocation_parent, expected=expected
                        )
                        try:
                            factory.check_selected_graph_node_use_locked(session)
                        finally:
                            command.lifetime_runtime.release_catalog_epoch_exclusion(
                                guard
                            )
                        node_state = materialization_operation._graph_node_admission_state(
                            node
                        )
                        plan = await operation._plan_resolver.resolve(
                            node_state.operation_admission
                        )
                        closure = SelectedProviderInvocationClosure(
                            plan.invocation, plan.input_bodies, plan.predecessor_body
                        )
                        with pytest.raises(RuntimeError, match="original node plan"):
                            factory.validate_selected_graph_node_use(
                                session, closure=closure
                            )
                        session.bind_execution_plan(plan)
                        factory.validate_selected_graph_node_use(
                            session, closure=closure
                        )
                        with pytest.raises(RuntimeError, match="original node plan"):
                            factory.validate_selected_graph_node_use(
                                session,
                                closure=SelectedProviderInvocationClosure(
                                    plan.invocation, plan.input_bodies,
                                    plan.predecessor_body,
                                    tuple(None for _ in plan.input_bodies),
                                ),
                            )
                        await asyncio.sleep(0)
                        session.validate()
                    with pytest.raises(RuntimeError, match="closed"):
                        session.validate()
                    with pytest.raises(RuntimeError, match="retired"):
                        factory.validate_selected_graph_node_use(session)
                    return await original_execute(node)

                operation._execute_graph_v2 = checked_execute
                return operation, operation_admission

            graph.ports = replace(graph.ports, operation_preparer=prepare)
            result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
                execution, owner=owner
            )
            assert result.status == "succeeded"
            assert checked_nodes
            assert len({id(node) for node in checked_nodes}) == 1
        with pytest.raises(RuntimeError, match="foreign or retired"):
            composition._validate_command_owned_graph_node_source(
                command, checked_nodes[0], admission
            )


async def test_fixed_v3_command_retains_and_retires_all_selected_roots(tmp_path):
    async with fixture(tmp_path) as (root, _, borrowed, _, _, _):
        _author_v3_repository(root)
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=_selection("repository", "demo")
            ) as bound:
                assert [root.semantic_package_name for root, _ in bound] == [
                    "kernel-example", "network-example", "network-nested"
                ]
                assert all(
                    issuer.read_selected_package_source(source).expectation.package_id
                    == root.package_id
                    for root, source in bound
                )
            for _, source in bound:
                with pytest.raises(SourceObservationUnavailable, match="foreign"):
                    issuer.read_selected_package_source(source)
        assert borrowed._session.authority_admitted


async def test_fixed_v3_root_failure_unwinds_every_selected_source(tmp_path):
    async with fixture(tmp_path) as (root, _, borrowed, _, _, _):
        _author_v3_repository(root)
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            with pytest.raises(RuntimeError, match="operation failed"):
                with (
                    composition._compose_direct_workspace_selected_materialization_roots(
                        command, selection=_selection("repository", "demo")
                    ) as bound
                ):
                    raise RuntimeError("operation failed")
            for _, source in bound:
                with pytest.raises(SourceObservationUnavailable, match="foreign"):
                    issuer.read_selected_package_source(source)


async def test_v3_command_failure_closes_owned_resources_and_keeps_borrowed(tmp_path):
    async with fixture(tmp_path) as (_, _, borrowed, _, _, _):
        with pytest.raises(RuntimeError, match="body failed"):
            with composition._compose_direct_workspace_command_resources(
                session=borrowed._session,
                store=borrowed._store,
                workspace_manifest_path="workspaces/network/aware.workspace.toml",
                source_rail="declaration_v3",
            ) as command:
                sources = command.sources
                raise RuntimeError("body failed")
        assert command.lifetime_runtime._closed
        assert sources.source_admission_runtime._closed
        assert sources.declaration_scope_runtime._closed
        assert sources.observation_runtime._closed
        assert borrowed._session.authority_admitted


async def test_v3_rejects_unregistered_staged_host_resources(tmp_path):
    async with fixture(tmp_path) as (_, _, borrowed, _, _, _):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            staged = composition._DirectWorkspaceStagedCommandResources(
                command, object(), ()
            )
            with pytest.raises(RuntimeError, match="original v3 Code/Workspace graph host"):
                composition._compose_direct_workspace_current_graph_planner(
                    staged,
                    object(),
                    epoch=object(),
                    expected_epoch=object(),
                    original_sources=(),
                    package_closure=(),
                    backing=object(),
                )
            with pytest.raises(RuntimeError, match="foreign, substituted or retired"):
                composition._assemble_direct_workspace_origin_factory(
                    staged,
                    composition_implementation=object(),
                    composition_configuration=object(),
                    policy_implementation=object(),
                    policy_configuration=object(),
                )
        with pytest.raises(ValueError, match="source rail"):
            with composition._compose_direct_workspace_command_resources(
                session=borrowed._session,
                store=borrowed._store,
                workspace_manifest_path="workspaces/network/aware.workspace.toml",
                qualified=True,
                source_rail="declaration_v3",
            ):
                pytest.fail("invalid mixed source rail entered")


async def test_v3_fixed_host_retains_original_selected_policy(tmp_path, real_sdk_factory):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_semantic_contract_runtime import (
        CodeSemanticContractCatalog, ContentDigest,
        SemanticConfigurationCoordinate, SemanticImplementationCoordinate,
    )
    from aware_sdk_contract_runtime_provider.catalog_contribution import (
        build_sdk_catalog_contribution,
    )
    from aware_workspace_runtime import WorkspaceSemanticMaterializationMembershipCatalog
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_sdk_factory,
            session=borrowed._session, store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as staged:
            contribution = build_sdk_catalog_contribution(staged.contribution)
            catalog = CodeSemanticContractCatalog.create(
                catalog_ref="fixture.sdk.v3", catalog_generation=1,
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
                dependency_planner_bindings=((
                    binding.dependency_planner_implementation,
                    binding.dependency_planner_configuration,
                    contribution.planner,
                ),),
            )
            digest = ContentDigest.of_bytes(b"fixture SDK v3 coordinates")
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
            with composition._compose_direct_workspace_policy_host(staged, **coords) as host:
                assert staged.command.sources.declaration_scope_runtime._planning_validator
                assert staged.command.sources.declaration_scope_runtime._authority_validator
                assert staged.command.sources.declaration_scope_runtime._dependency_validator
                with pytest.raises(RuntimeError, match="complete original root-plan"):
                    composition._compose_direct_workspace_current_graph_planner(
                        staged, host,
                        epoch=object(), expected_epoch=object(),
                    original_sources=(), package_closure=(), backing=object(),
                )
            with pytest.raises(RuntimeError, match="original v3 Code/Workspace root host"):
                class ForeignHost:
                    pass

                composition._compose_direct_workspace_selected_root_code_plans(
                    staged,
                    ForeignHost(),
                    epoch=object(),
                    expected_epoch=object(),
                    selection=_selection("package", "network-example"),
                    bound_roots=(),
                )
                from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
                    assemble_dependency_admission_consumer,
                )
                with composition._compose_direct_workspace_selected_package_source(
                    staged.command,
                    workspace_manifest_path="consumer/aware.workspace.toml",
                    module_id="main", package_id="home",
                ) as selected:
                    policy = code.produce_registry_policy(host, selected)
                    assert policy is not None
                    from aware_code_retained_registry_policy_runtime import (
                        operation_context as planning_contexts,
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
                        CodePortableSemanticContract, SemanticBody,
                        SemanticContractInvocation, SemanticValueCoordinate,
                        TypedEmptyCoordinate, selected_provider,
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
                    from aware_sdk_contract_runtime_provider.planning_stage import (
                        BINDING, MANIFEST_SOURCE_REF, MEANING_ROLE,
                        sdk_planning_body_codec_bindings,
                    )

                    issuer = staged.command.sources.declaration_scope_runtime
                    package, inventory = issuer.inspect_inputs(selected)
                    candidate = issuer.read_selected_package_source(selected).candidates
                    stage = staged.stage_runtime_bindings[0]
                    grant = code.validate_admitted_registry_policy(host, policy).grants[0]
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
                    manifest = staged.command.sources.observation_runtime.read_selected_package(
                        issuer._selected_record(selected).observation,
                        relative_path="aware.sdk.toml",
                    )
                    manifest_body = SemanticBody(
                        SemanticValueCoordinate(
                            "manifest_source", MANIFEST_SOURCE_REF,
                            "fixture:sdk-v3-manifest", ContentDigest.of_bytes(manifest),
                            len(manifest),
                        ), manifest,
                    )
                    request = RetainedSourcePlanningRequest(
                        manifest_body,
                        semantic_candidate_listing_body(candidate),
                        retained_projection_body(registry),
                        retained_projection_body(package),
                        retained_projection_body(inventory),
                    )
                    context = planning_contexts.begin_source_planning_operation(
                        host, policy, stage.registration, request
                    )
                    expected = planning_contexts.source_planning_expectation(host, context)
                    package_admission, inventory_admission = issuer.issue_source_planning_pair(
                        selected, context=context, expected=expected
                    )
                    origin = assemble_retained_input_admission_origin(host)
                    dependency_consumer = assemble_dependency_admission_consumer(host)
                    registry_admission = origin.issue_registry_package_admission(
                        context, package_admission
                    )
                    joined = origin.join(
                        context, registry_admission, package_admission,
                        inventory_admission,
                    )
                    origin.validate(joined)
                    planning_origin = planning.bind_planning_execution_origin(
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
                    execution = selected_provider.issue_selected_provider_execution(
                        stage.runtime, stage.registration,
                        selected_provider.SelectedProviderInvocationClosure(
                            invocation, bodies
                        ),
                        operation_context=context,
                    )
                    result = selected_provider.execute_selected_provider(
                        stage.runtime, execution
                    )
                    assert stage.runtime.owns_completion(result)
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
                        entry for entry in contribution.entries
                        if entry.profile_declaration.profile_ref != profile.profile_ref
                    )
                    delta = next(
                        product for product in authority_binding.result_product_contracts
                        if product.role == "sdk_code_package_delta"
                    )
                    intent = CodeSemanticMaterializationIntent.create(
                        operation_kind="materialize",
                        requested_semantic_root_refs=grant.owned_roots,
                        requested_terminal_output_roles=(delta.role,),
                        semantic_configuration_coordinate=None,
                    )
                    target = CodeSemanticPackagePlanningContext.create(
                        package=package.package,
                        package_family=registry.semantic_package_family,
                        package_role=registry.semantic_contract.role,
                        manifest_contract=MANIFEST_SOURCE_REF,
                        code_intent=intent,
                        required_result_products=(
                            CodeSemanticRequiredResultProduct.create(
                                role=delta.role, contract=delta.contract
                            ),
                        ),
                        required_semantic_provider_keys=(),
                    )
                    operation = await demand_runtime.execute_retained_dependency_demand(
                        source, context=target
                    )
                    demand_validator = demand_validation.retained_dependency_operation_validator(
                        host
                    )
                    expected_resolution = demand_validator.expectation(operation)
                    assert expected_resolution.demand_set.demands == ()
                    resolution, fulfillment, body = (
                        issuer.issue_empty_dependency_products(
                            operation,
                            inventory_admission=inventory_admission,
                            expected=expected_resolution,
                        )
                    )
                    record = issuer._dependency_resolution.records[resolution]
                    assert len(record.relationships) == 5
                    assert record.targets == ()
                    assert fulfillment in issuer._dependency_fulfillment.records
                    products = SemanticDependencyProductInputCodec().decode(
                        body.canonical_body
                    )
                    assert products.products == ()
                    assert len(products.declared_dependencies) == 5
                    admitted_products = dependency_consumer.admit_dependency_products(
                        operation, resolution, fulfillment, body=body
                    )
                    assert (
                        admitted_products.read_products().canonical_body
                        == body.canonical_body
                    )
                    (root / "consumer/modules/main/home/aware.sdk.toml").write_bytes(
                        b"changed"
                    )
                    with pytest.raises(SourceObservationUnavailable):
                        code.validate_admitted_registry_policy(host, policy)


def _live_cli_proposal(root):
    from aware_workspace_materialize_transport import (
        WorkspaceMaterializeCommandProposalV3,
    )

    return WorkspaceMaterializeCommandProposalV3.create(
        attempt_ref="workspace-materialize-attempt:live-generic",
        participant_checkout_root=str(root),
        workspace_manifest_name="consumer/aware.workspace.toml",
        package_address=("Consumer", "main", "home"),
        plan_only=True,
    )


def _live_cli_host_coordinates():
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )

    digest = ContentDigest.of_bytes(b"isolated generic command composition")
    return {
        "composition_implementation": SemanticImplementationCoordinate("fixture.generic", digest),
        "composition_configuration": SemanticConfigurationCoordinate("fixture.generic", digest),
        "policy_implementation": SemanticImplementationCoordinate("fixture.generic", digest),
        "policy_configuration": SemanticConfigurationCoordinate("fixture.generic", digest),
    }


async def test_live_cli_context_retains_exact_source_and_profile_with_unrelated_v1(tmp_path):
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, _qualified_repository_with_unrelated_v1) as (
        root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store,
            proposal=_live_cli_proposal(root),
        ) as (command, inspection, selected):
            assert selected is not None
            assert composition._COMMAND_ASSEMBLIES[command.lifetime_runtime][0] is command
            assert inspection.selected_root.package_id == "home"
            assert composition._resolve_direct_workspace_exact_provider_key(
                command, selected
            ) == "aware_environment"
            issuer = command.sources.declaration_scope_runtime
            issuer.read_selected_package_source(selected)
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES

        with pytest.raises(SourceObservationUnavailable):
            issuer.read_selected_package_source(selected)
        with pytest.raises(RuntimeError, match="command unavailable"):
            composition._resolve_direct_workspace_exact_provider_key(command, selected)


@pytest.mark.parametrize("changed_module", ("main", "legacy"))
async def test_live_cli_context_revalidates_after_consumer(tmp_path, changed_module):
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, _qualified_repository_with_unrelated_v1) as (
        root, _, _, borrowed, _, _,
    ):
        with pytest.raises(SourceObservationUnavailable):  # noqa: SIM117 - covers final currentness on exit
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session, store=borrowed._store,
                proposal=_live_cli_proposal(root),
            ) as (command, _inspection, selected):
                assert composition._resolve_direct_workspace_exact_provider_key(
                    command, selected
                ) == "aware_environment"
                path = root / f"consumer/modules/{changed_module}/aware.module.toml"
                path.write_text(path.read_text() + "\n# changed during consumer\n")
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES


async def test_borrowed_cli_selected_host_keeps_same_original_parent(
    tmp_path, request,
):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, _qualified_repository_with_unrelated_v1) as (
        root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store,
            proposal=_live_cli_proposal(root),
        ) as (command, _inspection, selected):
            parent = command.invocation_parent
            with composition.compose_direct_workspace_selected_host(
                factory_admission=request.getfixturevalue("real_environment_factory"),
                session=borrowed._session, store=borrowed._store,
                workspace_manifest_path="consumer/aware.workspace.toml",
                command_resources=command, **_live_cli_host_coordinates(),
            ) as host:
                assert host.staged.command is command
                assert host.staged.command.invocation_parent is parent
                with pytest.raises(RuntimeError, match="already has a selected host"), composition.compose_direct_workspace_selected_host(
                    factory_admission=request.getfixturevalue("real_environment_factory"),
                    session=borrowed._session, store=borrowed._store,
                    workspace_manifest_path="consumer/aware.workspace.toml",
                    command_resources=command, **_live_cli_host_coordinates(),
                ):
                    pytest.fail("a second selected host replaced the live original")
                policy = code.produce_registry_policy(host.code_host, selected)
                assert len(code.validate_admitted_registry_policy(host.code_host, policy).grants) == 1
            assert host.code_host not in code._HOSTS
            composition._require_live_direct_workspace_command(command)
            command.sources.declaration_scope_runtime.read_selected_package_source(selected)
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES


@pytest.mark.parametrize("substitution", ("copy", "store", "scope"))
async def test_borrowed_cli_host_refuses_substituted_command_resources(
    tmp_path, request, substitution,
):
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store,
            proposal=_live_cli_proposal(root),
        ) as (command, _inspection, _selected):
            with pytest.raises(RuntimeError, match="command unavailable|resources differ"):  # noqa: SIM117 - includes construction and cleanup
                with composition.compose_direct_workspace_selected_host(
                    factory_admission=request.getfixturevalue("real_environment_factory"),
                    session=borrowed._session,
                    store=object() if substitution == "store" else borrowed._store,
                    workspace_manifest_path=(
                        "target/aware.workspace.toml" if substitution == "scope"
                        else "consumer/aware.workspace.toml"
                    ),
                    command_resources=replace(command) if substitution == "copy" else command,
                    **_live_cli_host_coordinates(),
                ):
                    pytest.fail("substituted command reached the selected host")
            composition._require_live_direct_workspace_command(command)


async def test_live_cli_context_cancellation_retires_parent_and_selected_source(tmp_path):
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, qualified_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with pytest.raises(asyncio.CancelledError):  # noqa: SIM117 - proves cancellation cleanup on context exit
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session, store=borrowed._store,
                proposal=_live_cli_proposal(root),
            ) as (command, _inspection, selected):
                issuer = command.sources.declaration_scope_runtime
                raise asyncio.CancelledError()
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES
        with pytest.raises(SourceObservationUnavailable):
            issuer.read_selected_package_source(selected)


async def test_live_cli_async_mount_owns_session_until_consumer_finishes(tmp_path, monkeypatch):
    from test_dependency_scope_admission import fixture as sources

    async with sources(tmp_path, _qualified_repository_with_unrelated_v1) as (
        repository, _, _, _, _, _,
    ):
        pass
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    async with composition._compose_direct_workspace_cli_source(
        proposal=_live_cli_proposal(repository)
    ) as (command, _inspection, selected):
        assert composition._resolve_direct_workspace_exact_provider_key(
            command, selected
        ) == "aware_environment"
        session = command.sources.observation_runtime._session
        snapshot = session.current_snapshot
        assert snapshot is not None
        composition._require_live_direct_workspace_command(command)
    assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES


async def test_borrowed_cli_selected_execution_uses_original_source_join(tmp_path, request):
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime import (
        operation_context,
        planning_execution,
    )
    from aware_code_retained_registry_policy_runtime.operation_derivation import (
        RetainedSourcePlanningRequest,
    )
    from aware_code_retained_registry_policy_runtime.retained_input_admission import (
        assemble_retained_input_admission_origin,
    )
    from aware_code_semantic_contract_runtime import (
        SemanticContractInvocation,
        TypedEmptyCoordinate,
        selected_provider,
    )
    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        retained_projection_body,
    )
    from aware_code_semantic_contract_runtime.semantic_candidates import (
        semantic_candidate_listing_body,
    )
    from aware_environment_semantic_contract_runtime_provider.body_codecs import (
        environment_manifest_source_body,
    )
    from aware_environment_semantic_contract_runtime_provider.planning_stage import (
        BINDING,
        MEANING_ROLE,
        planning_body_codec_bindings,
    )
    from test_authority_derivation import arguments
    from test_dependency_scope_admission import fixture as sources

    def convergent_owner_declaration(root):
        _qualified_repository_with_unrelated_v1(root)
        path = root / "consumer/modules/main/aware.module.toml"
        # The existing policy-only fixture has deliberately unrelated meaning.
        # Execution requires the owner's independently derived manifest name.
        path.write_text(path.read_text().replace('value="home-demo"', 'value="home-story-environment"'))
        empty = 'dependency_targets = {state="present", value=[]}'
        mapping = (
            'dependency_targets = {state="present", value=['
            '{dependency_kind="module",dependency_ref="home",'
            'targets=[{scope={kind="dependency",workspace_handle="Target"},'
            'module_id="main",package_id="target"}],constraints=[]}]}'
        )
        # Author a real retained target occurrence before observation. This
        # proves planning input correspondence, not target result execution.
        original = path.read_text()
        path.write_text(original.replace(empty, mapping))
        target_path = root / "target/modules/main/aware.module.toml"
        target = original.split('[[packages]]', 1)[1]
        target = target.replace('id = "home"', 'id = "target"')
        target = target.replace('home/aware.environment.toml', 'target/aware.environment.toml')
        target = target.replace('value="home-story-environment"', 'value="target-environment"')
        target = target.replace('scope={kind="dependency", workspace_handle="Target"}', 'scope={kind="local"}')
        target = target.replace('value="home"', 'value="target"').replace('value=["home"]', 'value=["target"]')
        target_path.write_text(target_path.read_text() + '\n[[packages]]' + target)
        target_root = target_path.parent / "target"
        target_root.mkdir()
        (target_root / "aware.environment.toml").write_text(
            'aware=1\n[environment]\nhandle="target"\nmodules=["home"]\n'
        )

    async with sources(tmp_path, convergent_owner_declaration) as (
        root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_command_source(  # noqa: SIM117 - source must outlive borrowed host
            session=borrowed._session, store=borrowed._store,
            proposal=_live_cli_proposal(root),
        ) as (command, _inspection, selected):
            with composition.compose_direct_workspace_selected_host(
                factory_admission=request.getfixturevalue("real_environment_factory"),
                session=borrowed._session, store=borrowed._store,
                workspace_manifest_path="consumer/aware.workspace.toml",
                command_resources=command, **_live_cli_host_coordinates(),
            ) as host:
                stage = host.staged.stage_runtime_bindings[0]
                profile = stage.runtime.profile
                policy = code.produce_registry_policy(host.code_host, selected)
                grant = code.validate_admitted_registry_policy(host.code_host, policy).grants[0]
                issuer = command.sources.declaration_scope_runtime
                package, inventory = issuer.inspect_inputs(selected)
                source = issuer.read_selected_package_source(selected)
                raw = command.sources.observation_runtime.read_selected_package(
                    issuer._selected_record(selected).observation,
                    relative_path="aware.environment.toml",
                )
                owner_inputs, _ = arguments(raw)
                registry = replace(
                    owner_inputs["registry_package"],
                    fqn_prefix=grant.namespace, owned_semantic_root_refs=grant.owned_roots,
                    profile_ref=profile.profile_ref, profile_version=profile.version,
                    profile_digest=profile.digest, binding=BINDING,
                )
                inputs = RetainedSourcePlanningRequest(
                    environment_manifest_source_body(raw),
                    semantic_candidate_listing_body(source.candidates),
                    retained_projection_body(registry), retained_projection_body(package),
                    retained_projection_body(inventory),
                )
                context = operation_context.begin_source_planning_operation(
                    host.code_host, policy, stage.registration, inputs
                )
                expected = operation_context.source_planning_expectation(host.code_host, context)
                package_admission, inventory_admission = issuer.issue_source_planning_pair(
                    selected, context=context, expected=expected
                )
                origin = assemble_retained_input_admission_origin(host.code_host)
                registry_admission = origin.issue_registry_package_admission(context, package_admission)
                joined = origin.join(context, registry_admission, package_admission, inventory_admission)
                origin.validate(joined)
                planning_execution.bind_planning_execution_origin(
                    host.code_host, stage.registration, terminal_mode="runtime_completion"
                )
                bodies = tuple(sorted((
                    inputs.manifest_source, inputs.candidate_listing, inputs.registry_package,
                    inputs.package_context, inputs.declaration_inventory,
                ), key=lambda body: body.coordinate.role))
                invocation = SemanticContractInvocation(
                    invocation_ref="fixture:generic-cli-planning",
                    idempotency_key="fixture:generic-cli-planning",
                    profile_ref=profile.profile_ref, profile_digest=profile.digest,
                    target_package=package.package, operation_kind="materialize",
                    inputs=tuple(body.coordinate for body in bodies),
                    predecessor=TypedEmptyCoordinate(profile.providers[0].result_role.contract),
                    dependencies=(), body_codec_bindings=planning_body_codec_bindings(),
                    provider_bindings=(BINDING,), requested_output_roles=(MEANING_ROLE,),
                )
                execution = selected_provider.issue_selected_provider_execution(
                    stage.runtime, stage.registration,
                    selected_provider.SelectedProviderInvocationClosure(invocation, bodies),
                    operation_context=context,
                )
                completion = selected_provider.execute_selected_provider(stage.runtime, execution)
                assert stage.runtime.owns_completion(completion)
                assert host.staged.command is command
                composition._require_live_direct_workspace_command(command)
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES


# This closed AST capsule qualifies lookup mechanics only, not installation.
_INSTALLED_LOOKUP_REPAIR_SOURCE_SHA256 = "1c3971e7dfd32d87b69a9641a950b84637f15ea21486c9c923076e870b0943b4"
_INSTALLED_LOOKUP_REPAIR_CAPSULE_SHA256 = "fd41cb6c6c68f7489d3f3ebac8eed11d4dc6e03c0dd639aec9024bbdd31cb17e"


def _installed_lookup_repair_namespace():
    import sys
    from dataclasses import dataclass
    from threading import current_thread
    from types import ModuleType

    path = Path(__file__).resolve().parents[1] / "aware_workspace_runtime" / "direct_command_composition.py"
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == _INSTALLED_LOOKUP_REPAIR_SOURCE_SHA256
    names = {
        "_InstalledWorkspaceCommandContinuation", "_INSTALLED_CONTINUATION_SLOTS",
        "_INSTALLED_CONTINUATION_PROCESS", "_INSTALLED_CONTINUATION_RECORD",
        "_InstalledWorkspaceContinuationRecord", "_installed_continuation_values",
        "_publish_installed_continuation_phase", "_hold_installed_continuation",
        "_require_installed_continuation_record",
    }
    tree = ast.parse(body)
    nodes = []
    for node in tree.body:
        name = getattr(node, "name", None)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in names:
            nodes.append(node)
    assert len(nodes) == len(names)
    capsule = ast.Module(body=nodes, type_ignores=[])
    assert hashlib.sha256(ast.dump(capsule, include_attributes=False).encode()).hexdigest() == (
        _INSTALLED_LOOKUP_REPAIR_CAPSULE_SHA256
    )
    module_name = "_workspace_installed_lookup_repair_capsule"
    assert module_name not in sys.modules
    module = ModuleType(module_name)
    namespace = module.__dict__
    namespace.update(os=os, current_thread=current_thread, dataclass=dataclass)
    sys.modules[module_name] = module
    try:
        exec(compile(capsule, str(path), "exec"), namespace)  # noqa: S102 - reviewed finite AST capsule
    finally:
        del sys.modules[module_name]
    return namespace


@pytest.fixture
def installed_lookup_repair():
    from threading import current_thread

    namespace = _installed_lookup_repair_namespace()
    holder = object.__new__(namespace["_InstalledWorkspaceCommandContinuation"])
    references = tuple(object() for _ in range(6))
    values = (*references, "opening")
    for descriptor, value in zip(namespace["_INSTALLED_CONTINUATION_SLOTS"], values, strict=True):
        descriptor.__set__(holder, value)
    record = namespace["_InstalledWorkspaceContinuationRecord"](
        holder, os.getpid(), current_thread(), references,
        (object(), object()), b"local-lookup-proof", (object(),),
        source_context=object(), host_context=object(), selected_host=object(),
        source_opened=True, host_opened=True,
    )
    namespace["_INSTALLED_CONTINUATION_RECORD"] = record
    custody = (record.references, record.resources, record.pair_calls, record.source_context,
               record.host_context, record.selected_host)
    try:
        yield namespace, holder, record, values, custody
    finally:
        # Local objects only: no owner callback, borrowed disposal or installed gate.
        namespace["_INSTALLED_CONTINUATION_RECORD"] = None
        namespace.clear()


def _assert_installed_lookup_hold(proof):
    namespace, holder, record, values, custody = proof
    assert namespace["_INSTALLED_CONTINUATION_RECORD"] is record
    assert record.held is True
    assert record.phase == "held"
    retained = (record.references, record.resources, record.pair_calls, record.source_context,
                record.host_context, record.selected_host)
    assert all(actual is original for actual, original in zip(retained, custody, strict=True))
    assert record.source_opened and record.host_opened
    assert not record.source_closed and not record.host_closed
    assert not record.close_started and not record.release_started
    # Restore every original slot, including phase; this cannot undo local hold.
    for descriptor, value in zip(namespace["_INSTALLED_CONTINUATION_SLOTS"], values, strict=True):
        descriptor.__set__(holder, value)
    with pytest.raises(RuntimeError, match="changed or held"):
        namespace["_require_installed_continuation_record"](holder)
    assert record.held is True
    assert all(actual is original for actual, original in zip(
        (record.references, record.resources, record.pair_calls, record.source_context,
         record.host_context, record.selected_host), custody, strict=True,
    ))


@pytest.mark.parametrize("slot_index", range(7))
def test_installed_lookup_missing_slot_holds_after_restoration(installed_lookup_repair, slot_index):
    namespace, holder, _, _, _ = installed_lookup_repair
    namespace["_INSTALLED_CONTINUATION_SLOTS"][slot_index].__delete__(holder)
    with pytest.raises(AttributeError):
        namespace["_require_installed_continuation_record"](holder)
    _assert_installed_lookup_hold(installed_lookup_repair)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("checkpoint", ["slot_read", "structure"])
def test_installed_lookup_interruption_holds_after_restoration(installed_lookup_repair, error_type, checkpoint):
    import sys

    namespace, holder, _, _, _ = installed_lookup_repair
    lookup = namespace["_require_installed_continuation_record"]
    tree = ast.parse((Path(__file__).resolve().parents[1] / "aware_workspace_runtime" / "direct_command_composition.py").read_bytes())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == lookup.__name__)
    protected = next(node for node in function.body[2].body if isinstance(node, ast.Try))
    target = (
        protected.body[1].lineno if checkpoint == "slot_read"
        else protected.body[2].test.values[0].lineno
    )
    assert target in {line for _, _, line in lookup.__code__.co_lines()}
    fired = False
    original_trace = sys.gettrace()

    def interrupt(frame, event, argument):
        nonlocal fired
        if not fired and event == "line" and frame.f_code is lookup.__code__ and frame.f_lineno == target:
            fired = True
            raise error_type("lookup checkpoint interrupted")
        return interrupt

    try:
        sys.settrace(interrupt)
        with pytest.raises(error_type, match="lookup checkpoint interrupted"):
            lookup(holder)
    finally:
        sys.settrace(original_trace)
    assert fired
    _assert_installed_lookup_hold(installed_lookup_repair)


def test_installed_lookup_unknown_holder_is_behavior_free(installed_lookup_repair):
    namespace, holder, record, _, custody = installed_lookup_repair
    calls = []

    class Hostile:
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError("foreign attribute dispatch")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality dispatch")

        def __repr__(self):
            calls.append("repr")
            raise AssertionError("foreign repr dispatch")

    with pytest.raises(TypeError, match="original enrolled"):
        namespace["_require_installed_continuation_record"](Hostile())
    assert calls == []
    assert record.held is False
    assert record.phase == "opening"
    assert namespace["_require_installed_continuation_record"](holder) is record
    assert all(actual is original for actual, original in zip(
        (record.references, record.resources, record.pair_calls, record.source_context,
         record.host_context, record.selected_host), custody, strict=True,
    ))


# Proposed source-first footprint: static order/custody and local rejection only.
# No enrolled installation, original Code resolver, source or factory is run.
def _installed_source_first_nodes():
    path = (
        Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
        / "direct_command_composition.py"
    )
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == _INSTALLED_LOOKUP_REPAIR_SOURCE_SHA256
    return path, {getattr(node, "name", None): node for node in ast.parse(body).body}


def _installed_source_first_namespace(proof):
    namespace = proof[0]
    path, nodes = _installed_source_first_nodes()
    selected = [nodes[name] for name in (
        "_require_installed_workspace_continuation_binding",
        "_read_installed_workspace_provider_key",
    )]
    # Missing owner globals deliberately stay missing: every diagnostic must
    # reject before a live-command/source/resolver entrance could be reached.
    capsule = ast.Module(body=selected, type_ignores=[])
    exec(compile(capsule, str(path), "exec"), namespace)  # noqa: S102
    return namespace


def test_installed_source_first_orders_original_source_binding_before_full_resources():
    _, nodes = _installed_source_first_nodes()
    composer = nodes["_compose_installed_workspace_materialize_command"]
    calls = {}
    for node in ast.walk(composer):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.setdefault(node.func.id, []).append(node.lineno)
    ordered = (
        "read_source_resources", "_compose_direct_workspace_command_source",
        "bind_command", "read_resources", "compose_direct_workspace_selected_host",
    )
    positions = [calls[name] for name in ordered]
    assert all(len(position) == 1 for position in positions)
    assert [position[0] for position in positions] == sorted(
        position[0] for position in positions
    )
    readback = nodes["_read_installed_workspace_provider_key"]
    read_calls = [node.func.id for node in ast.walk(readback)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert read_calls.count("_resolve_direct_workspace_exact_provider_key") == 1
    assert read_calls.count("_require_installed_workspace_continuation_binding") == 2
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        for node in ast.walk(readback)
    )


def test_installed_source_first_retains_owner_returns_before_local_qualification():
    _, nodes = _installed_source_first_nodes()
    composer = nodes["_compose_installed_workspace_materialize_command"]
    assignments = {
        target.attr: node.value
        for node in ast.walk(composer) if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
        and target.value.id == "record" and isinstance(node.value, ast.Call)
    }
    for field, reader in (
        ("source_resources", "read_source_resources"),
        ("resources", "read_resources"),
    ):
        assert isinstance(assignments[field].func, ast.Name)
        assert assignments[field].func.id == reader
    for field in ("source_result", "selected_host"):
        assert isinstance(assignments[field].func, ast.Attribute)
        assert assignments[field].func.attr == "__enter__"
    assert "source_resources" in {
        node.target.id for node in nodes["_InstalledWorkspaceContinuationRecord"].body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }


@pytest.mark.parametrize("kind", ["none", "object", "copied", "hostile"])
def test_installed_source_first_unknown_readback_never_touches_owner(
    installed_lookup_repair, kind,
):
    namespace = _installed_source_first_namespace(installed_lookup_repair)
    holder, record, values = installed_lookup_repair[1:4]
    calls = []

    class Hostile:
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError("foreign attribute dispatch")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality dispatch")

    if kind == "copied":
        foreign = object.__new__(namespace["_InstalledWorkspaceCommandContinuation"])
        for descriptor, value in zip(
            namespace["_INSTALLED_CONTINUATION_SLOTS"], values, strict=True,
        ):
            descriptor.__set__(foreign, value)
    else:
        foreign = (
            None if kind == "none" else object() if kind == "object" else Hostile()
        )
    with pytest.raises(TypeError, match="original enrolled"):
        namespace["_read_installed_workspace_provider_key"](
            foreign, original_child_delivery=record.references[0],
            original_installed_composition=record.references[1],
            original_command=record.references[2],
        )
    assert calls == []
    assert record.held is False and record.phase == "opening"
    assert namespace["_require_installed_continuation_record"](holder) is record


@pytest.mark.parametrize("field", ["delivery", "composition", "command"])
def test_installed_source_first_mismatched_readback_terminally_holds_without_owner(
    installed_lookup_repair, field,
):
    namespace = _installed_source_first_namespace(installed_lookup_repair)
    holder, record = installed_lookup_repair[1:3]
    originals = dict(zip(
        ("delivery", "composition", "command"), record.references[:3], strict=True,
    ))
    originals[field] = object()
    with pytest.raises(RuntimeError, match="command binding differs"):
        namespace["_read_installed_workspace_provider_key"](
            holder, original_child_delivery=originals["delivery"],
            original_installed_composition=originals["composition"],
            original_command=originals["command"],
        )
    _assert_installed_lookup_hold(installed_lookup_repair)
