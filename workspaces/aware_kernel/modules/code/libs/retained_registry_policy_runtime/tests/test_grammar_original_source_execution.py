"""Genuine source interpretation; disposable bootstrap, not installed readiness.

SDK's genuine definition product is the bounded syntax consumer. No
fixture catalog/profile binding, manufactured Workspace expectation or observed
Language result frame supplies authority. Parser assembly and Meta are separate.
"""

from contextlib import ExitStack, asynccontextmanager, nullcontext
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_module_manifest_contract_runtime import (
    AwareModuleTomlError,
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
    parse_module_manifest,
)
from aware_code_module_manifest_contract_runtime.grammar_profile_source import (
    GrammarProfileSourceError,
    parse_registered_grammar_profile,
)
from aware_code_module_manifest_contract_runtime.profile_codec import (
    decode_profile_manifest,
    encode_profile_manifest,
)
from aware_code_module_manifest_contract_runtime.profile_models import (
    CodeSemanticContractProfileManifestSpec,
    CodeSemanticContractProfileManifestSpecV2,
)
from aware_code_module_manifest_contract_runtime.profile_parser import (
    parse_profile_manifest,
)
from aware_code_module_manifest_contract_runtime.v2_parser import thaw
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import grammar_profile_role as profile
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as cleanup
from aware_code_retained_registry_policy_runtime import grammar_syntax_role as syntax
from aware_code_semantic_contract_runtime import selected_provider
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    grammar_operational_profile,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_REF,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
)
from aware_language_parsed_document_contract import (
    SyntaxContractRefV1,
    SyntaxContributionSourceV1,
    SyntaxExpressionV1,
    SyntaxRuleV1,
    encode_syntax_assembly_value,
)
from aware_sdk_contract_runtime_provider import (
    SDK_GRAPH_PRODUCT_FACTORY_REF,
    construct_sdk_graph_product_factory_product,
)
from aware_sdk_contract_runtime_provider.authority_stage import (
    sdk_package_authority_profile,
)
from aware_sdk_contract_runtime_provider.planning_stage import sdk_planning_profile
from aware_sdk_contract_runtime_provider.profile import sdk_definition_profile
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as workspace
from test_current_head_two_stage_host import (
    real_sdk_factory as _original_stage_admission,
)
from test_dependency_scope_admission import fixture as repository
from test_grammar_original_planning_target import selected_carrier
from test_grammar_original_workspace_host import (
    grammar_admissions as _original_product_admissions,
)
from test_syntax_declaration import source, toml_value

grammar_admissions = _original_product_admissions
sdk_stage_admission = _original_stage_admission
PROFILE_KEY = "original.grammar"
SOURCE_PATH = "consumer/modules/main/provider/syntax/definition.syntax.json"
MODULE_PATH = "consumer/modules/main/aware.module.toml"
PROFILE_PATH = (
    "consumer/semantic_contract/profiles/original.grammar/"
    "aware.semantic_contract_profile.toml"
)


@pytest.fixture(scope="module")
def sdk_admission():
    return selected_provider._admit_selected_provider_factory(
        factory_ref=SDK_GRAPH_PRODUCT_FACTORY_REF,
        provider_key=sdk_definition_profile().providers[0].provider_key,
        selection_factory=construct_sdk_graph_product_factory_product,
    )


