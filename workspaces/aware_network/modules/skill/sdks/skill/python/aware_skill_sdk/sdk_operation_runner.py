from __future__ import annotations

from collections.abc import Awaitable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import importlib
import json
from typing import Protocol, cast

from aware_skill_sdk.client import SkillSdkError


SDK_OPERATION_CATALOG_CONTRACT = "aware.sdk_operation_catalog.v0"


class _SdkOperationDescriptor(Protocol):
    operation_ref: str
    sdk_name: str
    operation_name: str
    effect: str
    stability: str
    handler_ref: str | None
    endpoint_refs: Sequence[str]
    requires_confirmation: bool


class _SdkOperationCatalog(Protocol):
    sdk_name: str
    package_name: str
    version_number: int | None
    provider_ref: str
    operations: Sequence[_SdkOperationDescriptor]


class _SdkOperationCatalogIndex(Protocol):
    catalogs: Sequence[_SdkOperationCatalog]

    def resolve(self, operation_ref: str) -> _SdkOperationDescriptor: ...


class _SdkOperationCatalogRuntime(Protocol):
    SDK_OPERATION_CATALOG_CONTRACT: str

    def load_sdk_operation_catalog_index(
        self,
        *,
        extra_provider_refs: Iterable[str] = (),
        include_builtin_providers: bool = True,
    ) -> _SdkOperationCatalogIndex: ...

    def invoke_sdk_operation(
        self,
        *,
        operation: _SdkOperationDescriptor,
        request_payload: Mapping[str, object] | None = None,
        context: Mapping[str, object] | None = None,
        timeout_s: float | None = None,
        allow_mutation: bool = False,
    ) -> Awaitable[object]: ...


@dataclass(frozen=True, slots=True)
class SkillSdkOperationTarget:
    """Declared SDK package/catalog target for one Skill SDK operation run."""

    operation_ref: str
    sdk_package_name: str | None = None
    sdk_name: str | None = None
    sdk_package_revision_id: str | None = None
    catalog_hash_sha256: str | None = None
    catalog_schema_version: int | None = None
    runtime: str | None = "python"

    def evidence_payload(self) -> dict[str, object]:
        return {
            "operation_ref": self.operation_ref,
            "sdk_package_name": self.sdk_package_name,
            "sdk_name": self.sdk_name,
            "sdk_package_revision_id": self.sdk_package_revision_id,
            "catalog_hash_sha256": self.catalog_hash_sha256,
            "catalog_schema_version": self.catalog_schema_version,
            "runtime": self.runtime,
        }


@dataclass(frozen=True, slots=True)
class SkillSdkOperationRunRequest:
    """Request to run one catalog-declared SDK operation through Skill SDK."""

    operation_ref: str | None = None
    request_payload: Mapping[str, object] = field(default_factory=dict)
    context: Mapping[str, object] = field(default_factory=dict)
    timeout_s: float | None = None
    allow_mutation: bool = False
    target: SkillSdkOperationTarget | None = None


@dataclass(frozen=True, slots=True)
class SkillSdkOperationRunReceipt:
    """Receipt for one SDK operation run owned by the Skill SDK rail."""

    catalog_contract: str
    operation_ref: str
    sdk_name: str
    operation_name: str
    effect: str
    stability: str
    status: str
    result: object
    evidence: Mapping[str, object]
    target: SkillSdkOperationTarget | None = None
    catalog_package_name: str | None = None
    catalog_provider_ref: str | None = None
    catalog_version_number: int | None = None
    catalog_hash_sha256: str | None = None
    result_hash_sha256: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"


@dataclass(frozen=True, slots=True)
class SkillSdkOperationRunner:
    """Local Skill SDK runner for canonical SDK operation targets.

    The runner dispatches through `aware.sdk_operation_catalog.v0` providers. It
    is the SDK-first bridge for local effects while canonical SkillPackage
    execution grows first-class SDK operation targets.
    """

    extra_provider_refs: Sequence[str] = ()
    include_builtin_providers: bool = True

    async def run(
        self,
        request: SkillSdkOperationRunRequest,
    ) -> SkillSdkOperationRunReceipt:
        runtime = _load_sdk_operation_catalog_runtime()
        index = runtime.load_sdk_operation_catalog_index(
            extra_provider_refs=tuple(self.extra_provider_refs),
            include_builtin_providers=self.include_builtin_providers,
        )
        target = _target_from_request(request)
        operation = index.resolve(target.operation_ref)
        catalog = _catalog_for_operation(index=index, operation=operation)
        _validate_target_against_operation(
            target=target,
            operation=operation,
            catalog=catalog,
        )
        try:
            result = await runtime.invoke_sdk_operation(
                operation=operation,
                request_payload=dict(request.request_payload),
                context=dict(request.context),
                timeout_s=request.timeout_s,
                allow_mutation=request.allow_mutation,
            )
        except Exception as exc:
            if exc.__class__.__name__ == "SdkOperationCatalogError":
                raise SkillSdkError(str(exc)) from exc
            raise
        result_hash_sha256 = _result_hash_sha256(result)
        catalog_contract = str(runtime.SDK_OPERATION_CATALOG_CONTRACT)
        catalog_package_name = catalog.package_name if catalog is not None else None
        catalog_provider_ref = catalog.provider_ref if catalog is not None else None
        catalog_version_number = catalog.version_number if catalog is not None else None
        return SkillSdkOperationRunReceipt(
            catalog_contract=catalog_contract,
            operation_ref=operation.operation_ref,
            sdk_name=operation.sdk_name,
            operation_name=operation.operation_name,
            effect=operation.effect,
            stability=operation.stability,
            status="succeeded",
            result=result,
            evidence={
                "boundary": "aware_skill_sdk.sdk_operation_runner",
                "catalog_contract": catalog_contract,
                "catalog_package_name": catalog_package_name,
                "catalog_provider_ref": catalog_provider_ref,
                "catalog_version_number": catalog_version_number,
                "catalog_hash_sha256": target.catalog_hash_sha256,
                "target": target.evidence_payload(),
                "handler_ref": operation.handler_ref,
                "endpoint_refs": list(operation.endpoint_refs),
                "effect_policy": {
                    "effect": operation.effect,
                    "requires_confirmation": operation.requires_confirmation,
                    "allow_mutation": request.allow_mutation,
                },
                "result_hash_sha256": result_hash_sha256,
            },
            target=target,
            catalog_package_name=catalog_package_name,
            catalog_provider_ref=catalog_provider_ref,
            catalog_version_number=catalog_version_number,
            catalog_hash_sha256=target.catalog_hash_sha256,
            result_hash_sha256=result_hash_sha256,
        )


