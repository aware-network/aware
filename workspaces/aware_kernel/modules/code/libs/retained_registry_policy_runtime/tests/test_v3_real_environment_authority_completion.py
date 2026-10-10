"""V3 completion requires original Workspace dependency admission first."""

import pytest
from contextlib import nullcontext
from types import SimpleNamespace

from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime import target_context
from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
    assemble_dependency_admission_consumer,
)
from aware_code_retained_registry_policy_runtime.retained_input_admission import (
    assemble_retained_input_admission_origin,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticPackageCoordinate,
)
from test_declaration_host import OriginalEpochDeclarationOwner, registered_epoch


def _author_environment_v3_repository(root):
    from test_current_head_two_stage_host import qualified_repository

    qualified_repository(root)
    consumer = root / "consumer/modules/main/aware.module.toml"
    body = consumer.read_text()
    body = body.replace('value="home-demo"', 'value="home-story-environment"')
    body = body.replace('value="1.0"', 'value="1"')
    body = body.replace(
        'dependency_targets = {state="present", value=[]}',
        'dependency_targets = {state="present", value=['
        '{dependency_kind="module",dependency_ref="home",'
        'targets=[{scope={kind="dependency",workspace_handle="Target"},'
        'module_id="main",package_id="home_target"}],constraints=[]}'
        ']}'
    )
    consumer.write_text(body)
    source = root / "consumer/modules/main/home/aware/main.aware"
    source.parent.mkdir(parents=True)
    source.write_text("environment home-story {}\n")
    target_module = root / "target/modules/main/aware.module.toml"
    target_module.write_text(target_module.read_text() + '''
[[packages]]
id="home_target"
kind="environment"
manifest="home_target/aware.environment.toml"
[packages.semantic_admission]
registration={state="present",value={scope={kind="local"},module_id="main",package_id="provider",registration_key="demo"}}
semantic_version={state="present",value="1"}
semantic_package_name={state="present",value="target-environment"}
code_package_name={state="present",value="target_code"}
source_code_package_id={state="absent"}
configuration={state="absent"}
namespace={state="present",value="target_home"}
owned_roots={state="present",value=["target_home"]}
dependency_targets={state="present",value=[]}
''')
    target_manifest = root / "target/modules/main/home_target/aware.environment.toml"
    target_manifest.parent.mkdir()
    target_manifest.write_text(
        'aware=1\n[environment]\nhandle="target"\nmodules=[]\n'
    )


