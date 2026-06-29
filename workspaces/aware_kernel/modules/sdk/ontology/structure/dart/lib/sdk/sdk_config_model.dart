// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_operation_model.dart';
import 'package:aware_sdk_ontology/sdk/sdk_surface_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_config_model.freezed.dart';
part 'sdk_config_model.g.dart';

/// Canonical SDK semantic root.
/// SDKs are local orchestration surfaces over committed API contracts. They do
/// not own API ingress truth; operation endpoint bindings point back to
/// `ApiCapabilityEndpoint`.
@freezed
abstract class SdkConfig with _$SdkConfig {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkConfig.def({
    @UuidValueConverter() required UuidValue id,
    @Default(const []) List<SdkOperation> operations,
    @Default(const []) List<SdkSurface> surfaces,
    required String name,
    String? title,
    String? description,
  }) = _SdkConfig;

  factory SdkConfig({
    UuidValue? id,
    List<SdkOperation> operations = const [],
    List<SdkSurface> surfaces = const [],
    required String name,
    String? title,
    String? description,
  }) {
    return _SdkConfig(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      operations: operations,
      surfaces: surfaces,
      name: name,
      title: title,
      description: description,
    );
  }

  factory SdkConfig.fromJson(Map<String, dynamic> json) =>
      _$SdkConfigFromJson(json);
}
