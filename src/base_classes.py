from typing import Optional, List, Dict, Any, Set, Union, ClassVar, Type, TypeVar
from uuid import uuid4
import re
from datetime import datetime
import json

T = TypeVar('T', bound='Element')

class Element:
    """Base class for all elements in the productivity system.
    
    This serves as the foundation for both Thoughts (which are not nodes in the graph)
    and Nodes (which are part of the graph structure).
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional['Element'] = None, 
                 id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Element.
        
        Args:
            text: The text content of the element
            parent: The parent element, if any
            id: Optional unique identifier. If not provided, a UUID will be generated
            metadata: Optional metadata dictionary for additional attributes
        """
        self.text = text
        self.parent = parent
        self.id = id if id is not None else str(uuid4())
        self.children: List[Element] = []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        
    def add_child(self, child: 'Element') -> None:
        """Add a child element to this element.
        
        Args:
            child: The child element to add
        """
        self.children.append(child)
        child.parent = self
        self.updated_at = datetime.utcnow()
        
    def remove_child(self, child: 'Element') -> bool:
        """Remove a child element from this element.
        
        Args:
            child: The child element to remove
            
        Returns:
            bool: True if the child was found and removed, False otherwise
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_root(self) -> 'Element':
        """Get the root element of the tree.
        
        Returns:
            Element: The root element
        """
        current = self
        while current.parent is not None:
            current = current.parent
        return current
    
    def find_by_id(self, id: str) -> Optional['Element']:
        """Find an element by its ID.
        
        Args:
            id: The ID to search for
            
        Returns:
            Element or None: The found element, or None if not found
        """
        if self.id == id:
            return self
            
        for child in self.children:
            result = child.find_by_id(id)
            if result is not None:
                return result
                
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this element to a dictionary for storage in MongoDB.
        
        Returns:
            dict: The dictionary representation of this element
        """
        return {
            "_id": self.id,
            "text": self.text,
            "children": [child.id for child in self.children],
            "parent": self.parent.id if self.parent else None,
            "type": self.__class__.__name__,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any], elements_map: Dict[str, 'Element']) -> T:
        """Create an element from a dictionary representation.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects for resolving references
            
        Returns:
            Element: The created element
        """
        # Create the element without children or parent
        element = cls(
            text=data["text"],
            id=data["_id"],
            metadata=data.get("metadata", {})
        )
        
        # Add to elements map
        elements_map[element.id] = element
        
        # Set created_at and updated_at
        element.created_at = data.get("created_at", datetime.utcnow())
        element.updated_at = data.get("updated_at", datetime.utcnow())
        
        # Will need to set parent and children in a second pass
        return element
    
    def resolve_references(self, data: Dict[str, Any], elements_map: Dict[str, 'Element']) -> None:
        """Resolve parent and children references after loading from dictionary.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects
        """
        # Set parent
        parent_id = data.get("parent")
        if parent_id and parent_id in elements_map:
            self.parent = elements_map[parent_id]
        
        # Set children
        for child_id in data.get("children", []):
            if child_id in elements_map:
                child = elements_map[child_id]
                self.children.append(child)
                child.parent = self
    
    def to_markdown(self, level: int = 0) -> str:
        """Convert this element to Markdown format.
        
        Args:
            level: The indentation level (number of tabs)
            
        Returns:
            str: The Markdown representation of this element
        """
        indent = "\t" * level
        result = f"{indent}- {self.text}\n"
        
        for child in self.children:
            result += child.to_markdown(level + 1)
            
        return result
    
    @staticmethod
    def parse_markdown(text: str) -> 'Element':
        """Parse markdown text into a tree of elements.
        
        Args:
            text: The markdown text to parse
            
        Returns:
            Element: The root element of the parsed tree
        """
        # This is a placeholder - actual implementation would be more complex
        # and handle the various node types and indentation levels
        root = Element("Root")
        # Parsing logic would go here
        return root
    
    def __repr__(self) -> str:
        """String representation of this element."""
        return f"{self.__class__.__name__}(id='{self.id}', text='{self.text[:30]}{'...' if len(self.text) > 30 else ''}')"


class Thought(Element):
    """Represents a thought or comment in the system.
    
    Thoughts are not nodes in the graph but can contain nodes and other thoughts.
    They are primarily for organizing information and adding context.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Thought.
        
        Args:
            text: The text content of the thought
            parent: The parent element, if any
            id: Optional unique identifier
            metadata: Optional metadata dictionary
        """
        super().__init__(text, parent, id, metadata)
    
    def get_nodes(self) -> List['Node']:
        """Get all immediate children that are Node instances.
        
        Returns:
            List of Node objects that are direct children of this Thought
        """
        return [child for child in self.children if isinstance(child, Node)]
    
    def get_recursive_nodes(self) -> List['Node']:
        """Get all Node descendants recursively.
        
        Returns:
            List of all Node objects in the subtree rooted at this Thought
        """
        nodes = []
        for child in self.children:
            if isinstance(child, Node):
                nodes.append(child)
            # Get recursive nodes from all children (both Thoughts and Nodes)
            nodes.extend(child.get_recursive_nodes())
        return nodes
    
    def to_markdown(self, level: int = 0) -> str:
        """Convert this thought to Markdown format.
        
        Args:
            level: The indentation level (number of tabs)
            
        Returns:
            str: The Markdown representation of this thought
        """
        indent = "\t" * level
        result = f"{indent}- {self.text}\n"
        
        for child in self.children:
            result += child.to_markdown(level + 1)
            
        return result


