"""Definition-time wiring for the optional descriptive metadata converter.

The context contains declarations only. It cannot admit an operation, read a
source, spend an approval, execute a provider or publish any retained result.
"""

from __future__ import annotations

import sys
import types
from typing import Any


def prepare(namespace: dict[str, Any]) -> tuple[Any, ...] | None:
    # Unregistered source clones keep the portable implementation. A normal
    # import binds one original module before any operational factory is used.
    module = sys.modules.get(namespace["__name__"])
    if type(module) is not types.ModuleType or vars(module) is not namespace:
        return None
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        return None
    try:
        # Authored C plus its .pyi is built into an optional extension image.
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        # The extension is optional; unsupported/absent binaries use the same
        # portable codec. Build/installed qualification reports its own image.
        return None
    return (
        _tree_native.new_context(),
        _tree_native.convert_root,
        _tree_native.verify,
        _tree_native.seal,
    )


def seal(namespace: dict[str, Any], handoff: tuple[Any, ...] | None) -> None:
    if handoff is None:
        return
    # Bind only a genuine optional pure intrinsic into immutable code constants.
    # The receiving C sealer authenticates that exact tagged slot against itself.
    conversion = handoff[1]
    if type(conversion) is types.BuiltinFunctionType:
        module = conversion.__self__
        if type(module) is types.ModuleType:
            exports = vars(module)
            if all(type(key) is str for key in exports):
                abi = exports.get("ASCII_PATH_POSITIVE_ABI")
                method = exports.get("ascii_path_positive")
                if (
                    type(abi) is int
                    and abi == 2
                    and type(method) is types.BuiltinFunctionType
                    and method.__self__ is module
                    and method.__name__ == "ascii_path_positive"
                ):
                    function = namespace["_path"]
                    constants = tuple(
                        (value[0], method)
                        if type(value) is tuple
                        and len(value) == 2
                        and type(value[0]) is str
                        and value[0] == "__workspace_ascii_path_slot_v2__"
                        and value[1] is None
                        else value
                        for value in function.__code__.co_consts
                    )
                    function.__code__ = function.__code__.replace(co_consts=constants)
    names = (
        "_validate",
        "_path",
        "_native_record_fields",
        "_sequence",
        "_wire",
        "_refuse",
        "repository_workflow_source_value_from_payload",
        "_convert",
    )
    functions = tuple(
        (
            name,
            function,
            function.__code__,
            function.__defaults__,
            function.__kwdefaults__,
            tuple(function.__kwdefaults__.items())
            if function.__kwdefaults__ is not None
            else None,
        )
        for name in names
        for function in (namespace[name],)
    )
    registry_names = (
        "_DEFINITIONS_BY_ID",
        "_NATIVE_FIELDS_BY_ID",
        "_NATIVE_ORIGINALS_BY_ID",
        "_FIELD_CHECKS_BY_ID",
        "_HINT_SHAPES",
        "_COLLECTION_LIMITS",
    )
    registries = tuple((name, namespace[name]) for name in registry_names)
    records = tuple(
        (
            cls,
            definitions,
            namespace["_NATIVE_FIELDS_BY_ID"][id(cls)],
            namespace["_FIELD_CHECKS_BY_ID"][id(cls)],
            id(cls),
            namespace["_DEFINITIONS_BY_ID"][id(cls)],
        )
        for cls, definitions in namespace["_DEFINITIONS"]
    )
    values = namespace["values"]
    # Native positive-only leaf predicates recognize these exact field orders;
    # uncertain/invalid data is checked by the original Python validator.
    special = (
        values.WorkspaceTreeEntryPin,
        values.WorkspaceTreeFileTransition,
        values.WorkspaceTreeScratchEffect,
    )
    context, conversion, verification, sealing = handoff
    declaration = (
        sys.modules[namespace["__name__"]],
        records,
        functions,
        registries,
        conversion,
        verification,
        namespace["WorkspaceTreeProjectionValueError"],
        namespace["_COLLECTION_LIMITS"],
        tuple(
            (*shape, id(shape[0]), shape)
            for shape in namespace["_HINT_SHAPES"].values()
        ),
        0,
        -(2**63),
        2**64,
        (types.UnionType, namespace["Literal"]),
        values.MAX_TREE_RECEIPTS,
        "",
        values,
        special,
        tuple(cls.__name__ for cls in special),
        namespace["_DIGEST"],
        namespace["_path"].__kwdefaults__["maximum"],
        values.MAX_TREE_FILE_BYTES,
        1,
        "_DIGEST",
        "MAX_TREE_FILE_BYTES",
        "maximum",
        values.WorkspaceTreeProjectionBinding,
    )
    sealing(context, declaration)


