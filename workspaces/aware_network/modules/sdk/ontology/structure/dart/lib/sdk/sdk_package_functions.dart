// GENERATED CODE - DO NOT MODIFY BY HAND
// Function extensions for Dart OCG objects.

import 'sdk_package_model.dart';
import 'sdk_package_api_package_model.dart';
import 'sdk_package_dependency_model.dart';
import 'sdk_package_implementation_package_model.dart';
import 'sdk_package_object_config_graph_package_model.dart';
import 'package:aware_code_ontology/code/code_enums.dart';
import 'package:uuid/uuid.dart';
import 'package:aware_model_helpers/payload_decoders.dart' as payload_decoders;
import 'package:aware_api/aware_api.dart';

extension SdkPackageFunctions on SdkPackage {
  /// Sync mutable manifest/build/dependency/target truth onto an existing SdkPackage root.
  Future<SdkPackage> syncManifestTruth({
    required FunctionInvocationContext context,
    UuidValue? sdkConfigObjectInstanceGraphCommitId,
    UuidValue? sourceCodePackageId,
    String? fqnPrefix,
    required int versionNumber,
    String? title,
    String? description,
    required int awareSdkVersion,
    String? manifestRelativePath,
    required String packageRoot,
    required String sourcesRoot,
    required List<dynamic> includePaths,
    required List<dynamic> excludePaths,
    required bool forceFreshScan,
    required String compilationMode,
    required List<dynamic> dependencies,
    required Map<String, dynamic> targets,
  }) async {
    final args = <FunctionInvocationArgument>[];
    if (sdkConfigObjectInstanceGraphCommitId != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'sdk_config_object_instance_graph_commit_id',
          value: sdkConfigObjectInstanceGraphCommitId,
        ),
      );
    }
    if (sourceCodePackageId != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'source_code_package_id',
          value: sourceCodePackageId,
        ),
      );
    }
    if (fqnPrefix != null) {
      args.add(
        FunctionInvocationArgument(name: 'fqn_prefix', value: fqnPrefix),
      );
    }
    args.add(
      FunctionInvocationArgument(name: 'version_number', value: versionNumber),
    );
    if (title != null) {
      args.add(FunctionInvocationArgument(name: 'title', value: title));
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    args.add(
      FunctionInvocationArgument(
        name: 'aware_sdk_version',
        value: awareSdkVersion,
      ),
    );
    if (manifestRelativePath != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'manifest_relative_path',
          value: manifestRelativePath,
        ),
      );
    }
    args.add(
      FunctionInvocationArgument(name: 'package_root', value: packageRoot),
    );
    args.add(
      FunctionInvocationArgument(name: 'sources_root', value: sourcesRoot),
    );
    args.add(
      FunctionInvocationArgument(name: 'include_paths', value: includePaths),
    );
    args.add(
      FunctionInvocationArgument(name: 'exclude_paths', value: excludePaths),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'force_fresh_scan',
        value: forceFreshScan,
      ),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'compilation_mode',
        value: compilationMode,
      ),
    );
    args.add(
      FunctionInvocationArgument(name: 'dependencies', value: dependencies),
    );
    args.add(FunctionInvocationArgument(name: 'targets', value: targets));
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-package',
      objectId: id,
      functionName: 'sync-manifest-truth',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkPackage.sync_manifest_truth failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkPackage.fromJson(payload_decoders.decodeMap(responseValue));
  }

  /// Attach one API package to this SdkPackage.
  ///
  /// Contract:
  /// - This is the package/import rail for authored/generated SDK source.
  /// - Operation-level endpoint bindings remain separate `SdkOperation -> ApiCapabilityEndpoint` truth.
  Future<SdkPackageApiPackage> attachApiPackage({
    required FunctionInvocationContext context,
    required UuidValue apiPackageId,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(
      FunctionInvocationArgument(name: 'api_package_id', value: apiPackageId),
    );
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-package',
      objectId: id,
      functionName: 'attach-api-package',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkPackage.attach_api_package failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkPackageApiPackage.fromJson(
      payload_decoders.decodeMap(responseValue),
    );
  }

  /// Attach one concrete language implementation package owned by this SdkPackage.
  ///
  /// Contract:
  /// - The SDK package owns explicit language implementation packages as semantic package truth.
  /// - WorkspaceRevision checkout and SDK installers must resolve public package roots from this
  /// bridge, never from target JSON or workspace layout heuristics.
  /// - `code_package_id` points at the canonical CodePackage for the implementation package.
  /// - `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.
  Future<SdkPackageImplementationPackage> attachImplementationPackage({
    required FunctionInvocationContext context,
    required UuidValue codePackageId,
    required String packageName,
    required CodeLanguage language,
    required String importRoot,
    required String manifestRelativePath,
    required String packageRoot,
    String? entrypoint,
    required String role,
    required List<dynamic> includePaths,
    required List<dynamic> excludePaths,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(
      FunctionInvocationArgument(name: 'code_package_id', value: codePackageId),
    );
    args.add(
      FunctionInvocationArgument(name: 'package_name', value: packageName),
    );
    args.add(FunctionInvocationArgument(name: 'language', value: language));
    args.add(
      FunctionInvocationArgument(name: 'import_root', value: importRoot),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'manifest_relative_path',
        value: manifestRelativePath,
      ),
    );
    args.add(
      FunctionInvocationArgument(name: 'package_root', value: packageRoot),
    );
    if (entrypoint != null) {
      args.add(
        FunctionInvocationArgument(name: 'entrypoint', value: entrypoint),
      );
    }
    args.add(FunctionInvocationArgument(name: 'role', value: role));
    args.add(
      FunctionInvocationArgument(name: 'include_paths', value: includePaths),
    );
    args.add(
      FunctionInvocationArgument(name: 'exclude_paths', value: excludePaths),
    );
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-package',
      objectId: id,
      functionName: 'attach-implementation-package',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkPackage.attach_implementation_package failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkPackageImplementationPackage.fromJson(
      payload_decoders.decodeMap(responseValue),
    );
  }

  /// Attach one SDK-owned ObjectConfigGraphPackage to this SdkPackage.
  ///
  /// Contract:
  /// - This is SDK ownership truth, not SDK dependency truth.
  /// - The child package is declared by `aware.sdk.toml` and materialized through the
  /// canonical ObjectConfigGraphPackage rail.
  /// - WorkspaceRevision/Hub consumers can use the optional OIG commit pin to replay
  /// exact SDK-owned DB/schema truth without reopening local manifests.
  Future<SdkPackageObjectConfigGraphPackage> attachObjectConfigGraphPackage({
    required FunctionInvocationContext context,
    required UuidValue objectConfigGraphPackageId,
    required String manifestRelativePath,
    required String role,
    required String packageKind,
    UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId,
    String? expectedHashSha256,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(
      FunctionInvocationArgument(
        name: 'object_config_graph_package_id',
        value: objectConfigGraphPackageId,
      ),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'manifest_relative_path',
        value: manifestRelativePath,
      ),
    );
    args.add(FunctionInvocationArgument(name: 'role', value: role));
    args.add(
      FunctionInvocationArgument(name: 'package_kind', value: packageKind),
    );
    if (objectConfigGraphPackageObjectInstanceGraphCommitId != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'object_config_graph_package_object_instance_graph_commit_id',
          value: objectConfigGraphPackageObjectInstanceGraphCommitId,
        ),
      );
    }
    if (expectedHashSha256 != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'expected_hash_sha256',
          value: expectedHashSha256,
        ),
      );
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-package',
      objectId: id,
      functionName: 'attach-object-config-graph-package',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkPackage.attach_object_config_graph_package failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkPackageObjectConfigGraphPackage.fromJson(
      payload_decoders.decodeMap(responseValue),
    );
  }

  /// Attach one SDK package dependency to this SdkPackage.
  ///
  /// Contract:
  /// - This is package dependency truth, not operation invocation truth.
  /// - `target_version_number` is selector/compatibility metadata.
  /// - `target_sdk_package_object_instance_graph_commit_id` is the exact reproducibility authority
  /// when the dependency is locked or resolved through WorkspaceRevision/Hub evidence.
  /// - SDK operation composition must only target operations from the declared dependency closure.
  Future<SdkPackageDependency> attachSdkPackageDependency({
    required FunctionInvocationContext context,
    required UuidValue targetSdkPackageId,
    required String targetPackageName,
    UuidValue? targetSdkPackageObjectInstanceGraphCommitId,
    int? targetVersionNumber,
    String? expectedHashSha256,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(
      FunctionInvocationArgument(
        name: 'target_sdk_package_id',
        value: targetSdkPackageId,
      ),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'target_package_name',
        value: targetPackageName,
      ),
    );
    if (targetSdkPackageObjectInstanceGraphCommitId != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'target_sdk_package_object_instance_graph_commit_id',
          value: targetSdkPackageObjectInstanceGraphCommitId,
        ),
      );
    }
    if (targetVersionNumber != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'target_version_number',
          value: targetVersionNumber,
        ),
      );
    }
    if (expectedHashSha256 != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'expected_hash_sha256',
          value: expectedHashSha256,
        ),
      );
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-package',
      objectId: id,
      functionName: 'attach-sdk-package-dependency',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkPackage.attach_sdk_package_dependency failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkPackageDependency.fromJson(
      payload_decoders.decodeMap(responseValue),
    );
  }
}

