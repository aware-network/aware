"""Original local appointments for a bounded Meta pure-read model profile.

The profile accepts the existing TypeSchema wire contracts with one graph root,
required non-null scalar fields and no constraints, defaults or aliases. It owns
no Code admission and rejects wider schemas. Topology semantics belong to
Ontology. Portable schema values never recreate the nominal model appointment.
"""

from __future__ import annotations

import _json
import hashlib
import os
import threading
import time
import weakref
from types import CellType, FunctionType, MappingProxyType, ModuleType
from typing import Any, NamedTuple, Never

from . import _origin_profile, encoding

MODEL_ADMISSION_CONTRACT = "aware.meta.local-object-read-model-admission.v1"
MODEL_PROFILE = "aware.meta.local-single-graph-scalar-read-model.v1"


class LocalReadModelEvidence(NamedTuple):
    owner_ref: str
    owner_generation: str
    source_definition_ref: str
    model_ref: str
    model_revision_ref: str
    root_type_ref: str
    projection_ref: str
    bundle_bytes: bytes
    slice_bytes: bytes
    topology_bytes: bytes
    model_admission_bytes: bytes
    deadline: float


def _build_local_model_api():
    kind, identify, length = (type, id, len)
    text, byte_type, integer, boolean = (str, bytes, int, bool)
    tuple_type, list_type, dictionary, set_type, frozen_type, zipping = (
        tuple,
        list,
        dict,
        set,
        frozenset,
        zip,
    )
    get, object_new = (object.__getattribute__, object.__new__)
    raw_dict = type.__dict__["__dict__"].__get__
    raw_mro = type.__dict__["__mro__"].__get__
    raw_bases = type.__dict__["__bases__"].__get__
    items, get_dict, put, pop = (dict.items, dict.get, dict.__setitem__, dict.pop)
    proxy_items = MappingProxyType.items
    function_type, module_type, cell_type = (FunctionType, ModuleType, CellType)
    function_slots = FunctionType.__dict__
    code_get = function_slots["__code__"].__get__
    defaults_get = function_slots["__defaults__"].__get__
    keywords_get = function_slots["__kwdefaults__"].__get__
    closure_get = function_slots["__closure__"].__get__
    cell_get = CellType.__dict__["cell_contents"].__get__
    weak, deref = (weakref.ref, weakref.ReferenceType.__call__)
    pid, thread, now = (os.getpid, threading.get_ident, time.monotonic)
    original_pid, original_thread = (pid(), thread())
    error_new, error_init, error_class = (
        BaseException.__new__,
        BaseException.__init__,
        ValueError,
    )
    base_error = BaseException
    scan_string = _json.scanstring
    hash_new = hashlib.sha256
    hash_kind = kind(hash_new(b""))
    hex_digest = raw_dict(hash_kind)["hexdigest"]
    canonical = _origin_profile.canonical_json_for_origin
    evidence_class = LocalReadModelEvidence
    evidence_new = tuple.__new__
    own_namespace = globals()
    contract, profile = (MODEL_ADMISSION_CONTRACT, MODEL_PROFILE)
    schema_contract, slice_contract = (
        "aware.meta.semantic-type-schema.v1",
        "aware.meta.semantic-type-schema-slice.v1",
    )
    modules = (_origin_profile, encoding, _json)
    banks = tuple_type(
        (m, get(m, "__dict__"), tuple_type(items(get(m, "__dict__")))) for m in modules
    )
    primitive_bindings = (
        (os, "getpid", pid),
        (threading, "get_ident", thread),
        (time, "monotonic", now),
        (weakref, "ref", weak),
        (hashlib, "sha256", hash_new),
    )
    owners: dict[int, Any] = {}
    owner_definitions: dict[int, Any] = {}
    owner_limit, handle_limit, model_limit, retained_limit = (
        64,
        64,
        64,
        8 * 1024 * 1024,
    )
    live_classes = ()
    source_functions = ()
    source_data = ()
    own_entries: Any = None
    sealed = False
    entry_expectation = ()
    pinned_entry_expectation = ()
    primitives = (
        kind,
        identify,
        length,
        get_dict,
        put,
        pop,
        items,
        raw_dict,
        raw_mro,
        raw_bases,
        cell_get,
        code_get,
        defaults_get,
        keywords_get,
        closure_get,
        weak,
        deref,
        error_new,
        error_init,
        error_class,
        tuple_type,
        list_type,
        dictionary,
        set_type,
        frozen_type,
        zipping,
        text,
        byte_type,
        integer,
        boolean,
        get,
        object_new,
        proxy_items,
        pid,
        thread,
        now,
        scan_string,
        hash_new,
        hex_digest,
        evidence_new,
    )
    pinned_primitives = primitives
    call_codes: dict[int, Any] = {}

    def fail(code) -> Never:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        error_new = _native_envelope[17]
        error_init = _native_envelope[18]
        error_class = _native_envelope[19]
        error = error_new(error_class)
        error_init(error, code)
        raise error

    def fingerprint(value) -> Any:
        value_kind = kind(value)
        if value_kind is dictionary:
            return tuple_type(((identify(k), identify(v)) for k, v in items(value)))
        if (
            value_kind is tuple_type
            or value_kind is list_type
            or value_kind is set_type
            or (value_kind is frozen_type)
        ):
            return tuple_type(identify(v) for v in value)
        return None

    def guard():
        if primitives is not pinned_primitives:
            _refusal_type: Any = ().__class__.__class__
            _refusal_dict: Any = {}.__class__
            _refusal_tuple: Any = ().__class__
            _refusal_set: Any = {0}.__class__
            if _refusal_type(owners) is _refusal_dict:
                for _refusal_row in _refusal_dict.values(owners):
                    if (
                        _refusal_type(_refusal_row) is _refusal_tuple
                        and _refusal_tuple.__len__(_refusal_row) == 4
                    ):
                        if _refusal_type(_refusal_row[1]) is _refusal_dict:
                            _refusal_dict.clear(_refusal_row[1])
                        if _refusal_type(_refusal_row[2]) is _refusal_dict:
                            for _refusal_key, _refusal_record in _refusal_dict.items(
                                _refusal_row[2]
                            ):
                                if (
                                    _refusal_type(_refusal_record) is _refusal_tuple
                                    and _refusal_tuple.__len__(_refusal_record) == 3
                                ):
                                    _refusal_dict.__setitem__(
                                        _refusal_row[2],
                                        _refusal_key,
                                        (_refusal_record[0], None, None),
                                    )
                        if _refusal_type(_refusal_row[3]) is _refusal_set:
                            _refusal_set.add(_refusal_row[3], "*")
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        identify = _native_envelope[1]
        length = _native_envelope[2]
        get_dict = _native_envelope[3]
        items = _native_envelope[6]
        raw_dict = _native_envelope[7]
        raw_mro = _native_envelope[8]
        raw_bases = _native_envelope[9]
        cell_get = _native_envelope[10]
        code_get = _native_envelope[11]
        defaults_get = _native_envelope[12]
        keywords_get = _native_envelope[13]
        closure_get = _native_envelope[14]
        error_new = _native_envelope[17]
        error_class = _native_envelope[19]
        dictionary = _native_envelope[22]
        zipping = _native_envelope[25]
        text = _native_envelope[26]
        get = _native_envelope[30]
        proxy_items = _native_envelope[32]
        if entry_expectation is not pinned_entry_expectation:
            raise error_new(error_class, "model_owner_changed")
        for bank_cell, original_bank in entry_expectation:
            if cell_get(bank_cell) is not original_bank:
                raise error_new(error_class, "model_owner_changed")
        if not sealed or kind(own_namespace) is not dictionary:
            raise error_new(error_class, "model_owner_changed")
        if length(own_namespace) != length(own_entries):
            raise error_new(error_class, "model_owner_changed")
        for key in own_namespace:
            if kind(key) is not text:
                raise error_new(error_class, "model_owner_changed")
        for key, original in own_entries:
            if get_dict(own_namespace, key) is not original:
                raise error_new(error_class, "model_owner_changed")
        for module, name, original in primitive_bindings:
            if (
                kind(module) is not module_type
                or get_dict(get(module, "__dict__"), name) is not original
            ):
                raise error_new(error_class, "model_owner_changed")
        for module, namespace, entries in banks:
            if (
                kind(module) is not module_type
                or get(module, "__dict__") is not namespace
                or length(namespace) != length(entries)
            ):
                raise error_new(error_class, "model_owner_changed")
            for key in namespace:
                if kind(key) is not text:
                    raise error_new(error_class, "model_owner_changed")
            for key, original in entries:
                if get_dict(namespace, key) is not original:
                    raise error_new(error_class, "model_owner_changed")
        for cls, meta, bases, mro, entries in live_classes:
            if (
                kind(cls) is not meta
                or raw_bases(cls) is not bases
                or raw_mro(cls) is not mro
            ):
                raise error_new(error_class, "model_owner_changed")
            current = raw_dict(cls)
            if length(current) != length(entries):
                raise error_new(error_class, "model_owner_changed")
            for key, value in proxy_items(current):
                if kind(key) is not text:
                    raise error_new(error_class, "model_owner_changed")
            for key, original in entries:
                if current.get(key) is not original:
                    raise error_new(error_class, "model_owner_changed")
        for fn, code, defaults, keywords, cells, attributes in source_functions:
            if (
                kind(fn) is not function_type
                or code_get(fn) is not code
                or defaults_get(fn) is not defaults
                or (keywords_get(fn) is not keywords)
            ):
                raise error_new(error_class, "model_owner_changed")
            if closure_get(fn) is not cells[0]:
                raise error_new(error_class, "model_owner_changed")
            for cell, original in cells[1]:
                if kind(cell) is not cell_type or cell_get(cell) is not original:
                    raise error_new(error_class, "model_owner_changed")
            for name, original in attributes:
                if get(fn, name) is not original:
                    raise error_new(error_class, "model_owner_changed")
        for value, value_kind, original in source_data:
            if kind(value) is not value_kind:
                raise error_new(error_class, "model_owner_changed")
            if value_kind is dictionary:
                if length(value) != length(original):
                    raise error_new(error_class, "model_owner_changed")
                for (key, current), (key_id, value_id) in zipping(
                    items(value), original, strict=True
                ):
                    if identify(key) != key_id or identify(current) != value_id:
                        raise error_new(error_class, "model_owner_changed")
            else:
                if length(value) != length(original):
                    raise error_new(error_class, "model_owner_changed")
                for current, original_id in zipping(value, original, strict=True):
                    if identify(current) != original_id:
                        raise error_new(error_class, "model_owner_changed")

    guard_code = code_get(guard)

    def token(value) -> str:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        length = _native_envelope[2]
        text = _native_envelope[26]
        _actual_fail = fail
        if (
            kind(value) is not text
            or not value
            or length(value) > 512
            or (text.split(value) != [value])
            or ("\x00" in value)
        ):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_coordinate_invalid")
        if length(text.encode(value, "utf-8")) > 512:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_coordinate_invalid")
        return value

    def decode(payload) -> dict[str, Any]:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        length = _native_envelope[2]
        put = _native_envelope[4]
        list_type = _native_envelope[21]
        dictionary = _native_envelope[22]
        text = _native_envelope[26]
        byte_type = _native_envelope[27]
        integer = _native_envelope[28]
        scan_string = _native_envelope[36]
        _actual_canonical = canonical
        _actual_fail = fail
        _actual_guard = guard
        _actual_scan_string = scan_string
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        if kind(payload) is not byte_type or not payload or length(payload) > 1048576:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_schema_invalid")
        source = byte_type.decode(payload, "utf-8")
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        result: Any
        size, cursor, stack, result, nodes = (length(source), 0, [], None, 0)
        expecting_value = True
        while True:
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            while cursor < size and source[cursor] in " \t\r\n":
                cursor += 1
            if expecting_value:
                if cursor >= size:
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_schema_invalid")
                marker = source[cursor]
                if marker == "{" or marker == "[":
                    if length(stack) >= 32:
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_limit")
                    value = {} if marker == "{" else []
                    stack.append((value, "key" if marker == "{" else "value", None))
                    cursor += 1
                    expecting_value = False
                    continue
                if marker == '"':
                    value, cursor = _actual_scan_string(source, cursor + 1, True)
                    (
                        _actual_guard
                        if _native_code(_actual_guard)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_guard)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )()
                elif source[cursor : cursor + 4] == "true":
                    value, cursor = (True, cursor + 4)
                elif source[cursor : cursor + 5] == "false":
                    value, cursor = (False, cursor + 5)
                elif source[cursor : cursor + 4] == "null":
                    value, cursor = (None, cursor + 4)
                else:
                    end = cursor + (marker == "-")
                    while end < size and "0" <= source[end] <= "9":
                        end += 1
                    if end == cursor or source[cursor:end] == "-" or end - cursor > 128:
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_invalid")
                    value, cursor = (integer(source[cursor:end]), end)
                    (
                        _actual_guard
                        if _native_code(_actual_guard)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_guard)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )()
                nodes += 1
                if nodes > 16384:
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_schema_limit")
                if not stack:
                    result = value
                    break
                container, state, key = stack[-1]
                if kind(container) is dictionary:
                    put(container, key, value)
                else:
                    list_type.append(container, value)
                stack[-1] = (container, "comma", None)
                expecting_value = False
            else:
                container, state, key = stack[-1]
                close = "}" if kind(container) is dictionary else "]"
                if cursor >= size:
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_schema_invalid")
                if state in ("key", "value") and source[cursor] == close:
                    list_type.pop(stack)
                    cursor += 1
                    nodes += 1
                    if nodes > 16384:
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_limit")
                    if not stack:
                        result = container
                        break
                    parent, _, parent_key = stack[-1]
                    if kind(parent) is dictionary:
                        put(parent, parent_key, container)
                    else:
                        list_type.append(parent, container)
                    stack[-1] = (parent, "comma", None)
                    continue
                if state == "comma":
                    if source[cursor] == close:
                        stack[-1] = (
                            container,
                            "key" if kind(container) is dictionary else "value",
                            None,
                        )
                        continue
                    if source[cursor] != ",":
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_invalid")
                    cursor += 1
                    stack[-1] = (
                        container,
                        "required_key"
                        if kind(container) is dictionary
                        else "required_value",
                        None,
                    )
                    continue
                if state in ("key", "required_key"):
                    if source[cursor] != '"':
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_invalid")
                    key, cursor = _actual_scan_string(source, cursor + 1, True)
                    (
                        _actual_guard
                        if _native_code(_actual_guard)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_guard)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )()
                    if key in container:
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_duplicate_key")
                    while cursor < size and source[cursor] in " \t\r\n":
                        cursor += 1
                    if cursor >= size or source[cursor] != ":":
                        (
                            _actual_fail
                            if _native_code(_actual_fail)
                            is _native_dictionary_get(
                                call_codes, _native_identify(_actual_fail)
                            )
                            else (_unused for _unused in ()).throw(
                                _native_error_new(
                                    _native_error_class, "model_owner_changed"
                                )
                            )
                        )("model_schema_invalid")
                    cursor += 1
                    stack[-1] = (container, "pending", key)
                expecting_value = True
        while cursor < size and source[cursor] in " \t\r\n":
            cursor += 1
        if cursor != size or kind(result) is not dictionary:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_schema_invalid")
        rendered = (
            _actual_canonical
            if _native_code(_actual_canonical)
            is _native_dictionary_get(call_codes, _native_identify(_actual_canonical))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(result)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        if text.encode(rendered, "utf-8") != payload:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_schema_not_canonical")
        return result

    def exact(value, keys):
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        length = _native_envelope[2]
        dictionary = _native_envelope[22]
        text = _native_envelope[26]
        _actual_fail = fail
        if kind(value) is not dictionary or length(value) != length(keys):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_schema_invalid")
        for key in value:
            if kind(key) is not text or key not in keys:
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_schema_invalid")

    def digest(contract_value, body) -> str:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        text = _native_envelope[26]
        hash_new = _native_envelope[37]
        hex_digest = _native_envelope[38]
        _actual_canonical = canonical
        _actual_guard = guard
        _actual_hash_new = hash_new
        _actual_hex_digest = hex_digest
        rendered = (
            _actual_canonical
            if _native_code(_actual_canonical)
            is _native_dictionary_get(call_codes, _native_identify(_actual_canonical))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(body)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        raw = text.encode(contract_value + "\n" + rendered, "utf-8")
        hashed = _actual_hash_new(raw)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        result = "sha256:" + _actual_hex_digest(hashed)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        return result

    def admit_schema(bundle_bytes, slice_bytes, root_type_ref):
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        length = _native_envelope[2]
        items = _native_envelope[6]
        list_type = _native_envelope[21]
        set_type = _native_envelope[23]
        text = _native_envelope[26]
        _actual_canonical = canonical
        _actual_decode = decode
        _actual_digest = digest
        _actual_exact = exact
        _actual_fail = fail
        _actual_guard = guard
        _actual_token = token
        bundle = (
            _actual_decode
            if _native_code(_actual_decode)
            is _native_dictionary_get(call_codes, _native_identify(_actual_decode))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(bundle_bytes)
        supplied_slice = (
            _actual_decode
            if _native_code(_actual_decode)
            is _native_dictionary_get(call_codes, _native_identify(_actual_decode))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(slice_bytes)
        (
            _actual_exact
            if _native_code(_actual_exact)
            is _native_dictionary_get(call_codes, _native_identify(_actual_exact))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(
            bundle,
            ("contract", "namespace", "semantic_version", "types", "schema_digest"),
        )
        if bundle["contract"] != schema_contract:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_schema_contract_unsupported")
        (
            _actual_token
            if _native_code(_actual_token)
            is _native_dictionary_get(call_codes, _native_identify(_actual_token))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(bundle["namespace"])
        (
            _actual_token
            if _native_code(_actual_token)
            is _native_dictionary_get(call_codes, _native_identify(_actual_token))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(bundle["semantic_version"])
        types = bundle["types"]
        if kind(types) is not list_type or length(types) != 1:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_profile_unsupported")
        root = types[0]
        (
            _actual_exact
            if _native_code(_actual_exact)
            is _native_dictionary_get(call_codes, _native_identify(_actual_exact))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(
            root,
            (
                "type_ref",
                "name",
                "kind",
                "fields",
                "identity",
                "enum_values",
                "union_variants",
                "scalar_target",
                "discriminant_field_ref",
                "constraints",
                "aliases",
            ),
        )
        if (
            _actual_token
            if _native_code(_actual_token)
            is _native_dictionary_get(call_codes, _native_identify(_actual_token))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(root["type_ref"]) != root_type_ref or root["kind"] != "graph_object":
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_root_identity_missing")
        (
            _actual_token
            if _native_code(_actual_token)
            is _native_dictionary_get(call_codes, _native_identify(_actual_token))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(root["name"])
        if (
            root["enum_values"] != []
            or root["union_variants"] != []
            or root["scalar_target"] is not None
            or (root["discriminant_field_ref"] is not None)
            or (root["constraints"] != {})
            or (root["aliases"] != [])
        ):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_profile_unsupported")
        fields = root["fields"]
        if kind(fields) is not list_type or not fields or length(fields) > 256:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_profile_unsupported")
        refs, names = (set_type(), set_type())
        for field in fields:
            (
                _actual_exact
                if _native_code(_actual_exact)
                is _native_dictionary_get(call_codes, _native_identify(_actual_exact))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(
                field,
                (
                    "field_ref",
                    "name",
                    "shape",
                    "required",
                    "nullable",
                    "has_default",
                    "default_value",
                    "constraints",
                    "aliases",
                ),
            )
            field_ref, name = (
                (
                    _actual_token
                    if _native_code(_actual_token)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_token)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )(field["field_ref"]),
                (
                    _actual_token
                    if _native_code(_actual_token)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_token)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )(field["name"]),
            )
            if field_ref in refs or name in names:
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_schema_duplicate_field")
            refs.add(field_ref)
            names.add(name)
            if (
                field["required"] is not True
                or field["nullable"] is not False
                or field["has_default"] is not False
                or (field["default_value"] is not None)
                or (field["constraints"] != {})
                or (field["aliases"] != [])
            ):
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_profile_unsupported")
            shape = field["shape"]
            (
                _actual_exact
                if _native_code(_actual_exact)
                is _native_dictionary_get(call_codes, _native_identify(_actual_exact))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(
                shape,
                ("kind", "scalar_kind", "type_ref", "element", "map_value", "variants"),
            )
            if (
                shape["kind"] != "scalar"
                or shape["scalar_kind"] not in ("string", "integer", "boolean")
                or shape["type_ref"] is not None
                or (shape["element"] is not None)
                or (shape["map_value"] is not None)
                or (shape["variants"] != [])
            ):
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_profile_unsupported")
        identity = root["identity"]
        (
            _actual_exact
            if _native_code(_actual_exact)
            is _native_dictionary_get(call_codes, _native_identify(_actual_exact))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(identity, ("field_refs",))
        selected = identity["field_refs"]
        if (
            kind(selected) is not list_type
            or not selected
            or length(selected) > length(refs)
        ):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_root_identity_missing")
        seen = set_type()
        for ref in selected:
            (
                _actual_token
                if _native_code(_actual_token)
                is _native_dictionary_get(call_codes, _native_identify(_actual_token))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(ref)
            if ref not in refs or ref in seen:
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_root_identity_missing")
            seen.add(ref)
        semantic = {
            key: value for key, value in items(bundle) if key != "schema_digest"
        }
        if bundle["schema_digest"] != (
            _actual_digest
            if _native_code(_actual_digest)
            is _native_dictionary_get(call_codes, _native_identify(_actual_digest))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(schema_contract, semantic):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_schema_digest_invalid")
        derived = {
            "contract": slice_contract,
            "bundle_digest": bundle["schema_digest"],
            "namespace": bundle["namespace"],
            "semantic_version": bundle["semantic_version"],
            "root_type_refs": [root_type_ref],
            "types": types,
        }
        derived["slice_digest"] = (
            _actual_digest
            if _native_code(_actual_digest)
            is _native_dictionary_get(call_codes, _native_identify(_actual_digest))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(slice_contract, derived)
        rendered = (
            _actual_canonical
            if _native_code(_actual_canonical)
            is _native_dictionary_get(call_codes, _native_identify(_actual_canonical))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(derived)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        if text.encode(rendered, "utf-8") != slice_bytes or supplied_slice != derived:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_slice_not_original_closure")
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()

    def clear_model(row, model_ref):
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        put = _native_envelope[4]
        pop = _native_envelope[5]
        items = _native_envelope[6]
        tuple_type = _native_envelope[20]
        pop(row[1], model_ref, None)
        row[3].add(model_ref)
        for key, record in tuple_type(items(row[2])):
            if record[1] is not None and record[1][0] == model_ref:
                put(row[2], key, (record[0], None, None))

    def terminal(row):
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        put = _native_envelope[4]
        items = _native_envelope[6]
        tuple_type = _native_envelope[20]
        row[1].clear()
        for key, record in tuple_type(items(row[2])):
            put(row[2], key, (record[0], None, None))
        row[3].add("*")

    def original_owner(owner) -> Any:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        identify = _native_envelope[1]
        get_dict = _native_envelope[3]
        deref = _native_envelope[16]
        _actual_fail = fail
        row = get_dict(owners, identify(owner))
        if (
            row is None
            or deref(row[0]) is not owner
            or kind(owner) is not LocalReadModelOwner
        ):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_owner_not_issued")
        return row

    def original_handle(row, handle) -> Any:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        kind = _native_envelope[0]
        identify = _native_envelope[1]
        get_dict = _native_envelope[3]
        deref = _native_envelope[16]
        _actual_fail = fail
        record = get_dict(row[2], identify(handle))
        if (
            record is None
            or deref(record[0]) is not handle
            or kind(handle) is not ModelHandle
        ):
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_handle_not_issued")
        return record

    def current_owner(owner) -> Any:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        put = _native_envelope[4]
        items = _native_envelope[6]
        tuple_type = _native_envelope[20]
        pid = _native_envelope[33]
        thread = _native_envelope[34]
        _actual_fail = fail
        _actual_guard = guard
        _actual_original_owner = original_owner
        _actual_pid = pid
        _actual_thread = thread
        row = (
            _actual_original_owner
            if _native_code(_actual_original_owner)
            is _native_dictionary_get(
                call_codes, _native_identify(_actual_original_owner)
            )
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )(owner)
        try:
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            if _actual_pid() != original_pid or _actual_thread() != original_thread:
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_owner_context_changed")
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
        except base_error:
            row[1].clear()
            for key, record in tuple_type(items(row[2])):
                put(row[2], key, (record[0], None, None))
            row[3].add("*")
            raise
        if "*" in row[3]:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_owner_retired")
        return row

    def capacity() -> int:
        if primitives is not pinned_primitives:
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        length = _native_envelope[2]
        total = 0
        for row in owners.values():
            for definition in row[1].values():
                total += (
                    length(definition[4])
                    + length(definition[5])
                    + length(definition[6])
                )
            for record in row[2].values():
                if record[2] is not None:
                    total += length(record[2][10])
        return total

    class ModelHandle:
        __slots__ = ("__weakref__",)

        def __new__(cls, *args, **kwargs):
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            _actual_fail = fail
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_handle_is_owner_issued")

        def __copy__(self):
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            _actual_fail = fail
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_handle_is_nontransferable")

        def __deepcopy__(self, memo):
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            _actual_fail = fail
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_handle_is_nontransferable")

        def __reduce__(self) -> Never:
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            _actual_fail = fail
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_handle_is_nontransferable")

    class LocalReadModelOwner:
        __slots__ = ("__weakref__",)

        def __new__(cls, *args, **kwargs):
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            _actual_fail = fail
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_owner_is_composition_issued")

        def appoint(
            self,
            *,
            model_ref,
            model_revision_ref,
            root_type_ref,
            projection_ref,
            bundle_bytes,
            slice_bytes,
            topology_bytes,
            lifetime_ms=30000,
        ):
            if primitives is not pinned_primitives:
                _refusal_type: Any = ().__class__.__class__
                _refusal_dict: Any = {}.__class__
                _refusal_tuple: Any = ().__class__
                _refusal_set: Any = {0}.__class__
                if _refusal_type(owners) is _refusal_dict:
                    for _refusal_row in _refusal_dict.values(owners):
                        if (
                            _refusal_type(_refusal_row) is _refusal_tuple
                            and _refusal_tuple.__len__(_refusal_row) == 4
                        ):
                            if _refusal_type(_refusal_row[1]) is _refusal_dict:
                                _refusal_dict.clear(_refusal_row[1])
                            if _refusal_type(_refusal_row[2]) is _refusal_dict:
                                for (
                                    _refusal_key,
                                    _refusal_record,
                                ) in _refusal_dict.items(_refusal_row[2]):
                                    if (
                                        _refusal_type(_refusal_record) is _refusal_tuple
                                        and _refusal_tuple.__len__(_refusal_record) == 3
                                    ):
                                        _refusal_dict.__setitem__(
                                            _refusal_row[2],
                                            _refusal_key,
                                            (_refusal_record[0], None, None),
                                        )
                            if _refusal_type(_refusal_row[3]) is _refusal_set:
                                _refusal_set.add(_refusal_row[3], "*")
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            kind = _native_envelope[0]
            identify = _native_envelope[1]
            length = _native_envelope[2]
            get_dict = _native_envelope[3]
            put = _native_envelope[4]
            pop = _native_envelope[5]
            items = _native_envelope[6]
            cell_get = _native_envelope[10]
            code_get = _native_envelope[11]
            weak = _native_envelope[15]
            deref = _native_envelope[16]
            error_new = _native_envelope[17]
            error_class = _native_envelope[19]
            tuple_type = _native_envelope[20]
            text = _native_envelope[26]
            byte_type = _native_envelope[27]
            integer = _native_envelope[28]
            object_new = _native_envelope[31]
            now = _native_envelope[35]
            evidence_new = _native_envelope[39]
            _actual_admit_schema = admit_schema
            _actual_canonical = canonical
            _actual_capacity = capacity
            _actual_clear_model = clear_model
            _actual_current_owner = current_owner
            _actual_fail = fail
            _actual_guard = guard
            _actual_now = now
            _actual_token = token
            row = get_dict(owners, identify(self))
            if row is None or deref(row[0]) is not self:
                raise error_new(error_class, "model_owner_changed")
            try:
                if entry_expectation is not pinned_entry_expectation:
                    raise error_new(error_class, "model_owner_changed")
                for bank_cell, original_bank in entry_expectation:
                    if cell_get(bank_cell) is not original_bank:
                        raise error_new(error_class, "model_owner_changed")
                if code_get(_actual_guard) is not guard_code:
                    raise error_new(error_class, "model_owner_changed")
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
            except base_error:
                row[1].clear()
                for key, record in tuple_type(items(row[2])):
                    put(row[2], key, (record[0], None, None))
                row[3].add("*")
                raise
            row = (
                _actual_current_owner
                if _native_code(_actual_current_owner)
                is _native_dictionary_get(
                    call_codes, _native_identify(_actual_current_owner)
                )
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(self)
            try:
                coordinates = tuple_type(
                    (
                        _actual_token
                        if _native_code(_actual_token)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_token)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )(v)
                    for v in (
                        model_ref,
                        model_revision_ref,
                        root_type_ref,
                        projection_ref,
                    )
                )
                if (
                    kind(lifetime_ms) is not integer
                    or lifetime_ms < 1
                    or lifetime_ms > 30000
                    or (kind(topology_bytes) is not byte_type)
                    or (not topology_bytes)
                    or (length(topology_bytes) > 1048576)
                ):
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_appointment_invalid")
                for key, record in tuple_type(items(row[2])):
                    if deref(record[0]) is None:
                        pop(row[2], key)
                if length(row[2]) >= handle_limit or model_ref in row[3]:
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_capacity_or_retired")
                (
                    _actual_admit_schema
                    if _native_code(_actual_admit_schema)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_admit_schema)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )(bundle_bytes, slice_bytes, root_type_ref)
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                definition = (*coordinates, bundle_bytes, slice_bytes, topology_bytes)
                old = get_dict(row[1], model_ref)
                if old is not None and old != definition:
                    (
                        _actual_clear_model
                        if _native_code(_actual_clear_model)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_clear_model)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )(row, model_ref)
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_revision_changed")
                if old is None and length(row[1]) + length(row[3]) >= model_limit:
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_capacity_unavailable")
                original = owner_definitions[identify(self)]
                admission_body = {
                    "contract": contract,
                    "profile": profile,
                    "owner_ref": original[0],
                    "owner_generation": original[1],
                    "source_definition_ref": original[2],
                    "model_ref": model_ref,
                    "model_revision_ref": model_revision_ref,
                    "root_type_ref": root_type_ref,
                    "projection_ref": projection_ref,
                    "schema_bundle_hex": byte_type.hex(bundle_bytes),
                    "schema_slice_hex": byte_type.hex(slice_bytes),
                    "topology_hex": byte_type.hex(topology_bytes),
                }
                rendered = (
                    _actual_canonical
                    if _native_code(_actual_canonical)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_canonical)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )(admission_body)
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                admission = text.encode(rendered, "utf-8")
                added = length(admission) + (
                    length(bundle_bytes) + length(slice_bytes) + length(topology_bytes)
                    if old is None
                    else 0
                )
                if (
                    _actual_capacity
                    if _native_code(_actual_capacity)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_capacity)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )() + added > retained_limit:
                    (
                        _actual_fail
                        if _native_code(_actual_fail)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_fail)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )("model_retained_capacity_unavailable")
                started = _actual_now()
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                evidence = evidence_new(
                    evidence_class,
                    (
                        *original,
                        *coordinates,
                        bundle_bytes,
                        slice_bytes,
                        topology_bytes,
                        admission,
                        started + lifetime_ms / 1000,
                    ),
                )
                handle = object_new(ModelHandle)
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                put(row[1], model_ref, definition if old is None else old)
                put(
                    row[2],
                    identify(handle),
                    (weak(handle), row[1][model_ref], evidence),
                )
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                return handle
            except base_error:
                try:
                    (
                        _actual_guard
                        if _native_code(_actual_guard)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_guard)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )()
                except base_error:
                    row[1].clear()
                    for key, record in tuple_type(items(row[2])):
                        put(row[2], key, (record[0], None, None))
                    row[3].add("*")
                raise

        def verify(self, handle):
            if primitives is not pinned_primitives:
                _refusal_type: Any = ().__class__.__class__
                _refusal_dict: Any = {}.__class__
                _refusal_tuple: Any = ().__class__
                _refusal_set: Any = {0}.__class__
                if _refusal_type(owners) is _refusal_dict:
                    for _refusal_row in _refusal_dict.values(owners):
                        if (
                            _refusal_type(_refusal_row) is _refusal_tuple
                            and _refusal_tuple.__len__(_refusal_row) == 4
                        ):
                            if _refusal_type(_refusal_row[1]) is _refusal_dict:
                                _refusal_dict.clear(_refusal_row[1])
                            if _refusal_type(_refusal_row[2]) is _refusal_dict:
                                for (
                                    _refusal_key,
                                    _refusal_record,
                                ) in _refusal_dict.items(_refusal_row[2]):
                                    if (
                                        _refusal_type(_refusal_record) is _refusal_tuple
                                        and _refusal_tuple.__len__(_refusal_record) == 3
                                    ):
                                        _refusal_dict.__setitem__(
                                            _refusal_row[2],
                                            _refusal_key,
                                            (_refusal_record[0], None, None),
                                        )
                            if _refusal_type(_refusal_row[3]) is _refusal_set:
                                _refusal_set.add(_refusal_row[3], "*")
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            identify = _native_envelope[1]
            get_dict = _native_envelope[3]
            put = _native_envelope[4]
            items = _native_envelope[6]
            cell_get = _native_envelope[10]
            code_get = _native_envelope[11]
            deref = _native_envelope[16]
            error_new = _native_envelope[17]
            error_class = _native_envelope[19]
            tuple_type = _native_envelope[20]
            _actual_guard = guard
            _actual_verify_local_model = verify_local_model
            row = get_dict(owners, identify(self))
            if row is None or deref(row[0]) is not self:
                raise error_new(error_class, "model_owner_changed")
            try:
                if entry_expectation is not pinned_entry_expectation:
                    raise error_new(error_class, "model_owner_changed")
                for bank_cell, original_bank in entry_expectation:
                    if cell_get(bank_cell) is not original_bank:
                        raise error_new(error_class, "model_owner_changed")
                if code_get(_actual_guard) is not guard_code:
                    raise error_new(error_class, "model_owner_changed")
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                result = (
                    _actual_verify_local_model
                    if _native_code(_actual_verify_local_model)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_verify_local_model)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )(self, handle)
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
                return result
            except base_error:
                try:
                    if entry_expectation is not pinned_entry_expectation:
                        raise error_new(error_class, "model_owner_changed")
                    for bank_cell, original_bank in entry_expectation:
                        if cell_get(bank_cell) is not original_bank:
                            raise error_new(error_class, "model_owner_changed")
                    if code_get(_actual_guard) is not guard_code:
                        raise error_new(error_class, "model_owner_changed")
                    (
                        _actual_guard
                        if _native_code(_actual_guard)
                        is _native_dictionary_get(
                            call_codes, _native_identify(_actual_guard)
                        )
                        else (_unused for _unused in ()).throw(
                            _native_error_new(
                                _native_error_class, "model_owner_changed"
                            )
                        )
                    )()
                except base_error:
                    row[1].clear()
                    for key, record in tuple_type(items(row[2])):
                        put(row[2], key, (record[0], None, None))
                    row[3].add("*")
                raise

        def release(self, handle):
            if primitives is not pinned_primitives:
                _refusal_type: Any = ().__class__.__class__
                _refusal_dict: Any = {}.__class__
                _refusal_tuple: Any = ().__class__
                _refusal_set: Any = {0}.__class__
                if _refusal_type(owners) is _refusal_dict:
                    for _refusal_row in _refusal_dict.values(owners):
                        if (
                            _refusal_type(_refusal_row) is _refusal_tuple
                            and _refusal_tuple.__len__(_refusal_row) == 4
                        ):
                            if _refusal_type(_refusal_row[1]) is _refusal_dict:
                                _refusal_dict.clear(_refusal_row[1])
                            if _refusal_type(_refusal_row[2]) is _refusal_dict:
                                for (
                                    _refusal_key,
                                    _refusal_record,
                                ) in _refusal_dict.items(_refusal_row[2]):
                                    if (
                                        _refusal_type(_refusal_record) is _refusal_tuple
                                        and _refusal_tuple.__len__(_refusal_record) == 3
                                    ):
                                        _refusal_dict.__setitem__(
                                            _refusal_row[2],
                                            _refusal_key,
                                            (_refusal_record[0], None, None),
                                        )
                            if _refusal_type(_refusal_row[3]) is _refusal_set:
                                _refusal_set.add(_refusal_row[3], "*")
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            identify = _native_envelope[1]
            get_dict = _native_envelope[3]
            put = _native_envelope[4]
            items = _native_envelope[6]
            cell_get = _native_envelope[10]
            code_get = _native_envelope[11]
            deref = _native_envelope[16]
            error_new = _native_envelope[17]
            error_class = _native_envelope[19]
            tuple_type = _native_envelope[20]
            _actual_guard = guard
            row = get_dict(owners, identify(self))
            if row is None or deref(row[0]) is not self:
                raise error_new(error_class, "model_owner_changed")
            record = get_dict(row[2], identify(handle))
            if record is None or deref(record[0]) is not handle:
                raise error_new(error_class, "model_owner_changed")
            put(row[2], identify(handle), (record[0], None, None))
            try:
                if entry_expectation is not pinned_entry_expectation:
                    raise error_new(error_class, "model_owner_changed")
                for bank_cell, original_bank in entry_expectation:
                    if cell_get(bank_cell) is not original_bank:
                        raise error_new(error_class, "model_owner_changed")
                if code_get(_actual_guard) is not guard_code:
                    raise error_new(error_class, "model_owner_changed")
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
            except base_error:
                row[1].clear()
                for key, old_record in tuple_type(items(row[2])):
                    put(row[2], key, (old_record[0], None, None))
                row[3].add("*")
                raise

        def retire_model(self, model_ref):
            if primitives is not pinned_primitives:
                _refusal_type: Any = ().__class__.__class__
                _refusal_dict: Any = {}.__class__
                _refusal_tuple: Any = ().__class__
                _refusal_set: Any = {0}.__class__
                if _refusal_type(owners) is _refusal_dict:
                    for _refusal_row in _refusal_dict.values(owners):
                        if (
                            _refusal_type(_refusal_row) is _refusal_tuple
                            and _refusal_tuple.__len__(_refusal_row) == 4
                        ):
                            if _refusal_type(_refusal_row[1]) is _refusal_dict:
                                _refusal_dict.clear(_refusal_row[1])
                            if _refusal_type(_refusal_row[2]) is _refusal_dict:
                                for (
                                    _refusal_key,
                                    _refusal_record,
                                ) in _refusal_dict.items(_refusal_row[2]):
                                    if (
                                        _refusal_type(_refusal_record) is _refusal_tuple
                                        and _refusal_tuple.__len__(_refusal_record) == 3
                                    ):
                                        _refusal_dict.__setitem__(
                                            _refusal_row[2],
                                            _refusal_key,
                                            (_refusal_record[0], None, None),
                                        )
                            if _refusal_type(_refusal_row[3]) is _refusal_set:
                                _refusal_set.add(_refusal_row[3], "*")
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            identify = _native_envelope[1]
            get_dict = _native_envelope[3]
            put = _native_envelope[4]
            items = _native_envelope[6]
            cell_get = _native_envelope[10]
            code_get = _native_envelope[11]
            deref = _native_envelope[16]
            error_new = _native_envelope[17]
            error_class = _native_envelope[19]
            tuple_type = _native_envelope[20]
            _actual_clear_model = clear_model
            _actual_current_owner = current_owner
            _actual_fail = fail
            _actual_guard = guard
            _actual_token = token
            row = get_dict(owners, identify(self))
            if row is None or deref(row[0]) is not self:
                raise error_new(error_class, "model_owner_changed")
            try:
                if entry_expectation is not pinned_entry_expectation:
                    raise error_new(error_class, "model_owner_changed")
                for bank_cell, original_bank in entry_expectation:
                    if cell_get(bank_cell) is not original_bank:
                        raise error_new(error_class, "model_owner_changed")
                if code_get(_actual_guard) is not guard_code:
                    raise error_new(error_class, "model_owner_changed")
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
            except base_error:
                row[1].clear()
                for key, record in tuple_type(items(row[2])):
                    put(row[2], key, (record[0], None, None))
                row[3].add("*")
                raise
            row = (
                _actual_current_owner
                if _native_code(_actual_current_owner)
                is _native_dictionary_get(
                    call_codes, _native_identify(_actual_current_owner)
                )
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(self)
            (
                _actual_token
                if _native_code(_actual_token)
                is _native_dictionary_get(call_codes, _native_identify(_actual_token))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(model_ref)
            if model_ref not in row[1] and model_ref not in row[3]:
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_not_appointed")
            (
                _actual_clear_model
                if _native_code(_actual_clear_model)
                is _native_dictionary_get(
                    call_codes, _native_identify(_actual_clear_model)
                )
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(row, model_ref)
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()

        def close(self):
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            identify = _native_envelope[1]
            get_dict = _native_envelope[3]
            put = _native_envelope[4]
            items = _native_envelope[6]
            deref = _native_envelope[16]
            error_new = _native_envelope[17]
            error_class = _native_envelope[19]
            tuple_type = _native_envelope[20]
            row = get_dict(owners, identify(self))
            if row is None or deref(row[0]) is not self:
                raise error_new(error_class, "model_owner_changed")
            row[1].clear()
            for key, record in tuple_type(items(row[2])):
                put(row[2], key, (record[0], None, None))
            row[3].add("*")

    def validate_local_model_owner(owner) -> None:
        if primitives is not pinned_primitives:
            _refusal_type: Any = ().__class__.__class__
            _refusal_dict: Any = {}.__class__
            _refusal_tuple: Any = ().__class__
            _refusal_set: Any = {0}.__class__
            if _refusal_type(owners) is _refusal_dict:
                for _refusal_row in _refusal_dict.values(owners):
                    if (
                        _refusal_type(_refusal_row) is _refusal_tuple
                        and _refusal_tuple.__len__(_refusal_row) == 4
                    ):
                        if _refusal_type(_refusal_row[1]) is _refusal_dict:
                            _refusal_dict.clear(_refusal_row[1])
                        if _refusal_type(_refusal_row[2]) is _refusal_dict:
                            for _refusal_key, _refusal_record in _refusal_dict.items(
                                _refusal_row[2]
                            ):
                                if (
                                    _refusal_type(_refusal_record) is _refusal_tuple
                                    and _refusal_tuple.__len__(_refusal_record) == 3
                                ):
                                    _refusal_dict.__setitem__(
                                        _refusal_row[2],
                                        _refusal_key,
                                        (_refusal_record[0], None, None),
                                    )
                        if _refusal_type(_refusal_row[3]) is _refusal_set:
                            _refusal_set.add(_refusal_row[3], "*")
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        identify = _native_envelope[1]
        get_dict = _native_envelope[3]
        put = _native_envelope[4]
        items = _native_envelope[6]
        cell_get = _native_envelope[10]
        code_get = _native_envelope[11]
        deref = _native_envelope[16]
        error_new = _native_envelope[17]
        error_class = _native_envelope[19]
        tuple_type = _native_envelope[20]
        _actual_current_owner = current_owner
        _actual_guard = guard
        row = get_dict(owners, identify(owner))
        if row is None or deref(row[0]) is not owner:
            raise error_new(error_class, "model_owner_changed")
        try:
            if entry_expectation is not pinned_entry_expectation:
                raise error_new(error_class, "model_owner_changed")
            for bank_cell, original_bank in entry_expectation:
                if cell_get(bank_cell) is not original_bank:
                    raise error_new(error_class, "model_owner_changed")
            if code_get(_actual_guard) is not guard_code:
                raise error_new(error_class, "model_owner_changed")
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            row = (
                _actual_current_owner
                if _native_code(_actual_current_owner)
                is _native_dictionary_get(
                    call_codes, _native_identify(_actual_current_owner)
                )
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(owner)
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            return
        except base_error:
            try:
                if entry_expectation is not pinned_entry_expectation:
                    raise error_new(error_class, "model_owner_changed")
                for bank_cell, original_bank in entry_expectation:
                    if cell_get(bank_cell) is not original_bank:
                        raise error_new(error_class, "model_owner_changed")
                if code_get(_actual_guard) is not guard_code:
                    raise error_new(error_class, "model_owner_changed")
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
            except base_error:
                row[1].clear()
                for key, record in tuple_type(items(row[2])):
                    put(row[2], key, (record[0], None, None))
                row[3].add("*")
            raise

    def verify_local_model(owner, handle) -> LocalReadModelEvidence:
        if primitives is not pinned_primitives:
            _refusal_type: Any = ().__class__.__class__
            _refusal_dict: Any = {}.__class__
            _refusal_tuple: Any = ().__class__
            _refusal_set: Any = {0}.__class__
            if _refusal_type(owners) is _refusal_dict:
                for _refusal_row in _refusal_dict.values(owners):
                    if (
                        _refusal_type(_refusal_row) is _refusal_tuple
                        and _refusal_tuple.__len__(_refusal_row) == 4
                    ):
                        if _refusal_type(_refusal_row[1]) is _refusal_dict:
                            _refusal_dict.clear(_refusal_row[1])
                        if _refusal_type(_refusal_row[2]) is _refusal_dict:
                            for _refusal_key, _refusal_record in _refusal_dict.items(
                                _refusal_row[2]
                            ):
                                if (
                                    _refusal_type(_refusal_record) is _refusal_tuple
                                    and _refusal_tuple.__len__(_refusal_record) == 3
                                ):
                                    _refusal_dict.__setitem__(
                                        _refusal_row[2],
                                        _refusal_key,
                                        (_refusal_record[0], None, None),
                                    )
                        if _refusal_type(_refusal_row[3]) is _refusal_set:
                            _refusal_set.add(_refusal_row[3], "*")
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        identify = _native_envelope[1]
        get_dict = _native_envelope[3]
        put = _native_envelope[4]
        items = _native_envelope[6]
        cell_get = _native_envelope[10]
        code_get = _native_envelope[11]
        deref = _native_envelope[16]
        error_new = _native_envelope[17]
        error_class = _native_envelope[19]
        tuple_type = _native_envelope[20]
        now = _native_envelope[35]
        _actual_current_owner = current_owner
        _actual_fail = fail
        _actual_guard = guard
        _actual_now = now
        _actual_original_handle = original_handle
        row = get_dict(owners, identify(owner))
        if row is None or deref(row[0]) is not owner:
            raise error_new(error_class, "model_owner_changed")
        try:
            if entry_expectation is not pinned_entry_expectation:
                raise error_new(error_class, "model_owner_changed")
            for bank_cell, original_bank in entry_expectation:
                if cell_get(bank_cell) is not original_bank:
                    raise error_new(error_class, "model_owner_changed")
            if code_get(_actual_guard) is not guard_code:
                raise error_new(error_class, "model_owner_changed")
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            row = (
                _actual_current_owner
                if _native_code(_actual_current_owner)
                is _native_dictionary_get(
                    call_codes, _native_identify(_actual_current_owner)
                )
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(owner)
            record = (
                _actual_original_handle
                if _native_code(_actual_original_handle)
                is _native_dictionary_get(
                    call_codes, _native_identify(_actual_original_handle)
                )
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(row, handle)
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            if record[2] is None:
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_handle_retired")
            evidence = record[2]
            instant = _actual_now()
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            if (
                get_dict(row[1], evidence[3]) is not record[1]
                or instant >= evidence[11]
            ):
                put(row[2], identify(handle), (record[0], None, None))
                (
                    _actual_fail
                    if _native_code(_actual_fail)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_fail)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )("model_facts_expired")
            (
                _actual_guard
                if _native_code(_actual_guard)
                is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )()
            return evidence
        except base_error:
            try:
                if entry_expectation is not pinned_entry_expectation:
                    raise error_new(error_class, "model_owner_changed")
                for bank_cell, original_bank in entry_expectation:
                    if cell_get(bank_cell) is not original_bank:
                        raise error_new(error_class, "model_owner_changed")
                if code_get(_actual_guard) is not guard_code:
                    raise error_new(error_class, "model_owner_changed")
                (
                    _actual_guard
                    if _native_code(_actual_guard)
                    is _native_dictionary_get(
                        call_codes, _native_identify(_actual_guard)
                    )
                    else (_unused for _unused in ()).throw(
                        _native_error_new(_native_error_class, "model_owner_changed")
                    )
                )()
            except base_error:
                row[1].clear()
                for key, record in tuple_type(items(row[2])):
                    put(row[2], key, (record[0], None, None))
                row[3].add("*")
            raise

    def create_local_model_owner(*, owner_ref, owner_generation, source_definition_ref):
        if primitives is not pinned_primitives:
            _refusal_type: Any = ().__class__.__class__
            _refusal_dict: Any = {}.__class__
            _refusal_tuple: Any = ().__class__
            _refusal_set: Any = {0}.__class__
            if _refusal_type(owners) is _refusal_dict:
                for _refusal_row in _refusal_dict.values(owners):
                    if (
                        _refusal_type(_refusal_row) is _refusal_tuple
                        and _refusal_tuple.__len__(_refusal_row) == 4
                    ):
                        if _refusal_type(_refusal_row[1]) is _refusal_dict:
                            _refusal_dict.clear(_refusal_row[1])
                        if _refusal_type(_refusal_row[2]) is _refusal_dict:
                            for _refusal_key, _refusal_record in _refusal_dict.items(
                                _refusal_row[2]
                            ):
                                if (
                                    _refusal_type(_refusal_record) is _refusal_tuple
                                    and _refusal_tuple.__len__(_refusal_record) == 3
                                ):
                                    _refusal_dict.__setitem__(
                                        _refusal_row[2],
                                        _refusal_key,
                                        (_refusal_record[0], None, None),
                                    )
                        if _refusal_type(_refusal_row[3]) is _refusal_set:
                            _refusal_set.add(_refusal_row[3], "*")
            (0).__class__("model_owner_changed")
        _native_envelope: Any = primitives
        _native_cell = _native_envelope[10]
        _native_code = _native_envelope[11]
        _native_dictionary_get = _native_envelope[3]
        _native_identify = _native_envelope[1]
        _native_error_new = _native_envelope[17]
        _native_error_class = _native_envelope[19]
        identify = _native_envelope[1]
        length = _native_envelope[2]
        put = _native_envelope[4]
        pop = _native_envelope[5]
        items = _native_envelope[6]
        cell_get = _native_envelope[10]
        code_get = _native_envelope[11]
        weak = _native_envelope[15]
        deref = _native_envelope[16]
        error_new = _native_envelope[17]
        error_class = _native_envelope[19]
        tuple_type = _native_envelope[20]
        set_type = _native_envelope[23]
        object_new = _native_envelope[31]
        pid = _native_envelope[33]
        thread = _native_envelope[34]
        _actual_fail = fail
        _actual_guard = guard
        _actual_pid = pid
        _actual_thread = thread
        _actual_token = token
        if entry_expectation is not pinned_entry_expectation:
            raise error_new(error_class, "model_owner_changed")
        for bank_cell, original_bank in entry_expectation:
            if cell_get(bank_cell) is not original_bank:
                raise error_new(error_class, "model_owner_changed")
        if code_get(_actual_guard) is not guard_code:
            raise error_new(error_class, "model_owner_changed")
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        values = tuple_type(
            (
                _actual_token
                if _native_code(_actual_token)
                is _native_dictionary_get(call_codes, _native_identify(_actual_token))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )(v)
            for v in (owner_ref, owner_generation, source_definition_ref)
        )
        if _actual_pid() != original_pid or _actual_thread() != original_thread:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_owner_context_changed")
        for key, row in tuple_type(items(owners)):
            if deref(row[0]) is None:
                pop(owners, key)
                pop(owner_definitions, key, None)
        if length(owners) >= owner_limit:
            (
                _actual_fail
                if _native_code(_actual_fail)
                is _native_dictionary_get(call_codes, _native_identify(_actual_fail))
                else (_unused for _unused in ()).throw(
                    _native_error_new(_native_error_class, "model_owner_changed")
                )
            )("model_capacity_unavailable")
        owner = object_new(LocalReadModelOwner)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        put(owners, identify(owner), (weak(owner), {}, {}, set_type()))
        put(owner_definitions, identify(owner), values)
        (
            _actual_guard
            if _native_code(_actual_guard)
            is _native_dictionary_get(call_codes, _native_identify(_actual_guard))
            else (_unused for _unused in ()).throw(
                _native_error_new(_native_error_class, "model_owner_changed")
            )
        )()
        return owner

    def seal():
        nonlocal \
            live_classes, \
            source_functions, \
            source_data, \
            own_entries, \
            sealed, \
            entry_expectation, \
            pinned_entry_expectation
        if sealed:
            raise error_new(error_class, "model_owner_changed")
        own_entries = tuple_type(items(own_namespace))
        classes = (ModelHandle, LocalReadModelOwner, evidence_class, hash_kind)
        live_classes = tuple_type(
            (
                cls,
                kind(cls),
                raw_bases(cls),
                raw_mro(cls),
                tuple_type(proxy_items(raw_dict(cls))),
            )
            for cls in classes
        )
        pending = [
            fail,
            fingerprint,
            guard,
            token,
            decode,
            exact,
            digest,
            admit_schema,
            clear_model,
            terminal,
            original_owner,
            original_handle,
            current_owner,
            capacity,
            validate_local_model_owner,
            verify_local_model,
            create_local_model_owner,
            canonical,
        ]
        for cls in (ModelHandle, LocalReadModelOwner, evidence_class):
            for _, value in proxy_items(raw_dict(cls)):
                if kind(value) is function_type:
                    pending.append(value)
        for module, _, entries in banks:
            for _, value in entries:
                if kind(value) is function_type:
                    pending.append(value)
        rows, seen = ([], set_type())
        while pending:
            fn = list_type.pop(pending)
            if identify(fn) in seen:
                continue
            seen.add(identify(fn))
            closure = closure_get(fn)
            cells = tuple_type(
                (
                    (cell, cell_get(cell))
                    for name, cell in zipping(
                        code_get(fn).co_freevars, closure or (), strict=True
                    )
                    if name
                    not in (
                        "entry_expectation",
                        "pinned_entry_expectation",
                        "primitives",
                        "pinned_primitives",
                        "primitive_cells",
                        "pinned_primitive_cells",
                    )
                    and (
                        fn is not guard
                        or name
                        not in (
                            "live_classes",
                            "source_functions",
                            "source_data",
                            "own_entries",
                            "sealed",
                        )
                    )
                )
            )
            rows.append(
                (
                    fn,
                    code_get(fn),
                    defaults_get(fn),
                    keywords_get(fn),
                    (closure, cells),
                    tuple_type(
                        (name, get(fn, name))
                        for name in (
                            "__name__",
                            "__qualname__",
                            "__module__",
                            "__annotations__",
                            "__dict__",
                        )
                    ),
                )
            )
            for _, value in cells:
                if kind(value) is function_type:
                    pending.append(value)
        for row in rows:
            put(call_codes, identify(row[0]), row[1])
        source_functions = tuple_type(rows)
        retained, data_seen = ([], set_type())

        def retain(value):
            if primitives is not pinned_primitives:
                (0).__class__("model_owner_changed")
            _native_envelope: Any = primitives
            _native_cell = _native_envelope[10]
            _native_code = _native_envelope[11]
            _native_dictionary_get = _native_envelope[3]
            _native_identify = _native_envelope[1]
            _native_error_new = _native_envelope[17]
            _native_error_class = _native_envelope[19]
            kind = _native_envelope[0]
            identify = _native_envelope[1]
            items = _native_envelope[6]
            tuple_type = _native_envelope[20]
            list_type = _native_envelope[21]
            dictionary = _native_envelope[22]
            set_type = _native_envelope[23]
            frozen_type = _native_envelope[24]
            value_kind = kind(value)
            if (
                value_kind
                not in (dictionary, tuple_type, list_type, set_type, frozen_type)
                or identify(value) in data_seen
            ):
                return
            data_seen.add(identify(value))
            retained.append((value, value_kind, fingerprint(value)))
            contents = (
                (v for pair in items(value) for v in pair)
                if value_kind is dictionary
                else value
            )
            for child in contents:
                retain(child)

        for fn, _, defaults, keywords, _, attributes in source_functions:
            retain(defaults)
            retain(keywords)
            for _, value in attributes:
                retain(value)
        for _, _, _, _, entries in live_classes:
            for _, value in entries:
                retain(value)
        retain(call_codes)
        source_data = tuple_type(retained)
        sealed = True
        entry_expectation = tuple_type(
            (
                (cell, cell_get(cell))
                for name, cell in zipping(
                    code_get(guard).co_freevars, closure_get(guard), strict=True
                )
                if name
                in (
                    "live_classes",
                    "source_functions",
                    "source_data",
                    "own_entries",
                    "sealed",
                )
            )
        )
        pinned_entry_expectation = entry_expectation

    return (
        create_local_model_owner,
        validate_local_model_owner,
        verify_local_model,
        seal,
    )


create_local_model_owner, validate_local_model_owner, verify_local_model, _seal = (
    _build_local_model_api()
)
_seal()
