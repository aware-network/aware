"""Real owner recipe through original Workspace input/node custody."""

from contextlib import ExitStack, contextmanager
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_retained_registry_policy_runtime import product_execution
from aware_code_retained_registry_policy_runtime import (
    product_execution_inputs as inputs,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.direct_cli_product_execution import (
    execute_direct_cli_selected_product,
)
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as _factory
from test_single_product_command_composition import _attention_repository

factory = _factory
HOME = (
    Path(__file__).resolve().parents[6]
    / "aware_home/modules/home/attentions/home_story_app_shell"
)


def authored(root):
    _attention_repository(root)
    package = root / "consumer/modules/main/attention"
    (package / "source.aware").unlink()
    for path in HOME.iterdir():
        if path.is_file():
            (package / path.name).write_bytes(path.read_bytes())
    module = root / "consumer/modules/main/aware.module.toml"
    module.write_text(
        module.read_text().replace("sample_attention", "home_story_app_shell")
    )


async def test_genuine_recipe_completion_and_host_before_input_cleanup(
    tmp_path, factory, monkeypatch
):
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    released = []
    original_close = SemanticInputProducerHost.close

    def close(input_host):
        assert not any(
            record.host is host for record in product_execution._READ_ORIGINS.values()
        )
        assert not any(
            record.host is host for _, record in composition._SELECTED_INPUT_NODES
        )
        released.append(True)
        original_close(input_host)

    monkeypatch.setattr(SemanticInputProducerHost, "close", close)
    async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session,
            store=borrowed._store,
            proposal=_proposal(root),
        ) as (command, _, source):
            with (
                ExitStack() as retained,
                local.compose_direct_cli_selected_product(command, source) as product,
            ):
                host = product.host.code_host
                result = await execute_direct_cli_selected_product(
                    command, source, product, retention=retained
                )
                assert result.snapshot.result.status.value == "delta"
                assert any(
                    body.coordinate.role == "attention_definition_manifest"
                    for body in result.snapshot.bodies
                )
                assert not released
            assert released == [True]
            composition._require_live_direct_workspace_command(command)


async def test_mutation_after_input_production_refuses_before_selected_execution(
    tmp_path, factory, monkeypatch
):
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    original = inputs.execute_product_execution_inputs
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        pytest.fail("mutated input reached selected execution")

    monkeypatch.setattr(
        "aware_workspace_runtime.direct_cli_product_execution.selected_provider.execute_selected_provider",
        forbidden,
    )
    async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):

        async def mutate(*args, **kwargs):
            result = await original(*args, **kwargs)
            manifest = root / "consumer/modules/main/attention/aware.attention.toml"
            manifest.write_bytes(manifest.read_bytes() + b"\n# changed\n")
            return result

        monkeypatch.setattr(inputs, "execute_product_execution_inputs", mutate)
        with (  # noqa: SIM117 - inspect original retirement after the command unwinds
            pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)) as rejected
        ):
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, source):
                with (
                    ExitStack() as retained,
                    local.compose_direct_cli_selected_product(
                        command, source
                    ) as product,
                ):
                    host = product.host.code_host
                    await execute_direct_cli_selected_product(
                        command, source, product, retention=retained
                    )

        def leaves(error):
            if isinstance(error, BaseExceptionGroup):
                return tuple(
                    leaf for child in error.exceptions for leaf in leaves(child)
                )
            return (error,)

        assert any(
            isinstance(error, SourceObservationUnavailable)
            for error in leaves(rejected.value)
        )
        assert not any(
            record.host is host for record in product_execution._READ_ORIGINS.values()
        )
        assert not any(
            record.host is host for _, record in composition._SELECTED_INPUT_NODES
        )
        assert not calls


async def test_foreign_product_rejects_before_recipe_intake(
    tmp_path, factory, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        inputs, "enroll_product_execution_inputs", lambda *args: calls.append(True)
    )
    with ExitStack() as retained, pytest.raises(TypeError, match="original selected"):
        await execute_direct_cli_selected_product(
            None, None, object(), retention=retained
        )
    assert not calls


