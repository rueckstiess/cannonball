from typing import Optional
import networkx as nx
from cannonball.utils import get_subgraph, EdgeType


class Node:
    """A node in the graph."""

    def __init__(self, id: str, name: str, marker: Optional[str] = None, ref: Optional[str] = None) -> None:
        """Initialize a new node with an ID, name, and optional marker and reference.

        Args:
            id: The unique ID of the node.
            name: The name of the node.
            marker: Optional marker for the node.
            ref: Optional reference for the node.
        """
        self.id = id
        self.name = name
        self.marker = marker
        self.ref = ref

    def __hash__(self) -> str:
        """Return a hash of the node ID."""
        return hash(self.id)


class BlockingNode(Node):
    """A node that can potentially block its parent nodes based on its state."""

    can_block = True

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """Determine if this node is currently blocking based on its graph.

        Args:
            graph: The current graph

        Returns:
            bool: True if this node is blocking its parents, False otherwise
        """
        # Default implementation (to be overridden by specific node types)
        return False

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """Determine if this node is blocked by any of its children.

        By default, this method returns True if any of its "required" descendant nodes are blocking

        Args:
            graph: The current graph

        Returns:
            bool: True if this node is blocked by any graph, False otherwise
        """
        subgraph = get_subgraph(graph, root_node=self, edge_type=EdgeType.REQUIRES)
        return (
            any(getattr(node, "is_blocking", lambda _: False)(subgraph) for node in subgraph if node != self)
            if subgraph
            else False
        )


class QuestionNode(BlockingNode):
    """A question node that blocks until it's resolved."""

    def __init__(
        self, id: str, name: str, marker: Optional[str] = None, ref: Optional[str] = None, is_resolved: bool = False
    ) -> None:
        """Initialize a question node with an ID, name, and optional marker and reference.

        Args:
            id: The unique ID of the node.
            name: The name of the node.
            marker: Optional marker for the node.
            ref: Optional reference for the node.
        """
        super().__init__(id, name, marker, ref)
        self.is_resolved = is_resolved

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """A question blocks if it's not resolved."""
        return not self.is_resolved


class ProblemNode(BlockingNode):
    """A problem node that always blocks."""

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """A problem always blocks."""
        return True


class GoalNode(BlockingNode):
    """A goal node that blocks until achieved."""

    def __init__(
        self, id: str, name: str, marker: Optional[str] = None, ref: Optional[str] = None, is_achieved: bool = False
    ) -> None:
        """Initialize a goal node with an ID, name, and optional marker and reference.

        Args:
            id: The unique ID of the node.
            name: The name of the node.
            marker: Optional marker for the node.
            ref: Optional reference for the node.
        """
        super().__init__(id, name, marker, ref)
        self.is_achieved = is_achieved

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """A goal blocks if it's not achieved."""
        return not self.is_achieved
