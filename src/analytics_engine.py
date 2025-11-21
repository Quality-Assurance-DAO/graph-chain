"""Analytics engine for graph analytics calculations."""

from typing import Dict, List, Optional, Any, Callable, Set, Tuple
import networkx as nx
from collections import defaultdict
import math

from src.graph_builder import GraphBuilder


class AnalyticsEngine:
    """Analytics engine that wraps GraphBuilder and provides analytics calculations."""
    
    def __init__(self, graph_builder: GraphBuilder):
        """
        Initialize analytics engine with a GraphBuilder instance.
        
        Args:
            graph_builder: GraphBuilder instance to wrap
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph
        
        # Caching infrastructure with dirty flags
        self._dirty_flags = {
            'degree': True,
            'activity': True,
            'anomaly': True,
            'cluster': True,
            'flow': True,
        }
        
        # Cached metrics
        self._degree_cache: Dict[str, Dict[str, int]] = {}
        self._activity_cache: Dict[str, Dict[str, Any]] = {}
        self._anomaly_cache: Dict[str, Dict[str, Any]] = {}
        self._cluster_cache: Dict[str, Dict[str, Any]] = {}
        
        # Incremental update tracking
        self._changed_nodes: Set[str] = set()
        self._changed_edges: Set[Tuple[str, str]] = set()
        
        # Register update listener
        self.graph_builder.register_update_callback(self._on_graph_update)
    
    def _on_graph_update(self, update_data: Dict[str, Any]) -> None:
        """
        Handle graph update events and mark metrics as dirty.
        
        Args:
            update_data: Update event data from GraphBuilder
        """
        event_type = update_data.get('type')
        
        if event_type == 'node_added':
            node_id = update_data.get('node', {}).get('id')
            if node_id:
                self._changed_nodes.add(node_id)
                # Mark all metrics as dirty
                for key in self._dirty_flags:
                    self._dirty_flags[key] = True
        
        elif event_type == 'edge_added':
            edge = update_data.get('edge', {})
            from_node = edge.get('from')
            to_node = edge.get('to')
            if from_node and to_node:
                self._changed_edges.add((from_node, to_node))
                # Mark degree and activity metrics as dirty
                self._dirty_flags['degree'] = True
                self._dirty_flags['activity'] = True
                # Also mark nodes as changed
                self._changed_nodes.add(from_node)
                self._changed_nodes.add(to_node)
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate statistical measures (mean, std, percentiles) for a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dictionary with mean, std, percentile_5, percentile_95
        """
        if not values:
            return {
                'mean': 0.0,
                'std': 0.0,
                'percentile_5': 0.0,
                'percentile_95': 0.0,
            }
        
        # Use Python standard library for statistics
        import statistics
        
        mean = statistics.mean(values)
        
        # Calculate standard deviation
        if len(values) > 1:
            std = statistics.stdev(values)
        else:
            std = 0.0
        
        # Calculate percentiles
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n == 1:
            percentile_5 = sorted_values[0]
            percentile_95 = sorted_values[0]
        else:
            idx_5 = max(0, int(0.05 * n))
            idx_95 = min(n - 1, int(0.95 * n))
            percentile_5 = sorted_values[idx_5]
            percentile_95 = sorted_values[idx_95]
        
        return {
            'mean': mean,
            'std': std,
            'percentile_5': percentile_5,
            'percentile_95': percentile_95,
        }
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[int, int, int]:
        """
        Convert HSL color to RGB.
        
        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            l: Lightness (0-100)
            
        Returns:
            RGB tuple (0-255, 0-255, 0-255)
        """
        # Normalize HSL values
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        if s == 0:
            # Grayscale
            r = g = b = int(l * 255)
        else:
            def hue_to_rgb(p, q, t):
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1/6:
                    return p + (q - p) * 6 * t
                if t < 1/2:
                    return q
                if t < 2/3:
                    return p + (q - p) * (2/3 - t) * 6
                return p
            
            if l < 0.5:
                q = l * (1 + s)
            else:
                q = l + s - l * s
            p = 2 * l - q
            
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
            
            r = int(max(0, min(255, r * 255)))
            g = int(max(0, min(255, g * 255)))
            b = int(max(0, min(255, b * 255)))
        
        return (r, g, b)
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """
        Convert RGB to hex color code.
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            
        Returns:
            Hex color string (e.g., "#FF5733")
        """
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _map_color_scheme(self, normalized_value: float, color_scheme: str = 'heatmap') -> Tuple[float, float, float]:
        """
        Map normalized activity value (0-100) to HSL color based on color scheme.
        
        Args:
            normalized_value: Normalized activity value (0-100)
            color_scheme: Color scheme name ('heatmap', 'activity', 'grayscale')
            
        Returns:
            HSL tuple (hue, saturation, lightness)
        """
        normalized_value = max(0, min(100, normalized_value))
        
        if color_scheme == 'heatmap':
            # Red (low) → Yellow (medium) → Green (high)
            # Hue: 0 (red) → 60 (yellow) → 120 (green)
            hue = normalized_value * 1.2  # 0-120
            saturation = 80 + (normalized_value * 0.2)  # 80-100
            lightness = 50 - (normalized_value * 0.2)  # 50-30
        
        elif color_scheme == 'activity':
            # Blue (low) → Purple (medium) → Red (high)
            # Hue: 240 (blue) → 300 (purple) → 0/360 (red)
            hue = 240 - (normalized_value * 2.4)  # 240 → 0
            if hue < 0:
                hue += 360
            saturation = 70 + (normalized_value * 0.3)  # 70-100
            lightness = 50 - (normalized_value * 0.15)  # 50-35
        
        elif color_scheme == 'grayscale':
            # Black (low) → Gray (medium) → White (high)
            hue = 0  # Not used for grayscale
            saturation = 0  # No saturation for grayscale
            lightness = normalized_value  # 0-100
        
        else:
            # Default to heatmap
            hue = normalized_value * 1.2
            saturation = 80 + (normalized_value * 0.2)
            lightness = 50 - (normalized_value * 0.2)
        
        return (hue, saturation, lightness)
    
    def calculate_node_degrees(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate in_degree, out_degree, and total_degree for all nodes.
        
        Returns:
            Dictionary mapping node_id to degree metrics
        """
        if not self._dirty_flags['degree'] and self._degree_cache:
            return self._degree_cache
        
        degree_metrics = {}
        
        for node_id in self.graph.nodes():
            in_degree = self.graph.in_degree(node_id)
            out_degree = self.graph.out_degree(node_id)
            total_degree = in_degree + out_degree
            
            degree_metrics[node_id] = {
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_degree': total_degree,
            }
        
        self._degree_cache = degree_metrics
        self._dirty_flags['degree'] = False
        return degree_metrics
    
    def calculate_type_specific_degree(self, node_id: str) -> int:
        """
        Calculate type-specific degree for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Type-specific degree count
        """
        if not self.graph.has_node(node_id):
            return 0
        
        node_type = self.graph.nodes[node_id].get('type')
        
        if node_type == 'block':
            # Count block_tx edges (transactions in block)
            count = sum(1 for _, _, edge_type in self.graph.out_edges(node_id, data='type')
                       if edge_type == 'block_tx')
            return count
        
        elif node_type == 'transaction':
            # Count tx_input edges (inputs) + tx_output edges (outputs)
            input_count = sum(1 for _, _, edge_type in self.graph.in_edges(node_id, data='type')
                            if edge_type == 'tx_input')
            output_count = sum(1 for _, _, edge_type in self.graph.out_edges(node_id, data='type')
                             if edge_type == 'tx_output')
            return input_count + output_count
        
        elif node_type == 'address':
            # Count edges where address participates (UTxO count)
            count = sum(1 for _ in self.graph.edges(node_id))
            return count
        
        return 0
    
    def store_degree_metrics(self) -> None:
        """Store degree metrics as node attributes in NetworkX graph."""
        degree_metrics = self.calculate_node_degrees()
        
        for node_id, metrics in degree_metrics.items():
            if self.graph.has_node(node_id):
                type_degree = self.calculate_type_specific_degree(node_id)
                self.graph.nodes[node_id]['degree'] = metrics['total_degree']
                self.graph.nodes[node_id]['in_degree'] = metrics['in_degree']
                self.graph.nodes[node_id]['out_degree'] = metrics['out_degree']
                self.graph.nodes[node_id]['type_degree'] = type_degree
    
    def get_degree_metrics(self, node_type: Optional[str] = None, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get degree metrics filtered by node_type or node_id.
        
        Args:
            node_type: Filter by node type ('block', 'transaction', 'address')
            node_id: Filter by specific node ID
            
        Returns:
            List of degree metric dictionaries
        """
        self.store_degree_metrics()
        
        results = []
        
        for nid in self.graph.nodes():
            # Apply filters
            if node_id and nid != node_id:
                continue
            
            node_data = self.graph.nodes[nid]
            if node_type and node_data.get('type') != node_type:
                continue
            
            type_degree = self.calculate_type_specific_degree(nid)
            
            results.append({
                'node_id': nid,
                'node_type': node_data.get('type', 'unknown'),
                'in_degree': node_data.get('in_degree', 0),
                'out_degree': node_data.get('out_degree', 0),
                'total_degree': node_data.get('degree', 0),
                'type_degree': type_degree,
            })
        
        return results
    
    def calculate_activity_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate raw activity values for all nodes.
        
        Returns:
            Dictionary mapping node_id to activity metrics
        """
        activity_metrics = {}
        
        for node_id in self.graph.nodes():
            node_type = self.graph.nodes[node_id].get('type')
            raw_value = 0
            
            if node_type == 'block':
                # Transaction count for blocks
                raw_value = self.calculate_type_specific_degree(node_id)
            
            elif node_type == 'transaction':
                # Input + output count for transactions
                raw_value = self.calculate_type_specific_degree(node_id)
            
            elif node_type == 'address':
                # UTxO count for addresses
                raw_value = self.calculate_type_specific_degree(node_id)
            
            activity_metrics[node_id] = {
                'raw_value': raw_value,
                'node_type': node_type,
            }
        
        return activity_metrics
    
    def normalize_activity_values(self, activity_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Normalize activity values to 0-100 scale per metric type independently.
        
        Args:
            activity_metrics: Dictionary of raw activity metrics
            
        Returns:
            Dictionary with normalized values added
        """
        # Group by node type for independent normalization
        by_type: Dict[str, List[float]] = defaultdict(list)
        node_to_type: Dict[str, str] = {}
        
        for node_id, metrics in activity_metrics.items():
            node_type = metrics['node_type']
            raw_value = metrics['raw_value']
            by_type[node_type].append(raw_value)
            node_to_type[node_id] = node_type
        
        # Calculate min/max per type
        type_stats: Dict[str, Dict[str, float]] = {}
        for node_type, values in by_type.items():
            if values:
                type_stats[node_type] = {
                    'min': min(values),
                    'max': max(values),
                }
            else:
                type_stats[node_type] = {'min': 0, 'max': 0}
        
        # Normalize each node
        normalized_metrics = {}
        for node_id, metrics in activity_metrics.items():
            node_type = metrics['node_type']
            raw_value = metrics['raw_value']
            
            stats = type_stats[node_type]
            min_val = stats['min']
            max_val = stats['max']
            
            # Handle edge case: all values identical
            if max_val == min_val:
                normalized_value = 50.0  # Middle value
            else:
                normalized_value = ((raw_value - min_val) / (max_val - min_val)) * 100
            
            normalized_metrics[node_id] = {
                **metrics,
                'normalized_value': normalized_value,
                'min_value': min_val,
                'max_value': max_val,
            }
        
        return normalized_metrics
    
    def apply_color_coding(self, normalized_metrics: Dict[str, Dict[str, Any]], color_scheme: str = 'heatmap') -> Dict[str, Dict[str, Any]]:
        """
        Map normalized activity values to HSL colors and convert to hex.
        
        Args:
            normalized_metrics: Dictionary with normalized activity metrics
            color_scheme: Color scheme name ('heatmap', 'activity', 'grayscale')
            
        Returns:
            Dictionary with color mappings added
        """
        colored_metrics = {}
        
        for node_id, metrics in normalized_metrics.items():
            normalized_value = metrics['normalized_value']
            
            # Map to HSL
            hue, saturation, lightness = self._map_color_scheme(normalized_value, color_scheme)
            
            # Convert to RGB
            r, g, b = self._hsl_to_rgb(hue, saturation, lightness)
            
            # Convert to hex
            color_hex = self._rgb_to_hex(r, g, b)
            
            colored_metrics[node_id] = {
                **metrics,
                'color_hex': color_hex,
                'color_hsl': {
                    'hue': hue,
                    'saturation': saturation,
                    'lightness': lightness,
                },
            }
        
        return colored_metrics
    
    def store_color_attributes(self, colored_metrics: Dict[str, Dict[str, Any]], color_scheme: str = 'heatmap') -> None:
        """
        Store color_hex and color_scheme as node attributes in NetworkX graph.
        
        Args:
            colored_metrics: Dictionary with color mappings
            color_scheme: Color scheme name
        """
        for node_id, metrics in colored_metrics.items():
            if self.graph.has_node(node_id):
                self.graph.nodes[node_id]['color'] = metrics['color_hex']
                self.graph.nodes[node_id]['color_scheme'] = color_scheme
                self.graph.nodes[node_id]['activity_score'] = metrics['normalized_value']
    
    def get_activity_metrics(self, node_type: Optional[str] = None, color_scheme: str = 'heatmap') -> List[Dict[str, Any]]:
        """
        Get activity metrics and color mappings filtered by node_type and color_scheme.
        
        Args:
            node_type: Filter by node type
            color_scheme: Color scheme to use
            
        Returns:
            List of activity metric dictionaries
        """
        # Calculate raw activity
        activity_metrics = self.calculate_activity_metrics()
        
        # Normalize
        normalized_metrics = self.normalize_activity_values(activity_metrics)
        
        # Apply color coding
        colored_metrics = self.apply_color_coding(normalized_metrics, color_scheme)
        
        # Store as attributes
        self.store_color_attributes(colored_metrics, color_scheme)
        
        # Filter results
        results = []
        for node_id, metrics in colored_metrics.items():
            if node_type and metrics['node_type'] != node_type:
                continue
            
            results.append({
                'node_id': node_id,
                'node_type': metrics['node_type'],
                'raw_value': metrics['raw_value'],
                'normalized_value': metrics['normalized_value'],
                'color_hex': metrics['color_hex'],
                'color_hsl': metrics['color_hsl'],
            })
        
        return results
    
    def calculate_statistics(self, node_type: str, metric_type: str) -> Dict[str, float]:
        """
        Calculate mean, std, percentiles for transaction values or block transaction counts.
        
        Args:
            node_type: Type of nodes to analyze ('block' or 'transaction')
            metric_type: Type of metric ('transaction_count' for blocks, 'value' for transactions)
            
        Returns:
            Dictionary with statistical measures
        """
        values = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') != node_type:
                continue
            
            if metric_type == 'transaction_count' and node_type == 'block':
                # Get transaction count for block
                value = self.calculate_type_specific_degree(node_id)
                values.append(float(value))
            
            elif metric_type == 'value' and node_type == 'transaction':
                # Get transaction value (sum of outputs)
                total_value = 0
                for _, _, edge_data in self.graph.out_edges(node_id, data=True):
                    if edge_data.get('type') == 'tx_output':
                        weight = edge_data.get('weight', 0)
                        total_value += weight
                values.append(float(total_value))
        
        return self._calculate_statistics(values)
    
    def detect_anomalies_zscore(self, node_type: str, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Flag nodes where |value - mean| > threshold * std.
        
        Args:
            node_type: Type of nodes to analyze ('block' or 'transaction')
            threshold: Z-score threshold (default 2.0)
            
        Returns:
            List of anomaly detection results
        """
        if node_type == 'block':
            stats = self.calculate_statistics('block', 'transaction_count')
            metric_type = 'transaction_count'
        elif node_type == 'transaction':
            stats = self.calculate_statistics('transaction', 'value')
            metric_type = 'value'
        else:
            return []
        
        mean = stats['mean']
        std = stats['std']
        
        if std == 0:
            return []  # No variation, no anomalies
        
        anomalies = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') != node_type:
                continue
            
            if metric_type == 'transaction_count':
                actual_value = float(self.calculate_type_specific_degree(node_id))
                anomaly_type = 'high_transaction_count'
            else:
                total_value = 0
                for _, _, edge_data in self.graph.out_edges(node_id, data=True):
                    if edge_data.get('type') == 'tx_output':
                        total_value += edge_data.get('weight', 0)
                actual_value = float(total_value)
                anomaly_type = 'high_transaction_value'
            
            z_score = abs(actual_value - mean) / std if std > 0 else 0
            is_anomaly = z_score > threshold
            
            if is_anomaly:
                # Calculate anomaly score (0-100)
                anomaly_score = min(100, (z_score / threshold) * 50)
                
                anomalies.append({
                    'node_id': node_id,
                    'node_type': node_type,
                    'is_anomaly': True,
                    'anomaly_score': anomaly_score,
                    'anomaly_type': anomaly_type,
                    'actual_value': actual_value,
                    'detection_method': 'zscore',
                    'threshold_value': threshold * std,
                })
        
        return anomalies
    
    def detect_anomalies_percentile(self, node_type: str) -> List[Dict[str, Any]]:
        """
        Flag nodes above 95th percentile or below 5th percentile.
        
        Args:
            node_type: Type of nodes to analyze ('block' or 'transaction')
            
        Returns:
            List of anomaly detection results
        """
        if node_type == 'block':
            stats = self.calculate_statistics('block', 'transaction_count')
            metric_type = 'transaction_count'
        elif node_type == 'transaction':
            stats = self.calculate_statistics('transaction', 'value')
            metric_type = 'value'
        else:
            return []
        
        p95 = stats['percentile_95']
        p5 = stats['percentile_5']
        
        anomalies = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') != node_type:
                continue
            
            if metric_type == 'transaction_count':
                actual_value = float(self.calculate_type_specific_degree(node_id))
                anomaly_type = 'high_transaction_count'
            else:
                total_value = 0
                for _, _, edge_data in self.graph.out_edges(node_id, data=True):
                    if edge_data.get('type') == 'tx_output':
                        total_value += edge_data.get('weight', 0)
                actual_value = float(total_value)
                anomaly_type = 'high_transaction_value'
            
            is_anomaly = actual_value > p95 or actual_value < p5
            
            if is_anomaly:
                # Calculate anomaly score based on distance from percentile
                if actual_value > p95:
                    score_factor = (actual_value - p95) / (p95 - stats['mean']) if p95 > stats['mean'] else 1.0
                else:
                    score_factor = (p5 - actual_value) / (stats['mean'] - p5) if stats['mean'] > p5 else 1.0
                
                anomaly_score = min(100, 50 + (score_factor * 50))
                
                anomalies.append({
                    'node_id': node_id,
                    'node_type': node_type,
                    'is_anomaly': True,
                    'anomaly_score': anomaly_score,
                    'anomaly_type': anomaly_type,
                    'actual_value': actual_value,
                    'detection_method': 'percentile',
                    'threshold_value': p95 if actual_value > p95 else p5,
                })
        
        return anomalies
    
    def detect_anomalies_threshold(self, node_type: str, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Flag nodes where value > threshold * average.
        
        Args:
            node_type: Type of nodes to analyze ('block' or 'transaction')
            threshold: Threshold multiplier (default 2.0)
            
        Returns:
            List of anomaly detection results
        """
        if node_type == 'block':
            stats = self.calculate_statistics('block', 'transaction_count')
            metric_type = 'transaction_count'
        elif node_type == 'transaction':
            stats = self.calculate_statistics('transaction', 'value')
            metric_type = 'value'
        else:
            return []
        
        mean = stats['mean']
        threshold_value = threshold * mean
        
        anomalies = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') != node_type:
                continue
            
            if metric_type == 'transaction_count':
                actual_value = float(self.calculate_type_specific_degree(node_id))
                anomaly_type = 'high_transaction_count'
            else:
                total_value = 0
                for _, _, edge_data in self.graph.out_edges(node_id, data=True):
                    if edge_data.get('type') == 'tx_output':
                        total_value += edge_data.get('weight', 0)
                actual_value = float(total_value)
                anomaly_type = 'high_transaction_value'
            
            is_anomaly = actual_value > threshold_value
            
            if is_anomaly:
                # Calculate anomaly score
                score_factor = (actual_value - threshold_value) / threshold_value if threshold_value > 0 else 1.0
                anomaly_score = min(100, 50 + (score_factor * 50))
                
                anomalies.append({
                    'node_id': node_id,
                    'node_type': node_type,
                    'is_anomaly': True,
                    'anomaly_score': anomaly_score,
                    'anomaly_type': anomaly_type,
                    'actual_value': actual_value,
                    'detection_method': 'threshold',
                    'threshold_value': threshold_value,
                })
        
        return anomalies
    
    def detect_anomalies(self, node_type: Optional[str] = None, method: str = 'percentile', threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Unified anomaly detection method that selects appropriate detection method.
        
        Args:
            node_type: Filter by node type ('block' or 'transaction')
            method: Detection method ('zscore', 'percentile', 'threshold')
            threshold: Threshold for zscore or threshold methods
            
        Returns:
            List of anomaly detection results
        """
        # Check minimum node count
        node_types_to_check = [node_type] if node_type else ['block', 'transaction']
        
        all_anomalies = []
        
        for nt in node_types_to_check:
            node_count = sum(1 for nid in self.graph.nodes() if self.graph.nodes[nid].get('type') == nt)
            
            if node_count < 10:
                # Skip if insufficient data
                continue
            
            if method == 'zscore':
                anomalies = self.detect_anomalies_zscore(nt, threshold)
            elif method == 'percentile':
                anomalies = self.detect_anomalies_percentile(nt)
            elif method == 'threshold':
                anomalies = self.detect_anomalies_threshold(nt, threshold)
            else:
                anomalies = []
            
            all_anomalies.extend(anomalies)
        
        return all_anomalies
    
    def store_anomaly_attributes(self, anomalies: List[Dict[str, Any]]) -> None:
        """
        Store is_anomaly, anomaly_score, anomaly_type as node attributes.
        
        Args:
            anomalies: List of anomaly detection results
        """
        # First, clear all anomaly flags
        for node_id in self.graph.nodes():
            self.graph.nodes[node_id]['is_anomaly'] = False
            self.graph.nodes[node_id]['anomaly_score'] = 0.0
            self.graph.nodes[node_id]['anomaly_type'] = None
        
        # Set anomaly attributes
        for anomaly in anomalies:
            node_id = anomaly['node_id']
            if self.graph.has_node(node_id):
                self.graph.nodes[node_id]['is_anomaly'] = True
                self.graph.nodes[node_id]['anomaly_score'] = anomaly['anomaly_score']
                self.graph.nodes[node_id]['anomaly_type'] = anomaly['anomaly_type']
    
    def get_anomalies(self, node_type: Optional[str] = None, method: str = 'percentile', threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Get anomaly detection results filtered by node_type and method.
        
        Args:
            node_type: Filter by node type
            method: Detection method
            threshold: Threshold parameter
            
        Returns:
            List of anomaly results
        """
        anomalies = self.detect_anomalies(node_type, method, threshold)
        self.store_anomaly_attributes(anomalies)
        return anomalies
    
    def get_recent_blocks(self, time_window_blocks: int = 30) -> Set[str]:
        """
        Filter graph to nodes from last N blocks.
        
        Args:
            time_window_blocks: Number of recent blocks to include
            
        Returns:
            Set of node IDs from recent blocks
        """
        # Get block nodes sorted by height
        block_nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') == 'block':
                height = node_data.get('height', 0)
                block_nodes.append((height, node_id))
        
        if not block_nodes:
            return set()
        
        # Sort by height descending
        block_nodes.sort(reverse=True)
        
        # Get recent blocks
        recent_block_ids = set()
        for height, node_id in block_nodes[:time_window_blocks]:
            recent_block_ids.add(node_id)
        
        # Get all nodes connected to recent blocks
        recent_nodes = set(recent_block_ids)
        
        for block_id in recent_block_ids:
            # Add transactions in these blocks
            for _, tx_id, edge_data in self.graph.out_edges(block_id, data=True):
                if edge_data.get('type') == 'block_tx':
                    recent_nodes.add(tx_id)
            
            # Add addresses connected to transactions in these blocks
            for _, tx_id, edge_data in self.graph.out_edges(block_id, data=True):
                if edge_data.get('type') == 'block_tx':
                    # Get addresses connected to this transaction
                    for addr_id, _, edge_data2 in self.graph.in_edges(tx_id, data=True):
                        if edge_data2.get('type') == 'tx_input':
                            recent_nodes.add(addr_id)
                    for _, addr_id, edge_data2 in self.graph.out_edges(tx_id, data=True):
                        if edge_data2.get('type') == 'tx_output':
                            recent_nodes.add(addr_id)
        
        return recent_nodes
    
    def create_address_subgraph(self, recent_nodes: Set[str]) -> nx.Graph:
        """
        Create undirected subgraph of address-address connections.
        
        Args:
            recent_nodes: Set of node IDs from recent blocks
            
        Returns:
            Undirected NetworkX graph
        """
        subgraph = nx.Graph()
        
        # Add address nodes
        address_nodes = [nid for nid in recent_nodes if self.graph.nodes[nid].get('type') == 'address']
        
        for addr_id in address_nodes:
            subgraph.add_node(addr_id)
        
        # Add edges between addresses that share transactions
        for tx_id in recent_nodes:
            if self.graph.nodes[tx_id].get('type') != 'transaction':
                continue
            
            # Get all addresses connected to this transaction
            input_addresses = []
            output_addresses = []
            
            for addr_id, _, edge_data in self.graph.in_edges(tx_id, data=True):
                if edge_data.get('type') == 'tx_input' and addr_id in address_nodes:
                    input_addresses.append(addr_id)
            
            for _, addr_id, edge_data in self.graph.out_edges(tx_id, data=True):
                if edge_data.get('type') == 'tx_output' and addr_id in address_nodes:
                    output_addresses.append(addr_id)
            
            # Connect all addresses that interact through this transaction
            all_addresses = input_addresses + output_addresses
            for i, addr1 in enumerate(all_addresses):
                for addr2 in all_addresses[i+1:]:
                    if not subgraph.has_edge(addr1, addr2):
                        subgraph.add_edge(addr1, addr2)
        
        return subgraph
    
    def create_transaction_subgraph(self, recent_nodes: Set[str]) -> nx.Graph:
        """
        Create undirected subgraph of transaction-transaction connections.
        
        Args:
            recent_nodes: Set of node IDs from recent blocks
            
        Returns:
            Undirected NetworkX graph
        """
        subgraph = nx.Graph()
        
        # Add transaction nodes
        transaction_nodes = [nid for nid in recent_nodes if self.graph.nodes[nid].get('type') == 'transaction']
        
        for tx_id in transaction_nodes:
            subgraph.add_node(tx_id)
        
        # Connect transactions that share addresses
        address_to_txs: Dict[str, List[str]] = defaultdict(list)
        
        for tx_id in transaction_nodes:
            # Get addresses connected to this transaction
            for addr_id, _, edge_data in self.graph.in_edges(tx_id, data=True):
                if edge_data.get('type') == 'tx_input':
                    address_to_txs[addr_id].append(tx_id)
            
            for _, addr_id, edge_data in self.graph.out_edges(tx_id, data=True):
                if edge_data.get('type') == 'tx_output':
                    address_to_txs[addr_id].append(tx_id)
        
        # Connect transactions that share addresses
        for addr_id, tx_list in address_to_txs.items():
            for i, tx1 in enumerate(tx_list):
                for tx2 in tx_list[i+1:]:
                    if not subgraph.has_edge(tx1, tx2):
                        subgraph.add_edge(tx1, tx2)
        
        return subgraph
    
    def cluster_addresses(self, time_window_blocks: int = 30) -> Dict[int, List[str]]:
        """
        Cluster addresses using NetworkX community detection.
        
        Args:
            time_window_blocks: Number of recent blocks to analyze
            
        Returns:
            Dictionary mapping cluster_id to list of node IDs
        """
        recent_nodes = self.get_recent_blocks(time_window_blocks)
        subgraph = self.create_address_subgraph(recent_nodes)
        
        if len(subgraph.nodes()) < 2:
            return {}
        
        # Use greedy modularity communities
        try:
            communities = nx.community.greedy_modularity_communities(subgraph)
        except Exception:
            return {}
        
        cluster_map = {}
        for cluster_id, community in enumerate(communities):
            cluster_map[cluster_id] = list(community)
        
        return cluster_map
    
    def cluster_transactions(self, time_window_blocks: int = 30) -> Dict[int, List[str]]:
        """
        Cluster transactions using NetworkX community detection.
        
        Args:
            time_window_blocks: Number of recent blocks to analyze
            
        Returns:
            Dictionary mapping cluster_id to list of node IDs
        """
        recent_nodes = self.get_recent_blocks(time_window_blocks)
        subgraph = self.create_transaction_subgraph(recent_nodes)
        
        if len(subgraph.nodes()) < 2:
            return {}
        
        # Use greedy modularity communities
        try:
            communities = nx.community.greedy_modularity_communities(subgraph)
        except Exception:
            return {}
        
        cluster_map = {}
        for cluster_id, community in enumerate(communities):
            cluster_map[cluster_id] = list(community)
        
        return cluster_map
    
    def store_cluster_attributes(self, clusters: Dict[int, List[str]], cluster_type: str) -> None:
        """
        Assign cluster_id, cluster_type, cluster_color as node attributes.
        
        Args:
            clusters: Dictionary mapping cluster_id to node IDs
            cluster_type: Type of clustering ('address' or 'transaction')
        """
        # Clear existing cluster attributes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('cluster_type') == cluster_type:
                self.graph.nodes[node_id]['cluster_id'] = -1
                self.graph.nodes[node_id]['cluster_type'] = None
                self.graph.nodes[node_id]['cluster_color'] = None
        
        # Assign cluster colors
        colors = [
            '#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33',
            '#33FFF5', '#FF8C33', '#8C33FF', '#33FF8C', '#FF338C'
        ]
        
        for cluster_id, node_ids in clusters.items():
            color = colors[cluster_id % len(colors)]
            
            for node_id in node_ids:
                if self.graph.has_node(node_id):
                    self.graph.nodes[node_id]['cluster_id'] = cluster_id
                    self.graph.nodes[node_id]['cluster_type'] = cluster_type
                    self.graph.nodes[node_id]['cluster_color'] = color
    
    def get_clusters(self, cluster_type: str, time_window_blocks: int = 30) -> Dict[str, Any]:
        """
        Get cluster assignments filtered by cluster_type and time_window_blocks.
        
        Args:
            cluster_type: Type of clustering ('address' or 'transaction')
            time_window_blocks: Number of recent blocks to analyze
            
        Returns:
            Dictionary with cluster information
        """
        if cluster_type == 'address':
            clusters = self.cluster_addresses(time_window_blocks)
        elif cluster_type == 'transaction':
            clusters = self.cluster_transactions(time_window_blocks)
        else:
            clusters = {}
        
        self.store_cluster_attributes(clusters, cluster_type)
        
        # Format response
        cluster_list = []
        colors = [
            '#FF5733', '#33FF57', '#3357FF', '#33FFF5', '#FF33F5',
            '#F5FF33', '#FF8C33', '#8C33FF', '#33FF8C', '#FF338C'
        ]
        
        total_nodes_clustered = 0
        for cluster_id, node_ids in clusters.items():
            color = colors[cluster_id % len(colors)]
            cluster_list.append({
                'cluster_id': cluster_id,
                'node_ids': node_ids,
                'size': len(node_ids),
                'color_hex': color,
            })
            total_nodes_clustered += len(node_ids)
        
        return {
            'clusters': cluster_list,
            'cluster_type': cluster_type,
            'time_window_blocks': time_window_blocks,
            'total_clusters': len(clusters),
            'nodes_clustered': total_nodes_clustered,
        }
    
    def find_flow_paths_from_address(self, start_address: str, max_depth: int = 5, max_blocks: int = 5) -> List[Dict[str, Any]]:
        """
        Find paths from input addresses through transactions to output addresses.
        
        Args:
            start_address: Starting address node ID
            max_depth: Maximum path depth (hops)
            max_blocks: Maximum number of recent blocks to analyze
            
        Returns:
            List of flow path dictionaries
        """
        if not self.graph.has_node(start_address):
            return []
        
        # Get recent blocks
        recent_nodes = self.get_recent_blocks(max_blocks)
        
        if start_address not in recent_nodes:
            return []
        
        paths = []
        
        # Find transactions where this address is an input
        input_txs = []
        for tx_id, _, edge_data in self.graph.out_edges(start_address, data=True):
            if edge_data.get('type') == 'tx_input' and tx_id in recent_nodes:
                input_txs.append(tx_id)
        
        # For each transaction, find paths to output addresses
        for tx_id in input_txs:
            # Get output addresses from this transaction
            output_addresses = []
            for _, addr_id, edge_data in self.graph.out_edges(tx_id, data=True):
                if edge_data.get('type') == 'tx_output' and addr_id in recent_nodes:
                    output_addresses.append(addr_id)
            
            # Create paths
            for output_addr in output_addresses:
                path_nodes = [start_address, tx_id, output_addr]
                path_edges = [
                    {'from': start_address, 'to': tx_id, 'value': 0},
                    {'from': tx_id, 'to': output_addr, 'value': self.graph.edges[tx_id, output_addr].get('weight', 0)},
                ]
                
                total_value = sum(e['value'] for e in path_edges)
                
                paths.append({
                    'path_id': f"flow_{start_address}_{tx_id}_{output_addr}",
                    'start_address': start_address,
                    'end_address': output_addr,
                    'path_nodes': path_nodes,
                    'path_edges': path_edges,
                    'total_value': total_value,
                    'path_length': len(path_nodes) - 1,
                    'is_complete': True,
                })
        
        return paths
    
    def find_flow_paths_from_transaction(self, transaction_id: str, max_depth: int = 5, max_blocks: int = 5) -> List[Dict[str, Any]]:
        """
        Find flow paths when user clicks a transaction node.
        
        Args:
            transaction_id: Transaction node ID
            max_depth: Maximum path depth
            max_blocks: Maximum number of recent blocks
            
        Returns:
            List of flow path dictionaries
        """
        if not self.graph.has_node(transaction_id):
            return []
        
        # Get recent blocks
        recent_nodes = self.get_recent_blocks(max_blocks)
        
        if transaction_id not in recent_nodes:
            return []
        
        paths = []
        
        # Get input addresses
        input_addresses = []
        for addr_id, _, edge_data in self.graph.in_edges(transaction_id, data=True):
            if edge_data.get('type') == 'tx_input' and addr_id in recent_nodes:
                input_addresses.append(addr_id)
        
        # Get output addresses
        output_addresses = []
        for _, addr_id, edge_data in self.graph.out_edges(transaction_id, data=True):
            if edge_data.get('type') == 'tx_output' and addr_id in recent_nodes:
                output_addresses.append(addr_id)
        
        # Create paths from each input to each output
        for input_addr in input_addresses:
            for output_addr in output_addresses:
                path_nodes = [input_addr, transaction_id, output_addr]
                path_edges = [
                    {'from': input_addr, 'to': transaction_id, 'value': 0},
                    {'from': transaction_id, 'to': output_addr, 'value': self.graph.edges[transaction_id, output_addr].get('weight', 0)},
                ]
                
                total_value = sum(e['value'] for e in path_edges)
                
                paths.append({
                    'path_id': f"flow_{input_addr}_{transaction_id}_{output_addr}",
                    'start_address': input_addr,
                    'end_address': output_addr,
                    'path_nodes': path_nodes,
                    'path_edges': path_edges,
                    'total_value': total_value,
                    'path_length': len(path_nodes) - 1,
                    'is_complete': True,
                })
        
        return paths
    
    def aggregate_path_values(self, path_edges: List[Dict[str, Any]]) -> int:
        """
        Sum edge weights (transaction output amounts) along flow paths.
        
        Args:
            path_edges: List of edge dictionaries with 'value' keys
            
        Returns:
            Total value along path
        """
        return sum(edge.get('value', 0) for edge in path_edges)
    
    def limit_path_depth(self, paths: List[Dict[str, Any]], max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Limit paths to max_depth and filter to recent blocks.
        
        Args:
            paths: List of path dictionaries
            max_depth: Maximum path depth
            
        Returns:
            Filtered list of paths
        """
        return [p for p in paths if p['path_length'] <= max_depth]
    
    def get_flow_paths(self, start_address: Optional[str] = None, transaction_id: Optional[str] = None,
                      max_depth: int = 5, max_blocks: int = 5) -> List[Dict[str, Any]]:
        """
        Get flow paths filtered by start_address, transaction_id, max_depth, and max_blocks.
        
        Args:
            start_address: Starting address node ID
            transaction_id: Transaction node ID
            max_depth: Maximum path depth
            max_blocks: Maximum number of recent blocks
            
        Returns:
            List of flow path dictionaries
        """
        if transaction_id:
            paths = self.find_flow_paths_from_transaction(transaction_id, max_depth, max_blocks)
        elif start_address:
            paths = self.find_flow_paths_from_address(start_address, max_depth, max_blocks)
        else:
            # Get all flow paths from all addresses in recent blocks
            recent_nodes = self.get_recent_blocks(max_blocks)
            address_nodes = [nid for nid in recent_nodes if self.graph.nodes[nid].get('type') == 'address']
            
            paths = []
            for addr_id in address_nodes:
                addr_paths = self.find_flow_paths_from_address(addr_id, max_depth, max_blocks)
                paths.extend(addr_paths)
        
        # Limit depth
        paths = self.limit_path_depth(paths, max_depth)
        
        return paths

