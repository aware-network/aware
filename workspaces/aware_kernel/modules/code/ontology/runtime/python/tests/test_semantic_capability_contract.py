from __future__ import annotations

from aware_code.package.semantic_binding import package_semantic_binding_callable_name
from aware_code.semantic_capability import (
    SEMANTIC_ANALYSIS_CAPABILITY,
    SemanticCapabilityActionBinding,
    SemanticCapabilityEvent,
    SemanticCapabilityFunctionCallBinding,
)


def test_semantic_analysis_is_a_code_owned_package_binding_capability() -> None:
    assert (
        package_semantic_binding_callable_name(capability=SEMANTIC_ANALYSIS_CAPABILITY)
        == "semantic_analysis"
    )


def test_semantic_capability_event_keeps_function_call_policy_separate() -> None:
    event = SemanticCapabilityEvent(
        event_key="aware_fake.subject.upserted",
        semantic_key="fake:demo/subject:read_demo",
        verb="upsert",
        subject_type="aware_fake.Subject",
        source="aware_fake.semantic_analysis",
        source_refs=("fake/demo.aware",),
        delta_keys=("aware_fake.subject.upsert:demo",),
        condition_keys=("fake_subject_name_changed",),
        payload={"class_ref": "aware_demo.FakeRequest"},
    )
    binding = SemanticCapabilityActionBinding(
        action_key="aware_fake.subject.upserted.apply_ontology",
        event_key="aware_fake.subject.upserted",
        action_type="function_call",
        function_call_binding=SemanticCapabilityFunctionCallBinding(
            binding_key="aware_fake.subject.upserted.fake_subject_apply",
            event_key="aware_fake.subject.upserted",
            receiver_semantic_key_template="payload.subject_semantic_key",
            function_ref="aware_fake_ontology.subject.Subject.apply",
            argument_bindings={
                "name": "payload.name",
                "description": "payload.description",
            },
            argument_ref_bindings={
                "class_config_id": "payload.class_ref",
            },
            result_semantic_key_template="semantic_key",
            metadata={"argument_ref_resolution": "class_config_id"},
        ),
    )

    assert event.evidence_payload() == {
        "event_key": "aware_fake.subject.upserted",
        "event_type": "semantic_change",
        "semantic_key": "fake:demo/subject:read_demo",
        "verb": "upsert",
        "subject_type": "aware_fake.Subject",
        "source": "aware_fake.semantic_analysis",
        "source_refs": ("fake/demo.aware",),
        "delta_keys": ("aware_fake.subject.upsert:demo",),
        "condition_keys": ("fake_subject_name_changed",),
        "payload": {"class_ref": "aware_demo.FakeRequest"},
        "metadata": {},
    }
    assert "function_call" not in event.evidence_payload()
    assert binding.evidence_payload()["function_call_binding"] == {
        "binding_key": "aware_fake.subject.upserted.fake_subject_apply",
        "event_key": "aware_fake.subject.upserted",
        "function_ref": "aware_fake_ontology.subject.Subject.apply",
        "receiver_semantic_key_template": "payload.subject_semantic_key",
        "argument_bindings": {
            "name": "payload.name",
            "description": "payload.description",
        },
        "argument_ref_bindings": {
            "class_config_id": "payload.class_ref",
        },
        "constant_arguments": {},
        "result_semantic_key_template": "semantic_key",
        "metadata": {"argument_ref_resolution": "class_config_id"},
    }
