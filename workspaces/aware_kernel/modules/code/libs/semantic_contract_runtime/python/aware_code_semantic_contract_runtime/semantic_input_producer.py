"""Owner-neutral, nominal execution of original semantic-input producers."""

from __future__ import annotations

import inspect
import json
import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from threading import RLock, current_thread, get_ident
from types import MethodType
from typing import Awaitable, Callable, Protocol, cast

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .dependency_admission_interfaces import (
    DependencyFulfillmentAdmissionValidator,
    DependencyResolutionAdmissionValidator,
    RetainedDependencyFulfillmentExpectation,
    RetainedDependencyResolutionExpectation,
)
from .dependency_input_codec import (
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF,
    decode_dependency_product_input,
    dependency_product_input_body,
    encode_dependency_product_input,
)
from .dependency_inputs import SemanticDependencyProductInput
from .runtime import SemanticBody
from .semantic_candidates import _path as _candidate_path
from .source_selection import SemanticSourceSelection

_REGISTRATION_TOKEN = object()
_PREDECESSOR_CLOSURE_DOMAIN = b"aware.code.semantic-input-predecessor-closure.v1\0"
_CONTEXTUAL_PREDECESSOR_DOMAIN = b"aware.code.semantic-input-predecessor-closure.v2\0"
MAX_CONTEXT_BODIES = 64
MAX_CONTEXT_BYTES = 8_388_608
MAX_RETAINED_INPUT_RESULTS = 256
MAX_RETAINED_INPUT_RESULT_BYTES = 67_108_864
MAX_ORIGINAL_RESULT_VERIFICATION_WORK = 2_048


@dataclass(slots=True)
class _OriginalResultVerificationWork:
    remaining: list[int]
    process: int
    thread: object
    failed: bool = False


_ORIGINAL_RESULT_VERIFICATION_WORK: ContextVar[_OriginalResultVerificationWork | None] = (
    ContextVar("original_result_verification_work", default=None)
)


@contextmanager
def original_result_verification_work_scope(
    *, result_visits: int = MAX_ORIGINAL_RESULT_VERIFICATION_WORK,
    source_calls: int = MAX_ORIGINAL_RESULT_VERIFICATION_WORK,
    context_calls: int = MAX_ORIGINAL_RESULT_VERIFICATION_WORK,
):
    """Bound synchronous original checks, including recursion through owners.

    This quota grants no authority and performs no validation or owner call.
    Existing unscoped entrances retain their behavior. A nested scope cannot
    reset a partially spent or failed outer quota.
    """
    current = _ORIGINAL_RESULT_VERIFICATION_WORK.get()
    if current is not None:
        current.failed = True
        raise ContractViolation("original result verification work scope is nested")
    limits = (result_visits, source_calls, context_calls)
    if any(type(value) is not int or not 0 <= value <= MAX_ORIGINAL_RESULT_VERIFICATION_WORK
           for value in limits):
        raise ContractViolation("original result verification work limits differ")
    budget = _OriginalResultVerificationWork(list(limits), os.getpid(), current_thread())
    token = _ORIGINAL_RESULT_VERIFICATION_WORK.set(budget)
    try:
        yield
        if budget.failed:
            raise ContractViolation("original result verification work is terminal")
    finally:
        budget.failed = True
        _ORIGINAL_RESULT_VERIFICATION_WORK.reset(token)


def _charge_original_result_verification_work(index: int) -> None:
    budget = _ORIGINAL_RESULT_VERIFICATION_WORK.get()
    if budget is None:
        return
    if (budget.failed or budget.process != os.getpid()
            or budget.thread is not current_thread() or not current_thread().is_alive()
            or budget.remaining[index] == 0):
        budget.failed = True
        raise ContractViolation("original result verification work exhausted or expired")
    budget.remaining[index] -= 1


def _token(value: object, field: str) -> str:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise ContractViolation(f"{field} must be a nonempty token")
    return value


def _exact_coordinate(
    value: object, expected: type[object], field: str
) -> object:
    if type(value) is not expected:
        raise TypeError(f"{field} must be exact {expected.__name__}")
    value.__post_init__()  # type: ignore[attr-defined]
    return value


def _length_prefixed(value: bytes) -> bytes:
    if type(value) is not bytes:
        raise TypeError("predecessor closure field must be exact bytes")
    return len(value).to_bytes(8, "big") + value


@dataclass(frozen=True, slots=True)
class SemanticInputSourceContract:
    role: str
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "role"))
        _exact_coordinate(self.contract, SemanticContractRef, "contract")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"contract": self.contract.to_wire(), "role": self.role}


@dataclass(frozen=True, slots=True)
class SemanticInputContextContract:
    """Declared detached context, distinct from filesystem sources/products."""

    role: str
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "role"))
        _exact_coordinate(self.contract, SemanticContractRef, "contract")
        if self.contract == SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF:
            raise ContractViolation("dependency products require the existing dependency entrance")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"contract": self.contract.to_wire(), "role": self.role}


def _validate_context_bodies(bodies: tuple[SemanticBody, ...]) -> None:
    if type(bodies) is not tuple or len(bodies) > MAX_CONTEXT_BODIES:
        raise ContractViolation("context bodies must be an exact bounded tuple")
    total = 0
    roles = []
    for body in bodies:
        if type(body) is not SemanticBody:
            raise TypeError("exact context SemanticBody required")
        if type(body.canonical_body) is not bytes:
            raise TypeError("exact context bytes required")
        total += len(body.canonical_body)
        if total > MAX_CONTEXT_BYTES:
            raise ContractViolation("complete context body budget exceeded")
        body.__post_init__()
        if body.coordinate.contract == SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF:
            raise ContractViolation("dependency products require the existing dependency entrance")
        roles.append(body.coordinate.role)
        total += len(canonical_json_bytes(body.coordinate.to_wire()))
    if total > MAX_CONTEXT_BYTES:
        raise ContractViolation("complete context body budget exceeded")
    if roles != sorted(set(roles), key=str.encode):
        raise ContractViolation("context roles must be unique UTF-8 ordered")


def _production_payload(
    use_ref: str, operation_ref: str, stage: str,
    package_identity: SemanticInputPackageIdentity,
    sources: tuple[SemanticInputSourceCoordinate, ...], contexts: tuple[SemanticBody, ...],
) -> dict[str, object]:
    for value in sources:
        if type(value) is not SemanticInputSourceCoordinate:
            raise TypeError("source_coordinate must be exact SemanticInputSourceCoordinate")
        value.__post_init__()
    return _production_payload_from_validated_sources(
        use_ref, operation_ref, stage, package_identity, sources, contexts,
    )


def _production_payload_from_validated_sources(
    use_ref: str, operation_ref: str, stage: str,
    package_identity: SemanticInputPackageIdentity,
    sources: tuple[SemanticInputSourceCoordinate, ...], contexts: tuple[SemanticBody, ...],
) -> dict[str, object]:
    # Only the immediately preceding closed source validation is reused. There
    # is no callback, await, retained assertion or validation cache here. Context
    # bodies and package identity retain their original fresh validation.
    _validate_context_bodies(contexts)
    payload: dict[str, object] = {
        "operation_ref": operation_ref,
        "package_identity": package_identity.to_wire(),
        "source_coordinates": [_source_coordinate_wire(value) for value in sources],
        "stage": stage,
        "use_ref": use_ref,
    }
    if contexts:
        payload["contract"] = "aware.code.contextual-semantic-input-production.v2"
        payload["context_bodies"] = [body.coordinate.to_wire() for body in contexts]
    return payload


def _source_coordinate_wire(value: SemanticInputSourceCoordinate) -> dict[str, object]:
    coordinate = value.coordinate
    contract = coordinate.contract
    return {
        "coordinate": {"role": coordinate.role,
            "contract": {"key": contract.key, "version": contract.version,
                         "schema_digest": contract.schema_digest.value},
            "value_ref": coordinate.value_ref, "digest": coordinate.digest.value,
            "size_bytes": coordinate.size_bytes},
        "relative_path": value.relative_path,
    }


def _validated_production_payload_bytes(value: dict[str, object]) -> bytes:
    # Only used immediately after complete exact validation and projection in
    # the two closed input validators below. Fresh fixed-key native containers
    # and admitted scalar leaves need no second generic JSON walk. The ordinary
    # create/retention entrances keep their validating canonical serializer.
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SemanticInputDependencyContract:
    role: str
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "role"))
        _exact_coordinate(self.contract, SemanticContractRef, "contract")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"contract": self.contract.to_wire(), "role": self.role}


@dataclass(frozen=True, slots=True)
class SemanticInputProducerDeclaration:
    producer_ref: str
    profile_ref: str
    implementation: SemanticImplementationCoordinate
    configuration: SemanticConfigurationCoordinate
    source_contracts: tuple[SemanticInputSourceContract, ...]
    result_role: str
    result_contract: SemanticContractRef
    context_contracts: tuple[SemanticInputContextContract, ...] = ()

    def __post_init__(self) -> None:
        for field in ("producer_ref", "profile_ref", "result_role"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        _exact_coordinate(
            self.implementation,
            SemanticImplementationCoordinate,
            "implementation",
        )
        _exact_coordinate(
            self.configuration,
            SemanticConfigurationCoordinate,
            "configuration",
        )
        if type(self.source_contracts) is not tuple or not self.source_contracts:
            raise ContractViolation("source contracts must be a nonempty exact tuple")
        for source in self.source_contracts:
            if type(source) is not SemanticInputSourceContract:
                raise TypeError("exact SemanticInputSourceContract required")
            source.__post_init__()
        roles = tuple(source.role for source in self.source_contracts)
        if roles != tuple(sorted(roles, key=str.encode)) or len(set(roles)) != len(
            roles
        ):
            raise ContractViolation("source contracts must have unique ordered roles")
        _exact_coordinate(self.result_contract, SemanticContractRef, "result_contract")
        if type(self.context_contracts) is not tuple or len(self.context_contracts) > MAX_CONTEXT_BODIES:
            raise ContractViolation("context contracts must be an exact bounded tuple")
        for context in self.context_contracts:
            if type(context) is not SemanticInputContextContract:
                raise TypeError("exact SemanticInputContextContract required")
            context.__post_init__()
        context_roles = tuple(value.role for value in self.context_contracts)
        if context_roles != tuple(sorted(set(context_roles), key=str.encode)):
            raise ContractViolation("context contracts must have unique ordered roles")
        if set(context_roles) & set(roles):
            raise ContractViolation("context and source roles must be disjoint")

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        if self.context_contracts:
            ordinary = replace(self, context_contracts=())
            return ContentDigest.of_bytes(canonical_json_bytes({
                "contract": "aware.code.contextual-semantic-input-producer-declaration.v2",
                "ordinary_declaration_digest": ordinary.digest.to_wire(),
                "context_contracts": [value.to_wire() for value in self.context_contracts],
            }))
        return ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "configuration": self.configuration.to_wire(),
                    "contract": "aware.code.semantic-input-producer-declaration.v1",
                    "implementation": self.implementation.to_wire(),
                    "producer_ref": self.producer_ref,
                    "profile_ref": self.profile_ref,
                    "result_contract": self.result_contract.to_wire(),
                    "result_role": self.result_role,
                    "source_contracts": [
                        source.to_wire() for source in self.source_contracts
                    ],
                }
            )
        )