@contextmanager
def selection_owner(monkeypatch, calls):
    """Neutral test meaning; original Code admission and Workspace readers."""
    from aware_code_semantic_contract_runtime import selected_provider as selected
    from aware_code_semantic_contract_runtime.product_execution_input_plan import (
        ProductExecutionInputSourceScope,
        ProductExecutionInputStep,
    )
    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        PackageContextInputCodec,
    )
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputContextContract,
        SemanticInputSourceContract,
    )
    from aware_code_semantic_contract_runtime.source_origin import (
        SOURCE_ORIGIN_REF,
        decode_source_origin,
    )
    from aware_code_semantic_contract_runtime.source_selection import (
        SOURCE_SELECTION_REF,
        SemanticSelectedSource,
        SemanticSourceSelection,
        decode_source_selection,
        source_selection_body,
    )
    from product_supplier_fixture import supplier_factory
    from test_direct_cli_dependency_planning import (
        ROOT_KEY,
        SUPPLIER_KEY,
        _contract,
        _owner_factory,
    )

    root = _owner_factory(ROOT_KEY, calls)
    original_admit = selected._admit_selected_provider_factory
    seen = []

    def admit(*, selection_factory, **kwargs):
        def construct():
            product = selection_factory()
            original_recipe = product.execution_input_contribution_producer

            def recipe(contribution):
                plan = original_recipe(contribution)
                original, = plan.steps
                raw = original.ordinary.source_contracts[0].contract
                manifest = _contract("proof.raw-manifest")
                context = SemanticInputContextContract("package_context", PackageContextInputCodec.contract)

                def select(value):
                    package_context = PackageContextInputCodec().decode(value.context_bodies[0].canonical_body)
                    return source_selection_body(SemanticSourceSelection(
                        value.package_identity.package, package_context.source_identity_digest,
                        value.input_digest, (), tuple(SemanticSelectedSource(
                            "manifest_source" if source.source.relative_path.endswith(".toml") else "authored_source",
                            manifest if source.source.relative_path.endswith(".toml") else raw,
                            source.source.relative_path, source.source.coordinate.digest,
                        ) for source in value.sources),
                    ), role="selected_sources")

                def prepare(value):
                    _, selection_body, origin_body = value.context_bodies
                    selection = decode_source_selection(selection_body.canonical_body)
                    origin = decode_source_origin(origin_body.canonical_body)
                    assert origin.selection_coordinate.digest == selection_body.coordinate.digest
                    assert origin.outer_manifest.relative_path in {item.relative_path for item in selection.sources}
                    assert {item.source.coordinate.role for item in value.sources} == {"manifest_source", "authored_source"}
                    assert {item.source.coordinate.contract for item in value.sources} == {raw, manifest}
                    seen.append((selection, origin))
                    return original.producer(value)

                first = replace(original.ordinary, producer_ref=original.ordinary.producer_ref + ".selection",
                    result_role="selected_sources", result_contract=SOURCE_SELECTION_REF, context_contracts=(context,))
                final = replace(original.ordinary, source_contracts=(
                    SemanticInputSourceContract("authored_source", raw),
                    SemanticInputSourceContract("manifest_source", manifest),
                ), context_contracts=(
                    context,
                    SemanticInputContextContract("selected_sources", SOURCE_SELECTION_REF),
                    SemanticInputContextContract("source_origin", SOURCE_ORIGIN_REF),
                ))
                return replace(plan, steps=(
                    ProductExecutionInputStep("selection", first, select, original.source_scopes),
                    ProductExecutionInputStep(original.stage, final, prepare, (
                        ProductExecutionInputSourceScope("authored_source"),
                        ProductExecutionInputSourceScope("manifest_source"),
                    ), source_selection_index=0),
                ), input_result_indices=(1,))

            return replace(product, execution_input_contribution_producer=recipe)

        return original_admit(selection_factory=construct, **kwargs)

    monkeypatch.setattr(selected, "_admit_selected_provider_factory", admit)
    supplier = None
    try:
        supplier = supplier_factory(calls)
        yield {ROOT_KEY: root, SUPPLIER_KEY: supplier}, seen
    finally:
        for value in (root, supplier):
            if value is None:
                continue
            admission, _ = value
            state = selected._factory_state(admission)
            if selected._FACTORY_PROVIDER_KEYS.get(state.provider_key) is admission:
                del selected._FACTORY_PROVIDER_KEYS[state.provider_key]
            if selected._FACTORY_REFS.get(state.factory_ref) is admission:
                del selected._FACTORY_REFS[state.factory_ref]
            selected._FACTORIES.pop(id(admission), None)


@pytest.mark.parametrize("poison", [None, "copied_return", "changed_source"])
async def test_original_selection_roles_and_origin_reach_recipe_execution(tmp_path, monkeypatch, poison):
    from aware_code_semantic_contract_runtime import ContractViolation
    from aware_workspace_materialize_transport import (
        WorkspaceMaterializeCommandProposalV3,
    )
    from test_direct_cli_dependency_planning import _repository

    calls = []
    with selection_owner(monkeypatch, calls) as (owners, seen):
        monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: owners[key][0])
        profiles = {key: profile for key, (_, profile) in owners.items()}
        async with sources(tmp_path, lambda root: _repository(root, profiles)) as (root, _, _, borrowed, _, _):
            original_step = inputs.execute_product_execution_input_step

            async def step(*args, **kwargs):
                result = await original_step(*args, **kwargs)
                if len(kwargs["expectations"]) == 1:
                    if poison == "copied_return":
                        return replace(result)
                    if poison == "changed_source":
                        manifest = root / "consumer/modules/main/supplier/aware.example.toml"
                        manifest.write_bytes(manifest.read_bytes() + b"\n# changed after selection\n")
                return result

            monkeypatch.setattr(inputs, "execute_product_execution_input_step", step)
            proposal = WorkspaceMaterializeCommandProposalV3.create(
                attempt_ref="proof:original-recipe-selection", participant_checkout_root=str(root),
                workspace_manifest_name="consumer/aware.workspace.toml",
                package_address=("Consumer", "main", "supplier"), plan_only=True,
            )
            with ExitStack() as refusal:
                if poison is not None:
                    caught = refusal.enter_context(pytest.raises((
                        SourceObservationUnavailable, ContractViolation, BaseExceptionGroup,
                    )))
                with composition._compose_direct_workspace_command_source(
                    session=borrowed._session, store=borrowed._store, proposal=proposal,
                ) as (command, _, source), ExitStack() as retained, local.compose_direct_cli_selected_product(command, source) as product:
                    result = await execute_direct_cli_selected_product(command, source, product, retention=retained)
                    assert poison is None, "changed originals must never reach selected execution"
                    assert result.snapshot.result.status.value == "delta"
                    assert len(seen) == 1
                    assert len(composition._SELECTED_INPUT_NODES) == 1
            if poison is not None:
                def leaves(error):
                    if isinstance(error, BaseExceptionGroup):
                        return tuple(leaf for child in error.exceptions for leaf in leaves(child))
                    return (error,)

                assert any(isinstance(error, (SourceObservationUnavailable, ContractViolation))
                           for error in leaves(caught.value))
                assert not seen
                assert not any(item[0] == "execute" for item in calls)
            assert not composition._SELECTED_INPUT_NODES
