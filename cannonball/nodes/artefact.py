from .node import Node


class Artefact(Node):
    @property
    def marker(self) -> str:
        """Get the marker for the node."""
        return "A" if self._completed else "a"
