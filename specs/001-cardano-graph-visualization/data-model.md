# Data Model: Cardano Blockchain Graph Visualization

**Date**: 2025-01-27  
**Feature**: Cardano Blockchain Graph Visualization

## Overview

The system models Cardano blockchain data as a directed graph where nodes represent blocks, transactions, and addresses, and edges represent relationships between them. The graph structure is maintained in-memory using NetworkX and visualized using PyVis.

## Entities

### 1. Block

Represents a block on the Cardano blockchain containing multiple transactions.

**Attributes**:
- `block_hash` (string, required): Unique identifier for the block
- `block_height` (integer, required): Block number/height in the blockchain
- `timestamp` (datetime, required): When the block was created
- `slot` (integer, optional): Cardano slot number
- `tx_count` (integer, optional): Number of transactions in the block

**Relationships**:
- **Has many**: Transactions (block → transaction edges)
- **Belongs to**: Blockchain (implicit, sequential ordering)

**Validation Rules**:
- `block_hash` must be unique
- `block_height` must be positive integer
- `timestamp` must be valid datetime

**State Transitions**:
- Created when fetched from API
- Added to graph as node
- Connected to transaction nodes when transactions are processed

**Graph Representation**:
- **Node Type**: `block`
- **Node ID**: `block_{block_hash}` or `block_{block_height}`
- **Edges**: `block → transaction` (directed)

---

### 2. Transaction

Represents a transaction on the Cardano blockchain with inputs and outputs.

**Attributes**:
- `tx_hash` (string, required): Unique transaction identifier
- `block_hash` (string, required): Block containing this transaction
- `block_height` (integer, required): Block height for quick reference
- `inputs` (list[TransactionInput], required): List of input references
- `outputs` (list[TransactionOutput], required): List of output address-value pairs
- `fee` (integer, optional): Transaction fee in Lovelace
- `timestamp` (datetime, optional): Transaction timestamp (from block)

**Nested Structures**:

#### TransactionInput
- `tx_hash` (string): Hash of previous transaction
- `index` (integer): Output index in previous transaction
- `address` (string): Address that owns the input (for display)

#### TransactionOutput
- `address` (string, required): Recipient Cardano address
- `amount` (integer, required): Amount in Lovelace
- `assets` (dict, optional): Native tokens if any

**Relationships**:
- **Belongs to**: Block (transaction → block edge, implicit via block_hash)
- **Has many**: Input addresses (address → transaction edges for inputs)
- **Has many**: Output addresses (transaction → address edges for outputs)

**Validation Rules**:
- `tx_hash` must be unique
- `inputs` list cannot be empty
- `outputs` list cannot be empty
- Each input must reference valid previous transaction output
- `amount` in outputs must be positive

**State Transitions**:
- Created when fetched from API
- Added to graph as node
- Connected to input address nodes (address → transaction)
- Connected to output address nodes (transaction → address)
- Connected to block node (block → transaction)

**Graph Representation**:
- **Node Type**: `transaction`
- **Node ID**: `tx_{tx_hash}`
- **Edges**: 
  - `address → transaction` (for inputs)
  - `transaction → address` (for outputs)
  - `block → transaction` (from containing block)

---

### 3. Address

Represents a Cardano address that can send or receive value.

**Attributes**:
- `address` (string, required): Cardano address (Bech32 format)
- `first_seen` (datetime, optional): When address first appeared in graph
- `total_received` (integer, optional): Cumulative Lovelace received (for analytics)
- `total_sent` (integer, optional): Cumulative Lovelace sent (for analytics)
- `transaction_count` (integer, optional): Number of transactions involving this address

**Relationships**:
- **Has many**: Transactions as input (address → transaction edges)
- **Has many**: Transactions as output (transaction → address edges)

**Validation Rules**:
- `address` must be valid Cardano Bech32 address format
- `address` must be unique in graph

**State Transitions**:
- Created when first encountered in transaction input or output
- Updated when involved in new transactions
- Accumulates transaction count and value statistics

**Graph Representation**:
- **Node Type**: `address`
- **Node ID**: `addr_{address}` (or just `address` if unique)
- **Edges**: 
  - `address → transaction` (when address is input)
  - `transaction → address` (when address is output)

---

### 4. Graph Structure

The overall visualization structure containing all nodes and edges.

**Attributes**:
- `nodes` (dict): Collection of all graph nodes (blocks, transactions, addresses)
- `edges` (list): Collection of all graph edges (relationships)
- `last_update` (datetime): Timestamp of last graph update
- `node_count` (integer): Total number of nodes
- `edge_count` (integer): Total number of edges
- `latest_block_height` (integer): Highest block height in graph

**Structure**:
- Implemented using NetworkX `DiGraph` (directed graph)
- Nodes have attributes: `type` (block/transaction/address), `data` (entity-specific data)
- Edges have attributes: `type` (block_tx, tx_input, tx_output), `weight` (optional)

**Operations**:
- `add_block(block)`: Add block node and connect to transactions
- `add_transaction(tx)`: Add transaction node and connect to addresses and block
- `add_address(address)`: Add or update address node
- `get_neighbors(node_id)`: Get connected nodes
- `get_path(start, end)`: Find path between nodes (for transaction tracing)
- `to_pyvis()`: Convert NetworkX graph to PyVis network for visualization

**Validation Rules**:
- All edges must connect existing nodes
- No duplicate edges (same source and target)
- Node IDs must be unique

**State Transitions**:
- Initialized as empty graph
- Incrementally updated as new blockchain data arrives
- Nodes and edges added atomically per block/transaction
- Can be pruned (future enhancement) to limit memory usage

---

## Graph Schema Summary

### Node Types

| Type | ID Format | Attributes |
|------|-----------|------------|
| `block` | `block_{hash}` or `block_{height}` | hash, height, timestamp, slot, tx_count |
| `transaction` | `tx_{hash}` | hash, block_hash, inputs, outputs, fee |
| `address` | `addr_{address}` | address, first_seen, stats |

### Edge Types

| Type | Source | Target | Direction | Meaning |
|------|--------|--------|-----------|---------|
| `block_tx` | block | transaction | → | Block contains transaction |
| `tx_input` | address | transaction | → | Address is input to transaction |
| `tx_output` | transaction | address | → | Transaction sends to address |

### Example Graph Structure

```
block_12345
  ├─→ tx_abc123
  │     ├─→ (tx_input) addr_bech32_1
  │     ├─→ (tx_input) addr_bech32_2
  │     ├─→ (tx_output) addr_bech32_3
  │     └─→ (tx_output) addr_bech32_4
  └─→ tx_def456
        ├─→ (tx_input) addr_bech32_3
        └─→ (tx_output) addr_bech32_5
```

## Data Flow

1. **API Fetch**: `data_fetcher.py` polls Blockfrost API for latest blocks
2. **Parse**: Raw API responses parsed into Block/Transaction/Address entities
3. **Graph Update**: `graph_builder.py` adds entities to NetworkX graph
4. **Visualization**: PyVis converts NetworkX graph to interactive HTML
5. **Display**: Flask serves HTML, updates via SSE or polling

## Validation & Error Handling

- **Invalid Address Format**: Log warning, skip address node creation
- **Missing Transaction References**: Log error, create transaction node without input edges
- **Duplicate Nodes**: Check before adding, update existing node if needed
- **Graph Consistency**: Validate edges reference existing nodes before adding

## Future Enhancements (Out of Scope for POC)

- Persistent storage (database)
- Historical data queries
- Graph pruning for memory management
- Advanced analytics (clustering, path analysis)
- Address balance tracking
- Transaction fee analysis

