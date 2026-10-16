"""Original mixed command/source/target owners; test bootstrap is not installed."""

from contextlib import ExitStack, asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as code
from aware_code_retained_registry_policy_runtime import operation_context as planning
from aware_code_retained_registry_policy_runtime import planning_execution
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    RetainedSourcePlanningRequest,
)
from aware_code_retained_registry_policy_runtime.retained_input_admission import (
    assemble_retained_input_admission_origin,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticImplementationCoordinate,
    TypedEmptyCoordinate,
    selected_provider,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    SemanticContractRef,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_REF,
    decode_grammar_source_group,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    semantic_candidate_listing_body,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SOURCE_SELECTION_REF,
    SemanticSelectedSource,
    SemanticSourceSelection,
    source_selection_body,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)
from aware_environment_semantic_contract_runtime_provider.body_codecs import (
    environment_manifest_source_body,
)
from aware_environment_semantic_contract_runtime_provider.planning_stage import (
    BINDING,
    MEANING_ROLE,
    planning_body_codec_bindings,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as workspace
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspaceSelectedDependencyInputV1,
    WorkspaceSelectedSourceInputV1,
)
from test_authority_derivation import arguments
from test_current_head_two_stage_host import (
    qualified_repository,
)
from test_current_head_two_stage_host import (
    real_environment_factory as _environment_fixture,
)
from test_dependency_scope_admission import fixture as repository
from test_grammar_original_workspace_host import (
    grammar_admissions as _grammar_fixture,
)

# Reuse the original fixture objects without wrapping their admission functions.
real_environment_factory = _environment_fixture
grammar_admissions = _grammar_fixture


def authored_target_repository(root):
    qualified_repository(root)
    path = root / "consumer/modules/main/aware.module.toml"
    original = path.read_text().replace(
        'value="home-demo"', 'value="home-story-environment"'
    )
    empty = 'dependency_targets = {state="present", value=[]}'
    assert original.count(empty) == 1
    target = (
        'dependency_targets = {state="present", value=['
        '{dependency_kind="module",dependency_ref="home",'
        'targets=[{scope={kind="dependency",workspace_handle="Target"},'
        'module_id="main",package_id="target"}],constraints=[]}]}'
    )
    path.write_text(original.replace(empty, target))
    # Author the target before original observation; do not relabel a source.
    occurrence = original.split("[[packages]]", 1)[1]
    occurrence = occurrence.replace('id = "home"', 'id = "target"')
    occurrence = occurrence.replace(
        "home/aware.environment.toml", "target/aware.environment.toml"
    ).replace('value="home-story-environment"', 'value="target-environment"')
    occurrence = (
        occurrence.replace(
            'scope={kind="dependency", workspace_handle="Target"}',
            'scope={kind="local"}',
        )
        .replace('value="home"', 'value="target"')
        .replace('value=["home"]', 'value=["target"]')
    )
    target_module = root / "target/modules/main/aware.module.toml"
    target_module.write_text(target_module.read_text() + "\n[[packages]]" + occurrence)
    target_root = target_module.parent / "target"
    target_root.mkdir()
    (target_root / "aware.environment.toml").write_text(
        'aware=1\n[environment]\nhandle="target"\nmodules=["home"]\n'
    )


