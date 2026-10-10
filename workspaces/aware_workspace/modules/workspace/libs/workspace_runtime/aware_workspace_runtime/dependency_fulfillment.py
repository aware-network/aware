"""Original resolution fulfillment through the existing package-head publisher."""

import copy
import inspect
import os
from dataclasses import dataclass
from threading import current_thread
from types import MethodType

from aware_code_semantic_contract_runtime import (
    SemanticBody,
    SemanticDependencyCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyFulfillmentExpectation,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    decode_dependency_product_input,
    dependency_product_input_body,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyProduct,
    SemanticDependencyProductInput,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    decode_code_semantic_contract_match_admission,
)

from .observed_semantic_issuers import _unavailable


class WorkspaceDependencyFulfillmentAdmission:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("Workspace fulfillment issuer required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Workspace fulfillment admission is sealed")

    def __reduce__(self):
        raise TypeError("Workspace fulfillment admission is not portable")


@dataclass
class _Fulfillment:
    resolution: object
    body: SemanticBody | None
    heads: tuple[object, ...] = ()
    terminal: bool = False

    def retire(self):
        self.terminal = True
        self.body = None
        self.heads = ()


def _verify_original_entry(runtime, *, require_publisher=False):
    """Enter through retained verification before any mutable guard lookup."""
    if runtime.publisher_entrances:
        runtime.publisher_entrances[9][3]()
    elif require_publisher:
        _WorkspaceEmptyDependencyFulfillmentRuntime._check_publisher(runtime)
    else:
        _WorkspaceEmptyDependencyFulfillmentRuntime._check_live(runtime)


