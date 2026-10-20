"""Detached typed observations through an explicitly supplied original reader.

Binding checks correspondence, not permission. The infrastructure reader owns
fresh caller admission, configuration/history selection and backend I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Protocol, Self, TypeVar, cast
from uuid import uuid4

from aware_meta_type_schema import TypeKind, TypeSchemaBundle, ValueShape

from .object_snapshot_codec import encode_object_snapshot_data
from .owner_values import (
    CoverageGrade,
    OntologyObjectClassBinding,
    OntologyObjectSnapshotData,
    OntologyRuntimeActionInstanceRefTarget,
    ProjectionCoverage,
    ScalarKind,
    ShapeKind,
)

MAX_SNAPSHOT_BYTES = 262_144
MAX_CORRESPONDENCE_BYTES = 262_144
_KINDS = {ScalarKind.BOOLEAN: bool, ScalarKind.INTEGER: int, ScalarKind.STRING: str}
_State = TypeVar("_State", bound="OntologyObjectState")


def _enum_members(
    shape: ValueShape, schema: TypeSchemaBundle | None
) -> tuple[str, ...]:
    if schema is None or shape.kind is not ShapeKind.NAMED:
        return ()
    matches = tuple(t for t in schema.types if t.type_ref == shape.type_ref)
    return (
        matches[0].enum_values
        if len(matches) == 1 and matches[0].kind is TypeKind.ENUM
        else ()
    )


class ObjectReadError(RuntimeError):
    """An acquisition failed; no partially hydrated state is returned."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _text(value: object) -> bool:
    return (
        type(value) is str
        and 0 < len(value.encode("utf-8")) <= 4096
        and "\0" not in value
    )


def _digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 71
        and value.startswith("sha256:")
        and all(c in "0123456789abcdef" for c in value[7:])
    )


@dataclass(frozen=True, slots=True)
class ObjectReadRequest:
    """Read selection data. None of these coordinates grants authority."""

    read_ref: str
    target: OntologyRuntimeActionInstanceRefTarget
    binding_digest: str
    fragment_closure_digest: str
    configuration_binding: bytes
    expected_revision_ref: str | None


@dataclass(frozen=True, slots=True)
class ObjectReadResult:
    """Original snapshot and owner-projected history; not a live capability."""

    read_ref: str
    snapshot: OntologyObjectSnapshotData
    configuration_binding: bytes
    history_correspondence: bytes
    coverage: ProjectionCoverage
    field_refs: tuple[str, ...]


class ObjectReadInvoker(Protocol):
    async def acquire(self, request: ObjectReadRequest, /) -> ObjectReadResult:
        """Authenticate this read, observe state and release owned resources."""
        ...


class OntologyObjectState:
    """Generated immutable field surface. It carries no Action or reader port."""

    __slots__ = ("_values",)
    __ontology_type_ref__: ClassVar[str]
    __ontology_binding_digest__: ClassVar[str]
    __ontology_dependency_closure_digest__: ClassVar[str]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if "get" in cls.__dict__:
            raise ObjectReadError("read.state_helper_collision:get")

    @classmethod
    async def get(
        cls,
        object_reference: OntologyRuntimeActionInstanceRefTarget,
        *,
        using: ObjectReadContext,
        expected_revision_ref: str | None = None,
    ) -> ObjectObservation[Self]:
        """Acquire a fresh observation through an explicitly injected context."""
        return await using.bind(cls, object_reference).acquire(
            expected_revision_ref=expected_revision_ref
        )

    def __init__(self, values: tuple[tuple[str, bool | int | str | None], ...]) -> None:
        object.__setattr__(self, "_values", values)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Object state is immutable")

    def _read_field(self, field_ref: str) -> bool | int | str | None:
        for ref, value in self._values:
            if ref == field_ref:
                return value
        raise ObjectReadError("read.field_not_covered")


@dataclass(frozen=True, slots=True)
class ObjectObservation[State: OntologyObjectState]:
    state: State
    snapshot: OntologyObjectSnapshotData
    history_correspondence: bytes
    coverage: ProjectionCoverage
    field_refs: tuple[str, ...]

    @property
    def revision_ref(self) -> str:
        return self.snapshot.authority.revision_ref

    @property
    def branch_ref(self) -> str:
        return self.snapshot.authority.branch_ref


@dataclass(slots=True)
class _ReadLifetime:
    closed: bool = False


