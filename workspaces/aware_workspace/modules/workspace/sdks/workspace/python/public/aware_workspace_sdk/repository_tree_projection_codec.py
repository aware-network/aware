"""Bounded canonical tree metadata; decoding never restores owner authority."""

from __future__ import annotations

import hashlib
import json
import re
import types
import unicodedata
import weakref
from dataclasses import fields
from typing import Any, Literal, NoReturn, cast, get_args, get_origin, get_type_hints

from . import repository_tree_projection_values as values
from ._tree_native_binding import bind_tree_json as _bind_native_tree_json
from ._tree_native_binding import prepare as _prepare_native_tree_binding
from ._tree_native_binding import seal as _seal_native_tree_binding
from .repository_source_projection_values import RepositoryObservationCoordinate
from .repository_workflow_source_codec import (
    WorkspaceWorkflowSourceValueError,
    repository_workflow_source_value_from_payload,
)
from .repository_workflow_source_values import WorkspaceWorkflowSourceBinding
from .repository_workflow_values import WorkspaceWorkflowMarker

_TYPES = values.TREE_VALUE_TYPES
_NESTED_TYPES = _TYPES + (
    RepositoryObservationCoordinate,
    WorkspaceWorkflowSourceBinding,
    WorkspaceWorkflowMarker,
)
_DEFINITIONS: tuple[
    tuple[type[Any], tuple[tuple[str, types.MemberDescriptorType, Any], ...]], ...
] = tuple(
    (
        cls,
        tuple(
            (
                field.name,
                cast(types.MemberDescriptorType, vars(cls)[field.name]),
                get_type_hints(cls)[field.name],
            )
            for field in fields(cls)
        ),
    )
    for cls in _NESTED_TYPES
)
_DEFINITIONS_BY_ID = {id(cls): (cls, rows) for cls, rows in _DEFINITIONS}
_TOP_TYPES_BY_ID = {id(cls): cls for cls in _TYPES}

# Immutable schema classification only: no value, verdict or owner state survives
# a call. Original field order and every generic predicate remain unchanged.
_FIELD_CHECKS_BY_ID = {
    id(cls): (
        cls,
        tuple(
            (name, mask)
            for name, _, _ in definitions
            if (
                mask := (
                    int(name.endswith("_digest") or name == "content_digest")
                    | (
                        2
                        if name in ("path", "source_path", "source_output_path")
                        else 0
                    )
                    | (4 if "identity" in name else 0)
                    | (8 if name.endswith("_ref") else 0)
                )
            )
        ),
    )
    for cls, definitions in _DEFINITIONS
}


def _compile_hint_shapes() -> dict[int, tuple[Any, Any, tuple[Any, ...]]]:
    shapes: dict[int, tuple[Any, Any, tuple[Any, ...]]] = {}

    def retain(hint: Any) -> None:
        if id(hint) in shapes:
            return
        origin, args = get_origin(hint), get_args(hint)
        shapes[id(hint)] = (hint, origin, args)
        if origin in (tuple, types.UnionType):
            for child in args:
                retain(child)

    for cls, definitions in _DEFINITIONS:
        retain(cls)
        for _, _, hint in definitions:
            retain(hint)
    return shapes


_HINT_SHAPES = _compile_hint_shapes()
_TREE_JSON_ACTIVE = False
_TREE_NATIVE_HANDOFF = _prepare_native_tree_binding(globals())
if _TREE_NATIVE_HANDOFF is not None:
    _TREE_NATIVE_CONVERT = _TREE_NATIVE_HANDOFF[1]
    _TREE_NATIVE_VERIFY = _TREE_NATIVE_HANDOFF[2]


