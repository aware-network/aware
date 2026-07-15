from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.ocg_package_operation_plan import (
    META_OCG_PACKAGE_OPERATION_PLAN_CONTRACT_VERSION,
    MetaOcgPackageAttributeDescriptor,
    MetaOcgPackageClassDescriptor,
    MetaOcgPackageDescriptor,
    MetaOcgPackageEnumDescriptor,
    MetaOcgPackageEnumOptionDescriptor,
    MetaOcgPackageFunctionDescriptor,
    MetaOcgPackageRelationshipDescriptor,
    build_meta_ocg_package_descriptor_from_materialized_ocg,
    build_meta_ocg_package_operation_plan,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
)


def test_meta_ocg_package_operation_plan_emits_generic_intents() -> None:
    plan = build_meta_ocg_package_operation_plan(descriptor=_descriptor())
    payload = plan.evidence_payload()
    intents = tuple(
        _mapping(intent) for intent in _sequence(payload["operation_intents"])
    )
    coverage_members = tuple(
        _mapping(member) for member in _sequence(payload["coverage_members"])
    )

    assert plan.status == "operation_plan_ready"
    assert payload["contract_version"] == META_OCG_PACKAGE_OPERATION_PLAN_CONTRACT_VERSION
    assert payload["builder_fallback_used"] is False
    assert payload["workspace_internals_used"] is False
    assert payload["content_specific"] is False
    assert payload["operation_intent_count"] == 11
    assert [intent["semantic_operation_type"] for intent in intents] == [
        META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    ]
    assert all(
        intent["semantic_contract_provider_key"] == "aware_meta" for intent in intents
    )
    assert all(
        _mapping(intent.get("metadata")).get("meta_owned_operation_plan") is True
        for intent in intents
    )
    assert {
        member["category"]
        for member in coverage_members
    } >= {
        "package_identity",
        "graph_identity",
        "graph_node",
        "class_config",
        "enum_config",
        "enum_option",
        "relationship_config",
        "attribute_config",
        "function_config",
        "namespace_membership",
        "source_ref",
    }
    assert any(
        member["category"] == "source_ref" and member["key"] == "thing/thing.aware"
        for member in coverage_members
    )


def test_meta_ocg_package_operation_plan_blocks_invalid_descriptor() -> None:
    plan = build_meta_ocg_package_operation_plan(
        descriptor=MetaOcgPackageDescriptor(
            package_name="demo-ontology",
            fqn_prefix="aware_demo",
            source_refs=("demo/demo.aware",),
            classes=(
                MetaOcgPackageClassDescriptor(
                    class_fqn="aware_demo.Thing",
                ),
            ),
            relationships=(
                MetaOcgPackageRelationshipDescriptor(
                    source_class_fqn="aware_demo.Thing",
                    target_class_fqn="aware_demo.Missing",
                    relationship_key="missing",
                    relationship_type="one_to_one",
                ),
            ),
        )
    )
    payload = plan.evidence_payload()

    assert plan.status == "blocked"
    assert payload["operation_intent_count"] == 0
    assert payload["coverage_member_count"] == 0
    assert payload["builder_fallback_used"] is False
    assert payload["workspace_internals_used"] is False
    assert plan.blockers == ("relationship_target_class_missing:aware_demo.Missing",)


def test_meta_ocg_package_descriptor_builds_from_generic_ocg_snapshot() -> None:
    descriptor = build_meta_ocg_package_descriptor_from_materialized_ocg(
        package_name="demo-ontology",
        ocg_snapshot=_ocg_snapshot(),
        function_models={
            "classes": (
                {
                    "aware_class_ref": "aware_demo.Thing",
                    "functions": ({"name": "rename", "verb": "update"},),
                },
            ),
        },
    )
    plan = build_meta_ocg_package_operation_plan(descriptor=descriptor)
    payload = plan.evidence_payload()

    assert descriptor.package_name == "demo-ontology"
    assert descriptor.fqn_prefix == "aware_demo"
    assert tuple(item.class_fqn for item in descriptor.classes) == (
        "aware_demo.Thing",
        "aware_demo.Tag",
    )
    assert tuple(item.enum_fqn for item in descriptor.enums) == (
        "aware_demo.ThingKind",
    )
    assert tuple(item.relationship_key for item in descriptor.relationships) == (
        "tags",
    )
    assert plan.status == "operation_plan_ready"
    assert payload["operation_intent_count"] == 11
    assert payload["content_specific"] is False
    assert any(
        _mapping(member).get("category") == "source_ref"
        and _mapping(member).get("key") == "thing/thing.aware"
        for member in _sequence(payload["coverage_members"])
    )


