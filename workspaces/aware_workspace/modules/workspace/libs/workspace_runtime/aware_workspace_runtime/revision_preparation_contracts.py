# pyright: reportArgumentType=false, reportImplicitOverride=false
"""Portable exact values for zero-write Workspace revision preparation."""

from __future__ import annotations

import hashlib
import re
import weakref
from dataclasses import dataclass
from threading import RLock
from typing import ClassVar, Self, cast

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)

from .revision_preparation_codec import (
    WorkspaceRevisionPreparationContractError,
    canonical_revision_preparation_json_bytes,
    decode_revision_preparation_json_object,
    require_exact_keys,
)

WORKSPACE_REVISION_PIN_SLOT = "aware.workspace.revision-pin-slot.v1"
WORKSPACE_REVISION_PREPARED_PACKAGE_PIN = (
    "aware.workspace.revision-prepared-package-pin.v1"
)
WORKSPACE_REVISION_PACKAGE_MEMBERSHIP_TRANSITION = (
    "aware.workspace.revision-package-membership-transition.v1"
)
WORKSPACE_REVISION_PACKAGE_MEMBERSHIP_TRANSITION_SET = (
    "aware.workspace.revision-package-membership-transition-set.v1"
)
WORKSPACE_REVISION_PREDECESSOR_ADMISSION = (
    "aware.workspace.revision-predecessor-admission.v1"
)
WORKSPACE_REVISION_SELECTION_SCOPE_ADMISSION = (
    "aware.workspace.revision-selection-scope-admission.v1"
)
WORKSPACE_REVISION_SOURCE_PACKAGE_ENTRY = (
    "aware.workspace.revision-source-package-entry.v1"
)
WORKSPACE_REVISION_SOURCE_CLOSURE = "aware.workspace.revision-source-closure.v1"
WORKSPACE_REVISION_SOURCE_CLOSURE_ADMISSION = (
    "aware.workspace.revision-source-closure-admission.v1"
)
WORKSPACE_REVISION_STATE = "aware.workspace.revision-state.v1"
WORKSPACE_REVISION_CANDIDATE = "aware.workspace.revision-candidate.v1"
WORKSPACE_REVISION_PREPARATION_EVIDENCE = (
    "aware.workspace.revision-preparation-evidence.v1"
)
WORKSPACE_MATERIALIZATION_GRAPH_EXECUTION_ADMISSION = (
    "aware.workspace.materialization-graph-execution-admission.v1"
)

