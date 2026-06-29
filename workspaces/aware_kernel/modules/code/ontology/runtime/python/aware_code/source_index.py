from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256

from aware_code.semantic_materialization import (
    SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND,
    SemanticSourceSessionCacheRef,
    SemanticSourceSessionContext,
)
from tree_sitter import Node, Parser, Tree
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


CODE_GRAMMAR_SOURCE_INDEX_CONTRACT_VERSION = (
    "aware.code.semantic-source-index.grammar.v1"
)
DEFAULT_AWARE_GRAMMAR_PROFILE_KEY = "code.grammar_profile.aware_kernel"
GRAMMAR_RULE_NODE_ANCHOR_FIELD_PATH = "__node__"
_AWARE_SCALAR_TYPE_NAMES = frozenset(
    {
        "Any",
        "Bool",
        "Boolean",
        "Bytes",
        "Date",
        "DateTime",
        "Float",
        "Int",
        "Json",
        "JsonArray",
        "JsonObject",
        "String",
        "Time",
        "Uuid",
    }
)


@dataclass(frozen=True, slots=True)
class CodeGrammarGraphSelector:
    provider_key: str | None = None
    semantic_owner: str | None = None
    subject_kind: str | None = None
    subject_type: str | None = None
    semantic_key: str | None = None
    object_key: str | None = None
    field_path: str | None = None
    field_name: str | None = None
    class_config_id: str | None = None
    class_fqn: str | None = None
    class_name: str | None = None
    class_config_attribute_config_id: str | None = None
    attribute_config_id: str | None = None
    attribute_name: str | None = None
    attribute_path: str | None = None

    @classmethod
    def from_object(cls, selector: object) -> "CodeGrammarGraphSelector":
        return cls(
            provider_key=_optional_string_attr(selector, "provider_key"),
            semantic_owner=_optional_string_attr(selector, "semantic_owner"),
            subject_kind=_optional_string_attr(selector, "subject_kind"),
            subject_type=_optional_string_attr(selector, "subject_type"),
            semantic_key=_optional_string_attr(selector, "semantic_key"),
            object_key=_optional_string_attr(selector, "object_key"),
            field_path=_optional_string_attr(selector, "field_path"),
            field_name=_optional_string_attr(selector, "field_name"),
            class_config_id=_optional_string_attr(selector, "class_config_id"),
            class_fqn=_optional_string_attr(selector, "class_fqn"),
            class_name=_optional_string_attr(selector, "class_name"),
            class_config_attribute_config_id=_optional_string_attr(
                selector,
                "class_config_attribute_config_id",
            ),
            attribute_config_id=_optional_string_attr(
                selector,
                "attribute_config_id",
            ),
            attribute_name=_optional_string_attr(selector, "attribute_name"),
            attribute_path=_optional_string_attr(selector, "attribute_path"),
        )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in (
            ("provider_key", self.provider_key),
            ("semantic_owner", self.semantic_owner),
            ("subject_kind", self.subject_kind),
            ("subject_type", self.subject_type),
            ("semantic_key", self.semantic_key),
            ("object_key", self.object_key),
            ("field_path", self.field_path),
            ("field_name", self.field_name),
            ("class_config_id", self.class_config_id),
            ("class_fqn", self.class_fqn),
            ("class_name", self.class_name),
            (
                "class_config_attribute_config_id",
                self.class_config_attribute_config_id,
            ),
            ("attribute_config_id", self.attribute_config_id),
            ("attribute_name", self.attribute_name),
            ("attribute_path", self.attribute_path),
        ):
            if value is not None:
                payload[key] = value
        return payload


@dataclass(frozen=True, slots=True)
class CodeGrammarAnchorQuery:
    binding_key: str
    language: str
    grammar_rule_name: str
    anchor_field_path: str
    graph_selector: CodeGrammarGraphSelector
    grammar_profile_key: str | None = None
    anchor_role: str | None = None
    value_domain: str | None = None
    direction: str | None = None


@dataclass(frozen=True, slots=True)
class CodeGrammarSource:
    source_key: str
    source_text: str
    language: str = "aware"
    grammar_profile_key: str | None = DEFAULT_AWARE_GRAMMAR_PROFILE_KEY
    relative_path: str | None = None


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceIndexSessionEvidence:
    cache_status: str = "request_local"
    source_session_id: str | None = None
    source_delta_fingerprint: str | None = None
    lifecycle_stages: tuple[str, ...] = ()
    cache_refs: tuple[SemanticSourceSessionCacheRef, ...] = ()

    @classmethod
    def from_context(
        cls,
        context: SemanticSourceSessionContext | None,
        *,
        cache_status: str | None = None,
    ) -> "CodeGrammarSourceIndexSessionEvidence":
        if context is None or not _has_session_context_evidence(context):
            return cls()
        cache_refs = tuple(
            cache_ref
            for cache_ref in (
                *context.cache_refs,
                *(
                    package_cache_ref
                    for package in context.packages
                    for package_cache_ref in package.cache_refs
                ),
            )
            if cache_ref.cache_kind == SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND
        )
        return cls(
            cache_status=(
                cache_status
                if cache_status is not None
                else ("session_candidate" if cache_refs else "request_local")
            ),
            source_session_id=context.source_session_id,
            source_delta_fingerprint=context.source_delta_fingerprint,
            lifecycle_stages=context.lifecycle_stages,
            cache_refs=cache_refs,
        )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "cache_status": self.cache_status,
            "cache_ref_count": len(self.cache_refs),
        }
        if self.source_session_id is not None:
            payload["source_session_id"] = self.source_session_id
        if self.source_delta_fingerprint is not None:
            payload["source_delta_fingerprint"] = self.source_delta_fingerprint
        if self.lifecycle_stages:
            payload["lifecycle_stages"] = self.lifecycle_stages
        if self.cache_refs:
            payload["cache_refs"] = tuple(
                cache_ref.evidence_payload() for cache_ref in self.cache_refs
            )
        return payload


