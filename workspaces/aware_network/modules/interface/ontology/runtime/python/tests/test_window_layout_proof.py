from __future__ import annotations

from pathlib import Path

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    class_config_by_fqn,
    class_function_names,
    isolated_meta_aware_root,
    projection_by_name,
)
from _interface_runtime_test_paths import REPO_ROOT


def test_interface_layout_runtime_is_retired_or_removed(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        interface_layout = class_config_by_fqn(
            runtime,
            "aware_interface_ontology.window.layout.Layout",
        )
        attention_layout = class_config_by_fqn(
            runtime,
            "aware_attention.layout.Layout",
        )

        assert interface_layout is None
        assert attention_layout is not None
        assert "build" in class_function_names(attention_layout)
        assert projection_by_name(runtime, "Layout") is not None
