from __future__ import annotations

import json
from pathlib import Path
import socket
from uuid import uuid4

from aware_node_operator.ingress.operator_bundle import (
    PUBLIC_INGRESS_OPERATOR_BUNDLE_VERSION,
    PUBLIC_INGRESS_OPERATOR_RECEIPT_VERSION,
    PublicIngressOperatorBundleRequest,
    apply_public_ingress_operator_bundle,
    main,
    preflight_public_ingress_operator_bundle,
    render_public_ingress_operator_bundle,
)


def test_render_public_ingress_operator_bundle_writes_route_caddy_and_systemd(
    tmp_path: Path,
) -> None:
    bundle = render_public_ingress_operator_bundle(
        PublicIngressOperatorBundleRequest(
            run_dir=tmp_path / "operator-runs" / "public-ingress",
            repo_root=tmp_path / "aware",
            site_domain="node.aware.run",
            caddyfile_apply_path=tmp_path / "etc" / "caddy" / "Caddyfile",
            systemd_unit_apply_path=(
                tmp_path
                / "etc"
                / "systemd"
                / "system"
                / "aware-stripe-wallet-funding-webhook.service"
            ),
            economy_service_host_socket_path=tmp_path
            / "aware"
            / ".aware"
            / "service-host"
            / "runs"
            / "aware-economy-service-latest"
            / "service.sock",
            secret_env_files=(tmp_path / "secrets" / "stripe.env",),
            generated_at="2026-06-04T08:19:00Z",
        )
    )

    manifest = json.loads(bundle.route_manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == PUBLIC_INGRESS_OPERATOR_BUNDLE_VERSION
    assert manifest["generated_at"] == "2026-06-04T08:19:00Z"
    assert manifest["route"] == {
        "boundary_role": "provider_sensor_ingress",
        "expected_unsigned_post_status": 400,
        "path": "/webhook/stripe/wallet-funding",
        "provider_key": "stripe",
        "public_url": "https://node.aware.run/webhook/stripe/wallet-funding",
        "route_id": "stripe-wallet-funding-webhook",
        "site_domain": "node.aware.run",
        "status_label": "route_mounted",
        "supported_event_types": [
            "payment_intent.succeeded",
            "checkout.session.expired",
            "refund.created",
            "refund.updated",
            "charge.dispute.created",
            "charge.dispute.closed",
        ],
        "upstream": "http://127.0.0.1:18080",
    }
    assert manifest["default_upstream"]["upstream"] == "http://127.0.0.1:8445"
    assert manifest["ingress_process"]["systemd_service"] == (
        "aware-stripe-wallet-funding-webhook.service"
    )
    assert manifest["ingress_process"]["module"] == (
        "aware_economy_providers.stripe.wallet_funding_webhook_app"
    )
    assert manifest["ingress_process"]["economy_record_operations"] == [
        "record_verified_wallet_funding",
        "record_provider_lifecycle_event",
    ]
    assert manifest["ingress_process"]["required_env"] == [
        "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_SECRET",
        "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PUBLIC_URL",
        "AWARE_ECONOMY_SERVICE_HOST_SOCKET_PATH",
        "AWARE_STRIPE_WALLET_FUNDING_PROVIDER_IDENTITY_ID",
    ]
    assert [
        item["service_package"] for item in manifest["hosted_service_requirements"]
    ] == [
        "aware-economy-service",
        "aware-external-capital-provider-service",
    ]
    assert manifest["provider_runtime_requirements"]["test_mode_only"] is True

    caddyfile = bundle.caddyfile_path.read_text(encoding="utf-8")
    assert "node.aware.run {" in caddyfile
    assert "handle /webhook/stripe/wallet-funding {" in caddyfile
    assert "reverse_proxy 127.0.0.1:18080" in caddyfile
    assert "reverse_proxy 127.0.0.1:8445" in caddyfile

    systemd = bundle.systemd_unit_path.read_text(encoding="utf-8")
    assert "Description=Aware Stripe Wallet Funding webhook ingress" in systemd
    assert "Environment=HOST=127.0.0.1" in systemd
    assert "Environment=PORT=18080" in systemd
    assert (
        "Environment=AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PATH="
        "/webhook/stripe/wallet-funding"
    ) in systemd
    assert (
        "Environment=AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PUBLIC_URL="
        "https://node.aware.run/webhook/stripe/wallet-funding"
    ) in systemd
    assert (
        "Environment=AWARE_ECONOMY_SERVICE_HOST_SOCKET_PATH="
        f"{tmp_path}/aware/.aware/service-host/runs/"
        "aware-economy-service-latest/service.sock"
    ) in systemd
    assert "EnvironmentFile=-" in systemd
    assert "aware_economy_providers.stripe.wallet_funding_webhook_app" in systemd
    assert "stripe_service_contract_webhook_app" not in systemd

    command = bundle.command_file_path.read_text(encoding="utf-8")
    assert (
        "systemctl enable --now " "'aware-stripe-wallet-funding-webhook.service'"
    ) in command
    assert "caddy validate --config" in command
    assert "https://node.aware.run/webhook/stripe/wallet-funding" in command

    receipt = json.loads(bundle.receipt_path.read_text(encoding="utf-8"))
    assert receipt["version"] == PUBLIC_INGRESS_OPERATOR_RECEIPT_VERSION
    assert receipt["status"] == "rendered"
    assert receipt["notes"] == ["render_only"]


def test_public_ingress_operator_bundle_does_not_render_secret_values(
    tmp_path: Path,
) -> None:
    bundle = render_public_ingress_operator_bundle(
        PublicIngressOperatorBundleRequest(
            run_dir=tmp_path / "run",
            repo_root=tmp_path / "aware",
            secret_env_files=(tmp_path / "secrets" / "stripe.env",),
        )
    )

    rendered = "\n".join(
        (
            bundle.route_manifest_path.read_text(encoding="utf-8"),
            bundle.caddyfile_path.read_text(encoding="utf-8"),
            bundle.systemd_unit_path.read_text(encoding="utf-8"),
            bundle.command_file_path.read_text(encoding="utf-8"),
            bundle.receipt_path.read_text(encoding="utf-8"),
        )
    )

    assert "whsec_" not in rendered
    assert "sk_test" not in rendered
    assert "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_SECRET=" not in rendered
    assert "AWARE_STRIPE_SIGNING_SECRET" not in rendered
    assert "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_SECRET" in rendered
    assert "service-contract" not in rendered


def test_public_ingress_operator_bundle_cli_render(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    code = main(["render", "--run-dir", run_dir.as_posix(), "--json"])

    assert code == 0
    assert (run_dir / "route-manifest.json").is_file()
    assert (run_dir / "receipts" / "public-ingress-receipt.json").is_file()


def test_public_ingress_preflight_blocks_without_mutation_or_secret_output(
    tmp_path: Path,
) -> None:
    bundle = apply_public_ingress_operator_bundle(
        PublicIngressOperatorBundleRequest(
            run_dir=tmp_path / "run",
            repo_root=tmp_path / "missing-repo",
            caddyfile_apply_path=tmp_path / "etc" / "caddy" / "Caddyfile",
            systemd_unit_apply_path=tmp_path / "etc" / "systemd" / "webhook.service",
        ),
        run_public_probe=False,
        run_local_probe=False,
    )

    receipt = json.loads(bundle.receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "blocked_preflight"
    assert receipt["commands"] == []
    assert receipt["probes"] == []
    assert receipt["notes"] == ["no_host_mutation_performed"]
    assert not (tmp_path / "etc" / "caddy" / "Caddyfile").exists()
    assert not (tmp_path / "etc" / "systemd" / "webhook.service").exists()
    serialized = json.dumps(receipt, sort_keys=True)
    assert "sk_test_" not in serialized
    assert "whsec_" not in serialized


def test_public_ingress_preflight_ready_is_redacted(tmp_path: Path) -> None:
    repo_root = tmp_path / "aware"
    python_bin = repo_root / ".venv" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text("", encoding="utf-8")
    provider_values = tmp_path / "provider-values"
    provider_values.mkdir()
    private_values = {
        "AWARE_STRIPE_WALLET_FUNDING_SECRET_KEY": "sk_test_operator_value",
        "AWARE_STRIPE_WALLET_FUNDING_SUCCESS_URL": (
            "https://node.aware.run/wallet/funding/success"
        ),
        "AWARE_STRIPE_WALLET_FUNDING_CANCEL_URL": (
            "https://node.aware.run/wallet/funding/cancel"
        ),
    }
    for name, value in private_values.items():
        path = provider_values / name
        path.write_text(value + "\n", encoding="utf-8")
        path.chmod(0o600)
    webhook_env = tmp_path / "stripe-webhook.env"
    webhook_env.write_text(
        "\n".join(
            (
                "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_SECRET=whsec_operator_value",
                ("AWARE_STRIPE_WALLET_FUNDING_PROVIDER_IDENTITY_ID=" f"{uuid4()}"),
                "",
            )
        ),
        encoding="utf-8",
    )
    webhook_env.chmod(0o600)
    economy_socket_path = tmp_path / "economy.sock"
    provider_socket_path = tmp_path / "provider.sock"

    with (
        socket.socket(socket.AF_UNIX) as economy_socket,
        socket.socket(socket.AF_UNIX) as provider_socket,
    ):
        economy_socket.bind(economy_socket_path.as_posix())
        provider_socket.bind(provider_socket_path.as_posix())
        bundle = preflight_public_ingress_operator_bundle(
            PublicIngressOperatorBundleRequest(
                run_dir=tmp_path / "run",
                repo_root=repo_root,
                python_bin=python_bin,
                economy_service_host_socket_path=economy_socket_path,
                provider_service_host_socket_path=provider_socket_path,
                provider_runtime_values_dir=provider_values,
                secret_env_files=(webhook_env,),
                stripe_event_destination_attested=True,
            )
        )

    receipt = json.loads(bundle.receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "preflight_ready"
    assert all(item["status"] == "passed" for item in receipt["requirements"])
    serialized = json.dumps(receipt, sort_keys=True)
    assert "sk_test_operator_value" not in serialized
    assert "whsec_operator_value" not in serialized
    assert "checkout.stripe.com" not in serialized
