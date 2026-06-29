from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

import pytest

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code

from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN


@pytest.fixture(scope="session", autouse=True)
def _register_python_language_plugin() -> None:
    CodeLanguagePluginRegistry.register(PYTHON_CODE_PLUGIN)


@pytest.fixture(scope="session")
def sample_files() -> dict[str, str]:
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples"
    user_post = samples_dir / "user_post.py"
    if not user_post.exists():
        pytest.fail(f"Missing sample: {user_post}")
    return {"user_post": str(user_post)}


def _build_code(path: str) -> Code:
    return build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=path,
        code_key=path,
        language=CodeLanguage.python,
        symbol_table=CodeSymbolTable(),
    )


def _build_test_namespaces(
    *,
    package_name: str,
    codes: Sequence[tuple[str, Code]],
    namespace: str,
) -> tuple[dict[UUID, NamespacePath], list[object]]:
    namespace_by_code_id: dict[UUID, NamespacePath] = {
        code.id: NamespacePath(package=package_name, namespace=namespace) for _, code in codes
    }
    return namespace_by_code_id, []


def _classes_by_name(graph: ObjectConfigGraph) -> dict[str, ClassConfig]:
    classes: dict[str, ClassConfig] = {}
    for n in graph.object_config_graph_nodes:
        if n.type != ObjectConfigGraphNodeType.class_:
            continue
        cls = n.class_config
        if cls is None:
            continue
        classes[cls.name] = cls
    return classes


def _enums_by_name(graph: ObjectConfigGraph) -> dict[str, EnumConfig]:
    enums: dict[str, EnumConfig] = {}
    for n in graph.object_config_graph_nodes:
        if n.type != ObjectConfigGraphNodeType.enum:
            continue
        enum = n.enum_config
        if enum is None:
            continue
        enums[enum.name] = enum
    return enums


def _attribute_configs(cls: ClassConfig):
    return [link.attribute_config for link in cls.class_config_attribute_configs]


def test_ocg_builder_user_post_sample(sample_files: dict[str, str]) -> None:
    code = _build_code(sample_files["user_post"])
    codes = [("user_post", code)]
    namespace_by_code_id, domains = _build_test_namespaces(
        package_name="test_pkg",
        codes=codes,
        namespace="test_schema",
    )

    with pytest.raises(
        ValueError,
        match=r"Standalone/global functions are not modeled in canonical ObjectConfigGraph",
    ):
        build_object_config_graph_from_code(
            name="test_user_post_ocg",
            description="canonical kernel meta OCG build from python sample",
            fqn_prefix="test_pkg",
            file_codes=[("user_post", code)],
            namespace_by_code_id=namespace_by_code_id,
        )


def test_ocg_builder_resolves_import_aliases(tmp_path: Path) -> None:
    analytic_path = tmp_path / "analytic.py"
    agent_path = tmp_path / "agent.py"

    analytic_path.write_text(
        """
from pydantic import BaseModel


class Analytic(BaseModel):
    name: str
""".lstrip(),
        encoding="utf-8",
    )

    agent_path.write_text(
        """
from pydantic import BaseModel

from aware.workflow.analytic import Analytic as FooAlias
import aware.workflow.analytic as wf


class Agent(BaseModel):
    analytic: FooAlias
    analytic2: wf.Analytic
""".lstrip(),
        encoding="utf-8",
    )

    code_analytic = _build_code(str(analytic_path))
    code_agent = _build_code(str(agent_path))

    file_codes: list[tuple[str, Code]] = [
        (str(analytic_path), code_analytic),
        (str(agent_path), code_agent),
    ]

    namespace_by_code_id: dict[UUID, NamespacePath] = {
        code_analytic.id: NamespacePath(package="aware", namespace="workflow.analytic"),
        code_agent.id: NamespacePath(package="aware", namespace="identity.agent"),
    }
    result = build_object_config_graph_from_code(
        name="import_alias",
        description="import alias resolution in python",
        fqn_prefix="aware",
        file_codes=file_codes,
        namespace_by_code_id=namespace_by_code_id,
    )

    graph = result.graph
    classes = _classes_by_name(graph)
    assert "Analytic" in classes
    assert "Agent" in classes

    analytic = classes["Analytic"]
    agent = classes["Agent"]

    def _attr_descriptor_for(cls: ClassConfig, attr_name: str):
        for attribute_config in _attribute_configs(cls):
            if attribute_config.name == attr_name:
                return attribute_config.type_descriptor
        raise AssertionError(f"AttributeConfig not found: {cls.name}.{attr_name}")

    desc1 = _attr_descriptor_for(agent, "analytic")
    assert desc1.kind.value == "class"
    assert desc1.class_config_id == analytic.id

    desc2 = _attr_descriptor_for(agent, "analytic2")
    assert desc2.kind.value == "class"
    assert desc2.class_config_id == analytic.id
