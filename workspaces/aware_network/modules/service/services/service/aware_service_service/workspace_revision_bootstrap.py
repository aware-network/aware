from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID


_SERVICE_PACKAGE_KINDS = frozenset({"service", "service_package"})
_EXPERIENCE_PACKAGE_KINDS = frozenset({"experience", "experience_package"})


@dataclass(frozen=True, slots=True)
class ServiceHostWorkspaceRevisionPackageRef:
    family_key: str
    package_kind: str
    package_name: str
    manifest_path: Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "family_key": self.family_key,
            "package_kind": self.package_kind,
            "package_name": self.package_name,
            "manifest_path": (
                self.manifest_path.as_posix()
                if self.manifest_path is not None
                else None
            ),
            "workspace_package_id": self.workspace_package_id,
            "semantic_package_id": self.semantic_package_id,
            "semantic_object_instance_graph_commit_id": (
                self.semantic_object_instance_graph_commit_id
            ),
            "semantic_root_kind": self.semantic_root_kind,
            "semantic_root_id": self.semantic_root_id,
            "semantic_root_object_instance_graph_commit_id": (
                self.semantic_root_object_instance_graph_commit_id
            ),
            "source_code_package_id": self.source_code_package_id,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostWorkspaceRevisionArtifactRef:
    artifact_family: str
    artifact_key: str
    artifact_role: str
    required_for: tuple[str, ...] = ()
    producer_provider_key: str | None = None
    producer_key: str | None = None
    status: str = "available"
    package_name: str | None = None
    revision_code_package_id: str | None = None
    semantic_package_commit_id: str | None = None
    source_code_package_id: str | None = None
    source_object_instance_graph_commit_id: str | None = None
    input_object_instance_graph_commit_id: str | None = None
    workspace_relative_path: str | None = None
    manifest_path: str | None = None
    digest: str | None = None
    digest_algorithm: str | None = None
    media_type: str | None = None
    runtime_contract_version: str | None = None
    provider_payload: dict[str, object] | None = None
    receipt: dict[str, object] | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "artifact_family": self.artifact_family,
            "artifact_key": self.artifact_key,
            "artifact_role": self.artifact_role,
            "required_for": list(self.required_for),
            "producer_provider_key": self.producer_provider_key,
            "producer_key": self.producer_key,
            "status": self.status,
            "package_name": self.package_name,
            "revision_code_package_id": self.revision_code_package_id,
            "semantic_package_commit_id": self.semantic_package_commit_id,
            "source_code_package_id": self.source_code_package_id,
            "source_object_instance_graph_commit_id": (
                self.source_object_instance_graph_commit_id
            ),
            "input_object_instance_graph_commit_id": (
                self.input_object_instance_graph_commit_id
            ),
            "workspace_relative_path": self.workspace_relative_path,
            "manifest_path": self.manifest_path,
            "digest": self.digest,
            "digest_algorithm": self.digest_algorithm,
            "media_type": self.media_type,
            "runtime_contract_version": self.runtime_contract_version,
            "provider_payload": dict(self.provider_payload or {}),
            "receipt": dict(self.receipt or {}),
        }


