from __future__ import annotations

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_meta.materialization.function_refs import meta_ontology_function_ref


API_CREATE_FUNCTION = meta_ontology_function_ref(Api.create)
API_CREATE_CAPABILITY_FUNCTION = meta_ontology_function_ref(Api.create_capability)
API_CAPABILITY_CREATE_ENDPOINT_FUNCTION = meta_ontology_function_ref(
    ApiCapability.create_endpoint
)

API_CREATE_FUNCTION_REF = API_CREATE_FUNCTION.ref
API_CREATE_CAPABILITY_FUNCTION_REF = API_CREATE_CAPABILITY_FUNCTION.ref
API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF = (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION.ref
)

API_SEMANTIC_FUNCTION_REFS = frozenset(
    {
        API_CREATE_FUNCTION_REF,
        API_CREATE_CAPABILITY_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    }
)


__all__ = [
    "API_CAPABILITY_CREATE_ENDPOINT_FUNCTION",
    "API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF",
    "API_CREATE_CAPABILITY_FUNCTION",
    "API_CREATE_CAPABILITY_FUNCTION_REF",
    "API_CREATE_FUNCTION",
    "API_CREATE_FUNCTION_REF",
    "API_SEMANTIC_FUNCTION_REFS",
]
