"""Original Code/Workspace admissions; local owner/store, not installation.

No demand, source, inventory or resolution validator is replaced. The test
owner declares and executes its own contracts; it is not Meta or Ontology.
"""

import asyncio
from contextlib import ExitStack
from dataclasses import dataclass, replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as code
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime import planning_execution as planning
from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
    assemble_dependency_admission_consumer,
)
from aware_code_retained_registry_policy_runtime.dependency_operation_validator import (
    retained_dependency_operation_validator,
)
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    RetainedSourcePlanningRequest,
)
from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
    retained_planning_dependency_source,
)
from aware_code_retained_registry_policy_runtime.retained_demand_operation import (
    dependency_resolution_validation_session,
    execute_retained_dependency_demand,
)
from aware_code_retained_registry_policy_runtime.retained_input_admission import (
    assemble_retained_input_admission_origin,
)
from aware_code_semantic_contract_runtime import (
    CodePortableSemanticContract,
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    ContractViolation,
    SemanticBody,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractRuntime,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
)
from aware_code_semantic_contract_runtime import (
    selected_provider as selected,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    decode_dependency_product_input,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    decode_code_semantic_contract_match_admission,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DeclarationTargetInventoryCodec,
    DependencyPlanningInputCodec,
    PackageContextInputCodec,
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticRegistryPackageInput,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    semantic_candidate_listing_body,
)
from aware_code_semantic_contract_runtime.stage_contribution import (
    read_selected_provider_stage_catalog_inputs,
)
from aware_local_service_runtime import InMemoryLocalOperationalStateStore
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.semantic_materialization_publication import (
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationPublisher,
    WorkspaceSemanticMaterializationRequestV3,
)
from test_calculation import HEADER
from test_declaration_scope_admission import fixture
from test_operation_context import _BINDING, CONTRACTS, planning_profile
from test_profile_runtime import JsonBodyCodec
from test_semantic_materialization_publication import (
    RESULT,
    SOURCE,
    _BodyStore,
    _invocation,
    _JsonCodec,
    _profile,
    _Provider,
)

KEY = "test_upstream"
ARTIFACT = b'{"implementation":"original-upstream-test-owner"}'
CONFIGURATION = b'{"configuration":"original-upstream-test-owner"}'
BINDING = replace(
    _BINDING,
    provider_key=KEY,
    implementation=SemanticImplementationCoordinate(
        "test.upstream.owner", ContentDigest.of_bytes(ARTIFACT)
    ),
    configuration=SemanticConfigurationCoordinate(
        "test.upstream.owner", ContentDigest.of_bytes(CONFIGURATION)
    ),
)
AUTHORITY_ARTIFACT = b'{"implementation":"original-upstream-test-supplier"}'
AUTHORITY_BINDING = replace(
    BINDING,
    implementation=SemanticImplementationCoordinate(
        "test.upstream.supplier", ContentDigest.of_bytes(AUTHORITY_ARTIFACT)
    ),
)


def _profiles():
    p = planning_profile()
    declaration = replace(
        p.providers[0],
        provider_key=KEY,
        package_kinds=("fixture",),
        result_role=replace(
            p.providers[0].result_role,
            contract=DependencyPlanningInputCodec.contract,
        ),
    )
    p = replace(
        p,
        profile_ref="test.upstream.planning",
        package_kinds=("fixture",),
        providers=(declaration,),
        steps=(replace(p.steps[0], provider_key=KEY),),
    )
    a = _profile()
    a = replace(
        a,
        profile_ref="test.upstream.authority",
        package_kinds=("fixture",),
        providers=(
            replace(a.providers[0], provider_key=KEY, package_kinds=("fixture",)),
        ),
        steps=(replace(a.steps[0], provider_key=KEY),),
    )
    return p, a


