"""Entry points for the aware-sdk helper CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform as platform_lib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from . import __version__
from .commands.app import handle_app_command, register_app_parser
from .commands.interface import (
    handle_interface_renderer_command,
    register_interface_renderer_parsers,
)
from .commands.sdk import handle_sdk_command, register_sdk_operation_parsers

DEFAULT_PUBLIC_PROOF_RAIL = "compile-first"

_PUBLIC_BUNDLE_PROFILE = "workspaces/aware_network/modules/interface/sdks/aware/python/aware_sdk/configs/bundles/graph_os_linux_cli_public.toml"
_PUBLIC_PROOF_RAILS = {
    "compile-first": {
        "profile": "workspaces/aware_network/modules/interface/sdks/aware/python/aware_sdk/configs/proofs/graph_os_home_story_compile.toml",
        "status": "default",
    },
    "workspace-first": {
        "profile": "workspaces/aware_network/modules/interface/sdks/aware/python/aware_sdk/configs/proofs/graph_os_home_story_workspace.toml",
        "status": "preview",
    },
}
_PUBLIC_PROOF_PROFILE = _PUBLIC_PROOF_RAILS[DEFAULT_PUBLIC_PROOF_RAIL]["profile"]
_PUBLIC_PROOF_REPO_SLUG = "home-workspace"
_PUBLIC_COMMANDS = (
    "app",
    "status",
    "render",
    "panes",
    "invoke",
    "act",
    "follow",
    "capabilities",
    "profile",
)
_TRANSITIONAL_INTERFACE_COMMANDS = ("actions", "run")
_TRANSITIONAL_DIAGNOSTIC_COMMANDS = ("hub", "identity", "sdk")
_PLANNED_PRODUCT_COMMANDS = ("local",)
_LEGACY_KERNEL_PROOF_COMMANDS = ("compile", "workspace")
_PUBLIC_VALIDATION_COMMAND = "validate"
_PUBLIC_CAPABILITIES = (
    "committed-app-session-entry",
    "interface-status-rendering",
    "interface-surface-rendering",
    "interface-pane-listing",
    "interface-pane-capability-invocation",
    "interface-pane-action-invocation",
    "interface-capability-rendering",
    "interface-profile-selection",
)
_LOCAL_EXTRA_CAPABILITIES = (
    "local-node-activation",
    "deploy-adapter",
    "local-capability-providers",
)
_PRODUCT_LAUNCHERS = ("aware", "aware-sdk")
_LEGACY_BUNDLE_LAUNCHERS = ("aware-cli", "aware-sdk")
_LEGACY_KERNEL_CAPABILITIES = ("compile", "runtime", "python", "sql", "sqlite")
_DEFAULT_CHANNEL = "stable"
_DEFAULT_AUTHORITY_BASE_URL = "https://aware.run/distribution"
_INSTALLER_PAYLOAD_NAME = "aware-sdk-installer.pyz"
_PRIMARY_LEGACY_LAUNCHER_NAME = "aware-cli"


def info() -> int:
    """Emit the public aware-sdk distribution contract."""
    payload = {
        "aware_sdk": __version__,
        "aware_api": _safe_version("aware-api"),
        "aware_hub_service_api": _safe_version("aware_hub_service_api"),
        "aware_interface_sdk": _safe_version("aware-interface-sdk"),
        "public_contract": {
            "product_boundary": "interface-renderer",
            "commands": list(_PUBLIC_COMMANDS),
            "planned_commands": list(_PLANNED_PRODUCT_COMMANDS),
            "canonical_rail": (
                "aware-sdk -> interface-sdk -> Interface -> Experience -> "
                "API/Services"
            ),
            "transitional_diagnostics": {
                "commands": list(_TRANSITIONAL_DIAGNOSTIC_COMMANDS)
                + list(_TRANSITIONAL_INTERFACE_COMMANDS),
                "status": "hidden-bootstrap-diagnostic-only",
            },
            "operation_catalog_contract": {
                "status": "preview",
                "command": "sdk",
                "catalog_contract": "aware.sdk_operation_catalog.v0",
                "entry_point_group": "aware.sdk_operation_catalogs",
                "invariant": (
                    "SDK CLI operations must be declared by explicit SDK "
                    "operation catalog providers, not reflected from methods."
                ),
            },
            "validation_command": _PUBLIC_VALIDATION_COMMAND,
            "install_commands": ["install", "activate", "rollback"],
            "capabilities": list(_PUBLIC_CAPABILITIES),
            "local_extra_capabilities": list(_LOCAL_EXTRA_CAPABILITIES),
            "launchers": list(_PRODUCT_LAUNCHERS),
            "legacy_bundle_launchers": list(_LEGACY_BUNDLE_LAUNCHERS),
            "legacy_kernel_proof": {
                "commands": list(_LEGACY_KERNEL_PROOF_COMMANDS),
                "capabilities": list(_LEGACY_KERNEL_CAPABILITIES),
                "aware_cli": _safe_version("aware-cli"),
                "aware_cli_compile_pack": _safe_version("aware-cli-compile-pack"),
            },
            "bundle_profile": _PUBLIC_BUNDLE_PROFILE,
            "proof_profile": _PUBLIC_PROOF_PROFILE,
            "default_proof_rail": DEFAULT_PUBLIC_PROOF_RAIL,
            "proof_rails": [
                {
                    "id": rail_id,
                    "profile": rail_payload["profile"],
                    "status": rail_payload["status"],
                }
                for rail_id, rail_payload in _PUBLIC_PROOF_RAILS.items()
            ],
            "proof_repo_slug": _PUBLIC_PROOF_REPO_SLUG,
        },
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def install(args: argparse.Namespace) -> int:
    """Resolve one release entry and invoke the canonical installer payload."""
    platform = args.platform or _default_platform()
    authority_base_url = _optional_str(args.authority_base_url) or None
    index_url = args.index_url or _resolve_release_index_url(
        platform=platform,
        authority_base_url=authority_base_url,
    )
    install_root = Path(args.install_root).expanduser().resolve()
    receipt_path = _resolve_receipt_path(args.receipt_path, prefix="install")
    bootstrap_python = args.bootstrap_python or sys.executable
    installer_python = args.python_executable or sys.executable

    with tempfile.TemporaryDirectory(prefix="aware-sdk-install-") as temp_dir:
        temp_root = Path(temp_dir)
        index_payload = _load_json_source(index_url)
        entry = _resolve_install_entry(
            index_payload=index_payload,
            channel=args.channel,
            platform=platform,
            version=args.version,
        )
        installer_payload_url = _required_str(
            entry.get("installer_payload_url"), "installer_payload_url"
        )
        installer_path = _download_artifact(
            installer_payload_url,
            temp_root / _INSTALLER_PAYLOAD_NAME,
        )
        installer_sha256 = _optional_str(entry.get("installer_payload_sha256"))
        if installer_sha256:
            _verify_sha256(installer_path, installer_sha256)

        archive_url = _required_str(entry.get("archive_url"), "archive_url")
        archive_name = _download_name(archive_url, default="bundle.tar.gz")
        archive_path = _download_artifact(archive_url, temp_root / archive_name)
        _verify_sha256(
            archive_path, _required_str(entry.get("archive_sha256"), "archive_sha256")
        )

        install_payload = _invoke_installer_payload(
            bootstrap_python=bootstrap_python,
            installer_path=installer_path,
            archive_path=archive_path,
            install_root=install_root,
            receipt_path=receipt_path,
            force=args.force,
            python_executable=installer_python,
        )

    payload = {
        **install_payload,
        "receipt_path": str(receipt_path),
        "install_distribution": {
            "authority_base_url": authority_base_url or _DEFAULT_AUTHORITY_BASE_URL,
            "index_url": index_url,
            "channel": args.channel,
            "platform": platform,
            "requested_version": args.version,
            "resolved_entry": entry,
        },
    }
    if args.activate:
        activation_payload = _activate_channel(
            install_root=install_root,
            channel=_required_str(install_payload.get("channel"), "channel"),
            version=_required_str(install_payload.get("version"), "version"),
            launcher_names=_LEGACY_BUNDLE_LAUNCHERS,
        )
        activation = activation_payload.get("activation")
        if not isinstance(activation, dict):
            raise ValueError("Activation payload is missing activation details.")
        payload["activation"] = activation
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def activate(args: argparse.Namespace) -> int:
    """Activate one already-installed version for a channel."""
    install_root = Path(args.install_root).expanduser().resolve()
    receipt_path = _resolve_receipt_path(args.receipt_path, prefix="activate")
    payload = _activate_channel(
        install_root=install_root,
        channel=args.channel,
        version=args.version,
        launcher_names=_LEGACY_BUNDLE_LAUNCHERS,
    )
    _write_receipt_and_stdout(payload=payload, receipt_path=receipt_path)
    return 0


def rollback(args: argparse.Namespace) -> int:
    """Rollback a channel pointer to an earlier installed version."""
    install_root = Path(args.install_root).expanduser().resolve()
    sdk_root = _sdk_root_from_install_root(install_root)
    current = _resolve_current_activation(sdk_root=sdk_root, channel=args.channel)
    current_version = current["version"]
    target_version = args.version or _select_rollback_version(
        install_root=install_root,
        channel=args.channel,
        current_version=current_version,
    )
    receipt_path = _resolve_receipt_path(args.receipt_path, prefix="rollback")
    activation = _activate_channel(
        install_root=install_root,
        channel=args.channel,
        version=target_version,
        launcher_names=_LEGACY_BUNDLE_LAUNCHERS,
    )
    payload = {
        **activation,
        "rollback": {
            "from_version": current_version,
            "to_version": target_version,
        },
    }
    _write_receipt_and_stdout(payload=payload, receipt_path=receipt_path)
    return 0


def validate(args: argparse.Namespace) -> int:
    from .validate import run_validation

    """Run the current public aware-sdk validation rail."""

    raw_repo_assisted = getattr(args, "repo_assisted", None)
    repo_assisted: bool | None
    if raw_repo_assisted is None or isinstance(raw_repo_assisted, bool):
        repo_assisted = raw_repo_assisted
    else:
        repo_assisted = bool(raw_repo_assisted)

    result = run_validation(
        workspace_root=Path(args.workspace_root),
        validation_root=Path(args.validation_root),
        install_receipt_path=(
            Path(args.install_receipt_path) if args.install_receipt_path else None
        ),
        profile_path=(Path(args.profile) if args.profile else None),
        proof_rail=args.proof_rail,
        target_repo_root=(
            Path(args.target_repo_root) if args.target_repo_root else None
        ),
        sync_target_repo=args.sync_target_repo,
        operator=args.operator,
        publication_id=args.publication_id,
        consumer=args.consumer,
        release_track=args.release_track,
        required_kernel_repo_root=args.required_kernel_repo_root,
        used_dev_uv_run=args.used_dev_uv_run,
        repo_assisted=repo_assisted,
        honesty_notes=tuple(args.honesty_note),
    )
    payload = {
        "proof_rail": result.proof_rail,
        "profile_id": result.profile_id,
        "public_repo_slug": result.public_repo_slug,
        "workspace_root": str(result.workspace_root),
        "validation_root": str(result.validation_root),
        "install_receipt_path": str(result.install_receipt_path),
        "aware_cli_executable": str(result.aware_cli_executable),
        "staged_repo_root": str(result.staged_repo_root),
        "stage_receipt_path": str(result.stage_receipt_path),
        "verification_receipt_path": str(result.verification_receipt_path),
        "packaged_repo_root": str(result.packaged_repo_root),
        "package_receipt_path": str(result.package_receipt_path),
        "target_repo_root": (
            str(result.target_repo_root) if result.target_repo_root else None
        ),
        "sync_receipt_path": (
            str(result.sync_receipt_path) if result.sync_receipt_path else None
        ),
        "workspace_lifecycle_receipt_path": (
            str(result.workspace_lifecycle_receipt_path)
            if result.workspace_lifecycle_receipt_path
            else None
        ),
        "pack_root": str(result.pack_root),
        "index_path": str(result.index_path),
        "status": result.status,
        "summary": result.summary,
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser(
        include_hidden_hub=bool(raw_argv and raw_argv[0] == "hub"),
        include_hidden_identity=bool(raw_argv and raw_argv[0] == "identity"),
        include_hidden_sdk=bool(raw_argv and raw_argv[0] == "sdk"),
        include_transitional_interface=bool(
            raw_argv and raw_argv[0] in _TRANSITIONAL_INTERFACE_COMMANDS
        ),
    )
    args = parser.parse_args(raw_argv)
    command = args.command or "info"
    try:
        if command == "info":
            return info()
        if command == "install":
            return install(args)
        if command == "activate":
            return activate(args)
        if command == "rollback":
            return rollback(args)
        if command == "validate":
            return validate(args)
        if command == "app":
            return handle_app_command(args)
        if command in _PUBLIC_COMMANDS or command in _TRANSITIONAL_INTERFACE_COMMANDS:
            return handle_interface_renderer_command(args)
        if command == "hub":
            from .commands.hub import handle_hub_command

            return handle_hub_command(args)
        if command == "identity":
            from .commands.identity import handle_identity_command

            return handle_identity_command(args)
        if command == "sdk":
            return handle_sdk_command(args)
    except Exception as exc:
        sys.stderr.write(f"aware-sdk: {exc}\n")
        return 1
    parser.error(f"Unknown command: {command}")
    return 2


def _build_parser(
    *,
    include_hidden_hub: bool = False,
    include_hidden_identity: bool = False,
    include_hidden_sdk: bool = False,
    include_transitional_interface: bool = False,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aware-sdk",
        description="Public aware-sdk Interface renderer.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    subparsers.add_parser("info", help="Emit the current public aware-sdk contract.")
    register_interface_renderer_parsers(
        subparsers,
        include_transitional_actions=include_transitional_interface,
    )
    register_app_parser(subparsers)
    if include_hidden_hub:
        from .commands.hub import register_hub_parser

        register_hub_parser(subparsers)
    if include_hidden_identity:
        from .commands.identity import register_identity_parser

        register_identity_parser(subparsers)
    if include_hidden_sdk:
        register_sdk_operation_parsers(subparsers)

    install_parser = subparsers.add_parser(
        "install",
        help="Resolve a hosted release index entry and install the selected bundle.",
    )
    install_parser.add_argument("--index-url")
    install_parser.add_argument("--authority-base-url")
    install_parser.add_argument("--channel", default=_DEFAULT_CHANNEL)
    install_parser.add_argument("--version")
    install_parser.add_argument("--platform")
    install_parser.add_argument(
        "--install-root",
        default=str((Path.home() / ".aware-sdk" / "installs").resolve()),
    )
    install_parser.add_argument("--receipt-path")
    install_parser.add_argument("--bootstrap-python")
    install_parser.add_argument("--python-executable")
    install_parser.add_argument(
        "--activate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Update channel/launcher activation pointers after install (default: on).",
    )
    install_parser.add_argument("--force", action="store_true")

    activate_parser = subparsers.add_parser(
        "activate",
        help="Point one channel at an already-installed version without mutating install trees.",
    )
    activate_parser.add_argument("--channel", default=_DEFAULT_CHANNEL)
    activate_parser.add_argument("--version", required=True)
    activate_parser.add_argument(
        "--install-root",
        default=str((Path.home() / ".aware-sdk" / "installs").resolve()),
    )
    activate_parser.add_argument("--receipt-path")

    rollback_parser = subparsers.add_parser(
        "rollback",
        help="Move one channel pointer back to a prior installed version.",
    )
    rollback_parser.add_argument("--channel", default=_DEFAULT_CHANNEL)
    rollback_parser.add_argument("--version")
    rollback_parser.add_argument(
        "--install-root",
        default=str((Path.home() / ".aware-sdk" / "installs").resolve()),
    )
    rollback_parser.add_argument("--receipt-path")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Run the current public proof validation rail and emit a validation pack.",
    )
    validate_parser.add_argument("--workspace-root", required=True)
    validate_parser.add_argument("--validation-root", required=True)
    validate_parser.add_argument(
        "--proof-rail",
        choices=tuple(_PUBLIC_PROOF_RAILS),
        help=(
            "Named public proof rail to validate. Defaults to compile-first; "
            "use workspace-first to exercise the Home workspace-facing rail."
        ),
    )
    validate_parser.add_argument(
        "--profile",
        help="Explicit proof profile path override for internal use. Do not combine with --proof-rail.",
    )
    validate_parser.add_argument("--install-receipt-path")
    validate_parser.add_argument("--target-repo-root")
    validate_parser.add_argument(
        "--sync-target-repo",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Sync the packaged proof into a target repo root before pack emission (default: on).",
    )
    validate_parser.add_argument("--operator")
    validate_parser.add_argument("--publication-id")
    validate_parser.add_argument("--consumer")
    validate_parser.add_argument("--release-track")
    validate_parser.add_argument(
        "--required-kernel-repo-root",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    validate_parser.add_argument(
        "--used-dev-uv-run",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    validate_parser.add_argument(
        "--repo-assisted",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    validate_parser.add_argument("--honesty-note", action="append", default=[])
    return parser


def _load_json_source(source: str) -> dict[str, object]:
    payload = _read_source_bytes(source)
    decoded = json.loads(payload.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError(
            f"Install-distribution source must decode to a JSON object: {source}"
        )
    return decoded


def _resolve_release_index_url(*, platform: str, authority_base_url: str | None) -> str:
    if authority_base_url:
        return _build_authority_index_url(
            authority_base_url=authority_base_url, platform=platform
        )
    return _build_authority_index_url(
        authority_base_url=_DEFAULT_AUTHORITY_BASE_URL,
        platform=platform,
    )


def _build_authority_index_url(*, authority_base_url: str, platform: str) -> str:
    return (
        authority_base_url.rstrip("/") + f"/bootstrap/aware-sdk/{platform}/index.json"
    )


def _resolve_install_entry(
    *,
    index_payload: dict[str, object],
    channel: str,
    platform: str,
    version: str | None,
) -> dict[str, object]:
    if version is None:
        authority_entry = _resolve_authority_head_entry(
            index_payload=index_payload,
            channel=channel,
            platform=platform,
        )
        if authority_entry is not None:
            return authority_entry

    entries = index_payload.get("entries")
    if not isinstance(entries, list):
        version_suffix = f" version={version}" if version is not None else ""
        raise ValueError(
            "Install-distribution payload is missing mirror-compatible "
            f"'entries' for channel={channel} platform={platform}{version_suffix}."
        )
    matches: list[dict[str, object]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("channel") != channel or entry.get("platform") != platform:
            continue
        if version is not None and entry.get("version") != version:
            continue
        matches.append(entry)
    if not matches:
        version_suffix = f" version={version}" if version is not None else ""
        raise ValueError(
            f"No install-distribution entry for channel={channel} platform={platform}{version_suffix}."
        )
    matches.sort(
        key=lambda item: (
            str(item.get("published_at", "")),
            str(item.get("version", "")),
        )
    )
    return matches[-1]


def _resolve_authority_head_entry(
    *,
    index_payload: dict[str, object],
    channel: str,
    platform: str,
) -> dict[str, object] | None:
    channel_heads = index_payload.get("channel_heads")
    revisions = index_payload.get("revisions")
    if not isinstance(channel_heads, list) or not isinstance(revisions, list):
        return None

    head = next(
        (
            item
            for item in channel_heads
            if isinstance(item, dict)
            and item.get("channel") == channel
            and item.get("platform") == platform
        ),
        None,
    )
    if head is None:
        return None
    revision_id = _required_str(head.get("revision_id"), "revision_id")
    revision = next(
        (
            item
            for item in revisions
            if isinstance(item, dict) and item.get("revision_id") == revision_id
        ),
        None,
    )
    if revision is None:
        raise ValueError(
            "Install-distribution authority payload references a missing "
            f"revision_id={revision_id!r} for channel={channel} platform={platform}."
        )
    return {
        "revision_id": revision_id,
        "channel": channel,
        "version": _required_str(head.get("version"), "version"),
        "platform": platform,
        "archive_url": _required_str(revision.get("archive_url"), "archive_url"),
        "archive_sha256": _required_str(
            revision.get("archive_sha256"), "archive_sha256"
        ),
        "installer_payload_url": _required_str(
            revision.get("installer_payload_url"),
            "installer_payload_url",
        ),
        "installer_payload_sha256": _optional_str(
            revision.get("installer_payload_sha256")
        ),
        "manifest_url": _optional_str(revision.get("manifest_url")),
        "capabilities": _string_list(revision.get("capabilities")),
        "bootstrap_kind": _required_str(
            revision.get("bootstrap_kind"), "bootstrap_kind"
        ),
        "published_at": _required_str(revision.get("published_at"), "published_at"),
    }


def _download_artifact(source: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(source)
    if parsed.scheme in ("", "file"):
        local_path = _local_source_path(source)
        shutil.copyfile(local_path, destination)
        return destination

    with urlopen(source) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    return destination


def _read_source_bytes(source: str) -> bytes:
    parsed = urlparse(source)
    if parsed.scheme in ("", "file"):
        return _local_source_path(source).read_bytes()
    with urlopen(source) as response:
        return response.read()


def _local_source_path(source: str) -> Path:
    parsed = urlparse(source)
    if parsed.scheme == "file":
        return Path(parsed.path).expanduser().resolve()
    return Path(source).expanduser().resolve()


def _download_name(source: str, *, default: str) -> str:
    parsed = urlparse(source)
    name = Path(parsed.path).name if parsed.path else ""
    return name or default


def _verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise ValueError(
            f"Checksum mismatch for {path}: expected {expected} got {actual}"
        )


def _invoke_installer_payload(
    *,
    bootstrap_python: str,
    installer_path: Path,
    archive_path: Path,
    install_root: Path,
    receipt_path: Path,
    force: bool,
    python_executable: str,
) -> dict[str, object]:
    command = [
        bootstrap_python,
        str(installer_path),
        "--archive",
        str(archive_path),
        "--install-root",
        str(install_root),
        "--receipt-path",
        str(receipt_path),
        "--python-executable",
        python_executable,
    ]
    if force:
        command.append("--force")
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Installer payload failed:\n"
            f"command: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Installer payload did not emit valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Installer payload did not emit a JSON object.")
    return payload


def _default_platform() -> str:
    if sys.platform != "linux":
        raise ValueError(
            "aware-sdk install currently defaults only Linux platforms; pass --platform explicitly."
        )
    machine = platform_lib.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "linux-x86_64"
    if machine in {"aarch64", "arm64"}:
        return "linux-arm64"
    raise ValueError(
        f"Unsupported Linux machine for default platform resolution: {machine}"
    )


def _resolve_receipt_path(value: str | None, *, prefix: str) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        Path.home() / ".aware-sdk" / "receipts" / f"{prefix}-{timestamp}.json"
    ).resolve()


def _safe_version(dist: str) -> str:
    try:
        return version(dist)
    except Exception:
        return "unknown"


def _required_str(value: object, field_name: str) -> str:
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"Install-distribution entry is missing non-empty '{field_name}'.")


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _sdk_root_from_install_root(install_root: Path) -> Path:
    return install_root.parent


def _installed_version_dir(*, install_root: Path, channel: str, version: str) -> Path:
    return install_root / channel / version


def _activate_channel(
    *,
    install_root: Path,
    channel: str,
    version: str,
    launcher_names: tuple[str, ...],
) -> dict[str, object]:
    sdk_root = _sdk_root_from_install_root(install_root)
    install_dir = _installed_version_dir(
        install_root=install_root, channel=channel, version=version
    )
    channel_link = sdk_root / "channels" / channel / "current"
    _replace_symlink(channel_link, install_dir)

    launchers: dict[str, dict[str, str]] = {}
    missing_launchers: list[str] = []
    for launcher_name in launcher_names:
        launcher_path = install_dir / "bin" / launcher_name
        if not launcher_path.exists():
            missing_launchers.append(launcher_name)
            continue
        bin_link = sdk_root / "bin" / launcher_name
        _replace_symlink(
            bin_link, channel_link.parent / "current" / "bin" / launcher_name
        )
        launchers[launcher_name] = {
            "launcher_link": str(bin_link),
            "launcher_target": str(
                channel_link.parent / "current" / "bin" / launcher_name
            ),
        }

    primary_launcher = launchers.get(_PRIMARY_LEGACY_LAUNCHER_NAME)
    if primary_launcher is None:
        raise FileNotFoundError(
            "Installed primary launcher not found for activation: "
            f"{install_dir / 'bin' / _PRIMARY_LEGACY_LAUNCHER_NAME}"
        )
    return {
        "channel": channel,
        "version": version,
        "installed_dir": str(install_dir),
        "activation": {
            "sdk_root": str(sdk_root),
            "channel_current_link": str(channel_link),
            "channel_current_target": str(install_dir),
            "launcher_link": primary_launcher["launcher_link"],
            "launcher_target": primary_launcher["launcher_target"],
            "launchers": launchers,
            "missing_launchers": missing_launchers,
        },
    }


def _resolve_current_activation(*, sdk_root: Path, channel: str) -> dict[str, str]:
    current_link = sdk_root / "channels" / channel / "current"
    if not current_link.exists():
        raise FileNotFoundError(
            f"Channel activation link does not exist: {current_link}"
        )
    resolved = current_link.resolve()
    return {
        "link": str(current_link),
        "target": str(resolved),
        "version": resolved.name,
    }


def _select_rollback_version(
    *,
    install_root: Path,
    channel: str,
    current_version: str,
) -> str:
    channel_root = install_root / channel
    if not channel_root.is_dir():
        raise FileNotFoundError(f"Installed channel root not found: {channel_root}")
    candidates = [
        path
        for path in channel_root.iterdir()
        if path.is_dir()
        and path.name != current_version
        and (path / "bin" / _PRIMARY_LEGACY_LAUNCHER_NAME).exists()
    ]
    if not candidates:
        raise ValueError(
            f"No prior installed versions available for rollback in channel '{channel}'."
        )
    candidates.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
    return candidates[0].name


def _replace_symlink(link_path: Path, target_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    relative_target = os.path.relpath(target_path, start=link_path.parent)
    temp_link = link_path.parent / f".{link_path.name}.tmp"
    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink()
    temp_link.symlink_to(relative_target)
    os.replace(temp_link, link_path)


def _write_receipt_and_stdout(
    *, payload: dict[str, object], receipt_path: Path
) -> None:
    full_payload = {**payload, "receipt_path": str(receipt_path)}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(full_payload, indent=2) + "\n", encoding="utf-8")
    json.dump(full_payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
