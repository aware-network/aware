"""Neutral target validation seam; values and Protocol conformance grant no authority."""

from dataclasses import dataclass
from typing import Protocol

from .contracts import ContentDigest, SemanticContractRef, SemanticPackageCoordinate
from .retained_admission_interfaces import RetainedSemanticAdmissionExpectation


@dataclass(frozen=True, slots=True)
class RetainedTargetExpectation:
    """Code comparison input to the original Workspace target validator.

    Workspace must validate original inventory/source association and target
    membership/currentness, including semantic name/version and manifest digest.
    These values cannot create target, inventory or demand admissions.
    """

    source_planning: RetainedSemanticAdmissionExpectation
    target_source_identity_digest: ContentDigest
    target_package: SemanticPackageCoordinate


@dataclass(frozen=True, slots=True)
class TargetContextFields:
    """Detached Code-derived context fields, usable only with original validation."""

    package_family: str
    package_role: str
    manifest_contract: SemanticContractRef


@dataclass(frozen=True, slots=True)
class SourceTargetRegistrationFields:
    """Detached registration meaning, never result capability or manifest schema."""

    package_family: str
    package_role: str
    semantic_provider_key: str
    semantic_package_kind: str
    manifest_contract_kind: str
    manifest_filename: str


class DependencyTargetAdmissionValidator(Protocol):
    def validate_dependency_target_admission(
        self,
        admission: object,
        *,
        inventory_admission: object,
        expected: RetainedTargetExpectation,
    ) -> None:
        """Reject foreign targets, changed membership or wrong original inventory.

        Code authenticates this original issuer and retains its callable before
        invoking it. Workspace validates the original Code source context through
        its retained validator; a matching expectation is never admission.
        Demand identity and capability matching remain with resolution admission.
        """
        ...
