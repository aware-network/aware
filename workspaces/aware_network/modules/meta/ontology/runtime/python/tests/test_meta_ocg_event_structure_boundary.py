from __future__ import annotations

from pathlib import Path


def _join(*parts: str) -> str:
    return "".join(parts)


_LEGACY_EVENT_TOKENS = (
    _join("object_config_graph_", "event_declarations"),
    _join("object_config_graph_", "event_binding"),
    _join("object_config_graph_", "event_declaration"),
    _join("ObjectConfigGraph", "EventBinding"),
    _join("ObjectConfigGraph", "EventDeclaration"),
    _join("aware_meta_ontology.", "graph.", "event"),
    _join("aware_meta_ontology_orm_models.", "graph.", "event"),
    _join("aware_meta_ontology_dto.", "graph.", "event"),
)


def _repo_path(relative_path: str) -> Path:
    return Path(relative_path)


def _python_sources(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(
        sorted(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    )


def _text_sources(root: Path, *patterns: str) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in root.rglob(pattern) if path.is_file())
    return tuple(sorted(dict.fromkeys(paths)))


def _assert_no_legacy_tokens(paths: tuple[Path, ...]) -> None:
    offenders: dict[str, list[str]] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        matches = [token for token in _LEGACY_EVENT_TOKENS if token in text]
        if matches:
            offenders[path.as_posix()] = matches
    assert offenders == {}


def test_meta_runtime_source_has_no_ocg_event_compatibility_rails() -> None:
    _assert_no_legacy_tokens(
        _python_sources(
            _repo_path(
                "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta"
            )
        )
    )


def test_meta_generated_outputs_have_no_ocg_event_ontology() -> None:
    generated_roots = (
        _repo_path(
            "workspaces/aware_kernel/modules/meta/ontology/structure/python/dto/aware_meta_ontology_dto"
        ),
        _repo_path(
            "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_models/aware_meta_ontology_orm_models"
        ),
        _repo_path(
            "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_runtime/aware_meta_ontology"
        ),
        _repo_path("workspaces/aware_kernel/modules/meta/ontology/structure/sql"),
    )
    paths: list[Path] = []
    for root in generated_roots:
        paths.extend(_text_sources(root, "*.py", "*.json", "*.sql"))

    _assert_no_legacy_tokens(tuple(paths))
