from typing import Optional
from .node import Node


class Task(Node):
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
        super().__init__(name, id, parent, children, completed=completed, blocked=blocked, **kwargs)

        self._auto_resolve: bool = auto_resolve

    @property
    def auto_resolve(self) -> bool:
        return self._auto_resolve

    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        if self._blocked:
            return "!"
        if self._completed:
            return "x"
        return " "

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
