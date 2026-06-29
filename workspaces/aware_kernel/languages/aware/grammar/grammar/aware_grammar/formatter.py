from __future__ import annotations

import re
import textwrap
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE
from typing import final


_PARSER = Parser(language=AWARE_LANGUAGE)


def format_aware_source(
    *,
    text: str,
    indent_size: int = 4,
    max_line_length: int | None = 120,
) -> str:
    """Format Aware source using the canonical tree-sitter grammar.

    Design goals:
    - Deterministic + idempotent output.
    - Preserve token-level semantics (no inference; no reordering).
    - Preserve blank-line intent between adjacent items when possible.
    """
    if not text:
        return text

    source_bytes = text.encode("utf-8")
    if not source_bytes.strip():
        # Keep empty/whitespace-only documents stable.
        return text

    tree = _PARSER.parse(source_bytes)
    root = tree.root_node
    if root.has_error:
        # v0: refuse to format invalid syntax to avoid destructive edits.
        return text

    formatter = _AwareFormatter(
        source_bytes=source_bytes,
        indent_size=indent_size,
        max_line_length=max_line_length,
    )
    formatter.emit_source_file(root)
    return formatter.render()


_BLANK_LINE_RX = re.compile(r"\n[ \t\r]*\n")


def _node_text(*, source_bytes: bytes, node: Node) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode(
        "utf-8", errors="replace"
    )


def _has_blank_line_between(*, source_bytes: bytes, left: Node, right: Node) -> bool:
    if right.start_byte <= left.end_byte:
        return False
    gap = source_bytes[left.end_byte : right.start_byte].decode(
        "utf-8", errors="replace"
    )
    return bool(_BLANK_LINE_RX.search(gap))


@dataclass(slots=True)
class _LineWriter:
    indent_size: int
    indent_level: int = 0
    _lines: list[str] = field(default_factory=list)

    def line(self, text: str = "") -> None:
        if not text:
            self._lines.append("")
            return
        indent = " " * (self.indent_level * self.indent_size)
        self._lines.append(indent + text.rstrip())

    def blank_line(self) -> None:
        # Collapse multiple blank lines into a single blank line.
        if not self._lines:
            self._lines.append("")
            return
        if self._lines[-1] != "":
            self._lines.append("")

    @contextmanager
    def indent(self, levels: int = 1):
        self.indent_level += levels
        try:
            yield
        finally:
            self.indent_level -= levels

    def render(self) -> str:
        out = "\n".join(self._lines).rstrip("\n") + "\n"
        return out