@dataclass(frozen=True, slots=True)
class CodeGrammarAnchorResolution:
    binding_key: str
    source_key: str
    language: str
    grammar_profile_key: str | None
    grammar_rule_name: str
    anchor_field_path: str
    parser_node_kind: str
    anchor_node_kind: str
    byte_start: int
    byte_end: int
    text: str
    text_hash: str
    source_hash: str
    relative_path: str | None
    graph_selector: CodeGrammarGraphSelector
    template_values: Mapping[str, str] = field(default_factory=dict)
    session_evidence: CodeGrammarSourceIndexSessionEvidence = field(
        default_factory=CodeGrammarSourceIndexSessionEvidence
    )
    anchor_role: str | None = None
    value_domain: str | None = None
    direction: str | None = None

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source": "aware_code.source_index",
            "contract_version": CODE_GRAMMAR_SOURCE_INDEX_CONTRACT_VERSION,
            "source_key": self.source_key,
            "language": self.language,
            "grammar_rule_name": self.grammar_rule_name,
            "anchor_field_path": self.anchor_field_path,
            "parser_node_kind": self.parser_node_kind,
            "anchor_node_kind": self.anchor_node_kind,
            "byte_start": self.byte_start,
            "byte_end": self.byte_end,
            "text_hash": self.text_hash,
            "source_hash": self.source_hash,
            "graph_selector": self.graph_selector.evidence_payload(),
            "template_values": dict(self.template_values),
            "session": self.session_evidence.evidence_payload(),
        }
        if self.grammar_profile_key is not None:
            payload["grammar_profile_key"] = self.grammar_profile_key
        if self.relative_path is not None:
            payload["relative_path"] = self.relative_path
        if self.anchor_role is not None:
            payload["anchor_role"] = self.anchor_role
        if self.value_domain is not None:
            payload["value_domain"] = self.value_domain
        if self.direction is not None:
            payload["direction"] = self.direction
        return payload


@dataclass(slots=True)
class _CodeGrammarSourceRecord:
    source: CodeGrammarSource
    source_bytes: bytes
    source_hash: str
    tree: Tree
    _nodes_by_type: dict[str, tuple[Node, ...]] = field(default_factory=dict)

    def nodes_by_type(self, node_type: str) -> tuple[Node, ...]:
        cached = self._nodes_by_type.get(node_type)
        if cached is not None:
            return cached
        nodes = tuple(_nodes_by_type(self.tree.root_node, node_type))
        self._nodes_by_type[node_type] = nodes
        return nodes


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceIndexCacheKey:
    value: str


class CodeGrammarSourceIndexCache:
    """Small process-local cache for session-keyed grammar source indexes."""

    def __init__(self, *, max_entries: int = 32) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive.")
        self._max_entries = max_entries
        self._entries: OrderedDict[str, CodeGrammarSourceIndex] = OrderedDict()

    def get_or_build(
        self,
        *,
        sources: Iterable[CodeGrammarSource],
        session_context: SemanticSourceSessionContext | None,
        cache_keys: Iterable[str] = (),
    ) -> "CodeGrammarSourceIndex":
        sources_tuple = tuple(sources)
        explicit_cache_keys = tuple(
            cache_key_value.strip()
            for cache_key_value in cache_keys
            if cache_key_value.strip()
        )
        cache_key = code_grammar_source_index_cache_key(
            sources=sources_tuple,
            session_context=session_context,
        )
        source_cache_keys = (
            (cache_key.value,) if cache_key is not None else ()
        )
        session_cache_keys = (
            ()
            if explicit_cache_keys
            else semantic_source_index_cache_keys_from_context(session_context)
        )
        store_keys = tuple(
            dict.fromkeys(
                (
                    *source_cache_keys,
                    *session_cache_keys,
                    *explicit_cache_keys,
                )
            )
        )
        if not store_keys:
            return CodeGrammarSourceIndex.from_sources(
                sources_tuple,
                session_context=session_context,
            )
        for candidate_key in source_cache_keys:
            cached = self._entries.get(candidate_key)
            if cached is not None:
                self._entries.move_to_end(candidate_key)
                for alias_key in store_keys:
                    self._entries[alias_key] = cached
                    self._entries.move_to_end(alias_key)
                self._expire_oldest_entries()
                return cached.with_session_evidence(
                    CodeGrammarSourceIndexSessionEvidence.from_context(
                        session_context,
                        cache_status="process_cache_hit",
                    ),
                    parse_count=0,
                )
        source_index = CodeGrammarSourceIndex.from_sources(
            sources_tuple,
            session_context=session_context,
            cache_status="process_cache_miss",
        )
        for candidate_key in store_keys:
            self._entries[candidate_key] = source_index
            self._entries.move_to_end(candidate_key)
        self._expire_oldest_entries()
        return source_index

    def get_by_cache_key(
        self,
        *,
        cache_key: str,
        session_context: SemanticSourceSessionContext | None = None,
    ) -> "CodeGrammarSourceIndex | None":
        normalized_key = cache_key.strip()
        if not normalized_key:
            return None
        cached = self._entries.get(normalized_key)
        if cached is None:
            return None
        self._entries.move_to_end(normalized_key)
        return cached.with_session_evidence(
            CodeGrammarSourceIndexSessionEvidence.from_context(
                session_context,
                cache_status="process_cache_hit",
            ),
            parse_count=0,
        )

    def _expire_oldest_entries(self) -> None:
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def store(
        self,
        *,
        source_index: "CodeGrammarSourceIndex",
        cache_keys: Iterable[str],
    ) -> None:
        for cache_key in cache_keys:
            normalized_key = cache_key.strip()
            if not normalized_key:
                continue
            self._entries[normalized_key] = source_index
            self._entries.move_to_end(normalized_key)
        self._expire_oldest_entries()

    def contains_cache_key(self, cache_key: str) -> bool:
        return bool(cache_key.strip()) and cache_key.strip() in self._entries

    def get_or_build_from_context(
        self,
        *,
        sources: Iterable[CodeGrammarSource],
        session_context: SemanticSourceSessionContext | None,
    ) -> "CodeGrammarSourceIndex":
        return self.get_or_build(
            sources=sources,
            session_context=session_context,
        )

    def get_by_context_ref(
        self,
        *,
        session_context: SemanticSourceSessionContext | None,
    ) -> "CodeGrammarSourceIndex | None":
        for cache_key in semantic_source_index_cache_keys_from_context(
            session_context
        ):
            cached = self.get_by_cache_key(
                cache_key=cache_key,
                session_context=session_context,
            )
            if cached is not None:
                return cached
        return None

    def clear(self) -> None:
        self._entries.clear()


