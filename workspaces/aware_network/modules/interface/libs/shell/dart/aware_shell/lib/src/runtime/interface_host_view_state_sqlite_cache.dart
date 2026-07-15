import 'dart:convert';
import 'dart:io';

import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite_common_ffi/sqflite_ffi.dart' as sqlite;

import 'interface_host_view_state_cache.dart';

class SqliteInterfaceHostViewStateCacheStore
    implements
        InterfaceHostViewStateCacheStore,
        InterfaceHostViewStateCacheStoreLifecycle {
  SqliteInterfaceHostViewStateCacheStore({
    required this.databasePath,
    sqlite.DatabaseFactory? databaseFactory,
  }) : _databaseFactory = databaseFactory ?? sqlite.databaseFactoryFfi {
    if (databaseFactory == null) {
      sqlite.sqfliteFfiInit();
    }
  }

  static const int _schemaVersion = 1;
  static const String _namespacesTable =
      'interface_host_view_state_cache_namespaces';
  static const String _entriesTable = 'interface_host_view_state_cache_entries';

  final String databasePath;
  final sqlite.DatabaseFactory _databaseFactory;

  sqlite.Database? _db;
  Future<sqlite.Database>? _openingDatabase;

  Future<void> close() async {
    final db = _db;
    _db = null;
    if (db != null) {
      await db.close();
    }
  }

  Future<sqlite.Database> get _database async {
    final existing = _db;
    if (existing != null) {
      return existing;
    }
    final opening = _openingDatabase;
    if (opening != null) {
      return opening;
    }

    await Directory(p.dirname(databasePath)).create(recursive: true);
    final future = _databaseFactory.openDatabase(
      databasePath,
      options: sqlite.OpenDatabaseOptions(
        version: _schemaVersion,
        onConfigure: (db) async {
          await db.execute('PRAGMA foreign_keys = ON');
        },
        onCreate: (db, _) => _installSchema(db),
        onOpen: _installSchema,
      ),
    );
    _openingDatabase = future;
    try {
      final db = await future;
      _db = db;
      return db;
    } finally {
      _openingDatabase = null;
    }
  }

  @override
  Future<InterfaceHostViewStateCacheEntry?> read(
    InterfaceHostViewStateCacheKey key,
  ) async {
    final db = await _database;
    final rows = await db.query(
      _entriesTable,
      where: 'cache_key = ?',
      whereArgs: <Object?>[key.cacheKey],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return _entryFromRow(rows.single);
  }

  @override
  Future<InterfaceHostViewStateCacheEntry?> readPaneState({
    required String namespace,
    required String paneStateKey,
    String? viewRef,
    String? projectionViewKey,
  }) async {
    final normalizedNamespace = _requiredToken(namespace, 'namespace');
    final normalizedPaneStateKey = _requiredToken(paneStateKey, 'paneStateKey');
    final where = <String>['namespace = ?', 'pane_state_key = ?'];
    final whereArgs = <Object?>[normalizedNamespace, normalizedPaneStateKey];
    final normalizedViewRef = _trimmedOrNull(viewRef);
    if (normalizedViewRef != null) {
      where.add('view_ref = ?');
      whereArgs.add(normalizedViewRef);
    }
    final normalizedViewKey = _trimmedOrNull(projectionViewKey);
    if (normalizedViewKey != null) {
      where.add('projection_view_key = ?');
      whereArgs.add(normalizedViewKey);
    }

    final db = await _database;
    final rows = await db.query(
      _entriesTable,
      where: where.join(' AND '),
      whereArgs: whereArgs,
      orderBy: 'cache_key DESC',
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return _entryFromRow(rows.single);
  }

  @override
  Future<List<InterfaceHostViewStateCacheEntry>> entries({
    String? namespace,
  }) async {
    final normalizedNamespace = _trimmedOrNull(namespace);
    final db = await _database;
    final rows = await db.query(
      _entriesTable,
      where: normalizedNamespace == null ? null : 'namespace = ?',
      whereArgs: normalizedNamespace == null
          ? null
          : <Object?>[normalizedNamespace],
      orderBy: 'cache_key ASC',
    );
    return List<InterfaceHostViewStateCacheEntry>.unmodifiable(
      rows.map(_entryFromRow),
    );
  }

  @override
  Future<InterfaceHostViewStateCursorState?> viewStateCursor({
    required String namespace,
  }) async {
    final db = await _database;
    final rows = await db.query(
      _namespacesTable,
      where: 'namespace = ?',
      whereArgs: <Object?>[_requiredToken(namespace, 'namespace')],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return _cursorFromNamespaceRow(rows.single);
  }

  @override
  Future<InterfaceHostViewStateCacheSyncResult> replaceNamespace({
    required String namespace,
    required Iterable<InterfaceHostViewStateCacheEntry> entries,
    InterfaceHostViewStateCursorState? viewStateCursor,
  }) async {
    final normalizedNamespace = _requiredToken(namespace, 'namespace');
    final incoming = entries.toList(growable: false);
    for (final entry in incoming) {
      if (entry.key.namespace != normalizedNamespace) {
        throw ArgumentError.value(
          entry.key.namespace,
          'entry.key.namespace',
          'must match replace namespace $normalizedNamespace',
        );
      }
    }

    final cursor = _trimmedOrNull(viewStateCursor?.cursor);
    final digest = _trimmedOrNull(viewStateCursor?.digest);
    final db = await _database;
    return db.transaction((txn) async {
      final previousRows = await txn.query(
        _namespacesTable,
        where: 'namespace = ?',
        whereArgs: <Object?>[normalizedNamespace],
        limit: 1,
      );
      final previousCursor = previousRows.isEmpty
          ? null
          : _cursorFromNamespaceRow(previousRows.single);
      if (_sameViewStateCursor(previousCursor, viewStateCursor)) {
        return InterfaceHostViewStateCacheSyncResult(
          namespace: normalizedNamespace,
          storedEntryCount: 0,
          removedEntryCount: 0,
          cursor: cursor,
          digest: digest,
          skipped: true,
        );
      }

      final previousCount = await _entryCount(
        txn,
        namespace: normalizedNamespace,
      );
      await txn.delete(
        _entriesTable,
        where: 'namespace = ?',
        whereArgs: <Object?>[normalizedNamespace],
      );
      final updatedAt = DateTime.now().toUtc().toIso8601String();
      for (final entry in incoming) {
        await txn.insert(
          _entriesTable,
          _entryRow(entry, updatedAt: updatedAt),
          conflictAlgorithm: sqlite.ConflictAlgorithm.replace,
        );
      }

      if (viewStateCursor == null || cursor == null || digest == null) {
        await txn.delete(
          _namespacesTable,
          where: 'namespace = ?',
          whereArgs: <Object?>[normalizedNamespace],
        );
      } else {
        await txn.insert(_namespacesTable, <String, Object?>{
          'namespace': normalizedNamespace,
          'cursor': cursor,
          'digest': digest,
          'materialized_entry_count': viewStateCursor.materializedEntryCount,
          'cursor_json': jsonEncode(viewStateCursor.toJson()),
          'updated_at': updatedAt,
        }, conflictAlgorithm: sqlite.ConflictAlgorithm.replace);
      }

      return InterfaceHostViewStateCacheSyncResult(
        namespace: normalizedNamespace,
        storedEntryCount: incoming.length,
        removedEntryCount: previousCount,
        cursor: cursor,
        digest: digest,
      );
    });
  }

  @override
  Future<void> clear({String? namespace}) async {
    final normalizedNamespace = _trimmedOrNull(namespace);
    final db = await _database;
    await db.transaction((txn) async {
      if (normalizedNamespace == null) {
        await txn.delete(_entriesTable);
        await txn.delete(_namespacesTable);
        return;
      }
      await txn.delete(
        _entriesTable,
        where: 'namespace = ?',
        whereArgs: <Object?>[normalizedNamespace],
      );
      await txn.delete(
        _namespacesTable,
        where: 'namespace = ?',
        whereArgs: <Object?>[normalizedNamespace],
      );
    });
  }

  Future<void> _installSchema(sqlite.Database db) async {
    await db.execute('''
CREATE TABLE IF NOT EXISTS $_namespacesTable (
  namespace TEXT PRIMARY KEY,
  cursor TEXT,
  digest TEXT,
  materialized_entry_count INTEGER NOT NULL DEFAULT 0,
  cursor_json TEXT,
  updated_at TEXT NOT NULL
)
''');
    await db.execute('''
CREATE TABLE IF NOT EXISTS $_entriesTable (
  cache_key TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  pane_state_key TEXT NOT NULL,
  view_ref TEXT,
  projection_view_key TEXT,
  key_json TEXT NOT NULL,
  materialized_state_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
''');
    await db.execute('''
CREATE INDEX IF NOT EXISTS idx_${_entriesTable}_namespace
ON $_entriesTable(namespace)
''');
    await db.execute('''
CREATE INDEX IF NOT EXISTS idx_${_entriesTable}_pane_lookup
ON $_entriesTable(namespace, pane_state_key, view_ref, projection_view_key)
''');
  }

  Future<int> _entryCount(
    sqlite.Transaction txn, {
    required String namespace,
  }) async {
    final rows = await txn.rawQuery(
      'SELECT COUNT(*) AS entry_count FROM $_entriesTable WHERE namespace = ?',
      <Object?>[namespace],
    );
    return rows.single['entry_count'] as int? ?? 0;
  }

  Map<String, Object?> _entryRow(
    InterfaceHostViewStateCacheEntry entry, {
    required String updatedAt,
  }) {
    return <String, Object?>{
      'cache_key': entry.key.cacheKey,
      'namespace': entry.key.namespace,
      'pane_state_key': entry.key.paneStateKey,
      'view_ref': entry.key.viewRef,
      'projection_view_key': entry.key.projectionViewKey,
      'key_json': jsonEncode(entry.key.toJson()),
      'materialized_state_json': jsonEncode(entry.materializedState.toJson()),
      'updated_at': updatedAt,
    };
  }
}

InterfaceHostViewStateCacheEntry _entryFromRow(Map<String, Object?> row) {
  final keyJson = jsonDecode(row['key_json']! as String) as Map;
  final materializedJson =
      jsonDecode(row['materialized_state_json']! as String) as Map;
  return InterfaceHostViewStateCacheEntry(
    key: InterfaceHostViewStateCacheKey.fromJson(
      Map<String, dynamic>.from(keyJson),
    ),
    materializedState: InterfaceMaterializedPaneState.fromJson(
      Map<String, dynamic>.from(materializedJson),
    ),
  );
}

InterfaceHostViewStateCursorState? _cursorFromNamespaceRow(
  Map<String, Object?> row,
) {
  final cursorJson = row['cursor_json'];
  if (cursorJson is String && cursorJson.trim().isNotEmpty) {
    return InterfaceHostViewStateCursorState.fromJson(
      Map<String, dynamic>.from(jsonDecode(cursorJson) as Map),
    );
  }
  final cursor = row['cursor'];
  final digest = row['digest'];
  if (cursor is! String || digest is! String) {
    return null;
  }
  return InterfaceHostViewStateCursorState(
    cursor: cursor,
    digest: digest,
    materializedEntryCount: row['materialized_entry_count'] as int? ?? 0,
  );
}

bool _sameViewStateCursor(
  InterfaceHostViewStateCursorState? left,
  InterfaceHostViewStateCursorState? right,
) {
  if (left == null || right == null) {
    return false;
  }
  final leftCursor = _trimmedOrNull(left.cursor);
  final rightCursor = _trimmedOrNull(right.cursor);
  if (leftCursor != null && leftCursor == rightCursor) {
    return true;
  }
  final leftDigest = _trimmedOrNull(left.digest);
  final rightDigest = _trimmedOrNull(right.digest);
  return leftDigest != null && leftDigest == rightDigest;
}

String _requiredToken(String value, String label) {
  final normalized = _trimmedOrNull(value);
  if (normalized == null) {
    throw ArgumentError.value(value, label, 'must be non-empty');
  }
  return normalized;
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
