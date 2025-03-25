from anytree import NodeMixin, find
from typing import Optional, Tuple
from textwrap import dedent
from marko import Markdown
from marko.block import ListItem
from .utils import (
    walk_list_items,
    extract_node_marker_and_refs,
    get_raw_text_from_listtem,
    extract_str_content,
)
import uuid


def parse_markdown(
    content: str, auto_resolve: bool = True, auto_decide: bool = False
) -> "Node":
    """Parse a markdown string into a Nodes tree.

    Args:
        markdown (str): The markdown string to parse.

    Returns:
        The root node of the parsed tree.
    """
    parser = Markdown()
    ast = parser.parse(dedent(content.strip("\n")))

    def _convert_li_to_node(li: Optional[ListItem]) -> Optional[Node]:
        if li is None:
            return None
        text = get_raw_text_from_listtem(li)
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        content = extract_str_content(text)

        node_id = str(uuid.uuid4())[:8]
        return Node.from_contents(
            id=node_id,
            content=content,
            marker=marker,
            auto_resolve=auto_resolve,
            auto_decide=auto_decide,
        )

    item_to_node = {}

    for li, parent_li, level in walk_list_items(ast):
        if li in item_to_node:
            node = item_to_node[li]
        else:
            node = _convert_li_to_node(li)
            item_to_node[li] = node

        # this must already exist since we're parsing a tree
        parent = item_to_node[parent_li] if parent_li else None

        if parent:
            node.parent = parent

    # if we have multiple roots, we need to attach them to a common root
    roots = [node for node in item_to_node.values() if node.is_root]
    if len(roots) > 1:
        root = StatefulNode("Root")
        root.children = roots
    else:
        root = roots[0] if roots else None
    return root


class Node(NodeMixin):
    """Base node class for all tree nodes in the productivity system."""

    def __init__(
        self, name: str, id: Optional[str] = None, parent=None, children=None, **kwargs
    ):
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

        # Values are tuples of (node class, done, blocked)
        MD_MARKER_TO_NODE = {
            None: (Bullet, True, False),
            " ": (Task, False, False),
            "!": (Task, False, True),
            "x": (Task, True, False),
            "D": (Decision, False, False),
            "A": (Answer, True, False),
            "?": (Question, False, False),
            "P": (Problem, False, True),
        }

        # Get class and state, with fallback to default open, unblocked StatefulNode if not found
        cls, completed, blocked = MD_MARKER_TO_NODE.get(
            marker, (StatefulNode, False, False)
        )
        node = cls(content, id, completed=completed, blocked=blocked, **kwargs)
        return node

    def find_by_name(self, prefix: str) -> Optional["Node"]:
        """Find a child node by its name or prefix of a name."""
        return find(self, lambda node: node.name.startswith(prefix))


