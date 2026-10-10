from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from time import perf_counter_ns
from typing import Never, Protocol
from weakref import WeakKeyDictionary

from .codec import validate_result_context
from .contracts import (
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticContractInvocation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractResult,
    SemanticDependencyCoordinate,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from .profile import (
    ProfileStepDeclaration,
    SemanticContractProfileDeclaration,
    resolve_profile,
)


@dataclass(frozen=True, slots=True)
class SemanticBody:
    coordinate: SemanticValueCoordinate
    canonical_body: bytes

    def __post_init__(self) -> None:
        if type(self.coordinate) is not SemanticValueCoordinate:
            raise TypeError("body coordinate must be exact SemanticValueCoordinate")
        self.coordinate.to_wire()
        if type(self.canonical_body) is not bytes:
            raise TypeError("canonical body must be exact bytes")
        if ContentDigest.of_bytes(self.canonical_body) != self.coordinate.digest:
            raise ContractViolation("canonical body digest differs from coordinate")
        if len(self.canonical_body) != self.coordinate.size_bytes:
            raise ContractViolation("canonical body size differs from coordinate")


class SemanticBodyCodec(Protocol):
    @property
    def contract(self) -> SemanticContractRef: ...

    @property
    def implementation(self) -> SemanticImplementationCoordinate: ...

    def decode(self, canonical_body: bytes) -> object: ...

    def encode(self, value: object) -> bytes: ...


class InvocationValidatingSemanticBodyCodec(SemanticBodyCodec, Protocol):
    """Optional registered-codec check before any provider receives an input.

    Validators must be synchronous, return None, and preserve the input value
    and invocation. They validate correspondence; they do not issue authority.
    """

    def validate_invocation(
        self, value: object, invocation: SemanticContractInvocation
    ) -> None: ...


_BODY_ADMISSION = object()
_VALIDATION_EPOCH_CONSTRUCTION = object()
_VALIDATION_CONTEXT_REGISTRATION = object()


class AdmittedSemanticValue:
    __slots__ = (
        "_admission_token",
        "_canonical_body",
        "_codec",
        "_codec_implementation",
        "_context",
        "_coordinate",
        "_value",
    )

    def __init__(
        self,
        construction_token: object,
        body: SemanticBody,
        codec: SemanticBodyCodec,
        value: object,
        codec_implementation: SemanticImplementationCoordinate,
        context: SemanticBodyValidationContext | None = None,
        admission_token: object | None = None,
    ) -> None:
        if construction_token is not _BODY_ADMISSION:
            raise TypeError("AdmittedSemanticValue is runtime-constructed only")
        if admission_token is None:
            raise TypeError("admitted semantic value requires its Code admission token")
        self._admission_token = admission_token
        self._coordinate = body.coordinate
        self._canonical_body = body.canonical_body
        self._codec = codec
        self._value = value
        self._codec_implementation = codec_implementation
        self._context = context

    @property
    def coordinate(self) -> SemanticValueCoordinate:
        self._assert_intact()
        return self._coordinate

    @property
    def canonical_body(self) -> bytes:
        self._assert_intact()
        return self._canonical_body

    @property
    def value(self) -> object:
        self._assert_intact()
        return self._value

    def _assert_intact(self) -> None:
        self._coordinate.to_wire()
        contract = self._codec.contract
        implementation = self._codec.implementation
        if (
            type(contract) is not SemanticContractRef
            or contract != self._coordinate.contract
            or type(implementation) is not SemanticImplementationCoordinate
            or implementation != self._codec_implementation
        ):
            raise ContractViolation("semantic body codec changed after admission")
        if self._context is not None:
            self._context._assert_registered_body(
                self._admission_token,
                self._codec_implementation,
                self._coordinate,
                self._canonical_body,
            )
        encoded = _encode_with_context(self._codec, self._value, self._context)
        if type(encoded) is not bytes or encoded != self._canonical_body:
            raise ContractViolation("admitted semantic value changed after decode")
        if ContentDigest.of_bytes(encoded) != self._coordinate.digest:
            raise ContractViolation("admitted semantic value digest changed")
        if len(encoded) != self._coordinate.size_bytes:
            raise ContractViolation("admitted semantic value size changed")

    def _assert_publication_registration_intact(
        self,
        expected: _AdmittedPublicationIdentity,
    ) -> None:
        """Validate Code registration without re-entering a domain codec."""

        if type(expected) is not _AdmittedPublicationIdentity:
            raise TypeError("publication identity must be exact Code evidence")
        if expected.body is not self:
            raise ContractViolation("admitted publication body was transplanted")
        if self._admission_token is not expected.admission_token:
            raise ContractViolation("admitted publication token was transplanted")
        if self._context is not expected.context:
            raise ContractViolation("admitted publication context was transplanted")
        if type(self._coordinate) is not SemanticValueCoordinate:
            raise ContractViolation("admitted publication coordinate was restamped")
        self._coordinate.to_wire()
        if canonical_json_bytes(self._coordinate.to_wire()) != expected.coordinate_wire:
            raise ContractViolation("admitted publication coordinate was restamped")
        if type(self._canonical_body) is not bytes:
            raise ContractViolation("admitted publication body was restamped")
        if self._canonical_body != expected.canonical_body:
            raise ContractViolation("admitted publication body was restamped")
        if (
            ContentDigest.of_bytes(self._canonical_body) != self._coordinate.digest
            or len(self._canonical_body) != self._coordinate.size_bytes
        ):
            raise ContractViolation("admitted publication body differs from coordinate")
        if type(self._codec_implementation) is not SemanticImplementationCoordinate:
            raise ContractViolation("admitted publication codec was restamped")
        if (
            canonical_json_bytes(self._codec_implementation.to_wire())
            != expected.codec_implementation_wire
        ):
            raise ContractViolation("admitted publication codec was restamped")
        if expected.context is None:
            if expected.epoch is not None or expected.registration_snapshot is not None:
                raise ContractViolation(
                    "context-free publication evidence is malformed"
                )
            return
        if expected.epoch is None or expected.registration_snapshot is None:
            raise ContractViolation("contextual publication evidence is incomplete")
        if expected.context._validation_epoch is not expected.epoch:
            raise ContractViolation("admitted publication epoch was transplanted")
        if expected.context._execution_attempt_token is not expected.attempt_token:
            raise ContractViolation("admitted publication attempt was transplanted")
        observed = expected.context._assert_registered_body(
            self._admission_token,
            self._codec_implementation,
            self._coordinate,
            self._canonical_body,
        )
        if observed != expected.registration_snapshot:
            raise ContractViolation("admitted publication registration was restamped")

    def __reduce__(self) -> Never:
        raise TypeError("AdmittedSemanticValue is not serializable")


class _SemanticBodyValidationEpoch:
    __slots__ = (
        "_attempt_token",
        "_contexts",
        "_invocation_digest",
        "_profile_digest",
        "_provider_declaration_digest",
        "_provider_implementation",
        "_provider_key",
        "_runtime_token",
        "_witnesses",
    )

    def __init__(
        self,
        construction_token: object,
        runtime_token: object,
        attempt_token: object,
        invocation_digest: ContentDigest,
        profile_digest: ContentDigest,
        provider_key: str,
        provider_implementation: SemanticImplementationCoordinate,
        provider_declaration_digest: ContentDigest,
    ) -> None:
        if construction_token is not _VALIDATION_EPOCH_CONSTRUCTION:
            raise TypeError("validation epoch is Code-runtime-constructed only")
        if type(invocation_digest) is not ContentDigest:
            raise TypeError("validation epoch invocation digest must be exact")
        invocation_digest.to_wire()
        if type(profile_digest) is not ContentDigest:
            raise TypeError("validation epoch profile digest must be exact")
        profile_digest.to_wire()
        if type(provider_key) is not str or not provider_key:
            raise TypeError("validation epoch provider key must be exact nonempty str")
        if type(provider_implementation) is not SemanticImplementationCoordinate:
            raise TypeError("validation epoch provider implementation must be exact")
        provider_implementation.to_wire()
        if type(provider_declaration_digest) is not ContentDigest:
            raise TypeError(
                "validation epoch provider declaration digest must be exact"
            )
        provider_declaration_digest.to_wire()
        self._runtime_token = runtime_token
        self._attempt_token = attempt_token
        self._invocation_digest = invocation_digest
        self._profile_digest = profile_digest
        self._provider_key = provider_key
        self._provider_implementation = provider_implementation
        self._provider_declaration_digest = provider_declaration_digest
        self._contexts: dict[
            int, tuple[SemanticBodyValidationContext, tuple[object, ...]]
        ] = {}
        self._witnesses: dict[tuple[str, bytes], object] = {}

    def _assert_context(self, context: SemanticBodyValidationContext) -> None:
        if context._runtime_token is not self._runtime_token:
            raise ContractViolation("validation epoch runtime differs")
        if context._execution_attempt_token is not self._attempt_token:
            raise ContractViolation("validation epoch execution attempt differs")
        if context.invocation_digest != self._invocation_digest:
            raise ContractViolation("validation epoch invocation differs")
        if context._profile_digest != self._profile_digest:
            raise ContractViolation("validation epoch profile differs")
        if context.provider_key != self._provider_key:
            raise ContractViolation("validation epoch provider differs")
        if context._validation_epoch is not self:
            raise ContractViolation("validation context epoch differs")

    def register_context(
        self,
        construction_token: object,
        context: SemanticBodyValidationContext,
        admission_token: object,
        codec_implementation: SemanticImplementationCoordinate,
        coordinate: SemanticValueCoordinate,
        canonical_body: bytes,
    ) -> None:
        if construction_token is not _VALIDATION_CONTEXT_REGISTRATION:
            raise TypeError("validation context is Code-runtime-registered only")
        self._assert_context(context)
        snapshot = _validation_context_snapshot(
            context,
            admission_token,
            codec_implementation,
            coordinate,
            canonical_body,
        )
        key = id(context)
        prior = self._contexts.get(key)
        if prior is not None and (prior[0] is not context or prior[1] != snapshot):
            raise ContractViolation("validation context registration differs")
        self._contexts[key] = (context, snapshot)

    def assert_registered_context(
        self,
        context: SemanticBodyValidationContext,
        admission_token: object,
        codec_implementation: SemanticImplementationCoordinate,
        coordinate: SemanticValueCoordinate,
        canonical_body: bytes,
    ) -> tuple[object, ...]:
        self._assert_context(context)
        record = self._contexts.get(id(context))
        if record is None or record[0] is not context:
            raise ContractViolation("validation context is not registered")
        snapshot = _validation_context_snapshot(
            context,
            admission_token,
            codec_implementation,
            coordinate,
            canonical_body,
        )
        if record[1] != snapshot:
            raise ContractViolation("validation context changed after registration")
        return record[1]

    def registered_context_snapshot(
        self,
        context: SemanticBodyValidationContext,
    ) -> tuple[object, ...]:
        """Return the immutable snapshot captured at Code registration."""

        self._assert_context(context)
        record = self._contexts.get(id(context))
        if record is None or record[0] is not context:
            raise ContractViolation("validation context is not registered")
        return record[1]

    def witness(
        self,
        context: SemanticBodyValidationContext,
        namespace: str,
        key: bytes,
    ) -> object | None:
        if context._registered_admission_token is None:
            raise ContractViolation("validation context has no registered admission")
        implementation = context._registered_codec_implementation
        canonical_body = context._registered_canonical_body
        if type(implementation) is not SemanticImplementationCoordinate:
            raise ContractViolation("validation context has no registered codec")
        if type(canonical_body) is not bytes:
            raise ContractViolation("validation context has no registered body")
        self.assert_registered_context(
            context,
            context._registered_admission_token,
            implementation,
            context.coordinate,
            canonical_body,
        )
        return self._witnesses.get((namespace, key))

    def remember(
        self,
        context: SemanticBodyValidationContext,
        namespace: str,
        key: bytes,
        witness: object,
    ) -> None:
        if context._registered_admission_token is None:
            raise ContractViolation("validation context has no registered admission")
        implementation = context._registered_codec_implementation
        canonical_body = context._registered_canonical_body
        if type(implementation) is not SemanticImplementationCoordinate:
            raise ContractViolation("validation context has no registered codec")
        if type(canonical_body) is not bytes:
            raise ContractViolation("validation context has no registered body")
        self.assert_registered_context(
            context,
            context._registered_admission_token,
            implementation,
            context.coordinate,
            canonical_body,
        )
        coordinate = (namespace, key)
        prior = self._witnesses.get(coordinate)
        if prior is not None and prior is not witness:
            raise ContractViolation("validation epoch witness cannot be replaced")
        self._witnesses[coordinate] = witness

    def __copy__(self) -> Never:
        raise TypeError("validation epoch is not copyable")

    def __deepcopy__(self, memo: object) -> Never:
        raise TypeError("validation epoch is not copyable")

    def __reduce__(self) -> Never:
        raise TypeError("validation epoch is not serializable")


@dataclass(frozen=True, slots=True)
class SemanticBodyValidationContext:
    purpose: str
    coordinate: SemanticValueCoordinate
    invocation_digest: ContentDigest
    input_closure_digest: ContentDigest
    provider_key: str
    target_package: SemanticPackageCoordinate
    inputs: tuple[BoundSemanticInput, ...]
    predecessor: AdmittedSemanticValue | None
    candidate: AdmittedSemanticValue
    transition: AdmittedSemanticValue | None = None
    effect: AdmittedSemanticValue | None = None
    outer_transition_impacts: tuple[SemanticImpactCoordinate, ...] | None = None
    outer_effect_impacts: tuple[SemanticImpactCoordinate, ...] = ()
    _validation_epoch: _SemanticBodyValidationEpoch | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _runtime_token: object | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _execution_attempt_token: object | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _profile_digest: ContentDigest | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _registered_codec_implementation: SemanticImplementationCoordinate | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _registered_canonical_body: bytes | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _registered_admission_token: object | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if type(self.purpose) is not str or self.purpose not in {
            "transition",
            "effect",
            "output",
        }:
            raise ContractViolation("body validation context purpose is unsupported")
        if type(self.coordinate) is not SemanticValueCoordinate:
            raise TypeError("context coordinate must be exact SemanticValueCoordinate")
        self.coordinate.to_wire()
        if type(self.invocation_digest) is not ContentDigest:
            raise TypeError("context invocation_digest must be exact ContentDigest")
        self.invocation_digest.to_wire()
        if type(self.input_closure_digest) is not ContentDigest:
            raise TypeError("context input_closure_digest must be exact ContentDigest")
        self.input_closure_digest.to_wire()
        if type(self.provider_key) is not str or not self.provider_key:
            raise TypeError("context provider_key must be exact nonempty str")
        if type(self.target_package) is not SemanticPackageCoordinate:
            raise TypeError("context target_package must be exact")
        self.target_package.to_wire()
        if type(self.inputs) is not tuple or any(
            type(item) is not BoundSemanticInput for item in self.inputs
        ):
            raise TypeError("context inputs must be exact BoundSemanticInput values")
        if len({item.target_role for item in self.inputs}) != len(self.inputs):
            raise ContractViolation("context input roles must be unique")
        if (
            self.predecessor is not None
            and type(self.predecessor) is not AdmittedSemanticValue
        ):
            raise TypeError("context predecessor must be admitted or None")
        if type(self.candidate) is not AdmittedSemanticValue:
            raise TypeError("context candidate must be exact AdmittedSemanticValue")
        for name in ("transition", "effect"):
            value = getattr(self, name)
            if value is not None and type(value) is not AdmittedSemanticValue:
                raise TypeError(f"context {name} must be admitted or None")
        if self.outer_transition_impacts is not None and (
            type(self.outer_transition_impacts) is not tuple
            or any(
                type(item) is not SemanticImpactCoordinate
                for item in self.outer_transition_impacts
            )
        ):
            raise TypeError("context transition impacts must be exact or None")
        if type(self.outer_effect_impacts) is not tuple or any(
            type(item) is not SemanticImpactCoordinate
            for item in self.outer_effect_impacts
        ):
            raise TypeError("context effect impacts must be exact tuple")
        if not self.outer_effect_impacts:
            raise ContractViolation("context requires outer effect impacts")
        if (
            self.outer_transition_impacts is not None
            and self.outer_transition_impacts != self.outer_effect_impacts
        ):
            raise ContractViolation("context outer impacts differ")
        if self.purpose == "transition" and (
            self.transition is not None or self.effect is not None
        ):
            raise ContractViolation("transition context cannot contain later bodies")
        if self.purpose == "effect" and self.effect is not None:
            raise ContractViolation("effect context cannot contain an admitted effect")
        if self.purpose == "output" and self.effect is None:
            raise ContractViolation("output context requires an admitted effect")
        if (
            self._validation_epoch is not None
            and type(self._validation_epoch) is not _SemanticBodyValidationEpoch
        ):
            raise TypeError("validation epoch must be exact Code-owned value")
        if self._validation_epoch is not None and self._runtime_token is None:
            raise ContractViolation("validation epoch requires its Code runtime token")
        if self._validation_epoch is not None and self._execution_attempt_token is None:
            raise ContractViolation("validation epoch requires its execution attempt")
        if (
            self._validation_epoch is not None
            and type(self._profile_digest) is not ContentDigest
        ):
            raise ContractViolation("validation epoch requires exact profile digest")

    def validation_witness(self, namespace: str, key: bytes) -> object | None:
        if type(namespace) is not str or not namespace:
            raise TypeError("validation witness namespace must be exact nonempty str")
        if type(key) is not bytes:
            raise TypeError("validation witness key must be exact bytes")
        epoch = self._validation_epoch
        if epoch is None:
            return None
        return epoch.witness(self, namespace, key)

    @property
    def has_validation_epoch(self) -> bool:
        return self._validation_epoch is not None

    def remember_validation_witness(
        self,
        namespace: str,
        key: bytes,
        witness: object,
    ) -> None:
        if type(namespace) is not str or not namespace:
            raise TypeError("validation witness namespace must be exact nonempty str")
        if type(key) is not bytes:
            raise TypeError("validation witness key must be exact bytes")
        epoch = self._validation_epoch
        if epoch is None:
            raise ContractViolation("validation context has no Code-owned epoch")
        epoch.remember(self, namespace, key, witness)

    def _register_body(
        self,
        construction_token: object,
        admission_token: object,
        codec_implementation: SemanticImplementationCoordinate,
        coordinate: SemanticValueCoordinate,
        canonical_body: bytes,
    ) -> None:
        epoch = self._validation_epoch
        if epoch is None:
            raise ContractViolation("validation context has no Code-owned epoch")
        object.__setattr__(
            self,
            "_registered_codec_implementation",
            codec_implementation,
        )
        object.__setattr__(self, "_registered_canonical_body", canonical_body)
        object.__setattr__(self, "_registered_admission_token", admission_token)
        epoch.register_context(
            construction_token,
            self,
            admission_token,
            codec_implementation,
            coordinate,
            canonical_body,
        )

    def _assert_registered_body(
        self,
        admission_token: object,
        codec_implementation: SemanticImplementationCoordinate,
        coordinate: SemanticValueCoordinate,
        canonical_body: bytes,
    ) -> tuple[object, ...]:
        epoch = self._validation_epoch
        if epoch is None:
            raise ContractViolation("validation context has no Code-owned epoch")
        return epoch.assert_registered_context(
            self,
            admission_token,
            codec_implementation,
            coordinate,
            canonical_body,
        )

    def _registered_body_snapshot(self) -> tuple[object, ...]:
        epoch = self._validation_epoch
        if epoch is None:
            raise ContractViolation("validation context has no Code-owned epoch")
        return epoch.registered_context_snapshot(self)

    @property
    def predecessor_value(self) -> object | None:
        return None if self.predecessor is None else self.predecessor._value

    @property
    def candidate_value(self) -> object:
        return self.candidate._value

    @property
    def transition_value(self) -> object | None:
        return None if self.transition is None else self.transition._value

    @property
    def effect_value(self) -> object | None:
        return None if self.effect is None else self.effect._value

    def input_value(self, role: str) -> object:
        if type(role) is not str or not role:
            raise TypeError("context input role must be exact nonempty str")
        for item in self.inputs:
            if item.target_role == role:
                return item.admitted.value
        raise ContractViolation(f"context input role {role!r} is absent")


class ContextualSemanticBodyCodec(SemanticBodyCodec, Protocol):
    def decode_contextual(
        self, canonical_body: bytes, context: SemanticBodyValidationContext
    ) -> object: ...

    def encode_contextual(
        self, value: object, context: SemanticBodyValidationContext
    ) -> bytes: ...


def _decode_with_context(
    codec: SemanticBodyCodec,
    canonical_body: bytes,
    context: SemanticBodyValidationContext | None,
) -> object:
    if context is None:
        return codec.decode(canonical_body)
    context.__post_init__()
    decode = getattr(codec, "decode_contextual", None)
    if not callable(decode):
        raise ContractViolation("context-bound body codec has no contextual decoder")
    return decode(canonical_body, context)


def _encode_with_context(
    codec: SemanticBodyCodec,
    value: object,
    context: SemanticBodyValidationContext | None,
) -> bytes:
    if context is None:
        return codec.encode(value)
    context.__post_init__()
    encode = getattr(codec, "encode_contextual", None)
    if not callable(encode):
        raise ContractViolation("context-bound body codec has no contextual encoder")
    result = encode(value, context)
    if type(result) is not bytes:
        raise TypeError("contextual body encoder must return exact bytes")
    return result


@dataclass(frozen=True, slots=True)
class BoundSemanticInput:
    target_role: str
    admitted: AdmittedSemanticValue

    def __post_init__(self) -> None:
        if type(self.target_role) is not str or not self.target_role:
            raise TypeError("target_role must be an exact nonempty string")
        if type(self.admitted) is not AdmittedSemanticValue:
            raise TypeError("admitted must be exact AdmittedSemanticValue")

    @property
    def source(self) -> SemanticValueCoordinate:
        return self.admitted._coordinate

    @property
    def canonical_body(self) -> bytes:
        return self.admitted._canonical_body

    @property
    def value(self) -> object:
        return self.admitted._value


def _admitted_semantic_value_snapshot(
    value: AdmittedSemanticValue | None,
) -> tuple[object, ...] | None:
    if value is None:
        return None
    if type(value) is not AdmittedSemanticValue:
        raise TypeError("validation context body must be exactly admitted")
    if type(value._coordinate) is not SemanticValueCoordinate:
        raise ContractViolation("validation context body coordinate differs")
    if type(value._canonical_body) is not bytes:
        raise ContractViolation("validation context canonical body differs")
    if type(value._codec_implementation) is not SemanticImplementationCoordinate:
        raise ContractViolation("validation context codec implementation differs")
    return (
        id(value),
        id(value._admission_token),
        canonical_json_bytes(value._coordinate.to_wire()),
        value._canonical_body,
        canonical_json_bytes(value._codec_implementation.to_wire()),
        id(value._codec),
        id(value._value),
    )


def _validation_context_snapshot(
    context: SemanticBodyValidationContext,
    admission_token: object,
    codec_implementation: SemanticImplementationCoordinate,
    coordinate: SemanticValueCoordinate,
    canonical_body: bytes,
) -> tuple[object, ...]:
    if type(context) is not SemanticBodyValidationContext:
        raise TypeError("validation context must be exact")
    context.__post_init__()
    if type(codec_implementation) is not SemanticImplementationCoordinate:
        raise TypeError("validation codec implementation must be exact")
    if type(coordinate) is not SemanticValueCoordinate:
        raise TypeError("validation coordinate must be exact")
    if type(canonical_body) is not bytes:
        raise TypeError("validation canonical body must be exact bytes")
    if context.coordinate != coordinate:
        raise ContractViolation("validation context coordinate differs from body")
    if (
        ContentDigest.of_bytes(canonical_body) != coordinate.digest
        or len(canonical_body) != coordinate.size_bytes
    ):
        raise ContractViolation(
            "validation context canonical body differs from coordinate"
        )
    inputs = tuple(
        (item.target_role, _admitted_semantic_value_snapshot(item.admitted))
        for item in context.inputs
    )

    transition_impacts = (
        None
        if context.outer_transition_impacts is None
        else tuple(
            canonical_json_bytes(item.to_wire())
            for item in context.outer_transition_impacts
        )
    )
    effect_impacts = tuple(
        canonical_json_bytes(item.to_wire()) for item in context.outer_effect_impacts
    )
    if type(context._profile_digest) is not ContentDigest:
        raise ContractViolation("validation context profile digest differs")
    epoch = context._validation_epoch
    if type(epoch) is not _SemanticBodyValidationEpoch:
        raise ContractViolation("validation context epoch differs")
    return (
        context.purpose,
        canonical_json_bytes(context.coordinate.to_wire()),
        context.invocation_digest.value,
        context.input_closure_digest.value,
        context.provider_key,
        canonical_json_bytes(context.target_package.to_wire()),
        inputs,
        _admitted_semantic_value_snapshot(context.predecessor),
        _admitted_semantic_value_snapshot(context.candidate),
        _admitted_semantic_value_snapshot(context.transition),
        _admitted_semantic_value_snapshot(context.effect),
        transition_impacts,
        effect_impacts,
        context._profile_digest.value,
        canonical_json_bytes(codec_implementation.to_wire()),
        canonical_json_bytes(coordinate.to_wire()),
        canonical_body,
        id(admission_token),
        id(epoch._runtime_token),
        id(epoch._attempt_token),
        epoch._invocation_digest.value,
        epoch._profile_digest.value,
        epoch._provider_key,
        canonical_json_bytes(epoch._provider_implementation.to_wire()),
        epoch._provider_declaration_digest.value,
    )


@dataclass(frozen=True, slots=True)
class _AdmittedPublicationIdentity:
    """Code-owned immutable registration evidence for one admitted body."""

    body: AdmittedSemanticValue
    admission_token: object
    context: SemanticBodyValidationContext | None
    epoch: _SemanticBodyValidationEpoch | None
    attempt_token: object | None
    coordinate_wire: bytes
    canonical_body: bytes
    codec_implementation_wire: bytes
    registration_snapshot: tuple[object, ...] | None


def _copy_registration_snapshot(
    value: tuple[object, ...] | None,
) -> tuple[object, ...] | None:
    if value is None:
        return None

    def copy_item(item: object) -> object:
        if type(item) is tuple:
            return tuple(copy_item(nested) for nested in item)
        if item is None or type(item) in {bytes, int, str}:
            return item
        raise ContractViolation("registration snapshot contains a foreign value")

    return tuple(copy_item(item) for item in value)


def _registration_snapshots_match(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is tuple and type(right) is tuple:
        return len(left) == len(right) and all(
            _registration_snapshots_match(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    if left is None:
        return True
    if type(left) in {bytes, int, str}:
        return bool(left == right)
    return False


def _assert_independent_publication_identity(
    observed: _AdmittedPublicationIdentity,
    expected: _AdmittedPublicationIdentity,
) -> None:
    if (
        type(observed) is not _AdmittedPublicationIdentity
        or type(expected) is not _AdmittedPublicationIdentity
    ):
        raise ContractViolation("execution publication identity type differs")
    if observed is expected:
        raise ContractViolation("execution publication identity is shared")
    if observed.body is not expected.body:
        raise ContractViolation("execution publication identity body differs")
    for field_name in ("admission_token", "context", "epoch", "attempt_token"):
        if getattr(observed, field_name) is not getattr(expected, field_name):
            raise ContractViolation(
                f"execution publication identity {field_name} differs"
            )
    for field_name in (
        "coordinate_wire",
        "canonical_body",
        "codec_implementation_wire",
    ):
        observed_value = getattr(observed, field_name)
        expected_value = getattr(expected, field_name)
        if type(observed_value) is not bytes or observed_value != expected_value:
            raise ContractViolation(
                f"execution publication identity {field_name} differs"
            )
    if not _registration_snapshots_match(
        observed.registration_snapshot,
        expected.registration_snapshot,
    ):
        raise ContractViolation(
            "execution publication identity registration snapshot differs"
        )


def _capture_admitted_publication_identity(
    value: AdmittedSemanticValue,
) -> _AdmittedPublicationIdentity:
    if type(value) is not AdmittedSemanticValue:
        raise TypeError("publication identity requires exact admitted body")
    if type(value._coordinate) is not SemanticValueCoordinate:
        raise ContractViolation("publication identity coordinate differs")
    if type(value._canonical_body) is not bytes:
        raise ContractViolation("publication identity body differs")
    if type(value._codec_implementation) is not SemanticImplementationCoordinate:
        raise ContractViolation("publication identity codec differs")
    context = value._context
    if context is None:
        epoch = None
        attempt_token = None
        registration_snapshot = None
    else:
        if type(context) is not SemanticBodyValidationContext:
            raise ContractViolation("publication identity context differs")
        epoch = context._validation_epoch
        if type(epoch) is not _SemanticBodyValidationEpoch:
            raise ContractViolation("publication identity epoch differs")
        attempt_token = context._execution_attempt_token
        registration_snapshot = context._registered_body_snapshot()
    return _AdmittedPublicationIdentity(
        body=value,
        admission_token=value._admission_token,
        context=context,
        epoch=epoch,
        attempt_token=attempt_token,
        coordinate_wire=canonical_json_bytes(value._coordinate.to_wire()),
        canonical_body=value._canonical_body,
        codec_implementation_wire=canonical_json_bytes(
            value._codec_implementation.to_wire()
        ),
        registration_snapshot=_copy_registration_snapshot(registration_snapshot),
    )


@dataclass(frozen=True, slots=True)
class ProviderStepInvocation:
    invocation: SemanticContractInvocation
    step: ProfileStepDeclaration
    declaration: SemanticContractProviderDeclaration
    binding: ProviderExecutionBinding
    inputs: tuple[BoundSemanticInput, ...]
    predecessor: AdmittedSemanticValue | None
    dependencies: tuple[SemanticDependencyCoordinate, ...]
    _input_closure_body: bytes = field(init=False, repr=False, compare=False)
    _input_closure_digest: ContentDigest = field(init=False, repr=False, compare=False)
    _selected_primitive_snapshot_node_count: int = field(
        init=False, repr=False, compare=False, default=0
    )
    _selected_primitive_snapshot_scalar_bytes: int = field(
        init=False, repr=False, compare=False, default=0
    )

    def __post_init__(self) -> None:
        exact = (
            (self.invocation, SemanticContractInvocation, "invocation"),
            (self.step, ProfileStepDeclaration, "step"),
            (self.declaration, SemanticContractProviderDeclaration, "declaration"),
            (self.binding, ProviderExecutionBinding, "binding"),
        )
        for value, expected, path in exact:
            if type(value) is not expected:
                raise TypeError(f"{path} must be exact {expected.__name__}")
            value.to_wire()
        if self.step.provider_key != self.declaration.provider_key:
            raise ContractViolation("step and declaration providers differ")
        if self.binding.provider_key != self.declaration.provider_key:
            raise ContractViolation("binding and declaration providers differ")
        if type(self.inputs) is not tuple or any(
            type(item) is not BoundSemanticInput for item in self.inputs
        ):
            raise TypeError("inputs must be an exact tuple of BoundSemanticInput")
        if (
            self.predecessor is not None
            and type(self.predecessor) is not AdmittedSemanticValue
        ):
            raise TypeError("predecessor must be exact AdmittedSemanticValue or None")
        if type(self.dependencies) is not tuple or any(
            type(item) is not SemanticDependencyCoordinate for item in self.dependencies
        ):
            raise TypeError(
                "dependencies must be an exact tuple of SemanticDependencyCoordinate"
            )
        closure_body = canonical_json_bytes(
            {
                "dependencies": [item.to_wire() for item in self.dependencies],
                "inputs": [
                    {
                        "source": item.source.to_wire(),
                        "target_role": item.target_role,
                    }
                    for item in self.inputs
                ],
                "invocation_digest": self.invocation.digest.to_wire(),
                "predecessor": None
                if self.predecessor is None
                else self.predecessor._coordinate.to_wire(),
                "schema": "aware.code.provider-input-closure.v1",
            }
        )
        object.__setattr__(self, "_input_closure_body", closure_body)
        object.__setattr__(
            self, "_input_closure_digest", ContentDigest.of_bytes(closure_body)
        )

    @property
    def input_closure_digest(self) -> ContentDigest:
        return self._input_closure_digest

    @property
    def input_closure_body(self) -> bytes:
        return self._input_closure_body


@dataclass(frozen=True, slots=True)
class ProviderDerivation:
    result: SemanticContractResult
    bodies: tuple[SemanticBody, ...] = ()

    def __post_init__(self) -> None:
        if type(self.result) is not SemanticContractResult:
            raise TypeError("derivation result must be exact SemanticContractResult")
        self.result.to_wire()
        if type(self.bodies) is not tuple or any(
            type(item) is not SemanticBody for item in self.bodies
        ):
            raise TypeError("derivation bodies must be an exact tuple of SemanticBody")
        for item in self.bodies:
            item.__post_init__()
        ordered = tuple(
            sorted(
                self.bodies,
                key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
            )
        )
        if self.bodies != ordered or len(
            {item.coordinate for item in self.bodies}
        ) != len(self.bodies):
            raise ContractViolation(
                "derivation bodies must be coordinate-unique and ordered"
            )


class SemanticContractProvider(Protocol):
    @property
    def declaration(self) -> SemanticContractProviderDeclaration: ...

    async def derive(
        self, invocation: ProviderStepInvocation
    ) -> ProviderDerivation: ...


class ProviderTerminalFailure(RuntimeError):
    def __init__(self, result: SemanticContractResult) -> None:
        self.result = result
        super().__init__(
            f"semantic provider ended with {result.status.value}: {result.reason}"
        )


_COMPLETION_CONSTRUCTION = object()


def _nested_wire_digest(value: object, path: str) -> ContentDigest:
    if type(value) is not dict:
        raise ContractViolation(f"{path} must be an exact wire object")
    digest = value.get("digest")
    if type(digest) is not str:
        raise ContractViolation(f"{path} lacks an exact digest")
    return ContentDigest(digest)


@dataclass(frozen=True, slots=True)
class _ExecutionPublicationRecord:
    result_digest: str
    result_wire: bytes
    effect_digest: str
    transition_digest: str | None
    admitted_body_identities: tuple[_AdmittedPublicationIdentity, ...]


class ExecutionCompletion:
    __slots__ = (
        "__weakref__",  # pyright: ignore[reportUninitializedInstanceVariable]
        "_bodies",
        "_effect_digest",
        "_invocation_digest",
        "_profile_digest",
        "_publication_identities",
        "_result",
        "_result_digest",
        "_result_wire",
        "_runtime_token",
        "_transition_digest",
    )

    def __init__(
        self,
        construction_token: object,
        runtime_token: object,
        invocation_digest: ContentDigest,
        profile_digest: ContentDigest,
        result: SemanticContractResult,
        bodies: tuple[AdmittedSemanticValue, ...],
    ) -> None:
        if construction_token is not _COMPLETION_CONSTRUCTION:
            raise TypeError("ExecutionCompletion is runtime-constructed only")
        self._runtime_token = runtime_token
        self._invocation_digest = invocation_digest
        self._profile_digest = profile_digest
        self._result = result
        result_wire = result.to_wire()
        result_digest = result_wire.get("digest")
        if type(result_digest) is not str:
            raise ContractViolation("execution result wire lacks exact digest")
        self._result_digest = ContentDigest(result_digest)
        self._result_wire = canonical_json_bytes(result_wire)
        effect_wire = result_wire.get("effect")
        self._effect_digest = _nested_wire_digest(
            effect_wire, "execution result effect"
        )
        transition_wire = result_wire.get("transition")
        self._transition_digest = (
            None
            if transition_wire is None
            else _nested_wire_digest(transition_wire, "execution result transition")
        )
        self._bodies = bodies
        if type(self._bodies) is not tuple or any(
            type(item) is not AdmittedSemanticValue for item in self._bodies
        ):
            raise TypeError("execution completion requires exact admitted bodies")
        self._publication_identities = tuple(
            _capture_admitted_publication_identity(item) for item in bodies
        )

    @property
    def invocation_digest(self) -> ContentDigest:
        return self._invocation_digest

    @property
    def profile_digest(self) -> ContentDigest:
        return self._profile_digest

    @property
    def result(self) -> SemanticContractResult:
        self._assert_intact()
        return self._result

    @property
    def bodies(self) -> tuple[AdmittedSemanticValue, ...]:
        self._assert_intact()
        return self._bodies

    def body_for(self, coordinate: SemanticValueCoordinate) -> AdmittedSemanticValue:
        if type(coordinate) is not SemanticValueCoordinate:
            raise TypeError("coordinate must be exact SemanticValueCoordinate")
        self._assert_intact()
        matches = tuple(item for item in self._bodies if item.coordinate == coordinate)
        if len(matches) != 1:
            raise ContractViolation("completion has no unique body for coordinate")
        return matches[0]

    def _assert_intact(self) -> None:
        if self._result.digest != self._result_digest:
            raise ContractViolation("execution completion result was restamped")
        if type(self._bodies) is not tuple or any(
            type(item) is not AdmittedSemanticValue for item in self._bodies
        ):
            raise ContractViolation("execution completion body closure was restamped")
        if type(self._publication_identities) is not tuple or len(
            self._publication_identities
        ) != len(self._bodies):
            raise ContractViolation("execution completion body identity was restamped")
        if any(
            observed is not expected.body
            for observed, expected in zip(self._bodies, self._publication_identities)
        ):
            raise ContractViolation(
                "execution completion admitted body was transplanted"
            )
        for item, identity in zip(self._bodies, self._publication_identities):
            item._assert_publication_registration_intact(identity)
            item._assert_intact()

    def _publication_bodies(
        self,
        *,
        expected_result_digest: ContentDigest,
        expected_identities: tuple[_AdmittedPublicationIdentity, ...],
    ) -> tuple[SemanticBody, ...]:
        """Validate terminal coordinates/bytes without re-entering codecs."""

        if self._result.digest != expected_result_digest:
            raise ContractViolation("execution completion result was restamped")
        if type(self._bodies) is not tuple or any(
            type(item) is not AdmittedSemanticValue for item in self._bodies
        ):
            raise ContractViolation("execution completion body closure was restamped")
        if type(expected_identities) is not tuple or len(expected_identities) != len(
            self._bodies
        ):
            raise ContractViolation("execution publication body identity differs")
        if type(self._publication_identities) is not tuple or len(
            self._publication_identities
        ) != len(expected_identities):
            raise ContractViolation("execution completion body identity was restamped")
        for observed, expected in zip(
            self._publication_identities,
            expected_identities,
        ):
            _assert_independent_publication_identity(observed, expected)
        if any(
            type(expected) is not _AdmittedPublicationIdentity
            or observed is not expected.body
            for observed, expected in zip(self._bodies, expected_identities)
        ):
            raise ContractViolation(
                "execution publication admitted body was transplanted"
            )
        required = set(_publication_body_coordinates(self._result))
        coordinates: set[SemanticValueCoordinate] = set()
        selected: list[SemanticBody] = []
        for item, identity in zip(self._bodies, expected_identities):
            item._assert_publication_registration_intact(identity)
            coordinate = item._coordinate
            if type(coordinate) is not SemanticValueCoordinate:
                raise ContractViolation("completion body coordinate was restamped")
            coordinate.to_wire()
            if coordinate in coordinates:
                raise ContractViolation(
                    "completion portable body coordinate duplicated"
                )
            coordinates.add(coordinate)
            if coordinate not in required:
                continue
            body = item._canonical_body
            if type(body) is not bytes:
                raise ContractViolation("completion canonical body was restamped")
            if (
                ContentDigest.of_bytes(body) != coordinate.digest
                or len(body) != coordinate.size_bytes
            ):
                raise ContractViolation(
                    "completion portable body differs from coordinate"
                )
            selected.append(SemanticBody(coordinate, body))
        if {item.coordinate for item in selected} != required:
            raise ContractViolation(
                "completion lacks terminal publication body closure"
            )
        return tuple(
            sorted(
                selected,
                key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
            )
        )

    def __reduce__(self) -> Never:
        raise TypeError("ExecutionCompletion is not serializable")


@dataclass(frozen=True, slots=True)
class ExecutionPublicationSnapshot:
    """Invocation-local portable bytes captured by the owning Code runtime."""

    invocation_digest: ContentDigest
    profile_digest: ContentDigest
    result: SemanticContractResult
    result_digest: ContentDigest
    result_wire: bytes
    effect_digest: ContentDigest
    transition_digest: ContentDigest | None
    bodies: tuple[SemanticBody, ...]

    def __post_init__(self) -> None:
        if type(self.invocation_digest) is not ContentDigest:
            raise TypeError("snapshot invocation digest must be exact ContentDigest")
        if type(self.profile_digest) is not ContentDigest:
            raise TypeError("snapshot profile digest must be exact ContentDigest")
        if type(self.result) is not SemanticContractResult:
            raise TypeError("snapshot result must be exact SemanticContractResult")
        if self.result.invocation_digest != self.invocation_digest:
            raise ContractViolation("snapshot result differs from invocation")
        if type(self.result_digest) is not ContentDigest:
            raise TypeError("snapshot result digest must be exact ContentDigest")
        if type(self.result_wire) is not bytes:
            raise TypeError("snapshot result wire must be exact bytes")
        if type(self.effect_digest) is not ContentDigest:
            raise TypeError("snapshot effect digest must be exact ContentDigest")
        if (
            self.transition_digest is not None
            and type(self.transition_digest) is not ContentDigest
        ):
            raise TypeError("snapshot transition digest must be exact ContentDigest")
        if type(self.bodies) is not tuple or any(
            type(item) is not SemanticBody for item in self.bodies
        ):
            raise TypeError("snapshot bodies must be an exact SemanticBody tuple")
        expected = tuple(
            sorted(
                self.bodies,
                key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
            )
        )
        if self.bodies != expected or len(
            {item.coordinate for item in self.bodies}
        ) != len(self.bodies):
            raise ContractViolation("snapshot bodies must be unique and ordered")

    def body_for(self, coordinate: SemanticValueCoordinate) -> SemanticBody:
        if type(coordinate) is not SemanticValueCoordinate:
            raise TypeError("coordinate must be exact SemanticValueCoordinate")
        matches = tuple(item for item in self.bodies if item.coordinate == coordinate)
        if len(matches) != 1:
            raise ContractViolation("snapshot has no unique body for coordinate")
        return matches[0]


class SemanticContractRuntime:
    def __init__(
        self,
        profile: SemanticContractProfileDeclaration,
        providers: dict[str, SemanticContractProvider],
        body_codecs: dict[SemanticContractRef, SemanticBodyCodec],
    ) -> None:
        if type(profile) is not SemanticContractProfileDeclaration:
            raise TypeError("profile must be exact SemanticContractProfileDeclaration")
        profile.to_wire()
        if type(providers) is not dict or any(
            type(key) is not str for key in providers
        ):
            raise TypeError("providers must be an exact string-keyed dict")
        expected = {item.provider_key: item for item in profile.providers}
        if set(providers) != set(expected):
            raise ContractViolation(
                "runtime providers differ from the profile provider closure"
            )
        admitted: dict[str, SemanticContractProvider] = {}
        for key in sorted(providers, key=str.encode):
            provider = providers[key]
            declaration = provider.declaration
            if type(declaration) is not SemanticContractProviderDeclaration:
                raise TypeError("provider declaration must be exact module-owned value")
            if declaration != expected[key]:
                raise ContractViolation(
                    f"provider {key} declaration differs from profile"
                )
            admitted[key] = provider

        if type(body_codecs) is not dict or any(
            type(key) is not SemanticContractRef for key in body_codecs
        ):
            raise TypeError("body_codecs must be an exact contract-keyed dict")
        expected_contracts = self._profile_body_contracts(profile)
        if set(body_codecs) != expected_contracts:
            raise ContractViolation(
                "runtime body codecs differ from the profile body-contract closure"
            )
        admitted_codecs: dict[SemanticContractRef, SemanticBodyCodec] = {}
        codec_implementations: dict[
            SemanticContractRef, SemanticImplementationCoordinate
        ] = {}
        for contract in sorted(
            body_codecs, key=lambda item: canonical_json_bytes(item.to_wire())
        ):
            codec = body_codecs[contract]
            if (
                type(codec.contract) is not SemanticContractRef
                or codec.contract != contract
            ):
                raise ContractViolation("body codec contract differs from registry key")
            implementation = codec.implementation
            if type(implementation) is not SemanticImplementationCoordinate:
                raise TypeError("body codec implementation must be exact coordinate")
            implementation.to_wire()
            admitted_codecs[contract] = codec
            codec_implementations[contract] = implementation

        self._profile = profile
        self._profile_digest = profile.digest
        self._providers = admitted
        self._provider_declaration_digests = {
            key: declaration.digest for key, declaration in expected.items()
        }
        self._body_codecs = admitted_codecs
        self._codec_implementations = codec_implementations
        self._runtime_token = object()
        self._resolved_steps = resolve_profile(profile)
        self._publication_records: WeakKeyDictionary[
            ExecutionCompletion, _ExecutionPublicationRecord
        ] = WeakKeyDictionary()
        self._publication_records_lock = RLock()

    @staticmethod
    def _profile_body_contracts(
        profile: SemanticContractProfileDeclaration,
    ) -> set[SemanticContractRef]:
        result = {item.contract for item in profile.inputs}
        for provider in profile.providers:
            result.update(
                {
                    provider.result_role.contract,
                    provider.transition_contract,
                    provider.effect_contract,
                    *(item.contract for item in provider.output_roles),
                }
            )
        return result

    @property
    def profile(self) -> SemanticContractProfileDeclaration:
        return self._profile

    def _validate_selected_provider_registration_inputs(
        self, provider_key: str
    ) -> None:
        if type(provider_key) is not str or not provider_key:
            raise TypeError("selected provider key must be exact nonempty text")
        if canonical_json_bytes(self._profile.to_wire()) != canonical_json_bytes(
            self.profile.to_wire()
        ) or self._profile.digest != self._profile_digest:
            raise ContractViolation("runtime profile changed after admission")
        provider = self._providers.get(provider_key)
        if provider is None:
            raise ContractViolation("selected provider is absent from runtime")
        declaration = provider.declaration
        if (
            type(declaration) is not SemanticContractProviderDeclaration
            or declaration.digest != self._provider_declaration_digests[provider_key]
        ):
            raise ContractViolation("selected provider declaration differs")

    def _admit_selected_provider_step(
        self,
        provider_key: str,
        invocation: SemanticContractInvocation,
        input_bodies: tuple[SemanticBody, ...],
        predecessor_body: SemanticBody | None,
        input_values: tuple[object, ...] | None = None,
        diagnostic_spans_ns: list[tuple[str, int]] | None = None,
    ) -> ProviderStepInvocation:
        invocation_started = perf_counter_ns()
        self._validate_invocation(invocation)
        invocation_finished = perf_counter_ns()
        role_ledger, admitted_predecessor, _ = self._admit_invocation_bodies(
            invocation,
            input_bodies,
            predecessor_body,
            input_values=input_values,
            diagnostic_spans_ns=diagnostic_spans_ns,
        )
        bodies_finished = perf_counter_ns()
        steps = tuple(
            item for item in self._resolved_steps if item.provider_key == provider_key
        )
        if len(steps) != 1:
            raise ContractViolation(
                "selected provider must own exactly one resolved profile step"
            )
        step = steps[0]
        declaration = self._providers[provider_key].declaration
        if type(declaration) is not SemanticContractProviderDeclaration:
            raise TypeError("selected provider declaration must be exact")
        bindings = {item.provider_key: item for item in invocation.provider_bindings}
        binding = bindings.get(provider_key)
        if type(binding) is not ProviderExecutionBinding:
            raise ContractViolation("selected provider invocation binding is absent")
        bound_inputs = tuple(
            BoundSemanticInput(item.target_role, role_ledger[item.source_role])
            for item in step.bindings
        )
        result = ProviderStepInvocation(
            invocation=invocation,
            step=step,
            declaration=declaration,
            binding=binding,
            inputs=bound_inputs,
            predecessor=admitted_predecessor,
            dependencies=invocation.dependencies,
        )
        if diagnostic_spans_ns is not None:
            diagnostic_spans_ns.extend(
                (
                    ("code_invocation_admission", invocation_finished - invocation_started),
                    ("code_body_admission", bodies_finished - invocation_finished),
                    ("code_step_assembly", perf_counter_ns() - bodies_finished),
                )
            )
        return result

    def _rederive_selected_provider_step(
        self,
        provider_key: str,
        expected: ProviderStepInvocation,
        input_bodies: tuple[SemanticBody, ...],
        predecessor_body: SemanticBody | None,
    ) -> ProviderStepInvocation:
        """Rebuild a step from its retained Code admissions without decoding again."""

        if type(expected) is not ProviderStepInvocation:
            raise TypeError("expected selected provider step must be exact")
        self._validate_invocation(expected.invocation)
        if expected.declaration.provider_key != provider_key:
            raise ContractViolation("selected provider step key differs")
        if tuple(item.source for item in expected.inputs) != tuple(
            item.coordinate for item in input_bodies
        ):
            raise ContractViolation("selected provider admitted input coordinates differ")
        if tuple(item.canonical_body for item in expected.inputs) != tuple(
            item.canonical_body for item in input_bodies
        ):
            raise ContractViolation("selected provider admitted input bodies differ")
        for body, admitted in zip(input_bodies, expected.inputs, strict=True):
            body.__post_init__()
            admitted.admitted._assert_intact()
        if predecessor_body is None:
            if expected.predecessor is not None:
                raise ContractViolation("selected provider predecessor presence differs")
        else:
            predecessor_body.__post_init__()
            if expected.predecessor is None:
                raise ContractViolation("selected provider predecessor is absent")
            expected.predecessor._assert_intact()
            if (
                expected.predecessor.coordinate != predecessor_body.coordinate
                or expected.predecessor.canonical_body
                != predecessor_body.canonical_body
            ):
                raise ContractViolation("selected provider predecessor body differs")
        declaration = self._providers[provider_key].declaration
        if (
            type(declaration) is not SemanticContractProviderDeclaration
            or declaration.digest != self._provider_declaration_digests[provider_key]
        ):
            raise ContractViolation("selected provider declaration changed")
        binding = next(
            (
                item
                for item in expected.invocation.provider_bindings
                if item.provider_key == provider_key
            ),
            None,
        )
        if type(binding) is not ProviderExecutionBinding:
            raise ContractViolation("selected provider binding is absent")
        return ProviderStepInvocation(
            invocation=expected.invocation,
            step=expected.step,
            declaration=declaration,
            binding=binding,
            inputs=tuple(
                BoundSemanticInput(item.target_role, item.admitted)
                for item in expected.inputs
            ),
            predecessor=expected.predecessor,
            dependencies=expected.invocation.dependencies,
        )

    def owns_completion(self, completion: object) -> bool:
        if type(completion) is not ExecutionCompletion:
            return False
        if completion._runtime_token is not self._runtime_token:
            return False
        with self._publication_records_lock:
            record = self._publication_records.get(completion)
        if type(completion._bodies) is not tuple:
            return False
        if record is None or len(record.admitted_body_identities) != len(
            completion._bodies
        ):
            return False
        if any(
            type(expected) is not _AdmittedPublicationIdentity
            or observed is not expected.body
            for observed, expected in zip(
                completion._bodies,
                record.admitted_body_identities,
            )
        ):
            return False
        try:
            if type(completion._publication_identities) is not tuple or len(
                completion._publication_identities
            ) != len(record.admitted_body_identities):
                return False
            for observed, expected in zip(
                completion._publication_identities,
                record.admitted_body_identities,
            ):
                _assert_independent_publication_identity(observed, expected)
            for item, identity in zip(
                completion._bodies,
                record.admitted_body_identities,
            ):
                item._assert_publication_registration_intact(identity)
            completion._assert_intact()
        except (AttributeError, ContractViolation, TypeError):
            return False
        return True

    def snapshot_completion(
        self, completion: ExecutionCompletion
    ) -> ExecutionPublicationSnapshot:
        """Capture exact admitted bytes once for an outer authority adapter.

        This verifies the runtime token, result envelope, coordinates, byte
        digests and sizes. It deliberately does not re-enter domain codecs:
        publication consumes the already-admitted canonical bytes, never the
        mutable decoded Python values.
        """

        if type(completion) is not ExecutionCompletion:
            raise TypeError("completion must be exact ExecutionCompletion")
        if completion._runtime_token is not self._runtime_token:
            raise ContractViolation("runtime does not own execution completion")
        with self._publication_records_lock:
            record = self._publication_records.get(completion)
        if record is None:
            raise ContractViolation("runtime has no execution publication record")
        bodies = completion._publication_bodies(
            expected_result_digest=ContentDigest(record.result_digest),
            expected_identities=record.admitted_body_identities,
        )
        if (
            completion._result_digest.value != record.result_digest
            or completion._result_wire != record.result_wire
            or completion._effect_digest.value != record.effect_digest
            or (
                completion._transition_digest.value
                if completion._transition_digest is not None
                else None
            )
            != record.transition_digest
        ):
            raise ContractViolation("execution publication cache was restamped")
        return ExecutionPublicationSnapshot(
            invocation_digest=completion._invocation_digest,
            profile_digest=completion._profile_digest,
            result=completion._result,
            result_digest=ContentDigest(record.result_digest),
            result_wire=record.result_wire,
            effect_digest=ContentDigest(record.effect_digest),
            transition_digest=(
                ContentDigest(record.transition_digest)
                if record.transition_digest is not None
                else None
            ),
            bodies=bodies,
        )

    def _assert_codec_current(self, contract: SemanticContractRef) -> None:
        codec = self._body_codecs[contract]
        if (
            type(codec.contract) is not SemanticContractRef
            or codec.contract != contract
            or type(codec.implementation) is not SemanticImplementationCoordinate
            or codec.implementation != self._codec_implementations[contract]
        ):
            raise ContractViolation("runtime body codec changed after admission")

    def _admit_body(
        self,
        body: SemanticBody,
        *,
        context: SemanticBodyValidationContext | None = None,
    ) -> AdmittedSemanticValue:
        if type(body) is not SemanticBody:
            raise TypeError("body must be exact SemanticBody")
        body.__post_init__()
        contract = body.coordinate.contract
        if contract not in self._body_codecs:
            raise ContractViolation("body contract has no admitted codec")
        self._assert_codec_current(contract)
        codec = self._body_codecs[contract]
        admission_token = object()
        if context is not None:
            context._register_body(
                _VALIDATION_CONTEXT_REGISTRATION,
                admission_token,
                self._codec_implementations[contract],
                body.coordinate,
                body.canonical_body,
            )
        value = _decode_with_context(codec, body.canonical_body, context)
        encoded = _encode_with_context(codec, value, context)
        if type(encoded) is not bytes or encoded != body.canonical_body:
            raise ContractViolation(
                "body codec did not round-trip exact canonical bytes"
            )
        return AdmittedSemanticValue(
            _BODY_ADMISSION,
            body,
            codec,
            value,
            self._codec_implementations[contract],
            context,
            admission_token,
        )

    def _admit_body_value(
        self,
        body: SemanticBody,
        value: object,
    ) -> AdmittedSemanticValue:
        """Admit an already-present value by its owning codec and exact bytes."""

        if type(body) is not SemanticBody:
            raise TypeError("body must be exact SemanticBody")
        body.__post_init__()
        contract = body.coordinate.contract
        if contract not in self._body_codecs:
            raise ContractViolation("body contract has no admitted codec")
        self._assert_codec_current(contract)
        codec = self._body_codecs[contract]
        encoded = codec.encode(value)
        if type(encoded) is not bytes or encoded != body.canonical_body:
            raise ContractViolation(
                "supplied semantic value differs from exact canonical body"
            )
        return AdmittedSemanticValue(
            _BODY_ADMISSION,
            body,
            codec,
            value,
            self._codec_implementations[contract],
            admission_token=object(),
        )

    def _validate_invocation(self, invocation: SemanticContractInvocation) -> None:
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError("invocation must be exact SemanticContractInvocation")
        invocation.to_wire()
        if self._profile.digest != self._profile_digest:
            raise ContractViolation("runtime profile was restamped after admission")
        for key, provider in self._providers.items():
            declaration = provider.declaration
            if (
                type(declaration) is not SemanticContractProviderDeclaration
                or declaration.digest != self._provider_declaration_digests[key]
            ):
                raise ContractViolation(
                    "runtime provider declaration changed after admission"
                )
        for contract in self._body_codecs:
            self._assert_codec_current(contract)
        if (
            invocation.profile_ref != self._profile.profile_ref
            or invocation.profile_digest != self._profile_digest
        ):
            raise ContractViolation("invocation selects a different profile")
        if invocation.target_package.package_kind not in self._profile.package_kinds:
            raise ContractViolation("target package kind is not admitted by profile")
        if invocation.operation_kind not in self._profile.operation_kinds:
            raise ContractViolation("operation kind is not admitted by profile")
        expected_inputs = {item.role: item.contract for item in self._profile.inputs}
        actual_inputs = {item.role: item.contract for item in invocation.inputs}
        if actual_inputs != expected_inputs:
            raise ContractViolation("invocation input closure differs from profile")
        expected_providers = {item.provider_key for item in self._profile.providers}
        actual_providers = {item.provider_key for item in invocation.provider_bindings}
        if actual_providers != expected_providers:
            raise ContractViolation("invocation binding closure differs from profile")
        actual_codecs = {
            item.contract: item.implementation
            for item in invocation.body_codec_bindings
        }
        if actual_codecs != self._codec_implementations:
            raise ContractViolation("invocation codec closure differs from runtime")
        if not set(invocation.requested_output_roles).issubset(
            self._profile.terminal_output_roles
        ):
            raise ContractViolation(
                "invocation requests undeclared terminal output roles"
            )

    def _admit_invocation_bodies(
        self,
        invocation: SemanticContractInvocation,
        input_bodies: tuple[SemanticBody, ...],
        predecessor_body: SemanticBody | None,
        *,
        input_values: tuple[object, ...] | None = None,
        diagnostic_spans_ns: list[tuple[str, int]] | None = None,
    ) -> tuple[
        dict[str, AdmittedSemanticValue],
        AdmittedSemanticValue | None,
        dict[SemanticValueCoordinate, AdmittedSemanticValue],
    ]:
        if type(input_bodies) is not tuple or any(
            type(item) is not SemanticBody for item in input_bodies
        ):
            raise TypeError("input_bodies must be an exact tuple of SemanticBody")
        if len({item.coordinate for item in input_bodies}) != len(input_bodies):
            raise ContractViolation("input bodies contain duplicate coordinates")
        if {item.coordinate for item in input_bodies} != set(invocation.inputs):
            raise ContractViolation("input body closure differs from invocation inputs")
        if input_values is not None and (
            type(input_values) is not tuple
            or len(input_values) != len(input_bodies)
        ):
            raise TypeError("input_values must align as an exact tuple")
        admitted_items: list[AdmittedSemanticValue] = []
        if input_values is None:
            body_values = tuple((body, None) for body in input_bodies)
        else:
            body_values = tuple(zip(input_bodies, input_values, strict=True))
        for body, value in body_values:
            admission_started = perf_counter_ns()
            admitted_items.append(
                self._admit_body(body)
                if input_values is None
                else self._admit_body_value(body, value)
            )
            if diagnostic_spans_ns is not None:
                diagnostic_spans_ns.append(
                    (
                        f"code_codec_admission:{body.coordinate.role}",
                        perf_counter_ns() - admission_started,
                    )
                )
        admitted_inputs = tuple(admitted_items)
        for admitted in admitted_inputs:
            validation_started = perf_counter_ns()
            contract = admitted._coordinate.contract
            self._assert_codec_current(contract)
            codec = self._body_codecs[contract]
            validate = getattr(codec, "validate_invocation", None)
            if validate is None:
                if diagnostic_spans_ns is not None:
                    diagnostic_spans_ns.append(
                        (
                            f"code_invocation_validation:{admitted._coordinate.role}",
                            perf_counter_ns() - validation_started,
                        )
                    )
                continue
            if not callable(validate):
                raise ContractViolation("codec invocation validator must be callable")
            invocation_digest = invocation.digest
            validation_result = validate(admitted._value, invocation)
            self._assert_codec_current(contract)
            if (
                validation_result is not None
                or invocation.digest != invocation_digest
                or codec.encode(admitted._value) != admitted._canonical_body
            ):
                raise ContractViolation("codec invocation validator changed its inputs")
            if diagnostic_spans_ns is not None:
                diagnostic_spans_ns.append(
                    (
                        f"code_invocation_validation:{admitted._coordinate.role}",
                        perf_counter_ns() - validation_started,
                    )
                )
        role_ledger = {item._coordinate.role: item for item in admitted_inputs}
        body_ledger = {item._coordinate: item for item in admitted_inputs}

        admitted_predecessor: AdmittedSemanticValue | None = None
        if type(invocation.predecessor) is TypedEmptyCoordinate:
            if predecessor_body is not None:
                raise ContractViolation(
                    "typed-empty invocation cannot carry predecessor body"
                )
        else:
            if type(predecessor_body) is not SemanticBody:
                raise ContractViolation("exact predecessor requires one canonical body")
            if predecessor_body.coordinate != invocation.predecessor:
                raise ContractViolation(
                    "predecessor body coordinate differs from invocation"
                )
            admitted_predecessor = self._admit_body(predecessor_body)
            body_ledger[admitted_predecessor._coordinate] = admitted_predecessor
        return role_ledger, admitted_predecessor, body_ledger

    @staticmethod
    def _referenced_result_coordinates(
        result: SemanticContractResult,
    ) -> set[SemanticValueCoordinate]:
        coordinates: set[SemanticValueCoordinate] = set()
        if result.current_result is not None:
            coordinates.add(result.current_result)
        if result.transition is not None:
            coordinates.add(result.transition.result)
            coordinates.add(result.transition.transition_body)
        if result.effect is not None:
            coordinates.add(result.effect.candidate_state)
            coordinates.add(result.effect.effect_body)
            coordinates.update(result.effect.renderer_inputs)
        coordinates.update(item.output for item in result.outputs)
        return coordinates

    def _admit_provider_body_closure(
        self,
        *,
        step_invocation: ProviderStepInvocation,
        result: SemanticContractResult,
        bodies: tuple[SemanticBody, ...],
        body_ledger: dict[SemanticValueCoordinate, AdmittedSemanticValue],
        validation_epoch: _SemanticBodyValidationEpoch,
    ) -> None:
        supplied = {item.coordinate: item for item in bodies}
        if len(supplied) != len(bodies):
            raise ContractViolation("provider body closure contains duplicates")
        candidate_coordinate = (
            result.current_result
            if result.current_result is not None
            else None
            if result.transition is None
            else result.transition.result
        )
        if candidate_coordinate is None or result.effect is None:
            raise ContractViolation("successful provider result lacks candidate/effect")

        def admit_stateless(
            coordinate: SemanticValueCoordinate,
        ) -> AdmittedSemanticValue:
            admitted = body_ledger.get(coordinate)
            if admitted is not None:
                return admitted
            body = supplied.pop(coordinate, None)
            if body is None:
                raise ContractViolation("provider omitted a referenced semantic body")
            admitted = self._admit_body(body)
            body_ledger[coordinate] = admitted
            return admitted

        candidate = admit_stateless(candidate_coordinate)
        transition: AdmittedSemanticValue | None = None
        if result.transition is not None:
            coordinate = result.transition.transition_body
            body = supplied.pop(coordinate, None)
            if body is None:
                transition = body_ledger.get(coordinate)
                if transition is None:
                    raise ContractViolation("provider omitted its transition body")
            else:
                transition = self._admit_body(
                    body,
                    context=SemanticBodyValidationContext(
                        purpose="transition",
                        coordinate=coordinate,
                        invocation_digest=step_invocation.invocation.digest,
                        input_closure_digest=step_invocation.input_closure_digest,
                        provider_key=step_invocation.declaration.provider_key,
                        target_package=step_invocation.invocation.target_package,
                        inputs=step_invocation.inputs,
                        predecessor=step_invocation.predecessor,
                        candidate=candidate,
                        outer_transition_impacts=result.transition.impacts,
                        outer_effect_impacts=result.effect.impacts,
                        _validation_epoch=validation_epoch,
                        _runtime_token=self._runtime_token,
                        _execution_attempt_token=validation_epoch._attempt_token,
                        _profile_digest=step_invocation.invocation.profile_digest,
                    ),
                )
                body_ledger[coordinate] = transition

        effect_coordinate = result.effect.effect_body
        effect_body = supplied.pop(effect_coordinate, None)
        if effect_body is None:
            effect = body_ledger.get(effect_coordinate)
            if effect is None:
                raise ContractViolation("provider omitted its prepared-effect body")
        else:
            effect = self._admit_body(
                effect_body,
                context=SemanticBodyValidationContext(
                    purpose="effect",
                    coordinate=effect_coordinate,
                    invocation_digest=step_invocation.invocation.digest,
                    input_closure_digest=step_invocation.input_closure_digest,
                    provider_key=step_invocation.declaration.provider_key,
                    target_package=step_invocation.invocation.target_package,
                    inputs=step_invocation.inputs,
                    predecessor=step_invocation.predecessor,
                    candidate=candidate,
                    transition=transition,
                    outer_transition_impacts=(
                        None if result.transition is None else result.transition.impacts
                    ),
                    outer_effect_impacts=result.effect.impacts,
                    _validation_epoch=validation_epoch,
                    _runtime_token=self._runtime_token,
                    _execution_attempt_token=validation_epoch._attempt_token,
                    _profile_digest=step_invocation.invocation.profile_digest,
                ),
            )
            body_ledger[effect_coordinate] = effect

        for coordinate in result.effect.renderer_inputs:
            admit_stateless(coordinate)

        for output in result.outputs:
            coordinate = output.output
            body = supplied.pop(coordinate, None)
            if body is None:
                admitted_output = body_ledger.get(coordinate)
                if admitted_output is None:
                    raise ContractViolation("provider omitted a declared output body")
                continue
            admitted_output = self._admit_body(
                body,
                context=SemanticBodyValidationContext(
                    purpose="output",
                    coordinate=coordinate,
                    invocation_digest=step_invocation.invocation.digest,
                    input_closure_digest=step_invocation.input_closure_digest,
                    provider_key=step_invocation.declaration.provider_key,
                    target_package=step_invocation.invocation.target_package,
                    inputs=step_invocation.inputs,
                    predecessor=step_invocation.predecessor,
                    candidate=candidate,
                    transition=transition,
                    effect=effect,
                    outer_transition_impacts=(
                        None if result.transition is None else result.transition.impacts
                    ),
                    outer_effect_impacts=result.effect.impacts,
                    _validation_epoch=validation_epoch,
                    _runtime_token=self._runtime_token,
                    _execution_attempt_token=validation_epoch._attempt_token,
                    _profile_digest=step_invocation.invocation.profile_digest,
                ),
            )
            body_ledger[coordinate] = admitted_output

        if supplied:
            raise ContractViolation("provider returned unreferenced semantic bodies")

    async def execute(
        self,
        invocation: SemanticContractInvocation,
        input_bodies: tuple[SemanticBody, ...],
        *,
        predecessor_body: SemanticBody | None = None,
    ) -> ExecutionCompletion:
        from .selected_provider import _reject_untracked_direct_execution

        _reject_untracked_direct_execution(self)
        self._validate_invocation(invocation)
        execution_attempt_token = object()
        invocation_digest = invocation.digest
        role_ledger, admitted_predecessor, body_ledger = self._admit_invocation_bodies(
            invocation,
            input_bodies,
            predecessor_body,
        )
        bindings = {item.provider_key: item for item in invocation.provider_bindings}
        step_results: dict[str, SemanticContractResult] = {}

        for step in self._resolved_steps:
            provider = self._providers[step.provider_key]
            declaration = provider.declaration
            if (
                type(declaration) is not SemanticContractProviderDeclaration
                or declaration.digest
                != self._provider_declaration_digests[step.provider_key]
            ):
                raise ContractViolation("provider declaration changed before execution")
            bound_inputs = tuple(
                BoundSemanticInput(item.target_role, role_ledger[item.source_role])
                for item in step.bindings
            )
            step_invocation = ProviderStepInvocation(
                invocation=invocation,
                step=step,
                declaration=declaration,
                binding=bindings[step.provider_key],
                inputs=bound_inputs,
                predecessor=admitted_predecessor,
                dependencies=invocation.dependencies,
            )
            derivation = await provider.derive(step_invocation)
            result = self._accept_provider_derivation(
                invocation_digest, step_invocation, derivation, body_ledger,
                execution_attempt_token,
            )
            if result.current_result is not None:
                candidate = result.current_result
            elif result.transition is not None:
                candidate = result.transition.result
            else:
                raise ContractViolation(
                    "successful provider result has no semantic result"
                )
            role_ledger[candidate.role] = body_ledger[candidate]
            effect = result.effect
            assert effect is not None  # Guaranteed by shared derivation admission.
            role_ledger[effect.effect_body.role] = body_ledger[effect.effect_body]
            for output in result.outputs:
                role_ledger[output.output.role] = body_ledger[output.output]
            step_results[step.step_key] = result

        return self._publish_terminal_completion(
            invocation, invocation_digest, step_results, body_ledger
        )

    def _accept_provider_derivation(
        self,
        invocation_digest: ContentDigest,
        step_invocation: ProviderStepInvocation,
        derivation: ProviderDerivation,
        body_ledger: dict[SemanticValueCoordinate, AdmittedSemanticValue],
        execution_attempt_token: object,
    ) -> SemanticContractResult:
        invocation = step_invocation.invocation
        declaration = step_invocation.declaration
        step = step_invocation.step
        provider = self._providers[step.provider_key]
        if type(derivation) is not ProviderDerivation:
            raise TypeError("provider must return exact ProviderDerivation")
        derivation.__post_init__()
        if invocation.digest != invocation_digest:
            raise ContractViolation("invocation changed during provider execution")
        for body in body_ledger.values():
            body._assert_intact()
        returned_declaration = provider.declaration
        if (
            type(returned_declaration) is not SemanticContractProviderDeclaration
            or returned_declaration.digest
            != self._provider_declaration_digests[step.provider_key]
            or returned_declaration != declaration
        ):
            raise ContractViolation("provider declaration changed during execution")
        result = derivation.result
        validate_result_context(result, declaration, invocation)
        if result.status not in (TerminalStatus.CURRENT, TerminalStatus.DELTA):
            if derivation.bodies:
                raise ContractViolation(
                    "failed provider returned publishable bodies"
                )
            raise ProviderTerminalFailure(result)
        if result.effect is None:
            raise ContractViolation(
                "successful provider result has no prepared effect"
            )
        if (
            result.transition is not None
            and result.transition.input_closure_digest
            != step_invocation.input_closure_digest
        ):
            raise ContractViolation(
                "transition does not bind provider input closure"
            )

        referenced = self._referenced_result_coordinates(result)
        needed = referenced - set(body_ledger)
        supplied = {item.coordinate for item in derivation.bodies}
        if supplied != needed:
            raise ContractViolation(
                "provider body closure differs from result-referenced coordinates"
            )
        self._admit_provider_body_closure(
            step_invocation=step_invocation,
            result=result,
            bodies=derivation.bodies,
            body_ledger=body_ledger,
            validation_epoch=_SemanticBodyValidationEpoch(
                _VALIDATION_EPOCH_CONSTRUCTION,
                self._runtime_token,
                execution_attempt_token,
                step_invocation.invocation.digest,
                step_invocation.invocation.profile_digest,
                step_invocation.declaration.provider_key,
                step_invocation.binding.implementation,
                step_invocation.declaration.digest,
            ),
        )
        return result

    def _publish_terminal_completion(
        self,
        invocation: SemanticContractInvocation,
        invocation_digest: ContentDigest,
        step_results: dict[str, SemanticContractResult],
        body_ledger: dict[SemanticValueCoordinate, AdmittedSemanticValue],
    ) -> ExecutionCompletion:
        producer_by_role: dict[str, str] = {}
        declarations = {item.provider_key: item for item in self._profile.providers}
        for step in self._profile.steps:
            declaration = declarations[step.provider_key]
            for role in (
                declaration.result_role.role,
                declaration.effect_role.role,
                *(item.role for item in declaration.output_roles),
            ):
                producer_by_role[role] = step.step_key
        result_step = producer_by_role[self._profile.terminal_result_role]
        if producer_by_role[self._profile.terminal_effect_role] != result_step or any(
            producer_by_role[role] != result_step
            for role in self._profile.terminal_output_roles
        ):
            raise ContractViolation(
                "terminal roles do not belong to one atomic provider result"
            )
        result = step_results[result_step]
        actual_output_roles = {item.output.role for item in result.outputs}
        expected_output_roles = (
            set()
            if result.status is TerminalStatus.CURRENT
            else set(invocation.requested_output_roles)
        )
        if expected_output_roles != actual_output_roles:
            raise ContractViolation(
                "provider output closure differs from terminal-status demand"
            )
        bodies = tuple(
            sorted(
                body_ledger.values(),
                key=lambda item: canonical_json_bytes(item._coordinate.to_wire()),
            )
        )
        completion = ExecutionCompletion(
            _COMPLETION_CONSTRUCTION,
            self._runtime_token,
            invocation_digest,
            self._profile_digest,
            result,
            bodies,
        )
        publication_record = _ExecutionPublicationRecord(
            result_digest=completion._result_digest.value,
            result_wire=completion._result_wire,
            effect_digest=completion._effect_digest.value,
            transition_digest=(
                completion._transition_digest.value
                if completion._transition_digest is not None
                else None
            ),
            admitted_body_identities=tuple(
                _capture_admitted_publication_identity(item)
                for item in completion._bodies
            ),
        )
        with self._publication_records_lock:
            self._publication_records[completion] = publication_record
        return completion


    def _complete_selected_derivation(self, admission, derivation) -> ExecutionCompletion:
        from .selected_provider import _begin_selected_terminal_completion

        step = _begin_selected_terminal_completion(self, admission, derivation)
        self._validate_invocation(step.invocation)
        if len(self._resolved_steps) != 1 or step.step != self._resolved_steps[0]:
            raise ContractViolation("selected completion requires one exact terminal step")
        body_ledger = {item.admitted.coordinate: item.admitted for item in step.inputs}
        if step.predecessor is not None:
            body_ledger[step.predecessor.coordinate] = step.predecessor
        result = self._accept_provider_derivation(
            step.invocation.digest, step, derivation, body_ledger, object()
        )
        return self._publish_terminal_completion(
            step.invocation, step.invocation.digest,
            {step.step.step_key: result}, body_ledger,
        )


def _publication_body_coordinates(
    result: SemanticContractResult,
) -> tuple[SemanticValueCoordinate, ...]:
    effect = result.effect
    if (
        result.status not in (TerminalStatus.CURRENT, TerminalStatus.DELTA)
        or effect is None
    ):
        raise ContractViolation("completion result has no publishable terminal closure")
    coordinates: list[SemanticValueCoordinate] = [effect.effect_body]
    if result.current_result is not None:
        coordinates.append(result.current_result)
    if result.transition is not None:
        coordinates.extend(
            (result.transition.result, result.transition.transition_body)
        )
    coordinates.extend(effect.renderer_inputs)
    coordinates.extend(item.output for item in result.outputs)
    unique = {canonical_json_bytes(item.to_wire()): item for item in coordinates}
    return tuple(unique[key] for key in sorted(unique))


__all__ = [
    "AdmittedSemanticValue",
    "BoundSemanticInput",
    "ContextualSemanticBodyCodec",
    "ExecutionCompletion",
    "ExecutionPublicationSnapshot",
    "ProviderDerivation",
    "ProviderStepInvocation",
    "ProviderTerminalFailure",
    "SemanticBody",
    "SemanticBodyCodec",
    "SemanticBodyValidationContext",
    "SemanticContractProvider",
    "SemanticContractRuntime",
]
