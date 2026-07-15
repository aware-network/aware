from uuid import UUID

from aware_identity_ontology.stable_ids import stable_actor_id

DEFAULT_ACTOR_KEY = "default"


def normalize_actor_key(raw: str | None) -> str:
    return (raw or "").strip().casefold() or DEFAULT_ACTOR_KEY


def stable_actor_id_for_identity_key(*, identity_id: UUID, key: str) -> UUID:
    key_norm = normalize_actor_key(key)
    return stable_actor_id(identity_id=identity_id, key=key_norm)