class CodeGrammarSourceIndex:
    """Code-owned index over grammar anchors, independent from section enums."""

    def __init__(
        self,
        *,
        records: dict[str, _CodeGrammarSourceRecord],
        parse_count: int,
        session_evidence: CodeGrammarSourceIndexSessionEvidence | None = None,
    ) -> None:
        self._records = dict(records)
        self._parse_count = parse_count
        self._session_evidence = (
            session_evidence or CodeGrammarSourceIndexSessionEvidence()
        )

    @property
    def parse_count(self) -> int:
        return self._parse_count

    @property
    def source_count(self) -> int:
        return len(self._records)

    @classmethod
    def from_sources(
        cls,
        sources: Iterable[CodeGrammarSource],
        session_context: SemanticSourceSessionContext | None = None,
        cache_status: str | None = None,
    ) -> "CodeGrammarSourceIndex":
        records: dict[str, _CodeGrammarSourceRecord] = {}
        parse_count = 0
        for source in sources:
            source_key = source.source_key.strip()
            if not source_key:
                continue
            if source_key in records:
                raise ValueError(f"Duplicate source_key: {source_key!r}")
            language = _normalized_language(source.language)
            if language != "aware":
                raise ValueError(
                    "CodeGrammarSourceIndex currently supports aware sources only."
                )
            source_bytes = source.source_text.encode("utf-8")
            tree = Parser(language=AWARE_LANGUAGE).parse(source_bytes)
            parse_count += 1
            records[source_key] = _CodeGrammarSourceRecord(
                source=CodeGrammarSource(
                    source_key=source_key,
                    source_text=source.source_text,
                    language=language,
                    grammar_profile_key=source.grammar_profile_key,
                    relative_path=source.relative_path,
                ),
                source_bytes=source_bytes,
                source_hash=_sha256_bytes(source_bytes),
                tree=tree,
            )
        return cls(
            records=records,
            parse_count=parse_count,
            session_evidence=CodeGrammarSourceIndexSessionEvidence.from_context(
                session_context,
                cache_status=cache_status,
            ),
        )

    def with_session_evidence(
        self,
        session_evidence: CodeGrammarSourceIndexSessionEvidence,
        *,
        parse_count: int | None = None,
    ) -> "CodeGrammarSourceIndex":
        return CodeGrammarSourceIndex(
            records=self._records,
            parse_count=self._parse_count if parse_count is None else parse_count,
            session_evidence=session_evidence,
        )

    def source_hash(self, source_key: str) -> str | None:
        record = self._records.get(source_key)
        if record is None:
            return None
        return record.source_hash

    def resolve_anchor(
        self,
        *,
        query: CodeGrammarAnchorQuery,
        source_key: str | None = None,
    ) -> CodeGrammarAnchorResolution | None:
        resolutions = self.resolve_anchors(query=query, source_key=source_key)
        return resolutions[0] if resolutions else None

    def resolve_anchors(
        self,
        *,
        query: CodeGrammarAnchorQuery,
        source_key: str | None = None,
    ) -> tuple[CodeGrammarAnchorResolution, ...]:
        source_records = (
            (self._records.get(source_key),)
            if source_key is not None
            else tuple(self._records.values())
        )
        resolutions: list[CodeGrammarAnchorResolution] = []
        for record in source_records:
            if record is None:
                continue
            if record.source.language != _normalized_language(query.language):
                continue
            resolutions.extend(
                _resolve_anchors_from_record(
                    record=record,
                    query=query,
                    session_evidence=self._session_evidence,
                )
            )
        return tuple(resolutions)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "source": "aware_code.source_index",
            "contract_version": CODE_GRAMMAR_SOURCE_INDEX_CONTRACT_VERSION,
            "source_count": self.source_count,
            "parse_count": self.parse_count,
            "source_keys": tuple(sorted(self._records)),
            "session": self._session_evidence.evidence_payload(),
        }


