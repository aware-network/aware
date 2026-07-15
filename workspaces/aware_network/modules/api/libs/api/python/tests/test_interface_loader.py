from __future__ import annotations

import json

import pytest

from aware_api.interface import load_api_interface_spec_file, load_api_interface_spec_json


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "package_name": "home-story-api",
        "fqn_prefix": "aware_home_story_api",
        "apis": [
            {
                "name": "home_devices",
                "source_path": "apis/bindings/home.apis.aware",
                "capabilities": [
                    {
                        "name": "lock_door",
                        "source_path": "apis/bindings/home.apis.aware",
                        "description": "Lock a door.",
                        "endpoints": [
                            {
                                "name": "lock_door",
                                "source_path": "apis/bindings/home.apis.aware",
                                "discriminant": "home_devices.lock_door.lock_door",
                                "description": "Locks the selected door.",
                                "request": {
                                    "class_ref": "aware_home_api.door.LockDoor",
                                    "source_path": "apis/types/home/aware/door/endpoints.aware",
                                },
                                "response": {
                                    "class_ref": "aware_home_api.door.LockDoorResult",
                                    "source_path": "apis/types/home/aware/door/endpoints.aware",
                                },
                                "stream": {
                                    "stream_mode": "server",
                                    "source_path": "apis/bindings/home.apis.aware",
                                    "events": [
                                        {
                                            "kind": "snapshot",
                                            "class_ref": "aware_home_api.door.DoorSnapshot",
                                            "source_path": "apis/types/home/aware/door/endpoints.aware",
                                        },
                                        {
                                            "kind": "delta",
                                            "class_ref": "aware_home_api.door.DoorDelta",
                                            "source_path": "apis/types/home/aware/door/endpoints.aware",
                                        },
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_load_api_interface_spec_file_builds_index(tmp_path) -> None:
    path = tmp_path / "api.interface_spec.json"
    path.write_text(json.dumps(_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    loaded = load_api_interface_spec_file(path)

    assert loaded.source_path == path.resolve()
    assert loaded.spec.package_name == "home-story-api"
    assert len(loaded.hash_sha256) == 64

    capability = loaded.index.require_capability("home_devices", "lock_door")
    assert capability.capability_ref == "home_devices.lock_door"

    endpoint = loaded.index.require_endpoint_by_discriminant(
        "home_devices.lock_door.lock_door"
    )
    assert endpoint.api.name == "home_devices"
    assert endpoint.capability.name == "lock_door"
    assert endpoint.endpoint_ref == "home_devices.lock_door.lock_door"
    assert endpoint.endpoint.request.class_ref == "aware_home_api.door.LockDoor"
    assert endpoint.endpoint.response is not None
    assert endpoint.endpoint.response.class_ref == "aware_home_api.door.LockDoorResult"


def test_load_api_interface_spec_json_rejects_duplicate_discriminant() -> None:
    payload = _payload()
    capabilities = payload["apis"][0]["capabilities"]  # type: ignore[index]
    endpoints = capabilities[0]["endpoints"]  # type: ignore[index]
    endpoints.append(  # type: ignore[union-attr]
        {
            "name": "lock_door_again",
            "source_path": "apis/bindings/home.apis.aware",
            "discriminant": "home_devices.lock_door.lock_door",
            "request": {
                "class_ref": "aware_home_api.door.LockDoorAgain",
                "source_path": "apis/types/home/aware/door/endpoints.aware",
            },
        }
    )

    with pytest.raises(ValueError, match="Duplicate endpoint discriminant"):
        load_api_interface_spec_json(json.dumps(payload))


def test_load_api_interface_spec_json_rejects_unsupported_schema_version() -> None:
    payload = _payload()
    payload["schema_version"] = 2

    with pytest.raises(ValueError, match="Unsupported ApiInterfaceSpec schema_version"):
        load_api_interface_spec_json(json.dumps(payload))
