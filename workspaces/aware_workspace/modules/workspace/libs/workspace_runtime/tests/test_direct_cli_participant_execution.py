"""Original selected sources through the same host and tracked owner executor.

The original Attention factory is source-admitted by the fixture. No installed
factory qualification, dependency fulfillment or public publication is implied.
"""

import re
from contextlib import ExitStack, asynccontextmanager
from dataclasses import replace
from shutil import copytree

import pytest
from aware_code_semantic_contract_runtime import ContractViolation, selected_provider

# isort: split

from aware_workspace_runtime import direct_cli_product_execution as execution
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition

# isort: split

from test_direct_cli_dependency_planning import SUPPLIER_KEY
from test_direct_cli_dependency_planning import owners as fixture_owners
from test_direct_cli_product_execution import authored
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as original_factory
from test_observed_semantic_issuers import PROVIDER, occurrence

factory = original_factory
owners = fixture_owners


def observe_selected_invocations(monkeypatch):
    original = selected_provider.issue_selected_provider_execution
    invocations = []

    def issue(runtime, registration, semantic_input, **kwargs):
        admission = original(runtime, registration, semantic_input, **kwargs)
        invocations.append(semantic_input.invocation)
        return admission

    monkeypatch.setattr(selected_provider, "issue_selected_provider_execution", issue)
    return invocations


def two_packages(root):
    authored(root)
    module = root / "consumer/modules/main/aware.module.toml"
    text = module.read_text()
    first = text.index("[[packages]]")
    end = text.index("\n[[plugins]]\n", first + 1) + 1
    declaration = text[first:end]
    second = declaration.replace('id="attention"', 'id="second"').replace(
        'manifest="attention/', 'manifest="second/'
    ).replace("home_story_app_shell", "second_shell")
    module.write_text(text + "\n" + second)
    path = root / "consumer/modules/main/second"
    copytree(path.with_name("attention"), path)
    for member in path.iterdir():
        if member.is_file():
            member.write_bytes(member.read_bytes().replace(b"home_story_app_shell", b"second_shell"))


@asynccontextmanager
async def original_pair(tmp_path, monkeypatch, factory, *, other=None):
    def author(root):
        two_packages(root)
        if other is None:
            return
        module = root / "consumer/modules/main"
        (module / "other").mkdir()
        (module / "other/aware.example.toml").write_bytes(b"original other manifest")
        (module / "other_provider").mkdir()
        (module / "other_provider/pyproject.toml").write_bytes(b"other original owner distribution")
        semantic = occurrence("other").replace(
            'value={module_id="main",package_id="provider",',
            'value={scope={kind="local"},module_id="main",package_id="other_provider",',
        )
        profile = other[1]
        declaration = PROVIDER.replace('id="provider"', 'id="other_provider"').replace(
            'manifest="provider/pyproject.toml"', 'manifest="other_provider/pyproject.toml"',
        ).replace('provider_key="demo"', f'provider_key="{SUPPLIER_KEY}"')
        declaration = re.sub(r"profiles=\[.*?\n\]", (
            'profiles=[{stage="graph_product",profile_ref="' + profile.profile_ref
            + '",profile_version="' + profile.version + '",profile_digest="'
            + profile.digest.to_wire() + '"}]'
        ), declaration, flags=re.DOTALL)
        path = module / "aware.module.toml"
        path.write_text(path.read_text() + '\n[[packages]]\nid="other"\nkind="example"\nmanifest="other/aware.example.toml"\n' + semantic + declaration)

    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: other[0] if other is not None and key == SUPPLIER_KEY else factory)
    async with sources(tmp_path, author) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=_proposal(root),
        ) as (command, _, source), ExitStack() as resources:
            second = resources.enter_context(composition._compose_direct_workspace_selected_package_source(
                command, workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main", package_id="second",
            ))
            participants = (source, second)
            if other is not None:
                participants += (resources.enter_context(composition._compose_direct_workspace_selected_package_source(
                    command, workspace_manifest_path="consumer/aware.workspace.toml",
                    module_id="main", package_id="other",
                )),)
            with ExitStack() as retained, local.compose_direct_cli_selected_product(
                command, source, participating_sources=participants,
            ) as product:
                yield root, command, source, second, product, retained
            assert not any(record.host is product.host.code_host for _, record in composition._SELECTED_INPUT_NODES)


