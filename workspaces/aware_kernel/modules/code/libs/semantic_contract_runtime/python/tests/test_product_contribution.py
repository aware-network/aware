"""A graph product uses the original single-provider factory rail."""

import copy
from dataclasses import dataclass, replace
from uuid import uuid4

import pytest
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    CodeSemanticRequiredResultProduct,
)
from aware_code_semantic_contract_runtime.private_stage_contract import (
    CodePrivateStagePlanV1,
    PrivateStageBarrier,
    PrivateStageEntry,
    PrivateStageProfileIdentity,
    PrivateStageRoleContract,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime import stage_contribution as stages
from test_profile_runtime import profile
from test_selected_provider import (
    _ARTIFACT,
    _BINDING,
    _CONFIGURATION,
    _codecs,
    _SelectedProvider,
)
from test_stage_contribution import (
    _catalog_product as stage_catalog_product,
    factory_fixture as stage_factory_fixture,
)


def _factory(catalog_producer=None, private_plan_producer=None):
    key = "product_" + uuid4().hex
    created = []

    def create():
        provider = _SelectedProvider()
        provider._declaration = replace(provider.declaration, provider_key=key)
        declaration = profile()
        declaration = replace(
            declaration,
            profile_ref="graph_" + key,
            providers=(provider.declaration,),
            steps=(replace(declaration.steps[0], provider_key=key),),
        )
        runtime = SemanticContractRuntime(
            declaration, {key: provider}, _codecs()
        )
        created.append((runtime, provider))
        return selected._SelectedProviderFactoryProduct(
            runtime,
            provider,
            replace(_BINDING, provider_key=key),
            provider.execute,
            provider.input_closure,
            _ARTIFACT,
            _CONFIGURATION,
            catalog_producer,
            private_plan_producer,
        )

    factory = selected._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=create
    )
    return factory, created


def _private_plan(original):
    product = products.read_selected_provider_product_contribution(original)
    profile = product.profile
    binding = product.binding
    public_profile = PrivateStageProfileIdentity(
        profile.profile_ref, profile.version, profile.digest
    )
    candidate = PrivateStageRoleContract(
        "candidate",
        profile.inputs[0].contract,
    )
    committed = PrivateStageRoleContract(
        "committed",
        profile.providers[0].transition_contract,
    )
    private = PrivateStageEntry(
        "private", "private", "private_" + binding.provider_key,
        PrivateStageProfileIdentity("private.profile", "1", profile.digest),
        binding.implementation, binding.configuration, (), candidate,
    )
    terminal = PrivateStageEntry(
        "terminal", "public_terminal", binding.provider_key,
        public_profile, binding.implementation, binding.configuration,
        (PrivateStageRoleContract("committed_input", committed.contract),),
        PrivateStageRoleContract(
            profile.providers[0].result_role.role,
            profile.providers[0].result_role.contract,
        ),
    )
    return CodePrivateStagePlanV1(
        1,
        public_profile,
        (private, terminal),
        PrivateStageBarrier(
            "committed_product", "private", "terminal", candidate,
            committed, "committed_input",
        ),
    )


def test_original_private_stage_plan_producer_and_retained_revalidation():
    calls = []

    def producer(original):
        calls.append(original)
        return _private_plan(original)

    factory, _ = _factory(private_plan_producer=producer)
    contribution = products.issue_selected_provider_product_contribution(factory)
    try:
        first = products.produce_selected_provider_private_stage_plan(contribution)
        second = products.read_selected_provider_private_stage_plan(contribution)
        assert first == second
        assert first is not second
        assert calls == [contribution]
        with pytest.raises(ContractViolation, match="already consumed"):
            products.produce_selected_provider_private_stage_plan(contribution)
        original = products._PRIVATE_PLANS[contribution].original
        object.__setattr__(original.barrier, "before_stage", "substituted")
        with pytest.raises(ContractViolation):
            products.read_selected_provider_private_stage_plan(contribution)
    finally:
        products.close_selected_provider_product_contribution(contribution)
    with pytest.raises(ContractViolation):
        products.read_selected_provider_private_stage_plan(contribution)