def prepare_receipts(namespace: dict[str, Any]) -> tuple[Any, ...] | None:
    """Optional same-owner runtime field formatting, without runtime imports."""
    module = sys.modules.get(namespace["__name__"])
    if type(module) is not types.ModuleType or vars(module) is not namespace:
        return None
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        return None
    try:
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        return None
    # A tree-only image from an older supported SDK is a normal portable case.
    if type(_tree_native) is not types.ModuleType:
        return None
    exports: tuple[Any, ...] = tuple(
        vars(_tree_native).get(name)
        for name in (
            "new_receipt_context",
            "convert_receipt",
            "seal_receipts",
            "receipt_prelude",
        )
    )
    if not all(
        type(function) is types.BuiltinFunctionType
        and function.__self__ is _tree_native
        for function in exports
    ):
        return None
    factory, native, sealing, prelude = exports
    return factory(), native, sealing, prelude


def seal_receipts(namespace: dict[str, Any], handoff: tuple[Any, ...] | None) -> None:
    if handoff is None:
        return
    from dataclasses import Field, is_dataclass
    from datetime import datetime
    from enum import Enum
    from typing import get_args, get_origin

    records = []
    for entry in namespace["_RECEIPT_FIELDS_BY_ID"].values():
        definitions = entry[1]
        specs = []
        for row in definitions:
            hint = row[2]
            args = hint.__args__ if type(hint) is types.UnionType else ()
            scalar = nullable = None
            if len(args) == 2:
                selected = (
                    args[1]
                    if args[0] is type(None)
                    else (args[0] if args[1] is type(None) else None)
                )
                if selected is str or selected is int or selected is bool:
                    scalar = selected
                elif isinstance(selected, type) and (
                    selected is datetime
                    or issubclass(selected, Enum)
                    or is_dataclass(selected)
                ):
                    nullable = selected
            tuple_args = get_args(hint) if type(hint) is types.GenericAlias else ()
            primitive_tuple = (
                get_origin(hint) is tuple
                and len(tuple_args) == 2
                and tuple_args[1] is Ellipsis
                and (
                    tuple_args[0] is str
                    or tuple_args[0] is int
                    or tuple_args[0] is bool
                )
            )
            kind = (
                1
                if hint is str or hint is int or hint is bool
                else 2
                if scalar is not None
                else 3
                if nullable is not None
                else 4
                if primitive_tuple
                else 5
                if isinstance(hint, type) and issubclass(hint, Enum)
                else 6
                if hint is datetime
                else 0
            )
            specs.append(
                (kind, scalar if scalar is not None else nullable, args, tuple_args)
            )
        records.append((definitions, tuple(specs), entry[0], entry, id(entry[0])))
    import weakref

    context, native, sealing, prelude = handoff
    from functools import _lru_cache_wrapper

    from . import _tree_native  # pyright: ignore[reportMissingModuleSource]

    direct_abi = vars(_tree_native).get("RECEIPT_DIRECT_RECORD_ABI")
    original_hints = namespace.get("_type_hints")
    graph = (
        type(direct_abi) is int
        and direct_abi == 1
        and type(original_hints) is _lru_cache_wrapper
        and type(namespace.get("_encode_record_after_hints")) is types.FunctionType
    )
    original = namespace["_encode"]
    replacements = {
        "_RECEIPT_NATIVE_PRELUDE_": prelude,
        "_RECEIPT_NATIVE_CONVERT_": native,
        "_RECEIPT_NATIVE_CONTEXT_": weakref.ref(context),
    }
    constants = tuple(
        replacements.get(value, value) if type(value) is str else value
        for value in original.__code__.co_consts
    )
    assembled = types.FunctionType(
        original.__code__.replace(co_consts=constants),
        namespace,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )
    assembled.__kwdefaults__ = original.__kwdefaults__
    assembled.__annotations__ = original.__annotations__
    assembled.__qualname__ = original.__qualname__
    assembled.__module__ = original.__module__
    assembled.__doc__ = original.__doc__
    assembled.__dict__.update(original.__dict__)
    assembled.__type_params__ = original.__type_params__
    namespace["_encode"] = assembled
    if graph:
        continuation = namespace["_encode_record_after_hints"]
        continuation_constants = tuple(
            replacements.get(value, value) if type(value) is str else value
            for value in continuation.__code__.co_consts
        )
        prepared_continuation = types.FunctionType(
            continuation.__code__.replace(co_consts=continuation_constants),
            namespace,
            continuation.__name__,
            continuation.__defaults__,
            continuation.__closure__,
        )
        prepared_continuation.__annotations__ = continuation.__annotations__
        prepared_continuation.__module__ = continuation.__module__
        prepared_continuation.__qualname__ = continuation.__qualname__
        prepared_continuation.__doc__ = continuation.__doc__
        prepared_continuation.__type_params__ = continuation.__type_params__
        namespace["_encode_record_after_hints"] = prepared_continuation
    hints_extra = ()
    if graph:
        hints = namespace["_type_hints"]
        inner = hints.__wrapped__
        hints_extra = ((hints, type(hints), inner, inner.__code__, None),)
    functions = tuple(
        (name, namespace[name], namespace[name].__code__)
        for name in (
            ("_encode", "_timestamp", "_encode_record_after_hints")
            if graph
            else ("_encode", "_timestamp")
        )
    )
    sealing(
        context,
        (
            sys.modules[namespace["__name__"]],
            tuple(records),
            functions,
            (
                namespace["WorkspaceRepositoryMutationReceipt"],
                types.UnionType,
                types.GenericAlias,
                "_field_type",
                "name",
                "physical_effect",
                "value",
                "__args__",
                "__origin__",
                Field,
                None,
                vars(Field)["name"],
                vars(Field)["_field_type"],
            )
            + hints_extra,
            native,
            (
                namespace["_RECEIPT_FIELDS_BY_ID"],
                namespace["_RECEIPT_ORIGINAL_REGISTRY"],
                namespace["_RECEIPT_ORIGINAL_ENTRIES"],
            ),
            prelude,
        ),
    )


