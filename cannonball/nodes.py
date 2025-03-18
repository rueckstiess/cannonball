from dataclasses import dataclass
from typing import Optional


@dataclass
class Node:
    """A node in the graph."""

    id: str
    name: str
    marker: str
    ref: Optional[str] = None
