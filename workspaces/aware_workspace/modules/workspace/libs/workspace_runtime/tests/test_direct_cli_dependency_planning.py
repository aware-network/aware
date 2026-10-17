"""Original Workspace/Code multi-product planning with local fixture owners.

The two factories own their source interpretation and demands. This proves no
installed API/Ontology export or dependency-bearing publication.
"""

import re
from contextlib import ExitStack
from dataclasses import dataclass, fields, replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticBody,
    SemanticConfigurationCoordinate,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import selected_provider as selected_runtime
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DeclarationTargetInventoryCodec,
    DependencyPlanningInputCodec,
    PackageContextInputCodec,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputProducerDeclaration,
    SemanticInputSourceContract,
)

# isort: split

from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.direct_cli_product_planning import (
    plan_direct_cli_selected_product,
)
from aware_workspace_runtime.semantic_dependency_graph_codec import (
    decode_workspace_semantic_materialization_graph_plan_result,
)

# isort: split

from test_dependency_scope_admission import fixture as sources
from test_materialization_graph_planner import _code_binding, _contract
from test_observed_semantic_issuers import PROVIDER, occurrence

ROOT_KEY = "proof-consumer-product"
SUPPLIER_KEY = "proof-supplier-product"
RAW = _contract("proof.raw")


class PlanningOnlyCodec:
    def __init__(self, contract):
        self.contract = contract
        self.implementation = SemanticImplementationCoordinate(
            "proof.terminal-codec", ContentDigest.of_bytes(b"never used during planning"),
        )

    def encode(self, value):
        raise AssertionError("planning must not encode a terminal product")

    def decode(self, body):
        raise AssertionError("planning must not decode a terminal product")


class Provider:
    def __init__(self, declaration):
        self.declaration = declaration

    async def derive(self, step):
        raise AssertionError("planning must not execute the terminal owner")

    def execute(self, step, value):
        raise AssertionError("planning must not execute the terminal owner")

    def input_closure(self, value):
        raise AssertionError("planning must not assemble terminal input")


@dataclass(frozen=True, slots=True)
class Catalog:
    original: object
    entries: tuple
    executables: tuple
    planner: object


