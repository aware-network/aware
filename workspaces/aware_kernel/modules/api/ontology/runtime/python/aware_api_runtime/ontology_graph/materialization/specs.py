from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from ..ontology import (
    APIOntologyPlan,
    decode_api_ontology_plan_payload,
    encode_api_ontology_plan_payload,
)


@dataclass(frozen=True, slots=True)
class APIOntologyMaterializationSpec:
    api_name: str
    source_path: str
    plan: APIOntologyPlan


def resolve_api_ontology_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[APIOntologyMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    specs_by_key: dict[tuple[str, str], APIOntologyMaterializationSpec] = {}
    for payload in compile_plan_payloads:
        raw_plans = _expect_list(
            payload.get("api_ontology", ()), field_name="api_ontology"
        )
        if not raw_plans:
            continue
        plan_payloads = tuple(
            _expect_mapping(item, field_name="api_ontology[]") for item in raw_plans
        )
        plans = decode_api_ontology_plan_payload(payload=list(plan_payloads))
        for plan in plans:
            spec = APIOntologyMaterializationSpec(
                api_name=plan.api.name,
                source_path=plan.api.source_path,
                plan=plan,
            )
            key = (plan.api.name.casefold(), plan.api.source_path)
            existing = specs_by_key.get(key)
            if existing is not None and existing != spec:
                raise RuntimeError(
                    "Invalid API compile plan: duplicate api ontology entries disagree "
                    + f"(api={plan.api.name!r}, source_path={plan.api.source_path!r})"
                )
            specs_by_key[key] = spec

    return tuple(
        sorted(
            specs_by_key.values(),
            key=lambda item: (item.api_name.casefold(), item.source_path),
        )
    )


def encode_api_ontology_materialization_step_payload(
    *,
    spec: APIOntologyMaterializationSpec,
) -> dict[str, object]:
    return encode_api_ontology_plan_payload(plans=(spec.plan,))[0]


def decode_api_ontology_materialization_step_payload(
    payload: Mapping[str, object],
) -> APIOntologyMaterializationSpec:
    mapping = _expect_mapping(payload, field_name="api_ontology_step")
    plans = decode_api_ontology_plan_payload(payload=[dict(mapping)])
    if len(plans) != 1:
        raise RuntimeError(
            f"Invalid api ontology step payload: expected exactly one plan, got {len(plans)}"
        )
    plan = plans[0]
    return APIOntologyMaterializationSpec(
        api_name=plan.api.name,
        source_path=plan.api.source_path,
        plan=plan,
    )


def _expect_list(value: object, *, field_name: str) -> Sequence[object]:
    if isinstance(value, (list, tuple)):
        return cast(Sequence[object], value)
    raise RuntimeError(f"Invalid api compile plan payload: {field_name} must be a list")


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise RuntimeError(
        f"Invalid api compile plan payload: {field_name} must be an object"
    )


__all__ = [
    "APIOntologyMaterializationSpec",
    "decode_api_ontology_materialization_step_payload",
    "encode_api_ontology_materialization_step_payload",
    "resolve_api_ontology_materialization_specs",
]
