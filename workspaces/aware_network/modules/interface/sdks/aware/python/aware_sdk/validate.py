"""Public aware-sdk validation orchestration."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import getpass
from importlib import resources
import json
from pathlib import Path
from typing import Any

from aware_release.proof import (
    emit_validation_pack,
    load_proof_profile,
    package_verified_proof,
    resolve_proof_profile,
    stage_proof_profile,
    sync_packaged_proof,
    verify_staged_proof,
)
from aware_release.proof.profile import ResolvedProofProfile

from .workspace_lifecycle import run_workspace_lifecycle_proof

DEFAULT_PUBLIC_PROOF_RAIL = "compile-first"
PUBLIC_PROOF_RAIL_RESOURCES = {
    "compile-first": "graph_os_home_story_compile.toml",
    "workspace-first": "graph_os_home_story_workspace.toml",
}


class ValidationError(RuntimeError):
    """Raised when public aware-sdk validation cannot complete honestly."""


_VALIDATION_LAYOUT_HINT = (
    "Use separate SDK-root children: --install-root $SDK_ROOT/install, "
    "--receipt-path $SDK_ROOT/receipts/install.json, "
    "--validation-root $SDK_ROOT/validation, then run $SDK_ROOT/bin/aware-sdk validate."
)


@dataclass(slots=True, frozen=True)
class ValidationRunResult:
    """Summary of one public aware-sdk validation run."""

    proof_rail: str | None
    profile_id: str
    public_repo_slug: str
    workspace_root: Path
    validation_root: Path
    install_receipt_path: Path
    aware_cli_executable: Path
    staged_repo_root: Path
    stage_receipt_path: Path
    verification_receipt_path: Path
    packaged_repo_root: Path
    package_receipt_path: Path
    target_repo_root: Path | None
    sync_receipt_path: Path | None
    workspace_lifecycle_receipt_path: Path | None
    pack_root: Path
    index_path: Path
    status: str
    summary: str


def run_validation(
    *,
    workspace_root: Path,
    validation_root: Path,
    install_receipt_path: Path | None = None,
    profile_path: Path | None = None,
    proof_rail: str | None = None,
    target_repo_root: Path | None = None,
    sync_target_repo: bool = True,
    operator: str | None = None,
    publication_id: str | None = None,
    consumer: str | None = None,
    release_track: str | None = None,
    required_kernel_repo_root: bool = False,
    used_dev_uv_run: bool = False,
    repo_assisted: bool | None = None,
    honesty_notes: tuple[str, ...] = (),
) -> ValidationRunResult:
    """Run one public Home validation rail from aware-sdk."""

    resolved_workspace_root = workspace_root.expanduser().resolve()
    if not resolved_workspace_root.is_dir():
        raise FileNotFoundError(f"Workspace root not found: {resolved_workspace_root}")

    resolved_validation_root = validation_root.expanduser().resolve()
    resolved_install_receipt_path = _resolve_install_receipt_path(install_receipt_path)
    install_receipt = _load_install_receipt(resolved_install_receipt_path)
    install_root = _resolve_install_root(install_receipt)
    _validate_validation_root_layout(
        validation_root=resolved_validation_root,
        install_root=install_root,
        install_receipt_path=resolved_install_receipt_path,
    )
    if resolved_validation_root.exists() and any(resolved_validation_root.iterdir()):
        raise ValidationError(
            "Validation root must be absent or empty before one fresh run: "
            f"{resolved_validation_root}. {_VALIDATION_LAYOUT_HINT}"
        )
    resolved_validation_root.mkdir(parents=True, exist_ok=True)

    receipts_root = resolved_validation_root / "receipts"
    stage_root = resolved_validation_root / "stage"
    packaging_root = resolved_validation_root / "package"
    pack_root = resolved_validation_root / "pack"
    receipts_root.mkdir(parents=True, exist_ok=True)

    aware_cli_executable = _resolve_installed_launcher(install_receipt)

    effective_repo_assisted = repo_assisted if repo_assisted is not None else True
    effective_operator = operator or _default_operator()
    effective_honesty_notes = tuple(honesty_notes) or (
        "Proof orchestration currently still depends on a workspace checkout for source/publication truth.",
    )

    with ExitStack() as stack:
        effective_profile_path = _resolve_profile_path(
            profile_path=profile_path,
            proof_rail=proof_rail,
            stack=stack,
        )
        profile = load_proof_profile(effective_profile_path)
        resolved_profile = resolve_proof_profile(
            profile=profile,
            workspace_root=resolved_workspace_root,
        )

        stage_result = stage_proof_profile(
            resolved_profile=resolved_profile,
            staging_root=stage_root,
        )
        verify_result = verify_staged_proof(
            resolved_profile=resolved_profile,
            staged_repo_root=stage_result.staged_repo_root,
            aware_cli_executable=aware_cli_executable,
            receipt_path=receipts_root / "proof-verify.json",
        )
        package_result = package_verified_proof(
            resolved_profile=resolved_profile,
            staged_repo_root=stage_result.staged_repo_root,
            verification_receipt_path=verify_result.receipt_path,
            packaging_root=packaging_root,
        )

        effective_target_repo_root: Path | None = None
        sync_receipt_path: Path | None = None
        if sync_target_repo:
            effective_target_repo_root = (
                target_repo_root.expanduser().resolve()
                if target_repo_root is not None
                else resolved_validation_root
                / "targets"
                / resolved_profile.profile.public_repo_slug
            )
            sync_result = sync_packaged_proof(
                resolved_profile=resolved_profile,
                packaged_repo_root=package_result.packaged_repo_root,
                package_receipt_path=package_result.package_receipt_path,
                target_repo_root=effective_target_repo_root,
                sync_receipt_path=receipts_root / "proof-sync.json",
            )
            sync_receipt_path = sync_result.sync_receipt_path

        workspace_lifecycle_receipt_path: Path | None = None
        if _requires_workspace_lifecycle_proof(resolved_profile=resolved_profile):
            workspace_lifecycle_result = run_workspace_lifecycle_proof(
                aware_cli_executable=aware_cli_executable,
                validation_root=resolved_validation_root,
                receipt_path=receipts_root / "workspace-lifecycle.json",
            )
            workspace_lifecycle_receipt_path = workspace_lifecycle_result.receipt_path

        pack_result = emit_validation_pack(
            resolved_profile=resolved_profile,
            install_receipt_path=resolved_install_receipt_path,
            stage_receipt_path=stage_result.receipt_path,
            verification_receipt_path=verify_result.receipt_path,
            package_receipt_path=package_result.package_receipt_path,
            sync_receipt_path=sync_receipt_path,
            pack_root=pack_root,
            validation_root=resolved_validation_root,
            producer_tool="aware-sdk",
            operator=effective_operator,
            publication_id=publication_id,
            consumer=consumer,
            release_track=release_track,
            used_installed_launcher=True,
            used_dev_uv_run=used_dev_uv_run,
            required_kernel_repo_root=required_kernel_repo_root,
            repo_assisted=effective_repo_assisted,
            honesty_notes=effective_honesty_notes,
            workspace_lifecycle_receipt_path=workspace_lifecycle_receipt_path,
        )

    return ValidationRunResult(
        proof_rail=proof_rail
        or (DEFAULT_PUBLIC_PROOF_RAIL if profile_path is None else None),
        profile_id=resolved_profile.profile.profile_id,
        public_repo_slug=resolved_profile.profile.public_repo_slug,
        workspace_root=resolved_workspace_root,
        validation_root=resolved_validation_root,
        install_receipt_path=resolved_install_receipt_path,
        aware_cli_executable=aware_cli_executable,
        staged_repo_root=stage_result.staged_repo_root,
        stage_receipt_path=stage_result.receipt_path,
        verification_receipt_path=verify_result.receipt_path,
        packaged_repo_root=package_result.packaged_repo_root,
        package_receipt_path=package_result.package_receipt_path,
        target_repo_root=effective_target_repo_root,
        sync_receipt_path=sync_receipt_path,
        workspace_lifecycle_receipt_path=workspace_lifecycle_receipt_path,
        pack_root=pack_result.pack_root,
        index_path=pack_result.index_path,
        status=pack_result.status,
        summary=pack_result.summary,
    )


def _resolve_install_receipt_path(value: Path | None) -> Path:
    if value is not None:
        resolved = value.expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Install receipt not found: {resolved}")
        return resolved

    receipts_root = (Path.home() / ".aware-sdk" / "receipts").resolve()
    candidates = sorted(
        receipts_root.glob("install-*.json"),
        key=lambda item: (item.stat().st_mtime, item.name),
    )
    if not candidates:
        raise ValidationError(
            "No install receipt was provided and no default aware-sdk install receipt "
            f"was found under {receipts_root}. Run 'aware-sdk install' first or pass "
            "--install-receipt-path explicitly."
        )
    return candidates[-1]


def _load_install_receipt(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"Install receipt must decode to a JSON object: {path}")
    return payload


def _resolve_install_root(install_receipt: dict[str, Any]) -> Path:
    raw_install_root = install_receipt.get("install_root")
    if not isinstance(raw_install_root, str) or not raw_install_root:
        raise ValidationError("Install receipt is missing 'install_root'.")
    return Path(raw_install_root).expanduser().resolve()


def _validate_validation_root_layout(
    *,
    validation_root: Path,
    install_root: Path,
    install_receipt_path: Path,
) -> None:
    if validation_root == install_root:
        raise ValidationError(
            "Validation root must not be the SDK install root. "
            + _VALIDATION_LAYOUT_HINT
        )
    if _path_contains(validation_root, install_root):
        raise ValidationError(
            "Validation root must not contain the SDK install root. "
            + _VALIDATION_LAYOUT_HINT
        )
    if _path_contains(install_root, validation_root):
        raise ValidationError(
            "Validation root must not live inside the SDK install root. "
            + _VALIDATION_LAYOUT_HINT
        )
    if _path_contains(validation_root, install_receipt_path):
        raise ValidationError(
            "Validation root must not contain the install receipt. "
            + _VALIDATION_LAYOUT_HINT
        )


def _path_contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return child != parent


def _resolve_installed_launcher(install_receipt: dict[str, Any]) -> Path:
    raw_launcher = install_receipt.get("aware_cli_executable")
    if not isinstance(raw_launcher, str) or not raw_launcher:
        raise ValidationError("Install receipt is missing 'aware_cli_executable'.")
    launcher = Path(raw_launcher).expanduser().resolve()
    if not launcher.is_file():
        raise FileNotFoundError(f"Installed aware-cli launcher not found: {launcher}")
    return launcher


def _resolve_profile_path(
    *,
    profile_path: Path | None,
    proof_rail: str | None,
    stack: ExitStack,
) -> Path:
    if profile_path is not None:
        if proof_rail is not None:
            raise ValidationError("Cannot combine --profile with --proof-rail.")
        resolved = profile_path.expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Proof profile not found: {resolved}")
        return resolved
    effective_proof_rail = proof_rail or DEFAULT_PUBLIC_PROOF_RAIL
    resource_name = PUBLIC_PROOF_RAIL_RESOURCES.get(effective_proof_rail)
    if resource_name is None:
        available = ", ".join(sorted(PUBLIC_PROOF_RAIL_RESOURCES))
        raise ValidationError(
            f"Unknown proof rail '{effective_proof_rail}'. Available rails: {available}"
        )
    resource = resources.files("aware_sdk").joinpath(
        "configs",
        "proofs",
        resource_name,
    )
    return stack.enter_context(resources.as_file(resource)).resolve()


def _default_operator() -> str:
    try:
        resolved = getpass.getuser().strip()
    except Exception:
        resolved = ""
    return resolved or "unknown"


def _requires_workspace_lifecycle_proof(
    *,
    resolved_profile: ResolvedProofProfile,
) -> bool:
    return resolved_profile.profile.publication_release_track_id == "workspace-first"


__all__ = [
    "DEFAULT_PUBLIC_PROOF_RAIL",
    "PUBLIC_PROOF_RAIL_RESOURCES",
    "ValidationError",
    "ValidationRunResult",
    "run_validation",
]
