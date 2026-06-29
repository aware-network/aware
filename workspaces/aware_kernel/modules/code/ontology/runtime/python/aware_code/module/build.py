from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.module.code_module import CodeModule

from aware_code.module.schemas import CodeModuleFileInfo

# Logging
from aware_utils.logging import logger


def build_code_module(
    name: str,
    languages: list[CodeLanguage],
    code_module_file_info_list: list[CodeModuleFileInfo] | None = None,
) -> CodeModule:
    """
    Build a CodeModule directly from name and languages without tracking changes.

    Raw module->code construction is intentionally disabled under package-first
    ownership; repository bootstrap may still compute module hashes from file
    info, but CodeModule instances no longer inline code linkages here.
    """
    logger.debug(f"Building CodeModule '{name}' with languages: {[lang.value for lang in languages]}")
    if code_module_file_info_list:
        logger.debug(
            "Ignoring %s raw code file linkages while building CodeModule '%s' under package-first ownership",
            len(code_module_file_info_list),
            name,
        )
    return CodeModule(
        name=name,
        languages=languages.copy(),
    )
