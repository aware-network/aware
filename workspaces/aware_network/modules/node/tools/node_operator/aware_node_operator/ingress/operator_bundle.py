from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID


PUBLIC_INGRESS_OPERATOR_BUNDLE_VERSION = "aware.node.public_ingress.operator_bundle.v1"
PUBLIC_INGRESS_OPERATOR_RECEIPT_VERSION = (
    "aware.node.public_ingress.operator_receipt.v1"
)
DEFAULT_SITE_DOMAIN = "node.aware.run"
DEFAULT_WEBHOOK_PATH = "/webhook/stripe/wallet-funding"
DEFAULT_WEBHOOK_BIND_HOST = "127.0.0.1"
DEFAULT_WEBHOOK_BIND_PORT = 18080
DEFAULT_ENVIRONMENT_API_HOST = "127.0.0.1"
DEFAULT_ENVIRONMENT_API_PORT = 8445
DEFAULT_REPO_ROOT = Path("/opt/aware")
DEFAULT_WEBHOOK_SERVICE_NAME = "aware-stripe-wallet-funding-webhook.service"
DEFAULT_ECONOMY_SERVICE_HOST_SOCKET_PATH = Path(
    "/opt/aware/.aware/service-host/runs/aware-economy-service-latest/service.sock"
)
DEFAULT_PROVIDER_SERVICE_HOST_SOCKET_PATH = Path(
    "/opt/aware/.aware/service-host/runs/"
    "aware-external-capital-provider-service-latest/service.sock"
)
DEFAULT_PROVIDER_RUNTIME_VALUES_DIR = Path("/run/aware/secrets")
DEFAULT_CADDYFILE_PATH = Path("/etc/caddy/Caddyfile")
DEFAULT_SYSTEMD_UNIT_PATH = Path("/etc/systemd/system") / DEFAULT_WEBHOOK_SERVICE_NAME
DEFAULT_SECRET_ENV_FILES = (
    Path("/opt/aware/secrets/environment-node.env"),
    Path("/opt/aware/secrets/stripe-wallet-funding-webhook.env"),
)
WEBHOOK_PYTHONPATH_ROOTS = (
    "workspaces/aware_network/modules/economy/providers/economy",
    "workspaces/aware_network/modules/economy/sdks/economy/python/public",
    "workspaces/aware_network/modules/economy/apis/economy/python/aware_economy_service_api",
    "workspaces/aware_network/modules/economy/apis/economy/python/aware_economy_service_dto",
    "workspaces/aware_network/modules/service/ontology/runtime/python",
    "workspaces/aware_network/modules/service/apis/service/python/aware_service_service_dto",
    "workspaces/aware_network/modules/network/apis/network/python/aware_network_service_dto",
    "workspaces/aware_network/libs/comms/python",
    "workspaces/aware_kernel/modules/api/libs/api/python",
    "workspaces/aware_kernel/modules/api/apis/api/python/aware_api_service_dto",
    "workspaces/aware_kernel/modules/code/ontology/runtime/python",
    "workspaces/aware_kernel/libs/types/python",
)
SUPPORTED_STRIPE_WALLET_FUNDING_EVENT_TYPES = (
    "payment_intent.succeeded",
    "checkout.session.expired",
    "refund.created",
    "refund.updated",
    "charge.dispute.created",
    "charge.dispute.closed",
)
PROVIDER_SECRET_KEY_NAME = "AWARE_STRIPE_WALLET_FUNDING_SECRET_KEY"
PROVIDER_SUCCESS_URL_NAME = "AWARE_STRIPE_WALLET_FUNDING_SUCCESS_URL"
PROVIDER_CANCEL_URL_NAME = "AWARE_STRIPE_WALLET_FUNDING_CANCEL_URL"
WEBHOOK_SECRET_NAME = "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_SECRET"
WEBHOOK_PROVIDER_IDENTITY_ID_NAME = "AWARE_STRIPE_WALLET_FUNDING_PROVIDER_IDENTITY_ID"


