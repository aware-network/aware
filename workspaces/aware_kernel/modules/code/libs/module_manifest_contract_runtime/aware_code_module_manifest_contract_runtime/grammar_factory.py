"""Original grammar product/catalog construction, not source-role admission.

Import and factory construction perform no admission or source IO. Executable
ports refuse until the separately scoped original-host attachment is implemented;
coordinates and catalog construction must never enable that missing authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Never, cast

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.grammar_input_codecs import (
    grammar_input_body_codecs,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    GRAMMAR_PROFILE_RESULT_REF,
    GRAMMAR_READ_EFFECT_REF,
    GRAMMAR_READ_TRANSITION_REF,
    GRAMMAR_SOURCE_ROLE_DEMAND_REF,
    GRAMMAR_SOURCE_ROLE_PLANNER_DESCRIPTOR,
    GRAMMAR_SOURCE_ROLE_PLANNER_REF,
    GRAMMAR_SOURCE_ROLE_SELECTION_REF,
    GRAMMAR_SOURCE_ROLE_TARGET_INTENT_REF,
    GRAMMAR_SYNTAX_BINDING_V2_REF,
    CodeGrammarReadEffectCodec,
    CodeGrammarReadTransitionCodec,
    grammar_operational_profile,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarProfileSelectionCodec,
    CodeGrammarSyntaxBindingCodec,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractMatch,
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    CodeSemanticMaterializationIntent,
    CodeSemanticRequiredResultProduct,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    SelectedProviderProductContribution,
    read_selected_provider_product_catalog_contribution,
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.profile import (
    SemanticContractProfileDeclaration,
)
from aware_code_semantic_contract_runtime.runtime import (
    ProviderStepInvocation,
    SemanticBodyCodec,
    SemanticContractRuntime,
)
from aware_code_semantic_contract_runtime.selected_provider import (
    _SelectedProviderFactoryProduct,
)

_MODULE = "aware_code_module_manifest_contract_runtime.grammar_factory"
_RECIPE = "original attached source-role entry; exact operational provider/profile/codecs/binding; original full declaration/group and retained predecessor; before/after original source/catalog/epoch validation; no automatic graph plan or write"


class GrammarProfileSelectionProvider:
    """Fixed product identity; construction grants no invocation authority."""

    _profile: SemanticContractProfileDeclaration

    def __init__(self) -> None:
        self._profile = grammar_operational_profile("profile_selection")

    @property
    def declaration(self) -> SemanticContractProviderDeclaration:
        return self._profile.providers[0]

    def input_closure(self, value: object) -> Never:
        _ = value
        raise ContractViolation(
            "grammar product requires original source-role attachment"
        )

    def execute(self, step: ProviderStepInvocation, value: object) -> Never:
        _ = step, value
        raise ContractViolation(
            "grammar product requires original source-role attachment"
        )

    async def derive(self, invocation: ProviderStepInvocation) -> Never:
        _ = invocation
        raise ContractViolation(
            "grammar product requires original source-role attachment"
        )


class GrammarSyntaxBindingProvider(GrammarProfileSelectionProvider):
    def __init__(self) -> None:
        super().__init__()
        self._profile = grammar_operational_profile("syntax_binding")


def _construct(
    provider: GrammarProfileSelectionProvider,
    slot: str,
    version: str,
    interpretation: str,
) -> _SelectedProviderFactoryProduct:
    profile = grammar_operational_profile(slot)
    if provider.declaration != profile.providers[0]:
        raise ContractViolation("grammar factory provider/profile differs")
    codecs: dict[SemanticContractRef, object] = dict(grammar_input_body_codecs())
    codecs[GRAMMAR_PROFILE_RESULT_REF] = CodeGrammarProfileSelectionCodec()
    codecs[GRAMMAR_READ_TRANSITION_REF] = CodeGrammarReadTransitionCodec()
    codecs[GRAMMAR_READ_EFFECT_REF] = CodeGrammarReadEffectCodec()
    if slot == "syntax_binding":
        codecs[GRAMMAR_SYNTAX_BINDING_V2_REF] = CodeGrammarSyntaxBindingCodec()
    bindings = tuple(
        SemanticBodyCodecBinding(ref, codec.implementation)
        for ref, codec in sorted(
            cast(dict[SemanticContractRef, SemanticBodyCodec], codecs).items(),
            key=lambda row: canonical_json_bytes(row[0].to_wire()),
        )
    )
    name = type(provider).__name__
    target = _MODULE + "." + name
    factory = (
        "construct_grammar_profile_selection_product"
        if slot == "profile_selection"
        else "construct_grammar_syntax_binding_product"
    )
    implementation_body = canonical_json_bytes(
        {
            "contract": "aware.code.grammar-product-implementation-contract.v1",
            "slot": slot,
            "profile": profile.to_wire(),
            "provider": provider.declaration.to_wire(),
            "body_codecs": [binding.to_wire() for binding in bindings],
            "entrances": {
                "factory": _MODULE + ":" + factory,
                "provider_type": target,
                "input_closure": target + ".input_closure",
                "execute": target + ".execute",
                "derive": target + ".derive",
                "interpretation": "aware_code_module_manifest_contract_runtime.grammar_profile_composition."
                + interpretation,
                "catalog_producer": _MODULE + ".produce_grammar_product_catalog",
                "planner": _MODULE + ".GrammarSourceRoleDependencyPlanner.plan",
            },
            "validation_recipe": _RECIPE,
        }
    )
    configuration_body = canonical_json_bytes(
        {
            "contract": "aware.code.grammar-source-role-configuration.v1",
            "slot": slot,
            "options": {},
        }
    )
    stem = "aware.code.grammar." + slot.replace("_", "-")
    binding = ProviderExecutionBinding(
        provider.declaration.provider_key,
        SemanticImplementationCoordinate(
            stem + ".implementation.v" + version,
            ContentDigest.of_bytes(implementation_body),
        ),
        SemanticConfigurationCoordinate(
            stem + ".no-options.v" + version,
            ContentDigest.of_bytes(configuration_body),
        ),
    )
    runtime = SemanticContractRuntime(
        profile,
        {provider.declaration.provider_key: provider},
        cast(dict[SemanticContractRef, SemanticBodyCodec], codecs),
    )
    return _SelectedProviderFactoryProduct(
        runtime,
        provider,
        binding,
        provider.execute,
        provider.input_closure,
        implementation_body,
        configuration_body,
        produce_grammar_product_catalog,
    )


def construct_grammar_profile_selection_product() -> _SelectedProviderFactoryProduct:
    return _construct(
        GrammarProfileSelectionProvider(),
        "profile_selection",
        "1",
        "produce_grammar_profile_selection",
    )


def construct_grammar_syntax_binding_product() -> _SelectedProviderFactoryProduct:
    return _construct(
        GrammarSyntaxBindingProvider(),
        "syntax_binding",
        "2",
        "produce_grammar_source_binding",
    )


class GrammarSourceRoleDependencyPlanner:
    """Revalidate the original catalog, then refuse unsupported graph targeting."""

    _original: SelectedProviderProductContribution

    def __init__(self, original: SelectedProviderProductContribution) -> None:
        self._original = original

    async def plan(
        self,
        *,
        package: SemanticPackageCoordinate,
        intent: CodeSemanticMaterializationIntent,
        selected_match: CodeSemanticContractMatch,
        planning_input: SemanticDependencyPlanningInput,
    ) -> Never:
        retained = read_selected_provider_product_catalog_contribution(self._original)
        if retained.planner is not self or len(retained.entries) != 1:
            raise ContractViolation("grammar planner differs from original catalog")
        for value, expected in (
            (package, SemanticPackageCoordinate),
            (intent, CodeSemanticMaterializationIntent),
            (selected_match, CodeSemanticContractMatch),
            (planning_input, SemanticDependencyPlanningInput),
        ):
            if type(value) is not expected:
                raise TypeError("exact grammar planner input required")
        package.__post_init__()
        intent.__post_init__()
        selected_match.__post_init__()
        planning_input.__post_init__()
        if (
            selected_match.selected_binding != retained.entries[0]
            or planning_input.package != package
        ):
            raise ContractViolation("grammar planner original binding/target differs")
        _ = read_selected_provider_product_catalog_contribution(self._original)
        raise ContractViolation("grammar products require original source-role join")


@dataclass(frozen=True, slots=True)
class _GrammarCatalogProduct:
    original: SelectedProviderProductContribution
    entries: tuple[CodeSemanticMaterializationProfileBinding, ...]
    executables: tuple[tuple[object, object, object], ...]
    planner: GrammarSourceRoleDependencyPlanner


def produce_grammar_product_catalog(
    original: SelectedProviderProductContribution,
) -> _GrammarCatalogProduct:
    value = read_selected_provider_product_contribution(original)
    kind = type(value.executable)
    if kind not in (GrammarProfileSelectionProvider, GrammarSyntaxBindingProvider):
        raise ContractViolation("original grammar provider type differs")
    stage = (
        "syntax_binding"
        if kind is GrammarSyntaxBindingProvider
        else "profile_selection"
    )
    if value.profile != grammar_operational_profile(stage):
        raise ContractViolation("original grammar product profile differs")
    provider = value.profile.providers[0]
    planner_body = GRAMMAR_SOURCE_ROLE_PLANNER_DESCRIPTOR
    # Each planner retains one original product. Equal implementation code does
    # not make planners for distinct products the same configured owner.
    planner_configuration = canonical_json_bytes(
        {
            "contract": "aware.code.grammar-source-role-planner-configuration.v2",
            "product_binding": value.binding.to_wire(),
            "profile": value.profile.to_wire(),
            "options": {},
        }
    )
    entry = CodeSemanticMaterializationProfileBinding.create(
        semantic_owner_key="aware_code.grammar",
        semantic_provider_key=value.binding.provider_key,
        package_families=("public",),
        package_roles=("aware_code.grammar",),
        manifest_contracts=(GRAMMAR_SOURCE_ROLE_SELECTION_REF,),
        profile_declaration=value.profile,
        provider_execution_bindings=(value.binding,),
        dependency_planner_contract=GRAMMAR_SOURCE_ROLE_PLANNER_REF,
        dependency_planner_implementation=SemanticImplementationCoordinate(
            "aware.code.grammar-source-role-planner.implementation.v1",
            ContentDigest.of_bytes(planner_body),
        ),
        dependency_planner_configuration=SemanticConfigurationCoordinate(
            "aware.code.grammar-source-role-planner.bound-product.v2",
            ContentDigest.of_bytes(planner_configuration),
        ),
        dependency_demand_contract=GRAMMAR_SOURCE_ROLE_DEMAND_REF,
        dependency_target_intent_contract=GRAMMAR_SOURCE_ROLE_TARGET_INTENT_REF,
        result_product_contracts=tuple(
            CodeSemanticRequiredResultProduct.create(
                role=row.role, contract=row.contract
            )
            for row in sorted(
                (provider.result_role, provider.effect_role),
                key=lambda row: row.role.encode(),
            )
        ),
        priority=0,
    )
    result = _GrammarCatalogProduct(
        original,
        (entry,),
        (
            (
                value.binding.implementation,
                value.binding.configuration,
                value.executable,
            ),
        ),
        GrammarSourceRoleDependencyPlanner(original),
    )
    after = read_selected_provider_product_contribution(original)
    if (
        after.expected.runtime is not value.expected.runtime
        or after.expected.registration is not value.expected.registration
        or after.executable is not value.executable
        or after.profile != value.profile
        or after.binding != value.binding
    ):
        raise ContractViolation(
            "original grammar product changed during catalog production"
        )
    return result


__all__ = [
    "GrammarProfileSelectionProvider",
    "GrammarSyntaxBindingProvider",
    "GrammarSourceRoleDependencyPlanner",
    "construct_grammar_profile_selection_product",
    "construct_grammar_syntax_binding_product",
    "produce_grammar_product_catalog",
]
