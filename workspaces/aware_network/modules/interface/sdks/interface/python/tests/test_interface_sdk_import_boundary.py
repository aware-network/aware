from __future__ import annotations

import subprocess
import sys
import textwrap


def test_interface_sdk_root_does_not_import_api_client_rails() -> None:
    script = textwrap.dedent(
        """
        import sys

        import aware_interface_sdk
        import aware_interface_sdk.attachment

        for module_name in (
            "aware_session",
            "aware_interface_sdk.client",
            "aware_interface_sdk.operation_catalog",
            "aware_interface_service_api.client",
        ):
            assert module_name not in sys.modules, module_name
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
