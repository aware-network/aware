from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from typing_extensions import override

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig

from aware_code.language.registry import CodeLanguagePluginRegistry

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.annotation.compiler import parse_discriminate_args

from aware_code.language_service.features.annotation_relationships import (
    collect_structural_relationship_keys,
)
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.completion_capabilities.contracts import (
    CompletionItemAdder,
    CompletionItemDict,
    CompletionResultDict,
)
from aware_code.language_service.features.completion_capabilities.environment import (
    collect_environment_context_completion_items,
)
from aware_code.language_service.features.completion_capabilities.executor import (
    collect_context_completion_items,
)
from aware_code.language_service.features.completion_capabilities.experience import (
    collect_experience_context_completion_items,
)
from aware_code.language_service.features.completion_capabilities.role_actor import (
    collect_role_actor_context_completion_items,
)
from aware_code.language_service.features.segments import SegmentMixin
from aware_code.language_service.document import DocumentContext
from aware_code.language_service.position import Utf16Position
from aware_code.language_service.programs import (
    find_program_call_target_at,
    intrinsic_signature,
    intrinsic_targets_by_prefix,
    parse_tree,
    resolve_owner_to_class,
)
from aware_code.language_service.text import (
    extract_identifier_prefix,
    parse_annotation_statement_tokens,
)

from aware_workspace.compiler.workspace import WorkspaceSnapshot