def _owner_factory(key, calls):
    template = _code_binding("example", key)
    declaration = replace(template.profile_declaration.providers[0], output_roles=())
    profile = replace(template.profile_declaration, providers=(declaration,), terminal_output_roles=())
    artifact = canonical_json_bytes({"owner": key})
    configuration = canonical_json_bytes({"configuration": key})
    binding = ProviderExecutionBinding(
        key,
        SemanticImplementationCoordinate(key, ContentDigest.of_bytes(artifact)),
        SemanticConfigurationCoordinate(key, ContentDigest.of_bytes(configuration)),
    )
    values = {f.name: getattr(template, f.name) for f in fields(template) if f.name != "binding_digest"}
    values.update(
        package_families=("example",), package_roles=("example",),
        profile_declaration=profile, provider_execution_bindings=(binding,),
        dependency_planner_implementation=SemanticImplementationCoordinate(key + ".planner", ContentDigest.of_bytes(key.encode())),
        dependency_planner_configuration=binding.configuration,
        result_product_contracts=tuple(sorted((
            CodeSemanticRequiredResultProduct.create(role=role.role, contract=role.contract)
            for role in (declaration.result_role, declaration.effect_role)
        ), key=lambda role: role.role)),
    )
    entry = CodeSemanticMaterializationProfileBinding.create(**values)

    class Planner:
        def __init__(self, usage):
            self.usage = usage

        async def plan(self, *, package, intent, selected_match, planning_input):
            calls.append(("plan", package.package_ref, key))
            assert selected_match.selected_binding == entry
            demands = tuple(
                SemanticDependencyDemand.create(
                    consumer_semantic_role=role,
                    authored_dependency_kind=dependency.dependency_kind,
                    authored_dependency_ref=dependency.dependency_ref,
                    target_constraints=dependency.target_constraints,
                    required_result_role="result", result_product_contract=declaration.result_role.contract,
                    target_intent=CodeSemanticMaterializationIntent.create(
                        operation_kind="materialize",
                        requested_semantic_root_refs=dependency.targets[0].semantic_root_refs,
                        requested_terminal_output_roles=("result",), semantic_configuration_coordinate=None,
                    ), cardinality="required",
                )
                for dependency in planning_input.dependencies for role in ("first", "second")
                if self.usage[package.package_ref, planning_input.source_identity_digest.value]
            )
            return SemanticDependencyDemandSet.create(
                package=package, intent=intent, profile_ref=profile.profile_ref,
                profile_digest=profile.digest, contract_profile_binding_digest=entry.binding_digest,
                planner_implementation_ref=entry.dependency_planner_implementation.implementation_ref,
                planner_implementation_digest=entry.dependency_planner_implementation.closure_digest,
                planner_configuration=entry.dependency_planner_configuration,
                demands=tuple(sorted(demands, key=lambda demand: demand.demand_digest.value)),
            )

    def producer(value, usage):
        calls.append(("source", value.package_identity.package.package_ref, key))
        inventory = DeclarationTargetInventoryCodec().decode(value.context_bodies[0].canonical_body)
        context = PackageContextInputCodec().decode(value.context_bodies[1].canonical_body)
        assert context.package == inventory.package == value.package_identity.package
        assert inventory.source_identity_digest == context.source_identity_digest
        # Only this fixture owner interprets its authored feature, not Workspace.
        used = any(b"requires:target" in source.canonical_body for source in value.sources)
        usage[context.package.package_ref, context.source_identity_digest.value] = used
        dependencies = tuple(
            SemanticAuthoredDependency(item.dependency_kind, item.dependency_ref, item.targets, item.target_constraints)
            for item in inventory.entries
        )
        wire = DependencyPlanningInputCodec().encode(SemanticDependencyPlanningInput(
            context.package, context.source_identity_digest, dependencies,
        ))
        return SemanticBody(SemanticValueCoordinate(
            "planning_input", DependencyPlanningInputCodec.contract, key + ":planning",
            ContentDigest.of_bytes(wire), len(wire),
        ), wire)

    def factory():
        # Model meaning is local to this acquired factory operation, not a
        # cross-command cache or a Workspace interpretation of authored features.
        usage = {}
        provider = Provider(declaration)
        contracts = {
            *(item.contract for item in profile.inputs), declaration.result_role.contract,
            declaration.transition_contract, declaration.effect_contract,
        }
        runtime = SemanticContractRuntime(profile, {key: provider}, {
            contract: PlanningOnlyCodec(contract) for contract in contracts
        })

        def catalog(original):
            admitted = read_selected_provider_product_contribution(original)
            return Catalog(original, (entry,), ((binding.implementation, binding.configuration, admitted.executable),), Planner(usage))

        def produce(value):
            return producer(value, usage)

        return selected_runtime._SelectedProviderFactoryProduct(
            runtime, provider, binding, provider.execute, provider.input_closure,
            artifact, configuration, catalog_contribution_producer=catalog,
            planning_input_declaration=SemanticInputProducerDeclaration(
                key + ".source", profile.profile_ref, binding.implementation, binding.configuration,
                (SemanticInputSourceContract("raw", RAW),), "planning_input", DependencyPlanningInputCodec.contract,
                context_contracts=(
                    SemanticInputContextContract("declaration_inventory", DeclarationTargetInventoryCodec.contract),
                    SemanticInputContextContract("package_context", PackageContextInputCodec.contract),
                ),
            ), planning_input_producer=produce,
        )

    admission = selected_runtime._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory,
    )
    return admission, profile


