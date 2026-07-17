from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from aware_attention_ontology.stable_ids import (
    stable_attention_package_id,
    stable_layout_config_id,
    stable_layout_config_section_config_id,
    stable_section_config_id,
)

from .parser import AttentionLayoutConfigOwnership


@dataclass(frozen=True, slots=True)
class AttentionLayoutSectionConfigPlan:
    layout_config_section_config_id: str
    section_config_id: str
    section_key: str
    title: str
    description: str | None
    order: int
    flex: float
    is_visible: bool


@dataclass(frozen=True, slots=True)
class AttentionLayoutConfigPlan:
    layout_config_id: str
    layout_key: str
    title: str
    description: str | None
    frame_mode: str
    sections: tuple[AttentionLayoutSectionConfigPlan, ...]


@dataclass(frozen=True, slots=True)
class AttentionCompilePlan:
    schema_version: int
    package_name: str
    attention_package_id: str
    source_files: tuple[str, ...]
    layout_ontology: tuple[AttentionLayoutConfigPlan, ...]


@dataclass(frozen=True, slots=True)
class AttentionCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def build_attention_compile_plan_from_anchor(
    *,
    anchor_payload: Mapping[str, object],
    package_name: str,
    source_files: Sequence[str],
    frame_mode: str = "vertical",
) -> AttentionCompilePlan:
    resolved_package_name = package_name.strip()
    if not resolved_package_name:
        raise ValueError("Attention compile plan requires a non-empty package_name")

    layout_plan = tuple(
        _build_layout_plan(
            layout_payload=layout_payload,
            layout_index=layout_index,
            default_frame_mode=frame_mode,
        )
        for layout_index, layout_payload in enumerate(
            _iter_layout_payloads(anchor_payload=anchor_payload)
        )
    )
    return AttentionCompilePlan(
        schema_version=1,
        package_name=resolved_package_name,
        attention_package_id=str(
            stable_attention_package_id(name=resolved_package_name)
        ),
        source_files=tuple(source_files),
        layout_ontology=layout_plan,
    )


def build_attention_compile_plan_from_layout_ownership(
    *,
    layout_ownership: Sequence[AttentionLayoutConfigOwnership],
    package_name: str,
    source_files: Sequence[str],
    frame_mode: str = "vertical",
) -> AttentionCompilePlan:
    resolved_package_name = package_name.strip()
    if not resolved_package_name:
        raise ValueError("Attention compile plan requires a non-empty package_name")
    if not layout_ownership:
        raise ValueError("Attention compile plan requires at least one authored layout")

    layout_ontology = tuple(
        _build_layout_plan_from_ownership(
            layout=item,
            default_frame_mode=frame_mode,
        )
        for item in layout_ownership
    )
    return AttentionCompilePlan(
        schema_version=1,
        package_name=resolved_package_name,
        attention_package_id=str(
            stable_attention_package_id(name=resolved_package_name)
        ),
        source_files=tuple(source_files),
        layout_ontology=layout_ontology,
    )


def _build_layout_plan_from_ownership(
    *,
    layout: AttentionLayoutConfigOwnership,
    default_frame_mode: str,
) -> AttentionLayoutConfigPlan:
    layout_key = _expect_string(layout.key, field_name="layout.key")
    layout_config_id = stable_layout_config_id(key=layout_key)
    sections = tuple(
        AttentionLayoutSectionConfigPlan(
            layout_config_section_config_id=str(
                stable_layout_config_section_config_id(
                    layout_config_id=layout_config_id,
                    section_key=section.key,
                )
            ),
            section_config_id=str(
                stable_section_config_id(
                    layout_config_section_config_id=stable_layout_config_section_config_id(
                        layout_config_id=layout_config_id,
                        section_key=section.key,
                    ),
                    key=section.key,
                )
            ),
            section_key=section.key,
            title=section.title or _title_from_key(section.key),
            description=section.description,
            order=section.order,
            flex=1.0 if section.flex is None else section.flex,
            is_visible=True if section.is_visible is None else section.is_visible,
        )
        for section in layout.sections
    )
    return AttentionLayoutConfigPlan(
        layout_config_id=str(layout_config_id),
        layout_key=layout_key,
        title=_title_from_key(layout_key),
        description=None,
        frame_mode=_expect_string(default_frame_mode, field_name="frame_mode"),
        sections=sections,
    )