def _compile_native_fields() -> dict[int, tuple[Any, Any, tuple[Any, ...]]]:
    result: dict[int, tuple[Any, Any, tuple[Any, ...]]] = {}
    for cls, definitions in _DEFINITIONS:
        rows = []
        for name, descriptor, hint in definitions:
            selected, nullable = hint, False
            if hint is not str and hint is not int and hint is not bool:
                shape = _HINT_SHAPES.get(id(hint))
                if (
                    shape is not None
                    and shape[0] is hint
                    and shape[1] is types.UnionType
                    and len(shape[2]) == 2
                    and (shape[2][0] is type(None) or shape[2][1] is type(None))
                ):
                    selected = shape[2][1] if shape[2][0] is type(None) else shape[2][0]
                    nullable = True
            if selected is not str and selected is not int and selected is not bool:
                selected = None
            rows.append(
                (
                    name,
                    descriptor,
                    hint,
                    selected,
                    nullable,
                    -(2**63) if name in ("mtime_ns", "ctime_ns") else 0,
                )
            )
        # Emit only this module's closed schema and fixed primitive predicates.
        # Field names are Python literals; no caller text becomes program source.
        lines = [
            "def convert(annotation, value, definitions, depth, context):",
            "    converted = {}",
        ]
        native_root = (
            _TREE_NATIVE_HANDOFF is not None
            and cls is values.WorkspaceTreeProjectionBinding
        )
        if native_root:
            lines.extend(
                (
                    "    if context is None and type(depth) is int and -(2**31) <= depth <= 24:",
                    "        native_call = '__workspace_tree_native_call_v1__'",
                    "        native_context_ref = '__workspace_tree_native_context_v1__'",
                    "        native_context = native_context_ref()",
                    "        native_verify = '__workspace_tree_native_verify_v1__'",
                    "        native_result = native_call(native_context, annotation, value, '', depth)",
                    "        native_verify(native_context)",
                    "        return native_result",
                )
            )
        for index, (name, _, _, scalar, nullable, floor) in enumerate(rows):
            lines.extend(
                (
                    f"    item = definitions[{index}][1].__get__(value, annotation)",
                    "    if depth + 1 > 24:",
                    "        _refuse('tree metadata nesting exceeds bound')",
                )
            )
            prefix = "    "
            if scalar is not None:
                if nullable:
                    lines.extend(
                        (
                            "    if item is None:",
                            f"        converted[{name!r}] = None",
                            "    else:",
                        )
                    )
                    prefix = "        "
                    lines.extend(
                        (
                            prefix + "if depth + 2 > 24:",
                            prefix
                            + "    _refuse('tree metadata nesting exceeds bound')",
                        )
                    )
                lines.extend(
                    (
                        prefix + f"if type(item) is not {scalar.__name__}:",
                        prefix + "    _refuse('tree primitive type differs')",
                    )
                )
                if scalar is str:
                    lines.extend(
                        (
                            prefix + "try:",
                            prefix
                            + "    size = len(item) if item.isascii() else len(item.encode('utf-8'))",
                            prefix + "except UnicodeError:",
                            prefix + "    _refuse('tree text must be UTF-8')",
                            prefix + "if size > 16384:",
                            prefix + "    _refuse('tree text exceeds bound')",
                        )
                    )
                elif scalar is int:
                    lines.extend(
                        (
                            prefix + f"if not {floor} <= item <= 18446744073709551616:",
                            prefix + "    _refuse('tree integer exceeds bound')",
                        )
                    )
                lines.append(prefix + f"converted[{name!r}] = item")
            elif (
                (shape := _HINT_SHAPES.get(id(rows[index][2]))) is not None
                and shape[0] is rows[index][2]
                and shape[1] is Literal
                and all(type(member) is str for member in shape[2])
            ):
                # Only closed authored string enums use this path. Preserve
                # exact type, depth and member order without generic reflection.
                lines.extend(
                    (
                        f"    if type(item) is not str or item not in {shape[2]!r}:",
                        "        _refuse('unknown tree enum')",
                        f"    converted[{name!r}] = item",
                    )
                )
            else:
                lines.append(
                    f"    converted[{name!r}] = _convert(definitions[{index}][2], item, "
                    f"decode=False, depth=depth + 1, field_name={name!r}, context=context)"
                )
        lines.append("    return converted")
        namespace: dict[str, Any] = {}
        exec(  # noqa: S102 -- closed authored schema and fixed predicates only
            compile("\n".join(lines), "<workspace-tree-native-fields>", "exec"),
            globals(),
            namespace,
        )
        convert = namespace["convert"]
        if native_root:
            # Finish this declaration before publishing its original code pin.
            # Runtime dispatch uses immutable code constants, never mutable
            # globals/defaults or a later code-object replacement.
            assert _TREE_NATIVE_HANDOFF is not None
            captured = {
                # Code objects do not participate in cyclic GC. Keep only a
                # weak context reference in constants; the original module owns
                # its strong declaration lifetime through the handoff tuple.
                "__workspace_tree_native_context_v1__": weakref.ref(
                    _TREE_NATIVE_HANDOFF[0]
                ),
                "__workspace_tree_native_call_v1__": _TREE_NATIVE_HANDOFF[1],
                "__workspace_tree_native_verify_v1__": _TREE_NATIVE_HANDOFF[2],
            }
            constants = convert.__code__.co_consts
            if any(constants.count(marker) != 1 for marker in captured):
                raise RuntimeError("ambiguous native tree declaration constant")
            code = convert.__code__.replace(
                co_consts=tuple(
                    captured[item] if type(item) is str and item in captured else item
                    for item in constants
                )
            )
            convert = types.FunctionType(code, globals(), "convert")
        result[id(cls)] = (cls, definitions, (convert, convert.__code__))
    return result


_NATIVE_FIELDS_BY_ID = _compile_native_fields()
_NATIVE_ORIGINALS_BY_ID = _NATIVE_FIELDS_BY_ID.copy()
_LIMIT_CEILINGS = dict(
    zip(
        (field.name for field in fields(values.WorkspaceTreeLimits)),
        (
            values.MAX_TREE_FILES,
            values.MAX_TREE_ANCESTORS,
            values.MAX_TREE_FILE_BYTES,
            values.MAX_TREE_COMBINED_BODY_BYTES,
            values.MAX_TREE_METADATA_BYTES,
            values.MAX_TREE_PATH_BYTES,
            values.MAX_TREE_DESCRIPTORS,
            values.MAX_TREE_BODIES,
            values.MAX_TREE_CAPTURES,
            values.MAX_TREE_DELTAS,
        ),
        strict=True,
    )
)
_COLLECTION_LIMITS = {
    "files": values.MAX_TREE_FILES,
    "ancestors": values.MAX_TREE_ANCESTORS,
    "receipts": values.MAX_TREE_RECEIPTS,
    "final_entries": values.MAX_TREE_FILES,
    "physical_effects": values.MAX_TREE_SUBEFFECTS,
    "error_refs": values.MAX_TREE_SUBEFFECTS,
    "marker_environment": 64,
}
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ASCII_PATH_INVALID = re.compile(r"(?:^|/)\.{0,2}(?:/|$)|\\|[^\x20-\x7e]|[^/]{256}")


