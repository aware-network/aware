from __future__ import annotations

from tree_sitter import Node

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language_service.programs import intrinsic_signature, parse_tree
from aware_code.language_service.text import iter_identifier_tokens_in_range

from .collector import SemanticTokenCollector


def _is_ident_byte(value: int | None) -> bool:
    if value is None:
        return False
    return (ord("A") <= value <= ord("Z")) or (ord("a") <= value <= ord("z")) or value == ord("_") or (
        ord("0") <= value <= ord("9")
    )


def _find_keyword_span_in_node(*, document_bytes: bytes, node: Node, keyword: str) -> tuple[int, int] | None:
    keyword_bytes = keyword.encode("utf-8")
    if not keyword_bytes:
        return None

    scan_start = node.start_byte
    while True:
        found_at = document_bytes.find(keyword_bytes, scan_start, node.end_byte)
        if found_at == -1:
            return None

        before = document_bytes[found_at - 1] if found_at > 0 else None
        after_index = found_at + len(keyword_bytes)
        after = document_bytes[after_index] if after_index < len(document_bytes) else None

        if not _is_ident_byte(before) and not _is_ident_byte(after):
            return found_at, after_index

        scan_start = found_at + 1


def _add_keyword_literal_in_node(
    *,
    collector: SemanticTokenCollector,
    node: Node,
    keyword: str,
    modifier_names: tuple[str, ...] = (),
) -> None:
    keyword_span = _find_keyword_span_in_node(document_bytes=collector.document_bytes, node=node, keyword=keyword)
    if keyword_span is None:
        return
    collector.add_token(
        byte_start=keyword_span[0],
        byte_end=keyword_span[1],
        token_type_name="keyword",
        modifier_names=modifier_names,
    )


def _has_aware_markers(*, document_bytes: bytes) -> bool:
    return any(
        marker in document_bytes
        for marker in (
            b"graph",
            b"projection",
            b"api",
            b"service",
            b"operation",
            b"endpoint",
            b"pane",
            b"interface",
            b"window",
            b"layout",
            b"section",
            b"mount",
            b"narrative",
            b"contract",
            b"program",
            b"experience",
            b"environment",
            b"event",
            b"action",
            b"role",
            b"actor",
            b"port",
            b"bind",
            b"call",
            b"intent",
            b"expect",
            b"input",
        )
    )


def _add_graph_ref_tokens(
    *,
    collector: SemanticTokenCollector,
    ref_node: Node | None,
) -> None:
    if ref_node is None:
        return
    if ref_node.end_byte <= ref_node.start_byte:
        return
    raw = collector.document_bytes[ref_node.start_byte:ref_node.end_byte].decode("utf-8", errors="replace")
    dot_index = raw.find(".")
    if dot_index <= 0 or dot_index >= len(raw) - 1:
        collector.add_token(
            byte_start=ref_node.start_byte,
            byte_end=ref_node.end_byte,
            token_type_name="parameter",
            modifier_names=("experience",),
        )
        return
    node_start = ref_node.start_byte
    node_end = ref_node.start_byte + dot_index
    identity_start = node_end + 1
    identity_end = ref_node.end_byte
    collector.add_token(
        byte_start=node_start,
        byte_end=node_end,
        token_type_name="parameter",
        modifier_names=("experience",),
    )
    collector.add_token(
        byte_start=identity_start,
        byte_end=identity_end,
        token_type_name="property",
        modifier_names=("experience",),
    )


def _add_api_anchor_tokens(
    *,
    collector: SemanticTokenCollector,
    anchor_node: Node | None,
) -> None:
    if anchor_node is None:
        return
    parent_node = anchor_node.child_by_field_name("parent")
    relationship_node = anchor_node.child_by_field_name("relationship")
    key_node = anchor_node.child_by_field_name("key")
    if parent_node is not None:
        collector.add_type_span(
            byte_start=parent_node.start_byte,
            byte_end=parent_node.end_byte,
            modifier_names=("api",),
        )
    if relationship_node is not None:
        collector.add_token(
            byte_start=relationship_node.start_byte,
            byte_end=relationship_node.end_byte,
            token_type_name="property",
            modifier_names=("api",),
        )
    if key_node is not None:
        collector.add_token(
            byte_start=key_node.start_byte,
            byte_end=key_node.end_byte,
            token_type_name="property",
            modifier_names=("api",),
        )