@dataclass(frozen=True, slots=True)
class ServiceHostCodePackageArtifactRef:
    output_key: str
    artifact_key: str
    status: str = "available"
    code_package_id: str | None = None
    code_package_config_output_id: str | None = None
    artifact_family: str | None = None
    artifact_role: str | None = None
    required_for: tuple[str, ...] = ()
    producer_key: str | None = None
    producer_kind: str | None = None
    producer_provider_key: str | None = None
    materialization_index: int | None = None
    source_code_package_id: str | None = None
    source_object_instance_graph_commit_id: str | None = None
    input_code_package_id: str | None = None
    input_object_instance_graph_commit_id: str | None = None
    digest: str | None = None
    digest_algorithm: str | None = None
    relative_path: str | None = None
    uri: str | None = None
    media_type: str | None = None
    runtime_contract_version: str | None = None
    provider_payload: dict[str, object] | None = None
    receipt_payload: dict[str, object] | None = None
    error: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "code_package_id": self.code_package_id,
            "code_package_config_output_id": self.code_package_config_output_id,
            "output_key": self.output_key,
            "artifact_key": self.artifact_key,
            "status": self.status,
            "artifact_family": self.artifact_family,
            "artifact_role": self.artifact_role,
            "required_for": list(self.required_for),
            "producer_provider_key": self.producer_provider_key,
            "producer_key": self.producer_key,
            "producer_kind": self.producer_kind,
            "materialization_index": self.materialization_index,
            "source_code_package_id": self.source_code_package_id,
            "source_object_instance_graph_commit_id": (
                self.source_object_instance_graph_commit_id
            ),
            "input_code_package_id": self.input_code_package_id,
            "input_object_instance_graph_commit_id": (
                self.input_object_instance_graph_commit_id
            ),
            "digest": self.digest,
            "digest_algorithm": self.digest_algorithm,
            "relative_path": self.relative_path,
            "workspace_relative_path": self.relative_path,
            "manifest_path": self.relative_path,
            "uri": self.uri,
            "media_type": self.media_type,
            "runtime_contract_version": self.runtime_contract_version,
            "provider_payload": dict(self.provider_payload or {}),
            "receipt_payload": dict(self.receipt_payload or {}),
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostWorkspaceRevisionBootstrapPlan:
    status: str
    reason: str
    workspace_root: Path
    workspace_revision_id: str | None
    workspace_materialization_id: str | None
    service_package_name: str | None
    socket_path: Path
    config_path: Path
    service_package_refs: tuple[ServiceHostWorkspaceRevisionPackageRef, ...] = ()
    experience_package_refs: tuple[ServiceHostWorkspaceRevisionPackageRef, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    source_workspace_root: Path | None = None
    workspace_revision_filesystem_root_id: str | None = None
    revision_filesystem_manifest_path: Path | None = None
    runtime_manifest_path: Path | None = None
    environment_api_endpoint: str | None = None
    environment_id: str | None = None
    python_import_roots: tuple[Path, ...] = ()
    service_local_state_db_path: Path | None = None
    artifact_refs: tuple[ServiceHostWorkspaceRevisionArtifactRef, ...] = ()
    code_package_artifact_refs: tuple[ServiceHostCodePackageArtifactRef, ...] = ()
    reserved_revision_filesystem_root: bool = False

    @property
    def boot_ready(self) -> bool:
        return self.status == "planned" and not self.missing_requirements

    def to_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "boot_ready": self.boot_ready,
            "workspace_root": self.workspace_root.as_posix(),
            "workspace_revision_id": self.workspace_revision_id,
            "workspace_materialization_id": self.workspace_materialization_id,
            "source_workspace_root": (
                self.source_workspace_root.as_posix()
                if self.source_workspace_root is not None
                else None
            ),
            "workspace_revision_filesystem_root_id": (
                self.workspace_revision_filesystem_root_id
            ),
            "revision_filesystem_manifest_path": (
                self.revision_filesystem_manifest_path.as_posix()
                if self.revision_filesystem_manifest_path is not None
                else None
            ),
            "runtime_manifest_path": (
                self.runtime_manifest_path.as_posix()
                if self.runtime_manifest_path is not None
                else None
            ),
            "environment_api_endpoint": self.environment_api_endpoint,
            "environment_id": self.environment_id,
            "python_import_roots": [
                item.as_posix() for item in self.python_import_roots
            ],
            "service_local_state_db_path": (
                self.service_local_state_db_path.as_posix()
                if self.service_local_state_db_path is not None
                else None
            ),
            "artifact_refs": [item.to_payload() for item in self.artifact_refs],
            "code_package_artifact_refs": [
                item.to_payload() for item in self.code_package_artifact_refs
            ],
            "reserved_revision_filesystem_root": self.reserved_revision_filesystem_root,
            "service_package_name": self.service_package_name,
            "socket_path": self.socket_path.as_posix(),
            "config_path": self.config_path.as_posix(),
            "service_package_refs": [
                item.to_payload() for item in self.service_package_refs
            ],
            "experience_package_refs": [
                item.to_payload() for item in self.experience_package_refs
            ],
            "missing_requirements": list(self.missing_requirements),
        }


