"""Original Code factory mechanics; test products are not Environment qualification."""

import copy
from dataclasses import dataclass, replace
from uuid import uuid4

import pytest
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime import stage_contribution as stages
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    CodeSemanticRequiredResultProduct,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from test_profile_runtime import profile
from test_selected_provider import (
    _ARTIFACT,
    _BINDING,
    _CONFIGURATION,
    _codecs,
    _SelectedProvider,
)


def factory_fixture(transform=None, catalog_producer=None):
    key = "pair_" + uuid4().hex
    calls = []
    products = []

    def factory():
        calls.append(True)
        pair = []
        for label in ("source_planning", "authority_derivation"):
            provider = _SelectedProvider()
            provider._declaration = replace(provider.declaration, provider_key=key)
            p = profile()
            p = replace(
                p,
                profile_ref=label,
                providers=(provider.declaration,),
                steps=(replace(p.steps[0], provider_key=key),),
            )
            runtime = SemanticContractRuntime(p, {key: provider}, _codecs())
            pair.append(
                selected._SelectedProviderFactoryProduct(
                    runtime,
                    provider,
                    replace(_BINDING, provider_key=key),
                    provider.execute,
                    provider.input_closure,
                    _ARTIFACT,
                    _CONFIGURATION,
                )
            )
        result = selected.SelectedProviderStageFactoryProduct(
            *pair, catalog_contribution_producer=catalog_producer
        )
        products.append(result)
        return result if transform is None else transform(result)

    admission = selected._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory
    )
    return admission, calls, products


@dataclass(frozen=True, slots=True)
class _CatalogProduct:
    original: stages.SelectedProviderStageContribution
    entries: tuple[CodeSemanticMaterializationProfileBinding, ...]
    executables: tuple[tuple[object, object, object], ...]
    planner: object


class _Planner:
    async def plan(self, **kwargs):
        del kwargs
        raise AssertionError("catalog inspection cannot execute the planner")


def _catalog_product(original):
    inputs = stages.read_selected_provider_stage_catalog_inputs(original)
    entries = []
    for item in inputs:
        profile = item.stage.runtime.profile
        provider = profile.providers[0]
        roles = (provider.result_role, provider.effect_role, *provider.output_roles)
        entries.append(
            CodeSemanticMaterializationProfileBinding.create(
                semantic_owner_key="test.owner",
                semantic_provider_key=item.binding.provider_key,
                package_families=("public",),
                package_roles=("test.owner",),
                manifest_contracts=(profile.inputs[0].contract,),
                profile_declaration=profile,
                provider_execution_bindings=(item.binding,),
                dependency_planner_contract=profile.inputs[0].contract,
                dependency_planner_implementation=item.binding.implementation,
                dependency_planner_configuration=item.binding.configuration,
                dependency_demand_contract=profile.inputs[0].contract,
                dependency_target_intent_contract=profile.inputs[0].contract,
                result_product_contracts=tuple(
                    CodeSemanticRequiredResultProduct.create(
                        role=role.role, contract=role.contract
                    )
                    for role in sorted(roles, key=lambda role: role.role)
                ),
                priority=0,
            )
        )
    return _CatalogProduct(
        original,
        tuple(sorted(entries, key=lambda entry: entry.profile_declaration.profile_ref)),
        tuple(
            (
                item.binding.implementation,
                item.binding.configuration,
                item.executable,
            )
            for item in inputs
        ),
        _Planner(),
    )


def test_atomic_pair_and_owned_close():
    admission, calls, products = factory_fixture()
    pair = stages.issue_selected_provider_stage_contribution(admission)
    result = stages.read_selected_provider_stage_contribution(pair)
    assert calls == [True]
    assert tuple(s.stage for s in result) == ("source_planning", "authority_derivation")
    assert result[0].runtime is products[0].source_planning.runtime
    assert result[1].runtime is products[0].authority_derivation.runtime
    stages.close_selected_provider_stage_contribution(pair)
    with pytest.raises(ContractViolation):
        stages.read_selected_provider_stage_contribution(pair)
    for s in result:
        with pytest.raises(ContractViolation, match="closed"):
            selected._registration_state(s.registration)


def test_single_stage_entrance_rejects_pair():
    admission, calls, _ = factory_fixture()
    with pytest.raises(TypeError, match="product must be exact"):
        selected._issue_selected_provider_selection_root(admission)
    assert calls == [True]


