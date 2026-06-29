from aware_meta.graph.config.render.layout_strategy_template import (
    ObjectConfigGraphRenderLayoutStrategyTemplate,
)
from typing_extensions import override

# Code
from aware_code_ontology.code.code_enums import CodeLanguage


class AwareLayoutStrategy(ObjectConfigGraphRenderLayoutStrategyTemplate):
    """
    Layout strategy for Aware language files.

    Organizes files according to Aware conventions:
    - types/: Contains all type definitions
    - edges/: Contains all edge definitions
    - enums/: Contains all enum definitions
    - functions/: Contains global functions
    """

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.aware

    @override
    def get_file_extension(self) -> str:
        return ".aware"