def _prepare_store_json_native() -> tuple[Any, ...] | None:
    # One shared formatting-only memo, bounded across both original stores.
    import json
    import json.encoder

    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        return None
    try:
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        return None
    if (
        type(_tree_native) is not types.ModuleType
        or vars(_tree_native).get("INDEX_FORMATTER_ABI") != 1
    ):
        return None
    exports: tuple[Any, ...] = tuple(
        vars(_tree_native).get(name)
        for name in (
            "make_index_formatter",
            "call_index_formatter",
            "index_formatter_stats",
        )
    )
    if not all(
        type(function) is types.BuiltinFunctionType
        and function.__self__ is _tree_native
        for function in exports
    ):
        return None
    factory, native, _ = exports
    context = factory(json, json.encoder, 1, 1, 16 * 1024 * 1024)
    return None if context is None else (context, native)


def bind_store_json(owner: type[Any], method_name: str) -> tuple[Any, ...] | None:
    """Assemble an existing owner's pure formatter before its code is pinned."""
    if _STORE_JSON_HANDOFF is None:
        return None
    if type(owner) is not type or type(method_name) is not str:
        raise TypeError("Original store formatter declaration required")
    original = vars(owner)[method_name]
    if type(original) is not types.FunctionType:
        raise TypeError("Original store formatting method required")
    import weakref

    if type(_STORE_JSON_HANDOFF) is not tuple or len(_STORE_JSON_HANDOFF) != 2:
        raise TypeError("Original canonical formatting handoff required")
    context, native = _STORE_JSON_HANDOFF
    if (
        type(native) is not types.BuiltinFunctionType
        or type(native.__self__) is not types.ModuleType
        or native.__name__ != "call_index_formatter"
    ):
        raise TypeError("Original canonical formatting entrance required")
    replacements = {
        "_STORE_INDEX_NATIVE_CALL_": native,
        "_STORE_INDEX_NATIVE_CONTEXT_": weakref.ref(context),
    }
    constants = tuple(
        replacements.get(value, value) if type(value) is str else value
        for value in original.__code__.co_consts
    )
    assembled = types.FunctionType(
        original.__code__.replace(co_consts=constants),
        original.__globals__,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )
    assembled.__kwdefaults__ = original.__kwdefaults__
    assembled.__annotations__ = original.__annotations__
    assembled.__qualname__ = original.__qualname__
    assembled.__module__ = original.__module__
    assembled.__doc__ = original.__doc__
    assembled.__dict__.update(original.__dict__)
    assembled.__type_params__ = original.__type_params__
    setattr(owner, method_name, assembled)
    return _STORE_JSON_HANDOFF