async def build_service_host_workspace_revision_bootstrap_plan_from_workspace_root(
    *,
    workspace_root: Path,
    workspace_revision_id: UUID | None = None,
    service_package: str | None = None,
    socket_path: Path | None = None,
    run_root: Path | None = None,
    materialized_workspace_root: Path | None = None,
    reserve_revision_filesystem_root: bool = True,
    owner_execution_id: str | None = None,
    environment_api_endpoint: str | None = None,
    environment_id: UUID | str | None = None,
    python_import_roots: tuple[Path, ...] = (),
    service_local_state_db_path: Path | None = None,
) -> ServiceHostWorkspaceRevisionBootstrapPlan:
    """Fail closed when Workspace truth has not already been resolved upstream."""

    resolved_source_workspace_root = workspace_root.expanduser().resolve()
    resolved_materialized_workspace_root = (
        materialized_workspace_root.expanduser().resolve()
        if materialized_workspace_root is not None
        else resolved_source_workspace_root
    )
    _ = reserve_revision_filesystem_root, owner_execution_id
    reason = "workspace_revision_bootstrap_upstream_required"
    read_model = _semantic_receipt_read_failure(
        workspace_root=resolved_materialized_workspace_root,
        workspace_revision_id=workspace_revision_id,
        reason=reason,
    )
    return _bootstrap_plan_failed(
        reason=reason,
        missing_requirements=(reason,),
        workspace_root=resolved_materialized_workspace_root,
        source_workspace_root=resolved_source_workspace_root,
        read_model=read_model,
        service_package=service_package,
        socket_path=socket_path,
        run_root=run_root,
        revision_filesystem_manifest_path=_revision_filesystem_manifest_path(
            resolved_materialized_workspace_root,
        ),
        environment_api_endpoint=environment_api_endpoint,
        environment_id=_string_or_none(environment_id),
        python_import_roots=_normalize_import_roots(python_import_roots),
        service_local_state_db_path=(
            service_local_state_db_path.expanduser().resolve()
            if service_local_state_db_path is not None
            else None
        ),
    )


