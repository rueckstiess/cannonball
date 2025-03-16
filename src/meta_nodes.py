from typing import Optional, List, Dict, Any, Set, Union
from datetime import datetime

from base_classes import Element
from node_categories import MetaNode


class MetaComment(MetaNode):
    """Represents a meta-comment about the system itself.

    Meta-comments provide reflections, observations, or suggestions about
    the system rather than about the work being done.
    """

    def __init__(
        self,
        text: str,
        parent: Optional[Element] = None,
        id: Optional[str] = None,
        ref_marker: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a new MetaComment.

        Args:
            text: The meta-comment text
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "meta", parent, id, ref_marker, metadata)


class Example(MetaNode):
    """Represents an example or template.

    Examples create a boundary between actual workflow components and
    illustrative or template content.
    """

    def __init__(
        self,
        text: str,
        parent: Optional[Element] = None,
        id: Optional[str] = None,
        ref_marker: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a new Example.

        Args:
            text: The example text
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "example", parent, id, ref_marker, metadata)

    def to_graph_node(self) -> Dict[str, Any]:
        """Convert to a format suitable for NetworkX.

        Examples are excluded from the graph as they don't have semantic meaning.

        Returns:
            None: Examples are not included in the graph
        """
        return None


class LocationMarker(MetaNode):
    """Represents a location marker for navigation.

    Location markers serve as navigation aids within the graph,
    helping users efficiently navigate and work with the system.
    """

    def __init__(
        self,
        text: str,
        parent: Optional[Element] = None,
        id: Optional[str] = None,
        ref_marker: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a new LocationMarker.

        Args:
            text: The location marker text
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "location", parent, id, ref_marker, metadata)
