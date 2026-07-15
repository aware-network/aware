from __future__ import annotations

from .contracts import AnnotationAddDiagnostic, AnnotationVerbInput


def collect_project_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    add: AnnotationAddDiagnostic,
) -> None:
    add(
        rng=ann_input.verb_token.range,
        message=(
            "Legacy `ann ... project ...` is not supported. "
            "Declare projections via `projection { ... }` blocks."
        ),
        code="aware.annotation.deprecated",
    )
