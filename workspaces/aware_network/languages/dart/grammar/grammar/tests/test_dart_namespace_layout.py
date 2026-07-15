from __future__ import annotations

from aware_code_ontology.code.code_enums import CodeLanguage
from dart_grammar.code_language_plugin import DartAwareModelsLayout


def test_dart_aware_models_layout_emits_namespace_groups() -> None:
    layout = DartAwareModelsLayout()

    groups = layout.extract_namespace_groups(
        [
            "languages/dart/namespaces/aware_models/lib/meta/class_/class.dart",
            "languages/dart/namespaces/aware_models/lib/meta/class_/class_mirror.dart",
        ],
        CodeLanguage.dart,
        enforce_namespace_layout=True,
    )

    by_name = {group.name: group for group in groups}
    meta = by_name["meta"]

    assert meta.path == "languages/dart/namespaces/aware_models/lib/meta"
    assert [(entry.name, entry.path) for entry in meta.entries] == [("class", "class_")]
