"""Process-local authority for an exact profile-selected provider execution.

The values in this module are deliberately nonportable.  Portable provider
coordinates describe an implementation; they do not prove which live Python
object will execute.  A registration joins those two facts for one Code
runtime, and each execution admission binds one freshly admitted
``ProviderStepInvocation`` before calling the retained entrance.
"""

from __future__ import annotations

import builtins as _python_builtins
import dataclasses
import enum
import inspect
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock, Thread, current_thread, get_ident
from time import perf_counter_ns
from types import (
    FrameType,
    FunctionType,
    MemberDescriptorType,
    MethodType,
    ModuleType,
    TracebackType,
)
from typing import TYPE_CHECKING, Any, cast
from weakref import ReferenceType, WeakKeyDictionary, ref

from .contracts import (
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticContractInvocation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    canonical_json_bytes,
)
from .private_stage_contract import PrivateStageRoleContract
from .profile import SemanticContractProfileDeclaration
from .runtime import (
    AdmittedSemanticValue,
    BoundSemanticInput,
    ProviderStepInvocation,
    SemanticBody,
    SemanticContractProvider,
)

if TYPE_CHECKING:
    from .private_stage_contract import CodePrivateStagePlanV1
    from .product_contribution import SelectedProviderProductContribution
    from .runtime import SemanticContractRuntime
    from .stage_contribution import SelectedProviderStageContribution


_REGISTRATION_TOKEN = object()
_FACTORY_TOKEN = object()
_SELECTION_ROOT_TOKEN = object()
_EXECUTION_TOKEN = object()
_PROBE_TOKEN = object()
_QUALIFICATION_SESSION_TOKEN = object()
_QUALIFICATION_PHASE_TOKEN = object()
_MAX_SEQUENCE = (1 << 64) - 1


@dataclass(frozen=True, slots=True)
class SelectedProviderInvocationClosure:
    """Complete portable input supplied to Code before nominal admission."""

    invocation: SemanticContractInvocation
    input_bodies: tuple[SemanticBody, ...]
    predecessor_body: SemanticBody | None = None
    input_values: tuple[object, ...] | None = None

    def __post_init__(self) -> None:
        if type(self.invocation) is not SemanticContractInvocation:
            raise TypeError("selected invocation must be exact")
        self.invocation.to_wire()
        if type(self.input_bodies) is not tuple or any(
            type(item) is not SemanticBody for item in self.input_bodies
        ):
            raise TypeError("selected input bodies must be an exact SemanticBody tuple")
        for body in self.input_bodies:
            body.__post_init__()
        if (
            tuple(item.coordinate for item in self.input_bodies)
            != self.invocation.inputs
        ):
            raise ContractViolation(
                "selected input body order differs from invocation coordinates"
            )
        if self.predecessor_body is not None:
            if type(self.predecessor_body) is not SemanticBody:
                raise TypeError("selected predecessor body must be exact or absent")
            self.predecessor_body.__post_init__()
        if self.input_values is not None and (
            type(self.input_values) is not tuple
            or len(self.input_values) != len(self.input_bodies)
        ):
            raise TypeError("selected input values must align as an exact tuple")


