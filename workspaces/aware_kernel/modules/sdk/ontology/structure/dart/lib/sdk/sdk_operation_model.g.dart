// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_operation_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkOperation _$SdkOperationFromJson(Map<String, dynamic> json) =>
    _SdkOperation(
      id: const UuidValueConverter().fromJson(json['id'] as String),
      apiCapabilityEndpoints:
          (json['api_capability_endpoints'] as List<dynamic>?)
              ?.map(
                (e) => SdkOperationApiCapabilityEndpoint.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      sdkOperationDependencies:
          (json['sdk_operation_dependencies'] as List<dynamic>?)
              ?.map(
                (e) =>
                    SdkOperationDependency.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const [],
      name: json['name'] as String,
      title: json['title'] as String?,
      description: json['description'] as String?,
      implementationRef: json['implementation_ref'] as String?,
      sdkConfigId: const UuidValueConverter().fromJson(
        json['sdk_config_id'] as String,
      ),
    );

Map<String, dynamic> _$SdkOperationToJson(_SdkOperation instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'api_capability_endpoints': instance.apiCapabilityEndpoints
          .map((e) => e.toJson())
          .toList(),
      'sdk_operation_dependencies': instance.sdkOperationDependencies
          .map((e) => e.toJson())
          .toList(),
      'name': instance.name,
      'title': instance.title,
      'description': instance.description,
      'implementation_ref': instance.implementationRef,
      'sdk_config_id': const UuidValueConverter().toJson(instance.sdkConfigId),
    };
