from __future__ import annotations

from pydantic import BaseModel

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodeContentPlan
from aware_meta.runtime.handler_executor.argument_coercion import (
    coerce_meta_handler_call_kwargs,
)


def test_coerce_meta_handler_call_kwargs_resolves_forward_refs_when_any_missing() -> (
    None
):
    namespace = {
        "CodeContentPlan": CodeContentPlan,
    }
    exec(
        "from __future__ import annotations\n"
        "def handler(plan: CodeContentPlan) -> Any:\n"
        "    return None\n",
        namespace,
    )

    coerced = coerce_meta_handler_call_kwargs(
        namespace["handler"],
        {
            "plan": {
                "language": CodeLanguage.aware.value,
                "content_text": "class A {}",
                "section_plans": [],
            },
        },
    )

    assert isinstance(coerced["plan"], CodeContentPlan)
    assert coerced["plan"].language is CodeLanguage.aware


def test_coerce_meta_handler_call_kwargs_filters_unknown_without_kwargs() -> None:
    def handler(name: str) -> None:
        _ = name

    coerced = coerce_meta_handler_call_kwargs(
        handler,
        {
            "name": "aware",
            "public_facade_only": "ignored",
        },
    )

    assert coerced == {"name": "aware"}


def test_coerce_meta_handler_call_kwargs_keeps_unknown_with_kwargs() -> None:
    def handler(name: str, **kwargs: object) -> None:
        _ = name, kwargs

    coerced = coerce_meta_handler_call_kwargs(
        handler,
        {
            "name": "aware",
            "public_facade_only": "kept",
        },
    )

    assert coerced == {"name": "aware", "public_facade_only": "kept"}


def test_coerce_meta_handler_call_kwargs_passes_trusted_target_through() -> None:
    class HandlerTarget(BaseModel):
        value: int

    class RuntimeTarget(BaseModel):
        value: int

    def handler(target: HandlerTarget, count: int) -> None:
        _ = target, count

    target = RuntimeTarget(value=1)

    coerced = coerce_meta_handler_call_kwargs(
        handler,
        {"target": target, "count": "2"},
        trusted_parameter_names=frozenset({"target"}),
    )

    assert coerced["target"] is target
    assert coerced["count"] == 2
