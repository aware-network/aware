"""Original retained-source resolution; no fulfillment or bootstrap authority."""

from __future__ import annotations

import copy
import inspect
from dataclasses import dataclass, fields, replace

from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    encode_code_semantic_contract_match_admission,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)

from .observed_semantic_issuers import _snapshot, _unavailable


class WorkspaceDependencyResolutionAdmission:
    """Nominal owner handle; copies and reconstruction cannot reproduce issuance."""

    __slots__ = ()

    def __new__(cls):
        raise TypeError("Workspace resolution issuer required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Workspace resolution admission is sealed")

    def __reduce__(self):
        raise TypeError("Workspace resolution admission is not portable")


@dataclass(frozen=True)
class _Resolution:
    operation: object
    inventory: object
    expected: object
    targets: tuple
    relationships: tuple


def _freeze(expected):
    identity = {"parent_identity", "epoch_identity", "demand_operation_identity"}
    return replace(
        expected,
        **{
            f.name: (
                _snapshot(expected.source_planning)
                if f.name == "source_planning"
                else copy.deepcopy(getattr(expected, f.name))
            )
            for f in fields(expected)
            if f.name not in identity
        },
    )


class _WorkspaceDependencyResolutionRuntime:
    """Privileged original-resource assembly; constructor does not grant trust."""

    def __init__(self, issuer, target_origin, catalog):
        self.issuer = issuer
        self.target_origin = target_origin
        self.resolver = CodeSemanticContractCatalogResolver(catalog)
        self.entrances = {}
        for name in ("issue", "read", "issue_source", "read_source"):
            descriptor = inspect.getattr_static(target_origin, name)
            method = getattr(target_origin, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not target_origin
                or method.__func__ is not descriptor
            ):
                _unavailable("original_target_origin_required")
            self.entrances[name] = (descriptor, method)
        self.records = {}
        self.issued_operations = []

    def _call(self, name, *args, **kwargs):
        descriptor, method = self.entrances[name]
        if inspect.getattr_static(self.target_origin, name) is not descriptor:
            _unavailable("target_origin_substituted")
        value = method(*args, **kwargs)
        if inspect.getattr_static(self.target_origin, name) is not descriptor:
            _unavailable("target_origin_substituted")
        return value

    def _inventory(self, operation, inventory, expected):
        record = self.issuer._validate_dependency_inventory(
            operation, inventory, expected=expected
        )
        catalog = self.resolver.catalog
        admission = expected.catalog_match_admission
        if (
            catalog.catalog_ref,
            catalog.catalog_generation,
            catalog.catalog_root_digest,
        ) != (
            admission.catalog_ref,
            admission.catalog_generation,
            admission.catalog_root_digest,
        ):
            _unavailable("dependency_catalog_correspondence_differs")
        # Workspace authenticates correspondence, never synthesizes owner meaning.
        planned = expected.planning_input
        if (
            planned.package != record.source.context.package
            or planned.source_identity_digest
            != record.source.context.source_identity_digest
        ):
            _unavailable("dependency_planning_source_differs")
        authored = {
            (d.dependency_kind, d.dependency_ref): d for d in record.inventory.entries
        }
        if set(authored) != {
            (d.dependency_kind, d.dependency_ref) for d in planned.dependencies
        }:
            _unavailable("dependency_planning_declarations_differ")
        for dependency in planned.dependencies:
            original = authored[(dependency.dependency_kind, dependency.dependency_ref)]
            if (
                dependency.targets != original.targets
                or dependency.target_constraints != original.target_constraints
            ):
                _unavailable("dependency_planning_targets_differ")
        return record, authored

    @staticmethod
    def _matches(target, context, roots, constraints):
        for constraint in constraints:
            kind, value = constraint.constraint_kind, constraint.constraint_value
            if kind == "semantic_provider_key":
                continue
            if kind == "package_ref":
                actual = target.package_ref == value
            elif kind == "package_kind":
                actual = target.package_kind == value
            elif kind == "package_family":
                actual = context.package_family == value
            elif kind == "semantic_root_ref":
                actual = value in roots
            else:
                # Observed module_id is not a committed catalog module_ref.
                _unavailable("source_dependency_constraint_unsupported")
            if not actual:
                return False
        return True

    def _resolve_relationships(self, operation, inventory, expected, retained=None):
        """All direct owner targets, independently of executable result demands.

        Source handles remain on the original resolution record; validating that
        record rereads those handles rather than minting replacements.
        """
        record, _ = self._inventory(operation, inventory, expected)
        context = self.issuer._contexts[inventory]
        result = []
        for declaration in expected.planning_input.dependencies:
            for candidate in declaration.targets:
                sources = {
                    id(s.membership): s
                    for s in record.targets
                    if s.context.package == candidate.package
                }
                if len(sources) != 1:
                    _unavailable("original_source_target_not_unique")
                source = next(iter(sources.values()))
                expectation = RetainedTargetExpectation(
                    expected.source_planning,
                    source.context.source_identity_digest,
                    candidate.package,
                )
                target = self.issuer.select_dependency_target_admission(
                    inventory_admission=inventory,
                    expected=expectation,
                )
                key = (
                    declaration.dependency_kind,
                    declaration.dependency_ref,
                    copy.deepcopy(candidate),
                )
                if retained is None:
                    admission = self._call(
                        "issue_source",
                        context,
                        inventory,
                        target,
                        target_source_identity_digest=expectation.target_source_identity_digest,
                        target_package=candidate.package,
                    )
                else:
                    if len(result) >= len(retained):
                        _unavailable("source_relationship_set_changed")
                    old = retained[len(result)]
                    if old[0] != key or old[1] is not target:
                        _unavailable("source_relationship_target_changed")
                    admission = old[2]
                value = self._call(
                    "read_source",
                    admission,
                    source_context=context,
                    inventory_admission=inventory,
                    target_admission=target,
                )
                if retained is not None and value != retained[len(result)][3]:
                    _unavailable("source_relationship_registration_changed")
                result.append((key, target, admission, copy.deepcopy(value)))
        if retained is not None and len(result) != len(retained):
            _unavailable("source_relationship_set_changed")
        self._inventory(operation, inventory, expected)
        return tuple(result)

    def _resolve(self, operation, inventory, expected):
        record, authored = self._inventory(operation, inventory, expected)
        context = self.issuer._contexts[inventory]
        retained = []
        for demand in expected.demand_set.demands:
            declaration = authored.get(
                (demand.authored_dependency_kind, demand.authored_dependency_ref)
            )
            if declaration is None or not set(demand.target_constraints) <= set(
                declaration.target_constraints
            ):
                _unavailable("authored_dependency_mismatch")
            # Reject unsupported constraints even if no candidate would survive.
            if any(
                c.constraint_kind
                not in {
                    "package_ref",
                    "package_kind",
                    "package_family",
                    "semantic_root_ref",
                    "semantic_provider_key",
                }
                for c in demand.target_constraints
            ):
                _unavailable("source_dependency_constraint_unsupported")
            matches = []
            for candidate in declaration.targets:
                sources = [
                    s for s in record.targets if s.context.package == candidate.package
                ]
                if not sources:
                    _unavailable("original_target_absent")
                source = sources[0]
                expectation = RetainedTargetExpectation(
                    expected.source_planning,
                    source.context.source_identity_digest,
                    candidate.package,
                )
                target = self.issuer.select_dependency_target_admission(
                    inventory_admission=inventory, expected=expectation
                )
                origin_admission = self._call(
                    "issue",
                    context,
                    inventory,
                    target,
                    target_source_identity_digest=expectation.target_source_identity_digest,
                    target_package=candidate.package,
                )
                target_fields = self._call(
                    "read",
                    origin_admission,
                    source_context=context,
                    inventory_admission=inventory,
                    target_admission=target,
                )
                if not self._matches(
                    candidate.package,
                    target_fields,
                    candidate.semantic_root_refs,
                    demand.target_constraints,
                ):
                    continue
                if not set(demand.target_intent.requested_semantic_root_refs) <= set(
                    candidate.semantic_root_refs
                ):
                    continue
                requested = CodeSemanticPackagePlanningContext.create(
                    package=candidate.package,
                    package_family=target_fields.package_family,
                    package_role=target_fields.package_role,
                    manifest_contract=target_fields.manifest_contract,
                    code_intent=demand.target_intent,
                    required_result_products=(
                        CodeSemanticRequiredResultProduct.create(
                            role=demand.required_result_role,
                            contract=demand.result_product_contract,
                        ),
                    ),
                    required_semantic_provider_keys=tuple(
                        sorted(
                            {
                                c.constraint_value
                                for c in demand.target_constraints
                                if c.constraint_kind == "semantic_provider_key"
                            }
                        )
                    ),
                )
                try:
                    _, admission = self.resolver.resolve(requested)
                except ContractViolation as error:
                    if str(error) == "semantic_contract_match_absent":
                        continue
                    raise
                wire = encode_code_semantic_contract_match_admission(
                    admission, context=requested, resolver=self.resolver
                )
                reread = self._call(
                    "read",
                    origin_admission,
                    source_context=context,
                    inventory_admission=inventory,
                    target_admission=target,
                )
                if reread != target_fields:
                    _unavailable("target_context_changed")
                matches.append(
                    (demand.demand_digest, target, origin_admission, requested, wire)
                )
            if len(matches) > 1:
                _unavailable("dependency_target_ambiguous")
            if not matches and demand.cardinality == "required":
                _unavailable("dependency_target_absent")
            retained.extend(matches)
        self._inventory(operation, inventory, expected)
        return tuple(retained)

    def issue(self, operation, inventory, expected):
        if any(value is operation for value in self.issued_operations):
            _unavailable("dependency_resolution_replay")
        if len(self.records) >= 128:
            _unavailable("dependency_resolution_capacity")
        self._inventory(operation, inventory, expected)
        frozen = _freeze(expected)
        relationships = self._resolve_relationships(operation, inventory, frozen)
        targets = self._resolve(operation, inventory, frozen)
        self._resolve_relationships(operation, inventory, frozen, relationships)
        handle = object.__new__(WorkspaceDependencyResolutionAdmission)
        self.records[handle] = _Resolution(
            operation, inventory, frozen, targets, relationships
        )
        self.issued_operations.append(operation)
        return handle

    def validate(self, handle, expected):
        if (
            type(handle) is not WorkspaceDependencyResolutionAdmission
            or handle not in self.records
        ):
            _unavailable("foreign_dependency_resolution")
        record = self.records[handle]
        self._inventory(record.operation, record.inventory, expected)
        self._resolve_relationships(
            record.operation, record.inventory, record.expected, record.relationships
        )
        current = self._resolve(record.operation, record.inventory, record.expected)
        original = record.targets
        # Match origin handles stay original; fresh selection must agree on every
        # target identity, exact context and catalog-bound match admission.
        if len(current) != len(original) or any(
            (a[0] != b[0] or a[1] is not b[1] or a[3] != b[3] or a[4] != b[4])
            for a, b in zip(current, original, strict=True)
        ):
            _unavailable("dependency_resolution_changed")
        context = self.issuer._contexts[record.inventory]
        for _, target, admission, _, _ in original:
            self._call(
                "read",
                admission,
                source_context=context,
                inventory_admission=record.inventory,
                target_admission=target,
            )
        self._resolve_relationships(
            record.operation, record.inventory, record.expected, record.relationships
        )
        self._inventory(record.operation, record.inventory, record.expected)

    def close(self):
        self.records.clear()
        self.issued_operations.clear()