_STORE_JSON_HANDOFF = _prepare_store_json_native()


def bind_tree_json(namespace: dict[str, Any]) -> tuple[Any, ...] | None:
    """Bind the original tree profile before its existing converter is sealed."""
    if type(namespace) is not dict or type(namespace.get("__name__")) is not str:
        return None
    module = sys.modules.get(namespace["__name__"])
    if type(module) is not types.ModuleType or vars(module) is not namespace:
        return None
    if _STORE_JSON_HANDOFF is None:
        return None
    try:
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        return None
    if type(_tree_native) is not types.ModuleType:
        return None
    native = vars(_tree_native).get("call_tree_formatter")
    if (
        type(vars(_tree_native).get("TREE_FORMATTER_ABI")) is not int
        or _tree_native.TREE_FORMATTER_ABI != 1
        or type(native) is not types.BuiltinFunctionType
        or native.__self__ is not _tree_native
        or native.__name__ != "call_tree_formatter"
    ):
        return None
    if type(_STORE_JSON_HANDOFF) is not tuple or len(_STORE_JSON_HANDOFF) != 2:
        raise TypeError("Original shared formatting context required")
    context = _STORE_JSON_HANDOFF[0]
    original = namespace["_wire"]
    if type(original) is not types.FunctionType:
        raise TypeError("Original tree wire declaration required")
    import weakref

    replacements = {
        "_TREE_JSON_NATIVE_CALL_": native,
        "_TREE_JSON_NATIVE_CONTEXT_": weakref.ref(context),
    }
    constants = tuple(
        replacements.get(value, value) if type(value) is str else value
        for value in original.__code__.co_consts
    )
    assembled = types.FunctionType(
        original.__code__.replace(co_consts=constants),
        original.__globals__,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )
    assembled.__kwdefaults__ = original.__kwdefaults__
    assembled.__annotations__ = original.__annotations__
    assembled.__qualname__ = original.__qualname__
    assembled.__module__ = original.__module__
    assembled.__doc__ = original.__doc__
    assembled.__dict__.update(original.__dict__)
    assembled.__type_params__ = original.__type_params__
    namespace["_wire"] = assembled
    namespace["_TREE_JSON_ACTIVE"] = True
    return _STORE_JSON_HANDOFF


def prepare_preparation_copy(
    known: tuple[type[Any], ...],
    counts: tuple[int, ...],
    atomic: set[type[Any]] | frozenset[type[Any]],
    fields: Any,
    walk: Any,
    converters: tuple[Any, ...],
    unknown: Any,
) -> tuple[Any, ...] | None:
    """Bind generic detached copy declarations; never import a supplying owner."""
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        return None
    try:
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        return None
    if type(_tree_native) is not types.ModuleType:
        return None
    namespace = vars(_tree_native)
    if any(type(key) is not str for key in namespace):
        return None
    factory = namespace.get("make_preparation_copy")
    native = namespace.get("copy_preparation")
    if (
        type(factory) is not types.BuiltinFunctionType
        or factory.__self__ is not _tree_native
        or type(native) is not types.BuiltinFunctionType
        or native.__self__ is not _tree_native
    ):
        return None
    if (
        factory.__name__ != "make_preparation_copy"
        or native.__name__ != "copy_preparation"
    ):
        return None
    return factory(known, counts, atomic, fields, walk, converters, unknown), native


