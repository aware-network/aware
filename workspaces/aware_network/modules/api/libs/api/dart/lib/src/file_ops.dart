import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:logging/logging.dart';
import 'package:uuid/uuid.dart';

class AwareFileOpsException implements Exception {
  AwareFileOpsException(
    this.message, {
    this.statusCode,
    this.details,
  });

  final String message;
  final int? statusCode;
  final String? details;

  @override
  String toString() {
    final status = statusCode == null ? '' : ' (status=$statusCode)';
    final extra = details == null ? '' : ' - $details';
    return 'AwareFileOpsException: $message$status$extra';
  }
}

class UploadFileResult {
  const UploadFileResult({
    required this.objectId,
    required this.sha,
    required this.mimeType,
    required this.sizeBytes,
  });

  final UuidValue objectId;
  final String sha;
  final String mimeType;
  final int sizeBytes;
}

class DownloadFileResult {
  const DownloadFileResult({
    required this.objectId,
    required this.bytes,
    this.savedPath,
    this.contentType,
    this.filename,
  });

  final UuidValue objectId;
  final Uint8List bytes;
  final String? savedPath;
  final String? contentType;
  final String? filename;
}

class AwareFileOpsClient {
  AwareFileOpsClient({
    required Uri baseUrl,
    http.Client? client,
    Logger? logger,
  })  : _baseUrl = baseUrl,
        _client = client ?? http.Client(),
        _logger = logger ?? Logger('AwareFileOpsClient');

  final Uri _baseUrl;
  final http.Client _client;
  final Logger _logger;

  Uri _buildUri(String endpoint, [Map<String, String>? query]) {
    final normalized = endpoint.startsWith('/') ? endpoint : '/$endpoint';
    final basePath = _baseUrl.path;
    final mergedPath = basePath.isEmpty || basePath == '/'
        ? normalized
        : basePath.endsWith('/')
            ? '${basePath.substring(0, basePath.length - 1)}$normalized'
            : '$basePath$normalized';
    return _baseUrl.replace(path: mergedPath, queryParameters: query);
  }

  Map<String, String> _buildHeaders(String? authToken,
      [Map<String, String>? extra]) {
    final headers = <String, String>{};
    if (extra != null) {
      headers.addAll(extra);
    }
    if (authToken != null && authToken.trim().isNotEmpty) {
      headers['Authorization'] = 'Bearer ${authToken.trim()}';
    }
    return headers;
  }

  Future<UploadFileResult> uploadFile({
    required String filePath,
    required String mimeType,
    String? authToken,
  }) async {
    final file = File(filePath);
    if (!await file.exists()) {
      throw AwareFileOpsException('Upload file not found', details: filePath);
    }

    final uri = _buildUri('/crud/upload');
    _logger.fine('Uploading file to $uri');

    final request = http.MultipartRequest('POST', uri);
    request.headers.addAll(_buildHeaders(authToken));
    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        filePath,
        contentType: MediaType.parse(mimeType),
      ),
    );

    final response = await http.Response.fromStream(
      await _client.send(request),
    );

    if (response.statusCode != 200) {
      throw _buildError(
        response,
        action: 'upload',
      );
    }

    final payload = _decodeJson(response.body);
    if (payload is! Map<String, dynamic>) {
      throw AwareFileOpsException('Invalid upload response payload');
    }

    final rawId = payload['object_id'] ?? payload['objectId'];
    if (rawId == null) {
      throw AwareFileOpsException('Upload response missing object_id');
    }

    final rawSha = payload['sha'];
    if (rawSha == null) {
      throw AwareFileOpsException('Upload response missing sha');
    }

    final rawMimeType = payload['mime_type'] ?? payload['mimeType'];
    if (rawMimeType == null) {
      throw AwareFileOpsException('Upload response missing mime_type');
    }

    final rawSizeBytes = payload['size_bytes'] ?? payload['sizeBytes'];
    if (rawSizeBytes == null) {
      throw AwareFileOpsException('Upload response missing size_bytes');
    }

    final sizeBytes = switch (rawSizeBytes) {
      int() => rawSizeBytes,
      num() => rawSizeBytes.toInt(),
      _ => int.tryParse(rawSizeBytes.toString()),
    };
    if (sizeBytes == null) {
      throw AwareFileOpsException('Upload response has invalid size_bytes');
    }

    return UploadFileResult(
      objectId: UuidValue.fromString(rawId.toString()),
      sha: rawSha.toString(),
      mimeType: rawMimeType.toString(),
      sizeBytes: sizeBytes,
    );
  }

  Future<DownloadFileResult> downloadFile({
    required UuidValue objectId,
    String? savePath,
    String? authToken,
  }) async {
    final uri = _buildUri(
      '/crud/download',
      {'object_id': objectId.toString()},
    );
    _logger.fine('Downloading file from $uri');

    final request = http.Request('GET', uri);
    request.headers.addAll(_buildHeaders(authToken));

    final streamed = await _client.send(request);
    if (streamed.statusCode != 200) {
      final response = await http.Response.fromStream(streamed);
      throw _buildError(response, action: 'download');
    }

    final bytes = await streamed.stream.toBytes();
    String? resolvedPath;
    if (savePath != null && savePath.trim().isNotEmpty) {
      final path = savePath.trim();
      await File(path).writeAsBytes(bytes);
      resolvedPath = path;
    }

    final headers = streamed.headers;
    return DownloadFileResult(
      objectId: objectId,
      bytes: bytes,
      savedPath: resolvedPath,
      contentType: headers['content-type'],
      filename: _extractFilename(headers['content-disposition']),
    );
  }

  void close() {
    _client.close();
  }

  dynamic _decodeJson(String body) {
    if (body.trim().isEmpty) return null;
    return json.decode(body);
  }

  AwareFileOpsException _buildError(
    http.Response response, {
    required String action,
  }) {
    final status = response.statusCode;
    String? details;
    try {
      final payload = _decodeJson(response.body);
      if (payload is Map<String, dynamic>) {
        details = payload['detail']?.toString() ??
            payload['message']?.toString() ??
            payload['error']?.toString();
      } else if (payload != null) {
        details = payload.toString();
      }
    } catch (_) {
      details = response.body.trim().isEmpty ? null : response.body.trim();
    }

    return AwareFileOpsException(
      'File $action failed',
      statusCode: status,
      details: details,
    );
  }

  String? _extractFilename(String? contentDisposition) {
    if (contentDisposition == null || contentDisposition.isEmpty) return null;
    final parts = contentDisposition.split(';');
    for (final part in parts) {
      final trimmed = part.trim();
      if (trimmed.toLowerCase().startsWith('filename=')) {
        var name = trimmed.substring('filename='.length).trim();
        if (name.startsWith('"') && name.endsWith('"') && name.length > 1) {
          name = name.substring(1, name.length - 1);
        }
        return name.isEmpty ? null : name;
      }
    }
    return null;
  }
}