class Node(Thought):
    """Base class for all nodes in the graph.
    
    Nodes are elements that are part of the graph structure and can have
    explicit relationships with other nodes.
    """
    
    # Maps node type identifiers to their corresponding markers
    NODE_TYPES: ClassVar[Dict[str, str]] = {
        "task": "[ ]",
        "task_in_progress": "[/]",
        "task_done": "[x]",
        "task_cancelled": "[-]",
        "question": "[?]",
        "alternative": "[a]",
        "observation": "[o]",
        "decision": "[D]",
        "goal": "[g]",
        "edge": "[_]",
        "artifact": "[A]",
        "problem": "[P]",
        "experiment": "[e]",
        "meta": "[m]",
        "example": "["]",
        "idea": "[I]",
        "knowledge": "[i]",
        "location": "[l]"
    }
    
    # Reverse mapping from markers to node types
    MARKERS_TO_TYPES: ClassVar[Dict[str, str]] = {
        marker: node_type for node_type, marker in NODE_TYPES.items()
    }
    
    def __init__(self, 
                 text: str, 
                 node_type: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Node.
        
        Args:
            text: The text content of the node
            node_type: The type of node (see NODE_TYPES)
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker for this node (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, parent, id, metadata)
        
        if node_type not in self.NODE_TYPES:
            raise ValueError(f"Invalid node type: {node_type}")
            
        self.node_type = node_type
        self.marker = self.NODE_TYPES[node_type]
        self.ref_marker = ref_marker
        
        # References to other nodes (to be populated by the graph manager)
        self.references: Set[Node] = set()
        self.referenced_by: Set[Node] = set()
        
        # Blocking state
        self.blocking = self.can_block()
    
    def can_block(self) -> bool:
        """Determine if this node type can block parent nodes.
        
        Returns:
            bool: True if this node type can block, False otherwise
        """
        # By default, most node types can block
        # Override in subclasses for specific behavior
        return True
    
    def is_blocking(self) -> bool:
        """Determine if this node is currently blocking its parents.
        
        Returns:
            bool: True if this node is blocking, False otherwise
        """
        # Base implementation - override in subclasses
        return self.blocking
    
    def get_references_in_text(self) -> List[str]:
        """Extract reference markers from the node text.
        
        Returns:
            List[str]: List of reference markers found in the text
        """
        # Find all occurrences of ^marker in the text
        ref_pattern = r'\^(\w+)'
        return re.findall(ref_pattern, self.text)
    
    def find_by_ref(self, ref: str) -> Optional['Node']:
        """Find a node by its reference marker.
        
        Args:
            ref: The reference marker to search for (without the ^ symbol)
            
        Returns:
            Node or None: The found node, or None if not found
        """
        root = self.get_root()
        for node in root.get_recursive_nodes():
            if isinstance(node, Node) and node.ref_marker == ref:
                return node
        return None
    
    def to_graph_node(self) -> Dict[str, Any]:
        """Convert to a format suitable for NetworkX.
        
        Returns:
            dict: Dictionary representation for graph storage
        """
        return {
            "id": self.id,
            "type": self.node_type,
            "text": self.text,
            "blocking": self.is_blocking(),
            "ref_marker": self.ref_marker,
            "metadata": self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this node to a dictionary for storage in MongoDB.
        
        Returns:
            dict: The dictionary representation of this node
        """
        node_dict = super().to_dict()
        node_dict.update({
            "node_type": self.node_type,
            "marker": self.marker,
            "ref_marker": self.ref_marker,
            "references": [ref.id for ref in self.references],
            "referenced_by": [ref.id for ref in self.referenced_by],
            "blocking": self.is_blocking()
        })
        return node_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], elements_map: Dict[str, 'Element']) -> 'Node':
        """Create a node from a dictionary representation.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects for resolving references
            
        Returns:
            Node: The created node
        """
        node = super().from_dict(data, elements_map)
        node.node_type = data["node_type"]
        node.marker = data["marker"]
        node.ref_marker = data.get("ref_marker")
        node.blocking = data.get("blocking", True)
        
        # References will be resolved in a second pass
        return node
    
    def resolve_references(self, data: Dict[str, Any], elements_map: Dict[str, 'Element']) -> None:
        """Resolve references after loading from dictionary.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects
        """
        super().resolve_references(data, elements_map)
        
        # Resolve references to other nodes
        self.references = set()
        for ref_id in data.get("references", []):
            if ref_id in elements_map and isinstance(elements_map[ref_id], Node):
                self.references.add(elements_map[ref_id])
        
        # Resolve referenced_by
        self.referenced_by = set()
        for ref_id in data.get("referenced_by", []):
            if ref_id in elements_map and isinstance(elements_map[ref_id], Node):
                self.referenced_by.add(elements_map[ref_id])
    
    def to_markdown(self, level: int = 0) -> str:
        """Convert this node to Markdown format.
        
        Args:
            level: The indentation level (number of tabs)
            
        Returns:
            str: The Markdown representation of this node
        """
        indent = "\t" * level
        ref_suffix = f" ^{self.ref_marker}" if self.ref_marker else ""
        result = f"{indent}- {self.marker} {self.text}{ref_suffix}\n"
        
        for child in self.children:
            result += child.to_markdown(level + 1)
            
        return result
    
    def get_recursive_nodes(self) -> List['Node']:
        """Get all Node descendants recursively, including self.
        
        Returns:
            List of all Node objects in the subtree rooted at this Node
        """
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_recursive_nodes())
        return nodes