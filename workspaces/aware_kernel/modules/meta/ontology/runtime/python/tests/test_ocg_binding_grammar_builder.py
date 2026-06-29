from pathlib import Path
from uuid import UUID

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_content.builder import get_segment_text
from aware_content_ontology.stable_ids import (
    stable_content_part_text_id,
    stable_content_part_text_segment_id,
)

from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_binding_formula_id,
    stable_object_config_graph_binding_formula_segment_reference_id,
)

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.manifest.spec import AwarePackageKind


def _build_code(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def _build_target_graph(tmp_path: Path, content: str):
    target_code = _build_code(tmp_path, "target.aware", content)
    target_ns, target_domains = _ns(
        fqn_prefix="aware_home",
        namespace="home",
        code_ids=[target_code.id],
    )
    return build_object_config_graph_from_code(
        name="home_graph",
        description="home_graph",
        fqn_prefix="aware_home",
        file_codes=[("home/target.aware", target_code)],
        namespace_by_code_id=target_ns,
        package_kind=AwarePackageKind.ontology,
    )


def _build_source_graph(tmp_path: Path, content: str, *, external_graph):
    source_code = _build_code(tmp_path, "source.aware", content)
    source_ns, source_domains = _ns(
        fqn_prefix="aware_home_api",
        namespace="home.door",
        code_ids=[source_code.id],
    )
    return build_object_config_graph_from_code(
        name="home_api_graph",
        description="home_api_graph",
        fqn_prefix="aware_home_api",
        file_codes=[("door/source.aware", source_code)],
        namespace_by_code_id=source_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[external_graph],
    )


def test_ocg_builder_lowers_binding_sections_into_meta_binding_objects(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    target_res = _build_target_graph(
        tmp_path,
        ("class Door {\n" "    label String\n" "}\n"),
    )

    source_res = _build_source_graph(
        tmp_path,
        (
            "class DoorDevice : inline_value {\n"
            "    device_id String\n"
            "    provider String\n"
            "    door_label String\n"
            "}\n"
            "\n"
            "binding aware_home_api aware_home {\n"
            "    map door_by_label door.DoorDevice home.Door.label {\n"
            '        """Resolve external door payload onto canonical Door.label."""\n'
            "        template {\n"
            '            "device_id::{device_id}_provider::{provider}_label::{door_label}"\n'
            "        }\n"
            "    }\n"
            "}\n"
        ),
        external_graph=target_res.graph,
    )

    bindings = source_res.graph.object_config_graph_bindings
    assert len(bindings) == 1
    binding = bindings[0]
    assert binding.target_object_config_graph_id == target_res.graph.id
    assert binding.target_object_config_graph is not None
    assert binding.target_object_config_graph.fqn_prefix == "aware_home"

    assert len(binding.object_config_graph_binding_classes) == 1
    binding_class = binding.object_config_graph_binding_classes[0]
    assert binding_class.name == "door_by_label"
    assert (
        binding_class.description
        == "Resolve external door payload onto canonical Door.label."
    )
    assert binding_class.source_class is not None
    assert binding_class.source_class.name == "DoorDevice"
    assert binding_class.target_class is not None
    assert binding_class.target_class.name == "Door"
    assert binding_class.target_attribute is not None
    assert binding_class.target_attribute.attribute_config is not None
    assert binding_class.target_attribute.attribute_config.name == "label"
    assert binding_class.binding_formula is not None
    formula = binding_class.binding_formula
    assert formula.id == stable_object_config_graph_binding_formula_id(
        object_config_graph_binding_class_id=binding_class.id,
        key="default",
    )
    assert formula.content_part_text is not None
    assert formula.content_part_text.content_part_id == formula.id
    assert formula.content_part_text.id == stable_content_part_text_id(
        content_part_id=formula.id, key=f"{formula.id}:template"
    )
    assert (
        formula.content_part_text.inline_text
        == "device_id::{device_id}_provider::{provider}_label::{door_label}"
    )
    assert len(formula.object_config_graph_binding_formula_segment_references) == 3
    segment_refs = formula.object_config_graph_binding_formula_segment_references
    names = [
        ref.source_class_config_attribute_config.attribute_config.name
        for ref in segment_refs
        if ref.source_class_config_attribute_config is not None
        and ref.source_class_config_attribute_config.attribute_config is not None
    ]
    assert names == ["device_id", "provider", "door_label"]
    spans = [
        get_segment_text(ref.content_part_text_segment)
        for ref in segment_refs
        if ref.content_part_text_segment is not None
    ]
    assert spans == ["{device_id}", "{provider}", "{door_label}"]
    for idx, ref in enumerate(segment_refs):
        assert ref.content_part_text_segment is not None
        assert ref.content_part_text_segment.id == stable_content_part_text_segment_id(
            content_part_text_id=formula.content_part_text.id,
            key=f"{formula.id}:placeholder:{idx}:{names[idx]}",
        )
        assert ref.source_class_config_attribute_config is not None
        assert ref.id == stable_object_config_graph_binding_formula_segment_reference_id(
            object_config_graph_binding_formula_id=formula.id,
            content_part_text_segment_id=ref.content_part_text_segment.id,
            source_class_config_attribute_config_id=ref.source_class_config_attribute_config.id,
        )


def test_ocg_builder_rejects_binding_template_unknown_source_attribute(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    target_res = _build_target_graph(tmp_path, "class Door {\n    label String\n}\n")

    with pytest.raises(
        ValueError,
        match="Binding template placeholder 'missing_attr' not found on source class",
    ):
        _build_source_graph(
            tmp_path,
            (
                "class DoorDevice : inline_value {\n"
                "    device_id String\n"
                "    provider String\n"
                "    door_label String\n"
                "}\n"
                "\n"
                "binding aware_home_api aware_home {\n"
                "    map door_by_label door.DoorDevice home.Door.label {\n"
                "        template {\n"
                '            "device_id::{device_id}_missing::{missing_attr}"\n'
                "        }\n"
                "    }\n"
                "}\n"
            ),
            external_graph=target_res.graph,
        )


def test_ocg_builder_rejects_binding_template_invalid_placeholder_syntax(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    target_res = _build_target_graph(tmp_path, "class Door {\n    label String\n}\n")

    with pytest.raises(
        ValueError, match="Binding template placeholder 'door-label' is invalid"
    ):
        _build_source_graph(
            tmp_path,
            (
                "class DoorDevice : inline_value {\n"
                "    device_id String\n"
                "    provider String\n"
                "    door_label String\n"
                "}\n"
                "\n"
                "binding aware_home_api aware_home {\n"
                "    map door_by_label door.DoorDevice home.Door.label {\n"
                "        template {\n"
                '            "device_id::{device_id}_label::{door-label}"\n'
                "        }\n"
                "    }\n"
                "}\n"
            ),
            external_graph=target_res.graph,
        )


def test_ocg_builder_rejects_binding_template_non_string_target_attribute(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    target_res = _build_target_graph(
        tmp_path,
        ("class Door {\n" "    priority Int\n" "}\n"),
    )

    with pytest.raises(
        ValueError,
        match="Binding template target attribute 'priority' must be a String-compatible primitive",
    ):
        _build_source_graph(
            tmp_path,
            (
                "class DoorDevice : inline_value {\n"
                "    device_id String\n"
                "    provider String\n"
                "    door_label String\n"
                "}\n"
                "\n"
                "binding aware_home_api aware_home {\n"
                "    map door_by_priority door.DoorDevice home.Door.priority {\n"
                "        template {\n"
                '            "device_id::{device_id}_provider::{provider}_label::{door_label}"\n'
                "        }\n"
                "    }\n"
                "}\n"
            ),
            external_graph=target_res.graph,
        )
