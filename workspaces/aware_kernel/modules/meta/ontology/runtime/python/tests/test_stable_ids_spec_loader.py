from __future__ import annotations

from pathlib import Path

from aware_meta.graph.config.stable_ids_spec.loader import (
    load_stable_ids_spec_from_toml_text,
)


def test_stable_ids_spec_loader_parses_minimal_contract() -> None:
    spec = load_stable_ids_spec_from_toml_text(
        toml_text=(
            "version = 1\n"
            "\n"
            "[[namespaces]]\n"
            'name = "NS_TEST"\n'
            'kind = "ns_url"\n'
            'value = "aware://test/v1"\n'
            "\n"
            "[[functions]]\n"
            'name = "stable_demo_id"\n'
            'namespace = "NS_TEST"\n'
            'template = "aware:demo:{key_norm}"\n'
            "\n"
            "[[functions.params]]\n"
            'name = "key"\n'
            'type = "str"\n'
            "\n"
            "[[functions.lets]]\n"
            'op = "normalize"\n'
            'name = "key_norm"\n'
            'param = "key"\n'
            'normalize = ["casefold", "strip"]\n'
        ),
        source_label="<test>",
    )

    assert spec.version == 1
    assert len(spec.namespaces) == 1
    assert spec.namespaces[0].name == "NS_TEST"
    assert len(spec.functions) == 1
    assert spec.functions[0].name == "stable_demo_id"


def test_stable_ids_spec_loading_moved_out_of_renderer_module() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    renderer_path = (
        repo_root
        / "modules"
        / "meta"
        / "runtime"
        / "aware_meta"
        / "graph"
        / "config"
        / "render"
        / "stable_ids_codegen.py"
    )
    renderer_source = renderer_path.read_text(encoding="utf-8")
    assert "def _load_spec_from_raw" not in renderer_source
