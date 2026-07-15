from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from aware_service_runtime.local_dev_service_host import (
    LOCAL_SERVICEHOST_BOOT_SOURCE_ARTIFACT_BOOTSTRAP,
    LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML,
    LOCAL_SERVICEHOST_BOOT_SOURCE_NONE,
    evaluate_local_servicehost_boot_policy,
)


def test_local_servicehost_boot_policy_blocks_sdk_default_boot() -> None:
    decision = evaluate_local_servicehost_boot_policy(service_name="workspace-sdk")

    assert decision.allowed is False
    assert decision.source == LOCAL_SERVICEHOST_BOOT_SOURCE_NONE
    assert decision.production_safe is True
    assert "SDK import and client construction must not start services" in str(
        decision.error
    )


def test_local_servicehost_boot_policy_allows_artifact_bootstrap(
    tmp_path: Path,
) -> None:
    bootstrap_config_path = tmp_path / "aware-service-host.bootstrap.toml"

    decision = evaluate_local_servicehost_boot_policy(
        service_name="interface",
        bootstrap_config_path=bootstrap_config_path,
    )

    assert decision.allowed is True
    assert decision.source == LOCAL_SERVICEHOST_BOOT_SOURCE_ARTIFACT_BOOTSTRAP
    assert decision.production_safe is True
    assert decision.bootstrap_config_path == bootstrap_config_path
    assert decision.to_evidence()["bootstrap_config_path"] == (
        bootstrap_config_path.as_posix()
    )


def test_local_servicehost_boot_policy_blocks_dev_tomls_without_opt_in(
    tmp_path: Path,
) -> None:
    implementation_toml_path = tmp_path / "services" / "aware.service.toml"

    decision = evaluate_local_servicehost_boot_policy(
        service_name="interface",
        implementation_toml_paths=(implementation_toml_path,),
    )

    assert decision.allowed is False
    assert (
        decision.source == LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML
    )
    assert decision.production_safe is True
    assert "dev-only" in str(decision.error)
    assert "explicit local-dev boot opt-in" in str(decision.error)


def test_local_servicehost_boot_policy_allows_explicit_dev_toml_boot(
    tmp_path: Path,
) -> None:
    implementation_toml_path = tmp_path / "services" / "aware.service.toml"

    decision = evaluate_local_servicehost_boot_policy(
        service_name="interface",
        implementation_toml_paths=(implementation_toml_path,),
        allow_dev_implementation_boot=True,
    )

    assert decision.allowed is True
    assert (
        decision.source == LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML
    )
    assert decision.production_safe is False
    assert decision.implementation_toml_paths == (implementation_toml_path,)
    assert decision.error is None


def test_local_dev_servicehost_policy_import_is_lightweight() -> None:
    script = (
        "import json\n"
        "import sys\n"
        "import aware_service_runtime.local_dev_service_host\n"
        "forbidden = [\n"
        "    name for name in sorted(sys.modules)\n"
        "    if name == 'aware_service_service'\n"
        "    or name.startswith('aware_service_service.')\n"
        "    or name == 'aware_runtime'\n"
        "    or name.startswith('aware_runtime.')\n"
        "    or name == 'aware_workspace_service'\n"
        "    or name.startswith('aware_workspace_service.')\n"
        "]\n"
        "print(json.dumps(forbidden))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=True,
        text=True,
    )

    assert json.loads(result.stdout) == []