def code_grammar_source_index_cache_key(
    *,
    sources: Iterable[CodeGrammarSource],
    session_context: SemanticSourceSessionContext | None,
) -> CodeGrammarSourceIndexCacheKey | None:
    if session_context is None or not _has_session_context_evidence(session_context):
        return None
    source_parts = tuple(
        sorted(
            (
                source.source_key.strip(),
                _normalized_language(source.language),
                source.grammar_profile_key or "",
                _sha256_text(source.source_text),
            )
            for source in sources
            if source.source_key.strip()
        )
    )
    if not source_parts:
        return None
    key_payload = repr(
        (
            session_context.contract_version,
            session_context.source_session_id or "",
            session_context.source_delta_fingerprint or "",
            session_context.branch_key or "",
            session_context.session_key or "",
            source_parts,
        )
    )
    return CodeGrammarSourceIndexCacheKey(value=_sha256_text(key_payload))


def semantic_source_index_cache_keys_from_context(
    session_context: SemanticSourceSessionContext | None,
) -> tuple[str, ...]:
    if session_context is None:
        return ()
    return tuple(
        dict.fromkeys(
            cache_ref.cache_key.strip()
            for cache_ref in (
                *session_context.cache_refs,
                *(
                    package_cache_ref
                    for package in session_context.packages
                    for package_cache_ref in package.cache_refs
                ),
            )
            if (
                cache_ref.cache_kind == SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND
                and cache_ref.cache_key.strip()
            )
        )
    )


def _resolve_anchor_from_record(
    *,
    record: _CodeGrammarSourceRecord,
    query: CodeGrammarAnchorQuery,
    session_evidence: CodeGrammarSourceIndexSessionEvidence,
) -> CodeGrammarAnchorResolution | None:
    resolutions = _resolve_anchors_from_record(
        record=record,
        query=query,
        session_evidence=session_evidence,
    )
    return resolutions[0] if resolutions else None


def _resolve_anchors_from_record(
    *,
    record: _CodeGrammarSourceRecord,
    query: CodeGrammarAnchorQuery,
    session_evidence: CodeGrammarSourceIndexSessionEvidence,
) -> tuple[CodeGrammarAnchorResolution, ...]:
    resolutions: list[CodeGrammarAnchorResolution] = []
    for node in record.nodes_by_type(query.grammar_rule_name):
        if not _node_matches_graph_selector(
            node=node,
            query=query,
            source_bytes=record.source_bytes,
        ):
            continue
        anchor_node = _child_by_field_path(
            node,
            query.anchor_field_path,
            source_bytes=record.source_bytes,
        )
        if anchor_node is None:
            continue
        text = _anchor_text(
            node=node,
            anchor_node=anchor_node,
            query=query,
            source_bytes=record.source_bytes,
        )
        if text is None:
            continue
        byte_start, byte_end = _anchor_byte_span(
            node=node,
            anchor_node=anchor_node,
            query=query,
            source_bytes=record.source_bytes,
        )
        template_values = _template_values_for_node(
            node=node,
            query=query,
            source_bytes=record.source_bytes,
        )
        graph_selector = _resolved_graph_selector(
            selector=query.graph_selector,
            template_values=template_values,
        )
        resolutions.append(
            CodeGrammarAnchorResolution(
                binding_key=query.binding_key,
                source_key=record.source.source_key,
                language=record.source.language,
                grammar_profile_key=(
                    query.grammar_profile_key or record.source.grammar_profile_key
                ),
                grammar_rule_name=query.grammar_rule_name,
                anchor_field_path=query.anchor_field_path,
                parser_node_kind=node.type,
                anchor_node_kind=anchor_node.type,
                byte_start=byte_start,
                byte_end=byte_end,
                text=text,
                text_hash=_sha256_text(text),
                source_hash=record.source_hash,
                relative_path=record.source.relative_path,
                graph_selector=graph_selector,
                template_values=template_values,
                session_evidence=session_evidence,
                anchor_role=query.anchor_role,
                value_domain=query.value_domain,
                direction=query.direction,
            )
        )
    return tuple(resolutions)


