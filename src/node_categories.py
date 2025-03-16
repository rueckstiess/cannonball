from typing import Optional, List, Dict, Any, Set, Union, ClassVar, Type
from datetime import datetime

from base_classes import Node, Element, Thought
from state_nodes import StateProducerNode, StateDerivedNode, NodeState


class InformationNode(Node):
    """Base class for nodes that represent information or outputs.
    
    These are nodes like Observations, Knowledge, and Artifacts that
    capture information rather than representing work to be done.
    """
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 source: Optional[str] = None):
        """Initialize a new InformationNode.
        
        Args:
            text: The text content of the node
            node_type: The type of node (observation, knowledge, artifact)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            source: Optional source information (citation, origin, etc.)
        """
        super().__init__(text, node_type, parent, id, ref_marker, metadata)
        self.source = source
        self.verified = False
        self.verification_date = None
    
    def verify(self) -> None:
        """Mark this information as verified."""
        self.verified = True
        self.verification_date = datetime.utcnow()
    
    def is_blocking(self) -> bool:
        """Determine if this node is blocking.
        
        Information nodes generally don't block by default.
        
        Returns:
            bool: False, as information nodes don't block
        """
        return False
    
    def can_block(self) -> bool:
        """Determine if this node type can block.
        
        Returns:
            bool: False, as information nodes don't block
        """
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this information node to a dictionary for storage in MongoDB.
        
        Returns:
            dict: The dictionary representation of this information node
        """
        info_dict = super().to_dict()
        info_dict.update({
            "source": self.source,
            "verified": self.verified,
            "verification_date": self.verification_date.isoformat() if self.verification_date else None
        })
        return info_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], elements_map: Dict[str, Element]) -> 'InformationNode':
        """Create an information node from a dictionary representation.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects
            
        Returns:
            InformationNode: The created information node
        """
        info_node = super().from_dict(data, elements_map)
        info_node.source = data.get("source")
        info_node.verified = data.get("verified", False)
        
        if data.get("verification_date"):
            info_node.verification_date = datetime.fromisoformat(data["verification_date"])
        else:
            info_node.verification_date = None
            
        return info_node


class DecisionNode(StateProducerNode):
    """Base class for nodes representing choices or decisions.
    
    These include Decision nodes that resolve Questions or Problems,
    and Alternative nodes that represent options being considered.
    """
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 state: NodeState = NodeState.OPEN):
        """Initialize a new DecisionNode.
        
        Args:
            text: The text content of the node
            node_type: The type of node (decision, alternative)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            state: Initial state of the node
        """
        super().__init__(text, node_type, parent, id, ref_marker, metadata, state)
        self.selected_alternative_ref = None
    
    def select_alternative(self, alternative_ref: str) -> None:
        """Select an alternative by its reference marker.
        
        Args:
            alternative_ref: The reference marker of the selected alternative
        """
        self.selected_alternative_ref = alternative_ref
        
        # Update the text to include the reference if it's not already there
        if f"^{alternative_ref}" not in self.text:
            self.text += f" ^{alternative_ref}"
    
    def get_selected_alternative(self) -> Optional[Node]:
        """Get the selected alternative node.
        
        Returns:
            Node or None: The selected alternative, or None if not found
        """
        if not self.selected_alternative_ref:
            return None
            
        return self.find_by_ref(self.selected_alternative_ref)
    
    def is_alternative_valid(self) -> bool:
        """Check if the selected alternative is valid (has no unresolved problems).
        
        Returns:
            bool: True if the alternative is valid, False otherwise
        """
        alternative = self.get_selected_alternative()
        if not alternative:
            return False
            
        # Check if the alternative has any unresolved Problem children
        from specific_nodes import Problem  # Import here to avoid circular imports
        for child in alternative.children:
            if isinstance(child, Problem) and child.is_blocking():
                return False
                
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this decision node to a dictionary for storage in MongoDB.
        
        Returns:
            dict: The dictionary representation of this decision node
        """
        decision_dict = super().to_dict()
        decision_dict.update({
            "selected_alternative_ref": self.selected_alternative_ref
        })
        return decision_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], elements_map: Dict[str, Element]) -> 'DecisionNode':
        """Create a decision node from a dictionary representation.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects
            
        Returns:
            DecisionNode: The created decision node
        """
        decision_node = super().from_dict(data, elements_map)
        decision_node.selected_alternative_ref = data.get("selected_alternative_ref")
        return decision_node


class MetaNode(Node):
    """Base class for nodes that provide meta-information about the system.
    
    These include Meta Comments, Examples, and Location Markers that help
    with system organization and navigation but don't represent work or content.
    """
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new MetaNode.
        
        Args:
            text: The text content of the node
            node_type: The type of node (meta, example, location)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, node_type, parent, id, ref_marker, metadata)
    
    def is_blocking(self) -> bool:
        """Determine if this node is blocking.
        
        Meta nodes never block.
        
        Returns:
            bool: False, as meta nodes don't block
        """
        return False
    
    def can_block(self) -> bool:
        """Determine if this node type can block.
        
        Returns:
            bool: False, as meta nodes don't block
        """
        return False


class SpontaneousNode(Node):
    """Base class for nodes that appear without dependencies.
    
    These include Idea nodes that represent spontaneous insights or
    creative thoughts that emerge during the work process.
    """
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new SpontaneousNode.
        
        Args:
            text: The text content of the node
            node_type: The type of node (idea)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, node_type, parent, id, ref_marker, metadata)
    
    def is_blocking(self) -> bool:
        """Determine if this node is blocking.
        
        Spontaneous nodes never block.
        
        Returns:
            bool: False, as spontaneous nodes don't block
        """
        return False
    
    def can_block(self) -> bool:
        """Determine if this node type can block.
        
        Returns:
            bool: False, as spontaneous nodes don't block
        """
        return False