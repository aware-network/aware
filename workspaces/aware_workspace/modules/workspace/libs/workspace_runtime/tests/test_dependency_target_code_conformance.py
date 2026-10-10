"""Real Code and Workspace target mechanisms; fixture application parent/catalog."""

from contextlib import asynccontextmanager
from dataclasses import fields, replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    direct_host as direct,
)
from aware_code_retained_registry_policy_runtime import (
    operation_context as contexts,
)
from aware_code_retained_registry_policy_runtime import (
    target_context,
)
from aware_code_semantic_contract_runtime import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandResourceBinding,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    _issue_code_semantic_contract_catalog,
    _revoke_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    encode_code_semantic_contract_match_admission,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    semantic_candidate_listing_body,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)
from aware_workspace_runtime import SourceObservationUnavailable
from test_calculation import _catalog
from test_contracts import SOURCE
from test_direct_command_composition import fenced_direct_sources
from test_direct_host import Owner
from test_materialization_catalog import _context, _execution_closure
from test_observed_membership import fixture as repository_fixture
from test_operation_context import setup as code_setup


@asynccontextmanager
async def joined(tmp_path):
    previous, old_host, _, provider, registration, request = code_setup()
    host = None
    try:
        old_state = direct._state(old_host)
        async with repository_fixture(tmp_path) as (root, session, observer, _):
            (root / "aware.workspace.toml").write_text(
                'aware=1\n[workspace]\nhandle="demo"\n[[workspace.modules]]\nid="demo"\npath="demo"\n'
            )
            for body in [
                previous.projection.modules[0].manifest,
                *(p.manifest for p in previous.projection.packages),
            ]:
                path = root / body.relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                data = body.body
                if body is previous.projection.modules[0].manifest:
                    data = data.replace(
                        b'dependency_targets = {state="present", value=[]}',
                        b'dependency_targets = {state="present", value=[{dependency_kind="module", dependency_ref="self", targets=[{module_id="demo", package_id="home"}], constraints=[]}]}',
                    )
                path.write_bytes(data)
            with fenced_direct_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as sources:
                issuer = sources.semantic_issuer
                membership = sources.membership_runtime.admit(
                    observation=sources.observation,
                    workspace_manifest_path="aware.workspace.toml",
                    module_id="demo",
                    package_id="home",
                )
                context_input, inventory_value = issuer.inspect_inputs(membership)
                assert len(inventory_value.entries) == 1
                owner = Owner(
                    sources.scope_adapter.read_complete_scope_projection(
                        sources.scope_snapshot
                    )
                )
                entries = []
                for entry in old_state.check().entries:
                    values = {
                        f.name: getattr(entry, f.name)
                        for f in fields(entry)
                        if f.name != "binding_digest"
                    }
                    if entry.profile_declaration.profile_ref == "planning":
                        values["manifest_contracts"] = (SOURCE,)
                    entries.append(
                        CodeSemanticMaterializationProfileBinding.create(**values)
                    )
                catalog = _catalog(*entries)
                providers, planners = _execution_closure(catalog)
                admitted = _issue_code_semantic_contract_catalog(
                    catalog=catalog,
                    provider_executable_bindings=providers,
                    dependency_planner_bindings=planners,
                    host_liveness=lambda: owner.catalog_live,
                )
                resources = {b.role: b.resource for b in old_state.expected.resources}
                resources.update(
                    lifetime_runtime=owner,
                    composition_factory=owner,
                    scope_adapter=owner,
                    scope_runtime=sources.scope_runtime,
                    observation_runtime=sources.observation_runtime,
                    membership_runtime=sources.membership_runtime,
                    semantic_issuer=issuer,
                    catalog=admitted,
                )
                owner.expected = replace(
                    old_state.expected,
                    invocation_identity=object(),
                    epoch_identity=object(),
                    catalog=admitted,
                    resources=tuple(
                        DirectCommandResourceBinding(role, resource, "borrowed")
                        for role, resource in sorted(resources.items())
                    ),
                )
                bootstrap = direct._assemble_direct_command_bootstrap(
                    lifetime=owner.lifetime, expected=owner.expected
                )
                host = direct.register_direct_workspace_origin(
                    bootstrap, owner.lifetime
                )
                policy = direct.produce_registry_policy(host, owner.snapshot)
                request = replace(
                    request,
                    candidate_listing=semantic_candidate_listing_body(
                        sources.membership_runtime.evidence(
                            membership
                        ).candidate_listing
                    ),
                    package_context=retained_projection_body(context_input),
                    declaration_inventory=retained_projection_body(inventory_value),
                )
                context = contexts.begin_source_planning_operation(
                    host, policy, registration, request
                )
                expected = contexts.source_planning_expectation(host, context)
                issuer._bind_original_code_validator(
                    contexts.source_planning_context_validator(host)
                )
                _, inventory = issuer.issue_source_planning_pair(
                    membership, context=context, expected=expected
                )
                proposed = RetainedTargetExpectation(
                    expected,
                    context_input.source_identity_digest,
                    context_input.package,
                )
                target = issuer.select_dependency_target_admission(
                    inventory_admission=inventory, expected=proposed
                )
                origin = target_context.assemble_target_context_origin(host)
                admission = origin.issue(
                    context,
                    inventory,
                    target,
                    target_source_identity_digest=proposed.target_source_identity_digest,
                    target_package=proposed.target_package,
                )
                yield (
                    root,
                    host,
                    issuer,
                    origin,
                    admission,
                    context,
                    inventory,
                    target,
                    provider,
                )
    finally:
        if host is not None:
            direct.close_direct_validation_host(host)
        direct.close_direct_validation_host(old_host)


