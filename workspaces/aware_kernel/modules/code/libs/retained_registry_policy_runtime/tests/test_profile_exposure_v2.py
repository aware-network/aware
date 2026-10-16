"""Original selected imports bind exact v2 exposure, never a key alias."""

from dataclasses import replace

import pytest
import test_single_product_declaration_host as host_fixtures
from aware_code_module_manifest_contract_runtime import parse_module_manifest
from aware_code_module_manifest_contract_runtime.profile_models import (
    CodeSemanticContractProfileManifestSpecV2,
)
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime.profile_membership import (
    resolve_profile_memberships,
)
from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
    derive_selected_participant_view,
    validate_selected_participant_view,
)
from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipant,
)
from test_calculation import _binding
from test_selected_participant_calculation import _body


def _exposure_closure(entry):
    closure = host_fixtures._product_closure(entry)
    body = (
        '''aware_semantic_contract_profile = 2
[profile]
key = "custom.profile"
package_key = "independent.package"
[[providers]]
module_id = "demo"
package_id = "provider"
registration_key = "demo"
provider_key = "'''
        + entry.semantic_provider_key
        + """"
exposure = "graph_product"
"""
    ).encode()
    return _with_profile(closure, body)


def _with_profile(closure, body):
    old = closure.local_profiles[0].manifest
    retained = _body(old.relative_path, body)
    return replace(
        closure,
        local_profiles=(replace(closure.local_profiles[0], manifest=retained),),
        profile_associations=(
            replace(closure.profile_associations[0], manifest=retained),
        ),
    )


def _view(closure):
    return derive_selected_participant_view(
        closure, scope_key="consumer", module_id="demo", package_id="home"
    )


def test_exact_hyphenated_product_key_entitles_only_declared_registration():
    closure = _exposure_closure(
        _binding(
            provider_key="attention-layout-definition", profile_ref="owner.product"
        )
    )
    view = _view(closure)
    assert CodeSelectedParticipant("target", "demo", "provider") in view.participants
    assert len(view.profiles) == 1
    assert all(row.module_id != "unrelated" for row in view.participants)
    assert (
        view.profiles[0].manifest_content_digest
        == closure.profile_associations[0].manifest.content_digest
    )
    validate_selected_participant_view(closure, view)


@pytest.mark.parametrize(
    "before,after",
    [
        (b'package_id = "provider"', b'package_id = "home"'),
        (b'registration_key = "demo"', b'registration_key = "other"'),
        (b'module_id = "demo"', b'module_id = "foreign"'),
        (b'exposure = "graph_product"', b'exposure = "stage_pair"'),
        (
            b'exposure = "graph_product"',
            b'exposure = "graph_product"\nstatus="inactive"',
        ),
        (b'provider_key = "fixture_product"', b'provider_key = "aware_attention"'),
    ],
)
def test_selected_import_refuses_wrong_exposure_and_legacy_alias(before, after):
    closure = _exposure_closure(
        _binding(provider_key="fixture_product", profile_ref="owner.product")
    )
    changed = closure.local_profiles[0].manifest.body.replace(before, after)
    assert changed != closure.local_profiles[0].manifest.body
    with pytest.raises(ContractViolation):
        _view(_with_profile(closure, changed))


def test_same_package_different_registration_is_not_exposure_entitlement():
    closure = _exposure_closure(
        _binding(provider_key="fixture_product", profile_ref="owner.product")
    )
    consumer, target = closure.scopes
    module = target.projection.modules[0]
    raw = module.manifest.body.decode()
    start = raw.index("[[packages.semantic_contract.registrations]]")
    end = raw.index("\n[[packages]]", start)
    sibling = raw[start:end].replace('key = "demo"', 'key = "sibling"')
    raw = raw[:end] + "\n" + sibling + raw[end:]
    assert (
        len(parse_module_manifest(raw.encode()).package_declarations[0].registrations)
        == 2
    )
    module = replace(
        module, manifest=_body(module.manifest.relative_path, raw.encode())
    )
    target = replace(target, projection=replace(target.projection, modules=(module,)))
    closure = replace(closure, scopes=(consumer, target))
    body = closure.local_profiles[0].manifest.body.replace(
        b'registration_key = "demo"', b'registration_key = "sibling"'
    )
    with pytest.raises(ContractViolation, match="not entitled"):
        _view(_with_profile(closure, body))


def test_direct_provider_restriction_and_profile_body_are_not_reusable_authority():
    closure = _exposure_closure(
        _binding(
            provider_key="attention-layout-definition", profile_ref="owner.product"
        )
    )
    first = _view(closure)
    edge = closure.edges[0]
    with pytest.raises(ContractViolation):
        _view(
            replace(
                closure,
                edges=(
                    replace(
                        edge,
                        semantic_contract_provider_keys=replace(
                            edge.semantic_contract_provider_keys,
                            value=("aware_attention",),
                        ),
                    ),
                ),
            )
        )
    changed = _with_profile(
        closure,
        b"# different original body\n" + closure.local_profiles[0].manifest.body,
    )
    assert _view(changed).digest != first.digest
    with pytest.raises(ContractViolation):
        validate_selected_participant_view(changed, first)


def test_broad_profile_membership_binds_the_same_exact_product_registration():
    # Broad traversal retains its existing all-module version law. Remove only
    # the fixture's explicitly authored unrelated-v1 member from this separate
    # all-v3 fixture; the exact-selection proof above retains it.
    closure = _exposure_closure(
        _binding(
            provider_key="attention-layout-definition", profile_ref="owner.product"
        )
    )
    consumer, target = closure.scopes
    consumer = replace(
        consumer,
        projection=replace(
            consumer.projection,
            modules=consumer.projection.modules[:1],
            packages=consumer.projection.packages[:-1],
        ),
    )
    closure = replace(closure, scopes=(consumer, target))
    (selection,) = resolve_profile_memberships(closure)
    assert type(selection.meaning) is CodeSemanticContractProfileManifestSpecV2
    assert len(selection.members) == 1
    assert selection.members[0].member.provider_key == "attention-layout-definition"
    assert selection.members[0].package.package_id == "provider"
    assert selection.members[0].member.exposure == "graph_product"


def test_original_live_host_consumes_v2_profile_without_new_admission(monkeypatch):
    original = host_fixtures._product_closure

    # Avoid recursion while constructing the adapted fixture's profile body.
    def adapt(entry, *, declared_digest=None):
        value = original(entry, declared_digest=declared_digest)
        body = (
            '''aware_semantic_contract_profile=2
[profile]
key="custom.profile"
package_key="independent.package"
[[providers]]
module_id="demo"
package_id="provider"
registration_key="demo"
provider_key="'''
            + entry.semantic_provider_key
            + """"
exposure="graph_product"
"""
        ).encode()
        return _with_profile(value, body)

    monkeypatch.setattr(host_fixtures, "_product_closure", adapt)
    with host_fixtures.product_host(monkeypatch) as (
        owner,
        host,
        _registration,
        provider,
        _,
    ):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        intent, product = derive_selected_root_intent(host, policy)
        assert intent.requested_terminal_output_roles == ("result",)
        assert product.contract == provider.declaration.result_role.contract
        owner.selected_live = False
        with pytest.raises(ContractViolation):
            derive_selected_root_intent(host, policy)
