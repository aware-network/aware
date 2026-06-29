// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_code_ontology/code/code_enums.dart';
import 'package:aware_code_ontology/package/code_package.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_package_implementation_package_model.freezed.dart';
part 'sdk_package_implementation_package_model.g.dart';

@freezed
abstract class SdkPackageImplementationPackage
    with _$SdkPackageImplementationPackage {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkPackageImplementationPackage.def({
    @UuidValueConverter() required UuidValue id,
    CodePackage? codePackage,
    String? entrypoint,
    required List<dynamic> excludePaths,
    required String importRoot,
    required List<dynamic> includePaths,
    @JsonKey(
      fromJson: CodeLanguageExtension.fromJson,
      toJson: CodeLanguageExtension.toJson,
    )
    required CodeLanguage language,
    required String manifestRelativePath,
    required String packageName,
    required String packageRoot,
    required String role,
    @UuidValueConverter() required UuidValue sdkPackageId,
    @UuidValueConverter() UuidValue? codePackageId,
  }) = _SdkPackageImplementationPackage;

  factory SdkPackageImplementationPackage({
    UuidValue? id,
    CodePackage? codePackage,
    String? entrypoint,
    required List<dynamic> excludePaths,
    required String importRoot,
    required List<dynamic> includePaths,
    required CodeLanguage language,
    required String manifestRelativePath,
    required String packageName,
    required String packageRoot,
    required String role,
    required UuidValue sdkPackageId,
    UuidValue? codePackageId,
  }) {
    return _SdkPackageImplementationPackage(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      codePackage: codePackage,
      entrypoint: entrypoint,
      excludePaths: excludePaths,
      importRoot: importRoot,
      includePaths: includePaths,
      language: language,
      manifestRelativePath: manifestRelativePath,
      packageName: packageName,
      packageRoot: packageRoot,
      role: role,
      sdkPackageId: sdkPackageId,
      codePackageId: codePackageId,
    );
  }

  factory SdkPackageImplementationPackage.fromJson(Map<String, dynamic> json) =>
      _$SdkPackageImplementationPackageFromJson(json);
}
