from anytree import NodeMixin, find
from typing import Optional, Tuple, Union
from textwrap import dedent
from marko import Markdown
from marko.block import ListItem, Paragraph
from marko.inline import RawText
import uuid

from cannonball.utils import (
    extract_node_marker_and_refs,
    extract_str_content,
    get_raw_text_from_listtem,
    walk_list_items,
)


class Node(NodeMixin):
    """Stateful node with state propagation and resolution logic."""

    _node_registry = {}

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional["Node"] = None,
        children: Optional[list["Node"]] = None,
        completed: bool = False,
        blocked: bool = False,
        marker: Optional[str] = None,
        list_item: Optional[ListItem] = None,
        **kwargs,
    ):
        if blocked and completed:
            raise ValueError("A node cannot be both blocked and completed.")

        self._blocked = blocked
        self._completed = completed
        self._marker = marker
        self.name = name
        self.id = id
        self.parent = parent
        if list_item:
            assert isinstance(list_item, ListItem), "Expected a ListItem"
            self.list_item = list_item
        if children:
            self.children = children

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def is_blocked(self) -> bool:
        return self._blocked

    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        return self._marker

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, completed={self._completed}, blocked={self._blocked})"

    def __str__(self):
        if self.marker:
            return f"[{self.marker}] {self.name}"
        return f"{self.name}"

    @classmethod
    def register(cls, marker: Optional[str], node_class, completed: bool = False, blocked: bool = False):
        """Register a node type with the registry.

        Args:
            marker: The marker string that identifies this node type in markdown
            node_class: The class to instantiate for this marker
            completed: Default completed state for this node type
            blocked: Default blocked state for this node type
        """
        cls._node_registry[marker] = (node_class, completed, blocked)

    def _update_list_items(self):
        """Update the list item with the current node's attributes, ignoring its children"""

        # find the RawText node in the list item (inside Paragraph)
        # and update its text with the current node's attributes
        if self.list_item:
            try:
                paragraph = next(el for el in self.list_item.children if isinstance(el, Paragraph))
                raw_text = next(el for el in paragraph.children if isinstance(el, RawText))
                raw_text.children = str(self)
            except StopIteration:
                # If no paragraph or raw text found, do nothing
                pass
        # Recursively update list items for all children
        for child in self.children:
            child._update_list_items()

    def to_markdown(self, indent: int | str = 4) -> str:
        """Convert the node and its children to a markdown string.

        Args:
            indent: Number of spaces for each indentation level, or a string to use for indentation.

        Returns:
            str: Markdown representation of the node and its descendants.
        """
        # Determine the indentation string
        if isinstance(indent, int):
            indent_str = " " * indent
        else:
            indent_str = indent

        # Start with an empty list to store markdown lines
        result = []

        # Use depth-first traversal to build the markdown representation
        def _build_markdown(node, level=0):
            # Add the current node
            current_indent = indent_str * level
            result.append(f"{current_indent}- {str(node)}")

            # Add all children recursively
            for child in node.children:
                _build_markdown(child, level + 1)

        # Start the recursive generation from this node
        _build_markdown(self)

        # Join all lines into a single string
        return "\n".join(result)

    @classmethod
    def from_markdown(cls, content: str, **kwargs) -> Union["Node", list["Node"]]:
        """Create a node tree from a markdown string."""

        parser = Markdown()
        ast = parser.parse(dedent(content.strip("\n")))

        item_to_node = {}

        for li, parent_li, _ in walk_list_items(ast):
            if li in item_to_node:
                node = item_to_node[li]
            else:
                node = cls.from_list_item(li, **kwargs)
                item_to_node[li] = node

            # this must already exist since we're parsing a tree
            parent = item_to_node[parent_li] if parent_li else None

            if parent:
                node.parent = parent

        roots = [node for node in item_to_node.values() if node.is_root]

        # return None if no roots found, a single root node if only one root, or a list of roots
        if len(roots) == 0:
            return None
        if len(roots) == 1:
            return roots[0]
        return roots

    @classmethod
    def from_list_item(cls, list_item: ListItem, **kwargs) -> "Node":
        """Create a node from a ListItem."""
        if list_item is None:
            return None

        text = get_raw_text_from_listtem(list_item)
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        content = extract_str_content(text)
        node_id = str(uuid.uuid4())[:8]

        # Get class and state from registry with fallback to Node
        node_class, completed, blocked = cls._node_registry.get(marker, (Node, False, False))
        node = node_class(content, node_id, completed=completed, blocked=blocked, list_item=list_item, **kwargs)
        return node

    @classmethod
    def from_contents(
        cls, node_id: str, content: str, marker: Optional[str] = None, list_item: Optional[ListItem] = None, **kwargs
    ) -> "Node":
        """Create a node from contents."""

        # Get class and state from registry with fallback to Node
        node_class, completed, blocked = cls._node_registry.get(marker, (Node, False, False))
        node = node_class(content, node_id, completed=completed, blocked=blocked, list_item=list_item, **kwargs)
        return node

    def find_by_name(self, prefix: str) -> Optional["Node"]:
        """Find a child node by its name or prefix of a name."""
        return find(self, lambda node: node.name.startswith(prefix))

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
            is_blocked = any(isinstance(child, Node) and child.is_blocked for child in children)

            # a node is completed if it is not blocked and all its children are completed
            is_completed = (
                False if is_blocked else all(isinstance(child, Node) and child.is_completed for child in children)
            )

        # if any state changed, update the state and optionally notify the parent
        if self._completed != is_completed or self._blocked != is_blocked:
            self._completed = is_completed
            self._blocked = is_blocked

            # Notify parent if needed
            if notify:
                self._notify_parent()

    def _post_detach(self, parent: "Node"):
        """Notify parent of detachment"""
        parent._recompute_state()

    def _post_attach(self, parent: "Node"):
        """Recompute state after attaching to parent."""
        parent._recompute_state()

    def _post_attach_children(self, children: list["Node"]):
        """Recompute state after attaching children."""
        self._recompute_state()

    def _post_detach_children(self, children: list["Node"]):
        """Recompute state after detaching children."""
        self._recompute_state()