def _repository(root, profiles, *, used=True, shared=False):
    module = root / "consumer/modules/main"
    supplier_key = ROOT_KEY if shared else SUPPLIER_KEY
    mapping = (
        '[{dependency_kind="module",dependency_ref="target",'
        'targets=[{scope={kind="local"},module_id="main",package_id="supplier"}],'
        f'constraints=[{{constraint_kind="semantic_provider_key",constraint_value="{supplier_key}"}}]}}]'
    )
    parts = ["aware=3\n"]
    for package, key in (("consumer", ROOT_KEY), ("supplier", supplier_key)):
        directory = module / package
        directory.mkdir()
        (directory / "aware.example.toml").write_text(f'package_name="{package}"\n')
        (directory / "source.aware").write_bytes(b"requires:target" if package == "consumer" and used else b"leaf")
        semantic = occurrence(package, mapping if package == "consumer" else "[]")
        semantic = semantic.replace('value={module_id="main",', 'value={scope={kind="local"},module_id="main",')
        semantic = semantic.replace('package_id="provider"', f'package_id="provider_{package}"')
        if package == "supplier" and shared:
            semantic = semantic.replace('package_id="provider_supplier"', 'package_id="provider_consumer"')
        parts.append(f'[[packages]]\nid="{package}"\nkind="example"\nmanifest="{package}/aware.example.toml"\n' + semantic)
        if package == "supplier" and shared:
            continue
        provider = module / f"provider_{package}"
        provider.mkdir()
        (provider / "pyproject.toml").write_bytes(b"fixture owner distribution")
        declaration = PROVIDER.replace('id="provider"', f'id="provider_{package}"').replace(
            'manifest="provider/pyproject.toml"', f'manifest="provider_{package}/pyproject.toml"',
        ).replace('provider_key="demo"', f'provider_key="{key}"')
        profile = profiles[key]
        declaration = re.sub(r"profiles=\[.*?\n\]", (
            'profiles=[{stage="graph_product",profile_ref="' + profile.profile_ref
            + '",profile_version="' + profile.version + '",profile_digest="'
            + profile.digest.to_wire() + '"}]'
        ), declaration, flags=re.DOTALL)
        parts.append(declaration)
    (module / "aware.module.toml").write_text("\n".join(parts))


@pytest.fixture(scope="module")
def owners():
    calls = []
    admitted = {key: _owner_factory(key, calls) for key in (ROOT_KEY, SUPPLIER_KEY)}
    try:
        yield admitted, calls
    finally:
        for admission, _ in admitted.values():
            state = selected_runtime._factory_state(admission)
            if selected_runtime._FACTORY_PROVIDER_KEYS.get(state.provider_key) is admission:
                del selected_runtime._FACTORY_PROVIDER_KEYS[state.provider_key]
            if selected_runtime._FACTORY_REFS.get(state.factory_ref) is admission:
                del selected_runtime._FACTORY_REFS[state.factory_ref]
            selected_runtime._FACTORIES.pop(id(admission), None)


async def _plan(tmp_path, owners, monkeypatch, *, used=True, after_sources=None, include_supplier=True, shared=False):
    admitted, calls = owners
    calls.clear()
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "local-state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    async with sources(tmp_path, lambda root: _repository(root, profiles, used=used, shared=shared)) as (root, _, _, borrowed, _, _):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:dependency-plan", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer"), plan_only=True,
        )
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, selected), ExitStack() as retained:
            participants = (selected,)
            if include_supplier:
                supplier = retained.enter_context(composition._compose_direct_workspace_selected_package_source(
                    command, workspace_manifest_path="consumer/aware.workspace.toml",
                    module_id="main", package_id="supplier",
                ))
                participants += (supplier,)
            with local.compose_direct_cli_selected_product(
                command, selected, participating_sources=participants,
            ) as product:
                if after_sources is not None:
                    after_sources(root, command, selected, product)
                before = set(planning._SOURCES)
                try:
                    return await plan_direct_cli_selected_product(command, selected, product)
                finally:
                    assert set(planning._SOURCES) == before


