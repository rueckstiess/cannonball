from .node import Node


class Experiment(Node):
    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        if self._blocked:
            return "%"
        if self._completed:
            return "E"
        return "e"