class WorkspaceTreeProjectionValueError(ValueError):
    """Malformed descriptive evidence; contains no retry permission."""


def _refuse(reason: str) -> NoReturn:
    raise WorkspaceTreeProjectionValueError(reason)


def _known(value_type: object, *, top: bool = False) -> bool:
    if top:
        original = _TOP_TYPES_BY_ID.get(id(value_type))
        return original is not None and original is value_type
    definition = _DEFINITIONS_BY_ID.get(id(value_type))
    return definition is not None and definition[0] is value_type


def _native_record_fields(
    annotation: Any,
    value: Any,
    definitions: tuple[tuple[str, types.MemberDescriptorType, Any], ...],
    *,
    depth: int,
    context: Any,
) -> dict[str, Any]:
    """Read every authenticated field, inline only closed primitive checks.

    The caller authenticates the complete original descriptor set before entry.
    Nested records/collections keep the original traversal and logical quotas.
    This retains no data or validation verdict after the current conversion.
    """
    schema = _NATIVE_FIELDS_BY_ID.get(id(annotation))
    if (
        schema is None
        or schema is not _NATIVE_ORIGINALS_BY_ID.get(id(annotation))
        or schema[0] is not annotation
        or schema[1] is not definitions
    ):
        _refuse("exact descriptive tree value required")
    convert, code = schema[2]
    if (
        type(convert) is not types.FunctionType
        or convert.__code__ is not code
        or convert.__defaults__ is not None
        or convert.__kwdefaults__ is not None
    ):
        _refuse("native tree schema code or defaults changed")
    return cast(dict[str, Any], convert(annotation, value, definitions, depth, context))


def _convert(
    annotation: Any,
    value: Any,
    *,
    decode: bool,
    depth: int = 0,
    field_name: str = "",
    context: Any = None,
) -> Any:
    if depth > 24:
        _refuse("tree metadata nesting exceeds bound")
    if annotation is str or annotation is int or annotation is bool:
        if type(value) is not annotation:
            _refuse("tree primitive type differs")
        if annotation is str:
            try:
                text = cast(str, value)
                size = len(text) if text.isascii() else len(text.encode("utf-8"))
            except UnicodeError:
                _refuse("tree text must be UTF-8")
            if size > 16384:
                _refuse("tree text exceeds bound")
        elif annotation is int:
            # Stat timestamps can precede the Unix epoch; preserve their exact value.
            floor = -(2**63) if field_name in ("mtime_ns", "ctime_ns") else 0
            if not floor <= cast(int, value) <= 2**64:
                _refuse("tree integer exceeds bound")
        return value
    definition = _DEFINITIONS_BY_ID.get(id(annotation))
    if definition is not None and definition[0] is annotation:
        definitions = definition[1]
        namespace = cast(dict[str, object], vars(annotation))
        for name, descriptor, _ in definitions:
            if namespace.get(name) is not descriptor:
                _refuse("tree slot descriptor changed")
        memo_key = (annotation, id(value), decode)
        if context is not None and memo_key in context.memo:
            # Conversion may be shared; logical quota usage must not be.
            context.charge(context.memo_references[memo_key])
            return context.memo[memo_key]
        reference_start = context.references if context is not None else 0
        if decode:
            if type(value) is not dict:
                _refuse("tree record must be an exact object")
            source = cast(dict[str, Any], value)
            if any(type(key) is not str for key in source):
                _refuse("tree field names must be exact text")
            if set(source) != {name for name, _, _ in definitions}:
                _refuse("tree fields differ")
            converted = {
                name: _convert(
                    hint,
                    source[name],
                    decode=True,
                    depth=depth + 1,
                    field_name=name,
                    context=context,
                )
                for name, _, hint in definitions
            }
        else:
            if type(value) is not annotation:
                _refuse("exact descriptive tree value required")
            try:
                converted = _native_record_fields(
                    annotation, value, definitions, depth=depth, context=context
                )
            except AttributeError:
                _refuse("tree fields missing")
        if not decode:
            _validate(annotation, converted)
            if context is not None:
                context.memo[memo_key] = converted
                context.memo_references[memo_key] = context.references - reference_start
            return converted
        detached = object.__new__(annotation)
        for name, descriptor, _ in definitions:
            descriptor.__set__(detached, converted[name])
        if context is not None:
            context.memo[memo_key] = detached
            context.memo_references[memo_key] = context.references - reference_start
        return detached
    shape = _HINT_SHAPES.get(id(annotation))
    origin, args = (
        (shape[1], shape[2])
        if shape is not None and shape[0] is annotation
        else (get_origin(annotation), get_args(annotation))
    )
    if origin is types.UnionType:
        if value is None and type(None) in args:
            return None
        selected = next(arg for arg in args if arg is not type(None))
        if selected is str or selected is int or selected is bool:
            # Preserve the recursive scalar check, without another dispatch or
            # annotation lookup. None still returns before the deeper check.
            if depth >= 24:
                _refuse("tree metadata nesting exceeds bound")
            if type(value) is not selected:
                _refuse("tree primitive type differs")
            if selected is str:
                try:
                    text = cast(str, value)
                    size = len(text) if text.isascii() else len(text.encode("utf-8"))
                except UnicodeError:
                    _refuse("tree text must be UTF-8")
                if size > 16384:
                    _refuse("tree text exceeds bound")
            elif selected is int:
                floor = -(2**63) if field_name in ("mtime_ns", "ctime_ns") else 0
                if not floor <= cast(int, value) <= 2**64:
                    _refuse("tree integer exceeds bound")
            return value
        return _convert(
            selected,
            value,
            decode=decode,
            depth=depth + 1,
            field_name=field_name,
            context=context,
        )
    if origin is Literal:
        value_type = type(value)
        if value_type is str or value_type is int:
            for item in args:
                if value_type is type(item) and value == item:
                    return value
        _refuse("unknown tree enum")
    if origin is tuple:
        if field_name == "resources" and context is not None:
            return context.resources(value, decode=decode)
        if type(value) is not (list if decode else tuple):
            _refuse("tree ordered collection type differs")
        items = cast(list[Any] | tuple[Any, ...], value)
        limit = _COLLECTION_LIMITS.get(field_name, values.MAX_TREE_RECEIPTS)
        if len(items) > limit:
            _refuse("tree ordered collection exceeds bound")
        if (
            items
            and type(args) is tuple
            and args
            and (args[0] is str or args[0] is int or args[0] is bool)
        ):
            # These are the same recursive primitive checks, in member order.
            # Empty tuples do not enter a deeper level or invent a refusal.
            converted = []
            member_type = args[0]
            member_depth = depth + 1
            for item in items:
                if member_depth > 24:
                    _refuse("tree metadata nesting exceeds bound")
                if type(item) is not member_type:
                    _refuse("tree primitive type differs")
                if member_type is str:
                    try:
                        text = cast(str, item)
                        size = (
                            len(text) if text.isascii() else len(text.encode("utf-8"))
                        )
                    except UnicodeError:
                        _refuse("tree text must be UTF-8")
                    if size > 16384:
                        _refuse("tree text exceeds bound")
                elif member_type is int:
                    # Original tuple recursion does not pass its parent's name:
                    # tuple integers stay unsigned even for timestamp callers.
                    if not 0 <= cast(int, item) <= 2**64:
                        _refuse("tree integer exceeds bound")
                converted.append(item)
        else:
            converted = [
                _convert(args[0], item, decode=decode, depth=depth + 1, context=context)
                for item in items
            ]
        return tuple(converted) if decode else converted
    _refuse("unsupported tree metadata type")


