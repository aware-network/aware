from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import cast
from uuid import UUID

from .compiler import ProgramConfigApplyCall, ProgramConfigPlan
from .plan import (
    InvocationPlan,
    PlanActorContract,
    PlanCall,
    PlanCallArg,
    PlanExpectEventConfig,
    PlanExpr,
    PlanInput,
    PlanIntentActionConfig,
    PlanInvoke,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanPortProjectionNodeContract,
    PlanPortProjectionNodeKey,
    PlanStep,
    PlanSymbolRef,
)


INVOCATION_PLAN_ARTIFACT_KIND = "aware.program.invocation_plan"
PROGRAM_CONFIG_PLAN_ARTIFACT_KIND = "aware.program.program_config_plan"
PROGRAM_APPLY_CALLS_ARTIFACT_KIND = "aware.program.program_apply_calls"
ARTIFACT_VERSION = 1


def encode_invocation_plan_artifact(plan: InvocationPlan) -> dict[str, object]:
    return {
        "kind": INVOCATION_PLAN_ARTIFACT_KIND,
        "version": ARTIFACT_VERSION,
        "plan": _encode_invocation_plan(plan),
    }


def decode_invocation_plan_artifact(payload: object) -> InvocationPlan:
    data = _expect_mapping(payload, context="invocation_plan_artifact")
    kind = str(data.get("kind") or "").strip()
    version = _coerce_int(data.get("version"), context="invocation_plan_artifact.version")
    if kind != INVOCATION_PLAN_ARTIFACT_KIND:
        msg = f"Invalid invocation plan artifact kind: {kind!r} " + (
            f"(expected {INVOCATION_PLAN_ARTIFACT_KIND!r})"
        )
        raise ValueError(msg)
    if version != ARTIFACT_VERSION:
        raise ValueError(
            f"Unsupported invocation plan artifact version: {version} "
            + f"(expected {ARTIFACT_VERSION})"
        )
    return _decode_invocation_plan(data.get("plan"))


def encode_program_config_plan_artifact(plan: ProgramConfigPlan) -> dict[str, object]:
    return {
        "kind": PROGRAM_CONFIG_PLAN_ARTIFACT_KIND,
        "version": ARTIFACT_VERSION,
        "plan": _to_json_value(plan),
    }


def encode_program_apply_calls_artifact(
    calls: tuple[ProgramConfigApplyCall, ...],
) -> dict[str, object]:
    return {
        "kind": PROGRAM_APPLY_CALLS_ARTIFACT_KIND,
        "version": ARTIFACT_VERSION,
        "calls": _to_json_value(calls),
    }


def _encode_invocation_plan(plan: InvocationPlan) -> dict[str, object]:
    return {
        "name": plan.name,
        "steps": [_encode_step(step) for step in plan.steps],
        "actors": [_encode_actor_contract(actor) for actor in plan.actors],
        "ports": [_encode_port_contract(port) for port in plan.ports],
    }


def _decode_invocation_plan(payload: object) -> InvocationPlan:
    data = _expect_mapping(payload, context="invocation_plan")
    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("invocation_plan.name is required")
    raw_steps = _expect_list(data.get("steps"), context="invocation_plan.steps")
    raw_actors = _expect_list(data.get("actors") or [], context="invocation_plan.actors")
    raw_ports = _expect_list(data.get("ports") or [], context="invocation_plan.ports")
    return InvocationPlan(
        name=name,
        steps=tuple(_decode_step(step) for step in raw_steps),
        actors=tuple(_decode_actor_contract(actor) for actor in raw_actors),
        ports=tuple(_decode_port_contract(port) for port in raw_ports),
    )


def _encode_step(step: PlanStep) -> dict[str, object]:
    if isinstance(step, PlanInput):
        return {
            "$step": "input",
            "name": step.name,
            "source": _encode_expr(step.source),
            "default": _encode_expr(step.default),
            "required": bool(step.required),
            "type_ref": step.type_ref,
        }
    if isinstance(step, PlanExpectEventConfig):
        return {
            "$step": "expect_event_config",
            "ref": _encode_expr(step.ref),
            "required": bool(step.required),
        }
    if isinstance(step, PlanIntentActionConfig):
        return {
            "$step": "intent_action_config",
            "action_ref": _encode_expr(step.action_ref),
            "event_ref": _encode_expr(step.event_ref),
        }
    if isinstance(step, PlanLet):
        return {
            "$step": "let",
            "name": step.name,
            "value": _encode_expr(step.value),
        }
    return {
        "$step": "invoke",
        "kind": step.kind,
        "actor": step.actor,
        "call": _encode_call(step.call),
    }


