from .node import Node


# TODO stubs so that the tests pass
class Question(Node):
    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        if self._blocked:
            return "?"
        if self._completed:
            return "Q"
        return "q"


# class Question(Task):
#     """Question node with state propagation and resolution logic. They are similar to tasks but they cannot be
#     explicitly actioned (start, complete, reopen). Instead, they determine their status based on their children.

#     If a question has a Decision or Answer node as a child, it will be marked as COMPLETED.
#     If a question contains a blocked node, it will be marked as BLOCKED.
#     If a question contains no children, it will be marked as OPEN.
#     Otherwise it will be marked as IN_PROGRESS.

#     """

#     markers = {
#         NodeState.OPEN: "?",
#         NodeState.IN_PROGRESS: "?/",
#         NodeState.BLOCKED: "?!",
#         NodeState.COMPLETED: "?✓",
#         NodeState.CANCELLED: "?-",
#     }

#     def _recompute_state(self, notify=True):
#         # Collect states of child tasks
#         children = self._get_stateful_children()

#         # If no child tasks, maintain current state
#         if not children:
#             new_state = NodeState.OPEN

#         child_states = [child.state for child in children]

#         # Apply state derivation rules
#         if any(state == NodeState.BLOCKED for state in child_states):
#             # if any child is blocked, the question is blocked
#             new_state = NodeState.BLOCKED
#         elif any(isinstance(child, (Decision, Answer)) for child in children if child.state == NodeState.COMPLETED):
#             # if any child is a completed decision or answer, the question is completed
#             new_state = NodeState.COMPLETED
#         # otherwise the usual in-progress logic applies
#         elif any(state in {NodeState.IN_PROGRESS, NodeState.COMPLETED} for state in child_states):
#             new_state = NodeState.IN_PROGRESS
#         else:
#             new_state = NodeState.OPEN

#         # Only update if state actually changes
#         if self._state != new_state:
#             self._state = new_state

#             # Notify parent if needed
#             if notify:
#                 self._notify_parent()

#     def _get_leaf_state(self) -> NodeState:
#         return NodeState.OPEN
