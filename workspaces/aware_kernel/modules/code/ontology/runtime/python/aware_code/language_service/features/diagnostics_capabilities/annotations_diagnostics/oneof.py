from __future__ import annotations

from dataclasses import dataclass

from aware_meta.graph.config.annotation.compiler import parse_oneof_args

from aware_code.language_service.types import SpannedToken

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
)
from .helpers import first_arg_or_verb_range


@dataclass(frozen=True, slots=True)
class _OneOfAttrConfigProxy:
    name: str
    is_virtual: bool = False
    is_required: bool = False


@dataclass(frozen=True, slots=True)
class _OneOfClassAttrProxy:
    attribute_config: _OneOfAttrConfigProxy | None


@dataclass(frozen=True, slots=True)
class _OneOfClassConfigProxy:
    name: str
    class_config_attribute_configs: tuple[_OneOfClassAttrProxy, ...]


def _class_oneof_attribute_names(*, class_cfg) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for class_attr_config in class_cfg.class_config_attribute_configs:
        attr_config = class_attr_config.attribute_config
        if attr_config is None or bool(attr_config.is_virtual):
            continue
        name = (attr_config.name or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    if names:
        return names

    resolved_class = class_cfg.code_section_class
    if resolved_class is None:
        return names
    for attr in resolved_class.code_section_attributes:
        name = (attr.name or "").strip()
        if not name or not bool(attr.is_public) or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _extract_discriminator_member_tokens(tokens: list[SpannedToken]) -> list[SpannedToken]:
    if not tokens:
        return []
    has_equals = any("=" in ((tok.text or "").strip()) for tok in tokens)
    if not has_equals:
        return [tokens[idx] for idx in range(1, len(tokens), 2)]

    out: list[SpannedToken] = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        raw = (token.text or "").strip()
        if "=" in raw and raw != "=":
            _lhs, rhs = raw.split("=", 1)
            if not rhs and idx + 1 < len(tokens):
                out.append(tokens[idx + 1])
                idx += 2
                continue
            idx += 1
            continue
        if idx + 2 < len(tokens) and (tokens[idx + 1].text or "").strip() == "=":
            out.append(tokens[idx + 2])
            idx += 3
            continue
        break
    return out


def _oneof_attribute_tokens(args_tokens: tuple[SpannedToken, ...]) -> list[SpannedToken]:
    tokens = [tok for tok in args_tokens if (tok.text or "").strip()]
    if not tokens:
        return []

    first = (tokens[0].text or "").strip().casefold()
    if first in {"validation", "identity"}:
        tokens = tokens[1:]
    if not tokens:
        return []

    disc_positions = [idx for idx, tok in enumerate(tokens) if (tok.text or "").strip().casefold() == "discriminator"]
    if not disc_positions:
        return tokens

    disc_pos = disc_positions[0]
    member_tokens = tokens[:disc_pos]
    disc_tail = tokens[disc_pos + 1 :]
    if not disc_tail:
        return member_tokens

    out = list(member_tokens)
    out.append(disc_tail[0])
    out.extend(_extract_discriminator_member_tokens(disc_tail[1:]))
    return out


def _class_config_for_oneof_parse(*, class_cfg, cls):
    if class_cfg.class_config_attribute_configs:
        return class_cfg

    proxies: list[_OneOfClassAttrProxy] = []
    for attr in cls.code_section_attributes:
        name = (attr.name or "").strip()
        if not name:
            continue
        proxies.append(
            _OneOfClassAttrProxy(
                attribute_config=_OneOfAttrConfigProxy(
                    name=name,
                    is_virtual=False,
                    is_required=bool(attr.is_required),
                )
            )
        )
    return _OneOfClassConfigProxy(
        name=str(class_cfg.name),
        class_config_attribute_configs=tuple(proxies),
    )


def collect_oneof_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"oneof annotation must use 'TypeRef' (got: {ann_input.path.text})",
            code="aware.annotation.path_invalid",
        )
        return

    resolved = resolve_class(ann_input.type_ref.text)
    if resolved is None:
        add(
            rng=ann_input.type_ref.range,
            message=f"Class not found for annotation target: {ann_input.type_ref.text}",
            code="aware.annotation.class_not_found",
            data={"suggestions": suggest(ann_input.type_ref.text, list(ann_input.class_candidates))},
        )
        return

    _fqn, class_cfg = resolved
    cls = class_cfg.code_section_class
    if cls is None:
        return

    attr_names = _class_oneof_attribute_names(class_cfg=class_cfg)
    member_not_found = False
    for token in _oneof_attribute_tokens(ann_input.args_tokens):
        name = (token.text or "").strip()
        if name and name not in attr_names:
            member_not_found = True
            add(
                rng=token.range,
                message=f"Attribute {name!r} not found on class {class_cfg.name}",
                code="aware.annotation.member_not_found",
                data={"suggestions": suggest(name, attr_names)},
            )

    try:
        class_config_for_parse = _class_config_for_oneof_parse(class_cfg=class_cfg, cls=cls)
        _ = parse_oneof_args(args=list(ann_input.args), class_config=class_config_for_parse)
    except ValueError as exc:
        message = str(exc)
        if member_not_found and (
            "unknown attributes" in message
            or "does not exist" in message
            or "unknown oneof member attribute" in message
        ):
            return

        data: dict[str, list[str]] | None = None
        if ann_input.args_tokens:
            suggestion_seed = ann_input.args_tokens[0].text
            suggestion_candidates = ["validation", "identity", *attr_names]
            suggestions = suggest(suggestion_seed, suggestion_candidates)
            if suggestions:
                data = {"suggestions": suggestions}
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=message,
            code="aware.annotation.args_invalid",
            data=data,
        )
