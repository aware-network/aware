"""Opt-in original-owner rich reading; never a World/View admission receipt."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from typing import ClassVar

from .development_read_projection import IssueDevelopmentReadProjectionV2
from .operation import IssueReadProjectionResolveOutcome

ISSUE_READING_OPERATION_REF = "issue_sdk.resolve_issue_reading"
ISSUE_READING_PROVIDER_OPERATION_REF = "workflow.issue.reading.resolve"
ISSUE_READING_EXPOSURE_PROFILE = "issue.reading.local-private.v1"
SOURCE_LIMIT = 262_144
RESULT_LIMIT = 4_194_304
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ISSUE = re.compile(r"fb/\d{4}-\d{2}-\d{2}/[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def token(value: object, name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"invalid {name}")
    value.encode("utf-8")
    return value


def digest(value: object, name: str) -> str:
    text = token(value, name)
    if not _DIGEST.fullmatch(text):
        raise ValueError(f"invalid {name} digest")
    return text


def exact(value: object, keys: set[str], name: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"invalid {name} fields")
    return value


def canonical_bytes(value: object, *, limit: int = RESULT_LIMIT) -> bytes:
    """One bounded carriage encoding, not source normalization."""
    nodes = 0

    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        if nodes > 8192 or depth > 32:
            raise ValueError("reading structure limit")
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ValueError("reading object keys")
            for key, child in item.items():
                visit(key, depth + 1)
                visit(child, depth + 1)
        elif type(item) is list:
            if len(item) > 4096:
                raise ValueError("reading array limit")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            if len(item.encode("utf-8")) > SOURCE_LIMIT:
                raise ValueError("reading string limit")
        elif item is not None and type(item) not in (bool, int):
            raise ValueError("non-canonical reading value")

    visit(value, 0)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > limit:
        raise ValueError("reading result limit")
    return encoded


def decode_json(body: bytes, *, limit: int = RESULT_LIMIT) -> dict:
    if type(body) is not bytes or len(body) > limit:
        raise ValueError("reading encoded limit")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate reading key")
            result[key] = value
        return result

    value = json.loads(body.decode("utf-8"), object_pairs_hook=unique)
    canonical_bytes(value, limit=limit)
    if type(value) is not dict:
        raise ValueError("reading object required")
    return value


@dataclass(frozen=True, slots=True)
class IssueReadingProviderBinding:
    """Selected by installation, independently of request or payload."""

    provider_ref: str
    distribution: str
    version: str
    installation_ref: str
    generation_ref: str
    repository_ref: str
    profile_ref: str
    manifest_digest: str
    exposure_profile_ref: str

    def __post_init__(self):
        for field in fields(self):
            token(getattr(self, field.name), field.name)
        digest(self.manifest_digest, "manifest")
        if self.exposure_profile_ref != ISSUE_READING_EXPOSURE_PROFILE:
            raise ValueError("unsupported rich exposure")

    def to_wire(self) -> dict:
        self.__post_init__()
        return asdict(self)

    @classmethod
    def from_wire(cls, value):
        return cls(**exact(value, {field.name for field in fields(cls)}, "binding"))


@dataclass(frozen=True, slots=True)
class IssueReadingResolveRequest:
    request_ref: str
    issue_ref: str
    binding: IssueReadingProviderBinding
    contract: ClassVar[str] = "aware.issue.rich-reading-request.v1"

    def __post_init__(self):
        token(self.request_ref, "request")
        if not _ISSUE.fullmatch(token(self.issue_ref, "Issue")):
            raise ValueError("canonical Issue identity required")
        if type(self.binding) is not IssueReadingProviderBinding:
            raise TypeError("installed reading binding required")
        self.binding.__post_init__()

    def to_wire(self):
        self.__post_init__()
        return {
            "contract": self.contract,
            "request_ref": self.request_ref,
            "issue_ref": self.issue_ref,
            "binding": self.binding.to_wire(),
        }

    @classmethod
    def from_wire(cls, value):
        row = exact(
            value, {"contract", "request_ref", "issue_ref", "binding"}, "request"
        )
        if row["contract"] != cls.contract:
            raise ValueError("unsupported reading request")
        return cls(
            row["request_ref"],
            row["issue_ref"],
            IssueReadingProviderBinding.from_wire(row["binding"]),
        )


@dataclass(frozen=True, slots=True)
class IssueReadingResolveResult:
    request_ref: str
    issue_ref: str
    outcome: IssueReadProjectionResolveOutcome
    binding: IssueReadingProviderBinding
    projection: IssueDevelopmentReadProjectionV2 | None = None
    observation_ref: str | None = None
    horizon_ref: str | None = None
    diagnostics: tuple[str, ...] = ()
    contract: ClassVar[str] = "aware.issue.rich-reading-result.v1"

    def __post_init__(self):
        IssueReadingResolveRequest(self.request_ref, self.issue_ref, self.binding)
        if type(self.outcome) is not IssueReadProjectionResolveOutcome:
            raise TypeError("typed reading outcome required")
        if type(self.diagnostics) is not tuple:
            raise TypeError("immutable diagnostics required")
        for message in self.diagnostics:
            token(message, "diagnostic")
        if self.outcome is not IssueReadProjectionResolveOutcome.FOUND:
            if any(
                value is not None
                for value in (self.projection, self.observation_ref, self.horizon_ref)
            ):
                raise ValueError("non-success cannot carry source or projection")
            return
        if type(self.projection) is not IssueDevelopmentReadProjectionV2:
            raise TypeError("original rich projection required")
        token(self.observation_ref, "owner observation")
        token(self.horizon_ref, "completed snapshot horizon")
        projection = self.projection
        source = projection.source
        encoded = source.raw_markdown.encode("utf-8")
        if len(encoded) > SOURCE_LIMIT:
            raise ValueError("rich source limit")
        expected = "sha256:" + hashlib.sha256(encoded).hexdigest()
        if (
            source.digest != expected
            or projection.projection_revision != expected
            or projection.identity.issue_ref != self.issue_ref
            or source.observation_time_authority != "source_observed"
        ):
            raise ValueError("rich source/Issue correspondence mismatch")
        if (
            source.path.startswith("/")
            or "\\" in source.path
            or any(part in ("", ".", "..") for part in source.path.split("/"))
        ):
            raise ValueError("canonical source path required")
        instant = datetime.fromisoformat(source.observed_at)
        if instant.tzinfo is None:
            raise ValueError("owner observation requires timezone")
        canonical_bytes(projection.model_dump(mode="json"))

    def require_request(self, request: IssueReadingResolveRequest):
        self.__post_init__()
        if (
            self.request_ref != request.request_ref
            or self.issue_ref != request.issue_ref
            or self.binding != request.binding
        ):
            raise ValueError("rich request/result correspondence mismatch")
        return self

    def to_wire(self):
        self.__post_init__()
        return {
            "contract": self.contract,
            "request_ref": self.request_ref,
            "issue_ref": self.issue_ref,
            "outcome": self.outcome.value,
            "binding": self.binding.to_wire(),
            "projection": None
            if self.projection is None
            else self.projection.model_dump(mode="json"),
            "observation_ref": self.observation_ref,
            "horizon_ref": self.horizon_ref,
            "diagnostics": list(self.diagnostics),
        }

    @classmethod
    def from_wire(cls, value):
        row = exact(
            value,
            {
                "contract",
                "request_ref",
                "issue_ref",
                "outcome",
                "binding",
                "projection",
                "observation_ref",
                "horizon_ref",
                "diagnostics",
            },
            "result",
        )
        if row["contract"] != cls.contract or type(row["diagnostics"]) is not list:
            raise ValueError("invalid rich result")
        canonical_bytes(row)
        projection = None
        if row["projection"] is not None:
            # JSON-mode strict validation admits wire arrays, not Python coercion.
            projection = IssueDevelopmentReadProjectionV2.model_validate_json(
                canonical_bytes(row["projection"]), strict=True
            )
            if projection.model_dump(mode="json") != row["projection"]:
                raise ValueError("missing/defaulted projection fields")
        return cls(
            row["request_ref"],
            row["issue_ref"],
            IssueReadProjectionResolveOutcome(row["outcome"]),
            IssueReadingProviderBinding.from_wire(row["binding"]),
            projection,
            row["observation_ref"],
            row["horizon_ref"],
            tuple(row["diagnostics"]),
        )


def invoke_reading(provider: object, request: IssueReadingResolveRequest):
    if type(request) is not IssueReadingResolveRequest:
        raise TypeError("rich request required")
    request.__post_init__()
    method = getattr(provider, "resolve_reading", None)
    if not callable(method):
        raise TypeError("rich_reading_unsupported")
    result = method(request)
    if type(result) is not IssueReadingResolveResult:
        raise TypeError("original rich result required")
    return result.require_request(request)