@dataclass(frozen=True, slots=True)
class SemanticInputJoinedProducerDeclaration:
    ordinary: SemanticInputProducerDeclaration
    predecessor_contracts: tuple[SemanticInputSourceContract, ...]
    predecessor_stages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.ordinary) is not SemanticInputProducerDeclaration:
            raise TypeError("ordinary must be exact SemanticInputProducerDeclaration")
        self.ordinary.__post_init__()
        if (
            type(self.predecessor_contracts) is not tuple
            or not self.predecessor_contracts
        ):
            raise ContractViolation(
                "predecessor contracts must be a nonempty exact tuple"
            )
        roles: list[str] = []
        for value in self.predecessor_contracts:
            if type(value) is not SemanticInputSourceContract:
                raise TypeError("exact SemanticInputSourceContract required")
            value.__post_init__()
            roles.append(value.role)
        if len(roles) != len(set(roles)):
            raise ContractViolation("predecessor contract roles must be unique")
        if type(self.predecessor_stages) is not tuple or (
            self.predecessor_stages and len(self.predecessor_stages) != len(roles)
        ):
            raise ContractViolation("complete predecessor stage tuple required")
        for stage in self.predecessor_stages:
            _token(stage, "predecessor stage")

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        if self.predecessor_stages:
            return ContentDigest.of_bytes(canonical_json_bytes({
                "contract": "aware.code.staged-semantic-input-joined-producer-declaration.v2",
                "ordinary_join_digest": replace(self, predecessor_stages=()).digest.value,
                "predecessor_stages": list(self.predecessor_stages),
            }))
        return ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "contract": (
                        "aware.code.semantic-input-joined-producer-declaration.v1"
                    ),
                    "ordinary_declaration_digest": self.ordinary.digest.value,
                    "predecessor_contracts": [
                        value.to_wire() for value in self.predecessor_contracts
                    ],
                }
            )
        )


@dataclass(frozen=True, slots=True)
class SemanticDependencyInputProducerDeclaration:
    producer_ref: str
    profile_ref: str
    implementation: SemanticImplementationCoordinate
    configuration: SemanticConfigurationCoordinate
    dependency_contracts: tuple[SemanticInputDependencyContract, ...]
    result_role: str
    result_contract: SemanticContractRef

    def __post_init__(self) -> None:
        for field in ("producer_ref", "profile_ref", "result_role"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        _exact_coordinate(
            self.implementation, SemanticImplementationCoordinate, "implementation"
        )
        _exact_coordinate(
            self.configuration,
            SemanticConfigurationCoordinate,
            "configuration",
        )
        if (
            type(self.dependency_contracts) is not tuple
            or not self.dependency_contracts
        ):
            raise ContractViolation(
                "dependency contracts must be a nonempty exact tuple"
            )
        for dependency in self.dependency_contracts:
            if type(dependency) is not SemanticInputDependencyContract:
                raise TypeError("exact SemanticInputDependencyContract required")
            dependency.__post_init__()
        roles = tuple(value.role for value in self.dependency_contracts)
        if roles != tuple(sorted(roles, key=str.encode)) or len(set(roles)) != len(
            roles
        ):
            raise ContractViolation(
                "dependency contracts must have unique ordered roles"
            )
        _exact_coordinate(self.result_contract, SemanticContractRef, "result_contract")

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "configuration": self.configuration.to_wire(),
                    "contract": (
                        "aware.code.dependency-semantic-input-producer-declaration.v1"
                    ),
                    "dependency_contracts": [
                        value.to_wire() for value in self.dependency_contracts
                    ],
                    "implementation": self.implementation.to_wire(),
                    "producer_ref": self.producer_ref,
                    "profile_ref": self.profile_ref,
                    "result_contract": self.result_contract.to_wire(),
                    "result_role": self.result_role,
                }
            )
        )


@dataclass(frozen=True, slots=True)
class SemanticInputPackageIdentity:
    """Detached target-package identity validated by the source owner."""

    package: SemanticPackageCoordinate
    package_name: str

    def __post_init__(self) -> None:
        _exact_coordinate(self.package, SemanticPackageCoordinate, "package")
        object.__setattr__(
            self, "package_name", _token(self.package_name, "package_name")
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "package": self.package.to_wire(),
            "package_name": self.package_name,
        }


@dataclass(frozen=True, slots=True)
class SemanticInputSourceCoordinate:
    """One package-relative retained source coordinate.

    The path is independent of the semantic value reference because retained
    stores may deduplicate identical bytes at distinct package paths.
    """

    relative_path: str
    coordinate: SemanticValueCoordinate

    def __post_init__(self) -> None:
        _exact_coordinate(self.coordinate, SemanticValueCoordinate, "coordinate")
        # The exact coordinate, including its digest, was just recursively
        # admitted. Reuse the original path grammar without constructing a
        # discarded candidate and validating that same digest a second time.
        _ = _candidate_path(self.relative_path)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        # The closed coordinate graph was just recursively validated. Project
        # its exact built-in fields without revalidating each nested wire call.
        return _source_coordinate_wire(self)


@dataclass(frozen=True, slots=True)
class SemanticInputSourceBody:
    """Detached retained bytes for one exact source coordinate."""

    source: SemanticInputSourceCoordinate
    canonical_body: bytes

    def __post_init__(self) -> None:
        if type(self.source) is not SemanticInputSourceCoordinate:
            raise TypeError("source must be exact SemanticInputSourceCoordinate")
        self.source.__post_init__()
        if type(self.canonical_body) is not bytes:
            raise TypeError("canonical_body must be exact bytes")
        if (
            len(self.canonical_body) != self.source.coordinate.size_bytes
            or ContentDigest.of_bytes(self.canonical_body)
            != self.source.coordinate.digest
        ):
            raise ContractViolation("semantic input source body differs")


@dataclass(frozen=True, slots=True)
class SemanticInputProductionExpectation:
    """Input-only expectation; original identities make it nonportable authority."""

    use_ref: str
    operation_ref: str
    stage: str
    package_identity: SemanticInputPackageIdentity
    operation_identity: object
    source_identity: object
    source_coordinates: tuple[SemanticInputSourceCoordinate, ...]
    input_digest: ContentDigest
    context_bodies: tuple[SemanticBody, ...] = ()

    def __post_init__(self) -> None:
        for field in ("use_ref", "operation_ref", "stage"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        if type(self.package_identity) is not SemanticInputPackageIdentity:
            raise TypeError("exact SemanticInputPackageIdentity required")
        self.package_identity.__post_init__()
        if self.operation_identity is None or self.source_identity is None:
            raise ContractViolation("original operation and source identities required")
        if type(self.source_coordinates) is not tuple:
            raise TypeError("source_coordinates must be exact tuple")
        for value in self.source_coordinates:
            if type(value) is not SemanticInputSourceCoordinate:
                raise TypeError(
                    "source_coordinate must be exact SemanticInputSourceCoordinate"
                )
            value.__post_init__()
        paths = tuple(item.relative_path for item in self.source_coordinates)
        ordered = tuple(sorted(paths, key=str.encode))
        if paths != ordered or len(set(paths)) != len(paths):
            raise ContractViolation("source coordinates must be unique and ordered")
        _exact_coordinate(self.input_digest, ContentDigest, "input_digest")
        expected = ContentDigest.of_bytes(
            _validated_production_payload_bytes(
                _production_payload_from_validated_sources(
                    self.use_ref, self.operation_ref, self.stage,
                    self.package_identity, self.source_coordinates, self.context_bodies,
                )
            )
        )
        if self.input_digest != expected:
            raise ContractViolation("semantic input expectation digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        use_ref: str,
        operation_ref: str,
        stage: str,
        package_identity: SemanticInputPackageIdentity,
        operation_identity: object,
        source_identity: object,
        source_coordinates: tuple[SemanticInputSourceCoordinate, ...],
        context_bodies: tuple[SemanticBody, ...] = (),
    ) -> SemanticInputProductionExpectation:
        payload = _production_payload(
            use_ref, operation_ref, stage, package_identity, source_coordinates, context_bodies,
        )
        return cls(
            use_ref,
            operation_ref,
            stage,
            package_identity,
            operation_identity,
            source_identity,
            source_coordinates,
            ContentDigest.of_bytes(canonical_json_bytes(payload)),
            context_bodies,
        )


@dataclass(frozen=True, slots=True)
class SemanticInputProductionInput:
    """Detached owner input; it carries no nominal source authority."""

    use_ref: str
    operation_ref: str
    stage: str
    package_identity: SemanticInputPackageIdentity
    sources: tuple[SemanticInputSourceBody, ...]
    input_digest: ContentDigest
    context_bodies: tuple[SemanticBody, ...] = ()

    def __post_init__(self) -> None:
        for field in ("use_ref", "operation_ref", "stage"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        if type(self.package_identity) is not SemanticInputPackageIdentity:
            raise TypeError("exact SemanticInputPackageIdentity required")
        self.package_identity.__post_init__()
        if type(self.sources) is not tuple:
            raise TypeError("sources must be exact tuple")
        for source in self.sources:
            if type(source) is not SemanticInputSourceBody:
                raise TypeError("exact SemanticInputSourceBody required")
            source.__post_init__()
        coordinates = tuple(source.source for source in self.sources)
        paths = tuple(item.relative_path for item in coordinates)
        if (
            paths != tuple(sorted(paths, key=str.encode))
            or len(set(paths)) != len(paths)
        ):
            raise ContractViolation("semantic input sources must be unique and ordered")
        _exact_coordinate(self.input_digest, ContentDigest, "input_digest")
        expected = ContentDigest.of_bytes(
            _validated_production_payload_bytes(
                _production_payload_from_validated_sources(
                    self.use_ref, self.operation_ref, self.stage,
                    self.package_identity, coordinates, self.context_bodies,
                )
            )
        )
        if self.input_digest != expected:
            raise ContractViolation("semantic input production digest mismatched")


@dataclass(frozen=True, slots=True)
class SemanticInputRoleJoinPredecessor:
    registration: AdmittedSemanticInputProducerRegistration
    expected: SemanticInputProductionExpectation

    def __post_init__(self) -> None:
        if type(self.registration) is not AdmittedSemanticInputProducerRegistration:
            raise TypeError("predecessor registration must be exact")
        if type(self.expected) is not SemanticInputProductionExpectation:
            raise TypeError("predecessor expectation must be exact")
        self.expected.__post_init__()


@dataclass(frozen=True, slots=True)
class SemanticInputPredecessorBody:
    role: str
    coordinate: SemanticValueCoordinate
    canonical_body: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "role"))
        _exact_coordinate(self.coordinate, SemanticValueCoordinate, "coordinate")
        if type(self.canonical_body) is not bytes:
            raise TypeError("predecessor canonical_body must be exact bytes")
        if (
            self.coordinate.role != self.role
            or len(self.canonical_body) != self.coordinate.size_bytes
            or ContentDigest.of_bytes(self.canonical_body) != self.coordinate.digest
        ):
            raise ContractViolation("semantic input predecessor body differs")


