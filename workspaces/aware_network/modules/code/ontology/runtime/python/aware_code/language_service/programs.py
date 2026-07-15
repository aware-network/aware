from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Literal

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code.language_service.position import ByteRange
from aware_meta_ontology.class_.class_config import ClassConfig

_FqnParts = tuple[str, str, str, str]


_program_parser: Parser | None = None


def _parser() -> Parser:
    global _program_parser
    if _program_parser is None:
        _program_parser = Parser(language=AWARE_LANGUAGE)
    return _program_parser


def parse_tree(*, document_bytes: bytes) -> Node:
    """Parse a full `.aware` document and return the tree-sitter root node."""
    tree = _parser().parse(document_bytes or b"")
    return tree.root_node


def iter_program_defs(*, root: Node) -> Iterator[Node]:
    for child in root.named_children:
        if child.type == "program_def":
            yield child


def iter_program_body_statements(*, program_def: Node) -> Iterator[Node]:
    body = program_def.child_by_field_name("body")
    if body is None:
        return
    for child in body.named_children:
        if child.type == "comment":
            continue
        yield child


def iter_program_calls_in_expr(*, expr: Node) -> Iterator[Node]:
    """Yield program_call nodes inside a program expression subtree (including nested calls)."""
    if expr.type == "program_call":
        yield expr
    for child in expr.named_children:
        yield from iter_program_calls_in_expr(expr=child)


def _node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace")


def _cursor_in_range(byte_offset: int, start: int, end: int) -> bool:
    if end <= start:
        return False
    cursor = int(byte_offset)
    if cursor < start:
        return False
    if cursor > end:
        return False
    if cursor == end and cursor > start:
        cursor -= 1
    return start <= cursor < end


@dataclass(frozen=True, slots=True)
class ProgramCallTargetAtCursor:
    target: str
    target_range: ByteRange
    in_call_stmt: bool


def find_program_call_target_at(*, root: Node, byte_offset: int) -> ProgramCallTargetAtCursor | None:
    """Return the program call target at the cursor (call statements and call expressions)."""
    cursor = max(int(byte_offset), 0)

    for program_def in iter_program_defs(root=root):
        # Fast reject: cursor outside the program block.
        if not _cursor_in_range(cursor, program_def.start_byte, program_def.end_byte):
            continue

        for stmt in iter_program_body_statements(program_def=program_def):
            if stmt.type == "call_stmt":
                call = stmt.child_by_field_name("call")
                if call is None:
                    continue
                target_node = call.child_by_field_name("target")
                if target_node is None:
                    continue
                if _cursor_in_range(cursor, target_node.start_byte, target_node.end_byte):
                    target = _node_text(target_node).strip()
                    if not target:
                        return None
                    return ProgramCallTargetAtCursor(
                        target=target,
                        target_range=ByteRange(start=target_node.start_byte, end=target_node.end_byte),
                        in_call_stmt=True,
                    )
                continue

            if stmt.type == "let_stmt":
                value_node = stmt.child_by_field_name("value")
                if value_node is None:
                    continue
                for call in iter_program_calls_in_expr(expr=value_node):
                    target_node = call.child_by_field_name("target")
                    if target_node is None:
                        continue
                    if _cursor_in_range(cursor, target_node.start_byte, target_node.end_byte):
                        target = _node_text(target_node).strip()
                        if not target:
                            return None
                        return ProgramCallTargetAtCursor(
                            target=target,
                            target_range=ByteRange(start=target_node.start_byte, end=target_node.end_byte),
                            in_call_stmt=False,
                        )

    return None


@dataclass(frozen=True, slots=True)
class ProgramParamSpec:
    name: str
    type_hint: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class ProgramIntrinsicSignature:
    target: str
    kind: Literal["directive", "pure"]
    params: tuple[ProgramParamSpec, ...]
    return_type: str | None = None

    def render(self) -> str:
        rendered_params: list[str] = []
        for p in self.params:
            suffix = "" if p.required else "?"
            rendered_params.append(f"{p.name}: {p.type_hint}{suffix}")
        params = ", ".join(rendered_params)
        if self.return_type:
            return f"{self.target}({params}) -> {self.return_type}"
        return f"{self.target}({params})"