def test_second_registration_failure_closes_first(monkeypatch):
    admission, _, _ = factory_fixture()
    original = selected.register_selected_provider
    registered = []
    roots_before = set(selected._SELECTION_ROOTS)

    def fail_second(runtime, root):
        if registered:
            raise RuntimeError("second stage failed")
        result = original(runtime, root)
        registered.append(result)
        return result

    monkeypatch.setattr(selected, "register_selected_provider", fail_second)
    with pytest.raises(RuntimeError, match="second stage failed"):
        stages.issue_selected_provider_stage_contribution(admission)
    assert selected._REGISTRATIONS[id(registered[0])][1].closed
    # Only the registered first root remains as historical evidence.
    assert len(set(selected._SELECTION_ROOTS) - roots_before) == 1


def test_cleanup_failure_preserves_primary(monkeypatch):
    admission, _, _ = factory_fixture()
    original = selected.register_selected_provider
    count = []
    close_attempts = []

    def register(runtime, root):
        if count:
            raise RuntimeError("primary")
        result = original(runtime, root)
        count.append(result)
        return result

    def close(runtime, registration):
        close_attempts.append(registration)
        raise RuntimeError("cleanup")

    monkeypatch.setattr(selected, "register_selected_provider", register)
    monkeypatch.setattr(selected, "close_selected_provider_registration", close)
    with pytest.raises(ExceptionGroup) as caught:
        stages.issue_selected_provider_stage_contribution(admission)
    assert [str(e) for e in caught.value.exceptions] == ["primary", "cleanup"]
    assert close_attempts == count


@pytest.mark.parametrize("mode", ["copy", "reconstruct", "fork", "closed", "method"])
def test_contribution_rejects_invalid_lifetime_or_identity(mode, monkeypatch):
    admission, _, products = factory_fixture()
    pair = stages.issue_selected_provider_stage_contribution(admission)
    if mode == "copy":
        with pytest.raises(TypeError):
            copy.copy(pair)
        return
    if mode == "reconstruct":
        pair = object.__new__(stages.SelectedProviderStageContribution)
        pair._token = stages._TOKEN
    elif mode == "fork":
        monkeypatch.setattr(stages.os, "getpid", lambda: -1)
    elif mode == "closed":
        first = stages.read_selected_provider_stage_contribution(pair)[0]
        selected.close_selected_provider_registration(first.runtime, first.registration)
    else:
        products[0].source_planning.provider.execute = lambda *_: None
    with pytest.raises((ContractViolation, TypeError)):
        stages.read_selected_provider_stage_contribution(pair)


def test_cleanup_attempts_both_and_can_retry(monkeypatch):
    admission, _, _ = factory_fixture()
    pair = stages.issue_selected_provider_stage_contribution(admission)
    original = selected.close_selected_provider_registration
    attempted = []

    def close(runtime, registration):
        attempted.append(registration)
        if len(attempted) == 1:
            raise ContractViolation("active execution")
        original(runtime, registration)

    with monkeypatch.context() as patch:
        patch.setattr(selected, "close_selected_provider_registration", close)
        with pytest.raises(ExceptionGroup):
            stages.close_selected_provider_stage_contribution(pair)
    assert len(attempted) == 2
    stages.close_selected_provider_stage_contribution(pair)
    with pytest.raises(ContractViolation):
        stages.read_selected_provider_stage_contribution(pair)


@pytest.mark.parametrize(
    "mode", ["single", "same_runtime", "same_profile", "binding", "closure"]
)
def test_bad_factory_products_leave_no_registrations(mode):
    before = set(selected._REGISTRATIONS)
    roots_before = set(selected._SELECTION_ROOTS)

    def transform(pair):
        first, second = pair.source_planning, pair.authority_derivation
        if mode == "single":
            return first
        if mode == "same_runtime":
            return selected.SelectedProviderStageFactoryProduct(first, first)
        if mode == "same_profile":
            second.runtime._profile = first.runtime.profile
        elif mode == "binding":
            second = replace(
                second, binding=replace(second.binding, provider_key="foreign")
            )
        else:
            second = replace(second, semantic_implementation_contract_body=b"{}")
        return selected.SelectedProviderStageFactoryProduct(first, second)

    admission, _, _ = factory_fixture(transform)
    with pytest.raises((ContractViolation, TypeError)):
        stages.issue_selected_provider_stage_contribution(admission)
    assert set(selected._REGISTRATIONS) == before
    assert set(selected._SELECTION_ROOTS) == roots_before


