// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_api_ontology/api/api_package.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_package_api_package_model.freezed.dart';
part 'sdk_package_api_package_model.g.dart';

@freezed
abstract class SdkPackageApiPackage with _$SdkPackageApiPackage {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkPackageApiPackage.def({
    @UuidValueConverter() required UuidValue id,
    ApiPackage? apiPackage,
    String? description,
    @UuidValueConverter() required UuidValue sdkPackageId,
    @UuidValueConverter() UuidValue? apiPackageId,
  }) = _SdkPackageApiPackage;

  factory SdkPackageApiPackage({
    UuidValue? id,
    ApiPackage? apiPackage,
    String? description,
    required UuidValue sdkPackageId,
    UuidValue? apiPackageId,
  }) {
    return _SdkPackageApiPackage(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      apiPackage: apiPackage,
      description: description,
      sdkPackageId: sdkPackageId,
      apiPackageId: apiPackageId,
    );
  }

  factory SdkPackageApiPackage.fromJson(Map<String, dynamic> json) =>
      _$SdkPackageApiPackageFromJson(json);
}
