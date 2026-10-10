"""Consumer signatures only; implementing these protocols grants no authority.

The future Code composition must retain and authenticate the original issuer
validator and its method before calling it. An arbitrary callback, structural
Protocol match or successful return is never issuer registration. This module
contains no issuer factory, validator registration, admission or execution join.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar

from .contracts import (
    ContentDigest,
    ProviderExecutionBinding,
    SemanticContractProviderDeclaration,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from .profile import SemanticContractProfileDeclaration
from .runtime import SemanticContractRuntime
from .selected_provider import AdmittedSemanticProviderRegistration


@dataclass(frozen=True, slots=True, eq=False)
class RetainedSemanticAdmissionExpectation:
    """Expected context to check, never evidence that the context was admitted.

    Code derives this request from its actual invocation and retained bodies.
    Issuers compare runtime/generation/operation identities by ``is`` against
    their original retained context, validate process/liveness themselves, and
    compare complete portable coordinates by value. No constructor validation
    here can establish provenance. No serialization or admission codec exists.

    Stage authorization is separate: revalidating the same observation does not
    authorize another selected-provider execution or consume its single-use slot.
    """

    runtime: SemanticContractRuntime
    generation_identity: object
    operation_identity: object
    process_id: int
    selected_provider_registration: AdmittedSemanticProviderRegistration
    stage: Literal["source_planning", "authority_derivation"]
    profile: SemanticContractProfileDeclaration
    provider_declaration: SemanticContractProviderDeclaration
    binding: ProviderExecutionBinding
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    manifest_coordinate: SemanticValueCoordinate
    candidate_coordinate: SemanticValueCoordinate
    registry_package_coordinate: SemanticValueCoordinate
    package_context_coordinate: SemanticValueCoordinate
    declaration_inventory_coordinate: SemanticValueCoordinate


_Admission_contra = TypeVar("_Admission_contra", contravariant=True)


class RegistryPackageAdmissionValidator(Protocol[_Admission_contra]):
    """Code-owned original issuer validator, authenticated by Code composition."""

    def validate_registry_package_admission(
        self,
        admission: _Admission_contra,
        *,
        expected: RetainedSemanticAdmissionExpectation,
    ) -> None:
        """Raise on invalid original registry admission or changed live context."""
        ...


class PackageContextAdmissionValidator(Protocol[_Admission_contra]):
    """Workspace-owned validator; concrete nominal handle remains Workspace's."""

    def validate_package_context_admission(
        self,
        admission: _Admission_contra,
        *,
        expected: RetainedSemanticAdmissionExpectation,
    ) -> None:
        """Raise unless original membership/field evidence binds exact context."""
        ...


class DeclarationInventoryAdmissionValidator(Protocol[_Admission_contra]):
    """Workspace-owned validator for original authenticated selector mappings."""

    def validate_declaration_inventory_admission(
        self,
        admission: _Admission_contra,
        *,
        expected: RetainedSemanticAdmissionExpectation,
    ) -> None:
        """Raise on missing, remapped, reconstructed or stale inventory evidence."""
        ...
