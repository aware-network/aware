// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'service_diagnostic_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ServiceDiagnosticEntry _$ServiceDiagnosticEntryFromJson(
  Map<String, dynamic> json,
) => _ServiceDiagnosticEntry(key: json['key'] as String, value: json['value']);

Map<String, dynamic> _$ServiceDiagnosticEntryToJson(
  _ServiceDiagnosticEntry instance,
) => <String, dynamic>{'key': instance.key, 'value': instance.value};

_ServiceDiagnosticSection _$ServiceDiagnosticSectionFromJson(
  Map<String, dynamic> json,
) => _ServiceDiagnosticSection(
  title: json['title'] as String,
  entries:
      (json['entries'] as List<dynamic>?)
          ?.map(
            (e) => ServiceDiagnosticEntry.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$ServiceDiagnosticSectionToJson(
  _ServiceDiagnosticSection instance,
) => <String, dynamic>{
  'title': instance.title,
  'entries': instance.entries.map((e) => e.toJson()).toList(),
};

_ServiceDiagnostic _$ServiceDiagnosticFromJson(Map<String, dynamic> json) =>
    _ServiceDiagnostic(
      code: json['code'] as String,
      category: ServiceDiagnosticCategoryExtension.fromJson(
        json['category'] as String,
      ),
      severity: ServiceDiagnosticSeverityExtension.fromJson(
        json['severity'] as String,
      ),
      summary: json['summary'] as String,
      detail: json['detail'] as String?,
      hint: json['hint'] as String?,
      semanticRefs: ServiceDiagnosticSection.fromJson(
        json['semantic_refs'] as Map<String, dynamic>,
      ),
      invocationContext: ServiceDiagnosticSection.fromJson(
        json['invocation_context'] as Map<String, dynamic>,
      ),
      provenance: ServiceDiagnosticSection.fromJson(
        json['provenance'] as Map<String, dynamic>,
      ),
      resolutionStatus: ServiceDiagnosticResolutionStatusExtension.fromJson(
        json['resolution_status'] as String,
      ),
      debug: json['debug'] == null
          ? null
          : ServiceDiagnosticSection.fromJson(
              json['debug'] as Map<String, dynamic>,
            ),
    );

Map<String, dynamic> _$ServiceDiagnosticToJson(_ServiceDiagnostic instance) =>
    <String, dynamic>{
      'code': instance.code,
      'category': ServiceDiagnosticCategoryExtension.toJson(instance.category),
      'severity': ServiceDiagnosticSeverityExtension.toJson(instance.severity),
      'summary': instance.summary,
      'detail': instance.detail,
      'hint': instance.hint,
      'semantic_refs': instance.semanticRefs.toJson(),
      'invocation_context': instance.invocationContext.toJson(),
      'provenance': instance.provenance.toJson(),
      'resolution_status': ServiceDiagnosticResolutionStatusExtension.toJson(
        instance.resolutionStatus,
      ),
      'debug': instance.debug?.toJson(),
    };
