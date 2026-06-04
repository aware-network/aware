from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

from aware_orm.registry import ORMModelRegistry

from .errors import BundleInstallError


_COLLECTION_RELATIONSHIP_TYPES = {"one_to_many", "many_to_many"}


def _token(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).rsplit(".", 1)[-1].lower()


def _dict_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _parse_fk_columns(payload: Iterable[dict[str, Any]] | None) -> tuple[dict[str, Any], ...]:
    if not payload:
        return ()
    columns: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        columns.append(
            {
                "owner": item.get("owner"),
                "table_schema": item.get("table_schema"),
                "table_name": item.get("table_name"),
                "column_name": item.get("column_name"),
            }
        )
    return tuple(columns)


def _parse_join_chain(payload: Iterable[dict[str, Any]] | None) -> tuple[dict[str, Any], ...]:
    if not payload:
        return ()
    chain: list[dict[str, Any]] = []
    for hop in payload:
        if not isinstance(hop, dict):
            continue
        chain.append(
            {
                "ordinal": hop.get("ordinal"),
                "table_hint": hop.get("table_hint"),
                "from": hop.get("from") if isinstance(hop.get("from"), dict) else None,
                "to": hop.get("to") if isinstance(hop.get("to"), dict) else None,
            }
        )
    return tuple(chain)


@dataclass(frozen=True)
class RelationshipMetadata:
    relationship_id: UUID
    source_class_fqn: str
    target_class_fqn: str
    loading_strategy: str | None
    source_attribute: str | None
    target_attribute: str | None
    relationship_type: str | None
    fk_columns: tuple[dict[str, Any], ...] = ()
    join_chain: tuple[dict[str, Any], ...] = ()

    def has_source_attribute(self) -> bool:
        return bool(self.source_attribute)

    def has_target_attribute(self) -> bool:
        return bool(self.target_attribute)

    @property
    def is_collection(self) -> bool | None:
        if self.relationship_type is None:
            return None
        return _token(self.relationship_type) in _COLLECTION_RELATIONSHIP_TYPES

    def get_source_fk_column(self) -> dict[str, Any] | None:
        for column in self.fk_columns:
            if column.get("owner") == "source" and column.get("column_name"):
                return column
        return None


@dataclass(frozen=True)
class RelationshipStrategiesInstallResult:
    installed: int
    missing_relationships: list[str]
    missing_classes: list[str]


_relationship_metadata_by_id: dict[UUID, RelationshipMetadata] = {}
_relationship_metadata_by_source: dict[tuple[str, str], RelationshipMetadata] = {}
_relationship_metadata_by_target: dict[tuple[str, str], RelationshipMetadata] = {}


def get_relationship_metadata(
    relationship_id: UUID | str,
) -> RelationshipMetadata | None:
    rid = UUID(str(relationship_id))
    return _relationship_metadata_by_id.get(rid)


def get_relationship_metadata_by_source(
    source_class_fqn: str,
    source_attribute: str,
) -> RelationshipMetadata | None:
    return _relationship_metadata_by_source.get((source_class_fqn, source_attribute))


def get_relationship_metadata_by_target(
    target_class_fqn: str,
    target_attribute: str,
) -> RelationshipMetadata | None:
    return _relationship_metadata_by_target.get((target_class_fqn, target_attribute))


def register_relationship_metadata(metadata: RelationshipMetadata) -> None:
    _relationship_metadata_by_id[metadata.relationship_id] = metadata
    if metadata.source_attribute:
        _relationship_metadata_by_source[(metadata.source_class_fqn, metadata.source_attribute)] = metadata
    if metadata.target_attribute:
        _relationship_metadata_by_target[(metadata.target_class_fqn, metadata.target_attribute)] = metadata


def install_relationship_metadata_from_payload(
    relationship_strategies: bytes | None,
    *,
    strict: bool = False,
) -> RelationshipStrategiesInstallResult:
    if not relationship_strategies:
        if strict:
            raise BundleInstallError("Environment bundle missing relationship strategies manifest")
        return RelationshipStrategiesInstallResult(installed=0, missing_relationships=[], missing_classes=[])

    clear_relationship_metadata()

    try:
        payload = json.loads(relationship_strategies.decode("utf-8"))
    except Exception as exc:
        if strict:
            raise BundleInstallError(f"Relationship strategies manifest is not valid JSON: {exc}") from exc
        return RelationshipStrategiesInstallResult(installed=0, missing_relationships=[], missing_classes=[])
    if not isinstance(payload, dict):
        if strict:
            raise BundleInstallError("Relationship strategies manifest root must be an object")
        return RelationshipStrategiesInstallResult(installed=0, missing_relationships=[], missing_classes=[])

    relationships = _dict_items(payload.get("relationships", []))

    installed = 0
    missing_relationships: list[str] = []
    missing_classes: list[str] = []

    for entry in relationships:
        relationship_id = entry.get("relationship_id")
        if not relationship_id:
            continue

        try:
            rid = UUID(str(relationship_id))
        except Exception:
            missing_relationships.append(str(relationship_id))
            continue

        source_class_fqn = entry.get("source_class_fqn")
        target_class_fqn = entry.get("target_class_fqn")

        if not source_class_fqn or not target_class_fqn:
            missing_relationships.append(str(relationship_id))
            continue
        source_class_fqn = str(source_class_fqn)
        target_class_fqn = str(target_class_fqn)

        if ORMModelRegistry.get_class_by_fqn(source_class_fqn) is None:
            missing_classes.append(source_class_fqn)
        if ORMModelRegistry.get_class_by_fqn(target_class_fqn) is None:
            missing_classes.append(target_class_fqn)

        join_keys = _dict_items(entry.get("join_keys"))
        source_attr = _extract_join_attr(join_keys, owner="source")
        target_attr = _extract_join_attr(join_keys, owner="target")
        fk_columns = _parse_fk_columns(_dict_items(entry.get("fk_columns")))
        join_chain = _parse_join_chain(_dict_items(entry.get("join_chain")))

        metadata = RelationshipMetadata(
            relationship_id=rid,
            source_class_fqn=source_class_fqn,
            target_class_fqn=target_class_fqn,
            loading_strategy=(str(entry["loading_strategy"]) if entry.get("loading_strategy") is not None else None),
            source_attribute=source_attr,
            target_attribute=target_attr,
            relationship_type=(
                str(entry.get("relationship_type") or entry.get("type"))
                if entry.get("relationship_type") is not None or entry.get("type") is not None
                else None
            ),
            fk_columns=fk_columns,
            join_chain=join_chain,
        )

        register_relationship_metadata(metadata)
        installed += 1

    return RelationshipStrategiesInstallResult(
        installed=installed,
        missing_relationships=missing_relationships,
        missing_classes=missing_classes,
    )


def install_relationship_strategies(
    bundle: Any,
    *,
    strict: bool = False,
) -> RelationshipStrategiesInstallResult:
    """Compatibility wrapper for EnvironmentBundle-like objects."""

    return install_relationship_metadata_from_payload(
        getattr(bundle, "relationship_strategies", None),
        strict=strict,
    )


def _extract_join_attr(join_keys: Iterable[dict[str, Any]], *, owner: str) -> str | None:
    for key in join_keys:
        if key.get("owner") == owner:
            return key.get("attribute")
    return None


def clear_relationship_metadata() -> None:
    _relationship_metadata_by_id.clear()
    _relationship_metadata_by_source.clear()
    _relationship_metadata_by_target.clear()