def _template_values_for_node(
    *,
    node: Node,
    query: CodeGrammarAnchorQuery,
    source_bytes: bytes,
) -> dict[str, str]:
    values: dict[str, str] = {}
    if query.grammar_rule_name == "attr_def":
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            values["attribute_name"] = _node_text(
                source_bytes=source_bytes,
                node=name_node,
            )
        type_node = node.child_by_field_name("type")
        if type_node is not None:
            values["type"] = _node_text(
                source_bytes=source_bytes,
                node=type_node,
            )
        default_node = node.child_by_field_name("default")
        if default_node is not None:
            values["default_value"] = _node_text(
                source_bytes=source_bytes,
                node=default_node,
            )
        values["is_identity_key"] = (
            "true" if node.child_by_field_name("identity_key") is not None else "false"
        )
        class_node = _nearest_parent_by_type(node=node, node_type="class_def")
        if class_node is not None:
            class_name_node = class_node.child_by_field_name("name")
            if class_name_node is not None:
                values["class_name"] = _node_text(
                    source_bytes=source_bytes,
                    node=class_name_node,
                )
        values.update(
            _attr_relationship_values(
                node=node,
                class_name=values.get("class_name"),
                source_class_fqn=values.get("class_fqn"),
                relationship_key=values.get("attribute_name"),
                source_bytes=source_bytes,
            )
        )
    if query.grammar_rule_name == "fn_def":
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            values["function_name"] = _node_text(
                source_bytes=source_bytes,
                node=name_node,
            )
        verb_node = node.child_by_field_name("verb")
        if verb_node is not None:
            function_verb = _node_text(source_bytes=source_bytes, node=verb_node)
            values["function_verb"] = function_verb
            values["verb"] = function_verb
        class_node = _nearest_parent_by_type(node=node, node_type="class_def")
        if class_node is not None:
            class_name_node = class_node.child_by_field_name("name")
            if class_name_node is not None:
                values["class_name"] = _node_text(
                    source_bytes=source_bytes,
                    node=class_name_node,
                )
        description = _function_description(node=node, source_bytes=source_bytes)
        if description is not None:
            values["function_description"] = description
    if query.grammar_rule_name == "class_def":
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            values["class_name"] = _node_text(
                source_bytes=source_bytes,
                node=name_node,
            )
        description = _class_description(node=node, source_bytes=source_bytes)
        if description is not None:
            values["class_description"] = description
    if query.grammar_rule_name == "enum_def":
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            values["enum_name"] = _node_text(
                source_bytes=source_bytes,
                node=name_node,
            )
        description = _enum_description(node=node, source_bytes=source_bytes)
        if description is not None:
            values["enum_description"] = description
    if query.grammar_rule_name == "enum_value_def":
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            values["enum_option_value"] = _node_text(
                source_bytes=source_bytes,
                node=name_node,
            )
            values["value"] = values["enum_option_value"]
        value_node = node.child_by_field_name("value")
        if value_node is not None:
            values["enum_option_literal"] = _node_text(
                source_bytes=source_bytes,
                node=value_node,
            )
        enum_node = _nearest_parent_by_type(node=node, node_type="enum_def")
        if enum_node is not None:
            enum_name_node = enum_node.child_by_field_name("name")
            if enum_name_node is not None:
                values["enum_name"] = _node_text(
                    source_bytes=source_bytes,
                    node=enum_name_node,
                )
            position = _enum_value_position(node=node, enum_node=enum_node)
            if position is not None:
                values["position"] = str(position)
    if query.grammar_rule_name == "ann_def":
        path_node = node.child_by_field_name("path")
        if path_node is not None:
            ann_path = _node_text(source_bytes=source_bytes, node=path_node)
            values["ann_path"] = ann_path
            class_fqn, member_path = _ann_path_parts(ann_path)
            if class_fqn:
                values["class_fqn"] = class_fqn
                values["class_name"] = class_fqn.rsplit(".", maxsplit=1)[-1]
            if member_path:
                values["member_path"] = member_path
                values["attribute_name"] = member_path.rsplit(".", maxsplit=1)[-1]
                values["relationship_key"] = values["attribute_name"]
                values.update(
                    _ann_relationship_attribute_values(
                        node=node,
                        class_name=values.get("class_name"),
                        source_class_fqn=values.get("class_fqn"),
                        relationship_key=values["relationship_key"],
                        source_bytes=source_bytes,
                    )
                )
        verb_node = node.child_by_field_name("verb")
        if verb_node is not None:
            values["ann_verb"] = _node_text(source_bytes=source_bytes, node=verb_node)
        args_text = _ann_args_text(node=node, source_bytes=source_bytes)
        if args_text is not None:
            values["ann_args"] = args_text
            values["load_policy_args"] = args_text
    if "class_name" in values and "attribute_name" in values:
        values["attribute_path"] = (
            f"{values['class_name']}.{values['attribute_name']}."
            f"{query.anchor_field_path}"
        )
        values.setdefault("field_name", values["attribute_name"])
        values.setdefault("field_path", values["attribute_path"])
    if (
        query.grammar_rule_name == "ann_def"
        and "class_name" in values
        and "relationship_key" in values
    ):
        values["relationship_path"] = (
            f"{values['class_name']}.{values['relationship_key']}"
        )
        values.setdefault("field_name", values["relationship_key"])
        values.setdefault("field_path", values["relationship_path"])
    if "class_name" in values and "function_name" in values:
        values["function_path"] = f"{values['class_name']}.{values['function_name']}"
        values.setdefault("field_name", values["function_name"])
        values.setdefault("field_path", values["function_path"])
    if query.grammar_rule_name == "class_def" and "class_name" in values:
        values.setdefault("field_name", "description")
        values.setdefault("field_path", f"{values['class_name']}.description")
    if query.grammar_rule_name == "enum_def" and "enum_name" in values:
        values["enum_path"] = values["enum_name"]
        values.setdefault("field_name", "description")
        values.setdefault("field_path", f"{values['enum_name']}.description")
    if (
        query.grammar_rule_name == "enum_value_def"
        and "enum_name" in values
        and "enum_option_value" in values
    ):
        values["enum_option_path"] = (
            f"{values['enum_name']}.{values['enum_option_value']}"
        )
        values.setdefault("field_name", values["enum_option_value"])
        values.setdefault("field_path", values["enum_option_path"])
    return values