async def test_two_owner_factories_two_demand_edges_one_supplier(tmp_path, owners, monkeypatch):
    result = await _plan(tmp_path, owners, monkeypatch)
    assert len(result.plan.graph.nodes) == 2
    assert len(result.plan.graph.edges) == 2
    assert sorted(owners[1]) == sorted([
        (kind, "package:" + package + "@1.0", key)
        for kind in ("source", "plan")
        for package, key in (("consumer", ROOT_KEY), ("supplier", SUPPLIER_KEY))
    ])
    decoded = decode_workspace_semantic_materialization_graph_plan_result(result.wire, expected=result.plan)
    assert decoded.graph.graph_digest == result.plan.graph.graph_digest
    import sqlite3

    database, = (tmp_path / "local-state").rglob("heads.sqlite3")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM local_operational_state").fetchone() == (0,)


async def test_unused_declaration_creates_no_semantic_edge(tmp_path, owners, monkeypatch):
    result = await _plan(tmp_path, owners, monkeypatch, used=False, include_supplier=False)
    assert len(result.plan.graph.nodes) == 1 and result.plan.graph.edges == ()
    assert not any(kind == "plan" and key == SUPPLIER_KEY for kind, _, key in owners[1])


async def test_extra_unused_original_source_is_not_silently_authorized(tmp_path, owners, monkeypatch):
    with pytest.raises(RuntimeError, match="reachable graph packages differ"):
        await _plan(tmp_path, owners, monkeypatch, used=False)


async def test_shared_factory_is_loaded_once_for_both_original_packages(tmp_path, owners, monkeypatch):
    loaded = []

    def inspect(_root, _command, _selected, product):
        assert len(product.host.staged.product_contributions) == 1
        loaded.extend(item.provider_key for item in product.participants)

    result = await _plan(tmp_path, owners, monkeypatch, after_sources=inspect, shared=True)
    assert len(result.plan.graph.nodes) == 2 and len(result.plan.graph.edges) == 2
    assert loaded == [ROOT_KEY, ROOT_KEY]
    assert len(owners[1]) == 4 and all(key == ROOT_KEY for _, _, key in owners[1])


async def test_missing_original_supplier_cannot_return_plan(tmp_path, owners, monkeypatch):
    with pytest.raises((ContractViolation, RuntimeError)):
        await _plan(tmp_path, owners, monkeypatch, include_supplier=False)


async def test_supplier_source_change_refuses_and_clears_planning(tmp_path, owners, monkeypatch):
    original = planning.execute_product_planning_input

    async def mutate(*args, **kwargs):
        result = await original(*args, **kwargs)
        if kwargs["expected"].package_identity.package.package_ref == "package:supplier@1.0":
            # The callback is armed with the actual disposable repository path.
            mutation[0]()
        return result

    mutation = []

    def arm(root, *_):
        mutation.append(lambda: (root / "consumer/modules/main/supplier/source.aware").write_bytes(b"changed"))

    monkeypatch.setattr(planning, "execute_product_planning_input", mutate)
    with pytest.raises((SourceObservationUnavailable, ContractViolation)):
        await _plan(tmp_path, owners, monkeypatch, after_sources=arm)


async def test_duplicate_participant_is_rejected_before_factory_intake(tmp_path, owners, monkeypatch):
    def duplicate(_root, command, selected, _product):
        with (
            pytest.raises(ContractViolation, match="unique original participants"),
            local.compose_direct_cli_selected_product(command, selected, participating_sources=(selected, selected)),
        ):
            raise AssertionError("duplicate participant admitted")

    await _plan(tmp_path, owners, monkeypatch, used=False, after_sources=duplicate, include_supplier=False)


async def test_foreign_original_source_rejects_without_factory_contact(tmp_path, owners, monkeypatch):
    def foreign(_root, command, selected, _product):
        sources = command.sources
        with composition._compose_direct_workspace_command_resources(
            session=sources.observation_runtime._session, store=sources.observation_runtime._store,
            workspace_manifest_path="consumer/aware.workspace.toml", source_rail="declaration_v3",
        ) as other, composition._compose_direct_workspace_selected_package_source(
            other, workspace_manifest_path="consumer/aware.workspace.toml", module_id="main", package_id="supplier",
        ) as foreign_source, monkeypatch.context() as patch:
            calls = []

            def forbidden(key):
                calls.append(key)
                raise AssertionError("foreign source reached factory intake")

            patch.setattr(local, "admit_installed_semantic_stage_factory", forbidden)
            with (
                pytest.raises(SourceObservationUnavailable),
                local.compose_direct_cli_selected_product(
                    command, selected, participating_sources=(selected, foreign_source),
                ),
            ):
                raise AssertionError("foreign source admitted")
            assert calls == []
        composition._require_live_direct_workspace_command(command)

    result = await _plan(tmp_path, owners, monkeypatch, after_sources=foreign)
    assert len(result.plan.graph.edges) == 2


