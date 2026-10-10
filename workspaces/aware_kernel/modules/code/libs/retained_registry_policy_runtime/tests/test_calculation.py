from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import calculate_registry_policy
from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalog,
    CodeSemanticMaterializationProfileBinding,
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
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
    CodeRetainedScopePackage,
    CodeRetainedScopeProjection,
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
    *, provider_key: str = "demo", priority: int = 10, profile_ref: str = "authority"
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
        profile_ref=profile_ref,
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


HEADER = 'aware = 2\n[[plugins]]\nkind = "code.module_plugin"\nprovider_key = "demo"\n[[packages]]\nid = "provider"\nkind = "code"\nmanifest = "provider/pyproject.toml"\n[packages.semantic_contract]\nrole = "demo.provider"\ncontract = "aware.semantic_provider"\nprovider_key = "demo"\nmodule = "demo.provider"\nowns_manifest_kinds = ["demo_toml"]\ncapabilities = ["materialize"]\n[[packages.semantic_contract.registrations]]\nkey = "demo"\nmanifest_contract_kind = "demo_toml"\nmanifest_filename = "aware.demo.toml"\nsemantic_package_family = "demo"\nsemantic_package_kind = "demo_package"\nsemantic_contract = { role = "demo", name = "demo", provider_key = "demo", coordinate = "contract:demo" }\nsupported_languages = ["aware"]\ncode_package_surface = { state = "absent" }\nprofiles = [\n {stage="authority_derivation", profile_ref="demo.authority", profile_version="1", profile_digest="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},\n {stage="source_planning", profile_ref="demo.planning", profile_version="1", profile_digest="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}\n]\n[[packages]]\nid = "home"\nkind = "demo"\nmanifest = "home/aware.demo.toml"\n[packages.semantic_admission]\nregistration = {state="present", value={module_id="demo", package_id="provider", registration_key="demo"}}\nsemantic_version = {state="present", value="1.0"}\nsemantic_package_name = {state="present", value="home-demo"}\ncode_package_name = {state="present", value="home-code"}\nsource_code_package_id = {state="absent"}\nconfiguration = {state="absent"}\nnamespace = {state="present", value="home"}\nowned_roots = {state="present", value=["home"]}\ndependency_targets = {state="present", value=[{dependency_kind="module", dependency_ref="target", targets=[{module_id="demo", package_id="target"}], constraints=[{constraint_kind="package_kind", constraint_value="demo_package"}]}]}\n'


def _body(path, data):
    return CodeRetainedScopeBody(
        path, "body:" + path, ContentDigest.of_bytes(data), data
    )


def fixture(change=lambda source: source):
    authority = _binding(profile_ref="authority")
    planning = _binding(profile_ref="planning")
    source = HEADER.replace(
        'semantic_package_family = "demo"', 'semantic_package_family = "public"'
    )
    source = source.replace(
        'semantic_package_kind = "demo_package"', 'semantic_package_kind = "sdk"'
    )
    source = source.replace('kind = "demo"', 'kind = "sdk"')
    source = source.replace('role = "demo", name =', 'role = "sdk", name =')
    source = source.replace('profile_ref="demo.authority"', 'profile_ref="authority"')
    source = source.replace('profile_ref="demo.planning"', 'profile_ref="planning"')
    source = source.replace(
        "sha256:" + "a" * 64, authority.profile_declaration.digest.to_wire(), 1
    )
    source = source.replace(
        "sha256:" + "a" * 64, planning.profile_declaration.digest.to_wire(), 1
    )
    source = (
        source[: source.index("dependency_targets =")]
        + 'dependency_targets = {state="present", value=[]}\n'
    )
    source = change(source)
    module = CodeRetainedScopeModule(
        "demo", _body("demo/aware.module.toml", source.encode())
    )
    packages = (
        CodeRetainedScopePackage(
            "demo",
            "home",
            "sdk",
            module.manifest.relative_path,
            "demo/home",
            "aware.demo.toml",
            _digest("home"),
            _body("demo/home/aware.demo.toml", b"owner semantic source"),
        ),
        CodeRetainedScopePackage(
            "demo",
            "provider",
            "code",
            module.manifest.relative_path,
            "demo/provider",
            "pyproject.toml",
            _digest("provider"),
            _body("demo/provider/pyproject.toml", b"provider source"),
        ),
    )
    scope = CodeRetainedScopeProjection(
        "repo",
        _digest("observation"),
        _body("aware.workspace.toml", b"workspace"),
        (module,),
        packages,
    )
    return scope, _catalog(authority, planning)


