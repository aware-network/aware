from __future__ import annotations

from pathlib import Path

from python_grammar import import_grouping
from python_grammar.import_grouping import (
    PythonImportGroupingPolicy,
    group_python_imports,
    public_label_from_import_root,
    semantic_import_roots_from_renderer_inputs,
)
from python_grammar.renderer_policy import PythonRenderPolicy


def test_python_import_grouping_uses_explicit_semantic_roots_only() -> None:
    grouped = group_python_imports(
        {
            "pathlib": {"Path"},
            "demo_ontology.widget": {"Widget"},
            "aware_not_declared.example": {"Example"},
            "pydantic": {"BaseModel"},
        },
        policy=PythonImportGroupingPolicy(
            semantic_import_roots={"demo_ontology": "Demo Ontology"},
        ),
    )

    assert list(grouped) == ["Standard", "Third-party", "Demo Ontology"]
    assert grouped["Standard"] == {"pathlib": {"Path"}}
    assert grouped["Demo Ontology"] == {"demo_ontology.widget": {"Widget"}}
    assert grouped["Third-party"] == {
        "aware_not_declared.example": {"Example"},
        "pydantic": {"BaseModel"},
    }


def test_python_import_grouping_derives_roots_from_renderer_inputs() -> None:
    roots = semantic_import_roots_from_renderer_inputs(
        import_root="current_runtime",
        import_overrides={
            "class-id": "dependency_ontology.schema.thing",
            "enum-id": "dependency_enums.schema.thing_enums",
        },
        external_graph_fqn_prefixes=("external_graph", None, ""),
    )

    assert roots == {
        "current_runtime": "Current Runtime",
        "dependency_ontology": "Dependency Ontology",
        "dependency_enums": "Dependency Enums",
        "external_graph": "External Graph",
    }


def test_python_import_grouping_public_labels_strip_aware_prefix() -> None:
    assert public_label_from_import_root("aware_types") == "Types"
    assert public_label_from_import_root("aware_code_ontology_dto") == "Code Ontology Dto"
    assert public_label_from_import_root("content_ontology") == "Content Ontology"

    roots = semantic_import_roots_from_renderer_inputs(
        import_root="aware_code_ontology_dto",
        import_overrides={
            "class-id": "aware_content_ontology_dto.part.content_part",
        },
        external_graph_fqn_prefixes=("aware_meta_ontology",),
    )

    assert roots == {
        "aware_code_ontology_dto": "Code Ontology Dto",
        "aware_content_ontology_dto": "Content Ontology Dto",
        "aware_meta_ontology": "Meta Ontology",
    }


def test_python_import_grouping_uses_renderer_declared_support_roots() -> None:
    grouped = group_python_imports(
        {
            "aware_types": {"JsonArray"},
            "aware_orm.models.orm_model": {"ORMModel"},
            "pydantic": {"Field"},
        },
        policy=PythonImportGroupingPolicy(
            support_import_roots={
                "aware_orm": "Orm",
                "aware_types": "Types",
            },
        ),
    )

    assert list(grouped) == ["Third-party", "Orm", "Types"]
    assert grouped["Third-party"] == {"pydantic": {"Field"}}
    assert grouped["Orm"] == {
        "aware_orm.models.orm_model": {"ORMModel"},
    }
    assert grouped["Types"] == {
        "aware_types": {"JsonArray"},
    }


def test_python_import_grouping_uses_renderer_profile_policy_support_roots() -> None:
    orm_policy = PythonRenderPolicy.orm_models_default()
    api_policy = PythonRenderPolicy.api_default()
    dto_policy = PythonRenderPolicy.ontology_dto_default()

    assert dict(orm_policy.support_import_roots) == {
        "aware_types": "Types",
        "aware_orm": "Orm",
    }
    assert dict(api_policy.support_import_roots) == {"aware_types": "Types"}
    assert dict(dto_policy.support_import_roots) == {"aware_types": "Types"}

    grouped = group_python_imports(
        {
            "aware_types": {"JsonArray"},
            "aware_orm.models.orm_model": {"ORMModel"},
            "pydantic": {"Field"},
        },
        policy=PythonImportGroupingPolicy(
            support_import_roots=orm_policy.support_import_roots,
        ),
    )

    assert list(grouped) == ["Third-party", "Orm", "Types"]
    assert grouped["Third-party"] == {"pydantic": {"Field"}}
    assert grouped["Orm"] == {
        "aware_orm.models.orm_model": {"ORMModel"},
    }
    assert grouped["Types"] == {
        "aware_types": {"JsonArray"},
    }


def test_python_import_grouping_has_no_repo_or_prefix_discovery() -> None:
    source = Path(import_grouping.__file__).read_text(encoding="utf-8")

    forbidden_fragments = (
        "pyproject",
        "poetry",
        'startswith("aware_',
        "startswith('aware_",
        "aware_orm",
        "aware_agent",
        "aware_network",
        "aware_environment",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source
