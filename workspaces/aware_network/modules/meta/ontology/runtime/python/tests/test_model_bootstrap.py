from __future__ import annotations

from aware_meta.graph.config.model_bootstrap import (
    normalize_environment_config_payload_for_bootstrap,
)


def test_normalize_environment_payload_derives_class_and_node_identity_fields() -> None:
    class_node_id = "11111111-1111-1111-1111-111111111111"
    function_node_id = "22222222-2222-2222-2222-222222222222"
    relationship_node_id = "33333333-3333-3333-3333-333333333333"
    class_config_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    function_config_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    relationship_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    payload = {
        "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
        "object_config_graphs": [
            {
                "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                "fqn_prefix": "aware_meta_ontology",
                "object_config_graph_nodes": [
                    {
                        "id": class_node_id,
                        "type": "class",
                        "class_config_id": class_config_id,
                        "class_config": {
                            "id": class_config_id,
                            "name": "ClassConfig",
                            "class_fqn": "aware_meta_ontology.class_.ClassConfig",
                            "class_config_attribute_configs": [],
                            "class_config_relationships": [],
                            "class_config_function_configs": [
                                {
                                    "function_config_id": function_config_id,
                                    "function_config": {
                                        "id": function_config_id,
                                        "name": "create",
                                        "kind": "constructor",
                                    },
                                }
                            ],
                        },
                    },
                    {
                        "id": function_node_id,
                        "type": "function",
                        "function_config_id": function_config_id,
                        "function_config": {
                            "id": function_config_id,
                            "name": "create",
                            "kind": "constructor",
                        },
                    },
                    {
                        "id": relationship_node_id,
                        "type": "relationship",
                        "class_config_relationship_id": relationship_id,
                        "class_config_relationship": {
                            "id": relationship_id,
                            "class_config_id": class_config_id,
                            "target_class_config_id": class_config_id,
                            "relationship_type": "one_to_many",
                            "class_config_relationship_attributes": [
                                {
                                    "direction": "forward",
                                    "role": "reference",
                                    "attribute_config": {
                                        "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                                        "name": "children",
                                    },
                                }
                            ],
                        },
                    },
                ],
            }
        ],
    }

    normalized = normalize_environment_config_payload_for_bootstrap(payload=payload)
    graph = normalized["object_config_graphs"][0]
    class_node = graph["object_config_graph_nodes"][0]
    function_node = graph["object_config_graph_nodes"][1]
    relationship_node = graph["object_config_graph_nodes"][2]

    expected_class_fqn = "aware_meta_ontology.class_.ClassConfig"
    assert class_node["class_config"]["class_fqn"] == expected_class_fqn
    assert class_node["class_config"]["object_config_graph_node_id"] == class_node_id
    assert class_node["node_key"] == expected_class_fqn
    assert function_node["node_key"] == f"{expected_class_fqn}:constructor:create"
    assert (
        relationship_node["class_config_relationship"]["relationship_key"] == "children"
    )
    assert relationship_node["node_key"] == (
        f"{expected_class_fqn}:children:one_to_many:{expected_class_fqn}"
    )