def build_service_host_workspace_revision_bootstrap_plan_from_receipts(
    *,
    read_model: Any,
    workspace_root: Path | None = None,
    source_workspace_root: Path | None = None,
    service_package: str | None = None,
    socket_path: Path | None = None,
    run_root: Path | None = None,
    workspace_revision_filesystem_root_id: str | None = None,
    reserved_revision_filesystem_root: bool = False,
    environment_api_endpoint: str | None = None,
    environment_id: UUID | str | None = None,
    python_import_roots: tuple[Path, ...] = (),
    service_local_state_db_path: Path | None = None,
    require_revision_filesystem_manifest: bool = True,
    require_committed_semantic_refs: bool = True,
    require_environment_api_endpoint: bool = True,
) -> ServiceHostWorkspaceRevisionBootstrapPlan:
    resolved_workspace_root = _workspace_root(
        read_model=read_model, value=workspace_root
    )
    resolved_source_workspace_root = (
        source_workspace_root.expanduser().resolve()
        if source_workspace_root is not None
        else resolved_workspace_root
    )
    revision_id = _string_or_none(getattr(read_model, "workspace_revision_id", None))
    materialization_id = _string_or_none(
        getattr(read_model, "workspace_materialization_id", None)
    )
    selected_service_name = _string_or_none(service_package)
    default_run_root = _default_run_root(
        workspace_root=resolved_source_workspace_root,
        service_package=selected_service_name,
        workspace_revision_id=revision_id,
    )
    resolved_run_root = (run_root or default_run_root).expanduser().resolve()
    resolved_socket_path = (
        socket_path.expanduser().resolve()
        if socket_path is not None
        else (resolved_run_root / "service.sock").resolve()
    )
    resolved_config_path = (resolved_run_root / "aware.service.host.toml").resolve()
    resolved_python_import_roots = _normalize_import_roots(python_import_roots)
    resolved_environment_id = _string_or_none(environment_id)
    resolved_service_local_state_db_path = (
        service_local_state_db_path.expanduser().resolve()
        if service_local_state_db_path is not None
        else None
    )
    artifact_refs = _artifact_refs_from_read_model(read_model)
    code_package_artifact_refs = _code_package_artifact_refs_from_read_model(read_model)

    def _failed(
        *,
        reason: str,
        missing_requirements: tuple[str, ...],
        service_package_refs: tuple[ServiceHostWorkspaceRevisionPackageRef, ...] = (),
        experience_package_refs: tuple[
            ServiceHostWorkspaceRevisionPackageRef, ...
        ] = (),
        artifact_refs: tuple[ServiceHostWorkspaceRevisionArtifactRef, ...] = (
            artifact_refs
        ),
        code_package_artifact_refs: tuple[ServiceHostCodePackageArtifactRef, ...] = (
            code_package_artifact_refs
        ),
    ) -> ServiceHostWorkspaceRevisionBootstrapPlan:
        return _bootstrap_plan_failed(
            reason=reason,
            missing_requirements=missing_requirements,
            workspace_root=resolved_workspace_root,
            source_workspace_root=resolved_source_workspace_root,
            read_model=read_model,
            service_package=selected_service_name,
            socket_path=resolved_socket_path,
            run_root=resolved_run_root,
            workspace_revision_filesystem_root_id=workspace_revision_filesystem_root_id,
            revision_filesystem_manifest_path=revision_manifest_path,
            environment_api_endpoint=environment_api_endpoint,
            environment_id=resolved_environment_id,
            python_import_roots=resolved_python_import_roots,
            service_local_state_db_path=resolved_service_local_state_db_path,
            artifact_refs=artifact_refs,
            code_package_artifact_refs=code_package_artifact_refs,
            reserved_revision_filesystem_root=reserved_revision_filesystem_root,
            service_package_refs=service_package_refs,
            experience_package_refs=experience_package_refs,
        )

    revision_manifest_path = _revision_filesystem_manifest_path(resolved_workspace_root)
    if require_revision_filesystem_manifest and not revision_manifest_path.is_file():
        return _failed(
            reason="revision_filesystem_manifest_unavailable",
            missing_requirements=("revision_filesystem_manifest_unavailable",),
        )
    if not revision_manifest_path.is_file():
        revision_manifest_path = None

    if not bool(getattr(read_model, "available", False)):
        reason = _string_or_none(getattr(read_model, "reason", None)) or (
            "workspace_semantic_package_receipts_unavailable"
        )
        return _failed(reason=reason, missing_requirements=(reason,))

    receipts = tuple(getattr(read_model, "receipts", ()) or ())
    service_receipts = tuple(
        receipt
        for receipt in receipts
        if _semantic_package_kind(receipt) in _SERVICE_PACKAGE_KINDS
    )
    selected_service_receipts, service_error = _select_service_receipts(
        receipts=service_receipts,
        service_package=selected_service_name,
    )
    if service_error is not None:
        return _failed(reason=service_error, missing_requirements=(service_error,))

    experience_receipts = tuple(
        receipt
        for receipt in receipts
        if _semantic_package_kind(receipt) in _EXPERIENCE_PACKAGE_KINDS
    )
    service_package_refs = tuple(
        _package_ref_from_receipt(
            receipt,
            workspace_root=resolved_workspace_root,
            family_key="service",
            package_kind="service",
        )
        for receipt in selected_service_receipts
    )
    experience_package_refs = tuple(
        _package_ref_from_receipt(
            receipt,
            workspace_root=resolved_workspace_root,
            family_key="experience",
            package_kind="experience_package",
        )
        for receipt in experience_receipts
    )
    if require_committed_semantic_refs and any(
        ref.semantic_object_instance_graph_commit_id is None
        for ref in service_package_refs
    ):
        return _failed(
            reason="service_package_oig_pin_unavailable",
            missing_requirements=("service_package_oig_pin_unavailable",),
        )
    if require_committed_semantic_refs and any(
        ref.semantic_object_instance_graph_commit_id is None
        for ref in experience_package_refs
    ):
        return _failed(
            reason="experience_package_oig_pin_unavailable",
            missing_requirements=("experience_package_oig_pin_unavailable",),
        )

    if (
        require_environment_api_endpoint
        and _string_or_none(environment_api_endpoint) is None
    ):
        return _failed(
            reason="environment_sdk_endpoint_unavailable",
            missing_requirements=("environment_sdk_endpoint_unavailable",),
            service_package_refs=service_package_refs,
            experience_package_refs=experience_package_refs,
        )

    return ServiceHostWorkspaceRevisionBootstrapPlan(
        status="planned",
        reason="service_host_bootstrap_refs_resolved",
        workspace_root=resolved_workspace_root,
        workspace_revision_id=revision_id,
        workspace_materialization_id=materialization_id,
        source_workspace_root=resolved_source_workspace_root,
        workspace_revision_filesystem_root_id=workspace_revision_filesystem_root_id,
        revision_filesystem_manifest_path=revision_manifest_path,
        environment_api_endpoint=_string_or_none(environment_api_endpoint),
        environment_id=resolved_environment_id,
        python_import_roots=resolved_python_import_roots,
        service_local_state_db_path=resolved_service_local_state_db_path,
        artifact_refs=artifact_refs,
        code_package_artifact_refs=code_package_artifact_refs,
        reserved_revision_filesystem_root=reserved_revision_filesystem_root,
        service_package_name=(
            service_package_refs[0].package_name if service_package_refs else None
        ),
        socket_path=resolved_socket_path,
        config_path=resolved_config_path,
        service_package_refs=service_package_refs,
        experience_package_refs=experience_package_refs,
    )