def authored_repository(root, *, stage_pair=False):
    """Author bytes before original Workspace observation, without relabelling."""
    registered = sdk_planning_profile() if stage_pair else sdk_definition_profile()
    consumer = registered.providers[0]
    consumed = next(
        row
        for row in consumer.consumed_roles
        if row.role == ("manifest_source" if stage_pair else "definition_request")
    )
    ref = consumed.accepted_contracts[0]
    declaration = {
        "version": 1,
        "contributions": ["syntax/definition.syntax.json"],
        "anchors": [
            {
                "consumer_contract": {
                    "key": ref.key,
                    "version": ref.version,
                    "schema_digest": ref.schema_digest.value,
                },
                "role": consumed.role,
                "rule_name": "definition",
                "field_path": ["sdk_identity"],
                "required": True,
                "top_level": True,
            }
        ],
    }
    module = (
        source(declaration, version=3)
        .decode()
        .replace(
            'provider_key = "demo"', 'provider_key = "' + consumer.provider_key + '"'
        )
        .replace(
            'owns_manifest_kinds = ["demo"]', 'owns_manifest_kinds = ["aware_sdk_toml"]'
        )
        .replace('role = "demo.provider"', 'role = "aware_sdk.provider"')
        .replace(
            'module = "demo.provider"', 'module = "aware_sdk_contract_runtime_provider"'
        )
    )
    profiles = (
        [
            {
                "stage": "source_planning",
                "profile_ref": registered.profile_ref,
                "profile_version": registered.version,
                "profile_digest": registered.digest.value,
            },
            {
                "stage": "authority_derivation",
                "profile_ref": sdk_package_authority_profile().profile_ref,
                "profile_version": sdk_package_authority_profile().version,
                "profile_digest": sdk_package_authority_profile().digest.value,
            },
        ]
        if stage_pair
        else [
            {
                "stage": "graph_product",
                "profile_ref": registered.profile_ref,
                "profile_version": registered.version,
                "profile_digest": registered.digest.value,
            }
        ]
    )
    if stage_pair:
        profiles.reverse()  # Original module grammar orders authority before planning.
    module += (
        "[[packages.semantic_contract.registrations]]\n"
        'key="definition"\nmanifest_contract_kind="aware_sdk_toml"\n'
        'manifest_filename="aware.sdk.toml"\nsemantic_package_family="public"\n'
        'semantic_package_kind="sdk"\n'
        'semantic_contract={role="aware_sdk.provider",name="sdk_definition",'
        "provider_key="
        + toml_value(consumer.provider_key)
        + ',coordinate="code.semantic-contract:'
        + consumer.provider_key
        + '"}\n'
        'supported_languages=["aware"]\ncode_package_surface={state="absent"}\n'
        "profiles=" + toml_value(profiles) + "\n"
    )
    module += """
[packages.semantic_admission]
registration={state="unavailable"}
semantic_package_name={state="present",value="original-grammar"}
semantic_version={state="present",value="1"}
code_package_name={state="present",value="original-grammar-code"}
source_code_package_id={state="absent"}
configuration={state="absent"}
namespace={state="present",value="original_grammar"}
owned_roots={state="present",value=["original_grammar"]}
dependency_targets={state="present",value=[]}
"""
    (root / MODULE_PATH).write_text(module)
    package = root / "consumer/modules/main/provider"
    (package / "syntax").mkdir(parents=True)
    (package / "pyproject.toml").write_text(
        '[project]\nname="original-grammar-source"\nversion="1.0"\n'
    )
    payload = SyntaxContributionSourceV1(
        "original-definition",
        "1",
        SyntaxContractRefV1(
            consumer.provider_contract.key,
            consumer.provider_contract.version,
            consumer.provider_contract.schema_digest.value,
        ),
        (),
        (SyntaxRuleV1("definition", SyntaxExpressionV1("STRING", value="definition")),),
        ("definition",),
        ("definition",),
        (),
        (),
        None,
    )
    (root / SOURCE_PATH).write_bytes(encode_syntax_assembly_value(payload))
    (root / "consumer/aware.workspace.toml").write_text(
        'aware=2\n[workspace]\nhandle="Consumer"\n'
        '[[workspace.modules]]\nid="main"\npath="modules/main"\n'
        "[[workspace.code_semantic_contract_profile_packages]]\n"
        'profile_key="original.grammar"\n'
        'profile_package_ref="workspace://Consumer#original.grammar"\n'
    )
    profile_path = root / PROFILE_PATH
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(
        (
            "aware_semantic_contract_profile=1\n"
            if stage_pair
            else "aware_semantic_contract_profile=2\n"
        )
        + "[profile]\n"
        'key="original.grammar"\npackage_key="independent.package"\n'
        'runtime_import_mode="registered_contracts"\n'
        '[[providers]]\nmodule_id="main"\n'
        + (
            ""
            if stage_pair
            else 'package_id="provider"\nregistration_key="definition"\nexposure="graph_product"\n'
        )
        + "provider_key="
        + toml_value(consumer.provider_key)
        + "\n"
    )


