from anytree import NodeMixin
from typing import Optional, List, Set
from enum import Enum


class NodeType(Enum):
    TASK = "task"
    QUESTION = "question"
    GOAL = "goal"
    ALTERNATIVE = "alternative"
    DECISION = "decision"

    def __str__(self):
        return self.value


class Node(NodeMixin):
    """Base node class for all tree nodes in the productivity system."""

    def __init__(self, content: str, id: Optional[str] = None, parent=None, children=None):
        self.content = content
        self.id = id
        self.parent = parent
        if children:
            self.children = children

    def __repr__(self):
        return f"{self.__class__.__name__}({self.content})"


class TaskState(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def __str__(self):
        return self.value

    @classmethod
    def resolved_states(cls) -> Set["TaskState"]:
        """States that indicate a task requires no more work."""
        return {cls.COMPLETED, cls.CANCELLED}


class Task(Node):
    """Task node with state propagation and resolution logic."""

    def __init__(
        self,
        content: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        state: TaskState = TaskState.OPEN,
    ):
        super().__init__(content, id, parent, children)
        self._state = state
        if parent:
            parent.add_child(self)
        # Initial state computation if we have children
        if children and any(isinstance(child, Task) for child in children):
            self._recompute_state(notify=False)

    @property
    def state(self) -> TaskState:
        return self._state

    @state.setter
    def state(self, new_state: TaskState):
        """State setter with validation and propagation."""
        if self._state != new_state:
            self._state = new_state
            self._notify_parent()

            # Handle downward propagation for CANCELLED state
            if new_state == TaskState.CANCELLED:
                self._propagate_cancellation()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.content}, state={self.state})"

    def __str__(self):
        return f"{self.content} ({self.state})"

    def start(self) -> bool:
        """Start work on this task, setting it to IN_PROGRESS state.

        Returns:
            bool: True if the state was changed, False otherwise
        """
        if self.is_leaf and self.state not in TaskState.resolved_states():
            self.state = TaskState.IN_PROGRESS
            return True
        return False

    def block(self) -> bool:
        """Mark task as BLOCKED.

        Returns:
            bool: True if the state was changed, False otherwise
        """
        if self.state != TaskState.BLOCKED:
            self.state = TaskState.BLOCKED
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
        if self.state == TaskState.COMPLETED:
            return False

        # Tasks with no children can be completed directly
        if self.is_leaf:
            self.state = TaskState.COMPLETED
            return True

        # Tasks with children need all children to be resolved
        child_tasks = [child for child in self.children if isinstance(child, Task)]
        if all(child.state in TaskState.resolved_states() for child in child_tasks):
            self.state = TaskState.COMPLETED
            return True

        return False

    def cancel(self) -> bool:
        """Cancel this task and all its subtasks.

        Returns:
            bool: True if cancellation was successful
        """
        if self.state != TaskState.CANCELLED:
            self.state = TaskState.CANCELLED
            return True
        return False

    def reopen(self) -> bool:
        """Reopen a completed or cancelled leaf task.

        Returns:
            bool: True if reopening was successful
        """
        if self.is_leaf and self.state in TaskState.resolved_states():
            # Leaf tasks go to OPEN state
            self.state = TaskState.OPEN
            self._notify_parent()
            return True

        return False

    def _notify_parent(self):
        """Notify parent of state change to trigger state recomputation."""
        if self.parent and isinstance(self.parent, Task):
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
        if any(state == TaskState.BLOCKED for state in child_states):
            new_state = TaskState.BLOCKED
        elif all(state == TaskState.CANCELLED for state in child_states):
            new_state = TaskState.CANCELLED
        elif all(state in TaskState.resolved_states() for state in child_states):
            new_state = TaskState.COMPLETED
        elif any(state in {TaskState.IN_PROGRESS, TaskState.COMPLETED} for state in child_states):
            new_state = TaskState.IN_PROGRESS
        else:
            new_state = TaskState.OPEN

        # Only update if state actually changes
        if self._state != new_state:
            self._state = new_state

            # Notify parent if needed
            if notify:
                self._notify_parent()

    def _propagate_cancellation(self):
        """Propagate CANCELLED state to all children."""
        for child in self.children:
            if isinstance(child, Task) and child.state != TaskState.CANCELLED:
                child.state = TaskState.CANCELLED

    def is_resolved(self) -> bool:
        """Check if task is in a resolved state (COMPLETED or CANCELLED)."""
        return self.state in TaskState.resolved_states()

    def can_complete(self) -> bool:
        """Check if task can be marked as complete."""
        if self.is_leaf:
            return self.state not in TaskState.resolved_states()

        child_tasks = [child for child in self.children if isinstance(child, Task)]
        return all(child.state in TaskState.resolved_states() for child in child_tasks)

    def add_child(self, node: Node) -> None:
        """Add a child task and recompute state."""
        node.parent = self
        self._recompute_state()

    def remove_child(self, node: Node) -> None:
        """Remove a child task and recompute state."""
        if node in self.children:
            node.parent = None
            self._recompute_state()