PROGRAM_INTRINSICS: dict[str, ProgramIntrinsicSignature] = {
    # Reserved directives (statement-level).
    "bind": ProgramIntrinsicSignature(
        target="bind",
        kind="directive",
        params=(
            ProgramParamSpec("port", "Symbol(program.port.<key>)"),
            ProgramParamSpec("view", "Experience.Observable.View"),
            ProgramParamSpec("is_active", "Bool", required=False),
            ProgramParamSpec("require_head", "Bool", required=False),
            ProgramParamSpec("skip_if_head", "Bool", required=False),
        ),
    ),
    "plan.layout": ProgramIntrinsicSignature(
        target="plan.layout",
        kind="directive",
        params=(
            ProgramParamSpec("key", "String"),
            ProgramParamSpec("is_default", "Bool", required=False),
        ),
    ),
    "plan.section": ProgramIntrinsicSignature(
        target="plan.section",
        kind="directive",
        params=(
            ProgramParamSpec("layout_key", "String"),
            ProgramParamSpec("key", "String"),
            ProgramParamSpec("order", "Int"),
            ProgramParamSpec("is_visible", "Bool", required=False),
            ProgramParamSpec("flex", "Float", required=False),
        ),
    ),
    "plan.slot": ProgramIntrinsicSignature(
        target="plan.slot",
        kind="directive",
        params=(
            ProgramParamSpec("layout_key", "String"),
            ProgramParamSpec("port", "Symbol(program.port.<key>)"),
            ProgramParamSpec("section_key", "String"),
            ProgramParamSpec("on_bind", "String"),
            ProgramParamSpec("is_visible_default", "Bool", required=False),
        ),
    ),
    "plan.apply_program_ref": ProgramIntrinsicSignature(
        target="plan.apply_program_ref",
        kind="directive",
        params=(
            ProgramParamSpec("program_ref", "String"),
            ProgramParamSpec("symbols", "JsonObject", required=False),
            ProgramParamSpec("validate_only", "Bool", required=False),
        ),
    ),
    # Reserved stdlib (pure, expression-level).
    "meta.stable_class_config_id": ProgramIntrinsicSignature(
        target="meta.stable_class_config_id",
        kind="pure",
        params=(ProgramParamSpec("class_fqn", "String"),),
        return_type="UUID",
    ),
    "meta.stable_attribute_config_id": ProgramIntrinsicSignature(
        target="meta.stable_attribute_config_id",
        kind="pure",
        params=(
            ProgramParamSpec("owner_fqn", "String"),
            ProgramParamSpec("name", "String"),
        ),
        return_type="UUID",
    ),
    "meta.stable_class_relationship_id": ProgramIntrinsicSignature(
        target="meta.stable_class_relationship_id",
        kind="pure",
        params=(
            ProgramParamSpec("source_class_id", "UUID"),
            ProgramParamSpec("target_class_id", "UUID"),
            ProgramParamSpec("relationship_type", "String"),
            ProgramParamSpec("reference_attribute_config_id", "UUID"),
        ),
        return_type="UUID",
    ),
    "reactivity.stable_condition_config_id": ProgramIntrinsicSignature(
        target="reactivity.stable_condition_config_id",
        kind="pure",
        params=(ProgramParamSpec("name", "String"),),
        return_type="UUID",
    ),
    "reactivity.stable_event_config_id": ProgramIntrinsicSignature(
        target="reactivity.stable_event_config_id",
        kind="pure",
        params=(ProgramParamSpec("name", "String"),),
        return_type="UUID",
    ),
    "reactivity.stable_action_config_id": ProgramIntrinsicSignature(
        target="reactivity.stable_action_config_id",
        kind="pure",
        params=(ProgramParamSpec("name", "String"),),
        return_type="UUID",
    ),
    "reactivity.stable_condition_config_class_config_id": ProgramIntrinsicSignature(
        target="reactivity.stable_condition_config_class_config_id",
        kind="pure",
        params=(
            ProgramParamSpec("condition_config_id", "UUID"),
            ProgramParamSpec("class_config_id", "UUID"),
        ),
        return_type="UUID",
    ),
    "reactivity.stable_condition_config_attribute_config_id": ProgramIntrinsicSignature(
        target="reactivity.stable_condition_config_attribute_config_id",
        kind="pure",
        params=(
            ProgramParamSpec("condition_config_class_config_id", "UUID"),
            ProgramParamSpec("attribute_config_id", "UUID"),
            ProgramParamSpec("operator", "String"),
            ProgramParamSpec("negate", "Bool"),
        ),
        return_type="UUID",
    ),
}


