from anytree import NodeMixin
from typing import Optional, Set
from enum import Enum
from marko import Markdown
from marko.block import ListItem
from .utils import (
    walk_list_items,
    extract_node_marker_and_refs,
    get_raw_text_from_listtem,
    extract_str_content,
)
import uuid


def parse_markdown(content: str) -> "Node":
    """Parse a markdown string into a Nodes tree.

    Args:
        markdown (str): The markdown string to parse.

    Returns:
        The root node of the parsed tree.
    """
    parser = Markdown()
    ast = parser.parse(content)
    root = None

    def _convert_li_to_node(li: Optional[ListItem]) -> Node:
        if li is None:
            return None
        text = get_raw_text_from_listtem(li)
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        content = extract_str_content(text)

        node_id = str(uuid.uuid4())[:8]
        return Node.from_contents(id=node_id, content=content, marker=marker)

    item_to_node = {}

    for li, parent_li, level in walk_list_items(ast):
        if li in item_to_node:
            node = item_to_node[li]
        else:
            node = _convert_li_to_node(li)
            item_to_node[li] = node

        # this must already exist since we're parsing a tree
        parent = item_to_node[parent_li] if parent_li else None

        if not parent:
            root = node

        if parent:
            node.parent = parent
            parent.add_child(node)

    return root


class NodeType(Enum):
    TASK = "task"
    QUESTION = "question"
    GOAL = "goal"
    ALTERNATIVE = "alternative"
    DECISION = "decision"

    def __str__(self):
        return self.value


class NodeState(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def __str__(self):
        return self.value

    @classmethod
    def resolved_states(cls) -> Set["NodeState"]:
        """States that indicate a task requires no more work."""
        return {cls.COMPLETED, cls.CANCELLED}


class Node(NodeMixin):
    """Base node class for all tree nodes in the productivity system."""

    def __init__(self, name: str, id: Optional[str] = None, parent=None, children=None):
        self.name = name
        self.id = id
        self.parent = parent
        if children:
            self.children = children

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    @staticmethod
    def from_contents(
        id: str, content: str, marker: Optional[str] = None, **kwargs
    ) -> "Node":
        """Create a node from contents."""

        MD_MARKER_TO_NODE = {
            None: (Bullet, None),
            " ": (Task, NodeState.OPEN),
            "/": (Task, NodeState.IN_PROGRESS),
            "!": (Task, NodeState.BLOCKED),
            "x": (Task, NodeState.COMPLETED),
            "-": (Task, NodeState.CANCELLED),
            "?": (Question, NodeState.OPEN),
            "D": (Decision, NodeState.OPEN),
            "A": (Answer, NodeState.COMPLETED),
        }

        # Get class and state, with fallback to default open StatefulNode if not found
        cls, state = MD_MARKER_TO_NODE.get(marker, (StatefulNode, NodeState.OPEN))
        node = cls(content, id, state=state, **kwargs)
        return node


class StatefulNode(Node):
    """Stateful node with state propagation and resolution logic."""

    markers = {
        NodeState.OPEN: " ",
        NodeState.IN_PROGRESS: "/",
        NodeState.BLOCKED: "!",
        NodeState.COMPLETED: "✓",
        NodeState.CANCELLED: "-",
    }

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        state: NodeState = NodeState.OPEN,
    ):
        super().__init__(name, id, parent, children)
        self._state = state
        if parent:
            parent.add_child(self)
        # Initial state computation if we have children
        if children and any(isinstance(child, Task) for child in children):
            self._recompute_state(notify=False)

    @property
    def state(self) -> NodeState:
        return self._state

    @state.setter
    def state(self, new_state: NodeState):
        """State setter with validation and propagation."""
        if self._state != new_state:
            self._state = new_state
            self._notify_parent()

            # Handle downward propagation for CANCELLED state
            if new_state == NodeState.CANCELLED:
                self._propagate_cancellation()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, state={self.state})"

    def __str__(self):
        return f"[{self.markers[self.state]}] {self.name}"

    def _notify_parent(self):
        """Notify parent of state change to trigger state recomputation."""
        if self.parent:
            self.parent._recompute_state()

    def _recompute_state(self, notify: bool = True):
        """Derive task state from children's states.

        Args:
            notify: Whether to notify parent after recomputation
        """
        # Skip for leaf nodes - their state is set explicitly
        if self.is_leaf:
            return

        # Collect states of child tasks
        child_tasks = [child for child in self.children if isinstance(child, Task)]

        # If no child tasks, maintain current state
        if not child_tasks:
            return

        child_states = [child.state for child in child_tasks]

        # Apply state derivation rules
        if any(state == NodeState.BLOCKED for state in child_states):
            new_state = NodeState.BLOCKED
        elif all(state == NodeState.CANCELLED for state in child_states):
            new_state = NodeState.CANCELLED
        elif all(state in NodeState.resolved_states() for state in child_states):
            new_state = NodeState.COMPLETED
        elif any(
            state in {NodeState.IN_PROGRESS, NodeState.COMPLETED}
            for state in child_states
        ):
            new_state = NodeState.IN_PROGRESS
        else:
            new_state = NodeState.OPEN

        # Only update if state actually changes
        if self._state != new_state:
            self._state = new_state

            # Notify parent if needed
            if notify:
                self._notify_parent()

    def _propagate_cancellation(self):
        """Propagate CANCELLED state to all children."""
        for child in self.children:
            if isinstance(child, Task) and child.state != NodeState.CANCELLED:
                child.state = NodeState.CANCELLED

    def is_resolved(self) -> bool:
        """Check if task is in a resolved state (COMPLETED or CANCELLED)."""
        return self.state in NodeState.resolved_states()

    def can_complete(self) -> bool:
        """Check if task can be marked as complete."""
        if self.is_leaf:
            return self.state not in NodeState.resolved_states()

        child_tasks = [child for child in self.children if isinstance(child, Task)]
        return all(child.state in NodeState.resolved_states() for child in child_tasks)

    def add_child(self, node: Node) -> None:
        """Add a child task and recompute state."""
        node.parent = self
        self._recompute_state()

    def remove_child(self, node: Node) -> None:
        """Remove a child task and recompute state."""
        if node in self.children:
            node.parent = None
            self._recompute_state()