@dataclass(frozen=True, slots=True)
class SemanticInputJoinedProductionInput:
    ordinary: SemanticInputProductionInput
    predecessors: tuple[SemanticInputPredecessorBody, ...]
    predecessor_closure_digest: ContentDigest
    operation_ref: str

    def __post_init__(self) -> None:
        if type(self.ordinary) is not SemanticInputProductionInput:
            raise TypeError("ordinary must be exact SemanticInputProductionInput")
        self.ordinary.__post_init__()
        if type(self.predecessors) is not tuple or not self.predecessors:
            raise ContractViolation("predecessors must be a nonempty exact tuple")
        roles: list[str] = []
        for value in self.predecessors:
            if type(value) is not SemanticInputPredecessorBody:
                raise TypeError("exact SemanticInputPredecessorBody required")
            value.__post_init__()
            roles.append(value.role)
        if len(roles) != len(set(roles)):
            raise ContractViolation("predecessor body roles must be unique")
        _exact_coordinate(
            self.predecessor_closure_digest,
            ContentDigest,
            "predecessor_closure_digest",
        )
        object.__setattr__(
            self, "operation_ref", _token(self.operation_ref, "operation_ref")
        )
        if self.operation_ref != self.ordinary.operation_ref:
            raise ContractViolation("joined operation reference differs")


@dataclass(frozen=True, slots=True, eq=False)
class SemanticDependencyInputProductionExpectation:
    """Input-only binding to original dependency resolution and fulfillment."""

    use_ref: str
    operation_ref: str
    stage: str
    operation_identity: object
    resolution: RetainedDependencyResolutionExpectation
    fulfillment: RetainedDependencyFulfillmentExpectation
    input_digest: ContentDigest

    def __post_init__(self) -> None:
        for field in ("use_ref", "operation_ref", "stage"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        if self.operation_identity is None:
            raise ContractViolation("original operation identity required")
        if type(self.resolution) is not RetainedDependencyResolutionExpectation:
            raise TypeError("exact dependency resolution expectation required")
        if type(self.fulfillment) is not RetainedDependencyFulfillmentExpectation:
            raise TypeError("exact dependency fulfillment expectation required")
        if self.fulfillment.resolution is not self.resolution:
            raise ContractViolation("fulfillment resolution identity differs")
        body = dependency_product_input_body(self.fulfillment.dependency_products)
        if body.coordinate != self.fulfillment.dependency_products_coordinate:
            raise ContractViolation("dependency product coordinate differs")
        _exact_coordinate(self.input_digest, ContentDigest, "input_digest")
        expected = ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "dependency_products": body.coordinate.to_wire(),
                    "operation_ref": self.operation_ref,
                    "stage": self.stage,
                    "use_ref": self.use_ref,
                }
            )
        )
        if self.input_digest != expected:
            raise ContractViolation("dependency semantic input digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        use_ref: str,
        operation_ref: str,
        stage: str,
        operation_identity: object,
        resolution: RetainedDependencyResolutionExpectation,
        fulfillment: RetainedDependencyFulfillmentExpectation,
    ) -> SemanticDependencyInputProductionExpectation:
        body = dependency_product_input_body(fulfillment.dependency_products)
        payload = {
            "dependency_products": body.coordinate.to_wire(),
            "operation_ref": operation_ref,
            "stage": stage,
            "use_ref": use_ref,
        }
        return cls(
            use_ref,
            operation_ref,
            stage,
            operation_identity,
            resolution,
            fulfillment,
            ContentDigest.of_bytes(canonical_json_bytes(payload)),
        )


@dataclass(frozen=True, slots=True)
class SemanticDependencyInputProductionInput:
    """Detached dependency products; it carries no owner admission authority."""

    use_ref: str
    operation_ref: str
    stage: str
    dependency_products: SemanticDependencyProductInput
    input_digest: ContentDigest

    def __post_init__(self) -> None:
        for field in ("use_ref", "operation_ref", "stage"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        if type(self.dependency_products) is not SemanticDependencyProductInput:
            raise TypeError("exact SemanticDependencyProductInput required")
        body = dependency_product_input_body(self.dependency_products)
        _exact_coordinate(self.input_digest, ContentDigest, "input_digest")
        expected = ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "dependency_products": body.coordinate.to_wire(),
                    "operation_ref": self.operation_ref,
                    "stage": self.stage,
                    "use_ref": self.use_ref,
                }
            )
        )
        if self.input_digest != expected:
            raise ContractViolation("dependency semantic input digest mismatched")


