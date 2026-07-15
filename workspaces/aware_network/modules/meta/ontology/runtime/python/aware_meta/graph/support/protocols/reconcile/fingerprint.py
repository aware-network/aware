from enum import Enum
import hashlib
import json
from typing import Any

from aware_meta.graph.support.member import GraphMember, T_Kind


class FingerprintContext(Enum):
    """Context for fingerprinting operations."""

    RECONCILIATION = "reconciliation"  # For entity identity matching (uses only path_key)
    CONTENT = "content"  # For content comparison (uses all mutable fields)


def fingerprint(
    entity: GraphMember[T_Kind],
    context: FingerprintContext = FingerprintContext.RECONCILIATION,
) -> str:
    """
    Create fingerprint for an entity.

    Args:
        entity: The entity to fingerprint
        context: The context for fingerprinting:
            - RECONCILIATION: For entity identity matching (uses only path_key)
            - CONTENT: For content comparison (uses all mutable fields)

    Returns:
        A stable hash string for the entity
    """
    node_kind = entity.node_kind()
    kind_value = str(node_kind)

    # Reconciliation strictly via path_key
    if context == FingerprintContext.RECONCILIATION:
        path_key = entity.get_path_key()
        blob = f"{kind_value}:{path_key}" if isinstance(path_key, str) and path_key else f"{kind_value}:unknown"
        return hashlib.md5(blob.encode()).hexdigest()

    # Content fingerprint via content_fields mapping
    fields = entity.get_content_fields()
    data = {name: serialize_value(value) for name, value in fields.items()}
    blob = f"{kind_value}:{json.dumps(data, sort_keys=True)}"
    return hashlib.md5(blob.encode()).hexdigest()


# TODO: CLARIFY SERIALIZATION LOGIC
def serialize_value(value: Any) -> Any:
    """
    Serialize a value for fingerprinting.

    Handles common types like enums, None, primitives, lists, dicts.
    """
    if value is None:
        return None
    if hasattr(value, "value"):  # Enum
        return value.value
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    return str(value)
