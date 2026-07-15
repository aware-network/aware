from __future__ import annotations

import json
from uuid import uuid4

from aware_hub_service_dto.hub.deployment_artifact_authority import (
    DeploymentArtifactLock,
    DeploymentArtifactProducerProvenance,
    DeploymentArtifactTarget,
    ResolveDeploymentArtifactResponse,
)
from aware_sdk import cli
from aware_sdk.commands import hub as hub_command

_HUB_ENV_NAMES = (
    "AWARE_HUB_API_ENDPOINT",
    "AWARE_API_ENDPOINT",
    "AWARE_ACTOR_ID",
    "AWARE_INTERFACE_ACTOR_ID",
    "AWARE_AUTH_TOKEN",
    "AWARE_APT_TOKEN",
    "AWARE_API_TOKEN",
)


def test_hub_status_reports_ready_env_config_without_secret(
    monkeypatch, capsys
) -> None:
    _clear_hub_env(monkeypatch)
    actor_id = uuid4()
    monkeypatch.setenv("AWARE_HUB_API_ENDPOINT", "https://hub.example")
    monkeypatch.setenv("AWARE_ACTOR_ID", str(actor_id))
    monkeypatch.setenv("AWARE_AUTH_TOKEN", "secret-token")

    exit_code = cli.main(["hub", "status"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "secret-token" not in captured.out
    payload = json.loads(captured.out)
    assert payload["hub"]["ready"] is True
    assert payload["hub"]["endpoint"] == "https://hub.example"
    assert payload["hub"]["endpoint_source"] == "env:AWARE_HUB_API_ENDPOINT"
    assert payload["hub"]["actor_id"] == str(actor_id)
    assert payload["hub"]["actor_id_source"] == "env:AWARE_ACTOR_ID"
    assert payload["hub"]["actor_id_valid"] is True
    assert payload["hub"]["session_token_present"] is True
    assert payload["hub"]["session_token_source"] == "env:AWARE_AUTH_TOKEN"
    assert payload["api_boundary"]["kind"] == "generated-api-client"
    assert payload["api_boundary"]["package"] == "aware_hub_service_api"
    assert payload["api_boundary"]["service_imports_allowed"] is False


def test_hub_status_prefers_flags_over_env(monkeypatch, capsys) -> None:
    _clear_hub_env(monkeypatch)
    actor_id = uuid4()
    monkeypatch.setenv("AWARE_HUB_API_ENDPOINT", "https://env-hub.example")
    monkeypatch.setenv("AWARE_ACTOR_ID", str(uuid4()))
    monkeypatch.setenv("AWARE_AUTH_TOKEN", "env-token")

    exit_code = cli.main(
        [
            "hub",
            "status",
            "--endpoint",
            "https://flag-hub.example",
            "--actor-id",
            str(actor_id),
            "--session-token",
            "flag-token",
            "--request-timeout",
            "2.5",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "flag-token" not in captured.out
    assert "env-token" not in captured.out
    payload = json.loads(captured.out)
    assert payload["hub"]["ready"] is True
    assert payload["hub"]["endpoint"] == "https://flag-hub.example"
    assert payload["hub"]["endpoint_source"] == "argument"
    assert payload["hub"]["actor_id"] == str(actor_id)
    assert payload["hub"]["actor_id_source"] == "argument"
    assert payload["hub"]["session_token_present"] is True
    assert payload["hub"]["session_token_source"] == "argument"
    assert payload["hub"]["request_timeout"] == 2.5


def test_hub_status_require_ready_fails_closed(monkeypatch, capsys) -> None:
    _clear_hub_env(monkeypatch)

    exit_code = cli.main(["hub", "status", "--require-ready"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["hub"]["ready"] is False
    assert payload["hub"]["endpoint"] is None
    assert payload["hub"]["actor_id"] is None
    assert any("--endpoint" in error for error in payload["hub"]["errors"])
    assert any("--actor-id" in error for error in payload["hub"]["errors"])


def test_hub_workspace_deployment_resolve_uses_generated_api_request(
    monkeypatch,
    capsys,
) -> None:
    _clear_hub_env(monkeypatch)
    actor_id = uuid4()
    observed = {}

    class FakeDeploymentArtifactClient:
        async def resolve(self, request):
            observed["request"] = request
            return ResolveDeploymentArtifactResponse(
                authority_source_url="file:///authority/workspace-deployment/index.json",
                artifact_family="workspace-deployment",
                artifact_key="workspace/home",
                channel="stable",
                revision_id="workspace-deployment:home:stable:abc123",
                payload_url="file:///authority/payloads/home.json",
                payload_sha256="00" * 32,
                selector_key="home-local",
                target_ref="node:local",
                producer=DeploymentArtifactProducerProvenance(
                    producer_kind="workspace",
                    producer_revision_id="workspace-revision:home:1",
                    source_revision_id="workspace-source:home:1",
                    source_revision_kind="workspace-revision",
                    materialization_ref="workspace-materialization:home:1",
                    build_ref="workspace-build:home:1",
                ),
                node_package_name="aware-node-local",
                artifact_lock=DeploymentArtifactLock(
                    artifact_key="workspace/home",
                    revision_id="workspace-deployment:home:stable:abc123",
                    payload_url="file:///authority/payloads/home.json",
                    payload_sha256="00" * 32,
                ),
                target=DeploymentArtifactTarget(
                    selector_key="home-local",
                    target_ref="node:local",
                    node_package_name="aware-node-local",
                ),
            )

    class FakeHubClient:
        def __init__(self) -> None:
            self.deployment_artifact = FakeDeploymentArtifactClient()

    class FakeAwareHubServiceApiClient:
        def __init__(self) -> None:
            self.hub = FakeHubClient()

    def fake_build_hub_api_client(**kwargs):
        observed["client_kwargs"] = kwargs
        return FakeAwareHubServiceApiClient()

    monkeypatch.setattr(hub_command, "_build_hub_api_client", fake_build_hub_api_client)

    exit_code = cli.main(
        [
            "hub",
            "workspace-deployment",
            "resolve",
            "--endpoint",
            "ws://hub.example",
            "--actor-id",
            str(actor_id),
            "--session-token",
            "token",
            "--artifact-key",
            "workspace/home",
            "--channel",
            "stable",
            "--authority-base-url",
            "file:///authority",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["artifact_family"] == "workspace-deployment"
    assert payload["artifact_key"] == "workspace/home"
    assert payload["revision_id"] == "workspace-deployment:home:stable:abc123"
    assert observed["client_kwargs"] == {
        "endpoint": "ws://hub.example",
        "actor_id": actor_id,
        "session_token": "token",
        "request_timeout": 10.0,
    }
    request = observed["request"]
    assert request.artifact_key == "workspace/home"
    assert request.channel == "stable"
    assert request.authority_base_url == "file:///authority"
    assert request.index_url is None


def test_hub_workspace_deployment_resolve_uses_env_client_config(
    monkeypatch,
    capsys,
) -> None:
    _clear_hub_env(monkeypatch)
    actor_id = uuid4()
    observed = {}
    monkeypatch.setenv("AWARE_API_ENDPOINT", "https://hub-env.example")
    monkeypatch.setenv("AWARE_INTERFACE_ACTOR_ID", str(actor_id))
    monkeypatch.setenv("AWARE_API_TOKEN", "env-api-token")

    class FakeDeploymentArtifactClient:
        async def resolve(self, request):
            observed["request"] = request
            return {
                "artifact_family": "workspace-deployment",
                "artifact_key": request.artifact_key,
                "channel": request.channel,
                "revision_id": "workspace-deployment:home:stable:def456",
            }

    class FakeHubClient:
        def __init__(self) -> None:
            self.deployment_artifact = FakeDeploymentArtifactClient()

    class FakeAwareHubServiceApiClient:
        def __init__(self) -> None:
            self.hub = FakeHubClient()

    def fake_build_hub_api_client(**kwargs):
        observed["client_kwargs"] = kwargs
        return FakeAwareHubServiceApiClient()

    monkeypatch.setattr(hub_command, "_build_hub_api_client", fake_build_hub_api_client)

    exit_code = cli.main(
        [
            "hub",
            "workspace-deployment",
            "resolve",
            "--artifact-key",
            "workspace/home",
            "--index-url",
            "file:///authority/workspace-deployment/index.json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["artifact_key"] == "workspace/home"
    assert payload["revision_id"] == "workspace-deployment:home:stable:def456"
    assert observed["client_kwargs"] == {
        "endpoint": "https://hub-env.example",
        "actor_id": actor_id,
        "session_token": "env-api-token",
        "request_timeout": 10.0,
    }
    request = observed["request"]
    assert request.index_url == "file:///authority/workspace-deployment/index.json"
    assert request.authority_base_url is None


def test_hub_workspace_deployment_resolve_requires_client_endpoint(
    monkeypatch,
    capsys,
) -> None:
    _clear_hub_env(monkeypatch)
    exit_code = cli.main(
        [
            "hub",
            "workspace-deployment",
            "resolve",
            "--actor-id",
            str(uuid4()),
            "--artifact-key",
            "workspace/home",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert (
        "--endpoint or set AWARE_HUB_API_ENDPOINT or AWARE_API_ENDPOINT" in captured.err
    )


def test_hub_workspace_deployment_resolve_requires_authority_selector(
    monkeypatch,
    capsys,
) -> None:
    _clear_hub_env(monkeypatch)
    observed = {"client_built": False}

    def fake_build_hub_api_client(**kwargs):
        observed["client_built"] = True
        raise AssertionError(
            "selector validation should run before API client creation"
        )

    monkeypatch.setattr(hub_command, "_build_hub_api_client", fake_build_hub_api_client)

    exit_code = cli.main(
        [
            "hub",
            "workspace-deployment",
            "resolve",
            "--endpoint",
            "https://hub.example",
            "--actor-id",
            str(uuid4()),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert observed["client_built"] is False
    assert "--index-url or both --authority-base-url and --artifact-key" in captured.err


def _clear_hub_env(monkeypatch) -> None:
    for name in _HUB_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
