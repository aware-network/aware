from __future__ import annotations

import json

import pytest
from aware_code_semantic_contract_runtime import (
    AdmittedCodeSemanticContractCatalog,
    CodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
    CodeSemanticContractMatch,
    CodeSemanticContractMatchAdmission,
    CodeSemanticDependencyPlanner,
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    ProducedRoleDeclaration,
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    ProviderExecutionBinding,
    RoleBinding,
    SemanticConfigurationCoordinate,
    SemanticContractProfileDeclaration,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticDependencyDemandSet,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    canonical_json_bytes,
    decode_code_semantic_contract_catalog,
    decode_code_semantic_contract_match,
    decode_code_semantic_contract_match_admission,
    decode_code_semantic_package_planning_context,
    encode_code_semantic_contract_catalog,
    encode_code_semantic_contract_match,
    encode_code_semantic_contract_match_admission,
    encode_code_semantic_package_planning_context,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
    _revoke_code_semantic_contract_catalog,
)


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _contract(key: str) -> SemanticContractRef:
    return SemanticContractRef(key=key, version="1", schema_digest=_digest(key))


def _configuration(key: str) -> SemanticConfigurationCoordinate:
    return SemanticConfigurationCoordinate(
        configuration_ref=key, digest=_digest(f"configuration:{key}")
    )


def _implementation(key: str) -> SemanticImplementationCoordinate:
    return SemanticImplementationCoordinate(
        implementation_ref=key, closure_digest=_digest(f"implementation:{key}")
    )


def _binding(
    *, provider_key: str = "aware.sdk.python", priority: int = 10
) -> CodeSemanticMaterializationProfileBinding:
    source = _contract("aware.sdk.source")
    result = _contract("aware.sdk.result")
    effect = _contract("aware.sdk.effect")
    output = _contract("aware.sdk.python-wheel")
    provider = SemanticContractProviderDeclaration(
        provider_key=provider_key,
        provider_contract=_contract("aware.sdk.provider"),
        package_kinds=("sdk",),
        operation_kinds=("materialize",),
        consumed_roles=(
            ConsumedRoleDeclaration(role="source", accepted_contracts=(source,)),
        ),
        result_role=ProducedRoleDeclaration(role="result", contract=result),
        transition_contract=_contract("aware.sdk.transition"),
        effect_role=ProducedRoleDeclaration(role="effect", contract=effect),
        effect_contract=effect,
        output_roles=(ProducedRoleDeclaration(role="python_sdk", contract=output),),
    )
    profile = SemanticContractProfileDeclaration(
        profile_ref="sdk.materialization",
        version="1",
        package_kinds=("sdk",),
        operation_kinds=("materialize",),
        inputs=(ProfileInputDeclaration(role="source", contract=source),),
        providers=(provider,),
        steps=(
            ProfileStepDeclaration(
                step_key="render",
                provider_key=provider_key,
                bindings=(RoleBinding(target_role="source", source_role="source"),),
            ),
        ),
        terminal_result_role="result",
        terminal_effect_role="effect",
        terminal_output_roles=("python_sdk",),
    )
    provider_binding = ProviderExecutionBinding(
        provider_key=provider_key,
        implementation=_implementation("sdk.renderer"),
        configuration=_configuration("sdk.renderer"),
    )
    products = tuple(
        CodeSemanticRequiredResultProduct.create(role=role, contract=contract)
        for role, contract in (
            ("effect", effect),
            ("python_sdk", output),
            ("result", result),
        )
    )
    return CodeSemanticMaterializationProfileBinding.create(
        semantic_owner_key="aware.sdk",
        semantic_provider_key=provider_key,
        package_families=("public",),
        package_roles=("sdk",),
        manifest_contracts=(_contract("aware.sdk.manifest"),),
        profile_declaration=profile,
        provider_execution_bindings=(provider_binding,),
        dependency_planner_contract=_contract("aware.sdk.dependency-planner"),
        dependency_planner_implementation=_implementation("sdk.dependency-planner"),
        dependency_planner_configuration=_configuration("sdk.dependency-planner"),
        dependency_demand_contract=_contract("aware.code.dependency-demand"),
        dependency_target_intent_contract=_contract("aware.code.target-intent"),
        result_product_contracts=products,
        priority=priority,
    )


def _catalog(
    *entries: CodeSemanticMaterializationProfileBinding,
) -> CodeSemanticContractCatalog:
    ordered = tuple(
        sorted(
            entries,
            key=lambda item: (
                item.semantic_owner_key,
                item.semantic_provider_key,
                item.profile_declaration.profile_ref,
                item.profile_declaration.digest.value,
            ),
        )
    )
    return CodeSemanticContractCatalog.create(
        catalog_ref="code.production", catalog_generation=4, entries=ordered
    )