@final
class _AwareFormatter:
    def __init__(
        self, *, source_bytes: bytes, indent_size: int, max_line_length: int | None
    ) -> None:
        self._source_bytes = source_bytes
        self._w = _LineWriter(indent_size=indent_size)
        self._max_line_length = max_line_length

    def render(self) -> str:
        return self._w.render()

    def _fits_on_line(self, text: str) -> bool:
        if self._max_line_length is None:
            return True
        indent_len = self._w.indent_level * self._w.indent_size
        return indent_len + len(text.rstrip()) <= self._max_line_length

    def emit_source_file(self, node: Node) -> None:
        children = list(node.named_children)
        imports: list[Node] = []
        idx = 0
        while idx < len(children) and children[idx].type == "import_stmt":
            imports.append(children[idx])
            idx += 1
        rest = children[idx:]

        for imp_idx, imp in enumerate(imports):
            self._emit_import_stmt(imp)
            if imp_idx + 1 < len(imports) and _has_blank_line_between(
                source_bytes=self._source_bytes, left=imp, right=imports[imp_idx + 1]
            ):
                self._w.blank_line()

        if (
            imports
            and rest
            and _has_blank_line_between(
                source_bytes=self._source_bytes, left=imports[-1], right=rest[0]
            )
        ):
            self._w.blank_line()

        for item_idx, item in enumerate(rest):
            self._emit_top_level_item(item)
            if item_idx + 1 < len(rest) and _has_blank_line_between(
                source_bytes=self._source_bytes, left=item, right=rest[item_idx + 1]
            ):
                self._w.blank_line()

    def _emit_top_level_item(self, node: Node) -> None:
        t = node.type
        if t == "comment":
            self._emit_comment(node)
            return
        if t == "projection_def":
            self._emit_projection_def(node)
            return
        if t == "experience_def":
            self._emit_experience_def(node)
            return
        if t == "graph_def":
            self._emit_graph_def(node)
            return
        if t == "binding_def":
            self._emit_binding_def(node)
            return
        if t == "api_def":
            self._emit_api_def(node)
            return
        if t == "service_def":
            self._emit_service_def(node)
            return
        if t == "class_def":
            self._emit_class_like(node, keyword="class")
            return
        if t == "edge_def":
            self._emit_class_like(node, keyword="edge")
            return
        if t == "enum_def":
            self._emit_enum_def(node)
            return
        if t == "fn_def":
            self._emit_fn_def(node)
            return
        if t == "ann_def":
            self._emit_ann_def(node)
            return

        # Unknown top-level nodes: preserve their raw text as a best-effort fallback.
        raw = _node_text(source_bytes=self._source_bytes, node=node).strip()
        if raw:
            for line in raw.splitlines():
                self._w.line(line.rstrip())

    def _emit_projection_def(self, node: Node) -> None:
        name = node.child_by_field_name("name")
        options = node.child_by_field_name("options")

        head_parts: list[str] = ["projection"]
        if name is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=name).strip()
            )

        if options is not None:
            for opt in options.named_children:
                if opt.type != "projection_option":
                    continue
                projection_id = opt.child_by_field_name("projection_id")
                if projection_id is not None:
                    head_parts.append("name")
                    head_parts.append(
                        _node_text(
                            source_bytes=self._source_bytes, node=projection_id
                        ).strip()
                    )
                    continue
                label = opt.child_by_field_name("label")
                if label is not None:
                    head_parts.append("label")
                    head_parts.append(
                        _node_text(source_bytes=self._source_bytes, node=label).strip()
                    )
                    continue
                flag = opt.child_by_field_name("is_branchable")
                if flag is not None:
                    head_parts.append(
                        _node_text(source_bytes=self._source_bytes, node=flag).strip()
                        or "is_branchable"
                    )
                    continue
                raw_opt = _node_text(source_bytes=self._source_bytes, node=opt).strip()
                if raw_opt:
                    head_parts.append(raw_opt)

        self._w.line(" ".join(p for p in head_parts if p) + " {")
        with self._w.indent():
            members: list[Node] = []
            for c in node.named_children:
                if c.type == "comment":
                    members.append(c)
                    continue
                if c.type == "projection_item":
                    # projection_item is a wrapper; emit the inner node(s).
                    members.extend(
                        [
                            inner
                            for inner in c.named_children
                            if inner.type
                            in {
                                "projection_root",
                                "projection_edge",
                                "projection_branch",
                                "projection_view_group",
                                "projection_view_def",
                            }
                        ]
                    )
            self._emit_projection_members(members)
        self._w.line("}")

    def _emit_experience_def(self, node: Node) -> None:
        name = node.child_by_field_name("name")
        projection = node.child_by_field_name("projection")

        head_parts: list[str] = ["experience"]
        if name is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=name).strip()
            )
        if projection is not None:
            head_parts.extend(
                [
                    "on",
                    _node_text(
                        source_bytes=self._source_bytes, node=projection
                    ).strip(),
                ]
            )

        self._w.line(" ".join(p for p in head_parts if p) + " {")
        with self._w.indent():
            members: list[Node] = []
            for c in node.named_children:
                if c.type == "comment":
                    members.append(c)
                    continue
                if c.type == "experience_item":
                    members.extend(
                        [
                            inner
                            for inner in c.named_children
                            if inner.type
                            in {
                                "experience_branch",
                                "experience_observable_group",
                                "experience_node_def",
                                "experience_surface_def",
                            }
                        ]
                    )
            self._emit_experience_members(members)
        self._w.line("}")

    def _emit_graph_def(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        experience_node = node.child_by_field_name("experience")
        name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        experience = (
            _node_text(source_bytes=self._source_bytes, node=experience_node).strip()
            if experience_node is not None
            else ""
        )
        head = f"graph {name} on {experience}".strip()
        self._w.line(f"{head} {{")
        with self._w.indent():
            members: list[Node] = []
            for c in node.named_children:
                if c.type == "comment":
                    members.append(c)
                    continue
                if c.type == "graph_item":
                    members.extend(
                        [
                            inner
                            for inner in c.named_children
                            if inner.type in {"graph_root_stmt", "graph_edge_stmt"}
                        ]
                    )
            self._emit_graph_members(members)
        self._w.line("}")

    def _emit_graph_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "graph_root_stmt":
                self._emit_graph_root_stmt(member)
            elif member.type == "graph_edge_stmt":
                self._emit_graph_edge_stmt(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_graph_root_stmt(self, node: Node) -> None:
        ref_node = node.child_by_field_name("ref")
        ref = (
            _node_text(source_bytes=self._source_bytes, node=ref_node).strip()
            if ref_node is not None
            else ""
        )
        text = f"root {ref}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        self._w.line(text)

    def _emit_graph_edge_stmt(self, node: Node) -> None:
        parent_node = node.child_by_field_name("parent")
        child_node = node.child_by_field_name("child")
        parent = (
            _node_text(source_bytes=self._source_bytes, node=parent_node).strip()
            if parent_node is not None
            else ""
        )
        child = (
            _node_text(source_bytes=self._source_bytes, node=child_node).strip()
            if child_node is not None
            else ""
        )
        text = f"node {parent} {child}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        self._w.line(text)

    def _emit_api_def(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        head = f"api {name}".strip()
        self._w.line(f"{head} {{")
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type == "comment":
                    members.append(child)
                    continue
                if child.type == "api_item":
                    members.extend(
                        [
                            inner
                            for inner in child.named_children
                            if inner.type in {"api_capability_def", "api_graph_def"}
                        ]
                    )
            self._emit_api_members(members)
        self._w.line("}")

    def _emit_service_def(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        self._w.line(f"service {name} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type == "comment":
                    members.append(child)
                    continue
                if child.type == "service_item":
                    members.extend(
                        [
                            inner
                            for inner in child.named_children
                            if inner.type
                            in {
                                "service_api_decl",
                                "service_experience_decl",
                                "service_operation_def",
                                "service_contract_config_def",
                            }
                        ]
                    )
            self._emit_service_members(members)
        self._w.line("}")

    def _emit_service_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_api_decl":
                self._emit_service_api_decl(member)
            elif member.type == "service_experience_decl":
                self._emit_service_experience_decl(member)
            elif member.type == "service_operation_def":
                self._emit_service_operation_def(member)
            elif member.type == "service_contract_config_def":
                self._emit_service_contract_config_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_api_decl(self, node: Node) -> None:
        api_node = node.child_by_field_name("api")
        api = (
            _node_text(source_bytes=self._source_bytes, node=api_node).strip()
            if api_node is not None
            else ""
        )
        self._w.line(f"api {api};".rstrip())

    def _emit_service_experience_decl(self, node: Node) -> None:
        experience_node = node.child_by_field_name("experience")
        experience = (
            _node_text(source_bytes=self._source_bytes, node=experience_node).strip()
            if experience_node is not None
            else ""
        )
        self._w.line(f"experience {experience};".rstrip())

    def _emit_service_operation_def(self, node: Node) -> None:
        operation_name_node = node.child_by_field_name("operation_name")
        body_node = node.child_by_field_name("body")
        operation_name = (
            _node_text(
                source_bytes=self._source_bytes, node=operation_name_node
            ).strip()
            if operation_name_node is not None
            else ""
        )
        self._w.line(f"operation {operation_name} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type in {
                        "comment",
                        "service_operation_item",
                        "service_operation_endpoint_def",
                        "service_operation_view_def",
                        "service_operation_role_requirement_def",
                        "service_operation_admission_policy_decl",
                        "service_operation_receipt_policy_decl",
                        "service_operation_settlement_decl",
                        "service_operation_price_def",
                    }:
                        members.append(child)
            self._emit_service_operation_members(members)
        self._w.line("}")

    def _emit_service_operation_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_operation_item":
                for inner in member.named_children:
                    if inner.type == "service_operation_endpoint_def":
                        self._emit_service_operation_endpoint_def(inner)
                    elif inner.type == "service_operation_view_def":
                        self._emit_service_operation_view_def(inner)
                    elif inner.type == "service_operation_role_requirement_def":
                        self._emit_service_operation_role_requirement_def(inner)
                    elif inner.type == "service_operation_admission_policy_decl":
                        self._emit_service_operation_admission_policy_decl(inner)
                    elif inner.type == "service_operation_receipt_policy_decl":
                        self._emit_service_operation_receipt_policy_decl(inner)
                    elif inner.type == "service_operation_settlement_decl":
                        self._emit_service_operation_settlement_decl(inner)
                    elif inner.type == "service_operation_price_def":
                        self._emit_service_operation_price_def(inner)
            elif member.type == "service_operation_endpoint_def":
                self._emit_service_operation_endpoint_def(member)
            elif member.type == "service_operation_view_def":
                self._emit_service_operation_view_def(member)
            elif member.type == "service_operation_role_requirement_def":
                self._emit_service_operation_role_requirement_def(member)
            elif member.type == "service_operation_admission_policy_decl":
                self._emit_service_operation_admission_policy_decl(member)
            elif member.type == "service_operation_receipt_policy_decl":
                self._emit_service_operation_receipt_policy_decl(member)
            elif member.type == "service_operation_settlement_decl":
                self._emit_service_operation_settlement_decl(member)
            elif member.type == "service_operation_price_def":
                self._emit_service_operation_price_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_operation_endpoint_def(self, node: Node) -> None:
        endpoint_node = node.child_by_field_name("endpoint")
        endpoint = (
            _node_text(source_bytes=self._source_bytes, node=endpoint_node).strip()
            if endpoint_node is not None
            else ""
        )
        self._w.line(f"endpoint {endpoint};".rstrip())

    def _emit_service_operation_view_def(self, node: Node) -> None:
        view_node = node.child_by_field_name("view")
        body_node = node.child_by_field_name("body")
        view = (
            _node_text(source_bytes=self._source_bytes, node=view_node).strip()
            if view_node is not None
            else ""
        )
        if body_node is None:
            self._w.line(f"view {view};".rstrip())
            return
        self._w.line(f"view {view} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in body_node.named_children:
                if child.type in {
                    "comment",
                    "service_operation_view_item",
                    "service_operation_view_provider_decl",
                }:
                    members.append(child)
            self._emit_service_operation_view_members(members)
        self._w.line("}")

    def _emit_service_operation_view_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_operation_view_item":
                for inner in member.named_children:
                    if inner.type == "service_operation_view_provider_decl":
                        self._emit_service_operation_view_provider_decl(inner)
            elif member.type == "service_operation_view_provider_decl":
                self._emit_service_operation_view_provider_decl(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_operation_view_provider_decl(self, node: Node) -> None:
        provider_kind_node = node.child_by_field_name("provider_kind")
        provider_kind = (
            _node_text(source_bytes=self._source_bytes, node=provider_kind_node).strip()
            if provider_kind_node is not None
            else ""
        )
        self._w.line(f"provider {provider_kind};".rstrip())

    def _emit_service_operation_role_requirement_def(self, node: Node) -> None:
        role_node = node.child_by_field_name("role")
        body_node = node.child_by_field_name("body")
        role = (
            _node_text(source_bytes=self._source_bytes, node=role_node).strip()
            if role_node is not None
            else ""
        )
        if body_node is None:
            self._w.line(f"role {role};".rstrip())
            return
        self._w.line(f"role {role} {{".rstrip())
        self._emit_service_role_gate_body(body_node)
        self._w.line("}")

    def _emit_service_operation_admission_policy_decl(self, node: Node) -> None:
        admission_mode_node = node.child_by_field_name("admission_mode")
        admission_mode = (
            _node_text(
                source_bytes=self._source_bytes, node=admission_mode_node
            ).strip()
            if admission_mode_node is not None
            else ""
        )
        self._w.line(f"admission {admission_mode};".rstrip())

    def _emit_service_operation_receipt_policy_decl(self, node: Node) -> None:
        receipt_policy_node = node.child_by_field_name("receipt_policy")
        receipt_policy = (
            _node_text(
                source_bytes=self._source_bytes, node=receipt_policy_node
            ).strip()
            if receipt_policy_node is not None
            else ""
        )
        self._w.line(f"receipt {receipt_policy};".rstrip())

    def _emit_service_operation_settlement_decl(self, node: Node) -> None:
        settlement_policy_node = node.child_by_field_name("settlement_policy")
        settlement_policy = (
            _node_text(
                source_bytes=self._source_bytes, node=settlement_policy_node
            ).strip()
            if settlement_policy_node is not None
            else ""
        )
        self._w.line(f"settlement {settlement_policy};".rstrip())

    def _emit_service_operation_price_def(self, node: Node) -> None:
        body_node = node.child_by_field_name("body")
        self._w.line("price {")
        with self._w.indent():
            members: list[Node] = []
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type in {
                        "comment",
                        "service_operation_price_item",
                        "service_operation_price_coin_decl",
                        "service_operation_price_type_decl",
                        "service_operation_price_fixed_amount_decl",
                        "service_operation_price_markup_percentage_decl",
                        "service_operation_price_effective_from_decl",
                        "service_operation_price_effective_until_decl",
                        "service_operation_price_policy_def",
                    }:
                        members.append(child)
            self._emit_service_operation_price_members(members)
        self._w.line("}")

    def _emit_service_operation_price_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_operation_price_item":
                for inner in member.named_children:
                    self._emit_service_operation_price_member(inner)
            else:
                self._emit_service_operation_price_member(member)

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_operation_price_member(self, node: Node) -> None:
        if node.type == "service_operation_price_coin_decl":
            self._emit_service_operation_price_coin_decl(node)
        elif node.type == "service_operation_price_type_decl":
            self._emit_service_operation_price_type_decl(node)
        elif node.type == "service_operation_price_fixed_amount_decl":
            self._emit_service_operation_price_fixed_amount_decl(node)
        elif node.type == "service_operation_price_markup_percentage_decl":
            self._emit_service_operation_price_markup_percentage_decl(node)
        elif node.type == "service_operation_price_effective_from_decl":
            self._emit_service_operation_price_effective_from_decl(node)
        elif node.type == "service_operation_price_effective_until_decl":
            self._emit_service_operation_price_effective_until_decl(node)
        elif node.type == "service_operation_price_policy_def":
            self._emit_service_operation_price_policy_def(node)
        else:
            raw = _node_text(source_bytes=self._source_bytes, node=node).strip()
            if raw:
                for line in raw.splitlines():
                    self._w.line(line.rstrip())

    def _emit_service_operation_price_coin_decl(self, node: Node) -> None:
        coin_symbol_node = node.child_by_field_name("coin_symbol")
        coin_symbol = (
            _node_text(source_bytes=self._source_bytes, node=coin_symbol_node).strip()
            if coin_symbol_node is not None
            else ""
        )
        self._w.line(f"coin {coin_symbol};".rstrip())

    def _emit_service_operation_price_type_decl(self, node: Node) -> None:
        price_type_node = node.child_by_field_name("price_type")
        price_type = (
            _node_text(source_bytes=self._source_bytes, node=price_type_node).strip()
            if price_type_node is not None
            else ""
        )
        self._w.line(f"type {price_type};".rstrip())

    def _emit_service_operation_price_fixed_amount_decl(self, node: Node) -> None:
        fixed_amount_node = node.child_by_field_name("fixed_amount")
        fixed_amount = (
            _node_text(source_bytes=self._source_bytes, node=fixed_amount_node).strip()
            if fixed_amount_node is not None
            else ""
        )
        self._w.line(f"fixed_amount {fixed_amount};".rstrip())

    def _emit_service_operation_price_markup_percentage_decl(self, node: Node) -> None:
        markup_percentage_node = node.child_by_field_name("markup_percentage")
        markup_percentage = (
            _node_text(
                source_bytes=self._source_bytes, node=markup_percentage_node
            ).strip()
            if markup_percentage_node is not None
            else ""
        )
        self._w.line(f"markup_percentage {markup_percentage};".rstrip())

    def _emit_service_operation_price_effective_from_decl(self, node: Node) -> None:
        effective_from_node = node.child_by_field_name("effective_from")
        effective_from = (
            _node_text(
                source_bytes=self._source_bytes, node=effective_from_node
            ).strip()
            if effective_from_node is not None
            else ""
        )
        self._w.line(f"effective_from {effective_from};".rstrip())

    def _emit_service_operation_price_effective_until_decl(self, node: Node) -> None:
        effective_until_node = node.child_by_field_name("effective_until")
        effective_until = (
            _node_text(
                source_bytes=self._source_bytes, node=effective_until_node
            ).strip()
            if effective_until_node is not None
            else ""
        )
        self._w.line(f"effective_until {effective_until};".rstrip())

    def _emit_service_operation_price_policy_def(self, node: Node) -> None:
        body_node = node.child_by_field_name("body")
        self._w.line("policy {")
        with self._w.indent():
            members: list[Node] = []
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type in {
                        "comment",
                        "service_operation_price_policy_item",
                        "service_operation_price_policy_fail_closed_decl",
                    }:
                        members.append(child)
            self._emit_service_operation_price_policy_members(members)
        self._w.line("}")

    def _emit_service_operation_price_policy_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_operation_price_policy_item":
                for inner in member.named_children:
                    if inner.type == "service_operation_price_policy_fail_closed_decl":
                        self._emit_service_operation_price_policy_fail_closed_decl(
                            inner
                        )
            elif member.type == "service_operation_price_policy_fail_closed_decl":
                self._emit_service_operation_price_policy_fail_closed_decl(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_operation_price_policy_fail_closed_decl(self, node: Node) -> None:
        fail_closed_node = node.child_by_field_name("fail_closed")
        fail_closed = (
            _node_text(source_bytes=self._source_bytes, node=fail_closed_node).strip()
            if fail_closed_node is not None
            else ""
        )
        self._w.line(f"fail_closed {fail_closed};".rstrip())

    def _emit_service_contract_config_def(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        body_node = node.child_by_field_name("body")
        name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        self._w.line(f"contract {name} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type in {
                        "comment",
                        "service_contract_config_item",
                        "service_contract_kind_decl",
                        "service_contract_projection_experience_decl",
                        "service_contract_operation_grant_def",
                        "service_contract_actor_role_grant_def",
                    }:
                        members.append(child)
            self._emit_service_contract_config_members(members)
        self._w.line("}")

    def _emit_service_contract_config_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_contract_config_item":
                for inner in member.named_children:
                    self._emit_service_contract_config_member(inner)
            else:
                self._emit_service_contract_config_member(member)

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_contract_config_member(self, node: Node) -> None:
        if node.type == "service_contract_kind_decl":
            self._emit_service_contract_kind_decl(node)
        elif node.type == "service_contract_projection_experience_decl":
            self._emit_service_contract_projection_experience_decl(node)
        elif node.type == "service_contract_operation_grant_def":
            self._emit_service_contract_operation_grant_def(node)
        elif node.type == "service_contract_actor_role_grant_def":
            self._emit_service_contract_actor_role_grant_def(node)
        else:
            raw = _node_text(source_bytes=self._source_bytes, node=node).strip()
            if raw:
                for line in raw.splitlines():
                    self._w.line(line.rstrip())

    def _emit_service_contract_kind_decl(self, node: Node) -> None:
        contract_kind_node = node.child_by_field_name("contract_kind")
        contract_kind = (
            _node_text(source_bytes=self._source_bytes, node=contract_kind_node).strip()
            if contract_kind_node is not None
            else ""
        )
        self._w.line(f"kind {contract_kind};".rstrip())

    def _emit_service_contract_projection_experience_decl(self, node: Node) -> None:
        projection_experience_node = node.child_by_field_name("projection_experience")
        projection_experience = (
            _node_text(
                source_bytes=self._source_bytes, node=projection_experience_node
            ).strip()
            if projection_experience_node is not None
            else ""
        )
        self._w.line(f"projection_experience {projection_experience};".rstrip())

    def _emit_service_contract_operation_grant_def(self, node: Node) -> None:
        operation_node = node.child_by_field_name("operation")
        body_node = node.child_by_field_name("body")
        operation = (
            _node_text(source_bytes=self._source_bytes, node=operation_node).strip()
            if operation_node is not None
            else ""
        )
        if body_node is None:
            self._w.line(f"grant operation {operation};".rstrip())
            return
        self._w.line(f"grant operation {operation} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in body_node.named_children:
                if child.type in {
                    "comment",
                    "service_contract_operation_grant_item",
                    "service_role_access_decl",
                }:
                    members.append(child)
            self._emit_service_contract_operation_grant_members(members)
        self._w.line("}")

    def _emit_service_contract_operation_grant_members(
        self, members: list[Node]
    ) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_contract_operation_grant_item":
                for inner in member.named_children:
                    if inner.type == "service_role_access_decl":
                        self._emit_service_role_access_decl(inner)
            elif member.type == "service_role_access_decl":
                self._emit_service_role_access_decl(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_contract_actor_role_grant_def(self, node: Node) -> None:
        role_node = node.child_by_field_name("role")
        body_node = node.child_by_field_name("body")
        role = (
            _node_text(source_bytes=self._source_bytes, node=role_node).strip()
            if role_node is not None
            else ""
        )
        if body_node is None:
            self._w.line(f"grant actor_role {role};".rstrip())
            return
        self._w.line(f"grant actor_role {role} {{".rstrip())
        self._emit_service_role_gate_body(body_node)
        self._w.line("}")

    def _emit_service_role_gate_body(self, body_node: Node) -> None:
        with self._w.indent():
            members: list[Node] = []
            for child in body_node.named_children:
                if child.type in {
                    "comment",
                    "service_role_gate_item",
                    "service_role_access_decl",
                    "service_role_scope_decl",
                    "service_role_class_instance_identity_required_decl",
                    "service_role_assignment_binding_required_decl",
                }:
                    members.append(child)
            self._emit_service_role_gate_members(members)

    def _emit_service_role_gate_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "service_role_gate_item":
                for inner in member.named_children:
                    self._emit_service_role_gate_member(inner)
            else:
                self._emit_service_role_gate_member(member)

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_service_role_gate_member(self, node: Node) -> None:
        if node.type == "service_role_access_decl":
            self._emit_service_role_access_decl(node)
        elif node.type == "service_role_scope_decl":
            self._emit_service_role_scope_decl(node)
        elif node.type == "service_role_class_instance_identity_required_decl":
            self._emit_service_role_class_instance_identity_required_decl(node)
        elif node.type == "service_role_assignment_binding_required_decl":
            self._emit_service_role_assignment_binding_required_decl(node)
        else:
            raw = _node_text(source_bytes=self._source_bytes, node=node).strip()
            if raw:
                for line in raw.splitlines():
                    self._w.line(line.rstrip())

    def _emit_service_role_access_decl(self, node: Node) -> None:
        access_scope_node = node.child_by_field_name("access_scope")
        access_scope = (
            _node_text(source_bytes=self._source_bytes, node=access_scope_node).strip()
            if access_scope_node is not None
            else ""
        )
        self._w.line(f"access {access_scope};".rstrip())

    def _emit_service_role_scope_decl(self, node: Node) -> None:
        scope_kind_node = node.child_by_field_name("scope_kind")
        scope_ref_node = node.child_by_field_name("scope_ref")
        scope_kind = (
            _node_text(source_bytes=self._source_bytes, node=scope_kind_node).strip()
            if scope_kind_node is not None
            else ""
        )
        scope_ref = (
            _node_text(source_bytes=self._source_bytes, node=scope_ref_node).strip()
            if scope_ref_node is not None
            else ""
        )
        suffix = f" {scope_ref}" if scope_ref else ""
        self._w.line(f"scope {scope_kind}{suffix};".rstrip())

    def _emit_service_role_class_instance_identity_required_decl(
        self, node: Node
    ) -> None:
        value_node = node.child_by_field_name("class_instance_identity_required")
        value = (
            _node_text(source_bytes=self._source_bytes, node=value_node).strip()
            if value_node is not None
            else ""
        )
        self._w.line(f"class_instance_identity_required {value};".rstrip())

    def _emit_service_role_assignment_binding_required_decl(self, node: Node) -> None:
        value_node = node.child_by_field_name("role_assignment_binding_required")
        value = (
            _node_text(source_bytes=self._source_bytes, node=value_node).strip()
            if value_node is not None
            else ""
        )
        self._w.line(f"role_assignment_binding_required {value};".rstrip())

    def _emit_binding_def(self, node: Node) -> None:
        source_graph_node = node.child_by_field_name("source_graph")
        target_graph_node = node.child_by_field_name("target_graph")
        source_graph = (
            _node_text(source_bytes=self._source_bytes, node=source_graph_node).strip()
            if source_graph_node is not None
            else ""
        )
        target_graph = (
            _node_text(source_bytes=self._source_bytes, node=target_graph_node).strip()
            if target_graph_node is not None
            else ""
        )
        self._w.line(f"binding {source_graph} {target_graph} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type in {"comment", "binding_map_def"}:
                    members.append(child)
            self._emit_binding_members(members)
        self._w.line("}")

    def _emit_binding_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "binding_map_def":
                self._emit_binding_map_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_binding_map_def(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        source_node = node.child_by_field_name("source")
        target_node = node.child_by_field_name("target")
        body_node = node.child_by_field_name("body")
        name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        source_ref = (
            _node_text(source_bytes=self._source_bytes, node=source_node).strip()
            if source_node is not None
            else ""
        )
        target_ref = (
            _node_text(source_bytes=self._source_bytes, node=target_node).strip()
            if target_node is not None
            else ""
        )
        head = f"map {name} {source_ref} {target_ref}".strip()
        if body_node is None:
            if (
                _node_text(source_bytes=self._source_bytes, node=node)
                .rstrip()
                .endswith(";")
            ):
                head += ";"
            self._w.line(head)
            return

        self._w.line(f"{head} {{")
        with self._w.indent():
            self._emit_binding_map_body(body_node)
        self._w.line("}")

    def _emit_binding_map_body(self, node: Node) -> None:
        members = [
            child
            for child in node.named_children
            if child.type
            in {
                "comment",
                "triple_string_literal",
                "string_literal",
                "binding_map_template_def",
            }
        ]
        self._emit_binding_map_body_members(members)

    def _emit_binding_map_body_members(self, members: list[Node]) -> None:
        idx = 0
        while idx < len(members):
            member = members[idx]
            next_idx = self._emit_string_literal_sequence_if_any(members, idx)
            if next_idx is not None:
                last_member = members[next_idx - 1]
                idx = next_idx
            else:
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "binding_map_template_def":
                    self._emit_binding_map_template_def(member)
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        self._w.line(raw)
                last_member = member
                idx += 1

            if idx < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=last_member,
                right=members[idx],
            ):
                self._w.blank_line()

    def _emit_binding_map_template_def(self, node: Node) -> None:
        body_node = node.child_by_field_name("body")
        if body_node is None:
            self._w.line("template {")
            self._w.line("}")
            return
        value_node = body_node.child_by_field_name("value")
        value = (
            _node_text(source_bytes=self._source_bytes, node=value_node).strip()
            if value_node is not None
            else ""
        )
        self._w.line("template {")
        with self._w.indent():
            if value:
                self._w.line(value)
        self._w.line("}")

    def _emit_api_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "api_capability_def":
                self._emit_api_capability_def(member)
            elif member.type == "api_graph_def":
                self._emit_api_graph_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_api_capability_def(self, node: Node) -> None:
        capability_name_node = node.child_by_field_name("capability_name")
        body_node = node.child_by_field_name("body")
        capability_name = (
            _node_text(
                source_bytes=self._source_bytes, node=capability_name_node
            ).strip()
            if capability_name_node is not None
            else ""
        )
        self._w.line(f"capability {capability_name} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type in {
                        "comment",
                        "triple_string_literal",
                        "string_literal",
                        "api_capability_item",
                        "api_capability_endpoint_def",
                    }:
                        members.append(child)
            self._emit_api_capability_members(members)
        self._w.line("}")

    def _emit_api_capability_members(self, members: list[Node]) -> None:
        idx = 0
        while idx < len(members):
            member = members[idx]
            next_idx = self._emit_string_literal_sequence_if_any(members, idx)
            if next_idx is not None:
                last_member = members[next_idx - 1]
                idx = next_idx
            else:
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "api_capability_item":
                    for inner in member.named_children:
                        if inner.type == "api_capability_endpoint_def":
                            self._emit_api_capability_endpoint_def(inner)
                elif member.type == "api_capability_endpoint_def":
                    self._emit_api_capability_endpoint_def(member)
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        for line in raw.splitlines():
                            self._w.line(line.rstrip())
                last_member = member
                idx += 1

            if idx < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=last_member,
                right=members[idx],
            ):
                self._w.blank_line()

    def _emit_api_capability_endpoint_def(self, node: Node) -> None:
        endpoint_name_node = node.child_by_field_name("endpoint_name")
        request_node = node.child_by_field_name("request")
        body_node = node.child_by_field_name("body")
        endpoint_name = (
            _node_text(source_bytes=self._source_bytes, node=endpoint_name_node).strip()
            if endpoint_name_node is not None
            else ""
        )
        request = (
            _node_text(source_bytes=self._source_bytes, node=request_node).strip()
            if request_node is not None
            else ""
        )
        head = f"endpoint {endpoint_name} {request}".strip()
        if body_node is None:
            self._w.line(f"{head};")
            return
        self._w.line(f"{head} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in body_node.named_children:
                if child.type in {
                    "comment",
                    "triple_string_literal",
                    "string_literal",
                    "api_capability_endpoint_item",
                    "api_capability_endpoint_response_def",
                    "api_capability_endpoint_stream_def",
                }:
                    members.append(child)
            self._emit_api_capability_endpoint_members(members)
        self._w.line("}")

    def _emit_api_capability_endpoint_members(self, members: list[Node]) -> None:
        idx = 0
        while idx < len(members):
            member = members[idx]
            next_idx = self._emit_string_literal_sequence_if_any(members, idx)
            if next_idx is not None:
                last_member = members[next_idx - 1]
                idx = next_idx
            else:
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "api_capability_endpoint_item":
                    for inner in member.named_children:
                        if inner.type == "api_capability_endpoint_response_def":
                            self._emit_api_capability_endpoint_response_def(inner)
                        elif inner.type == "api_capability_endpoint_stream_def":
                            self._emit_api_capability_endpoint_stream_def(inner)
                elif member.type == "api_capability_endpoint_response_def":
                    self._emit_api_capability_endpoint_response_def(member)
                elif member.type == "api_capability_endpoint_stream_def":
                    self._emit_api_capability_endpoint_stream_def(member)
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        for line in raw.splitlines():
                            self._w.line(line.rstrip())
                last_member = member
                idx += 1

            if idx < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=last_member,
                right=members[idx],
            ):
                self._w.blank_line()

    def _emit_api_capability_endpoint_response_def(self, node: Node) -> None:
        response_node = node.child_by_field_name("response")
        response = (
            _node_text(source_bytes=self._source_bytes, node=response_node).strip()
            if response_node is not None
            else ""
        )
        head = f"response {response}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            head += ";"
        self._w.line(head)

    def _emit_api_capability_endpoint_stream_def(self, node: Node) -> None:
        stream_mode_node = node.child_by_field_name("stream_mode")
        body_node = node.child_by_field_name("body")
        stream_mode = (
            _node_text(source_bytes=self._source_bytes, node=stream_mode_node).strip()
            if stream_mode_node is not None
            else ""
        )
        self._w.line(f"stream {stream_mode} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type in {
                        "comment",
                        "triple_string_literal",
                        "string_literal",
                        "api_capability_endpoint_stream_item",
                        "api_capability_endpoint_stream_event_def",
                    }:
                        members.append(child)
            self._emit_api_capability_endpoint_stream_members(members)
        self._w.line("}")

    def _emit_api_capability_endpoint_stream_members(self, members: list[Node]) -> None:
        idx = 0
        while idx < len(members):
            member = members[idx]
            next_idx = self._emit_string_literal_sequence_if_any(members, idx)
            if next_idx is not None:
                last_member = members[next_idx - 1]
                idx = next_idx
            else:
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "api_capability_endpoint_stream_item":
                    for inner in member.named_children:
                        if inner.type == "api_capability_endpoint_stream_event_def":
                            self._emit_api_capability_endpoint_stream_event_def(inner)
                elif member.type == "api_capability_endpoint_stream_event_def":
                    self._emit_api_capability_endpoint_stream_event_def(member)
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        for line in raw.splitlines():
                            self._w.line(line.rstrip())
                last_member = member
                idx += 1

            if idx < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=last_member,
                right=members[idx],
            ):
                self._w.blank_line()

    def _emit_api_capability_endpoint_stream_event_def(self, node: Node) -> None:
        kind_node = node.child_by_field_name("kind")
        class_node = node.child_by_field_name("class")
        kind = (
            _node_text(source_bytes=self._source_bytes, node=kind_node).strip()
            if kind_node is not None
            else ""
        )
        class_ref = (
            _node_text(source_bytes=self._source_bytes, node=class_node).strip()
            if class_node is not None
            else ""
        )
        head = f"event {kind} {class_ref}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            head += ";"
        self._w.line(head)

    def _emit_api_graph_def(self, node: Node) -> None:
        graph_node = node.child_by_field_name("graph")
        graph = (
            _node_text(source_bytes=self._source_bytes, node=graph_node).strip()
            if graph_node is not None
            else ""
        )
        self._w.line(f"graph {graph} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type == "comment":
                    members.append(child)
                    continue
                if child.type == "api_graph_item":
                    members.extend(
                        [
                            inner
                            for inner in child.named_children
                            if inner.type
                            in {"api_graph_projection_def", "api_graph_capability_def"}
                        ]
                    )
            self._emit_api_graph_members(members)
        self._w.line("}")

    def _emit_api_graph_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "api_graph_projection_def":
                self._emit_api_graph_projection_def(member)
            elif member.type == "api_graph_capability_def":
                self._emit_api_graph_capability_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_api_graph_projection_def(self, node: Node) -> None:
        projection_node = node.child_by_field_name("projection")
        projection = (
            _node_text(source_bytes=self._source_bytes, node=projection_node).strip()
            if projection_node is not None
            else ""
        )
        self._w.line(f"projection {projection} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type == "comment":
                    members.append(child)
                    continue
                if child.type == "api_graph_projection_item":
                    members.extend(
                        [
                            inner
                            for inner in child.named_children
                            if inner.type == "api_graph_projection_binding_def"
                        ]
                    )
            self._emit_api_graph_projection_members(members)
        self._w.line("}")

    def _emit_api_graph_projection_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "api_graph_projection_binding_def":
                self._emit_api_graph_projection_binding_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_api_graph_projection_binding_def(self, node: Node) -> None:
        binding_node = node.child_by_field_name("binding")
        anchor_node = node.child_by_field_name("anchor")
        binding_ref = (
            _node_text(source_bytes=self._source_bytes, node=binding_node).strip()
            if binding_node is not None
            else ""
        )
        anchor = (
            _node_text(source_bytes=self._source_bytes, node=anchor_node).strip()
            if anchor_node is not None
            else ""
        )
        head = f"binding {binding_ref} {anchor}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            head += ";"
        self._w.line(head)

    def _emit_api_graph_capability_def(self, node: Node) -> None:
        capability_name_node = node.child_by_field_name("capability_name")
        capability_name = (
            _node_text(
                source_bytes=self._source_bytes, node=capability_name_node
            ).strip()
            if capability_name_node is not None
            else ""
        )
        self._w.line(f"capability {capability_name} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type == "comment":
                    members.append(child)
                    continue
                if child.type == "api_graph_capability_item":
                    members.extend(
                        [
                            inner
                            for inner in child.named_children
                            if inner.type == "api_graph_capability_function_def"
                        ]
                    )
            self._emit_api_graph_capability_members(members)
        self._w.line("}")

    def _emit_api_graph_capability_members(self, members: list[Node]) -> None:
        for idx, member in enumerate(members):
            if member.type == "comment":
                self._emit_comment(member)
            elif member.type == "api_graph_capability_function_def":
                self._emit_api_graph_capability_function_def(member)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=member).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes,
                left=member,
                right=members[idx + 1],
            ):
                self._w.blank_line()

    def _emit_api_graph_capability_function_def(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        target_node = node.child_by_field_name("target")
        name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        target = (
            _node_text(source_bytes=self._source_bytes, node=target_node).strip()
            if target_node is not None
            else ""
        )
        head = f"function {name} {target}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            head += ";"
        self._w.line(head)

    def _emit_string_literal_sequence_if_any(
        self, members: list[Node], start_idx: int
    ) -> int | None:
        if members[start_idx].type not in {"string_literal", "triple_string_literal"}:
            return None

        idx = start_idx
        literal_texts: list[str] = []
        while idx < len(members) and members[idx].type in {
            "string_literal",
            "triple_string_literal",
        }:
            literal_texts.append(
                _node_text(source_bytes=self._source_bytes, node=members[idx]).strip()
            )
            idx += 1

        for line in self._canonicalize_string_literal_sequence(literal_texts):
            self._w.line(line)
        return idx

    def _canonicalize_string_literal_sequence(
        self, literal_texts: list[str]
    ) -> list[str]:
        if (
            len(literal_texts) == 3
            and literal_texts[0] == '""'
            and literal_texts[2] == '""'
        ):
            middle = literal_texts[1]
            if len(middle) >= 2 and middle[0] == '"' and middle[-1] == '"':
                return [f'"""{middle[1:-1]}"""']
        return literal_texts

    def _emit_comment(self, node: Node) -> None:
        self._w.line(_node_text(source_bytes=self._source_bytes, node=node).rstrip())

    def _emit_raw_block_contents(self, block_node: Node) -> None:
        raw = _node_text(source_bytes=self._source_bytes, node=block_node)
        if len(raw) >= 2 and raw[0] == "{" and raw[-1] == "}":
            raw = raw[1:-1]
        body = textwrap.dedent(raw).strip("\n")
        if not body.strip():
            return
        for line in body.splitlines():
            stripped = line.rstrip()
            if stripped:
                self._w.line(stripped)
            else:
                self._w.line()

    def _emit_import_stmt(self, node: Node) -> None:
        target = node.child_by_field_name("target")
        alias = node.child_by_field_name("alias")
        if target is None:
            return
        parts = [
            "import",
            _node_text(source_bytes=self._source_bytes, node=target).strip(),
        ]
        if alias is not None:
            parts.extend(
                ["as", _node_text(source_bytes=self._source_bytes, node=alias).strip()]
            )
        text = " ".join(p for p in parts if p)
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        self._w.line(text)

    def _emit_class_like(self, node: Node, *, keyword: str) -> None:
        name = node.child_by_field_name("name")
        mods = node.child_by_field_name("modifiers")
        verb = node.child_by_field_name("verb")
        verb_target = node.child_by_field_name("verb_target")

        head_parts: list[str] = [keyword]
        if name is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=name).strip()
            )

        if mods is not None:
            attrs = [
                _node_text(source_bytes=self._source_bytes, node=ch).strip()
                for ch in mods.named_children
                if ch.type == "class_attr"
            ]
            if attrs:
                head_parts.append(":")
                head_parts.append(", ".join(attrs))

        if verb is not None and verb_target is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=verb).strip()
            )
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=verb_target).strip()
            )

        self._w.line(" ".join(p for p in head_parts if p) + " {")
        with self._w.indent():
            members = [
                c
                for c in node.named_children
                if c.type in {"comment", "attr_def", "fn_def"}
            ]
            self._emit_block_members(members)
        self._w.line("}")

    def _emit_enum_def(self, node: Node) -> None:
        name = node.child_by_field_name("name")
        mods = node.child_by_field_name("modifiers")

        head_parts: list[str] = ["enum"]
        if name is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=name).strip()
            )
        if mods is not None:
            attrs = [
                _node_text(source_bytes=self._source_bytes, node=ch).strip()
                for ch in mods.named_children
                if ch.type == "class_attr"
            ]
            if attrs:
                head_parts.append(":")
                head_parts.append(", ".join(attrs))

        self._w.line(" ".join(p for p in head_parts if p) + " {")
        with self._w.indent():
            members = [
                c
                for c in node.named_children
                if c.type in {"comment", "enum_value_def"}
            ]
            self._emit_block_members(members)
        self._w.line("}")

    def _emit_block_members(self, members: list[Node]) -> None:
        for idx, m in enumerate(members):
            if m.type == "comment":
                self._emit_comment(m)
            elif m.type == "attr_def":
                self._w.line(self._format_attr_def(m))
            elif m.type == "fn_def":
                self._emit_fn_def(m)
            elif m.type == "enum_value_def":
                self._w.line(self._format_enum_value_def(m))
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=m).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes, left=m, right=members[idx + 1]
            ):
                self._w.blank_line()

    def _emit_projection_members(self, members: list[Node]) -> None:
        for idx, m in enumerate(members):
            t = m.type
            if t == "comment":
                self._emit_comment(m)
            elif t == "projection_root":
                self._w.line(self._format_projection_root(m))
            elif t == "projection_edge":
                self._w.line(self._format_projection_edge(m))
            elif t == "projection_branch":
                self._emit_projection_branch(m)
            elif t == "projection_view_group":
                self._emit_projection_view_group(m)
            elif t == "projection_view_def":
                self._emit_projection_view_def(m)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=m).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes, left=m, right=members[idx + 1]
            ):
                self._w.blank_line()

    def _emit_experience_members(self, members: list[Node]) -> None:
        for idx, m in enumerate(members):
            t = m.type
            if t == "comment":
                self._emit_comment(m)
            elif t == "experience_branch":
                self._emit_experience_branch(m)
            elif t == "experience_observable_group":
                self._emit_experience_observable_group(m)
            elif t == "experience_node_def":
                self._emit_experience_node_def(m)
            elif t == "experience_surface_def":
                self._emit_experience_surface_def(m)
            else:
                raw = _node_text(source_bytes=self._source_bytes, node=m).strip()
                if raw:
                    for line in raw.splitlines():
                        self._w.line(line.rstrip())

            if idx + 1 < len(members) and _has_blank_line_between(
                source_bytes=self._source_bytes, left=m, right=members[idx + 1]
            ):
                self._w.blank_line()

    def _format_projection_root(self, node: Node) -> str:
        type_node = node.child_by_field_name("type")
        type_ref = (
            _node_text(source_bytes=self._source_bytes, node=type_node).strip()
            if type_node is not None
            else ""
        )
        text = f"root {type_ref}".strip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        return text

    def _emit_projection_branch(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        branch_name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        body_node = node.child_by_field_name("body")
        if body_node is None:
            text = f"branch {branch_name}".strip()
            if (
                _node_text(source_bytes=self._source_bytes, node=node)
                .rstrip()
                .endswith(";")
            ):
                text += ";"
            self._w.line(text)
            return

        self._w.line(f"branch {branch_name} {{".rstrip())
        inner = self._format_block_inner(body_node)
        if inner:
            with self._w.indent():
                for raw_line in inner:
                    self._w.line(raw_line.rstrip())
        self._w.line("}")

    def _emit_experience_branch(self, node: Node) -> None:
        name_node = node.child_by_field_name("name")
        branch_name = (
            _node_text(source_bytes=self._source_bytes, node=name_node).strip()
            if name_node is not None
            else ""
        )
        is_default = any(ch.type == "default" for ch in node.children)
        body_node = node.child_by_field_name("body")

        head = f"branch {branch_name}".strip()
        if is_default:
            head = f"{head} default".strip()

        if body_node is None:
            text = head
            if (
                _node_text(source_bytes=self._source_bytes, node=node)
                .rstrip()
                .endswith(";")
            ):
                text += ";"
            self._w.line(text)
            return

        self._w.line(f"{head} {{")
        inner = self._format_block_inner(body_node)
        if inner:
            with self._w.indent():
                for raw_line in inner:
                    self._w.line(raw_line.rstrip())
        self._w.line("}")

    def _emit_experience_observable_group(self, node: Node) -> None:
        observable_node = node.child_by_field_name("observable")
        observable = (
            _node_text(source_bytes=self._source_bytes, node=observable_node).strip()
            if observable_node is not None
            else ""
        )

        self._w.line(f"observable {observable} {{".rstrip())
        with self._w.indent():
            members = [
                c
                for c in node.named_children
                if c.type in {"comment", "experience_view_def"}
            ]
            for idx, member in enumerate(members):
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "experience_view_def":
                    self._emit_experience_view_def(member)
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        for line in raw.splitlines():
                            self._w.line(line.rstrip())

                if idx + 1 < len(members) and _has_blank_line_between(
                    source_bytes=self._source_bytes, left=member, right=members[idx + 1]
                ):
                    self._w.blank_line()
        self._w.line("}")

    def _emit_experience_view_def(self, node: Node) -> None:
        view_key_node = node.child_by_field_name("view_key")
        state_model_node = node.child_by_field_name("state_model")
        state_provider_node = node.child_by_field_name("state_provider")
        body_node = node.child_by_field_name("body")
        view_key = (
            _node_text(source_bytes=self._source_bytes, node=view_key_node).strip()
            if view_key_node is not None
            else ""
        )
        state_model = (
            _node_text(source_bytes=self._source_bytes, node=state_model_node).strip()
            if state_model_node is not None
            else ""
        )
        state_provider = (
            _node_text(
                source_bytes=self._source_bytes, node=state_provider_node
            ).strip()
            if state_provider_node is not None
            else ""
        )
        is_default = any(ch.type == "default" for ch in node.children)

        head_parts = ["view", view_key]
        if is_default:
            head_parts.append("default")
        head_parts.extend(["state", state_model])
        if state_provider:
            head_parts.extend(["provider", state_provider])
        self._w.line(" ".join(p for p in head_parts if p) + " {")
        if body_node is not None:
            inner = self._format_block_inner(body_node)
            if inner:
                with self._w.indent():
                    for line in inner:
                        self._w.line(line)
        self._w.line("}")

    def _emit_experience_node_def(self, node: Node) -> None:
        node_ref_node = node.child_by_field_name("node_ref")

        node_ref = (
            _node_text(source_bytes=self._source_bytes, node=node_ref_node).strip()
            if node_ref_node is not None
            else ""
        )
        head = f"node {node_ref}".strip()

        self._w.line(f"{head} {{")
        with self._w.indent():
            members = [
                c
                for c in node.named_children
                if c.type in {"comment", "experience_node_identity_def"}
            ]
            for idx, member in enumerate(members):
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "experience_node_identity_def":
                    self._emit_experience_node_identity_def(member)
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        for line in raw.splitlines():
                            self._w.line(line.rstrip())

                if idx + 1 < len(members) and _has_blank_line_between(
                    source_bytes=self._source_bytes, left=member, right=members[idx + 1]
                ):
                    self._w.blank_line()
        self._w.line("}")

    def _emit_experience_node_identity_def(self, node: Node) -> None:
        key_node = node.child_by_field_name("key_name")
        body_node = node.child_by_field_name("body")
        key_name = (
            _node_text(source_bytes=self._source_bytes, node=key_node).strip()
            if key_node is not None
            else ""
        )
        head = f"id {key_name}".strip()
        if body_node is None:
            line = head
            if (
                _node_text(source_bytes=self._source_bytes, node=node)
                .rstrip()
                .endswith(";")
            ):
                line += ";"
            self._w.line(line)
            return

        self._w.line(f"{head} {{")
        inner = self._format_block_inner(body_node)
        if inner:
            with self._w.indent():
                for raw_line in inner:
                    self._w.line(raw_line.rstrip())
        self._w.line("}")

    def _emit_experience_surface_def(self, node: Node) -> None:
        surface_key_node = node.child_by_field_name("surface_key")
        surface_key = (
            _node_text(source_bytes=self._source_bytes, node=surface_key_node).strip()
            if surface_key_node is not None
            else ""
        )
        self._w.line(f"surface {surface_key} {{".rstrip())
        with self._w.indent():
            members: list[Node] = []
            for child in node.named_children:
                if child.type == "comment":
                    members.append(child)
                    continue
                if child.type in {
                    "experience_surface_section_decl",
                    "experience_surface_view_decl",
                    "experience_surface_graph_anchor_decl",
                    "experience_surface_node_anchor_decl",
                    "experience_surface_source_decl",
                }:
                    members.append(child)
                    continue
                if child.type == "experience_surface_item":
                    members.extend(
                        [
                            inner
                            for inner in child.named_children
                            if inner.type
                            in {
                                "comment",
                                "experience_surface_section_decl",
                                "experience_surface_view_decl",
                                "experience_surface_graph_anchor_decl",
                                "experience_surface_node_anchor_decl",
                                "experience_surface_source_decl",
                            }
                        ]
                    )
            for idx, member in enumerate(members):
                if member.type == "comment":
                    self._emit_comment(member)
                elif member.type == "experience_surface_section_decl":
                    self._emit_simple_keyword_field_line(
                        member, keyword="section", field_name="section_key"
                    )
                elif member.type == "experience_surface_view_decl":
                    self._emit_simple_keyword_field_line(
                        member, keyword="view", field_name="view_ref"
                    )
                elif member.type == "experience_surface_graph_anchor_decl":
                    self._emit_simple_keyword_field_line(
                        member, keyword="graph", field_name="graph_identity"
                    )
                elif member.type == "experience_surface_node_anchor_decl":
                    self._emit_simple_keyword_field_line(
                        member, keyword="node", field_name="node_identity"
                    )
                elif member.type == "experience_surface_source_decl":
                    self._emit_simple_keyword_field_line(
                        member, keyword="source", field_name="source_surface"
                    )
                else:
                    raw = _node_text(
                        source_bytes=self._source_bytes, node=member
                    ).strip()
                    if raw:
                        for line in raw.splitlines():
                            self._w.line(line.rstrip())

                if idx + 1 < len(members) and _has_blank_line_between(
                    source_bytes=self._source_bytes, left=member, right=members[idx + 1]
                ):
                    self._w.blank_line()
        self._w.line("}")

    def _emit_simple_keyword_field_line(
        self, node: Node, *, keyword: str, field_name: str
    ) -> None:
        value_node = node.child_by_field_name(field_name)
        value = (
            _node_text(source_bytes=self._source_bytes, node=value_node).strip()
            if value_node is not None
            else ""
        )
        line = f"{keyword} {value}".rstrip()
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            line += ";"
        self._w.line(line)

    def _format_projection_edge(self, node: Node) -> str:
        type_node = node.child_by_field_name("type")
        member_node = node.child_by_field_name("member")
        target_node = node.child_by_field_name("target")

        type_ref = (
            _node_text(source_bytes=self._source_bytes, node=type_node).strip()
            if type_node is not None
            else ""
        )
        member = (
            _node_text(source_bytes=self._source_bytes, node=member_node).strip()
            if member_node is not None
            else ""
        )

        parts: list[str] = []
        if type_ref and member:
            parts.append(f"{type_ref}::{member}")
        else:
            raw = _node_text(source_bytes=self._source_bytes, node=node).strip()
            if raw:
                parts.append(raw)

        if target_node is not None:
            target = _node_text(
                source_bytes=self._source_bytes, node=target_node
            ).strip()
            if target:
                parts.append(target)

        text = " ".join(p for p in parts if p)
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        return text

    def _emit_projection_view_group(self, node: Node) -> None:
        prefix_node = node.child_by_field_name("prefix")
        prefix = (
            _node_text(source_bytes=self._source_bytes, node=prefix_node).strip()
            if prefix_node is not None
            else ""
        )
        self._w.line(f"observable {prefix} {{".rstrip())
        with self._w.indent():
            members = [
                c
                for c in node.named_children
                if c.type in {"comment", "projection_view_group", "projection_view_def"}
            ]
            self._emit_projection_members(members)
        self._w.line("}")

    def _emit_projection_view_def(self, node: Node) -> None:
        view_key_node = node.child_by_field_name("view_key")
        kind_node = node.child_by_field_name("kind")
        body_node = node.child_by_field_name("body")

        view_key = (
            _node_text(source_bytes=self._source_bytes, node=view_key_node).strip()
            if view_key_node is not None
            else ""
        )
        kind = (
            _node_text(source_bytes=self._source_bytes, node=kind_node).strip()
            if kind_node is not None
            else ""
        )
        is_default = any(ch.type == "default" for ch in node.children)

        head_parts = ["observable", view_key, kind]
        if is_default:
            head_parts.append("default")

        self._w.line(" ".join(p for p in head_parts if p) + " {")
        if body_node is not None:
            inner = self._format_block_inner(body_node)
            if inner:
                with self._w.indent():
                    for line in inner:
                        self._w.line(line)
        self._w.line("}")

    def _format_attr_def(self, node: Node) -> str:
        name = node.child_by_field_name("name")
        type_ref = node.child_by_field_name("type")
        cardinality = node.child_by_field_name("cardinality")
        identity_key = node.child_by_field_name("identity_key")
        default = node.child_by_field_name("default")

        parts: list[str] = []
        if name is not None:
            parts.append(_node_text(source_bytes=self._source_bytes, node=name).strip())
        if type_ref is not None:
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=type_ref).strip()
            )
        if cardinality is not None:
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=cardinality).strip()
            )
        if identity_key is not None:
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=identity_key).strip()
            )
        if default is not None:
            parts.append("=")
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=default).strip()
            )

        text = " ".join(p for p in parts if p)
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        return text

    def _format_enum_value_def(self, node: Node) -> str:
        name = node.child_by_field_name("name")
        value = node.child_by_field_name("value")
        parts: list[str] = []
        if name is not None:
            parts.append(_node_text(source_bytes=self._source_bytes, node=name).strip())
        if value is not None:
            parts.append("=")
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=value).strip()
            )
        text = " ".join(p for p in parts if p)
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        return text

    def _emit_fn_def(self, node: Node) -> None:
        # Detect `async` by looking at the raw prefix (token isn't field-named).
        raw = _node_text(source_bytes=self._source_bytes, node=node).lstrip()
        is_async = raw.startswith("async")

        name = node.child_by_field_name("name")
        verb = node.child_by_field_name("verb")
        sig = node.child_by_field_name("sig")
        block = next((c for c in node.named_children if c.type == "block"), None)

        head_parts: list[str] = []
        if is_async:
            head_parts.append("async")
        head_parts.append("fn")
        if name is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=name).strip()
            )
        if verb is not None:
            head_parts.append(
                _node_text(source_bytes=self._source_bytes, node=verb).strip()
            )

        params, return_text, return_tuple_items = self._signature_parts(sig)
        signature = self._format_signature(params=params, return_text=return_text)

        if block is None:
            header = " ".join(head_parts) + " " + signature
            if self._fits_on_line(header):
                self._w.line(header)
            else:
                self._emit_wrapped_fn_signature(
                    prefix=" ".join(head_parts),
                    params=params,
                    return_text=return_text,
                    return_tuple_items=return_tuple_items,
                    has_block=False,
                )
            return

        header = " ".join(head_parts) + " " + signature + " {"
        if self._fits_on_line(header):
            self._w.line(header)
        else:
            self._emit_wrapped_fn_signature(
                prefix=" ".join(head_parts),
                params=params,
                return_text=return_text,
                return_tuple_items=return_tuple_items,
                has_block=True,
            )
        inner = self._format_block_inner(block)
        if inner:
            with self._w.indent():
                for line in inner:
                    self._w.line(line)
        self._w.line("}")

    def _signature_parts(
        self, node: Node | None
    ) -> tuple[list[str], str, list[str] | None]:
        if node is None:
            return [], "Any", None

        inputs = [c for c in node.named_children if c.type == "input_attr"]
        params = [self._format_input_attr(inp) for inp in inputs]

        return_clause = node.child_by_field_name("return_clause")
        if return_clause is None:
            return params, "Any", None

        return_tuple = next(
            (c for c in return_clause.named_children if c.type == "return_tuple"), None
        )
        if return_tuple is not None:
            outputs = [
                c for c in return_tuple.named_children if c.type == "output_attr"
            ]
            items = [self._format_output_attr(out) for out in outputs]
            return params, "(" + ", ".join(items) + ")", items

        return (
            params,
            _node_text(source_bytes=self._source_bytes, node=return_clause).strip(),
            None,
        )

    def _format_signature(self, *, params: list[str], return_text: str) -> str:
        return f"({', '.join(params)}) -> {return_text}"

    def _emit_wrapped_fn_signature(
        self,
        *,
        prefix: str,
        params: list[str],
        return_text: str,
        return_tuple_items: list[str] | None,
        has_block: bool,
    ) -> None:
        brace = " {" if has_block else ""

        if return_tuple_items is not None:
            inline_params = prefix + " (" + ", ".join(params) + ") -> ("
            if self._fits_on_line(inline_params):
                self._w.line(inline_params)
                with self._w.indent():
                    for idx, item in enumerate(return_tuple_items):
                        suffix = "," if idx + 1 < len(return_tuple_items) else ""
                        self._w.line(item + suffix)
                self._w.line(")" + brace)
                return

        self._w.line(prefix + " (")
        if params:
            with self._w.indent():
                for idx, p in enumerate(params):
                    suffix = "," if idx + 1 < len(params) else ""
                    self._w.line(p + suffix)

        if return_tuple_items is not None:
            inline_return = ") -> " + return_text + brace
            if self._fits_on_line(inline_return):
                self._w.line(inline_return)
                return
            self._w.line(") -> (")
            with self._w.indent():
                for idx, item in enumerate(return_tuple_items):
                    suffix = "," if idx + 1 < len(return_tuple_items) else ""
                    self._w.line(item + suffix)
            self._w.line(")" + brace)
            return

        inline_return = ") -> " + return_text + brace
        if self._fits_on_line(inline_return):
            self._w.line(inline_return)
            return

        self._w.line(") ->")
        with self._w.indent():
            self._w.line(return_text + brace)

    def _format_input_attr(self, node: Node) -> str:
        name = node.child_by_field_name("name")
        type_ref = node.child_by_field_name("type")
        identity_key = node.child_by_field_name("identity_key")
        default = node.child_by_field_name("default")

        parts: list[str] = []
        if name is not None:
            parts.append(_node_text(source_bytes=self._source_bytes, node=name).strip())
        if type_ref is not None:
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=type_ref).strip()
            )
        if identity_key is not None:
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=identity_key).strip()
            )
        if default is not None:
            parts.append("=")
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=default).strip()
            )
        return " ".join(p for p in parts if p)

    def _format_output_attr(self, node: Node) -> str:
        name = node.child_by_field_name("name")
        type_ref = node.child_by_field_name("type")
        parts: list[str] = []
        if name is not None:
            parts.append(_node_text(source_bytes=self._source_bytes, node=name).strip())
        if type_ref is not None:
            parts.append(
                _node_text(source_bytes=self._source_bytes, node=type_ref).strip()
            )
        return " ".join(p for p in parts if p)

    def _format_block_inner(self, block: Node) -> list[str]:
        raw = _node_text(source_bytes=self._source_bytes, node=block).strip()
        if raw.startswith("{") and raw.endswith("}"):
            inner = raw[1:-1]
        else:
            inner = raw

        lines = inner.splitlines()
        # Drop leading/trailing empty lines.
        while lines and not lines[0].strip():
            _ = lines.pop(0)
        while lines and not lines[-1].strip():
            _ = lines.pop()
        if not lines:
            return []

        # Dedent using minimal indentation of non-empty lines.
        indents: list[int] = []
        for line in lines:
            if not line.strip():
                continue
            indents.append(len(line) - len(line.lstrip(" \t")))
        min_indent = min(indents) if indents else 0

        out: list[str] = []
        for line in lines:
            if min_indent and len(line) >= min_indent:
                out.append(line[min_indent:].rstrip())
            else:
                out.append(line.rstrip())
        return out

    def _emit_ann_def(self, node: Node) -> None:
        path = node.child_by_field_name("path")
        verb = node.child_by_field_name("verb")
        args: list[str] = [
            _node_text(source_bytes=self._source_bytes, node=arg).strip()
            for arg in node.children_by_field_name("arg")
        ]

        parts: list[str] = ["ann"]
        if path is not None:
            parts.append(_node_text(source_bytes=self._source_bytes, node=path).strip())
        if verb is not None:
            parts.append(_node_text(source_bytes=self._source_bytes, node=verb).strip())
        parts.extend(args)

        text = " ".join(p for p in parts if p)
        if (
            _node_text(source_bytes=self._source_bytes, node=node)
            .rstrip()
            .endswith(";")
        ):
            text += ";"
        self._w.line(text)