@dataclass(frozen=True, slots=True)
class PublicIngressOperatorBundleRequest:
    run_dir: Path
    repo_root: Path = DEFAULT_REPO_ROOT
    site_domain: str = DEFAULT_SITE_DOMAIN
    webhook_path: str = DEFAULT_WEBHOOK_PATH
    webhook_bind_host: str = DEFAULT_WEBHOOK_BIND_HOST
    webhook_bind_port: int = DEFAULT_WEBHOOK_BIND_PORT
    environment_api_host: str = DEFAULT_ENVIRONMENT_API_HOST
    environment_api_port: int = DEFAULT_ENVIRONMENT_API_PORT
    webhook_service_name: str = DEFAULT_WEBHOOK_SERVICE_NAME
    economy_service_host_socket_path: Path = DEFAULT_ECONOMY_SERVICE_HOST_SOCKET_PATH
    provider_service_host_socket_path: Path = DEFAULT_PROVIDER_SERVICE_HOST_SOCKET_PATH
    provider_runtime_values_dir: Path = DEFAULT_PROVIDER_RUNTIME_VALUES_DIR
    caddyfile_apply_path: Path = DEFAULT_CADDYFILE_PATH
    systemd_unit_apply_path: Path = DEFAULT_SYSTEMD_UNIT_PATH
    python_bin: Path | None = None
    secret_env_files: tuple[Path, ...] = DEFAULT_SECRET_ENV_FILES
    public_url_scheme: str = "https"
    route_id: str = "stripe-wallet-funding-webhook"
    stripe_event_destination_attested: bool = False
    generated_at: str | None = None


@dataclass(frozen=True, slots=True)
class PublicIngressOperatorBundle:
    request: PublicIngressOperatorBundleRequest
    run_dir: Path
    route_manifest_path: Path
    caddyfile_path: Path
    systemd_unit_path: Path
    command_file_path: Path
    receipt_path: Path
    log_path: Path

    @property
    def public_url(self) -> str:
        return (
            f"{self.request.public_url_scheme}://"
            f"{self.request.site_domain}{self.request.webhook_path}"
        )

    @property
    def local_webhook_url(self) -> str:
        return (
            f"http://{self.request.webhook_bind_host}:"
            f"{self.request.webhook_bind_port}{self.request.webhook_path}"
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "version": PUBLIC_INGRESS_OPERATOR_BUNDLE_VERSION,
            "generated_at": _generated_at(self.request),
            "run_dir": self.run_dir.as_posix(),
            "route": {
                "boundary_role": "provider_sensor_ingress",
                "provider_key": "stripe",
                "route_id": self.request.route_id,
                "site_domain": self.request.site_domain,
                "path": self.request.webhook_path,
                "public_url": self.public_url,
                "upstream": (
                    f"http://{self.request.webhook_bind_host}:"
                    f"{self.request.webhook_bind_port}"
                ),
                "expected_unsigned_post_status": 400,
                "status_label": "route_mounted",
                "supported_event_types": list(
                    SUPPORTED_STRIPE_WALLET_FUNDING_EVENT_TYPES
                ),
            },
            "default_upstream": {
                "kind": "environment_api",
                "upstream": (
                    f"http://{self.request.environment_api_host}:"
                    f"{self.request.environment_api_port}"
                ),
                "health_url": (
                    f"http://{self.request.environment_api_host}:"
                    f"{self.request.environment_api_port}/health"
                ),
            },
            "ingress_process": {
                "process_id": self.request.webhook_service_name.removesuffix(
                    ".service"
                ),
                "systemd_service": self.request.webhook_service_name,
                "module": ("aware_economy_providers.stripe.wallet_funding_webhook_app"),
                "bind_host": self.request.webhook_bind_host,
                "bind_port": self.request.webhook_bind_port,
                "economy_record_operations": [
                    "record_verified_wallet_funding",
                    "record_provider_lifecycle_event",
                ],
                "required_env": [
                    WEBHOOK_SECRET_NAME,
                    "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PUBLIC_URL",
                    "AWARE_ECONOMY_SERVICE_HOST_SOCKET_PATH",
                    WEBHOOK_PROVIDER_IDENTITY_ID_NAME,
                ],
                "optional_env": [
                    "AWARE_ECONOMY_SERVICE_HOST_REQUEST_TIMEOUT_S",
                ],
            },
            "hosted_service_requirements": [
                {
                    "service_package": "aware-economy-service",
                    "role": "economy_graph_authority",
                    "socket_path": (
                        self.request.economy_service_host_socket_path.as_posix()
                    ),
                },
                {
                    "service_package": ("aware-external-capital-provider-service"),
                    "role": "external_capital_actuator",
                    "socket_path": (
                        self.request.provider_service_host_socket_path.as_posix()
                    ),
                },
            ],
            "provider_runtime_requirements": {
                "values_dir": self.request.provider_runtime_values_dir.as_posix(),
                "required_names": [
                    PROVIDER_SECRET_KEY_NAME,
                    PROVIDER_SUCCESS_URL_NAME,
                    PROVIDER_CANCEL_URL_NAME,
                ],
                "test_mode_only": True,
            },
            "operator_attestations": {
                "stripe_event_destination_exact": (
                    self.request.stripe_event_destination_attested
                ),
            },
            "files": {
                "route_manifest_path": self.route_manifest_path.as_posix(),
                "caddyfile_path": self.caddyfile_path.as_posix(),
                "caddyfile_apply_path": (self.request.caddyfile_apply_path.as_posix()),
                "systemd_unit_path": self.systemd_unit_path.as_posix(),
                "systemd_unit_apply_path": (
                    self.request.systemd_unit_apply_path.as_posix()
                ),
                "command_file_path": self.command_file_path.as_posix(),
                "receipt_path": self.receipt_path.as_posix(),
                "log_path": self.log_path.as_posix(),
                "secret_env_files": [
                    path.as_posix() for path in self.request.secret_env_files
                ],
            },
        }


