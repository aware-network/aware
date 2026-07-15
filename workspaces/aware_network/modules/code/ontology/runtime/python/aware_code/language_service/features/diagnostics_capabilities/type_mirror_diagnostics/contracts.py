from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter


class TypeMirrorPluginContract(Protocol):
    primitive_codec: CodePrimitiveCodec
    type_descriptor_adapter: CodeTypeDescriptorAdapter


TypeMirrorSuggestFn = Callable[[str, list[str]], list[str]]
