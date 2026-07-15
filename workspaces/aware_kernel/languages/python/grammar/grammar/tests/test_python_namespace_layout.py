from __future__ import annotations

from aware_code_ontology.code.code_enums import CodeLanguage
from python_grammar.layout_plugin import PythonCodeLanguagePluginLayout


def test_python_layout_emits_namespace_groups_for_package_layout() -> None:
    layout = PythonCodeLanguagePluginLayout()

    groups = layout.extract_namespace_groups(
        [
            "python/namespaces/identity/aware_identity/class_/model.py",
            "python/namespaces/identity/aware_identity/class_/service.py",
        ],
        CodeLanguage.python,
        enforce_namespace_layout=True,
    )

    by_name = {group.name: group for group in groups}
    identity = by_name["identity"]

    assert identity.path == "python/namespaces/identity"
    assert [(entry.name, entry.path) for entry in identity.entries] == [
        ("class", "aware_identity/class_")
    ]
