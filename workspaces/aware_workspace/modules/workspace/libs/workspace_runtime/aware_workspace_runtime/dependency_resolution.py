"""Original retained-source resolution; no fulfillment or bootstrap authority."""

from __future__ import annotations

import copy
import inspect
from dataclasses import dataclass, fields, replace
from types import FunctionType
from weakref import ref

from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedProductPlanningExpectation,
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


def _source_snapshot(source):
    if type(source) is not RetainedProductPlanningExpectation:
        return _snapshot(source)
    identities = {"runtime", "epoch_identity", "operation_identity", "selected_provider_registration"}
    source_input = replace(source.source_input, **{
        field.name: copy.deepcopy(getattr(source.source_input, field.name))
        for field in fields(source.source_input)
        if field.name not in {"source_identity", "operation_identity"}
    })
    return replace(source, **{
        field.name: source_input if field.name == "source_input" else copy.deepcopy(getattr(source, field.name))
        for field in fields(source) if field.name not in identities
    })


def _freeze(expected):
    identity = {"parent_identity", "epoch_identity", "demand_operation_identity"}
    return replace(
        expected,
        **{
            f.name: (
                _source_snapshot(expected.source_planning)
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
        descriptor = inspect.getattr_static(issuer, "_dependency_inventory_checkpoint", None)
        self._checkpoint_factory = None
        if descriptor is not None:
            if type(descriptor) is not FunctionType:
                _unavailable("original_inventory_checkpoint_required")
            cells = descriptor.__closure__
            self._checkpoint_factory = (
                descriptor, descriptor.__code__, descriptor.__defaults__,
                descriptor.__kwdefaults__, tuple((descriptor.__kwdefaults__ or {}).items()),
                cells, tuple(cell.cell_contents for cell in cells or ()),
            )

    def _check_checkpoint_factory(self):
        retained = self._checkpoint_factory
        if retained is None:
            return
        descriptor, code, defaults, keywords, items, cells, contents = retained
        if (inspect.getattr_static(self.issuer, "_dependency_inventory_checkpoint", None) is not descriptor
            or descriptor.__code__ is not code or descriptor.__defaults__ is not defaults
            or descriptor.__kwdefaults__ is not keywords
            or (len(keywords or {}) != len(items) or any(key is not original_key or value is not original_value for (key, value), (original_key, original_value) in zip((keywords or {}).items(), items, strict=True))) or descriptor.__closure__ is not cells
            or any(cell.cell_contents is not value
                   for cell, value in zip(cells or (), contents, strict=True))):
            _unavailable("original_inventory_checkpoint_changed")

    def _inventory_checkpoint(self, operation, inventory, expected, *, _verify):
        _verify(self)
        retained = self._checkpoint_factory
        if retained is None:
            return None
        descriptor, code, defaults, _, items, cells, contents = retained
        frozen = FunctionType(code, descriptor.__globals__, argdefs=defaults,
            closure=None if cells is None else tuple(type(cell)(value)
                for cell, value in zip(cells, contents, strict=True)))
        frozen.__kwdefaults__ = dict(items) or None
        scope = frozen(self.issuer, operation, inventory, expected)
        _verify(self)
        return scope

    def _call(self, name, *args, **kwargs):
        descriptor, method = self.entrances[name]
        if inspect.getattr_static(self.target_origin, name) is not descriptor:
            _unavailable("target_origin_substituted")
        value = method(*args, **kwargs)
        if inspect.getattr_static(self.target_origin, name) is not descriptor:
            _unavailable("target_origin_substituted")
        return value

    def _inventory(self, operation, inventory, expected):
        raise NotImplementedError("definition-time original inventory dispatcher required")

    def _inventory_impl(self, operation, inventory, expected, *, _catalog_read):
        record = self.issuer._validate_dependency_inventory(
            operation, inventory, expected=expected
        )
        coordinates = _catalog_read(self)
        admission = expected.catalog_match_admission
        if coordinates != (
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

    def _resolve(self, operation, inventory, expected, *, original_targets=()):
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
                originals = tuple(
                    row[2] for row in original_targets
                    if row[0] == demand.demand_digest and row[1] is target
                )
                if len(originals) > 1:
                    _unavailable("dependency_original_target_ambiguous")
                # Validation retains the original owner admission. Its read
                # still derives/checks current fields on both sides of matching;
                # there is no cached context and no new owner issuance to discard.
                origin_admission = originals[0] if originals else self._call(
                    "issue", context, inventory, target,
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
        raise NotImplementedError("definition-time original dispatcher required")

    def validate(self, handle, expected):
        raise NotImplementedError("definition-time original dispatcher required")

    def _issue(self, operation, inventory, expected):
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

    def _validate(self, handle, expected):
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
        original = record.targets
        current = self._resolve(record.operation, record.inventory, record.expected,
                                original_targets=original)
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


def _bind_checkpoint_runtime(kind):
    """Keep constructor evidence independent of mutable runtime records."""
    namespace = type.__getattribute__(kind, "__dict__")
    dictionary = namespace["__dict__"]
    native_get = dict.get
    function_kind, weak = FunctionType, ref
    catalog_kind = CodeSemanticContractCatalogResolver
    catalog_namespace = type.__getattribute__(catalog_kind, "__dict__")
    catalog_dictionary = catalog_namespace["__dict__"]
    catalog_reader = catalog_namespace["read_catalog_coordinate"]
    reader_code, reader_defaults, reader_keywords, reader_cells = (
        catalog_reader.__code__, catalog_reader.__defaults__,
        catalog_reader.__kwdefaults__, catalog_reader.__closure__)
    reader_items = tuple((reader_keywords or {}).items())
    reader_contents = tuple(cell.cell_contents for cell in reader_cells or ())
    reader_frozen = function_kind(reader_code, catalog_reader.__globals__, argdefs=reader_defaults,
        closure=None if reader_cells is None else tuple(type(cell)(value)
            for cell, value in zip(reader_cells, reader_contents, strict=True)))
    reader_frozen.__kwdefaults__ = dict(reader_items) or None
    names = ("__init__", "_check_checkpoint_factory", "_inventory_checkpoint", "_inventory_impl", "_issue", "_validate", "close")
    origins = tuple((name, namespace[name], namespace[name].__code__,
        namespace[name].__defaults__, namespace[name].__kwdefaults__,
        tuple((namespace[name].__kwdefaults__ or {}).items()), namespace[name].__closure__,
        tuple(cell.cell_contents for cell in namespace[name].__closure__ or ())) for name in names)
    frozen = {}
    for name, function, code, defaults, _, items, cells, contents in origins:
        clone = function_kind(code, dict(function.__globals__), argdefs=defaults,
            closure=None if cells is None else tuple(type(cell)(value)
                for cell, value in zip(cells, contents, strict=True)))
        clone.__kwdefaults__ = dict(items) or None
        frozen[name] = clone
    rows = []

    def binding(value):
        if type(value) is not kind or namespace.get("__dict__") is not dictionary:
            raise ContractViolation("original resolution runtime required")
        for name in ("issuer", "_checkpoint_factory"):
            if namespace.get(name) is not None:
                raise ContractViolation("original resolution storage changed")
        instance = dictionary.__get__(value, kind)
        for name, function, code, defaults, keywords, items, cells, contents in origins:
            if (name not in ("__init__", "close") and (
                    namespace.get(name) is not function
                    or native_get(instance, name, function) is not function)
                or function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not keywords
                or (len(keywords or {}) != len(items) or any(key is not original_key or value is not original_value for (key, value), (original_key, original_value) in zip((keywords or {}).items(), items, strict=True))) or function.__closure__ is not cells
                or any(cell.cell_contents is not item
                    for cell, item in zip(cells or (), contents, strict=True))):
                raise ContractViolation("original resolution checkpoint dispatch changed")
        row = next((row for row in rows if row[0]() is value), None)
        instance = dictionary.__get__(value, kind)
        if (row is None or native_get(instance, "_checkpoint_factory") is not row[2]
            or row[1] is not None and native_get(instance, "issuer") is not row[1]()):
            raise ContractViolation("original resolution checkpoint binding changed")
        if native_get(instance, "resolver") is not row[3]():
            raise ContractViolation("original resolution catalog resolver changed")
        return row

    def read_catalog(value):
        row = resolver = result = None
        try:
            row = binding(value)
            resolver = row[3]()
            def check():
                if (type(resolver) is not catalog_kind
                    or catalog_namespace.get("__dict__") is not catalog_dictionary
                    or catalog_namespace.get("__getattribute__", object.__getattribute__) is not object.__getattribute__
                    or catalog_namespace.get("read_catalog_coordinate") is not catalog_reader
                    or catalog_reader.__code__ is not reader_code
                    or catalog_reader.__defaults__ is not reader_defaults
                    or catalog_reader.__kwdefaults__ is not reader_keywords
                    or (len(reader_keywords or {}) != len(reader_items) or any(key is not original_key or item is not original_item for (key, item), (original_key, original_item) in zip((reader_keywords or {}).items(), reader_items, strict=True)))
                    or catalog_reader.__closure__ is not reader_cells
                    or any(cell.cell_contents is not original
                           for cell, original in zip(reader_cells or (), reader_contents, strict=True))):
                    raise ContractViolation("original Code catalog reader changed")
                state = catalog_dictionary.__get__(resolver, catalog_kind)
                if (row is None or "read_catalog_coordinate" in state or state.get("_admission") is not row[4]()):
                    raise ContractViolation("original Code catalog reader binding changed")
            check()
            result = reader_frozen(resolver)
            check()
            binding(value)
            return result
        finally:
            value = row = resolver = result = None

    def inventory(self, operation, inventory, expected):
        binding(self)
        return frozen["_inventory_impl"](self, operation, inventory, expected, _catalog_read=read_catalog)

    def verify(value):
        binding(value)
        frozen["_check_checkpoint_factory"](value)
        binding(value)

    def create(self, *args, **kwargs):
        frozen["__init__"](self, *args, **kwargs)
        instance = dictionary.__get__(self, kind)
        factory = native_get(instance, "_checkpoint_factory")
        rows[:] = [row for row in rows if row[0]() is not None]
        resolver = native_get(instance, "resolver")
        if type(resolver) is not CodeSemanticContractCatalogResolver:
            raise ContractViolation("original Code catalog resolver required")
        rows.append((weak(self), None if factory is None else weak(native_get(instance, "issuer")), factory,
                     weak(resolver), weak(resolver._admission)))

    def issue(self, operation, inventory, expected):
        if type(self) is not kind or not any(row[0]() is self for row in rows):
            raise ContractViolation("original resolution runtime required")
        scope = handle = None
        try:
            binding(self)
            scope = frozen["_inventory_checkpoint"](self, operation, inventory, expected, _verify=verify)
            if scope is None:
                return frozen["_issue"](self, operation, inventory, expected)
            with scope:
                handle = frozen["_issue"](self, operation, inventory, expected)
                verify(self)
            verify(self)
            return handle
        except BaseException:
            if handle is not None:
                self.records.pop(handle, None)
            if not any(original is operation for original in self.issued_operations):
                self.issued_operations.append(operation)
            raise
        finally:
            scope = handle = operation = inventory = expected = None

    def validate(self, handle, expected):
        if type(self) is not kind:
            raise ContractViolation("original resolution runtime required")
        instance = dictionary.__get__(self, kind)
        records = native_get(instance, "records")
        if type(records) is not dict:
            raise ContractViolation("original resolution records required")
        record = next((value for original, value in dict.items(records) if original is handle), None)
        scope = None
        try:
            binding(self)
            if type(handle) is not WorkspaceDependencyResolutionAdmission or record is None:
                raise ContractViolation("foreign dependency resolution")
            scope = frozen["_inventory_checkpoint"](self, record.operation, record.inventory, expected, _verify=verify)
            if scope is None:
                return frozen["_validate"](self, handle, expected)
            with scope:
                frozen["_validate"](self, handle, expected)
                verify(self)
            verify(self)
        except BaseException:
            if record is not None and dict.get(records, handle) is record:
                dict.pop(records, handle, None)
            raise
        finally:
            scope = record = records = handle = expected = None

    def close(self):
        try:
            frozen["close"](self)
        finally:
            rows[:] = [row for row in rows if row[0]() is not self and row[0]() is not None]

    return create, issue, validate, close, inventory


(_WorkspaceDependencyResolutionRuntime.__init__, _WorkspaceDependencyResolutionRuntime.issue,
 _WorkspaceDependencyResolutionRuntime.validate, _WorkspaceDependencyResolutionRuntime.close,
 _WorkspaceDependencyResolutionRuntime._inventory) = (
    _bind_checkpoint_runtime(_WorkspaceDependencyResolutionRuntime)
)
del _bind_checkpoint_runtime