@pytest.mark.parametrize(
    "change", [None, "target", "inventory", "source", "issuer_close", "host_close"]
)
async def test_original_target_context_join(tmp_path, change):
    async with joined(tmp_path) as (
        root,
        host,
        issuer,
        origin,
        admission,
        context,
        inventory,
        target,
        provider,
    ):

        def read():
            return origin.read(
                admission,
                source_context=context,
                inventory_admission=inventory,
                target_admission=target,
            )

        result = read()
        assert result.package_role == "sdk"
        assert result.manifest_contract == SOURCE
        object.__setattr__(result.manifest_contract, "version", "foreign")
        assert read().manifest_contract.version == "1"
        assert provider.calls == 0
        if change is None:
            return
        if change == "target":
            target = object()
        elif change == "inventory":
            inventory = object()
        elif change == "source":
            (root / "demo/home/aware.demo.toml").write_bytes(b"changed")
        elif change == "issuer_close":
            issuer.close()
        else:
            direct.close_direct_validation_host(host)
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            read()


async def test_original_target_fields_feed_existing_capability_matcher(tmp_path):
    """Capability conformance only: requested intent is not an admitted demand."""
    async with joined(tmp_path) as (
        _, host, _, origin, admission, context, inventory, target, provider
    ):
        state = direct._state(host)
        catalog = state.expected.catalog
        resolver = CodeSemanticContractCatalogResolver(catalog)
        binding = next(
            entry for entry in state.check().entries
            if entry.profile_declaration.profile_ref == "planning"
        )
        requested = _context(binding)
        expected = contexts.source_planning_expectation(host, context)

        def read():
            return origin.read(
                admission,
                source_context=context,
                inventory_admission=inventory,
                target_admission=target,
            )

        original = read()

        def planning_context(**changes):
            values = dict(
                package=expected.package,
                package_family=original.package_family,
                package_role=original.package_role,
                manifest_contract=original.manifest_contract,
                code_intent=requested.code_intent,
                required_result_products=requested.required_result_products,
                required_semantic_provider_keys=(),
            )
            values.update(changes)
            return CodeSemanticPackagePlanningContext.create(**values)

        selected_context = planning_context()
        match, match_admission = resolver.resolve(selected_context)
        assert match.selected_entry_digest == binding.binding_digest
        assert read() == original
        encoded = encode_code_semantic_contract_match_admission(
            match_admission, context=selected_context, resolver=resolver
        )
        assert encoded

        # Valid target membership does not imply any requested capability.
        product = requested.required_result_products[0]
        for changes in (
            {"package_role": "unsupported"},
            {"required_semantic_provider_keys": ("unsupported",)},
            {"manifest_contract": replace(original.manifest_contract, version="2")},
            {"required_result_products": (
                CodeSemanticRequiredResultProduct.create(
                    role=product.role,
                    contract=replace(product.contract, version="2"),
                ),
            )},
        ):
            with pytest.raises(ContractViolation, match="semantic_contract_match_absent"):
                resolver.resolve(planning_context(**changes))
            assert read() == original

        # Retained portable matches cannot outlive the original catalog.
        _revoke_code_semantic_contract_catalog(catalog)
        with pytest.raises(ContractViolation):
            read()
        with pytest.raises(ContractViolation):
            resolver.resolve(selected_context)
        with pytest.raises(ContractViolation):
            encode_code_semantic_contract_match_admission(
                match_admission, context=selected_context, resolver=resolver
            )
        assert provider.calls == 0