class _PlanningOwner:
    def __init__(self, declaration):
        self._declaration = declaration
        self.calls = 0

    @property
    def declaration(self):
        return self._declaration

    def input_closure(self, closure):
        return closure

    def execute(self, step, closure):
        self.calls += 1
        bodies = {b.coordinate.role: b.canonical_body for b in closure.input_bodies}
        package = PackageContextInputCodec().decode(bodies["package_context"])
        inventory = DeclarationTargetInventoryCodec().decode(
            bodies["declaration_inventory"]
        )
        return SemanticDependencyPlanningInput(
            package.package,
            package.source_identity_digest,
            tuple(
                SemanticAuthoredDependency(
                    d.dependency_kind, d.dependency_ref, d.targets, d.target_constraints
                )
                for d in inventory.entries
            ),
        )


class _SupplierOwner(_Provider):
    def __init__(self, declaration):
        self._declaration = declaration

    @property
    def declaration(self):
        return self._declaration

    def input_closure(self, closure):
        return closure

    def execute(self, step, closure):
        return asyncio.run(self.derive(step))

    async def derive(self, step):
        original = await super().derive(step)
        transition = replace(original.result.transition, provider_key=KEY)
        effect = replace(
            original.result.effect,
            provider_key=KEY,
            transition_digest=transition.digest,
        )
        result = replace(
            original.result,
            transition=transition,
            effect=effect,
            outputs=tuple(
                replace(o, provider_key=KEY, prepared_effect_digest=effect.digest)
                for o in original.result.outputs
            ),
        )
        return replace(original, result=result)


class _OriginalPlanner:
    def __init__(self):
        self.calls = 0

    async def plan(self, *, package, intent, selected_match, planning_input):
        self.calls += 1
        b = selected_match.selected_binding
        demands = tuple(
            SemanticDependencyDemand.create(
                consumer_semantic_role=role,
                authored_dependency_kind=d.dependency_kind,
                authored_dependency_ref=d.dependency_ref,
                target_constraints=d.target_constraints,
                required_result_role="result",
                result_product_contract=RESULT,
                target_intent=CodeSemanticMaterializationIntent.create(
                    operation_kind="materialize",
                    requested_semantic_root_refs=d.targets[0].semantic_root_refs,
                    requested_terminal_output_roles=("result",),
                    semantic_configuration_coordinate=None,
                ),
                cardinality="required",
            )
            for d in planning_input.dependencies
            for role in ("first", "second")
        )
        return SemanticDependencyDemandSet.create(
            package=package,
            intent=intent,
            profile_ref=b.profile_declaration.profile_ref,
            profile_digest=b.profile_declaration.digest,
            contract_profile_binding_digest=b.binding_digest,
            planner_implementation_ref=b.dependency_planner_implementation.implementation_ref,
            planner_implementation_digest=b.dependency_planner_implementation.closure_digest,
            planner_configuration=b.dependency_planner_configuration,
            demands=tuple(sorted(demands, key=lambda d: d.demand_digest.value)),
        )


@dataclass(frozen=True, slots=True)
class _CatalogProduct:
    original: object
    entries: tuple
    executables: tuple
    planner: object