class _NoopDependencyPlanner:
    async def plan(
        self,
        *,
        package: SemanticPackageCoordinate,
        intent: CodeSemanticMaterializationIntent,
        selected_match: CodeSemanticContractMatch,
    ) -> SemanticDependencyDemandSet:
        del package, intent, selected_match
        raise AssertionError("matching proof must not invoke dependency planning")


def _execution_closure(
    catalog: CodeSemanticContractCatalog,
    *,
    include_executables: bool = True,
) -> tuple[
    tuple[
        tuple[
            SemanticImplementationCoordinate,
            SemanticConfigurationCoordinate,
            object,
        ],
        ...,
    ],
    tuple[
        tuple[
            SemanticImplementationCoordinate,
            SemanticConfigurationCoordinate,
            CodeSemanticDependencyPlanner,
        ],
        ...,
    ],
]:
    provider_coordinates = {
        (binding.implementation, binding.configuration)
        for entry in catalog.entries
        for binding in entry.provider_execution_bindings
    }
    planner_coordinates = {
        (
            entry.dependency_planner_implementation,
            entry.dependency_planner_configuration,
        )
        for entry in catalog.entries
    }
    return (
        tuple(
            (implementation, configuration, object())
            for implementation, configuration in sorted(provider_coordinates)
        )
        if include_executables
        else (),
        tuple(
            (implementation, configuration, _NoopDependencyPlanner())
            for implementation, configuration in sorted(planner_coordinates)
        )
        if include_executables
        else (),
    )


def _resolver(
    catalog: CodeSemanticContractCatalog,
) -> CodeSemanticContractCatalogResolver:
    providers, planners = _execution_closure(catalog)
    return CodeSemanticContractCatalogResolver(
        _issue_code_semantic_contract_catalog(
            catalog=catalog,
            provider_executable_bindings=providers,
            dependency_planner_bindings=planners,
            host_liveness=lambda: True,
        )
    )


def _context(
    binding: CodeSemanticMaterializationProfileBinding,
    *,
    contract: SemanticContractRef | None = None,
    providers: tuple[str, ...] = (),
) -> CodeSemanticPackagePlanningContext:
    result_contract = contract or next(
        item.contract
        for item in binding.result_product_contracts
        if item.role == "python_sdk"
    )
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=("sdk.public",),
        requested_terminal_output_roles=("python_sdk",),
        semantic_configuration_coordinate=binding.provider_execution_bindings[
            0
        ].configuration,
    )
    return CodeSemanticPackagePlanningContext.create(
        package=SemanticPackageCoordinate(
            package_ref="package:sdk",
            package_kind="sdk",
            manifest_digest=_digest("manifest-v1"),
        ),
        package_family="public",
        package_role="sdk",
        manifest_contract=binding.manifest_contracts[0],
        code_intent=intent,
        required_result_products=(
            CodeSemanticRequiredResultProduct.create(
                role="python_sdk", contract=result_contract
            ),
        ),
        required_semantic_provider_keys=providers,
    )


def test_catalog_resolves_exact_role_contract_and_provider_context() -> None:
    binding = _binding()
    resolver = _resolver(_catalog(binding))
    context = _context(binding, providers=(binding.semantic_provider_key,))

    match, admission = resolver.resolve(context)

    assert match.selected_entry_digest == binding.binding_digest
    assert match.context_digest == context.context_digest
    assert admission.catalog_root_digest == resolver.catalog.catalog_root_digest


def test_matching_rejects_wrong_result_contract_and_unknown_provider() -> None:
    binding = _binding()
    resolver = _resolver(_catalog(binding))

    with pytest.raises(ContractViolation, match="match_absent"):
        resolver.resolve(_context(binding, contract=_contract("wrong.contract")))
    with pytest.raises(ContractViolation, match="match_absent"):
        resolver.resolve(_context(binding, providers=("unknown.provider",)))


def test_equal_priority_matches_are_ambiguous_and_priority_is_deterministic() -> None:
    first = _binding(provider_key="aware.sdk.a", priority=10)
    second = _binding(provider_key="aware.sdk.b", priority=10)
    context = _context(first)
    with pytest.raises(ContractViolation, match="match_ambiguous"):
        _resolver(_catalog(first, second)).resolve(context)

    preferred = _binding(provider_key="aware.sdk.b", priority=11)
    match, _ = _resolver(_catalog(first, preferred)).resolve(context)
    assert match.selected_binding.semantic_provider_key == "aware.sdk.b"


