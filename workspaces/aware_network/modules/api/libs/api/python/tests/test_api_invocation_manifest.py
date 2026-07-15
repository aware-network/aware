from __future__ import annotations

import json
from typing import Any, cast

import pytest

from aware_api.invocation import (
    load_api_invocation_manifest_file,
    load_api_invocation_manifest_json,
)


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
                        "description": "Lock the front door.",
                        "endpoints": [
                            {
                                "name": "lock_door",
                                "source_path": "apis/bindings/home.apis.aware",
                                "endpoint_ref": "home_devices.lock_door.lock_door",
                                "discriminant": "home_devices.lock_door.lock_door",
                                "invocation_kind": "shared_client_endpoint",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "addressing_strategy": "session_bound",
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
                                        }
                                    ],
                                },
                                "fulfillment_bindings": [
                                    {
                                        "name": "lock",
                                        "graph_target": "aware_home",
                                        "graph_capability_function_name": "lock",
                                        "source_path": "apis/bindings/home.apis.aware",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_load_api_invocation_manifest_file_builds_index(tmp_path) -> None:
    path = tmp_path / "api.invocation_manifest.json"
    path.write_text(json.dumps(_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    loaded = load_api_invocation_manifest_file(path)

    assert loaded.source_path == path.resolve()
    assert loaded.manifest.package_name == "home-story-api"
    assert len(loaded.hash_sha256) == 64

    endpoint = loaded.index.require_endpoint_by_ref("home_devices.lock_door.lock_door")
    assert endpoint.endpoint.discriminant == "home_devices.lock_door.lock_door"
    assert endpoint.endpoint.client_operation == "invoke_api_endpoint"
    assert endpoint.endpoint.request.class_ref == "aware_home_api.door.LockDoor"
    assert endpoint.endpoint.response is not None
    assert endpoint.endpoint.response.class_ref == "aware_home_api.door.LockDoorResult"


def test_load_api_invocation_manifest_accepts_runtime_model_refs() -> None:
    payload = _payload()
    endpoint = payload["apis"][0]["capabilities"][0]["endpoints"][0]  # type: ignore[index]
    endpoint["request"]["python_model_ref"] = "aware_home_story_api.models.lock_door.LockDoor"  # type: ignore[index]
    endpoint["response"]["python_model_ref"] = "aware_home_story_api.models.lock_door_result.LockDoorResult"  # type: ignore[index]
    endpoint["stream"]["events"][0]["python_model_ref"] = "aware_home_story_api.models.door_snapshot.DoorSnapshot"  # type: ignore[index]

    loaded = load_api_invocation_manifest_json(json.dumps(payload))
    endpoint_spec = loaded.index.require_endpoint_by_ref("home_devices.lock_door.lock_door").endpoint

    assert endpoint_spec.request.python_model_ref == "aware_home_story_api.models.lock_door.LockDoor"
    assert endpoint_spec.response is not None
    assert endpoint_spec.response.python_model_ref == (
        "aware_home_story_api.models.lock_door_result.LockDoorResult"
    )
    assert endpoint_spec.stream is not None
    assert endpoint_spec.stream.events[0].python_model_ref == (
        "aware_home_story_api.models.door_snapshot.DoorSnapshot"
    )


def test_load_api_invocation_manifest_json_rejects_duplicate_endpoint_ref() -> None:
    payload = cast(dict[str, Any], _payload())
    endpoints = payload["apis"][0]["capabilities"][0]["endpoints"]  # type: ignore[index]
    endpoints.append(  # type: ignore[union-attr]
        {
            "name": "lock_door_again",
            "source_path": "apis/bindings/home.apis.aware",
            "endpoint_ref": "home_devices.lock_door.lock_door",
            "discriminant": "home_devices.lock_door.lock_door_again",
            "invocation_kind": "shared_client_endpoint",
            "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
            "client_operation": "invoke_api_endpoint",
            "addressing_strategy": "session_bound",
            "request": {
                "class_ref": "aware_home_api.door.LockDoorAgain",
                "source_path": "apis/types/home/aware/door/endpoints.aware",
            },
        }
    )

    with pytest.raises(ValueError, match="Duplicate endpoint ref"):
        load_api_invocation_manifest_json(json.dumps(payload))


def test_load_api_invocation_manifest_json_rejects_unsupported_schema_version() -> None:
    payload = _payload()
    payload["schema_version"] = 2

    with pytest.raises(ValueError, match="Unsupported ApiInvocationManifest schema_version"):
        load_api_invocation_manifest_json(json.dumps(payload))
