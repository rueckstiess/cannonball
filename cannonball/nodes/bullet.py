from typing import Optional, Tuple
from .node import Node


class Bullet(Node):
    """Bullet nodes behave like StatefulNodes internally but don't show their state in the UI and their state
    cannot be manually changed. They are for grouping tasks together and regular thoughts. They still
    propagate their chilren states to the parent."""

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        parent: Optional[Node] = None,
        children: Optional[list[Node]] = None,
        **kwargs,
    ):
        super().__init__(name, id, parent, children, marker=None, **kwargs)
        self._recompute_state()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def _leaf_state(self) -> Tuple[bool, bool]:
        """Leaf Bullets are always completed and not blocked."""
        return (True, False)
