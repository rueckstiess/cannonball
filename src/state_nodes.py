from typing import Optional, List, Dict, Any, Set, Union, ClassVar, Literal, Tuple
from enum import Enum
from datetime import datetime

from base_classes import Node, Element, Thought

class NodeState(Enum):
    """Enumeration of possible node states."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class StateProducerNode(Node):
    """Base class for nodes that generate their own state.
    
    These are nodes that have an explicitly tracked state, such as Tasks
    and Decisions. Their state is directly set rather than derived from children.
    """
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 state: NodeState = NodeState.OPEN):
        """Initialize a new StateProducerNode.
        
        Args:
            text: The text content of the node
            node_type: The type of node (see NODE_TYPES)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            state: Initial state of the node
        """
        super().__init__(text, node_type, parent, id, ref_marker, metadata)
        self.state = state
        self.state_history: List[Tuple[NodeState, datetime]] = [(state, datetime.utcnow())]
    
    def get_state(self) -> NodeState:
        """Get the current state of this node.
        
        Returns:
            NodeState: The current state
        """
        return self.state
    
    def set_state(self, state: NodeState) -> None:
        """Set the state of this node.
        
        Args:
            state: The new state
        """
        if self.state != state:
            self.state = state
            self.state_history.append((state, datetime.utcnow()))
            self.updated_at = datetime.utcnow()
            
            # Update blocking status based on state
            self._update_blocking_status()
    
    def _update_blocking_status(self) -> None:
        """Update the blocking status based on the current state.
        
        By default, a node is blocking if it's not in the DONE state.
        Override in subclasses for specific behavior.
        """
        self.blocking = self.state != NodeState.DONE and self.state != NodeState.CANCELLED
    
    def is_blocking(self) -> bool:
        """Determine if this node is currently blocking its parents.
        
        Returns:
            bool: True if this node is blocking, False otherwise
        """
        return self.blocking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this node to a dictionary for storage in MongoDB.
        
        Returns:
            dict: The dictionary representation of this node
        """
        node_dict = super().to_dict()
        node_dict.update({
            "state": self.state.value,
            "state_history": [(state.value, timestamp.isoformat()) 
                              for state, timestamp in self.state_history]
        })
        return node_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], elements_map: Dict[str, Element]) -> 'StateProducerNode':
        """Create a node from a dictionary representation.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects
            
        Returns:
            StateProducerNode: The created node
        """
        # Get the state from the data
        state_str = data.get("state", NodeState.OPEN.value)
        state = NodeState(state_str)
        
        # Create the node
        node = super().from_dict(data, elements_map)
        node.state = state
        
        # Parse state history
        node.state_history = []
        for state_str, timestamp_str in data.get("state_history", []):
            state = NodeState(state_str)
            timestamp = datetime.fromisoformat(timestamp_str)
            node.state_history.append((state, timestamp))
        
        return node
    
    def to_graph_node(self) -> Dict[str, Any]:
        """Convert to a format suitable for NetworkX.
        
        Returns:
            dict: Dictionary representation for graph storage
        """
        graph_node = super().to_graph_node()
        graph_node.update({
            "state": self.state.value
        })
        return graph_node


class StateDerivedNode(Node):
    """Base class for nodes that derive their state from children.
    
    These are nodes like Questions, Problems, Goals, and Experiments whose
    state is inferred from the state of their children rather than set directly.
    """
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new StateDerivedNode.
        
        Args:
            text: The text content of the node
            node_type: The type of node (see NODE_TYPES)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, node_type, parent, id, ref_marker, metadata)
    
    def infer_state(self) -> NodeState:
        """Infer the state of this node based on its children.
        
        This base implementation provides a general algorithm for inferring state:
        - DONE if has valid resolution
        - IN_PROGRESS if has any child nodes but no valid resolution
        - OPEN if has no child nodes
        
        Override in subclasses for specific state inference logic.
        
        Returns:
            NodeState: The inferred state
        """
        if self.has_valid_resolution():
            return NodeState.DONE
        elif len(self.children) > 0:
            return NodeState.IN_PROGRESS
        else:
            return NodeState.OPEN
    
    def has_valid_resolution(self) -> bool:
        """Determine if this node has a valid resolution.
        
        This base implementation always returns False.
        Override in subclasses with specific resolution criteria.
        
        Returns:
            bool: True if this node has a valid resolution, False otherwise
        """
        return False
    
    def is_blocking(self) -> bool:
        """Determine if this node is currently blocking its parents.
        
        A StateDerivedNode is blocking if it doesn't have a valid resolution.
        
        Returns:
            bool: True if this node is blocking, False otherwise
        """
        return not self.has_valid_resolution()
    
    def get_blocking_children(self) -> List[Node]:
        """Get all children that are currently blocking this node.
        
        Returns:
            List[Node]: List of blocking child nodes
        """
        return [child for child in self.get_nodes() if child.is_blocking()]
    
    def to_graph_node(self) -> Dict[str, Any]:
        """Convert to a format suitable for NetworkX.
        
        Returns:
            dict: Dictionary representation for graph storage
        """
        graph_node = super().to_graph_node()
        graph_node.update({
            "state": self.infer_state().value,
            "has_resolution": self.has_valid_resolution()
        })
        return graph_node