def _factory():
    original_planner = _OriginalPlanner()

    def catalog_product(original):
        inputs = read_selected_provider_stage_catalog_inputs(original)
        entries = []
        for item in inputs:
            p = item.stage.runtime.profile
            provider = p.providers[0]
            entries.append(
                CodeSemanticMaterializationProfileBinding.create(
                    semantic_owner_key="test.upstream",
                    semantic_provider_key=KEY,
                    package_families=("public",),
                    package_roles=("fixture",),
                    manifest_contracts=(CONTRACTS["manifest_source"],),
                    profile_declaration=p,
                    provider_execution_bindings=(item.binding,),
                    dependency_planner_contract=SOURCE,
                    dependency_planner_implementation=BINDING.implementation,
                    dependency_planner_configuration=BINDING.configuration,
                    dependency_demand_contract=SOURCE,
                    dependency_target_intent_contract=SOURCE,
                    result_product_contracts=tuple(
                        CodeSemanticRequiredResultProduct.create(
                            role=r.role, contract=r.contract
                        )
                        for r in sorted(
                            (
                                provider.result_role,
                                provider.effect_role,
                                *provider.output_roles,
                            ),
                            key=lambda r: r.role,
                        )
                    ),
                    priority=0,
                )
            )
        return _CatalogProduct(
            original,
            tuple(sorted(entries, key=lambda e: e.profile_declaration.profile_ref)),
            tuple(
                (i.binding.implementation, i.binding.configuration, i.executable)
                for i in inputs
            ),
            original_planner,
        )

    def construct():
        p, a = _profiles()
        providers = (_PlanningOwner(p.providers[0]), _SupplierOwner(a.providers[0]))
        products = []
        for profile, provider in zip((p, a), providers, strict=True):
            contracts = SemanticContractRuntime._profile_body_contracts(profile)
            codecs = {c: JsonBodyCodec(c) for c in contracts}
            if profile is p:
                codecs[DependencyPlanningInputCodec.contract] = (
                    DependencyPlanningInputCodec()
                )
            else:
                codecs = {c: _JsonCodec(c) for c in contracts}
            binding = BINDING if profile is p else AUTHORITY_BINDING
            artifact = ARTIFACT if profile is p else AUTHORITY_ARTIFACT
            products.append(
                selected._SelectedProviderFactoryProduct(
                    SemanticContractRuntime(profile, {KEY: provider}, codecs),
                    provider,
                    binding,
                    provider.execute,
                    provider.input_closure,
                    artifact,
                    CONFIGURATION,
                )
            )
        return selected.SelectedProviderStageFactoryProduct(
            *products, catalog_contribution_producer=catalog_product
        )

    admission = selected._admit_selected_provider_factory(
        factory_ref="test.upstream.original.factory",
        provider_key=KEY,
        selection_factory=construct,
    )
    return admission, original_planner


def _read_product_factory():
    read_key = "test_upstream_read"
    artifact = b'{"implementation":"original-upstream-read-owner"}'
    binding = replace(
        AUTHORITY_BINDING,
        provider_key=read_key,
        implementation=SemanticImplementationCoordinate(
            "test.upstream.read", ContentDigest.of_bytes(artifact)
        ),
    )
    planner = _OriginalPlanner()

    def catalog_product(original):
        item = read_selected_provider_product_contribution(original)
        p = item.profile
        provider = p.providers[0]
        entry = CodeSemanticMaterializationProfileBinding.create(
            semantic_owner_key="test.upstream",
            semantic_provider_key=read_key,
            package_families=("public",),
            package_roles=("read",),
            manifest_contracts=(CONTRACTS["manifest_source"],),
            profile_declaration=p,
            provider_execution_bindings=(item.binding,),
            dependency_planner_contract=SOURCE,
            dependency_planner_implementation=binding.implementation,
            dependency_planner_configuration=binding.configuration,
            dependency_demand_contract=SOURCE,
            dependency_target_intent_contract=SOURCE,
            result_product_contracts=tuple(
                CodeSemanticRequiredResultProduct.create(
                    role=r.role, contract=r.contract
                )
                for r in sorted(
                    (
                        provider.result_role,
                        provider.effect_role,
                        *provider.output_roles,
                    ),
                    key=lambda r: r.role,
                )
            ),
            priority=0,
        )
        return _CatalogProduct(
            original,
            (entry,),
            (
                (
                    item.binding.implementation,
                    item.binding.configuration,
                    item.executable,
                ),
            ),
            planner,
        )

    def construct():
        _, profile = _profiles()
        profile = replace(
            profile,
            profile_ref="test.upstream.read",
            providers=(replace(profile.providers[0], provider_key=read_key),),
            steps=(replace(profile.steps[0], provider_key=read_key),),
        )
        provider = _SupplierOwner(profile.providers[0])
        runtime = SemanticContractRuntime(
            profile,
            {read_key: provider},
            {
                c: _JsonCodec(c)
                for c in SemanticContractRuntime._profile_body_contracts(profile)
            },
        )
        return selected._SelectedProviderFactoryProduct(
            runtime,
            provider,
            binding,
            provider.execute,
            provider.input_closure,
            artifact,
            CONFIGURATION,
            catalog_contribution_producer=catalog_product,
        )

    return selected._admit_selected_provider_factory(
        factory_ref="test.upstream.original.read.factory",
        provider_key=read_key,
        selection_factory=construct,
    )


