"""Graph builder for managing Cardano blockchain graph structure."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import networkx as nx

from src.models import Block, Transaction, Address
from src.config import MAX_NODES


class GraphBuilder:
    """Manages the NetworkX graph structure for blockchain visualization."""
    
    def __init__(self):
        """Initialize an empty directed graph."""
        self.graph = nx.DiGraph()
        self.last_update: Optional[datetime] = None
        self._update_callbacks: List[Callable] = []
        # Track block sequence for chain visualization
        self.block_heights: Dict[int, str] = {}  # height -> block_id mapping
        self.block_sequence: List[str] = []  # Ordered list of block IDs
        # Track metrics for color-coding
        self.block_metrics: Dict[str, Dict[str, Any]] = {}  # block_id -> metrics
    
    def add_block(self, block: Block) -> None:
        """
        Add a block node to the graph and connect it to its predecessor.
        
        Args:
            block: Block instance to add
        """
        # Check if we've reached the node limit
        if len(self.graph.nodes()) >= MAX_NODES:
            return  # Don't add more nodes if limit reached
        
        node_id = f"block_{block.block_hash}"
        
        # Initialize metrics for this block
        self.block_metrics[node_id] = {
            'transaction_count': 0,
            'total_value': 0,
            'address_count': 0,
            'activity_score': 0,
        }
        
        # Add block node if not already present
        if not self.graph.has_node(node_id):
            # Double-check limit before adding
            if len(self.graph.nodes()) >= MAX_NODES:
                return
            
            # Calculate initial activity score based on tx_count
            activity_score = min(block.tx_count or 0, 100)  # Normalize to 0-100
            
            self.graph.add_node(
                node_id,
                type='block',
                data=block.to_dict(),
                label=f"Block {block.block_height}",
                height=block.block_height,
                tx_count=block.tx_count or 0,
                activity_score=activity_score,
                level=0,  # Block level for hierarchical layout
            )
            
            # Track block sequence
            self.block_heights[block.block_height] = node_id
            if node_id not in self.block_sequence:
                self.block_sequence.append(node_id)
                self.block_sequence.sort(key=lambda bid: self.graph.nodes[bid].get('height', 0))
            
            # Connect to previous block if exists
            prev_height = block.block_height - 1
            if prev_height in self.block_heights:
                prev_block_id = self.block_heights[prev_height]
                if not self.graph.has_edge(prev_block_id, node_id):
                    self.graph.add_edge(
                        prev_block_id,
                        node_id,
                        type='chain',
                        label='prev',
                        weight=1,
                    )
                    self._emit_update('edge_added', edge={
                        'from': prev_block_id,
                        'to': node_id,
                        'type': 'chain'
                    })
            
            self._emit_update('node_added', node={
                'id': node_id,
                'type': 'block',
                'data': block.to_dict(),
                'height': block.block_height,
                'activity_score': activity_score
            })
        
        self.last_update = datetime.now()
    
    def add_transaction(self, transaction: Transaction) -> None:
        """
        Add a transaction node and connect it to related nodes.
        
        Args:
            transaction: Transaction instance to add
        """
        # Check if we've reached the node limit
        if len(self.graph.nodes()) >= MAX_NODES:
            return  # Don't add more nodes if limit reached
        
        tx_id = f"tx_{transaction.tx_hash}"
        
        # Add transaction node if not already present
        if not self.graph.has_node(tx_id):
            # Double-check limit before adding
            if len(self.graph.nodes()) >= MAX_NODES:
                return
            self.graph.add_node(
                tx_id,
                type='transaction',
                data=transaction.to_dict(),
                label=f"Tx {transaction.tx_hash[:16]}...",
            )
            self._emit_update('node_added', node={'id': tx_id, 'type': 'transaction', 'data': transaction.to_dict()})
        
        # Connect transaction to block
        block_id = f"block_{transaction.block_hash}"
        if self.graph.has_node(block_id):
            edge_id = (block_id, tx_id)
            if not self.graph.has_edge(*edge_id):
                self.graph.add_edge(
                    block_id,
                    tx_id,
                    type='block_tx',
                    label='contains',
                )
                self._emit_update('edge_added', edge={'from': block_id, 'to': tx_id, 'type': 'block_tx'})
                
                # Update block metrics
                if block_id in self.block_metrics:
                    self.block_metrics[block_id]['transaction_count'] += 1
                    # Update activity score
                    tx_value = sum(out.amount for out in transaction.outputs)
                    self.block_metrics[block_id]['total_value'] += tx_value
                    self.block_metrics[block_id]['activity_score'] = min(
                        self.block_metrics[block_id]['transaction_count'] * 10 +
                        min(self.block_metrics[block_id]['total_value'] / 1000000, 50),  # Normalize
                        100
                    )
                    # Update node with new metrics
                    if self.graph.has_node(block_id):
                        self.graph.nodes[block_id]['tx_count'] = self.block_metrics[block_id]['transaction_count']
                        self.graph.nodes[block_id]['activity_score'] = self.block_metrics[block_id]['activity_score']
        
        # Connect ALL input addresses to transaction (enhanced for T027)
        for inp in transaction.inputs:
            if inp.address:
                addr_id = f"addr_{inp.address}"
                # Ensure address node exists
                if not self.graph.has_node(addr_id):
                    # Create address node if it doesn't exist
                    from src.models import Address
                    addr = Address(address=inp.address, first_seen=transaction.timestamp)
                    self.add_address(addr)
                    # Update block metrics
                    block_id = f"block_{transaction.block_hash}"
                    if block_id in self.block_metrics:
                        self.block_metrics[block_id]['address_count'] += 1
                
                edge_id = (addr_id, tx_id)
                if not self.graph.has_edge(*edge_id):
                    self.graph.add_edge(
                        addr_id,
                        tx_id,
                        type='tx_input',
                        label='input',
                        title='Transaction Input',
                    )
                    self._emit_update('edge_added', edge={'from': addr_id, 'to': tx_id, 'type': 'tx_input'})
        
        # Connect transaction to ALL output addresses (enhanced for T028)
        for out in transaction.outputs:
            addr_id = f"addr_{out.address}"
            # Ensure address node exists
            if not self.graph.has_node(addr_id):
                # Create address node if it doesn't exist
                from src.models import Address
                addr = Address(address=out.address, first_seen=transaction.timestamp)
                addr.update_stats(received=out.amount)
                self.add_address(addr)
                # Update block metrics
                block_id = f"block_{transaction.block_hash}"
                if block_id in self.block_metrics:
                    self.block_metrics[block_id]['address_count'] += 1
            
            edge_id = (tx_id, addr_id)
            if not self.graph.has_edge(*edge_id):
                # Format amount for display (convert Lovelace to ADA if large)
                amount_label = f"{out.amount:,} L"
                if out.amount >= 1000000:
                    ada_amount = out.amount / 1000000
                    amount_label = f"{ada_amount:.2f} ADA"
                
                self.graph.add_edge(
                    tx_id,
                    addr_id,
                    type='tx_output',
                    label=amount_label,
                    weight=out.amount,
                    title=f'Transaction Output: {amount_label}',
                )
                self._emit_update('edge_added', edge={'from': tx_id, 'to': addr_id, 'type': 'tx_output', 'weight': out.amount, 'label': amount_label})
        
        self.last_update = datetime.now()
    
    def add_address(self, address: Address) -> None:
        """
        Add or update an address node in the graph with statistics aggregation.
        
        Args:
            address: Address instance to add or update
        """
        addr_id = f"addr_{address.address}"
        
        # Add or update address node with aggregation
        if not self.graph.has_node(addr_id):
            # Check if we've reached the node limit
            if len(self.graph.nodes()) >= MAX_NODES:
                return  # Don't add more nodes if limit reached
            # New address - add node
            self.graph.add_node(
                addr_id,
                type='address',
                data=address.to_dict(),
                label=address.address[:16] + '...' if len(address.address) > 16 else address.address,
            )
            self._emit_update('node_added', node={'id': addr_id, 'type': 'address', 'data': address.to_dict()})
        else:
            # Existing address - aggregate statistics
            existing_data = self.graph.nodes[addr_id].get('data', {})
            aggregated_address = Address(
                address=address.address,
                first_seen=address.first_seen or (existing_data.get('first_seen') and datetime.fromisoformat(existing_data['first_seen'].replace('Z', '+00:00'))),
                total_received=(existing_data.get('total_received', 0) or 0) + (address.total_received or 0),
                total_sent=(existing_data.get('total_sent', 0) or 0) + (address.total_sent or 0),
                transaction_count=(existing_data.get('transaction_count', 0) or 0) + (address.transaction_count or 0),
            )
            self.graph.nodes[addr_id]['data'] = aggregated_address.to_dict()
            self.graph.nodes[addr_id]['label'] = f"{address.address[:16]}... (tx: {aggregated_address.transaction_count})"
            self._emit_update('node_updated', node={'id': addr_id, 'type': 'address', 'data': aggregated_address.to_dict()})
        
        self.last_update = datetime.now()
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """
        Get all neighbor nodes (both predecessors and successors).
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of neighbor node IDs
        """
        if not self.graph.has_node(node_id):
            return []
        
        predecessors = list(self.graph.predecessors(node_id))
        successors = list(self.graph.successors(node_id))
        return list(set(predecessors + successors))
    
    def get_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """
        Find a path between two nodes.
        
        Args:
            start_id: Starting node ID
            end_id: Ending node ID
            
        Returns:
            List of node IDs forming the path, or None if no path exists
        """
        try:
            if not self.graph.has_node(start_id) or not self.graph.has_node(end_id):
                return None
            return nx.shortest_path(self.graph, start_id, end_id)
        except nx.NetworkXNoPath:
            return None
    
    def to_pyvis(self) -> Dict[str, Any]:
        """
        Convert NetworkX graph to PyVis-compatible format.
        
        Returns:
            Dictionary with 'nodes' and 'edges' arrays
        """
        nodes = []
        edges = []
        
        # Convert nodes with enhanced metadata
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            node_data = {
                'id': node_id,
                'label': data.get('label', node_id),
                'type': node_type,
                'data': data.get('data', {}),
                'level': data.get('level', 1 if node_type == 'transaction' else 0),
                'height': data.get('height'),
                'tx_count': data.get('tx_count', 0),
                'activity_score': data.get('activity_score', 0),
            }
            # Add metrics if available
            if node_id in self.block_metrics:
                metrics = self.block_metrics[node_id]
                node_data['metrics'] = metrics
            nodes.append(node_data)
        
        # Convert edges
        for source, target, data in self.graph.edges(data=True):
            edge_data = {
                'from': source,
                'to': target,
                'type': data.get('type', 'unknown'),
                'label': data.get('label', ''),
                'weight': data.get('weight', 1),
            }
            edges.append(edge_data)
        
        return {
            'nodes': nodes,
            'edges': edges,
        }
    
    def to_json(self, max_blocks: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert graph to JSON-compatible format for API responses.
        
        Args:
            max_blocks: Maximum number of recent blocks to include (None for all)
        
        Returns:
            Dictionary with nodes, edges, and metadata
        """
        graph_data = self.to_pyvis()
        
        # If max_blocks is specified, filter to show only recent blocks and their connections
        if max_blocks and len(self.block_sequence) > max_blocks:
            # Keep only the most recent blocks
            recent_blocks = set(self.block_sequence[-max_blocks:])
            
            # Filter nodes: keep blocks in recent set, and their connected transactions/addresses
            filtered_nodes = []
            filtered_node_ids = set()
            
            for node in graph_data['nodes']:
                node_id = node['id']
                node_type = node.get('type', 'unknown')
                
                if node_type == 'block':
                    if node_id in recent_blocks:
                        filtered_nodes.append(node)
                        filtered_node_ids.add(node_id)
                else:
                    # For transactions and addresses, check if connected to recent blocks
                    # This will be handled by edge filtering
                    pass
            
            # Add transactions and addresses connected to recent blocks
            for edge in graph_data['edges']:
                from_id = edge['from']
                to_id = edge['to']
                
                # If edge connects to a recent block, include both nodes
                if from_id in filtered_node_ids or to_id in filtered_node_ids:
                    filtered_node_ids.add(from_id)
                    filtered_node_ids.add(to_id)
            
            # Now add all nodes that are in filtered_node_ids
            filtered_nodes = [n for n in graph_data['nodes'] if n['id'] in filtered_node_ids]
            filtered_edges = [e for e in graph_data['edges'] 
                            if e['from'] in filtered_node_ids and e['to'] in filtered_node_ids]
            
            graph_data = {
                'nodes': filtered_nodes,
                'edges': filtered_edges
            }
        
        return {
            'nodes': graph_data['nodes'],
            'edges': graph_data['edges'],
            'metadata': {
                'node_count': len(graph_data['nodes']),
                'edge_count': len(graph_data['edges']),
                'latest_block_height': self._get_latest_block_height(),
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'block_sequence_length': len(self.block_sequence),
            }
        }
    
    def _get_latest_block_height(self) -> Optional[int]:
        """Get the highest block height in the graph."""
        max_height = None
        for node_id, data in self.graph.nodes(data=True):
            if data.get('type') == 'block':
                block_data = data.get('data', {})
                height = block_data.get('block_height')
                if height is not None:
                    if max_height is None or height > max_height:
                        max_height = height
        return max_height
    
    def register_update_callback(self, callback: Callable) -> None:
        """
        Register a callback function to be called on graph updates.
        
        Args:
            callback: Function to call with update event data
        """
        self._update_callbacks.append(callback)
    
    def _emit_update(self, event_type: str, **kwargs) -> None:
        """Emit an update event to all registered callbacks."""
        update_data = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        for callback in self._update_callbacks:
            try:
                callback(update_data)
            except Exception as e:
                print(f"Error in update callback: {e}")