def test_one_grant_nonparticipant_retained_and_deterministic():
    scope, catalog = fixture()
    policy = calculate_registry_policy(scope, catalog)
    assert len(scope.packages) == 2
    assert len(policy.grants) == 1
    assert policy.grants[0].namespace == "home"
    assert policy.grants[0].owned_roots == ("home",)
    assert policy.declaration_scope_digest == scope.projection_digest
    assert calculate_registry_policy(scope, catalog) == policy


@pytest.mark.parametrize(
    "before,after",
    [
        (
            'semantic_version = {state="present", value="1.0"}',
            'semantic_version = {state="unavailable"}',
        ),
        (
            'module_id="demo", package_id="provider"',
            'module_id="foreign", package_id="provider"',
        ),
        ('registration_key="demo"', 'registration_key="missing"'),
        ('semantic_package_kind = "sdk"', 'semantic_package_kind = "alias"'),
        ('manifest_filename = "aware.demo.toml"', 'manifest_filename = "other.toml"'),
    ],
)
def test_invalid_retained_claims_refuse(before, after):
    scope, catalog = fixture(lambda s: s.replace(before, after))
    with pytest.raises(ValueError):
        calculate_registry_policy(scope, catalog)


def test_filtered_nonparticipant_refuses():
    scope, catalog = fixture()
    with pytest.raises(ContractViolation, match="membership"):
        calculate_registry_policy(replace(scope, packages=scope.packages[:1]), catalog)


def test_relationship_policy_does_not_require_target_execution_profile():
    scope, catalog = fixture()
    unavailable = _catalog(_binding(profile_ref="foreign"))
    assert calculate_registry_policy(scope, unavailable) == calculate_registry_policy(
        scope, catalog
    )


@pytest.mark.parametrize(
    "before,after",
    [
        ('profile_ref="planning"', 'profile_ref="substitute"'),
        ('semantic_package_family = "public"', 'semantic_package_family = "foreign"'),
        ('role = "sdk", name =', 'role = "foreign", name ='),
    ],
)
def test_declared_relationship_facts_do_not_imply_catalog_correspondence(before, after):
    from aware_code_module_manifest_contract_runtime import parse_module_manifest
    from aware_code_retained_registry_policy_runtime.calculation import (
        _catalog_correspondence,
        _plain,
    )

    scope, catalog = fixture(lambda s: s.replace(before, after))
    grant = calculate_registry_policy(scope, catalog)
    assert len(grant.grants) == 1
    model = parse_module_manifest(scope.modules[0].manifest.body)
    registration = next(r for d in model.package_declarations for r in d.registrations)
    with pytest.raises(ContractViolation):
        _catalog_correspondence(_plain(registration), catalog, package_kind="sdk")


def test_relationship_policy_still_rejects_malformed_catalog():
    scope, _ = fixture()
    with pytest.raises(ContractViolation, match="exact Code catalog"):
        calculate_registry_policy(scope, object())


def test_comment_changes_scope_not_grants():
    scope, catalog = fixture()
    changed, _ = fixture(lambda s: "# comment\n" + s)
    first = calculate_registry_policy(scope, catalog)
    second = calculate_registry_policy(changed, catalog)
    assert first.grants == second.grants
    assert first.declaration_scope_digest != second.declaration_scope_digest


def test_missing_dependency_target_refuses():
    scope, catalog = fixture(
        lambda s: s.replace(
            'dependency_targets = {state="present", value=[]}',
            'dependency_targets = {state="present", value=[{dependency_kind="module", dependency_ref="x", targets=[{module_id="foreign", package_id="x"}], constraints=[]}]}',
        )
    )
    with pytest.raises(ContractViolation, match="dependency"):
        calculate_registry_policy(scope, catalog)


