from __future__ import annotations

from pathlib import Path
import sys

import pytest

_MODULES_ROOT = Path(__file__).resolve().parents[3]
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from kernel_ocg_completeness_support import (  # noqa: E402
    analyze_kernel_module_ocg_completeness,
    assert_no_error_diagnostics,
)


@pytest.mark.asyncio
async def test_code_ocg_completeness_reports_warning_debt() -> None:
    response = await analyze_kernel_module_ocg_completeness("code")

    assert response.status == "succeeded"
    assert response.package_name == "code-ontology"
    assert_no_error_diagnostics(response)