@asynccontextmanager
async def original_execution(
    tmp_path, admissions, *, stage_admission=None, amend=None, compose_roles=True
):
    # The original helper owns a real session/store and borrowed lifecycle.
    # Its six returned resources are consumed without manufacturing another owner.
    def author(root):
        authored_repository(root, stage_pair=stage_admission is not None)
        if amend is not None:
            amend(root)

    async with repository(tmp_path, author) as (
        root,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        digest = ContentDigest.of_bytes(b"original source execution test bootstrap")
        implementation = SemanticImplementationCoordinate(
            "test.original.grammar", digest
        )
        configuration = SemanticConfigurationCoordinate("test.original.grammar", digest)
        with workspace.compose_direct_workspace_selected_host(
            factory_admission=stage_admission,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            composition_implementation=implementation,
            composition_configuration=configuration,
            policy_implementation=implementation,
            policy_configuration=configuration,
            product_factory_admissions=admissions,
        ) as paired:
            command = paired.staged.command
            issuer = command.sources.declaration_scope_runtime
            with workspace._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="provider",
            ) as selected:
                with ExitStack() as stack:
                    c = SimpleNamespace(issuer=issuer)
                    carrier = await selected_carrier(
                        stack, c, selected, "original-authored-grammar-selection"
                    )
                    contexts = (
                        inputs.SemanticInputContextContract(
                            "declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF
                        ),
                        inputs.SemanticInputContextContract(
                            "grammar_source_group", GRAMMAR_SOURCE_GROUP_REF
                        ),
                    )
                    uses = tuple(
                        stack.enter_context(
                            issuer.original_grouped_selected_source_input(
                                root=carrier,
                                participants=(),
                                dependency_edges=(),
                                use_ref="original-authored-grammar-" + stage,
                                stage=stage,
                                source_contracts=carrier.source_contracts,
                                context_contracts=contexts,
                            )
                        )
                        for stage in ("profile_selection", "syntax_binding")
                    )
                    first = role = None
                    if compose_roles:
                        first = profile._compose_grammar_profile_source_role(
                            code_host=paired.code_host,
                            profile_expected=uses[0],
                            syntax_expected=uses[1],
                            profile_key=PROFILE_KEY,
                        )
                        stack.callback(profile.close_grammar_profile_source_role, first)
                        role = syntax._compose_grammar_syntax_role_join(
                            profile_role=first
                        )
                        stack.callback(syntax.close_grammar_syntax_role_join, role)
                    yield SimpleNamespace(
                        root=root,
                        paired=paired,
                        issuer=issuer,
                        selected=selected,
                        carrier=carrier,
                        expected=uses,
                        first=first,
                        role=role,
                    )


def test_original_code_product_key_cannot_be_aliased_into_v1_module():
    consumer = grammar_operational_profile("profile_selection").providers[0]
    body = source(version=3).replace(
        b'provider_key = "demo"',
        ('provider_key = "' + consumer.provider_key + '"').encode(),
    )
    with pytest.raises(AwareModuleTomlError, match="provider_key must match"):
        parse_module_manifest(body)


def test_v1_profile_cannot_name_original_sdk_product():
    key = sdk_definition_profile().providers[0].provider_key
    body = (
        'aware_semantic_contract_profile=1\n[profile]\nkey="original.grammar"\n'
        'package_key="independent.package"\nruntime_import_mode="registered_contracts"\n'
        '[[providers]]\nmodule_id="main"\nprovider_key=' + toml_value(key) + "\n"
    ).encode()
    with pytest.raises(AwareModuleTomlError, match="provider_key must match"):
        parse_registered_grammar_profile(body, profile_key=PROFILE_KEY)


