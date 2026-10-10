"""Code-owned dependency admission signatures, never issuer implementations.

Expectations are freely constructible comparison values, not authority. Fixed
composition must authenticate each original validator instance and retain its
method before either owner calls it. Structural Protocol conformance, a decoded
body, or a successful no-op callback cannot establish an admission origin.

This module neither imports Workspace nor issues a demand, resolution, fulfillment,
provider execution admission, authority completion or catalog transfer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from .contracts import SemanticValueCoordinate
from .dependency_inputs import (
    SemanticDependencyPlanningInput,
    SemanticDependencyProductInput,
)
from .materialization_catalog import (
    CodeSemanticContractMatch,
    CodeSemanticContractMatchAdmission,
    CodeSemanticPackagePlanningContext,
)
from .materialization_planning import SemanticDependencyDemandSet
from .retained_admission_interfaces import RetainedSemanticAdmissionExpectation


@dataclass(frozen=True, slots=True, eq=False)
class RetainedDependencyResolutionExpectation:
    """Comparison context derived from an original returned Code demand operation.

    Identity fields compare by ``is``; source-planning context supplies the exact
    Code runtime, source operation, process, registration and retained coordinates.
    It must still name source_planning, never a not-yet-issued authority stage.
    The demand identity is a separately retained original Code operation handle.

    Existing codecs bind planning meaning to its full coordinate and demand meaning
    to the exact context/catalog match. They prove portable correspondence only.
    Construction, copying and decoding cannot prove any of these identities live.
    """

    parent_identity: object
    epoch_identity: object
    demand_operation_identity: object
    source_planning: RetainedSemanticAdmissionExpectation
    planning_input_coordinate: SemanticValueCoordinate
    planning_input: SemanticDependencyPlanningInput
    planning_context: CodeSemanticPackagePlanningContext
    catalog_match: CodeSemanticContractMatch
    catalog_match_admission: CodeSemanticContractMatchAdmission
    demand_set: SemanticDependencyDemandSet


@dataclass(frozen=True, slots=True, eq=False)
class RetainedDependencyFulfillmentExpectation:
    """The exact product projection to validate against original resolution.

    The product coordinate and value use the existing dependency-product codec.
    No second target-resolution, graph, head or fulfillment model belongs in Code.
    Original owner evidence authenticates the selected targets and retained bodies.
    An empty product value requires the same original admission join.
    """

    resolution: RetainedDependencyResolutionExpectation
    dependency_products_coordinate: SemanticValueCoordinate
    dependency_products: SemanticDependencyProductInput


_Demand_contra = TypeVar("_Demand_contra", contravariant=True)
_Resolution_contra = TypeVar("_Resolution_contra", contravariant=True)
_Fulfillment_contra = TypeVar("_Fulfillment_contra", contravariant=True)


class RetainedDependencyOperationValidator(Protocol[_Demand_contra]):
    """Code's original demand validator, authenticated by fixed composition."""

    def validate_retained_dependency_operation(
        self,
        operation: _Demand_contra,
        *,
        expected: RetainedDependencyResolutionExpectation,
    ) -> None:
        """Reject foreign/reconstructed demand evidence or changed source/lifetime.

        The owner issuer calls this original Code entrance before issuing its
        admissions; it must not promote the freely constructible expectation.
        Revalidation neither executes a planner nor consumes a new execution slot.
        """
        ...


class DependencyResolutionAdmissionValidator(Protocol[_Resolution_contra]):
    """Owner's original membership/target-resolution validator, consumed by Code."""

    def validate_dependency_resolution_admission(
        self,
        admission: _Resolution_contra,
        *,
        expected: RetainedDependencyResolutionExpectation,
    ) -> None:
        """Require original resolution of this exact demand under live membership.

        Reject foreign handles, missing/extra/substituted demands or targets,
        changed source/currentness, expired lifetime and reconstructed evidence.
        Target resolution remains owner implementation behind this interface.
        """
        ...


class DependencyFulfillmentAdmissionValidator(
    Protocol[_Resolution_contra, _Fulfillment_contra]
):
    """Owner's original fulfillment validator over the same resolution handle."""

    def validate_dependency_fulfillment_admission(
        self,
        admission: _Fulfillment_contra,
        *,
        resolution_admission: _Resolution_contra,
        expected: RetainedDependencyFulfillmentExpectation,
    ) -> None:
        """Bind exact products to original resolution, retained bytes and liveness.

        Validate original observations/head evidence as owned by the issuer;
        Code does not interpret that owner's graph, revision or storage models.
        No portable provenance digest or empty product list substitutes for this
        check. Repeated validation grants no authority-stage execution admission.
        """
        ...