def _iter_layout_payloads(
    *,
    anchor_payload: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    if "layouts" in anchor_payload:
        if "layout" in anchor_payload or "section" in anchor_payload:
            raise ValueError(
                "Attention compile plan must use either layouts[] or legacy layout/section fields, not both"
            )
        layout_rows = anchor_payload.get("layouts")
        if not isinstance(layout_rows, Sequence) or isinstance(
            layout_rows, (str, bytes, bytearray)
        ):
            raise ValueError(
                "Attention compile plan requires layouts to be an array of layout objects"
            )
        resolved_layouts = tuple(
            _expect_mapping(layout_row, field_name=f"layouts[{layout_index}]")
            for layout_index, layout_row in enumerate(layout_rows)
        )
        if not resolved_layouts:
            raise ValueError(
                "Attention compile plan requires layouts to contain at least one layout"
            )
        return resolved_layouts

    layout_payload = _expect_mapping(anchor_payload.get("layout"), field_name="layout")
    legacy_section_payload = anchor_payload.get("section")
    if legacy_section_payload is not None:
        sections = layout_payload.get("sections")
        if sections is not None:
            raise ValueError(
                "Attention compile plan must use either layout.sections[] or legacy section, not both"
            )
        merged_payload = dict(layout_payload)
        merged_payload["sections"] = [
            _expect_mapping(legacy_section_payload, field_name="section"),
        ]
        return (merged_payload,)
    return (layout_payload,)


def _build_layout_plan(
    *,
    layout_payload: Mapping[str, object],
    layout_index: int,
    default_frame_mode: str,
) -> AttentionLayoutConfigPlan:
    layout_key = _expect_string(
        layout_payload.get("key"), field_name=f"layout[{layout_index}].key"
    )
    layout_title = _expect_string(
        layout_payload.get("title"),
        field_name=f"layout[{layout_index}].title",
    )
    layout_description = _expect_optional_string(
        layout_payload.get("description"),
        field_name=f"layout[{layout_index}].description",
    )
    frame_mode = _expect_optional_string(
        layout_payload.get("frame_mode"),
        field_name=f"layout[{layout_index}].frame_mode",
    ) or _expect_string(default_frame_mode, field_name="frame_mode")
    layout_config_id = stable_layout_config_id(key=layout_key)
    sections = _build_section_plans(
        layout_payload=layout_payload,
        layout_index=layout_index,
        layout_config_id=layout_config_id,
    )
    return AttentionLayoutConfigPlan(
        layout_config_id=str(layout_config_id),
        layout_key=layout_key,
        title=layout_title,
        description=layout_description,
        frame_mode=frame_mode,
        sections=sections,
    )


def _build_section_plans(
    *,
    layout_payload: Mapping[str, object],
    layout_index: int,
    layout_config_id: UUID,
) -> tuple[AttentionLayoutSectionConfigPlan, ...]:
    section_rows = layout_payload.get("sections")
    if not isinstance(section_rows, Sequence) or isinstance(
        section_rows, (str, bytes, bytearray)
    ):
        raise ValueError(
            "Attention compile plan requires layout.sections to be an array of section objects: "
            + f"layout[{layout_index}]"
        )

    seen_section_keys: set[str] = set()
    section_plans: list[AttentionLayoutSectionConfigPlan] = []
    for section_index, section_row in enumerate(section_rows):
        section_payload = _expect_mapping(
            section_row,
            field_name=f"layout[{layout_index}].sections[{section_index}]",
        )
        section_key = _expect_string(
            section_payload.get("key"),
            field_name=f"layout[{layout_index}].sections[{section_index}].key",
        )
        normalized_section_key = section_key.casefold()
        if normalized_section_key in seen_section_keys:
            raise ValueError(
                "Attention compile plan requires unique section keys per layout: "
                + f"layout[{layout_index}] section {section_key!r}"
            )
        seen_section_keys.add(normalized_section_key)

        section_title = _expect_string(
            section_payload.get("title"),
            field_name=f"layout[{layout_index}].sections[{section_index}].title",
        )
        section_description = _expect_optional_string(
            section_payload.get("description"),
            field_name=f"layout[{layout_index}].sections[{section_index}].description",
        )
        order = _expect_optional_int(
            section_payload.get("order"),
            field_name=f"layout[{layout_index}].sections[{section_index}].order",
        )
        flex = _expect_optional_number(
            section_payload.get("flex"),
            field_name=f"layout[{layout_index}].sections[{section_index}].flex",
        )
        is_visible = _expect_optional_bool(
            section_payload.get("is_visible"),
            field_name=f"layout[{layout_index}].sections[{section_index}].is_visible",
        )

        layout_config_section_config_id = stable_layout_config_section_config_id(
            layout_config_id=layout_config_id,
            section_key=section_key,
        )
        section_config_id = stable_section_config_id(
            layout_config_section_config_id=layout_config_section_config_id,
            key=section_key,
        )

        section_plans.append(
            AttentionLayoutSectionConfigPlan(
                layout_config_section_config_id=str(layout_config_section_config_id),
                section_config_id=str(section_config_id),
                section_key=section_key,
                title=section_title,
                description=section_description,
                order=section_index if order is None else order,
                flex=1.0 if flex is None else float(flex),
                is_visible=True if is_visible is None else is_visible,
            )
        )

    if not section_plans:
        raise ValueError(
            "Attention compile plan requires each layout to declare at least one section: "
            + f"layout[{layout_index}]"
        )
    return tuple(section_plans)


def emit_attention_compile_plan_artifact(
    *,
    plan: AttentionCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> AttentionCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "attention.compile_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return AttentionCompilePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def _encode_plan(*, plan: AttentionCompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "attention_package_id": plan.attention_package_id,
        "source_files": list(plan.source_files),
        "layout_ontology": [
            {
                "layout_config_id": layout.layout_config_id,
                "layout_key": layout.layout_key,
                "title": layout.title,
                "description": layout.description,
                "frame_mode": layout.frame_mode,
                "sections": [
                    {
                        "layout_config_section_config_id": section.layout_config_section_config_id,
                        "section_config_id": section.section_config_id,
                        "section_key": section.section_key,
                        "title": section.title,
                        "description": section.description,
                        "order": section.order,
                        "flex": section.flex,
                        "is_visible": section.is_visible,
                    }
                    for section in layout.sections
                ],
            }
            for layout in plan.layout_ontology
        ],
    }


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise ValueError(f"Attention compile plan requires {field_name} to be an object")


def _expect_string(value: object, *, field_name: str) -> str:
    if isinstance(value, str):
        resolved = value.strip()
        if resolved:
            return resolved
    raise ValueError(
        f"Attention compile plan requires {field_name} to be a non-empty string"
    )


def _expect_optional_string(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        resolved = value.strip()
        return resolved or None
    raise ValueError(
        f"Attention compile plan requires {field_name} to be a string or null"
    )


def _expect_optional_int(value: object, *, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"Attention compile plan requires {field_name} to be an int or null"
        )
    return value


def _expect_optional_number(value: object, *, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"Attention compile plan requires {field_name} to be numeric or null"
        )
    return float(value)


def _expect_optional_bool(value: object, *, field_name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(
            f"Attention compile plan requires {field_name} to be a bool or null"
        )
    return value


def _title_from_key(value: str) -> str:
    normalized = value.strip().replace("-", "_")
    parts = [part for part in normalized.split("_") if part]
    if not parts:
        return value.strip()
    return " ".join(part[:1].upper() + part[1:] for part in parts)


__all__ = [
    "AttentionCompilePlan",
    "AttentionCompilePlanArtifact",
    "AttentionLayoutConfigPlan",
    "AttentionLayoutSectionConfigPlan",
    "build_attention_compile_plan_from_layout_ownership",
    "build_attention_compile_plan_from_anchor",
    "emit_attention_compile_plan_artifact",
]
