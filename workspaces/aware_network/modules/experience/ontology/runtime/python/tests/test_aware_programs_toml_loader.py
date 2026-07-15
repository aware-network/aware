import pytest

from aware_experience.program.loader import (
    AwareProgramsTomlError,
    load_aware_programs_toml_spec,
)


def test_load_aware_programs_toml_happy_path(tmp_path) -> None:
    p = tmp_path / "aware.programs.toml"
    p.write_text(
        """
aware = 1

[[programs]]
ref = "conversation_default:ConversationReactivityPolicies_v1"
path = "reactivity/conversation_reactivity_policies_v1.aware"
name = "ConversationReactivityPolicies_v1"
dependencies = ["conversation-ontology", "reactivity-ontology", "meta-ontology"]
required_symbols = []
optional_symbols = ["plan.environment_id", "plan.thread_id"]
""",
        encoding="utf-8",
    )

    spec = load_aware_programs_toml_spec(toml_path=p)
    assert spec.aware == 1
    assert len(spec.programs) == 1
    row = spec.programs[0]
    assert row.ref == "conversation_default:ConversationReactivityPolicies_v1"
    assert row.module_id == "conversation_default"
    assert row.program_name == "ConversationReactivityPolicies_v1"
    assert row.path == "reactivity/conversation_reactivity_policies_v1.aware"
    assert row.dependencies == (
        "conversation-ontology",
        "reactivity-ontology",
        "meta-ontology",
    )
    assert row.required_symbols == ()
    assert row.optional_symbols == ("plan.environment_id", "plan.thread_id")


def test_load_aware_programs_toml_ref_name_mismatch_fails(tmp_path) -> None:
    p = tmp_path / "aware.programs.toml"
    p.write_text(
        """
aware = 1

[[programs]]
ref = "agent:EnsureBootAgentGraph_v0"
path = "boot/ensure_boot_agent_graph_v0.aware"
name = "WrongName"
""",
        encoding="utf-8",
    )

    with pytest.raises(
        AwareProgramsTomlError,
        match=r"must match ref program name",
    ):
        load_aware_programs_toml_spec(toml_path=p)


def test_load_aware_programs_toml_requires_namespaced_symbols(tmp_path) -> None:
    p = tmp_path / "aware.programs.toml"
    p.write_text(
        """
aware = 1

[[programs]]
ref = "agent:EnsureBootAgentGraph_v0"
path = "boot/ensure_boot_agent_graph_v0.aware"
name = "EnsureBootAgentGraph_v0"
required_symbols = ["interface_id"]
""",
        encoding="utf-8",
    )

    with pytest.raises(
        AwareProgramsTomlError,
        match=r"must be namespaced",
    ):
        load_aware_programs_toml_spec(toml_path=p)