def bind_owner_json(
    namespace: dict[str, Any], function_name: str
) -> tuple[Any, ...] | None:
    """Bind the same pure profile before an original owner seals its functions."""
    if type(namespace) is not dict or any(type(key) is not str for key in namespace):
        return None
    if type(namespace.get("__name__")) is not str:
        return None
    module = sys.modules.get(namespace["__name__"])
    if type(module) is not types.ModuleType or vars(module) is not namespace:
        return None
    if _STORE_JSON_HANDOFF is None:
        return None
    try:
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        return None
    if type(_tree_native) is not types.ModuleType:
        return None
    native_namespace = vars(_tree_native)
    if any(type(key) is not str for key in native_namespace):
        return None
    if (
        type(native_namespace.get("OWNER_FORMATTER_ABI")) is not int
        or native_namespace["OWNER_FORMATTER_ABI"] != 1
    ):
        return None
    native = native_namespace.get("call_tree_formatter")
    if (
        type(vars(_tree_native).get("TREE_FORMATTER_ABI")) is not int
        or _tree_native.TREE_FORMATTER_ABI != 1
        or type(native) is not types.BuiltinFunctionType
        or native.__self__ is not _tree_native
        or native.__name__ != "call_tree_formatter"
    ):
        return None
    if type(_STORE_JSON_HANDOFF) is not tuple or len(_STORE_JSON_HANDOFF) != 2:
        raise TypeError("Original shared formatting context required")
    context = _STORE_JSON_HANDOFF[0]
    if type(function_name) is not str:
        raise TypeError("exact original formatter name required")
    original = namespace[function_name]
    if type(original) is not types.FunctionType:
        raise TypeError("Original tree wire declaration required")
    keyword_order = ("sort_keys", "ensure_ascii", "separators", "allow_nan")
    keyword_names = next(
        (
            value
            for value in original.__code__.co_consts
            if type(value) is tuple
            and len(value) == 4
            and all(type(item) is str for item in value)
            and value == keyword_order
        ),
        None,
    )
    if keyword_names is None:
        return None
    import weakref

    replacements = {
        "_OWNER_JSON_NATIVE_CALL_": native,
        "_OWNER_JSON_NATIVE_CONTEXT_": weakref.ref(context),
        "_OWNER_JSON_NATIVE_KEYWORDS_": keyword_names,
    }
    constants = tuple(
        replacements.get(value, value) if type(value) is str else value
        for value in original.__code__.co_consts
    )
    assembled = types.FunctionType(
        original.__code__.replace(co_consts=constants),
        original.__globals__,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )
    assembled.__kwdefaults__ = original.__kwdefaults__
    assembled.__annotations__ = original.__annotations__
    assembled.__qualname__ = original.__qualname__
    assembled.__module__ = original.__module__
    assembled.__doc__ = original.__doc__
    assembled.__dict__.update(original.__dict__)
    assembled.__type_params__ = original.__type_params__
    namespace[function_name] = assembled
    return _STORE_JSON_HANDOFF


def prepare_index_delta() -> Any:
    """Retain the original pure bytes codec; older images use FULL fallback."""
    try:
        from . import _tree_native  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        return None
    if type(_tree_native) is not types.ModuleType:
        return None
    namespace = vars(_tree_native)
    abi = namespace.get("INDEX_BYTES_DELTA_ABI")
    native = namespace.get("index_bytes_delta")
    if (
        type(abi) is not int
        or abi != 1
        or type(native) is not types.BuiltinFunctionType
        or native.__self__ is not _tree_native
        or native.__name__ != "index_bytes_delta"
    ):
        return None
    return native
