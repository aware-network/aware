from contextlib import contextmanager

import pytest


@pytest.mark.asyncio
async def test_real_environment_completion_publishes_successor(tmp_path, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        ContractViolation,
        SemanticContractInvocation,
        TypedEmptyCoordinate,
        selected_provider,
    )
    from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
        CatalogCompletionTransferExpectation,
        EpochSemanticOperationExpectation,
    )
    from aware_code_semantic_contract_runtime.package_authority_body_codec import (
        PackageAuthorityBodyCodec,
    )
    from aware_code_retained_registry_policy_runtime import authority_execution
    from aware_code_retained_registry_policy_runtime import direct_host
    from aware_code_retained_registry_policy_runtime import planning_dependency_source
    from aware_code_retained_registry_policy_runtime.planning_source_composition import (
        compose_retained_planning_sources,
        validate_composed_retained_planning_source,
    )
    from aware_code_retained_registry_policy_runtime import operation_context
    from aware_code_retained_registry_policy_runtime import retained_input_admission
    from aware_code_retained_registry_policy_runtime import successor_epoch
    from aware_environment_semantic_contract_runtime_provider import planning_stage
    from aware_code_retained_registry_policy_runtime.catalog_completion_transfer import (
        bind_catalog_completion_transfer_runtime,
    )
    from aware_workspace_runtime import WorkspaceSemanticMaterializationMembershipCatalog
    from aware_workspace_runtime import direct_command_composition as composition
    from aware_workspace_runtime.declaration_scope_admission import (
        WorkspaceDeclarationScopeRuntime,
    )
    from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeUnavailable
    from aware_workspace_runtime.materialization_selection import (
        WorkspaceMaterializationRootSelector,
        WorkspaceMaterializationSelectionProposal,
    )
    from aware_workspace_runtime.source_admission_catalog import (
        derive_owner_defined_catalog_entry,
    )
    from test_v3_real_environment_authority_completion import (
        test_real_v3_environment_authority_uses_original_empty_products,
    )

    original_staged = composition._compose_direct_workspace_staged_command_resources
    original_selected = composition._compose_direct_workspace_selected_package_source
    original_policy = composition._compose_direct_workspace_policy_host
    original_pair = WorkspaceDeclarationScopeRuntime.issue_authority_pair
    original_decode = PackageAuthorityBodyCodec.decode
    original_planning_source = planning_dependency_source.retained_planning_dependency_source
    retained = {}

    @contextmanager
    def staged_resources(**kwargs):
        with original_staged(**kwargs) as staged:
            retained["staged"] = staged
            yield staged

    @contextmanager
    def selected_source(*args, **kwargs):
        with original_selected(*args, **kwargs) as selected:
            retained["selected"] = selected
            yield selected

    def authority_pair(self, selected, *, context, expected):
        pair = original_pair(self, selected, context=context, expected=expected)
        retained["authority"] = (self, selected, context, expected, pair)
        return pair

    def planning_source(origin, context):
        source = original_planning_source(origin, context)
        retained["planning_source"] = source
        return source

    @contextmanager
    def policy_host(staged, **coordinates):
        retained["coordinates"] = coordinates
        with original_policy(staged, **coordinates) as host:
            yield host

    def decode_and_publish(codec, body):
        result = original_decode(codec, body)
        if "authority" not in retained or "done" in retained or "busy" in retained:
            return result
        issuer, selected, context, expected, pair = retained["authority"]
        try:
            completion = authority_execution.read_authority_completion(context)
        except Exception:
            return result
        retained["busy"] = True
        staged = retained["staged"]
        sources = staged.command.sources
        selection = WorkspaceMaterializationSelectionProposal.create(
            selectors=(WorkspaceMaterializationRootSelector.create(
                selector_kind="package", selector_ref="home-story-environment"
            ),)
        )
        roots = issuer.inspect_materialization_roots(
            sources.declaration_scope, selection=selection
        )
        admission = sources.source_admission_runtime.issue(
            roots[0], selected, pair[0], pair[1],
            context=context, expected=expected, completion=completion,
        )
        entry = derive_owner_defined_catalog_entry(
            sources.source_admission_runtime, admission
        )
        successor = WorkspaceSemanticMaterializationMembershipCatalog.create(
            catalog_ref="test.v3.environment.successor",
            catalog_generation=2,
            entries=(entry,),
        )
        catalog_host = staged.command.catalog_host
        initial = catalog_host.read_initial_publication()
        code_catalog, _, _, providers, planners = catalog_host._contribution
        preparation, publication = catalog_host.prepare_successor_catalogs(
            code_catalog=code_catalog,
            workspace_catalog_reader=lambda: successor,
            provider_executable_bindings=providers,
            dependency_planner_bindings=planners,
        )
        code_host = next(iter(composition._POLICY_HOSTS.keys()))
        transfer_runtime = bind_catalog_completion_transfer_runtime(code_host)
        transfer_expected = CatalogCompletionTransferExpectation(
            EpochSemanticOperationExpectation(expected, initial), publication
        )
        transfer = transfer_runtime.prepare_catalog_completion_transfer(
            context, completion, preparation, expected=transfer_expected
        )
        published = catalog_host.publish_successor_catalogs(
            preparation, transfer,
            publication_expected=publication,
            transfer_expected=transfer_expected,
            transfer_runtime=transfer_runtime,
        )
        assert published.workspace.catalog == successor
        package, _inventory = issuer.inspect_inputs(selected)
        with pytest.raises(ContractViolation):
            retained["planning_source"].read_dependencies(package.package)
        with pytest.raises(WorkspaceCommandLifetimeUnavailable, match="command_binding_replay"):
            with original_policy(staged, **retained["coordinates"]):
                pass
        old_source = retained["planning_source"]
        old_context = planning_dependency_source._SOURCES[old_source][1]
        old_record = operation_context._CONTEXTS[old_context]
        successor_epoch.adopt_committed_successor_epoch(
            code_host, transfer_runtime, transfer, expected=transfer_expected
        )
        with pytest.raises(ContractViolation, match="policy unavailable"):
            direct_host.validate_admitted_registry_policy(code_host, old_record.policy)
        policy = direct_host.produce_registry_policy(code_host, selected)
        assert direct_host.validate_admitted_registry_policy(code_host, policy).grants
        fresh_context = operation_context.begin_source_planning_operation(
            code_host, policy, old_record.registration, old_record.request
        )
        fresh_expected = operation_context.source_planning_expectation(
            code_host, fresh_context
        )
        fresh_package, fresh_inventory = issuer.issue_source_planning_pair(
            selected, context=fresh_context, expected=fresh_expected
        )
        origin = retained_input_admission._INSTALLED[code_host]()
        fresh_registry = origin.issue_registry_package_admission(
            fresh_context, fresh_package
        )
        joined = origin.join(
            fresh_context, fresh_registry, fresh_package, fresh_inventory
        )
        origin.validate(joined)
        request = old_record.request
        bodies = tuple(sorted((
            request.manifest_source,
            request.candidate_listing,
            request.registry_package,
            request.package_context,
            request.declaration_inventory,
        ), key=lambda body: body.coordinate.role))
        planning = staged.stage_runtime_bindings[0]
        profile = planning.runtime.profile
        invocation = SemanticContractInvocation(
            invocation_ref="test:v3-environment-successor-planning",
            idempotency_key="test:v3-environment-successor-planning",
            profile_ref=profile.profile_ref,
            profile_digest=profile.digest,
            target_package=old_record.expected.package,
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
        selected_run = selected_provider.issue_selected_provider_execution(
            planning.runtime,
            planning.registration,
            selected_provider.SelectedProviderInvocationClosure(invocation, bodies),
            operation_context=fresh_context,
        )
        selected_provider.execute_selected_provider(planning.runtime, selected_run)
        planning_origin = planning_dependency_source._SOURCES[old_source][0]
        fresh_source = planning_dependency_source.retained_planning_dependency_source(
            planning_origin, fresh_context
        )
        assert fresh_source.read_dependencies(old_record.expected.package).package == (
            old_record.expected.package
        )
        composed = compose_retained_planning_sources((fresh_source,))
        validate_composed_retained_planning_source(
            code_host, composed, (old_record.expected.package,)
        )
        with pytest.raises(ContractViolation, match="predecessor transfer"):
            successor_epoch.adopt_committed_successor_epoch(
                code_host, transfer_runtime, transfer, expected=transfer_expected
            )
        assert composed.read_dependencies(old_record.expected.package).package == (
            old_record.expected.package
        )
        retained["fresh_context"] = fresh_context
        retained["done"] = True
        return result

    monkeypatch.setattr(composition, "_compose_direct_workspace_staged_command_resources", staged_resources)
    monkeypatch.setattr(composition, "_compose_direct_workspace_selected_package_source", selected_source)
    monkeypatch.setattr(composition, "_compose_direct_workspace_policy_host", policy_host)
    monkeypatch.setattr(WorkspaceDeclarationScopeRuntime, "issue_authority_pair", authority_pair)
    monkeypatch.setattr(PackageAuthorityBodyCodec, "decode", decode_and_publish)
    monkeypatch.setattr(planning_dependency_source, "retained_planning_dependency_source", planning_source)
    await test_real_v3_environment_authority_uses_original_empty_products(tmp_path)
    assert retained.get("done") is True
    assert retained.get("fresh_context") is not None
