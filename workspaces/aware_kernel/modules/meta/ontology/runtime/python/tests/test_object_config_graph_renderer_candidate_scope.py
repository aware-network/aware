from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.section.writer import CodeSectionWriter
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer import ObjectConfigGraphRenderer
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    build_renderer_empty_code,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)


class _CandidateScopeLayout(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("models") / f"{class_config.name}.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return Path("enums") / f"{enum_config.name}.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return Path("functions") / f"{function_config.name}.py"

    def get_file_extension(self) -> str:
        return ".py"


class _ExtraOutputOnlyLayout(_CandidateScopeLayout):
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        raise AssertionError("extra-output-only render should not group class files")

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        _ = enum_config
        raise AssertionError("extra-output-only render should not group enum files")

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        raise AssertionError("extra-output-only render should not group function files")


class _CandidateScopeRendererLanguage(ObjectConfigGraphRendererLanguage):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self.emit_calls: list[tuple[str, ...]] = []

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    def indent(self) -> int:
        return 4

    @property
    def comment_prefix(self) -> str:
        return "#"

    def define_assemblers(self) -> None:
        return None

    def extra_output_paths(self) -> list[Path]:
        return [Path("index.py")]

    def create_empty_code(self):
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key="candidate_scope_test",
        )

    def emit_file(
        self,
        meta_objects: list[Any],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = (
            schema,
            class_to_class_config_map,
            base_class_module,
            base_class_name,
        )
        names = tuple(getattr(item, "name", "extra") for item in meta_objects)
        self.emit_calls.append(names)
        writer.token(f"# rendered {','.join(names) if names else 'extra'}\n")


class _ExtraOutputOnlyRendererLanguage(_CandidateScopeRendererLanguage):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self.requires_metadata_hydration = True

    def renders_only_extra_output_paths(self) -> bool:
        return True

    def requires_graph_metadata_hydration(self) -> bool:
        return self.requires_metadata_hydration


def _renderer(output_dir: Path) -> tuple[
    ObjectConfigGraphRenderer,
    _CandidateScopeRendererLanguage,
]:
    language = _CandidateScopeRendererLanguage(_CandidateScopeLayout(output_dir))
    return (
        ObjectConfigGraphRenderer(
            renderer_language=language,
            output_directory=output_dir,
        ),
        language,
    )


def _extra_output_only_renderer(output_dir: Path) -> tuple[
    ObjectConfigGraphRenderer,
    _ExtraOutputOnlyRendererLanguage,
]:
    language = _ExtraOutputOnlyRendererLanguage(_ExtraOutputOnlyLayout(output_dir))
    return (
        ObjectConfigGraphRenderer(
            renderer_language=language,
            output_directory=output_dir,
        ),
        language,
    )


def _graph() -> ObjectConfigGraph:
    graph_id = uuid4()
    alpha = ClassConfig(
        class_fqn="demo.Alpha",
        name="Alpha",
        is_base=True,
        class_config_attribute_configs=[],
    )
    beta = ClassConfig(
        class_fqn="demo.Beta",
        name="Beta",
        is_base=True,
        class_config_attribute_configs=[],
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="candidate_scope_demo",
        hash="sha256:candidate_scope_demo",
        fqn_prefix="demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=alpha.class_fqn,
                object_config_graph_id=graph_id,
                class_config=alpha,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=beta.class_fqn,
                object_config_graph_id=graph_id,
                class_config=beta,
            ),
        ],
    )


def test_renderer_candidate_scope_prunes_non_candidate_class_files(
    tmp_path: Path,
) -> None:
    renderer, language = _renderer(tmp_path)

    written = renderer.render_graph(
        _graph(),
        candidate_paths=(Path("models/Alpha.py"),),
    )

    assert written == [tmp_path / "models" / "Alpha.py"]
    assert (tmp_path / "models" / "Alpha.py").read_text(encoding="utf-8") == (
        "# rendered Alpha\n"
    )
    assert not (tmp_path / "models" / "Beta.py").exists()
    assert not (tmp_path / "index.py").exists()
    assert language.emit_calls == [("Alpha",)]


def test_renderer_candidate_scope_accepts_absolute_extra_output_path(
    tmp_path: Path,
) -> None:
    renderer, language = _renderer(tmp_path)

    written = renderer.render_graph(
        _graph(),
        candidate_paths=(tmp_path / "index.py",),
    )

    assert written == [tmp_path / "index.py"]
    assert (tmp_path / "index.py").read_text(encoding="utf-8") == ("# rendered extra\n")
    assert not (tmp_path / "models" / "Alpha.py").exists()
    assert not (tmp_path / "models" / "Beta.py").exists()
    assert language.emit_calls == [()]


def test_renderer_without_candidate_scope_preserves_full_render(
    tmp_path: Path,
) -> None:
    renderer, language = _renderer(tmp_path)

    written = renderer.render_graph(_graph())

    assert written == [
        tmp_path / "models" / "Alpha.py",
        tmp_path / "models" / "Beta.py",
        tmp_path / "index.py",
    ]
    assert (tmp_path / "models" / "Alpha.py").exists()
    assert (tmp_path / "models" / "Beta.py").exists()
    assert (tmp_path / "index.py").exists()
    assert language.emit_calls == [("Alpha",), ("Beta",), ()]


def test_renderer_reports_internal_phase_timings(
    tmp_path: Path,
) -> None:
    renderer, _ = _renderer(tmp_path)

    renderer.render_graph(_graph())

    timings = renderer.get_render_phase_timings()
    assert timings["total"] >= 0.0
    assert timings["layout_bind_graph"] >= 0.0
    assert timings["bind_object_config_graph"] >= 0.0
    assert timings["candidate_scope"] >= 0.0
    assert timings["collect_render_results"] >= 0.0
    assert timings["collect.group_objects_by_file"] >= 0.0
    assert timings["collect.emit_files"] >= 0.0
    assert timings["collect.total"] >= 0.0
    assert timings["write_render_results"] >= 0.0
    assert timings["log_written_files"] >= 0.0


def test_renderer_extra_output_only_skips_node_file_grouping(
    tmp_path: Path,
) -> None:
    renderer, language = _extra_output_only_renderer(tmp_path)

    written = renderer.render_graph(_graph())

    assert written == [tmp_path / "index.py"]
    assert (tmp_path / "index.py").read_text(encoding="utf-8") == ("# rendered extra\n")
    assert not (tmp_path / "models" / "Alpha.py").exists()
    assert not (tmp_path / "models" / "Beta.py").exists()
    assert language.emit_calls == [()]


def test_renderer_extra_output_only_honors_candidate_scope(
    tmp_path: Path,
) -> None:
    renderer, language = _extra_output_only_renderer(tmp_path)

    written = renderer.render_graph(
        _graph(),
        candidate_paths=(Path("models/Alpha.py"),),
    )

    assert written == []
    assert not (tmp_path / "index.py").exists()
    assert language.emit_calls == []


def test_renderer_extra_output_only_can_skip_graph_metadata_hydration(
    tmp_path: Path,
) -> None:
    renderer, language = _extra_output_only_renderer(tmp_path)
    language.requires_metadata_hydration = False

    def _fail_hydration(graph: ObjectConfigGraph) -> None:
        _ = graph
        raise AssertionError("metadata hydration should be skipped")

    renderer._hydrate_graph_metadata = _fail_hydration

    written = renderer.render_graph(_graph())

    assert written == [tmp_path / "index.py"]
    assert (tmp_path / "index.py").read_text(encoding="utf-8") == ("# rendered extra\n")
    assert language.emit_calls == [()]
