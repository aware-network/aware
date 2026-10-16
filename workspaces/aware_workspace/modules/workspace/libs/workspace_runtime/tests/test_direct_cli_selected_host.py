"""Original host/lifetime binding; factory fixtures are explicitly source grade.

The real public command separately qualifies actual local metadata. These tests
reuse the original Attention source factory and Workspace observations; they
never construct a registration, policy, receipt or catalog as a substitute.
"""

import pytest
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_semantic_contract_runtime import ContractViolation
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from test_single_product_command_composition import (
    _attention_repository,
    sources,
)
from test_single_product_command_composition import (
    factory as original_factory_fixture,
)


@pytest.fixture(scope="module")
def factory():
    from aware_code_semantic_contract_runtime import selected_provider as selected

    key = "attention-layout-definition"
    existing = selected._FACTORY_PROVIDER_KEYS.get(key)
    if existing is not None:
        yield existing
        return
    original = original_factory_fixture.__wrapped__()
    state = selected._factory_state(original)
    try:
        yield original
    finally:
        # Isolate only this source-grade fixture enrollment. The real CLI proof
        # uses a fresh process and original installed intake instead.
        if selected._FACTORY_PROVIDER_KEYS.get(key) is original:
            del selected._FACTORY_PROVIDER_KEYS[key]
        if selected._FACTORY_REFS.get(state.factory_ref) is original:
            del selected._FACTORY_REFS[state.factory_ref]
        if selected._FACTORIES.get(id(original), (None,))[0] is original:
            del selected._FACTORIES[id(original)]


def _proposal(root):
    return WorkspaceMaterializeCommandProposalV3.create(
        attempt_ref="workspace-materialize-attempt:public-product-host",
        participant_checkout_root=str(root),
        workspace_manifest_name="consumer/aware.workspace.toml",
        package_address=("Consumer", "main", "attention"),
        plan_only=True,
    )


async def test_original_product_host_remains_inside_one_command(
    tmp_path, factory, monkeypatch
):
    requested = []

    def admit(key):
        requested.append(key)
        return factory

    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", admit)
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session,
            store=borrowed._store,
            proposal=_proposal(root),
        ) as (command, _, selected):
            with local.compose_direct_cli_selected_product(
                command, selected
            ) as product:
                assert product.host.staged.command is command
                assert product.provider_key == "attention-layout-definition"
                assert product.requested_role == "attention_definition_manifest"
                assert product.package_ref == "package:sample_attention@1"
                assert (
                    product.host.catalog_pair.workspace.package_if_present(
                        product.package_ref
                    )
                    is not None
                )
                assert product.catalog_timing_ns >= 0
                assert product.host.staged.stage_runtime_bindings == ()
                original = product.host.staged.product_contributions[0]
                code_host = product.host.code_host
                products.read_selected_provider_product_contribution(original)
            composition._require_live_direct_workspace_command(command)
            assert code_host not in direct_host._HOSTS
            with pytest.raises(ContractViolation):
                products.read_selected_provider_product_contribution(original)
        with pytest.raises(RuntimeError):
            composition._require_live_direct_workspace_command(command)
    assert requested == ["attention-layout-definition"]


async def test_missing_factory_does_not_assemble_a_catalog(tmp_path, monkeypatch):
    def unavailable(key):
        raise ContractViolation("unique installed semantic provider factory required")

    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", unavailable)
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session,
            store=borrowed._store,
            proposal=_proposal(root),
        ) as (command, _, selected):
            before = set(products._CONTRIBUTIONS)
            with (
                pytest.raises(
                    local.DirectCLIProviderFactoryUnavailable,
                    match="attention-layout-definition",
                ),
                local.compose_direct_cli_selected_product(command, selected),
            ):
                pytest.fail("missing factory opened a host")
            assert set(products._CONTRIBUTIONS) == before
            composition._require_live_direct_workspace_command(command)


async def test_source_move_during_factory_intake_rejects_before_catalog(
    tmp_path, factory, monkeypatch
):
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):

        def change(key):
            path = root / "consumer/modules/main/attention/source.aware"
            path.write_bytes(
                path.read_bytes() + b"\nchanged while loading executable\n"
            )
            return factory

        monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", change)
        before = set(products._CONTRIBUTIONS)
        with pytest.raises(SourceObservationUnavailable):  # noqa: SIM117 - retain handles for cleanup assertions
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, selected):
                with local.compose_direct_cli_selected_product(command, selected):
                    pytest.fail("changed source opened a host")
        assert set(products._CONTRIBUTIONS) == before
        assert command.lifetime_runtime not in composition._COMMAND_ASSEMBLIES


