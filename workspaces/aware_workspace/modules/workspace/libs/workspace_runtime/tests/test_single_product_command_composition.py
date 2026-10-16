"""Original Workspace/Code composition with Attention's real source factory.

Disposable declarations and source-admitted factory mechanics are explicit;
this does not install that factory or publish a production package HEAD.
"""

import re

import pytest
from aware_attention_definition_contract_runtime_provider.profile import (
    ATTENTION_DEFINITION_PROVIDER_KEY,
    attention_definition_profile,
)
from aware_attention_definition_contract_runtime_provider.selected_factory import (
    construct_attention_definition_factory_product,
)
from aware_code_retained_registry_policy_runtime import direct_host as code
from aware_code_retained_registry_policy_runtime.selected_catalog_eligibility import (
    check_selected_product_catalog_eligibility_locked,
    issue_selected_product_catalog_eligibility,
    read_selected_product_catalog_eligibility,
)
from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.stage_contribution import (
    compose_selected_provider_stage_catalog_input,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from test_current_head_two_stage_host import (
    real_environment_factory as _original_stage_factory,
)
from test_dependency_scope_admission import fixture as sources
from test_observed_semantic_issuers import PROVIDER, occurrence


@pytest.fixture(scope="module")
def factory():
    return selected._admit_selected_provider_factory(
        factory_ref="proof:workspace.attention.product-only.v1",
        provider_key=ATTENTION_DEFINITION_PROVIDER_KEY,
        selection_factory=construct_attention_definition_factory_product,
    )


@pytest.fixture(scope="module")
def stage_factory():
    return _original_stage_factory.__wrapped__()


def _attention_repository(root, *, imported=False):
    key = ATTENTION_DEFINITION_PROVIDER_KEY
    profile = attention_definition_profile()
    consumer = root / "consumer/modules/main"
    package = consumer / "attention"
    package.mkdir()
    (package / "aware.attention.toml").write_text(
        'aware_attention=1\n[attention]\npackage_name="sample_attention"\n'
        'fqn_prefix="sample_attention"\n[build]\nsources_dir="."\n'
        'include_paths=["**/*.aware"]\nexclude_paths=[]\n'
    )
    (package / "source.aware").write_text("authored source retained by Workspace")
    admission = (
        occurrence("sample_attention")
        .replace(
            'value={module_id="main",package_id="provider",',
            'value={scope={kind="dependency",workspace_handle="Target"},'
            'module_id="main",package_id="provider",',
        )
        .replace('value="1.0"', 'value="1"')
    )
    if not imported:
        admission = admission.replace(
            'scope={kind="dependency",workspace_handle="Target"}',
            'scope={kind="local"}',
        )
    (consumer / "aware.module.toml").write_text(
        'aware=3\n[[packages]]\nid="attention"\nkind="attention"\n'
        'manifest="attention/aware.attention.toml"\nvisibility="module"\n' + admission
    )
    provider = root / "target/modules/main"
    (provider / "provider").mkdir()
    (provider / "provider/pyproject.toml").write_bytes(b"declared owner distribution")
    body = PROVIDER.replace('provider_key="demo"', f'provider_key="{key}"')
    body = body.replace("example_toml", "aware_attention_toml")
    body = body.replace("aware.example.toml", "aware.attention.toml")
    body = body.replace(
        'semantic_package_family="example"', 'semantic_package_family="attention"'
    )
    body = body.replace(
        'semantic_package_kind="example"', 'semantic_package_kind="attention"'
    )
    body = body.replace(
        'role="example",name="example"',
        'role="aware_attention.provider",name="attention_definition"',
    )
    body = re.sub(
        r"profiles=\[.*?\n\]",
        'profiles=[{stage="graph_product",profile_ref="'
        + profile.profile_ref
        + '",profile_version="'
        + profile.version
        + '",profile_digest="'
        + profile.digest.to_wire()
        + '"}]',
        body,
        flags=re.DOTALL,
    )
    if imported:
        (provider / "aware.module.toml").write_text("aware=3\n" + body)
        for path in (
            root / "consumer/aware.workspace.toml",
            root
            / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml",
        ):
            path.write_text(path.read_text().replace('"demo"', '"' + key + '"'))
    else:
        (consumer / "provider").mkdir()
        (consumer / "provider/pyproject.toml").write_bytes(
            b"declared owner distribution"
        )
        path = consumer / "aware.module.toml"
        path.write_text(path.read_text() + body)


def _coordinates():
    digest = ContentDigest.of_bytes(b"source-only fixed Workspace test composition")
    return {
        "composition_implementation": SemanticImplementationCoordinate(
            "proof.workspace", digest
        ),
        "composition_configuration": SemanticConfigurationCoordinate(
            "proof.workspace", digest
        ),
        "policy_implementation": SemanticImplementationCoordinate(
            "proof.policy", digest
        ),
        "policy_configuration": SemanticConfigurationCoordinate("proof.policy", digest),
    }


def _host(borrowed, factory, *, command=None):
    return composition.compose_direct_workspace_selected_host(
        product_factory_admissions=(factory,),
        session=borrowed._session,
        store=borrowed._store,
        workspace_manifest_path="consumer/aware.workspace.toml",
        command_resources=command,
        **_coordinates(),
    )


async def test_original_attention_product_host_policy_intent_and_locked_eligibility(
    tmp_path,
    factory,
    monkeypatch,
):
    def forbidden_stage_pair(*args):
        raise AssertionError("product-only host must never acquire a stage pair")

    monkeypatch.setattr(
        composition, "issue_selected_provider_stage_contribution", forbidden_stage_pair
    )
    async with sources(tmp_path, _attention_repository) as (_, _, _, borrowed, _, _):
        with _host(borrowed, factory) as hosted:
            staged, host = hosted.staged, hosted.code_host
            command = staged.command
            assert staged.contribution is None
            assert staged.stage_runtime_bindings == ()
            assert len(staged.product_runtime_bindings) == 1
            expected = code._HOSTS[host].expected
            assert expected.stage_runtime_bindings == ()
            assert expected.runtime is staged.product_runtime_bindings[0].runtime
            assert "authority_code_runtime" not in {
                item.role for item in expected.resources
            }
            with composition._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="attention",
            ) as source:
                policy = code.produce_registry_policy(host, source)
                intent, product = derive_selected_root_intent(host, policy)
                assert product.role == "attention_definition_manifest"
                assert intent.requested_semantic_root_refs == (
                    "sample_attention.a",
                    "sample_attention.b",
                )
                registration = staged.product_runtime_bindings[0].registration
                eligibility = issue_selected_product_catalog_eligibility(
                    host, policy, registration
                )
                view = read_selected_product_catalog_eligibility(eligibility)
                assert view.semantic_provider_key == ATTENTION_DEFINITION_PROVIDER_KEY
                guard = command.lifetime_runtime.acquire_catalog_epoch_exclusion(
                    command.invocation_parent,
                    expected=command.catalog_host.read_initial_publication().invocation,
                )
                try:
                    check_selected_product_catalog_eligibility_locked(
                        eligibility, guard=guard
                    )
                finally:
                    command.lifetime_runtime.release_catalog_epoch_exclusion(guard)
                original = staged.product_contributions[0]
        assert host not in code._HOSTS
        with pytest.raises(ContractViolation):
            products.read_selected_provider_product_contribution(original)
        with pytest.raises(ContractViolation):
            read_selected_product_catalog_eligibility(eligibility)
        assert borrowed._session.authority_admitted