class StatefulNode(Node):
    """Stateful node with state propagation and resolution logic."""

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        completed: bool = False,
        blocked: bool = False,
        **kwargs,
    ):
        if blocked and completed:
            raise ValueError("A node cannot be both blocked and completed.")

        self._blocked = blocked
        self._completed = completed
        super().__init__(name, id, parent, children)

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def is_blocked(self) -> bool:
        return self._blocked

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, completed={self._completed}, blocked={self._blocked})"

    def _notify_parent(self):
        """Notify parent of state change to trigger state recomputation."""
        if self.parent:
            self.parent._recompute_state()

    def _leaf_state(self) -> Tuple[bool, bool]:
        """The default state of a leaf node. Subclasses can override this behavior."""
        return self._completed, self._blocked

    def _recompute_state(self, notify: bool = True):
        """Derive task state from children's states.

        Args:
            notify: Whether to notify parent after recomputation
        """
        # current state is the default
        is_blocked = self._blocked
        is_completed = self._completed

        # Collect states of child tasks
        children = self.children

        if not children:
            # Stateful Nodes by default just maintain their current state when they are leaves.
            # Subclasses can override this bevavior.
            is_completed, is_blocked = self._leaf_state()
        else:
            # by default, a node is blocked if any of its children are blocked
            is_blocked = any(
                isinstance(child, StatefulNode) and child.is_blocked
                for child in children
            )

            # a node is completed if it is not blocked and all its children are completed
            is_completed = (
                False
                if is_blocked
                else all(
                    isinstance(child, StatefulNode) and child.is_completed
                    for child in children
                )
            )

        # if any state changed, update the state and optionally notify the parent
        if self._completed != is_completed or self._blocked != is_blocked:
            self._completed = is_completed
            self._blocked = is_blocked

            # Notify parent if needed
            if notify:
                self._notify_parent()

    def _post_detach(self, parent: Node):
        """Notify parent of detachment"""
        parent._recompute_state()

    def _post_attach(self, parent: Node):
        """Recompute state after attaching to parent."""
        parent._recompute_state()

    def _post_attach_children(self, children: list[Node]):
        """Recompute state after attaching children."""
        self._recompute_state()

    def _post_detach_children(self, children: list[Node]):
        """Recompute state after detaching children."""
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
        # Leaf bullets are completed and not blocked
        kwargs.pop(
            "completed", None
        )  # The None is the default value if key doesn't exist
        kwargs.pop("blocked", None)
        super().__init__(
            name, id, parent, children, completed=True, blocked=False, **kwargs
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __str__(self):
        return f"{self.name}"

    def _leaf_state(self) -> Tuple[bool, bool]:
        """Leaf Bullets are always completed and not blocked."""
        return (True, False)


class Task(StatefulNode):
    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        completed: bool = False,
        blocked: bool = False,
        auto_resolve: bool = True,
        **kwargs,
    ):
        super().__init__(
            name, id, parent, children, completed=completed, blocked=blocked
        )

        self._auto_resolve: bool = auto_resolve

    @property
    def auto_resolve(self) -> bool:
        return self._auto_resolve

    @auto_resolve.setter
    def auto_resolve(self, value: bool):
        """Set auto_resolve property and recompute state."""
        if self._auto_resolve != value:
            self._auto_resolve = value
            if self._auto_resolve:
                self._blocked = False
                self._completed = False
                self._recompute_state()

    def _leaf_state(self):
        if self._auto_resolve:
            return (False, False)
        return self._completed, self._blocked

    def block(self) -> bool:
        """Block a leaf task. Sets auto_resolve to False.

        Returns:
            bool: True if the state was changed, False otherwise
        """
        if not self.is_leaf:
            return False

        self._auto_resolve = False
        if self._blocked:
            return False

        self._blocked = True
        self._completed = False

        # Notify parent
        self._notify_parent()

        return True

    def unblock(self) -> bool:
        """Unblock a leaf task. Sets auto_resolve to False.

        Returns:
            bool: True if the state was changed, False otherwise
        """
        if not self.is_leaf:
            return False

        self._auto_resolve = False
        if not self._blocked:
            return False

        self._blocked = False
        self._completed = False

        # Notify parent
        self._notify_parent()

        return True

    def complete(self) -> bool:
        """Complete a leaf task. Sets auto_resolve to False.

        Returns:
            bool: True if task was completed, False if not completable
        """
        if not self.is_leaf:
            return False

        self._auto_resolve = False
        if self._completed or self._blocked:
            return False

        # Mark task as completed
        self._completed = True

        # Notify parent
        self._notify_parent()

        return True

    def reopen(self) -> bool:
        """Reopen a completed or blocked leaf task. Sets auto_resolve to False.

        Returns:
            bool: True if reopening was successful
        """
        if not self.is_leaf:
            return False

        self._auto_resolve = False
        if not self._completed:
            return False

        # Reopen task
        self._completed = False

        # Notify parent
        self._notify_parent()

        return True

    def _recompute_state(self, notify: bool = True):
        """Derive task state from children's states. If auto_resolve is enabled, use
        StatefulNode's recompute_state method. Otherwise do nothing.

        Args:
            notify: Whether to notify parent after recomputation
        """
        if self._auto_resolve:
            return super()._recompute_state(notify=notify)


