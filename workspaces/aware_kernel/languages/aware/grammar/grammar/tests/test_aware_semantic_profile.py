from __future__ import annotations

import aware_api_runtime.semantic_contract as api_semantic_contract
import aware_experience.semantic_contract as experience_semantic_contract
import aware_interface.semantic_contract as interface_semantic_contract
import aware_meta.semantic_contract as meta_semantic_contract
import aware_service_runtime.semantic_contract as service_semantic_contract
import aware_skill.semantic_contract as skill_semantic_contract
import pytest
from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticGrammarRuleDescriptor,
    ModuleSemanticGrammarRuleFieldDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_grammar.code_language_plugin import (
    AWARE_CODE_PLUGIN,
    AWARE_GRAMMAR_FULL_PROFILE,
    build_aware_code_language_plugin,
)
from aware_grammar.semantic_profile import (
    AwareGrammarSemanticProfileError,
    build_aware_grammar_declaration_coverage_profile,
    build_aware_grammar_semantic_profile,
    validate_aware_grammar_rule,
)


def test_current_profile_preserves_existing_code_plugin_sections() -> None:
    expected_section_types = {
        CodeSectionType.annotation,
        CodeSectionType.attribute,
        CodeSectionType.binding,
        CodeSectionType.class_,
        CodeSectionType.comment,
        CodeSectionType.enum,
        CodeSectionType.enum_value,
        CodeSectionType.function,
        CodeSectionType.import_,
        CodeSectionType.mirror,
        CodeSectionType.projection,
    }

    assert set(AWARE_GRAMMAR_FULL_PROFILE.code_section_types) == expected_section_types
    assert set(AWARE_CODE_PLUGIN.node_adapters) == expected_section_types

    rebuilt = build_aware_code_language_plugin(profile=AWARE_GRAMMAR_FULL_PROFILE)
    assert rebuilt.language == AWARE_CODE_PLUGIN.language
    assert set(rebuilt.node_adapters) == set(AWARE_CODE_PLUGIN.node_adapters)
    assert {
        section_type: type(adapter)
        for section_type, adapter in rebuilt.node_adapters.items()
    } == {
        section_type: type(adapter)
        for section_type, adapter in AWARE_CODE_PLUGIN.node_adapters.items()
    }


def test_semantic_contract_profile_maps_active_lanes_to_parser_rules() -> None:
    profile = build_aware_grammar_semantic_profile(
        profile_key="aware_kernel.semantic_contracts",
        semantic_contracts=(
            meta_semantic_contract.AWARE_META_SEMANTIC_CONTRACT,
            api_semantic_contract.AWARE_API_SEMANTIC_CONTRACT,
            service_semantic_contract.AWARE_SERVICE_SEMANTIC_CONTRACT,
            experience_semantic_contract.AWARE_EXPERIENCE_SEMANTIC_CONTRACT,
            interface_semantic_contract.AWARE_INTERFACE_SEMANTIC_CONTRACT,
            skill_semantic_contract.AWARE_SKILL_SEMANTIC_CONTRACT,
        ),
    )

    assert "aware_meta" in profile.provider_keys
    assert "aware_api" in profile.provider_keys
    assert "projection_def" in profile.grammar_rules
    assert "api_capability_endpoint_def" in profile.grammar_rules
    assert "pane_render_component_stmt" in profile.grammar_rules
    assert "skill_step_def" in profile.grammar_rules
    assert profile.semantic_owners_for_rule("projection_def") == (
        meta_semantic_contract.META_PROJECTION_OWNER,
    )
    assert profile.semantic_owners_for_rule("api_capability_endpoint_def") == (
        api_semantic_contract.API_CAPABILITY_OWNER,
    )
    assert profile.semantic_owners_for_rule("pane_render_component_stmt") == (
        interface_semantic_contract.INTERFACE_RENDER_COMPONENT_OWNER,
    )
    assert profile.code_section_type_for_rule("projection_def") == (
        CodeSectionType.projection
    )
    assert profile.code_section_type_for_rule("api_def") is None


def test_semantic_profile_fails_closed_for_unknown_grammar_rule() -> None:
    contract = ModuleSemanticContract(
        provider_key="aware_demo",
        syntax_lanes=(
            ModuleSemanticSyntaxLaneDescriptor(
                lane_key="aware_demo.unknown",
                semantic_owner="aware_demo.unknown",
                compiler_owner="aware_demo.unknown",
                grammar_rules=("not_a_real_aware_rule",),
            ),
        ),
    )

    with pytest.raises(AwareGrammarSemanticProfileError) as exc:
        build_aware_grammar_semantic_profile(
            profile_key="broken",
            semantic_contracts=(contract,),
        )

    assert "not_a_real_aware_rule" in str(exc.value)
    assert "aware_demo.unknown" in str(exc.value)


def test_profile_rule_validation_uses_current_tree_sitter_parser() -> None:
    assert validate_aware_grammar_rule("source_file") is True
    assert validate_aware_grammar_rule("class_def") is True
    assert validate_aware_grammar_rule("function_that_does_not_exist") is False


def test_meta_grammar_declarations_cover_source_meaning_anchors() -> None:
    coverage = build_aware_grammar_declaration_coverage_profile(
        profile_key="aware_meta.grammar_contract",
        semantic_contracts=(meta_semantic_contract.AWARE_META_SEMANTIC_CONTRACT,),
        source_meaning_contracts=(
            meta_semantic_contract.META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT,
        ),
    )

    declared = {
        (item.semantic_owner, item.rule_name): item.declared_anchor_fields
        for item in coverage.rule_declarations
    }

    assert coverage.ok is True
    assert (
        meta_semantic_contract.META_OBJECT_CONFIG_GRAPH_OWNER,
        "class_def",
    ) in declared
    assert (
        "description_comment"
        in declared[
            (meta_semantic_contract.META_OBJECT_CONFIG_GRAPH_OWNER, "class_def")
        ]
    )
    assert (
        "type"
        in declared[(meta_semantic_contract.META_OBJECT_CONFIG_GRAPH_OWNER, "attr_def")]
    )
    assert coverage.anchor_diagnostics == ()


def test_grammar_declaration_coverage_reports_missing_anchor_field() -> None:
    contract = ModuleSemanticContract(
        provider_key="aware_demo",
        syntax_lanes=(
            ModuleSemanticSyntaxLaneDescriptor(
                lane_key="aware_demo.class",
                semantic_owner="aware_demo.object_graph",
                compiler_owner="aware_demo.object_graph",
                grammar_rules=("class_def",),
            ),
        ),
        grammar_rule_declarations=(
            ModuleSemanticGrammarRuleDescriptor(
                semantic_owner="aware_demo.object_graph",
                rule_name="class_def",
                fields=(
                    ModuleSemanticGrammarRuleFieldDescriptor(
                        field_path="name",
                        required=True,
                    ),
                ),
            ),
        ),
    )

    coverage = build_aware_grammar_declaration_coverage_profile(
        profile_key="aware_demo.grammar_contract",
        semantic_contracts=(contract,),
        source_meaning_contracts=(
            {
                "provider_key": "aware_demo",
                "semantic_owner": "aware_demo.object_graph",
                "bindings": [
                    {
                        "binding_key": "aware_demo.class.description",
                        "grammar_rule_name": "class_def",
                        "anchor_field_path": "description_comment",
                    }
                ],
            },
        ),
    )

    assert coverage.ok is False
    assert len(coverage.anchor_diagnostics) == 1
    assert "description_comment" in coverage.anchor_diagnostics[0].message()
