from __future__ import annotations

from uuid import UUID

from aware_code_ontology.code.code_section_enums import CodeSectionType

from .collector import SemanticTokenCollector


def collect_code_section_tokens(*, collector: SemanticTokenCollector) -> None:
    code = collector.context.code

    # Imports.
    for section in code.code_sections:
        if section.type != CodeSectionType.import_:
            continue
        import_section = section.code_section_import
        if import_section is None:
            continue

        module_segment = import_section.module_segment
        collector.add_token(
            byte_start=module_segment.byte_start,
            byte_end=module_segment.byte_end,
            token_type_name="namespace",
        )
        for import_name in import_section.code_section_import_names:
            alias_segment = import_name.alias_segment
            if alias_segment is not None:
                collector.add_token(
                    byte_start=alias_segment.byte_start,
                    byte_end=alias_segment.byte_end,
                    token_type_name="namespace",
                )

    member_function_section_ids: set[UUID] = set()
    for section in code.code_sections:
        if section.type != CodeSectionType.class_:
            continue
        class_section = section.code_section_class
        if class_section is None:
            continue
        for function_section in class_section.code_section_functions:
            member_function_section_ids.add(function_section.code_section.id)

    for section in code.code_sections:
        if section.type == CodeSectionType.class_:
            class_section = section.code_section_class
            if class_section is None:
                continue

            class_name_segment = class_section.name_segment
            collector.add_token(
                byte_start=class_name_segment.byte_start,
                byte_end=class_name_segment.byte_end,
                token_type_name="class",
            )

            for class_base in class_section.code_section_class_bases:
                base_segment = class_base.segment
                collector.add_type_tokens(segment=base_segment)

            for attribute in class_section.code_section_attributes:
                attr_name_segment = attribute.name_segment
                if attr_name_segment is not None:
                    collector.add_token(
                        byte_start=attr_name_segment.byte_start,
                        byte_end=attr_name_segment.byte_end,
                        token_type_name="property",
                    )
                collector.add_type_tokens(segment=attribute.type_segment)

            for class_function in class_section.code_section_functions:
                function_name_segment = class_function.name_segment
                if function_name_segment is not None:
                    collector.add_token(
                        byte_start=function_name_segment.byte_start,
                        byte_end=function_name_segment.byte_end,
                        token_type_name="method",
                    )
                collector.add_type_tokens(segment=class_function.return_type_segment)
                for parameter in class_function.code_section_attributes:
                    parameter_name_segment = parameter.name_segment
                    if parameter_name_segment is not None:
                        collector.add_token(
                            byte_start=parameter_name_segment.byte_start,
                            byte_end=parameter_name_segment.byte_end,
                            token_type_name="parameter",
                        )
                    collector.add_type_tokens(segment=parameter.type_segment)
            continue

        if section.type == CodeSectionType.enum:
            enum_section = section.code_section_enum
            if enum_section is None:
                continue

            enum_name_segment = enum_section.name_segment
            collector.add_token(
                byte_start=enum_name_segment.byte_start,
                byte_end=enum_name_segment.byte_end,
                token_type_name="enum",
            )

            for enum_value in enum_section.code_section_enum_values:
                value_segment = enum_value.value_segment
                collector.add_token(
                    byte_start=value_segment.byte_start,
                    byte_end=value_segment.byte_end,
                    token_type_name="enumMember",
                )
            continue

        if section.type == CodeSectionType.function:
            if section.id in member_function_section_ids:
                continue

            top_level_function = section.code_section_function
            if top_level_function is None:
                continue

            function_name_segment = top_level_function.name_segment
            if function_name_segment is not None:
                collector.add_token(
                    byte_start=function_name_segment.byte_start,
                    byte_end=function_name_segment.byte_end,
                    token_type_name="function",
                )

            collector.add_type_tokens(segment=top_level_function.return_type_segment)
            for parameter in top_level_function.code_section_attributes:
                parameter_name_segment = parameter.name_segment
                if parameter_name_segment is not None:
                    collector.add_token(
                        byte_start=parameter_name_segment.byte_start,
                        byte_end=parameter_name_segment.byte_end,
                        token_type_name="parameter",
                    )
                collector.add_type_tokens(segment=parameter.type_segment)
