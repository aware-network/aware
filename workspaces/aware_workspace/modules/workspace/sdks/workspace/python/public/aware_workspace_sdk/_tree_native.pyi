from types import NotImplementedType
from typing import Any

def new_context() -> object: ...
def seal(context: object, declaration: tuple[Any, ...]) -> None: ...
def verify(context: object) -> None: ...
def convert_root(
    context: object,
    annotation: type[Any],
    value: object,
    field_name: str,
    depth: int,
) -> dict[str, Any] | NotImplementedType: ...
def new_receipt_context() -> object: ...
def seal_receipts(context: object, declaration: tuple[Any, ...]) -> None: ...
def convert_receipt(
    context: object,
    value: object,
    entry: tuple[Any, ...],
    registry: dict[int, Any],
    hints: dict[str, Any],
) -> dict[str, Any] | NotImplementedType: ...
def receipt_prelude(
    context: object,
    annotation: object,
    registry: object,
    original: object,
    entries: object,
) -> tuple[dict[int, Any], tuple[Any, ...]] | NotImplementedType: ...
def make_index_formatter(
    json_module: object,
    encoder_module: object,
    ascii_profile: int,
    nan_profile: int,
    budget: int,
) -> object | None: ...
def call_index_formatter(
    context: object,
    callee: object,
    payload: object,
    json_module: object,
) -> str: ...
def index_formatter_stats(context: object) -> dict[str, int]: ...

INDEX_FORMATTER_ABI: int

TREE_FORMATTER_ABI: int

def call_tree_formatter(
    context: object,
    callee: object,
    payload: object,
    json_module: object,
    keyword_names: object = ...,
) -> str: ...

RECEIPT_DIRECT_RECORD_ABI: int

def receipt_graph_stats() -> dict[str, int]: ...
def make_preparation_copy(
    known: tuple[type, ...],
    counts: tuple[int, ...],
    atomic: set[type] | frozenset[type],
    fields: object,
    walk: object,
    converters: tuple[object, ...],
    unknown: object,
) -> object: ...
def copy_preparation(context: object, value: object) -> object: ...

OWNER_FORMATTER_ABI: int

ASCII_PATH_POSITIVE_ABI: int

def ascii_path_positive(value: object, maximum: object, /) -> bool: ...

INDEX_BYTES_DELTA_ABI: int

def index_bytes_delta(previous: bytes, current: bytes, /) -> bytes | None: ...

ASCII_PATH_BATCH_ABI: int

def ascii_paths_last(
    context: object, effects: object, payload: object, limits: object, /
) -> str | None: ...