def test_owner_v2_profile_is_preserved_by_explicit_grammar_receiving(tmp_path):
    root = tmp_path / "repository"
    (root / "consumer/modules/main").mkdir(parents=True)
    authored_repository(root)
    body = (root / PROFILE_PATH).read_bytes()
    value = parse_profile_manifest(body)
    assert type(value) is CodeSemanticContractProfileManifestSpecV2
    assert decode_profile_manifest(encode_profile_manifest(value)) == value
    assert value.providers[0].provider_key == "sdk-definition"
    assert value.providers[0].exposure == "graph_product"
    assert (
        parse_module_manifest((root / MODULE_PATH).read_bytes())
        .packages[0]
        .semantic_contract.syntax
    )
    assert parse_registered_grammar_profile(body, profile_key=PROFILE_KEY) == value


async def test_original_workspace_reaches_registered_v2_execution_and_normal_close(
    tmp_path, grammar_admissions, sdk_admission
):
    async with original_execution(tmp_path, (*grammar_admissions, sdk_admission)) as c:
        state = profile._state(c.first, live=True)
        assert state.attachment.methods[0].receiver is c.issuer
        assert (
            c.expected[0].operation_identity
            is c.paired.staged.command.invocation_parent
        )
        predecessor = await profile.execute_grammar_profile_source_role(c.first)
        syntax_state = syntax._state(c.role, live=True)
        result = await syntax.execute_grammar_syntax_role_join(
            c.role, predecessor=predecessor
        )
        value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
        assert value.profile_ref == sdk_definition_profile().profile_ref
        assert value.code_profile_digest == sdk_definition_profile().digest
        assert value.interpretation_profile == predecessor.coordinate
        assert len(value.provider_bindings) == len(value.contribution_bindings) == 1
        assert value.provider_bindings[0].provider_key == "sdk-definition"
        assert syntax_state.resources.result is result
        assert syntax_state.resources.result_status == "pending"
        assert syntax_state.resources.join_status == "released"
        assert syntax_state.join_record.consumed
        assert len(syntax_state.resources.profile.host._results) == 2
        receipt = syntax.close_grammar_syntax_role_join(c.role)
        assert receipt.completion == "verified" and receipt.cause == "normal_close"
        assert (
            syntax_state.resources.result_status
            == state.resources.result_status
            == "released"
        )
        assert syntax.close_grammar_syntax_role_join(c.role) is receipt
        assert not direct._HOSTS[c.paired.code_host].closed


@pytest.mark.parametrize(
    "field",
    (
        "module_id",
        "package_id",
        "registration_key",
        "provider_key",
        "profile_ref",
        "profile_version",
        "profile_digest",
    ),
)
async def test_original_v2_nomination_substitutions_refuse_before_retention(
    tmp_path, grammar_admissions, sdk_admission, field
):
    def amend(root):
        registered = sdk_definition_profile()
        before = {
            "module_id": "main",
            "package_id": "provider",
            "registration_key": "definition",
            "provider_key": "sdk-definition",
            "profile_ref": registered.profile_ref,
            "profile_version": registered.version,
            "profile_digest": registered.digest.value,
        }
        changed = "sha256:" + "b" * 64 if field == "profile_digest" else "foreign"
        path = root / (MODULE_PATH if field.startswith("profile_") else PROFILE_PATH)
        body = path.read_bytes()
        needle = (field + "=" + toml_value(before[field])).encode()
        assert body.count(needle) == 1
        path.write_bytes(
            body.replace(needle, (field + "=" + toml_value(changed)).encode())
        )

    async with original_execution(
        tmp_path, (*grammar_admissions, sdk_admission), amend=amend
    ) as c:
        state = profile._state(c.first, live=True)
        expected_error = (
            GrammarProfileSourceError
            if field == "package_id"
            else (ContractViolation, GrammarProfileSourceError)
        )
        with pytest.raises(expected_error) as caught:
            await profile.execute_grammar_profile_source_role(c.first)
        if field == "package_id":
            assert type(caught.value) is GrammarProfileSourceError
            assert caught.value.reason == "syntax_provider_declaration_mismatch"
        assert state.resources.result is None and state.attachment.retired
        with pytest.raises(ContractViolation, match="role join is unavailable"):
            syntax.close_grammar_syntax_role_join(c.role)
        receipt = cleanup.read_grammar_role_cleanup(state.resources.custody.ticket)
        assert receipt.completion == "unverified"
        assert syntax.close_grammar_syntax_role_join(c.role) is receipt
        assert not direct._HOSTS[c.paired.code_host].closed