def _author(root):
    planning_profile_, authority = _profiles()
    text = HEADER.replace("aware = 2", "aware = 3", 1)
    text = text.replace('"demo"', f'"{KEY}"').replace("demo_toml", "fixture_toml")
    text = text.replace("aware.demo.toml", "aware.example.toml")
    text = text.replace(
        f'semantic_package_family = "{KEY}"', 'semantic_package_family = "public"'
    )
    text = text.replace(
        'semantic_package_kind = "demo_package"',
        'semantic_package_kind = "fixture"\ndeclared_package_kinds = ["fixture"]',
    )
    text = text.replace(f'role = "{KEY}", name =', 'role = "fixture", name =')
    text = text.replace('kind = "' + KEY + '"', 'kind = "fixture"')
    for stage, profile in (("authority", authority), ("planning", planning_profile_)):
        text = text.replace(
            f'profile_ref="demo.{stage}"', f'profile_ref="{profile.profile_ref}"'
        )
        text = text.replace(
            '"sha256:' + "a" * 64 + '"', '"' + profile.digest.to_wire() + '"', 1
        )
    text = text[: text.index("dependency_targets =")]
    provider, package = text.split('[[packages]]\nid = "home"', 1)
    package = '[[packages]]\nid = "example"' + package
    package = package.replace("home/aware.example.toml", "package/aware.example.toml")
    package = package.replace(
        f'module_id="{KEY}"',
        'scope={kind="dependency", workspace_handle="Kernel"},module_id="main"',
    )
    consumer = "aware=3\n" + package
    consumer += 'dependency_targets={state="present",value=[{dependency_kind="workspace",dependency_ref="kernel",targets=[{scope={kind="dependency",workspace_handle="Kernel"},module_id="main",package_id="example"}],constraints=[]}]}\n'
    target = provider + package.replace(
        'scope={kind="dependency", workspace_handle="Kernel"}', 'scope={kind="local"}'
    )
    target = (
        target.replace('value="home-demo"', 'value="foundation"')
        .replace('value="home-code"', 'value="foundation-code"')
        .replace('value="home"', 'value="foundation"')
        .replace('value=["home"]', 'value=["foundation"]')
    )
    target += 'dependency_targets={state="present",value=[]}\n'
    (root / "workspaces/network/modules/main/aware.module.toml").write_text(consumer)
    (root / "workspaces/kernel/modules/main/aware.module.toml").write_text(target)
    provider_root = root / "workspaces/kernel/modules/main/provider"
    provider_root.mkdir()
    (provider_root / "pyproject.toml").write_bytes(
        b'[project]\nname="original-owner"\n'
    )
    profile_path = (
        root
        / "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml"
    )
    profile_path.write_text(
        'aware_semantic_contract_profile=1\n[profile]\nkey="kernel.default"\npackage_key="arbitrary.provider.package"\n[[providers]]\nmodule_id="main"\nprovider_key="test_upstream"\n'
    )
    workspace = root / "workspaces/network/aware.workspace.toml"
    workspace.write_text(
        workspace.read_text().replace('"aware_code"', '"test_upstream"')
    )
    (root / "workspaces/network/modules/main/package/aware.example.toml").write_bytes(
        b'{"source":"consumer"}'
    )
    (root / "workspaces/kernel/modules/main/package/aware.example.toml").write_bytes(
        b'{"source":"foundation"}'
    )


