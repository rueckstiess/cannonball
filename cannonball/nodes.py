from dataclasses import dataclass
from typing import Optional
import networkx as nx


@dataclass
class Node:
    """A node in the graph."""

    id: str
    name: str
    marker: Optional[str] = None
    ref: Optional[str] = None
    is_blocking: bool = False


@dataclass
class BlockingNode(Node):
    """A node that can potentially block its parent nodes based on its state."""

    can_block: bool = True  # Whether this node type can block parent nodes

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

        return False


@dataclass
class QuestionNode(BlockingNode):
    """A question node that blocks until it's resolved."""

    is_resolved: bool = False

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """A question blocks if it's not resolved."""
        return not self.is_resolved

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        pass


@dataclass
class ProblemNode(BlockingNode):
    """A problem node that always blocks."""

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """A problem always blocks."""
        return True


@dataclass
class GoalNode(BlockingNode):
    """A goal node that blocks until achieved."""

    is_achieved: bool = False

    def is_blocking(self, graph: nx.DiGraph) -> bool:
        """A goal blocks if it's not achieved."""
        return not self.is_achieved