def test_private_stage_plan_requires_original_public_profile_and_result():
    def wrong_profile(original):
        plan = _private_plan(original)
        return replace(
            plan,
            public_profile=replace(plan.public_profile, profile_ref="foreign.profile"),
            stages=(plan.stages[0], replace(
                plan.stages[1],
                profile=replace(plan.public_profile, profile_ref="foreign.profile"),
            )),
        )

    factory, _ = _factory(private_plan_producer=wrong_profile)
    contribution = products.issue_selected_provider_product_contribution(factory)
    try:
        with pytest.raises(ContractViolation, match="public registration"):
            products.produce_selected_provider_private_stage_plan(contribution)
        with pytest.raises(ContractViolation, match="already consumed"):
            products.produce_selected_provider_private_stage_plan(contribution)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_stage_plan_producer_substitution_refuses():
    factory, _ = _factory(private_plan_producer=_private_plan)
    contribution = products.issue_selected_provider_product_contribution(factory)
    try:
        state = products._CONTRIBUTIONS[contribution]
        object.__setattr__(state.product, "private_stage_plan_producer", lambda _: None)
        with pytest.raises(ContractViolation, match="producer changed"):
            products.produce_selected_provider_private_stage_plan(contribution)
        object.__setattr__(state.product, "private_stage_plan_producer", _private_plan)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_stage_plan_terminal_must_be_declared_public_result():
    def wrong_result(original):
        plan = _private_plan(original)
        terminal = replace(
            plan.stages[1],
            terminal=PrivateStageRoleContract(
                "invented", plan.stages[1].terminal.contract
            ),
        )
        return replace(plan, stages=(plan.stages[0], terminal))

    factory, _ = _factory(private_plan_producer=wrong_result)
    contribution = products.issue_selected_provider_product_contribution(factory)
    try:
        with pytest.raises(ContractViolation, match="public result"):
            products.produce_selected_provider_private_stage_plan(contribution)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_stage_plan_producer_must_be_original_function():
    class CallableObject:
        def __call__(self, original):
            return _private_plan(original)

    factory, _ = _factory(private_plan_producer=CallableObject())
    with pytest.raises(TypeError, match="exact function"):
        products.issue_selected_provider_product_contribution(factory)


@dataclass(frozen=True, slots=True)
class _CatalogProduct:
    original: products.SelectedProviderProductContribution
    entries: tuple[CodeSemanticMaterializationProfileBinding, ...]
    executables: tuple[tuple[object, object, object], ...]
    planner: object


class _Planner:
    async def plan(self, **kwargs):
        del kwargs
        raise AssertionError("catalog inspection cannot execute the planner")


def _catalog_product(original):
    value = products.read_selected_provider_product_contribution(original)
    declaration = value.profile.providers[0]
    roles = (
        declaration.result_role,
        declaration.effect_role,
        *declaration.output_roles,
    )
    entry = CodeSemanticMaterializationProfileBinding.create(
        semantic_owner_key="test.product.owner",
        semantic_provider_key=value.binding.provider_key,
        package_families=("public",),
        package_roles=("test.product.owner",),
        manifest_contracts=(value.profile.inputs[0].contract,),
        profile_declaration=value.profile,
        provider_execution_bindings=(value.binding,),
        dependency_planner_contract=value.profile.inputs[0].contract,
        dependency_planner_implementation=value.binding.implementation,
        dependency_planner_configuration=value.binding.configuration,
        dependency_demand_contract=value.profile.inputs[0].contract,
        dependency_target_intent_contract=value.profile.inputs[0].contract,
        result_product_contracts=tuple(
            CodeSemanticRequiredResultProduct.create(
                role=role.role, contract=role.contract
            )
            for role in sorted(roles, key=lambda role: role.role)
        ),
        priority=0,
    )
    return _CatalogProduct(
        original,
        (entry,),
        ((value.binding.implementation, value.binding.configuration, value.executable),),
        _Planner(),
    )


def test_original_product_registration_and_cleanup():
    factory, created = _factory()
    contribution = products.issue_selected_provider_product_contribution(factory)
    try:
        first = products.read_selected_provider_product_contribution(contribution)
        second = products.read_selected_provider_product_contribution(contribution)
        assert first.expected.runtime is created[0][0]
        assert first.expected.registration is second.expected.registration
        assert first.executable is created[0][1]
        assert first.binding == second.binding
        assert first.binding is not second.binding
        with pytest.raises(TypeError):
            copy.copy(contribution)
    finally:
        products.close_selected_provider_product_contribution(contribution)
    with pytest.raises(ContractViolation):
        products.read_selected_provider_product_contribution(contribution)


def test_wrong_factory_product_rejects():
    key = "wrong_" + uuid4().hex

    def wrong():
        return object()

    bad = selected._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=wrong
    )
    with pytest.raises(TypeError):
        products.issue_selected_provider_product_contribution(bad)