@pytest.mark.asyncio
async def test_real_v3_environment_authority_uses_original_empty_products(tmp_path):
    """The selected owner completes after every direct source relationship is admitted."""
    from aware_code_retained_registry_policy_runtime import (
        authority_execution,
        authority_operation_context,
        dependency_operation_validator,
        planning_execution,
        retained_demand_operation,
    )
    from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
        retained_planning_dependency_source,
    )
    from aware_code_semantic_contract_runtime import (
        CodeSemanticContractCatalog,
        CodeSemanticMaterializationIntent,
        CodeSemanticPackagePlanningContext,
        CodeSemanticRequiredResultProduct,
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
        SemanticContractInvocation,
        TypedEmptyCoordinate,
        selected_provider,
    )
    from aware_environment_semantic_contract_runtime_provider import (
        construct_environment_stage_factory_product,
    )
    from aware_environment_semantic_contract_runtime_provider import planning_stage
    from aware_environment_semantic_contract_runtime_provider.catalog_contribution import (
        build_environment_catalog_contribution,
    )
    from aware_workspace_runtime import WorkspaceSemanticMaterializationMembershipCatalog
    from aware_workspace_runtime import direct_command_composition as composition
    from test_current_head_two_stage_host import stage_request
    from test_dependency_scope_admission import fixture as original_sources

    factory = selected_provider._admit_selected_provider_factory(
        factory_ref="test.code.v3-environment-authority",
        provider_key="aware_environment",
        selection_factory=construct_environment_stage_factory_product,
    )
    async with original_sources(tmp_path, _author_environment_v3_repository) as (
        _root, _, _, borrowed, _, _,
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as staged:
            contribution = build_environment_catalog_contribution(staged.contribution)
            catalog = CodeSemanticContractCatalog.create(
                catalog_ref="test.code.v3-environment", catalog_generation=1,
                entries=contribution.entries,
            )
            membership = WorkspaceSemanticMaterializationMembershipCatalog.create(
                catalog_ref="test.code.v3-empty", catalog_generation=1, entries=(),
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
            digest = ContentDigest.of_bytes(b"test v3 Environment authority host")
            coords = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "test.v3.environment.composition", digest,
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "test.v3.environment.composition", digest,
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "test.v3.environment.policy", digest,
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "test.v3.environment.policy", digest,
                ),
            )
            with composition._compose_direct_workspace_policy_host(staged, **coords) as host:
                with composition._compose_direct_workspace_selected_package_source(
                    staged.command,
                    workspace_manifest_path="consumer/aware.workspace.toml",
                    module_id="main", package_id="home",
                ) as selected:
                    issuer = staged.command.sources.declaration_scope_runtime
                    policy = direct_host.produce_registry_policy(host, selected)
                    package, inventory = issuer.inspect_inputs(selected)
                    selected_source = issuer.read_selected_package_source(selected)
                    stage = staged.stage_runtime_bindings[0]
                    grant = direct_host.validate_admitted_registry_policy(
                        host, policy,
                    ).grants[0]
                    manifest = staged.command.sources.observation_runtime.read_selected_package(
                        issuer._selected_record(selected).observation,
                        relative_path="aware.environment.toml",
                    )
                    fixture_package = SimpleNamespace(
                        manifest=SimpleNamespace(
                            body=manifest,
                            content_digest=ContentDigest.of_bytes(manifest),
                        ),
                        manifest_relative_path="aware.environment.toml",
                        package_kind="environment",
                        source_identity_digest=selected_source.candidates.source_identity_digest,
                    )
                    request = stage_request(
                        fixture_package, stage,
                        package_coordinate=package.package,
                        package_context=package,
                        declaration_inventory=inventory,
                        candidate_listing=selected_source.candidates,
                    )
                    planning_context = contexts.begin_source_planning_operation(
                        host, policy, stage.registration, request,
                    )
                    expected = contexts.source_planning_expectation(
                        host, planning_context,
                    )
                    package_admission, inventory_admission = issuer.issue_source_planning_pair(
                        selected, context=planning_context, expected=expected,
                    )
                    origin = assemble_retained_input_admission_origin(host)
                    registry_admission = origin.issue_registry_package_admission(
                        planning_context, package_admission,
                    )
                    joined = origin.join(
                        planning_context, registry_admission, package_admission,
                        inventory_admission,
                    )
                    origin.validate(joined)
                    planning_origin = planning_execution.bind_planning_execution_origin(
                        host, stage.registration, terminal_mode="runtime_completion",
                    )
                    bodies = tuple(sorted((
                        request.manifest_source,
                        request.candidate_listing,
                        request.registry_package,
                        request.package_context,
                        request.declaration_inventory,
                    ), key=lambda body: body.coordinate.role))
                    profile = stage.runtime.profile
                    invocation = SemanticContractInvocation(
                        invocation_ref="test:v3-environment-planning",
                        idempotency_key="test:v3-environment-planning",
                        profile_ref=profile.profile_ref,
                        profile_digest=profile.digest,
                        target_package=package.package,
                        operation_kind="materialize",
                        inputs=tuple(body.coordinate for body in bodies),
                        predecessor=TypedEmptyCoordinate(
                            profile.providers[0].result_role.contract,
                        ),
                        dependencies=(),
                        body_codec_bindings=planning_stage.planning_body_codec_bindings(),
                        provider_bindings=(planning_stage.BINDING,),
                        requested_output_roles=(planning_stage.MEANING_ROLE,),
                    )
                    execution = selected_provider.issue_selected_provider_execution(
                        stage.runtime, stage.registration,
                        selected_provider.SelectedProviderInvocationClosure(invocation, bodies),
                        operation_context=planning_context,
                    )
                    selected_provider.execute_selected_provider(stage.runtime, execution)
                    source = retained_planning_dependency_source(
                        planning_origin, planning_context,
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
                        package_family="environment",
                        package_role="aware_environment.environment_config.provider",
                        manifest_contract=planning_stage.MANIFEST_SOURCE_REF,
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
                        source, context=target,
                    )
                    demand_validator = dependency_operation_validator.retained_dependency_operation_validator(
                        host,
                    )
                    expected_resolution = demand_validator.expectation(operation)
                    assert expected_resolution.demand_set.demands == ()
                    resolution, fulfillment, products_body = issuer.issue_empty_dependency_products(
                        operation,
                        inventory_admission=inventory_admission,
                        expected=expected_resolution,
                    )
                    assert len(issuer._dependency_resolution.records[resolution].relationships) == 1
                    admitted_products = assemble_dependency_admission_consumer(
                        host,
                    ).admit_dependency_products(
                        operation, resolution, fulfillment, body=products_body,
                    )
                    authority_context = authority_operation_context.begin_authority_operation(
                        host, admitted_products,
                    )
                    authority_expected = authority_operation_context.authority_operation_expectation(
                        host, authority_context,
                    )
                    authority_package, authority_inventory = issuer.issue_authority_pair(
                        selected, context=authority_context,
                        expected=authority_expected,
                    )
                    authority_registry = origin.issue_registry_package_admission(
                        authority_context, authority_package,
                    )
                    authority_join = origin.join(
                        authority_context, authority_registry,
                        authority_package, authority_inventory,
                    )
                    origin.validate(authority_join)
                    from aware_local_service_runtime import (
                        InMemoryLocalOperationalStateStore,
                    )
                    from aware_workspace_runtime.semantic_materialization_publication import (
                        WorkspaceSemanticMaterializationPublisher,
                    )
                    from test_semantic_materialization_publication import (
                        _BodyStore, _runtime,
                    )

                    publisher = WorkspaceSemanticMaterializationPublisher(
                        runtime=_runtime(),
                        state_store=InMemoryLocalOperationalStateStore(),
                        body_store=_BodyStore(),
                    )
                    with composition._compose_direct_workspace_authority_predecessor_issuer(
                        staged, host, publisher=publisher,
                    ) as predecessor_issuer:
                        authority_stage = staged.stage_runtime_bindings[1]
                        result_contract = (
                            authority_stage.runtime.profile.providers[0].result_role.contract
                        )
                        execution_identity = object()
                        predecessor_admission = predecessor_issuer.issue_authority_predecessor(
                            authority_context,
                            authority_expected=authority_expected,
                            execution_identity=execution_identity,
                            result_contract=result_contract,
                        )
                        retained_predecessor = authority_execution.retain_authority_predecessor(
                            predecessor_issuer,
                            predecessor_admission,
                            authority_context=authority_context,
                            authority_expected=authority_expected,
                            execution_identity=execution_identity,
                            result_contract=result_contract,
                        )
                        authority_execution.bind_authority_execution_origin(
                            host, authority_stage.registration,
                        )
                        closure = authority_execution.prepare_authority_execution(
                            authority_context, retained_predecessor,
                        )
                        authority_run = selected_provider.issue_selected_provider_execution(
                            authority_stage.runtime, authority_stage.registration,
                            closure, operation_context=authority_context,
                        )
                        selected_provider.execute_selected_provider(
                            authority_stage.runtime, authority_run,
                        )
                        completion = authority_execution.read_authority_completion(
                            authority_context,
                        )
                        assert authority_stage.runtime.owns_completion(completion)
                        snapshot = authority_stage.runtime.snapshot_completion(completion)
                        assert snapshot.result.transition is not None
                        result_coordinate = snapshot.result.transition.result
                        from aware_code_semantic_contract_runtime.package_authority_body_codec import (
                            PackageAuthorityBodyCodec,
                        )
                        authority_value = PackageAuthorityBodyCodec().decode(
                            snapshot.body_for(result_coordinate).canonical_body,
                        )
                        assert authority_value.semantic_package.name == "home-story-environment"
                        assert len(authority_value.direct_dependency_package_refs) == 1