class SdkPackageConstructors {
  /// Create the canonical SDK-owned package root over an existing `SdkConfig`.
  ///
  /// Contract:
  /// - Identity is keyed by SDK package `name`.
  /// - `SdkPackage` is the package/public root over an existing canonical `SdkConfig`.
  /// - `sdk_config_id` must point at the canonical SdkConfig stable id for this package root.
  /// - `sdk_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
  /// for the semantic SdkConfig root so package consumers can replay exact SDK truth without
  /// resolving branch head or reopening authoring TOML.
  /// - `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.
  /// - `SdkPackageApiPackage` declares which API packages are available to generated/runtime SDKs.
  /// - `SdkPackageImplementationPackage` declares concrete Python/Dart package roots owned by
  /// the SDK package for public install/runtime consumption.
  /// - `SdkPackageObjectConfigGraphPackage` declares SDK-owned OCG/state packages that travel
  /// with this SDK package rather than acting as external dependencies.
  /// - `SdkPackageDependency` declares package-level SDK dependencies; operation composition may only
  /// target SDK operations from this declared dependency closure.
  static Future<FunctionCallResult> build({
    required FunctionInvocationContext context,
    required String name,
    required UuidValue sdkConfigId,
    UuidValue? sdkConfigObjectInstanceGraphCommitId,
    UuidValue? sourceCodePackageId,
    String? fqnPrefix,
    required int versionNumber,
    String? title,
    String? description,
    required int awareSdkVersion,
    String? manifestRelativePath,
    required String packageRoot,
    required String sourcesRoot,
    required List<dynamic> includePaths,
    required List<dynamic> excludePaths,
    required bool forceFreshScan,
    required String compilationMode,
    required List<dynamic> dependencies,
    required Map<String, dynamic> targets,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(FunctionInvocationArgument(name: 'name', value: name));
    args.add(
      FunctionInvocationArgument(name: 'sdk_config_id', value: sdkConfigId),
    );
    if (sdkConfigObjectInstanceGraphCommitId != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'sdk_config_object_instance_graph_commit_id',
          value: sdkConfigObjectInstanceGraphCommitId,
        ),
      );
    }
    if (sourceCodePackageId != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'source_code_package_id',
          value: sourceCodePackageId,
        ),
      );
    }
    if (fqnPrefix != null) {
      args.add(
        FunctionInvocationArgument(name: 'fqn_prefix', value: fqnPrefix),
      );
    }
    args.add(
      FunctionInvocationArgument(name: 'version_number', value: versionNumber),
    );
    if (title != null) {
      args.add(FunctionInvocationArgument(name: 'title', value: title));
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    args.add(
      FunctionInvocationArgument(
        name: 'aware_sdk_version',
        value: awareSdkVersion,
      ),
    );
    if (manifestRelativePath != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'manifest_relative_path',
          value: manifestRelativePath,
        ),
      );
    }
    args.add(
      FunctionInvocationArgument(name: 'package_root', value: packageRoot),
    );
    args.add(
      FunctionInvocationArgument(name: 'sources_root', value: sourcesRoot),
    );
    args.add(
      FunctionInvocationArgument(name: 'include_paths', value: includePaths),
    );
    args.add(
      FunctionInvocationArgument(name: 'exclude_paths', value: excludePaths),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'force_fresh_scan',
        value: forceFreshScan,
      ),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'compilation_mode',
        value: compilationMode,
      ),
    );
    args.add(
      FunctionInvocationArgument(name: 'dependencies', value: dependencies),
    );
    args.add(FunctionInvocationArgument(name: 'targets', value: targets));
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-package',
      functionName: 'build',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      callTarget: FunctionInvocationCallTarget.opgConstructor,
      objectProjectionGraphId: context.opgId,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkPackage.build failed: ' +
            (response.error ?? response.status.name),
      );
    }
    return response;
  }
}
