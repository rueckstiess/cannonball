from typing import Optional
from .node import Node


class Decision(Node):
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

        super().__init__(name, id, parent, children, **kwargs)
        self._recompute_state()

    @property
    def decision(self) -> Optional[Node]:
        """Get the decision node."""
        return self._decision

    @property
    def is_decided(self) -> bool:
        """Check if the decision has been made."""
        return self._decision is not None

    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        if self._blocked:
            return "$"
        if self._completed:
            return "D"
        return "d"

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