def _decode_step(payload: object) -> PlanStep:
    data = _expect_mapping(payload, context="plan_step")
    step_type = str(data.get("$step") or "").strip()
    if step_type == "input":
        name = str(data.get("name") or "").strip()
        if not name:
            raise ValueError("plan_step[input].name is required")
        return PlanInput(
            name=name,
            source=_decode_expr(data.get("source")),
            default=_decode_expr(data.get("default")),
            required=bool(data.get("required", True)),
            type_ref=_coerce_optional_str(data.get("type_ref")),
        )
    if step_type == "expect_event_config":
        return PlanExpectEventConfig(
            ref=_decode_expr(data.get("ref")),
            required=bool(data.get("required", True)),
        )
    if step_type == "intent_action_config":
        return PlanIntentActionConfig(
            action_ref=_decode_expr(data.get("action_ref")),
            event_ref=_decode_expr(data.get("event_ref")),
        )
    if step_type == "let":
        name = str(data.get("name") or "").strip()
        if not name:
            raise ValueError("plan_step[let].name is required")
        return PlanLet(name=name, value=_decode_expr(data.get("value")))
    if step_type == "invoke":
        return PlanInvoke(
            call=_decode_call(data.get("call")),
            kind="effect",
            actor=_coerce_optional_str(data.get("actor")),
        )
    raise ValueError(f"Unsupported plan step type: {step_type!r}")


def _encode_call(call: PlanCall) -> dict[str, object]:
    return {
        "$expr": "call",
        "target": call.target,
        "args": [_encode_call_arg(arg) for arg in call.args],
        "object_expr": _encode_expr(call.object_expr),
    }


def _decode_call(payload: object) -> PlanCall:
    data = _expect_mapping(payload, context="plan_call")
    target = str(data.get("target") or "").strip()
    if not target:
        raise ValueError("plan_call.target is required")
    raw_args = _expect_list(data.get("args") or [], context="plan_call.args")
    return PlanCall(
        target=target,
        args=tuple(_decode_call_arg(arg) for arg in raw_args),
        object_expr=_decode_expr(data.get("object_expr")),
    )


def _encode_call_arg(arg: PlanCallArg) -> dict[str, object]:
    return {
        "name": arg.name,
        "value": _encode_expr(arg.value),
    }


def _decode_call_arg(payload: object) -> PlanCallArg:
    data = _expect_mapping(payload, context="plan_call_arg")
    return PlanCallArg(
        name=_coerce_optional_str(data.get("name")),
        value=_decode_expr(data.get("value")),
    )


def _encode_port_contract(contract: PlanPortContract) -> dict[str, object]:
    return {
        "key": contract.key,
        "projection": contract.projection,
        "projection_nodes": [
            _encode_port_projection_node_contract(node)
            for node in contract.projection_nodes
        ],
        "intent": contract.intent,
    }


def _encode_actor_contract(contract: PlanActorContract) -> dict[str, object]:
    return {
        "key": contract.key,
        "actor": contract.actor,
    }


def _decode_actor_contract(payload: object) -> PlanActorContract:
    data = _expect_mapping(payload, context="plan_actor_contract")
    key = str(data.get("key") or "").strip()
    actor = str(data.get("actor") or "").strip()
    if not key or not actor:
        raise ValueError("plan_actor_contract requires key and actor")
    return PlanActorContract(
        key=key,
        actor=actor,
    )


def _decode_port_contract(payload: object) -> PlanPortContract:
    data = _expect_mapping(payload, context="plan_port_contract")
    key = str(data.get("key") or "").strip()
    projection = str(data.get("projection") or "").strip()
    if not key or not projection:
        raise ValueError("plan_port_contract requires key and projection")
    raw_projection_nodes = _expect_list(
        data.get("projection_nodes") or [],
        context="plan_port_contract.projection_nodes",
    )
    return PlanPortContract(
        key=key,
        projection=projection,
        projection_nodes=tuple(
            _decode_port_projection_node_contract(item) for item in raw_projection_nodes
        ),
        intent=_coerce_optional_str(data.get("intent")),
    )


def _encode_port_projection_node_contract(
    contract: PlanPortProjectionNodeContract,
) -> dict[str, object]:
    return {
        "key": contract.key,
        "node": contract.node,
        "keys": [_encode_port_projection_node_key(key) for key in contract.keys],
    }


