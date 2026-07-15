"""Code-owned section/segment capability registry."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aware_code.section.annotation.segments import CodeSectionAnnotationSegment
from aware_code.section.attribute.segments import CodeSectionAttributeSegment
from aware_code.section.class_.segments import CodeSectionClassSegment
from aware_code.section.decorator.segments import CodeSectionDecoratorSegment
from aware_code.section.enum.segments import CodeSectionEnumSegment
from aware_code.section.function.segments import CodeSectionFunctionSegment
from aware_code.section.import_.segments import CodeSectionImportSegment
from aware_code.section.mirror.segments import CodeSectionMirrorSegment


CODE_SECTION_SEGMENT_REGISTRY_AUTHORITY = "aware_code.section_segment_registry"


@dataclass(frozen=True, slots=True)
class CodeSectionSegmentCapability:
    """Resolvable segment names for one Code section type."""

    section_type: str
    segment_names: tuple[str, ...]
    resolver_key: str
    authority: str = CODE_SECTION_SEGMENT_REGISTRY_AUTHORITY
    is_builtin: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "section_type", self.section_type.strip())
        object.__setattr__(
            self,
            "segment_names",
            tuple(sorted({name.strip() for name in self.segment_names if name.strip()})),
        )
        object.__setattr__(self, "resolver_key", self.resolver_key.strip())
        object.__setattr__(self, "authority", self.authority.strip())
        if not self.section_type:
            raise ValueError("section_type is required.")
        if not self.segment_names:
            raise ValueError("segment_names must include at least one segment.")
        if not self.resolver_key:
            raise ValueError("resolver_key is required.")
        if not self.authority:
            raise ValueError("authority is required.")

    def supports_segment(self, segment_name: str) -> bool:
        return segment_name.strip() in self.segment_names


class CodeSectionSegmentCapabilityRegistry:
    """Registry for Code-owned section/segment resolver capabilities."""

    def __init__(
        self,
        capabilities: Iterable[CodeSectionSegmentCapability],
    ) -> None:
        normalized = tuple(
            sorted(
                capabilities,
                key=lambda item: item.section_type,
            )
        )
        seen: set[str] = set()
        duplicate_section_types: list[str] = []
        for capability in normalized:
            if capability.section_type in seen:
                duplicate_section_types.append(capability.section_type)
            seen.add(capability.section_type)
        if duplicate_section_types:
            duplicates = ", ".join(sorted(set(duplicate_section_types)))
            raise ValueError(
                "Duplicate Code section-segment capability registrations: "
                f"{duplicates}."
            )
        self._capabilities = {
            capability.section_type: capability
            for capability in normalized
        }

    def with_capabilities(
        self,
        capabilities: Iterable[CodeSectionSegmentCapability],
    ) -> "CodeSectionSegmentCapabilityRegistry":
        return CodeSectionSegmentCapabilityRegistry(
            capabilities=(*self._capabilities.values(), *tuple(capabilities)),
        )

    def capability_for_section_type(
        self,
        section_type: str,
    ) -> CodeSectionSegmentCapability | None:
        return self._capabilities.get(section_type.strip())

    def supported_section_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._capabilities))

    def supported_segment_names(self, section_type: str) -> tuple[str, ...]:
        capability = self.capability_for_section_type(section_type)
        if capability is None:
            return ()
        return capability.segment_names

    def supports_segment(self, *, section_type: str, segment_name: str) -> bool:
        capability = self.capability_for_section_type(section_type)
        return capability is not None and capability.supports_segment(segment_name)


def built_in_code_section_segment_capabilities() -> tuple[CodeSectionSegmentCapability, ...]:
    """Return built-in Code segment resolver capabilities.

    This registry intentionally lists only segments that Code can currently
    resolve as durable `ContentPartTextSegment` values. Function
    `description_comment` resolves through the attached doc comment content
    segment; `is_async` remains excluded because it is not stored as an
    individual segment.
    """

    return (
        CodeSectionSegmentCapability(
            section_type="annotation",
            resolver_key="aware_code.section.annotation",
            segment_names=(
                CodeSectionAnnotationSegment.ARGS.value,
                CodeSectionAnnotationSegment.PATH.value,
                CodeSectionAnnotationSegment.RAW.value,
                CodeSectionAnnotationSegment.VERB.value,
            ),
        ),
        CodeSectionSegmentCapability(
            section_type="attribute",
            resolver_key="aware_code.section.attribute",
            segment_names=(
                CodeSectionAttributeSegment.DEFAULT_VALUE.value,
                CodeSectionAttributeSegment.NAME.value,
                CodeSectionAttributeSegment.TYPE.value,
            ),
        ),
        CodeSectionSegmentCapability(
            section_type="class",
            resolver_key="aware_code.section.class",
            segment_names=(
                CodeSectionClassSegment.KEYWORD.value,
                CodeSectionClassSegment.MODIFIERS.value,
                CodeSectionClassSegment.NAME.value,
                CodeSectionClassSegment.DESCRIPTION_COMMENT.value,
            ),
        ),
        CodeSectionSegmentCapability(
            section_type="decorator",
            resolver_key="aware_code.section.decorator",
            segment_names=(CodeSectionDecoratorSegment.NAME.value,),
        ),
        CodeSectionSegmentCapability(
            section_type="enum",
            resolver_key="aware_code.section.enum",
            segment_names=(CodeSectionEnumSegment.NAME.value,),
        ),
        CodeSectionSegmentCapability(
            section_type="function",
            resolver_key="aware_code.section.function",
            segment_names=(
                CodeSectionFunctionSegment.BODY.value,
                CodeSectionFunctionSegment.DESCRIPTION_COMMENT.value,
                CodeSectionFunctionSegment.NAME.value,
                CodeSectionFunctionSegment.RETURN_TYPE.value,
                CodeSectionFunctionSegment.SIGNATURE.value,
            ),
        ),
        CodeSectionSegmentCapability(
            section_type="import",
            resolver_key="aware_code.section.import",
            segment_names=(CodeSectionImportSegment.MODULE.value,),
        ),
        CodeSectionSegmentCapability(
            section_type="mirror",
            resolver_key="aware_code.section.mirror",
            segment_names=(CodeSectionMirrorSegment.TARGET.value,),
        ),
    )


DEFAULT_CODE_SECTION_SEGMENT_CAPABILITY_REGISTRY = (
    CodeSectionSegmentCapabilityRegistry(
        capabilities=built_in_code_section_segment_capabilities(),
    )
)


__all__ = [
    "CODE_SECTION_SEGMENT_REGISTRY_AUTHORITY",
    "CodeSectionSegmentCapability",
    "CodeSectionSegmentCapabilityRegistry",
    "DEFAULT_CODE_SECTION_SEGMENT_CAPABILITY_REGISTRY",
    "built_in_code_section_segment_capabilities",
]
