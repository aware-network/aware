// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:freezed_annotation/freezed_annotation.dart';
import 'service_diagnostic_enums.dart';

part 'service_diagnostic_model.freezed.dart';
part 'service_diagnostic_model.g.dart';

@freezed
abstract class ServiceDiagnosticEntry with _$ServiceDiagnosticEntry {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceDiagnosticEntry.def({
    required String key,
    required Object? value,
  }) = _ServiceDiagnosticEntry;

  factory ServiceDiagnosticEntry({
    required String key,
    required Object? value,
  }) {
    return _ServiceDiagnosticEntry(key: key, value: value);
  }

  factory ServiceDiagnosticEntry.fromJson(Map<String, dynamic> json) =>
      _$ServiceDiagnosticEntryFromJson(json);
}

@freezed
abstract class ServiceDiagnosticSection with _$ServiceDiagnosticSection {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceDiagnosticSection.def({
    required String title,
    @Default(const []) List<ServiceDiagnosticEntry> entries,
  }) = _ServiceDiagnosticSection;

  factory ServiceDiagnosticSection({
    required String title,
    List<ServiceDiagnosticEntry> entries = const [],
  }) {
    return _ServiceDiagnosticSection(title: title, entries: entries);
  }

  factory ServiceDiagnosticSection.fromJson(Map<String, dynamic> json) =>
      _$ServiceDiagnosticSectionFromJson(json);
}

@freezed
abstract class ServiceDiagnostic with _$ServiceDiagnostic {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceDiagnostic.def({
    required String code,
    @JsonKey(
      fromJson: ServiceDiagnosticCategoryExtension.fromJson,
      toJson: ServiceDiagnosticCategoryExtension.toJson,
    )
    required ServiceDiagnosticCategory category,
    @JsonKey(
      fromJson: ServiceDiagnosticSeverityExtension.fromJson,
      toJson: ServiceDiagnosticSeverityExtension.toJson,
    )
    required ServiceDiagnosticSeverity severity,
    required String summary,
    String? detail,
    String? hint,
    required ServiceDiagnosticSection semanticRefs,
    required ServiceDiagnosticSection invocationContext,
    required ServiceDiagnosticSection provenance,
    @JsonKey(
      fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson,
      toJson: ServiceDiagnosticResolutionStatusExtension.toJson,
    )
    required ServiceDiagnosticResolutionStatus resolutionStatus,
    ServiceDiagnosticSection? debug,
  }) = _ServiceDiagnostic;

  factory ServiceDiagnostic({
    required String code,
    required ServiceDiagnosticCategory category,
    required ServiceDiagnosticSeverity severity,
    required String summary,
    String? detail,
    String? hint,
    required ServiceDiagnosticSection semanticRefs,
    required ServiceDiagnosticSection invocationContext,
    required ServiceDiagnosticSection provenance,
    ServiceDiagnosticResolutionStatus? resolutionStatus,
    ServiceDiagnosticSection? debug,
  }) {
    return _ServiceDiagnostic(
      code: code,
      category: category,
      severity: severity,
      summary: summary,
      detail: detail,
      hint: hint,
      semanticRefs: semanticRefs,
      invocationContext: invocationContext,
      provenance: provenance,
      resolutionStatus:
          resolutionStatus ?? ServiceDiagnosticResolutionStatus.unresolved,
      debug: debug,
    );
  }

  factory ServiceDiagnostic.fromJson(Map<String, dynamic> json) =>
      _$ServiceDiagnosticFromJson({
        ...json,
        if (!json.containsKey('resolution_status'))
          'resolution_status': 'unresolved',
      });
}
