from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.config.builder import build_object_config_graph
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.overlay.reserved_keywords import (
    apply_reserved_keyword_overlays,
)
from aware_meta.graph.config.stable_ids import (
    stable_ocg_overlay_entry_id,
    stable_ocg_overlay_id,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.reserved_keyword_policy import ReservedKeywordEntityPolicy
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)


def test_stable_ocg_overlay_id_is_deterministic() -> None:
    ocg_id = uuid4()
    overlay_id_1 = stable_ocg_overlay_id(
        object_config_graph_id=ocg_id, language=CodeLanguage.python.value
    )
    overlay_id_2 = stable_ocg_overlay_id(
        object_config_graph_id=ocg_id, language=CodeLanguage.python.value
    )
    assert overlay_id_1 == overlay_id_2


def test_reserved_keyword_overlay_normalizes_overlay_and_entry_ids() -> None:
    class _DummyPlugin:
        def __init__(self, language: CodeLanguage):
            self.language = language
            self.reserved_keyword_policies = {
                CodeSectionAnnotationOverlayEntity.class_: ReservedKeywordEntityPolicy(
                    reserved_identifiers=frozenset({"class"}),
                    default_rendered_name=lambda x: getattr(x, "name", ""),
                )
            }

    lang = CodeLanguage.python
    prev_plugins = dict(MetaLanguagePluginRegistry._plugins)  # type: ignore[attr-defined]
    prev_supported = set(MetaLanguagePluginRegistry._supported_languages)  # type: ignore[attr-defined]
    try:
        MetaLanguagePluginRegistry._plugins[lang] = _DummyPlugin(lang)  # type: ignore[attr-defined]
        MetaLanguagePluginRegistry._supported_languages.add(lang)  # type: ignore[attr-defined]

        ocg = build_object_config_graph(
            language=CodeLanguage.aware,
            name="test",
            fqn_prefix="aware_test",
            class_configs=[],
            class_config_relationships=[],
            enum_configs=[],
            function_configs=[],
            namespace_bundle=ObjectConfigGraphNamespaceBundle(
                namespace_by_class_config_id={},
                namespace_by_enum_config_id={},
                namespace_by_function_config_id={},
            ),
        )

        legacy_overlay = ObjectConfigGraphOverlay(
            id=uuid4(),
            language=lang,
            object_config_graph_id=ocg.id,
            class_config_overlays=[
                ClassConfigOverlay(
                    id=uuid4(),
                    object_config_graph_overlay_id=uuid4(),
                    class_config_id=uuid4(),
                    rendered_name="class_",
                )
            ],
        )
        overlays_by_language = {lang: legacy_overlay}

        out = apply_reserved_keyword_overlays(
            ocg, overlays_by_language=overlays_by_language
        )
        overlay = out[lang]

        expected_overlay_id = stable_ocg_overlay_id(
            object_config_graph_id=ocg.id, language=lang.value
        )
        assert overlay.id == expected_overlay_id

        assert overlay.class_config_overlays
        co = overlay.class_config_overlays[0]
        assert co.object_config_graph_overlay_id == expected_overlay_id
        assert co.id == stable_ocg_overlay_entry_id(
            overlay_id=expected_overlay_id, kind="class", target_id=co.class_config_id
        )
    finally:
        MetaLanguagePluginRegistry._plugins = prev_plugins  # type: ignore[attr-defined]
        MetaLanguagePluginRegistry._supported_languages = prev_supported  # type: ignore[attr-defined]