class _WorkspaceEmptyDependencyFulfillmentRuntime:
    def __init__(self, resolutions):
        self.resolutions = resolutions
        self.records = {}
        self.issued = []
        self.publisher = None
        self.publisher_resources = None
        self.publisher_entrances: tuple[
            tuple[object, str, object, MethodType, type], ...
        ] = ()
        self._closed = False
        self._pid = os.getpid()
        self._thread = current_thread()

    def _check_live(self):
        if (
            self._closed
            or self._pid != os.getpid()
            or self._thread is not current_thread()
        ):
            _unavailable("dependency_fulfillment_lifetime_unavailable")

    def bind_publisher(self, publisher):
        """Fixed composition supplies a borrowed original publisher, never a callback."""
        from .semantic_materialization_publication import (
            WorkspaceSemanticMaterializationPublisher,
        )

        _verify_original_entry(self)
        if type(publisher) is not WorkspaceSemanticMaterializationPublisher:
            _unavailable("original_dependency_publisher_required")
        if self.publisher is not None or self.records or self.issued:
            _unavailable("dependency_publisher_binding_replay")
        resources = (
            publisher._state_store,
            publisher._body_store,
            publisher._state_namespace,
        )
        entrances = []
        for receiver, name in (
            (publisher, "_read_graph_package_head_evidence"),
            (publisher, "_read_graph_v2_body"),
            (resources[0], "read"),
            (resources[1], "read_body"),
            (publisher, "_read_graph_v2_head"),
            (publisher, "_read_graph_v4_head_evidence"),
            (publisher, "_read_graph_v4_head"),
            (publisher, "_read_graph_v4_output_state"),
            (self, "_call_publisher"),
            (self, "_check_publisher"),
            (self, "_check_live"),
        ):
            descriptor = inspect.getattr_static(receiver, name)
            method = getattr(receiver, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not receiver
                or method.__func__ is not descriptor
            ):
                _unavailable("original_dependency_reader_required")
            entrances.append((receiver, name, descriptor, method, type(receiver)))
        self.publisher = publisher
        self.publisher_resources = resources
        self.publisher_entrances = tuple(entrances)

    def _check_publisher(self):
        from .semantic_materialization_publication import (
            WorkspaceSemanticMaterializationPublisher,
        )

        if self.publisher_entrances:
            self.publisher_entrances[10][3]()
        else:
            _WorkspaceEmptyDependencyFulfillmentRuntime._check_live(self)
        if self.publisher is None:
            _unavailable("dependency_product_publisher_unavailable")
        if type(self.publisher) is not WorkspaceSemanticMaterializationPublisher:
            _unavailable("dependency_product_publisher_substituted")
        if self.publisher_resources is None:
            raise RuntimeError("original publisher resource retention missing")
        state, body, namespace = self.publisher_resources
        if (
            self.publisher._state_store is not state
            or self.publisher._body_store is not body
            or type(self.publisher._state_namespace) is not str
            or self.publisher._state_namespace != namespace
        ):
            _unavailable("dependency_publisher_resources_changed")
        for (
            receiver,
            name,
            descriptor,
            method,
            receiver_type,
        ) in self.publisher_entrances:
            if (
                type(receiver) is not receiver_type
                or inspect.getattr_static(receiver, name) is not descriptor
                or method.__self__ is not receiver
                or method.__func__ is not descriptor
            ):
                _unavailable("dependency_product_reader_substituted")

    def _call_publisher(self, index, *args, **kwargs):
        check = self.publisher_entrances[9][3]
        check()
        if index in (0, 1, 4, 5, 6, 7):
            # Preserve this captured dispatcher through the complete nested chain.
            # Publisher/store readers never dynamically look up the next method.
            kwargs["_retained_read"] = self.publisher_entrances[8][3]
        result = self.publisher_entrances[index][3](*args, **kwargs)
        check()
        return result

    def _resolution(self, resolution, expected, *, empty=True):
        _verify_original_entry(self)
        self.resolutions.validate(resolution, expected)
        _verify_original_entry(self)
        record = self.resolutions.records[resolution]
        if empty and record.targets:
            _unavailable("dependency_products_require_original_fulfillment")
        return record

    def issue(self, resolution, expected):
        record = self._resolution(resolution, expected)
        if any(original is resolution for original in self.issued):
            _unavailable("dependency_fulfillment_replay")
        if len(self.records) >= 128:
            _unavailable("dependency_fulfillment_capacity")
        original = record.expected
        products = SemanticDependencyProductInput(
            copy.deepcopy(original.planning_input.package),
            copy.deepcopy(original.planning_input.source_identity_digest),
            tuple(
                (d.dependency_kind, d.dependency_ref)
                for d in original.planning_input.dependencies
            ),
            copy.deepcopy(original.demand_set),
            (),
            copy.deepcopy(original.planning_context.code_intent),
        )
        body = dependency_product_input_body(products)
        self._resolution(resolution, original)
        handle = object.__new__(WorkspaceDependencyFulfillmentAdmission)
        self.records[handle] = _Fulfillment(resolution, body)
        self.issued.append(resolution)
        return handle

    def _products(self, resolution, expected):
        from .semantic_materialization_publication import (
            WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
            WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
        )

        record = self._resolution(resolution, expected, empty=False)
        if not record.targets:
            return (), ()
        _verify_original_entry(self, require_publisher=True)
        if len(record.targets) > 128:
            _unavailable("dependency_product_target_capacity")
        inventory, _ = self.resolutions._inventory(
            record.operation, record.inventory, record.expected
        )
        products, heads, bodies, package_heads = [], [], {}, {}
        total_bytes = 0
        for demand, target, _origin, context, wire in record.targets:
            sources = tuple(
                source
                for source in inventory.targets
                if source.membership is target
                and source.context.package == context.package
            )
            if len(sources) != 1:
                _unavailable("dependency_product_source_not_unique")
            match = decode_code_semantic_contract_match_admission(
                wire, context=context, resolver=self.resolutions.resolver
            )
            h1 = self.publisher_entrances[8][3](
                0, context.package.package_ref, observation_role="dependency_h1"
            )
            if type(h1) not in (
                WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
                WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
            ):
                _unavailable("dependency_product_head_unavailable")
            h1.__post_init__()
            base = (
                h1.head.base_head
                if type(h1) is WorkspaceSemanticMaterializationHeadRereadEvidenceV4
                else h1.head
            )
            required = context.required_result_products
            if (
                len(required) != 1
                or base.package != context.package
                or base.source_identity_digest
                != sources[0].context.source_identity_digest
                or base.code_intent_digest != context.code_intent.intent_digest
                or base.code_match_digest != match.match_digest
                or base.result_coordinate.role != required[0].role
                or base.result_coordinate.contract != required[0].contract
            ):
                _unavailable("dependency_product_head_correspondence_differs")
            coordinate = base.result_coordinate
            key = canonical_json_bytes(coordinate.to_wire())
            if key not in bodies:
                total_bytes += coordinate.size_bytes
                if total_bytes > 8 * 1024 * 1024:
                    _unavailable("dependency_product_body_capacity")
                bodies[key] = self.publisher_entrances[8][3](1, coordinate)
            body = bodies[key]
            if body.coordinate != coordinate:
                _unavailable("dependency_product_body_correspondence_differs")
            h2 = self.publisher_entrances[8][3](
                0, context.package.package_ref, observation_role="dependency_h2"
            )
            if (
                type(h2) is not type(h1)
                or h2.materialization_head_revision != h1.materialization_head_revision
                or canonical_json_bytes(h2.head.to_wire())
                != canonical_json_bytes(h1.head.to_wire())
            ):
                _unavailable("dependency_product_head_changed")
            head_key = (
                h1.materialization_head_revision,
                canonical_json_bytes(h1.head.to_wire()),
            )
            prior = package_heads.setdefault(context.package.package_ref, head_key)
            if head_key != prior:
                _unavailable("dependency_product_shared_head_changed")
            products.append(
                SemanticDependencyProduct(
                    demand,
                    SemanticDependencyCoordinate(
                        context.package,
                        coordinate.contract,
                        coordinate.value_ref,
                        coordinate.digest,
                    ),
                    body,
                    h1.reread_evidence_digest,
                )
            )
            heads.append(
                (
                    h1.materialization_head_revision,
                    canonical_json_bytes(h1.head.to_wire()),
                )
            )
        self._resolution(resolution, expected, empty=False)
        for package_ref, retained in package_heads.items():
            final = self.publisher_entrances[8][3](
                0, package_ref, observation_role="dependency_h2"
            )
            if (
                type(final)
                not in (
                    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
                    WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
                )
                or (
                    final.materialization_head_revision,
                    canonical_json_bytes(final.head.to_wire()),
                )
                != retained
            ):
                _unavailable("dependency_product_head_changed")
        self._resolution(resolution, expected, empty=False)
        _verify_original_entry(self, require_publisher=True)
        return tuple(products), tuple(heads)

    def issue_products(self, resolution, expected):
        if any(original is resolution for original in self.issued):
            _unavailable("dependency_fulfillment_replay")
        try:
            record = self._resolution(resolution, expected, empty=False)
        except BaseException:
            # Recognize an original resolution without foreign hashing/equality.
            # Entry rejection is terminal even though body reads never started.
            if any(original is resolution for original in self.resolutions.records):
                self.issued.append(resolution)
            raise
        if not record.targets:
            return self.issue(resolution, expected)
        if len(self.records) >= 128:
            _unavailable("dependency_fulfillment_capacity")
        # Once reads start, failure cannot retry the same resolution as a fresh use.
        self.issued.append(resolution)
        products, heads = self._products(resolution, expected)
        original = record.expected
        value = SemanticDependencyProductInput(
            copy.deepcopy(original.planning_input.package),
            copy.deepcopy(original.planning_input.source_identity_digest),
            tuple(
                (d.dependency_kind, d.dependency_ref)
                for d in original.planning_input.dependencies
            ),
            copy.deepcopy(original.demand_set),
            products,
            copy.deepcopy(original.planning_context.code_intent),
        )
        body = dependency_product_input_body(value)
        self._resolution(resolution, expected, empty=False)
        handle = object.__new__(WorkspaceDependencyFulfillmentAdmission)
        self.records[handle] = _Fulfillment(resolution, body, heads)
        return handle

    def read(self, handle, resolution, expected):
        # Recognize retained identity without invoking a restamped handle's behavior.
        record = next(
            (value for original, value in self.records.items() if original is handle),
            None,
        )
        if record is None:
            _unavailable("foreign_dependency_fulfillment")
        try:
            if (
                type(handle) is not WorkspaceDependencyFulfillmentAdmission
                or record.terminal
                or record.body is None
            ):
                _unavailable("dependency_fulfillment_terminal")
            if resolution is not record.resolution:
                _unavailable("foreign_fulfillment_resolution")
            if record.heads:
                products, heads = self._products(resolution, expected)
                original = decode_dependency_product_input(record.body.canonical_body)
                if products != original.products or heads != record.heads:
                    _unavailable("dependency_product_currentness_changed")
            else:
                self._resolution(resolution, expected)
            return copy.deepcopy(record.body)
        except BaseException:
            record.retire()
            raise

    def validate(self, handle, resolution, expected):
        record = next(
            (value for original, value in self.records.items() if original is handle),
            None,
        )
        try:
            if type(expected) is not RetainedDependencyFulfillmentExpectation:
                _unavailable("exact_fulfillment_expectation_required")
            body = self.read(handle, resolution, expected.resolution)
            if (
                body.coordinate != expected.dependency_products_coordinate
                or body != dependency_product_input_body(expected.dependency_products)
            ):
                _unavailable("dependency_products_correspondence_differs")
            self._resolution(resolution, expected.resolution, empty=False)
        except BaseException:
            if record is not None:
                record.retire()
            raise

    def close(self):
        self._closed = True
        for record in self.records.values():
            record.retire()
        self.records.clear()
        self.issued.clear()
        self.publisher = None
        self.publisher_resources = None
        self.publisher_entrances = ()