def test_catalog_admission_rejects_missing_execution_closure() -> None:
    catalog = _catalog(_binding())
    with pytest.raises(ContractViolation, match="executable closure"):
        _issue_code_semantic_contract_catalog(
            catalog=catalog,
            provider_executable_bindings=(),
            dependency_planner_bindings=(),
            host_liveness=lambda: True,
        )

    forged = object.__new__(AdmittedCodeSemanticContractCatalog)
    with pytest.raises(ContractViolation, match="not registered"):
        CodeSemanticContractCatalogResolver(forged)


def test_catalog_admission_is_private_and_revocation_invalidates_resolver() -> None:
    import aware_code_semantic_contract_runtime as public_runtime

    assert not hasattr(public_runtime, "CodeSemanticContractDeploymentHost")
    assert not hasattr(public_runtime, "CodeSemanticContractCatalogSource")
    assert not hasattr(public_runtime, "admit_code_semantic_contract_catalog")

    catalog = _catalog(_binding())
    providers, planners = _execution_closure(catalog)
    live = True
    admission = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        host_liveness=lambda: live,
    )
    resolver = CodeSemanticContractCatalogResolver(admission)
    assert resolver.catalog == catalog
    assert resolver.catalog is not catalog
    live = False
    _revoke_code_semantic_contract_catalog(admission)
    with pytest.raises(ContractViolation, match="not registered"):
        _ = resolver.catalog


def test_catalog_admission_and_resolver_observation_detach_source_graph() -> None:
    source = _catalog()
    admission = _issue_code_semantic_contract_catalog(
        catalog=source,
        provider_executable_bindings=(),
        dependency_planner_bindings=(),
        host_liveness=lambda: True,
    )
    resolver = CodeSemanticContractCatalogResolver(admission)
    replacement = CodeSemanticContractCatalog.create(
        catalog_ref=source.catalog_ref,
        catalog_generation=source.catalog_generation + 1,
        entries=source.entries,
    )

    object.__setattr__(source, "catalog_generation", replacement.catalog_generation)
    object.__setattr__(source, "catalog_root_digest", replacement.catalog_root_digest)
    assert resolver.catalog.catalog_generation == 4

    exposed = resolver.catalog
    object.__setattr__(exposed, "catalog_generation", replacement.catalog_generation)
    object.__setattr__(exposed, "catalog_root_digest", replacement.catalog_root_digest)
    assert resolver.catalog.catalog_generation == 4


def test_foreign_context_fails_before_foreign_method() -> None:
    calls: list[str] = []

    class ForeignContext(CodeSemanticPackagePlanningContext):
        def __post_init__(self) -> None:
            calls.append("foreign")

    binding = _binding()
    exact = _context(binding)
    foreign = ForeignContext(
        package=exact.package,
        package_family=exact.package_family,
        package_role=exact.package_role,
        manifest_contract=exact.manifest_contract,
        code_intent=exact.code_intent,
        required_result_products=exact.required_result_products,
        required_semantic_provider_keys=exact.required_semantic_provider_keys,
        context_digest=exact.context_digest,
    )
    calls.clear()
    with pytest.raises(TypeError, match="exact CodeSemanticPackagePlanningContext"):
        _resolver(_catalog(binding)).resolve(foreign)
    assert calls == []


def test_catalog_context_match_and_admission_round_trip_exact() -> None:
    binding = _binding()
    catalog = _catalog(binding)
    resolver = _resolver(catalog)
    context = _context(binding)
    match, admission = resolver.resolve(context)

    catalog_wire = encode_code_semantic_contract_catalog(catalog)
    assert (
        decode_code_semantic_contract_catalog(
            catalog_wire,
            catalog_ref=catalog.catalog_ref,
            catalog_generation=catalog.catalog_generation,
            entries=catalog.entries,
        )
        == catalog
    )
    context_wire = encode_code_semantic_package_planning_context(context)
    assert (
        decode_code_semantic_package_planning_context(
            context_wire,
            package=context.package,
            package_family=context.package_family,
            package_role=context.package_role,
            manifest_contract=context.manifest_contract,
            code_intent=context.code_intent,
            required_result_products=context.required_result_products,
            required_semantic_provider_keys=context.required_semantic_provider_keys,
        )
        == context
    )
    match_wire = encode_code_semantic_contract_match(
        match, context=context, resolver=resolver
    )
    assert (
        decode_code_semantic_contract_match(
            match_wire, context=context, resolver=resolver
        )
        == match
    )
    admission_wire = encode_code_semantic_contract_match_admission(
        admission, context=context, resolver=resolver
    )
    assert (
        decode_code_semantic_contract_match_admission(
            admission_wire, context=context, resolver=resolver
        )
        == admission
    )


