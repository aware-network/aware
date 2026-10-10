"""Real local Code planning under one Workspace command, without installation.

The existing SDK stage pair is an execution/lifetime regression supplier only.
It is not selected as the Storage canary and grants no Meta/store authority.
"""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    RetainedSourcePlanningRequest,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticBody,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
    selected_provider,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodePortableSemanticContract,
    CodeSemanticRegistryPackageInput,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    semantic_candidate_listing_body,
)
from aware_sdk_contract_runtime_provider import construct_sdk_stage_factory_product
from aware_sdk_contract_runtime_provider.planning_stage import (
    BINDING,
    MANIFEST_SOURCE_REF,
    MEANING_ROLE,
    sdk_planning_body_codec_bindings,
)
from aware_workspace_materialize_transport import (
    WorkspaceMaterializeCommandProposalV3,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.local_materialize_command import (
    compose_local_materialize_command,
)
from test_current_head_two_stage_host import qualified_sdk_five_target_repository
from test_dependency_scope_admission import fixture as sources


@pytest.fixture(scope="module")
def original_factory():
    return selected_provider._admit_selected_provider_factory(
        factory_ref="test.workspace.local-command.sdk-stage-pair",
        provider_key="aware_sdk",
        selection_factory=construct_sdk_stage_factory_product,
    )


def proposal(root):
    return WorkspaceMaterializeCommandProposalV3.create(
        attempt_ref="workspace-materialize-attempt:local-execution",
        participant_checkout_root=str(root),
        workspace_manifest_name="consumer/aware.workspace.toml",
        package_address=("Consumer", "main", "home"),
        plan_only=True,
    )


def coordinates():
    digest = ContentDigest.of_bytes(b"local command test composition")
    return {
        "composition_implementation": SemanticImplementationCoordinate("test.local", digest),
        "composition_configuration": SemanticConfigurationCoordinate("test.local", digest),
        "policy_implementation": SemanticImplementationCoordinate("test.local", digest),
        "policy_configuration": SemanticConfigurationCoordinate("test.local", digest),
    }


def planning_inputs(local):
    stage = local.host.staged.stage_runtime_bindings[0]
    profile = stage.runtime.profile
    code_host = local.host.code_host
    issuer = local.host.staged.command.sources.declaration_scope_runtime
    source = local.selected_source
    policy = direct_host.produce_registry_policy(code_host, source)
    grant = direct_host.validate_admitted_registry_policy(code_host, policy).grants[0]
    package, inventory = issuer.inspect_inputs(source)
    selected = issuer.read_selected_package_source(source)
    raw = local.host.staged.command.sources.observation_runtime.read_selected_package(
        issuer._selected_record(source).observation,
        relative_path="aware.sdk.toml",
    )
    registry = CodeSemanticRegistryPackageInput(
        "aware_sdk_toml", "aware.sdk.toml", "aware_sdk", "public", "sdk",
        CodePortableSemanticContract(
            "aware_sdk.provider", "sdk_definition", "aware_sdk",
            "code.semantic-contract:aware_sdk.provider",
        ),
        ("aware",), None, grant.namespace, grant.owned_roots,
        profile.profile_ref, profile.version, profile.digest, BINDING,
    )
    request = RetainedSourcePlanningRequest(
        SemanticBody(
            SemanticValueCoordinate(
                "manifest_source", MANIFEST_SOURCE_REF,
                "source:original-local-sdk-manifest", ContentDigest.of_bytes(raw), len(raw),
            ), raw,
        ),
        semantic_candidate_listing_body(selected.candidates),
        retained_projection_body(registry), retained_projection_body(package),
        retained_projection_body(inventory),
    )
    bodies = tuple(sorted((
        request.manifest_source, request.candidate_listing, request.registry_package,
        request.package_context, request.declaration_inventory,
    ), key=lambda body: body.coordinate.role))
    invocation = SemanticContractInvocation(
        invocation_ref="test:local-command-planning",
        idempotency_key="test:local-command-planning",
        profile_ref=profile.profile_ref, profile_digest=profile.digest,
        target_package=package.package, operation_kind="materialize",
        inputs=tuple(body.coordinate for body in bodies),
        predecessor=TypedEmptyCoordinate(profile.providers[0].result_role.contract),
        dependencies=(), body_codec_bindings=sdk_planning_body_codec_bindings(),
        provider_bindings=(BINDING,), requested_output_roles=(MEANING_ROLE,),
    )
    return request, invocation


async def test_local_command_executes_original_planning_and_retires_host(
    tmp_path, original_factory,
):
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with compose_local_materialize_command(
            proposal=proposal(root), session=borrowed._session, store=borrowed._store,
            factory_admission=original_factory, **coordinates(),
        ) as local:
            command = local.host.staged.command
            assert command.sources.observation_runtime._session is borrowed._session
            assert local.provider_key == "aware_sdk"
            request, invocation = planning_inputs(local)
            completion = local.execute_planning(request=request, invocation=invocation)
            stage = local.host.staged.stage_runtime_bindings[0]
            assert stage.runtime.owns_completion(completion)
            assert completion.result.status.value == "delta"
            assert command.lifetime_runtime in composition._COMMAND_ASSEMBLIES
            local.validate()
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES
        assert local.host.code_host not in direct_host._HOSTS
        assert borrowed._session.authority_admitted
        with pytest.raises(RuntimeError):
            local.validate()


async def test_local_command_changed_source_refuses_before_owner_execution(
    tmp_path, original_factory,
):
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with pytest.raises(SourceObservationUnavailable):  # noqa: SIM117 - inspect closed host afterward
            with compose_local_materialize_command(
                proposal=proposal(root), session=borrowed._session, store=borrowed._store,
                factory_admission=original_factory, **coordinates(),
            ) as local:
                request, invocation = planning_inputs(local)
                manifest = root / "consumer/modules/main/home/aware.sdk.toml"
                manifest.write_bytes(manifest.read_bytes() + b"\n# changed after capture\n")
                local.execute_planning(request=request, invocation=invocation)
        assert local.host.code_host not in direct_host._HOSTS


async def test_local_command_failure_closes_host_but_preserves_borrowed_sources(
    tmp_path, original_factory,
):
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with pytest.raises(RuntimeError, match="consumer failed"):  # noqa: SIM117 - inspect closed host afterward
            with compose_local_materialize_command(
                proposal=proposal(root), session=borrowed._session, store=borrowed._store,
                factory_admission=original_factory, **coordinates(),
            ) as local:
                raise RuntimeError("consumer failed")
        assert local.host.code_host not in direct_host._HOSTS
        assert local.host.staged.command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES
        assert borrowed._session.authority_admitted


async def test_local_command_substituted_invocation_refuses(
    tmp_path, original_factory,
):
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        with pytest.raises(Exception, match="(input|differ|closure|planning)"):  # noqa: SIM117 - inspect closed host afterward
            with compose_local_materialize_command(
                proposal=proposal(root), session=borrowed._session, store=borrowed._store,
                factory_admission=original_factory, **coordinates(),
            ) as local:
                request, invocation = planning_inputs(local)
                local.execute_planning(
                    request=request, invocation=replace(invocation, inputs=invocation.inputs[:-1]),
                )
        assert local.host.code_host not in direct_host._HOSTS


async def test_local_command_wrong_repository_refuses_before_host(tmp_path, original_factory):
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        original = proposal(root)
        proposed = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref=original.attempt_ref,
            participant_checkout_root=str(tmp_path / "other"),
            workspace_manifest_name=original.workspace_manifest_name,
            package_address=original.package_address, plan_only=True,
        )
        before = tuple(composition._COMMAND_ASSEMBLIES)
        with pytest.raises(RuntimeError, match="original repository binding"), compose_local_materialize_command(
            proposal=proposed, session=borrowed._session, store=borrowed._store,
            factory_admission=original_factory, **coordinates(),
        ):
            pytest.fail("wrong repository admitted")
        assert tuple(composition._COMMAND_ASSEMBLIES) == before
        assert borrowed._session.authority_admitted


async def test_local_command_foreign_factory_cannot_create_host(tmp_path):
    async with sources(tmp_path, qualified_sdk_five_target_repository) as (
        root, _, _, borrowed, _, _,
    ):
        before = tuple(composition._COMMAND_ASSEMBLIES)
        with pytest.raises(TypeError, match="factory"), compose_local_materialize_command(
            proposal=proposal(root), session=borrowed._session, store=borrowed._store,
            factory_admission=object(), **coordinates(),
        ):
            pytest.fail("foreign factory admitted")
        assert tuple(composition._COMMAND_ASSEMBLIES) == before
        assert borrowed._session.authority_admitted