def test_factory_bound_catalog_producer_is_single_use():
    produced = []

    def owner_product(original):
        product = _catalog_product(original)
        produced.append(product)
        return product

    factory, _ = _factory(owner_product)
    original = products.issue_selected_provider_product_contribution(factory)
    try:
        with pytest.raises(ContractViolation, match="unavailable"):
            products.read_selected_provider_product_catalog_contribution(original)
        first = products.produce_selected_provider_product_catalog_contribution(original)
        second = products.read_selected_provider_product_catalog_contribution(original)
        assert first.entries is second.entries is produced[0].entries
        assert first.executables is produced[0].executables
        with pytest.raises(ContractViolation, match="already consumed"):
            products.produce_selected_provider_product_catalog_contribution(original)
        object.__setattr__(produced[0], "entries", ())
        with pytest.raises(ContractViolation):
            products.read_selected_provider_product_catalog_contribution(original)
    finally:
        products.close_selected_provider_product_contribution(original)


def test_product_and_package_stages_compose_one_catalog():
    stage_factory, _, _ = stage_factory_fixture(
        catalog_producer=stage_catalog_product
    )
    product_factory, _ = _factory(_catalog_product)
    pair = stages.issue_selected_provider_stage_contribution(stage_factory)
    product = products.issue_selected_provider_product_contribution(product_factory)
    try:
        stages.produce_selected_provider_stage_catalog_contribution(pair)
        products.produce_selected_provider_product_catalog_contribution(product)
        catalog = stages.compose_selected_provider_stage_catalog_input(
            (pair,),
            product_contributions=(product,),
            catalog_ref="test.product-and-stages",
            catalog_generation=1,
        )
        assert len(catalog.entries) == 3
        product_entry = products.read_selected_provider_product_catalog_contribution(
            product
        ).entries[0]
        assert product_entry in catalog.entries
        with pytest.raises(ContractViolation):
            stages.compose_selected_provider_stage_catalog_input(
                (pair,),
                product_contributions=(product, product),
                catalog_ref="test.duplicate-product",
                catalog_generation=1,
            )
    finally:
        products.close_selected_provider_product_contribution(product)
        stages.close_selected_provider_stage_contribution(pair)


def test_wrong_product_catalog_value_cannot_be_retried():
    def bad(original):
        product = _catalog_product(original)
        object.__setattr__(product, "executables", ((object(), object(), object()),))
        return product

    factory, _ = _factory(bad)
    original = products.issue_selected_provider_product_contribution(factory)
    try:
        with pytest.raises(ContractViolation):
            products.produce_selected_provider_product_catalog_contribution(original)
        with pytest.raises(ContractViolation, match="already consumed"):
            products.produce_selected_provider_product_catalog_contribution(original)
    finally:
        products.close_selected_provider_product_contribution(original)


def test_missing_or_substituted_factory_producer_refuses():
    factory, _ = _factory()
    original = products.issue_selected_provider_product_contribution(factory)
    try:
        with pytest.raises(ContractViolation, match="unavailable"):
            products.produce_selected_provider_product_catalog_contribution(original)
    finally:
        products.close_selected_provider_product_contribution(original)

    factory, _ = _factory(_catalog_product)
    original = products.issue_selected_provider_product_contribution(factory)
    state = products._CONTRIBUTIONS[original]
    retained = state.product.catalog_contribution_producer
    object.__setattr__(state.product, "catalog_contribution_producer", lambda x: x)
    try:
        with pytest.raises(ContractViolation, match="producer changed"):
            products.produce_selected_provider_product_catalog_contribution(original)
    finally:
        object.__setattr__(state.product, "catalog_contribution_producer", retained)
        products.close_selected_provider_product_contribution(original)


def test_hostile_catalog_value_rejects_without_attribute_execution():
    calls = []

    class Hostile:
        __slots__ = ("original", "entries", "executables", "planner")

        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("hostile catalog accessor executed")

    def bad(original):
        value = Hostile()
        object.__setattr__(value, "original", original)
        return value

    factory, _ = _factory(bad)
    original = products.issue_selected_provider_product_contribution(factory)
    try:
        with pytest.raises(ContractViolation, match="inert slots"):
            products.produce_selected_provider_product_catalog_contribution(original)
        assert calls == []
    finally:
        products.close_selected_provider_product_contribution(original)
