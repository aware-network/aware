"""Original Code policy/demand resources, isolated owner; no application trust."""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_retained_registry_policy_runtime.stage_policy_binding import (
    validate_stage_policy_occurrence,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from test_calculation import _body, fixture
from test_direct_host import Owner
from test_stage_runtime_retention import case as retained_case  # noqa: F401


class StageOwner(Owner):
    close_registration_on_acquire = None

    def acquire_command_publication_guard(self, lifetime, *, expected):
        guard = super().acquire_command_publication_guard(lifetime, expected=expected)
        if self.close_registration_on_acquire is not None:
            from aware_code_semantic_contract_runtime import selected_provider

            runtime, registration = self.close_registration_on_acquire
            selected_provider.close_selected_provider_registration(
                runtime, registration
            )
        return guard


@pytest.fixture
def joined(retained_case):  # noqa: F811 - imported pytest fixture
    expected, retention, _, live = retained_case
    scope, catalog = fixture()
    text = (
        scope.modules[0]
        .manifest.body.decode()
        .replace('provider_key = "demo"', 'provider_key = "stage_retention_test"')
    )
    by_ref = {entry[1].profile_ref: entry[1] for entry in retention.entries}
    for entry in catalog.entries:
        text = text.replace(
            entry.profile_declaration.digest.to_wire(),
            by_ref[entry.profile_declaration.profile_ref].digest.to_wire(),
        )
    module = replace(
        scope.modules[0], manifest=_body("demo/aware.module.toml", text.encode())
    )
    scope = replace(scope, modules=(module,))
    owner = StageOwner(scope)
    objects = {
        "composition_factory": owner,
        "lifetime_runtime": owner,
        "scope_adapter": owner,
        "policy_producer": calculate_registry_policy,
    }
    owner.expected = replace(
        expected,
        resources=tuple(
            replace(b, resource=objects[b.role]) if b.role in objects else b
            for b in expected.resources
        ),
    )
    bootstrap = hosts._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=owner.expected
    )
    host = hosts.register_direct_workspace_origin(bootstrap, owner.lifetime)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    source = scope.packages[0].source_identity_digest
    try:
        yield owner, host, policy, source, live
    finally:
        hosts.close_direct_validation_host(host)


def test_original_host_policy_resolves_stage_declaration(joined):
    _, host, policy, source, _ = joined
    assert validate_stage_policy_occurrence(host, policy, source) is None
    assert validate_stage_policy_occurrence(host, policy, source) is None


def test_source_digest_without_original_grant_refuses(joined):
    _, host, policy, _, _ = joined
    with pytest.raises(ContractViolation, match="unique admitted stage occurrence"):
        validate_stage_policy_occurrence(
            host, policy, ContentDigest.of_bytes(b"foreign")
        )


def test_portable_policy_is_not_original_admission(joined):
    _, host, policy, source, _ = joined
    portable = hosts.validate_admitted_registry_policy(host, policy)
    with pytest.raises(TypeError, match="exact policy"):
        validate_stage_policy_occurrence(host, portable, source)


def test_foreign_nominal_policy_rejects(joined):
    from test_direct_host import registered

    _, host, _, source, _ = joined
    owner, other = registered()
    try:
        foreign = hosts.produce_registry_policy(other, owner.snapshot)
        with pytest.raises(ContractViolation, match="foreign policy"):
            validate_stage_policy_occurrence(host, foreign, source)
    finally:
        hosts.close_direct_validation_host(other)


def test_source_only_host_cannot_validate_authority_occurrence(joined):
    from test_direct_host import registered

    _, _, _, source, _ = joined
    owner, other = registered()
    try:
        policy = hosts.produce_registry_policy(other, owner.snapshot)
        with pytest.raises(ContractViolation, match="no retained authority stage"):
            validate_stage_policy_occurrence(other, policy, source)
    finally:
        hosts.close_direct_validation_host(other)


def test_changed_projection_from_original_reader_refuses(joined):
    owner, host, policy, source, _ = joined
    original = owner.projection
    # Owner scope validator reads current projection, so substitution changes
    # the projection digest and the original nominal policy must refuse.
    owner.projection = replace(original, packages=())
    try:
        with pytest.raises(ContractViolation):
            validate_stage_policy_occurrence(host, policy, source)
    finally:
        owner.projection = original


def test_registration_closure_at_final_guard_rejects(joined):
    owner, host, policy, source, _ = joined
    stage = owner.expected.stage_runtime_bindings[1]
    owner.close_registration_on_acquire = (stage.runtime, stage.registration)
    with pytest.raises(ContractViolation, match="closed"):
        validate_stage_policy_occurrence(host, policy, source)
    assert owner.guard is None
