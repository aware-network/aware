from __future__ import annotations

import subprocess
import sys


def test_node_semantic_contract_import_does_not_bootstrap_ontology_runtime() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import aware_node.semantic_contract; "
            "assert 'aware_node_ontology' not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