class Bullet(StatefulNode):
    """Bullet nodes behave like StatefulNodes internally but don't show their state in the UI and their state
    cannot be manually changed. They are for grouping tasks together and regular thoughts. They still
    propagate their chilren states to the parent."""

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        **kwargs,  # for API compatibility
    ):
        super().__init__(name, id, parent, children)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __str__(self):
        return f"{self.name}"


class Decision(StatefulNode):
    def __str__(self):
        return f"[D] {self.name}"


class Answer(StatefulNode):
    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        **kwargs,  # for API compatibility
    ):
        # Set the state to COMPLETED by default
        super().__init__(name, id, parent, children, state=NodeState.COMPLETED)

    def __str__(self):
        return f"[A] {self.name}"


class Task(StatefulNode):
    def start(self) -> bool:
        """Start work on this task, setting it to IN_PROGRESS state.

        Returns:
            bool: True if the state was changed, False otherwise
        """
        if self.is_leaf and self.state not in NodeState.resolved_states():
            self.state = NodeState.IN_PROGRESS
            return True
        return False

    def block(self) -> bool:
        """Mark task as BLOCKED.

        Returns:
            bool: True if the state was changed, False otherwise
        """
        if self.state != NodeState.BLOCKED:
            self.state = NodeState.BLOCKED
            return True
        return False

    def complete(self) -> bool:
        """Mark task as COMPLETED if possible.

        For tasks with children, all children must be in a resolved state
        (COMPLETED or CANCELLED) for the task to be completable.

        Returns:
            bool: True if task was completed, False if not completable
        """
        # Prevent completing if already completed
        if self.state == NodeState.COMPLETED:
            return False

        # Tasks with no children can be completed directly
        if self.is_leaf:
            self.state = NodeState.COMPLETED
            return True

        # Tasks with children need all children to be resolved
        child_tasks = [child for child in self.children if isinstance(child, Task)]
        if all(child.state in NodeState.resolved_states() for child in child_tasks):
            self.state = NodeState.COMPLETED
            return True

        return False

    def cancel(self) -> bool:
        """Cancel this task and all its subtasks.

        Returns:
            bool: True if cancellation was successful
        """
        if self.state != NodeState.CANCELLED:
            self.state = NodeState.CANCELLED
            return True
        return False

    def reopen(self) -> bool:
        """Reopen a completed or cancelled leaf task.

        Returns:
            bool: True if reopening was successful
        """
        if self.is_leaf and self.state in NodeState.resolved_states():
            # Leaf tasks go to OPEN state
            self.state = NodeState.OPEN
            self._notify_parent()
            return True

        return False


class Question(Task):
    """Question node with state propagation and resolution logic. They are similar to tasks but they cannot be
    explicitly actioned (start, complete, reopen). Instead, they determine their status based on their children.

    If a question has a Decision or Answer node as a child, it will be marked as COMPLETED.
    If a question contains a blocked node, it will be marked as BLOCKED.
    If a question contains no children, it will be marked as OPEN.
    Otherwise it will be marked as IN_PROGRESS.

    """

    markers = {
        NodeState.OPEN: "?",
        NodeState.IN_PROGRESS: "?/",
        NodeState.BLOCKED: "?!",
        NodeState.COMPLETED: "?✓",
        NodeState.CANCELLED: "?-",
    }

    def _recompute_state(self, notify=True):
        # Collect states of child tasks
        child_tasks = [
            child for child in self.children if isinstance(child, StatefulNode)
        ]

        # If no child tasks, maintain current state
        if not child_tasks:
            new_state = NodeState.OPEN

        child_states = [child.state for child in child_tasks]

        # Apply state derivation rules
        if any(state == NodeState.BLOCKED for state in child_states):
            # if any child is blocked, the question is blocked
            new_state = NodeState.BLOCKED
        elif any(
            isinstance(child, (Decision, Answer))
            for child in child_tasks
            if child.state == NodeState.COMPLETED
        ):
            # if any child is a completed decision or answer, the question is completed
            new_state = NodeState.COMPLETED
        # otherwise the usual in-progress logic applies
        elif any(
            state in {NodeState.IN_PROGRESS, NodeState.COMPLETED}
            for state in child_states
        ):
            new_state = NodeState.IN_PROGRESS
        else:
            new_state = NodeState.OPEN

        # Only update if state actually changes
        if self._state != new_state:
            self._state = new_state

            # Notify parent if needed
            if notify:
                self._notify_parent()
