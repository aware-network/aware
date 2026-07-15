from __future__ import annotations

from pathlib import Path
import sys

_TEST_ROOT = Path(__file__).resolve().parent
_TEST_ROOT_STR = str(_TEST_ROOT)
if _TEST_ROOT_STR not in sys.path:
    sys.path.insert(0, _TEST_ROOT_STR)

from test_interface_compile_entrypoint import (  # noqa: E402
    _build_projection_identity_ocg,
    _write_interface_source,
    _write_interface_toml_with_dependencies,
    _write_pane_package,
    _write_workspace_truth,
    compile_interface_workspace,
)


def _write_module_local_meta_render_component_package(root: Path) -> None:
    component_root = (
        root
        / "modules"
        / "meta"
        / "interfaces"
        / "render_components"
        / "aware_meta_graph_render_components"
    )
    component_root.mkdir(parents=True, exist_ok=True)
    _ = (component_root / "aware.render_component.toml").write_text(
        "\n".join(
            [
                "aware_render_component = 1",
                "",
                "[render_component]",
                'package_name = "aware-meta-graph-render-components"',
                'fqn_prefix = "aware_meta_graph_render_components"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                "",
                "[dart]",
                'package_path = "dart/aware_meta_graph_render_components"',
                'package_name = "aware_meta_graph_render_components"',
                "",
                "[dart.flutter]",
                (
                    'library = "package:aware_meta_graph_render_components/'
                    'aware_meta_graph_render_components.dart"'
                ),
                'symbol = "registerRenderComponents"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_compile_interface_workspace_resolves_module_local_render_component_registrars(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(
            ("home-story-experience", "experience_package"),
            (
                "aware-meta-graph-render-components",
                "render_component_package",
            ),
        ),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    _write_module_local_meta_render_component_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.dart_registrar_bundle_artifact is not None
    dart_payload = result.dart_registrar_bundle_artifact.path.read_text(
        encoding="utf-8"
    )
    assert (
        "package:aware_meta_graph_render_components/"
        "aware_meta_graph_render_components.dart" in dart_payload
    )
    assert (
        "void registerRenderComponents(RenderComponentRegistryBuilder registry)"
        in dart_payload
    )
    assert ".registerRenderComponents(registry);" in dart_payload
    assert (
        "final renderComponentRegistryBuilder = RenderComponentRegistryBuilder();"
        in dart_payload
    )
    assert "registerRenderComponents(renderComponentRegistryBuilder);" in dart_payload
    assert (
        "renderComponentRegistry: renderComponentRegistryBuilder.build(),"
        in dart_payload
    )
