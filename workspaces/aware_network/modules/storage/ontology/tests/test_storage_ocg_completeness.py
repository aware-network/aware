from __future__ import annotations

from pathlib import Path
import sys

import pytest
from aware_meta_sdk import (
    FunctionCoverageSkip,
    ProjectionBehaviorProof,
    ProjectionProof,
)

_MODULES_ROOT = Path(__file__).resolve().parents[3]
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from kernel_ocg_completeness_support import (  # noqa: E402
    prove_kernel_module_ontology,
)


@pytest.mark.asyncio
async def test_storage_ocg_completeness_has_no_diagnostics() -> None:
    proof = await prove_kernel_module_ontology(
        "storage",
        projection_proofs=(ProjectionProof("StorageBlob"),),
        behavior_proofs=(
            ProjectionBehaviorProof(
                projection_name="StorageBlob",
                expected_skips=(
                    FunctionCoverageSkip(
                        "StorageBlob.create",
                        (
                            "covered by the receipt-gated workspace local "
                            "native behavior proof"
                        ),
                    ),
                ),
            ),
        ),
    )

    proof.assert_complete()
    report = proof.report
    assert report.status == "passed"
    assert report.behavior_reports[0].skipped_function_keys == (
        "StorageBlob.create",
    )
    assert proof.package_name == "storage-ontology"
