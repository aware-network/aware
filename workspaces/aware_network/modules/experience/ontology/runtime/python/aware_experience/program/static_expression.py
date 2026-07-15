from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import cast
from uuid import UUID

from aware_experience.program.language import (
    InvocationPlan,
    PlanCall,
    PlanExpr,
    PlanLet,
    PlanLocalRef,
    PlanSymbolRef,
)


class ProgramStaticExpressionError(ValueError):
    """A Program materialization identity expression is not statically safe."""


def resolve_program_static_values(plan: InvocationPlan) -> dict[str, object]:
    values: dict[str, object] = {}
    for step in plan.steps:
        if not isinstance(step, PlanLet):
            continue
        if step.name in values:
            raise ProgramStaticExpressionError(
                f"program_static_expression_duplicate_local:{step.name}"
            )
        values[step.name] = evaluate_program_static_expression(
            step.value,
            values=values,
        )
    return values


def evaluate_program_static_expression(
    expr: PlanExpr,
    *,
    values: Mapping[str, object],
) -> object:
    if isinstance(expr, PlanLocalRef):
        if expr.name not in values:
            raise ProgramStaticExpressionError(
                f"program_static_expression_local_unresolved:{expr.name}"
            )
        return values[expr.name]
    if isinstance(expr, PlanSymbolRef):
        return expr.name
    if isinstance(expr, PlanCall):
        function = _resolve_stable_function(expr.target)
        args: list[object] = []
        kwargs: dict[str, object] = {}
        for arg in expr.args:
            value = evaluate_program_static_expression(arg.value, values=values)
            if arg.name is None:
                args.append(value)
            else:
                kwargs[arg.name] = value
        try:
            return function(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            raise ProgramStaticExpressionError(
                f"program_static_expression_call_failed:{expr.target}:{exc}"
            ) from exc
    if isinstance(expr, list):
        return [
            evaluate_program_static_expression(cast(PlanExpr, item), values=values)
            for item in expr
        ]
    if isinstance(expr, dict):
        return {
            str(key): evaluate_program_static_expression(
                cast(PlanExpr, value), values=values
            )
            for key, value in expr.items()
        }
    return expr


def resolve_program_static_uuid(
    expr: PlanExpr | None,
    *,
    values: Mapping[str, object],
    label: str,
) -> UUID:
    if expr is None:
        raise ProgramStaticExpressionError(
            f"program_static_expression_uuid_missing:{label}"
        )
    value = evaluate_program_static_expression(expr, values=values)
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ProgramStaticExpressionError(
            f"program_static_expression_uuid_invalid:{label}:{value!r}"
        ) from exc


def resolve_program_static_uuid_from_plan(
    expr: PlanExpr | None,
    *,
    plan: InvocationPlan,
    label: str,
) -> UUID:
    let_expressions = {
        step.name: step.value for step in plan.steps if isinstance(step, PlanLet)
    }
    values: dict[str, object] = {}
    resolving: set[str] = set()

    def evaluate(value_expr: PlanExpr) -> object:
        if isinstance(value_expr, PlanLocalRef):
            name = value_expr.name
            if name in values:
                return values[name]
            definition = let_expressions.get(name)
            if definition is None:
                raise ProgramStaticExpressionError(
                    f"program_static_expression_local_unresolved:{name}"
                )
            if name in resolving:
                raise ProgramStaticExpressionError(
                    f"program_static_expression_local_cycle:{name}"
                )
            resolving.add(name)
            try:
                resolved = evaluate(definition)
            finally:
                resolving.remove(name)
            values[name] = resolved
            return resolved
        if isinstance(value_expr, PlanCall):
            function = _resolve_stable_function(value_expr.target)
            args: list[object] = []
            kwargs: dict[str, object] = {}
            for arg in value_expr.args:
                resolved_arg = evaluate(arg.value)
                if arg.name is None:
                    args.append(resolved_arg)
                else:
                    kwargs[arg.name] = resolved_arg
            try:
                return function(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                raise ProgramStaticExpressionError(
                    f"program_static_expression_call_failed:{value_expr.target}:{exc}"
                ) from exc
        return evaluate_program_static_expression(value_expr, values=values)

    if expr is None:
        raise ProgramStaticExpressionError(
            f"program_static_expression_uuid_missing:{label}"
        )
    value = evaluate(expr)
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ProgramStaticExpressionError(
            f"program_static_expression_uuid_invalid:{label}:{value!r}"
        ) from exc


def _resolve_stable_function(target: str) -> Callable[..., object]:
    raw = (target or "").strip()
    module_id, separator, function_name = raw.partition(".")
    if (
        not separator
        or not module_id
        or not function_name.startswith("stable_")
        or not all(character.isalnum() or character == "_" for character in module_id)
    ):
        raise ProgramStaticExpressionError(
            f"program_static_expression_function_not_allowed:{raw}"
        )
    for module_name in (
        f"aware_{module_id}_ontology.stable_ids",
        f"aware_{module_id}.stable_ids",
    ):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        function = getattr(module, function_name, None)
        if callable(function):
            return function
    raise ProgramStaticExpressionError(
        f"program_static_expression_function_unresolved:{raw}"
    )


__all__ = [
    "ProgramStaticExpressionError",
    "evaluate_program_static_expression",
    "resolve_program_static_uuid",
    "resolve_program_static_uuid_from_plan",
    "resolve_program_static_values",
]
