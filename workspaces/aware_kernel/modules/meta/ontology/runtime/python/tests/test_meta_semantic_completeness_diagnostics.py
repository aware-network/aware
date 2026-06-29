from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from aware_code.semantic_capability import SemanticAnalysisCapabilityRequest
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.semantic_diagnostics import collect_meta_completeness_diagnostics
from aware_meta.semantic_analysis import (
    analyze_meta_ocg_semantic_capability,
    analyze_meta_ocg_sources,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_aware_toml(root: Path) -> Path:
    toml_path = root / "aware.toml"
    _write(
        toml_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                "[build.namespace]",
                '"**/*.aware" = "default.demo"',
                "",
            ]
        ),
    )
    return toml_path


def _analyze_with_completeness(tmp_path: Path, source: str):
    manifest_path = _write_aware_toml(tmp_path)
    source_path = tmp_path / "aware" / "demo.aware"
    _write(source_path, source)
    return analyze_meta_ocg_sources(
        package_root=tmp_path,
        source_files=(Path("aware/demo.aware"),),
        manifest_path=manifest_path,
        completeness_diagnostics=True,
    )


def _diagnostic_codes(result: object) -> set[str]:
    return {diagnostic.code for diagnostic in getattr(result, "diagnostics")}


def test_meta_completeness_diagnostics_report_missing_constructor(
    tmp_path: Path,
) -> None:
    result = _analyze_with_completeness(
        tmp_path,
        """
class Room {
    name String
}

projection RoomProjection {
    root demo.Room
}
""".strip(),
    )

    assert "aware_meta.completeness.class_missing_constructor" in _diagnostic_codes(
        result
    )


def test_meta_completeness_diagnostics_report_missing_projection_membership(
    tmp_path: Path,
) -> None:
    result = _analyze_with_completeness(
        tmp_path,
        """
class Room {
    name String

    fn build construct() -> Room {
        \"\"\"Build a room.\"\"\"
    }
}
""".strip(),
    )

    codes = _diagnostic_codes(result)
    assert "aware_meta.completeness.projection_membership_missing" in codes
    assert "aware_meta.completeness.constructor_projection_unreachable" in codes


def test_meta_completeness_diagnostics_report_unreachable_projection_node(
    tmp_path: Path,
) -> None:
    result = _analyze_with_completeness(
        tmp_path,
        """
class Parent {
    child Child

    fn build construct() -> Parent {
        \"\"\"Build a parent.\"\"\"
    }
}

class Child {
    name String

    fn build construct() -> Child {
        \"\"\"Build a child.\"\"\"
    }
}

projection BrokenProjection {
    root demo.Child
    demo.Parent::child
}
""".strip(),
    )

    codes = _diagnostic_codes(result)
    assert "aware_meta.completeness.projection_node_unreachable" in codes
    assert "aware_meta.completeness.constructor_projection_unreachable" in codes


def test_meta_completeness_diagnostics_report_missing_constructor_path(
    tmp_path: Path,
) -> None:
    result = _analyze_with_completeness(
        tmp_path,
        """
class Parent {
    child Child

    fn build construct() -> Parent {
        \"\"\"Build a parent without materializing its child.\"\"\"
    }
}

class Child {
    name String key

    fn build construct(name String key) -> Child {
        \"\"\"Build a child.\"\"\"
    }
}

projection ParentProjection {
    root demo.Parent
    demo.Parent::child
}
""".strip(),
    )

    codes = _diagnostic_codes(result)
    assert "aware_meta.completeness.constructor_path_missing" in codes


def test_meta_completeness_diagnostics_accept_direct_constructor_path(
    tmp_path: Path,
) -> None:
    result = _analyze_with_completeness(
        tmp_path,
        """
class Parent {
    child Child

    fn build construct(child_name String key = "child") -> Parent {
        \"\"\"Build a parent and materialize its child.\"\"\"
        let created_child = construct Child(name = child_name)
    }
}

class Child {
    name String key

    fn build construct(name String key) -> Child {
        \"\"\"Build a child.\"\"\"
    }
}

projection ParentProjection {
    root demo.Parent
    demo.Parent::child
}
""".strip(),
    )

    assert "aware_meta.completeness.constructor_path_missing" not in _diagnostic_codes(
        result
    )


def test_meta_completeness_diagnostics_report_native_instance_function_without_impl() -> (
    None
):
    class_config = ClassConfig(
        class_fqn="aware_demo.default.demo.Room",
        name="Room",
    )
    constructor = FunctionConfig(
        owner_key=class_config.class_fqn,
        name="build",
        kind=FunctionKind.instance,
    )
    instance_function = FunctionConfig(
        owner_key=class_config.class_fqn,
        name="rename",
        kind=FunctionKind.instance,
    )
    class_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=class_config.id,
            function_config=constructor,
            function_config_id=constructor.id,
            is_constructor=True,
        ),
        ClassConfigFunctionConfig(
            class_config_id=class_config.id,
            function_config=instance_function,
            function_config_id=instance_function.id,
            is_constructor=False,
        ),
    ]
    graph = ObjectConfigGraph(
        name="aware_demo",
        hash="sha256:test",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=uuid4(),
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_config.class_fqn,
                class_config=class_config,
            )
        ],
    )

    diagnostics = collect_meta_completeness_diagnostics(
        source_graph=graph,
        runtime_derivation=SimpleNamespace(
            runtime_graph=graph,
            runtime_external_graphs=(),
        ),
        native_function_impl_required=True,
        native_function_impl_severity="error",
    )

    native_diagnostics = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.code == "aware_meta.completeness.native_function_impl_missing"
    ]
    assert len(native_diagnostics) == 1
    assert native_diagnostics[0].severity == "error"
    assert "Room.rename" in native_diagnostics[0].message


def test_meta_completeness_diagnostics_flow_through_semantic_capability(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "demo.aware",
        """
class Room {
    name String
}

projection RoomProjection {
    root demo.Room
}
""".strip(),
    )

    result = analyze_meta_ocg_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("aware/demo.aware"),),
            manifest_path=manifest_path,
            metadata={"meta_completeness_diagnostics": True},
        )
    )

    assert result.diagnostics
    assert {diagnostic.code for diagnostic in result.diagnostics} == {
        "aware_meta.completeness.class_missing_constructor"
    }
