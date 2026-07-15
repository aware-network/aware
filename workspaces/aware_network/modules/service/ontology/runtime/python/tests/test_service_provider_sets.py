from __future__ import annotations

import json
from uuid import UUID

from aware_service_runtime.service_api_dependency_routes import (
    ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY,
    ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
)
from aware_service_runtime.service_provider_sets import (
    SERVICE_API_PROVIDER_SET_CONTRACT_VERSION,
    ServiceApiProviderRef,
    ServiceApiProviderSet,
    build_ontology_authority_catalog,
    load_service_api_provider_set,
    service_api_provider_refs_from_provider_sets,
    service_api_provider_refs_from_payload,
    service_api_provider_refs_to_json,
    write_service_api_provider_set,
)


def test_service_api_provider_set_round_trips_remote_provider_refs(tmp_path):
    provider_ref = ServiceApiProviderRef(
        provider_node_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        provider_node_package="kernel-services-node",
        provider_node_base_url="ws://127.0.0.1:8912",
        provider_node_runtime_source={
            "source_kind": "node_ontology_manifest",
            "ontology_targets": [{"package_name": "storage-ontology"}],
            "environment_targets": [],
        },
        service_package_ref={
            "family_key": "service",
            "package_kind": "service",
            "package_name": "aware-experience-service",
            "semantic_package_id": "11111111-1111-1111-1111-111111111111",
        },
    )
    provider_set = ServiceApiProviderSet(
        provider_set_id="kernel.global_services.v1",
        workspace_revision_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        workspace_deployment_revision_id="workspace-deployment:kernel:1",
        workspace_deployment_channel="stable",
        workspace_deployment_artifact_key="kernel-services-node",
        provider_refs=(provider_ref,),
    )

    path = write_service_api_provider_set(
        path=tmp_path / "kernel-services-provider-set.json",
        provider_set=provider_set,
    )

    loaded = load_service_api_provider_set(path)
    assert loaded.contract_version == SERVICE_API_PROVIDER_SET_CONTRACT_VERSION
    assert loaded.provider_set_id == "kernel.global_services.v1"
    assert loaded.provider_refs == (provider_ref,)

    provider_refs_json = service_api_provider_refs_to_json(loaded.provider_refs)
    provider_refs_payload = json.loads(provider_refs_json)
    assert provider_refs_payload == [
        {
            "provider_node_base_url": "ws://127.0.0.1:8912",
            "provider_node_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "provider_node_package": "kernel-services-node",
            "provider_node_runtime_source": {
                "environment_targets": [],
                "ontology_targets": [{"package_name": "storage-ontology"}],
                "source_kind": "node_ontology_manifest",
            },
            "service_package_ref": {
                "family_key": "service",
                "package_kind": "service",
                "package_name": "aware-experience-service",
                "semantic_package_id": "11111111-1111-1111-1111-111111111111",
            },
        }
    ]
    assert service_api_provider_refs_from_payload(provider_refs_payload) == (
        provider_ref,
    )

    flattened_refs = service_api_provider_refs_from_provider_sets((loaded,))
    assert len(flattened_refs) == 1
    flattened_ref = flattened_refs[0]
    assert flattened_ref.authority is not None
    assert flattened_ref.authority.provider_set_id == "kernel.global_services.v1"
    assert flattened_ref.authority.workspace_revision_id == UUID(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )
    assert (
        flattened_ref.authority.workspace_deployment_revision_id
        == "workspace-deployment:kernel:1"
    )
    assert flattened_ref.authority.workspace_deployment_channel == "stable"
    assert (
        flattened_ref.authority.workspace_deployment_artifact_key
        == "kernel-services-node"
    )
    assert flattened_ref.authority.metadata == {
        ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY: {
            "schema": ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
            "source_kind": "node_ontology_manifest",
            "ontology_package_names": ["storage-ontology"],
            "ontology_targets": [{"package_name": "storage-ontology"}],
        }
    }

    flattened_payload = service_api_provider_refs_from_payload(
        json.loads(service_api_provider_refs_to_json(flattened_refs))
    )
    assert flattened_payload == flattened_refs


def test_build_ontology_authority_catalog_normalizes_runtime_source_targets():
    catalog = build_ontology_authority_catalog(
        {
            "source_kind": "node_ontology_manifest",
            "ontology_targets": [
                {"package_name": "content-ontology", "fqn_prefix": "aware_content"},
                {"package_name": "storage-ontology"},
                {"package_name": "content-ontology", "fqn_prefix": "aware_content"},
                {"package_name": "  "},
                "not-a-target",
            ],
        }
    )

    assert catalog == {
        "schema": ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
        "source_kind": "node_ontology_manifest",
        "ontology_package_names": ["content-ontology", "storage-ontology"],
        "ontology_targets": [
            {
                "fqn_prefix": "aware_content",
                "package_name": "content-ontology",
            },
            {"package_name": "storage-ontology"},
        ],
        "fqn_prefixes": ["aware_content"],
    }