@asynccontextmanager
async def original_join(tmp_path, stage_admission, product_admissions):
    async with repository(tmp_path, authored_target_repository) as (
        root,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        digest = ContentDigest.of_bytes(b"original mixed-host source proof")
        implementation = SemanticImplementationCoordinate("test.mixed.host", digest)
        configuration = SemanticConfigurationCoordinate("test.mixed.host", digest)
        with workspace.compose_direct_workspace_selected_host(
            factory_admission=stage_admission,
            product_factory_admissions=product_admissions,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            composition_implementation=implementation,
            composition_configuration=configuration,
            policy_implementation=implementation,
            policy_configuration=configuration,
        ) as paired:
            command = paired.staged.command
            issuer = command.sources.declaration_scope_runtime
            with workspace._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="home",
            ) as selected:
                policy = code.produce_registry_policy(paired.code_host, selected)
                grant = code.validate_admitted_registry_policy(
                    paired.code_host, policy
                ).grants[0]
                stage = paired.staged.stage_runtime_bindings[0]
                profile = stage.runtime.profile
                package, inventory = issuer.inspect_inputs(selected)
                raw = command.sources.observation_runtime.read_selected_package(
                    issuer._selected_record(selected).observation,
                    relative_path="aware.environment.toml",
                )
                owner_inputs, _ = arguments(raw)
                registry = replace(
                    owner_inputs["registry_package"],
                    fqn_prefix=grant.namespace,
                    owned_semantic_root_refs=grant.owned_roots,
                    profile_ref=profile.profile_ref,
                    profile_version=profile.version,
                    profile_digest=profile.digest,
                    binding=BINDING,
                )
                source = issuer.read_selected_package_source(selected)
                request = RetainedSourcePlanningRequest(
                    environment_manifest_source_body(raw),
                    semantic_candidate_listing_body(source.candidates),
                    retained_projection_body(registry),
                    retained_projection_body(package),
                    retained_projection_body(inventory),
                )
                context = planning.begin_source_planning_operation(
                    paired.code_host, policy, stage.registration, request
                )
                expected = planning.source_planning_expectation(
                    paired.code_host, context
                )
                package_admission, inventory_admission = (
                    issuer.issue_source_planning_pair(
                        selected, context=context, expected=expected
                    )
                )
                origin = assemble_retained_input_admission_origin(paired.code_host)
                registry_admission = origin.issue_registry_package_admission(
                    context, package_admission
                )
                retained = origin.join(
                    context, registry_admission, package_admission, inventory_admission
                )
                origin.validate(retained)
                # Obtain the original target origin already installed by Workspace.
                # A second constructor would be a duplicate owner and must not be used.
                target_origin = issuer._dependency_resolution.target_origin
                record = issuer._semantic[inventory_admission]
                assert len(record.targets) == 1
                target = record.targets[0]
                target_expected = RetainedTargetExpectation(
                    expected,
                    target.context.source_identity_digest,
                    target.context.package,
                )
                target_admission = issuer.select_dependency_target_admission(
                    inventory_admission=inventory_admission, expected=target_expected
                )
                target_context = target_origin.issue_source(
                    context,
                    inventory_admission,
                    target_admission,
                    target_source_identity_digest=target.context.source_identity_digest,
                    target_package=target.context.package,
                )
                yield SimpleNamespace(
                    root=root,
                    paired=paired,
                    issuer=issuer,
                    command=command,
                    selected=selected,
                    context=context,
                    expected=expected,
                    inventory=inventory_admission,
                    package_admission=package_admission,
                    target=target_admission,
                    target_expected=target_expected,
                    target_context=target_context,
                    target_origin=target_origin,
                    retained_origin=origin,
                    retained=retained,
                    request=request,
                    package=package,
                    stage=stage,
                )


def read_target(case, **changes):
    return case.target_origin.read_source(
        changes.get("admission", case.target_context),
        source_context=changes.get("context", case.context),
        inventory_admission=changes.get("inventory", case.inventory),
        target_admission=changes.get("target", case.target),
    )


def retain_selection(stack, case, selected, use_ref):
    """Disclosed raw test selector, through the original reader/executor/retention."""
    issuer = case.issuer
    context = issuer.inspect_inputs(selected)[0]
    raw_ref = SemanticContractRef(
        "test.mixed.raw-source", "1", ContentDigest.of_bytes(b"raw")
    )
    contracts = (inputs.SemanticInputSourceContract("selected_raw", raw_ref),)
    coordinates = tuple(
        inputs.SemanticInputSourceCoordinate(
            row.relative_path,
            SemanticValueCoordinate(
                "raw_source",
                raw_ref,
                row.body_ref,
                ContentDigest(row.content_digest),
                row.size_bytes,
            ),
        )
        for row in issuer.inspect_selected_package_evidence(selected).bodies
    )
    expected = stack.enter_context(
        issuer.original_pre_request_input(
            selected,
            use_ref=use_ref,
            stage="test_selection",
            source_coordinates=coordinates,
        )
    )
    host = inputs.SemanticInputProducerHost()
    stack.callback(host.close)

    async def choose(value):
        return source_selection_body(
            SemanticSourceSelection(
                context.package,
                context.source_identity_digest,
                value.input_digest,
                (),
                tuple(
                    SemanticSelectedSource(
                        "selected_raw",
                        raw_ref,
                        item.source.relative_path,
                        item.source.coordinate.digest,
                    )
                    for item in value.sources
                ),
            ),
            role="selection",
        )

    registration = inputs.register_semantic_input_producer(
        host,
        declaration=inputs.SemanticInputProducerDeclaration(
            "test.mixed.selection",
            "test.mixed.selection.v1",
            SemanticImplementationCoordinate(
                "test.mixed.selection", ContentDigest.of_bytes(b"selector")
            ),
            SemanticConfigurationCoordinate(
                "test.mixed.selection", ContentDigest.of_bytes(b"selector")
            ),
            (inputs.SemanticInputSourceContract("raw_source", raw_ref),),
            "selection",
            SOURCE_SELECTION_REF,
        ),
        producer=choose,
        validator=issuer,
        validator_entrance=issuer.validate_semantic_input_source,
        reader=issuer,
        reader_entrance=issuer.read_semantic_input_sources,
        retain_result=True,
    )
    return host, registration, expected, contracts