@dataclass(frozen=True, slots=True)
class ObjectReadContext:
    """Reusable infrastructure wiring. Acquisition remains separately admitted."""

    binding: OntologyObjectClassBinding
    fragment_closure_digest: str
    provider_key: str
    provider_generation: str
    branch_ref: str
    projection_ref: str
    configuration_binding: bytes
    invoker: ObjectReadInvoker
    schema: TypeSchemaBundle | None = None
    _lifetime: _ReadLifetime = field(
        default_factory=_ReadLifetime, init=False, repr=False
    )

    def __post_init__(self) -> None:
        if (
            type(self.binding) is not OntologyObjectClassBinding
            or not _digest(self.fragment_closure_digest)
            or any(
                not _text(v)
                for v in (
                    self.provider_key,
                    self.provider_generation,
                    self.branch_ref,
                    self.projection_ref,
                )
            )
            or type(self.configuration_binding) is not bytes
            or not 0 < len(self.configuration_binding) <= MAX_CORRESPONDENCE_BYTES
            or self.schema is not None
            and type(self.schema) is not TypeSchemaBundle
        ):
            raise ObjectReadError("read.invalid_context")
        for member in self.binding.fields:
            if member.attribute_name == "get":
                raise ObjectReadError("read.state_helper_collision:get")
            if not (
                member.shape.kind is ShapeKind.SCALAR
                and member.shape.scalar_kind in _KINDS
            ) and not _enum_members(member.shape, self.schema):
                raise ObjectReadError("read.unsupported_profile")

    def close(self) -> None:
        """Stop new acquisitions without closing a borrowed host or transport."""
        self._lifetime.closed = True

    def bind(
        self,
        state_type: type[_State],
        target: OntologyRuntimeActionInstanceRefTarget,
    ) -> ObjectReadSelection[_State]:
        self._require_open()
        if (
            not isinstance(state_type, type)
            or not issubclass(state_type, OntologyObjectState)
            or getattr(state_type, "__ontology_type_ref__", None)
            != self.binding.type_ref
            or getattr(state_type, "__ontology_binding_digest__", None)
            != self.binding.binding_digest
            or getattr(state_type, "__ontology_dependency_closure_digest__", None)
            != self.fragment_closure_digest
            or self.schema is not None
            and getattr(state_type, "__ontology_schema_digest__", None)
            != self.schema.schema_digest
            or type(target) is not OntologyRuntimeActionInstanceRefTarget
            or target.type_ref != self.binding.type_ref
            or target.provider_key != self.provider_key
            or target.provider_generation != self.provider_generation
        ):
            raise ObjectReadError("read.binding_mismatch")
        return ObjectReadSelection(self, state_type, target)

    def _require_open(self) -> None:
        if self._lifetime.closed:
            raise ObjectReadError("read.context_closed")


@dataclass(frozen=True, slots=True)
class ObjectReadSelection[State: OntologyObjectState]:
    context: ObjectReadContext
    state_type: type[State]
    target: OntologyRuntimeActionInstanceRefTarget

    async def acquire(
        self, *, expected_revision_ref: str | None = None
    ) -> ObjectObservation[State]:
        context = self.context
        context._require_open()
        if expected_revision_ref is not None and not _text(expected_revision_ref):
            raise ObjectReadError("read.invalid_revision")
        request = ObjectReadRequest(
            "read:" + uuid4().hex,
            self.target,
            context.binding.binding_digest,
            context.fragment_closure_digest,
            context.configuration_binding,
            expected_revision_ref,
        )
        result = await context.invoker.acquire(request)
        context._require_open()
        if (
            type(result) is not ObjectReadResult
            or result.read_ref != request.read_ref
            or type(result.snapshot) is not OntologyObjectSnapshotData
            or result.configuration_binding != context.configuration_binding
            or type(result.history_correspondence) is not bytes
            or not 0 < len(result.history_correspondence) <= MAX_CORRESPONDENCE_BYTES
            or type(result.coverage) is not ProjectionCoverage
            or result.coverage.grade is not CoverageGrade.COMPLETE
            or result.coverage.missing_refs
            or type(result.field_refs) is not tuple
        ):
            raise ObjectReadError("read.invalid_result")
        if len(encode_object_snapshot_data(result.snapshot)) > MAX_SNAPSHOT_BYTES:
            raise ObjectReadError("read.limit_exceeded")
        snapshot, binding = result.snapshot, context.binding
        authority, value = snapshot.authority, snapshot.value
        provider = authority.provider_authority
        expected_fields = tuple(sorted(member.field_ref for member in binding.fields))
        if (
            value.type_ref != self.target.type_ref
            or value.instance_ref != self.target.instance_ref
            or authority.class_binding_digest != binding.binding_digest
            or authority.branch_ref != context.branch_ref
            or authority.projection_ref != context.projection_ref
            or (provider.provider_key, provider.provider_generation)
            != (context.provider_key, context.provider_generation)
            or result.field_refs != expected_fields
            or any(member.field_ref not in expected_fields for member in value.fields)
        ):
            raise ObjectReadError("read.binding_mismatch")
        if (
            expected_revision_ref is not None
            and authority.revision_ref != expected_revision_ref
        ):
            raise ObjectReadError("read.revision_conflict")
        fields = {
            member.field_ref: member.value.value.to_wire() for member in value.fields
        }
        values: list[tuple[str, bool | int | str | None]] = []
        for member in binding.fields:
            if member.field_ref not in fields:
                if member.required or not member.nullable:
                    raise ObjectReadError("read.field_not_covered")
                values.append((member.field_ref, None))
                continue
            item = fields[member.field_ref]
            if item is None:
                if not member.nullable:
                    raise ObjectReadError("read.invalid_field")
            elif member.shape.kind is ShapeKind.NAMED:
                if type(item) is not str or item not in _enum_members(
                    member.shape, context.schema
                ):
                    raise ObjectReadError("read.invalid_field")
            elif (
                member.shape.scalar_kind is None
                or type(item) is not _KINDS[member.shape.scalar_kind]
            ):
                raise ObjectReadError("read.invalid_field")
            values.append((member.field_ref, cast(bool | int | str | None, item)))
        return ObjectObservation(
            self.state_type(tuple(values)),
            snapshot,
            result.history_correspondence,
            result.coverage,
            result.field_refs,
        )