def test_v3_host_refuses_dependency_products_without_original_owner_entrances(
    monkeypatch,
):
    # Supply only the three already-published semantic admission methods on
    # this fixture issuer. They are never called: the test proves that Code
    # cannot promote those handles into dependency fulfillment authority.
    def semantic_validator(self, *args, **kwargs):
        raise AssertionError("semantic validator must not grant fulfillment")

    for name in (
        "validate_package_context_admission",
        "validate_declaration_inventory_admission",
        "validate_occurrence_assignments",
    ):
        monkeypatch.setattr(
            OriginalEpochDeclarationOwner, name, semantic_validator, raising=False
        )
    _owner, host = registered_epoch()
    try:
        source_origin = assemble_retained_input_admission_origin(host)
        assert source_origin is not None
        with pytest.raises(
            ContractViolation, match="original dependency issuer entrances unavailable"
        ):
            assemble_dependency_admission_consumer(host)
    finally:
        direct_host.close_direct_validation_host(host)


def test_v3_target_origin_uses_original_declaration_and_selected_source(
    monkeypatch,
):
    def validate_target(self, admission, *, inventory_admission, expected):
        if (
            admission is not self.selected
            or inventory_admission is not self.snapshot
            or expected.target_source_identity_digest
            != self.selected_value.expectation.source_identity_digest
        ):
            raise ContractViolation("foreign original target")
        self.validate_selected_package_source(
            admission, expectation=self.selected_value.expectation
        )

    monkeypatch.setattr(
        OriginalEpochDeclarationOwner,
        "validate_dependency_target_admission",
        validate_target,
        raising=False,
    )
    owner, host = registered_epoch()
    try:
        origin = target_context.assemble_target_context_origin(host)
        policy = direct_host.produce_registry_policy(host, owner.selected)
        context = object()
        expected = object()
        monkeypatch.setattr(contexts, "_CONTEXTS", {
            context: SimpleNamespace(host=host, policy=policy)
        })
        monkeypatch.setattr(
            contexts, "source_planning_expectation", lambda *_: expected
        )
        def same_source(actual, wanted):
            assert actual is wanted

        monkeypatch.setattr(contexts, "_equal", same_source)
        monkeypatch.setattr(
            contexts, "_synchronous_validation_window", lambda *_: nullcontext()
        )
        selected = owner.selected_value.expectation
        package = next(
            package for scope in owner.projection.scopes
            if scope.scope_key == selected.scope_key
            for package in scope.projection.packages
            if (package.module_id, package.package_id)
            == (selected.module_id, selected.package_id)
        )
        target_package = SemanticPackageCoordinate(
            "fixture-target@1", package.package_kind,
            package.manifest.content_digest,
        )
        admission = origin.issue_source(
            context, owner.snapshot, owner.selected,
            target_source_identity_digest=selected.source_identity_digest,
            target_package=target_package,
        )
        fields = origin.read_source(
            admission, source_context=context,
            inventory_admission=owner.snapshot,
            target_admission=owner.selected,
        )
        assert fields.semantic_provider_key
        assert policy is not None
        owner.selected_live = False
        with pytest.raises(ContractViolation, match="selected source unavailable"):
            origin.read_source(
                admission, source_context=context,
                inventory_admission=owner.snapshot,
                target_admission=owner.selected,
            )
    finally:
        direct_host.close_direct_validation_host(host)
