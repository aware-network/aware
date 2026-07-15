from __future__ import annotations

from aware_code.language.layout import DefaultCodeLanguagePluginLayout
from aware_code_ontology.code.code_enums import CodeLanguage


def test_default_layout_emits_namespace_groups() -> None:
    layout = DefaultCodeLanguagePluginLayout()

    groups = layout.extract_namespace_groups(
        [
            "python/namespaces/identity/auth/model.py",
            "python/namespaces/identity/auth/service.py",
        ],
        CodeLanguage.python,
        enforce_namespace_layout=True,
    )

    by_name = {group.name: group for group in groups}
    identity = by_name["identity"]

    assert identity.path == "python/namespaces/identity"
    assert [(entry.name, entry.path) for entry in identity.entries] == [
        ("auth", "auth")
    ]
