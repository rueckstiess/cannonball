import re
from typing import List, Dict, Tuple, Optional, Any, Union, Type
import networkx as nx

from base_classes import Element, Thought, Node
from state_nodes import NodeState

# Import all specific node types
from specific_nodes import (
    Task, Question, Problem, Alternative, Decision,
    Observation, Knowledge, Goal, Experiment,
    Idea, Artifact
)
from meta_nodes import MetaComment, Example, LocationMarker


class MarkdownParser:
    """Parser for converting markdown text to node structure and back."""
    
    # Map of markers to node classes
    MARKER_TO_CLASS = {
        "[ ]": Task,
        "[/]": Task,
        "[x]": Task,
        "[-]": Task,
        "[?]": Question,
        "[a]": Alternative,
        "[o]": Observation,
        "[D]": Decision,
        "[g]": Goal,
        "[_]": None,  # Edge node, not implemented yet
        "[A]": Artifact,
        "[P]": Problem,
        "[e]": Experiment,
        "[m]": MetaComment,
        "["]": Example,
        "[I]": Idea,
        "[i]": Knowledge,
        "[l]": LocationMarker
    }
    
    # Map of task markers to states
    TASK_MARKER_TO_STATE = {
        "[ ]": NodeState.OPEN,
        "[/]": NodeState.IN_PROGRESS,
        "[x]": NodeState.DONE,
        "[-]": NodeState.CANCELLED
    }
    
    @classmethod
    def parse_markdown(cls, markdown_text: str) -> Tuple[Element, Dict[str, Node]]:
        """Parse markdown text into a tree of elements and a node map.
        
        Args:
            markdown_text: The markdown text to parse
            
        Returns:
            Tuple[Element, Dict[str, Node]]: The root element and a map of reference markers to nodes
        """
        lines = markdown_text.strip().split("\n")
        root = Element("Root")
        current_path = [root]
        ref_map = {}  # Maps reference markers to nodes
        
        current_level = 0
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Extract indentation level (count leading tabs)
            indent_match = re.match(r'^(\t*)', line)
            if indent_match:
                level = len(indent_match.group(1))
            else:
                level = 0
                
            # Adjust the current path based on the indent level
            if level > current_level:
                # Going deeper in the hierarchy
                current_path = current_path[:current_level+1]
            elif level < current_level:
                # Going back up the hierarchy
                current_path = current_path[:level+1]
                
            current_level = level
            parent = current_path[-1]
            
            # Extract the text content (without the bullet and indentation)
            content_match = re.match(r'^\t*- (.*?)$', line)
            if not content_match:
                continue
                
            content = content_match.group(1)
            
            # Check for node markers like "[ ]", "[?]", etc.
            marker_match = re.match(r'(\[[^\]]*\])\s+(.*?)$', content)
            
            if marker_match:
                # This is a node with a marker
                marker = marker_match.group(1)
                text = marker_match.group(2)
                
                # Check for reference marker
                ref_marker = None
                ref_match = re.search(r'\^(\w+)$', text)
                if ref_match:
                    ref_marker = ref_match.group(1)
                    # Remove the reference marker from the text
                    text = text[:ref_match.start()].strip()
                
                # Create the appropriate node type
                if marker in cls.MARKER_TO_CLASS:
                    node_class = cls.MARKER_TO_CLASS[marker]
                    
                    if node_class == Task:
                        # For tasks, set the appropriate state
                        state = cls.TASK_MARKER_TO_STATE.get(marker, NodeState.OPEN)
                        node = Task(text, parent, ref_marker=ref_marker, state=state)
                    elif node_class:
                        # For other node types
                        node = node_class(text, parent, ref_marker=ref_marker)
                    else:
                        # Fallback for unimplemented node types
                        node = Thought(f"{marker} {text}", parent)
                else:
                    # Custom node type
                    custom_type = marker[1:-1]  # Remove the brackets
                    node = Node(text, custom_type, parent, ref_marker=ref_marker)
                
                parent.add_child(node)
                current_path.append(node)
                
                # Add to reference map if it has a marker
                if ref_marker:
                    ref_map[ref_marker] = node
            else:
                # This is a regular thought
                thought = Thought(content, parent)
                parent.add_child(thought)
                current_path.append(thought)
        
        # Process references after all nodes are created
        cls._process_references(root, ref_map)
        
        return root, ref_map
    
    @classmethod
    def _process_references(cls, root: Element, ref_map: Dict[str, Node]) -> None:
        """Process references between nodes.
        
        Args:
            root: The root element
            ref_map: A map of reference markers to nodes
        """
        # Find all nodes with references in their text
        if isinstance(root, Node):
            refs = root.get_references_in_text()
            
            for ref in refs:
                if ref in ref_map:
                    target_node = ref_map[ref]
                    if isinstance(target_node, Node) and isinstance(root, Node):
                        root.references.add(target_node)
                        target_node.referenced_by.add(root)
                        
                        # For Decision nodes, check if they reference an Alternative
                        if isinstance(root, Decision) and isinstance(target_node, Alternative):
                            root.selected_alternative_ref = ref
        
        # Process children recursively
        for child in root.children:
            cls._process_references(child, ref_map)
    
    @classmethod
    def generate_graph(cls, root: Element) -> nx.DiGraph:
        """Generate a NetworkX graph from the element tree.
        
        Args:
            root: The root element
            
        Returns:
            nx.DiGraph: A directed graph representation
        """
        G = nx.DiGraph()
        
        # Add all nodes to the graph
        def add_nodes_recursive(element):
            if isinstance(element, Node):
                # Add this node to the graph
                G.add_node(element.id, **element.to_graph_node())
                
                # Add parent-child edges
                if element.parent and isinstance(element.parent, Node):
                    G.add_edge(element.parent.id, element.id, type="parent-child")
                
                # Add reference edges
                for ref in element.references:
                    G.add_edge(element.id, ref.id, type="reference")
            
            # Process children recursively
            for child in element.children:
                add_nodes_recursive(child)
        
        add_nodes_recursive(root)
        return G
    
    @classmethod
    def to_markdown(cls, root: Element) -> str:
        """Convert an element tree back to markdown.
        
        Args:
            root: The root element
            
        Returns:
            str: The markdown representation
        """
        # Skip the artificial root node
        result = ""
        for child in root.children:
            result += child.to_markdown()
        return result