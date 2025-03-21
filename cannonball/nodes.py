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

        self._node_attributes = ("id", "name", "marker", "ref")

    @staticmethod
    def from_contents(
        id: str, name: str, marker: Optional[str] = None, ref: Optional[str] = None
    ) -> "Node":
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
        if marker == "a":
            return Alternative(id, name, marker, ref)

        # Fallback to a generic BlockingNode if no specific type is matched
        return BlockingNode(id, name, marker, ref)

    def to_dict(self) -> dict:
        """Convert the relevant node attributes to a dictionary representation."""
        node_attrs = {attr: getattr(self, attr) for attr in self._node_attributes}
        node_attrs["type"] = self.__class__.__name__
        return node_attrs

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
        subgraph = get_subgraph(graph, root_node=self, edge_filter=EdgeType.REQUIRES)
        return (
            any(
                getattr(node, "is_blocked", lambda _: False)(subgraph)
                for node in subgraph.successors(self)
            )
            if subgraph
            else False
        )


class Thought(BlockingNode):
    """A thought node is a node without a marker (single `-` bullet point).
    It just propagates the blocking state of its children."""

    pass


class AlternativeContainer(BlockingNode):
    """A container that holds Alternative nodes for decision-making.

    AlternativeContainer implements special blocking logic for decision trees:

    1. Blocking Behavior:
       - Blocked if any non-Alternative child is blocked (standard behavior)
       - Blocked if it has Alternative children but doesn't have exactly one viable
         leaf Alternative in its entire subtree

    2. Leaf Alternative Definition:
       - A leaf Alternative is an Alternative with no Alternative children
       - Must be unblocked itself to be considered viable

    3. Decision Tree Semantics:
       - The container is considered "decided" when exactly one viable path exists
       - All viable leaf Alternatives in the subtree are counted, regardless of nesting
       - Only leaf Alternatives reachable through unblocked paths are counted

    This implementation ensures that a decision is fully resolved only when there's
    exactly one unambiguous path through the entire decision tree, even when alternatives
    are nested in a hierarchical structure.

    Examples:
        - A Question with two unblocked Alternatives: BLOCKED (no single choice)
        - A Question with one unblocked Alternative: NOT BLOCKED (clear choice)
        - A Question with one Alternative that has two unblocked sub-Alternatives: BLOCKED (no clear leaf choice)
        - A Question with all Alternatives blocked: BLOCKED (no viable choice)
    """

    def is_blocked(self, graph):
        # First check if we're blocked by standard criteria (non-alternative children)
        non_alternative_children = [
            n
            for n in graph.successors(self)
            if graph.edges[self, n].get("type") == EdgeType.REQUIRES.value
            and not isinstance(n, Alternative)
        ]

        if any(n.is_blocked(graph) for n in non_alternative_children):
            return True

        # Get direct Alternative children with REQUIRES edges
        direct_alternatives = [
            n
            for n in graph.successors(self)
            if graph.edges[self, n].get("type") == EdgeType.REQUIRES.value
            and isinstance(n, Alternative)
        ]

        # If no alternatives, we're not blocked
        if not direct_alternatives:
            return False

        # Use helper function to collect viable leaf alternatives
        viable_leaf_alternatives = []
        self._collect_viable_leaf_alternatives(
            graph, direct_alternatives, viable_leaf_alternatives
        )

        # We are blocked if there is not exactly one viable leaf alternative
        return len(viable_leaf_alternatives) != 1

    def _collect_viable_leaf_alternatives(self, graph, alternatives, result_list):
        """
        Recursively collect viable leaf alternatives.

        Args:
            graph: The graph containing the nodes
            alternatives: List of alternative nodes to check
            result_list: List where viable leaf alternatives will be stored
        """
        for alt in alternatives:
            # Skip blocked alternatives - they can't lead to viable paths
            if alt.is_blocked(graph):
                continue

            # Get this alternative's direct alternative children
            alt_children = [
                n
                for n in graph.successors(alt)
                if graph.edges[alt, n].get("type") == EdgeType.REQUIRES.value
                and isinstance(n, Alternative)
            ]

            if alt_children:
                # If it has alternative children, recursively process them
                self._collect_viable_leaf_alternatives(graph, alt_children, result_list)
            else:
                # If it's a leaf alternative (no alternative children) and not blocked, add it
                result_list.append(alt)


class Alternative(BlockingNode):
    """An alternative node that can be selected as a child of an AlternativeContainer.

    Blocking behaviour of an Alternative is different from a standard BlockingNode.
        - it blocks on non-Alternative children as usual
        - additionally, it blocks if **all** of its Alternative children are blocked
    """

    def is_blocked(self, graph):
        # if it doesn't have any children, it is not blocked
        if graph.out_degree(self) == 0:
            return False

        # First check non-Alternative children (standard BlockingNode behavior)
        non_alt_subgraph = get_subgraph(
            graph,
            root_node=self,
            node_filter=lambda n: not isinstance(n, Alternative),
            edge_filter=EdgeType.REQUIRES,
        )

        if any(
            node.is_blocked(non_alt_subgraph)
            for node in non_alt_subgraph.successors(self)
            if non_alt_subgraph.has_node(node)
        ):
            return True

        # Get all direct Alternative children
        alt_children = [
            n
            for n in graph.successors(self)
            if graph.edges[self, n].get("type") == EdgeType.REQUIRES.value
            and isinstance(n, Alternative)
        ]

        # If no Alternative children, we're not blocked by alternatives
        if not alt_children:
            return False

        # For intermediate alternatives: blocked if all Alternative children are blocked
        return all(child.is_blocked(graph) for child in alt_children)


class TaskType(Enum):
    """An enumeration of task types."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(AlternativeContainer):
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
        self._node_attributes = ("id", "name", "marker", "ref", "_status")

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


class Question(AlternativeContainer):
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
        self._node_attributes = ("id", "name", "marker", "ref", "is_resolved")

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


class Goal(AlternativeContainer):
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
        self._node_attributes = ("id", "name", "marker", "ref", "is_achieved")

    def is_blocked(self, graph: nx.DiGraph) -> bool:
        """A goal blocks if it's not achieved."""
        blocked = super().is_blocked(graph)
        # A goal is blocked if any of its children are blocked or if it is not achieved
        return blocked or not self.is_achieved


class Decision(BlockingNode):
    pass