async def test_nonroot_original_source_executes_under_shared_host(tmp_path, monkeypatch, factory):
    issued = observe_selected_invocations(monkeypatch)
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, source, second, product, retained):
        result = await execution.execute_direct_cli_selected_product(
            command, second, product, retention=retained,
        )
        assert result.snapshot.result.status.value == "delta"
        assert len(issued) == 1 and issued[0].digest == result.snapshot.invocation_digest
        assert issued[0].target_package.package_ref == product.participants[1].package_ref
        assert issued[0].target_package.package_ref != product.package_ref
        assert command.sources.declaration_scope_runtime.inspect_inputs(source)[0].package.package_ref == product.package_ref
        assert len(product.host.staged.product_contributions) == 1
        composition._require_live_direct_workspace_command(command)


async def test_nonroot_execution_selects_original_registration_among_two_factories(tmp_path, monkeypatch, factory, owners):
    issued = observe_selected_invocations(monkeypatch)
    async with original_pair(tmp_path, monkeypatch, factory, other=owners[0][SUPPLIER_KEY]) as (_, command, _, second, product, retained):
        assert len(product.host.staged.product_contributions) == 2
        assert len(product.host.staged.product_runtime_bindings) == 2
        result = await execution.execute_direct_cli_selected_product(command, second, product, retention=retained)
        assert result.snapshot.result.status.value == "delta"
        assert len(issued) == 1 and issued[0].digest == result.snapshot.invocation_digest
        assert issued[0].target_package.package_ref == product.participants[1].package_ref
        assert owners[1] == []  # The unrelated factory performs no semantic work.


async def test_standalone_root_cannot_rebind_or_revoke_prior_completion(tmp_path, monkeypatch, factory):
    from aware_code_retained_registry_policy_runtime import product_execution_inputs

    issued = observe_selected_invocations(monkeypatch)
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, source, second, product, retained):
        first = await execution.execute_direct_cli_selected_product(command, second, product, retention=retained)
        with pytest.raises(ContractViolation, match="late or replayed execution lifecycle binding"):
            await execution.execute_direct_cli_selected_product(command, source, product, retention=retained)
        completion = product_execution_inputs.read_product_execution_input_completion(
            product.host.code_host, first.execution_context)
        assert issued[0].digest == product.host.staged.product_runtime_bindings[0].runtime.snapshot_completion(completion).invocation_digest
    assert len(issued) == 1


@pytest.mark.parametrize("later", ("complete", "cancel", "refuse"))
async def test_one_original_root_has_distinct_operation_inputs(tmp_path, monkeypatch, factory, later):
    from aware_code_retained_registry_policy_runtime import product_execution_inputs

    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, source, second, product, retained):
        execution._bind_direct_cli_product_execution_origins(command, product, (source, second))
        contexts = []
        completions = []
        first_input = None
        for current in (source, second):
            with ExitStack() as inputs:
                prepared = await execution.prepare_direct_cli_selected_product_inputs(
                    command, current, product, retention=inputs)
                contexts.append(prepared.execution_context)
                _, _, binding = execution._execution_participant(command, current, product)
                host = product.host.code_host
                retained.callback(product_execution_inputs.close_product_execution_input_context, host,
                                  prepared.execution_context)
                if current is second and later == "refuse":
                    with pytest.raises(ContractViolation):
                        selected_provider.issue_selected_provider_execution(binding.runtime, binding.registration,
                            first_input, operation_context=prepared.execution_context)
                    continue
                first_input = prepared.assembly.semantic_input
                admission = selected_provider.issue_selected_provider_execution(binding.runtime, binding.registration,
                    first_input, operation_context=prepared.execution_context)
                if current is second and later == "cancel":
                    product_execution_inputs.close_product_execution_input_context(host, prepared.execution_context)
                    with pytest.raises(ContractViolation):
                        selected_provider.execute_selected_provider(binding.runtime, admission)
                else:
                    completion = selected_provider.execute_selected_provider(binding.runtime, admission)
                    completions.append(completion)
            # Input readers have just retired; historical completion is still
            # available through the original outer operation retention.
            assert product_execution_inputs.read_product_execution_input_completion(host, contexts[0]) is completions[0]
        assert contexts[0] is not contexts[1]
        assert len(product.host.staged.product_runtime_bindings) == 1
        assert product_execution_inputs.read_product_execution_input_completion(host, contexts[0]) is completions[0]