def _wire(payload: object) -> str:
    try:
        callee = json.dumps
        try:
            if not _TREE_JSON_ACTIVE:
                text = callee(
                    payload,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            else:
                native: Any = "_TREE_JSON_NATIVE_CALL_"
                context: Any = "_TREE_JSON_NATIVE_CONTEXT_"
                text = native(context(), callee, payload, json)
        finally:
            callee = None
        size = len(text.encode("utf-8"))
    except (ValueError, RecursionError, UnicodeError):
        _refuse("malformed tree JSON")
    if size > values.MAX_TREE_METADATA_BYTES:
        _refuse("tree metadata byte bound exceeded")
    return text


def _path(path: str, *, maximum: int = values.MAX_TREE_PATH_BYTES) -> None:
    ascii_only = path.isascii()
    if ascii_only:
        if type(path) is not str:
            # Preserve the original short-circuit and exception behavior for
            # malformed values and subclasses; only exact text takes this cut.
            if (
                not path
                or len(path) > maximum
                or _ASCII_PATH_INVALID.search(path) is not None
            ):
                _refuse("noncanonical tree path")
            return
        native_slot: Any = (
            "__workspace_ascii_path_slot_v2__",
            None,
        )
        native_positive = native_slot[1]
        if native_positive is not None and native_positive(path, maximum):
            return
        if not path or len(path) > maximum or "\\" in path or not path.isprintable():
            _refuse("noncanonical tree path")
        for part in path.split("/"):
            if part in ("", ".", "..") or len(part) > 255:
                _refuse("noncanonical tree path")
        return
    parts = path.split("/")
    if (
        not path
        or (len(path) if ascii_only else len(path.encode("utf-8"))) > maximum
        or (not ascii_only and unicodedata.normalize("NFC", path) != path)
        or "\\" in path
        or (
            not path.isprintable()
            if ascii_only
            else any(unicodedata.category(char).startswith("C") for char in path)
        )
        or any(part in ("", ".", "..") for part in parts)
        or any(
            (len(part) if ascii_only else len(part.encode("utf-8"))) > 255
            for part in parts
        )
    ):
        _refuse("noncanonical tree path")


def _sequence(payload: dict[str, Any]) -> str:
    files, ancestors, limits = (
        payload["files"],
        payload["ancestors"],
        payload["limits"],
    )
    if (
        len(files) > limits["maximum_file_transitions"]
        or len(ancestors) > limits["maximum_ancestors"]
    ):
        _refuse("tree sequence exceeds requested counts")
    file_paths = [row["path"] for row in files]
    ancestor_paths = [row["path"] for row in ancestors]
    if file_paths != sorted(set(file_paths)) or ancestor_paths != sorted(
        set(ancestor_paths), key=lambda path: (path.count("/"), path)
    ):
        _refuse("tree sequence is duplicated or reordered")
    if set(file_paths).intersection(ancestor_paths):
        _refuse("tree file and ancestor paths collide")
    parents = set(ancestor_paths)
    for path in file_paths + ancestor_paths:
        _path(path, maximum=limits["maximum_path_utf8_bytes"])
        parts = path.split("/")
        if any("/".join(parts[:i]) not in parents for i in range(1, len(parts))):
            _refuse("tree ancestor set is incomplete")
    # The detached payload is unchanged throughout this complete sequence check.
    wire = _wire(payload)
    wire_size = len(wire.encode("utf-8"))
    if wire_size > limits["maximum_metadata_bytes"]:
        _refuse("tree metadata exceeds requested byte bound")
    if "before" not in (files[0] if files else {}):
        return wire
    combined_bytes = 0
    body_refs: set[str] = set()
    for row in files:
        before_bytes = row["before"]["size_bytes"] or 0
        after_bytes = row["successor_size_bytes"] or 0
        if max(before_bytes, after_bytes) > limits["maximum_file_bytes"]:
            _refuse("tree file exceeds requested byte bound")
        combined_bytes += before_bytes + after_bytes
        for key in ("before_body_ref", "successor_body_ref"):
            if row[key] is not None:
                body_refs.add(row[key])
    if combined_bytes > limits["maximum_combined_body_bytes"]:
        _refuse("tree preimage and successor budget exceeded")
    if len(body_refs) > limits["maximum_retained_bodies"]:
        _refuse("tree original body quota exceeded")
    effects = [row["path"] for row in payload["scratch_effects"]]
    if set(effects).intersection(file_paths + ancestor_paths):
        _refuse("tree scratch paths collide with transitions")
    if len(payload["effect_paths"]) != len(set(payload["effect_paths"])) or len(
        payload["read_guard_paths"]
    ) != len(set(payload["read_guard_paths"])):
        _refuse("tree effect or guard paths duplicate")
    for path in effects + payload["effect_paths"] + payload["read_guard_paths"]:
        _path(path, maximum=limits["maximum_path_utf8_bytes"])
    if wire_size > limits["maximum_metadata_bytes"]:
        _refuse("tree metadata exceeds requested byte bound")
    return wire


def _validate(cls: type[Any], payload: dict[str, Any]) -> None:
    if cls is WorkspaceWorkflowSourceBinding:
        try:
            repository_workflow_source_value_from_payload(cls, payload)
        except WorkspaceWorkflowSourceValueError as error:
            raise WorkspaceTreeProjectionValueError(
                "invalid original source metadata"
            ) from error
        return
    schema = _FIELD_CHECKS_BY_ID.get(id(cls))
    if schema is None or schema[0] is not cls:
        _refuse("exact descriptive tree value required")
    for name, mask in schema[1]:
        item = payload[name]
        if item is None:
            continue
        if mask & 1 and (type(item) is not str or not _DIGEST.fullmatch(item)):
            _refuse("invalid tree digest")
        if mask & 2:
            _path(item)
        if mask & 4 and len(item) != 2:
            _refuse("tree identity must contain exactly two integers")
        if mask & 8 and not item:
            _refuse("empty tree reference")
    if cls is values.WorkspaceTreeLimits:
        if any(not 1 <= payload[name] <= cap for name, cap in _LIMIT_CEILINGS.items()):
            _refuse("tree limit exceeds accepted ceiling or is empty")
        return
    if cls is values.WorkspaceTreeEntryPin:
        details = [item for name, item in payload.items() if name != "exists"]
        if not payload["exists"]:
            if any(item is not None for item in details):
                _refuse("absent tree entry cannot invent a preimage")
        elif any(
            payload[name] is None
            for name in (
                "device",
                "inode",
                "size_bytes",
                "mtime_ns",
                "ctime_ns",
                "mode",
                "link_count",
            )
        ):
            _refuse("present tree entry lacks identity or mode")
        elif not 0 <= payload["mode"] <= 0o7777 or payload["link_count"] < 1:
            _refuse("invalid observed tree mode or link count")
        return
    if cls in (values.WorkspaceTreeFileIntent, values.WorkspaceTreeFileTransition):
        deleted = payload["kind"] == "DELETE"
        if deleted:
            if (
                payload["source_output_path"] is not None
                or payload["requested_mode"] is not None
            ):
                _refuse("DELETE must have no successor intent")
        elif payload["source_output_path"] is None or payload["requested_mode"] not in (
            0o644,
            0o755,
        ):
            _refuse("tree successor requires original output and explicit mode")
        if cls is values.WorkspaceTreeFileTransition:
            before = payload["before"]
            if before["exists"] != (payload["kind"] != "CREATE"):
                _refuse("tree transition preimage existence differs")
            if before["exists"] and (
                before["link_count"] != 1
                or before["content_digest"] is None
                or payload["before_body_ref"] is None
            ):
                _refuse("tree regular preimage or retained body is missing")
            if not before["exists"] and payload["before_body_ref"] is not None:
                _refuse("CREATE cannot invent a retained preimage")
            successor = [
                payload[name]
                for name in (
                    "source_path",
                    "successor_body_ref",
                    "successor_digest",
                    "successor_size_bytes",
                )
            ]
            if deleted and any(item is not None for item in successor):
                _refuse("DELETE cannot retain a successor")
            if not deleted and any(item is None for item in successor):
                _refuse("tree successor metadata is incomplete")
            if (payload["successor_size_bytes"] or 0) > values.MAX_TREE_FILE_BYTES:
                _refuse("tree successor exceeds accepted byte bound")
            if (before["size_bytes"] or 0) > values.MAX_TREE_FILE_BYTES:
                _refuse("tree preimage exceeds accepted byte bound")
        return
    if cls in (
        values.WorkspaceTreeAncestorIntent,
        values.WorkspaceTreeAncestorTransition,
    ):
        created = payload["intent"] == "create"
        if payload["requested_mode"] != (0o755 if created else None):
            _refuse("tree ancestor mode changes require explicit create intent")
        if cls is values.WorkspaceTreeAncestorTransition:
            if payload["before"]["exists"] == created:
                _refuse("tree ancestor preimage differs from intent")
            if payload["before"]["content_digest"] is not None:
                _refuse("tree ancestor cannot masquerade as a regular file")
        return
    if (
        cls is values.WorkspaceTreeScratchEffect
        and payload["requested_mode"] is not None
        and payload["requested_mode"]
        not in (
            (0o600, 0o644, 0o755) if payload["kind"] == "create" else (0o644, 0o755)
        )
    ):
        _refuse("scratch mode differs")
    sequence_wire = None
    if cls in (
        values.WorkspaceTreeProjectionRequest,
        values.WorkspaceTreeProjectionBinding,
    ):
        sequence_wire = _sequence(payload)
    if (
        cls is values.WorkspaceTreeProjectionRequest
        and payload["workflow_ref"]
        != payload["expected_source_binding"]["workflow_ref"]
    ):
        _refuse("tree request workflow correspondence differs")
    if cls is values.WorkspaceTreeProjectionRequest:
        return
    if cls is values.WorkspaceTreeProjectionBinding:
        source = payload["source_binding"]
        for name in ("execution_id", "process_id", "thread_id"):
            if payload[name] != source[name]:
                _refuse("tree source execution correspondence differs")
        if (
            payload["target_repository_binding_ref"]
            != source["target_repository_binding_ref"]
            or payload["target_root_identity"] != source["target_root_identity"]
        ):
            _refuse("tree source target correspondence differs")
        if payload["workflow_ref"] != source["workflow_ref"]:
            _refuse("tree workflow correspondence differs")
        if (
            payload["observation_coordinate"]["repository_binding_ref"]
            != payload["target_repository_binding_ref"]
        ):
            _refuse("tree observation target differs")
        if payload["transition_count"] != len(payload["files"]) + len(
            payload["ancestors"]
        ):
            _refuse("tree complete ordinal count differs")
        # Reuse this invocation's unchanged, fully validated canonical text.
        # In this exact closed schema, ancestors precede binding_ref and
        # effect_paths follows it. Ancestors have no binding_ref field; quoted
        # caller text is escaped, so neither delimiter can occur in a string.
        # Removing that single member yields exactly the original complete
        # commitment bytes, without serializing all file rows a second time.
        assert sequence_wire is not None
        first = sequence_wire.index(',"binding_ref":')
        following = sequence_wire.index(',"effect_paths":', first)
        complete_wire = sequence_wire[:first] + sequence_wire[following:]
        expected = "sha256:" + hashlib.sha256(complete_wire.encode()).hexdigest()
        if payload["binding_ref"] != expected:
            _refuse("tree binding commitment differs")
        return
    if (
        cls
        in (
            values.WorkspaceTreeProjectionResolution,
            values.WorkspaceTreeProjectionRefusalEvidence,
        )
        and payload["authorizes_retry"]
    ):
        _refuse("descriptive tree evidence cannot authorize retry")
    if cls is values.WorkspaceTreeProjectionObservation:
        if payload["completed_prefix"] > payload["binding"]["transition_count"]:
            _refuse("tree completed prefix exceeds original sequence")
        pending = payload["pending_ordinal"]
        if pending is not None and pending >= payload["binding"]["transition_count"]:
            _refuse("tree pending ordinal exceeds original sequence")
        receipts = payload["receipts"]
        if [row["ordinal"] for row in receipts] != list(range(len(receipts))):
            _refuse("tree receipt order is not the original prefix")
        if len(receipts) > payload["binding"]["transition_count"]:
            _refuse("tree receipt count exceeds original sequence")
        for row in receipts:
            if (
                row["binding_ref"] != payload["binding"]["binding_ref"]
                or row["invocation_ref"] != payload["binding"]["invocation_ref"]
            ):
                _refuse("tree receipt binding differs")


_RESOURCE_ENCODING = "aware.workspace.tree-cleanup-resource-table.v1"
# A lossless expansion ceiling, independent of wire bytes and the per-snapshot
# 8,192-item limit. This bounds tuple storage even for malicious range bodies.
_MAX_RESOURCE_REFERENCES = values.MAX_TREE_RECEIPTS * 512


def _cleanup_groups(value: object) -> list[tuple[Any, ...]]:
    groups: list[tuple[Any, ...]] = []

    def visit(item: object) -> None:
        cls = type(item)
        if not _known(cls):
            return  # _convert rejects any foreign value without dispatch.
        definitions = next(rows for kind, rows in _DEFINITIONS if kind is cls)
        for name, descriptor, _ in definitions:
            if name not in ("cleanup", "observation", "receipts", "resources"):
                continue
            if vars(cls).get(name) is not descriptor:
                _refuse("tree slot descriptor changed")
            try:
                child = descriptor.__get__(item, cls)
            except AttributeError:
                _refuse("tree fields missing")
            if (
                cls is values.WorkspaceTreeProjectionCleanupObservation
                and name == "resources"
            ):
                if (
                    type(child) is not tuple
                    or len(cast(tuple[Any, ...], child)) > values.MAX_TREE_RECEIPTS
                ):
                    _refuse("tree ordered collection exceeds bound")
                groups.append(cast(tuple[Any, ...], child))
            elif name == "receipts" and type(child) is tuple:
                if len(cast(tuple[Any, ...], child)) > values.MAX_TREE_RECEIPTS:
                    _refuse("tree ordered collection exceeds bound")
                for row in cast(tuple[Any, ...], child):
                    visit(row)
            elif name in ("cleanup", "observation"):
                visit(child)

    visit(value)
    return groups


class _ResourceContext:
    def __init__(self) -> None:
        self.memo: dict[Any, Any] = {}
        self.memo_references: dict[Any, int] = {}
        self.pool: list[dict[str, Any]] = []
        self.keys: dict[tuple[Any, ...], int] = {}
        self.identities: dict[int, int] = {}
        self.decoded: list[Any] = []
        self.references = 0

    def charge(self, count: int) -> None:
        self.references += count
        if self.references > _MAX_RESOURCE_REFERENCES:
            _refuse("tree resource expansion exceeds bound")

    def index(self, row: object) -> int:
        if type(row) is not values.WorkspaceTreeResourceCleanup:
            _refuse("exact descriptive tree value required")
        if id(row) in self.identities:
            return self.identities[id(row)]
        converted = _convert(type(row), row, decode=False, context=self)
        # Conversion has freshly checked all seven closed fields. Hash only
        # these detached primitives, preserving every null and diagnostic order.
        diagnostics = tuple(converted["diagnostics"])
        key = (
            converted["resource_ref"],
            converted["kind"],
            converted["path"],
            converted["ownership"],
            converted["cleanup_attempted"],
            converted["cleanup_state"],
            diagnostics,
        )
        # Fixed keys/punctuation/booleans/null fit within 512 bytes. Any Unicode
        # character needs at most six UTF-8 JSON bytes; each diagnostic adds at
        # most three punctuation bytes. If this conservative proof is too large,
        # use the original exact wire check instead of refusing a legal row.
        maximum_bytes = (
            512
            + 3 * len(diagnostics)
            + 6
            * (
                sum(len(item) for item in key[:6] if type(item) is str)
                + sum(len(item) for item in diagnostics)
            )
        )
        if maximum_bytes > values.MAX_TREE_METADATA_BYTES:
            _wire(converted)
        index = self.keys.get(key)
        if index is None:
            if len(self.pool) >= values.MAX_TREE_RECEIPTS:
                _refuse("tree resource table exceeds bound")
            index = len(self.pool)
            self.keys[key] = index
            self.pool.append(converted)
        self.identities[id(row)] = index
        return index

    def resources(self, value: Any, *, decode: bool) -> Any:
        if decode:
            if (
                type(value) is not dict
                or set(cast(dict[str, Any], value)) != {"ranges"}
                or type(cast(dict[str, Any], value)["ranges"]) is not list
            ):
                _refuse("tree resource ranges differ")
            ranges = cast(list[Any], cast(dict[str, Any], value)["ranges"])
            if len(ranges) > values.MAX_TREE_RECEIPTS:
                _refuse("tree resource ranges exceed bound")
            count = 0
            end = None
            for span in ranges:
                if (
                    type(span) is not list
                    or len(cast(list[Any], span)) != 2
                    or any(type(i) is not int for i in cast(list[Any], span))
                ):
                    _refuse("tree resource range shape differs")
                first, length = cast(list[int], span)
                if (
                    first < 0
                    or length <= 0
                    or first + length > len(self.decoded)
                    or first == end
                ):
                    _refuse("tree resource range is invalid or noncanonical")
                count += length
                end = first + length
            if count > values.MAX_TREE_RECEIPTS:
                _refuse("tree ordered collection exceeds bound")
            self.charge(count)
            return tuple(
                row
                for first, length in cast(list[list[int]], ranges)
                for row in self.decoded[first : first + length]
            )
        if (
            type(value) is not tuple
            or len(cast(tuple[Any, ...], value)) > values.MAX_TREE_RECEIPTS
        ):
            _refuse("tree ordered collection exceeds bound")
        self.charge(len(cast(tuple[Any, ...], value)))
        ranges_out: list[list[int]] = []
        for row in cast(tuple[Any, ...], value):
            index = self.index(row)
            if ranges_out and ranges_out[-1][0] + ranges_out[-1][1] == index:
                ranges_out[-1][1] += 1
            else:
                ranges_out.append([index, 1])
        return {"ranges": ranges_out}


def repository_tree_projection_value_to_payload(value: object) -> dict[str, Any]:
    if not _known(type(value), top=True):
        _refuse("live handles and native bodies cannot be encoded")
    groups = _cleanup_groups(value)
    context = _ResourceContext()
    shared = sum(len(rows) for rows in groups) > values.MAX_TREE_RECEIPTS
    if shared:
        # Seed from the largest complete snapshot, in original row order. Prefix
        # snapshots then use spans into that lossless table; changed dispositions
        # get distinct records, never overwrite older evidence.
        for row in max(groups, key=len):
            context.index(row)
    payload = cast(
        dict[str, Any],
        _convert(type(value), value, decode=False, context=context if shared else None),
    )
    if shared:
        payload = {
            "encoding": _RESOURCE_ENCODING,
            "type": cast(dict[type[Any], str], values.TREE_SCHEMA_IDS)[type(value)],
            "resources": context.pool,
            "value": payload,
        }
    # Request/binding sequence validation already measured this exact detached
    # payload against both original byte ceilings. Nothing changes it afterward.
    # Every other top-level value, and every changed resource envelope, needs its
    # own complete wire measurement. No size verdict survives this invocation.
    if shared or type(value) not in (
        values.WorkspaceTreeProjectionRequest,
        values.WorkspaceTreeProjectionBinding,
    ):
        _wire(payload)
    return payload


def _plain_payload(value: object, depth: int = 0) -> None:
    # Validate exact JSON containers before envelope membership or serialization;
    # neither operation may dispatch foreign key/hash/iterator behavior.
    if depth > 28:
        _refuse("tree metadata nesting exceeds bound")
    if type(value) is dict:
        if any(type(key) is not str for key in cast(dict[Any, Any], value)):
            _refuse("tree field names must be exact text")
        for child in cast(dict[str, Any], value).values():
            _plain_payload(child, depth + 1)
    elif type(value) is list:
        for child in cast(list[Any], value):
            _plain_payload(child, depth + 1)
    elif value is not None and type(value) not in (str, int, bool):
        _refuse("tree payload must contain exact JSON values")


def repository_tree_projection_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    if not _known(value_type, top=True):
        _refuse("unknown descriptive tree type")
    _plain_payload(payload)
    _wire(payload)  # Bound the wire before any reference expansion.
    context = None
    raw = payload
    compact = type(payload) is dict and "encoding" in cast(dict[str, Any], payload)
    if compact:
        body = cast(dict[str, Any], payload)
        if (
            set(body) != {"encoding", "type", "resources", "value"}
            or body["encoding"] != _RESOURCE_ENCODING
            or body["type"]
            != cast(dict[type[Any], str], values.TREE_SCHEMA_IDS)[value_type]
        ):
            _refuse("tree resource envelope differs")
        pool = body["resources"]
        if (
            type(pool) is not list
            or len(cast(list[Any], pool)) > values.MAX_TREE_RECEIPTS
        ):
            _refuse("tree resource table exceeds bound")
        context = _ResourceContext()
        for row in cast(list[Any], pool):
            detached = _convert(
                values.WorkspaceTreeResourceCleanup, row, decode=True, context=context
            )
            # Preserve the original closed-field/value validation.
            _convert(
                values.WorkspaceTreeResourceCleanup,
                detached,
                decode=False,
                context=context,
            )
            context.decoded.append(detached)
        raw = body["value"]
    decoded = cast(T, _convert(value_type, raw, decode=True, context=context))
    encoded = repository_tree_projection_value_to_payload(decoded)
    if compact and _wire(encoded) != _wire(cast(dict[str, Any], payload)):
        _refuse("tree resource envelope is not canonical")
    return decoded


def repository_tree_projection_value_clone[T](value: T) -> T:
    return repository_tree_projection_value_from_payload(
        type(value), repository_tree_projection_value_to_payload(value)
    )


def repository_tree_projection_value_to_json(value: object) -> str:
    return _wire(repository_tree_projection_value_to_payload(value))


def repository_tree_projection_value_from_json[T](value_type: type[T], text: str) -> T:
    if type(text) is not str:
        _refuse("tree JSON must be exact text")
    try:
        if len(text.encode("utf-8")) > values.MAX_TREE_METADATA_BYTES:
            _refuse("tree metadata byte bound exceeded")
    except UnicodeError:
        _refuse("tree JSON must be UTF-8")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, item in items:
            if key in output:
                _refuse("duplicate tree field")
            output[key] = item
        return output

    try:
        payload = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda _: _refuse("nonfinite tree number"),
        )
    except (ValueError, RecursionError, UnicodeError) as error:
        raise WorkspaceTreeProjectionValueError("malformed tree JSON") from error
    if _wire(payload) != text:
        _refuse("tree JSON is not canonical")
    return repository_tree_projection_value_from_payload(value_type, payload)


def repository_tree_projection_value_digest(value: object) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            repository_tree_projection_value_to_json(value).encode("utf-8")
        ).hexdigest()
    )


def repository_tree_projection_value_validate_equal(
    value: object, *, expected_value: object
) -> None:
    """Validate descriptive equality without cloning the native tree value graph.

    Both sides pass the original encoding checks, even when they are identical.
    Original nested source-metadata validation and canonical payload work remain.
    This check grants no owner authority and retains no evidence between calls.
    """
    actual = expected = None
    try:
        if type(value) is not type(expected_value) or not _known(type(value), top=True):
            _refuse("exact matching descriptive tree types required")
        actual = repository_tree_projection_value_to_payload(value)
        expected = repository_tree_projection_value_to_payload(expected_value)
        # Only the validated, exact JSON primitives and containers reach equality.
        if actual != expected:
            _refuse("descriptive tree values differ")
    finally:
        value = expected_value = actual = expected = None


_TREE_JSON_HANDOFF = _bind_native_tree_json(globals())
_seal_native_tree_binding(globals(), _TREE_NATIVE_HANDOFF)
