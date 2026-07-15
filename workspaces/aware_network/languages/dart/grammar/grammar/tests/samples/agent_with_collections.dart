import 'package:freezed_annotation/freezed_annotation.dart';

part 'agent_with_collections.freezed.dart';
part 'agent_with_collections.g.dart';

/// Test model to validate collection type extraction
/// Specifically testing List<CustomClass> with @Default([]) annotation
@freezed
abstract class Agent with _$Agent {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory Agent.def({
    // Primitive collections - should be PRIMITIVE
    @Default([]) List<String>? stringList,
    @Default([]) List<int>? intList,
    
    // Class collections - should be CLASS type, not PRIMITIVE
    @Default([]) List<AgentProcess>? agentProcessList,
    @Default([]) List<AgentProcessThread>? threadList,
    
    // Single class references - should be CLASS
    AgentConfig? config,
    Identity? identity,
    
    // Collections without @Default - should still be CLASS
    List<AgentProcessTool>? toolList,
    
    // Nullable collections with different patterns
    List<AgentInferenceModel>? inferenceModels,
    
    // Required collections
    required List<AgentTask> taskList,
  }) = _Agent;

  factory Agent.fromJson(Map<String, dynamic> json) => _$AgentFromJson(json);
}

// Supporting classes referenced above
class AgentProcess {}
class AgentProcessThread {}
class AgentConfig {}
class Identity {}
class AgentProcessTool {}
class AgentInferenceModel {}
class AgentTask {}