class Decision(StatefulNode):
    """Decision nodes represent forks in the road."""

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        options: Optional[list[Node]] = None,
        completed: bool = False,
        blocked: bool = False,
        auto_decide: bool = False,
        **kwargs,
    ):
        self._decision = None
        self._options = options
        self._auto_decide = auto_decide

        super().__init__(
            name, id, parent, children, completed=completed, blocked=blocked
        )
        self._recompute_state()

    def __str__(self):
        return f"[D] {self.name}"

    @property
    def decision(self) -> Optional[Node]:
        """Get the decision node."""
        return self._decision

    @property
    def is_decided(self) -> bool:
        """Check if the decision has been made."""
        return self._decision is not None

    @property
    def auto_decide(self) -> bool:
        return self._auto_decide

    @auto_decide.setter
    def auto_decide(self, value: bool):
        """Set auto_decide property and recompute state."""
        if self._auto_decide != value:
            self._auto_decide = value
            if self._auto_decide:
                # If auto_decide is set to True, reset decision
                self._decision = None
            self._recompute_state()

    def set_options(self, options: list[Node]):
        """Set the options for the decision node.

        Args:
            options (list[Node]): List of option nodes.
        """
        self._options = options
        self._recompute_state()

    def get_options(self, include_blocked: bool = False) -> list[Node]:
        """Returns all options of the decision, optionally including blocked ones.
        Args:
            include_blocked (bool): Whether to include blocked nodes in the options.
        Returns:
            list[Node]: List of options, including blocked ones if specified.
        """
        options = self._options or self.children

        if include_blocked:
            return options
        return [n for n in options if not n.is_blocked]

    def decide(self, decision: Optional[Node]) -> bool:
        """Set the decision node to a specific node from the available options. Cannot be set to a blocked option.

        Args:
            decision (Node): The child node to set as the decision, or None to unset the decision.
        Returns:
            bool: True if the decision was set successfully, False otherwise.
        """
        # when we manually decide, set auto_decide to False
        self.auto_decide = False
        if decision == self._decision:
            return False
        if decision is None:
            self._decision = None
            self._completed = False
            self._recompute_state()
        if decision in self.get_options():
            self._decision = decision
            self._completed = True
            self._recompute_state()
            return True
        return False

    def _recompute_state(self, notify=True):
        """Recompute the state of the decision node."""

        # Get all options
        valid_options = self.get_options(include_blocked=False)

        # Reset invalid decision
        if self._decision and self._decision not in valid_options:
            self._decision = None

        # Determine blocked state first - a decision is blocked if there are no valid options
        is_blocked = len(valid_options) == 0

        # Determine completion state
        if is_blocked:
            # If blocked, we can't be completed
            is_completed = False
        else:
            if not self._auto_decide:
                # Manual decision mode - completed only if a decision has been made
                is_completed = self._decision is not None
            else:
                # Auto decision mode - we can complete if exactly one valid option exists
                if len(valid_options) == 1:
                    self._decision = valid_options[0]
                    is_completed = True
                else:
                    self._decision = None
                    is_completed = False

        # Update states
        if self._completed != is_completed or self._blocked != is_blocked:
            self._completed = is_completed
            self._blocked = is_blocked

            # Notify parent if needed
            if notify:
                self._notify_parent()


# TODO stubs so that the tests pass
class Question(StatefulNode):
    pass


class Answer(StatefulNode):
    pass


class Problem(StatefulNode):
    pass


# class Answer(StatefulNode):
#     """Answer nodes are semantically like Tasks, but they start in COMPLETED state (if they have no children).
#     Semantically, a Question looks for a completed Answer or Decision to be resolved.
#     They are also different from Tasks in that they cannot be started or cancelled manually, but they can
#     derive state from their children as usual.
#     """

#     def __init__(
#         self,
#         name: str,
#         id: Optional[str] = None,
#         parent: Optional[Node] = None,
#         children: Optional[list[Node]] = None,
#         **kwargs,  # for API compatibility
#     ):
#         # Set the state to COMPLETED by default
#         super().__init__(name, id, parent, children, state=NodeState.COMPLETED)

#     def __str__(self):
#         return f"[A] {self.name}"

#     def _get_leaf_state(self) -> NodeState:
#         return NodeState.COMPLETED


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
