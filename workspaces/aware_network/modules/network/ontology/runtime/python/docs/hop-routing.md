# Hop-Based Routing Implementation

## Overview

This implementation provides a comprehensive hop-based routing system for NetworkOperations in the Aware network. The system enables decentralized communication while maintaining privacy, auditability, and proper access control.

## Key Components

### 1. NetworkOperation (Updated)
- **File**: `network/network_operation.py`
- **Changes**: Removed direct routing fields, now uses `network_operation_hop_list`
- **Purpose**: Container for messages with hop-based routing headers

### 2. NetworkOperationHop (Enhanced)
- **File**: `network/network_operation_hop.py`
- **Changes**: Added `hop_index`, `timestamp`, and `network_operation_id` for audit trails
- **Purpose**: Individual routing information with source/target platform details

### 3. NetworkRouter (Completely Redesigned)
- **File**: `network_router.py`
- **Changes**: Full hop-based routing implementation with privacy protection
- **Purpose**: Routes NetworkOperations using single-hop headers with audit persistence

## Architecture Pattern

```
NetworkOperation
├── Single hop in network_operation_hop_list (the "header")
├── Database audit trail (all hops persisted)
└── Privacy protection (interface IDs stripped at node boundaries)
```

## Key Features

### ✅ Single-Hop Header Pattern
- **On Wire**: NetworkOperation carries exactly 1 hop (the current routing header)
- **In Database**: All hops are persisted for complete audit trail
- **Benefits**: Small packets, clear routing, complete auditability

### ✅ Privacy Protection
- Interface IDs are automatically stripped when crossing node boundaries
- Remote nodes only see node-to-node routing
- Users' device details remain private to their home node

### ✅ Audit Trail
- Every hop is persisted with `hop_index` and `timestamp`
- Complete path reconstruction possible
- Tamper-evident trail for compliance and debugging

### ✅ Platform Type Support
- **NETWORK_NODE**: Standard node-to-node routing
- **INTERFACE**: User devices (phones, computers)
- **EXTERNAL**: External services or gateways

### ✅ XOR Constraints
- Each hop validates source/target platform consistency
- Prevents invalid routing combinations
- Ensures data integrity

## Usage Patterns

### 1. Interface → Home Node → Target Node
```python
# Create initial hop: Interface → Home Node
initial_hop = router.create_initial_hop(
    source_platform_type=PlatformType.INTERFACE,
    source_node_id=home_node_id,
    source_interface_id=interface_id,
    target_platform_type=PlatformType.NETWORK_NODE,
    target_node_id=home_node_id,
)

network_op = NetworkOperation(
    message_type=NetworkMessageType.REQUEST,
    type=NetworkOperationType.api,
    api_operation=api_op,
    network_request=network_request,
    network_operation_hop_list=[initial_hop],
)
```

### 2. Node-to-Node Forwarding
```python
# Router automatically:
# 1. Persists current hop for audit
# 2. Creates new hop to target
# 3. Strips interface IDs for privacy
# 4. Updates hop list and forwards
```

### 3. Audit Trail Query
```python
# Get complete hop history
hop_trail = await router.get_hop_audit_trail(network_operation_id)
for hop in hop_trail:
    print(f"Hop {hop.hop_index}: {hop.source_platform_type} → {hop.target_platform_type}")
```

## Database Schema

### NetworkOperationHop Table
```sql
CREATE TABLE network_operation_hop (
    id                   uuid PRIMARY KEY,
    network_operation_id uuid NOT NULL,
    hop_index           int NOT NULL,
    timestamp           timestamptz NOT NULL,
    
    source_platform_type platform_type NOT NULL,
    source_node_id      uuid NULL,
    source_interface_id uuid NULL,
    
    target_platform_type platform_type NOT NULL,
    target_node_id      uuid NULL,
    target_interface_id uuid NULL,
    
    -- XOR constraints for platform consistency
    CONSTRAINT src_platform_check CHECK (...),
    CONSTRAINT tgt_platform_check CHECK (...)
);
```

## Message Flow

### Request Path
1. **Interface** creates NetworkOperation with initial hop
2. **Home Node** persists hop, creates forwarding hop (strips interface ID)
3. **Target Node** persists hop, routes to environment service
4. **Environment Service** processes with full NetworkOperation (including network_request for ACL)

### Response Path
1. **Environment Service** returns updated NetworkOperation
2. **Target Node** creates reverse hop, forwards to home node
3. **Home Node** creates reverse hop, forwards to interface
4. **Interface** receives response with same NetworkOperation.id

## Security & Privacy

### Identity Propagation
- `NetworkRequest.requester_id` travels with every operation
- Environment services can perform ACL without shared database
- Identity context preserved throughout routing chain

### Interface Protection
- Interface IDs automatically stripped when leaving home node
- Remote nodes never see user device identifiers
- Privacy maintained while enabling audit trails

### Tamper Evidence
- Every hop is timestamped and persisted immutably
- Complete chain reconstruction possible
- Optional hash-chaining for cryptographic proof

## Example Usage

See `examples/hop_routing_example.py` for complete demonstrations including:
- Creating NetworkOperations with proper hops
- Forwarding flow simulation
- Audit trail examples
- Privacy protection demonstration

## Benefits

1. **Scalability**: Small packets, efficient routing
2. **Privacy**: User devices protected from remote visibility
3. **Auditability**: Complete immutable hop trails
4. **Flexibility**: Same pattern works local and remote
5. **Security**: Identity propagation without shared DB
6. **Standards**: OS-inspired patterns (completion ports, etc.)

## Future Extensions

- **Path Disclosure**: Optional full-path sharing for compliance
- **Hash Chaining**: Cryptographic hop integrity
- **Performance Metrics**: Hop timing and latency analysis
- **Service Discovery**: Automatic environment service location

This implementation provides a production-ready foundation for decentralized communication with enterprise-grade auditability and privacy protection.
