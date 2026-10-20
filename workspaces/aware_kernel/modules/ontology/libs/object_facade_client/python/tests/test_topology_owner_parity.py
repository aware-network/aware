"""Frozen-parent wire parity and the exact retained host definition surface."""

import ast
import dataclasses
import hashlib
import json
from pathlib import Path

import pytest
from aware_meta_type_schema import decode_schema_slice
from aware_ontology_object_facade_client import owner_values as owner
from aware_ontology_object_facade_client import topology_codec as codec
from aware_ontology_object_facade_client import topology_values as values
from test_owner_body_parity import _legacy_scan, _scan_cells

# Independently generated in an isolated, clean d7efa7d71bd109b1dea638119669917dbb7781ab
# source cut. All loaded Aware modules were checked against that cut; no evaluator.
FROZEN_VECTORS = [
    {
        "name": "association_external",
        "schema": {
            "bundle_digest": "sha256:45ae3c53a29579359af087152f1234d044c112550c84bb7071590b3877c87530",
            "contract": "aware.meta.semantic-type-schema-slice.v1",
            "namespace": "aware_demo",
            "root_type_refs": [
                "aware_content.ContentPart",
                "aware_content.ContentPartFile",
                "aware_content.InlineLabel",
                "aware_demo.Door",
                "aware_demo.Home",
                "aware_storage.StorageBlob",
            ],
            "semantic_version": "1.0.0",
            "slice_digest": "sha256:5cea2e82ecf9c5dacffa8fd1d544f0bd0887ada25f037ecc0645230e860e64c5",
            "types": [
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPart.name",
                            "has_default": False,
                            "name": "name",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPart.storage_blobs",
                            "has_default": False,
                            "name": "storage_blobs",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": {
                                    "element": None,
                                    "kind": "named",
                                    "map_value": None,
                                    "scalar_kind": None,
                                    "type_ref": "aware_content.ContentPartFile",
                                    "variants": [],
                                },
                                "kind": "list",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_content.ContentPart.name"]},
                    "kind": "graph_object",
                    "name": "ContentPart",
                    "scalar_target": None,
                    "type_ref": "aware_content.ContentPart",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.path",
                            "has_default": False,
                            "name": "path",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.storage_blob",
                            "has_default": False,
                            "name": "storage_blob",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "named",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": "aware_storage.StorageBlob",
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.content_part",
                            "has_default": False,
                            "name": "content_part",
                            "nullable": True,
                            "required": False,
                            "shape": {
                                "element": None,
                                "kind": "named",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": "aware_content.ContentPart",
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_content.ContentPartFile.path"]},
                    "kind": "graph_object",
                    "name": "ContentPartFile",
                    "scalar_target": None,
                    "type_ref": "aware_content.ContentPartFile",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [],
                    "identity": None,
                    "kind": "value_object",
                    "name": "InlineLabel",
                    "scalar_target": None,
                    "type_ref": "aware_content.InlineLabel",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Door.label",
                            "has_default": False,
                            "name": "label",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        }
                    ],
                    "identity": {"field_refs": ["aware_demo.Door.label"]},
                    "kind": "graph_object",
                    "name": "Door",
                    "scalar_target": None,
                    "type_ref": "aware_demo.Door",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Home.name",
                            "has_default": False,
                            "name": "name",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Home.doors",
                            "has_default": False,
                            "name": "doors",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": {
                                    "element": None,
                                    "kind": "named",
                                    "map_value": None,
                                    "scalar_kind": None,
                                    "type_ref": "aware_demo.Door",
                                    "variants": [],
                                },
                                "kind": "list",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_demo.Home.name"]},
                    "kind": "graph_object",
                    "name": "Home",
                    "scalar_target": None,
                    "type_ref": "aware_demo.Home",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_storage.StorageBlob.id",
                            "has_default": False,
                            "name": "id",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        }
                    ],
                    "identity": {"field_refs": ["aware_storage.StorageBlob.id"]},
                    "kind": "graph_object",
                    "name": "StorageBlob",
                    "scalar_target": None,
                    "type_ref": "aware_storage.StorageBlob",
                    "union_variants": [],
                },
            ],
        },
        "sha256": "b6325df5fc8fc3ebaeae385743b783b9edc586c8dfe04860a41fd75081769311",
        "size": 3098,
        "topology": {
            "actions": [],
            "contract": "aware.ontology.runtime-schema-topology.v5",
            "graph_types": [
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_content.ContentPart.name"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_content.ContentPart",
                },
                {
                    "association_role_refs": [
                        "aware_content.ContentPartFile.storage_blob"
                    ],
                    "identity_field_refs": ["aware_content.ContentPartFile.path"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_content.ContentPartFile",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_demo.Door.label"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_demo.Door",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_demo.Home.name"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": ["aware_demo.Home.doors"],
                    "type_ref": "aware_demo.Home",
                },
            ],
            "input_grade": "portable_input",
            "namespace": "aware_demo",
            "projections": [
                {
                    "action_refs": [],
                    "field_refs": [
                        "aware_content.ContentPart.name",
                        "aware_content.ContentPartFile.path",
                    ],
                    "projection_ref": "aware_content.projection.Content.content",
                    "relationship_refs": ["aware_content.ContentPartFile.storage_blob"],
                    "root_type_refs": ["aware_content.ContentPart"],
                    "type_refs": [
                        "aware_content.ContentPart",
                        "aware_content.ContentPartFile",
                    ],
                }
            ],
            "relationships": [
                {
                    "association_role_digest": "sha256:association-role",
                    "association_type_ref": "aware_content.ContentPartFile",
                    "direction": "association_to_target",
                    "endpoint_cardinality": "one",
                    "endpoint_residence": "external_dependency",
                    "input_kind": "association_endpoint_role",
                    "meaning_resolution_digest": "sha256:meaning-resolution",
                    "member_name": "storage_blob",
                    "projection_role_coordinate": "projection-role:content-file-storage",
                    "relationship_semantics": "reference",
                    "role_ref": "aware_content.ContentPartFile.storage_blob",
                    "schema_evidence_ref": "sha256:schema-evidence",
                    "selecting_projection_ref": "aware_content.projection.Content.content",
                    "source_field_ref": "aware_content.ContentPartFile.storage_blob",
                    "source_type_ref": "aware_content.ContentPartFile",
                    "target_package_ref": "package:aware_storage@1.0.0",
                    "target_type_ref": "aware_storage.StorageBlob",
                    "traversal": "source_to_target",
                },
                {
                    "endpoint_residence": "resident_target",
                    "input_kind": "schema_field_relationship",
                    "relationship_kind": "containment",
                    "relationship_ref": "aware_demo.Home.doors",
                    "schema_evidence_ref": "sha256:home-doors-schema-evidence",
                    "source_cardinality": "many",
                    "source_type_ref": "aware_demo.Home",
                    "target_cardinality": "one",
                    "target_package_ref": "package:demo-ontology",
                    "target_type_ref": "aware_demo.Door",
                    "traversal": "bidirectional",
                },
            ],
            "schema_digest": "sha256:45ae3c53a29579359af087152f1234d044c112550c84bb7071590b3877c87530",
            "schema_root_type_refs": [
                "aware_content.ContentPart",
                "aware_content.ContentPartFile",
                "aware_content.InlineLabel",
                "aware_demo.Door",
                "aware_demo.Home",
                "aware_storage.StorageBlob",
            ],
            "schema_slice_digest": "sha256:5cea2e82ecf9c5dacffa8fd1d544f0bd0887ada25f037ecc0645230e860e64c5",
            "semantic_version": "1.0.0",
            "topology_digest": "sha256:15bc5432e9ece3349cb458605c266a908eadb7ec697754367caf73450b70e84a",
        },
    },
    {
        "name": "association_resident",
        "schema": {
            "bundle_digest": "sha256:45ae3c53a29579359af087152f1234d044c112550c84bb7071590b3877c87530",
            "contract": "aware.meta.semantic-type-schema-slice.v1",
            "namespace": "aware_demo",
            "root_type_refs": [
                "aware_content.ContentPart",
                "aware_content.ContentPartFile",
                "aware_content.InlineLabel",
                "aware_demo.Door",
                "aware_demo.Home",
                "aware_storage.StorageBlob",
            ],
            "semantic_version": "1.0.0",
            "slice_digest": "sha256:5cea2e82ecf9c5dacffa8fd1d544f0bd0887ada25f037ecc0645230e860e64c5",
            "types": [
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPart.name",
                            "has_default": False,
                            "name": "name",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPart.storage_blobs",
                            "has_default": False,
                            "name": "storage_blobs",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": {
                                    "element": None,
                                    "kind": "named",
                                    "map_value": None,
                                    "scalar_kind": None,
                                    "type_ref": "aware_content.ContentPartFile",
                                    "variants": [],
                                },
                                "kind": "list",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_content.ContentPart.name"]},
                    "kind": "graph_object",
                    "name": "ContentPart",
                    "scalar_target": None,
                    "type_ref": "aware_content.ContentPart",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.path",
                            "has_default": False,
                            "name": "path",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.storage_blob",
                            "has_default": False,
                            "name": "storage_blob",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "named",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": "aware_storage.StorageBlob",
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.content_part",
                            "has_default": False,
                            "name": "content_part",
                            "nullable": True,
                            "required": False,
                            "shape": {
                                "element": None,
                                "kind": "named",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": "aware_content.ContentPart",
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_content.ContentPartFile.path"]},
                    "kind": "graph_object",
                    "name": "ContentPartFile",
                    "scalar_target": None,
                    "type_ref": "aware_content.ContentPartFile",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [],
                    "identity": None,
                    "kind": "value_object",
                    "name": "InlineLabel",
                    "scalar_target": None,
                    "type_ref": "aware_content.InlineLabel",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Door.label",
                            "has_default": False,
                            "name": "label",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        }
                    ],
                    "identity": {"field_refs": ["aware_demo.Door.label"]},
                    "kind": "graph_object",
                    "name": "Door",
                    "scalar_target": None,
                    "type_ref": "aware_demo.Door",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Home.name",
                            "has_default": False,
                            "name": "name",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Home.doors",
                            "has_default": False,
                            "name": "doors",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": {
                                    "element": None,
                                    "kind": "named",
                                    "map_value": None,
                                    "scalar_kind": None,
                                    "type_ref": "aware_demo.Door",
                                    "variants": [],
                                },
                                "kind": "list",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_demo.Home.name"]},
                    "kind": "graph_object",
                    "name": "Home",
                    "scalar_target": None,
                    "type_ref": "aware_demo.Home",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_storage.StorageBlob.id",
                            "has_default": False,
                            "name": "id",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        }
                    ],
                    "identity": {"field_refs": ["aware_storage.StorageBlob.id"]},
                    "kind": "graph_object",
                    "name": "StorageBlob",
                    "scalar_target": None,
                    "type_ref": "aware_storage.StorageBlob",
                    "union_variants": [],
                },
            ],
        },
        "sha256": "4d4d25f36f33d8f4f30c3a8fb629383e1f29ce1ff5c8feef17048a989ba3942d",
        "size": 3123,
        "topology": {
            "actions": [],
            "contract": "aware.ontology.runtime-schema-topology.v5",
            "graph_types": [
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_content.ContentPart.name"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_content.ContentPart",
                },
                {
                    "association_role_refs": [
                        "aware_content.ContentPartFile.content_part"
                    ],
                    "identity_field_refs": ["aware_content.ContentPartFile.path"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_content.ContentPartFile",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_demo.Door.label"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_demo.Door",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_demo.Home.name"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": ["aware_demo.Home.doors"],
                    "type_ref": "aware_demo.Home",
                },
            ],
            "input_grade": "portable_input",
            "namespace": "aware_demo",
            "projections": [
                {
                    "action_refs": [],
                    "field_refs": [
                        "aware_content.ContentPart.name",
                        "aware_content.ContentPartFile.path",
                    ],
                    "projection_ref": "aware_content.projection.Content.content",
                    "relationship_refs": ["aware_content.ContentPartFile.content_part"],
                    "root_type_refs": ["aware_content.ContentPart"],
                    "type_refs": [
                        "aware_content.ContentPart",
                        "aware_content.ContentPartFile",
                    ],
                }
            ],
            "relationships": [
                {
                    "association_role_digest": "sha256:resident-association-role",
                    "association_type_ref": "aware_content.ContentPartFile",
                    "direction": "association_to_target",
                    "endpoint_cardinality": "optional_one",
                    "endpoint_residence": "resident_target",
                    "input_kind": "association_endpoint_role",
                    "meaning_resolution_digest": "sha256:meaning-resolution",
                    "member_name": "content_part",
                    "projection_role_coordinate": "projection-role:content-file-content-part",
                    "relationship_semantics": "reference",
                    "role_ref": "aware_content.ContentPartFile.content_part",
                    "schema_evidence_ref": "sha256:resident-schema-evidence",
                    "selecting_projection_ref": "aware_content.projection.Content.content",
                    "source_field_ref": "aware_content.ContentPartFile.content_part",
                    "source_type_ref": "aware_content.ContentPartFile",
                    "target_package_ref": "package:aware_content@1.0.0",
                    "target_type_ref": "aware_content.ContentPart",
                    "traversal": "bidirectional",
                },
                {
                    "endpoint_residence": "resident_target",
                    "input_kind": "schema_field_relationship",
                    "relationship_kind": "containment",
                    "relationship_ref": "aware_demo.Home.doors",
                    "schema_evidence_ref": "sha256:home-doors-schema-evidence",
                    "source_cardinality": "many",
                    "source_type_ref": "aware_demo.Home",
                    "target_cardinality": "one",
                    "target_package_ref": "package:demo-ontology",
                    "target_type_ref": "aware_demo.Door",
                    "traversal": "bidirectional",
                },
            ],
            "schema_digest": "sha256:45ae3c53a29579359af087152f1234d044c112550c84bb7071590b3877c87530",
            "schema_root_type_refs": [
                "aware_content.ContentPart",
                "aware_content.ContentPartFile",
                "aware_content.InlineLabel",
                "aware_demo.Door",
                "aware_demo.Home",
                "aware_storage.StorageBlob",
            ],
            "schema_slice_digest": "sha256:5cea2e82ecf9c5dacffa8fd1d544f0bd0887ada25f037ecc0645230e860e64c5",
            "semantic_version": "1.0.0",
            "topology_digest": "sha256:96718028606f2005abb889ce6527ac7e3d091c4c168fb0e9199239548745d6da",
        },
    },
    {
        "name": "schema_external",
        "schema": {
            "bundle_digest": "sha256:45ae3c53a29579359af087152f1234d044c112550c84bb7071590b3877c87530",
            "contract": "aware.meta.semantic-type-schema-slice.v1",
            "namespace": "aware_demo",
            "root_type_refs": [
                "aware_content.ContentPart",
                "aware_content.ContentPartFile",
                "aware_content.InlineLabel",
                "aware_demo.Door",
                "aware_demo.Home",
                "aware_storage.StorageBlob",
            ],
            "semantic_version": "1.0.0",
            "slice_digest": "sha256:5cea2e82ecf9c5dacffa8fd1d544f0bd0887ada25f037ecc0645230e860e64c5",
            "types": [
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPart.name",
                            "has_default": False,
                            "name": "name",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPart.storage_blobs",
                            "has_default": False,
                            "name": "storage_blobs",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": {
                                    "element": None,
                                    "kind": "named",
                                    "map_value": None,
                                    "scalar_kind": None,
                                    "type_ref": "aware_content.ContentPartFile",
                                    "variants": [],
                                },
                                "kind": "list",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_content.ContentPart.name"]},
                    "kind": "graph_object",
                    "name": "ContentPart",
                    "scalar_target": None,
                    "type_ref": "aware_content.ContentPart",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.path",
                            "has_default": False,
                            "name": "path",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.storage_blob",
                            "has_default": False,
                            "name": "storage_blob",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "named",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": "aware_storage.StorageBlob",
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_content.ContentPartFile.content_part",
                            "has_default": False,
                            "name": "content_part",
                            "nullable": True,
                            "required": False,
                            "shape": {
                                "element": None,
                                "kind": "named",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": "aware_content.ContentPart",
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_content.ContentPartFile.path"]},
                    "kind": "graph_object",
                    "name": "ContentPartFile",
                    "scalar_target": None,
                    "type_ref": "aware_content.ContentPartFile",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [],
                    "identity": None,
                    "kind": "value_object",
                    "name": "InlineLabel",
                    "scalar_target": None,
                    "type_ref": "aware_content.InlineLabel",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Door.label",
                            "has_default": False,
                            "name": "label",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        }
                    ],
                    "identity": {"field_refs": ["aware_demo.Door.label"]},
                    "kind": "graph_object",
                    "name": "Door",
                    "scalar_target": None,
                    "type_ref": "aware_demo.Door",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Home.name",
                            "has_default": False,
                            "name": "name",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_demo.Home.doors",
                            "has_default": False,
                            "name": "doors",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": {
                                    "element": None,
                                    "kind": "named",
                                    "map_value": None,
                                    "scalar_kind": None,
                                    "type_ref": "aware_demo.Door",
                                    "variants": [],
                                },
                                "kind": "list",
                                "map_value": None,
                                "scalar_kind": None,
                                "type_ref": None,
                                "variants": [],
                            },
                        },
                    ],
                    "identity": {"field_refs": ["aware_demo.Home.name"]},
                    "kind": "graph_object",
                    "name": "Home",
                    "scalar_target": None,
                    "type_ref": "aware_demo.Home",
                    "union_variants": [],
                },
                {
                    "aliases": [],
                    "constraints": {},
                    "discriminant_field_ref": None,
                    "enum_values": [],
                    "fields": [
                        {
                            "aliases": [],
                            "constraints": {},
                            "default_value": None,
                            "field_ref": "aware_storage.StorageBlob.id",
                            "has_default": False,
                            "name": "id",
                            "nullable": False,
                            "required": True,
                            "shape": {
                                "element": None,
                                "kind": "scalar",
                                "map_value": None,
                                "scalar_kind": "string",
                                "type_ref": None,
                                "variants": [],
                            },
                        }
                    ],
                    "identity": {"field_refs": ["aware_storage.StorageBlob.id"]},
                    "kind": "graph_object",
                    "name": "StorageBlob",
                    "scalar_target": None,
                    "type_ref": "aware_storage.StorageBlob",
                    "union_variants": [],
                },
            ],
        },
        "sha256": "65c32a101bc240eca6e3802a86bf4a6ff5bd71cb5a00a345bb9aeda5db5a78d3",
        "size": 2711,
        "topology": {
            "actions": [],
            "contract": "aware.ontology.runtime-schema-topology.v5",
            "graph_types": [
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_content.ContentPart.name"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_content.ContentPart",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_content.ContentPartFile.path"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [
                        "aware_content.ContentPartFile.storage_blob"
                    ],
                    "type_ref": "aware_content.ContentPartFile",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_demo.Door.label"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": [],
                    "type_ref": "aware_demo.Door",
                },
                {
                    "association_role_refs": [],
                    "identity_field_refs": ["aware_demo.Home.name"],
                    "identity_mode": "schema_fields",
                    "schema_relationship_field_refs": ["aware_demo.Home.doors"],
                    "type_ref": "aware_demo.Home",
                },
            ],
            "input_grade": "portable_input",
            "namespace": "aware_demo",
            "projections": [
                {
                    "action_refs": [],
                    "field_refs": [
                        "aware_content.ContentPart.name",
                        "aware_content.ContentPartFile.path",
                    ],
                    "projection_ref": "aware_content.projection.Content.content",
                    "relationship_refs": ["aware_content.ContentPartFile.storage_blob"],
                    "root_type_refs": ["aware_content.ContentPart"],
                    "type_refs": [
                        "aware_content.ContentPart",
                        "aware_content.ContentPartFile",
                    ],
                }
            ],
            "relationships": [
                {
                    "endpoint_residence": "external_dependency",
                    "input_kind": "schema_field_relationship",
                    "relationship_kind": "reference",
                    "relationship_ref": "aware_content.ContentPartFile.storage_blob",
                    "schema_evidence_ref": "sha256:external-schema-field-evidence",
                    "source_cardinality": "one",
                    "source_type_ref": "aware_content.ContentPartFile",
                    "target_cardinality": "one",
                    "target_package_ref": "package:aware_storage@1.0.0",
                    "target_type_ref": "aware_storage.StorageBlob",
                    "traversal": "source_to_target",
                },
                {
                    "endpoint_residence": "resident_target",
                    "input_kind": "schema_field_relationship",
                    "relationship_kind": "containment",
                    "relationship_ref": "aware_demo.Home.doors",
                    "schema_evidence_ref": "sha256:home-doors-schema-evidence",
                    "source_cardinality": "many",
                    "source_type_ref": "aware_demo.Home",
                    "target_cardinality": "one",
                    "target_package_ref": "package:demo-ontology",
                    "target_type_ref": "aware_demo.Door",
                    "traversal": "bidirectional",
                },
            ],
            "schema_digest": "sha256:45ae3c53a29579359af087152f1234d044c112550c84bb7071590b3877c87530",
            "schema_root_type_refs": [
                "aware_content.ContentPart",
                "aware_content.ContentPartFile",
                "aware_content.InlineLabel",
                "aware_demo.Door",
                "aware_demo.Home",
                "aware_storage.StorageBlob",
            ],
            "schema_slice_digest": "sha256:5cea2e82ecf9c5dacffa8fd1d544f0bd0887ada25f037ecc0645230e860e64c5",
            "semantic_version": "1.0.0",
            "topology_digest": "sha256:55d77a65ca9cdc37ae4a01599b4589db8dfd7112f31ba02d0140263f24db0a4a",
        },
    },
]


