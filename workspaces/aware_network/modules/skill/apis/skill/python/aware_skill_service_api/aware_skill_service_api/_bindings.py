# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "skill-service-api"
API_FQN_PREFIX: Final[str] = "aware_skill_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Invoke one committed SkillPackage "
                                "through the canonical Skill Service "
                                "boundary.",
                                "discriminant": "skill.invoke.invoke",
                                "name": "invoke",
                                "request": {
                                    "class_ref": "aware_skill_service_dto.skill.SkillInvokeRequest",
                                    "source_path": "bindings/skill.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_skill_service_dto.skill.SkillInvokeResponse",
                                    "source_path": "bindings/skill.apis.aware",
                                },
                                "source_path": "bindings/skill.apis.aware",
                            }
                        ],
                        "name": "invoke",
                        "source_path": "bindings/skill.apis.aware",
                    }
                ],
                "name": "skill",
                "source_path": "bindings/skill.apis.aware",
            }
        ],
        "fqn_prefix": "aware_skill_service_api",
        "package_name": "skill-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke one committed SkillPackage "
                                "through the canonical Skill Service "
                                "boundary.",
                                "discriminant": "skill.invoke.invoke",
                                "endpoint_ref": "skill.invoke.invoke",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke",
                                "request": {
                                    "class_ref": "aware_skill_service_dto.skill.SkillInvokeRequest",
                                    "python_model_ref": "aware_skill_service_dto.skill.service_operation.SkillInvokeRequest",
                                    "source_path": "bindings/skill.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_skill_service_dto.skill.SkillInvokeResponse",
                                    "python_model_ref": "aware_skill_service_dto.skill.service_operation.SkillInvokeResponse",
                                    "source_path": "bindings/skill.apis.aware",
                                },
                                "source_path": "bindings/skill.apis.aware",
                            }
                        ],
                        "name": "invoke",
                        "source_path": "bindings/skill.apis.aware",
                    }
                ],
                "name": "skill",
                "source_path": "bindings/skill.apis.aware",
            }
        ],
        "fqn_prefix": "aware_skill_service_api",
        "package_name": "skill-service-api",
        "schema_version": 1,
    }
)

SKILL__INVOKE__INVOKE_ENDPOINT_REF: Final[str] = "skill.invoke.invoke"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "skill.invoke.invoke": SKILL__INVOKE__INVOKE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "SKILL__INVOKE__INVOKE_ENDPOINT_REF",
]