@pytest.mark.parametrize("change", ["missing", "duplicate", "wrong_key", "wrong_package", "wrong_policy", "foreign_metadata"])
async def test_changed_participants_refuse_before_recipe(tmp_path, monkeypatch, factory, change):
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, _, second, product, retained):
        root, target = product.participants
        calls = []

        class Foreign:
            def __hash__(self):
                calls.append("hash")
                raise AssertionError("foreign hash")

            def __eq__(self, other):
                calls.append("equality")
                raise AssertionError("foreign equality")

        rows = {
            "missing": (root,),
            "duplicate": (root, target, target),
            "wrong_key": (root, target._replace(provider_key="different")),
            "wrong_package": (root, target._replace(package_ref="package:different@1")),
            "wrong_policy": (root, target._replace(policy=root.policy)),
            "foreign_metadata": (root, target._replace(provider_key=Foreign())),
        }
        changed = replace(product, participants=rows[change])
        monkeypatch.setattr(execution.inputs, "enroll_product_execution_inputs", lambda *args: calls.append("recipe"))
        with pytest.raises(ContractViolation):
            await execution.prepare_direct_cli_selected_product_inputs(command, second, changed, retention=retained)
        assert calls == []


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_original_contribution_reader_alias_refuses_without_dispatch(tmp_path, monkeypatch, factory, mode):
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, _, second, product, retained):
        original = execution.read_selected_provider_product_contribution
        calls = []

        def hostile(*args):
            calls.append(True)
            if mode == "restore":
                monkeypatch.setattr(execution, "read_selected_provider_product_contribution", original)
            if mode == "raise":
                raise AssertionError("hostile contribution reader")

        monkeypatch.setattr(execution, "read_selected_provider_product_contribution", hostile)
        with pytest.raises(ContractViolation, match="reader changed"):
            await execution.prepare_direct_cli_selected_product_inputs(command, second, product, retention=retained)
        assert not calls


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_original_policy_reader_refuses_without_dispatch(tmp_path, monkeypatch, factory, mode):
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, _, second, product, retained):
        original = execution.direct_host.validate_admitted_registry_policy
        calls = []

        def hostile(*args):
            calls.append(True)
            if mode == "restore":
                monkeypatch.setattr(execution.direct_host, "validate_admitted_registry_policy", original)
            if mode == "raise":
                raise AssertionError("hostile policy reader")

        with monkeypatch.context() as mutation:
            mutation.setattr(execution.direct_host, "validate_admitted_registry_policy", hostile)
            with pytest.raises(ContractViolation, match="policy reader changed"):
                await execution.prepare_direct_cli_selected_product_inputs(command, second, product, retention=retained)
            assert not calls


async def test_source_only_recipe_cannot_accept_portable_products(tmp_path, monkeypatch, factory):
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, _, second, product, retained):
        before = tuple(composition._SELECTED_INPUT_NODES)
        with pytest.raises(TypeError, match="admission tuple"):
            await execution.prepare_direct_cli_selected_product_inputs(
                command, second, product, retention=retained, dependency_admissions=object(),
            )
        with pytest.raises(ContractViolation, match="complete declared"):
            await execution.prepare_direct_cli_selected_product_inputs(
                command, second, product, retention=retained,
                dependency_admissions=execution.DirectCLIProductDependencyAdmissions(object(), object(), object(), object()),
            )
        assert tuple(composition._SELECTED_INPUT_NODES) == before


async def test_late_participant_change_refuses_before_selected_execution(tmp_path, monkeypatch, factory):
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, _, second, product, retained):
        original = execution.inputs.execute_product_execution_inputs
        calls = []

        async def change(*args, **kwargs):
            result = await original(*args, **kwargs)
            object.__setattr__(product, "participants", product.participants[:1])
            return result

        def forbidden(*args, **kwargs):
            calls.append(True)
            raise AssertionError("changed participant reached execution")

        monkeypatch.setattr(execution.inputs, "execute_product_execution_inputs", change)
        monkeypatch.setattr(selected_provider, "execute_selected_provider", forbidden)
        with pytest.raises(ContractViolation, match="unique original"):
            await execution.execute_direct_cli_selected_product(command, second, product, retention=retained)
        assert not calls


async def test_participant_change_at_selected_return_is_rejected(tmp_path, monkeypatch, factory):
    async with original_pair(tmp_path, monkeypatch, factory) as (_, command, _, second, product, retained):
        original = selected_provider.execute_selected_provider
        completions = []

        def change(*args, **kwargs):
            result = original(*args, **kwargs)
            completions.append(result)
            object.__setattr__(product, "participants", product.participants[:1])
            return result

        monkeypatch.setattr(selected_provider, "execute_selected_provider", change)
        with pytest.raises(ContractViolation, match="unique original"):
            await execution.execute_direct_cli_selected_product(command, second, product, retention=retained)
        assert len(completions) == 1