class SemanticInputSourceValidator(Protocol):
    def validate_semantic_input_source(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> None: ...


class SemanticInputContextValidator(Protocol):
    """Original source owner also authenticates every declared context body.

    Code binds bytes/contracts only. This entrance must validate those bodies
    against original retained evidence, not admit a portable decoded value.
    """

    def validate_semantic_input_context(
        self, source_admission: object, *, expected: SemanticInputProductionExpectation
    ) -> None: ...


class SemanticInputSourceReader(Protocol):
    def read_semantic_input_sources(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> tuple[SemanticInputSourceBody, ...]: ...


type SemanticInputProducer = Callable[
    [SemanticInputProductionInput],
    SemanticBody | Awaitable[SemanticBody],
]

type SemanticDependencyInputProducer = Callable[
    [SemanticDependencyInputProductionInput],
    SemanticBody | Awaitable[SemanticBody],
]

type SemanticInputJoinedProducer = Callable[
    [SemanticInputJoinedProductionInput],
    SemanticBody | Awaitable[SemanticBody],
]


class AdmittedSemanticInputProducerRegistration:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _REGISTRATION_TOKEN:
            raise TypeError("semantic input registration is Code-issued only")
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("semantic input registration cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("semantic input registration cannot be copied")


class AdmittedDependencySemanticInputProducerRegistration:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _REGISTRATION_TOKEN:
            raise TypeError(
                "dependency semantic input registration is Code-issued only"
            )
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("dependency semantic input registration cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("dependency semantic input registration cannot be copied")


class AdmittedSemanticInputRoleJoin:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _REGISTRATION_TOKEN:
            raise TypeError("semantic input role join is Code-issued only")
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("semantic input role join cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("semantic input role join cannot be copied")


@dataclass(slots=True)
class _RegistrationState:
    declaration: SemanticInputProducerDeclaration
    producer: SemanticInputProducer
    validator: SemanticInputSourceValidator
    validator_entrance: Callable[..., None]
    reader: SemanticInputSourceReader
    reader_entrance: Callable[..., tuple[SemanticInputSourceBody, ...]]
    context_validator_entrance: Callable[..., None] | None = None
    context_declaration_digest: str | None = None
    retain_result: bool = False
    closed: bool = False
    running: int = 0


@dataclass(slots=True)
class _UseState:
    operation_identity: object
    source_identity: object
    running: bool = False
    consumed: bool = False


@dataclass(slots=True)
class _DependencyRegistrationState:
    declaration: SemanticDependencyInputProducerDeclaration
    producer: SemanticDependencyInputProducer
    resolution_validator: DependencyResolutionAdmissionValidator[object]
    resolution_validator_entrance: Callable[..., None]
    fulfillment_validator: DependencyFulfillmentAdmissionValidator[object, object]
    fulfillment_validator_entrance: Callable[..., None]
    closed: bool = False
    running: int = 0


@dataclass(slots=True)
class _DependencyUseState:
    operation_identity: object
    demand_operation_identity: object
    running: bool = False
    consumed: bool = False


@dataclass(slots=True)
class _JoinedRegistrationState:
    declaration: SemanticInputJoinedProducerDeclaration
    producer: SemanticInputJoinedProducer
    validator: SemanticInputSourceValidator
    validator_entrance: Callable[..., None]
    reader: SemanticInputSourceReader
    reader_entrance: Callable[..., tuple[SemanticInputSourceBody, ...]]
    context_validator_entrance: Callable[..., None] | None = None
    context_declaration_digest: str | None = None
    retain_result: bool = False
    closed: bool = False
    running: int = 0


@dataclass(slots=True)
class _RoleSlot:
    registration: AdmittedSemanticInputProducerRegistration
    expected: SemanticInputProductionExpectation
    role: str
    contract: SemanticContractRef
    result: SemanticBody | None = None
    context_binding: _ContextBinding | None = None


@dataclass(slots=True)
class _RoleJoinState:
    joined_registration: AdmittedSemanticInputProducerRegistration
    joined_expected: SemanticInputProductionExpectation
    source_admission: object
    operation_identity: object
    package_identity: SemanticInputPackageIdentity
    creator_thread: int
    slots: tuple[_RoleSlot, ...]
    next_slot: int = 0
    active_predecessors: int = 0
    running: bool = False
    consumed: bool = False
    context_binding: _ContextBinding | None = None
    bind_input_digests: bool = False


class SemanticInputProducerHost:
    """One process-local registry; registration values are nominal capabilities."""

    def __init__(self) -> None:
        self._pid = os.getpid()
        self._lock = RLock()
        self._registrations: dict[
            AdmittedSemanticInputProducerRegistration, _RegistrationState
        ] = {}
        self._uses: dict[
            tuple[AdmittedSemanticInputProducerRegistration, str], _UseState
        ] = {}
        self._dependency_registrations: dict[
            AdmittedDependencySemanticInputProducerRegistration,
            _DependencyRegistrationState,
        ] = {}
        self._dependency_uses: dict[
            tuple[AdmittedDependencySemanticInputProducerRegistration, str],
            _DependencyUseState,
        ] = {}
        self._joined_registrations: dict[
            AdmittedSemanticInputProducerRegistration, _JoinedRegistrationState
        ] = {}
        self._joined_uses: dict[
            tuple[AdmittedSemanticInputProducerRegistration, str], _UseState
        ] = {}
        self._role_joins: dict[
            AdmittedSemanticInputRoleJoin, _RoleJoinState
        ] = {}
        self._role_slots: dict[
            tuple[AdmittedSemanticInputProducerRegistration, str],
            tuple[AdmittedSemanticInputRoleJoin, int],
        ] = {}
        self._results: dict[int, _OriginalResult] = {}
        self._result_sequence = 0
        self._closed = False

    def _check_process(self) -> None:
        if self._pid != os.getpid():
            raise ContractViolation("semantic input host belongs to another process")
        if self._closed:
            raise ContractViolation("semantic input host is closed")

    def close(self) -> None:
        with self._lock:
            self._check_process()
            if any(state.running for state in self._registrations.values()):
                raise ContractViolation("semantic input execution is active")
            if any(state.running for state in self._dependency_registrations.values()):
                raise ContractViolation("dependency semantic input execution is active")
            if any(state.running for state in self._joined_registrations.values()):
                raise ContractViolation("joined semantic input execution is active")
            if any(
                state.active_predecessors or state.running
                for state in self._role_joins.values()
                if not state.consumed
            ):
                raise ContractViolation("semantic input role join is active")
            for handle, state in tuple(self._role_joins.items()):
                if not state.consumed:
                    _consume_role_join(self, handle, state)
            for state in self._registrations.values():
                state.closed = True
            for state in self._dependency_registrations.values():
                state.closed = True
            for state in self._joined_registrations.values():
                state.closed = True
            self._results.clear()
            self._closed = True


def _bound_method_is_original(
    owner: object, entrance: Callable[..., object], method_name: str
) -> bool:
    if type(entrance) is not MethodType:
        return False
    method = cast(MethodType, entrance)
    if method.__self__ is not owner:
        return False
    # Static namespace lookup never executes a replaced owner descriptor.
    for base in type.__getattribute__(type(owner), "__mro__"):
        namespace = type.__getattribute__(base, "__dict__")
        if method_name in namespace:
            return namespace[method_name] is method.__func__
    return False


def _producer_ref_registered(
    host: SemanticInputProducerHost,
    producer_ref: str,
) -> bool:
    return any(
        state.declaration.producer_ref == producer_ref
        for state in host._registrations.values()
        if not state.closed
    ) or any(
        state.declaration.ordinary.producer_ref == producer_ref
        for state in host._joined_registrations.values()
        if not state.closed
    )


def _check_context_validator(declaration, validator, entrance) -> None:
    if declaration.context_contracts:
        if not _bound_method_is_original(
            validator, entrance, "validate_semantic_input_context"
        ):
            raise ContractViolation("original context validator entrance required")
    elif entrance is not None:
        raise ContractViolation("context validator requires declared context contracts")


@dataclass(frozen=True, slots=True)
class _ContextBinding:
    bodies: tuple[SemanticBody, ...]
    input_tree: _ResultTree
    declaration_tree: _ResultTree

    def check(self, expected, declaration, delivered=None) -> None:
        # The exact graph was fully validated before retention. Fresh closed
        # identity/value/slot checks preserve it around every original callback
        # without rebuilding its canonical payload or rehashing unchanged bytes.
        self.input_tree.check(expected)
        self.declaration_tree.check(declaration)
        if delivered is not None and delivered.context_bodies is not self.bodies:
            raise ContractViolation("original context delivered tuple changed")


def _bind_context(declaration, expected) -> _ContextBinding | None:
    declaration.__post_init__()
    _validate_context_bodies(expected.context_bodies)
    actual = tuple(
        SemanticInputContextContract(body.coordinate.role, body.coordinate.contract)
        for body in expected.context_bodies
    )
    if actual != declaration.context_contracts:
        raise ContractViolation("complete declared context inventory differs")
    if not actual:
        return None
    return _ContextBinding(
        expected.context_bodies,
        _result_tree(expected),
        _result_tree(declaration),
    )


def _validate_original_context(entrance, source_admission, expected, declaration, binding, delivered=None):
    if binding is None:
        return
    binding.check(expected, declaration, delivered)
    _call_original_context(entrance, source_admission, expected, declaration)
    binding.check(expected, declaration, delivered)


def _call_original_context(entrance, source_admission, expected, declaration):
    _check_context_validator(declaration, getattr(entrance, "__self__", None), entrance)
    if entrance is None or entrance(source_admission, expected=expected) is not None:
        raise ContractViolation("original context validator must return None")
    _check_context_validator(declaration, getattr(entrance, "__self__", None), entrance)


# Closed Code field inventory: never traverse a provider or source handle.
_RESULT_FIELDS = {
    ContentDigest: ("value",),
    SemanticContractRef: ("key", "version", "schema_digest"),
    SemanticValueCoordinate: ("role", "contract", "value_ref", "digest", "size_bytes"),
    SemanticPackageCoordinate: ("package_ref", "package_kind", "manifest_digest"),
    SemanticImplementationCoordinate: ("implementation_ref", "closure_digest"),
    SemanticConfigurationCoordinate: ("configuration_ref", "digest"),
    SemanticInputPackageIdentity: ("package", "package_name"),
    SemanticInputSourceCoordinate: ("relative_path", "coordinate"),
    SemanticInputSourceContract: ("role", "contract"),
    SemanticInputContextContract: ("role", "contract"),
    SemanticInputProducerDeclaration: ("producer_ref", "profile_ref", "implementation",
        "configuration", "source_contracts", "result_role", "result_contract", "context_contracts"),
    SemanticInputJoinedProducerDeclaration: ("ordinary", "predecessor_contracts", "predecessor_stages"),
    SemanticBody: ("coordinate", "canonical_body"),
    SemanticInputProductionExpectation: ("use_ref", "operation_ref", "stage", "package_identity",
        "operation_identity", "source_identity", "source_coordinates", "input_digest", "context_bodies"),
}
_RESULT_SLOTS = {cls: tuple(type.__getattribute__(cls, "__dict__")[name]
                          for name in names) for cls, names in _RESULT_FIELDS.items()}


@dataclass(frozen=True, slots=True)
class _ResultTree:
    original: object
    kind: type
    children: tuple[_ResultTree, ...] = ()
    opaque: bool = False

    def check(self, current: object) -> None:
        pending: list[tuple[_ResultTree, object]] = [(self, current)]
        checked: set[type] = set()
        contracts: list[_ResultTree] = []
        while pending:
            tree, node = pending.pop()
            if tree.opaque:
                if node is not tree.original:
                    raise ContractViolation("original opaque result identity changed")
                continue
            kind = tree.kind
            if type(node) is not kind:
                raise ContractViolation("original result node type changed")
            if kind is str or kind is bytes or kind is int or kind is bool or kind is type(None):
                if node != tree.original:
                    raise ContractViolation("original result scalar changed")
                continue
            if node is not tree.original:
                raise ContractViolation("original result node identity changed")
            # Repeated source rows often share one original contract. Validate
            # its retained subtree once in this behavior-free synchronous walk;
            # every occurrence still requires exact type and original identity.
            if kind is SemanticContractRef:
                if any(tree is original for original in contracts):
                    continue
                if len(contracts) < 32:
                    contracts.append(tree)
            if kind is tuple:
                items = cast(tuple[object, ...], node)
                if len(items) != len(tree.children):
                    raise ContractViolation("original result tuple changed")
                pending.extend(zip(tree.children, items, strict=True))
            else:
                # Original slot descriptors are checked before their first
                # use, then again after this synchronous behavior-free walk.
                # This list contains only retained closed Code classes.
                if kind not in checked:
                    _check_result_slots(kind)
                    checked.add(kind)
                pending.extend((child, slot.__get__(node, kind))
                    for child, slot in zip(tree.children, _RESULT_SLOTS[kind], strict=True))
        for kind in checked:
            _check_result_slots(kind)


def _check_result_slots(kind):
    namespace = type.__getattribute__(kind, "__dict__")
    if any(namespace.get(name) is not slot for name, slot in
           zip(_RESULT_FIELDS[kind], _RESULT_SLOTS[kind], strict=True)):
        raise ContractViolation("original Code result slot changed")


def _result_tree(value, *, opaque=False, shared_contracts=None):
    if shared_contracts is None:
        shared_contracts = []
    kind = type(value)
    if opaque or any(kind is scalar for scalar in (str, bytes, int, bool, type(None))):
        return _ResultTree(value, kind, opaque=opaque)
    if type(value) is tuple:
        return _ResultTree(value, kind, tuple(_result_tree(x, shared_contracts=shared_contracts) for x in value))
    if not any(kind is cls for cls in _RESULT_FIELDS):
        raise ContractViolation("foreign result tree node")
    _check_result_slots(kind)
    if kind is SemanticContractRef:
        for original in shared_contracts:
            if value is original.original:
                return original
    result = _ResultTree(value, kind, tuple(_result_tree(slot.__get__(value, kind),
        opaque=(kind is SemanticInputProductionExpectation and name in
                ("operation_identity", "source_identity")), shared_contracts=shared_contracts)
        for name, slot in zip(_RESULT_FIELDS[kind], _RESULT_SLOTS[kind], strict=True)))
    if kind is SemanticContractRef and len(shared_contracts) < 32:
        shared_contracts.append(result)
    return result


@dataclass(slots=True)
class _OriginalResult:
    key: tuple[AdmittedSemanticInputProducerRegistration, str]
    sequence: int
    state: _RegistrationState | _JoinedRegistrationState
    source_admission: object
    expected: SemanticInputProductionExpectation
    result: SemanticBody
    input_tree: _ResultTree
    declaration_tree: _ResultTree
    result_tree: _ResultTree
    entrances: tuple[object, ...]
    receiver_types: tuple[type, type]
    context_binding: _ContextBinding | None
    thread: object
    predecessors: tuple[_OriginalResult, ...]
    size_bytes: int
    active: bool = False


def _prepare_result(state, expected):
    if not state.retain_result:
        return None
    return (_result_tree(expected), _result_tree(state.declaration),
            (state.producer, state.validator, state.validator_entrance,
             state.reader, state.reader_entrance, state.context_validator_entrance),
            current_thread(), (type(state.validator), type(state.reader)))


def _result_state(host, record):
    registration = record.key[0]
    if type(record.state) is _RegistrationState:
        return _registration_state(host, registration)
    return _joined_registration_state(host, registration)


def _check_result(host, record):
    if host._results.get(record.sequence) is not record:
        raise ContractViolation("original result is retired")
    if record.thread is not current_thread() or not current_thread().is_alive():
        raise ContractViolation("original result belongs to another thread")
    record.input_tree.check(record.expected)
    record.declaration_tree.check(record.state.declaration)
    record.result_tree.check(record.result)
    if (type(record.state.validator) is not record.receiver_types[0]
            or type(record.state.reader) is not record.receiver_types[1]):
        raise ContractViolation("original result owner receiver type changed")
    if _result_state(host, record) is not record.state:
        raise ContractViolation("original result registration changed")
    if record.state.retain_result is not True:
        raise ContractViolation("original result retention policy changed")
    current = (record.state.producer, record.state.validator, record.state.validator_entrance,
               record.state.reader, record.state.reader_entrance, record.state.context_validator_entrance)
    if any(a is not b for a, b in zip(current, record.entrances, strict=True)):
        raise ContractViolation("original result execution entrance changed")


def _retire_result(host, record):
    host._results.pop(record.sequence, None)
    for child in tuple(host._results.values()):
        if any(parent is record for parent in child.predecessors):
            _retire_result(host, child)


def _retain_result(host, registration, state, source_admission, expected, result,
                   prepared, context_binding, predecessors=()):
    if prepared is None:
        return
    if any(record.result is result for record in host._results.values()):
        raise ContractViolation("returned result already has a retained invocation")
    input_tree, declaration_tree, entrances, thread, receiver_types = prepared
    input_tree.check(expected)
    declaration_tree.check(state.declaration)
    wire = canonical_json_bytes(_production_payload(expected.use_ref, expected.operation_ref,
        expected.stage, expected.package_identity, expected.source_coordinates, expected.context_bodies))
    size = (len(result.canonical_body) + len(canonical_json_bytes(result.coordinate.to_wire()))
            + len(wire) + sum(len(x.canonical_body) for x in expected.context_bodies))
    if (len(host._results) >= MAX_RETAINED_INPUT_RESULTS
            or len(result.canonical_body) > MAX_CONTEXT_BYTES
            or size + sum(x.size_bytes for x in host._results.values()) > MAX_RETAINED_INPUT_RESULT_BYTES):
        raise ContractViolation("original result retention budget exceeded")
    for parent in predecessors:
        _check_result(host, parent)
    from .source_selection import SOURCE_SELECTION_REF, decode_source_selection
    if result.coordinate.contract == SOURCE_SELECTION_REF:
        selection = decode_source_selection(result.canonical_body)
        if (selection.package != expected.package_identity.package
                or selection.production_input_digest != expected.input_digest
                or selection.predecessor_coordinates != tuple(x.result.coordinate for x in predecessors)):
            raise ContractViolation("source selection original production differs")
    key = (registration, expected.use_ref)
    host._result_sequence += 1
    sequence = host._result_sequence
    host._results[sequence] = _OriginalResult(key, sequence, state, source_admission, expected, result,
        input_tree, declaration_tree, _result_tree(result), entrances, receiver_types, context_binding,
        thread, predecessors, size)


def _find_result(host, registration, source_admission, expected, result):
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("exact original semantic input host required")
    host._check_process()
    record = next((x for x in host._results.values() if x.result is result), None)
    if record is None:
        raise ContractViolation("original returned semantic input result required")
    try:
        if (registration is not record.key[0] or source_admission is not record.source_admission
                or expected is not record.expected):
            raise ContractViolation("original result invocation differs")
        _check_result(host, record)
    except BaseException:
        _retire_result(host, record)
        raise
    return record


def _validate_result_source(host, record):
    state = record.state
    try:
        _charge_original_result_verification_work(0)
        with host._lock:
            _check_result(host, record)
        validator = cast(Callable[..., None], record.entrances[2])
        _charge_original_result_verification_work(1)
        if validator(record.source_admission, expected=record.expected) is not None:
            raise ContractViolation("original result source validator must return None")
        with host._lock:
            _check_result(host, record)
        declaration = state.declaration if type(state) is _RegistrationState else state.declaration.ordinary
        if record.context_binding is not None:
            # The immediately preceding and following complete record checks
            # cover the same original expectation, contexts and declaration.
            # Retain the fresh callback and original entrance checks here.
            _charge_original_result_verification_work(2)
            _call_original_context(record.entrances[5], record.source_admission,
                record.expected, declaration)
        with host._lock:
            _check_result(host, record)
    except BaseException:
        with host._lock:
            _retire_result(host, record)
        raise


@contextmanager
def _original_result_use(host, registration, *, source_admission, expected, result):
    with host._lock:
        record = _find_result(host, registration, source_admission, expected, result)
        involved = (*record.predecessors, record)
        try:
            for item in involved:
                _check_result(host, item)
                if item.active:
                    raise ContractViolation("original result read is already active")
            for item in involved:
                item.active = True
                item.state.running += 1
        except BaseException:
            _retire_result(host, record)
            raise
    try:
        for item in involved:
            _validate_result_source(host, item)
        yield record
        for item in involved:
            _validate_result_source(host, item)
        with host._lock:
            host._check_process()
            for item in involved:
                _check_result(host, item)
    except BaseException:
        with host._lock:
            _retire_result(host, record)
        raise
    finally:
        with host._lock:
            for item in involved:
                item.active = False
                item.state.running -= 1


def validate_registered_semantic_input_result(
    host: SemanticInputProducerHost, registration: AdmittedSemanticInputProducerRegistration,
    *, source_admission: object, expected: SemanticInputProductionExpectation,
    result: SemanticBody,
) -> None:
    """Validate a retained original return; repeated validation is not execution."""
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("exact original semantic input host required")
    with _original_result_use(host, registration, source_admission=source_admission,
                              expected=expected, result=result):
        pass


def read_registered_semantic_input_source_selection(
    host: SemanticInputProducerHost, registration: AdmittedSemanticInputProducerRegistration,
    *, source_admission: object, expected: SemanticInputProductionExpectation,
    result: SemanticBody,
) -> SemanticSourceSelection:
    """Return detached generic selection after original result/currentness checks."""
    from .source_selection import SOURCE_SELECTION_REF, decode_source_selection
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("exact original semantic input host required")
    with _original_result_use(host, registration, source_admission=source_admission,
                              expected=expected, result=result) as record:
        if record.result.coordinate.contract != SOURCE_SELECTION_REF:
            raise ContractViolation("original result is not a declared source selection")
        return decode_source_selection(record.result.canonical_body)


def release_registered_semantic_input_result(
    host: SemanticInputProducerHost, registration: AdmittedSemanticInputProducerRegistration,
    *, source_admission: object, expected: SemanticInputProductionExpectation,
    result: SemanticBody,
) -> None:
    """Retire retained data without calling an expired source owner."""
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("exact original semantic input host required")
    with host._lock:
        record = _find_result(host, registration, source_admission, expected, result)
        if record.active or any(child.active for child in host._results.values()
                               if any(parent is record for parent in child.predecessors)):
            raise ContractViolation("original result read is active")
        _retire_result(host, record)


def register_semantic_input_producer(
    host: SemanticInputProducerHost,
    *,
    declaration: SemanticInputProducerDeclaration,
    producer: SemanticInputProducer,
    validator: SemanticInputSourceValidator,
    validator_entrance: Callable[..., None],
    reader: SemanticInputSourceReader,
    reader_entrance: Callable[..., tuple[SemanticInputSourceBody, ...]],
    context_validator_entrance: Callable[..., None] | None = None,
    retain_result: bool = False,
) -> AdmittedSemanticInputProducerRegistration:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(declaration) is not SemanticInputProducerDeclaration:
        raise TypeError("declaration must be exact SemanticInputProducerDeclaration")
    declaration.__post_init__()
    if not callable(producer):
        raise TypeError("producer must be callable")
    if not _bound_method_is_original(
        validator, validator_entrance, "validate_semantic_input_source"
    ):
        raise ContractViolation("original registered validator entrance required")
    if not _bound_method_is_original(
        reader, reader_entrance, "read_semantic_input_sources"
    ):
        raise ContractViolation("original registered reader entrance required")
    _check_context_validator(declaration, validator, context_validator_entrance)
    if type(retain_result) is not bool:
        raise TypeError("retain_result must be an exact boolean")
    with host._lock:
        host._check_process()
        if _producer_ref_registered(host, declaration.producer_ref):
            raise ContractViolation("semantic input producer already registered")
        registration = AdmittedSemanticInputProducerRegistration(_REGISTRATION_TOKEN)
        host._registrations[registration] = _RegistrationState(
            declaration,
            producer,
            validator,
            validator_entrance,
            reader,
            reader_entrance,
            context_validator_entrance,
            declaration.digest.value if declaration.context_contracts else None,
            retain_result,
        )
        return registration


def register_joined_semantic_input_producer(
    host: SemanticInputProducerHost,
    *,
    declaration: SemanticInputJoinedProducerDeclaration,
    producer: SemanticInputJoinedProducer,
    validator: SemanticInputSourceValidator,
    validator_entrance: Callable[..., None],
    reader: SemanticInputSourceReader,
    reader_entrance: Callable[..., tuple[SemanticInputSourceBody, ...]],
    context_validator_entrance: Callable[..., None] | None = None,
    retain_result: bool = False,
) -> AdmittedSemanticInputProducerRegistration:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(declaration) is not SemanticInputJoinedProducerDeclaration:
        raise TypeError(
            "declaration must be exact SemanticInputJoinedProducerDeclaration"
        )
    declaration.__post_init__()
    if not callable(producer):
        raise TypeError("producer must be callable")
    if not _bound_method_is_original(
        validator, validator_entrance, "validate_semantic_input_source"
    ):
        raise ContractViolation("original registered validator entrance required")
    if not _bound_method_is_original(
        reader, reader_entrance, "read_semantic_input_sources"
    ):
        raise ContractViolation("original registered reader entrance required")
    _check_context_validator(declaration.ordinary, validator, context_validator_entrance)
    if type(retain_result) is not bool:
        raise TypeError("retain_result must be an exact boolean")
    with host._lock:
        host._check_process()
        if _producer_ref_registered(host, declaration.ordinary.producer_ref):
            raise ContractViolation("semantic input producer already registered")
        registration = AdmittedSemanticInputProducerRegistration(_REGISTRATION_TOKEN)
        host._joined_registrations[registration] = _JoinedRegistrationState(
            declaration,
            producer,
            validator,
            validator_entrance,
            reader,
            reader_entrance,
            context_validator_entrance,
            declaration.digest.value if declaration.ordinary.context_contracts else None,
            retain_result,
        )
        return registration


def register_dependency_semantic_input_producer(
    host: SemanticInputProducerHost,
    *,
    declaration: SemanticDependencyInputProducerDeclaration,
    producer: SemanticDependencyInputProducer,
    resolution_validator: DependencyResolutionAdmissionValidator[object],
    resolution_validator_entrance: Callable[..., None],
    fulfillment_validator: DependencyFulfillmentAdmissionValidator[object, object],
    fulfillment_validator_entrance: Callable[..., None],
) -> AdmittedDependencySemanticInputProducerRegistration:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(declaration) is not SemanticDependencyInputProducerDeclaration:
        raise TypeError(
            "declaration must be exact SemanticDependencyInputProducerDeclaration"
        )
    declaration.__post_init__()
    if not callable(producer):
        raise TypeError("producer must be callable")
    if not _bound_method_is_original(
        resolution_validator,
        resolution_validator_entrance,
        "validate_dependency_resolution_admission",
    ):
        raise ContractViolation("original dependency resolution entrance required")
    if not _bound_method_is_original(
        fulfillment_validator,
        fulfillment_validator_entrance,
        "validate_dependency_fulfillment_admission",
    ):
        raise ContractViolation("original dependency fulfillment entrance required")
    with host._lock:
        host._check_process()
        if any(
            state.declaration.producer_ref == declaration.producer_ref
            for state in host._dependency_registrations.values()
            if not state.closed
        ):
            raise ContractViolation(
                "dependency semantic input producer already registered"
            )
        registration = AdmittedDependencySemanticInputProducerRegistration(
            _REGISTRATION_TOKEN
        )
        host._dependency_registrations[registration] = _DependencyRegistrationState(
            declaration,
            producer,
            resolution_validator,
            resolution_validator_entrance,
            fulfillment_validator,
            fulfillment_validator_entrance,
        )
        return registration


def _registration_state(
    host: SemanticInputProducerHost,
    registration: AdmittedSemanticInputProducerRegistration,
) -> _RegistrationState:
    if type(registration) is not AdmittedSemanticInputProducerRegistration:
        raise TypeError("registration must be exact")
    state = host._registrations.get(registration)
    if (
        state is None
        or registration._token is not _REGISTRATION_TOKEN
        or state.closed
    ):
        raise ContractViolation("semantic input registration is unavailable")
    if not _bound_method_is_original(
        state.validator,
        state.validator_entrance,
        "validate_semantic_input_source",
    ):
        raise ContractViolation("semantic input validator entrance changed")
    if not _bound_method_is_original(
        state.reader, state.reader_entrance, "read_semantic_input_sources"
    ):
        raise ContractViolation("semantic input reader entrance changed")
    _check_context_validator(state.declaration, state.validator, state.context_validator_entrance)
    if state.context_declaration_digest is not None and state.declaration.digest.value != state.context_declaration_digest:
        raise ContractViolation("registered context declaration changed")
    return state


def _dependency_registration_state(
    host: SemanticInputProducerHost,
    registration: AdmittedDependencySemanticInputProducerRegistration,
) -> _DependencyRegistrationState:
    if type(registration) is not AdmittedDependencySemanticInputProducerRegistration:
        raise TypeError("dependency registration must be exact")
    state = host._dependency_registrations.get(registration)
    if (
        state is None
        or registration._token is not _REGISTRATION_TOKEN
        or state.closed
    ):
        raise ContractViolation("dependency semantic input registration is unavailable")
    if not _bound_method_is_original(
        state.resolution_validator,
        state.resolution_validator_entrance,
        "validate_dependency_resolution_admission",
    ):
        raise ContractViolation("dependency resolution entrance changed")
    if not _bound_method_is_original(
        state.fulfillment_validator,
        state.fulfillment_validator_entrance,
        "validate_dependency_fulfillment_admission",
    ):
        raise ContractViolation("dependency fulfillment entrance changed")
    return state


def _joined_registration_state(
    host: SemanticInputProducerHost,
    registration: AdmittedSemanticInputProducerRegistration,
) -> _JoinedRegistrationState:
    if type(registration) is not AdmittedSemanticInputProducerRegistration:
        raise TypeError("joined registration must be exact")
    state = host._joined_registrations.get(registration)
    if (
        state is None
        or registration._token is not _REGISTRATION_TOKEN
        or state.closed
    ):
        raise ContractViolation("joined semantic input registration is unavailable")
    if not _bound_method_is_original(
        state.validator,
        state.validator_entrance,
        "validate_semantic_input_source",
    ):
        raise ContractViolation("joined semantic input validator entrance changed")
    if not _bound_method_is_original(
        state.reader,
        state.reader_entrance,
        "read_semantic_input_sources",
    ):
        raise ContractViolation("joined semantic input reader entrance changed")
    _check_context_validator(state.declaration.ordinary, state.validator, state.context_validator_entrance)
    if state.context_declaration_digest is not None and state.declaration.digest.value != state.context_declaration_digest:
        raise ContractViolation("registered context declaration changed")
    return state


def _role_join_state(
    host: SemanticInputProducerHost,
    role_join: AdmittedSemanticInputRoleJoin,
) -> _RoleJoinState:
    if type(role_join) is not AdmittedSemanticInputRoleJoin:
        raise TypeError("role_join must be exact AdmittedSemanticInputRoleJoin")
    state = host._role_joins.get(role_join)
    if (
        state is None
        or role_join._token is not _REGISTRATION_TOKEN
        or state.consumed
    ):
        raise ContractViolation("semantic input role join is unavailable")
    if state.creator_thread != get_ident():
        raise ContractViolation("semantic input role join belongs to another thread")
    try:
        if state.context_binding is not None:
            declared = _joined_registration_state(host, state.joined_registration).declaration.ordinary
            state.context_binding.check(state.joined_expected, declared)
        for slot in state.slots:
            if slot.context_binding is not None:
                slot.context_binding.check(slot.expected, _registration_state(host, slot.registration).declaration)
    except BaseException:
        _consume_role_join(host, role_join, state)
        raise
    return state


def _consume_role_join(
    host: SemanticInputProducerHost,
    role_join: AdmittedSemanticInputRoleJoin,
    state: _RoleJoinState,
) -> None:
    for index, slot in enumerate(state.slots):
        key = (slot.registration, slot.expected.use_ref)
        if host._role_slots.get(key) == (role_join, index):
            del host._role_slots[key]
        slot.result = None
    state.consumed = True
    if host._role_joins.get(role_join) is state:
        del host._role_joins[role_join]


def _predecessor_closure_digest(state: _RoleJoinState) -> ContentDigest:
    contextual = state.bind_input_digests or bool(state.joined_expected.context_bodies) or any(
        slot.expected.context_bodies for slot in state.slots
    )
    payload = bytearray(
        _CONTEXTUAL_PREDECESSOR_DOMAIN if contextual else _PREDECESSOR_CLOSURE_DOMAIN
    )
    payload.extend(_length_prefixed(state.joined_expected.operation_ref.encode()))
    payload.extend(
        _length_prefixed(canonical_json_bytes(state.package_identity.to_wire()))
    )
    if contextual:
        payload.extend(_length_prefixed(state.joined_expected.input_digest.value.encode()))
    for slot in state.slots:
        if slot.result is None:
            raise ContractViolation("semantic input predecessor is missing")
        payload.extend(_length_prefixed(slot.role.encode()))
        payload.extend(_length_prefixed(slot.expected.use_ref.encode()))
        if contextual:
            payload.extend(_length_prefixed(slot.expected.input_digest.value.encode()))
        payload.extend(
            _length_prefixed(
                canonical_json_bytes(
                    [value.to_wire() for value in slot.expected.source_coordinates]
                )
            )
        )
        payload.extend(
            _length_prefixed(canonical_json_bytes(slot.result.coordinate.to_wire()))
        )
        payload.extend(_length_prefixed(slot.result.canonical_body))
    return ContentDigest.of_bytes(bytes(payload))


def _detached_predecessors(
    state: _RoleJoinState,
) -> tuple[SemanticInputPredecessorBody, ...]:
    values: list[SemanticInputPredecessorBody] = []
    for slot in state.slots:
        if slot.result is None:
            raise ContractViolation("semantic input predecessor is missing")
        coordinate = slot.result.coordinate
        detached_coordinate = SemanticValueCoordinate(
            coordinate.role,
            coordinate.contract,
            coordinate.value_ref,
            coordinate.digest,
            coordinate.size_bytes,
        )
        values.append(
            SemanticInputPredecessorBody(
                slot.role,
                detached_coordinate,
                memoryview(slot.result.canonical_body).tobytes(),
            )
        )
    return tuple(values)


def open_semantic_input_role_join(
    host: SemanticInputProducerHost,
    *,
    joined_registration: AdmittedSemanticInputProducerRegistration,
    joined_expected: SemanticInputProductionExpectation,
    source_admission: object,
    predecessors: tuple[SemanticInputRoleJoinPredecessor, ...],
) -> AdmittedSemanticInputRoleJoin:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(joined_expected) is not SemanticInputProductionExpectation:
        raise TypeError("joined_expected must be exact")
    joined_expected.__post_init__()
    if source_admission is None:
        raise ContractViolation("original source admission identity required")
    if type(predecessors) is not tuple or not predecessors:
        raise ContractViolation("predecessors must be a nonempty exact tuple")
    for value in predecessors:
        if type(value) is not SemanticInputRoleJoinPredecessor:
            raise TypeError("exact SemanticInputRoleJoinPredecessor required")
        value.__post_init__()
    with host._lock:
        host._check_process()
        joined_state = _joined_registration_state(host, joined_registration)
        joined_context = _bind_context(joined_state.declaration.ordinary, joined_expected)
        contracts = joined_state.declaration.predecessor_contracts
        if len(predecessors) != len(contracts):
            raise ContractViolation("semantic input predecessor count differs")
        validator_calls: list[
            tuple[Callable[..., None], SemanticInputProductionExpectation]
        ] = [(joined_state.validator_entrance, joined_expected)]
        context_calls = [(
            joined_state.context_validator_entrance, joined_expected,
            joined_state.declaration.ordinary, joined_context,
        )]
        slots: list[_RoleSlot] = []
        predecessor_states: list[_RegistrationState] = []
        seen_keys: set[tuple[AdmittedSemanticInputProducerRegistration, str]] = set()
        stages = joined_state.declaration.predecessor_stages or tuple(x.role for x in contracts)
        for value, contract, stage in zip(predecessors, contracts, stages, strict=True):
            state = _registration_state(host, value.registration)
            if joined_state.retain_result and not state.retain_result:
                raise ContractViolation("retained joined result requires retained predecessor origins")
            expected = value.expected
            key = (value.registration, expected.use_ref)
            if key in seen_keys:
                raise ContractViolation("semantic input predecessor use is duplicate")
            seen_keys.add(key)
            if (
                state.declaration.result_role != contract.role
                or state.declaration.result_contract != contract.contract
                or expected.stage != stage
                or expected.operation_ref != joined_expected.operation_ref
                or expected.operation_identity is not joined_expected.operation_identity
                or expected.package_identity != joined_expected.package_identity
            ):
                raise ContractViolation("semantic input predecessor identity differs")
            slots.append(
                _RoleSlot(
                    value.registration,
                    expected,
                    contract.role,
                    contract.contract,
                    context_binding=_bind_context(state.declaration, expected),
                )
            )
            predecessor_states.append(state)
            validator_calls.append((state.validator_entrance, expected))
            context_calls.append((
                state.context_validator_entrance, expected,
                state.declaration, slots[-1].context_binding,
            ))
    for entrance, expected, declaration, binding in context_calls:
        _validate_original_context(entrance, source_admission, expected, declaration, binding)
    for validator, expected in validator_calls:
        if validator(source_admission, expected=expected) is not None:
            raise ContractViolation("semantic input validator must return None")
    with host._lock:
        host._check_process()
        for _entrance, expected, declaration, binding in context_calls:
            if binding is not None:
                binding.check(expected, declaration)
        if _joined_registration_state(host, joined_registration) is not joined_state:
            raise ContractViolation("joined semantic input registration changed")
        for value, slot, prior_state in zip(
            predecessors, slots, predecessor_states, strict=True
        ):
            if _registration_state(host, value.registration) is not prior_state:
                raise ContractViolation(
                    "semantic input predecessor registration changed"
                )
            key = (slot.registration, slot.expected.use_ref)
            if key in host._role_slots:
                raise ContractViolation("semantic input predecessor use already joined")
            if key in host._uses:
                raise ContractViolation("semantic input predecessor use is unavailable")
        if (joined_registration, joined_expected.use_ref) in host._joined_uses:
            raise ContractViolation("joined semantic input use is unavailable")
        if any(
            not state.consumed
            and state.operation_identity is joined_expected.operation_identity
            for state in host._role_joins.values()
        ):
            raise ContractViolation("semantic input operation already has a role join")
        role_join = AdmittedSemanticInputRoleJoin(_REGISTRATION_TOKEN)
        state = _RoleJoinState(
            joined_registration,
            joined_expected,
            source_admission,
            joined_expected.operation_identity,
            joined_expected.package_identity,
            get_ident(),
            tuple(slots),
            context_binding=joined_context,
            bind_input_digests=bool(joined_state.declaration.predecessor_stages),
        )
        host._role_joins[role_join] = state
        for index, slot in enumerate(state.slots):
            host._role_slots[(slot.registration, slot.expected.use_ref)] = (
                role_join,
                index,
            )
        return role_join


def close_semantic_input_role_join(
    host: SemanticInputProducerHost,
    role_join: AdmittedSemanticInputRoleJoin,
) -> None:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    with host._lock:
        host._check_process()
        state = _role_join_state(host, role_join)
        if state.running or state.active_predecessors:
            raise ContractViolation("semantic input role join is active")
        _consume_role_join(host, role_join, state)


async def execute_registered_semantic_input(
    host: SemanticInputProducerHost,
    registration: AdmittedSemanticInputProducerRegistration,
    *,
    source_admission: object,
    expected: SemanticInputProductionExpectation,
) -> SemanticBody:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(expected) is not SemanticInputProductionExpectation:
        raise TypeError("expected must be exact SemanticInputProductionExpectation")
    expected.__post_init__()
    key = (registration, expected.use_ref)
    role_join: AdmittedSemanticInputRoleJoin | None = None
    role_state: _RoleJoinState | None = None
    role_slot_index: int | None = None
    role_slot_completed = False
    with host._lock:
        host._check_process()
        state = _registration_state(host, registration)
        binding = host._role_slots.get(key)
        if binding is not None:
            role_join, role_slot_index = binding
            role_state = _role_join_state(host, role_join)
        use = host._uses.get(key)
        if use is None:
            use = _UseState(expected.operation_identity, expected.source_identity)
            host._uses[key] = use
        if (
            use.operation_identity is not expected.operation_identity
            or use.source_identity is not expected.source_identity
        ):
            if role_state is not None:
                assert role_join is not None
                _consume_role_join(host, role_join, role_state)
            raise ContractViolation("semantic input use identity differs")
        if use.running or use.consumed:
            if role_state is not None:
                assert role_join is not None
                _consume_role_join(host, role_join, role_state)
            raise ContractViolation("semantic input use already consumed")
        if role_state is not None:
            assert role_join is not None
            assert role_slot_index is not None
            slot = role_state.slots[role_slot_index]
            if (
                slot.expected is not expected
                or role_state.source_admission is not source_admission
                or role_state.operation_identity is not expected.operation_identity
                or role_state.package_identity != expected.package_identity
                or role_state.next_slot != role_slot_index
                or slot.result is not None
            ):
                _consume_role_join(host, role_join, role_state)
                raise ContractViolation("semantic input predecessor slot differs")
            role_state.active_predecessors += 1
        use.running = True
        state.running += 1
        producer = state.producer
        validator = state.validator_entrance
        reader = state.reader_entrance
        declaration = state.declaration
        context_validator = state.context_validator_entrance
    try:
        prepared_result = _prepare_result(state, expected)
        context_binding = _bind_context(declaration, expected)
        _validate_original_context(context_validator, source_admission, expected, declaration, context_binding)
        if validator(source_admission, expected=expected) is not None:
            raise ContractViolation("semantic input validator must return None")
        sources = reader(source_admission, expected=expected)
        if type(sources) is not tuple:
            raise TypeError("semantic input reader must return exact tuple")
        for source in sources:
            if type(source) is not SemanticInputSourceBody:
                raise TypeError("semantic input reader returned foreign body")
            source.__post_init__()
        if tuple(source.source for source in sources) != expected.source_coordinates:
            raise ContractViolation("semantic input source closure differs")
        actual_source_contracts = tuple(
            sorted(
                {
                    SemanticInputSourceContract(
                        source.source.coordinate.role,
                        source.source.coordinate.contract,
                    )
                    for source in sources
                },
                key=lambda item: item.role.encode("utf-8"),
            )
        )
        if actual_source_contracts != declaration.source_contracts:
            raise ContractViolation("semantic input source contracts differ")
        production_input = SemanticInputProductionInput(
            expected.use_ref,
            expected.operation_ref,
            expected.stage,
            expected.package_identity,
            sources,
            expected.input_digest,
            expected.context_bodies,
        )
        _validate_original_context(context_validator, source_admission, expected, declaration, context_binding, production_input)
        produced = producer(production_input)
        result = await produced if inspect.isawaitable(produced) else produced
        if type(result) is not SemanticBody:
            raise TypeError("producer must return exact SemanticBody")
        result.__post_init__()
        if (
            result.coordinate.role != declaration.result_role
            or result.coordinate.contract != declaration.result_contract
        ):
            raise ContractViolation("semantic input result declaration differs")
        if validator(source_admission, expected=expected) is not None:
            raise ContractViolation("semantic input validator must return None")
        _validate_original_context(context_validator, source_admission, expected, declaration, context_binding, production_input)
        with host._lock:
            host._check_process()
            if _registration_state(host, registration) is not state:
                raise ContractViolation("semantic input registration changed")
            current = host._uses.get(key)
            if current is None or current is not use or not current.running:
                raise ContractViolation("semantic input use changed")
            if role_state is not None:
                assert role_join is not None
                assert role_slot_index is not None
                if _role_join_state(host, role_join) is not role_state:
                    raise ContractViolation("semantic input role join changed")
                if host._role_slots.get(key) != (role_join, role_slot_index):
                    raise ContractViolation("semantic input predecessor slot changed")
                slot = role_state.slots[role_slot_index]
                if (
                    role_state.next_slot != role_slot_index
                    or slot.result is not None
                    or result.coordinate.role != slot.role
                    or result.coordinate.contract != slot.contract
                ):
                    raise ContractViolation("semantic input predecessor result differs")
                coordinate = result.coordinate
                slot.result = SemanticBody(
                    SemanticValueCoordinate(
                        coordinate.role,
                        coordinate.contract,
                        coordinate.value_ref,
                        coordinate.digest,
                        coordinate.size_bytes,
                    ),
                    memoryview(result.canonical_body).tobytes(),
                )
                role_state.next_slot += 1
            _retain_result(host, registration, state, source_admission, expected,
                           result, prepared_result, context_binding)
            if role_state is not None:
                role_slot_completed = True
        return result
    finally:
        with host._lock:
            if role_state is not None:
                role_state.active_predecessors -= 1
                if not role_slot_completed and not role_state.consumed:
                    assert role_join is not None
                    _consume_role_join(host, role_join, role_state)
            use.running = False
            use.consumed = True
            state.running -= 1


async def execute_registered_joined_semantic_input(
    host: SemanticInputProducerHost,
    registration: AdmittedSemanticInputProducerRegistration,
    *,
    role_join: AdmittedSemanticInputRoleJoin,
    source_admission: object,
    expected: SemanticInputProductionExpectation,
) -> SemanticBody:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(expected) is not SemanticInputProductionExpectation:
        raise TypeError("expected must be exact SemanticInputProductionExpectation")
    expected.__post_init__()
    key = (registration, expected.use_ref)
    with host._lock:
        host._check_process()
        state = _joined_registration_state(host, registration)
        join_state = _role_join_state(host, role_join)
        if (
            join_state.joined_registration is not registration
            or join_state.joined_expected is not expected
            or join_state.source_admission is not source_admission
            or join_state.operation_identity is not expected.operation_identity
            or join_state.package_identity != expected.package_identity
            or join_state.active_predecessors
            or join_state.running
            or join_state.next_slot != len(join_state.slots)
            or any(slot.result is None for slot in join_state.slots)
        ):
            _consume_role_join(host, role_join, join_state)
            raise ContractViolation("semantic input role join is incomplete or differs")
        use = host._joined_uses.get(key)
        if use is None:
            use = _UseState(expected.operation_identity, expected.source_identity)
            host._joined_uses[key] = use
        if (
            use.operation_identity is not expected.operation_identity
            or use.source_identity is not expected.source_identity
        ):
            _consume_role_join(host, role_join, join_state)
            raise ContractViolation("joined semantic input use identity differs")
        if use.running or use.consumed:
            _consume_role_join(host, role_join, join_state)
            raise ContractViolation("joined semantic input use already consumed")
        use.running = True
        state.running += 1
        join_state.running = True
        producer = state.producer
        validator = state.validator_entrance
        reader = state.reader_entrance
        declaration = state.declaration.ordinary
        context_validator = state.context_validator_entrance
    try:
        prepared_result = _prepare_result(state, expected)
        context_binding = _bind_context(declaration, expected)
        _validate_original_context(context_validator, source_admission, expected, declaration, context_binding)
        if validator(source_admission, expected=expected) is not None:
            raise ContractViolation("semantic input validator must return None")
        sources = reader(source_admission, expected=expected)
        if type(sources) is not tuple:
            raise TypeError("semantic input reader must return exact tuple")
        for source in sources:
            if type(source) is not SemanticInputSourceBody:
                raise TypeError("semantic input reader returned foreign body")
            source.__post_init__()
        if tuple(source.source for source in sources) != expected.source_coordinates:
            raise ContractViolation("semantic input source closure differs")
        actual_source_contracts = tuple(
            sorted(
                {
                    SemanticInputSourceContract(
                        source.source.coordinate.role,
                        source.source.coordinate.contract,
                    )
                    for source in sources
                },
                key=lambda item: item.role.encode("utf-8"),
            )
        )
        if actual_source_contracts != declaration.source_contracts:
            raise ContractViolation("semantic input source contracts differ")
        if validator(source_admission, expected=expected) is not None:
            raise ContractViolation("semantic input validator must return None")
        ordinary = SemanticInputProductionInput(
            expected.use_ref,
            expected.operation_ref,
            expected.stage,
            expected.package_identity,
            sources,
            expected.input_digest,
            expected.context_bodies,
        )
        with host._lock:
            host._check_process()
            if (
                _joined_registration_state(host, registration) is not state
                or _role_join_state(host, role_join) is not join_state
                or not join_state.running
                or join_state.next_slot != len(join_state.slots)
            ):
                raise ContractViolation("semantic input role join changed")
            for slot, contract in zip(
                join_state.slots,
                state.declaration.predecessor_contracts,
                strict=True,
            ):
                if (
                    slot.result is None
                    or slot.role != contract.role
                    or slot.contract != contract.contract
                    or slot.result.coordinate.role != contract.role
                    or slot.result.coordinate.contract != contract.contract
                ):
                    raise ContractViolation("semantic input predecessor differs")
                slot.result.__post_init__()
            predecessors = _detached_predecessors(join_state)
            closure_digest = _predecessor_closure_digest(join_state)
        joined_input = SemanticInputJoinedProductionInput(
            ordinary,
            predecessors,
            closure_digest,
            expected.operation_ref,
        )
        _validate_original_context(context_validator, source_admission, expected, declaration, context_binding, ordinary)
        produced = producer(joined_input)
        result = await produced if inspect.isawaitable(produced) else produced
        if type(result) is not SemanticBody:
            raise TypeError("producer must return exact SemanticBody")
        result.__post_init__()
        if (
            result.coordinate.role != declaration.result_role
            or result.coordinate.contract != declaration.result_contract
        ):
            raise ContractViolation("semantic input result declaration differs")
        if validator(source_admission, expected=expected) is not None:
            raise ContractViolation("semantic input validator must return None")
        _validate_original_context(context_validator, source_admission, expected, declaration, context_binding, ordinary)
        with host._lock:
            host._check_process()
            if (
                _joined_registration_state(host, registration) is not state
                or _role_join_state(host, role_join) is not join_state
                or not join_state.running
                or host._joined_uses.get(key) is not use
                or not use.running
            ):
                raise ContractViolation("joined semantic input execution changed")
            parents = ()
            if state.retain_result:
                parents = tuple(next((record for record in host._results.values()
                    if record.key[0] is slot.registration and record.expected is slot.expected), None)
                    for slot in join_state.slots)
                if any(parent is None for parent in parents):
                    raise ContractViolation("original joined predecessor result is unavailable")
            _retain_result(host, registration, state, source_admission, expected,
                           result, prepared_result, context_binding, parents)
        return result
    finally:
        with host._lock:
            if not join_state.consumed:
                _consume_role_join(host, role_join, join_state)
            join_state.running = False
            use.running = False
            use.consumed = True
            state.running -= 1


async def execute_registered_dependency_semantic_input(
    host: SemanticInputProducerHost,
    registration: AdmittedDependencySemanticInputProducerRegistration,
    *,
    resolution_admission: object,
    fulfillment_admission: object,
    expected: SemanticDependencyInputProductionExpectation,
) -> SemanticBody:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(expected) is not SemanticDependencyInputProductionExpectation:
        raise TypeError(
            "expected must be exact SemanticDependencyInputProductionExpectation"
        )
    expected.__post_init__()
    key = (registration, expected.use_ref)
    with host._lock:
        host._check_process()
        state = _dependency_registration_state(host, registration)
        use = host._dependency_uses.get(key)
        if use is None:
            use = _DependencyUseState(
                expected.operation_identity,
                expected.resolution.demand_operation_identity,
            )
            host._dependency_uses[key] = use
        if (
            use.operation_identity is not expected.operation_identity
            or use.demand_operation_identity
            is not expected.resolution.demand_operation_identity
        ):
            raise ContractViolation("dependency semantic input use identity differs")
        if use.running or use.consumed:
            raise ContractViolation("dependency semantic input use already consumed")
        use.running = True
        state.running += 1
        producer = state.producer
        resolution_validator = state.resolution_validator_entrance
        fulfillment_validator = state.fulfillment_validator_entrance
        declaration = state.declaration
    try:
        if (
            resolution_validator(resolution_admission, expected=expected.resolution)
            is not None
        ):
            raise ContractViolation("dependency resolution validator must return None")
        if (
            fulfillment_validator(
                fulfillment_admission,
                resolution_admission=resolution_admission,
                expected=expected.fulfillment,
            )
            is not None
        ):
            raise ContractViolation("dependency fulfillment validator must return None")
        products = decode_dependency_product_input(
            encode_dependency_product_input(expected.fulfillment.dependency_products)
        )
        actual_contracts = tuple(
            sorted(
                {
                    SemanticInputDependencyContract(
                        product.body.coordinate.role,
                        product.body.coordinate.contract,
                    )
                    for product in products.products
                },
                key=lambda item: item.role.encode("utf-8"),
            )
        )
        if actual_contracts != declaration.dependency_contracts:
            raise ContractViolation("semantic input dependency contracts differ")
        production_input = SemanticDependencyInputProductionInput(
            expected.use_ref,
            expected.operation_ref,
            expected.stage,
            products,
            expected.input_digest,
        )
        produced = producer(production_input)
        result = await produced if inspect.isawaitable(produced) else produced
        if type(result) is not SemanticBody:
            raise TypeError("producer must return exact SemanticBody")
        result.__post_init__()
        if (
            result.coordinate.role != declaration.result_role
            or result.coordinate.contract != declaration.result_contract
        ):
            raise ContractViolation("semantic input result declaration differs")
        if (
            resolution_validator(resolution_admission, expected=expected.resolution)
            is not None
        ):
            raise ContractViolation("dependency resolution validator must return None")
        if (
            fulfillment_validator(
                fulfillment_admission,
                resolution_admission=resolution_admission,
                expected=expected.fulfillment,
            )
            is not None
        ):
            raise ContractViolation("dependency fulfillment validator must return None")
        with host._lock:
            host._check_process()
            if _dependency_registration_state(host, registration) is not state:
                raise ContractViolation(
                    "dependency semantic input registration changed"
                )
            current = host._dependency_uses.get(key)
            if current is None or current is not use or not current.running:
                raise ContractViolation("dependency semantic input use changed")
        return result
    finally:
        with host._lock:
            use.running = False
            use.consumed = True
            state.running -= 1


def close_semantic_input_producer_registration(
    host: SemanticInputProducerHost,
    registration: AdmittedSemanticInputProducerRegistration,
) -> None:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    if type(registration) is not AdmittedSemanticInputProducerRegistration:
        raise TypeError("registration must be exact")
    with host._lock:
        host._check_process()
        state = host._registrations.get(registration)
        joined_state = host._joined_registrations.get(registration)
        if state is None and joined_state is None:
            raise ContractViolation("semantic input registration is unavailable")
        selected = state if state is not None else joined_state
        assert selected is not None
        if selected.closed:
            raise ContractViolation("semantic input registration is unavailable")
        if registration._token is not _REGISTRATION_TOKEN:
            raise ContractViolation("semantic input registration is unavailable")
        if selected.running:
            raise ContractViolation("semantic input execution is active")
        for role_join, role_state in tuple(host._role_joins.items()):
            if role_state.consumed:
                continue
            if role_state.joined_registration is registration or any(
                slot.registration is registration for slot in role_state.slots
            ):
                if role_state.running or role_state.active_predecessors:
                    raise ContractViolation("semantic input role join is active")
                _consume_role_join(host, role_join, role_state)
        selected.closed = True
        for record in tuple(host._results.values()):
            if record.key[0] is registration:
                _retire_result(host, record)


def close_dependency_semantic_input_producer_registration(
    host: SemanticInputProducerHost,
    registration: AdmittedDependencySemanticInputProducerRegistration,
) -> None:
    if type(host) is not SemanticInputProducerHost:
        raise TypeError("host must be exact SemanticInputProducerHost")
    with host._lock:
        host._check_process()
        state = _dependency_registration_state(host, registration)
        if state.running:
            raise ContractViolation("dependency semantic input execution is active")
        state.closed = True


__all__ = [
    "validate_registered_semantic_input_result",
    "read_registered_semantic_input_source_selection",
    "release_registered_semantic_input_result",
    "AdmittedDependencySemanticInputProducerRegistration",
    "AdmittedSemanticInputRoleJoin",
    "AdmittedSemanticInputProducerRegistration",
    "SemanticDependencyInputProducerDeclaration",
    "SemanticDependencyInputProductionExpectation",
    "SemanticDependencyInputProductionInput",
    "SemanticInputDependencyContract",
    "SemanticInputContextContract",
    "SemanticInputContextValidator",
    "SemanticInputJoinedProducerDeclaration",
    "SemanticInputJoinedProductionInput",
    "SemanticInputPredecessorBody",
    "SemanticInputProducerDeclaration",
    "SemanticInputProducerHost",
    "SemanticInputPackageIdentity",
    "SemanticInputProductionInput",
    "SemanticInputProductionExpectation",
    "SemanticInputRoleJoinPredecessor",
    "SemanticInputSourceBody",
    "SemanticInputSourceContract",
    "SemanticInputSourceCoordinate",
    "SemanticInputSourceReader",
    "SemanticInputSourceValidator",
    "close_dependency_semantic_input_producer_registration",
    "close_semantic_input_role_join",
    "close_semantic_input_producer_registration",
    "execute_registered_dependency_semantic_input",
    "execute_registered_joined_semantic_input",
    "execute_registered_semantic_input",
    "register_dependency_semantic_input_producer",
    "register_joined_semantic_input_producer",
    "register_semantic_input_producer",
]
