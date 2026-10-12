"""Protected owner-local Origin entrances.

Only canonical encoding is implemented in this checkpoint. The remaining
profile ports require their own complete reachable-dispatch proofs.
"""

from __future__ import annotations

import builtins
import sys
from collections.abc import Callable
from types import CellType, FunctionType, ModuleType
from typing import Any

from . import encoding


def _install_canonical_entrance() -> Callable[[object], str]:
    # Bootstrap belongs to the authenticated source/import closure. Runtime
    # dispatch never obtains its verifier or encoder from a writable binding.
    owner = encoding
    owner_namespace: Any = vars(owner)
    owner_bindings = tuple(owner_namespace.items())
    encoder = encoding._canonical_json_native_for_origin
    encoder_cells = tuple(
        (cell, cell.cell_contents) for cell in encoder.__closure__ or ()
    )
    encoder_defaults = encoder.__defaults__
    encoder_kwdefaults = encoder.__kwdefaults__
    builtins_namespace: Any = vars(builtins)
    builtins_bindings = tuple(builtins_namespace.items())
    system = sys
    system_namespace: Any = vars(system)
    registry = sys.modules
    owner_name = owner.__name__
    backend = encoding._json
    backend_namespace: Any = vars(backend)
    backend_bindings = tuple(backend_namespace.items())
    native_module_type = ModuleType
    native_function_type = FunctionType
    native_cell_type = CellType
    error_class = ValueError

    def canonical_json_for_origin(value: object) -> str:
        # Native immutable type dictionaries provide these primitives afresh.
        # No retained Python verifier is dispatched, and no writable module
        # global participates in this invocation's checks.
        # Stubs model this reflective __class__ access as a property. Runtime
        # capability identity is native; Any is confined to raw introspection.
        kind: Any = ().__class__.__class__
        text_type, tuple_type, bytes_type = "".__class__, ().__class__, b"".__class__
        int_type, bool_type, none_type = (0).__class__, True.__class__, None.__class__
        dictionary_type = {}.__class__
        items = dictionary_type.items
        get: Any = dictionary_type.get
        function_type = native_function_type
        module_type: Any = native_module_type
        retained_encoder = encoder
        retained_cells = encoder_cells
        retained_defaults, retained_kwdefaults = encoder_defaults, encoder_kwdefaults
        retained_owner, retained_namespace = owner, owner_namespace
        retained_bindings = owner_bindings
        retained_builtins, retained_builtin_bindings = (
            builtins_namespace,
            builtins_bindings,
        )
        retained_system, retained_system_namespace = system, system_namespace
        retained_registry, retained_owner_name = registry, owner_name
        retained_backend, retained_backend_namespace = backend, backend_namespace
        retained_backend_bindings = backend_bindings
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
        class_mro = kind.__dict__["__mro__"].__get__
        class_dict = kind.__dict__["__dict__"].__get__
        if error_class is not refusal_type:
            error = new_error(refusal_type)
            init_error(error, "origin_owner_changed")
            raise error
        cell_type = native_cell_type
        if kind(retained_cells) is not tuple_type:
            error = new_error(refusal_type)
            init_error(error, "origin_owner_changed")
            raise error
        for row in retained_cells:
            if (
                kind(row) is not tuple_type
                or row.__len__() != 2
                or kind(row[0]) is not cell_type
            ):
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error

        result = ""
        # Keep verification inline: a mutable verifier binding or its return
        # cannot create another unauthenticated dispatch boundary.
        for after_encoding in (False, True):
            if after_encoding:
                result = retained_encoder(value)
            # Admit *all* keys before get/equality. A retained native dict.get
            # would otherwise still execute a foreign key's equality method.
            for namespace in (
                retained_namespace,
                retained_backend_namespace,
                retained_builtins,
                retained_system_namespace,
                retained_registry,
            ):
                if kind(namespace) is not dictionary_type:
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
                for key in items(namespace):
                    if kind(key[0]) is not text_type:
                        error = new_error(refusal_type)
                        init_error(error, "origin_owner_changed")
                        raise error
            if (
                kind(retained_owner) is not module_type
                or kind(retained_system) is not module_type
                or get(retained_system_namespace, "modules") is not retained_registry
                or get(retained_registry, retained_owner_name) is not retained_owner
                or kind(retained_backend) is not module_type
                or get(retained_registry, "_json") is not retained_backend
            ):
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error
            for namespace, bindings in (
                (retained_namespace, retained_bindings),
                (retained_backend_namespace, retained_backend_bindings),
                (retained_builtins, retained_builtin_bindings),
            ):
                if kind(bindings) is not tuple_type:
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
                if namespace.__len__() != bindings.__len__():
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
                for row in bindings:
                    if (
                        kind(row) is not tuple_type
                        or row.__len__() != 2
                        or kind(row[0]) is not text_type
                    ):
                        error = new_error(refusal_type)
                        init_error(error, "origin_owner_changed")
                        raise error
                expected_names = []
                for name, _ in bindings:
                    expected_names.append(name)
                for name, _ in items(namespace):
                    if name not in expected_names:
                        error = new_error(refusal_type)
                        init_error(error, "origin_owner_changed")
                        raise error
                for name, expected in bindings:
                    if get(namespace, name) is not expected:
                        error = new_error(refusal_type)
                        init_error(error, "origin_owner_changed")
                        raise error
            if kind(retained_encoder) is not function_type:
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error
            code = retained_encoder.__code__
            # Fixed executable coordinates are literal constants in the
            # executing entrance. Restamping code plus a retained expectation
            # cannot authorize a replacement. Location metadata is excluded.
            actual = (
                code.co_argcount,
                code.co_posonlyargcount,
                code.co_kwonlyargcount,
                code.co_nlocals,
                code.co_stacksize,
                code.co_flags,
                code.co_code,
                code.co_consts,
                code.co_names,
                code.co_varnames,
                code.co_freevars,
                code.co_cellvars,
                code.co_exceptiontable,
            )
            # Do not compare nested constants until their exact native types
            # are admitted: CodeType.replace can insert a foreign constant.
            pending: list[Any] = [actual]
            while pending:
                current = pending.pop()
                current_type = kind(current)
                if current_type is tuple_type:
                    pending.extend(current)
                elif (
                    current_type is not text_type
                    and current_type is not bytes_type
                    and current_type is not int_type
                    and current_type is not bool_type
                    and current_type is not none_type
                ):
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
            if actual != (
                1,
                0,
                0,
                64,
                12,
                16777235,
                b"\x95\x1f\x97\x00\x89Y\x89P\x89U}\x03}\x02}\x01\x89X\x89S\x89O\x89Vf\x04\\\x04\x00\x00}\x04}\x05}\x06}\x07\x89B\x89L\x89K\x89Mf\x04\\\x04\x00\x00}\x08}\t}\n}\x0b\x89C\x89N}\r}\x0c\x89]\x89^\x89R\x89Tf\x04\\\x04\x00\x00}\x0e}\x0f}\x10}\x11\x89W\x89Q}\x13}\x12\x89F\x89D\x89E\x89\\f\x04\\\x04\x00\x00}\x14}\x15}\x16}\x17\x89@\x89A\x89[}\x1a}\x19}\x18\x89Z\x89J}\x1c}\x1bd\x01j\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00}\x1d|\x1dj\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x02\x19\x00\x00\x00j\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00}\x1e|\x1dj\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x03\x19\x00\x00\x00j\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00}\x1f|\x1dj\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x04\x19\x00\x00\x00j\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00} |\x1dj\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x05\x19\x00\x00\x00j\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00}!|\x1dj\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x06\x19\x00\x00\x00j\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00}\"|\x1dj\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x07\x19\x00\x00\x00}#\x02\x00|\x1fd\x01j\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00d\x08\x19\x00\x00\x00}$d\tD\x00]A\x00\x00}%\x02\x00|#|$\xab\x01\x00\x00\x00\x00\x00\x00D\x00]4\x00\x00}&\x02\x00|\x1d|&\xab\x01\x00\x00\x00\x00\x00\x00|\x1du\x00s\x01\x8c\x0e\x02\x00| |&\xab\x01\x00\x00\x00\x00\x00\x00d\nz\x01\x00\x00s\x01\x8c\x1a\x02\x00|\"|&\xab\x01\x00\x00\x00\x00\x00\x00d\x0bk(\x00\x00s\x01\x8c&\x02\x00|!|&\xab\x01\x00\x00\x00\x00\x00\x00|%k(\x00\x00s\x01\x8c2|&}$\x01\x00\x8cA\x04\x00\x8cC\x04\x00\x02\x00|\x1e\x02\x00|\x1f|$\xab\x01\x00\x00\x00\x00\x00\x00d\x0c\x19\x00\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00}'|'d\r\x19\x00\x00\x00|'d\x0e\x19\x00\x00\x00})}(\x89G|$u\x01s\x08\x89I|(u\x01s\x04\x89H|)u\x01r\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x0f\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01d\x00g\x01}+d\x10|\x00|+d\x11d\x11f\x05g\x01},\x02\x00|\x12\xab\x00\x00\x00\x00\x00\x00\x00}-|,\x90\x01r2\x02\x00|\x0b|,\xab\x01\x00\x00\x00\x00\x00\x00\\\x05\x00\x00}.}/}0}1}2|.r\x10\x02\x00|\x0f|-\x02\x00|\x10|/\xab\x01\x00\x00\x00\x00\x00\x00\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00\x8c#\x02\x00|\x01|/\xab\x01\x00\x00\x00\x00\x00\x00}3|3|\x07u\x00s\x0c|3|\x06u\x00s\x08|3|\x05u\x00s\x04|3|\x04u\x00r\x03|/}4n\xd4|3|\x02u\x00s\x04|3|\x03u\x00r\xb9|2d\x12k\\\x00\x00s\n\x02\x00|\x10|/\xab\x01\x00\x00\x00\x00\x00\x00|-v\x00r\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x13\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01\x02\x00|\x0e|-\x02\x00|\x10|/\xab\x01\x00\x00\x00\x00\x00\x00\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00|\n|,d\x14|/|0|1|2f\x05\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|3|\x02u\x00rCi\x00}4\x02\x00|\x08|/\xab\x01\x00\x00\x00\x00\x00\x00D\x00]5\x00\x00\\\x02\x00\x00}5}6\x02\x00|\x01|5\xab\x01\x00\x00\x00\x00\x00\x00|\x04u\x01s\x02|5s\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x15\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01\x02\x00|\n|,d\x10|6|4|5|2d\x16z\x00\x00\x00f\x05\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00\x8c7\x04\x00nFg\x00}4\x02\x00|\x13\x02\x00|\t|/\xab\x01\x00\x00\x00\x00\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00D\x00]\x1f\x00\x00\\\x02\x00\x00}7}6\x02\x00|\n|4d\x00\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00|\n|,d\x10|6|4|7|2d\x16z\x00\x00\x00f\x05\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00\x8c!\x04\x00n\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x15\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01\x02\x00|\x01|0\xab\x01\x00\x00\x00\x00\x00\x00|\x02u\x00r\x0b\x02\x00|\x0c|0|1|4\xab\x03\x00\x00\x00\x00\x00\x00\x01\x00n\n\x02\x00|\r|0|1|4\xab\x03\x00\x00\x00\x00\x00\x00\x01\x00|,r\x02\x90\x01\x8c2\x02\x00|\x19|\x16\xab\x01\x00\x00\x00\x00\x00\x00}8|8|\x1bu\x01r\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x17\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01|\x1cD\x00]z\x00\x00\\\x02\x00\x00}9}:d\x10};|8D\x00]Y\x00\x00}<\x02\x00|\x1a\x02\x00|\x18|<\xab\x01\x00\x00\x00\x00\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00D\x00]B\x00\x00\\\x02\x00\x00}5}=\x02\x00|\x01|5\xab\x01\x00\x00\x00\x00\x00\x00|\x04u\x01r\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x17\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01|5|9k(\x00\x00s\x01\x8c)|=|:u\x01r\x13\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x17\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01d\x14};\x01\x00n\x01\x04\x00|;s\x01\x8cY\x01\x00n\x01\x04\x00|;r\x01\x8ci\x02\x00|(|$\xab\x01\x00\x00\x00\x00\x00\x00}*\x02\x00|)|*d\x17\xab\x02\x00\x00\x00\x00\x00\x00\x01\x00|*\x82\x01\x04\x00\x02\x00|\x14|\x16i\x00d\x00|\x17d\x00d\x18d\x19d\x14d\x10d\x10\xab\n\x00\x00\x00\x00\x00\x00}>\x02\x00|\x15|>|+d\x11\x19\x00\x00\x00d\x11\xab\x03\x00\x00\x00\x00\x00\x00}?\x02\x00|\x11d\x1a|?\xab\x02\x00\x00\x00\x00\x00\x00S\x00",
                (
                    None,
                    (),
                    "__dict__",
                    "__mro__",
                    "__flags__",
                    "__name__",
                    "__module__",
                    "__subclasses__",
                    -1,
                    ("BaseException", "Exception", "ValueError"),
                    256,
                    "builtins",
                    -2,
                    "__new__",
                    "__init__",
                    "origin_owner_changed",
                    False,
                    0,
                    64,
                    "origin_native_data_limit",
                    True,
                    "origin_native_data_invalid",
                    1,
                    "origin_native_backend_changed",
                    ":",
                    ",",
                    "",
                ),
                ("__class__", "__dict__", "__get__"),
                (
                    "value",
                    "kind_of",
                    "dict_type",
                    "list_type",
                    "str_type",
                    "int_type",
                    "bool_type",
                    "none_type",
                    "items",
                    "iterate",
                    "append",
                    "pop",
                    "put_dict",
                    "put_list",
                    "add",
                    "remove",
                    "identify",
                    "join",
                    "make_set",
                    "enumerate_native",
                    "new_encoder",
                    "call_encoder",
                    "encoder_type",
                    "escape",
                    "get_class_dict",
                    "get_class_mro",
                    "raw_items",
                    "initial_mro",
                    "initial_members",
                    "refusal_kind",
                    "refusal_dict",
                    "refusal_mro",
                    "refusal_flags",
                    "refusal_name",
                    "refusal_module",
                    "refusal_subclasses",
                    "refusal_type",
                    "required_name",
                    "candidate",
                    "refusal_slots",
                    "new_error",
                    "init_error",
                    "error",
                    "root",
                    "tasks",
                    "active",
                    "leaving",
                    "current",
                    "destination",
                    "slot",
                    "depth",
                    "current_type",
                    "copied",
                    "key",
                    "child",
                    "index",
                    "current_mro",
                    "member",
                    "expected",
                    "found",
                    "base",
                    "raw",
                    "encoder",
                    "chunks",
                ),
                (
                    "class_dict",
                    "class_mro",
                    "dict_items",
                    "dict_set",
                    "encoder_call",
                    "encoder_class",
                    "encoder_new",
                    "error_class",
                    "error_init",
                    "error_new",
                    "guarded_members",
                    "list_append",
                    "list_iter",
                    "list_pop",
                    "list_set",
                    "native_bool",
                    "native_dict",
                    "native_enumerate",
                    "native_id",
                    "native_int",
                    "native_join",
                    "native_list",
                    "native_none",
                    "native_set",
                    "native_str",
                    "native_type",
                    "original_mro",
                    "proxy_items",
                    "quote",
                    "set_add",
                    "set_remove",
                ),
                (),
                b"",
            ):
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error
            if (
                retained_encoder.__globals__ is not retained_namespace
                or retained_encoder.__defaults__ is not retained_defaults
                or retained_encoder.__kwdefaults__ is not retained_kwdefaults
                or retained_encoder.__closure__ is None
                or retained_encoder.__closure__.__len__() != retained_cells.__len__()
            ):
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error
            native_encoder_class = get(retained_backend_namespace, "make_encoder")
            native_quote = get(retained_backend_namespace, "encode_basestring")
            native_identify = get(retained_builtins, "id")
            native_enumerator = get(retained_builtins, "enumerate")
            if (
                kind(native_encoder_class) is not kind
                or kind(native_quote) is not kind(new_error)
                or native_quote.__name__ != "encode_basestring"
                or native_quote.__self__ is not retained_backend
                or kind(native_identify) is not kind(new_error)
                or native_identify.__name__ != "id"
                or kind(native_identify.__self__) is not module_type
                or module_type.__dict__["__dict__"].__get__(native_identify.__self__)
                is not retained_builtins
                or kind(native_enumerator) is not kind
            ):
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error
            native_mro = class_mro(native_encoder_class)
            native_members = []
            for member in ("__new__", "__call__", "__init__"):
                found = False
                for base in native_mro:
                    raw_namespace = class_dict(base)
                    for key in raw_namespace:
                        if kind(key) is not text_type:
                            error = new_error(refusal_type)
                            init_error(error, "origin_owner_changed")
                            raise error
                    for key, raw in raw_namespace.items():
                        if key == member:
                            # Native slots may not be restamped into Python
                            # functions/descriptors, even with an updated table.
                            native_slot_type = (
                                kind(new_error)
                                if member == "__new__"
                                else kind(init_error)
                            )
                            if kind(raw) is not native_slot_type:
                                error = new_error(refusal_type)
                                init_error(error, "origin_owner_changed")
                                raise error
                            if member == "__new__":
                                genuine_receiver = raw.__self__ is native_encoder_class
                            else:
                                expected_receiver = (
                                    native_encoder_class
                                    if member == "__call__"
                                    else native_mro[-1]
                                )
                                genuine_receiver = raw.__objclass__ is expected_receiver
                            if raw.__name__ != member or not genuine_receiver:
                                error = new_error(refusal_type)
                                init_error(error, "origin_owner_changed")
                                raise error
                            native_members.append((member, raw))
                            found = True
                            break
                    if found:
                        break
                if not found:
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
            enumeration_namespace = class_dict(native_enumerator)
            for key in enumeration_namespace:
                if kind(key) is not text_type:
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
            enumeration_new = enumeration_namespace.get("__new__")
            if (
                kind(enumeration_new) is not kind(new_error)
                or enumeration_new.__self__ is not native_enumerator
                or kind.__dict__["__name__"].__get__(native_enumerator) != "enumerate"
            ):
                error = new_error(refusal_type)
                init_error(error, "origin_owner_changed")
                raise error
            set_type = {*()}.__class__
            native_capabilities = {
                "class_dict": class_dict,
                "class_mro": class_mro,
                "dict_items": dictionary_type.items,
                "dict_set": dictionary_type.__setitem__,
                "encoder_call": native_members[1][1],
                "encoder_class": native_encoder_class,
                "encoder_new": native_members[0][1],
                "error_class": refusal_type,
                "error_init": init_error,
                "error_new": new_error,
                "list_append": [].__class__.append,
                "list_iter": [].__class__.__iter__,
                "list_pop": [].__class__.pop,
                "list_set": [].__class__.__setitem__,
                "native_bool": bool_type,
                "native_dict": dictionary_type,
                "native_enumerate": native_enumerator,
                "native_id": native_identify,
                "native_int": int_type,
                "native_join": text_type.join,
                "native_list": [].__class__,
                "native_none": none_type,
                "native_set": set_type,
                "native_str": text_type,
                "native_type": kind,
                "proxy_items": kind(class_dict(kind)).items,
                "quote": native_quote,
                "set_add": set_type.add,
                "set_remove": set_type.remove,
            }
            index = 0
            while index < retained_cells.__len__():
                cell, expected = retained_cells[index]
                if (
                    retained_encoder.__closure__[index] is not cell
                    or cell.cell_contents is not expected
                ):
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
                name = code.co_freevars[index]
                current_value = cell.cell_contents
                if name == "original_mro":
                    valid = current_value is native_mro
                elif name == "guarded_members":
                    valid = kind(current_value) is tuple_type
                    if valid:
                        valid = current_value.__len__() == native_members.__len__()
                    if valid:
                        member_index = 0
                        for row in current_value:
                            if (
                                kind(row) is not tuple_type
                                or row.__len__() != 2
                                or kind(row[0]) is not text_type
                                or row[0] != native_members[member_index][0]
                                or row[1] is not native_members[member_index][1]
                            ):
                                valid = False
                                break
                            member_index += 1  # noqa: SIM113 -- no ambient enumerate
                elif name == "class_dict" or name == "class_mro":
                    expected_native = native_capabilities[name]
                    # Inspect the native wrapper receiver and slot name by
                    # identity/native text; never compare bound receivers.
                    valid = (
                        kind(current_value) is kind(expected_native)
                        and current_value.__self__ is expected_native.__self__
                        and current_value.__name__ == expected_native.__name__
                    )
                else:
                    valid = current_value is native_capabilities[name]
                if not valid:
                    error = new_error(refusal_type)
                    init_error(error, "origin_owner_changed")
                    raise error
                index += 1

        if kind(result) is not text_type:
            error = new_error(refusal_type)
            init_error(error, "origin_owner_changed")
            raise error
        return result

    return canonical_json_for_origin


canonical_json_for_origin = _install_canonical_entrance()