def _resolved_graph_selector(
    *,
    selector: CodeGrammarGraphSelector,
    template_values: Mapping[str, str],
) -> CodeGrammarGraphSelector:
    field_name = selector.field_name or template_values.get("field_name")
    field_path = selector.field_path or template_values.get("field_path")
    class_name = selector.class_name or template_values.get("class_name")
    attribute_name = selector.attribute_name or template_values.get("attribute_name")
    attribute_path = selector.attribute_path or template_values.get("attribute_path")
    if field_name is None:
        field_name = attribute_name
    if field_path is None:
        field_path = attribute_path or template_values.get("function_path")
    return CodeGrammarGraphSelector(
        provider_key=selector.provider_key,
        semantic_owner=selector.semantic_owner,
        subject_kind=selector.subject_kind,
        subject_type=selector.subject_type,
        semantic_key=selector.semantic_key,
        object_key=selector.object_key,
        field_path=field_path,
        field_name=field_name,
        class_config_id=selector.class_config_id,
        class_fqn=selector.class_fqn,
        class_name=class_name,
        class_config_attribute_config_id=(selector.class_config_attribute_config_id),
        attribute_config_id=selector.attribute_config_id,
        attribute_name=attribute_name,
        attribute_path=attribute_path,
    )


def _node_matches_graph_selector(
    *,
    node: Node,
    query: CodeGrammarAnchorQuery,
    source_bytes: bytes,
) -> bool:
    if query.grammar_rule_name not in {
        "attr_def",
        "fn_def",
        "class_def",
        "enum_def",
    }:
        return True
    if query.grammar_rule_name == "enum_def":
        enum_names = _selector_enum_names(query.graph_selector)
        if enum_names:
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return False
            if _node_text(source_bytes=source_bytes, node=name_node) not in enum_names:
                return False
        return True
    if query.grammar_rule_name == "attr_def":
        attribute_names = _selector_attribute_names(query.graph_selector)
    else:
        attribute_names = set()
    if attribute_names:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return False
        if _node_text(source_bytes=source_bytes, node=name_node) not in attribute_names:
            return False
    class_names = _selector_class_names(query.graph_selector)
    if class_names:
        class_node = (
            node
            if query.grammar_rule_name == "class_def"
            else _nearest_parent_by_type(node=node, node_type="class_def")
        )
        if class_node is None:
            return False
        class_name_node = class_node.child_by_field_name("name")
        if class_name_node is None:
            return False
        if (
            _node_text(source_bytes=source_bytes, node=class_name_node)
            not in class_names
        ):
            return False
    return True


def _selector_attribute_names(selector: CodeGrammarGraphSelector) -> set[str]:
    names: set[str] = set()
    if selector.field_name is not None and selector.field_name.strip():
        names.add(selector.field_name.strip())
    if selector.field_path is not None and selector.field_path.strip():
        parts = [part for part in selector.field_path.split(".") if part]
        if len(parts) >= 2:
            names.add(parts[-2].strip())
    if selector.attribute_name is not None and selector.attribute_name.strip():
        names.add(selector.attribute_name.strip())
    if selector.attribute_path is not None and selector.attribute_path.strip():
        parts = [part for part in selector.attribute_path.split(".") if part]
        if len(parts) >= 2:
            names.add(parts[-2].strip())
    return names


def _selector_class_names(selector: CodeGrammarGraphSelector) -> set[str]:
    names: set[str] = set()
    if selector.class_name is not None and selector.class_name.strip():
        names.add(selector.class_name.strip())
    if selector.class_fqn is not None and selector.class_fqn.strip():
        names.add(selector.class_fqn.rsplit(".", maxsplit=1)[-1].strip())
    return names


def _selector_enum_names(selector: CodeGrammarGraphSelector) -> set[str]:
    names: set[str] = set()
    for value in (
        selector.object_key,
        selector.field_name,
        selector.field_path,
        selector.semantic_key,
    ):
        if value is None or not value.strip():
            continue
        names.update(_enum_name_candidates(value.strip()))
    return names


def _enum_name_candidates(value: str) -> set[str]:
    candidates: set[str] = {value}
    if "." in value:
        candidates.add(value.rsplit(".", maxsplit=1)[-1])
    if "/" in value:
        tail = value.rsplit("/", maxsplit=1)[-1]
        if ":" in tail:
            candidates.add(tail.split(":", maxsplit=1)[-1])
        candidates.add(tail)
    if ":" in value:
        candidates.add(value.rsplit(":", maxsplit=1)[-1])
    first_path_part = value.split(".", maxsplit=1)[0]
    if first_path_part:
        candidates.add(first_path_part)
    return {candidate for candidate in candidates if candidate}


def _nodes_by_type(root_node: Node, node_type: str) -> Iterable[Node]:
    if root_node.type == node_type:
        yield root_node
    for child in root_node.named_children:
        yield from _nodes_by_type(child, node_type)


def _child_by_field_path(
    node: Node,
    field_path: str,
    *,
    source_bytes: bytes | None = None,
) -> Node | None:
    current: Node | None = node
    for field_name in field_path.split("."):
        normalized = field_name.strip()
        if not normalized:
            return None
        if current is None:
            return None
        if normalized == GRAMMAR_RULE_NODE_ANCHOR_FIELD_PATH:
            return current
        if (
            normalized == "description_comment"
            and current.type in {"class_def", "enum_def"}
            and source_bytes is not None
        ):
            nodes = _description_comment_nodes_for_node(
                node=current,
                source_bytes=source_bytes,
            )
            return nodes[0] if nodes else None
        if normalized == "args" and current.type == "ann_def":
            nodes = _ann_arg_nodes(node=current)
            return nodes[0] if nodes else None
        current = current.child_by_field_name(normalized)
    return current


