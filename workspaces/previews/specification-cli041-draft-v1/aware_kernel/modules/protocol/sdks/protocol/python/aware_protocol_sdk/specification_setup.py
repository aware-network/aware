"""Neutral setup values and provider port. Values never grant source authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import PurePosixPath
from typing import Protocol

from aware_protocol_runtime import ProtocolContractError

PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF = "protocol_sdk.setup_specification"
PROTOCOL_SETUP_SPECIFICATION_PROVIDER_OPERATION_REF = "protocol.specification.setup"


def _text(value: object) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(ord(c) < 32 or ord(c) == 127 for c in value)
    ):
        raise ProtocolContractError("Setup coordinates must be exact trimmed text")
    return value


def _digest(value: object) -> str:
    text = _text(value)
    if (
        not text.startswith("sha256:")
        or len(text) != 71
        or any(c not in "0123456789abcdef" for c in text[7:])
    ):
        raise ProtocolContractError("Setup requires exact byte SHA-256 references")
    return text


@dataclass(frozen=True, slots=True)
class ProtocolSpecificationSetupRequest:
    repository_root: str
    manifest_path: str
    expected_manifest_sha256: str
    issue_ref: str
    expected_issue_sha256: str
    specification_root: str
    directory_paths: tuple[str, ...]
    client_intent_id: str
    dry_run: bool = True

    def __post_init__(self) -> None:
        for value in (
            self.repository_root,
            self.manifest_path,
            self.issue_ref,
            self.specification_root,
            self.client_intent_id,
        ):
            _text(value)
        _digest(self.expected_manifest_sha256)
        _digest(self.expected_issue_sha256)
        if type(self.dry_run) is not bool:
            raise ProtocolContractError("dry_run must be exact bool")
        if type(self.directory_paths) is not tuple or len(self.directory_paths) > 64:
            raise ProtocolContractError("Directories require a bounded ordered tuple")
        for value in (self.specification_root, *self.directory_paths):
            path = PurePosixPath(_text(value))
            if (
                path.is_absolute()
                or ".." in path.parts
                or str(path) != value
                or value == "."
                or "\\" in value
            ):
                raise ProtocolContractError(
                    "Setup roots must be canonical relative paths"
                )
        if len(set(self.directory_paths)) != len(self.directory_paths):
            raise ProtocolContractError("Setup directory paths must be unique")


@dataclass(frozen=True, slots=True)
class ProtocolSpecificationSetupEffect:
    path: str
    kind: str
    state: str
    durability_confirmed: bool
    mode: int | None
    before_digest: str | None
    after_digest: str | None
    after_identity: tuple[int, int] | None

    def __post_init__(self) -> None:
        _text(self.path)
        if self.kind not in {"directory", "manifest"} or self.state not in {
            "none",
            "applied",
            "unknown",
        }:
            raise ProtocolContractError("Unsupported setup effect")
        if type(self.durability_confirmed) is not bool:
            raise ProtocolContractError("Durability must be exact bool")
        if self.durability_confirmed and self.state != "applied":
            raise ProtocolContractError("Only applied effects can confirm durability")
        for digest in (self.before_digest, self.after_digest):
            if digest is not None:
                _digest(digest)
        if self.mode is not None and (
            type(self.mode) is not int or not 0 <= self.mode <= 0o7777
        ):
            raise ProtocolContractError("Invalid effect mode")
        if self.after_identity is not None and (
            type(self.after_identity) is not tuple
            or len(self.after_identity) != 2
            or any(type(x) is not int or x < 0 for x in self.after_identity)
        ):
            raise ProtocolContractError("Invalid effect identity")


class ProtocolSpecificationSetupError(RuntimeError):
    def __init__(
        self,
        code: str,
        effects: tuple[ProtocolSpecificationSetupEffect, ...] = (),
        residual_scratch_paths: tuple[str, ...] = (),
        *,
        effect_unknown: bool = False,
    ):
        super().__init__(code)
        self.code = code
        self.effects = tuple(effects)
        self.residual_scratch_paths = tuple(residual_scratch_paths)
        self.effect_unknown = effect_unknown

    @property
    def effect(self) -> str:
        if (
            self.effect_unknown
            or self.residual_scratch_paths
            or any(e.state == "unknown" for e in self.effects)
        ):
            return "unknown"
        return "applied" if any(e.state == "applied" for e in self.effects) else "none"


@dataclass(frozen=True, slots=True)
class ProtocolSpecificationSetupResult:
    status: str
    manifest_preimage_sha256: str
    manifest_postimage_sha256: str
    specification_root: str
    ordered_effect_paths: tuple[str, ...]
    effects: tuple[ProtocolSpecificationSetupEffect, ...] = ()
    execution_ref: str | None = None
    authority_grade: str | None = None
    operation_ref: str = PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF
    confinement_profile: str = "descriptor_walk_v1"

    def __post_init__(self) -> None:
        if (
            self.status not in {"planned", "completed"}
            or self.operation_ref != PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF
        ):
            raise ProtocolContractError("Unsupported setup result")
        _digest(self.manifest_preimage_sha256)
        _digest(self.manifest_postimage_sha256)
        _text(self.specification_root)
        if type(self.ordered_effect_paths) is not tuple or any(
            type(p) is not str or not p for p in self.ordered_effect_paths
        ):
            raise ProtocolContractError("Result paths must be an exact tuple")
        if type(self.effects) is not tuple or any(
            type(e) is not ProtocolSpecificationSetupEffect for e in self.effects
        ):
            raise ProtocolContractError("Result effects must be exact neutral values")
        for effect in self.effects:
            effect.__post_init__()
        if self.confinement_profile != "descriptor_walk_v1":
            raise ProtocolContractError("Unsupported confinement grade")
        if self.status == "planned":
            if (
                self.effects
                or self.execution_ref is not None
                or self.authority_grade is not None
            ):
                raise ProtocolContractError("Preview cannot claim consumption evidence")
        elif (
            self.execution_ref is None
            or self.authority_grade != "filesystem_harness_observed_v1"
            or tuple(e.path for e in self.effects) != self.ordered_effect_paths
            or any(e.state == "unknown" for e in self.effects)
        ):
            raise ProtocolContractError(
                "Completed setup requires actual consumption evidence"
            )
        if self.execution_ref is not None:
            _text(self.execution_ref)

    @property
    def effect(self) -> str:
        return "applied" if any(e.state == "applied" for e in self.effects) else "none"

    def to_wire(self) -> dict[str, object]:
        return {**asdict(self), "effect": self.effect}


class ProtocolSpecificationSetupProvider(Protocol):
    def setup_specification(
        self, request: ProtocolSpecificationSetupRequest
    ) -> ProtocolSpecificationSetupResult: ...


@dataclass(frozen=True)
class ProtocolSpecificationSetupClient:
    provider: ProtocolSpecificationSetupProvider

    def setup_specification(
        self, request: ProtocolSpecificationSetupRequest
    ) -> ProtocolSpecificationSetupResult:
        if type(request) is not ProtocolSpecificationSetupRequest:
            raise ProtocolContractError("Setup requires the exact request contract")
        result = self.provider.setup_specification(request)
        try:
            if type(result) is not ProtocolSpecificationSetupResult:
                raise ProtocolContractError("Setup provider returned an invalid result")
            result = replace(result)
            if (
                result.manifest_preimage_sha256 != request.expected_manifest_sha256
                or result.specification_root != request.specification_root
                or result.status != ("planned" if request.dry_run else "completed")
            ):
                raise ProtocolContractError("Setup result does not match its request")
        except (ProtocolContractError, TypeError, ValueError, AttributeError) as error:
            # The provider was invoked: malformed transport cannot prove no effects.
            raise ProtocolSpecificationSetupError(
                "setup_provider_result_invalid", effect_unknown=True
            ) from error
        return result