@dataclass(frozen=True, slots=True)
class _CommandResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def to_payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "status": "passed" if self.returncode == 0 else "failed",
        }


@dataclass(frozen=True, slots=True)
class _PreflightRequirement:
    name: str
    status: str
    detail: str

    def to_payload(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
        }


def render_public_ingress_operator_bundle(
    request: PublicIngressOperatorBundleRequest,
) -> PublicIngressOperatorBundle:
    run_dir = request.run_dir.expanduser().resolve()
    route_manifest_path = run_dir / "route-manifest.json"
    caddyfile_path = run_dir / "caddy" / "Caddyfile"
    systemd_unit_path = run_dir / "systemd" / request.webhook_service_name
    command_file_path = run_dir / "commands" / "apply-public-ingress.sh"
    receipt_path = run_dir / "receipts" / "public-ingress-receipt.json"
    log_path = run_dir / "logs" / "public-ingress.log"
    bundle = PublicIngressOperatorBundle(
        request=request,
        run_dir=run_dir,
        route_manifest_path=route_manifest_path,
        caddyfile_path=caddyfile_path,
        systemd_unit_path=systemd_unit_path,
        command_file_path=command_file_path,
        receipt_path=receipt_path,
        log_path=log_path,
    )

    route_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    caddyfile_path.parent.mkdir(parents=True, exist_ok=True)
    systemd_unit_path.parent.mkdir(parents=True, exist_ok=True)
    command_file_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    route_manifest_path.write_text(
        json.dumps(bundle.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    caddyfile_path.write_text(_render_caddyfile(bundle), encoding="utf-8")
    systemd_unit_path.write_text(_render_systemd_unit(bundle), encoding="utf-8")
    command_file_path.write_text(_render_apply_command(bundle), encoding="utf-8")
    command_file_path.chmod(0o755)
    _write_receipt(
        bundle=bundle,
        status="rendered",
        commands=(),
        probes=(),
        notes=("render_only",),
    )
    return bundle


def apply_public_ingress_operator_bundle(
    request: PublicIngressOperatorBundleRequest,
    *,
    run_public_probe: bool = True,
    run_local_probe: bool = True,
) -> PublicIngressOperatorBundle:
    bundle = render_public_ingress_operator_bundle(request)
    requirements = _preflight_requirements(request)
    if any(requirement.status != "passed" for requirement in requirements):
        _write_receipt(
            bundle=bundle,
            status="blocked_preflight",
            commands=(),
            probes=(),
            notes=("no_host_mutation_performed",),
            requirements=requirements,
        )
        return bundle

    commands: list[_CommandResult] = []

    _copy_file(
        source=bundle.caddyfile_path,
        target=request.caddyfile_apply_path,
    )
    _copy_file(
        source=bundle.systemd_unit_path,
        target=request.systemd_unit_apply_path,
    )
    commands.append(
        _run_command("systemctl_daemon_reload", ("systemctl", "daemon-reload"))
    )
    commands.append(
        _run_command(
            "webhook_service_enable_now",
            ("systemctl", "enable", "--now", request.webhook_service_name),
        )
    )
    commands.append(
        _run_command(
            "caddy_validate",
            ("caddy", "validate", "--config", request.caddyfile_apply_path.as_posix()),
        )
    )
    commands.append(_run_command("caddy_reload", ("systemctl", "reload", "caddy")))

    probes: list[dict[str, object]] = []
    if run_local_probe:
        probes.append(
            _probe_post_status(
                name="local_unsigned_webhook_post",
                url=bundle.local_webhook_url,
                expected_status=400,
            )
        )
    if run_public_probe:
        probes.append(
            _probe_post_status(
                name="public_unsigned_webhook_post",
                url=bundle.public_url,
                expected_status=400,
            )
        )

    status = (
        "applied"
        if all(command.returncode == 0 for command in commands)
        and all(probe.get("status") == "passed" for probe in probes)
        else "failed"
    )
    _write_receipt(
        bundle=bundle,
        status=status,
        commands=tuple(commands),
        probes=tuple(probes),
        notes=("stripe_wallet_funding_economy_recording_required",),
        requirements=requirements,
    )
    return bundle


def preflight_public_ingress_operator_bundle(
    request: PublicIngressOperatorBundleRequest,
) -> PublicIngressOperatorBundle:
    bundle = render_public_ingress_operator_bundle(request)
    requirements = _preflight_requirements(request)
    status = (
        "preflight_ready"
        if all(requirement.status == "passed" for requirement in requirements)
        else "blocked_preflight"
    )
    _write_receipt(
        bundle=bundle,
        status=status,
        commands=(),
        probes=(),
        notes=("read_only_preflight",),
        requirements=requirements,
    )
    return bundle


def _preflight_requirements(
    request: PublicIngressOperatorBundleRequest,
) -> tuple[_PreflightRequirement, ...]:
    python_bin = request.python_bin or request.repo_root / ".venv" / "bin" / "python"
    requirements = [
        _path_requirement(
            name="repo_root",
            path=request.repo_root,
            expected_kind="directory",
        ),
        _path_requirement(
            name="python_runtime",
            path=python_bin,
            expected_kind="file",
        ),
        _path_requirement(
            name="economy_service_host_socket",
            path=request.economy_service_host_socket_path,
            expected_kind="socket",
        ),
        _path_requirement(
            name="external_capital_provider_service_host_socket",
            path=request.provider_service_host_socket_path,
            expected_kind="socket",
        ),
        _attestation_requirement(
            name="stripe_event_destination_exact_six",
            attested=request.stripe_event_destination_attested,
        ),
        _runtime_value_file_requirement(
            name="stripe_test_secret_key",
            path=request.provider_runtime_values_dir / PROVIDER_SECRET_KEY_NAME,
            validator=lambda value: value.startswith("sk_test_"),
            expected="scoped test-mode key file",
        ),
        _runtime_value_file_requirement(
            name="stripe_success_url",
            path=request.provider_runtime_values_dir / PROVIDER_SUCCESS_URL_NAME,
            validator=_is_https_url,
            expected="scoped HTTPS runtime-value file",
        ),
        _runtime_value_file_requirement(
            name="stripe_cancel_url",
            path=request.provider_runtime_values_dir / PROVIDER_CANCEL_URL_NAME,
            validator=_is_https_url,
            expected="scoped HTTPS runtime-value file",
        ),
        _environment_file_requirement(
            name="stripe_webhook_signing_secret",
            paths=request.secret_env_files,
            variable_name=WEBHOOK_SECRET_NAME,
            validator=lambda value: value.startswith("whsec_"),
            expected="webhook EnvironmentFile value",
        ),
        _environment_file_requirement(
            name="stripe_webhook_provider_identity_id",
            paths=request.secret_env_files,
            variable_name=WEBHOOK_PROVIDER_IDENTITY_ID_NAME,
            validator=_is_uuid,
            expected="provider Identity UUID",
        ),
    ]
    return tuple(requirements)


def _path_requirement(
    *,
    name: str,
    path: Path,
    expected_kind: str,
) -> _PreflightRequirement:
    resolved = path.expanduser().resolve()
    matches = {
        "directory": resolved.is_dir(),
        "file": resolved.is_file(),
        "socket": resolved.is_socket(),
    }[expected_kind]
    return _PreflightRequirement(
        name=name,
        status="passed" if matches else "blocked",
        detail=(
            f"{expected_kind}_ready" if matches else f"required_{expected_kind}_missing"
        ),
    )


def _attestation_requirement(
    *,
    name: str,
    attested: bool,
) -> _PreflightRequirement:
    return _PreflightRequirement(
        name=name,
        status="passed" if attested else "blocked",
        detail="operator_attested" if attested else "operator_attestation_required",
    )


def _runtime_value_file_requirement(
    *,
    name: str,
    path: Path,
    validator: Any,
    expected: str,
) -> _PreflightRequirement:
    value = _read_private_value_file(path)
    valid = value is not None and bool(validator(value))
    return _PreflightRequirement(
        name=name,
        status="passed" if valid else "blocked",
        detail=(
            "runtime_value_ready" if valid else f"required_{expected.replace(' ', '_')}"
        ),
    )


def _environment_file_requirement(
    *,
    name: str,
    paths: tuple[Path, ...],
    variable_name: str,
    validator: Any,
    expected: str,
) -> _PreflightRequirement:
    value = _environment_file_value(paths=paths, variable_name=variable_name)
    valid = value is not None and bool(validator(value))
    return _PreflightRequirement(
        name=name,
        status="passed" if valid else "blocked",
        detail=(
            "environment_value_ready"
            if valid
            else f"required_{expected.replace(' ', '_')}"
        ),
    )


def _read_private_value_file(path: Path) -> str | None:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        return None
    try:
        if resolved.stat().st_mode & 0o077:
            return None
        value = resolved.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _environment_file_value(
    *,
    paths: tuple[Path, ...],
    variable_name: str,
) -> str | None:
    for path in paths:
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            continue
        try:
            if resolved.stat().st_mode & 0o077:
                continue
            lines = resolved.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, raw_value = line.partition("=")
            if not separator or key.strip() != variable_name:
                continue
            value = raw_value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value or None
    return None


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def _generated_at(request: PublicIngressOperatorBundleRequest) -> str:
    return request.generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _render_caddyfile(bundle: PublicIngressOperatorBundle) -> str:
    request = bundle.request
    return "\n".join(
        (
            "# Generated by Aware Node public ingress operator bundle.",
            "# Do not hand-edit as deployment truth; update the operator route manifest.",
            f"{request.site_domain} {{",
            f"\thandle {request.webhook_path} {{",
            (
                "\t\treverse_proxy "
                f"{request.webhook_bind_host}:{request.webhook_bind_port}"
            ),
            "\t}",
            "",
            "\thandle {",
            (
                "\t\treverse_proxy "
                f"{request.environment_api_host}:{request.environment_api_port}"
            ),
            "\t}",
            "}",
            "",
        )
    )


def _render_systemd_unit(bundle: PublicIngressOperatorBundle) -> str:
    request = bundle.request
    repo_root = request.repo_root.expanduser().resolve()
    python_bin = request.python_bin or repo_root / ".venv" / "bin" / "python"
    economy_socket_path = (
        request.economy_service_host_socket_path.expanduser().resolve().as_posix()
    )
    env_files = [
        f"EnvironmentFile=-{path.expanduser().resolve().as_posix()}"
        for path in request.secret_env_files
    ]
    lines = [
        "# Generated by Aware Node public ingress operator bundle.",
        "[Unit]",
        "Description=Aware Stripe Wallet Funding webhook ingress",
        "Wants=network-online.target",
        "After=network-online.target",
        "",
        "[Service]",
        "Type=simple",
        f"WorkingDirectory={repo_root.as_posix()}",
        f"Environment=HOST={request.webhook_bind_host}",
        f"Environment=PORT={request.webhook_bind_port}",
        f"Environment=PYTHONPATH={':'.join(WEBHOOK_PYTHONPATH_ROOTS)}",
        f"Environment=AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PATH={request.webhook_path}",
        (
            "Environment=AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PUBLIC_URL="
            f"{bundle.public_url}"
        ),
        f"Environment=AWARE_ECONOMY_SERVICE_HOST_SOCKET_PATH={economy_socket_path}",
        *env_files,
        (
            "ExecStart="
            f"{python_bin.as_posix()} "
            "-m aware_economy_providers.stripe.wallet_funding_webhook_app"
        ),
        "Restart=on-failure",
        "RestartSec=5s",
        "",
        "[Install]",
        "WantedBy=multi-user.target",
        "",
    ]
    return "\n".join(lines)


def _render_apply_command(bundle: PublicIngressOperatorBundle) -> str:
    request = bundle.request
    return "\n".join(
        (
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
            'RUN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"',
            (
                "install -m 0644 "
                f'"$RUN_DIR/caddy/Caddyfile" '
                f"{_shell_quote(request.caddyfile_apply_path.as_posix())}"
            ),
            (
                "install -m 0644 "
                f'"$RUN_DIR/systemd/{request.webhook_service_name}" '
                f"{_shell_quote(request.systemd_unit_apply_path.as_posix())}"
            ),
            "systemctl daemon-reload",
            f"systemctl enable --now {_shell_quote(request.webhook_service_name)}",
            (
                "caddy validate --config "
                f"{_shell_quote(request.caddyfile_apply_path.as_posix())}"
            ),
            "systemctl reload caddy",
            ("curl -i -sS --max-time 10 -X POST " f"{_shell_quote(bundle.public_url)}"),
            "",
        )
    )


def _copy_file(*, source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(0o644)


def _run_command(name: str, command: tuple[str, ...]) -> _CommandResult:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )
    return _CommandResult(
        name=name,
        command=command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _probe_post_status(
    *,
    name: str,
    url: str,
    expected_status: int,
) -> dict[str, object]:
    request = Request(url, data=b"", method="POST")
    try:
        with urlopen(request, timeout=10) as response:
            status_code = int(response.status)
            body = response.read(2048).decode("utf-8", errors="replace")
    except HTTPError as exc:
        status_code = int(exc.code)
        body = exc.read(2048).decode("utf-8", errors="replace")
    except URLError as exc:
        return {
            "name": name,
            "url": url,
            "expected_status": expected_status,
            "status": "failed",
            "error": str(exc),
        }
    except Exception as exc:  # pragma: no cover - defensive operator receipt
        return {
            "name": name,
            "url": url,
            "expected_status": expected_status,
            "status": "failed",
            "error": str(exc),
        }
    return {
        "name": name,
        "url": url,
        "expected_status": expected_status,
        "status_code": status_code,
        "status": "passed" if status_code == expected_status else "failed",
        "body_preview": body[:500],
    }


def _write_receipt(
    *,
    bundle: PublicIngressOperatorBundle,
    status: str,
    commands: tuple[_CommandResult, ...],
    probes: tuple[dict[str, object], ...],
    notes: tuple[str, ...],
    requirements: tuple[_PreflightRequirement, ...] = (),
) -> None:
    payload = {
        "version": PUBLIC_INGRESS_OPERATOR_RECEIPT_VERSION,
        "status": status,
        "recorded_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "bundle": bundle.to_payload(),
        "commands": [command.to_payload() for command in commands],
        "probes": list(probes),
        "requirements": [requirement.to_payload() for requirement in requirements],
        "notes": list(notes),
    }
    bundle.receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render/apply the Aware public ingress operator bundle.",
    )
    parser.add_argument(
        "command",
        choices=("render", "preflight", "apply"),
        help=(
            "Render files, run read-only readiness preflight, or apply "
            "systemd/Caddy changes on this host."
        ),
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--repo-root", default=DEFAULT_REPO_ROOT.as_posix())
    parser.add_argument("--site-domain", default=DEFAULT_SITE_DOMAIN)
    parser.add_argument("--webhook-path", default=DEFAULT_WEBHOOK_PATH)
    parser.add_argument("--webhook-bind-host", default=DEFAULT_WEBHOOK_BIND_HOST)
    parser.add_argument(
        "--webhook-bind-port",
        type=int,
        default=DEFAULT_WEBHOOK_BIND_PORT,
    )
    parser.add_argument("--environment-api-host", default=DEFAULT_ENVIRONMENT_API_HOST)
    parser.add_argument(
        "--environment-api-port",
        type=int,
        default=DEFAULT_ENVIRONMENT_API_PORT,
    )
    parser.add_argument("--webhook-service-name", default=DEFAULT_WEBHOOK_SERVICE_NAME)
    parser.add_argument(
        "--economy-service-host-socket-path",
        default=DEFAULT_ECONOMY_SERVICE_HOST_SOCKET_PATH.as_posix(),
    )
    parser.add_argument(
        "--provider-service-host-socket-path",
        default=DEFAULT_PROVIDER_SERVICE_HOST_SOCKET_PATH.as_posix(),
    )
    parser.add_argument(
        "--provider-runtime-values-dir",
        default=DEFAULT_PROVIDER_RUNTIME_VALUES_DIR.as_posix(),
    )
    parser.add_argument(
        "--caddyfile-apply-path", default=DEFAULT_CADDYFILE_PATH.as_posix()
    )
    parser.add_argument(
        "--systemd-unit-apply-path",
        default=DEFAULT_SYSTEMD_UNIT_PATH.as_posix(),
    )
    parser.add_argument("--python-bin", default=None)
    parser.add_argument(
        "--secret-env-file",
        action="append",
        default=None,
        help="Repeatable EnvironmentFile path for the webhook systemd unit.",
    )
    parser.add_argument("--skip-public-probe", action="store_true")
    parser.add_argument("--skip-local-probe", action="store_true")
    parser.add_argument(
        "--stripe-event-destination-attested",
        action="store_true",
        help=(
            "Attest that Stripe selects exactly the six event types in the "
            "rendered route manifest."
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _request_from_args(args: argparse.Namespace) -> PublicIngressOperatorBundleRequest:
    secret_env_files = (
        tuple(Path(path) for path in args.secret_env_file)
        if args.secret_env_file
        else DEFAULT_SECRET_ENV_FILES
    )
    return PublicIngressOperatorBundleRequest(
        run_dir=Path(args.run_dir),
        repo_root=Path(args.repo_root),
        site_domain=args.site_domain,
        webhook_path=args.webhook_path,
        webhook_bind_host=args.webhook_bind_host,
        webhook_bind_port=args.webhook_bind_port,
        environment_api_host=args.environment_api_host,
        environment_api_port=args.environment_api_port,
        webhook_service_name=args.webhook_service_name,
        economy_service_host_socket_path=Path(args.economy_service_host_socket_path),
        provider_service_host_socket_path=Path(args.provider_service_host_socket_path),
        provider_runtime_values_dir=Path(args.provider_runtime_values_dir),
        caddyfile_apply_path=Path(args.caddyfile_apply_path),
        systemd_unit_apply_path=Path(args.systemd_unit_apply_path),
        python_bin=Path(args.python_bin) if args.python_bin else None,
        secret_env_files=secret_env_files,
        stripe_event_destination_attested=(args.stripe_event_destination_attested),
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    request = _request_from_args(args)
    if args.command == "apply":
        bundle = apply_public_ingress_operator_bundle(
            request,
            run_public_probe=not args.skip_public_probe,
            run_local_probe=not args.skip_local_probe,
        )
    elif args.command == "preflight":
        bundle = preflight_public_ingress_operator_bundle(request)
    else:
        bundle = render_public_ingress_operator_bundle(request)
    payload: dict[str, Any] = {
        "status": json.loads(bundle.receipt_path.read_text(encoding="utf-8"))["status"],
        "route_manifest_path": bundle.route_manifest_path.as_posix(),
        "receipt_path": bundle.receipt_path.as_posix(),
        "public_url": bundle.public_url,
        "local_webhook_url": bundle.local_webhook_url,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Public ingress bundle: {payload['status']}")
        print(f"Route manifest: {payload['route_manifest_path']}")
        print(f"Receipt: {payload['receipt_path']}")
        print(f"Public URL: {payload['public_url']}")
    return 0 if payload["status"] in {"rendered", "preflight_ready", "applied"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