async def test_participant_change_during_owner_execution_refuses(tmp_path, owners, monkeypatch):
    products = []
    original = planning.execute_product_planning_input

    async def change(*args, **kwargs):
        result = await original(*args, **kwargs)
        product = products[0]
        object.__setattr__(product, "participants", product.participants[:1])
        return result

    monkeypatch.setattr(planning, "execute_product_planning_input", change)
    with pytest.raises(ContractViolation, match="participant set changed"):
        await _plan(tmp_path, owners, monkeypatch, after_sources=lambda _r, _c, _s, p: products.append(p))
    assert not any(kind == "source" and key == SUPPLIER_KEY for kind, _, key in owners[1])


async def test_foreign_participant_metadata_never_hashes_or_compares(tmp_path, owners, monkeypatch):
    calls = []

    class Foreign:
        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign metadata hashed")

        def __eq__(self, other):
            calls.append("eq")
            raise AssertionError("foreign metadata compared")

    def change(_root, _command, _selected, product):
        root, supplier = product.participants
        forged = local.DirectCLIProductParticipant(
            supplier.source, supplier.provider_key, Foreign(), supplier.policy, supplier.contribution,
        )
        object.__setattr__(product, "participants", (root, forged))

    with pytest.raises(ContractViolation, match="complete original planning participants"):
        await _plan(tmp_path, owners, monkeypatch, after_sources=change)
    assert calls == [] and owners[1] == []


async def test_selected_target_verification_mints_no_resolution_admission(tmp_path, owners, monkeypatch):
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign target behavior executed")

    def verify(_root, command, source, product):
        issuer = command.sources.declaration_scope_runtime
        context, inventory = issuer.inspect_inputs(source)
        assert not issuer._selected_targets and not issuer._target_records
        relationship, = inventory.entries
        target, = relationship.targets
        validator = issuer.bind_original_graph_target_validator(tuple(
            item.source for item in product.participants
        ))
        kwargs = {"package": context.package, "dependency_kind": relationship.dependency_kind, "dependency_ref": relationship.dependency_ref}
        validator.validate_target(**kwargs, target=target)
        assert not issuer._selected_targets and not issuer._target_records
        with pytest.raises(SourceObservationUnavailable):
            validator.validate_target(**kwargs, target=replace(target, semantic_root_refs=("wrong",)))
        with pytest.raises(SourceObservationUnavailable, match="coordinates_required"):
            validator.validate_target(**kwargs, target=Foreign())
        assert calls == []

    result = await _plan(tmp_path, owners, monkeypatch, after_sources=verify)
    assert len(result.plan.graph.edges) == 2


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_original_target_retainer_substitution_never_dispatches(tmp_path, owners, monkeypatch, mode):
    calls = []

    def substitute(_root, command, _source, _product):
        kind = type(command.sources.declaration_scope_runtime)
        original = kind._retain_targets

        def hostile(self, source, addresses):
            calls.append(source)
            if mode == "restore":
                monkeypatch.setattr(kind, "_retain_targets", original)
            if mode == "raise":
                raise AssertionError("foreign target retainer executed")
            return ()

        monkeypatch.setattr(kind, "_retain_targets", hostile)

    with pytest.raises(ContractViolation, match="source retainer changed"):
        await _plan(tmp_path, owners, monkeypatch, used=False, include_supplier=False, after_sources=substitute)
    assert calls == [] and owners[1] == []