async def test_foreign_factory_cannot_supply_product_registration(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: object()
    )
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session,
            store=borrowed._store,
            proposal=_proposal(root),
        ) as (command, _, selected):
            before = set(products._CONTRIBUTIONS)
            with (
                pytest.raises(TypeError, match="factory"),
                local.compose_direct_cli_selected_product(command, selected),
            ):
                pytest.fail("foreign factory opened a host")
            assert set(products._CONTRIBUTIONS) == before
            composition._require_live_direct_workspace_command(command)


@pytest.mark.parametrize("failure", ["consumer", "source"])
async def test_host_terminal_cleanup_preserves_borrowed_command(
    tmp_path, factory, monkeypatch, failure
):
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        expected_error = (
            RuntimeError if failure == "consumer" else SourceObservationUnavailable
        )
        with pytest.raises(expected_error):  # noqa: SIM117 - retain handles for cleanup assertions
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, selected):
                with local.compose_direct_cli_selected_product(
                    command, selected
                ) as product:
                    code_host = product.host.code_host
                    original = product.host.staged.product_contributions[0]
                    if failure == "consumer":
                        raise RuntimeError("consumer failed")
                    path = root / "consumer/modules/main/attention/source.aware"
                    path.write_bytes(
                        path.read_bytes() + b"\nchanged after host admission\n"
                    )
        assert code_host not in direct_host._HOSTS
        with pytest.raises(ContractViolation):
            products.read_selected_provider_product_contribution(original)
        assert borrowed._session.authority_admitted


def test_local_coordinates_identify_actual_source_and_fixed_configuration():
    from pathlib import Path

    from aware_code_semantic_contract_runtime import ContentDigest

    values = local._coordinates()
    assert values[
        "composition_implementation"
    ].closure_digest == ContentDigest.of_bytes(Path(composition.__file__).read_bytes())
    assert (
        values["composition_configuration"]
        == local._coordinates()["composition_configuration"]
    )


@pytest.mark.parametrize("plan_only", [True, False])
def test_public_command_uses_actual_local_factory_and_returns_original_graph_plan(
    tmp_path,
    monkeypatch,
    plan_only,
):
    import json
    import subprocess
    from pathlib import Path

    from test_direct_live_profile_selection import _repository

    root = tmp_path / "repository"
    _repository(root)
    # Reuse the generic original Workspace fixture, then author the exact real
    # Attention declaration before observation. No executable or metadata stub.
    consumer = root / "consumer"
    (root / "workspaces/kernel").rename(consumer)
    (consumer / "modules/main/provider/pyproject.toml").unlink()
    (consumer / "modules/main/provider").rmdir()
    target = root / "target/modules/main"
    target.mkdir(parents=True)
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\n[[workspaces]]\nhandle="Consumer"\npath="consumer"\n'
        '[[workspaces]]\nhandle="Target"\npath="target"\n'
    )
    (consumer / "aware.workspace.toml").write_text(
        'aware=1\n[workspace]\nhandle="Consumer"\n[[workspace.modules]]\nid="main"\npath="modules/main"\n'
    )
    (root / "target/aware.workspace.toml").write_text(
        'aware=1\n[workspace]\nhandle="Target"\n'
    )
    # The helper's local-product case needs no imported profile entitlement.
    _attention_repository(root)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    # A source-grade factory already occupies this key in the fixture process.
    # Use the real CLI's fresh process for original installed-key admission.
    captured = subprocess.run(
        [
            str(Path(__file__).resolve().parents[7] / ".venv/bin/aware-cli"),
            "workspace",
            "materialize",
            "--repo-root",
            str(root),
            "--workspace-toml",
            "consumer/aware.workspace.toml",
            "--package-address",
            "Consumer:main:attention",
            *(["--plan"] if plan_only else []),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    payload = json.loads(captured.stdout)
    assert captured.returncode == (0 if plan_only else 2)
    assert captured.stderr.strip() == (
        "" if plan_only else
        "selected_product_execution_inputs_unavailable: package:sample_attention@1"
    )
    assert payload["outcome"] == ("succeeded" if plan_only else "blocked")
    assert payload["terminal_stage"] == "graph_plan"
    assert payload["operation"]["plan_result"]["graph"]["nodes"][0]["package"]["package_ref"] == "package:sample_attention@1"
    counters = {row["counter"]: row["value"] for row in payload["host_counters"]}
    assert counters["catalog_observation_count"] == 1
    assert counters["selected_package_count"] == 1
    assert counters["graph_node_count"] == 1
    assert counters["graph_execution_count"] == 0
    assert not list((tmp_path / "state").rglob("command-*"))
