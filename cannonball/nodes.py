from typing import Optional
import networkx as nx
from cannonball.utils import get_subgraph, EdgeType
from enum import Enum


class Node:
    """A node in the graph."""

    def __init__(
        self,
        id: str,
        name: str,
        marker: Optional[str] = None,
        ref: Optional[str] = None,
    ) -> None:
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

    @staticmethod
    def from_contents(id: str, name: str, marker: Optional[str] = None, ref: Optional[str] = None) -> "Node":
        """Creates a node with the correct derived class based on the content.

        Args:
            id: The unique ID of the node.
            name: The name of the node.
            marker: Optional marker that determines the node type:
                None: Thought node
                " ": Open task
                "/": In-progress task
                "x": Completed task
                "-": Cancelled task
                "?": Question node
                "g": Goal node
                "P": Problem node
            ref: Optional reference for the node.

        Returns:
            An instance of the appropriate node subclass.

        Raises:
            ValueError: If an unknown marker is provided.
        """

        if marker is None:
            return Thought(id, name, marker, ref)
        if marker == " ":
            return Task(id, name, ref, TaskType.OPEN)
        if marker == "/":
            return Task(id, name, ref, TaskType.IN_PROGRESS)
        if marker == "x":
            return Task(id, name, ref, TaskType.COMPLETED)
        if marker == "-":
            return Task(id, name, ref, TaskType.CANCELLED)
        if marker == "?":
            return Question(id, name, marker, ref)
        if marker == "g":
            return Goal(id, name, marker, ref)
        if marker == "P":
            return Problem(id, name, marker, ref)

        raise ValueError(f"Unknown marker '{marker}' for node '{name}'")

    def __hash__(self) -> str:
        """Return a hash of the node ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a string representation of the node."""
        return f"{self.__class__.__name__}({self.name})"


class BlockingNode(Node):
    """A node that can potentially block its parent nodes based on its state."""

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """Determine if this node is in blocked state.

        By default, a node is blocked if any of its children are blocked.
        This can be overridden by subclasses to implement custom blocking logic.

        Args:
            graph: The current graph

        Returns:
            bool: True if this node is blocked
        """
        subgraph = get_subgraph(graph, root_node=self, edge_type=EdgeType.REQUIRES)
        return (
            any(getattr(node, "is_blocked", lambda _: False)(subgraph) for node in subgraph.successors(self))
            if subgraph
            else False
        )


class Thought(BlockingNode):
    """A thought node is a node without a marker (single `-` bullet point).
    It just propagates the blocking state of its children."""

    pass


class TaskType(Enum):
    """An enumeration of task types."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BlockingNode):
    """A task node that blocks until completed."""

    def __init__(
        self,
        id: str,
        name: str,
        ref: Optional[str] = None,
        status: TaskType = TaskType.OPEN,
    ) -> None:
        """Initialize a task node with an ID, name, and optional marker and reference.

        Args:
            id: The unique ID of the node.
            name: The name of the node.
            marker: Optional marker for the node.
            ref: Optional reference for the node.
        """
        self.status_markers = {
            TaskType.OPEN: " ",
            TaskType.IN_PROGRESS: "/",
            TaskType.COMPLETED: "x",
            TaskType.CANCELLED: "-",
        }

        # Derive marker from status
        marker = self.status_markers[status]
        super().__init__(id, name, marker, ref)
        self._status = status

    @property
    def status(self):
        """Returns the status."""
        return self._status

    @status.setter
    def status(self, status):
        """Sets the status and appropriate marker."""
        self._status = status
        self.marker = self.status_markers[status]

    def is_finished(self) -> bool:
        """Check if the task is completed or cancelled.

        Returns:
            bool: True if the task is completed or cancelled
        """
        return self._status in (TaskType.COMPLETED, TaskType.CANCELLED)

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """A task blocks if it's not completed."""

        blocked = super().is_blocked(graph)

        # A task is blocked if any of its children are blocked or if it is not finished (completed or cancellled)
        return blocked or not self.is_finished()


class Question(BlockingNode):
    """A question node that blocks until it's resolved."""

    def __init__(
        self,
        id: str,
        name: str,
        marker: Optional[str] = None,
        ref: Optional[str] = None,
        is_resolved: bool = False,
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

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """A question blocks if it's not resolved."""
        blocked = super().is_blocked(graph)

        # A question is blocked if any of its children are blocked or if it is not resolved
        return blocked or not self.is_resolved


class Problem(BlockingNode):
    """A problem node that always blocks."""

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """A problem always blocks."""
        return True


class Goal(BlockingNode):
    """A goal node that blocks until achieved."""

    def __init__(
        self,
        id: str,
        name: str,
        marker: Optional[str] = None,
        ref: Optional[str] = None,
        is_achieved: bool = False,
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

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """A goal blocks if it's not achieved."""
        blocked = super().is_blocked(graph)
        # A goal is blocked if any of its children are blocked or if it is not achieved
        return blocked or not self.is_achieved
