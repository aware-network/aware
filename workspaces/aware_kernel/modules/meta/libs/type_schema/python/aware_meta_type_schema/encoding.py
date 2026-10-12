from __future__ import annotations

import _json
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

type JsonScalar = None | bool | int | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


class TypeSchemaEncodingError(ValueError):
    pass


def normalize_json(value: object, *, path: str = "$") -> JsonValue:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise TypeSchemaEncodingError(
            f"{path} uses float; decimals must use canonical strings"
        )
    if isinstance(value, (list, tuple)):
        return [
            normalize_json(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, JsonValue] = {}
        if any(not isinstance(key, str) or not key for key in value):
            raise TypeSchemaEncodingError(f"{path} keys must be non-empty strings")
        for key in sorted(value):
            result[key] = normalize_json(value[key], path=f"{path}.{key}")
        return result
    raise TypeSchemaEncodingError(
        f"{path} has unsupported value {type(value).__name__}"
    )


def canonical_json(value: object) -> str:
    return json.dumps(
        normalize_json(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _make_origin_native_canonical_encoder() -> Callable[[object], str]:
    """Retain the native backend already used by the ordinary canonical encoder.

    This is a private prerequisite for the protected Origin entrance, not that
    entrance. Its eventual owner guard must authenticate this function and its
    retained closure before dispatch. No Python JSON constructor, renderer,
    callback or recursive normalizer is dispatched inside this helper.
    """
    # Recover the fixed native hierarchy independently of writable aliases or
    # retained expectation cells. CPython's immutable-type flag excludes heap
    # lookalikes before raw name/module inspection; no descriptor is resolved.
    refusal_kind: Any = ().__class__.__class__
    refusal_dict = refusal_kind.__dict__["__dict__"].__get__
    refusal_mro = refusal_kind.__dict__["__mro__"].__get__
    refusal_flags = refusal_kind.__dict__["__flags__"].__get__
    refusal_name = refusal_kind.__dict__["__name__"].__get__
    refusal_module = refusal_kind.__dict__["__module__"].__get__
    refusal_subclasses = refusal_kind.__dict__["__subclasses__"]
    refusal_type = refusal_mro(().__class__)[-1]
    for required_name in ("BaseException", "Exception", "ValueError"):
        for candidate in refusal_subclasses(refusal_type):
            if (
                refusal_kind(candidate) is refusal_kind
                and refusal_flags(candidate) & 256
                and refusal_module(candidate) == "builtins"
                and refusal_name(candidate) == required_name
            ):
                refusal_type = candidate
                break
    # The admitted CPython image supplies this immutable native hierarchy.
    # Its BaseException slots allocate only the authenticated native ValueError.
    refusal_slots = refusal_dict(refusal_mro(refusal_type)[-2])
    new_error, init_error = refusal_slots["__new__"], refusal_slots["__init__"]
    encoder_class = _json.make_encoder
    # Call the genuine native descriptors themselves: type.__getattribute__
    # would still resolve a substituted descriptor before returning its value.
    class_dict = type.__dict__["__dict__"].__get__
    class_mro = type.__dict__["__mro__"].__get__
    proxy_items = MappingProxyType.items
    original_mro = class_mro(encoder_class)
    original_members = []
    for member in ("__new__", "__call__", "__init__"):
        found = False
        for base in original_mro:
            for key, raw in proxy_items(class_dict(base)):
                if type(key) is not str:
                    error = new_error(refusal_type)
                    init_error(error, "origin_native_backend_changed")
                    raise error
                if key == member:
                    original_members.append((member, raw))
                    found = True
                    break
            if found:
                break
        if not found:
            error = new_error(refusal_type)
            init_error(error, "origin_native_backend_changed")
            raise error
    guarded_members = tuple(original_members)
    encoder_new: Callable[..., _json.make_encoder] = guarded_members[0][1]
    encoder_call = guarded_members[1][1]
    quote = _json.encode_basestring
    native_type = type
    native_dict = dict
    native_list = list
    native_str = str
    native_int = int
    native_bool = bool
    native_none = type(None)
    native_set = set
    native_enumerate = enumerate
    dict_items = dict.items
    list_iter = list.__iter__
    list_append = list.append
    list_pop = list.pop
    dict_set = dict.__setitem__
    list_set = list.__setitem__
    set_add = set.add
    set_remove = set.remove
    native_id = id
    native_join = str.join
    error_class = refusal_type
    error_new = new_error
    error_init = init_error

    def encode(value: object) -> str:
        # Copy every capability into this invocation before any traversal. The
        # caller's containers never reach the native encoder or a callback.
        kind_of, dict_type, list_type = native_type, native_dict, native_list
        str_type, int_type, bool_type, none_type = (
            native_str,
            native_int,
            native_bool,
            native_none,
        )
        items, iterate, append, pop = dict_items, list_iter, list_append, list_pop
        put_dict, put_list = dict_set, list_set
        add, remove, identify, join = set_add, set_remove, native_id, native_join
        make_set, enumerate_native = native_set, native_enumerate
        new_encoder, call_encoder, encoder_type, escape = (
            encoder_new,
            encoder_call,
            encoder_class,
            quote,
        )
        get_class_dict, get_class_mro, raw_items = class_dict, class_mro, proxy_items
        initial_mro, initial_members = original_mro, guarded_members
        # Recover the fixed native hierarchy independently of writable aliases or
        # retained expectation cells. CPython's immutable-type flag excludes heap
        # lookalikes before raw name/module inspection; no descriptor is resolved.
        refusal_kind: Any = ().__class__.__class__
        refusal_dict = refusal_kind.__dict__["__dict__"].__get__
        refusal_mro = refusal_kind.__dict__["__mro__"].__get__
        refusal_flags = refusal_kind.__dict__["__flags__"].__get__
        refusal_name = refusal_kind.__dict__["__name__"].__get__
        refusal_module = refusal_kind.__dict__["__module__"].__get__
        refusal_subclasses = refusal_kind.__dict__["__subclasses__"]
        refusal_type = refusal_mro(().__class__)[-1]
        for required_name in ("BaseException", "Exception", "ValueError"):
            for candidate in refusal_subclasses(refusal_type):
                if (
                    refusal_kind(candidate) is refusal_kind
                    and refusal_flags(candidate) & 256
                    and refusal_module(candidate) == "builtins"
                    and refusal_name(candidate) == required_name
                ):
                    refusal_type = candidate
                    break
        # The admitted CPython image supplies this immutable native hierarchy.
        # Its BaseException slots allocate only the authenticated native ValueError.
        refusal_slots = refusal_dict(refusal_mro(refusal_type)[-2])
        new_error, init_error = refusal_slots["__new__"], refusal_slots["__init__"]
        if (
            error_class is not refusal_type
            or error_new is not new_error
            or error_init is not init_error
        ):
            error = new_error(refusal_type)
            init_error(error, "origin_owner_changed")
            raise error
        root: list[object] = [None]
        # False tasks assign a value; True tasks remove a container from the
        # active ancestor set. Repeated, noncyclic references remain valid.
        tasks: list[tuple[bool, object, object, object, int]] = [
            (False, value, root, 0, 0)
        ]
        active: set[int] = make_set()
        while tasks:
            leaving, current, destination, slot, depth = pop(tasks)
            if leaving:
                remove(active, identify(current))
                continue
            current_type = kind_of(current)
            if (
                current_type is none_type
                or current_type is bool_type
                or current_type is int_type
                or current_type is str_type
            ):
                copied = current
            elif current_type is dict_type or current_type is list_type:
                if depth >= 64 or identify(current) in active:
                    error = new_error(refusal_type)
                    init_error(error, "origin_native_data_limit")
                    raise error
                add(active, identify(current))
                append(tasks, (True, current, destination, slot, depth))
                if current_type is dict_type:
                    copied = {}
                    for key, child in items(current):
                        if kind_of(key) is not str_type or not key:
                            error = new_error(refusal_type)
                            init_error(error, "origin_native_data_invalid")
                            raise error
                        append(tasks, (False, child, copied, key, depth + 1))
                else:
                    copied = []
                    for index, child in enumerate_native(iterate(current)):
                        append(copied, None)
                        append(tasks, (False, child, copied, index, depth + 1))
            else:
                error = new_error(refusal_type)
                init_error(error, "origin_native_data_invalid")
                raise error
            if kind_of(destination) is dict_type:
                put_dict(destination, slot, copied)
            else:
                put_list(destination, slot, copied)

        # Call the retained native descriptors directly. _json.Encoder itself
        # is a mutable heap type; retaining only that type would still permit a
        # replacement __new__ or __call__ to run. None is the fixed unreachable
        # default callback: all encoder operands have already been exact-admitted.
        current_mro = get_class_mro(encoder_type)
        if current_mro is not initial_mro:
            error = new_error(refusal_type)
            init_error(error, "origin_native_backend_changed")
            raise error
        for member, expected in initial_members:
            found = False
            for base in current_mro:
                for key, raw in raw_items(get_class_dict(base)):
                    # Admit keys before equality; neither this iteration nor
                    # the comparison resolves a stored descriptor value.
                    if kind_of(key) is not str_type:
                        error = new_error(refusal_type)
                        init_error(error, "origin_native_backend_changed")
                        raise error
                    if key == member:
                        if raw is not expected:
                            error = new_error(refusal_type)
                            init_error(error, "origin_native_backend_changed")
                            raise error
                        found = True
                        break
                if found:
                    break
            if not found:
                error = new_error(refusal_type)
                init_error(error, "origin_native_backend_changed")
                raise error
        encoder = new_encoder(
            encoder_type, {}, None, escape, None, ":", ",", True, False, False
        )
        chunks = call_encoder(encoder, root[0], 0)
        return join("", chunks)

    return encode


_canonical_json_native_for_origin = _make_origin_native_canonical_encoder()


def digest_payload(contract: str, payload: object) -> str:
    if not isinstance(contract, str) or not contract or contract.strip() != contract:
        raise TypeSchemaEncodingError("contract must be a non-empty token")
    encoded = f"{contract}\n{canonical_json(payload)}".encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True, slots=True)
class FrozenJson:
    canonical: str

    def __post_init__(self) -> None:
        if not isinstance(self.canonical, str):
            raise TypeError("FrozenJson.canonical must be str")
        try:
            value = json.loads(self.canonical)
        except (TypeError, ValueError) as error:
            raise TypeSchemaEncodingError("FrozenJson is invalid JSON") from error
        if canonical_json(value) != self.canonical:
            raise TypeSchemaEncodingError("FrozenJson must be canonical")

    @classmethod
    def from_value(cls, value: object) -> FrozenJson:
        return cls(canonical_json(value))

    def to_wire(self) -> JsonValue:
        canonical = self.canonical
        # Only exact plain-string literals bypass the established decoder.
        # Read the current string and allocate mutable containers on every call.
        if type(canonical) is str:
            if canonical == "{}":
                return {}
            if canonical == "[]":
                return []
            if canonical == "null":
                return None
            if canonical == "true":
                return True
            if canonical == "false":
                return False
            if canonical == "0":
                return 0
        return normalize_json(json.loads(canonical))