class CompletionMixin(ServiceMixinBase, SegmentMixin):
    _snapshot: WorkspaceSnapshot | None

    @override
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        raise NotImplementedError

    @override
    def _rebuild_full(self, *, focus_uri: str | None = None, reason: str = "change") -> None:
        raise NotImplementedError

    @override
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        raise NotImplementedError

    def _program_call_target_completion_items(self, *, prefix: str) -> list[CompletionItemDict]:
        if self._snapshot is None:
            return []

        raw = (prefix or "").strip()
        items: list[CompletionItemDict] = []
        seen: set[tuple[str, int | None]] = set()

        def _add(label: str, *, kind: int | None = None, detail: str | None = None) -> None:
            key = (label, kind)
            if key in seen:
                return
            seen.add(key)
            payload: CompletionItemDict = {"label": label}
            if kind is not None:
                payload["kind"] = kind
            if detail:
                payload["detail"] = detail
            items.append(payload)

        namespaces = ("plan", "meta", "reactivity")

        # First segment: offer reserved intrinsic namespaces.
        if "." not in raw:
            for ns in namespaces:
                if raw and not ns.startswith(raw):
                    continue
                _add(ns, kind=9, detail="intrinsic namespace")
            return items

        base, partial = raw.rsplit(".", 1)
        if base in namespaces:
            prefix0 = f"{base}."
            for full in intrinsic_targets_by_prefix(prefix0):
                if not full.startswith(prefix0):
                    continue
                name = full[len(prefix0):]
                if partial and not name.startswith(partial):
                    continue
                sig = intrinsic_signature(full)
                _add(
                    name,
                    kind=3,  # Function
                    detail=sig.render() if sig is not None else full,
                )
            return items

        # Owner-resolved call targets: offer methods when the owner resolves unambiguously.
        res = resolve_owner_to_class(owner=base, classes_by_fqn=self._snapshot.fqn_resolver.classes_by_fqn)
        if res.status != "ok" or res.class_cfg is None:
            return items
        cls = res.class_cfg.code_section_class
        if cls is None:
            return items
        for fn in cls.code_section_functions:
            if not getattr(fn, "is_public", False):
                continue
            name = fn.name.strip()
            if not name:
                continue
            if partial and not name.startswith(partial):
                continue
            detail = f"{res.fqn}::{name}" if res.fqn else None
            _add(name, kind=2, detail=detail)  # Method
        return items

    def _experience_context_completion_items(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[CompletionItemDict] | None:
        return collect_experience_context_completion_items(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
        )

    def _environment_context_completion_items(
        self, *, byte_offset: int, document_bytes: bytes
    ) -> list[CompletionItemDict] | None:
        return collect_environment_context_completion_items(
            byte_offset=byte_offset,
            document_bytes=document_bytes,
        )

    def _role_actor_context_completion_items(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[CompletionItemDict] | None:
        return collect_role_actor_context_completion_items(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
        )

    def completion(self, *, uri: str, position: Utf16Position, document_text: str) -> CompletionResultDict:
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return {"isIncomplete": False, "items": []}
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return {"isIncomplete": False, "items": []}

        ctx = self._document_context(uri=uri, document_text=document_text)
        offset = ctx.mapper.position_to_byte_offset(position)
        doc_bytes = ctx.document_bytes

        context_items = collect_context_completion_items(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
        )
        if context_items is not None:
            return {"isIncomplete": False, "items": context_items}

        seg = self._find_completion_segment_at(uri=uri, byte_offset=offset, document_bytes=doc_bytes)
        if seg is None:
            # Program call targets are not tracked as code-sections; detect them via tree-sitter.
            if not doc_bytes or b"program" not in doc_bytes:
                return {"isIncomplete": False, "items": []}
            try:
                root = parse_tree(document_bytes=doc_bytes)
                call_at = find_program_call_target_at(root=root, byte_offset=offset)
                if call_at is None and offset > 0:
                    call_at = find_program_call_target_at(root=root, byte_offset=offset - 1)
            except Exception:
                call_at = None
            if call_at is None:
                return {"isIncomplete": False, "items": []}

            allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
            prefix = extract_identifier_prefix(
                document_bytes=doc_bytes,
                byte_offset=offset,
                segment_start=call_at.target_range.start,
                segment_end=max(call_at.target_range.end, offset),
                allowed=allowed,
            )
            items = self._program_call_target_completion_items(prefix=prefix)
            return {"isIncomplete": False, "items": items}

        if seg.kind == "annotation_args":
            return {
                "isIncomplete": False,
                "items": self._annotation_args_completion_items(uri=uri, byte_offset=offset, document_bytes=doc_bytes),
            }

        if seg.kind == "default_value":
            return {
                "isIncomplete": False,
                "items": self._default_value_completion_items(
                    uri=uri,
                    byte_offset=offset,
                    document_bytes=doc_bytes,
                    segment_start=seg.range.start,
                    segment_end=seg.range.end,
                ),
            }

        allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
        if seg.kind == "annotation_path":
            allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:"
        if seg.kind == "import_alias":
            allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

        prefix = extract_identifier_prefix(
            document_bytes=doc_bytes,
            byte_offset=offset,
            segment_start=seg.range.start,
            segment_end=seg.range.end,
            allowed=allowed,
        )

        if seg.kind == "annotation_path" and "::" in prefix:
            items = self._annotation_path_completion_items(uri=uri, prefix=prefix)
            return {"isIncomplete": False, "items": items}

        items = self._completion_items_for_prefix(uri=uri, prefix=prefix, mode=seg.kind)
        return {"isIncomplete": False, "items": items}

    def _default_value_completion_items(
        self,
        *,
        uri: str,
        byte_offset: int,
        document_bytes: bytes,
        segment_start: int,
        segment_end: int,
    ) -> list[CompletionItemDict]:
        """Complete default values (`= ...`) for attributes and parameters."""
        if self._snapshot is None:
            return []
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return []

        attr = self._find_attribute_with_default_at(uri=uri, byte_offset=byte_offset)
        if attr is None or not isinstance(attr.type_text, str) or not attr.type_text.strip():
            return []

        try:
            plugin = CodeLanguagePluginRegistry.get(self._workspace.language)
        except Exception:
            return []

        # Filter by the current identifier prefix (e.g., `tr` -> `true`).
        prefix = extract_identifier_prefix(
            document_bytes=document_bytes,
            byte_offset=byte_offset,
            segment_start=segment_start,
            segment_end=segment_end,
            allowed=b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
        )
        raw_prefix = (prefix or "").strip()

        items: list[CompletionItemDict] = []
        seen: set[str] = set()

        def _add(label: str, *, kind: int | None = 12) -> None:
            if not label or label in seen:
                return
            if raw_prefix and not label.startswith(raw_prefix):
                return
            seen.add(label)
            payload: CompletionItemDict = {"label": label}
            if kind is not None:
                payload["kind"] = kind
            items.append(payload)

        type_text = attr.type_text.strip()
        is_optional = type_text.endswith("?")
        if is_optional:
            _add("null")

        prim = None
        try:
            prim = plugin.primitive_codec.parse(type_text)
        except Exception:
            prim = None

        if prim is not None:
            if prim.base_type == CodePrimitiveBaseType.boolean:
                _add("true")
                _add("false")
                return items

            if prim.base_type == CodePrimitiveBaseType.integer:
                _add("0")
                return items

            if prim.base_type == CodePrimitiveBaseType.float:
                _add("0")
                _add("0.0")
                return items

            if prim.base_type == CodePrimitiveBaseType.datetime:
                # Canonical dynamic default.
                _add("now()")
                return items

            if prim.base_type == CodePrimitiveBaseType.string:
                _add('""')
                return items

            if prim.base_type == CodePrimitiveBaseType.json:
                kind = None
                constraints = prim.constraints if isinstance(prim.constraints, dict) else None
                if constraints is not None:
                    kind_val = constraints.get("json_kind")
                    if isinstance(kind_val, str):
                        kind = kind_val.lower()

                if kind == "object":
                    _add("{}")
                    _add('{"key":"value"}')
                    return items
                if kind == "array":
                    _add("[]")
                    return items
                if kind == "value":
                    _add("null")
                    _add("true")
                    _add("false")
                    _add("0")
                    _add('""')
                    _add("{}")
                    _add("[]")
                    return items

        # Non-primitive: enum values.
        scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)
        base_ident = type_text
        try:
            base_ident = plugin.primitive_codec.enum_ident(type_text)
        except Exception:
            base_ident = type_text

        resolved_enum = scope.try_resolve_enum_with_fqn(base_ident)
        if resolved_enum is not None:
            _fqn, enum_cfg = resolved_enum
            enum = enum_cfg.code_section_enum
            if enum is not None:
                for val in enum.code_section_enum_values:
                    name = val.value.strip()
                    if name:
                        _add(name, kind=20)  # EnumMember
        return items

    def _annotation_args_completion_items(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[CompletionItemDict]:
        """Complete annotation args after the verb (project/overlay/override/load)."""
        # Parse the current line so completions work even before the parser sees new tokens.
        cursor = max(byte_offset, 0)
        line_start = document_bytes.rfind(b"\n", 0, cursor)
        line_start = 0 if line_start == -1 else line_start + 1
        line_end = document_bytes.find(b"\n", cursor)
        if line_end == -1:
            line_end = len(document_bytes)

        stmt = parse_annotation_statement_tokens(
            document_bytes=document_bytes,
            segment_start=line_start,
            segment_end=line_end,
        )
        if stmt is None or stmt.verb is None:
            return []

        verb = (stmt.verb.text or "").strip().lower()
        args = list(stmt.args)

        # Determine which arg token we're in (or the insertion index if in whitespace).
        token_idx: int | None = None
        for idx, tok in enumerate(args):
            c = cursor
            if c == tok.range.end and c > tok.range.start:
                c -= 1
            if tok.range.start <= c < tok.range.end:
                token_idx = idx
                break

        if token_idx is not None:
            arg_index = token_idx
            tok = args[token_idx]
            prefix = extract_identifier_prefix(
                document_bytes=document_bytes,
                byte_offset=cursor,
                segment_start=tok.range.start,
                segment_end=tok.range.end,
                allowed=b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
            )
        else:
            arg_index = sum(1 for tok in args if tok.range.end <= cursor)
            prefix = ""

        prev = (args[arg_index - 1].text or "").strip().lower() if arg_index > 0 and args else ""
        seen = {(t.text or "").strip().lower() for t in args}

        def _norm(s: str) -> str:
            v = (s or "").strip().lower()
            if v and v[0] in "\"'":
                v = v[1:]
            if v and v[-1] in "\"'":
                v = v[:-1]
            return v

        norm_prefix = _norm(prefix)

        items: list[CompletionItemDict] = []
        dedup: set[str] = set()

        def _add(label: str, *, kind: int = 14) -> None:
            raw = (label or "").strip()
            if not raw:
                return
            if norm_prefix and not _norm(raw).startswith(norm_prefix):
                return
            if raw in dedup:
                return
            dedup.add(raw)
            items.append({"label": raw, "kind": kind})

        # load
        if verb == "load":
            if prev in {"forward", "reverse", "both"}:
                _add("eager")
                _add("lazy")
                return items
            for t in ("forward", "reverse", "both", "eager", "lazy"):
                _add(t)
            return items

        # project
        if verb == "project":
            if prev == "side":
                for t in ("forward", "reverse", "both"):
                    _add(t)
                return items
            if prev in {"name", "target"}:
                for t in ('"identity"', '"environment"'):
                    _add(t, kind=12)
                return items

            _add("name")
            _add("side")
            _add("target")
            _add("is_branchable")
            # Also allow direct names (parser supports `project <name>`).
            for t in ('"identity"', '"environment"'):
                _add(t, kind=12)
            return items

        # overlay
        if verb == "overlay":
            if prev == "entity":
                try:
                    from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
                        CodeSectionAnnotationOverlayEntity,
                    )

                    for entity in CodeSectionAnnotationOverlayEntity:
                        _add(str(entity.value))
                except Exception:
                    for t in ("class", "enum", "enum_option", "attribute", "function"):
                        _add(t)
                return items

            if prev == "language":
                try:
                    from aware_code_ontology.code.code_enums import CodeLanguage

                    for lang in CodeLanguage:
                        _add(str(lang.value))
                except Exception:
                    for t in ("aware", "python", "dart", "sql"):
                        _add(t)
                return items

            if prev in {"rename", "wire_name"}:
                _add('"name"', kind=12)
                return items

            for t in ("entity", "language", "rename", "wire_name"):
                _add(t)
            return items

        # override
        if verb == "override":
            kind = (args[0].text or "").strip().lower() if args else ""
            if arg_index == 0 and (token_idx is not None or not kind):
                _add("fk")
                _add("relationship")
                return items

            if kind == "fk":
                if prev == "name":
                    _add('"fk_name"', kind=12)
                    return items
                if "nullable" not in seen:
                    _add("nullable")
                _add("name")
                return items

            if kind == "relationship":
                if prev == "name":
                    _add('"name"', kind=12)
                    return items
                _add("name")
                return items

            _add("fk")
            _add("relationship")
            return items

        # discriminate
        if verb == "discriminate":
            if prev == "tag":
                tag_values: list[str] = []
                if self._snapshot is not None:
                    seen_tags: set[str] = set()
                    for code in self._snapshot.codes_by_uri.values():
                        for section in code.code_sections:
                            if section.type != CodeSectionType.annotation:
                                continue
                            ann = section.code_section_annotation
                            if ann is None:
                                continue
                            if (ann.verb or "").strip().lower() != "discriminate":
                                continue
                            try:
                                mode, tag_value = parse_discriminate_args(ann.args)
                            except Exception:
                                continue
                            if mode != "tag" or not tag_value:
                                continue
                            seen_tags.add(tag_value)
                    tag_values = sorted(seen_tags)

                if not tag_values:
                    _add('"tag"', kind=12)
                    return items

                for val in tag_values[:100]:
                    _add(f'"{val}"', kind=12)
                return items

            _add("key")
            _add("tag")
            return items

        # identity
        if verb == "identity":
            if arg_index == 0:
                _add("contained")
                _add("standalone")
                return items

            mode = (args[0].text or "").strip().lower() if args else ""
            if mode not in {"contained", "standalone"}:
                _add("contained")
                _add("standalone")
                return items

            if arg_index == 1:
                _add("structural")
                return items

            structural_token = (args[1].text or "").strip().lower() if len(args) >= 2 else ""
            if structural_token != "structural":
                _add("structural")
                return items

            if self._snapshot is None:
                return items
            code = self._snapshot.codes_by_uri.get(uri)
            if code is None:
                return items

            type_ref = (stmt.path.text or "").strip() if stmt.path is not None else ""
            if "::" in type_ref:
                type_ref = type_ref.split("::", 1)[0].strip()
            if not type_ref:
                return items

            scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)
            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                return items

            _fqn, class_cfg = resolved
            relationship_scope = scope
            if class_cfg.code_section_class is not None:
                relationship_scope = self._snapshot.fqn_resolver.scope_for_code_id(
                    class_cfg.code_section_class.code_section.code_id
                )
            for relationship_key in collect_structural_relationship_keys(
                class_cfg=class_cfg,
                scope=relationship_scope,
                workspace_language=self._workspace.language,
            ):
                _add(relationship_key, kind=10)
            return items

        # reference
        if verb == "reference":
            if arg_index == 0:
                _add("port")
                _add("bind")
                return items

            if prev == "bind":
                if token_idx is not None:
                    tok = args[token_idx]
                    path_prefix = extract_identifier_prefix(
                        document_bytes=document_bytes,
                        byte_offset=cursor,
                        segment_start=tok.range.start,
                        segment_end=tok.range.end,
                        allowed=b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-",
                    )
                else:
                    path_prefix = ""
                return self._annotation_path_completion_items(uri=uri, prefix=path_prefix)

            _add("port")
            _add("bind")
            return items

        # oneof
        if verb == "oneof":
            if self._snapshot is None:
                return []
            code = self._snapshot.codes_by_uri.get(uri)
            if code is None:
                return []
            code_ns = self._snapshot.namespace_by_code_id.get(code.id)

            scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)
            type_ref = (stmt.path.text or "").strip() if stmt.path is not None else ""
            if "::" in type_ref:
                type_ref = type_ref.split("::", 1)[0].strip()
            if not type_ref:
                return []

            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                return []
            _fqn, class_cfg = resolved
            cls = class_cfg.code_section_class
            if cls is None:
                return []

            class_attr_names: list[str] = []
            class_attr_seen: set[str] = set()
            attr_cfg_by_name: dict[str, object] = {}
            for class_attr_cfg in class_cfg.class_config_attribute_configs:
                attr_cfg = class_attr_cfg.attribute_config
                if attr_cfg is None or bool(attr_cfg.is_virtual):
                    continue
                name = (attr_cfg.name or "").strip()
                if not name or name in class_attr_seen:
                    continue
                class_attr_seen.add(name)
                class_attr_names.append(name)
                attr_cfg_by_name[name] = attr_cfg
            if not class_attr_names:
                for attr in cls.code_section_attributes:
                    name = attr.name.strip()
                    if not name or not bool(attr.is_public) or name in class_attr_seen:
                        continue
                    class_attr_seen.add(name)
                    class_attr_names.append(name)

            if not class_attr_names:
                return items

            def _add_class_attr_items(
                *,
                exclude: set[str] | None = None,
                include: set[str] | None = None,
            ) -> None:
                for name in class_attr_names:
                    lowered = name.casefold()
                    if exclude is not None and lowered in exclude:
                        continue
                    if include is not None and lowered not in include:
                        continue
                    _add(name, kind=10)

            args_texts = [(tok.text or "").strip() for tok in args if (tok.text or "").strip()]
            mode: str | None = None
            mode_offset = 0
            if args_texts and args_texts[0].casefold() in {"validation", "identity"}:
                mode = args_texts[0].casefold()
                mode_offset = 1

            if arg_index == 0:
                _add("validation")
                _add("identity")
                if not args_texts:
                    _add_class_attr_items()
                return items

            effective_mode = mode or "validation"
            if effective_mode != "identity":
                selected_members = {text.casefold() for text in args_texts[mode_offset:]}
                _add_class_attr_items(exclude=selected_members)
                return items

            identity_tokens = args_texts[mode_offset:]
            discriminator_positions = [
                idx for idx, text in enumerate(identity_tokens) if text.casefold() == "discriminator"
            ]
            discriminator_pos = discriminator_positions[0] if discriminator_positions else None

            if discriminator_pos is None:
                selected_members = {text.casefold() for text in identity_tokens}
                _add_class_attr_items(exclude=selected_members)
                _add("discriminator")
                return items

            member_tokens = identity_tokens[:discriminator_pos]
            member_names = [text for text in member_tokens if text.casefold() != "discriminator"]
            member_name_set = {text.casefold() for text in member_names}
            local_index = max(0, arg_index - mode_offset)
            if local_index <= discriminator_pos:
                _add_class_attr_items(exclude=member_name_set)
                _add("discriminator")
                return items

            # Immediately after `discriminator`, suggest the discriminator attribute.
            if local_index == discriminator_pos + 1:
                _add_class_attr_items(exclude=member_name_set)
                return items

            mapping_slot = local_index - (discriminator_pos + 2)
            if mapping_slot < 0:
                return items

            discriminator_attr_name = (
                identity_tokens[discriminator_pos + 1] if len(identity_tokens) > discriminator_pos + 1 else ""
            )
            if mapping_slot % 2 == 0:
                variant_values: list[str] = []
                attr_cfg = attr_cfg_by_name.get(discriminator_attr_name)
                type_descriptor = getattr(attr_cfg, "type_descriptor", None)
                enum_config = getattr(type_descriptor, "enum_config", None) if type_descriptor is not None else None
                enum_options = getattr(enum_config, "enum_options", ()) if enum_config is not None else ()
                for option in enum_options:
                    value = (getattr(option, "value", "") or "").strip()
                    if value:
                        variant_values.append(value)
                if not variant_values:
                    discriminator_attr = next(
                        (attr for attr in cls.code_section_attributes if (attr.name or "").strip() == discriminator_attr_name),
                        None,
                    )
                    discriminator_type_ref = (
                        (discriminator_attr.type_text or "").strip() if discriminator_attr is not None else ""
                    )
                    if discriminator_type_ref:
                        enum_candidates = [discriminator_type_ref]
                        if "." not in discriminator_type_ref and code_ns is not None:
                            enum_candidates.append(f"{code_ns.prefix()}.{discriminator_type_ref}")
                        resolved_enum = None
                        for enum_candidate in enum_candidates:
                            resolved_enum = scope.try_resolve_enum_with_fqn(enum_candidate)
                            if resolved_enum is not None:
                                break
                        if resolved_enum is not None:
                            _enum_fqn, enum_cfg = resolved_enum
                            enum = enum_cfg.code_section_enum
                            if enum is not None:
                                for enum_value in enum.code_section_enum_values:
                                    value = (enum_value.value or "").strip()
                                    if value:
                                        variant_values.append(value)
                if variant_values:
                    for value in variant_values:
                        _add(value)
                else:
                    _add("variant")
                return items

            _add_class_attr_items(include=member_name_set)
            return items

        return items

    def _annotation_path_completion_items(self, *, uri: str, prefix: str) -> list[CompletionItemDict]:
        """Complete member segments within `ann <path>` (after `::`)."""
        if self._snapshot is None:
            return []
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return []

        scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)
        parts = prefix.split("::")
        if len(parts) <= 1:
            return self._completion_items_for_prefix(uri=uri, prefix=prefix, mode="annotation_path")

        type_ref = (parts[0] or "").strip()
        member_parts = [p or "" for p in parts[1:]]
        fixed_members = member_parts[:-1]
        partial = member_parts[-1] if member_parts else ""

        if not type_ref:
            return []

        items: list[CompletionItemDict] = []
        seen: set[tuple[str, int | None]] = set()

        def _add(label: str, *, kind: int | None = None, detail: str | None = None) -> None:
            key = (label, kind)
            if key in seen:
                return
            seen.add(key)
            payload: CompletionItemDict = {"label": label}
            if kind is not None:
                payload["kind"] = kind
            if detail:
                payload["detail"] = detail
            items.append(payload)

        resolved_class = scope.try_resolve_class_with_fqn(type_ref)
        if resolved_class is not None:
            _fqn, class_cfg = resolved_class
            cls = class_cfg.code_section_class
            if cls is None:
                return []

            def _add_attrs(attrs: list[CodeSectionAttribute], *, kind: int) -> None:
                for attr in attrs:
                    name = attr.name.strip()
                    if not name:
                        continue
                    if partial and not name.startswith(partial):
                        continue
                    _add(name, kind=kind)

            def _add_funcs(fns: list[CodeSectionFunction], *, kind: int) -> None:
                for fn in fns:
                    name = fn.name.strip()
                    if not name:
                        continue
                    if partial and not name.startswith(partial):
                        continue
                    _add(name, kind=kind)

            def _find_attr(name: str):
                for a in cls.code_section_attributes:
                    if a.name == name:
                        return a
                return None

            def _find_fn(name: str):
                for f in cls.code_section_functions:
                    if f.name == name:
                        return f
                return None

            if len(fixed_members) == 0:
                _add_attrs(cls.code_section_attributes, kind=5)  # Field
                _add_funcs(cls.code_section_functions, kind=2)  # Method
                return items

            if len(fixed_members) == 1:
                head = fixed_members[0]
                fn = _find_fn(head)
                if fn is not None:
                    _add_attrs(fn.code_section_attributes, kind=5)
                    return items

                attr = _find_attr(head)
                edge_name = attr.edge_spec_name if attr is not None else None
                if isinstance(edge_name, str) and edge_name:
                    if not partial or edge_name.startswith(partial):
                        _add(edge_name, kind=7)
                return items

            # Extended overlay patterns:
            # - TypeRef::relationship_attr::EdgeName::edge_member
            # - TypeRef::relationship_attr::EdgeName::edge_fn::edge_fn_attr
            if len(fixed_members) >= 2:
                edge_type_ref = fixed_members[1]
                resolved_edge = scope.try_resolve_class_with_fqn(edge_type_ref)
                if resolved_edge is None:
                    return items
                _, edge_cfg = resolved_edge
                edge_cls = edge_cfg.code_section_class
                if edge_cls is None:
                    return items

                if len(fixed_members) == 2:
                    _add_attrs(edge_cls.code_section_attributes, kind=5)
                    _add_funcs(edge_cls.code_section_functions, kind=2)
                    return items

                edge_fn_name = fixed_members[2]
                edge_fn = None
                for f in edge_cls.code_section_functions:
                    if f.name == edge_fn_name:
                        edge_fn = f
                        break
                if edge_fn is None:
                    return items
                _add_attrs(edge_fn.code_section_attributes, kind=5)
                return items

        resolved_enum = scope.try_resolve_enum_with_fqn(type_ref)
        if resolved_enum is None:
            return items
        _fqn, enum_cfg = resolved_enum
        enum = enum_cfg.code_section_enum
        if enum is None:
            return items
        if fixed_members:
            return items
        for val in enum.code_section_enum_values:
            name = val.value.strip()
            if not name:
                continue
            if partial and not name.startswith(partial):
                continue
            _add(name, kind=20)  # EnumMember

        return items

    def _completion_items_for_prefix(
        self,
        *,
        uri: str,
        prefix: str,
        mode: Literal["type", "import_module", "import_alias", "annotation_path"] = "type",
    ) -> list[CompletionItemDict]:
        if self._snapshot is None:
            return []
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return []

        ns = self._snapshot.namespace_by_code_id.get(code.id)
        if ns is None:
            return []

        resolver = self._snapshot.fqn_resolver
        classes_by_fqn = resolver.classes_by_fqn
        enums_by_fqn = resolver.enums_by_fqn
        scope = resolver.scope_for_code_id(code.id)
        package_prefixes: set[str] = set()
        try:
            for fqn in list(classes_by_fqn.keys()) + list(enums_by_fqn.keys()):
                parts = [p for p in (fqn or "").split(".") if p]
                if parts:
                    package_prefixes.add(parts[0])
        except Exception:
            package_prefixes = set()

        items: list[CompletionItemDict] = []
        seen: set[tuple[str, int | None]] = set()

        def _add(label: str, *, kind: int | None = None, detail: str | None = None) -> None:
            key = (label, kind)
            if key in seen:
                return
            seen.add(key)
            payload: CompletionItemDict = {"label": label}
            if kind is not None:
                payload["kind"] = kind
            if detail:
                payload["detail"] = detail
            items.append(payload)

        raw = (prefix or "").strip()
        if "." not in raw:
            # Unqualified name completion: local schema symbols + import aliases.
            local_prefix = f"{ns.prefix()}."
            for fqn, _ in classes_by_fqn.items():
                if not fqn.startswith(local_prefix):
                    continue
                name = fqn.rsplit(".", 1)[-1]
                if raw and not name.startswith(raw):
                    continue
                _add(name, kind=7, detail=fqn)
            for fqn, _ in enums_by_fqn.items():
                if not fqn.startswith(local_prefix):
                    continue
                name = fqn.rsplit(".", 1)[-1]
                if raw and not name.startswith(raw):
                    continue
                _add(name, kind=13, detail=fqn)

            for alias in resolver.import_aliases_for_code_id(code.id).keys():
                if raw and not alias.startswith(raw):
                    continue
                kind = 9
                resolved = scope.try_resolve_class_with_fqn(alias)
                if resolved is not None:
                    kind = 7
                else:
                    resolved_enum = scope.try_resolve_enum_with_fqn(alias)
                    if resolved_enum is not None:
                        kind = 13
                _add(alias, kind=kind)

            # Primitive types.
            try:
                plugin = CodeLanguagePluginRegistry.get(self._workspace.language)
                primitive_bases = [
                    CodePrimitiveBaseType.any,
                    CodePrimitiveBaseType.boolean,
                    CodePrimitiveBaseType.bytes,
                    CodePrimitiveBaseType.datetime,
                    CodePrimitiveBaseType.float,
                    CodePrimitiveBaseType.integer,
                    CodePrimitiveBaseType.null,
                    CodePrimitiveBaseType.string,
                    CodePrimitiveBaseType.uuid,
                    CodePrimitiveBaseType.vector,
                ]
                # Prefer explicit JSON kind tokens (JsonValue/JsonObject/JsonArray) over raw Json.
                for json_label in ("JsonValue", "JsonObject", "JsonArray"):
                    if raw and not json_label.startswith(raw):
                        continue
                    _add(json_label, kind=14)
                # Dict mapping helper (requires explicit key/value types).
                dict_label = "Dict[String, JsonValue]"
                if not raw or dict_label.startswith(raw):
                    _add(dict_label, kind=14)
                for primitive_base in primitive_bases:
                    try:
                        label = plugin.primitive_codec.render(CodePrimitiveType(base_type=primitive_base))
                    except Exception:
                        continue
                    if label is None:
                        continue
                    if raw and not label.startswith(raw):
                        continue
                    _add(label, kind=14)
            except Exception:
                pass

            return items

        base, partial = raw.rsplit(".", 1)
        if mode in ("type", "annotation_path") and "." not in base:
            # Cross-package shorthand: `dep_pkg.<schema>.<Name>` omits the domain.
            # Offer schema completions when the prefix is a known package namespace.
            if base in package_prefixes:
                schemas: set[str] = set()
                for fqn in list(classes_by_fqn.keys()) + list(enums_by_fqn.keys()):
                    parts = [p for p in (fqn or "").split(".") if p]
                    if len(parts) < 3:
                        continue
                    if parts[0] != base:
                        continue
                    schemas.add(parts[2])
                for schema in sorted(schemas):
                    if partial and not schema.startswith(partial):
                        continue
                    _add(schema, kind=9, detail=f"{base}.{schema}")
            else:
                _add_schema_name_completions(
                    add=_add,
                    classes_by_fqn=classes_by_fqn,
                    enums_by_fqn=enums_by_fqn,
                    namespace=ns,
                    schema=base,
                    partial=partial,
                )

        # Cross-package shorthand leaf completion: `dep_pkg.schema.<Name>`
        if mode in ("type", "annotation_path") and "." in base:
            base_parts = [p for p in base.split(".") if p]
            if len(base_parts) == 2 and base_parts[0] in package_prefixes:
                pkg_prefix, schema = base_parts

                # Only suggest names that are unambiguous across domains for this (pkg, schema).
                seen_names: dict[str, tuple[int, str, object]] = {}
                ambiguous: set[str] = set()

                for fqn, cfg in classes_by_fqn.items():
                    parts = [p for p in (fqn or "").split(".") if p]
                    if len(parts) != 4:
                        continue
                    if parts[0] != pkg_prefix or parts[2] != schema:
                        continue
                    name = parts[3]
                    if partial and not name.startswith(partial):
                        continue
                    prev = seen_names.get(name)
                    if prev is None:
                        seen_names[name] = (7, fqn, cfg.id)
                    else:
                        _, _, prev_id = prev
                        if prev_id != cfg.id:
                            ambiguous.add(name)

                for fqn, cfg in enums_by_fqn.items():
                    parts = [p for p in (fqn or "").split(".") if p]
                    if len(parts) != 4:
                        continue
                    if parts[0] != pkg_prefix or parts[2] != schema:
                        continue
                    name = parts[3]
                    if partial and not name.startswith(partial):
                        continue
                    prev = seen_names.get(name)
                    if prev is None:
                        seen_names[name] = (13, fqn, cfg.id)
                    else:
                        _, _, prev_id = prev
                        if prev_id != cfg.id:
                            ambiguous.add(name)

                for name in sorted(set(seen_names.keys()) - ambiguous):
                    kind, fqn, _ = seen_names[name]
                    _add(name, kind=kind, detail=fqn)

        candidate_prefixes = _candidate_completion_prefixes(
            base_prefix=base,
            namespace=ns,
            import_aliases=resolver.import_aliases_for_code_id(code.id),
        )
        for search_prefix in candidate_prefixes:
            parts = [p for p in search_prefix.split(".") if p]
            if not parts:
                continue
            part_count = len(parts)

            def _scan(symbol_fqn: str) -> None:
                sym_parts = symbol_fqn.split(".")
                if len(sym_parts) <= part_count:
                    return
                if sym_parts[:part_count] != parts:
                    return
                candidate = sym_parts[part_count]
                if partial and not candidate.startswith(partial):
                    return
                # Decide if this candidate is a leaf (class/enum name) or an intermediate segment.
                if part_count == 3:
                    # pkg.domain.schema.<Name>
                    kind = 7  # default class; caller overrides for enums
                    _add(candidate, kind=kind)
                else:
                    _add(candidate, kind=9)

            for fqn in classes_by_fqn.keys():
                _scan(fqn)
            for fqn in enums_by_fqn.keys():
                _scan(fqn)

        # Post-process: refine kinds for leaf symbols when completing at the schema boundary.
        if candidate_prefixes and all(len(p.split(".")) >= 3 for p in candidate_prefixes):
            # When prefix is pkg.domain.schema, candidates can be class/enum names.
            leaf_map: dict[str, int] = {}
            for fqn in classes_by_fqn.keys():
                leaf_map[fqn.rsplit(".", 1)[-1]] = 7
            for fqn in enums_by_fqn.keys():
                leaf_map[fqn.rsplit(".", 1)[-1]] = 13
            for item in items:
                label = item["label"]
                if label in leaf_map:
                    item["kind"] = leaf_map[label]

        return items