def _anchor_text(
    *,
    node: Node,
    anchor_node: Node,
    query: CodeGrammarAnchorQuery,
    source_bytes: bytes,
) -> str | None:
    if query.grammar_rule_name == "class_def" and (
        query.anchor_field_path == "description_comment"
    ):
        return _class_description(node=node, source_bytes=source_bytes)
    if query.grammar_rule_name == "enum_def" and (
        query.anchor_field_path == "description_comment"
    ):
        return _enum_description(node=node, source_bytes=source_bytes)
    if query.grammar_rule_name == "ann_def" and query.anchor_field_path == "args":
        return _ann_args_text(node=node, source_bytes=source_bytes)
    return _node_text(source_bytes=source_bytes, node=anchor_node)


def _anchor_byte_span(
    *,
    node: Node,
    anchor_node: Node,
    query: CodeGrammarAnchorQuery,
    source_bytes: bytes,
) -> tuple[int, int]:
    if query.grammar_rule_name == "class_def" and (
        query.anchor_field_path == "description_comment"
    ):
        nodes = _description_comment_nodes_for_node(
            node=node,
            source_bytes=source_bytes,
        )
        if nodes:
            return nodes[0].start_byte, nodes[-1].end_byte
    if query.grammar_rule_name == "enum_def" and (
        query.anchor_field_path == "description_comment"
    ):
        nodes = _description_comment_nodes_for_node(
            node=node,
            source_bytes=source_bytes,
        )
        if nodes:
            return nodes[0].start_byte, nodes[-1].end_byte
    if query.grammar_rule_name == "ann_def" and query.anchor_field_path == "args":
        nodes = _ann_arg_nodes(node=node)
        if nodes:
            return nodes[0].start_byte, nodes[-1].end_byte
    return anchor_node.start_byte, anchor_node.end_byte


def _nearest_parent_by_type(*, node: Node, node_type: str) -> Node | None:
    current = node.parent
    while current is not None:
        if current.type == node_type:
            return current
        current = current.parent
    return None


def _enum_value_position(*, node: Node, enum_node: Node) -> int | None:
    position = 0
    for child in enum_node.named_children:
        if child.type != "enum_value_def":
            continue
        if child.start_byte == node.start_byte and child.end_byte == node.end_byte:
            return position
        position += 1
    return None


def _function_description(*, node: Node, source_bytes: bytes) -> str | None:
    block_node = _first_named_child_by_type(node=node, node_type="block")
    if block_node is None:
        return None
    comment_node = _first_descendant_by_type(node=block_node, node_type="comment")
    if comment_node is not None:
        return _normalize_doc_comment(
            _node_text(source_bytes=source_bytes, node=comment_node)
        )
    return _triple_quoted_doc_comment(
        _node_text(source_bytes=source_bytes, node=block_node)
    )


def _class_description(*, node: Node, source_bytes: bytes) -> str | None:
    nodes = _description_comment_nodes_for_node(
        node=node,
        source_bytes=source_bytes,
    )
    if not nodes:
        return None
    text = "\n".join(_node_text(source_bytes=source_bytes, node=item) for item in nodes)
    return _normalize_doc_comment(text)


def _enum_description(*, node: Node, source_bytes: bytes) -> str | None:
    nodes = _description_comment_nodes_for_node(
        node=node,
        source_bytes=source_bytes,
    )
    if not nodes:
        return None
    text = "\n".join(_node_text(source_bytes=source_bytes, node=item) for item in nodes)
    return _normalize_doc_comment(text)


def _description_comment_nodes_for_node(
    *,
    node: Node,
    source_bytes: bytes,
) -> tuple[Node, ...]:
    nodes: list[Node] = []
    current = node.prev_named_sibling
    while current is not None and current.type == "comment":
        text = _node_text(source_bytes=source_bytes, node=current)
        if not _is_doc_comment_text(text):
            break
        nodes.append(current)
        current = current.prev_named_sibling
    return tuple(reversed(nodes))


def _ann_arg_nodes(*, node: Node) -> tuple[Node, ...]:
    return tuple(node.children_by_field_name("arg"))


def _ann_args_text(*, node: Node, source_bytes: bytes) -> str | None:
    nodes = _ann_arg_nodes(node=node)
    if not nodes:
        return None
    text = " ".join(_node_text(source_bytes=source_bytes, node=item) for item in nodes)
    return text.strip() or None


def _ann_path_parts(value: str) -> tuple[str, str | None]:
    class_fqn, separator, member_path = value.partition("::")
    class_fqn = class_fqn.strip()
    member_path = member_path.strip() if separator else ""
    return class_fqn, member_path or None


def _ann_relationship_attribute_values(
    *,
    node: Node,
    class_name: str | None,
    source_class_fqn: str | None,
    relationship_key: str,
    source_bytes: bytes,
) -> dict[str, str]:
    if class_name is None:
        return {}
    class_node = _class_def_for_name(
        root_node=_root_node(node=node),
        class_name=class_name,
        source_bytes=source_bytes,
    )
    if class_node is None:
        return {}
    attr_node = _attr_def_for_name(
        class_node=class_node,
        attribute_name=relationship_key,
        source_bytes=source_bytes,
    )
    if attr_node is None:
        return {}
    type_node = attr_node.child_by_field_name("type")
    if type_node is None:
        return {}
    type_text = _node_text(source_bytes=source_bytes, node=type_node)
    target_class_name = _target_class_name_from_type_text(type_text)
    if target_class_name is None:
        return {}
    values = {
        "target_class_name": target_class_name,
        "target_class_fqn": _target_class_fqn(
            source_class_fqn=source_class_fqn or class_name,
            target_class_name=target_class_name,
        ),
        "relationship_type": _relationship_type_from_type_text(type_text),
    }
    return {key: value for key, value in values.items() if value}


