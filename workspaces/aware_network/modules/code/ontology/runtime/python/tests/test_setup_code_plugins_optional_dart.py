from __future__ import annotations

from types import SimpleNamespace

import aware_code.setup_language_plugins as language_plugins
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage


def test_setup_code_plugins_allows_missing_optional_dart(monkeypatch) -> None:
    registered_languages: list[CodeLanguage] = []
    monkeypatch.setattr(
        AwareModulePluginRegistry,
        "get_builtin_code_language_plugins",
        classmethod(
            lambda cls: (
                SimpleNamespace(language=CodeLanguage.aware),
                SimpleNamespace(language=CodeLanguage.sql),
                SimpleNamespace(language=CodeLanguage.python),
            )
        ),
    )
    monkeypatch.setattr(
        language_plugins.CodeLanguagePluginRegistry,
        "register",
        lambda plugin: registered_languages.append(plugin.language),
    )

    language_plugins.setup_code_plugins()

    assert registered_languages == [
        CodeLanguage.aware,
        CodeLanguage.sql,
        CodeLanguage.python,
    ]