class AdmittedSemanticProviderSelectionRoot:
    """One-shot nominal result of an exact domain provider factory."""

    __slots__ = (
        "__weakref__",  # pyright: ignore[reportUninitializedInstanceVariable]
        "_token",
    )

    def __init__(self, token: object) -> None:
        if token is not _SELECTION_ROOT_TOKEN:
            raise TypeError("provider selection root is Code-issued only")
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("provider selection root cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("provider selection root cannot be copied")


class _AdmittedSemanticProviderFactory:
    """Private nominal binding for one domain-owned zero-argument factory."""

    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _FACTORY_TOKEN:
            raise TypeError("selected-provider factory is Code-issued only")
        self._token = token


class AdmittedSemanticProviderRegistration:
    __slots__ = (
        "__weakref__",  # pyright: ignore[reportUninitializedInstanceVariable]
        "_token",
    )

    def __init__(self, token: object) -> None:
        if token is not _REGISTRATION_TOKEN:
            raise TypeError("provider registration is Code-runtime-issued only")
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("provider registration cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("provider registration cannot be copied")


class SelectedSemanticProviderExecutionAdmission:
    __slots__ = (
        "__weakref__",  # pyright: ignore[reportUninitializedInstanceVariable]
        "_issue_timings_ns",
        "_timings_ns",
        "_token",
    )

    def __init__(self, token: object) -> None:
        if token is not _EXECUTION_TOKEN:
            raise TypeError("provider execution admission is Code-runtime-issued only")
        self._token = token
        self._issue_timings_ns: tuple[tuple[str, int], ...] = ()
        self._timings_ns: tuple[tuple[str, int], ...] = ()

    def __copy__(self) -> None:
        raise TypeError("provider execution admission cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("provider execution admission cannot be copied")


class SelectedInvocationUse:
    """Code-issued attribution of one original tracked invocation; never a wire."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("selected invocation use is Code-issued only")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("selected invocation use is sealed")

    def __copy__(self):
        raise TypeError("selected invocation use cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("selected invocation use cannot be copied")

    def __reduce__(self):
        raise TypeError("selected invocation use cannot be serialized")


@dataclass(frozen=True, slots=True)
class SelectedInvocationEvidence:
    """Read-only projection. Only the original use verifier grants attribution."""

    runtime: object
    registration: AdmittedSemanticProviderRegistration
    provider: object
    admission: SelectedSemanticProviderExecutionAdmission
    semantic_input: object
    closure: SelectedProviderInvocationClosure
    step_invocation: ProviderStepInvocation
    sequence: int
    phase: str
    completion: object | None
    terminal_success: bool


class SelectedSemanticProviderProbe:
    """Exact Code-owned callable used by a semantic preparation owner."""

    __slots__ = ("_last_timings_ns", "_registration", "_runtime", "_token")

    def __init__(
        self,
        token: object,
        runtime: SemanticContractRuntime,
        registration: AdmittedSemanticProviderRegistration,
    ) -> None:
        if token is not _PROBE_TOKEN:
            raise TypeError("selected provider probe is Code-runtime-issued only")
        self._token = token
        self._runtime = runtime
        self._registration = registration
        self._last_timings_ns: tuple[tuple[str, int], ...] = ()

    def __call__(self, semantic_input: object) -> Any:
        return _execute_probe(self, semantic_input)

    def close(self) -> None:
        state = _probe_state(self)
        close_selected_provider_registration(state.runtime, state.registration)

    @property
    def last_timings_ns(self) -> tuple[tuple[str, int], ...]:
        return self._last_timings_ns

    def __copy__(self) -> None:
        raise TypeError("selected provider probe cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("selected provider probe cannot be copied")


class _SelectedProviderQualificationSession:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _QUALIFICATION_SESSION_TOKEN:
            raise TypeError("provider qualification session is Code-issued only")
        self._token = token


class _SelectedProviderQualificationPhaseBinding:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _QUALIFICATION_PHASE_TOKEN:
            raise TypeError("provider qualification binding is Code-issued only")
        self._token = token


@dataclass(frozen=True, slots=True)
class _ProviderOperationWitness:
    sequence: int
    invocation_digest: str
    input_closure_digest: str
    input_coordinates: tuple[tuple[str, str, str, str, str, str, int], ...]


@dataclass(frozen=True, slots=True)
class _SelectedProviderFactoryProduct:
    """Exact result returned only by a retained domain selection factory."""

    runtime: SemanticContractRuntime
    provider: SemanticContractProvider
    binding: ProviderExecutionBinding
    executable_entrance: Callable[[ProviderStepInvocation, object], object]
    input_closure_entrance: Callable[[object], SelectedProviderInvocationClosure]
    semantic_implementation_contract_body: bytes
    configuration_body: bytes
    catalog_contribution_producer: (
        Callable[[SelectedProviderProductContribution], object] | None
    ) = None
    private_stage_plan_producer: (
        Callable[[SelectedProviderProductContribution], CodePrivateStagePlanV1] | None
    ) = None
    private_stage_predecessor_port: Callable[..., object] | None = None
    private_stage_predecessor_input: PrivateStageRoleContract | None = None
    selected_invocation_observer: Callable[[str, SelectedInvocationUse], None] | None = None


_PREDECESSOR_INPUT_SLOTS = tuple(
    (cls, name, inspect.getattr_static(cls, name))
    for cls, names in (
        (PrivateStageRoleContract, ("role", "contract")),
        (SemanticContractRef, ("key", "version", "schema_digest")),
        (ContentDigest, ("value",)),
    )
    for name in names
)


def _predecessor_input_identity(binding: PrivateStageRoleContract) -> tuple[object, ...]:
    """Closed, strong identity/scalar snapshot; safe under parent exclusion."""
    if type(binding) is not PrivateStageRoleContract or any(
        inspect.getattr_static(cls, name) is not descriptor
        for cls, name, descriptor in _PREDECESSOR_INPUT_SLOTS
    ):
        raise ContractViolation("original predecessor input descriptors changed")
    role = object.__getattribute__(binding, "role")
    contract = object.__getattribute__(binding, "contract")
    if type(role) is not str or type(contract) is not SemanticContractRef:
        raise ContractViolation("exact predecessor input role/contract required")
    key = object.__getattribute__(contract, "key")
    version = object.__getattribute__(contract, "version")
    digest = object.__getattribute__(contract, "schema_digest")
    if type(key) is not str or type(version) is not str or type(digest) is not ContentDigest:
        raise ContractViolation("exact predecessor input contract required")
    digest_value = object.__getattribute__(digest, "value")
    if type(digest_value) is not str:
        raise ContractViolation("exact predecessor input digest required")
    return binding, contract, digest, role, key, version, digest_value


def _predecessor_input_identity_matches(binding, snapshot) -> bool:
    if type(snapshot) is not tuple or len(snapshot) != 7:
        return False
    current = _predecessor_input_identity(binding)
    return (
        all(current[index] is snapshot[index] for index in range(3))
        and all(type(snapshot[index]) is str and current[index] == snapshot[index]
                for index in range(3, 7))
    )


@dataclass(frozen=True, slots=True)
class _FactoryState:
    creator_pid: int
    factory_ref: str
    provider_key: str
    selection_factory: Callable[
        [], _SelectedProviderFactoryProduct | SelectedProviderStageFactoryProduct
    ]
    selection_factory_function: object


@dataclass(frozen=True, slots=True)
class SelectedProviderStageFactoryProduct:
    """Non-authoritative ordered owner products; only factory acquisition admits them."""

    source_planning: _SelectedProviderFactoryProduct
    authority_derivation: _SelectedProviderFactoryProduct
    catalog_contribution_producer: (
        Callable[[SelectedProviderStageContribution], object] | None
    ) = None

    def __post_init__(self) -> None:
        if any(
            type(item) is not _SelectedProviderFactoryProduct
            for item in (self.source_planning, self.authority_derivation)
        ):
            raise TypeError("stage factory products must be exact")
        if self.source_planning.runtime is self.authority_derivation.runtime:
            raise ContractViolation("stage factory runtimes must be distinct")
        if self.source_planning.provider is self.authority_derivation.provider:
            raise ContractViolation("stage factory providers must be distinct")
        producer = self.catalog_contribution_producer
        if producer is not None:
            if not inspect.isfunction(producer):
                raise TypeError("stage catalog producer must be an exact function")
            parameters = tuple(inspect.signature(producer).parameters.values())
            if (
                len(parameters) != 1
                or parameters[0].kind
                not in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
                or parameters[0].default is not inspect.Parameter.empty
            ):
                raise TypeError("stage catalog producer must take one original pair")


@dataclass(slots=True)
class _SelectionRootState:
    factory_admission: _AdmittedSemanticProviderFactory
    runtime: SemanticContractRuntime
    runtime_token: object
    creator_pid: int
    selection_factory: object
    provider_type: type[object]
    profile_bytes: bytes
    provider_key: str
    declaration_bytes: bytes
    binding_bytes: bytes
    provider: SemanticContractProvider
    executable_entrance: Callable[[ProviderStepInvocation, object], object]
    input_closure_entrance: Callable[[object], SelectedProviderInvocationClosure]
    executable_function: object
    input_closure_function: object
    semantic_implementation_contract_body: bytes
    configuration_body: bytes
    private_stage_predecessor_port: object
    private_stage_predecessor_function: object
    private_stage_predecessor_input: PrivateStageRoleContract | None
    private_stage_predecessor_input_bytes: bytes | None
    private_stage_predecessor_input_identity: tuple[object, ...] | None
    selected_invocation_observer: Any
    selected_invocation_observer_identity: Any
    consumed: bool = False


@dataclass(slots=True)
class _RegistrationState:
    selection_root: AdmittedSemanticProviderSelectionRoot
    runtime: SemanticContractRuntime
    runtime_token: object
    creator_pid: int
    profile_bytes: bytes
    provider_key: str
    declaration_bytes: bytes
    binding_bytes: bytes
    provider: SemanticContractProvider
    executable_entrance: Callable[[ProviderStepInvocation, object], object]
    input_closure_entrance: Callable[[object], SelectedProviderInvocationClosure]
    executable_function: object
    input_closure_function: object
    semantic_implementation_contract_body: bytes
    configuration_body: bytes
    private_stage_predecessor_port: object
    private_stage_predecessor_function: object
    private_stage_predecessor_input: PrivateStageRoleContract | None
    private_stage_predecessor_input_bytes: bytes | None
    private_stage_predecessor_input_identity: tuple[object, ...] | None
    selected_invocation_observer: Any
    selected_invocation_observer_identity: Any
    sequence: int = 0
    probe_issued: bool = False
    witnesses: list[_ProviderOperationWitness] | None = None
    closed: bool = False
    execution_lifecycle: Any = None
    execution_started: bool = False


@dataclass(frozen=True, slots=True)
class _ProbeState:
    runtime: SemanticContractRuntime
    registration: AdmittedSemanticProviderRegistration
    creator_pid: int


@dataclass(slots=True)
class _QualificationSessionState:
    probe: SelectedSemanticProviderProbe
    registration: AdmittedSemanticProviderRegistration
    selection_root: AdmittedSemanticProviderSelectionRoot
    runtime: SemanticContractRuntime
    creator_pid: int
    creator_thread: int
    next_phase_index: int = 0
    active_phase: _SelectedProviderQualificationPhaseBinding | None = None
    completed_bindings: list[_SelectedProviderQualificationPhaseBinding] | None = None
    closed: bool = False


@dataclass(slots=True)
class _QualificationPhaseState:
    session: _SelectedProviderQualificationSession
    phase: str
    phase_index: int
    start_witness_index: int
    expected_operation_count: int
    witnesses: tuple[_ProviderOperationWitness, ...] = ()
    lifecycle: str = "active"


@dataclass(slots=True)
class _ExecutionState:
    registration: AdmittedSemanticProviderRegistration
    sequence: int
    creator_pid: int
    runtime_token: object
    semantic_input: object
    closure: SelectedProviderInvocationClosure
    step_invocation: ProviderStepInvocation
    invocation_bytes: bytes
    input_evidence: tuple[tuple[bytes, bytes], ...]
    predecessor_evidence: tuple[bytes, bytes] | None
    dependency_bytes: bytes
    closure_body: bytes
    primitive_snapshot: _PrimitiveSnapshot
    step_guard: tuple[object, ...]
    observed_use: SelectedInvocationUse | None = None
    lifecycle_use: Any = None
    uninterrupted_probe_execution: bool = False
    lifecycle: str = "active"
    terminal_started: bool = False
    terminal_derivation: object = None
    terminal_thread: int | None = None


@dataclass(frozen=True, slots=True)
class _PrimitiveSchema:
    value_type: type[object]
    descriptors: tuple[MemberDescriptorType, ...]
    enum_members: tuple[enum.Enum, ...]


@dataclass(frozen=True, slots=True)
class _PrimitiveIdentityGraph:
    values: tuple[object, ...]
    node_count: int
    scalar_bytes: int


@dataclass(frozen=True, slots=True)
class _PrimitiveSnapshot:
    root: object
    schemas: tuple[_PrimitiveSchema, ...]
    module_globals: dict[str, object]
    descriptor_get: Callable[..., object]
    encoder: Callable[..., object]
    matcher: Callable[..., bool]
    absent_builtin_names: tuple[str, ...]
    present_bindings: tuple[tuple[str, object], ...]
    dict_contains: Callable[..., object]
    dict_getitem: Callable[..., object]


_LOCK = RLock()
_FACTORIES: dict[int, tuple[_AdmittedSemanticProviderFactory, _FactoryState]] = {}
_FACTORY_PROVIDER_KEYS: dict[str, _AdmittedSemanticProviderFactory] = {}
_FACTORY_REFS: dict[str, _AdmittedSemanticProviderFactory] = {}
_SELECTION_ROOTS: dict[
    int, tuple[AdmittedSemanticProviderSelectionRoot, _SelectionRootState]
] = {}
_REGISTRATIONS: dict[
    int, tuple[AdmittedSemanticProviderRegistration, _RegistrationState]
] = {}
_PROBES: dict[int, tuple[SelectedSemanticProviderProbe, _ProbeState]] = {}
_EXECUTIONS: dict[
    int, tuple[SelectedSemanticProviderExecutionAdmission, _ExecutionState]
] = {}
_TERMINAL_EXECUTIONS: WeakKeyDictionary[
    SelectedSemanticProviderExecutionAdmission, str
] = WeakKeyDictionary()
_UNINTERRUPTED_PROBE_TOKEN = object()
_QUALIFICATION_SESSIONS: dict[
    int, tuple[_SelectedProviderQualificationSession, _QualificationSessionState]
] = {}
_QUALIFICATION_PHASES: dict[
    int, tuple[_SelectedProviderQualificationPhaseBinding, _QualificationPhaseState]
] = {}
_MEMBER_DESCRIPTOR_GET = MemberDescriptorType.__get__
_RETAINED_MEMBER_DESCRIPTOR_GET = _MEMBER_DESCRIPTOR_GET
_SELECTED_PROVIDER_MODULE_GLOBALS: dict[str, object] = globals()
_RETAINED_DICT_CONTAINS = dict.__contains__
_RETAINED_DICT_GETITEM = dict.__getitem__
_PRIMITIVE_VERIFIER_ABSENT_BUILTIN_NAMES = tuple(
    name
    for name in vars(_python_builtins)
    if name not in _SELECTED_PROVIDER_MODULE_GLOBALS
)
def _primitive_schema_index(
    schemas: list[_PrimitiveSchema], value_type: type[object]
) -> int | None:
    for index, schema in enumerate(schemas):
        if schema.value_type is value_type:
            return index
    return None


def _capture_flat_primitive_graph(
    value: object,
    schemas: list[_PrimitiveSchema],
    *,
    allow_new: bool,
    descriptor_get: Callable[..., object],
) -> _PrimitiveIdentityGraph:
    """Capture one admitted graph as one compact exact identity stream."""

    values: list[object] = []
    scalar_bytes = 0
    memo: set[int] = set()
    pending: list[object] = [value]
    while pending:
        item = pending.pop()
        values.append(item)
        item_type = type(item)
        if item_type is str:
            scalar_bytes += len(cast(str, item).encode("utf-8"))
        elif item_type is int:
            scalar_bytes += max(1, (cast(int, item).bit_length() + 8) // 8)
        elif item_type is bool:
            scalar_bytes += 1
        elif item_type is float:
            scalar_bytes += 8
        elif item_type is bytes:
            scalar_bytes += len(cast(bytes, item))
        elif item_type is object:
            scalar_bytes += 8
        if (
            item is None
            or item_type is str
            or item_type is int
            or item_type is bool
            or item_type is float
            or item_type is bytes
            or item_type is object
        ):
            continue
        identity = id(item)
        if identity in memo:
            continue
        memo.add(identity)
        if item_type is tuple or item_type is list:
            pending.extend(reversed(cast(tuple[object, ...] | list[object], item)))
            continue
        if item_type is dict:
            mapping = cast(dict[object, object], item)
            for key, child in reversed(tuple(dict.items(mapping))):
                pending.extend((child, key))
            continue
        schema_index = _primitive_schema_index(schemas, item_type)
        if schema_index is None:
            if not allow_new:
                raise TypeError("selected-provider graph type changed")
            if any(
                base is enum.Enum
                for base in type.__getattribute__(item_type, "__mro__")
            ):
                member_map = type.__getattribute__(item_type, "_member_map_")
                if type(member_map) is not dict:
                    raise TypeError("selected-provider enum map must be exact")
                members = tuple(
                    cast(enum.Enum, member) for member in dict.values(member_map)
                )
                if any(type(member) is not item_type for member in members):
                    raise TypeError("selected-provider enum member must be exact")
                schemas.append(_PrimitiveSchema(item_type, (), members))
            else:
                schema_fields = tuple(dataclasses.fields(cast(Any, item)))
                schemas.append(
                    _PrimitiveSchema(
                        item_type,
                        tuple(
                            _slot_descriptor(item_type, field.name)
                            for field in schema_fields
                        ),
                        (),
                    )
                )
            schema_index = len(schemas) - 1
        schema = schemas[schema_index]
        if schema.enum_members:
            if not any(item is member for member in schema.enum_members):
                raise TypeError("selected-provider enum member identity changed")
            enum_value = object.__getattribute__(item, "_value_")
            pending.append(enum_value)
            continue
        for descriptor in reversed(schema.descriptors):
            pending.append(descriptor_get(descriptor, item, schema.value_type))
    return _PrimitiveIdentityGraph(tuple(values), len(values), scalar_bytes)


def _flat_primitive_graph_matches(
    value: object,
    expected: object,
    schemas: tuple[_PrimitiveSchema, ...],
    *,
    descriptor_get: Callable[..., object],
) -> bool:
    """Match a graph against direct admitted identity/field records."""

    if type(expected) is not _PrimitiveIdentityGraph:
        return False

    expected_values = iter(expected.values)
    schema_by_type_id = {
        id(schema.value_type): schema for schema in schemas
    }
    seen: set[int] = set()
    pending: list[object] = [value]
    try:
        while pending:
            item = pending.pop()
            if item is not next(expected_values):
                return False
            item_type = type(item)
            if (
                item is None
                or item_type is str
                or item_type is int
                or item_type is bool
                or item_type is float
                or item_type is bytes
                or item_type is object
            ):
                continue
            identity = id(item)
            if identity in seen:
                continue
            seen.add(identity)
            if item_type is tuple or item_type is list:
                pending.extend(
                    reversed(cast(tuple[object, ...] | list[object], item))
                )
                continue
            if item_type is dict:
                mapping = cast(dict[object, object], item)
                for key in reversed(mapping):
                    pending.append(mapping[key])
                    pending.append(key)
                continue
            schema = schema_by_type_id.get(id(item_type))
            if schema is None or schema.value_type is not item_type:
                return False
            if schema.enum_members:
                if not any(item is member for member in schema.enum_members):
                    return False
                pending.append(object.__getattribute__(item, "_value_"))
                continue
            for descriptor in reversed(schema.descriptors):
                pending.append(descriptor_get(descriptor, item, schema.value_type))
        next(expected_values)
    except StopIteration:
        return not pending
    return False


def _encode_primitive_graph(
    value: object,
    schemas: list[_PrimitiveSchema],
    *,
    allow_new: bool,
    descriptor_get: Callable[..., object],
) -> bytes:
    output = bytearray()
    active: set[int] = set()
    memo: dict[int, int] = {}
    schema_by_type_id = {
        id(schema.value_type): (index, schema) for index, schema in enumerate(schemas)
    }

    def unsigned(number: int) -> None:
        while number >= 0x80:
            output.append((number & 0x7F) | 0x80)
            number >>= 7
        output.append(number)

    def scalar(tag: int, body: bytes) -> None:
        output.append(tag)
        unsigned(len(body))
        output.extend(body)

    def visit(item: object) -> None:
        item_type = type(item)
        if item is None:
            output.append(0)
            return
        if item_type is str:
            scalar(1, cast(str, item).encode("utf-8"))
            return
        if item_type is int:
            scalar(2, str(item).encode("ascii"))
            return
        if item_type is bool:
            output.append(3 if item else 4)
            return
        if item_type is float:
            scalar(5, cast(float, item).hex().encode("ascii"))
            return
        if item_type is bytes:
            scalar(6, cast(bytes, item))
            return
        if item_type is object:
            scalar(7, str(id(item)).encode("ascii"))
            return
        identity = id(item)
        if identity in active:
            raise TypeError("selected-provider admitted graph must be acyclic")
        retained_index = memo.get(identity)
        if retained_index is not None:
            output.append(8)
            unsigned(retained_index)
            return
        memo[identity] = len(memo)
        active.add(identity)
        try:
            if item_type is tuple or item_type is list:
                output.append(9 if item_type is tuple else 10)
                values = cast(tuple[object, ...] | list[object], item)
                unsigned(len(values))
                for child in values:
                    visit(child)
                return
            if item_type is dict:
                output.append(11)
                values = cast(dict[object, object], item)
                unsigned(len(values))
                for key, child in dict.items(values):
                    visit(key)
                    visit(child)
                return
            schema_entry = schema_by_type_id.get(id(item_type))
            if schema_entry is not None and schema_entry[1].value_type is not item_type:
                schema_entry = None
            if schema_entry is None:
                if not allow_new:
                    raise TypeError("selected-provider graph type changed")
                if any(
                    base is enum.Enum
                    for base in type.__getattribute__(item_type, "__mro__")
                ):
                    member_map = type.__getattribute__(item_type, "_member_map_")
                    if type(member_map) is not dict:
                        raise TypeError("selected-provider enum map must be exact")
                    members = tuple(
                        cast(enum.Enum, member) for member in dict.values(member_map)
                    )
                    if any(type(member) is not item_type for member in members):
                        raise TypeError("selected-provider enum member must be exact")
                    schema = _PrimitiveSchema(item_type, (), members)
                else:
                    fields = tuple(dataclasses.fields(cast(Any, item)))
                    schema = _PrimitiveSchema(
                        item_type,
                        tuple(
                            _slot_descriptor(item_type, field.name) for field in fields
                        ),
                        (),
                    )
                schemas.append(schema)
                schema_index = len(schemas) - 1
                schema_by_type_id[id(item_type)] = (schema_index, schema)
            else:
                schema_index, schema = schema_entry
            if schema.enum_members:
                if not any(item is member for member in schema.enum_members):
                    raise TypeError("selected-provider enum member identity changed")
                output.append(12)
                unsigned(schema_index)
                visit(object.__getattribute__(item, "_value_"))
                return
            output.append(13)
            unsigned(schema_index)
            unsigned(len(schema.descriptors))
            for descriptor in schema.descriptors:
                visit(descriptor_get(descriptor, item, schema.value_type))
        finally:
            active.remove(identity)

    visit(value)
    return bytes(output)


def _slot_descriptor(value_type: type[object], field_name: str) -> MemberDescriptorType:
    for base in type.__getattribute__(value_type, "__mro__"):
        descriptor = type.__getattribute__(base, "__dict__").get(field_name)
        if type(descriptor) is MemberDescriptorType:
            return cast(MemberDescriptorType, descriptor)
    raise TypeError("admitted value field lacks an exact slot descriptor")


def _capture_primitive_node(
    value: object,
    schemas: list[_PrimitiveSchema],
    active: set[int],
    memo: dict[int, int],
    *,
    allow_new: bool,
    descriptor_get: Callable[..., object],
) -> object:
    value_type = type(value)
    if value is None:
        return (0,)
    if value_type is str:
        return (1, value)
    if value_type is int:
        return (2, value)
    if value_type is bool:
        return (3, value)
    if value_type is float:
        return (4, value)
    if value_type is bytes:
        return (5, value)
    if value_type is object:
        return (11, id(value))
    identity = id(value)
    if identity in active:
        raise TypeError("selected-provider admitted graph must be acyclic")
    retained_index = memo.get(identity)
    if retained_index is not None:
        return (12, retained_index)
    memo[identity] = len(memo)
    active.add(identity)
    try:
        if value_type is tuple:
            return (
                6,
                tuple(
                    _capture_primitive_node(
                        item,
                        schemas,
                        active,
                        memo,
                        allow_new=allow_new,
                        descriptor_get=descriptor_get,
                    )
                    for item in cast(tuple[object, ...], value)
                ),
            )
        if value_type is list:
            return (
                7,
                tuple(
                    _capture_primitive_node(
                        item,
                        schemas,
                        active,
                        memo,
                        allow_new=allow_new,
                        descriptor_get=descriptor_get,
                    )
                    for item in cast(list[object], value)
                ),
            )
        if value_type is dict:
            return (
                8,
                tuple(
                    (
                        _capture_primitive_node(
                            key,
                            schemas,
                            active,
                            memo,
                            allow_new=allow_new,
                            descriptor_get=descriptor_get,
                        ),
                        _capture_primitive_node(
                            item,
                            schemas,
                            active,
                            memo,
                            allow_new=allow_new,
                            descriptor_get=descriptor_get,
                        ),
                    )
                    for key, item in dict.items(cast(dict[object, object], value))
                ),
            )
        schema_index = _primitive_schema_index(schemas, value_type)
        if schema_index is None:
            if not allow_new:
                raise TypeError("selected-provider graph type changed")
            if any(
                base is enum.Enum
                for base in type.__getattribute__(value_type, "__mro__")
            ):
                member_map = type.__getattribute__(value_type, "_member_map_")
                if type(member_map) is not dict:
                    raise TypeError("selected-provider enum map must be exact")
                members = tuple(
                    cast(enum.Enum, item) for item in dict.values(member_map)
                )
                if any(type(item) is not value_type for item in members):
                    raise TypeError("selected-provider enum member must be exact")
                schemas.append(_PrimitiveSchema(value_type, (), members))
            else:
                fields = tuple(dataclasses.fields(cast(Any, value)))
                schemas.append(
                    _PrimitiveSchema(
                        value_type,
                        tuple(
                            _slot_descriptor(value_type, item.name) for item in fields
                        ),
                        (),
                    )
                )
            schema_index = len(schemas) - 1
        schema = schemas[schema_index]
        if schema.enum_members:
            if not any(value is member for member in schema.enum_members):
                raise TypeError("selected-provider enum member identity changed")
            return (
                9,
                schema_index,
                _capture_primitive_node(
                    object.__getattribute__(value, "_value_"),
                    schemas,
                    active,
                    memo,
                    allow_new=allow_new,
                    descriptor_get=descriptor_get,
                ),
            )
        return (
            10,
            schema_index,
            tuple(
                _capture_primitive_node(
                    descriptor_get(descriptor, value, schema.value_type),
                    schemas,
                    active,
                    memo,
                    allow_new=allow_new,
                    descriptor_get=descriptor_get,
                )
                for descriptor in schema.descriptors
            ),
        )
    finally:
        active.remove(identity)


def _primitive_node_matches(
    value: object,
    expected: object,
    schemas: tuple[_PrimitiveSchema, ...],
    *,
    descriptor_get: Callable[..., object],
) -> bool:
    """Compare a live graph with one positional snapshot without rebuilding it."""

    seen: dict[int, int] = {}
    active: set[int] = set()
    def visit(item: object, node: object) -> bool:
        if type(node) is not tuple or not node:
            return False
        values = cast(tuple[object, ...], node)
        tag = values[0]
        item_type = type(item)
        if tag == 0:
            return len(values) == 1 and item is None
        if tag == 1:
            return len(values) == 2 and item_type is str and item == values[1]
        if tag == 2:
            return len(values) == 2 and item_type is int and item == values[1]
        if tag == 3:
            return len(values) == 2 and item_type is bool and item is values[1]
        if tag == 4:
            return (
                len(values) == 2
                and item_type is float
                and cast(float, item).hex() == cast(float, values[1]).hex()
            )
        if tag == 5:
            return len(values) == 2 and item_type is bytes and item == values[1]
        if tag == 11:
            return len(values) == 2 and item_type is object and id(item) == values[1]

        identity = id(item)
        if tag == 12:
            return len(values) == 2 and seen.get(identity) == values[1]
        if identity in seen or identity in active:
            return False
        seen[identity] = len(seen)
        active.add(identity)
        try:
            if tag in (6, 7):
                expected_type = tuple if tag == 6 else list
                if item_type is not expected_type or len(values) != 2:
                    return False
                children = values[1]
                if type(children) is not tuple:
                    return False
                items = cast(tuple[object, ...] | list[object], item)
                return len(items) == len(children) and all(
                    visit(child, child_node)
                    for child, child_node in zip(items, children, strict=True)
                )
            if tag == 8:
                if item_type is not dict or len(values) != 2:
                    return False
                entries = values[1]
                if type(entries) is not tuple:
                    return False
                items = tuple(dict.items(cast(dict[object, object], item)))
                if len(items) != len(entries):
                    return False
                return all(
                    type(entry) is tuple
                    and len(entry) == 2
                    and visit(key, entry[0])
                    and visit(child, entry[1])
                    for (key, child), entry in zip(items, entries, strict=True)
                )
            if tag not in (9, 10) or len(values) != 3:
                return False
            schema_index = values[1]
            if type(schema_index) is not int or not 0 <= schema_index < len(schemas):
                return False
            schema = schemas[schema_index]
            if item_type is not schema.value_type:
                return False
            if tag == 9:
                return bool(schema.enum_members) and any(
                    item is member for member in schema.enum_members
                ) and visit(object.__getattribute__(item, "_value_"), values[2])
            children = values[2]
            return (
                not schema.enum_members
                and type(children) is tuple
                and len(children) == len(schema.descriptors)
                and all(
                    visit(
                        descriptor_get(descriptor, item, schema.value_type),
                        child_node,
                    )
                    for descriptor, child_node in zip(
                        schema.descriptors, children, strict=True
                    )
                )
            )
        finally:
            active.remove(identity)

    return visit(value, expected)


def _primitive_bytes_match(
    value: object,
    expected: object,
    schemas: tuple[_PrimitiveSchema, ...],
    *,
    descriptor_get: Callable[..., object],
) -> bool:
    """Match the compact admitted record without allocating another record."""

    if type(expected) is not bytes:
        return False
    body = cast(bytes, expected)
    offset = 0
    seen: dict[int, int] = {}
    active: set[int] = set()
    schema_by_type_id = {
        id(schema.value_type): (index, schema) for index, schema in enumerate(schemas)
    }

    def unsigned() -> int | None:
        nonlocal offset
        number = 0
        shift = 0
        while offset < len(body):
            part = body[offset]
            offset += 1
            number |= (part & 0x7F) << shift
            if part < 0x80:
                return number
            shift += 7
            if shift > 63:
                return None
        return None

    def scalar(tag: int, value_bytes: bytes) -> bool:
        nonlocal offset
        if offset >= len(body) or body[offset] != tag:
            return False
        offset += 1
        size = unsigned()
        if size is None or size != len(value_bytes):
            return False
        end = offset + size
        if end > len(body) or not body.startswith(value_bytes, offset, end):
            return False
        offset = end
        return True

    def visit(item: object) -> bool:
        nonlocal offset
        if offset >= len(body):
            return False
        item_type = type(item)
        if item is None:
            offset += 1
            return body[offset - 1] == 0
        if item_type is str:
            return scalar(1, cast(str, item).encode("utf-8"))
        if item_type is int:
            return scalar(2, str(item).encode("ascii"))
        if item_type is bool:
            offset += 1
            return body[offset - 1] == (3 if item else 4)
        if item_type is float:
            return scalar(5, cast(float, item).hex().encode("ascii"))
        if item_type is bytes:
            return scalar(6, cast(bytes, item))
        if item_type is object:
            return scalar(7, str(id(item)).encode("ascii"))

        identity = id(item)
        retained_index = seen.get(identity)
        if retained_index is not None:
            if body[offset] != 8:
                return False
            offset += 1
            return unsigned() == retained_index
        if identity in active:
            return False
        seen[identity] = len(seen)
        active.add(identity)
        try:
            if item_type is tuple or item_type is list:
                tag = 9 if item_type is tuple else 10
                if body[offset] != tag:
                    return False
                offset += 1
                values = cast(tuple[object, ...] | list[object], item)
                return unsigned() == len(values) and all(visit(child) for child in values)
            if item_type is dict:
                if body[offset] != 11:
                    return False
                offset += 1
                values = cast(dict[object, object], item)
                return unsigned() == len(values) and all(
                    visit(key) and visit(child) for key, child in dict.items(values)
                )
            schema_entry = schema_by_type_id.get(id(item_type))
            if schema_entry is None or schema_entry[1].value_type is not item_type:
                return False
            schema_index, schema = schema_entry
            if schema.enum_members:
                if body[offset] != 12 or not any(
                    item is member for member in schema.enum_members
                ):
                    return False
                offset += 1
                return unsigned() == schema_index and visit(
                    object.__getattribute__(item, "_value_")
                )
            if body[offset] != 13:
                return False
            offset += 1
            return (
                unsigned() == schema_index
                and unsigned() == len(schema.descriptors)
                and all(
                    visit(descriptor_get(descriptor, item, schema.value_type))
                    for descriptor in schema.descriptors
                )
            )
        finally:
            active.remove(identity)

    return visit(value) and offset == len(body)


def _capture_primitive_snapshot(
    value: object,
    *,
    _type: Callable[[object], type[object]] = type,
    _snapshot_type: type[_PrimitiveSnapshot] = _PrimitiveSnapshot,
    _encoder: Callable[..., object] = _capture_flat_primitive_graph,
    _matcher: Callable[..., bool] = _flat_primitive_graph_matches,
    _dict_contains: Callable[..., object] = dict.__contains__,
    _dict_getitem: Callable[..., object] = dict.__getitem__,
    _any: Callable[..., bool] = any,
    _retained_type: Callable[[object], type[object]] = type,
    _error_type: type[TypeError] = TypeError,
    _module_globals: dict[str, object] = _SELECTED_PROVIDER_MODULE_GLOBALS,
    _absent_builtin_names: tuple[
        str, ...
    ] = _PRIMITIVE_VERIFIER_ABSENT_BUILTIN_NAMES,
    _descriptor_get: Callable[..., object] = MemberDescriptorType.__get__,
    _expected_present_bindings: tuple[tuple[str, object], ...] = (
        ("_MEMBER_DESCRIPTOR_GET", MemberDescriptorType.__get__),
        ("_RETAINED_MEMBER_DESCRIPTOR_GET", MemberDescriptorType.__get__),
        ("_encode_primitive_graph", _encode_primitive_graph),
        ("_primitive_bytes_match", _primitive_bytes_match),
        ("_capture_flat_primitive_graph", _capture_flat_primitive_graph),
        ("_flat_primitive_graph_matches", _flat_primitive_graph_matches),
        ("_PrimitiveIdentityGraph", _PrimitiveIdentityGraph),
        ("cast", cast),
        ("_RETAINED_DICT_CONTAINS", dict.__contains__),
        ("_RETAINED_DICT_GETITEM", dict.__getitem__),
        ("_SELECTED_PROVIDER_MODULE_GLOBALS", _SELECTED_PROVIDER_MODULE_GLOBALS),
        (
            "_PRIMITIVE_VERIFIER_ABSENT_BUILTIN_NAMES",
            _PRIMITIVE_VERIFIER_ABSENT_BUILTIN_NAMES,
        ),
        ("_PrimitiveSnapshot", _PrimitiveSnapshot),
    ),
) -> _PrimitiveSnapshot:
    module_globals = _module_globals
    absent_builtin_names = _absent_builtin_names
    if (
        _type is not _retained_type
        or _any(_dict_contains(module_globals, name) for name in absent_builtin_names)
        or _any(
            not _dict_contains(module_globals, name)
            or _dict_getitem(module_globals, name) is not expected
            for name, expected in _expected_present_bindings
        )
        or _snapshot_type
        is not _dict_getitem(module_globals, "_PrimitiveSnapshot")
    ):
        raise _error_type("selected-provider verification primitive changed")
    schemas: list[_PrimitiveSchema] = []
    return _PrimitiveSnapshot(
        _encoder(
            value,
            schemas,
            allow_new=True,
            descriptor_get=_descriptor_get,
        ),
        tuple(schemas),
        module_globals,
        _descriptor_get,
        _encoder,
        _matcher,
        absent_builtin_names,
        _expected_present_bindings,
        _dict_contains,
        _dict_getitem,
    )


def _primitive_snapshot_matches(
    value: object,
    snapshot: _PrimitiveSnapshot,
    *,
    _type: Callable[[object], type[object]] = type,
    _snapshot_type: type[_PrimitiveSnapshot] = _PrimitiveSnapshot,
    _object_getattribute: Callable[..., object] = object.__getattribute__,
    _any: Callable[..., bool] = any,
    _error_type: type[TypeError] = TypeError,
) -> bool:
    if _type(snapshot) is not _snapshot_type:
        raise _error_type("selected-provider primitive snapshot must be exact")
    module_globals = snapshot.module_globals
    dict_contains = snapshot.dict_contains
    dict_getitem = snapshot.dict_getitem
    absent_builtin_names = snapshot.absent_builtin_names
    present_bindings = snapshot.present_bindings
    if _any(
        dict_contains(module_globals, name) for name in absent_builtin_names
    ) or _any(
        not dict_contains(module_globals, name)
        or dict_getitem(module_globals, name) is not expected
        for name, expected in present_bindings
    ):
        raise _error_type("selected-provider verification primitive changed")
    return snapshot.matcher(
        value,
        snapshot.root,
        snapshot.schemas,
        descriptor_get=snapshot.descriptor_get,
    )


def _canonical_body(value: bytes, label: str) -> bytes:
    if type(value) is not bytes:
        raise TypeError(f"{label} must be exact bytes")

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in items:
            if key in result:
                raise ContractViolation(f"{label} contains duplicate keys")
            result[key] = item
        return result

    try:
        decoded = json.loads(value.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation(f"{label} must be canonical JSON") from error
    if canonical_json_bytes(decoded) != value:
        raise ContractViolation(f"{label} must be canonical JSON")
    return value


def _bound_function(entrance: object, provider: object, label: str) -> object:
    if not inspect.ismethod(entrance):
        raise TypeError(f"{label} must be an exact bound provider method")
    if entrance.__self__ is not provider:
        raise ContractViolation(f"{label} is not bound to the selected provider")
    return entrance.__func__


def _capture_observer(observer, provider):
    if observer is None:
        return None
    if type(observer) is not MethodType or observer.__self__ is not provider:
        raise TypeError("selected observer must be an original bound provider method")
    function = observer.__func__
    if type(function) is not FunctionType or inspect.getattr_static(
        provider, function.__name__, None
    ) is not function:
        raise ContractViolation("selected observer descriptor differs")
    parameters = tuple(inspect.signature(observer).parameters.values())
    if len(parameters) != 2 or any(
        item.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        or item.default is not inspect.Parameter.empty for item in parameters
    ):
        raise TypeError("selected observer must take exactly event and use")
    # Retain code and referenced bindings, rather than rediscovering a callback.
    # Do not walk arbitrary owner objects or invoke their descriptors/equality.
    namespace = function.__globals__
    bindings = tuple((name, namespace[name]) for name in function.__code__.co_names if name in namespace)
    module_bindings = tuple(
        (value.__dict__, name, value.__dict__[name])
        for _, value in bindings if type(value) is ModuleType
        for name in function.__code__.co_names if name in value.__dict__
    )
    function_bindings = tuple(
        (value, value.__code__, value.__defaults__, value.__kwdefaults__, value.__closure__)
        for value in (*(value for _, value in bindings), *(value for _, _, value in module_bindings))
        if type(value) is FunctionType
    )
    provider_access = tuple(
        (cls, name, type.__getattribute__(cls, "__dict__").get(name))
        for cls in type.__getattribute__(type(provider), "__mro__")
        for name in ("__getattribute__", "__getattr__")
    )
    return (
        type(provider), function.__name__, function, function.__code__,
        function.__defaults__, function.__kwdefaults__, function.__closure__, bindings,
        module_bindings, function_bindings, provider_access,
    )


def _observer_intact(observer, provider, identity):
    if identity is None:
        return observer is None
    (provider_type, name, function, code, defaults, kwdefaults, closure, bindings,
     module_bindings, function_bindings, provider_access) = identity
    if (
        type(provider) is not provider_type
        or type(observer) is not MethodType
        or observer.__self__ is not provider
        or observer.__func__ is not function
        or type(function) is not FunctionType
        or inspect.getattr_static(provider, name, None) is not function
        or object.__getattribute__(function, "__code__") is not code
        or function.__defaults__ is not defaults
        or function.__kwdefaults__ is not kwdefaults
        or function.__closure__ is not closure
    ):
        return False
    namespace = function.__globals__
    return (
        all(namespace.get(name) is original for name, original in bindings)
        and all(namespace.get(name) is original for namespace, name, original in module_bindings)
        and all(
            function.__code__ is code and function.__defaults__ is defaults
            and function.__kwdefaults__ is kwdefaults and function.__closure__ is closure
            for function, code, defaults, kwdefaults, closure in function_bindings
        )
        and all(type.__getattribute__(cls, "__dict__").get(name) is original
                for cls, name, original in provider_access)
    )


def _check_observer_registration(state, root):
    if (
        state.selected_invocation_observer is not root.selected_invocation_observer
        or state.selected_invocation_observer_identity is not root.selected_invocation_observer_identity
        or not _observer_intact(
            state.selected_invocation_observer, state.provider,
            state.selected_invocation_observer_identity,
        )
    ):
        raise ContractViolation("original selected observer changed")


def _registration_state(
    registration: AdmittedSemanticProviderRegistration,
) -> _RegistrationState:
    if type(registration) is not AdmittedSemanticProviderRegistration:
        raise TypeError("registration must be exact")
    retained = _REGISTRATIONS.get(id(registration))
    if retained is None or retained[0] is not registration:
        raise ContractViolation("provider registration is not nominally admitted")
    state = retained[1]
    if state.closed:
        raise ContractViolation("provider registration is closed")
    if state.creator_pid != os.getpid():
        raise ContractViolation("provider registration belongs to another process")
    if registration._token is not _REGISTRATION_TOKEN:
        raise ContractViolation("provider registration token differs")
    _check_execution_lifecycle(registration, state)
    return state


def validate_selected_provider_registration(
    runtime: SemanticContractRuntime,
    registration: AdmittedSemanticProviderRegistration,
    *,
    expected_profile: SemanticContractProfileDeclaration,
    expected_declaration: SemanticContractProviderDeclaration,
    expected_binding: ProviderExecutionBinding,
) -> None:
    """Read-only original registration validation, not step/execution admission.

    Expected values are comparisons, never admission sources. No factory,
    input-closure or executable entrance is invoked and no sequence is consumed.
    The original registration remains the sole nominal authority being checked.
    """
    if (
        type(expected_profile) is not SemanticContractProfileDeclaration
        or type(expected_declaration) is not SemanticContractProviderDeclaration
        or type(expected_binding) is not ProviderExecutionBinding
    ):
        raise TypeError("exact selected registration expectations required")
    with _LOCK:
        state = _registration_state(registration)
        root = _selection_root_state(state.selection_root)
        factory = _factory_state(root.factory_admission)
        if (
            state.runtime is not runtime
            or state.runtime_token is not runtime._runtime_token
            or root.runtime is not runtime
            or root.runtime_token is not state.runtime_token
            or root.provider is not state.provider
            or type(state.provider) is not root.provider_type
            or root.selection_factory is not factory.selection_factory
            or not root.consumed
        ):
            raise ContractViolation("selected registration original origin differs")
        runtime._validate_selected_provider_registration_inputs(state.provider_key)
        if runtime._providers[state.provider_key] is not state.provider:
            raise ContractViolation("selected registration provider substituted")
        actual_declaration = state.provider.declaration
        if type(actual_declaration) is not SemanticContractProviderDeclaration:
            raise ContractViolation("selected registration declaration type differs")
        if (
            canonical_json_bytes(runtime.profile.to_wire()) != state.profile_bytes
            or canonical_json_bytes(expected_profile.to_wire()) != state.profile_bytes
            or canonical_json_bytes(actual_declaration.to_wire())
            != state.declaration_bytes
            or canonical_json_bytes(expected_declaration.to_wire())
            != state.declaration_bytes
            or canonical_json_bytes(expected_binding.to_wire()) != state.binding_bytes
            or root.profile_bytes != state.profile_bytes
            or root.declaration_bytes != state.declaration_bytes
            or root.binding_bytes != state.binding_bytes
            or root.semantic_implementation_contract_body
            != state.semantic_implementation_contract_body
            or root.configuration_body != state.configuration_body
            or ContentDigest.of_bytes(state.semantic_implementation_contract_body)
            != expected_binding.implementation.closure_digest
            or ContentDigest.of_bytes(state.configuration_body)
            != expected_binding.configuration.digest
        ):
            raise ContractViolation("selected registration complete context differs")
        for retained, function, original in (
            (
                state.executable_entrance,
                state.executable_function,
                root.executable_entrance,
            ),
            (
                state.input_closure_entrance,
                state.input_closure_function,
                root.input_closure_entrance,
            ),
        ):
            if (
                retained is not original
                or _bound_function(
                    retained, state.provider, "retained registration entrance"
                )
                is not function
            ):
                raise ContractViolation("selected registration entrance differs")
            # Compare current owner method to retained original without executing it.
            current = getattr(state.provider, retained.__name__)
            if (
                _bound_function(
                    current, state.provider, "current registration entrance"
                )
                is not function
            ):
                raise ContractViolation("selected registration method substituted")
        _check_observer_registration(state, root)
        _check_selected_private_stage_predecessor_port(state, root)
        # A reentrant owner property must not close/replace the record during checks.
        if _registration_state(registration) is not state:
            raise ContractViolation("selected registration changed during validation")


def _selection_root_state(
    root: AdmittedSemanticProviderSelectionRoot,
) -> _SelectionRootState:
    if type(root) is not AdmittedSemanticProviderSelectionRoot:
        raise TypeError("provider selection root must be exact")
    retained = _SELECTION_ROOTS.get(id(root))
    if retained is None or retained[0] is not root:
        raise ContractViolation("provider selection root is not nominally admitted")
    state = retained[1]
    if state.creator_pid != os.getpid():
        raise ContractViolation("provider selection root belongs to another process")
    if root._token is not _SELECTION_ROOT_TOKEN:
        raise ContractViolation("provider selection root token differs")
    factory = _factory_state(state.factory_admission)
    if (
        factory.selection_factory is not state.selection_factory
        or factory.provider_key != state.provider_key
    ):
        raise ContractViolation("provider selection root factory differs")
    return state


def _check_selected_private_stage_predecessor_port(state, root) -> None:
    """Identity only: Code never receives or invokes an owner view handle."""
    port = state.private_stage_predecessor_port
    function = state.private_stage_predecessor_function
    if (
        port is not root.private_stage_predecessor_port
        or function is not root.private_stage_predecessor_function
        or state.private_stage_predecessor_input is not root.private_stage_predecessor_input
        or state.private_stage_predecessor_input_bytes != root.private_stage_predecessor_input_bytes
        or state.private_stage_predecessor_input_identity is not root.private_stage_predecessor_input_identity
    ):
        raise ContractViolation("original predecessor port changed")
    binding = state.private_stage_predecessor_input
    if binding is not None:
        if type(binding) is not PrivateStageRoleContract:
            raise TypeError("exact predecessor input binding required")
        if canonical_json_bytes(binding.to_wire()) != state.private_stage_predecessor_input_bytes:
            raise ContractViolation("original predecessor input binding changed")
        if not _predecessor_input_identity_matches(binding, state.private_stage_predecessor_input_identity):
            raise ContractViolation("original predecessor input identity changed")
    if port is None:
        if function is not None:
            raise ContractViolation("absent predecessor port has a function")
        return
    if (
        _bound_function(port, state.provider, "selected predecessor port")
        is not function
        or inspect.getattr_static(state.provider, port.__name__, None) is not function
        or _bound_function(
            getattr(state.provider, port.__name__),
            state.provider,
            "current predecessor port",
        ) is not function
    ):
        raise ContractViolation("original predecessor port substituted")


def _validate_selected_private_stage_predecessor_port(
    registration: AdmittedSemanticProviderRegistration,
) -> None:
    """Require an original, live owner port; this does not authorize a read."""
    with _LOCK:
        state = _registration_state(registration)
        root = _selection_root_state(state.selection_root)
        if (
            state.provider is not root.provider
            or state.runtime is not root.runtime
            or state.runtime_token is not root.runtime_token
            or state.runtime._providers[state.provider_key] is not state.provider
            or canonical_json_bytes(state.runtime.profile.to_wire())
            != state.profile_bytes
            or canonical_json_bytes(state.provider.declaration.to_wire())
            != state.declaration_bytes
        ):
            raise ContractViolation("predecessor port provider changed")
        _check_selected_private_stage_predecessor_port(state, root)
        if state.private_stage_predecessor_port is None:
            raise ContractViolation("original predecessor port unavailable")


def _admit_selected_provider_factory(
    *,
    factory_ref: str,
    provider_key: str,
    selection_factory: Callable[
        [], _SelectedProviderFactoryProduct | SelectedProviderStageFactoryProduct
    ],
) -> _AdmittedSemanticProviderFactory:
    """Bind the first trusted domain factory for one selected provider key.

    Domain modules perform this private composition step while defining their
    exact factory.  Once a provider key is occupied, no alternate factory can
    nominate a provider for that key.
    """

    if type(factory_ref) is not str or not factory_ref:
        raise TypeError("selected-provider factory ref must be exact text")
    if type(provider_key) is not str or not provider_key:
        raise TypeError("selected-provider factory key must be exact text")
    if (
        not inspect.isfunction(selection_factory)
        or inspect.signature(selection_factory).parameters
    ):
        raise TypeError(
            "selected-provider factory must be an exact zero-argument function"
        )
    admission = _AdmittedSemanticProviderFactory(_FACTORY_TOKEN)
    state = _FactoryState(
        creator_pid=os.getpid(),
        factory_ref=factory_ref,
        provider_key=provider_key,
        selection_factory=selection_factory,
        selection_factory_function=selection_factory,
    )
    with _LOCK:
        if provider_key in _FACTORY_PROVIDER_KEYS or factory_ref in _FACTORY_REFS:
            raise ContractViolation(
                "selected-provider key or ref already has an exact factory"
            )
        _FACTORIES[id(admission)] = (admission, state)
        _FACTORY_PROVIDER_KEYS[provider_key] = admission
        _FACTORY_REFS[factory_ref] = admission
    return admission


def _factory_state(admission: _AdmittedSemanticProviderFactory) -> _FactoryState:
    if type(admission) is not _AdmittedSemanticProviderFactory:
        raise TypeError("selected-provider factory admission must be exact")
    retained = _FACTORIES.get(id(admission))
    if retained is None or retained[0] is not admission:
        raise ContractViolation("selected-provider factory is not nominally admitted")
    state = retained[1]
    if state.creator_pid != os.getpid():
        raise ContractViolation("selected-provider factory belongs to another process")
    if admission._token is not _FACTORY_TOKEN:
        raise ContractViolation("selected-provider factory token differs")
    if (
        _FACTORY_PROVIDER_KEYS.get(state.provider_key) is not admission
        or _FACTORY_REFS.get(state.factory_ref) is not admission
        or state.selection_factory is not state.selection_factory_function
    ):
        raise ContractViolation("selected-provider factory binding differs")
    return state


def _issue_selected_provider_selection_root(
    factory_admission: _AdmittedSemanticProviderFactory,
) -> AdmittedSemanticProviderSelectionRoot:
    """Invoke one retained exact domain factory and issue its nominal root.

    No provider, provider type, runtime, entrance, or closure evidence crosses
    this issuance boundary from the caller.
    """

    with _LOCK:
        factory = _factory_state(factory_admission)
        selection_factory = factory.selection_factory
    product = selection_factory()
    return _selection_root_from_factory_product(factory_admission, product)


def _selection_root_from_factory_product(
    factory_admission: _AdmittedSemanticProviderFactory,
    product: _SelectedProviderFactoryProduct | SelectedProviderStageFactoryProduct,
) -> AdmittedSemanticProviderSelectionRoot:
    """Shared internal validation after an original factory has returned a product."""

    with _LOCK:
        factory = _factory_state(factory_admission)
    if type(product) is not _SelectedProviderFactoryProduct:
        raise TypeError("selected-provider factory product must be exact")
    runtime = product.runtime
    provider = product.provider
    provider_type = type(provider)
    binding = product.binding
    executable_entrance = product.executable_entrance
    input_closure_entrance = product.input_closure_entrance
    if type(binding) is not ProviderExecutionBinding:
        raise TypeError("selected provider binding must be exact")
    binding.to_wire()
    provider_key = binding.provider_key
    if provider_key != factory.provider_key:
        raise ContractViolation("selected-provider factory key differs")
    runtime._validate_selected_provider_registration_inputs(provider_key)
    if runtime._providers[provider_key] is not provider:
        raise ContractViolation("factory-selected provider differs from runtime")
    declaration = provider.declaration
    if type(declaration) is not SemanticContractProviderDeclaration:
        raise TypeError("selected provider declaration must be exact")
    executable_function = _bound_function(
        executable_entrance, provider, "selected executable entrance"
    )
    input_closure_function = _bound_function(
        input_closure_entrance, provider, "selected input-closure entrance"
    )
    predecessor_port = product.private_stage_predecessor_port
    predecessor_input = product.private_stage_predecessor_input
    predecessor_input_bytes = None
    predecessor_input_identity = None
    predecessor_function = None
    if predecessor_port is not None:
        predecessor_function = _bound_function(
            predecessor_port, provider, "selected predecessor port"
        )
        if (
            inspect.getattr_static(
                provider, predecessor_port.__name__, None
            ) is not predecessor_function
        ):
            raise ContractViolation("selected predecessor port descriptor differs")
    if predecessor_input is not None:
        if type(predecessor_input) is not PrivateStageRoleContract:
            raise TypeError("exact predecessor input binding required")
        predecessor_input_bytes = canonical_json_bytes(predecessor_input.to_wire())
        predecessor_input_identity = _predecessor_input_identity(predecessor_input)
        if predecessor_port is None or sum(
            item.role == predecessor_input.role and item.contract == predecessor_input.contract
            for item in runtime.profile.inputs
        ) != 1:
            raise ContractViolation("predecessor port must bind one declared profile input")
        parameters = tuple(inspect.signature(predecessor_port).parameters.values())
        if len(parameters) != 3 or any(
            item.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            or item.default is not inspect.Parameter.empty for item in parameters
        ):
            raise TypeError("bound predecessor port must take role, body and grant")
    observer = product.selected_invocation_observer
    observer_identity = _capture_observer(observer, provider)
    implementation_body = _canonical_body(
        product.semantic_implementation_contract_body,
        "semantic implementation contract closure",
    )
    configuration = _canonical_body(
        product.configuration_body, "provider configuration"
    )
    if (
        ContentDigest.of_bytes(implementation_body)
        != binding.implementation.closure_digest
    ):
        raise ContractViolation("implementation artifact closure digest differs")
    if ContentDigest.of_bytes(configuration) != binding.configuration.digest:
        raise ContractViolation("provider configuration digest differs")
    root = AdmittedSemanticProviderSelectionRoot(_SELECTION_ROOT_TOKEN)
    state = _SelectionRootState(
        factory_admission=factory_admission,
        runtime=runtime,
        runtime_token=runtime._runtime_token,
        creator_pid=os.getpid(),
        selection_factory=factory.selection_factory,
        provider_type=provider_type,
        profile_bytes=canonical_json_bytes(runtime.profile.to_wire()),
        provider_key=provider_key,
        declaration_bytes=canonical_json_bytes(declaration.to_wire()),
        binding_bytes=canonical_json_bytes(binding.to_wire()),
        provider=provider,
        executable_entrance=executable_entrance,
        input_closure_entrance=input_closure_entrance,
        executable_function=executable_function,
        input_closure_function=input_closure_function,
        semantic_implementation_contract_body=implementation_body,
        configuration_body=configuration,
        private_stage_predecessor_port=predecessor_port,
        private_stage_predecessor_function=predecessor_function,
        private_stage_predecessor_input=predecessor_input,
        private_stage_predecessor_input_bytes=predecessor_input_bytes,
        private_stage_predecessor_input_identity=predecessor_input_identity,
        selected_invocation_observer=observer,
        selected_invocation_observer_identity=observer_identity,
    )
    with _LOCK:
        _SELECTION_ROOTS[id(root)] = (root, state)
    return root


def register_selected_provider(
    runtime: SemanticContractRuntime,
    selection_root: AdmittedSemanticProviderSelectionRoot,
) -> AdmittedSemanticProviderRegistration:
    """Consume one exact factory-issued selection root."""

    with _LOCK:
        root = _selection_root_state(selection_root)
        if root.consumed:
            raise ContractViolation("provider selection root is already consumed")
        if (
            root.runtime is not runtime
            or root.runtime_token is not runtime._runtime_token
        ):
            raise ContractViolation(
                "provider selection root belongs to another runtime"
            )
        runtime._validate_selected_provider_registration_inputs(root.provider_key)
        if (
            runtime._providers[root.provider_key] is not root.provider
            or type(root.provider) is not root.provider_type
            or canonical_json_bytes(runtime.profile.to_wire()) != root.profile_bytes
            or canonical_json_bytes(root.provider.declaration.to_wire())
            != root.declaration_bytes
            or _bound_function(
                root.executable_entrance,
                root.provider,
                "selected executable entrance",
            )
            is not root.executable_function
            or _bound_function(
                root.input_closure_entrance,
                root.provider,
                "selected input-closure entrance",
            )
            is not root.input_closure_function
            or (
                root.private_stage_predecessor_port is not None
                and _bound_function(
                    root.private_stage_predecessor_port,
                    root.provider,
                    "selected predecessor port",
                ) is not root.private_stage_predecessor_function
            )
        ):
            raise ContractViolation(
                "provider selection root changed before registration"
            )
        _check_observer_registration(root, root)
        root.consumed = True
    registration = AdmittedSemanticProviderRegistration(_REGISTRATION_TOKEN)
    state = _RegistrationState(
        selection_root=selection_root,
        runtime=runtime,
        runtime_token=runtime._runtime_token,
        creator_pid=os.getpid(),
        profile_bytes=root.profile_bytes,
        provider_key=root.provider_key,
        declaration_bytes=root.declaration_bytes,
        binding_bytes=root.binding_bytes,
        provider=root.provider,
        executable_entrance=root.executable_entrance,
        input_closure_entrance=root.input_closure_entrance,
        executable_function=root.executable_function,
        input_closure_function=root.input_closure_function,
        semantic_implementation_contract_body=(
            root.semantic_implementation_contract_body
        ),
        configuration_body=root.configuration_body,
        private_stage_predecessor_port=root.private_stage_predecessor_port,
        private_stage_predecessor_function=root.private_stage_predecessor_function,
        private_stage_predecessor_input=root.private_stage_predecessor_input,
        private_stage_predecessor_input_bytes=root.private_stage_predecessor_input_bytes,
        private_stage_predecessor_input_identity=root.private_stage_predecessor_input_identity,
        selected_invocation_observer=root.selected_invocation_observer,
        selected_invocation_observer_identity=root.selected_invocation_observer_identity,
        witnesses=[],
    )
    with _LOCK:
        if any(
            existing.runtime is runtime
            and existing.provider_key == root.provider_key
            and not existing.closed
            for _, existing in _REGISTRATIONS.values()
        ):
            root.consumed = False
            raise ContractViolation("selected provider is already registered")
        _REGISTRATIONS[id(registration)] = (registration, state)
    return registration


def selected_provider_probe(
    runtime: SemanticContractRuntime,
    registration: AdmittedSemanticProviderRegistration,
) -> SelectedSemanticProviderProbe:
    state = _registration_state(registration)
    if (
        state.runtime is not runtime
        or state.runtime_token is not runtime._runtime_token
    ):
        raise ContractViolation("provider registration belongs to another runtime")
    with _LOCK:
        if state.probe_issued:
            raise ContractViolation("selected provider probe is already issued")
        state.probe_issued = True
    probe = SelectedSemanticProviderProbe(_PROBE_TOKEN, runtime, registration)
    with _LOCK:
        _PROBES[id(probe)] = (
            probe,
            _ProbeState(runtime, registration, os.getpid()),
        )
    return probe


def _probe_state(probe: SelectedSemanticProviderProbe) -> _ProbeState:
    if type(probe) is not SelectedSemanticProviderProbe:
        raise TypeError("selected provider probe must be exact")
    retained = _PROBES.get(id(probe))
    if retained is None or retained[0] is not probe:
        raise ContractViolation("selected provider probe is not nominally admitted")
    state = retained[1]
    if state.creator_pid != os.getpid():
        raise ContractViolation("selected provider probe belongs to another process")
    if (
        probe._token is not _PROBE_TOKEN
        or probe._runtime is not state.runtime
        or probe._registration is not state.registration
    ):
        raise ContractViolation("selected provider probe context differs")
    registration = _registration_state(state.registration)
    if registration.runtime is not state.runtime:
        raise ContractViolation("selected provider probe runtime differs")
    return state


def _require_selected_provider_probe_factory(
    probe: SelectedSemanticProviderProbe,
    *,
    factory_ref: str,
) -> None:
    """Require one probe to descend from an exact retained domain factory."""

    if type(factory_ref) is not str or not factory_ref:
        raise TypeError("selected-provider factory ref must be exact text")
    with _LOCK:
        probe_state = _probe_state(probe)
        registration = _registration_state(probe_state.registration)
        root = _selection_root_state(registration.selection_root)
        factory = _factory_state(root.factory_admission)
        if factory.factory_ref != factory_ref:
            raise ContractViolation("selected-provider probe factory differs")


def close_selected_provider_registration(
    runtime: SemanticContractRuntime,
    registration: AdmittedSemanticProviderRegistration,
) -> None:
    with _LOCK:
        state = _registration_state(registration)
        if (
            state.runtime is not runtime
            or state.runtime_token is not runtime._runtime_token
        ):
            raise ContractViolation("provider registration belongs to another runtime")
        if any(
            execution.registration is registration
            and execution.lifecycle in {"active", "executing", "terminalizing"}
            for _, execution in _EXECUTIONS.values()
        ):
            raise ContractViolation("provider registration has an active execution")
        if state.execution_lifecycle is not None and "retire_inputs" in state.execution_lifecycle.entrances:
            state.execution_lifecycle.call("retire_inputs")
        _OBSERVATION_ISSUER.close(registration)
        state.closed = True


def _closure_evidence(
    closure: SelectedProviderInvocationClosure,
    step_invocation: ProviderStepInvocation,
) -> tuple[
    bytes,
    tuple[tuple[bytes, bytes], ...],
    tuple[bytes, bytes] | None,
    bytes,
    bytes,
]:
    invocation_bytes = canonical_json_bytes(closure.invocation.to_wire())
    input_evidence = tuple(
        (canonical_json_bytes(item.coordinate.to_wire()), item.canonical_body)
        for item in closure.input_bodies
    )
    predecessor_evidence = (
        None
        if closure.predecessor_body is None
        else (
            canonical_json_bytes(closure.predecessor_body.coordinate.to_wire()),
            closure.predecessor_body.canonical_body,
        )
    )
    dependency_bytes = canonical_json_bytes(
        [item.to_wire() for item in closure.invocation.dependencies]
    )
    return (
        invocation_bytes,
        input_evidence,
        predecessor_evidence,
        dependency_bytes,
        step_invocation.input_closure_body,
    )


def _step_identity_guard(value: ProviderStepInvocation) -> tuple[object, ...]:
    """Retain the Code-owned step graph without re-entering domain codecs."""

    if type(value) is not ProviderStepInvocation:
        raise TypeError("selected provider step must be exact")
    inputs = object.__getattribute__(value, "inputs")
    if type(inputs) is not tuple:
        raise TypeError("selected provider inputs must be exact")
    return (
        id(object.__getattribute__(value, "invocation")),
        id(object.__getattribute__(value, "step")),
        id(object.__getattribute__(value, "declaration")),
        id(object.__getattribute__(value, "binding")),
        id(inputs),
        tuple(
            (
                id(item),
                id(object.__getattribute__(item, "source")),
                object.__getattribute__(item, "target_role"),
                id(object.__getattribute__(item, "admitted")),
            )
            for item in inputs
        ),
        id(object.__getattribute__(value, "predecessor")),
        id(object.__getattribute__(value, "dependencies")),
        object.__getattribute__(value, "_input_closure_body"),
        object.__getattribute__(
            object.__getattribute__(value, "_input_closure_digest"), "value"
        ),
        object.__getattribute__(value, "_selected_primitive_snapshot_node_count"),
        object.__getattribute__(value, "_selected_primitive_snapshot_scalar_bytes"),
    )


def _observed_step_nodes(value: ProviderStepInvocation) -> tuple[object, ...]:
    """Strong references for each node used by the existing step guard."""
    if type(value) is not ProviderStepInvocation:
        raise ContractViolation("exact observed step required")
    inputs = object.__getattribute__(value, "inputs")
    if type(inputs) is not tuple:
        raise ContractViolation("exact observed input tuple required")
    nodes: list[object] = [value, inputs]
    for name in ("invocation", "step", "declaration", "binding", "predecessor", "dependencies"):
        nodes.append(object.__getattribute__(value, name))
    for item in inputs:
        if type(item) is not BoundSemanticInput:
            raise ContractViolation("exact observed bound input required")
        admitted = object.__getattribute__(item, "admitted")
        if type(admitted) is not AdmittedSemanticValue:
            raise ContractViolation("exact observed admitted value required")
        nodes.extend((item, object.__getattribute__(item, "source"), admitted))
        for name in AdmittedSemanticValue.__slots__:
            nodes.append(object.__getattribute__(admitted, name))
    return tuple(nodes)


def _clear_input_rejection_frames(error, filename):
    """Clear completed frames from one Code module; foreign owner frames stay intact."""
    pending, seen = [error], []
    while pending:
        current = pending.pop()
        if any(current is original for original in seen):
            continue
        seen.append(current)
        # Use the built-in exception slots, not overridden owner attributes.
        trace = BaseException.__dict__["__traceback__"].__get__(current)
        while trace is not None:
            frame = trace.tb_frame
            if frame.f_code.co_filename == filename:
                try:
                    frame.clear()
                except RuntimeError:
                    pass  # Active callers clear their references before rethrowing.
            trace = trace.tb_next
        for slot in (BaseException.__dict__["__context__"], BaseException.__dict__["__cause__"]):
            related = slot.__get__(current)
            if related is not None:
                pending.append(related)


@dataclass(frozen=True, slots=True)
class _ExecutionLifecycle:
    origin: object
    entrances: dict[str, tuple[object, Any, object, object]]
    terminal_mode: str = "owner_value"

    def call(self, name, *args):
        try:
            descriptor, method, function, code = self.entrances[name]
            if (inspect.getattr_static(self.origin, name) is not descriptor
                    or method.__func__ is not function or object.__getattribute__(function, "__code__") is not code):
                raise ContractViolation("selected lifecycle entrance substituted")
            result = method(*args)
            if (inspect.getattr_static(self.origin, name) is not descriptor
                    or method.__func__ is not function or object.__getattribute__(function, "__code__") is not code):
                raise ContractViolation("selected lifecycle entrance substituted")
            return result
        except BaseException as error:
            args = code = descriptor = function = method = name = result = self = None  # noqa: PLW0642 - release rejection-frame custody
            _clear_input_rejection_frames(error, __file__)
            raise


_ORIGINAL_LIFECYCLES: dict[int, tuple[object, _ExecutionLifecycle, Any]] = {}
_LIFECYCLE_KIND = _ExecutionLifecycle
_LIFECYCLE_SLOTS = tuple(_ExecutionLifecycle.__dict__[name]
                        for name in ("origin", "entrances", "terminal_mode"))


def _check_execution_lifecycle(registration, state):
    retained = _ORIGINAL_LIFECYCLES.get(id(registration))
    if retained is None:
        if state.execution_lifecycle is not None:
            raise ContractViolation("unregistered selected execution lifecycle")
        return
    if retained[0] is not registration or state.execution_lifecycle is not retained[1]:
        raise ContractViolation("original selected execution lifecycle changed")
    lifecycle, snapshot = retained[1], retained[2]
    if type(lifecycle) is not _LIFECYCLE_KIND or _ExecutionLifecycle is not _LIFECYCLE_KIND:
        raise ContractViolation("original selected lifecycle type changed")
    namespace = type.__getattribute__(_LIFECYCLE_KIND, "__dict__")
    if any(namespace.get(name) is not slot for name, slot in zip(
        ("origin", "entrances", "terminal_mode"), _LIFECYCLE_SLOTS, strict=True)):
        raise ContractViolation("original selected lifecycle slot changed")
    if (lifecycle.origin is not snapshot[0] or lifecycle.entrances is not snapshot[1]
            or lifecycle.terminal_mode is not snapshot[2]
            or type(lifecycle.entrances) is not dict
            or len(lifecycle.entrances) != len(snapshot[3])
            or any(dict.get(lifecycle.entrances, name) is not entry
                   for name, entry in snapshot[3])):
        raise ContractViolation("original selected lifecycle entrance record changed")


def _bind_selected_execution_lifecycle(
    runtime, registration, origin, *, terminal_mode="owner_value", input_verification=False
):
    """Privileged Code composition only; callers cannot nominate a validator.

    The retained-policy owner authenticates its original host/context origin.
    This consumes that fixed handoff, not structural Protocol agreement.
    """
    if type(terminal_mode) is not str or terminal_mode not in ("owner_value", "runtime_completion"):
        raise ContractViolation("selected terminal mode differs")
    state = _registration_state(registration)
    if state.runtime is not runtime:
        raise ContractViolation("foreign lifecycle runtime")
    if type(input_verification) is not bool:
        raise TypeError("exact input verification flag required")
    entrances = {}
    names = ("adopt", "validate", "complete", "fail")
    if input_verification:
        names += ("verify_inputs", "release_inputs", "retire_inputs")
    for name in names:
        method = getattr(origin, name)
        function = _bound_function(method, origin, name)
        entrances[name] = (inspect.getattr_static(origin, name), method,
                           function, object.__getattribute__(function, "__code__"))
    with _LOCK:
        state = _registration_state(registration)
        if (
            state.sequence
            or state.probe_issued
            or state.execution_started
            or runtime in _DIRECT_EXECUTION_STARTED
            or state.execution_lifecycle is not None
        ):
            raise ContractViolation("late or replayed execution lifecycle binding")
        state.execution_lifecycle = _ExecutionLifecycle(origin, entrances, terminal_mode)
        _ORIGINAL_LIFECYCLES[id(registration)] = (
            registration, state.execution_lifecycle,
            (origin, entrances, terminal_mode, tuple(entrances.items())),
        )


_DIRECT_EXECUTION_STARTED: WeakKeyDictionary = WeakKeyDictionary()


def _reject_untracked_direct_execution(runtime):
    # Registration retention is also the lifetime ledger after close; closing a
    # bound registration must not reopen a raw, untracked runtime entrance.
    if any(state.runtime is runtime and state.creator_pid != os.getpid()
           for _, state in _REGISTRATIONS.values()):
        raise ContractViolation("selected runtime process changed")
    with _LOCK:
        if any(
            state.runtime is runtime and state.execution_lifecycle is not None
            for _, state in _REGISTRATIONS.values()
        ):
            raise ContractViolation("bound runtime requires tracked selected execution")
        _DIRECT_EXECUTION_STARTED[runtime] = True


def issue_selected_provider_execution(
    runtime: SemanticContractRuntime,
    registration: AdmittedSemanticProviderRegistration,
    semantic_input: object,
    *,
    operation_context: object | None = None,
    _uninterrupted_probe_token: object | None = None,
) -> SelectedSemanticProviderExecutionAdmission:
    state = _registration_state(registration)
    if state.runtime is not runtime:
        raise ContractViolation("foreign execution runtime")
    with _LOCK:
        state = _registration_state(registration)
        state.execution_started = True
        lifecycle = state.execution_lifecycle
        if lifecycle is None and any(
            other.runtime is runtime and other.execution_lifecycle is not None
            for _, other in _REGISTRATIONS.values()
        ):
            raise ContractViolation("runtime already requires original tracked registration")
    if lifecycle is None:
        if operation_context is not None:
            raise ContractViolation("context requires original lifecycle binding")
        return _issue_selected_provider_execution(
            runtime,
            registration,
            semantic_input,
            _uninterrupted_probe_token=_uninterrupted_probe_token,
        )
    if operation_context is None or _uninterrupted_probe_token is not None:
        raise ContractViolation("original tracked operation context required")
    use = (lifecycle.call("adopt", operation_context, semantic_input)
           if "verify_inputs" in lifecycle.entrances
           else lifecycle.call("adopt", operation_context))
    try:
        return _issue_selected_provider_execution(
            runtime, registration, semantic_input, _lifecycle_use=use
        )
    except BaseException:
        lifecycle.call("fail", use)
        raise


def _issue_selected_provider_execution(
    runtime: SemanticContractRuntime,
    registration: AdmittedSemanticProviderRegistration,
    semantic_input: object,
    *,
    _uninterrupted_probe_token: object | None = None,
    _lifecycle_use: object | None = None,
) -> SelectedSemanticProviderExecutionAdmission:
    state = _registration_state(registration)
    if (
        state.runtime is not runtime
        or state.runtime_token is not runtime._runtime_token
    ):
        raise ContractViolation("provider registration belongs to another runtime")
    if state.selected_invocation_observer is not None and (
        state.execution_lifecycle is None
        or state.execution_lifecycle.terminal_mode != "runtime_completion"
        or _uninterrupted_probe_token is not None
    ):
        raise ContractViolation("observed invocation requires original runtime-completion lifecycle")
    _check_observer_registration(state, _selection_root_state(state.selection_root))
    started = perf_counter_ns()
    closure = state.input_closure_entrance(semantic_input)
    closure_finished = perf_counter_ns()
    if type(closure) is not SelectedProviderInvocationClosure:
        raise TypeError("selected invocation closure must be exact")
    closure.__post_init__()
    if state.execution_lifecycle is not None:
        state.execution_lifecycle.call("validate", _lifecycle_use, closure)
    admission_diagnostics: list[tuple[str, int]] = []
    step_started = perf_counter_ns()
    step_invocation = runtime._admit_selected_provider_step(
        state.provider_key,
        closure.invocation,
        closure.input_bodies,
        closure.predecessor_body,
        closure.input_values,
        diagnostic_spans_ns=admission_diagnostics,
    )
    step_finished = perf_counter_ns()
    evidence = _closure_evidence(closure, step_invocation)
    evidence_finished = perf_counter_ns()
    primitive_snapshot = _capture_primitive_snapshot(closure)
    snapshot_finished = perf_counter_ns()
    primitive_root = primitive_snapshot.root
    if type(primitive_root) is not _PrimitiveIdentityGraph:
        raise ContractViolation("selected provider primitive graph differs")
    object.__setattr__(
        step_invocation,
        "_selected_primitive_snapshot_node_count",
        primitive_root.node_count,
    )
    object.__setattr__(
        step_invocation,
        "_selected_primitive_snapshot_scalar_bytes",
        primitive_root.scalar_bytes,
    )
    step_guard = _step_identity_guard(step_invocation)
    guard_finished = perf_counter_ns()
    with _LOCK:
        state = _registration_state(registration)
        if state.sequence == _MAX_SEQUENCE:
            state.closed = True
            raise ContractViolation("selected provider operation sequence exhausted")
        state.sequence += 1
        admission = SelectedSemanticProviderExecutionAdmission(_EXECUTION_TOKEN)
        _EXECUTIONS[id(admission)] = (
            admission,
            _ExecutionState(
                registration=registration,
                lifecycle_use=_lifecycle_use,
                sequence=state.sequence,
                creator_pid=os.getpid(),
                runtime_token=runtime._runtime_token,
                semantic_input=semantic_input,
                closure=closure,
                step_invocation=step_invocation,
                invocation_bytes=evidence[0],
                input_evidence=evidence[1],
                predecessor_evidence=evidence[2],
                dependency_bytes=evidence[3],
                closure_body=evidence[4],
                primitive_snapshot=primitive_snapshot,
                step_guard=step_guard,
                uninterrupted_probe_execution=(
                    _uninterrupted_probe_token is _UNINTERRUPTED_PROBE_TOKEN
                ),
            ),
        )
    admission._issue_timings_ns = (
        ("input_closure_derivation", closure_finished - started),
        ("code_admission", perf_counter_ns() - closure_finished),
        *admission_diagnostics,
        ("code_step_total", step_finished - step_started),
        ("code_closure_evidence", evidence_finished - step_finished),
        ("code_primitive_snapshot", snapshot_finished - evidence_finished),
        ("code_step_guard", guard_finished - snapshot_finished),
    )
    if state.selected_invocation_observer is not None:
        try:
            _OBSERVATION_ISSUER.associate(runtime, admission)
        except BaseException as error:
            # Association can fail before issue returns to its outer owner.
            with _LOCK:
                retained = _EXECUTIONS.pop(id(admission), None)
                if retained is not None:
                    retained[1].lifecycle = "failed"
                    _TERMINAL_EXECUTIONS[admission] = "failed"
            if retained is not None:
                _OBSERVATION_ISSUER.release_failed(retained[1], error)
            del semantic_input, closure, step_invocation, primitive_snapshot, primitive_root, step_guard, evidence
            raise
    return admission


def _execution_state(
    runtime: SemanticContractRuntime,
    admission: SelectedSemanticProviderExecutionAdmission,
) -> tuple[_ExecutionState, _RegistrationState]:
    if type(admission) is not SelectedSemanticProviderExecutionAdmission:
        raise TypeError("provider execution admission must be exact")
    retained = _EXECUTIONS.get(id(admission))
    if retained is None or retained[0] is not admission:
        if admission in _TERMINAL_EXECUTIONS:
            raise ContractViolation("provider execution admission is not active")
        raise ContractViolation("provider execution is not nominally admitted")
    execution = retained[1]
    registration = _registration_state(execution.registration)
    if (
        execution.creator_pid != os.getpid()
        or execution.runtime_token is not runtime._runtime_token
        or registration.runtime is not runtime
    ):
        raise ContractViolation("provider execution belongs to another runtime/process")
    if admission._token is not _EXECUTION_TOKEN:
        raise ContractViolation("provider execution token differs")
    return execution, registration


def _abort_selected_provider_execution(
    runtime: SemanticContractRuntime,
    admission: SelectedSemanticProviderExecutionAdmission,
) -> None:
    """Terminally abandon a tracked admission before provider dispatch.

    The private-stage predecessor port runs between issuance and dispatch. A
    refusal there must not leave an executable selected admission behind.
    This is an internal Code lifecycle operation, not a caller cancellation
    capability or a provider callback.
    """
    _execution_state(runtime, admission)  # Fork refusal before inherited lock.
    with _LOCK:
        execution, registration = _execution_state(runtime, admission)
        lifecycle = registration.execution_lifecycle
        if execution.lifecycle != "active" or lifecycle is None:
            raise ContractViolation("active tracked execution required for abort")
        execution.lifecycle = "failed"
        retained = _EXECUTIONS.pop(id(admission), None)
        if retained is None or retained[0] is not admission:
            raise ContractViolation("selected admission changed during abort")
        _TERMINAL_EXECUTIONS[admission] = "failed"
        use = execution.lifecycle_use
    try:
        _OBSERVATION_ISSUER.fail(execution)
    finally:
        try:
            lifecycle.call("fail", use)
        finally:
            if registration.selected_invocation_observer is not None:
                _OBSERVATION_ISSUER.release_failed(execution)


def _private_predecessor_execution_input(
    runtime: SemanticContractRuntime,
    admission: SelectedSemanticProviderExecutionAdmission,
) -> tuple[_ExecutionState, _RegistrationState, PrivateStageRoleContract, SemanticBody]:
    """Read original pending input/port identity without calling an owner.

    The port's own read verifier uses this Code-only check. Full host and owner
    checks belong outside parent exclusion, before the grant is issued.
    """
    execution, registration = _execution_state(runtime, admission)
    root = _selection_root_state(registration.selection_root)
    binding = registration.private_stage_predecessor_input
    port = registration.private_stage_predecessor_port
    function = registration.private_stage_predecessor_function
    if (
        execution.lifecycle != "active"
        or execution.uninterrupted_probe_execution
        or registration.execution_lifecycle is None
        or binding is None
        or type(binding) is not PrivateStageRoleContract
        or binding is not root.private_stage_predecessor_input
        or port is None
        or port is not root.private_stage_predecessor_port
        or function is not root.private_stage_predecessor_function
        or registration.private_stage_predecessor_input_bytes
        != root.private_stage_predecessor_input_bytes
        or registration.private_stage_predecessor_input_identity
        is not root.private_stage_predecessor_input_identity
        or not _predecessor_input_identity_matches(binding, root.private_stage_predecessor_input_identity)
        or registration.provider is not root.provider
        or type(registration.provider) is not root.provider_type
        or runtime._providers[registration.provider_key] is not registration.provider
        or inspect.getattr_static(registration.provider, cast(Any, port).__name__, None) is not function
        or not _primitive_snapshot_matches(execution.closure, execution.primitive_snapshot)
        or _step_identity_guard(execution.step_invocation) != execution.step_guard
    ):
        raise ContractViolation("original pending predecessor input or port changed")
    matches = tuple(
        body for body in execution.closure.input_bodies
        if body.coordinate.role == binding.role
        and body.coordinate.contract == binding.contract
    )
    if len(matches) != 1:
        raise ContractViolation("predecessor port input is not uniquely admitted")
    return execution, registration, binding, matches[0]


def _fresh_step_invocation(
    runtime: SemanticContractRuntime,
    registration: _RegistrationState,
    execution: _ExecutionState,
    *,
    verify_closure: bool = True,
) -> ProviderStepInvocation:
    closure = execution.closure
    closure_unchanged = True
    if verify_closure:
        try:
            closure_unchanged = _primitive_snapshot_matches(
                closure, execution.primitive_snapshot
            )
        except (AttributeError, TypeError, ValueError) as error:
            raise ContractViolation(
                "selected provider input closure changed after admission"
            ) from error
    fresh = execution.step_invocation
    if not closure_unchanged or _step_identity_guard(fresh) != execution.step_guard:
        raise ContractViolation(
            "selected provider input closure changed after admission"
        )
    declaration = registration.provider.declaration
    if (
        type(declaration) is not SemanticContractProviderDeclaration
        or canonical_json_bytes(declaration.to_wire()) != registration.declaration_bytes
        or canonical_json_bytes(fresh.binding.to_wire()) != registration.binding_bytes
        or ContentDigest.of_bytes(registration.semantic_implementation_contract_body)
        != fresh.binding.implementation.closure_digest
        or ContentDigest.of_bytes(registration.configuration_body)
        != fresh.binding.configuration.digest
    ):
        raise ContractViolation("selected provider registration context changed")
    return fresh


def _begin_selected_terminal_completion(runtime, admission, derivation):
    _execution_state(runtime, admission)  # Fork refusal before inherited lock.
    with _LOCK:
        execution, registration = _execution_state(runtime, admission)
        lifecycle = registration.execution_lifecycle
        if (
            execution.lifecycle != "terminalizing"
            or execution.terminal_started
            or execution.terminal_derivation is not derivation
            or execution.terminal_thread != get_ident()
            or lifecycle is None
            or lifecycle.terminal_mode != "runtime_completion"
        ):
            raise ContractViolation("selected terminal completion is unavailable")
        execution.terminal_started = True
    return _fresh_step_invocation(runtime, registration, execution)


def execute_selected_provider(
    runtime: SemanticContractRuntime,
    admission: SelectedSemanticProviderExecutionAdmission,
) -> object:
    _execution_state(runtime, admission)  # Reject fork before the inherited lock.
    with _LOCK:
        execution, registration = _execution_state(runtime, admission)
        if execution.lifecycle != "active":
            raise ContractViolation("provider execution admission is not active")
        execution.lifecycle = "executing"
    completed = False
    completion = None
    try:
        _OBSERVATION_ISSUER.check(execution)
        if registration.execution_lifecycle is not None:
            registration.execution_lifecycle.call(
                "validate", execution.lifecycle_use, execution.closure
            )
        preverify_started = perf_counter_ns()
        fresh = _fresh_step_invocation(
            runtime,
            registration,
            execution,
            verify_closure=True,
        )
        if (
            canonical_json_bytes(runtime.profile.to_wire())
            != registration.profile_bytes
        ):
            raise ContractViolation("selected provider profile changed")
        if runtime._providers[registration.provider_key] is not registration.provider:
            raise ContractViolation("selected live provider changed")
        if (
            _bound_function(
                registration.executable_entrance,
                registration.provider,
                "selected executable entrance",
            )
            is not registration.executable_function
            or _bound_function(
                registration.input_closure_entrance,
                registration.provider,
                "selected input-closure entrance",
            )
            is not registration.input_closure_function
        ):
            raise ContractViolation("selected provider entrance changed")
        _OBSERVATION_ISSUER.notify(execution, "dispatch")
        _fresh_step_invocation(runtime, registration, execution)
        preverify_finished = perf_counter_ns()
        result = registration.executable_entrance(fresh, execution.semantic_input)
        provider_finished = perf_counter_ns()
        if inspect.isawaitable(result):
            raise TypeError("selected preparation entrance must be synchronous")
        _fresh_step_invocation(runtime, registration, execution)
        postverify_finished = perf_counter_ns()
        admission._timings_ns = (
            ("preinvoke_rederivation", preverify_finished - preverify_started),
            ("provider_execution", provider_finished - preverify_finished),
            ("terminal_rederivation", postverify_finished - provider_finished),
        )
        with _LOCK:
            witnesses = registration.witnesses
            if witnesses is None:
                raise ContractViolation("selected provider witness ledger is absent")
            witnesses.append(
                _ProviderOperationWitness(
                    execution.sequence,
                    fresh.invocation.digest.value,
                    fresh.input_closure_digest.value,
                    tuple(
                        (
                            coordinate.role,
                            coordinate.contract.key,
                            coordinate.contract.version,
                            coordinate.contract.schema_digest.value,
                            coordinate.value_ref,
                            coordinate.digest.value,
                            coordinate.size_bytes,
                        )
                        for coordinate in fresh.invocation.inputs
                    ),
                )
            )
        if registration.execution_lifecycle is not None:
            if registration.execution_lifecycle.terminal_mode == "runtime_completion":
                with _LOCK:
                    if execution.lifecycle != "executing":
                        raise ContractViolation("selected terminal state changed")
                    execution.terminal_derivation = result
                    execution.terminal_thread = get_ident()
                    execution.lifecycle = "terminalizing"
                completion = runtime._complete_selected_derivation(admission, result)
                _fresh_step_invocation(runtime, registration, execution)
                registration.execution_lifecycle.call(
                    "validate", execution.lifecycle_use, execution.closure
                )
                _OBSERVATION_ISSUER.provisional(execution, completion)
                _fresh_step_invocation(runtime, registration, execution)
                if not runtime.owns_completion(completion):
                    raise ContractViolation("observed provisional completion changed")
                result = completion
            registration.execution_lifecycle.call(
                "complete", execution.lifecycle_use, result
            )
        _OBSERVATION_ISSUER.succeed(execution)
        completed = True
        return result
    except BaseException as error:
        if completion is not None:
            with runtime._publication_records_lock:
                runtime._publication_records.pop(completion, None)
        try:
            _OBSERVATION_ISSUER.fail(execution)
        except BaseException:  # noqa: BLE001 - terminal cleanup must run for cancellation too.
            BaseException.add_note(error, "selected observer abort failed")
        if registration.execution_lifecycle is not None:
            try:
                registration.execution_lifecycle.call("fail", execution.lifecycle_use)
            except BaseException:  # noqa: BLE001 - preserve the original error after all cleanup.
                BaseException.add_note(error, "selected lifecycle abort failed")
        if registration.selected_invocation_observer is not None:
            _OBSERVATION_ISSUER.release_failed(execution, error)
            # These locals belong to the active frame, which Frame.clear()
            # cannot clear while its exception is being propagated.
            fresh = result = completion = None
        raise
    finally:
        with _LOCK:
            retained = _EXECUTIONS.pop(id(admission), None)
            if retained is not None and retained[0] is admission:
                retained[1].lifecycle = "completed" if completed else "failed"
                _TERMINAL_EXECUTIONS[admission] = retained[1].lifecycle


def _execute_probe(
    probe: SelectedSemanticProviderProbe, semantic_input: object
) -> object:
    probe_state = _probe_state(probe)
    started = perf_counter_ns()
    admission = issue_selected_provider_execution(
        probe_state.runtime,
        probe_state.registration,
        semantic_input,
        _uninterrupted_probe_token=_UNINTERRUPTED_PROBE_TOKEN,
    )
    result = execute_selected_provider(probe_state.runtime, admission)
    finished = perf_counter_ns()
    probe._last_timings_ns = (
        *admission._issue_timings_ns,
        *admission._timings_ns,
        ("selected_provider_total", finished - started),
    )
    return result


_QUALIFICATION_PHASE_ORDER = (
    "bootstrap",
    "operational_current",
    "operational_delta",
)


def _qualification_session_state(
    session: _SelectedProviderQualificationSession,
) -> _QualificationSessionState:
    if type(session) is not _SelectedProviderQualificationSession:
        raise TypeError("selected-provider qualification session must be exact")
    retained = _QUALIFICATION_SESSIONS.get(id(session))
    if retained is None or retained[0] is not session:
        raise ContractViolation(
            "selected-provider qualification session is not admitted"
        )
    state = retained[1]
    if state.closed:
        raise ContractViolation("selected-provider qualification session is closed")
    if state.creator_pid != os.getpid() or state.creator_thread != get_ident():
        raise ContractViolation(
            "selected-provider qualification session belongs to another owner"
        )
    if session._token is not _QUALIFICATION_SESSION_TOKEN:
        raise ContractViolation("selected-provider qualification session token differs")
    probe_state = _probe_state(state.probe)
    registration = _registration_state(state.registration)
    if (
        registration.runtime is not state.runtime
        or registration.selection_root is not state.selection_root
        or probe_state.registration is not state.registration
        or probe_state.runtime is not state.runtime
    ):
        raise ContractViolation("selected-provider qualification context changed")
    return state


def _open_selected_provider_qualification_session(
    probe: SelectedSemanticProviderProbe,
) -> _SelectedProviderQualificationSession:
    if type(probe) is not SelectedSemanticProviderProbe:
        raise TypeError("qualification requires an exact selected-provider probe")
    with _LOCK:
        probe_state = _probe_state(probe)
        registration = _registration_state(probe_state.registration)
        witnesses = registration.witnesses
        if registration.runtime is not probe_state.runtime or witnesses is None:
            raise ContractViolation("qualification probe context differs")
        if registration.sequence != 0 or witnesses:
            raise ContractViolation(
                "qualification requires a fresh provider registration"
            )
        session = _SelectedProviderQualificationSession(_QUALIFICATION_SESSION_TOKEN)
        _QUALIFICATION_SESSIONS[id(session)] = (
            session,
            _QualificationSessionState(
                probe=probe,
                registration=probe_state.registration,
                selection_root=registration.selection_root,
                runtime=probe_state.runtime,
                creator_pid=os.getpid(),
                creator_thread=get_ident(),
                completed_bindings=[],
            ),
        )
        return session


def _begin_selected_provider_qualification_phase(
    session: _SelectedProviderQualificationSession,
    phase: str,
    *,
    expected_operation_count: int,
) -> _SelectedProviderQualificationPhaseBinding:
    if type(phase) is not str or phase not in _QUALIFICATION_PHASE_ORDER:
        raise ValueError("selected-provider qualification phase differs")
    if type(expected_operation_count) is not int or expected_operation_count <= 0:
        raise ValueError("selected-provider expected operation count is invalid")
    with _LOCK:
        state = _qualification_session_state(session)
        if state.active_phase is not None:
            raise ContractViolation("selected-provider qualification phase is active")
        if (
            state.next_phase_index >= len(_QUALIFICATION_PHASE_ORDER)
            or _QUALIFICATION_PHASE_ORDER[state.next_phase_index] != phase
        ):
            raise ContractViolation(
                "selected-provider qualification phase order differs"
            )
        registration = _registration_state(state.registration)
        witnesses = registration.witnesses
        if witnesses is None:
            raise ContractViolation("selected-provider witness ledger is absent")
        binding = _SelectedProviderQualificationPhaseBinding(_QUALIFICATION_PHASE_TOKEN)
        _QUALIFICATION_PHASES[id(binding)] = (
            binding,
            _QualificationPhaseState(
                session=session,
                phase=phase,
                phase_index=state.next_phase_index,
                start_witness_index=len(witnesses),
                expected_operation_count=expected_operation_count,
            ),
        )
        state.active_phase = binding
        return binding


def _finish_selected_provider_qualification_phase(
    binding: _SelectedProviderQualificationPhaseBinding,
) -> _SelectedProviderQualificationPhaseBinding:
    if type(binding) is not _SelectedProviderQualificationPhaseBinding:
        raise TypeError("selected-provider phase binding must be exact")
    with _LOCK:
        retained = _QUALIFICATION_PHASES.get(id(binding))
        if retained is None or retained[0] is not binding:
            raise ContractViolation("selected-provider phase binding is not admitted")
        phase = retained[1]
        if phase.lifecycle != "active":
            raise ContractViolation("selected-provider phase binding is not active")
        session = _qualification_session_state(phase.session)
        if session.active_phase is not binding:
            raise ContractViolation("selected-provider active phase differs")
        registration = _registration_state(session.registration)
        witness_ledger = registration.witnesses
        if witness_ledger is None:
            raise ContractViolation("selected-provider witness ledger is absent")
        witnesses = tuple(witness_ledger[phase.start_witness_index :])
        if len(witnesses) != phase.expected_operation_count:
            phase.lifecycle = "failed"
            session.closed = True
            registration.closed = True
            raise ContractViolation(
                "selected-provider qualification operation count differs"
            )
        expected_sequences = tuple(
            range(witnesses[0].sequence, witnesses[0].sequence + len(witnesses))
        )
        if tuple(item.sequence for item in witnesses) != expected_sequences:
            phase.lifecycle = "failed"
            session.closed = True
            registration.closed = True
            raise ContractViolation(
                "selected-provider qualification operation order differs"
            )
        phase.witnesses = witnesses
        phase.lifecycle = "completed"
        session.active_phase = None
        session.next_phase_index += 1
        if session.completed_bindings is None:
            raise ContractViolation(
                "selected-provider completed phase ledger is absent"
            )
        session.completed_bindings.append(binding)
        return binding


def _selected_provider_phase_witnesses(
    binding: _SelectedProviderQualificationPhaseBinding,
) -> tuple[
    tuple[
        int,
        str,
        str,
        tuple[tuple[str, str, str, str, str, str, int], ...],
    ],
    ...,
]:
    if type(binding) is not _SelectedProviderQualificationPhaseBinding:
        raise TypeError("selected-provider phase binding must be exact")
    retained = _QUALIFICATION_PHASES.get(id(binding))
    if (
        retained is None
        or retained[0] is not binding
        or retained[1].lifecycle != "completed"
    ):
        raise ContractViolation("selected-provider phase binding is not completed")
    _qualification_session_state(retained[1].session)
    return tuple(
        (
            item.sequence,
            item.invocation_digest,
            item.input_closure_digest,
            item.input_coordinates,
        )
        for item in retained[1].witnesses
    )


def _consume_selected_provider_qualification_session(
    bindings: tuple[_SelectedProviderQualificationPhaseBinding, ...],
) -> None:
    if type(bindings) is not tuple or len(bindings) != 3:
        raise TypeError(
            "selected-provider qualification bindings must be an exact triplet"
        )
    with _LOCK:
        retained_phases: list[_QualificationPhaseState] = []
        for binding in bindings:
            if type(binding) is not _SelectedProviderQualificationPhaseBinding:
                raise TypeError("selected-provider qualification binding must be exact")
            retained = _QUALIFICATION_PHASES.get(id(binding))
            if retained is None or retained[0] is not binding:
                raise ContractViolation(
                    "selected-provider qualification binding is absent"
                )
            retained_phases.append(retained[1])
        session_handle = retained_phases[0].session
        try:
            if any(item.session is not session_handle for item in retained_phases):
                raise ContractViolation(
                    "selected-provider qualification sessions differ"
                )
            session = _qualification_session_state(session_handle)
            if session.active_phase is not None or session.next_phase_index != 3:
                raise ContractViolation(
                    "selected-provider qualification session is incomplete"
                )
            if session.completed_bindings != list(bindings):
                raise ContractViolation(
                    "selected-provider qualification bindings differ"
                )
            if tuple(item.phase for item in retained_phases) != (
                _QUALIFICATION_PHASE_ORDER
            ):
                raise ContractViolation(
                    "selected-provider qualification phase order differs"
                )
            for item in retained_phases:
                if item.lifecycle != "completed" or not item.witnesses:
                    raise ContractViolation(
                        "selected-provider qualification phase is incomplete"
                    )
                item.lifecycle = "consumed"
            session.closed = True
            registration = _registration_state(session.registration)
            registration.closed = True
        except BaseException:
            retained_session = _QUALIFICATION_SESSIONS.get(id(session_handle))
            if retained_session is not None and retained_session[0] is session_handle:
                failed = retained_session[1]
                failed.closed = True
                retained_registration = _REGISTRATIONS.get(id(failed.registration))
                if (
                    retained_registration is not None
                    and retained_registration[0] is failed.registration
                ):
                    retained_registration[1].closed = True
            raise


def _fail_selected_provider_qualification_session(
    session: _SelectedProviderQualificationSession,
) -> None:
    with _LOCK:
        if type(session) is not _SelectedProviderQualificationSession:
            raise TypeError("selected-provider qualification session must be exact")
        retained_session = _QUALIFICATION_SESSIONS.get(id(session))
        if retained_session is None or retained_session[0] is not session:
            raise ContractViolation(
                "selected-provider qualification session is not admitted"
            )
        state = retained_session[1]
        if state.closed:
            return
        if state.creator_pid != os.getpid() or state.creator_thread != get_ident():
            raise ContractViolation(
                "selected-provider qualification session belongs to another owner"
            )
        if state.active_phase is not None:
            retained = _QUALIFICATION_PHASES.get(id(state.active_phase))
            if retained is not None and retained[0] is state.active_phase:
                retained[1].lifecycle = "failed"
        state.closed = True
        retained_registration = _REGISTRATIONS.get(id(state.registration))
        if (
            retained_registration is not None
            and retained_registration[0] is state.registration
        ):
            retained_registration[1].closed = True


@dataclass(slots=True)
class _ObservedInvocation:
    reference: ReferenceType[SelectedInvocationUse]
    runtime: Any
    admission: Any
    execution: Any
    registration: Any
    originals: Any
    step_nodes: Any
    thread: Thread
    pid: int
    phase: str = "associated"
    completion: Any = None
    terminal_success: bool = False
    invalid: bool = False


@dataclass(frozen=True, slots=True)
class _ObservationIssuer:
    associate: Any
    notify: Any
    provisional: Any
    succeed: Any
    fail: Any
    check: Any
    close: Any
    release_failed: Any
    require: Any
    project: Any


def _selected_invocation_inputs(use, provider, *, release=False):
    """Use the original registration's captured lifecycle, never a callback argument."""
    try:
        record = _require_observed_invocation(use, provider)
        evidence = require_selected_invocation(use, provider)
        lifecycle = record.registration.execution_lifecycle
        name = "release_inputs" if release else "verify_inputs"
        if lifecycle is None or name not in lifecycle.entrances:
            raise ContractViolation("selected input verification was not bound")
        if evidence.phase == "failed":
            raise ContractViolation("failed invocation has no input verification authority")
        result = lifecycle.call(name, record.execution.lifecycle_use, evidence)
        if result is not None:
            raise ContractViolation("selected input verifier returned a value")
        if not release:
            final = require_selected_invocation(use, provider)
            if (final.admission is not evidence.admission
                    or final.semantic_input is not evidence.semantic_input
                    or final.closure is not evidence.closure
                    or final.completion is not evidence.completion
                    or final.phase != evidence.phase
                    or final.terminal_success is not evidence.terminal_success):
                raise ContractViolation("selected input invocation changed during verification")
    except BaseException as error:
        evidence = final = lifecycle = name = provider = record = release = result = use = None
        _clear_input_rejection_frames(error, __file__)
        raise


def _make_observation_issuer():
    """One private identity table, with independent native record retirement."""
    records: dict[int, _ObservedInvocation] = {}
    active: dict[int, int] = {}
    native_id, native_type, native_get = id, type, object.__getattribute__
    native_pop, native_lookup = dict.pop, dict.get
    native_pid, native_thread = os.getpid, current_thread
    native_error, native_exception = ContractViolation, BaseException
    native_items, native_tuple = dict.items, tuple
    native_reference_call = ReferenceType.__call__
    use_type, evidence_type = SelectedInvocationUse, SelectedInvocationEvidence
    check_execution = _execution_state
    check_registration = _registration_state
    check_root = _selection_root_state
    check_observer = _check_observer_registration
    check_step = _fresh_step_invocation
    namespace = globals()
    builtins_namespace = _python_builtins.__dict__
    inspect_namespace = inspect.__dict__
    entrances = tuple((function.__name__, function, object.__getattribute__(function, "__code__")) for function in (
        check_execution, check_registration, check_root, check_observer, check_step,
        _observer_intact, _bound_function, _observed_step_nodes, _selected_invocation_inputs,
        _check_execution_lifecycle,
    ))
    primitives = tuple((name, native_lookup(namespace, name, native_lookup(builtins_namespace, name)))
                       for name in ("type", "id", "all", "getattr", "object", "tuple", "any", "len", "zip", "int"))
    classes = tuple(
        (cls, name, descriptor)
        for cls in (
            use_type, evidence_type, _ObservedInvocation, _RegistrationState, _ExecutionState,
            _SelectionRootState, _ExecutionLifecycle, AdmittedSemanticProviderSelectionRoot,
            AdmittedSemanticProviderRegistration, SelectedSemanticProviderExecutionAdmission,
            ProviderStepInvocation, BoundSemanticInput, AdmittedSemanticValue,
        )
        for name, descriptor in type.__getattribute__(cls, "__dict__").items()
    )
    original_static = inspect.getattr_static
    lifecycle_call = _ExecutionLifecycle.call
    lifecycle_call_code = lifecycle_call.__code__
    class_dict = type.__getattribute__
    record_type = _ObservedInvocation
    slots = {name: descriptor for cls, name, descriptor in classes
             if cls is record_type and native_type(descriptor) is MemberDescriptorType}
    slot_get, slot_set = MemberDescriptorType.__get__, MemberDescriptorType.__set__
    registration_provider_slot = class_dict(_RegistrationState, "__dict__")["provider"]
    execution_use_slot = class_dict(_ExecutionState, "__dict__")["observed_use"]
    execution_type = _ExecutionState
    execution_slots = {
        name: class_dict(execution_type, "__dict__")[name]
        for name in (
            "semantic_input", "closure", "step_invocation", "primitive_snapshot", "step_guard",
            "terminal_derivation", "input_evidence", "predecessor_evidence", "closure_body",
        )
    }
    traceback_get = class_dict(BaseException, "__dict__")["__traceback__"].__get__
    traceback_frame_get = class_dict(TracebackType, "__dict__")["tb_frame"].__get__
    traceback_next_get = class_dict(TracebackType, "__dict__")["tb_next"].__get__
    frame_code_get = class_dict(FrameType, "__dict__")["f_code"].__get__
    code_filename_get = class_dict(type(_make_observation_issuer.__code__), "__dict__")["co_filename"].__get__
    frame_clear, frame_error = FrameType.clear, RuntimeError
    owner_filename = _make_observation_issuer.__code__.co_filename

    def get_record(record, name):
        return slot_get(slots[name], record, record_type)

    def set_record(record, name, value):
        slot_set(slots[name], record, value)

    def guard():
        for name, function, code in entrances:
            if native_lookup(namespace, name) is not function or native_get(function, "__code__") is not code:
                raise native_error("selected invocation verifier entrance changed")
        for name, function, code in api_entrances:
            if native_lookup(namespace, name) is not function or native_get(function, "__code__") is not code:
                raise native_error("selected invocation original public entrance changed")
        if native_lookup(namespace, "_OBSERVATION_ISSUER") is not issuer:
            raise native_error("selected invocation issuer substituted")
        for name, original in primitives:
            if native_lookup(namespace, name, native_lookup(builtins_namespace, name)) is not original:
                raise native_error("selected invocation native primitive changed")
        for cls, name, descriptor in classes:
            if class_dict(cls, "__dict__").get(name) is not descriptor:
                raise native_error("selected invocation original class/descriptor changed")
        if native_get(lifecycle_call, "__code__") is not lifecycle_call_code:
            raise native_error("selected lifecycle call code changed")
        if native_lookup(inspect_namespace, "getattr_static") is not original_static:
            raise native_error("selected invocation descriptor verifier changed")
        if native_lookup(namespace, "SelectedInvocationUse") is not use_type or native_lookup(namespace, "SelectedInvocationEvidence") is not evidence_type:
            raise native_error("selected invocation original nominal class changed")

    def retire(key):
        record = native_pop(records, key, None)
        if record is None:
            return
        registration = get_record(record, "registration")
        if registration is not None:
            provider_key = native_id(slot_get(registration_provider_slot, registration, _RegistrationState))
            if native_lookup(active, provider_key) == key:
                native_pop(active, provider_key, None)
        execution = get_record(record, "execution")
        if execution is not None:
            slot_set(execution_use_slot, execution, None)
        for name in ("runtime", "admission", "execution", "registration", "originals", "step_nodes", "completion"):
            set_record(record, name, None)
        set_record(record, "terminal_success", False)

    def require(use, provider):
        if native_type(use) is not use_type:
            raise native_error("exact original selected invocation use required")
        key = native_id(use)
        record = native_lookup(records, key)
        if record is None:
            raise native_error("selected invocation use is unavailable")
        reference = get_record(record, "reference")
        if native_type(reference) is not ReferenceType or native_reference_call(reference) is not use:
            raise native_error("selected invocation use is unavailable")
        try:
            guard()
            if get_record(record, "invalid") and get_record(record, "phase") != "failed":
                raise native_error("selected invocation use has been revoked")
            if (
                record.pid != native_pid() or native_thread() is not record.thread
                or not record.thread.is_alive()
            ):
                raise native_error("selected invocation process/thread changed")
            registration = check_registration(record.execution.registration)
            root = check_root(registration.selection_root)
            if registration is not record.registration or registration.runtime is not record.runtime:
                raise native_error("original observed registration changed")
            if provider is not registration.provider or native_type(provider) is not root.provider_type:
                raise native_error("original observed provider changed")
            original = record.originals
            execution = record.execution
            if (
                record.runtime is not original[0]
                or execution.registration is not original[1]
                or registration.provider is not original[2]
                or record.admission is not original[3]
                or execution.semantic_input is not original[4]
                or execution.closure is not original[5]
                or execution.step_invocation is not original[6]
                or native_type(execution.sequence) is not int or execution.sequence != original[7]
                or registration.execution_lifecycle is not original[8]
                or execution.lifecycle_use is not original[9]
            ):
                raise native_error("original observed invocation identity changed")
            check_observer(registration, root)
            if record.phase == "failed":
                # Available only during original terminal notification. It is
                # an attribution of failure, never dispatch/read authority.
                return record
            current_nodes = _observed_step_nodes(execution.step_invocation)
            if len(current_nodes) != len(record.step_nodes) or any(
                observed is not original for observed, original in zip(current_nodes, record.step_nodes, strict=True)
            ):
                raise native_error("original observed step node changed")
            check_step(record.runtime, registration, record.execution)
            if record.terminal_success:
                if record.execution.lifecycle != "completed" or not record.runtime.owns_completion(record.completion):
                    raise native_error("original successful completion changed")
            else:
                execution, current = check_execution(record.runtime, record.admission)
                if execution is not record.execution or current is not registration:
                    raise native_error("original observed execution changed")
            return record
        except native_exception:
            # Preserve the original handle long enough to notify its owner.
            # Successful historical uses can retire immediately.
            set_record(record, "invalid", True)
            if get_record(record, "terminal_success"):
                retire(key)
            raise

    def project(use, provider):
        record = require(use, provider)
        execution = record.execution
        return evidence_type(
            record.runtime, execution.registration, record.registration.provider,
            record.admission, execution.semantic_input, execution.closure,
            execution.step_invocation, execution.sequence, record.phase,
            record.completion, record.terminal_success,
        )

    def notify(execution, event):
        use = execution.observed_use
        if use is None:
            return
        record = require(use, check_registration(execution.registration).provider)
        record.phase = event
        observer = record.registration.selected_invocation_observer
        if observer(event, use) is not None:
            raise native_error("selected invocation observer must return None")
        require(use, record.registration.provider)

    def check(execution):
        use = slot_get(execution_use_slot, execution, _ExecutionState)
        if use is not None:
            record = native_lookup(records, native_id(use))
            if record is None:
                raise native_error("original observed invocation unavailable")
            registration = get_record(record, "registration")
            provider = slot_get(registration_provider_slot, registration, _RegistrationState)
            require(use, provider)

    def associate(runtime, admission):
        execution, registration = check_execution(runtime, admission)
        provider_key = native_id(registration.provider)
        if provider_key in active:
            raise native_error("selected observer already has an active invocation")
        use = object.__new__(use_type)
        key = native_id(use)

        def collected(reference):
            record = native_lookup(records, key)
            if record is not None and record.reference is reference:
                retire(key)

        records[key] = _ObservedInvocation(
            ref(use, collected), runtime, admission, execution, registration,
            (runtime, execution.registration, registration.provider, admission,
             execution.semantic_input, execution.closure, execution.step_invocation, execution.sequence,
             registration.execution_lifecycle, execution.lifecycle_use),
            _observed_step_nodes(execution.step_invocation),
            native_thread(), native_pid(),
        )
        active[provider_key] = key
        execution.observed_use = use
        try:
            notify(execution, "associated")
        except native_exception:
            fail(execution)
            raise

    def provisional(execution, completion):
        use = execution.observed_use
        if use is None:
            return
        record = require(use, check_registration(execution.registration).provider)
        if record.completion is not None or not record.runtime.owns_completion(completion):
            raise native_error("original observed terminal completion required once")
        record.completion = completion
        notify(execution, "complete")

    def succeed(execution):
        use = execution.observed_use
        if use is None:
            return
        record = require(use, check_registration(execution.registration).provider)
        if record.phase != "complete" or not record.runtime.owns_completion(record.completion):
            raise native_error("original observed completion has not passed terminal checks")
        execution.lifecycle = "completed"
        record.terminal_success = True
        native_pop(active, native_id(record.registration.provider), None)
        # The weak use, rather than the record's execution, controls retention.
        execution.observed_use = None

    def fail(execution):
        use = slot_get(execution_use_slot, execution, _ExecutionState)
        if use is None:
            return
        key = native_id(use)
        record = native_lookup(records, key)
        if record is None:
            slot_set(execution_use_slot, execution, None)
            return
        try:
            # A failure event is best effort. Never call a substituted observer.
            guard()
            registration = get_record(record, "registration")
            root = check_root(registration.selection_root)
            check_observer(registration, root)
            record.phase = "failed"
            record.completion = None
            record.terminal_success = False
            if registration.selected_invocation_observer("failed", use) is not None:
                raise native_error("selected invocation observer must return None")
        finally:
            retire(key)

    def close(registration):
        for key, record in native_tuple(native_items(records)):
            if get_record(record, "originals")[1] is registration:
                retire(key)

    def release_failed(execution, error=None):
        # No current namespace/class method participates in native retirement.
        # Only Code-owned execution graphs/Code frames are cleared. Owner and
        # Workspace resources remain their owners' responsibility.
        for descriptor in execution_slots.values():
            slot_set(descriptor, execution, None)
        if error is not None:
            traceback = traceback_get(error)
            while traceback is not None:
                frame = traceback_frame_get(traceback)
                if code_filename_get(frame_code_get(frame)) == owner_filename:
                    try:
                        frame_clear(frame)
                    except frame_error:
                        pass  # Active callers clear their own retained locals.
                traceback = traceback_next_get(traceback)

    issuer = _ObservationIssuer(
        associate=associate, notify=notify, provisional=provisional,
        succeed=succeed, fail=fail, check=check, close=close, release_failed=release_failed,
        require=require, project=project,
    )
    def public(use: SelectedInvocationUse, provider: object) -> SelectedInvocationEvidence:
        """Authenticate fresh original attribution; detached evidence is not authority."""
        return project(use, provider)

    def private(use, provider):
        """Code-only original record join for the existing predecessor grant issuer."""
        return require(use, provider)

    public.__name__ = "require_selected_invocation"
    private.__name__ = "_require_observed_invocation"
    api_entrances = (
        (public.__name__, public, public.__code__),
        (private.__name__, private, private.__code__),
    )
    return issuer, public, private


_OBSERVATION_ISSUER, require_selected_invocation, _require_observed_invocation = _make_observation_issuer()


__all__ = [
    "AdmittedSemanticProviderRegistration",
    "AdmittedSemanticProviderSelectionRoot",
    "SelectedInvocationEvidence",
    "SelectedInvocationUse",
    "SelectedProviderInvocationClosure",
    "SelectedSemanticProviderExecutionAdmission",
    "SelectedSemanticProviderProbe",
    "close_selected_provider_registration",
    "execute_selected_provider",
    "issue_selected_provider_execution",
    "register_selected_provider",
    "require_selected_invocation",
    "selected_provider_probe",
    "validate_selected_provider_registration",
]