def _load_sdk_operation_catalog_runtime() -> _SdkOperationCatalogRuntime:
    try:
        module = cast(object, importlib.import_module("aware_sdk.operation_catalog"))
        return cast(_SdkOperationCatalogRuntime, module)
    except ModuleNotFoundError as exc:
        raise SkillSdkError(
            "Skill SDK SDK-operation runner requires aware-sdk operation catalog "
            "support. Install aware-sdk or provide the catalog package in the "
            "runtime environment."
        ) from exc


def _target_from_request(
    request: SkillSdkOperationRunRequest,
) -> SkillSdkOperationTarget:
    if request.target is None:
        return SkillSdkOperationTarget(
            operation_ref=_required_operation_ref(request.operation_ref),
        )
    target = request.target
    target_operation_ref = _required_operation_ref(target.operation_ref)
    if request.operation_ref is not None:
        request_operation_ref = _required_operation_ref(request.operation_ref)
        if request_operation_ref != target_operation_ref:
            raise SkillSdkError(
                "operation_ref must match target.operation_ref when both are set."
            )
    sdk_package_name = _optional_non_empty_text(target.sdk_package_name)
    if sdk_package_name is None:
        raise SkillSdkError(
            "target.sdk_package_name must be non-empty for materialized SDK "
            "operation targets."
        )
    catalog_hash_sha256 = _optional_hash_sha256(target.catalog_hash_sha256)
    return SkillSdkOperationTarget(
        operation_ref=target_operation_ref,
        sdk_package_name=sdk_package_name,
        sdk_name=_optional_non_empty_text(target.sdk_name),
        sdk_package_revision_id=_optional_non_empty_text(
            target.sdk_package_revision_id,
        ),
        catalog_hash_sha256=catalog_hash_sha256,
        catalog_schema_version=target.catalog_schema_version,
        runtime=_optional_non_empty_text(target.runtime),
    )


def _catalog_for_operation(
    *,
    index: _SdkOperationCatalogIndex,
    operation: _SdkOperationDescriptor,
) -> _SdkOperationCatalog | None:
    for catalog in index.catalogs:
        for item in catalog.operations:
            if item.operation_ref == operation.operation_ref:
                return catalog
    return None


def _validate_target_against_operation(
    *,
    target: SkillSdkOperationTarget,
    operation: _SdkOperationDescriptor,
    catalog: _SdkOperationCatalog | None,
) -> None:
    target_sdk_name = _optional_non_empty_text(target.sdk_name)
    if target_sdk_name is not None and target_sdk_name != operation.sdk_name:
        raise SkillSdkError(
            "target.sdk_name does not match resolved SDK operation: "
            f"{target_sdk_name!r} != {operation.sdk_name!r}."
        )
    operation_ref_sdk_name = _sdk_name_from_operation_ref(target.operation_ref)
    if operation_ref_sdk_name != operation.sdk_name:
        raise SkillSdkError(
            "target.operation_ref does not match resolved SDK name: "
            f"{operation_ref_sdk_name!r} != {operation.sdk_name!r}."
        )
    if catalog is None:
        raise SkillSdkError(
            "resolved SDK operation is not attached to a catalog package: "
            + operation.operation_ref
        )
    if (
        target.sdk_package_name is not None
        and target.sdk_package_name != catalog.package_name
    ):
        raise SkillSdkError(
            "target.sdk_package_name does not match resolved SDK catalog: "
            f"{target.sdk_package_name!r} != {catalog.package_name!r}."
        )


def _required_operation_ref(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        raise SkillSdkError("operation_ref must be non-empty.")
    _ = _sdk_name_from_operation_ref(text)
    return text


def _sdk_name_from_operation_ref(value: str) -> str:
    parts = value.split(".", 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise SkillSdkError(
            "operation_ref must use '<sdk_name>.<operation_name>' format."
        )
    return parts[0].strip()


def _optional_non_empty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_hash_sha256(value: object) -> str | None:
    text = _optional_non_empty_text(value)
    if text is None:
        return None
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise SkillSdkError("catalog_hash_sha256 must be lowercase SHA-256 hex.")
    return text


def _result_hash_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        default=str,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = [
    "SkillSdkOperationRunReceipt",
    "SkillSdkOperationRunRequest",
    "SkillSdkOperationRunner",
    "SkillSdkOperationTarget",
]
