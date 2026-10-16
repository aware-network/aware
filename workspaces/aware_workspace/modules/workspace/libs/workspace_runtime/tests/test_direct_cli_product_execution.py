"""Real owner recipe through original Workspace input/node custody."""

from contextlib import ExitStack
from pathlib import Path

import pytest
from aware_code_retained_registry_policy_runtime import product_execution
from aware_code_retained_registry_policy_runtime import (
    product_execution_inputs as inputs,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
)
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as _factory
from test_single_product_command_composition import _attention_repository

from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.direct_cli_product_execution import (
    execute_direct_cli_selected_product,
)

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
