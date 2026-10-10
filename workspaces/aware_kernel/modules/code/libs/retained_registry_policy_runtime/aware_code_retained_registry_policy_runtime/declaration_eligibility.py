"""V3 declaration eligibility with one broad or exact selected entrance.

The broad call keeps the all-v3 qualified traversal. The selected call follows
the complete participant view while retaining the full declaration closure.
Workspace authenticates the view and selected source; neither portable result
can authorize provider execution by itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipantViewV1,
)

from .calculation import _plain
from .qualified_calculation import _qualified_occurrences
from .selected_participant_calculation import selected_qualified_occurrences


@dataclass(frozen=True, slots=True)
class DeclaredPackageEligibility:
    scope_key: str
    module_id: str
    package_id: str
    registration_declaration_digest: ContentDigest
    provider_key: str
    declared_package_kind: str
    semantic_package_kind: str
    namespace: str
    owned_roots: tuple[str, ...]

    @property
    def occurrence_key(self) -> tuple[str, str, str]:
        return self.scope_key, self.module_id, self.package_id


@dataclass(frozen=True, slots=True)
class DeclarationEligibility:
    """Portable, input-only result; no source identity or policy admission."""

    closure_digest: ContentDigest
    packages: tuple[DeclaredPackageEligibility, ...]

    def __post_init__(self) -> None:
        if type(self.closure_digest) is not ContentDigest:
            raise ContractViolation("exact declaration closure digest required")
        self.closure_digest.__post_init__()
        if type(self.packages) is not tuple:
            raise ContractViolation("exact declaration eligibility tuple required")
        keys = []
        namespaces = set()
        roots = set()
        for row in self.packages:
            if type(row) is not DeclaredPackageEligibility:
                raise ContractViolation("exact declaration eligibility row required")
            keys.append(row.occurrence_key)
            if row.namespace in namespaces or roots.intersection(row.owned_roots):
                raise ContractViolation("conflicting declaration assignment")
            namespaces.add(row.namespace)
            roots.update(row.owned_roots)
        if keys != sorted(set(keys), key=lambda key: tuple(part.encode() for part in key)):
            raise ContractViolation("declaration eligibility unordered or duplicate")


def calculate_declaration_eligibility(
    closure: CodeRetainedDependencyScopeClosureV3,
    *,
    selected_view: CodeSelectedParticipantViewV1 | None = None,
) -> DeclarationEligibility:
    """Apply the registered declaration policy without source grants.

    An exact view narrows participation while the original closure stays
    complete. Without a view the existing all-v3 broad-selector law applies.
    The view is portable meaning; only original Workspace validation and a
    selected-source binding can later support a host-issued grant.
    """
    if type(closure) is not CodeRetainedDependencyScopeClosureV3:
        raise TypeError("exact declaration-only closure required")
    if selected_view is not None:
        return _calculate_selected_declaration_eligibility(closure, selected_view)
    rows = []
    for key, package, occurrence, declaration in _qualified_occurrences(closure):
        meaning = _plain(declaration)
        rows.append(
            DeclaredPackageEligibility(
                key[0], key[1], key[2],
                ContentDigest.of_bytes(canonical_json_bytes(meaning)),
                meaning["semantic_contract"]["provider_key"],
                package.package_kind,
                meaning["semantic_package_kind"],
                occurrence.namespace.value,
                occurrence.owned_roots.value,
            )
        )
    rows.sort(key=lambda row: tuple(part.encode() for part in row.occurrence_key))
    return DeclarationEligibility(closure.closure_digest, tuple(rows))


def _calculate_selected_declaration_eligibility(
    closure: CodeRetainedDependencyScopeClosureV3,
    view: CodeSelectedParticipantViewV1,
) -> DeclarationEligibility:
    """Apply the same package law only to authenticated selected participants."""
    rows = []
    for key, package, occurrence, declaration in selected_qualified_occurrences(
        closure, view
    ):
        meaning = _plain(declaration)
        rows.append(DeclaredPackageEligibility(
            key[0], key[1], key[2],
            ContentDigest.of_bytes(canonical_json_bytes(meaning)),
            meaning["semantic_contract"]["provider_key"],
            package.package_kind,
            meaning["semantic_package_kind"],
            occurrence.namespace.value,
            occurrence.owned_roots.value,
        ))
    rows.sort(key=lambda row: tuple(part.encode() for part in row.occurrence_key))
    return DeclarationEligibility(closure.closure_digest, tuple(rows))


__all__ = [
    "DeclaredPackageEligibility",
    "DeclarationEligibility",
    "calculate_declaration_eligibility",
]