@pytest.mark.parametrize("path", (MODULE_PATH, PROFILE_PATH, SOURCE_PATH))
async def test_genuine_source_mutation_cannot_be_revived_by_restoration(
    tmp_path, grammar_admissions, sdk_admission, path
):
    # A changed selected body permanently retires its original Workspace use;
    # restoration cannot turn that context's own exit validation into success.
    exit_refusal = (
        pytest.raises(
            SourceObservationUnavailable, match="original_pre_request_input_required"
        )
        if path == SOURCE_PATH
        else nullcontext()
    )
    with exit_refusal:
        async with original_execution(
            tmp_path, (*grammar_admissions, sdk_admission)
        ) as c:
            state = profile._state(c.first, live=True)
            target = c.root / path
            before = target.read_bytes()
            target.write_bytes(before + b"\n")
            with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                await profile.execute_grammar_profile_source_role(c.first)
            assert state.resources.result is None and state.attachment.retired
            target.write_bytes(before)
            with pytest.raises(ContractViolation):
                await profile.execute_grammar_profile_source_role(c.first)
            receipt = syntax.close_grammar_syntax_role_join(c.role)
            assert receipt.cause != "normal_close"
            assert syntax.close_grammar_syntax_role_join(c.role) is receipt
            assert not direct._HOSTS[c.paired.code_host].closed


@pytest.mark.parametrize(
    "field", ("module_id", "package_id", "registration_key", "provider_key")
)
def test_v2_portable_coordinates_are_not_registration_authority(tmp_path, field):
    """Existing owner data accepts valid text; the proposed receiving join must correlate it."""
    root = tmp_path / "repository"
    (root / "consumer/modules/main").mkdir(parents=True)
    authored_repository(root)
    value = parse_profile_manifest((root / PROFILE_PATH).read_bytes())
    original = value.providers[0]
    replacement = "foreign-product" if field == "provider_key" else "foreign"
    changed = replace(value, providers=(replace(original, **{field: replacement}),))
    assert decode_profile_manifest(encode_profile_manifest(changed)) == changed
    assert getattr(changed.providers[0], field) != getattr(original, field)
    body = (root / PROFILE_PATH).read_bytes()
    needle = (field + "=" + toml_value(getattr(original, field))).encode()
    assert body.count(needle) == 1
    body = body.replace(needle, (field + "=" + toml_value(replacement)).encode())
    assert parse_profile_manifest(body) == changed
    # Portable nominations are data; original execution must correlate them.
    assert parse_registered_grammar_profile(body, profile_key=PROFILE_KEY) == changed


@pytest.mark.parametrize("field", ("profile_ref", "profile_version", "profile_digest"))
def test_v3_full_product_identity_survives_owner_codec_without_becoming_admission(
    tmp_path, field
):
    root = tmp_path / "repository"
    (root / "consumer/modules/main").mkdir(parents=True)
    authored_repository(root)
    original = sdk_definition_profile()
    replacements = {
        "profile_ref": "aware.sdk.foreign-product",
        "profile_version": "99",
        "profile_digest": "sha256:" + "b" * 64,
    }
    before = {
        "profile_ref": original.profile_ref,
        "profile_version": original.version,
        "profile_digest": original.digest.value,
    }
    body = (root / MODULE_PATH).read_bytes()
    needle = (field + "=" + toml_value(before[field])).encode()
    assert body.count(needle) == 1
    changed = body.replace(
        needle, (field + "=" + toml_value(replacements[field])).encode()
    )
    model = parse_module_manifest(changed)
    assert (
        decode_module_manifest_meaning(encode_module_manifest_meaning(model)) == model
    )
    registration = thaw(model.package_declarations[0].registrations[0])
    assert registration["profiles"][0]["stage"] == "graph_product"
    assert registration["profiles"][0][field] == replacements[field]
    assert registration["profiles"][0][field] != before[field]
    # A well-formed nomination may be inconsistent with the genuine profile.
    assert original == sdk_definition_profile()


