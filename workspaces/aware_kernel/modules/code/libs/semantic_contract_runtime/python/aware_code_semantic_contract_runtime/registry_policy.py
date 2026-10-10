"""Exact local registry-policy evaluation, not policy or issuer authentication.

A host must independently authenticate this policy and bind it to original
Workspace evidence. Constructing a matching policy cannot authorize a package.
"""

from dataclasses import dataclass

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .retained_input_projections import (
    MAX_PROJECTION_BODY_BYTES,
    MAX_PROJECTION_ITEMS,
    _strings,
    _text,
)


def _digest(value: ContentDigest) -> None:
    if type(value) is not ContentDigest:
        raise TypeError("exact Code digest required")
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class RegistryPolicyGrant:
    source_identity_digest: ContentDigest
    registration_declaration_digest: ContentDigest
    declared_package_kind: str
    semantic_package_kind: str
    namespace: str
    owned_roots: tuple[str, ...]

    def __post_init__(self) -> None:
        _digest(self.source_identity_digest)
        _digest(self.registration_declaration_digest)
        for value in (
            self.declared_package_kind,
            self.semantic_package_kind,
            self.namespace,
        ):
            _text(value)
        _strings(self.owned_roots)

    def to_wire(self) -> dict[str, object]:
        return {
            "source_identity_digest": self.source_identity_digest.to_wire(),
            "registration_declaration_digest": self.registration_declaration_digest.to_wire(),
            "declared_package_kind": self.declared_package_kind,
            "semantic_package_kind": self.semantic_package_kind,
            "namespace": self.namespace,
            "owned_roots": list(self.owned_roots),
        }


def _key(grant: RegistryPolicyGrant) -> tuple[str, str]:
    return (
        grant.source_identity_digest.value,
        grant.registration_declaration_digest.value,
    )


@dataclass(frozen=True, slots=True)
class RegistryPolicy:
    """Host-proposed exact grant set for one declaration scope; input only."""

    declaration_scope_digest: ContentDigest
    grants: tuple[RegistryPolicyGrant, ...]

    def __post_init__(self) -> None:
        _digest(self.declaration_scope_digest)
        if type(self.grants) is not tuple or len(self.grants) > MAX_PROJECTION_ITEMS:
            raise ContractViolation("policy grant tuple type or capacity differs")
        keys = []
        namespaces = set()
        roots = set()
        for grant in self.grants:
            if type(grant) is not RegistryPolicyGrant:
                raise TypeError("exact policy grant required")
            grant.__post_init__()
            keys.append(_key(grant))
            if grant.namespace in namespaces or roots.intersection(grant.owned_roots):
                raise ContractViolation("conflicting exact assignment in policy scope")
            namespaces.add(grant.namespace)
            roots.update(grant.owned_roots)
        if keys != sorted(set(keys)):
            raise ContractViolation("policy grants must be ordered and unique")
        body = canonical_json_bytes(
            {
                "scope": self.declaration_scope_digest.to_wire(),
                "grants": [grant.to_wire() for grant in self.grants],
            }
        )
        if len(body) > MAX_PROJECTION_BODY_BYTES:
            raise ContractViolation("policy exceeds canonical byte bound")


def validate_registry_policy_candidate(
    policy: RegistryPolicy,
    *,
    declaration_scope_digest: ContentDigest,
    source_identity_digest: ContentDigest,
    registration_declaration_digest: ContentDigest,
    declared_package_kind: str,
    semantic_package_kind: str,
    namespace: str,
    owned_roots: tuple[str, ...],
) -> None:
    """Compare against exact grant data; success is never a nominal admission."""
    if type(policy) is not RegistryPolicy:
        raise TypeError("exact registry policy required")
    policy.__post_init__()
    _digest(declaration_scope_digest)
    if declaration_scope_digest != policy.declaration_scope_digest:
        raise ContractViolation("policy declaration scope differs")
    candidate = RegistryPolicyGrant(
        source_identity_digest,
        registration_declaration_digest,
        declared_package_kind,
        semantic_package_kind,
        namespace,
        owned_roots,
    )
    matches = [grant for grant in policy.grants if _key(grant) == _key(candidate)]
    if len(matches) != 1 or matches[0] != candidate:
        raise ContractViolation("exact registry assignment grant unavailable")