def write_service_host_workspace_revision_bootstrap_config(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
) -> Path:
    if not plan.boot_ready:
        raise RuntimeError(
            "Cannot write ServiceHost bootstrap config for non-ready plan: "
            f"{plan.reason}"
        )
    plan.config_path.parent.mkdir(parents=True, exist_ok=True)
    plan.config_path.write_text(_bootstrap_config_toml(plan=plan), encoding="utf-8")
    return plan.config_path


def _semantic_receipt_read_failure(
    *,
    workspace_root: Path,
    workspace_revision_id: UUID | None,
    reason: str,
) -> object:
    return SimpleNamespace(
        available=False,
        reason=reason,
        workspace_root=workspace_root,
        workspace_revision_id=(
            str(workspace_revision_id) if workspace_revision_id is not None else None
        ),
        workspace_materialization_id=None,
        receipts=(),
    )


def _bootstrap_plan_failed(
    *,
    reason: str,
    missing_requirements: tuple[str, ...],
    workspace_root: Path,
    source_workspace_root: Path,
    read_model: object,
    service_package: str | None,
    socket_path: Path | None,
    run_root: Path | None,
    workspace_revision_filesystem_root_id: str | None = None,
    revision_filesystem_manifest_path: Path | None = None,
    runtime_manifest_path: Path | None = None,
    environment_api_endpoint: str | None = None,
    environment_id: str | None = None,
    python_import_roots: tuple[Path, ...] = (),
    service_local_state_db_path: Path | None = None,
    artifact_refs: tuple[ServiceHostWorkspaceRevisionArtifactRef, ...] = (),
    code_package_artifact_refs: tuple[ServiceHostCodePackageArtifactRef, ...] = (),
    reserved_revision_filesystem_root: bool = False,
    service_package_refs: tuple[ServiceHostWorkspaceRevisionPackageRef, ...] = (),
    experience_package_refs: tuple[ServiceHostWorkspaceRevisionPackageRef, ...] = (),
) -> ServiceHostWorkspaceRevisionBootstrapPlan:
    revision_id = _string_or_none(getattr(read_model, "workspace_revision_id", None))
    materialization_id = _string_or_none(
        getattr(read_model, "workspace_materialization_id", None)
    )
    selected_service_name = _string_or_none(service_package)
    resolved_run_root = (
        (
            run_root
            or _default_run_root(
                workspace_root=source_workspace_root,
                service_package=selected_service_name,
                workspace_revision_id=revision_id,
            )
        )
        .expanduser()
        .resolve()
    )
    resolved_socket_path = (
        socket_path.expanduser().resolve()
        if socket_path is not None
        else (resolved_run_root / "service.sock").resolve()
    )
    return ServiceHostWorkspaceRevisionBootstrapPlan(
        status="failed",
        reason=reason,
        workspace_root=workspace_root.expanduser().resolve(),
        workspace_revision_id=revision_id,
        workspace_materialization_id=materialization_id,
        source_workspace_root=source_workspace_root.expanduser().resolve(),
        workspace_revision_filesystem_root_id=workspace_revision_filesystem_root_id,
        revision_filesystem_manifest_path=revision_filesystem_manifest_path,
        runtime_manifest_path=runtime_manifest_path,
        environment_api_endpoint=_string_or_none(environment_api_endpoint),
        environment_id=_string_or_none(environment_id),
        python_import_roots=python_import_roots,
        service_local_state_db_path=service_local_state_db_path,
        artifact_refs=artifact_refs,
        code_package_artifact_refs=code_package_artifact_refs,
        reserved_revision_filesystem_root=reserved_revision_filesystem_root,
        service_package_name=selected_service_name,
        socket_path=resolved_socket_path,
        config_path=(resolved_run_root / "aware.service.host.toml").resolve(),
        service_package_refs=service_package_refs,
        experience_package_refs=experience_package_refs,
        missing_requirements=missing_requirements,
    )


