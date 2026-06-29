from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.function.code_section_function import CodeSectionFunction

from aware_code.language_service.position import ByteRange
from aware_code.language_service.types import DefinitionTarget
from aware_workspace.compiler.workspace import WorkspaceSnapshot


class TargetMixin:
    _snapshot: WorkspaceSnapshot | None = None

    def _class_definition_target(self, class_cfg: ClassConfig) -> DefinitionTarget | None:
        if self._snapshot is None:
            return None
        cs = class_cfg.code_section_class
        if cs is None:
            return None
        code_id = cs.code_section.code_id
        uri = self._snapshot.uri_by_code_id.get(code_id)
        if uri is None:
            return None
        name_seg = cs.name_segment
        if name_seg.byte_start is None or name_seg.byte_end is None:
            return None
        return DefinitionTarget(uri=uri, range=ByteRange(start=name_seg.byte_start, end=name_seg.byte_end))

    def _enum_definition_target(self, enum_cfg: EnumConfig) -> DefinitionTarget | None:
        if self._snapshot is None:
            return None
        cs = enum_cfg.code_section_enum
        if cs is None:
            return None
        code_id = cs.code_section.code_id
        uri = self._snapshot.uri_by_code_id.get(code_id)
        if uri is None:
            return None
        name_seg = cs.name_segment
        if name_seg.byte_start is None or name_seg.byte_end is None:
            return None
        return DefinitionTarget(uri=uri, range=ByteRange(start=name_seg.byte_start, end=name_seg.byte_end))

    def _attribute_definition_target(self, attr: CodeSectionAttribute) -> DefinitionTarget | None:
        if self._snapshot is None:
            return None
        cs = attr.code_section
        name_seg = attr.name_segment
        if name_seg is None:
            return None
        code_id = cs.code_id
        uri = self._snapshot.uri_by_code_id.get(code_id)
        if uri is None:
            return None
        if name_seg.byte_start is None or name_seg.byte_end is None or name_seg.byte_end <= name_seg.byte_start:
            return None
        return DefinitionTarget(uri=uri, range=ByteRange(start=name_seg.byte_start, end=name_seg.byte_end))

    def _function_definition_target(self, fn: CodeSectionFunction) -> DefinitionTarget | None:
        if self._snapshot is None:
            return None
        cs = fn.code_section
        name_seg = fn.name_segment
        if name_seg is None:
            return None
        code_id = cs.code_id
        uri = self._snapshot.uri_by_code_id.get(code_id)
        if uri is None:
            return None
        if name_seg.byte_start is None or name_seg.byte_end is None or name_seg.byte_end <= name_seg.byte_start:
            return None
        return DefinitionTarget(uri=uri, range=ByteRange(start=name_seg.byte_start, end=name_seg.byte_end))

    def _enum_value_definition_target(self, val: CodeSectionEnumValue) -> DefinitionTarget | None:
        if self._snapshot is None:
            return None
        cs = val.code_section
        seg = val.value_segment
        code_id = cs.code_id
        uri = self._snapshot.uri_by_code_id.get(code_id)
        if uri is None:
            return None
        if seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
            return None
        return DefinitionTarget(uri=uri, range=ByteRange(start=seg.byte_start, end=seg.byte_end))