def _add_api_anchor_text_tokens(
    *,
    collector: SemanticTokenCollector,
    byte_start: int,
    byte_end: int,
) -> None:
    if byte_end <= byte_start:
        return
    raw = collector.document_bytes[byte_start:byte_end].decode("utf-8", errors="replace").strip()
    if not raw:
        return

    parts = [part.strip() for part in raw.split("::")]
    if not parts:
        return

    type_part = parts[0]
    if type_part:
        type_end = byte_start + len(type_part)
        collector.add_type_span(
            byte_start=byte_start,
            byte_end=type_end,
            modifier_names=("api",),
        )

    if len(parts) >= 2:
        relationship_start = byte_start + len(type_part) + len("::")
        relationship_end = relationship_start + len(parts[1])
        collector.add_token(
            byte_start=relationship_start,
            byte_end=relationship_end,
            token_type_name="property",
            modifier_names=("api",),
        )

    if len(parts) >= 3:
        key_start = byte_start + len(type_part) + len("::") + len(parts[1]) + len("::")
        key_end = key_start + len(parts[2])
        collector.add_token(
            byte_start=key_start,
            byte_end=key_end,
            token_type_name="property",
            modifier_names=("api",),
        )


def _add_api_contract_recovery_tokens(
    *,
    collector: SemanticTokenCollector,
    api_node: Node,
) -> None:
    document_bytes = collector.document_bytes
    start = api_node.start_byte
    end = api_node.end_byte
    line_start = start

    while line_start < end:
        line_end = document_bytes.find(b"\n", line_start, end)
        if line_end == -1:
            line_end = end

        raw_line = document_bytes[line_start:line_end]
        stripped = raw_line.lstrip(b" \t")
        if stripped.startswith(b"contract "):
            indent = len(raw_line) - len(stripped)
            contract_start = line_start + indent
            keyword_end = contract_start + len("contract")
            collector.add_token(
                byte_start=contract_start,
                byte_end=keyword_end,
                token_type_name="keyword",
                modifier_names=("api",),
            )

            cursor = keyword_end
            while cursor < line_end and document_bytes[cursor:cursor + 1] in {b" ", b"\t"}:
                cursor += 1

            class_start = cursor
            while cursor < line_end and document_bytes[cursor:cursor + 1] not in {b" ", b"\t", b";"}:
                cursor += 1
            if cursor > class_start:
                collector.add_type_span(
                    byte_start=class_start,
                    byte_end=cursor,
                    modifier_names=("api",),
                )

            while cursor < line_end and document_bytes[cursor:cursor + 1] in {b" ", b"\t"}:
                cursor += 1

            anchor_start = cursor
            anchor_end = document_bytes.find(b";", anchor_start, line_end)
            if anchor_end == -1:
                anchor_end = line_end
            if anchor_end > anchor_start:
                _add_api_anchor_text_tokens(
                    collector=collector,
                    byte_start=anchor_start,
                    byte_end=anchor_end,
                )

        line_start = line_end + 1


def _add_qualified_reference_tokens(
    *,
    collector: SemanticTokenCollector,
    ref_node: Node | None,
    leading_token_type_name: str = "type",
    trailing_token_type_name: str = "type",
    modifier_names: tuple[str, ...] = (),
) -> None:
    if ref_node is None or ref_node.end_byte <= ref_node.start_byte:
        return

    target_tokens = list(
        iter_identifier_tokens_in_range(
            document_bytes=collector.document_bytes,
            segment_start=ref_node.start_byte,
            segment_end=ref_node.end_byte,
        )
    )
    if not target_tokens:
        return

    if len(target_tokens) == 1:
        _token_text, _token_bytes, token_range = target_tokens[0]
        collector.add_token(
            byte_start=token_range.start,
            byte_end=token_range.end,
            token_type_name=trailing_token_type_name,
            modifier_names=modifier_names,
        )
        return

    for _token_text, _token_bytes, token_range in target_tokens[:-1]:
        collector.add_token(
            byte_start=token_range.start,
            byte_end=token_range.end,
            token_type_name=leading_token_type_name,
            modifier_names=modifier_names,
        )
    _last_text, _last_bytes, last_range = target_tokens[-1]
    collector.add_token(
        byte_start=last_range.start,
        byte_end=last_range.end,
        token_type_name=trailing_token_type_name,
        modifier_names=modifier_names,
    )


def collect_aware_contextual_tokens(*, collector: SemanticTokenCollector) -> None:
    collect_aware_contextual_tokens_for_owner_groups(collector=collector, enabled_owner_groups=None)


