from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import ContentDigest, ContractViolation
from aware_code_semantic_contract_runtime.registry_policy import (
    RegistryPolicy,
    RegistryPolicyGrant,
    validate_registry_policy_candidate,
)

SCOPE = ContentDigest.of_bytes(b"declaring scope")
SOURCE = ContentDigest.of_bytes(b"observed package source")
REGISTRATION = ContentDigest.of_bytes(b"retained selected registration declaration")
GRANT = RegistryPolicyGrant(
    SOURCE,
    REGISTRATION,
    "environment",
    "environment_config_package",
    "home",
    ("home:a", "home:b"),
)


def arguments(grant=GRANT):
    return {
        "declaration_scope_digest": SCOPE,
        "source_identity_digest": grant.source_identity_digest,
        "registration_declaration_digest": grant.registration_declaration_digest,
        "declared_package_kind": grant.declared_package_kind,
        "semantic_package_kind": grant.semantic_package_kind,
        "namespace": grant.namespace,
        "owned_roots": grant.owned_roots,
    }



def test_explicit_alias_matches_only_exact_grant():
    policy = RegistryPolicy(SCOPE, (GRANT,))
    assert validate_registry_policy_candidate(policy, **arguments()) is None
    # Repeat is a data check, never execution or admission consumption.
    assert validate_registry_policy_candidate(policy, **arguments()) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("declaration_scope_digest", ContentDigest.of_bytes(b"foreign scope")),
        ("source_identity_digest", ContentDigest.of_bytes(b"changed observation")),
        (
            "registration_declaration_digest",
            ContentDigest.of_bytes(b"other registration"),
        ),
        ("declared_package_kind", "other"),
        ("semantic_package_kind", "other"),
        ("namespace", "home.child"),
        ("owned_roots", ("home:a",)),
        ("owned_roots", ("home:a", "home:b", "home:c")),
    ],
)
def test_policy_substitution_rejects(field, value):
    args = arguments()
    args[field] = value
    with pytest.raises(ContractViolation):
        validate_registry_policy_candidate(RegistryPolicy(SCOPE, (GRANT,)), **args)


def test_no_implicit_grants_even_for_identity_kind():
    same = replace(GRANT, declared_package_kind=GRANT.semantic_package_kind)
    with pytest.raises(ContractViolation):
        validate_registry_policy_candidate(RegistryPolicy(SCOPE, ()), **arguments(same))


@pytest.mark.parametrize(
    "other",
    [
        GRANT,
        replace(GRANT, source_identity_digest=ContentDigest.of_bytes(b"other")),
        replace(
            GRANT,
            source_identity_digest=ContentDigest.of_bytes(b"other"),
            namespace="other",
        ),
    ],
)
def test_duplicate_or_conflicting_grants_reject(other):
    with pytest.raises(ContractViolation):
        RegistryPolicy(SCOPE, (GRANT, other))


def test_explicit_empty_roots_and_opaque_namespace():
    grant = replace(GRANT, owned_roots=())
    validate_registry_policy_candidate(
        RegistryPolicy(SCOPE, (grant,)), **arguments(grant)
    )
    with pytest.raises(ContractViolation):
        validate_registry_policy_candidate(
            RegistryPolicy(SCOPE, (grant,)), **arguments()
        )


def test_mutated_grant_revalidated():
    grant = replace(GRANT)
    policy = RegistryPolicy(SCOPE, (grant,))
    object.__setattr__(grant, "owned_roots", ["home:a"])
    with pytest.raises(ContractViolation):
        validate_registry_policy_candidate(policy, **arguments())