@pytest.mark.parametrize("changed", ["source", "profile"])
async def test_product_host_rejects_changed_original_source_and_cleans_owned_product(
    tmp_path,
    factory,
    changed,
):
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with _host(borrowed, factory) as hosted:
            command = hosted.staged.command
            with composition._compose_direct_workspace_selected_package_source(
                command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="attention",
            ) as source:
                code.produce_registry_policy(hosted.code_host, source)
                path = (
                    root / "consumer/modules/main/attention/source.aware"
                    if changed == "source"
                    else root
                    / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
                )
                path.write_bytes(path.read_bytes() + b"\nchanged retained evidence\n")
                with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                    code.produce_registry_policy(hosted.code_host, source)
                original = hosted.staged.product_contributions[0]
        with pytest.raises(ContractViolation):
            products.read_selected_provider_product_contribution(original)


async def test_product_only_host_borrows_one_original_command_parent(tmp_path, factory):
    async with sources(tmp_path, _attention_repository) as (_, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            with _host(borrowed, factory, command=command) as hosted:
                assert hosted.staged.command is command
                assert hosted.staged.stage_runtime_bindings == ()
            composition._require_live_direct_workspace_command(command)


async def test_partial_product_acquisition_retires_owned_registration(
    tmp_path, factory
):
    async with sources(tmp_path, _attention_repository) as (_, _, _, borrowed, _, _):
        before = set(products._CONTRIBUTIONS)
        with (
            pytest.raises(TypeError),
            composition._compose_direct_workspace_staged_command_resources(
                product_factory_admissions=(factory, object()),
                session=borrowed._session,
                store=borrowed._store,
                workspace_manifest_path="consumer/aware.workspace.toml",
                source_rail="declaration_v3",
            ),
        ):
            raise AssertionError("foreign factory cannot open a host")
        assert set(products._CONTRIBUTIONS) == before


async def test_imported_product_key_gap_refuses_without_alias_or_profile_grammar_change(
    tmp_path,
    factory,
):
    from aware_code_module_manifest_contract_runtime import AwareModuleTomlError

    async with sources(
        tmp_path, lambda root: _attention_repository(root, imported=True)
    ) as (
        _,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        with (
            _host(borrowed, factory) as hosted,
            composition._compose_direct_workspace_selected_package_source(
                hosted.staged.command,
                workspace_manifest_path="consumer/aware.workspace.toml",
                module_id="main",
                package_id="attention",
            ) as source,
        ):
            with pytest.raises(AwareModuleTomlError, match="provider_key must match"):
                code.produce_registry_policy(hosted.code_host, source)
            original = hosted.staged.product_contributions[0]
        with pytest.raises(ContractViolation):
            products.read_selected_provider_product_contribution(original)


def test_empty_original_catalog_and_legacy_product_only_mode_refuse():
    with pytest.raises(ContractViolation, match="at least one original"):
        compose_selected_provider_stage_catalog_input(
            (), catalog_ref="proof.empty", catalog_generation=1
        )
    with (
        pytest.raises(TypeError, match="original v3 products"),
        composition._compose_direct_workspace_staged_command_resources(
            product_factory_admissions=(),
            session=object(),
            store=object(),
            workspace_manifest_path="consumer/aware.workspace.toml",
        ),
    ):
        raise AssertionError("empty/legacy composition cannot acquire resources")


async def test_existing_stage_pair_still_uses_original_host(tmp_path, stage_factory):
    from test_v3_direct_command_composition import (
        test_direct_selected_host_composes_original_environment_without_service,
    )

    await test_direct_selected_host_composes_original_environment_without_service(
        tmp_path,
        stage_factory,
    )


@pytest.mark.parametrize("version", [1, 2, 3])
async def test_hyphenated_product_key_is_versioned_and_round_trips(tmp_path, version):
    from aware_code_module_manifest_contract_runtime import (
        AwareModuleTomlError,
        decode_module_manifest_meaning_v3,
        encode_module_manifest_meaning_v3,
        parse_module_manifest,
    )

    async with sources(tmp_path, _attention_repository) as (root, _, _, _, _, _):
        raw = (root / "consumer/modules/main/aware.module.toml").read_bytes()
        raw = raw.replace(b"aware=3", f"aware={version}".encode(), 1)
        if version != 3:
            with pytest.raises(AwareModuleTomlError, match="provider_key must match"):
                parse_module_manifest(raw)
        else:
            value = parse_module_manifest(raw)
            wire = encode_module_manifest_meaning_v3(value)
            assert decode_module_manifest_meaning_v3(wire) == value
            assert (
                encode_module_manifest_meaning_v3(
                    decode_module_manifest_meaning_v3(wire)
                )
                == wire
            )


@pytest.mark.parametrize("key", ["bad/key", "bad.key", "-bad", "BadKey", "bad key"])
async def test_product_provider_key_stays_a_bounded_lowercase_component(tmp_path, key):
    from aware_code_module_manifest_contract_runtime import (
        AwareModuleTomlError,
        parse_module_manifest,
    )

    async with sources(tmp_path, _attention_repository) as (root, _, _, _, _, _):
        raw = (root / "consumer/modules/main/aware.module.toml").read_bytes()
        raw = raw.replace(ATTENTION_DEFINITION_PROVIDER_KEY.encode(), key.encode())
        with pytest.raises(AwareModuleTomlError):
            parse_module_manifest(raw)


async def test_v3_pair_without_product_does_not_change_legacy_provider_key_grammar(
    tmp_path,
):
    from aware_code_module_manifest_contract_runtime import (
        AwareModuleTomlError,
        parse_module_manifest,
    )

    async with sources(tmp_path, _attention_repository) as (root, _, _, _, _, _):
        raw = (root / "consumer/modules/main/aware.module.toml").read_text()
        pair = (
            'profiles=[{stage="authority_derivation",profile_ref="proof.authority",'
            'profile_version="1",profile_digest="sha256:'
            + "a"
            * 64
            + '"},{stage="source_planning",profile_ref="proof.planning",'
            'profile_version="1",profile_digest="sha256:' + "b" * 64 + '"}]'
        )
        raw = re.sub(r"profiles=\[.*?\]", pair, raw)
        with pytest.raises(AwareModuleTomlError, match="provider_key must match"):
            parse_module_manifest(raw.encode())
        assert (
            parse_module_manifest(
                raw.replace(
                    ATTENTION_DEFINITION_PROVIDER_KEY, "attention_layout_definition"
                ).encode()
            ).aware
            == 3
        )