def _descriptor() -> MetaOcgPackageDescriptor:
    return MetaOcgPackageDescriptor(
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        source_refs=("demo/aware.toml",),
        package_description="Demo ontology.",
        classes=(
            MetaOcgPackageClassDescriptor(
                class_fqn="aware_demo.Thing",
                description="Thing config.",
                source_refs=("thing/thing.aware",),
                attributes=(
                    MetaOcgPackageAttributeDescriptor(
                        owner_class_fqn="aware_demo.Thing",
                        name="title",
                        description="Visible title.",
                        source_refs=("thing/thing.aware",),
                    ),
                ),
                functions=(
                    MetaOcgPackageFunctionDescriptor(
                        owner_class_fqn="aware_demo.Thing",
                        name="rename",
                        description="Rename the thing.",
                        verb="update",
                        source_refs=("thing/thing.aware",),
                    ),
                ),
            ),
            MetaOcgPackageClassDescriptor(
                class_fqn="aware_demo.Tag",
                source_refs=("thing/tag.aware",),
            ),
        ),
        enums=(
            MetaOcgPackageEnumDescriptor(
                enum_fqn="aware_demo.ThingKind",
                source_refs=("thing/thing_kind.aware",),
                options=(
                    MetaOcgPackageEnumOptionDescriptor(
                        value="primary",
                        position=0,
                        source_refs=("thing/thing_kind.aware",),
                    ),
                ),
            ),
        ),
        relationships=(
            MetaOcgPackageRelationshipDescriptor(
                source_class_fqn="aware_demo.Thing",
                target_class_fqn="aware_demo.Tag",
                relationship_key="tags",
                relationship_type="one_to_many",
                source_refs=("thing/thing.aware",),
            ),
        ),
    )


def _ocg_snapshot() -> Mapping[str, object]:
    return {
        "fqn_prefix": "aware_demo",
        "language": "aware",
        "name": "demo-ontology",
        "description": "Demo ontology.",
        "object_config_graph_nodes": (
            {
                "type": "class",
                "node_key": "aware_demo.Thing",
                "class_config": {
                    "id": "thing-class-id",
                    "name": "Thing",
                    "description": "Thing config.",
                    "class_config_attribute_configs": (
                        {
                            "position": 0,
                            "attribute_config": {
                                "name": "title",
                                "description": "Visible title.",
                                "is_required": True,
                                "is_public": True,
                                "type_descriptor": {
                                    "kind": "primitive",
                                    "primitive_config": {
                                        "primitive_type": {"base_type": "string"},
                                    },
                                },
                            },
                        },
                    ),
                },
                "layouts": ({"relative_path": "thing/thing.aware"},),
            },
            {
                "type": "class",
                "node_key": "aware_demo.Tag",
                "class_config": {"id": "tag-class-id", "name": "Tag"},
                "layouts": ({"relative_path": "thing/tag.aware"},),
            },
            {
                "type": "enum",
                "node_key": "aware_demo.ThingKind",
                "enum_config": {
                    "id": "thing-kind-id",
                    "name": "ThingKind",
                    "enum_options": (
                        {
                            "value": "primary",
                            "label": "primary",
                            "position": 0,
                        },
                    ),
                },
                "layouts": ({"relative_path": "thing/thing_kind.aware"},),
            },
            {
                "type": "relationship",
                "class_config_relationship": {
                    "class_config_id": "thing-class-id",
                    "target_class_config_id": "tag-class-id",
                    "relationship_key": "tags",
                    "relationship_type": "one_to_many",
                },
                "layouts": ({"relative_path": "thing/thing.aware"},),
            },
        ),
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _sequence(value: object) -> tuple[object, ...]:
    return tuple(value) if isinstance(value, tuple) else ()