@pytest.mark.parametrize("shape", ("stage_pair", "multiple_products"))
def test_public_v2_shapes_do_not_implicitly_enable_the_narrow_grammar_cut(
    tmp_path, shape
):
    root = tmp_path / "repository"
    (root / "consumer/modules/main").mkdir(parents=True)
    authored_repository(root)
    value = parse_profile_manifest((root / PROFILE_PATH).read_bytes())
    row = value.providers[0]
    if shape == "stage_pair":
        changed = replace(
            value,
            providers=(replace(row, provider_key="aware_sdk", exposure="stage_pair"),),
        )
    else:
        changed = replace(
            value,
            providers=(
                row,
                replace(row, provider_key="foreign-product", package_id="foreign"),
            ),
        )
    assert decode_profile_manifest(encode_profile_manifest(changed)) == changed
    body = (root / PROFILE_PATH).read_bytes()
    if shape == "stage_pair":
        body = body.replace(b'"sdk-definition"', b'"aware_sdk"').replace(
            b'exposure="graph_product"', b'exposure="stage_pair"'
        )
    else:
        body += (
            b'[[providers]]\nmodule_id="main"\npackage_id="foreign"\n'
            b'registration_key="definition"\nexposure="graph_product"\n'
            b'provider_key="foreign-product"\n'
        )
    assert parse_profile_manifest(body) == changed
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_registered_grammar_profile(body, profile_key=PROFILE_KEY)
    assert caught.value.reason == "unsupported_profile_mode"


def test_legacy_grammar_receiving_keeps_its_existing_owner_model_and_wire(tmp_path):
    root = tmp_path / "repository"
    (root / "consumer/modules/main").mkdir(parents=True)
    authored_repository(root, stage_pair=True)
    body = (root / PROFILE_PATH).read_bytes()
    original = parse_profile_manifest(body)
    assert type(original) is CodeSemanticContractProfileManifestSpec
    received = parse_registered_grammar_profile(body, profile_key=PROFILE_KEY)
    assert type(received) is CodeSemanticContractProfileManifestSpec
    assert encode_profile_manifest(received) == encode_profile_manifest(original)
    assert received.providers[0].provider_key == "aware_sdk"
    assert not hasattr(received.providers[0], "registration_key")


async def test_original_stage_pair_catalog_cannot_choose_profile_by_key(
    tmp_path, grammar_admissions, sdk_stage_admission
):
    async with original_execution(
        tmp_path, grammar_admissions, stage_admission=sdk_stage_admission
    ) as c:
        state = profile._state(c.first, live=True)
        resolver = state.attachment.retention.resolver
        candidates = tuple(
            row.profile_declaration
            for row in resolver.catalog.entries
            if tuple(p.provider_key for p in row.profile_declaration.providers)
            == ("aware_sdk",)
        )
        assert {row.profile_ref for row in candidates} == {
            sdk_planning_profile().profile_ref,
            sdk_package_authority_profile().profile_ref,
        }
        with pytest.raises(
            ContractViolation,
            match="complete original grammar profile is absent or ambiguous",
        ):
            await profile.execute_grammar_profile_source_role(c.first)
        assert state.resources.result is None and state.attachment.retired
        with pytest.raises(ContractViolation, match="role join is unavailable"):
            syntax.close_grammar_syntax_role_join(c.role)
        receipt = cleanup.read_grammar_role_cleanup(state.resources.custody.ticket)
        assert receipt.completion == "unverified"
