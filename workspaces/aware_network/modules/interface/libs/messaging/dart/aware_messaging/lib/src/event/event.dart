/// Base representation of a domain event.
abstract class Event {
  final DateTime timestamp;
  final Map<String, dynamic>? metadata;

  Event({DateTime? timestamp, this.metadata})
    : timestamp = timestamp ?? DateTime.now().toUtc();

  String get eventType => runtimeType.toString();

  Map<String, dynamic> toJson() {
    return {
      'eventType': eventType,
      'timestamp': timestamp.toIso8601String(),
      if (metadata != null) 'metadata': metadata,
    };
  }
}