def _attr_relationship_values(
    *,
    node: Node,
    class_name: str | None,
    source_class_fqn: str | None,
    relationship_key: str | None,
    source_bytes: bytes,
) -> dict[str, str]:
    if class_name is None or relationship_key is None:
        return {}
    type_node = node.child_by_field_name("type")
    if type_node is None:
        return {}
    type_text = _node_text(source_bytes=source_bytes, node=type_node)
    target_class_name = _target_class_name_from_type_text(type_text)
    if target_class_name is None:
        return {}
    values = {
        "relationship_key": relationship_key,
        "relationship_path": f"{class_name}.{relationship_key}",
        "target_class_name": target_class_name,
        "target_class_fqn": _target_class_fqn(
            source_class_fqn=source_class_fqn or class_name,
            target_class_name=target_class_name,
        ),
        "relationship_type": _relationship_type_from_type_text(type_text),
    }
    return {key: value for key, value in values.items() if value}


def _root_node(*, node: Node) -> Node:
    current = node
    while current.parent is not None:
        current = current.parent
    return current


def _class_def_for_name(
    *,
    root_node: Node,
    class_name: str,
    source_bytes: bytes,
) -> Node | None:
    for candidate in _nodes_by_type(root_node, "class_def"):
        name_node = candidate.child_by_field_name("name")
        if name_node is None:
            continue
        if _node_text(source_bytes=source_bytes, node=name_node) == class_name:
            return candidate
    return None


def _attr_def_for_name(
    *,
    class_node: Node,
    attribute_name: str,
    source_bytes: bytes,
) -> Node | None:
    for candidate in _nodes_by_type(class_node, "attr_def"):
        name_node = candidate.child_by_field_name("name")
        if name_node is None:
            continue
        if _node_text(source_bytes=source_bytes, node=name_node) == attribute_name:
            return candidate
    return None


def _target_class_name_from_type_text(value: str) -> str | None:
    type_text = _base_type_text(value)
    if not type_text:
        return None
    if type_text in _AWARE_SCALAR_TYPE_NAMES:
        return None
    if type_text[0].isupper():
        return type_text.rsplit(".", maxsplit=1)[-1]
    return None


def _target_class_fqn(*, source_class_fqn: str, target_class_name: str) -> str:
    if "." not in source_class_fqn:
        return target_class_name
    namespace = source_class_fqn.rsplit(".", maxsplit=1)[0]
    return f"{namespace}.{target_class_name}"


def _relationship_type_from_type_text(value: str) -> str:
    return "one_to_many" if _is_collection_type_text(value) else "many_to_one"


def _base_type_text(value: str) -> str:
    text = value.strip().removesuffix("?").strip()
    if text.endswith("[]"):
        return text[:-2].strip().removesuffix("?").strip()
    return text


def _is_collection_type_text(value: str) -> bool:
    text = value.strip()
    return text.endswith("[]")


def _is_doc_comment_text(value: str) -> bool:
    text = value.lstrip()
    return text.startswith("///") or text.startswith('"""')


def _first_named_child_by_type(*, node: Node, node_type: str) -> Node | None:
    for child in node.named_children:
        if child.type == node_type:
            return child
    return None


def _first_descendant_by_type(*, node: Node, node_type: str) -> Node | None:
    if node.type == node_type:
        return node
    for child in node.named_children:
        found = _first_descendant_by_type(node=child, node_type=node_type)
        if found is not None:
            return found
    return None


def _normalize_doc_comment(value: str) -> str | None:
    text = value.strip()
    if text.startswith('"""') and text.endswith('"""') and len(text) >= 6:
        text = text[3:-3]
    lines = tuple(_normalize_doc_comment_line(line) for line in text.splitlines())
    normalized = "\n".join(line for line in lines if line).strip()
    return normalized or None


def _normalize_doc_comment_line(value: str) -> str:
    line = value.strip()
    if line.startswith("///"):
        line = line[3:]
    elif line.startswith("//"):
        line = line[2:]
    return line.strip()


def _triple_quoted_doc_comment(value: str) -> str | None:
    start = value.find('"""')
    if start < 0:
        return None
    end = value.find('"""', start + 3)
    if end < 0:
        return None
    return _normalize_doc_comment(value[start : end + 3])


def _node_text(*, source_bytes: bytes, node: Node) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _optional_string_attr(value: object, attribute_name: str) -> str | None:
    raw_value = getattr(value, attribute_name, None)
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    return text or None


def _has_session_context_evidence(context: SemanticSourceSessionContext) -> bool:
    return any(
        (
            context.source_session_id is not None,
            context.source_delta_fingerprint is not None,
            bool(context.lifecycle_stages),
            bool(context.packages),
            bool(context.cache_refs),
        )
    )


def _normalized_language(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value).strip()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


__all__ = [
    "CODE_GRAMMAR_SOURCE_INDEX_CONTRACT_VERSION",
    "DEFAULT_AWARE_GRAMMAR_PROFILE_KEY",
    "CodeGrammarAnchorQuery",
    "CodeGrammarAnchorResolution",
    "CodeGrammarGraphSelector",
    "CodeGrammarSource",
    "CodeGrammarSourceIndex",
    "CodeGrammarSourceIndexCache",
    "CodeGrammarSourceIndexCacheKey",
    "CodeGrammarSourceIndexSessionEvidence",
    "code_grammar_source_index_cache_key",
    "semantic_source_index_cache_keys_from_context",
]