@pytest.mark.parametrize("vector", FROZEN_VECTORS, ids=lambda v: v["name"])
def test_frozen_parent_roundtrip(vector):
    canonical = json.dumps(
        vector["topology"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    assert len(canonical) == vector["size"]
    assert hashlib.sha256(canonical).hexdigest() == vector["sha256"]
    schema = decode_schema_slice(json.dumps(vector["schema"]).encode())
    topology = codec.decode_schema_topology_manifest(canonical, schema)
    assert codec.encode_schema_topology_manifest(topology, schema) == canonical
    assert topology.to_wire() == vector["topology"]
    for field in dataclasses.fields(topology):
        assert field.name in vector["topology"]


def test_record_flags_fields_and_enum_values_are_unchanged():
    assert [(m.name, m.value) for m in owner.RelationshipKind] == [
        ("REFERENCE", "reference"),
        ("CONTAINMENT", "containment"),
    ]
    assert [(m.name, m.value) for m in values.GraphIdentityMode] == [
        ("SCHEMA_FIELDS", "schema_fields"),
        ("INSTANCE_REF", "instance_ref"),
    ]
    expected = {
        values.GraphTypeBinding: (
            "type_ref",
            "identity_mode",
            "identity_field_refs",
            "schema_relationship_field_refs",
            "association_role_refs",
        ),
        owner.ProjectionDefinition: (
            "projection_ref",
            "root_type_refs",
            "type_refs",
            "field_refs",
            "relationship_refs",
            "action_refs",
        ),
        values.SchemaOntologyRuntimeTopology: (
            "namespace",
            "semantic_version",
            "schema_digest",
            "schema_slice_digest",
            "schema_root_type_refs",
            "graph_types",
            "relationships",
            "projections",
            "actions",
            "input_grade",
            "topology_digest",
        ),
    }
    for cls, fields in expected.items():
        assert tuple(f.name for f in dataclasses.fields(cls)) == fields
        assert cls.__slots__ == fields
        assert cls.__dataclass_params__.frozen and cls.__dataclass_params__.eq
    assert vars(values.GraphTypeBinding)["__dataclass_params__"].order
    assert not vars(owner.ProjectionDefinition)["__dataclass_params__"].order
    assert not vars(values.SchemaOntologyRuntimeTopology)["__dataclass_params__"].order


def test_all_64_unselected_host_definitions_retain_frozen_body_bytes():
    root = Path(__file__).resolve().parents[8]
    evidence = json.loads(
        root.joinpath(
            "docs/reports/ontology-facade-topology-decoder-evidence-20261004.json"
        ).read_text()
    )
    retained = evidence["retained_host_slices"]
    assert len(retained) == 64
    for row in retained:
        body = root.joinpath(row["path"]).read_text()
        nodes = {
            n.name: n
            for n in ast.parse(body).body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        node = nodes[row["name"]]
        start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
        raw = "".join(
            body.splitlines(keepends=True)[start - 1 : node.end_lineno]
        ).encode()
        assert len(raw) == row["size"], row["name"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256"], row["name"]


@pytest.mark.parametrize("change", ("clean", "module_value", "class_member", "code", "defaults", "kwdefaults", "cell", "container", "list", "primitive_port"))
def test_topology_complete_scan_matches_original_comparator(monkeypatch, change):
    checked = _scan_cells(values._call)["checked"]
    current = _scan_cells(checked)["guard"]
    original = _legacy_scan(current, values, 1219)
    current()
    original()
    state = _scan_cells(current)
    calls = []
    list_target = None
    def foreign(*_args, **_kwargs):
        calls.append("foreign")
        raise AssertionError("scanner dispatched foreign behavior")
    with monkeypatch.context() as patch:
        if change == "module_value":
            patch.setattr(values, "SCHEMA_TOPOLOGY_CONTRACT", foreign)
        elif change == "class_member":
            patch.setattr(values.GraphTypeBinding, "_scan_extra", foreign, raising=False)
        elif change in ("code", "defaults", "kwdefaults"):
            target = values._revalidate
            patch.setattr(target, "__" + change + "__",
                          foreign.__code__.replace(co_freevars=target.__code__.co_freevars) if change == "code" else
                          (foreign,) if change == "defaults" else {"foreign": foreign})
        elif change == "cell":
            patch.setattr(state["cell_plan"][0][0][0], "cell_contents", foreign)
        elif change == "container":
            target = next(row[0] for row in state["container_plans"] if type(row[0]) is dict)
            patch.setitem(target, "_scan_extra", foreign)
        elif change == "list":
            target = next(row[0] for row in state["container_plans"] if type(row[0]) is list)
            list_target = target
            target.append(foreign)
        elif change == "primitive_port":
            import _operator
            patch.setattr(_operator, "attrgetter", foreign)
        try:
            for checker in (original, current):
                if change == "clean":
                    checker()
                else:
                    with pytest.raises(TypeError):
                        checker()
            assert calls == []
        finally:
            if change == "list":
                assert list_target is not None
                assert list_target.pop() is foreign
    current()
    original()
