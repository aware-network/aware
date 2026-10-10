"""Shared provider dependency inputs. Values describe evidence, never issue authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticDependencyCoordinate,
    SemanticPackageCoordinate,
    _token,
    _token_tuple,
)
from .materialization_planning import (
    CodeSemanticMaterializationIntent,
    SemanticDependencyDemandSet,
    SemanticDependencyTargetConstraint,
)
from .runtime import SemanticBody


@dataclass(frozen=True, slots=True)
class SemanticDependencyTarget:
    package: SemanticPackageCoordinate
    semantic_root_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.package) is not SemanticPackageCoordinate:
            raise TypeError("dependency target package must be exact")
        self.package.__post_init__()
        _token_tuple(
            self.semantic_root_refs, "target.semantic_root_refs", nonempty=True
        )


@dataclass(frozen=True, slots=True)
class SemanticAuthoredDependency:
    dependency_kind: str
    dependency_ref: str
    targets: tuple[SemanticDependencyTarget, ...]
    target_constraints: tuple[SemanticDependencyTargetConstraint, ...] = ()

    def __post_init__(self) -> None:
        _token(self.dependency_kind, "dependency.kind")
        _token(self.dependency_ref, "dependency.ref")
        if type(self.targets) is not tuple or not self.targets:
            raise TypeError("dependency targets must be a nonempty tuple")
        for target in self.targets:
            if type(target) is not SemanticDependencyTarget:
                raise TypeError("dependency target must be exact")
            target.__post_init__()
        refs = tuple(target.package.package_ref for target in self.targets)
        if refs != tuple(sorted(set(refs))):
            raise ContractViolation("dependency targets must be unique and ordered")
        if type(self.target_constraints) is not tuple:
            raise TypeError("dependency constraints must be a tuple")
        for constraint in self.target_constraints:
            if type(constraint) is not SemanticDependencyTargetConstraint:
                raise TypeError("dependency constraint must be exact")
            constraint.__post_init__()


@dataclass(frozen=True, slots=True)
class SemanticDependencyPlanningInput:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    dependencies: tuple[SemanticAuthoredDependency, ...]

    def __post_init__(self) -> None:
        if type(self.package) is not SemanticPackageCoordinate:
            raise TypeError("planning package must be exact")
        self.package.__post_init__()
        if type(self.source_identity_digest) is not ContentDigest:
            raise TypeError("planning source digest must be exact")
        self.source_identity_digest.__post_init__()
        if type(self.dependencies) is not tuple:
            raise TypeError("planning dependencies must be a tuple")
        keys = []
        for dependency in self.dependencies:
            if type(dependency) is not SemanticAuthoredDependency:
                raise TypeError("authored dependency must be exact")
            dependency.__post_init__()
            keys.append((dependency.dependency_kind, dependency.dependency_ref))
        if keys != sorted(set(keys)):
            raise ContractViolation("authored dependencies must be unique and ordered")


class SemanticDependencySource(Protocol):
    """Host-supplied source; admission and liveness remain the host's responsibility."""

    def read_dependencies(
        self, package: SemanticPackageCoordinate
    ) -> SemanticDependencyPlanningInput: ...


@dataclass(frozen=True, slots=True)
class SemanticDependencyProduct:
    demand_digest: ContentDigest
    coordinate: SemanticDependencyCoordinate
    body: SemanticBody
    provenance_digest: ContentDigest

    def __post_init__(self) -> None:
        if type(self.coordinate) is not SemanticDependencyCoordinate:
            raise TypeError("dependency coordinate must be exact")
        if type(self.body) is not SemanticBody:
            raise TypeError("dependency body must be exact")
        self.coordinate.__post_init__()
        self.body.__post_init__()
        for value in (self.demand_digest, self.provenance_digest):
            if type(value) is not ContentDigest:
                raise TypeError("dependency digest must be exact")
            value.__post_init__()
        coordinate = self.body.coordinate
        if (
            self.coordinate.result_contract != coordinate.contract
            or self.coordinate.result_ref != coordinate.value_ref
            or self.coordinate.result_digest != coordinate.digest
        ):
            raise ContractViolation("dependency coordinate and body differ")


@dataclass(frozen=True, slots=True)
class SemanticDependencyProductInput:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    declared_dependencies: tuple[tuple[str, str], ...]
    demand_set: SemanticDependencyDemandSet
    products: tuple[SemanticDependencyProduct, ...]
    intent: CodeSemanticMaterializationIntent

    def __post_init__(self) -> None:
        if type(self.package) is not SemanticPackageCoordinate:
            raise TypeError("product input package must be exact")
        self.package.__post_init__()
        if type(self.source_identity_digest) is not ContentDigest:
            raise TypeError("product source digest must be exact")
        self.source_identity_digest.__post_init__()
        if type(self.demand_set) is not SemanticDependencyDemandSet:
            raise TypeError("dependency demand set must be exact")
        self.demand_set.__post_init__()
        if type(self.intent) is not CodeSemanticMaterializationIntent:
            raise TypeError("dependency intent must be exact")
        self.intent.__post_init__()
        if self.intent.intent_digest != self.demand_set.intent_digest:
            raise ContractViolation("dependency intent differs from demand set")
        if self.package != self.demand_set.package:
            raise ContractViolation("dependency consumer package differs")
        if type(self.declared_dependencies) is not tuple:
            raise TypeError("dependency declaration keys must be a tuple")
        for key in self.declared_dependencies:
            if type(key) is not tuple or len(key) != 2:
                raise TypeError("dependency declaration key must be exact pair")
            for value in key:
                _token(value, "dependency declaration key")
        if self.declared_dependencies != tuple(sorted(set(self.declared_dependencies))):
            raise ContractViolation("declaration keys must be unique and ordered")
        demands = {value.demand_digest: value for value in self.demand_set.demands}
        if any(
            (d.authored_dependency_kind, d.authored_dependency_ref)
            not in self.declared_dependencies
            for d in demands.values()
        ):
            raise ContractViolation("dependency demand is not declared")
        if type(self.products) is not tuple:
            raise TypeError("dependency products must be a tuple")
        seen = set()
        for product in self.products:
            if type(product) is not SemanticDependencyProduct:
                raise TypeError("dependency product must be exact")
            product.__post_init__()
            if product.demand_digest in seen or product.demand_digest not in demands:
                raise ContractViolation(
                    "dependency product demand is duplicate or absent"
                )
            seen.add(product.demand_digest)
            demand = demands[product.demand_digest]
            if (
                product.body.coordinate.role != demand.required_result_role
                or product.coordinate.result_contract != demand.result_product_contract
            ):
                raise ContractViolation(
                    "dependency product contract differs from demand"
                )
        if any(
            d.cardinality == "required" and key not in seen
            for key, d in demands.items()
        ):
            raise ContractViolation("required dependency product is absent")


__all__ = [
    "SemanticAuthoredDependency",
    "SemanticDependencyPlanningInput",
    "SemanticDependencyProduct",
    "SemanticDependencyProductInput",
    "SemanticDependencySource",
    "SemanticDependencyTarget",
]
