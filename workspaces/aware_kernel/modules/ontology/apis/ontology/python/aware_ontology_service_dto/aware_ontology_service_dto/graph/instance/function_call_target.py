from __future__ import annotations

# Standard
from enum import Enum


class OntologyGraphFunctionCallTarget(Enum):
    """Function-call target variants supported by the Ontology GraphOS API."""

    instance = "instance"
    opg_constructor = "opg_constructor"