def test_reused_products_reject_without_closing_original():
    original = []

    def retain(pair):
        if not original:
            original.append(pair)
        return original[0]

    admission, _, _ = factory_fixture(retain)
    contribution = stages.issue_selected_provider_stage_contribution(admission)
    with pytest.raises(ContractViolation, match="fresh owned runtimes"):
        stages.issue_selected_provider_stage_contribution(admission)
    assert len(stages.read_selected_provider_stage_contribution(contribution)) == 2
    stages.close_selected_provider_stage_contribution(contribution)
    with pytest.raises(ContractViolation, match="fresh owned runtimes"):
        stages.issue_selected_provider_stage_contribution(admission)


def test_returned_expectations_cannot_redirect_retained_pair():
    admission, _, _ = factory_fixture()
    contribution = stages.issue_selected_provider_stage_contribution(admission)
    exposed = stages.read_selected_provider_stage_contribution(contribution)
    original = exposed[0].runtime
    object.__setattr__(exposed[0], "runtime", exposed[1].runtime)
    object.__setattr__(exposed[0], "registration", exposed[1].registration)
    reread = stages.read_selected_provider_stage_contribution(contribution)
    assert reread[0].runtime is original
    assert reread[0].registration is not exposed[0].registration
    stages.close_selected_provider_stage_contribution(contribution)


def test_catalog_inputs_use_original_pair_without_reconstruction():
    admission, calls, products = factory_fixture()
    pair = stages.issue_selected_provider_stage_contribution(admission)
    try:
        values = stages.read_selected_provider_stage_catalog_inputs(pair)
        original = (products[0].source_planning, products[0].authority_derivation)
        assert calls == [True]
        for value, product in zip(values, original, strict=True):
            assert value.stage.runtime is product.runtime
            assert value.executable is product.provider
            assert value.binding == product.binding
            assert value.binding is not product.binding
        object.__setattr__(
            values[0].binding.implementation, "implementation_ref", "foreign"
        )
        assert (
            stages.read_selected_provider_stage_catalog_inputs(pair)[0].binding
            == original[0].binding
        )
    finally:
        stages.close_selected_provider_stage_contribution(pair)
    with pytest.raises(ContractViolation):
        stages.read_selected_provider_stage_catalog_inputs(pair)


def test_catalog_inputs_reject_foreign_contribution_and_provider_substitution(
    monkeypatch,
):
    with pytest.raises(ContractViolation):
        stages.read_selected_provider_stage_catalog_inputs(
            object.__new__(stages.SelectedProviderStageContribution)
        )
    admission, _, products = factory_fixture()
    pair = stages.issue_selected_provider_stage_contribution(admission)
    try:
        provider = products[0].source_planning.provider
        monkeypatch.setattr(provider, "execute", lambda *args, **kwargs: None)
        with pytest.raises(TypeError, match="exact bound provider method"):
            stages.read_selected_provider_stage_catalog_inputs(pair)
    finally:
        monkeypatch.undo()
        stages.close_selected_provider_stage_contribution(pair)


def test_catalog_input_read_rejects_revocation_during_projection(monkeypatch):
    admission, _, _ = factory_fixture()
    pair = stages.issue_selected_provider_stage_contribution(admission)
    original = stages.deepcopy

    revoked = False

    def revoke(value):
        nonlocal revoked
        if not revoked:
            revoked = True
            stages.close_selected_provider_stage_contribution(pair)
        return original(value)

    monkeypatch.setattr(stages, "deepcopy", revoke)
    with pytest.raises(ContractViolation):
        stages.read_selected_provider_stage_catalog_inputs(pair)


def test_owner_catalog_producer_is_bound_to_original_pair_and_consumed_once():
    calls = []

    def produce(original):
        calls.append(original)
        return _catalog_product(original)

    admission, _, products = factory_fixture(catalog_producer=produce)
    pair = stages.issue_selected_provider_stage_contribution(admission)
    try:
        with pytest.raises(ContractViolation, match="unavailable"):
            stages.read_selected_provider_stage_catalog_contribution(pair)
        result = stages.produce_selected_provider_stage_catalog_contribution(pair)
        assert calls == [pair]
        assert len(result.entries) == 2
        reread = stages.read_selected_provider_stage_catalog_contribution(pair)
        assert result.planner is reread.planner
        with pytest.raises(ContractViolation, match="already consumed"):
            stages.produce_selected_provider_stage_catalog_contribution(pair)
        object.__setattr__(
            products[0], "catalog_contribution_producer", _catalog_product
        )
        with pytest.raises(ContractViolation, match="producer changed"):
            stages.read_selected_provider_stage_catalog_contribution(pair)
    finally:
        object.__setattr__(products[0], "catalog_contribution_producer", produce)
        stages.close_selected_provider_stage_contribution(pair)
    with pytest.raises(ContractViolation):
        stages.read_selected_provider_stage_catalog_contribution(pair)


