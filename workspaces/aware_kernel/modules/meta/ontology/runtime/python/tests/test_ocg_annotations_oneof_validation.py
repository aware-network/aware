from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_ocg_ann_oneof_compiles(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "oneof_ok.aware",
        """
class Envelope {
    request String?
    response String?
}

ann default.Envelope oneof request response
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="oneof_graph",
        description="oneof_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("oneof_ok.aware", code)],
        namespace_by_code_id=ns,
    )

    annos = list(res.graph.object_config_graph_annotations)
    oneofs = [
        a
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.oneof
        and a.code_section_annotation_oneof is not None
    ]
    assert len(oneofs) == 1
    v = oneofs[0].code_section_annotation_oneof
    assert v is not None
    assert v.class_name == "Envelope"
    assert str(getattr(v.mode, "value", v.mode)) == "validation"
    assert v.attribute_names == ["request", "response"]


def test_ocg_ann_oneof_identity_mode_compiles(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "oneof_identity.aware",
        """
class Envelope {
    request String?
    response String?
}

ann default.Envelope oneof identity request response
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="oneof_graph_identity",
        description="oneof_graph_identity",
        fqn_prefix="ann_pkg",
        file_codes=[("oneof_identity.aware", code)],
        namespace_by_code_id=ns,
    )

    annos = list(res.graph.object_config_graph_annotations)
    oneofs = [
        a
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.oneof
        and a.code_section_annotation_oneof is not None
    ]
    assert len(oneofs) == 1
    v = oneofs[0].code_section_annotation_oneof
    assert v is not None
    assert str(getattr(v.mode, "value", v.mode)) == "identity"
    assert v.attribute_names == ["request", "response"]


def test_ocg_ann_oneof_identity_discriminator_mapping_compiles(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "oneof_identity_discriminator.aware",
        """
enum EnvelopeKind {
    request
    response
}

class Envelope {
    kind EnvelopeKind key
    request_id UUID?
    response_id UUID?
}

ann default.Envelope oneof identity request_id response_id discriminator kind request request_id response response_id
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="oneof_graph_identity_discriminator",
        description="oneof_graph_identity_discriminator",
        fqn_prefix="ann_pkg",
        file_codes=[("oneof_identity_discriminator.aware", code)],
        namespace_by_code_id=ns,
    )

    annos = list(res.graph.object_config_graph_annotations)
    oneofs = [
        a
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.oneof
        and a.code_section_annotation_oneof is not None
    ]
    assert len(oneofs) == 1
    v = oneofs[0].code_section_annotation_oneof
    assert v is not None
    assert str(getattr(v.mode, "value", v.mode)) == "identity"
    assert v.attribute_names == ["request_id", "response_id"]
    assert v.discriminator_attribute_name == "kind"
    assert v.discriminator_cases == ["request=request_id", "response=response_id"]


def test_ocg_ann_oneof_requires_existing_attrs(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "oneof_missing.aware",
        """
class Envelope {
    request String?
    response String?
}

ann default.Envelope oneof request missing
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    with pytest.raises(ValueError, match="unknown attributes"):
        build_object_config_graph_from_code(
            name="oneof_graph",
            description="oneof_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("oneof_missing.aware", code)],
            namespace_by_code_id=ns,
        )


def test_ocg_ann_oneof_requires_optional_attrs(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "oneof_required.aware",
        """
class Envelope {
    request String
    response String?
}

ann default.Envelope oneof request response
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    with pytest.raises(ValueError, match="requires optional attributes"):
        build_object_config_graph_from_code(
            name="oneof_graph",
            description="oneof_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("oneof_required.aware", code)],
            namespace_by_code_id=ns,
        )
