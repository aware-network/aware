from __future__ import annotations

from aware_code.language_service.position import ByteRange

from .contracts import AnnotationVerbInput


def first_arg_or_verb_range(*, ann_input: AnnotationVerbInput) -> ByteRange:
    if ann_input.args_tokens:
        return ann_input.args_tokens[0].range
    return ann_input.verb_token.range
