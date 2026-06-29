# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_API = uuid5(NAMESPACE_URL, "aware://api/v1")


def stable_api_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_API, f"aware:api:{name_norm}")


def stable_api_call_id(*, api_capability_endpoint_id: UUID, call_key: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_endpoint_id, call_key"""

    return uuid5(NS_API, f"aware:api_call:{api_capability_endpoint_id}:{call_key}")


def stable_api_call_outcome_id(*, api_call_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_call_id"""

    return uuid5(NS_API, f"aware:api_call_outcome:{api_call_id}")


def stable_api_capability_id(*, api_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_API, f"aware:api_capability:{api_id}:{name_norm}")


def stable_api_capability_endpoint_id(*, api_capability_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_API, f"aware:api_capability_endpoint:{api_capability_id}:{name_norm}")


def stable_api_capability_endpoint_function_id(
    *, api_capability_endpoint_id: UUID, api_graph_capability_function_id: UUID, name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_endpoint_id, api_graph_capability_function_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_API,
        f"aware:api_capability_endpoint_function:{api_capability_endpoint_id}:{api_graph_capability_function_id}:{name_norm}",
    )


def stable_api_capability_endpoint_request_config_id(
    *, api_capability_endpoint_id: UUID, class_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_endpoint_id, class_config_id"""

    return uuid5(NS_API, f"aware:api_capability_endpoint_request_config:{api_capability_endpoint_id}:{class_config_id}")


def stable_api_capability_endpoint_response_config_id(
    *, api_capability_endpoint_request_config_id: UUID, class_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_endpoint_request_config_id, class_config_id"""

    return uuid5(
        NS_API,
        f"aware:api_capability_endpoint_response_config:{api_capability_endpoint_request_config_id}:{class_config_id}",
    )


def stable_api_capability_endpoint_stream_config_id(
    *, api_capability_endpoint_request_config_id: UUID, stream_mode: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_endpoint_request_config_id, stream_mode"""

    stream_mode_norm = (stream_mode or "").casefold().strip()
    return uuid5(
        NS_API,
        f"aware:api_capability_endpoint_stream_config:{api_capability_endpoint_request_config_id}:{stream_mode_norm}",
    )


def stable_api_capability_endpoint_stream_event_config_id(
    *, api_capability_endpoint_stream_config_id: UUID, class_config_id: UUID, kind: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_capability_endpoint_stream_config_id, class_config_id, kind"""

    kind_norm = (kind or "").casefold().strip()
    return uuid5(
        NS_API,
        f"aware:api_capability_endpoint_stream_event_config:{api_capability_endpoint_stream_config_id}:{class_config_id}:{kind_norm}",
    )


def stable_api_graph_id(*, api_id: UUID, object_config_graph_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_id, object_config_graph_id"""

    return uuid5(NS_API, f"aware:api_graph:{api_id}:{object_config_graph_id}")


def stable_api_graph_capability_id(*, api_graph_id: UUID, api_capability_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_graph_id, api_capability_id"""

    return uuid5(NS_API, f"aware:api_graph_capability:{api_graph_id}:{api_capability_id}")


def stable_api_graph_capability_function_id(
    *, api_graph_capability_id: UUID, api_graph_function_id: UUID, name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_graph_capability_id, api_graph_function_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_API, f"aware:api_graph_capability_function:{api_graph_capability_id}:{api_graph_function_id}:{name_norm}"
    )


def stable_api_graph_function_id(*, api_graph_id: UUID, class_config_function_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_graph_id, class_config_function_config_id"""

    return uuid5(NS_API, f"aware:api_graph_function:{api_graph_id}:{class_config_function_config_id}")


def stable_api_graph_projection_id(*, api_graph_id: UUID, object_projection_graph_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_graph_id, object_projection_graph_id"""

    return uuid5(NS_API, f"aware:api_graph_projection:{api_graph_id}:{object_projection_graph_id}")


def stable_api_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_API, f"aware:api_package:{name_norm}")


def stable_api_package_language_package_id(*, api_package_id: UUID, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: api_package_id, code_package_id"""

    return uuid5(NS_API, f"aware:api_package_language_package:{api_package_id}:{code_package_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "09aec6a2-69e2-5aa3-9e7f-aef4fa6fe347": ("stable_api_capability_id", ("api_id", "name")),
    "2ae826c7-5759-5612-8647-856a91b2574b": ("stable_api_id", ("name",)),
    "3404e083-0719-5698-aa97-0239d9d0d656": ("stable_api_package_id", ("name",)),
    "356e7a31-925d-505c-8809-cdadec28eb64": (
        "stable_api_capability_endpoint_request_config_id",
        ("api_capability_endpoint_id", "class_config_id"),
    ),
    "359f3452-0eb5-5b4b-abf7-e3984e45a45e": (
        "stable_api_package_language_package_id",
        ("api_package_id", "code_package_id"),
    ),
    "8295b3d1-cc94-591d-b783-8aeeea66f454": (
        "stable_api_capability_endpoint_stream_config_id",
        ("api_capability_endpoint_request_config_id", "stream_mode"),
    ),
    "995a05e1-ec54-51ad-9d12-af5574f10732": ("stable_api_call_outcome_id", ("api_call_id",)),
    "a4b3359e-ea13-5b0a-9d6e-19d843275d4b": (
        "stable_api_capability_endpoint_response_config_id",
        ("api_capability_endpoint_request_config_id", "class_config_id"),
    ),
    "a6f5fa70-14fe-5f17-8a85-f123a0078e8e": ("stable_api_call_id", ("api_capability_endpoint_id", "call_key")),
    "aca1fbe2-4ac7-5acc-9106-327be1974a8f": (
        "stable_api_capability_endpoint_stream_event_config_id",
        ("api_capability_endpoint_stream_config_id", "class_config_id", "kind"),
    ),
    "ace608e1-36d7-55ac-9f44-156ab8d32398": ("stable_api_graph_id", ("api_id", "object_config_graph_id")),
    "ce21aee7-d1ea-5acb-bd0a-6237568cfa93": (
        "stable_api_graph_function_id",
        ("api_graph_id", "class_config_function_config_id"),
    ),
    "cedefaa4-9c7a-59d0-8984-bfdab7138c3b": ("stable_api_capability_endpoint_id", ("api_capability_id", "name")),
    "d0886596-c800-5eb9-a18f-d426401bdeee": (
        "stable_api_graph_capability_function_id",
        ("api_graph_capability_id", "api_graph_function_id", "name"),
    ),
    "d2e5d5c4-48c1-56f6-ae22-10d7d69ade1d": (
        "stable_api_capability_endpoint_function_id",
        ("api_capability_endpoint_id", "api_graph_capability_function_id", "name"),
    ),
    "f2fbb2c0-f386-5af0-be11-2ec718b519f8": (
        "stable_api_graph_projection_id",
        ("api_graph_id", "object_projection_graph_id"),
    ),
    "faf109d9-545f-5a4f-8657-1b328c2b83b4": ("stable_api_graph_capability_id", ("api_graph_id", "api_capability_id")),
}

__all__ = [
    "stable_api_id",
    "stable_api_call_id",
    "stable_api_call_outcome_id",
    "stable_api_capability_id",
    "stable_api_capability_endpoint_id",
    "stable_api_capability_endpoint_function_id",
    "stable_api_capability_endpoint_request_config_id",
    "stable_api_capability_endpoint_response_config_id",
    "stable_api_capability_endpoint_stream_config_id",
    "stable_api_capability_endpoint_stream_event_config_id",
    "stable_api_graph_id",
    "stable_api_graph_capability_id",
    "stable_api_graph_capability_function_id",
    "stable_api_graph_function_id",
    "stable_api_graph_projection_id",
    "stable_api_package_id",
    "stable_api_package_language_package_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