def collect_aware_contextual_tokens_for_owner_groups(
    *,
    collector: SemanticTokenCollector,
    enabled_owner_groups: frozenset[str] | None,
) -> None:
    if collector.context.workspace_language != CodeLanguage.aware:
        return

    document_bytes = collector.document_bytes
    if not _has_aware_markers(document_bytes=document_bytes):
        return

    def _is_enabled(owner_group: str) -> bool:
        return enabled_owner_groups is None or owner_group in enabled_owner_groups

    aware_root = parse_tree(document_bytes=document_bytes)
    stack = [aware_root]

    while stack:
        node = stack.pop()
        node_type = node.type

        if _is_enabled("meta_projection") and node_type == "projection_def":
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="projection",
                modifier_names=("projection",),
            )
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="class",
                    modifier_names=("projection",),
                )

        elif _is_enabled("meta_projection") and node_type == "projection_root":
            type_node = node.child_by_field_name("type")
            if type_node is not None:
                collector.add_type_span(
                    byte_start=type_node.start_byte,
                    byte_end=type_node.end_byte,
                    modifier_names=("projection",),
                )

        elif _is_enabled("meta_projection") and node_type == "projection_edge":
            type_node = node.child_by_field_name("type")
            member_node = node.child_by_field_name("member")
            target_node = node.child_by_field_name("target")
            if type_node is not None:
                collector.add_type_span(
                    byte_start=type_node.start_byte,
                    byte_end=type_node.end_byte,
                    modifier_names=("projection",),
                )
            if member_node is not None:
                collector.add_token(
                    byte_start=member_node.start_byte,
                    byte_end=member_node.end_byte,
                    token_type_name="property",
                    modifier_names=("projection",),
                )
            if target_node is not None and target_node.type != "string_literal":
                collector.add_token(
                    byte_start=target_node.start_byte,
                    byte_end=target_node.end_byte,
                    token_type_name="type",
                    modifier_names=("projection",),
                )

        elif _is_enabled("meta_projection") and node_type == "projection_view_group":
            prefix_node = node.child_by_field_name("prefix")
            if prefix_node is not None:
                collector.add_token(
                    byte_start=prefix_node.start_byte,
                    byte_end=prefix_node.end_byte,
                    token_type_name="property",
                    modifier_names=("projection",),
                )

        elif _is_enabled("meta_projection") and node_type == "projection_view_def":
            view_key_node = node.child_by_field_name("view_key")
            if view_key_node is not None:
                collector.add_token(
                    byte_start=view_key_node.start_byte,
                    byte_end=view_key_node.end_byte,
                    token_type_name="property",
                    modifier_names=("projection",),
                )

        elif _is_enabled("experience_projection") and node_type == "experience_def":
            name_node = node.child_by_field_name("name")
            projection_node = node.child_by_field_name("projection")
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="class",
                    modifier_names=("experience",),
                )
            if projection_node is not None:
                collector.add_type_span(
                    byte_start=projection_node.start_byte,
                    byte_end=projection_node.end_byte,
                    modifier_names=("experience",),
                )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="on",
                modifier_names=("experience",),
            )

        elif _is_enabled("experience_projection") and node_type == "experience_observable_group":
            observable_node = node.child_by_field_name("observable")
            if observable_node is not None:
                collector.add_token(
                    byte_start=observable_node.start_byte,
                    byte_end=observable_node.end_byte,
                    token_type_name="property",
                    modifier_names=("experience",),
                )

        elif _is_enabled("experience_projection") and node_type == "experience_view_def":
            view_key_node = node.child_by_field_name("view_key")
            if view_key_node is not None:
                collector.add_token(
                    byte_start=view_key_node.start_byte,
                    byte_end=view_key_node.end_byte,
                    token_type_name="property",
                    modifier_names=("experience",),
                )

        elif _is_enabled("experience_projection") and node_type == "experience_node_def":
            name_node = node.child_by_field_name("name")
            node_ref = node.child_by_field_name("node_ref")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="node",
                modifier_names=("experience",),
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="parameter",
                    modifier_names=("experience",),
                )
            if node_ref is not None:
                collector.add_token(
                    byte_start=node_ref.start_byte,
                    byte_end=node_ref.end_byte,
                    token_type_name="property",
                    modifier_names=("experience",),
                )

        elif _is_enabled("experience_projection") and node_type == "experience_node_identity_def":
            key_name = node.child_by_field_name("key_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="id",
                modifier_names=("experience", "identity"),
            )
            if key_name is not None:
                collector.add_token(
                    byte_start=key_name.start_byte,
                    byte_end=key_name.end_byte,
                    token_type_name="property",
                    modifier_names=("experience", "identity"),
                )

        elif _is_enabled("experience_projection") and node_type == "experience_node_param":
            name_node = node.child_by_field_name("name")
            type_node = node.child_by_field_name("type")
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="parameter",
                    modifier_names=("experience",),
                )
            if type_node is not None:
                collector.add_type_span(
                    byte_start=type_node.start_byte,
                    byte_end=type_node.end_byte,
                    modifier_names=("experience",),
                )

        elif _is_enabled("experience_graph") and node_type == "graph_def":
            name_node = node.child_by_field_name("name")
            experience_node = node.child_by_field_name("experience")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="graph",
                modifier_names=("experience",),
            )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="on",
                modifier_names=("experience",),
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="class",
                    modifier_names=("experience",),
                )
            if experience_node is not None:
                collector.add_token(
                    byte_start=experience_node.start_byte,
                    byte_end=experience_node.end_byte,
                    token_type_name="class",
                    modifier_names=("experience",),
                )

        elif _is_enabled("experience_graph") and node_type == "graph_root_stmt":
            ref_node = node.child_by_field_name("ref")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="root",
                modifier_names=("experience",),
            )
            _add_graph_ref_tokens(collector=collector, ref_node=ref_node)

        elif _is_enabled("experience_graph") and node_type == "graph_edge_stmt":
            parent_node = node.child_by_field_name("parent")
            child_node = node.child_by_field_name("child")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="node",
                modifier_names=("experience",),
            )
            _add_graph_ref_tokens(collector=collector, ref_node=parent_node)
            _add_graph_ref_tokens(collector=collector, ref_node=child_node)

        elif node_type == "api_def":
            name_node = node.child_by_field_name("name")
            if _is_enabled("api_api"):
                _add_keyword_literal_in_node(
                    collector=collector,
                    node=node,
                    keyword="api",
                    modifier_names=("api",),
                )
                if name_node is not None:
                    collector.add_token(
                        byte_start=name_node.start_byte,
                        byte_end=name_node.end_byte,
                        token_type_name="class",
                        modifier_names=("api",),
                    )
            if _is_enabled("api_projection"):
                _add_api_contract_recovery_tokens(collector=collector, api_node=node)

        elif _is_enabled("api_capability") and node_type == "api_capability_def":
            capability_name_node = node.child_by_field_name("capability_name")
            class_node = node.child_by_field_name("class")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="capability",
                modifier_names=("api",),
            )
            if capability_name_node is not None:
                collector.add_token(
                    byte_start=capability_name_node.start_byte,
                    byte_end=capability_name_node.end_byte,
                    token_type_name="class",
                    modifier_names=("api",),
                )
            if class_node is not None:
                collector.add_type_span(
                    byte_start=class_node.start_byte,
                    byte_end=class_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("api_capability") and node_type == "api_capability_endpoint_def":
            endpoint_name = node.child_by_field_name("endpoint_name")
            request_node = node.child_by_field_name("request")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="endpoint",
                modifier_names=("api",),
            )
            if endpoint_name is not None:
                collector.add_token(
                    byte_start=endpoint_name.start_byte,
                    byte_end=endpoint_name.end_byte,
                    token_type_name="function",
                    modifier_names=("api",),
                )
            if request_node is not None:
                collector.add_type_span(
                    byte_start=request_node.start_byte,
                    byte_end=request_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("api_capability") and node_type == "api_capability_endpoint_response_def":
            response_node = node.child_by_field_name("response")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="response",
                modifier_names=("api",),
            )
            if response_node is not None:
                collector.add_type_span(
                    byte_start=response_node.start_byte,
                    byte_end=response_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("api_capability") and node_type == "api_capability_endpoint_stream_def":
            stream_mode = node.child_by_field_name("stream_mode")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="stream",
                modifier_names=("api",),
            )
            if stream_mode is not None:
                collector.add_token(
                    byte_start=stream_mode.start_byte,
                    byte_end=stream_mode.end_byte,
                    token_type_name="enumMember",
                    modifier_names=("api",),
                )

        elif _is_enabled("api_capability") and node_type == "api_capability_endpoint_stream_event_def":
            kind_node = node.child_by_field_name("kind")
            class_node = node.child_by_field_name("class")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="event",
                modifier_names=("api",),
            )
            if kind_node is not None:
                collector.add_token(
                    byte_start=kind_node.start_byte,
                    byte_end=kind_node.end_byte,
                    token_type_name="enumMember",
                    modifier_names=("api",),
                )
            if class_node is not None:
                collector.add_type_span(
                    byte_start=class_node.start_byte,
                    byte_end=class_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("api_graph") and node_type == "api_graph_def":
            graph_node = node.child_by_field_name("graph")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="graph",
                modifier_names=("api",),
            )
            if graph_node is not None:
                collector.add_type_span(
                    byte_start=graph_node.start_byte,
                    byte_end=graph_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("api_projection") and node_type == "api_graph_projection_def":
            projection_node = node.child_by_field_name("projection")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="projection",
                modifier_names=("api",),
            )
            if projection_node is not None:
                collector.add_type_span(
                    byte_start=projection_node.start_byte,
                    byte_end=projection_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("api_projection") and node_type == "api_graph_projection_contract_def":
            class_node = node.child_by_field_name("class")
            anchor_node = node.child_by_field_name("anchor")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="contract",
                modifier_names=("api",),
            )
            if class_node is not None:
                collector.add_type_span(
                    byte_start=class_node.start_byte,
                    byte_end=class_node.end_byte,
                    modifier_names=("api",),
                )
            _add_api_anchor_tokens(collector=collector, anchor_node=anchor_node)

        elif _is_enabled("api_graph") and node_type == "api_graph_capability_def":
            capability_name_node = node.child_by_field_name("capability_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="capability",
                modifier_names=("api",),
            )
            if capability_name_node is not None:
                collector.add_token(
                    byte_start=capability_name_node.start_byte,
                    byte_end=capability_name_node.end_byte,
                    token_type_name="class",
                    modifier_names=("api",),
                )

        elif _is_enabled("api_graph") and node_type == "api_graph_capability_function_def":
            name_node = node.child_by_field_name("name")
            target_node = node.child_by_field_name("target")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="function",
                modifier_names=("api",),
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="function",
                    modifier_names=("api",),
                )
            if target_node is not None:
                collector.add_type_span(
                    byte_start=target_node.start_byte,
                    byte_end=target_node.end_byte,
                    modifier_names=("api",),
                )

        elif _is_enabled("service_service") and node_type == "service_def":
            name_node = node.child_by_field_name("name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="service",
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="class",
                )

        elif _is_enabled("service_api") and node_type == "service_api_decl":
            api_ref_node = node.child_by_field_name("api")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="api",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=api_ref_node,
            )

        elif _is_enabled("service_experience") and node_type == "service_experience_decl":
            experience_ref_node = node.child_by_field_name("experience")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="experience",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=experience_ref_node,
            )

        elif _is_enabled("service_projection") and node_type == "service_api_projection_decl":
            projection_ref_node = node.child_by_field_name("projection")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="projection",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=projection_ref_node,
            )

        elif _is_enabled("service_operation") and node_type == "service_operation_def":
            operation_name_node = node.child_by_field_name("operation_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="operation",
            )
            if operation_name_node is not None:
                collector.add_token(
                    byte_start=operation_name_node.start_byte,
                    byte_end=operation_name_node.end_byte,
                    token_type_name="function",
                )

        elif _is_enabled("service_endpoint") and node_type == "service_operation_endpoint_def":
            endpoint_ref_node = node.child_by_field_name("endpoint")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="endpoint",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=endpoint_ref_node,
                trailing_token_type_name="function",
            )

        elif _is_enabled("interface_pane") and node_type == "pane_def":
            name_node = node.child_by_field_name("name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="pane",
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="class",
                )

        elif _is_enabled("interface_pane") and node_type == "pane_kind_decl":
            kind_node = node.child_by_field_name("kind")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="kind",
            )
            if kind_node is not None:
                collector.add_token(
                    byte_start=kind_node.start_byte,
                    byte_end=kind_node.end_byte,
                    token_type_name="enumMember",
                )

        elif _is_enabled("interface_view") and node_type == "pane_view_def":
            view_ref_node = node.child_by_field_name("view")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="view",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=view_ref_node,
                trailing_token_type_name="property",
            )

        elif _is_enabled("interface_endpoint") and node_type == "pane_endpoint_def":
            endpoint_ref_node = node.child_by_field_name("endpoint")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="endpoint",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=endpoint_ref_node,
                trailing_token_type_name="function",
            )

        elif _is_enabled("interface_interface") and node_type == "interface_def":
            name_node = node.child_by_field_name("name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="interface",
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="namespace",
                )

        elif _is_enabled("interface_api") and node_type == "interface_api_decl":
            api_ref_node = node.child_by_field_name("api")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="api",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=api_ref_node,
            )

        elif _is_enabled("interface_window") and node_type == "interface_window_def":
            window_name_node = node.child_by_field_name("window_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="window",
            )
            if window_name_node is not None:
                collector.add_token(
                    byte_start=window_name_node.start_byte,
                    byte_end=window_name_node.end_byte,
                    token_type_name="namespace",
                )

        elif _is_enabled("interface_layout") and node_type == "interface_layout_def":
            layout_name_node = node.child_by_field_name("layout_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="layout",
            )
            if layout_name_node is not None:
                collector.add_token(
                    byte_start=layout_name_node.start_byte,
                    byte_end=layout_name_node.end_byte,
                    token_type_name="class",
                )

        elif _is_enabled("interface_section") and node_type == "interface_layout_section_def":
            section_name_node = node.child_by_field_name("section_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="section",
            )
            if section_name_node is not None:
                collector.add_token(
                    byte_start=section_name_node.start_byte,
                    byte_end=section_name_node.end_byte,
                    token_type_name="property",
                )

        elif _is_enabled("interface_pane_composition") and node_type == "interface_pane_def":
            pane_name_node = node.child_by_field_name("pane_name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="pane",
            )
            if pane_name_node is not None:
                collector.add_token(
                    byte_start=pane_name_node.start_byte,
                    byte_end=pane_name_node.end_byte,
                    token_type_name="class",
                )

        elif _is_enabled("interface_mount") and node_type == "interface_pane_mount_def":
            view_ref_node = node.child_by_field_name("view")
            target_node = node.child_by_field_name("target")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="mount",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=view_ref_node,
                trailing_token_type_name="property",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=target_node,
                leading_token_type_name="property",
                trailing_token_type_name="property",
            )

        elif _is_enabled("interface_narrative") and node_type == "interface_pane_narrative_def":
            narrative_node = node.child_by_field_name("narrative")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="narrative",
            )
            _add_qualified_reference_tokens(
                collector=collector,
                ref_node=narrative_node,
                trailing_token_type_name="property",
            )

        elif _is_enabled("experience_event") and node_type == "event_def":
            name_node = node.child_by_field_name("name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="event",
                modifier_names=("event",),
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="class",
                    modifier_names=("event",),
                )

        elif _is_enabled("experience_event") and node_type == "event_binding":
            projection_node = node.child_by_field_name("projection")
            type_node = node.child_by_field_name("type")
            operation_node = node.child_by_field_name("operation")
            attribute_node = node.child_by_field_name("attribute")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="bind",
                modifier_names=("event",),
            )
            if projection_node is not None:
                collector.add_type_span(
                    byte_start=projection_node.start_byte,
                    byte_end=projection_node.end_byte,
                    modifier_names=("event",),
                )
            if type_node is not None:
                collector.add_type_span(
                    byte_start=type_node.start_byte,
                    byte_end=type_node.end_byte,
                    modifier_names=("event",),
                )
            if operation_node is not None:
                collector.add_token(
                    byte_start=operation_node.start_byte,
                    byte_end=operation_node.end_byte,
                    token_type_name="keyword",
                    modifier_names=("event",),
                )
            if attribute_node is not None:
                collector.add_token(
                    byte_start=attribute_node.start_byte,
                    byte_end=attribute_node.end_byte,
                    token_type_name="property",
                    modifier_names=("event",),
                )

        elif _is_enabled("experience_role") and node_type == "role_def":
            role_name = node.child_by_field_name("name")
            if role_name is not None:
                collector.add_token(
                    byte_start=role_name.start_byte,
                    byte_end=role_name.end_byte,
                    token_type_name="class",
                    modifier_names=("role",),
                )

        elif _is_enabled("experience_role") and node_type == "role_capability_stmt":
            target_node = node.child_by_field_name("target")
            if target_node is not None:
                target_tokens = list(
                    iter_identifier_tokens_in_range(
                        document_bytes=document_bytes,
                        segment_start=target_node.start_byte,
                        segment_end=target_node.end_byte,
                    )
                )
                if target_tokens:
                    for _token_str, _token_bytes, token_range in target_tokens[:-1]:
                        collector.add_token(
                            byte_start=token_range.start,
                            byte_end=token_range.end,
                            token_type_name="type",
                            modifier_names=("role",),
                        )
                    _last_text, _last_bytes, last_range = target_tokens[-1]
                    collector.add_token(
                        byte_start=last_range.start,
                        byte_end=last_range.end,
                        token_type_name="function",
                        modifier_names=("role",),
                    )

        elif _is_enabled("experience_action") and node_type == "action_def":
            name_node = node.child_by_field_name("name")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="action",
                modifier_names=("action",),
            )
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="function",
                    modifier_names=("action",),
                )

        elif _is_enabled("experience_action") and node_type == "action_program_stmt":
            program_node = node.child_by_field_name("program")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="program",
                modifier_names=("action",),
            )
            if program_node is not None:
                collector.add_type_span(
                    byte_start=program_node.start_byte,
                    byte_end=program_node.end_byte,
                    modifier_names=("action",),
                )

        elif _is_enabled("experience_program") and node_type == "program_def":
            name_node = node.child_by_field_name("name")
            impl_node = node.child_by_field_name("impl")
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="function",
                    modifier_names=("program",),
                )
            if impl_node is not None:
                collector.add_type_span(
                    byte_start=impl_node.start_byte,
                    byte_end=impl_node.end_byte,
                    modifier_names=("program",),
                )

        elif _is_enabled("experience_program") and node_type == "actor_decl_stmt":
            actor_alias = node.child_by_field_name("name")
            actor_ref = node.child_by_field_name("actor")
            if actor_alias is not None:
                collector.add_token(
                    byte_start=actor_alias.start_byte,
                    byte_end=actor_alias.end_byte,
                    token_type_name="parameter",
                    modifier_names=("program", "actor"),
                )
            if actor_ref is not None:
                collector.add_type_span(
                    byte_start=actor_ref.start_byte,
                    byte_end=actor_ref.end_byte,
                    modifier_names=("program", "actor"),
                )

        elif _is_enabled("experience_program") and node_type == "port_decl_stmt":
            port_name = node.child_by_field_name("name")
            port_ref = node.child_by_field_name("ref")
            if port_name is not None:
                collector.add_token(
                    byte_start=port_name.start_byte,
                    byte_end=port_name.end_byte,
                    token_type_name="parameter",
                    modifier_names=("program", "portNode"),
                )
            if port_ref is not None:
                collector.add_type_span(
                    byte_start=port_ref.start_byte,
                    byte_end=port_ref.end_byte,
                    modifier_names=("program",),
                )

        elif _is_enabled("experience_program") and node_type == "port_decl_node_stmt":
            node_name = node.child_by_field_name("name")
            node_ref = node.child_by_field_name("ref")
            if node_name is not None:
                collector.add_token(
                    byte_start=node_name.start_byte,
                    byte_end=node_name.end_byte,
                    token_type_name="parameter",
                    modifier_names=("program", "portNode"),
                )
            if node_ref is not None:
                collector.add_type_span(
                    byte_start=node_ref.start_byte,
                    byte_end=node_ref.end_byte,
                    modifier_names=("program", "portNode"),
                )

        elif _is_enabled("experience_program") and node_type == "bind_stmt":
            port_node = node.child_by_field_name("port")
            view_node = node.child_by_field_name("view")
            if port_node is not None:
                collector.add_token(
                    byte_start=port_node.start_byte,
                    byte_end=port_node.end_byte,
                    token_type_name="parameter",
                    modifier_names=("program", "portNode"),
                )
            if view_node is not None:
                collector.add_token(
                    byte_start=view_node.start_byte,
                    byte_end=view_node.end_byte,
                    token_type_name="property",
                    modifier_names=("program",),
                )

        elif _is_enabled("experience_program") and node_type == "call_stmt":
            actor_node = node.child_by_field_name("actor")
            object_node = node.child_by_field_name("object")
            if actor_node is not None:
                collector.add_token(
                    byte_start=actor_node.start_byte,
                    byte_end=actor_node.end_byte,
                    token_type_name="parameter",
                    modifier_names=("program", "actor"),
                )
            if object_node is not None:
                collector.add_token(
                    byte_start=object_node.start_byte,
                    byte_end=object_node.end_byte,
                    token_type_name="parameter",
                    modifier_names=("program", "portNode"),
                )

        elif _is_enabled("experience_program") and node_type == "program_call":
            target_node = node.child_by_field_name("target")
            if target_node is not None:
                target_text = document_bytes[target_node.start_byte:target_node.end_byte].decode(
                    "utf-8",
                    errors="replace",
                )
                modifier_names: tuple[str, ...] = ("program",)
                if intrinsic_signature(target_text.strip()) is not None:
                    modifier_names = ("program", "intrinsic")

                target_tokens = list(
                    iter_identifier_tokens_in_range(
                        document_bytes=document_bytes,
                        segment_start=target_node.start_byte,
                        segment_end=target_node.end_byte,
                    )
                )
                if target_tokens:
                    for _token_str, _token_bytes, token_range in target_tokens[:-1]:
                        collector.add_token(
                            byte_start=token_range.start,
                            byte_end=token_range.end,
                            token_type_name="type",
                            modifier_names=modifier_names,
                        )
                    _last_text, _last_bytes, last_range = target_tokens[-1]
                    collector.add_token(
                        byte_start=last_range.start,
                        byte_end=last_range.end,
                        token_type_name="function",
                        modifier_names=modifier_names,
                    )

        elif _is_enabled("experience_program") and node_type == "input_stmt":
            source_node = node.child_by_field_name("source")
            default_node = node.child_by_field_name("default")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="input",
                modifier_names=("program",),
            )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="from",
                modifier_names=("program",),
            )
            if default_node is not None:
                _add_keyword_literal_in_node(
                    collector=collector,
                    node=node,
                    keyword="default",
                    modifier_names=("program",),
                )
            if source_node is not None:
                collector.add_type_span(
                    byte_start=source_node.start_byte,
                    byte_end=source_node.end_byte,
                    modifier_names=("program",),
                )

        elif _is_enabled("experience_program") and node_type == "expect_stmt":
            ref_node = node.child_by_field_name("ref")
            requirement_node = node.child_by_field_name("requirement")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="expect",
                modifier_names=("program",),
            )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="event_config",
                modifier_names=("program",),
            )
            if requirement_node is not None:
                collector.add_token(
                    byte_start=requirement_node.start_byte,
                    byte_end=requirement_node.end_byte,
                    token_type_name="keyword",
                    modifier_names=("program",),
                )
            if ref_node is not None:
                collector.add_type_span(
                    byte_start=ref_node.start_byte,
                    byte_end=ref_node.end_byte,
                    modifier_names=("program",),
                )

        elif _is_enabled("experience_program") and node_type == "intent_stmt":
            action_ref = node.child_by_field_name("action_ref")
            event_ref = node.child_by_field_name("event_ref")
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="intent",
                modifier_names=("program",),
            )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="action_config",
                modifier_names=("program",),
            )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="on",
                modifier_names=("program",),
            )
            _add_keyword_literal_in_node(
                collector=collector,
                node=node,
                keyword="event_config",
                modifier_names=("program",),
            )
            if action_ref is not None:
                collector.add_type_span(
                    byte_start=action_ref.start_byte,
                    byte_end=action_ref.end_byte,
                    modifier_names=("program",),
                )
            if event_ref is not None:
                collector.add_type_span(
                    byte_start=event_ref.start_byte,
                    byte_end=event_ref.end_byte,
                    modifier_names=("program",),
                )

        elif _is_enabled("experience_environment") and node_type == "environment_def":
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                collector.add_token(
                    byte_start=name_node.start_byte,
                    byte_end=name_node.end_byte,
                    token_type_name="namespace",
                    modifier_names=("environment",),
                )

        elif _is_enabled("experience_actor") and node_type == "environment_actor_stmt":
            actor_ref = node.child_by_field_name("actor")
            if actor_ref is not None:
                collector.add_type_span(
                    byte_start=actor_ref.start_byte,
                    byte_end=actor_ref.end_byte,
                    modifier_names=("actor",),
                )

        elif _is_enabled("experience_actor") and node_type == "environment_actor_role_stmt":
            role_ref = node.child_by_field_name("role")
            if role_ref is not None:
                collector.add_type_span(
                    byte_start=role_ref.start_byte,
                    byte_end=role_ref.end_byte,
                    modifier_names=("actor", "role"),
                )

        elif _is_enabled("experience_environment") and node_type == "environment_experience_stmt":
            experience_ref = node.child_by_field_name("experience")
            if experience_ref is not None:
                collector.add_type_span(
                    byte_start=experience_ref.start_byte,
                    byte_end=experience_ref.end_byte,
                    modifier_names=("environment", "experience"),
                )

        elif _is_enabled("experience_environment") and node_type == "environment_program_stmt":
            program_config = node.child_by_field_name("program_config")
            program_impl = node.child_by_field_name("program_impl")
            if program_config is not None:
                collector.add_type_span(
                    byte_start=program_config.start_byte,
                    byte_end=program_config.end_byte,
                    modifier_names=("environment", "program"),
                )
            if program_impl is not None:
                collector.add_type_span(
                    byte_start=program_impl.start_byte,
                    byte_end=program_impl.end_byte,
                    modifier_names=("environment", "program"),
                )

        elif _is_enabled("experience_environment") and node_type == "environment_event_stmt":
            event_ref = node.child_by_field_name("event")
            if event_ref is not None:
                collector.add_type_span(
                    byte_start=event_ref.start_byte,
                    byte_end=event_ref.end_byte,
                    modifier_names=("environment",),
                )

        elif _is_enabled("experience_environment") and node_type == "environment_event_action_stmt":
            action_ref = node.child_by_field_name("action")
            if action_ref is not None:
                collector.add_type_span(
                    byte_start=action_ref.start_byte,
                    byte_end=action_ref.end_byte,
                    modifier_names=("environment",),
                )

        elif _is_enabled("experience_actor") and node_type == "actor_def":
            actor_name = node.child_by_field_name("name")
            actor_kind = node.child_by_field_name("kind")
            if actor_name is not None:
                collector.add_token(
                    byte_start=actor_name.start_byte,
                    byte_end=actor_name.end_byte,
                    token_type_name="class",
                    modifier_names=("actor",),
                )
            if actor_kind is not None:
                collector.add_type_span(
                    byte_start=actor_kind.start_byte,
                    byte_end=actor_kind.end_byte,
                    modifier_names=("actor",),
                )

        elif _is_enabled("experience_actor") and node_type == "actor_role_stmt":
            role_ref = node.child_by_field_name("role")
            if role_ref is not None:
                collector.add_type_span(
                    byte_start=role_ref.start_byte,
                    byte_end=role_ref.end_byte,
                    modifier_names=("actor", "role"),
                )

        elif _is_enabled("meta_identity") and node_type in {"attr_def", "input_attr"}:
            identity_key = node.child_by_field_name("identity_key")
            if identity_key is not None:
                collector.add_token(
                    byte_start=identity_key.start_byte,
                    byte_end=identity_key.end_byte,
                    token_type_name="keyword",
                )

        stack.extend(reversed(list(node.named_children)))
