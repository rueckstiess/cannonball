from .nodes import Node
from .utils import get_raw_text_from_listtem, walk_list_items, extract_node_marker_and_refs
import networkx as nx
from marko import Markdown
from typing import Dict, Optional, List
import uuid
import re
from enum import Enum


class EdgeType(Enum):
    REQUIRES = "requires"
    REFERENCES = "references"


class GraphMgr:
    """A graph manager that manages a directed acyclic graph of nodes from markdown list items."""

    parser = Markdown()

    def __init__(self, allow_cycles: bool = False) -> None:
        """Initialize a new graph manager with an empty graph."""
        self.graph = nx.DiGraph()
        self.nodes_by_ref = {}  # Maps reference IDs to node IDs
        self.allow_cycles = allow_cycles

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add.
        """
        self.graph.add_node(node.id, **node.__dict__)

        # If the node has a reference, add it to the ref mapping
        if node.ref:
            self.nodes_by_ref[node.ref] = node.id

    def add_edge(self, parent_id: str, child_id: str, edge_type: EdgeType = EdgeType.REQUIRES) -> None:
        """Add a directed edge from parent to child with an edge type.

        Args:
            parent_id: The ID of the parent node.
            child_id: The ID of the child node.
            edge_type: The type of edge (default is EdgeType.REQUIRES).
        """
        self.graph.add_edge(parent_id, child_id, type=edge_type.value)

    def get_node_by_ref(self, ref: str) -> Optional[str]:
        """Get a node ID by its reference ID.

        Args:
            ref: The reference ID of the node.

        Returns:
            The node ID if found, None otherwise.
        """
        return self.nodes_by_ref.get(ref)

    def get_node_attributes(self, node_id: str) -> Dict:
        """Get the attributes of a node.

        Args:
            node_id: The ID of the node.

        Returns:
            Dictionary of node attributes.
        """
        return self.graph.nodes[node_id]

    def is_acyclic(self) -> bool:
        """Check if the graph is acyclic.

        Returns:
            True if the graph is acyclic, False otherwise.
        """
        return nx.is_directed_acyclic_graph(self.graph)

    def topological_sort(self) -> List[str]:
        """Return nodes in topological order if graph is a DAG.

        Returns:
            List of node IDs in topological order.
        """
        if not self.is_acyclic():
            raise ValueError("Graph contains cycles and cannot be topologically sorted")
        return list(nx.topological_sort(self.graph))

    def get_roots(self) -> List[str]:
        """Get all root nodes (nodes with no incoming edges).

        Returns:
            List of root node IDs.
        """
        return [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]

    def get_leaves(self) -> List[str]:
        """Get all leaf nodes (nodes with no outgoing edges).

        Returns:
            List of leaf node IDs.
        """
        return [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]

    @classmethod
    def from_markdown(cls, markdown: str, allow_cycles: bool = False) -> "GraphMgr":
        """Create a graph from a markdown string.

        Args:
            markdown: A markdown string containing hierarchical list items.

        Returns:
            A GraphMgr instance containing the constructed DAG.
        """
        instance = cls(allow_cycles)
        ast = cls.parser.parse(markdown)

        # First pass: create nodes and collect reference links
        item_to_node_id = {}  # Maps ListItem objects to node IDs
        node_id_to_links = {}  # Maps node IDs to their reference links

        for list_item, parent_item, level in walk_list_items(ast):
            text = get_raw_text_from_listtem(list_item)
            marker, ref, ref_links = extract_node_marker_and_refs(text)

            # Always use a UUID for node ID to ensure uniqueness
            node_id = str(uuid.uuid4())[:8]

            # Create and add the node
            node = Node(id=node_id, name=text, marker=marker, ref=ref)
            instance.add_node(node)

            # Map the ListItem to its node ID for the second pass
            item_to_node_id[list_item] = node_id

            # Store the reference links for the second pass
            if ref_links:
                node_id_to_links[node_id] = ref_links

        # Second pass: create all edges
        for list_item, parent_item, _ in walk_list_items(ast):
            node_id = item_to_node_id.get(list_item)
            if not node_id:
                continue

            # Create parent-child (requires) edge if applicable
            if parent_item and parent_item in item_to_node_id:
                parent_id = item_to_node_id[parent_item]
                instance.add_edge(parent_id, node_id, edge_type=EdgeType.REQUIRES)

            # Process reference links for this node
            if node_id in node_id_to_links:
                for ref_id in node_id_to_links[node_id]:
                    # Find the node with this reference ID
                    target_node_id = instance.get_node_by_ref(ref_id)
                    if target_node_id and target_node_id != node_id:  # Avoid self-references
                        # Create a reference edge from source to target
                        instance.add_edge(node_id, target_node_id, edge_type=EdgeType.REFERENCES)

        # Ensure the graph is acyclic (unless cycles are allowed)
        if not instance.allow_cycles and not instance.is_acyclic():
            raise ValueError("Graph contains cycles and cannot be constructed as a DAG")
        return instance

    def to_dict(self) -> Dict:
        """Convert the graph to a dictionary for serialization.

        Returns:
            Dictionary representation of the graph.
        """
        return {
            "nodes": [self.graph.nodes[n] for n in self.graph.nodes()],
            "edges": [{"source": s, "target": t, **d} for s, t, d in self.graph.edges(data=True)],
        }

    def find_paths(self, source: str, target: str) -> List[List[str]]:
        """Find all paths from source to target.

        Args:
            source: Source node ID.
            target: Target node ID.

        Returns:
            List of paths, where each path is a list of node IDs.
        """
        if source not in self.graph or target not in self.graph:
            return []

        try:
            return list(nx.all_simple_paths(self.graph, source, target))
        except nx.NetworkXNoPath:
            return []

    def find_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find a path from source to target.

        Args:
            source: Source node ID.
            target: Target node ID.

        Returns:
            A path as a list of node IDs, or None if no path exists.
        """
        paths = self.find_paths(source, target)
        return paths[0] if paths else None

    def get_subgraph_by_edge_type(self, edge_type: EdgeType | str) -> "GraphMgr":
        """Get a subgraph containing only edges of the specified type.

        Args:
            edge_type: The type of edges to include in the subgraph.

        Returns:
            A new GraphMgr instance containing the subgraph.
        """
        instance = GraphMgr()

        if isinstance(edge_type, str):
            edge_type = EdgeType(edge_type)

        # Add nodes
        for node_id in self.graph.nodes():
            node_attrs = self.get_node_attributes(node_id)
            node = Node(**node_attrs)
            instance.add_node(node)

        # Add edges of the specified type
        for source, target, data in self.graph.edges(data=True):
            if data.get("type") == edge_type.value:
                instance.add_edge(source, target, edge_type=edge_type)

        return instance

    def get_subgraph(self, node_ids: List[str]) -> "GraphMgr":
        """Get a subgraph containing only the specified nodes.

        Args:
            node_ids: List of node IDs to include in the subgraph.

        Returns:
            A new GraphMgr instance containing the subgraph.
        """
        instance = GraphMgr()

        # Add nodes
        for node_id in node_ids:
            if node_id in self.graph:
                node_attrs = self.get_node_attributes(node_id)
                node = Node(
                    id=node_attrs["id"], name=node_attrs["name"], marker=node_attrs["marker"], ref=node_attrs.get("ref")
                )
                instance.add_node(node)

        # Add edges
        for source, target in self.graph.edges():
            if source in node_ids and target in node_ids:
                instance.add_edge(source, target)

        return instance

    def get_descendants_subgraph(self, node_id: str) -> "GraphMgr":
        """Create a subgraph containing the specified node and all its descendants.

        Args:
            node_id: The ID of the root node to start from.

        Returns:
            A new GraphMgr instance containing the node and all its descendants.
        """
        if node_id not in self.graph:
            return GraphMgr()  # Return empty graph if node doesn't exist

        # Use NetworkX's built-in bfs_tree to get a tree of all descendants
        descendants_tree = nx.bfs_tree(self.graph, node_id)

        # Get the node IDs from the tree
        node_ids = list(descendants_tree.nodes())

        # Create a subgraph with the descendants
        return self.get_subgraph(node_ids)

    def to_markdown(self, root_nodes: Optional[List[str]] = None, indent: int | str = 2) -> str:
        """Convert the graph back to a markdown string with hierarchical list items.

        Args:
            root_nodes: Optional list of node IDs to use as roots. If not provided,
                        will use all nodes with no incoming edges.

        Returns:
            A markdown string representing the graph as hierarchical list items.
        """
        if not self.graph.nodes:
            return ""  # Empty graph results in empty string

        # If no root nodes provided, use all nodes without incoming edges
        if root_nodes is None:
            root_nodes = self.get_roots()

        # If still no root nodes (graph might have cycles), use any node
        if not root_nodes and self.graph.nodes:
            root_nodes = [next(iter(self.graph.nodes))]

        # Get a list of edges with type="requires"
        requires_edges = [
            (u, v) for u, v, data in self.graph.edges(data=True) if data.get("type") == EdgeType.REQUIRES.value
        ]

        # Create the subgraph
        requires_subgraph = self.graph.edge_subgraph(requires_edges)

        if isinstance(indent, int):
            indent = " " * indent

        # Recursive function to process each node and its children
        def process_node(graph: nx.DiGraph, node_id: str, level: int, visited: set) -> str:
            if node_id in visited:
                return ""  # Prevent cycles

            visited.add(node_id)
            attrs = self.get_node_attributes(node_id)
            result = indent * level + "- " + attrs.get("name", "") + "\n"

            # Sort children to ensure consistent output
            children = list(graph.successors(node_id))

            for child in children:
                # Only process children that weren't handled as reference links
                if child not in visited:
                    result += process_node(graph, child, level + 1, visited.copy())

            return result

        # Process all root nodes
        result = ""
        for root in root_nodes:
            if root in requires_subgraph.nodes:
                result += process_node(requires_subgraph, root, 0, set())

        return result