def test_catalog_and_context_substitution_fail_against_exact_context() -> None:
    binding = _binding()
    catalog = _catalog(binding)
    wire = encode_code_semantic_contract_catalog(catalog)
    payload = json.loads(wire)
    payload["catalog_generation"] = 5
    with pytest.raises(ContractViolation, match="exact semantic context"):
        decode_code_semantic_contract_catalog(
            canonical_json_bytes(payload),
            catalog_ref=catalog.catalog_ref,
            catalog_generation=catalog.catalog_generation,
            entries=catalog.entries,
        )

    context = _context(binding)
    context_wire = encode_code_semantic_package_planning_context(context)
    payload = json.loads(context_wire)
    payload["required_result_products"][0]["result_contract"]["key"] = "wrong"
    with pytest.raises(ContractViolation, match="exact semantic context"):
        decode_code_semantic_package_planning_context(
            canonical_json_bytes(payload),
            package=context.package,
            package_family=context.package_family,
            package_role=context.package_role,
            manifest_contract=context.manifest_contract,
            code_intent=context.code_intent,
            required_result_products=context.required_result_products,
            required_semantic_provider_keys=context.required_semantic_provider_keys,
        )


def test_match_encoding_rederives_catalog_authority() -> None:
    first = _binding(provider_key="aware.sdk.a", priority=10)
    second = _binding(provider_key="aware.sdk.b", priority=11)
    context = _context(first)
    first_match, _ = _resolver(_catalog(first)).resolve(context)
    winning_resolver = _resolver(_catalog(first, second))

    with pytest.raises(ContractViolation, match="fresh catalog resolution"):
        encode_code_semantic_contract_match(
            first_match, context=context, resolver=winning_resolver
        )


def test_contextual_encoders_preflight_before_foreign_equality() -> None:
    calls: list[str] = []

    class ForeignBinding(CodeSemanticMaterializationProfileBinding):
        def __eq__(self, other: object) -> bool:
            del other
            calls.append("binding-equality")
            return False

    class ForeignDigest(ContentDigest):
        def __eq__(self, other: object) -> bool:
            del other
            calls.append("digest-equality")
            return False

    binding = _binding()
    resolver = _resolver(_catalog(binding))
    context = _context(binding)
    match, admission = resolver.resolve(context)
    foreign_binding = ForeignBinding(
        semantic_owner_key=binding.semantic_owner_key,
        semantic_provider_key=binding.semantic_provider_key,
        package_families=binding.package_families,
        package_roles=binding.package_roles,
        manifest_contracts=binding.manifest_contracts,
        profile_declaration=binding.profile_declaration,
        provider_execution_bindings=binding.provider_execution_bindings,
        dependency_planner_contract=binding.dependency_planner_contract,
        dependency_planner_implementation=binding.dependency_planner_implementation,
        dependency_planner_configuration=binding.dependency_planner_configuration,
        dependency_demand_contract=binding.dependency_demand_contract,
        dependency_target_intent_contract=binding.dependency_target_intent_contract,
        result_product_contracts=binding.result_product_contracts,
        priority=binding.priority,
        binding_digest=binding.binding_digest,
    )
    poisoned_match = object.__new__(CodeSemanticContractMatch)
    for name, value in (
        ("context_digest", match.context_digest),
        ("selected_entry_digest", match.selected_entry_digest),
        ("selected_binding", foreign_binding),
        ("match_digest", match.match_digest),
    ):
        object.__setattr__(poisoned_match, name, value)
    with pytest.raises(
        TypeError, match="exact CodeSemanticMaterializationProfileBinding"
    ):
        encode_code_semantic_contract_match(
            poisoned_match, context=context, resolver=resolver
        )
    assert calls == []

    poisoned_admission = object.__new__(CodeSemanticContractMatchAdmission)
    for name, value in (
        ("match_digest", ForeignDigest(admission.match_digest.value)),
        ("catalog_ref", admission.catalog_ref),
        ("catalog_generation", admission.catalog_generation),
        ("catalog_root_digest", admission.catalog_root_digest),
        ("admission_digest", admission.admission_digest),
    ):
        object.__setattr__(poisoned_admission, name, value)
    with pytest.raises(TypeError, match="exact ContentDigest"):
        encode_code_semantic_contract_match_admission(
            poisoned_admission, context=context, resolver=resolver
        )
    assert calls == []
