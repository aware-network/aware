from __future__ import annotations

from uuid import UUID

from aware_ontology_ontology.stable_ids import stable_ontology_package_id


def ontology_package_fqn_prefix_for_name(package_name: str) -> str:
    normalized = (package_name or "").strip()
    if not normalized:
        raise RuntimeError("Ontology package identity requires non-empty package_name")
    stem = normalized
    if stem.endswith("-ontology"):
        stem = stem[: -len("-ontology")]
    return f"aware_{stem.replace('-', '_')}"


def ontology_package_id_for_name(package_name: str) -> UUID:
    normalized = (package_name or "").strip()
    if not normalized:
        raise RuntimeError("Ontology package identity requires non-empty package_name")
    return stable_ontology_package_id(
        name=normalized,
        fqn_prefix=ontology_package_fqn_prefix_for_name(normalized),
    )
