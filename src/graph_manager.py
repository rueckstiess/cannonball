import networkx as nx
from typing import Dict, List, Optional, Tuple, Any, Set, Union
import json
import re
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

from base_classes import Element, Thought, Node
from markdown_parser import MarkdownParser
from specific_nodes import Task, Decision, Alternative


class GraphManager:
    """Manages the productivity graph, including persistence and operations."""
    
    def __init__(self, 
                 mongodb_uri: Optional[str] = None, 
                 database_name: str = "productivity_system"):
        """Initialize a new GraphManager.
        
        Args:
            mongodb_uri: Optional MongoDB connection URI
            database_name: The name of the database to use
        """
        self.root = Element("Root")
        self.ref_map: Dict[str, Node] = {}
        self.element_map: Dict[str, Element] = {"root": self.root}
        self.graph = nx.DiGraph()
        
        # Set up MongoDB connection if provided
        if mongodb_uri:
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database_name]
            self.elements_collection = self.db.elements
        else:
            self.client = None
            self.db = None
            self.elements_collection = None
    
    def load_from_markdown(self, markdown_text: str) -> None:
        """Load a productivity graph from markdown text.
        
        Args:
            markdown_text: The markdown text to parse
        """
        self.root, self.ref_map = MarkdownParser.parse_markdown(markdown_text)
        
        # Build element map for quick lookups
        self.element_map = {"root": self.root}
        self._build_element_map(self.root)
        
        # Generate the graph
        self.graph = MarkdownParser.generate_graph(self.root)
    
    def _build_element_map(self, element: Element) -> None:
        """Recursively build the element map for quick lookups.
        
        Args:
            element: The current element to process
        """
        self.element_map[element.id] = element
        
        for child in element.children:
            self._build_element_map(child)
    
    def to_markdown(self) -> str:
        """Convert the productivity graph to markdown text.
        
        Returns:
            str: The markdown representation
        """
        return MarkdownParser.to_markdown(self.root)
    
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID.
        
        Args:
            node_id: The ID of the node to find
            
        Returns:
            Node or None: The found node, or None if not found
        """
        element = self.element_map.get(node_id)
        if isinstance(element, Node):
            return element
        return None
    
    def get_node_by_ref(self, ref_marker: str) -> Optional[Node]:
        """Get a node by its reference marker.
        
        Args:
            ref_marker: The reference marker to find (without the ^ symbol)
            
        Returns:
            Node or None: The found node, or None if not found
        """
        return self.ref_map.get(ref_marker)
    
    def add_node(self, 
                node_type: str, 
                text: str, 
                parent_id: str, 
                ref_marker: Optional[str] = None) -> Optional[Node]:
        """Add a new node to the graph.
        
        Args:
            node_type: The type of node to add (e.g., "task", "question")
            text: The text content of the node
            parent_id: The ID of the parent element
            ref_marker: Optional reference marker for the node
            
        Returns:
            Node or None: The created node, or None if creation failed
        """
        # Get the parent element
        parent = self.element_map.get(parent_id)
        if not parent:
            return None
        
        # Create the appropriate node type
        from specific_nodes import (
            Task, Question, Problem, Alternative, Decision,
            Observation, Knowledge, Goal, Experiment,
            Idea, Artifact
        )
        from meta_nodes import MetaComment, Example, LocationMarker
        
        node_classes = {
            "task": Task,
            "question": Question,
            "problem": Problem,
            "alternative": Alternative,
            "decision": Decision,
            "observation": Observation,
            "knowledge": Knowledge,
            "goal": Goal,
            "experiment": Experiment,
            "idea": Idea,
            "artifact": Artifact,
            "meta": MetaComment,
            "example": Example,
            "location": LocationMarker
        }
        
        if node_type not in node_classes:
            return None
            
        node_class = node_classes[node_type]
        
        # Create the node
        node = node_class(text, parent, ref_marker=ref_marker)
        parent.add_child(node)
        
        # Add to maps
        self.element_map[node.id] = node
        if ref_marker:
            self.ref_map[ref_marker] = node
        
        # Add to graph
        self.graph.add_node(node.id, **node.to_graph_node())
        if isinstance(parent, Node):
            self.graph.add_edge(parent.id, node.id, type="parent-child")
        
        # Save to database if connected
        if self.elements_collection:
            self._save_element_to_db(node)
        
        return node
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the graph.
        
        Args:
            node_id: The ID of the node to remove
            
        Returns:
            bool: True if the node was found and removed, False otherwise
        """
        node = self.get_node_by_id(node_id)
        if not node or not node.parent:
            return False
            
        # Remove from parent
        parent = node.parent
        parent.remove_child(node)
        
        # Remove from maps
        if node.id in self.element_map:
            del self.element_map[node.id]
        if node.ref_marker and node.ref_marker in self.ref_map:
            del self.ref_map[node.ref_marker]
        
        # Remove from graph
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)
        
        # Remove from database if connected
        if self.elements_collection:
            self.elements_collection.delete_one({"_id": node.id})
        
        return True
    
    def update_node_text(self, node_id: str, new_text: str) -> bool:
        """Update the text content of a node.
        
        Args:
            node_id: The ID of the node to update
            new_text: The new text content
            
        Returns:
            bool: True if the node was found and updated, False otherwise
        """
        node = self.get_node_by_id(node_id)
        if not node:
            return False
            
        node.set_text(new_text)
        node.updated_at = datetime.utcnow()
        
        # Update graph
        if self.graph.has_node(node_id):
            nx.set_node_attributes(self.graph, {node_id: {"text": new_text}})
        
        # Update database if connected
        if self.elements_collection:
            self.elements_collection.update_one(
                {"_id": node.id},
                {"$set": {"text": new_text, "updated_at": node.updated_at}}
            )
        
        return True
    
    def update_task_state(self, node_id: str, new_state: str) -> bool:
        """Update the state of a task.
        
        Args:
            node_id: The ID of the task to update
            new_state: The new state (open, in_progress, done, cancelled)
            
        Returns:
            bool: True if the task was found and updated, False otherwise
        """
        node = self.get_node_by_id(node_id)
        if not isinstance(node, Task):
            return False
            
        from state_nodes import NodeState
        state_map = {
            "open": NodeState.OPEN,
            "in_progress": NodeState.IN_PROGRESS,
            "done": NodeState.DONE,
            "cancelled": NodeState.CANCELLED
        }
        
        if new_state not in state_map:
            return False
            
        node.set_state(state_map[new_state])
        
        # Update graph
        if self.graph.has_node(node_id):
            nx.set_node_attributes(self.graph, {node_id: {"state": new_state}})
        
        # Update database if connected
        if self.elements_collection:
            self._save_element_to_db(node)
        
        return True
    
    def make_decision(self, decision_id: str, alternative_ref: str) -> bool:
        """Set the selected alternative for a decision.
        
        Args:
            decision_id: The ID of the decision node
            alternative_ref: The reference marker of the selected alternative
            
        Returns:
            bool: True if the decision was found and updated, False otherwise
        """
        decision = self.get_node_by_id(decision_id)
        if not isinstance(decision, Decision):
            return False
            
        alternative = self.get_node_by_ref(alternative_ref)
        if not isinstance(alternative, Alternative):
            return False
            
        decision.select_alternative(alternative_ref)
        
        # Update graph
        if self.graph.has_node(decision_id):
            nx.set_node_attributes(self.graph, {
                decision_id: {"selected_alternative_ref": alternative_ref}
            })
        
        # Update database if connected
        if self.elements_collection:
            self._save_element_to_db(decision)
        
        return True
    
    def get_blocking_nodes(self) -> List[Node]:
        """Get all nodes that are currently blocking progress.
        
        Returns:
            List[Node]: List of blocking nodes
        """
        return [node for node in self._get_all_nodes() 
                if isinstance(node, Node) and node.is_blocking()]
    
    def get_actionable_tasks(self) -> List[Task]:
        """Get all tasks that are actionable (not blocked).
        
        Returns:
            List[Task]: List of actionable tasks
        """
        return [node for node in self._get_all_nodes() 
                if isinstance(node, Task) and 
                   node.get_state() == "open" and 
                   not node.is_blocked_by_dependencies()]
    
    def _get_all_nodes(self) -> List[Node]:
        """Get all nodes in the graph.
        
        Returns:
            List[Node]: All nodes in the graph
        """
        nodes = []
        for element_id in self.element_map:
            element = self.element_map[element_id]
            if isinstance(element, Node):
                nodes.append(element)
        return nodes
    
    def _save_element_to_db(self, element: Element) -> None:
        """Save an element to the database.
        
        Args:
            element: The element to save
        """
        if not self.elements_collection:
            return
            
        # Convert to dictionary
        element_dict = element.to_dict()
        
        # Save to database
        self.elements_collection.replace_one(
            {"_id": element.id},
            element_dict,
            upsert=True
        )
    
    def load_from_db(self) -> bool:
        """Load the productivity graph from the database.
        
        Returns:
            bool: True if loading was successful, False otherwise
        """
        if not self.elements_collection:
            return False
            
        # Clear existing data
        self.root = Element("Root")
        self.ref_map = {}
        self.element_map = {"root": self.root}
        self.graph = nx.DiGraph()
        
        # Get all elements from the database
        elements_data = list(self.elements_collection.find())
        
        # First pass: Create all elements
        for data in elements_data:
            element_type = data.get("type")
            
            if element_type == "Element":
                element = Element.from_dict(data, self.element_map)
            elif element_type == "Thought":
                element = Thought.from_dict(data, self.element_map)
            else:
                # Attempt to create the appropriate node type
                from specific_nodes import (
                    Task, Question, Problem, Alternative, Decision,
                    Observation, Knowledge, Goal, Experiment,
                    Idea, Artifact
                )
                from meta_nodes import MetaComment, Example, LocationMarker
                
                node_classes = {
                    "Task": Task,
                    "Question": Question,
                    "Problem": Problem,
                    "Alternative": Alternative,
                    "Decision": Decision,
                    "Observation": Observation,
                    "Knowledge": Knowledge,
                    "Goal": Goal,
                    "Experiment": Experiment,
                    "Idea": Idea,
                    "Artifact": Artifact,
                    "MetaComment": MetaComment,
                    "Example": Example,
                    "LocationMarker": LocationMarker
                }
                
                if element_type in node_classes:
                    element = node_classes[element_type].from_dict(data, self.element_map)
                else:
                    # Fallback to base Node
                    element = Node.from_dict(data, self.element_map)
                    
            # Add to element map
            self.element_map[element.id] = element
            
            # Add to ref map if it's a node with a ref marker
            if isinstance(element, Node) and element.ref_marker:
                self.ref_map[element.ref_marker] = element
        
        # Second pass: Resolve references
        for data in elements_data:
            element_id = data.get("_id")
            if element_id in self.element_map:
                element = self.element_map[element_id]
                element.resolve_references(data, self.element_map)
        
        # Find the root element
        for element_id, element in self.element_map.items():
            if element.parent is None and element_id != "root":
                self.root.add_child(element)
        
        # Generate the graph
        self.graph = MarkdownParser.generate_graph(self.root)
        
        return True
    
    def export_to_json(self, filepath: str) -> bool:
        """Export the productivity graph to a JSON file.
        
        Args:
            filepath: The path to save the JSON file
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        # Convert all elements to dictionaries
        elements_data = []
        for element_id in self.element_map:
            if element_id == "root":
                continue
            element = self.element_map[element_id]
            elements_data.append(element.to_dict())
        
        # Write to file
        try:
            with open(filepath, 'w') as f:
                json.dump(elements_data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def import_from_json(self, filepath: str) -> bool:
        """Import the productivity graph from a JSON file.
        
        Args:
            filepath: The path to the JSON file
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                elements_data = json.load(f)
                
            # Clear existing data
            self.root = Element("Root")
            self.ref_map = {}
            self.element_map = {"root": self.root}
            self.graph = nx.DiGraph()
            
            # First pass: Create all elements
            for data in elements_data:
                element_type = data.get("type")
                
                if element_type == "Element":
                    element = Element.from_dict(data, self.element_map)
                elif element_type == "Thought":
                    element = Thought.from_dict(data, self.element_map)
                else:
                    # Attempt to create the appropriate node type
                    from specific_nodes import (
                        Task, Question, Problem, Alternative, Decision,
                        Observation, Knowledge, Goal, Experiment,
                        Idea, Artifact
                    )
                    from meta_nodes import MetaComment, Example, LocationMarker
                    
                    node_classes = {
                        "Task": Task,
                        "Question": Question,
                        "Problem": Problem,
                        "Alternative": Alternative,
                        "Decision": Decision,
                        "Observation": Observation,
                        "Knowledge": Knowledge,
                        "Goal": Goal,
                        "Experiment": Experiment,
                        "Idea": Idea,
                        "Artifact": Artifact,
                        "MetaComment": MetaComment,
                        "Example": Example,
                        "LocationMarker": LocationMarker
                    }
                    
                    if element_type in node_classes:
                        element = node_classes[element_type].from_dict(data, self.element_map)
                    else:
                        # Fallback to base Node
                        element = Node.from_dict(data, self.element_map)
                        
                # Add to element map
                self.element_map[element.id] = element
                
                # Add to ref map if it's a node with a ref marker
                if isinstance(element, Node) and element.ref_marker:
                    self.ref_map[element.ref_marker] = element
            
            # Second pass: Resolve references
            for data in elements_data:
                element_id = data.get("_id")
                if element_id in self.element_map:
                    element = self.element_map[element_id]
                    element.resolve_references(data, self.element_map)
            
            # Find the root element
            for element_id, element in self.element_map.items():
                if element.parent is None and element_id != "root":
                    self.root.add_child(element)
            
            # Generate the graph
            self.graph = MarkdownParser.generate_graph(self.root)
            
            return True
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return False