def _decode_port_projection_node_contract(
    payload: object,
) -> PlanPortProjectionNodeContract:
    data = _expect_mapping(payload, context="plan_port_projection_node")
    key = str(data.get("key") or "").strip()
    node = str(data.get("node") or "").strip()
    if not key or not node:
        raise ValueError("plan_port_projection_node requires key and node")
    raw_keys = _expect_list(data.get("keys") or [], context="plan_port_projection_node.keys")
    return PlanPortProjectionNodeContract(
        key=key,
        node=node,
        keys=tuple(_decode_port_projection_node_key(item) for item in raw_keys),
    )


def _encode_port_projection_node_key(
    key: PlanPortProjectionNodeKey,
) -> dict[str, object]:
    return {
        "name": key.name,
        "value_expr": _encode_expr(key.value_expr),
    }


def _decode_port_projection_node_key(payload: object) -> PlanPortProjectionNodeKey:
    data = _expect_mapping(payload, context="plan_port_projection_node_key")
    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("plan_port_projection_node_key.name is required")
    return PlanPortProjectionNodeKey(
        name=name,
        value_expr=_decode_expr(data.get("value_expr")),
    )


def _encode_expr(expr: object) -> object:
    if expr is None:
        return None
    if isinstance(expr, PlanLocalRef):
        return {"$expr": "local_ref", "name": expr.name}
    if isinstance(expr, PlanSymbolRef):
        return {"$expr": "symbol_ref", "name": expr.name}
    if isinstance(expr, PlanCall):
        return _encode_call(expr)
    if isinstance(expr, list):
        items = cast(list[object], expr)
        return [_encode_expr(item) for item in items]
    if isinstance(expr, dict):
        mapping = cast(dict[object, object], expr)
        out: dict[str, object] = {}
        for key, value in mapping.items():
            out[str(key)] = _encode_expr(value)
        return out
    if isinstance(expr, (str, int, float, bool)):
        return expr
    raise TypeError(f"Unsupported plan expression type: {type(expr).__name__}")


def _decode_expr(payload: object) -> PlanExpr | None:
    if payload is None:
        return None
    if isinstance(payload, (str, int, float, bool)):
        return payload
    if isinstance(payload, list):
        items = cast(list[object], payload)
        return [_decode_expr(item) for item in items]
    if isinstance(payload, dict):
        mapping = cast(dict[object, object], payload)
        data = {str(k): v for k, v in mapping.items()}
        expr_type = data.get("$expr")
        if expr_type == "local_ref":
            name = str(data.get("name") or "").strip()
            if not name:
                raise ValueError("plan_expr[local_ref].name is required")
            return PlanLocalRef(name=name)
        if expr_type == "symbol_ref":
            name = str(data.get("name") or "").strip()
            if not name:
                raise ValueError("plan_expr[symbol_ref].name is required")
            return PlanSymbolRef(name=name)
        if expr_type == "call":
            return _decode_call(data)
        out: dict[str, object] = {}
        for key, value in data.items():
            out[str(key)] = _decode_expr(value)
        return out
    raise ValueError(f"Unsupported plan expression payload type: {type(payload).__name__}")


def _expect_mapping(payload: object, *, context: str) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object")
    mapping = cast(dict[object, object], payload)
    return {str(k): v for k, v in mapping.items()}


def _expect_list(payload: object, *, context: str) -> list[object]:
    if not isinstance(payload, list):
        raise ValueError(f"{context} must be a list")
    return cast(list[object], payload)


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        items = cast(list[object] | tuple[object, ...], value)
        return [_to_json_value(item) for item in items]
    if isinstance(value, dict):
        data = _expect_mapping(cast(object, value), context="artifact_json")
        out: dict[str, object] = {}
        for key in sorted(data.keys()):
            out[key] = _to_json_value(data[key])
        return out
    if is_dataclass(value) and not isinstance(value, type):
        return _to_json_value(asdict(value))
    raise TypeError(f"Unsupported artifact payload value: {type(value).__name__}")


def _coerce_int(value: object, *, context: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw:
            try:
                return int(raw)
            except ValueError as exc:
                raise ValueError(f"{context} must be an integer, got {value!r}") from exc
    raise ValueError(f"{context} must be an integer, got {value!r}")


__all__ = [
    "ARTIFACT_VERSION",
    "INVOCATION_PLAN_ARTIFACT_KIND",
    "PROGRAM_APPLY_CALLS_ARTIFACT_KIND",
    "PROGRAM_CONFIG_PLAN_ARTIFACT_KIND",
    "decode_invocation_plan_artifact",
    "encode_invocation_plan_artifact",
    "encode_program_apply_calls_artifact",
    "encode_program_config_plan_artifact",
]
