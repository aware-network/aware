// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_surface_method_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_surface_model.freezed.dart';
part 'sdk_surface_model.g.dart';

/// SDK conceptual surface truth.
/// A surface groups stable SDK methods around one product concept. It is not a
/// CLI command and does not replace API endpoint truth; CLI, Skill, and other
/// renderers project from surface methods.
@freezed
abstract class SdkSurface with _$SdkSurface {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkSurface.def({
    @UuidValueConverter() required UuidValue id,
    @Default(const []) List<SdkSurfaceMethod> methods,
    required String name,
    String? title,
    String? description,
    @UuidValueConverter() required UuidValue sdkConfigId,
  }) = _SdkSurface;

  factory SdkSurface({
    UuidValue? id,
    List<SdkSurfaceMethod> methods = const [],
    required String name,
    String? title,
    String? description,
    required UuidValue sdkConfigId,
  }) {
    return _SdkSurface(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      methods: methods,
      name: name,
      title: title,
      description: description,
      sdkConfigId: sdkConfigId,
    );
  }

  factory SdkSurface.fromJson(Map<String, dynamic> json) =>
      _$SdkSurfaceFromJson(json);
}