def _bootstrap_config_toml(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
) -> str:
    lines = [
        "[ipc]",
        f'socket_path = "{_toml_string(plan.socket_path.as_posix())}"',
        "",
    ]
    if plan.environment_api_endpoint is not None:
        lines.extend(
            [
                "[environment]",
                f'api_endpoint = "{_toml_string(plan.environment_api_endpoint)}"',
                "",
            ]
        )
    if plan.service_local_state_db_path is not None:
        lines.extend(
            [
                "[ontology_replica]",
                (
                    'state_db_path = "'
                    + _toml_string(plan.service_local_state_db_path.as_posix())
                    + '"'
                ),
                "",
            ]
        )
    lines.extend(
        [
            "[artifact]",
            ('root = "' + _toml_string(plan.workspace_root.as_posix()) + '"'),
            "",
            "[implementation_packages]",
        ]
    )
    for package_ref in plan.service_package_refs:
        lines.extend(("", "[[implementation_packages.package_refs]]"))
        lines.extend(_package_ref_toml_lines(package_ref))
    for package_ref in plan.experience_package_refs:
        lines.extend(("", "[[reference_packages.experience_package_refs]]"))
        lines.extend(_package_ref_toml_lines(package_ref))
    lines.append("")
    return "\n".join(lines)


def _normalize_import_roots(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        token = resolved.as_posix()
        if token in seen:
            continue
        seen.add(token)
        result.append(resolved)
    return tuple(result)


def _package_ref_toml_lines(
    package_ref: ServiceHostWorkspaceRevisionPackageRef,
) -> list[str]:
    fields: tuple[tuple[str, str | None], ...] = (
        ("family_key", package_ref.family_key),
        ("package_kind", package_ref.package_kind),
        ("package_name", package_ref.package_name),
        (
            "manifest_path",
            (
                package_ref.manifest_path.as_posix()
                if package_ref.manifest_path is not None
                else None
            ),
        ),
        ("workspace_package_id", package_ref.workspace_package_id),
        ("semantic_package_id", package_ref.semantic_package_id),
        (
            "semantic_object_instance_graph_commit_id",
            package_ref.semantic_object_instance_graph_commit_id,
        ),
        ("semantic_root_kind", package_ref.semantic_root_kind),
        ("semantic_root_id", package_ref.semantic_root_id),
        (
            "semantic_root_object_instance_graph_commit_id",
            package_ref.semantic_root_object_instance_graph_commit_id,
        ),
        ("source_code_package_id", package_ref.source_code_package_id),
    )
    return [
        f'{key} = "{_toml_string(value)}"'
        for key, value in fields
        if value is not None and str(value).strip()
    ]


def _select_service_receipts(
    *,
    receipts: tuple[object, ...],
    service_package: str | None,
) -> tuple[tuple[object, ...], str | None]:
    selected_name = _string_or_none(service_package)
    matches = (
        tuple(
            receipt for receipt in receipts if _package_name(receipt) == selected_name
        )
        if selected_name
        else receipts
    )
    if not matches:
        return (), "service_package_ref_unavailable"
    if len(matches) > 1:
        return (), "service_package_ref_ambiguous"
    return matches, None


def _package_ref_from_receipt(
    receipt: object,
    *,
    workspace_root: Path,
    family_key: str,
    package_kind: str,
) -> ServiceHostWorkspaceRevisionPackageRef:
    semantic_package_id = _string_or_none(getattr(receipt, "semantic_package_id", None))
    semantic_oig_commit_id = _string_or_none(
        getattr(receipt, "semantic_object_instance_graph_commit_id", None)
    )
    manifest_path = (
        None
        if semantic_oig_commit_id is not None
        else _receipt_manifest_path(receipt=receipt, workspace_root=workspace_root)
    )
    return ServiceHostWorkspaceRevisionPackageRef(
        family_key=family_key,
        package_kind=package_kind,
        package_name=(
            _package_name(receipt) or semantic_package_id or "unknown-package"
        ),
        manifest_path=manifest_path,
        workspace_package_id=_string_or_none(
            getattr(receipt, "revision_code_package_id", None)
        ),
        semantic_package_id=semantic_package_id,
        semantic_object_instance_graph_commit_id=semantic_oig_commit_id,
        semantic_root_kind=_string_or_none(
            getattr(receipt, "semantic_root_kind", None)
        ),
        semantic_root_id=_string_or_none(getattr(receipt, "semantic_root_id", None)),
        semantic_root_object_instance_graph_commit_id=_string_or_none(
            getattr(receipt, "semantic_root_object_instance_graph_commit_id", None)
        ),
        source_code_package_id=_string_or_none(
            getattr(receipt, "source_code_package_id", None)
        ),
    )


def _artifact_refs_from_read_model(
    read_model: object,
) -> tuple[ServiceHostWorkspaceRevisionArtifactRef, ...]:
    for attribute in (
        "artifact_refs",
        "workspace_revision_artifact_refs",
    ):
        items = _object_sequence(getattr(read_model, attribute, None))
        if not items:
            continue
        return tuple(
            ref
            for item in items
            if (ref := _artifact_ref_from_payload(item)) is not None
        )
    return ()


def _code_package_artifact_refs_from_read_model(
    read_model: object,
) -> tuple[ServiceHostCodePackageArtifactRef, ...]:
    candidates: tuple[object, ...] = (read_model,)
    result = _payload_value(read_model, "result")
    if result is not None:
        candidates = (read_model, result)
    for candidate in candidates:
        items = _object_sequence(
            _payload_value(candidate, "code_package_artifact_refs")
        )
        if not items:
            continue
        return tuple(
            ref
            for item in items
            if (ref := _code_package_artifact_ref_from_payload(item)) is not None
        )
    return ()


def _artifact_ref_from_payload(
    payload: object,
) -> ServiceHostWorkspaceRevisionArtifactRef | None:
    artifact_family = _payload_string(payload, "artifact_family")
    artifact_key = _payload_string(payload, "artifact_key")
    artifact_role = _payload_string(payload, "artifact_role")
    if artifact_family is None or artifact_key is None or artifact_role is None:
        return None
    return ServiceHostWorkspaceRevisionArtifactRef(
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        artifact_role=artifact_role,
        required_for=_payload_string_tuple(payload, "required_for"),
        producer_provider_key=_payload_string(payload, "producer_provider_key"),
        producer_key=_payload_string(payload, "producer_key"),
        status=_payload_string(payload, "status") or "available",
        package_name=_payload_string(payload, "package_name"),
        revision_code_package_id=_payload_string(
            payload,
            "revision_code_package_id",
        ),
        semantic_package_commit_id=_payload_string(
            payload,
            "semantic_package_commit_id",
        ),
        source_code_package_id=_payload_string(payload, "source_code_package_id"),
        source_object_instance_graph_commit_id=_payload_string(
            payload,
            "source_object_instance_graph_commit_id",
        ),
        input_object_instance_graph_commit_id=_payload_string(
            payload,
            "input_object_instance_graph_commit_id",
        ),
        workspace_relative_path=_payload_string(payload, "workspace_relative_path"),
        manifest_path=_payload_string(payload, "manifest_path"),
        digest=_payload_string(payload, "digest"),
        digest_algorithm=_payload_string(payload, "digest_algorithm"),
        media_type=_payload_string(payload, "media_type"),
        runtime_contract_version=_payload_string(
            payload,
            "runtime_contract_version",
        ),
        provider_payload=_payload_mapping(payload, "provider_payload"),
        receipt=_payload_mapping(payload, "receipt"),
    )


def _code_package_artifact_ref_from_payload(
    payload: object,
) -> ServiceHostCodePackageArtifactRef | None:
    output_key = _payload_string(payload, "output_key")
    artifact_key = _payload_string(payload, "artifact_key")
    if output_key is None or artifact_key is None:
        return None
    receipt_payload = _payload_mapping(payload, "receipt_payload")
    provider_payload = _payload_mapping(payload, "provider_payload")
    producer_provider_key = (
        _payload_string(payload, "producer_provider_key")
        or _payload_mapping_string(provider_payload, "producer_provider_key")
        or _payload_mapping_string(receipt_payload, "producer_provider_key")
    )
    digest_algorithm = _payload_string(
        payload, "digest_algorithm"
    ) or _payload_mapping_string(receipt_payload, "digest_algorithm")
    return ServiceHostCodePackageArtifactRef(
        output_key=output_key,
        artifact_key=artifact_key,
        status=_payload_string(payload, "status") or "available",
        code_package_id=_payload_string(payload, "code_package_id"),
        code_package_config_output_id=_payload_string(
            payload,
            "code_package_config_output_id",
        ),
        artifact_family=_payload_string(payload, "artifact_family"),
        artifact_role=_payload_string(payload, "artifact_role"),
        required_for=_payload_string_tuple(payload, "required_for"),
        producer_key=_payload_string(payload, "producer_key"),
        producer_kind=_payload_string(payload, "producer_kind"),
        producer_provider_key=producer_provider_key,
        materialization_index=_payload_int(payload, "materialization_index"),
        source_code_package_id=_payload_string(payload, "source_code_package_id"),
        source_object_instance_graph_commit_id=_payload_string(
            payload,
            "source_object_instance_graph_commit_id",
        ),
        input_code_package_id=_payload_string(payload, "input_code_package_id"),
        input_object_instance_graph_commit_id=_payload_string(
            payload,
            "input_object_instance_graph_commit_id",
        ),
        digest=_payload_string(payload, "digest"),
        digest_algorithm=digest_algorithm,
        relative_path=_payload_string(payload, "relative_path"),
        uri=_payload_string(payload, "uri"),
        media_type=_payload_string(payload, "media_type"),
        runtime_contract_version=_payload_string(
            payload,
            "runtime_contract_version",
        ),
        provider_payload=provider_payload,
        receipt_payload=receipt_payload,
        error=_payload_string(payload, "error"),
    )


def _receipt_manifest_path(*, receipt: object, workspace_root: Path) -> Path | None:
    raw = _string_or_none(getattr(receipt, "manifest_path", None))
    if raw is None:
        raw = _string_or_none(getattr(receipt, "manifest_toml_path", None))
    if raw is None:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    return path.resolve()


def _workspace_root(*, read_model: object, value: Path | None) -> Path:
    if value is not None:
        return value.expanduser().resolve()
    raw = getattr(read_model, "workspace_root", None)
    if raw is None:
        raise RuntimeError(
            "ServiceHost WorkspaceRevision bootstrap requires workspace_root."
        )
    return Path(raw).expanduser().resolve()


def _default_run_root(
    *,
    workspace_root: Path,
    service_package: str | None,
    workspace_revision_id: str | None,
) -> Path:
    service_key = _safe_path_key(service_package or "service")
    revision_key = _safe_path_key(workspace_revision_id or "latest")
    return (
        workspace_root
        / ".aware"
        / "service-host"
        / "runs"
        / f"{service_key}-{revision_key[:12]}"
    )


def _revision_filesystem_manifest_path(workspace_root: Path) -> Path:
    return (
        workspace_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    ).resolve()


def _runtime_manifest_path(workspace_root: Path) -> Path | None:
    path = (
        workspace_root
        / ".aware"
        / "environment"
        / "runtime"
        / "environment.manifest.json"
    ).resolve()
    return path if path.is_file() else None


def _semantic_package_kind(receipt: object) -> str:
    return _string_or_none(getattr(receipt, "semantic_package_kind", None)) or ""


def _package_name(receipt: object) -> str | None:
    return _string_or_none(getattr(receipt, "semantic_package_name", None))


def _string_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _object_sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _payload_value(payload: object, key: str) -> object:
    if isinstance(payload, dict):
        return payload.get(key)
    return getattr(payload, key, None)


def _payload_string(payload: object, key: str) -> str | None:
    return _string_or_none(_payload_value(payload, key))


def _payload_mapping_string(
    payload: Mapping[str, object] | None,
    key: str,
) -> str | None:
    if payload is None:
        return None
    return _string_or_none(payload.get(key))


def _payload_int(payload: object, key: str) -> int | None:
    value = _payload_value(payload, key)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except ValueError:
        return None


def _payload_string_tuple(payload: object, key: str) -> tuple[str, ...]:
    value = _payload_value(payload, key)
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _payload_mapping(payload: object, key: str) -> dict[str, object] | None:
    value = _payload_value(payload, key)
    if not isinstance(value, Mapping):
        return None
    return {str(item_key): item_value for item_key, item_value in value.items()}


def _safe_path_key(value: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "-"
        for char in value.strip()
    ).strip("-._")
    return cleaned or "service"


def _toml_string(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


__all__ = [
    "ServiceHostCodePackageArtifactRef",
    "ServiceHostWorkspaceRevisionArtifactRef",
    "ServiceHostWorkspaceRevisionBootstrapPlan",
    "ServiceHostWorkspaceRevisionPackageRef",
    "build_service_host_workspace_revision_bootstrap_plan_from_receipts",
    "build_service_host_workspace_revision_bootstrap_plan_from_workspace_root",
    "write_service_host_workspace_revision_bootstrap_config",
]