WORKSPACE_REVISION_PREPARATION_REFUSAL_CODES = (
    "operation_currentness_mismatch",
    "predecessor_authority_unavailable",
    "source_closure_not_admitted",
    "selection_scope_not_admitted",
    "graph_execution_provenance_unavailable",
    "graph_not_succeeded",
    "graph_coverage_mismatch",
    "package_membership_transition_invalid",
    "pin_derivation_invalid",
    "pin_slot_collision",
    "source_result_mismatch",
    "state_derivation_invalid",
)

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_LINEAGE = re.compile(
    r"^workspace-package-lineage:"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_ISSUED_LOCK = RLock()
_ISSUED: dict[int, tuple[weakref.ReferenceType[object], bytes]] = {}


def _record_issued(value: object, wire: bytes) -> None:
    identity = id(value)

    def remove(reference: weakref.ReferenceType[object]) -> None:
        with _ISSUED_LOCK:
            current = _ISSUED.get(identity)
            if current is not None and current[0] is reference:
                _ISSUED.pop(identity, None)

    reference = weakref.ref(value, remove)
    with _ISSUED_LOCK:
        _ISSUED[identity] = (reference, wire)


def _require_issued(value: object, wire: bytes) -> None:
    with _ISSUED_LOCK:
        record = _ISSUED.get(id(value))
    if record is None or record[0]() is not value or record[1] != wire:
        raise WorkspaceRevisionPreparationContractError(
            "revision preparation value differs from issued state"
        )


def _text(value: object, path: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise WorkspaceRevisionPreparationContractError(
            f"{path} must be exact nonempty unpadded text"
        )
    return value


def _digest_text(value: object, path: str) -> str:
    result = _text(value, path)
    if _DIGEST.fullmatch(result) is None:
        raise WorkspaceRevisionPreparationContractError(
            f"{path} must be canonical SHA-256"
        )
    return result


def _lineage(value: object, path: str) -> str:
    result = _text(value, path)
    if _LINEAGE.fullmatch(result) is None:
        raise WorkspaceRevisionPreparationContractError(
            f"{path} must be a canonical Workspace package lineage ref"
        )
    return result


def _nonnegative(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceRevisionPreparationContractError(
            f"{path} must be exact nonnegative int"
        )
    return value


def _literal(value: object, allowed: tuple[str, ...], path: str) -> str:
    result = _text(value, path)
    if result not in allowed:
        raise WorkspaceRevisionPreparationContractError(f"{path} is unsupported")
    return result


def _exact_tuple(value: object, expected: type, path: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    for index, item in enumerate(value):
        if type(item) is not expected:
            raise TypeError(f"{path}[{index}] must be exact {expected.__name__}")
        item.canonical_bytes()
    return value


def _wire_list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{path} must be exact list")
    return cast(list[object], value)


def _body_digest(domain: str, body: dict[str, object]) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            domain.encode("utf-8")
            + b"\0"
            + canonical_revision_preparation_json_bytes(body)
        ).hexdigest()
    )


def _code_contract_from_wire(value: object, path: str) -> SemanticContractRef:
    root = require_exact_keys(
        value, frozenset({"key", "schema_digest", "version"}), path
    )
    return SemanticContractRef(
        key=_text(root["key"], f"{path}.key"),
        version=_text(root["version"], f"{path}.version"),
        schema_digest=ContentDigest(
            _digest_text(root["schema_digest"], f"{path}.schema_digest")
        ),
    )


def _code_package_from_wire(value: object, path: str) -> SemanticPackageCoordinate:
    root = require_exact_keys(
        value, frozenset({"manifest_digest", "package_kind", "package_ref"}), path
    )
    return SemanticPackageCoordinate(
        package_ref=_text(root["package_ref"], f"{path}.package_ref"),
        package_kind=_text(root["package_kind"], f"{path}.package_kind"),
        manifest_digest=ContentDigest(
            _digest_text(root["manifest_digest"], f"{path}.manifest_digest")
        ),
    )


def _code_value_from_wire(value: object, path: str) -> SemanticValueCoordinate:
    root = require_exact_keys(
        value,
        frozenset({"contract", "digest", "role", "size_bytes", "value_ref"}),
        path,
    )
    return SemanticValueCoordinate(
        role=_text(root["role"], f"{path}.role"),
        contract=_code_contract_from_wire(root["contract"], f"{path}.contract"),
        value_ref=_text(root["value_ref"], f"{path}.value_ref"),
        digest=ContentDigest(_digest_text(root["digest"], f"{path}.digest")),
        size_bytes=_nonnegative(root["size_bytes"], f"{path}.size_bytes"),
    )


class _PortableValue:
    SCHEMA: ClassVar[str]
    DIGEST_FIELD: ClassVar[str]

    def _wire_unchecked(self) -> dict[str, object]:
        raise NotImplementedError

    @classmethod
    def from_wire(cls, value: object) -> Self:
        del value
        raise NotImplementedError

    def _seal(self) -> None:
        wire = canonical_revision_preparation_json_bytes(self._wire_unchecked())
        _record_issued(self, wire)

    def to_wire(self) -> dict[str, object]:
        wire = self._wire_unchecked()
        _require_issued(self, canonical_revision_preparation_json_bytes(wire))
        return cast(dict[str, object], _copy_wire(wire))

    def canonical_bytes(self) -> bytes:
        return canonical_revision_preparation_json_bytes(self.to_wire())

    @classmethod
    def from_canonical_bytes(cls, value: bytes) -> Self:
        result = cls.from_wire(decode_revision_preparation_json_object(value))
        if result.canonical_bytes() != value:
            raise WorkspaceRevisionPreparationContractError(
                f"{cls.__name__} canonical bytes differ"
            )
        return result


def _copy_wire(value: object) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is list:
        return [_copy_wire(item) for item in cast(list[object], value)]
    if type(value) is dict:
        return {
            key: _copy_wire(item)
            for key, item in cast(dict[str, object], value).items()
        }
    raise TypeError("portable wire contains foreign value")


def _validate_digest(value: _PortableValue, field: str, domain: str) -> None:
    wire = value._wire_unchecked()
    supplied = _digest_text(getattr(value, field), field)
    body = {key: item for key, item in wire.items() if key != field}
    if supplied != _body_digest(domain, body):
        raise WorkspaceRevisionPreparationContractError(f"{field} mismatched")


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionPinSlot(_PortableValue):
    package_lineage_ref: str
    result_role: str
    semantic_contract: SemanticContractRef
    slot_digest: str

    SCHEMA = WORKSPACE_REVISION_PIN_SLOT
    DIGEST_FIELD = "slot_digest"

    @classmethod
    def create(
        cls,
        *,
        package_lineage_ref: str,
        result_role: str,
        semantic_contract: SemanticContractRef,
    ) -> Self:
        if type(semantic_contract) is not SemanticContractRef:
            raise TypeError("slot.semantic_contract must be exact SemanticContractRef")
        semantic_contract.__post_init__()
        body = {
            "codec_version": 1,
            "package_lineage_ref": _lineage(
                package_lineage_ref, "slot.package_lineage_ref"
            ),
            "result_role": _text(result_role, "slot.result_role"),
            "schema": cls.SCHEMA,
            "semantic_contract": semantic_contract.to_wire(),
        }
        return cls(
            package_lineage_ref=package_lineage_ref,
            result_role=result_role,
            semantic_contract=semantic_contract,
            slot_digest=_body_digest(cls.SCHEMA, body),
        )

    def __post_init__(self) -> None:
        _lineage(self.package_lineage_ref, "slot.package_lineage_ref")
        _text(self.result_role, "slot.result_role")
        if type(self.semantic_contract) is not SemanticContractRef:
            raise TypeError("slot.semantic_contract must be exact SemanticContractRef")
        self.semantic_contract.__post_init__()
        _validate_digest(self, "slot_digest", self.SCHEMA)
        self._seal()

    def ordering_key(self) -> tuple[bytes, bytes, bytes, bytes, bytes]:
        contract = self.semantic_contract
        return (
            self.package_lineage_ref.encode("utf-8"),
            self.result_role.encode("utf-8"),
            contract.key.encode("utf-8"),
            contract.version.encode("utf-8"),
            contract.schema_digest.value.encode("utf-8"),
        )

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            "codec_version": 1,
            "package_lineage_ref": self.package_lineage_ref,
            "result_role": self.result_role,
            "schema": self.SCHEMA,
            "semantic_contract": self.semantic_contract.to_wire(),
            "slot_digest": self.slot_digest,
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        root = require_exact_keys(
            value,
            frozenset(
                {
                    "codec_version",
                    "package_lineage_ref",
                    "result_role",
                    "schema",
                    "semantic_contract",
                    "slot_digest",
                }
            ),
            "slot",
        )
        _constant_header(root, cls.SCHEMA, "slot")
        return cls(
            package_lineage_ref=_lineage(
                root["package_lineage_ref"], "slot.package_lineage_ref"
            ),
            result_role=_text(root["result_role"], "slot.result_role"),
            semantic_contract=_code_contract_from_wire(
                root["semantic_contract"], "slot.semantic_contract"
            ),
            slot_digest=_digest_text(root["slot_digest"], "slot.slot_digest"),
        )


def _constant_header(root: dict[str, object], schema: str, path: str) -> None:
    if type(root["codec_version"]) is not int or root["codec_version"] != 1:
        raise WorkspaceRevisionPreparationContractError(f"{path}.codec_version differs")
    if type(root["schema"]) is not str or root["schema"] != schema:
        raise WorkspaceRevisionPreparationContractError(f"{path}.schema differs")


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionPreparedPackagePin(_PortableValue):
    slot: WorkspaceRevisionPinSlot
    semantic_package: SemanticPackageCoordinate
    source_package_identity_digest: str
    source_after_state_authority_digest: str
    code_intent_digest: str
    code_match_digest: str
    execution_input_closure_digest: str
    result_coordinate: SemanticValueCoordinate
    package_head_revision: int
    package_head_digest: str
    package_head_body_sha256: str
    pin_digest: str

    SCHEMA = WORKSPACE_REVISION_PREPARED_PACKAGE_PIN
    DIGEST_FIELD = "pin_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body_from_values(values)
        return cls(**values, pin_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body_from_values(cls, values: dict[str, object]) -> dict[str, object]:
        slot = cast(WorkspaceRevisionPinSlot, values["slot"])
        package = cast(SemanticPackageCoordinate, values["semantic_package"])
        result = cast(SemanticValueCoordinate, values["result_coordinate"])
        if type(slot) is not WorkspaceRevisionPinSlot:
            raise TypeError("pin.slot must be exact WorkspaceRevisionPinSlot")
        slot.canonical_bytes()
        if type(package) is not SemanticPackageCoordinate:
            raise TypeError(
                "pin.semantic_package must be exact SemanticPackageCoordinate"
            )
        package.__post_init__()
        if type(result) is not SemanticValueCoordinate:
            raise TypeError(
                "pin.result_coordinate must be exact SemanticValueCoordinate"
            )
        result.__post_init__()
        if (
            slot.result_role != result.role
            or slot.semantic_contract.to_wire() != result.contract.to_wire()
        ):
            raise WorkspaceRevisionPreparationContractError(
                "pin result coordinate differs from its stable slot"
            )
        body: dict[str, object] = {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "slot": slot.to_wire(),
            "semantic_package": package.to_wire(),
            "result_coordinate": result.to_wire(),
            "package_head_revision": _nonnegative(
                values["package_head_revision"], "pin.package_head_revision"
            ),
        }
        for field in (
            "source_package_identity_digest",
            "source_after_state_authority_digest",
            "code_intent_digest",
            "code_match_digest",
            "execution_input_closure_digest",
            "package_head_digest",
            "package_head_body_sha256",
        ):
            body[field] = _digest_text(values[field], f"pin.{field}")
        return body

    def __post_init__(self) -> None:
        _validate_digest(self, "pin_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body_from_values(self.__dict_values()),
            "pin_digest": self.pin_digest,
        }

    def __dict_values(self) -> dict[str, object]:
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "pin_digest"
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "slot",
            "semantic_package",
            "source_package_identity_digest",
            "source_after_state_authority_digest",
            "code_intent_digest",
            "code_match_digest",
            "execution_input_closure_digest",
            "result_coordinate",
            "package_head_revision",
            "package_head_digest",
            "package_head_body_sha256",
            "pin_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "pin")
        _constant_header(root, cls.SCHEMA, "pin")
        return cls(
            slot=WorkspaceRevisionPinSlot.from_wire(root["slot"]),
            semantic_package=_code_package_from_wire(
                root["semantic_package"], "pin.semantic_package"
            ),
            source_package_identity_digest=_digest_text(
                root["source_package_identity_digest"],
                "pin.source_package_identity_digest",
            ),
            source_after_state_authority_digest=_digest_text(
                root["source_after_state_authority_digest"],
                "pin.source_after_state_authority_digest",
            ),
            code_intent_digest=_digest_text(
                root["code_intent_digest"], "pin.code_intent_digest"
            ),
            code_match_digest=_digest_text(
                root["code_match_digest"], "pin.code_match_digest"
            ),
            execution_input_closure_digest=_digest_text(
                root["execution_input_closure_digest"],
                "pin.execution_input_closure_digest",
            ),
            result_coordinate=_code_value_from_wire(
                root["result_coordinate"], "pin.result_coordinate"
            ),
            package_head_revision=_nonnegative(
                root["package_head_revision"], "pin.package_head_revision"
            ),
            package_head_digest=_digest_text(
                root["package_head_digest"], "pin.package_head_digest"
            ),
            package_head_body_sha256=_digest_text(
                root["package_head_body_sha256"], "pin.package_head_body_sha256"
            ),
            pin_digest=_digest_text(root["pin_digest"], "pin.pin_digest"),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionPackageMembershipTransitionAuthority(_PortableValue):
    disposition: str
    workspace_ref: str
    operation_authority_digest: str
    package_lineage_ref: str
    predecessor_membership_digest: str | None
    current_membership_proof_digest: str | None
    current_nonmembership_proof_digest: str | None
    current_source_after_state_authority_digest: str | None
    authority_digest: str

    SCHEMA = WORKSPACE_REVISION_PACKAGE_MEMBERSHIP_TRANSITION
    DIGEST_FIELD = "authority_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, authority_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        disposition = _literal(
            values["disposition"], ("present", "removed"), "membership.disposition"
        )
        optional = {}
        for field in (
            "predecessor_membership_digest",
            "current_membership_proof_digest",
            "current_nonmembership_proof_digest",
            "current_source_after_state_authority_digest",
        ):
            item = values[field]
            optional[field] = (
                None if item is None else _digest_text(item, f"membership.{field}")
            )
        if disposition == "present":
            if (
                optional["current_membership_proof_digest"] is None
                or optional["current_source_after_state_authority_digest"] is None
                or optional["current_nonmembership_proof_digest"] is not None
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "present membership nullability differs"
                )
        elif (
            optional["predecessor_membership_digest"] is None
            or optional["current_nonmembership_proof_digest"] is None
            or optional["current_membership_proof_digest"] is not None
            or optional["current_source_after_state_authority_digest"] is not None
        ):
            raise WorkspaceRevisionPreparationContractError(
                "removed membership nullability differs"
            )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "disposition": disposition,
            "workspace_ref": _text(values["workspace_ref"], "membership.workspace_ref"),
            "operation_authority_digest": _digest_text(
                values["operation_authority_digest"],
                "membership.operation_authority_digest",
            ),
            "package_lineage_ref": _lineage(
                values["package_lineage_ref"], "membership.package_lineage_ref"
            ),
            **optional,
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "authority_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "authority_digest"
        }
        return {**self._body(values), "authority_digest": self.authority_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "disposition",
            "workspace_ref",
            "operation_authority_digest",
            "package_lineage_ref",
            "predecessor_membership_digest",
            "current_membership_proof_digest",
            "current_nonmembership_proof_digest",
            "current_source_after_state_authority_digest",
            "authority_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "membership")
        _constant_header(root, cls.SCHEMA, "membership")
        values = {
            field: root[field]
            for field in fields - {"codec_version", "schema", "authority_digest"}
        }
        return cls(
            **values,
            authority_digest=_digest_text(
                root["authority_digest"], "membership.authority_digest"
            ),
        )  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionPackageMembershipTransitionSet(_PortableValue):
    ordered_authorities: tuple[
        WorkspaceRevisionPackageMembershipTransitionAuthority, ...
    ]
    set_digest: str

    SCHEMA = WORKSPACE_REVISION_PACKAGE_MEMBERSHIP_TRANSITION_SET
    DIGEST_FIELD = "set_digest"

    @classmethod
    def create(
        cls,
        *,
        ordered_authorities: tuple[
            WorkspaceRevisionPackageMembershipTransitionAuthority, ...
        ],
    ) -> Self:
        body = cls._body({"ordered_authorities": ordered_authorities})
        return cls(
            ordered_authorities=ordered_authorities,
            set_digest=_body_digest(cls.SCHEMA, body),
        )

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        items = cast(
            tuple[WorkspaceRevisionPackageMembershipTransitionAuthority, ...],
            _exact_tuple(
                values["ordered_authorities"],
                WorkspaceRevisionPackageMembershipTransitionAuthority,
                "membership_set.ordered_authorities",
            ),
        )
        keys = tuple(
            (item.package_lineage_ref.encode(), item.disposition.encode())
            for item in items
        )
        if keys != tuple(sorted(keys)) or len(
            {item.package_lineage_ref for item in items}
        ) != len(items):
            raise WorkspaceRevisionPreparationContractError(
                "membership transitions must be uniquely ordered by lineage"
            )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "ordered_authorities": [item.to_wire() for item in items],
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "set_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body({"ordered_authorities": self.ordered_authorities}),
            "set_digest": self.set_digest,
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        root = require_exact_keys(
            value,
            frozenset({"codec_version", "schema", "ordered_authorities", "set_digest"}),
            "membership_set",
        )
        _constant_header(root, cls.SCHEMA, "membership_set")
        items = tuple(
            WorkspaceRevisionPackageMembershipTransitionAuthority.from_wire(item)
            for item in _wire_list(
                root["ordered_authorities"], "membership_set.ordered_authorities"
            )
        )
        return cls(
            ordered_authorities=items,
            set_digest=_digest_text(root["set_digest"], "membership_set.set_digest"),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionPredecessorAdmission(_PortableValue):
    disposition: str
    operation_authority_digest: str
    workspace_ref: str
    branch_ref: str
    observed_branch_head_ref: str | None
    observed_branch_head_digest: str | None
    revision_nonmembership_digest: str | None
    predecessor_workspace_revision_ref: str | None
    predecessor_workspace_revision_digest: str | None
    predecessor_state_digest: str | None
    predecessor_source_closure_digest: str | None
    admission_digest: str

    SCHEMA = WORKSPACE_REVISION_PREDECESSOR_ADMISSION
    DIGEST_FIELD = "admission_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, admission_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        disposition = _literal(
            values["disposition"], ("genesis", "revision"), "predecessor.disposition"
        )
        refs = ("observed_branch_head_ref", "predecessor_workspace_revision_ref")
        digests = (
            "observed_branch_head_digest",
            "revision_nonmembership_digest",
            "predecessor_workspace_revision_digest",
            "predecessor_state_digest",
            "predecessor_source_closure_digest",
        )
        optionals: dict[str, object] = {}
        for field in refs:
            item = values[field]
            optionals[field] = (
                None if item is None else _text(item, f"predecessor.{field}")
            )
        for field in digests:
            item = values[field]
            optionals[field] = (
                None if item is None else _digest_text(item, f"predecessor.{field}")
            )
        if disposition == "genesis":
            if optionals["revision_nonmembership_digest"] is None or any(
                optionals[field] is not None
                for field in (
                    *refs,
                    "observed_branch_head_digest",
                    "predecessor_workspace_revision_digest",
                    "predecessor_state_digest",
                    "predecessor_source_closure_digest",
                )
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "genesis predecessor nullability differs"
                )
        else:
            if (
                optionals["revision_nonmembership_digest"] is not None
                or any(
                    optionals[field] is None
                    for field in (
                        *refs,
                        "observed_branch_head_digest",
                        "predecessor_workspace_revision_digest",
                        "predecessor_state_digest",
                        "predecessor_source_closure_digest",
                    )
                )
                or optionals["observed_branch_head_ref"]
                != optionals["predecessor_workspace_revision_ref"]
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "revision predecessor nullability or head identity differs"
                )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "disposition": disposition,
            "operation_authority_digest": _digest_text(
                values["operation_authority_digest"],
                "predecessor.operation_authority_digest",
            ),
            "workspace_ref": _text(
                values["workspace_ref"], "predecessor.workspace_ref"
            ),
            "branch_ref": _text(values["branch_ref"], "predecessor.branch_ref"),
            **optionals,
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "admission_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "admission_digest"
        }
        return {**self._body(values), "admission_digest": self.admission_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "disposition",
            "operation_authority_digest",
            "workspace_ref",
            "branch_ref",
            "observed_branch_head_ref",
            "observed_branch_head_digest",
            "revision_nonmembership_digest",
            "predecessor_workspace_revision_ref",
            "predecessor_workspace_revision_digest",
            "predecessor_state_digest",
            "predecessor_source_closure_digest",
            "admission_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "predecessor")
        _constant_header(root, cls.SCHEMA, "predecessor")
        values = {
            field: root[field]
            for field in fields - {"codec_version", "schema", "admission_digest"}
        }
        return cls(
            **values,
            admission_digest=_digest_text(
                root["admission_digest"], "predecessor.admission_digest"
            ),
        )  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionSelectionScopeAdmission(_PortableValue):
    scope: str
    operation_authority_digest: str
    workspace_ref: str
    graph_digest: str
    ordered_selected_slots: tuple[WorkspaceRevisionPinSlot, ...]
    current_membership_catalog_root_digest: str
    complete_profile_proof_digest: str | None
    admission_digest: str

    SCHEMA = WORKSPACE_REVISION_SELECTION_SCOPE_ADMISSION
    DIGEST_FIELD = "admission_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, admission_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        scope = _literal(
            values["scope"],
            ("complete_workspace_profile", "partial_workspace_update"),
            "selection.scope",
        )
        slots = cast(
            tuple[WorkspaceRevisionPinSlot, ...],
            _exact_tuple(
                values["ordered_selected_slots"],
                WorkspaceRevisionPinSlot,
                "selection.ordered_selected_slots",
            ),
        )
        keys = tuple(item.ordering_key() for item in slots)
        if keys != tuple(sorted(keys)) or len(
            {item.slot_digest for item in slots}
        ) != len(slots):
            raise WorkspaceRevisionPreparationContractError(
                "selected slots must be uniquely ordered"
            )
        proof = values["complete_profile_proof_digest"]
        proof_value = (
            None
            if proof is None
            else _digest_text(proof, "selection.complete_profile_proof_digest")
        )
        if (scope == "complete_workspace_profile") != (proof_value is not None):
            raise WorkspaceRevisionPreparationContractError(
                "selection complete-profile proof nullability differs"
            )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "scope": scope,
            "operation_authority_digest": _digest_text(
                values["operation_authority_digest"],
                "selection.operation_authority_digest",
            ),
            "workspace_ref": _text(values["workspace_ref"], "selection.workspace_ref"),
            "graph_digest": _digest_text(
                values["graph_digest"], "selection.graph_digest"
            ),
            "ordered_selected_slots": [item.to_wire() for item in slots],
            "current_membership_catalog_root_digest": _digest_text(
                values["current_membership_catalog_root_digest"],
                "selection.current_membership_catalog_root_digest",
            ),
            "complete_profile_proof_digest": proof_value,
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "admission_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "admission_digest"
        }
        return {**self._body(values), "admission_digest": self.admission_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "scope",
            "operation_authority_digest",
            "workspace_ref",
            "graph_digest",
            "ordered_selected_slots",
            "current_membership_catalog_root_digest",
            "complete_profile_proof_digest",
            "admission_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "selection")
        _constant_header(root, cls.SCHEMA, "selection")
        slots = tuple(
            WorkspaceRevisionPinSlot.from_wire(item)
            for item in _wire_list(
                root["ordered_selected_slots"], "selection.ordered_selected_slots"
            )
        )
        return cls(
            scope=cast(str, root["scope"]),
            operation_authority_digest=cast(str, root["operation_authority_digest"]),
            workspace_ref=cast(str, root["workspace_ref"]),
            graph_digest=cast(str, root["graph_digest"]),
            ordered_selected_slots=slots,
            current_membership_catalog_root_digest=cast(
                str, root["current_membership_catalog_root_digest"]
            ),
            complete_profile_proof_digest=cast(
                str | None, root["complete_profile_proof_digest"]
            ),
            admission_digest=_digest_text(
                root["admission_digest"], "selection.admission_digest"
            ),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionSourcePackageEntry(_PortableValue):
    package_lineage_ref: str
    source_package_identity_digest: str
    current_package_ref: str
    source_after_state_authority_digest: str
    source_after_state_body_sha256: str
    entry_digest: str

    SCHEMA = WORKSPACE_REVISION_SOURCE_PACKAGE_ENTRY
    DIGEST_FIELD = "entry_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, entry_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "package_lineage_ref": _lineage(
                values["package_lineage_ref"], "source_entry.package_lineage_ref"
            ),
            "source_package_identity_digest": _digest_text(
                values["source_package_identity_digest"],
                "source_entry.source_package_identity_digest",
            ),
            "current_package_ref": _text(
                values["current_package_ref"], "source_entry.current_package_ref"
            ),
            "source_after_state_authority_digest": _digest_text(
                values["source_after_state_authority_digest"],
                "source_entry.source_after_state_authority_digest",
            ),
            "source_after_state_body_sha256": _digest_text(
                values["source_after_state_body_sha256"],
                "source_entry.source_after_state_body_sha256",
            ),
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "entry_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "entry_digest"
        }
        return {**self._body(values), "entry_digest": self.entry_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "package_lineage_ref",
            "source_package_identity_digest",
            "current_package_ref",
            "source_after_state_authority_digest",
            "source_after_state_body_sha256",
            "entry_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "source_entry")
        _constant_header(root, cls.SCHEMA, "source_entry")
        values = {
            field: root[field]
            for field in fields - {"codec_version", "schema", "entry_digest"}
        }
        return cls(
            **values,
            entry_digest=_digest_text(
                root["entry_digest"], "source_entry.entry_digest"
            ),
        )  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionSourceClosure(_PortableValue):
    workspace_ref: str
    ordered_packages: tuple[WorkspaceRevisionSourcePackageEntry, ...]
    closure_digest: str

    SCHEMA = WORKSPACE_REVISION_SOURCE_CLOSURE
    DIGEST_FIELD = "closure_digest"

    @classmethod
    def create(
        cls,
        *,
        workspace_ref: str,
        ordered_packages: tuple[WorkspaceRevisionSourcePackageEntry, ...],
    ) -> Self:
        body = cls._body(
            {"workspace_ref": workspace_ref, "ordered_packages": ordered_packages}
        )
        return cls(
            workspace_ref=workspace_ref,
            ordered_packages=ordered_packages,
            closure_digest=_body_digest(cls.SCHEMA, body),
        )

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        items = cast(
            tuple[WorkspaceRevisionSourcePackageEntry, ...],
            _exact_tuple(
                values["ordered_packages"],
                WorkspaceRevisionSourcePackageEntry,
                "source_closure.ordered_packages",
            ),
        )
        keys = tuple(item.package_lineage_ref.encode() for item in items)
        if keys != tuple(sorted(keys)) or len(set(keys)) != len(keys):
            raise WorkspaceRevisionPreparationContractError(
                "source packages must be uniquely ordered by lineage"
            )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "workspace_ref": _text(
                values["workspace_ref"], "source_closure.workspace_ref"
            ),
            "ordered_packages": [item.to_wire() for item in items],
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "closure_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(
                {
                    "workspace_ref": self.workspace_ref,
                    "ordered_packages": self.ordered_packages,
                }
            ),
            "closure_digest": self.closure_digest,
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        root = require_exact_keys(
            value,
            frozenset(
                {
                    "codec_version",
                    "schema",
                    "workspace_ref",
                    "ordered_packages",
                    "closure_digest",
                }
            ),
            "source_closure",
        )
        _constant_header(root, cls.SCHEMA, "source_closure")
        items = tuple(
            WorkspaceRevisionSourcePackageEntry.from_wire(item)
            for item in _wire_list(
                root["ordered_packages"], "source_closure.ordered_packages"
            )
        )
        return cls(
            workspace_ref=cast(str, root["workspace_ref"]),
            ordered_packages=items,
            closure_digest=_digest_text(
                root["closure_digest"], "source_closure.closure_digest"
            ),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionSourceClosureAdmission(_PortableValue):
    disposition: str
    operation_authority_digest: str
    workspace_ref: str
    predecessor_source_closure_digest: str | None
    selection_scope: str
    selection_scope_admission_digest: str
    package_membership_transition_set_digest: str
    source_closure_digest: str
    admission_digest: str

    SCHEMA = WORKSPACE_REVISION_SOURCE_CLOSURE_ADMISSION
    DIGEST_FIELD = "admission_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, admission_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        predecessor = values["predecessor_source_closure_digest"]
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "disposition": _literal(
                values["disposition"], ("admitted",), "source_admission.disposition"
            ),
            "operation_authority_digest": _digest_text(
                values["operation_authority_digest"],
                "source_admission.operation_authority_digest",
            ),
            "workspace_ref": _text(
                values["workspace_ref"], "source_admission.workspace_ref"
            ),
            "predecessor_source_closure_digest": None
            if predecessor is None
            else _digest_text(
                predecessor, "source_admission.predecessor_source_closure_digest"
            ),
            "selection_scope": _literal(
                values["selection_scope"],
                ("complete_workspace_profile", "partial_workspace_update"),
                "source_admission.selection_scope",
            ),
            "selection_scope_admission_digest": _digest_text(
                values["selection_scope_admission_digest"],
                "source_admission.selection_scope_admission_digest",
            ),
            "package_membership_transition_set_digest": _digest_text(
                values["package_membership_transition_set_digest"],
                "source_admission.package_membership_transition_set_digest",
            ),
            "source_closure_digest": _digest_text(
                values["source_closure_digest"],
                "source_admission.source_closure_digest",
            ),
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "admission_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "admission_digest"
        }
        return {**self._body(values), "admission_digest": self.admission_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "disposition",
            "operation_authority_digest",
            "workspace_ref",
            "predecessor_source_closure_digest",
            "selection_scope",
            "selection_scope_admission_digest",
            "package_membership_transition_set_digest",
            "source_closure_digest",
            "admission_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "source_admission")
        _constant_header(root, cls.SCHEMA, "source_admission")
        values = {
            field: root[field]
            for field in fields - {"codec_version", "schema", "admission_digest"}
        }
        return cls(
            **values,
            admission_digest=_digest_text(
                root["admission_digest"], "source_admission.admission_digest"
            ),
        )  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionState(_PortableValue):
    workspace_ref: str
    source_closure_digest: str
    ordered_package_pins: tuple[WorkspaceRevisionPreparedPackagePin, ...]
    state_digest: str

    SCHEMA = WORKSPACE_REVISION_STATE
    DIGEST_FIELD = "state_digest"

    @classmethod
    def create(
        cls,
        *,
        workspace_ref: str,
        source_closure_digest: str,
        ordered_package_pins: tuple[WorkspaceRevisionPreparedPackagePin, ...],
    ) -> Self:
        body = cls._body(
            {
                "workspace_ref": workspace_ref,
                "source_closure_digest": source_closure_digest,
                "ordered_package_pins": ordered_package_pins,
            }
        )
        return cls(
            workspace_ref=workspace_ref,
            source_closure_digest=source_closure_digest,
            ordered_package_pins=ordered_package_pins,
            state_digest=_body_digest(cls.SCHEMA, body),
        )

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        pins = cast(
            tuple[WorkspaceRevisionPreparedPackagePin, ...],
            _exact_tuple(
                values["ordered_package_pins"],
                WorkspaceRevisionPreparedPackagePin,
                "state.ordered_package_pins",
            ),
        )
        keys = tuple(pin.slot.ordering_key() for pin in pins)
        if keys != tuple(sorted(keys)) or len(
            {pin.slot.slot_digest for pin in pins}
        ) != len(pins):
            raise WorkspaceRevisionPreparationContractError(
                "state pins must be uniquely slot ordered"
            )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "workspace_ref": _text(values["workspace_ref"], "state.workspace_ref"),
            "source_closure_digest": _digest_text(
                values["source_closure_digest"], "state.source_closure_digest"
            ),
            "ordered_package_pins": [pin.to_wire() for pin in pins],
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "state_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(
                {
                    "workspace_ref": self.workspace_ref,
                    "source_closure_digest": self.source_closure_digest,
                    "ordered_package_pins": self.ordered_package_pins,
                }
            ),
            "state_digest": self.state_digest,
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        root = require_exact_keys(
            value,
            frozenset(
                {
                    "codec_version",
                    "schema",
                    "workspace_ref",
                    "source_closure_digest",
                    "ordered_package_pins",
                    "state_digest",
                }
            ),
            "state",
        )
        _constant_header(root, cls.SCHEMA, "state")
        pins = tuple(
            WorkspaceRevisionPreparedPackagePin.from_wire(item)
            for item in _wire_list(
                root["ordered_package_pins"], "state.ordered_package_pins"
            )
        )
        return cls(
            workspace_ref=cast(str, root["workspace_ref"]),
            source_closure_digest=cast(str, root["source_closure_digest"]),
            ordered_package_pins=pins,
            state_digest=_digest_text(root["state_digest"], "state.state_digest"),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionCandidatePredecessor:
    kind: str
    revision_nonmembership_digest: str | None
    workspace_revision_ref: str | None
    workspace_revision_digest: str | None
    state_digest: str | None

    @classmethod
    def genesis(cls, revision_nonmembership_digest: str) -> Self:
        return cls("genesis", revision_nonmembership_digest, None, None, None)

    @classmethod
    def revision(
        cls,
        *,
        workspace_revision_ref: str,
        workspace_revision_digest: str,
        state_digest: str,
    ) -> Self:
        return cls(
            "revision",
            None,
            workspace_revision_ref,
            workspace_revision_digest,
            state_digest,
        )

    def __post_init__(self) -> None:
        _literal(self.kind, ("genesis", "revision"), "candidate.predecessor.kind")
        if self.kind == "genesis":
            if self.revision_nonmembership_digest is None or any(
                item is not None
                for item in (
                    self.workspace_revision_ref,
                    self.workspace_revision_digest,
                    self.state_digest,
                )
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "candidate genesis predecessor differs"
                )
            _digest_text(
                self.revision_nonmembership_digest,
                "candidate.predecessor.revision_nonmembership_digest",
            )
        else:
            if self.revision_nonmembership_digest is not None or any(
                item is None
                for item in (
                    self.workspace_revision_ref,
                    self.workspace_revision_digest,
                    self.state_digest,
                )
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "candidate revision predecessor differs"
                )
            _text(
                self.workspace_revision_ref,
                "candidate.predecessor.workspace_revision_ref",
            )
            _digest_text(
                self.workspace_revision_digest,
                "candidate.predecessor.workspace_revision_digest",
            )
            _digest_text(self.state_digest, "candidate.predecessor.state_digest")
        _record_issued(
            self, canonical_revision_preparation_json_bytes(self._wire_unchecked())
        )

    def _wire_unchecked(self) -> dict[str, object]:
        if self.kind == "genesis":
            return {
                "kind": "genesis",
                "revision_nonmembership_digest": self.revision_nonmembership_digest,
            }
        return {
            "kind": "revision",
            "workspace_revision_ref": self.workspace_revision_ref,
            "workspace_revision_digest": self.workspace_revision_digest,
            "state_digest": self.state_digest,
        }

    def to_wire(self) -> dict[str, object]:
        wire = self._wire_unchecked()
        _require_issued(self, canonical_revision_preparation_json_bytes(wire))
        return cast(dict[str, object], _copy_wire(wire))

    def canonical_bytes(self) -> bytes:
        return canonical_revision_preparation_json_bytes(self.to_wire())

    @classmethod
    def from_wire(cls, value: object) -> Self:
        if type(value) is not dict:
            raise TypeError("candidate.predecessor must be exact dict")
        root = cast(dict[object, object], value)
        if any(type(key) is not str for key in root):
            raise TypeError("candidate.predecessor keys must be exact str")
        kind = root.get("kind")
        if kind == "genesis":
            admitted = require_exact_keys(
                value,
                frozenset({"kind", "revision_nonmembership_digest"}),
                "candidate.predecessor",
            )
            return cls.genesis(
                _digest_text(
                    admitted["revision_nonmembership_digest"],
                    "candidate.predecessor.revision_nonmembership_digest",
                )
            )
        if kind == "revision":
            admitted = require_exact_keys(
                value,
                frozenset(
                    {
                        "kind",
                        "workspace_revision_ref",
                        "workspace_revision_digest",
                        "state_digest",
                    }
                ),
                "candidate.predecessor",
            )
            return cls.revision(
                workspace_revision_ref=_text(
                    admitted["workspace_revision_ref"],
                    "candidate.predecessor.workspace_revision_ref",
                ),
                workspace_revision_digest=_digest_text(
                    admitted["workspace_revision_digest"],
                    "candidate.predecessor.workspace_revision_digest",
                ),
                state_digest=_digest_text(
                    admitted["state_digest"], "candidate.predecessor.state_digest"
                ),
            )
        raise WorkspaceRevisionPreparationContractError(
            "candidate predecessor kind unsupported"
        )

    @classmethod
    def from_canonical_bytes(cls, value: bytes) -> Self:
        result = cls.from_wire(decode_revision_preparation_json_object(value))
        if result.canonical_bytes() != value:
            raise WorkspaceRevisionPreparationContractError(
                "candidate predecessor canonical bytes differ"
            )
        return result


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionCandidate(_PortableValue):
    state: WorkspaceRevisionState
    predecessor: WorkspaceRevisionCandidatePredecessor
    candidate_digest: str

    SCHEMA = WORKSPACE_REVISION_CANDIDATE
    DIGEST_FIELD = "candidate_digest"

    @classmethod
    def create(
        cls,
        *,
        state: WorkspaceRevisionState,
        predecessor: WorkspaceRevisionCandidatePredecessor,
    ) -> Self:
        body = cls._body({"state": state, "predecessor": predecessor})
        return cls(
            state=state,
            predecessor=predecessor,
            candidate_digest=_body_digest(cls.SCHEMA, body),
        )

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        state = values["state"]
        predecessor = values["predecessor"]
        if type(state) is not WorkspaceRevisionState:
            raise TypeError("candidate.state must be exact WorkspaceRevisionState")
        if type(predecessor) is not WorkspaceRevisionCandidatePredecessor:
            raise TypeError("candidate.predecessor must be exact predecessor")
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "state": state.to_wire(),
            "predecessor": predecessor.to_wire(),
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "candidate_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body({"state": self.state, "predecessor": self.predecessor}),
            "candidate_digest": self.candidate_digest,
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        root = require_exact_keys(
            value,
            frozenset(
                {"codec_version", "schema", "state", "predecessor", "candidate_digest"}
            ),
            "candidate",
        )
        _constant_header(root, cls.SCHEMA, "candidate")
        return cls(
            state=WorkspaceRevisionState.from_wire(root["state"]),
            predecessor=WorkspaceRevisionCandidatePredecessor.from_wire(
                root["predecessor"]
            ),
            candidate_digest=_digest_text(
                root["candidate_digest"], "candidate.candidate_digest"
            ),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceMaterializationGraphExecutionAdmission(_PortableValue):
    disposition: str
    operation_authority_digest: str
    execution_provenance_lifecycle: str
    plan_body_sha256: str
    plan_body_size_bytes: int
    graph_result_body_sha256: str
    graph_result_body_size_bytes: int
    graph_result_digest: str
    admission_digest: str

    SCHEMA = WORKSPACE_MATERIALIZATION_GRAPH_EXECUTION_ADMISSION
    DIGEST_FIELD = "admission_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, admission_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "disposition": _literal(
                values["disposition"], ("admitted",), "graph_admission.disposition"
            ),
            "operation_authority_digest": _digest_text(
                values["operation_authority_digest"],
                "graph_admission.operation_authority_digest",
            ),
            "execution_provenance_lifecycle": _literal(
                values["execution_provenance_lifecycle"],
                ("same_process_execution", "reexecuted_after_process_loss"),
                "graph_admission.execution_provenance_lifecycle",
            ),
            "plan_body_sha256": _digest_text(
                values["plan_body_sha256"], "graph_admission.plan_body_sha256"
            ),
            "plan_body_size_bytes": _nonnegative(
                values["plan_body_size_bytes"], "graph_admission.plan_body_size_bytes"
            ),
            "graph_result_body_sha256": _digest_text(
                values["graph_result_body_sha256"],
                "graph_admission.graph_result_body_sha256",
            ),
            "graph_result_body_size_bytes": _nonnegative(
                values["graph_result_body_size_bytes"],
                "graph_admission.graph_result_body_size_bytes",
            ),
            "graph_result_digest": _digest_text(
                values["graph_result_digest"], "graph_admission.graph_result_digest"
            ),
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "admission_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "admission_digest"
        }
        return {**self._body(values), "admission_digest": self.admission_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = {
            "codec_version",
            "schema",
            "disposition",
            "operation_authority_digest",
            "execution_provenance_lifecycle",
            "plan_body_sha256",
            "plan_body_size_bytes",
            "graph_result_body_sha256",
            "graph_result_body_size_bytes",
            "graph_result_digest",
            "admission_digest",
        }
        root = require_exact_keys(value, frozenset(fields), "graph_admission")
        _constant_header(root, cls.SCHEMA, "graph_admission")
        values = {
            field: root[field]
            for field in fields - {"codec_version", "schema", "admission_digest"}
        }
        return cls(
            **values,
            admission_digest=_digest_text(
                root["admission_digest"], "graph_admission.admission_digest"
            ),
        )  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRevisionPreparationEvidence(_PortableValue):
    outcome: str
    operation_authority_digest: str
    workspace_ref: str
    branch_ref: str
    predecessor_admission_digest: str | None
    source_closure_admission_digest: str | None
    selection_scope: str
    selection_scope_admission_digest: str | None
    graph_execution_admission_digest: str | None
    execution_provenance_lifecycle: str | None
    plan_body_sha256: str
    plan_body_size_bytes: int
    graph_result_body_sha256: str
    graph_result_body_size_bytes: int
    graph_result_digest: str
    package_membership_transition_set_digest: str
    derived_state_digest: str | None
    candidate_digest: str | None
    refusal_code: str | None
    provider_execution_count: int
    external_read_count: int
    external_write_count: int
    ontology_call_count: int
    meta_oig_call_count: int
    evidence_digest: str

    SCHEMA = WORKSPACE_REVISION_PREPARATION_EVIDENCE
    DIGEST_FIELD = "evidence_digest"

    @classmethod
    def create(cls, **values: object) -> Self:
        body = cls._body(values)
        return cls(**values, evidence_digest=_body_digest(cls.SCHEMA, body))  # type: ignore[arg-type]

    @classmethod
    def _body(cls, values: dict[str, object]) -> dict[str, object]:
        outcome = _literal(
            values["outcome"],
            ("candidate_prepared", "revision_unchanged", "preparation_refused"),
            "evidence.outcome",
        )
        selection_scope = _literal(
            values["selection_scope"],
            ("complete_workspace_profile", "partial_workspace_update"),
            "evidence.selection_scope",
        )
        optional_digests: dict[str, object] = {}
        for field in (
            "predecessor_admission_digest",
            "source_closure_admission_digest",
            "selection_scope_admission_digest",
            "graph_execution_admission_digest",
            "derived_state_digest",
            "candidate_digest",
        ):
            item = values[field]
            optional_digests[field] = (
                None if item is None else _digest_text(item, f"evidence.{field}")
            )
        lifecycle = values["execution_provenance_lifecycle"]
        lifecycle_value = (
            None
            if lifecycle is None
            else _literal(
                lifecycle,
                ("same_process_execution", "reexecuted_after_process_loss"),
                "evidence.execution_provenance_lifecycle",
            )
        )
        refusal = values["refusal_code"]
        refusal_value = (
            None
            if refusal is None
            else _literal(
                refusal,
                WORKSPACE_REVISION_PREPARATION_REFUSAL_CODES,
                "evidence.refusal_code",
            )
        )
        if outcome == "candidate_prepared":
            if (
                optional_digests["derived_state_digest"] is None
                or optional_digests["candidate_digest"] is None
                or refusal_value is not None
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "candidate-prepared evidence nullability differs"
                )
        elif outcome == "revision_unchanged":
            if (
                optional_digests["derived_state_digest"] is None
                or optional_digests["candidate_digest"] is not None
                or refusal_value is not None
            ):
                raise WorkspaceRevisionPreparationContractError(
                    "unchanged evidence nullability differs"
                )
        elif (
            optional_digests["derived_state_digest"] is not None
            or optional_digests["candidate_digest"] is not None
            or refusal_value is None
        ):
            raise WorkspaceRevisionPreparationContractError(
                "refused evidence nullability differs"
            )
        if outcome != "preparation_refused" and (
            any(
                optional_digests[field] is None
                for field in (
                    "predecessor_admission_digest",
                    "source_closure_admission_digest",
                    "selection_scope_admission_digest",
                    "graph_execution_admission_digest",
                )
            )
            or lifecycle_value is None
        ):
            raise WorkspaceRevisionPreparationContractError(
                "positive evidence requires complete admissions"
            )
        if outcome == "preparation_refused":
            assert refusal_value is not None
            refusal_index = WORKSPACE_REVISION_PREPARATION_REFUSAL_CODES.index(
                refusal_value
            )
            expected_presence = (
                refusal_index >= 2,
                refusal_index >= 3,
                refusal_index >= 4,
                refusal_index >= 5,
            )
            actual_presence = tuple(
                optional_digests[field] is not None
                for field in (
                    "predecessor_admission_digest",
                    "source_closure_admission_digest",
                    "selection_scope_admission_digest",
                    "graph_execution_admission_digest",
                )
            )
            if actual_presence != expected_presence:
                raise WorkspaceRevisionPreparationContractError(
                    "refused evidence retained an invalid admission prefix"
                )
            if (lifecycle_value is not None) != expected_presence[-1]:
                raise WorkspaceRevisionPreparationContractError(
                    "refused evidence provenance lifecycle differs"
                )
        counters = {}
        for field in (
            "provider_execution_count",
            "external_read_count",
            "external_write_count",
            "ontology_call_count",
            "meta_oig_call_count",
        ):
            counters[field] = _nonnegative(values[field], f"evidence.{field}")
            if counters[field] != 0:
                raise WorkspaceRevisionPreparationContractError(
                    "preparation counters must be zero"
                )
        return {
            "codec_version": 1,
            "schema": cls.SCHEMA,
            "outcome": outcome,
            "operation_authority_digest": _digest_text(
                values["operation_authority_digest"],
                "evidence.operation_authority_digest",
            ),
            "workspace_ref": _text(values["workspace_ref"], "evidence.workspace_ref"),
            "branch_ref": _text(values["branch_ref"], "evidence.branch_ref"),
            **optional_digests,
            "selection_scope": selection_scope,
            "execution_provenance_lifecycle": lifecycle_value,
            "plan_body_sha256": _digest_text(
                values["plan_body_sha256"], "evidence.plan_body_sha256"
            ),
            "plan_body_size_bytes": _nonnegative(
                values["plan_body_size_bytes"], "evidence.plan_body_size_bytes"
            ),
            "graph_result_body_sha256": _digest_text(
                values["graph_result_body_sha256"], "evidence.graph_result_body_sha256"
            ),
            "graph_result_body_size_bytes": _nonnegative(
                values["graph_result_body_size_bytes"],
                "evidence.graph_result_body_size_bytes",
            ),
            "graph_result_digest": _digest_text(
                values["graph_result_digest"], "evidence.graph_result_digest"
            ),
            "package_membership_transition_set_digest": _digest_text(
                values["package_membership_transition_set_digest"],
                "evidence.package_membership_transition_set_digest",
            ),
            "refusal_code": refusal_value,
            **counters,
        }

    def __post_init__(self) -> None:
        _validate_digest(self, "evidence_digest", self.SCHEMA)
        self._seal()

    def _wire_unchecked(self) -> dict[str, object]:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "evidence_digest"
        }
        return {**self._body(values), "evidence_digest": self.evidence_digest}

    @classmethod
    def from_wire(cls, value: object) -> Self:
        fields = set(cls.__dataclass_fields__) | {"codec_version", "schema"}
        root = require_exact_keys(value, frozenset(fields), "evidence")
        _constant_header(root, cls.SCHEMA, "evidence")
        values = {
            field: root[field]
            for field in cls.__dataclass_fields__
            if field != "evidence_digest"
        }
        return cls(
            **values,
            evidence_digest=_digest_text(
                root["evidence_digest"], "evidence.evidence_digest"
            ),
        )  # type: ignore[arg-type]


__all__ = [
    "WORKSPACE_MATERIALIZATION_GRAPH_EXECUTION_ADMISSION",
    "WORKSPACE_REVISION_CANDIDATE",
    "WORKSPACE_REVISION_PACKAGE_MEMBERSHIP_TRANSITION",
    "WORKSPACE_REVISION_PACKAGE_MEMBERSHIP_TRANSITION_SET",
    "WORKSPACE_REVISION_PIN_SLOT",
    "WORKSPACE_REVISION_PREDECESSOR_ADMISSION",
    "WORKSPACE_REVISION_PREPARATION_EVIDENCE",
    "WORKSPACE_REVISION_PREPARATION_REFUSAL_CODES",
    "WORKSPACE_REVISION_PREPARED_PACKAGE_PIN",
    "WORKSPACE_REVISION_SELECTION_SCOPE_ADMISSION",
    "WORKSPACE_REVISION_SOURCE_CLOSURE",
    "WORKSPACE_REVISION_SOURCE_CLOSURE_ADMISSION",
    "WORKSPACE_REVISION_SOURCE_PACKAGE_ENTRY",
    "WORKSPACE_REVISION_STATE",
    "WorkspaceMaterializationGraphExecutionAdmission",
    "WorkspaceRevisionCandidate",
    "WorkspaceRevisionCandidatePredecessor",
    "WorkspaceRevisionPackageMembershipTransitionAuthority",
    "WorkspaceRevisionPackageMembershipTransitionSet",
    "WorkspaceRevisionPinSlot",
    "WorkspaceRevisionPredecessorAdmission",
    "WorkspaceRevisionPreparationEvidence",
    "WorkspaceRevisionPreparedPackagePin",
    "WorkspaceRevisionSelectionScopeAdmission",
    "WorkspaceRevisionSourceClosure",
    "WorkspaceRevisionSourceClosureAdmission",
    "WorkspaceRevisionSourcePackageEntry",
    "WorkspaceRevisionState",
]
