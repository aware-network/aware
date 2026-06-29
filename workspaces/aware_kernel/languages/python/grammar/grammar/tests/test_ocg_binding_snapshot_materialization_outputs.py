from __future__ import annotations

import msgpack

from python_grammar.materialization_outputs import (
    _dump_ocg_binding_snapshot_msgpack,
    _strip_volatile_ocg_binding_fields,
)


def _collect_code_section_keys(value: object, keys: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key.startswith("code_section_"):
                keys.add(key)
            _collect_code_section_keys(child, keys)
    elif isinstance(value, list | tuple):
        for child in value:
            _collect_code_section_keys(child, keys)


def _snapshot(*, class_section_id: str, attr_section_id: str) -> dict[str, object]:
    return {
        "id": "graph-id",
        "object_config_graph_nodes": [
            {
                "id": "node-id",
                "type": "class_",
                "node_key": "pkg.default.User",
                "class_config": {
                    "id": "class-id",
                    "code_section_class_id": class_section_id,
                    "class_fqn": "pkg.default.User",
                    "name": "User",
                    "class_config_attribute_configs": [
                        {
                            "id": "edge-id",
                            "attribute_config": {
                                "id": "attribute-id",
                                "code_section_attribute_id": attr_section_id,
                                "name": "name",
                                "is_required": True,
                            },
                        }
                    ],
                },
            }
        ],
    }


def test_ocg_binding_snapshot_ignores_volatile_code_section_fields() -> None:
    first = _dump_ocg_binding_snapshot_msgpack(
        object_config_graph=_snapshot(
            class_section_id="volatile-class-section-a",
            attr_section_id="volatile-attribute-section-a",
        )
    )
    second = _dump_ocg_binding_snapshot_msgpack(
        object_config_graph=_snapshot(
            class_section_id="volatile-class-section-b",
            attr_section_id="volatile-attribute-section-b",
        )
    )

    assert first == second

    payload = msgpack.unpackb(first, raw=False)
    assert payload["version"] == 1
    assert payload["object_config_graph_nodes"][0]["class_config"]["id"] == "class-id"
    assert (
        payload["object_config_graph_nodes"][0]["class_config"]["class_config_attribute_configs"][0][
            "attribute_config"
        ]["id"]
        == "attribute-id"
    )
    found: set[str] = set()
    _collect_code_section_keys(payload, found)
    assert not found


def test_ocg_binding_snapshot_clean_payload_uses_original_subtrees() -> None:
    clean = {
        "object_config_graph_nodes": [
            {
                "id": "node-id",
                "class_config": {
                    "id": "class-id",
                    "name": "User",
                },
            }
        ]
    }

    nodes = clean["object_config_graph_nodes"]
    assert _strip_volatile_ocg_binding_fields(nodes) is nodes