def intrinsic_signature(target: str) -> ProgramIntrinsicSignature | None:
    return PROGRAM_INTRINSICS.get((target or "").strip())


def intrinsic_targets_by_prefix(prefix: str) -> tuple[str, ...]:
    """Return intrinsic targets starting with `prefix` (deterministic)."""
    raw = (prefix or "").strip()
    return tuple(sorted(k for k in PROGRAM_INTRINSICS.keys() if k.startswith(raw)))


@dataclass(frozen=True, slots=True)
class ProgramOwnerResolution:
    status: Literal["ok", "unresolved", "ambiguous"]
    fqn: str | None = None
    class_cfg: ClassConfig | None = None
    candidates: tuple[str, ...] = ()


def class_candidates_for_owner(
    *, owner: str, classes_by_fqn: Mapping[str, ClassConfig]
) -> tuple[tuple[str, ClassConfig], ...]:
    """Resolve owner -> candidate ClassConfigs from the snapshot symbol universe.

    Program call owners are resolved globally (across packages) because program runners
    (capabilities/registries) are not constrained by the current file's package scope.
    """
    raw = (owner or "").strip()
    if not raw:
        return ()
    parts = [p for p in raw.split(".") if p]
    if not parts:
        return ()

    packages: set[str] = set()
    for fqn in classes_by_fqn.keys():
        head = (fqn or "").split(".", 1)[0]
        if head:
            packages.add(head)

    candidates: list[tuple[str, ClassConfig]] = []

    def _scan(match: Callable[[_FqnParts], bool]) -> None:
        for fqn, cfg in classes_by_fqn.items():
            fqn_parts = [p for p in (fqn or "").split(".") if p]
            if len(fqn_parts) != 4:
                continue
            parts4: _FqnParts = (fqn_parts[0], fqn_parts[1], fqn_parts[2], fqn_parts[3])
            if match(parts4):
                candidates.append((fqn, cfg))

    if len(parts) >= 4:
        # Fully qualified owner (best-effort exact match).
        fqn = raw
        cfg = classes_by_fqn.get(fqn)
        return ((fqn, cfg),) if cfg is not None else ()

    if len(parts) == 3:
        a, b, name = parts
        if a in packages:
            # Cross-package shorthand: package.schema.Name (domain inferred when unambiguous).
            _scan(lambda fp: fp[0] == a and fp[2] == b and fp[3] == name)
        else:
            # Domain-qualified: domain.schema.Name (package inferred when unambiguous).
            _scan(lambda fp: fp[1] == a and fp[2] == b and fp[3] == name)

    if len(parts) == 2:
        schema, name = parts
        _scan(lambda fp: fp[2] == schema and fp[3] == name)

    if len(parts) == 1:
        name = parts[0]
        _scan(lambda fp: fp[3] == name)

    # Deduplicate by semantic identity (class_config.id) to avoid mirror aliases causing
    # false ambiguity in program resolution.
    out: list[tuple[str, ClassConfig]] = []
    seen_ids: set[str] = set()
    for fqn, cfg in sorted(candidates, key=lambda item: item[0]):
        key = str(cfg.id)
        if key in seen_ids:
            continue
        seen_ids.add(key)
        out.append((fqn, cfg))
    return tuple(out)


def resolve_owner_to_class(*, owner: str, classes_by_fqn: Mapping[str, ClassConfig]) -> ProgramOwnerResolution:
    candidates = class_candidates_for_owner(owner=owner, classes_by_fqn=classes_by_fqn)
    if not candidates:
        return ProgramOwnerResolution(status="unresolved")
    if len(candidates) == 1:
        fqn, cfg = candidates[0]
        return ProgramOwnerResolution(status="ok", fqn=fqn, class_cfg=cfg)
    return ProgramOwnerResolution(
        status="ambiguous",
        candidates=tuple(fqn for fqn, _ in candidates),
    )