@pytest.mark.parametrize(
    "mode", ["original", "entries", "executable", "planner", "hostile"]
)
def test_owner_catalog_product_substitution_refuses(mode):
    def produce(original):
        if mode == "hostile":
            class Hostile:
                def __getattribute__(self, name):
                    raise AssertionError(f"foreign accessor invoked: {name}")

            return Hostile()
        product = _catalog_product(original)
        if mode == "original":
            return replace(product, original=object())
        if mode == "entries":
            return replace(product, entries=product.entries[:1])
        if mode == "executable":
            return replace(
                product,
                executables=(
                    (object(), *product.executables[0][1:]),
                    *product.executables[1:],
                ),
            )
        return replace(product, planner=object())

    admission, _, _ = factory_fixture(catalog_producer=produce)
    pair = stages.issue_selected_provider_stage_contribution(admission)
    try:
        with pytest.raises(ContractViolation):
            stages.produce_selected_provider_stage_catalog_contribution(pair)
        with pytest.raises(ContractViolation, match="already consumed"):
            stages.produce_selected_provider_stage_catalog_contribution(pair)
    finally:
        stages.close_selected_provider_stage_contribution(pair)


def test_catalog_producer_requires_exact_one_argument_function():
    admission, _, _ = factory_fixture(catalog_producer=lambda: None)
    with pytest.raises(TypeError, match="one original pair"):
        stages.issue_selected_provider_stage_contribution(admission)


def test_catalog_producer_failure_is_single_use_and_owner_can_close_pair():
    calls = []

    def fail(original):
        calls.append(original)
        raise RuntimeError("owner catalog failed")

    admission, _, _ = factory_fixture(catalog_producer=fail)
    pair = stages.issue_selected_provider_stage_contribution(admission)
    retained = stages.read_selected_provider_stage_contribution(pair)
    try:
        with pytest.raises(RuntimeError, match="owner catalog failed"):
            stages.produce_selected_provider_stage_catalog_contribution(pair)
        with pytest.raises(ContractViolation, match="already consumed"):
            stages.produce_selected_provider_stage_catalog_contribution(pair)
        assert calls == [pair]
    finally:
        stages.close_selected_provider_stage_contribution(pair)
    for stage in retained:
        with pytest.raises(ContractViolation, match="closed"):
            selected._registration_state(stage.registration)


def test_catalog_product_mutation_rejects_reread():
    produced = []

    def produce(original):
        product = _catalog_product(original)
        produced.append(product)
        return product

    admission, _, _ = factory_fixture(catalog_producer=produce)
    pair = stages.issue_selected_provider_stage_contribution(admission)
    try:
        stages.produce_selected_provider_stage_catalog_contribution(pair)
        object.__setattr__(produced[0], "entries", tuple(list(produced[0].entries)))
        with pytest.raises(ContractViolation, match="product changed"):
            stages.read_selected_provider_stage_catalog_contribution(pair)
    finally:
        stages.close_selected_provider_stage_contribution(pair)


def test_two_original_owners_compose_one_existing_code_catalog_input():
    admissions = [
        factory_fixture(catalog_producer=_catalog_product)[0] for _ in range(2)
    ]
    pairs = [
        stages.issue_selected_provider_stage_contribution(item)
        for item in admissions
    ]
    try:
        for pair in pairs:
            stages.produce_selected_provider_stage_catalog_contribution(pair)
        ordered = tuple(
            sorted(
                pairs,
                key=lambda pair: stages.read_selected_provider_stage_catalog_inputs(
                    pair
                )[0].binding.provider_key,
            )
        )
        catalog = stages.compose_selected_provider_stage_catalog_input(
            ordered, catalog_ref="test.original-pool", catalog_generation=1
        )
        assert len(catalog.entries) == 4
        assert len({entry.semantic_provider_key for entry in catalog.entries}) == 2
        catalog.__post_init__()
        with pytest.raises(ContractViolation, match="unique and ordered"):
            stages.compose_selected_provider_stage_catalog_input(
                tuple(reversed(ordered)),
                catalog_ref="test.original-pool",
                catalog_generation=1,
            )
        with pytest.raises(ContractViolation, match="duplicate"):
            stages.compose_selected_provider_stage_catalog_input(
                (ordered[0], ordered[0]),
                catalog_ref="test.original-pool",
                catalog_generation=1,
            )
    finally:
        for pair in reversed(pairs):
            stages.close_selected_provider_stage_contribution(pair)
    with pytest.raises(ContractViolation):
        stages.compose_selected_provider_stage_catalog_input(
            ordered, catalog_ref="test.original-pool", catalog_generation=1
        )
