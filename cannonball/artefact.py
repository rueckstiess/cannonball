from .node import Node


class Artefact(Node):
    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        if self._completed:
            return "A"
        return "a"