def _coordinates():
    digest = ContentDigest.of_bytes(b"original-admission local composition")
    return {
        "composition_implementation": SemanticImplementationCoordinate(
            "test.upstream.composition", digest
        ),
        "composition_configuration": SemanticConfigurationCoordinate(
            "test.upstream.composition", digest
        ),
        "policy_implementation": SemanticImplementationCoordinate(
            "test.upstream.policy", digest
        ),
        "policy_configuration": SemanticConfigurationCoordinate(
            "test.upstream.policy", digest
        ),
    }


@pytest.fixture(scope="module")
def original_owner_factory():
    # One original factory; each command acquires fresh owned registrations.
    return _factory()


@pytest.fixture(scope="module")
def original_read_factory():
    return _read_product_factory()


@pytest.mark.parametrize(
    "change", [None, "source", "head", "body", "host", "replay", "read-attachment"]
)
async def test_original_code_demand_to_upstream_fulfillment(
    tmp_path, change, original_owner_factory, request
):
    factory, planner = original_owner_factory
    original_read_factory = (
        request.getfixturevalue("original_read_factory")
        if change == "read-attachment"
        else None
    )
    planner_calls = planner.calls
    async with fixture(tmp_path) as (root, _, borrowed, _, _, _):
        _author(root)
        with composition.compose_direct_workspace_selected_host(
            factory_admission=factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            product_factory_admissions=(
                (original_read_factory,) if change == "read-attachment" else ()
            ),
            **_coordinates(),
        ) as fixed:
            staged, host = fixed.staged, fixed.code_host
            issuer = staged.command.sources.declaration_scope_runtime
            with (
                composition._compose_direct_workspace_selected_package_source(
                    staged.command,
                    workspace_manifest_path="workspaces/network/aware.workspace.toml",
                    module_id="main",
                    package_id="example",
                ) as source,
                ExitStack() as reads,
            ):
                node = None
                if change == "read-attachment":
                    node = reads.enter_context(
                        composition._command_owned_selected_input_read_session(
                            staged.command,
                            host=host,
                            selected_source=source,
                            registration=staged.product_runtime_bindings[
                                0
                            ].registration,
                        )
                    )
                policy = code.produce_registry_policy(host, source)
                grant = code.validate_admitted_registry_policy(host, policy).grants[0]
                package, inventory = issuer.inspect_inputs(source)
                stage = staged.stage_runtime_bindings[0]
                registry = CodeSemanticRegistryPackageInput(
                    "fixture_toml",
                    "aware.example.toml",
                    KEY,
                    "public",
                    "fixture",
                    CodePortableSemanticContract("fixture", KEY, KEY, "contract:demo"),
                    ("aware",),
                    None,
                    grant.namespace,
                    grant.owned_roots,
                    stage.runtime.profile.profile_ref,
                    stage.runtime.profile.version,
                    stage.runtime.profile.digest,
                    BINDING,
                )
                manifest = (
                    staged.command.sources.observation_runtime.read_selected_package(
                        issuer._selected_record(source).observation,
                        relative_path="aware.example.toml",
                    )
                )
                request = RetainedSourcePlanningRequest(
                    SemanticBody(
                        SemanticValueCoordinate(
                            "manifest_source",
                            CONTRACTS["manifest_source"],
                            "test:manifest",
                            ContentDigest.of_bytes(manifest),
                            len(manifest),
                        ),
                        manifest,
                    ),
                    semantic_candidate_listing_body(
                        issuer.read_selected_package_source(source).candidates
                    ),
                    retained_projection_body(registry),
                    retained_projection_body(package),
                    retained_projection_body(inventory),
                )
                context = contexts.begin_source_planning_operation(
                    host, policy, stage.registration, request
                )
                expected = contexts.source_planning_expectation(host, context)
                package_admission, inventory_admission = (
                    issuer.issue_source_planning_pair(
                        source, context=context, expected=expected
                    )
                )
                origin = assemble_retained_input_admission_origin(host)
                registered = origin.issue_registry_package_admission(
                    context, package_admission
                )
                origin.validate(
                    origin.join(
                        context, registered, package_admission, inventory_admission
                    )
                )
                planning_origin = planning.bind_planning_execution_origin(
                    host, stage.registration
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
                        key=lambda b: b.coordinate.role,
                    )
                )
                call = SemanticContractInvocation(
                    invocation_ref="test:original-planning",
                    idempotency_key="test:original-planning",
                    profile_ref=stage.runtime.profile.profile_ref,
                    profile_digest=stage.runtime.profile.digest,
                    target_package=package.package,
                    operation_kind="materialize",
                    inputs=tuple(b.coordinate for b in bodies),
                    predecessor=TypedEmptyCoordinate(
                        DependencyPlanningInputCodec.contract
                    ),
                    dependencies=(),
                    body_codec_bindings=tuple(
                        SemanticBodyCodecBinding(c, i)
                        for c, i in sorted(
                            stage.runtime._codec_implementations.items(),
                            key=lambda item: item[0].key,
                        )
                    ),
                    provider_bindings=(BINDING,),
                    requested_output_roles=(),
                )
                execution = selected.issue_selected_provider_execution(
                    stage.runtime,
                    stage.registration,
                    selected.SelectedProviderInvocationClosure(call, bodies),
                    operation_context=context,
                )
                selected.execute_selected_provider(stage.runtime, execution)
                retained = retained_planning_dependency_source(planning_origin, context)
                intent = CodeSemanticMaterializationIntent.create(
                    operation_kind="materialize",
                    requested_semantic_root_refs=grant.owned_roots,
                    requested_terminal_output_roles=("result",),
                    semantic_configuration_coordinate=None,
                )
                target = CodeSemanticPackagePlanningContext.create(
                    package=package.package,
                    package_family="public",
                    package_role="fixture",
                    manifest_contract=CONTRACTS["manifest_source"],
                    code_intent=intent,
                    required_result_products=(
                        CodeSemanticRequiredResultProduct.create(
                            role="result", contract=RESULT
                        ),
                    ),
                    required_semantic_provider_keys=(KEY,),
                )
                demand = await execute_retained_dependency_demand(
                    retained, context=target
                )
                expectation = retained_dependency_operation_validator(host).expectation(
                    demand
                )
                assert (
                    len(demand.read_demand().demands) == 2
                    and planner.calls == planner_calls + 1
                )
                body_store = _BodyStore()
                store = InMemoryLocalOperationalStateStore()
                publisher = WorkspaceSemanticMaterializationPublisher(
                    state_store=store, body_store=body_store
                )
                composition._compose_direct_workspace_dependency_product_issuer(
                    staged, host, publisher=publisher
                )
                with dependency_resolution_validation_session(demand):
                    resolution = issuer.issue_dependency_resolution(
                        demand,
                        inventory_admission=inventory_admission,
                        expected=expectation,
                    )
                resolution_record = issuer._dependency_resolution.records[resolution]
                assert len(resolution_record.targets) == 2
                target_context = resolution_record.targets[0][3]
                wire = resolution_record.targets[0][4]
                match = decode_code_semantic_contract_match_admission(
                    wire,
                    context=target_context,
                    resolver=issuer._dependency_resolution.resolver,
                )
                owner_context = issuer._semantic[inventory_admission].targets[0].context
                authority = staged.stage_runtime_bindings[1].runtime
                supplier_call, supplier_bodies = _invocation("foundation")
                supplier_call = replace(
                    supplier_call,
                    profile_ref=authority.profile.profile_ref,
                    profile_digest=authority.profile.digest,
                    target_package=target_context.package,
                    provider_bindings=(AUTHORITY_BINDING,),
                )
                completion = await authority.execute(supplier_call, supplier_bodies)
                assert authority.owns_completion(completion)
                snapshot = authority.snapshot_completion(completion)
                publication = WorkspaceSemanticMaterializationRequestV3.create(
                    package=target_context.package,
                    result_coordinate=snapshot.result.transition.result,
                    source_identity_digest=owner_context.source_identity_digest,
                    code_intent_digest=target_context.code_intent.intent_digest,
                    code_match_digest=match.match_digest,
                    planning_input_digest=ContentDigest.of_bytes(
                        DependencyPlanningInputCodec().encode(
                            expectation.planning_input
                        )
                    ),
                    execution_input_closure_digest=snapshot.result.transition.input_closure_digest,
                    operation_result_digest=snapshot.result_digest,
                    expected_head_revision=0,
                )
                publisher._publish_graph_v2(
                    request=publication, snapshot=snapshot, invocation=supplier_call
                )
                consumer = assemble_dependency_admission_consumer(host)
                with dependency_resolution_validation_session(demand):
                    fulfillment = issuer.issue_dependency_fulfillment(
                        resolution, expected=expectation
                    )
                    body = issuer.read_dependency_products(
                        fulfillment,
                        resolution_admission=resolution,
                        expected=expectation,
                    )
                    products = (
                        consumer if node is None else node
                    ).admit_dependency_products(
                        demand, resolution, fulfillment, body=body
                    )
                    decoded = decode_dependency_product_input(
                        products.read_products().canonical_body
                    )
                assert len(decoded.products) == 2
                assert len({p.demand_digest.value for p in decoded.products}) == 2
                assert all(
                    p.body.canonical_body
                    == snapshot.body_for(publication.result_coordinate).canonical_body
                    for p in decoded.products
                )
                if node is not None:
                    node.validate()
                    read_record = composition._selected_input_read_record(node)
                    original = issuer._dependency_fulfillment.records[fulfillment]
                    assert read_record.dependency_binding.originals[3] is original
                    assert read_record.dependency_binding.originals[5] is original.body
                    assert read_record.dependency_binding.originals[6] is original.heads
                    held_body = original.body
                    original.body = replace(held_body)
                    with pytest.raises(
                        RuntimeError, match="original dependency records changed"
                    ):
                        node.validate()
                    original.body = held_body
                    with pytest.raises(RuntimeError, match="terminal"):
                        node.validate()
                    # The read borrows admissions. Rejecting it must not dispose
                    # the issuer family or the still-live admitted Code products.
                    assert original.body is held_body and not original.terminal
                if change == "source":
                    (
                        root / "workspaces/kernel/modules/main/package/body.bin"
                    ).write_bytes(b"changed")
                elif change == "head":
                    store.compare_and_set(
                        publisher._state_namespace,
                        target_context.package.package_ref,
                        expected_revision=1,
                        value={"bad": True},
                    )
                elif change == "body":
                    body_store.substitute_reads = True
                elif change == "host":
                    code.close_direct_validation_host(host)
                elif change == "replay":
                    with pytest.raises(SourceObservationUnavailable, match="replay"):
                        issuer.issue_dependency_fulfillment(
                            resolution, expected=expectation
                        )
                if change in ("source", "head", "body", "host"):
                    with pytest.raises(
                        (
                            SourceObservationUnavailable,
                            ContractViolation,
                            WorkspaceSemanticMaterializationPublicationError,
                        )
                    ):
                        products.read_products()
                else:
                    assert (
                        products.read_products().canonical_body == body.canonical_body
                    )
        assert issuer._closed
        assert not issuer._dependency_fulfillment.records
        assert borrowed._session.authority_admitted
        with pytest.raises((SourceObservationUnavailable, ContractViolation)):
            products.read_products()