async def selected_carrier(stack, case, selected, use_ref):
    host, registration, expected, contracts = retain_selection(
        stack, case, selected, use_ref
    )
    result = await inputs.execute_registered_semantic_input(
        host,
        registration,
        source_admission=selected,
        expected=expected,
    )
    return WorkspaceSelectedSourceInputV1(
        selected, host, registration, expected, result, contracts
    )


def grouped_use(case, root, target, edge):
    return case.issuer.original_grouped_selected_source_input(
        root=root,
        participants=(target,),
        dependency_edges=(edge,),
        use_ref="mixed-original-grammar-source",
        stage="profile_selection",
        source_contracts=root.source_contracts,
        context_contracts=(
            inputs.SemanticInputContextContract(
                "declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF
            ),
            inputs.SemanticInputContextContract(
                "grammar_source_group", GRAMMAR_SOURCE_GROUP_REF
            ),
        ),
    )


async def test_original_admitted_target_reaches_grouped_source_context(
    tmp_path, real_environment_factory, grammar_admissions
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        with ExitStack() as stack:
            root = await selected_carrier(stack, c, c.selected, "mixed-root-selection")
            target = await selected_carrier(
                stack, c, c.target, "mixed-target-selection"
            )
            edge = WorkspaceSelectedDependencyInputV1(
                c.selected, c.target, c.inventory, c.target_expected, "module", "home"
            )
            with grouped_use(c, root, target, edge) as expected:
                c.issuer.validate_semantic_input_source(c.selected, expected=expected)
                c.issuer.validate_semantic_input_context(c.selected, expected=expected)
                body = next(
                    b
                    for b in expected.context_bodies
                    if b.coordinate.role == "grammar_source_group"
                )
                group = decode_grammar_source_group(body.canonical_body)
                assert len(group.members) == 2
                assert len(group.dependency_edges) == 1
                admitted = group.dependency_edges[0]
                assert admitted.owner_occurrence_ref == group.root_occurrence_ref
                assert admitted.target_occurrence_ref != admitted.owner_occurrence_ref
                assert (admitted.dependency_kind, admitted.dependency_ref) == (
                    "module",
                    "home",
                )
                assert expected.operation_identity is c.command.invocation_parent
                read_target(c)


@pytest.mark.parametrize("change", ("inventory", "owner", "selector"))
async def test_grouped_edge_cannot_manufacture_original_target_grant(
    tmp_path, real_environment_factory, grammar_admissions, change
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        with ExitStack() as stack:
            root = await selected_carrier(stack, c, c.selected, "mixed-root-selection")
            target = await selected_carrier(
                stack, c, c.target, "mixed-target-selection"
            )
            edge = WorkspaceSelectedDependencyInputV1(
                c.target if change == "owner" else c.selected,
                c.target,
                object() if change == "inventory" else c.inventory,
                c.target_expected,
                "module",
                "foreign" if change == "selector" else "home",
            )
            with (
                pytest.raises(SourceObservationUnavailable),
                grouped_use(c, root, target, edge),
            ):
                pytest.fail("foreign grouped edge reached interpretation")


async def test_mixed_original_host_admits_planning_and_target_source(
    tmp_path, real_environment_factory, grammar_admissions
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        assert len(c.paired.staged.stage_runtime_bindings) == 2
        assert len(c.paired.staged.product_runtime_bindings) == 2
        assert c.issuer._planning_validator is not None
        assert c.issuer._authority_validator is not None
        assert c.issuer._dependency_validator is not None
        assert (
            code._state(c.paired.code_host).expected.invocation_identity
            is c.command.lifetime_runtime.invocation_identity
        )
        assert (
            planning._CONTEXTS[c.context].reservation.binding.tracker.parent
            is c.command.invocation_parent
        )
        assert (
            c.expected.generation_identity
            is code._state(c.paired.code_host).expected.epoch_identity
        )
        assert c.issuer._semantic_contexts[c.inventory] is c.context
        assert c.target is c.issuer._semantic[c.inventory].targets[0].membership
        source = read_target(c)
        assert source.package_family == "environment"
        assert source.semantic_provider_key == "aware_environment"
        assert c.target_expected.target_package != c.package.package
        assert c.target_origin is c.issuer._dependency_resolution.target_origin
        c.retained_origin.validate(c.retained)


async def test_original_catalog_supplies_typed_target_manifest_contract(
    tmp_path, real_environment_factory, grammar_admissions
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        admission = c.target_origin.issue(
            c.context,
            c.inventory,
            c.target,
            target_source_identity_digest=c.target_expected.target_source_identity_digest,
            target_package=c.target_expected.target_package,
        )
        fields = c.target_origin.read(
            admission,
            source_context=c.context,
            inventory_admission=c.inventory,
            target_admission=c.target,
        )
        source = read_target(c)
        assert fields.package_family == source.package_family
        assert fields.package_role == source.package_role
        manifest_inputs = [
            i for i in c.stage.runtime.profile.inputs if i.role == "manifest_source"
        ]
        assert fields.manifest_contract == manifest_inputs[0].contract
        with pytest.raises(TypeError):
            read_target(c, admission=admission)
        read_target(c)


async def test_original_stage_executes_with_grammar_products_in_same_catalog(
    tmp_path, real_environment_factory, grammar_admissions
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        planning_execution.bind_planning_execution_origin(
            c.paired.code_host, c.stage.registration, terminal_mode="runtime_completion"
        )
        bodies = tuple(
            sorted(
                (
                    c.request.manifest_source,
                    c.request.candidate_listing,
                    c.request.registry_package,
                    c.request.package_context,
                    c.request.declaration_inventory,
                ),
                key=lambda body: body.coordinate.role,
            )
        )
        profile = c.stage.runtime.profile
        invocation = SemanticContractInvocation(
            invocation_ref="test:mixed-original-planning",
            idempotency_key="test:mixed-original-planning",
            profile_ref=profile.profile_ref,
            profile_digest=profile.digest,
            target_package=c.package.package,
            operation_kind="materialize",
            inputs=tuple(body.coordinate for body in bodies),
            predecessor=TypedEmptyCoordinate(profile.providers[0].result_role.contract),
            dependencies=(),
            body_codec_bindings=planning_body_codec_bindings(),
            provider_bindings=(BINDING,),
            requested_output_roles=(MEANING_ROLE,),
        )
        execution = selected_provider.issue_selected_provider_execution(
            c.stage.runtime,
            c.stage.registration,
            selected_provider.SelectedProviderInvocationClosure(invocation, bodies),
            operation_context=c.context,
        )
        completion = selected_provider.execute_selected_provider(
            c.stage.runtime, execution
        )
        assert c.stage.runtime.owns_completion(completion)
        read_target(c)
        workspace._require_live_direct_workspace_command(c.command)


@pytest.mark.parametrize("slot", ("admission", "context", "inventory", "target"))
async def test_detached_coordinates_cannot_replace_original_target_handles(
    tmp_path, real_environment_factory, grammar_admissions, slot
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        read_target(c)
        with pytest.raises(
            (TypeError, ContractViolation, SourceObservationUnavailable)
        ):
            read_target(c, **{slot: object()})
        # Foreign arguments neither consume the valid handles nor close owners.
        read_target(c)
        c.retained_origin.validate(c.retained)


@pytest.mark.parametrize("slot", ("context", "inventory", "target"))
async def test_same_nominal_type_cannot_reconstruct_original_target_handles(
    tmp_path, real_environment_factory, grammar_admissions, slot
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        original = getattr(c, slot)
        forged = object.__new__(type(original))
        assert type(forged) is type(original)
        with pytest.raises(ContractViolation):
            read_target(c, **{slot: forged})
        read_target(c)


@pytest.mark.parametrize(
    "field", ("runtime", "generation_identity", "operation_identity")
)
async def test_target_expectation_cannot_substitute_original_operation(
    tmp_path, real_environment_factory, grammar_admissions, field
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        changed = replace(
            c.target_expected, source_planning=replace(c.expected, **{field: object()})
        )
        with pytest.raises(SourceObservationUnavailable):
            c.issuer.validate_dependency_target_admission(
                c.target, inventory_admission=c.inventory, expected=changed
            )
        read_target(c)


async def test_target_source_mutation_and_restoration_retire_original_use(
    tmp_path, real_environment_factory, grammar_admissions
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        path = c.root / "target/modules/main/target/aware.environment.toml"
        original = path.read_bytes()
        path.write_bytes(b"changed target")
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            read_target(c)
        path.write_bytes(original)
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            read_target(c)


async def test_closed_command_cannot_reuse_target_or_inventory(
    tmp_path, real_environment_factory, grammar_admissions
):
    async with original_join(
        tmp_path, real_environment_factory, grammar_admissions
    ) as c:
        read_target(c)
    assert c.command.sources.declaration_scope_runtime._closed
    with pytest.raises((ContractViolation, SourceObservationUnavailable)):
        read_target(c)
    with pytest.raises((ContractViolation, SourceObservationUnavailable)):
        c.retained_origin.validate(c.retained)