def _add_schema_name_completions(
    *,
    add: CompletionItemAdder,
    classes_by_fqn: Mapping[str, ClassConfig],
    enums_by_fqn: Mapping[str, EnumConfig],
    namespace: NamespacePath,
    schema: str,
    partial: str,
) -> None:
    """Add `schema.Name` completion candidates across domains (current package only)."""
    base = (schema or "").strip()
    if not base:
        return

    pkg = namespace.package
    for fqn in classes_by_fqn.keys():
        parts = fqn.split(".")
        if len(parts) != 4:
            continue
        if parts[0] != pkg:
            continue
        if parts[2] != base:
            continue
        name = parts[3]
        if partial and not name.startswith(partial):
            continue
        add(name, kind=7, detail=fqn)

    for fqn in enums_by_fqn.keys():
        parts = fqn.split(".")
        if len(parts) != 4:
            continue
        if parts[0] != pkg:
            continue
        if parts[2] != base:
            continue
        name = parts[3]
        if partial and not name.startswith(partial):
            continue
        add(name, kind=13, detail=fqn)


def _candidate_completion_prefixes(
    *,
    base_prefix: str,
    namespace: NamespacePath,
    import_aliases: Mapping[str, str] | None = None,
) -> list[str]:
    """Return normalized completion prefixes to search under for dotted completion."""
    pkg = namespace.package
    raw = (base_prefix or "").strip()
    if not raw:
        return []

    aliases = dict(import_aliases or {})
    expanded = _expand_import_alias(raw, aliases)
    prefixes = [expanded] if expanded else []
    if expanded and pkg and not expanded.startswith(pkg + ".") and expanded.split(".", 1)[0] != pkg:
        prefixes.append(f"{pkg}.{expanded}")
    # Dedup while preserving order.
    out: list[str] = []
    for p in prefixes:
        if p and p not in out:
            out.append(p)
    return out


def _expand_import_alias(identifier: str, aliases: Mapping[str, str]) -> str:
    raw = (identifier or "").strip()
    if not raw or not aliases:
        return raw

    def _normalize(target: str) -> str:
        t = (target or "").strip()
        return t.removesuffix(".*")

    direct = aliases.get(raw)
    if direct:
        return _normalize(direct) or raw
    if "." not in raw:
        return raw
    head, rest = raw.split(".", 1)
    target = aliases.get(head)
    if not target:
        return raw
    normalized = _normalize(target)
    if not normalized:
        return raw
    return f"{normalized}.{rest}"
