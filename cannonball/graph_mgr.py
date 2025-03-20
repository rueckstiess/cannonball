from .nodes import Node
from .utils import (
    get_raw_text_from_listtem,
    walk_list_items,
    extract_node_marker_and_refs,
    EdgeType,
)
import networkx as nx
from marko import Markdown
from typing import Dict, Optional, List
import uuid


class GraphMgr:
    """A graph manager that manages a directed graph of nodes from markdown list items."""

    parser = Markdown()

    def __init__(self) -> None:
        """Initialize a new graph manager with an empty graph."""
        self.nxgraph = nx.DiGraph()
        self.nodes_by_ref = {}  # Maps reference IDs to node IDs

    @classmethod
    def from_graph(cls, graph: nx.DiGraph) -> "GraphMgr":
        """Create a GraphMgr instance from an existing NetworkX graph.

        Args:
            graph: A NetworkX directed graph.

        Returns:
            A GraphMgr instance containing the provided graph.
        """
        instance = cls()
        instance.nxgraph = graph
        instance.nodes_by_ref = {node: data.get("ref") for node, data in graph.nodes(data=True) if data.get("ref")}
        return instance

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add.
        """
        self.nxgraph.add_node(node, **node.__dict__)

        # If the node has a reference, add it to the ref mapping
        if node.ref:
            self.nodes_by_ref[node.ref] = node

    def add_edge(self, parent: Node, child: Node, edge_type: EdgeType = EdgeType.REQUIRES) -> None:
        """Add a directed edge from parent to child with an edge type.

        Args:
            parent: The parent node.
            child: The child node.
            edge_type: The type of edge (default is EdgeType.REQUIRES).
        """
        self.nxgraph.add_edge(parent, child, type=edge_type.value)

    def get_node_by_ref(self, ref: str) -> Optional[Node]:
        """Get a node by its reference ID.

        Args:
            ref: The reference ID of the node.

        Returns:
            The node if found, None otherwise.
        """
        return self.nodes_by_ref.get(ref)

    def get_node_attributes(self, node: Node) -> Dict:
        """Get the attributes of a node.

        Args:
            node_id: The ID of the node.

        Returns:
            Dictionary of node attributes.
        """
        return self.nxgraph.nodes[node]

    def get_requires_subgraph(self) -> nx.DiGraph:
        """Get the subgraph of all nodes connected with requires edges.

        Returns:
            A directed subgraph containing only the nodes connected with "requires" edges.
        """
        requires_edges = [
            (u, v) for u, v, data in self.nxgraph.edges(data=True) if data.get("type") == EdgeType.REQUIRES.value
        ]
        return self.nxgraph.edge_subgraph(requires_edges)

    def has_circular_dependencies(self) -> bool:
        """Check if the subgraph connected with "requires" edges is acyclic.

        Returns:
            True if the subsgraph is acyclic, False otherwise.
        """
        requires_subgraph = self.get_requires_subgraph()
        # Check if the subgraph is acyclic
        return not nx.is_directed_acyclic_graph(requires_subgraph)

    def topological_sort(self) -> List[Node]:
        """Return nodes in topological order based on "requires" edges.

        Returns:
            List of node IDs in topological order.
        """
        requires_subgraph = self.get_requires_subgraph()

        if not nx.is_directed_acyclic_graph(requires_subgraph):
            raise ValueError("Graph has circular dependencies and cannot be topologically sorted")

        return list(nx.topological_sort(requires_subgraph))

    def get_roots(self) -> List[Node]:
        """Get all root nodes (nodes with no incoming edges).

        Returns:
            List of root nodes
        """
        return [n for n in self.nxgraph.nodes() if self.nxgraph.in_degree(n) == 0]

    def get_leaves(self) -> List[Node]:
        """Get all leaf nodes (nodes with no outgoing edges).

        Returns:
            List of leaf node IDs.
        """
        return [n for n in self.nxgraph.nodes() if self.nxgraph.out_degree(n) == 0]

    @classmethod
    def from_markdown(cls, markdown: str) -> "GraphMgr":
        """Create a graph from a markdown string.

        Args:
            markdown: A markdown string containing hierarchical list items.

        Returns:
            A GraphMgr instance containing the constructed DAG.
        """
        instance = cls()
        ast = cls.parser.parse(markdown)

        # First pass: create nodes and collect reference links
        item_to_node = {}  # Maps ListItem objects to node IDs
        node_to_links = {}  # Maps node IDs to their reference links

        for list_item, parent_item, level in walk_list_items(ast):
            text = get_raw_text_from_listtem(list_item)
            marker, ref, ref_links = extract_node_marker_and_refs(text)

            # Always use a UUID for node ID to ensure uniqueness

            # Create and add the node
            node = Node(id=str(uuid.uuid4())[:8], name=text, marker=marker, ref=ref)
            instance.add_node(node)

            # Map the ListItem to its node ID for the second pass
            item_to_node[list_item] = node

            # Store the reference links for the second pass
            if ref_links:
                node_to_links[node] = ref_links

        # Second pass: create all edges
        for list_item, parent_item, _ in walk_list_items(ast):
            node = item_to_node.get(list_item)
            if not node:
                continue

            # Create parent-child (requires) edge if applicable
            if parent_item and parent_item in item_to_node:
                parent = item_to_node[parent_item]
                instance.add_edge(parent, node, edge_type=EdgeType.REQUIRES)

            # Process reference links for this node
            if node in node_to_links:
                for ref_id in node_to_links[node]:
                    # Find the node with this reference ID
                    target_node = instance.get_node_by_ref(ref_id)
                    if target_node and target_node != node:  # Avoid self-references
                        # Create a reference edge from source to target
                        instance.add_edge(node, target_node, edge_type=EdgeType.REFERENCES)

        return instance

    def to_dict(self) -> Dict:
        """Convert the graph to a dictionary for serialization.

        Returns:
            Dictionary representation of the graph.
        """
        return {
            "nodes": [self.nxgraph.nodes[n] for n in self.nxgraph.nodes()],
            "edges": [{"source": s, "target": t, **d} for s, t, d in self.nxgraph.edges(data=True)],
        }

    def to_markdown(self, root_nodes: Optional[List[Node]] = None, indent: int | str = 2) -> str:
        """Convert the graph back to a markdown string with hierarchical list items.

        Args:
            root_nodes: Optional list of node IDs to use as roots. If not provided,
                        will use all nodes with no incoming edges.

        Returns:
            A markdown string representing the graph as hierarchical list items.
        """
        if not self.nxgraph.nodes:
            return ""  # Empty graph results in empty string

        # If no root nodes provided, use all nodes without incoming edges
        if root_nodes is None:
            root_nodes = self.get_roots()

        # If still no root nodes (graph might have cycles), use any node
        if not root_nodes and self.nxgraph.nodes:
            root_nodes = [next(iter(self.nxgraph.nodes))]

        # Get a list of edges with type="requires"
        requires_edges = [
            (u, v) for u, v, data in self.nxgraph.edges(data=True) if data.get("type") == EdgeType.REQUIRES.value
        ]

        # Create the subgraph
        requires_subgraph = self.nxgraph.edge_subgraph(requires_edges)

        if isinstance(indent, int):
            indent = " " * indent

        # Recursive function to process each node and its children
        def process_node(graph: nx.DiGraph, node: Node, level: int, visited: set) -> str:
            if node in visited:
                return ""  # Prevent cycles

            visited.add(node)
            attrs = self.get_node_attributes(node)
            result = indent * level + "- " + attrs.get("name", "") + "\n"

            # Sort children to ensure consistent output
            children = list(graph.successors(node))

            for child in children:
                # Only process children that weren't handled as reference links
                if child not in visited:
                    result += process_node(graph, child, level + 1, visited.copy())

            return result

        # Process all root nodes
        result = ""
        for root in root_nodes:
            if root in requires_subgraph:
                result += process_node(requires_subgraph, root, 0, set())

        return result