@pytest.mark.parametrize("conflict", ["namespace", "roots", "none"])
def test_multiple_occurrences_conflict_or_complete_grants(conflict):
    scope, catalog = fixture()
    source = scope.modules[0].manifest.body.decode()
    start = source.index('[[packages]]\nid = "home"')
    extra = source[start:].replace("home", "second")
    if conflict == "namespace":
        extra = extra.replace(
            'namespace = {state="present", value="second"}',
            'namespace = {state="present", value="home"}',
        )
    if conflict == "roots":
        extra = extra.replace(
            'owned_roots = {state="present", value=["second"]}',
            'owned_roots = {state="present", value=["home"]}',
        )
    module = replace(
        scope.modules[0],
        manifest=_body("demo/aware.module.toml", (source + extra).encode()),
    )
    second = replace(
        scope.packages[0],
        package_id="second",
        package_root="demo/second",
        source_identity_digest=_digest("second"),
        manifest=_body("demo/second/aware.demo.toml", b"second"),
    )
    scope = replace(scope, modules=(module,), packages=(*scope.packages, second))
    if conflict == "none":
        assert len(calculate_registry_policy(scope, catalog).grants) == 2
    else:
        with pytest.raises(ContractViolation, match="conflicting"):
            calculate_registry_policy(scope, catalog)


def test_v1_module_refuses_even_without_occurrences():
    scope, catalog = fixture()
    module = replace(
        scope.modules[0],
        manifest=_body(
            "demo/aware.module.toml",
            b'aware = 1\n[[packages]]\nid = "home"\nkind = "sdk"\nmanifest = "home/aware.demo.toml"\n',
        ),
    )
    with pytest.raises(ContractViolation, match="all modules v2"):
        calculate_registry_policy(replace(scope, modules=(module,)), catalog)


def test_wrong_retained_kind_refuses():
    scope, catalog = fixture()
    with pytest.raises(ContractViolation, match="membership"):
        calculate_registry_policy(
            replace(
                scope,
                packages=(
                    replace(scope.packages[0], package_kind="foreign"),
                    scope.packages[1],
                ),
            ),
            catalog,
        )


def test_explicit_kind_correspondence_is_retained_and_execution_checked():
    from aware_code_module_manifest_contract_runtime import parse_module_manifest
    from aware_code_module_manifest_contract_runtime.v2_codec import (
        decode_module_manifest_meaning_v2,
        encode_module_manifest_meaning_v2,
    )
    from aware_code_retained_registry_policy_runtime.calculation import (
        _catalog_correspondence,
        _plain,
    )

    scope, catalog = fixture(
        lambda s: s.replace(
            'semantic_package_kind = "sdk"',
            'semantic_package_kind = "sdk_semantic"\ndeclared_package_kinds = ["sdk"]',
        )
    )
    policy = calculate_registry_policy(scope, catalog)
    grant = policy.grants[0]
    assert (grant.declared_package_kind, grant.semantic_package_kind) == (
        "sdk",
        "sdk_semantic",
    )
    model = parse_module_manifest(scope.modules[0].manifest.body)
    body = encode_module_manifest_meaning_v2(model)
    assert (
        encode_module_manifest_meaning_v2(decode_module_manifest_meaning_v2(body))
        == body
    )
    registration = next(r for d in model.package_declarations for r in d.registrations)
    declared = _plain(registration)
    assert declared["declared_package_kinds"] == ["sdk"]
    _catalog_correspondence(declared, catalog, package_kind="sdk")
    with pytest.raises(ContractViolation, match="correspondence unavailable"):
        _catalog_correspondence(declared, catalog, package_kind="foreign")
    # Even an owner-declared kind must be supported by the actual execution profile.
    declared["declared_package_kinds"] = ["foreign", "sdk"]
    with pytest.raises(ContractViolation, match="catalog package"):
        _catalog_correspondence(declared, catalog, package_kind="foreign")


@pytest.mark.parametrize(
    "value", ["[]", "[true]", '"sdk"', '["sdk", "sdk"]', '["z", "a"]']
)
def test_malformed_kind_correspondence_rejects(value):
    with pytest.raises(ValueError):
        scope, catalog = fixture(
            lambda s: s.replace(
                'semantic_package_kind = "sdk"',
                'semantic_package_kind = "sdk"\ndeclared_package_kinds = ' + value,
            )
        )

        calculate_registry_policy(scope, catalog)

def test_kind_correspondence_is_bound_to_registration_digest():
    original_scope, catalog = fixture()
    explicit_scope, _ = fixture(
        lambda s: s.replace(
            'semantic_package_kind = "sdk"',
            'semantic_package_kind = "sdk"\ndeclared_package_kinds = ["sdk"]',
        )
    )
    before = calculate_registry_policy(original_scope, catalog).grants[0]
    after = calculate_registry_policy(explicit_scope, catalog).grants[0]
    assert (
        before.registration_declaration_digest != after.registration_declaration_digest
    )
    assert before.declared_package_kind == after.declared_package_kind == "sdk"
    assert before.semantic_package_kind == after.semantic_package_kind == "sdk"
