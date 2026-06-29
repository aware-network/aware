from typing import Protocol

from aware_orm.models.orm_model import ORMModel

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.config.overlay.payload import (
    ObjectConfigGraphOverlayPayload,
)


class OverlayBundle(Protocol):
    def load_overlay(
        self,
        language: CodeLanguage,
    ) -> ObjectConfigGraphOverlayPayload | None: ...


# Return a REPORT PER LANGUAGE via:
def get_python_overlay(
    bundle: OverlayBundle,
) -> ObjectConfigGraphOverlayPayload | None:
    # TODO: EXTEND TO HELP PROCESS MODELs per OVERLAY to CANONICALIZE.
    return bundle.load_overlay(CodeLanguage.python)


def process_model_by_overlay(bundle: OverlayBundle, model: ORMModel) -> ORMModel:
    # TODO: PROCESS MODEL BY OVERLAY TO CANONICALIZE.
    python_overlay = get_python_overlay(bundle)
    if not python_overlay:
        return model
    # TODO: Pass ORM to extra attrs and apply overlay.
    return model
