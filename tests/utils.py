from cannonball.graph_mgr import GraphMgr
from cannonball.utils import extract_str_content
import textwrap
import pytest


def create_graph_fixture(markdown):
    """Helper function to create standardized graph fixtures."""
    mgr = GraphMgr.from_markdown(markdown)
    graph = mgr.nxgraph
    nodes = list(graph)

    class NodesByName(dict):
        """Custom dictionary to allow node retrieval by name or prefix."""

        def __getitem__(self, name):
            """Get a node by its name or prefix."""
            if name in self:
                return super().__getitem__(name)
            if name.endswith("..."):
                name = name[:-3]
            for name, item in self.items():
                if name.startswith(name):
                    return item
            raise KeyError(f"Node with name '{name}' not found.")

    nodes_by_name = NodesByName(
        {extract_str_content(node.name): node for node in nodes}
    )

    return {"graph": graph, "nodes": nodes, "nodes_by_name": nodes_by_name}


def shorten_text(text, length=20):
    """Shorten text to a specified length, adding ellipsis if needed."""
    if len(text) > length:
        return text[:length] + "..."
    return text


# Define reusable test functions
def check_node_type(fixture, node_name, expected_type, reason):
    """Generic function to check node types."""
    node = fixture["nodes_by_name"][node_name]
    assertion = f"Node '{shorten_text(node_name)}' is type {type(node)} but should be type {expected_type} because {reason}"
    assert isinstance(node, expected_type), assertion


def check_task_status(fixture, node_name, expected_status, reason):
    """Generic function to check task status."""
    node = fixture["nodes_by_name"][node_name]
    assertion = f"Status for '{shorten_text(node_name)}' is {node.status} but should be {expected_status} because {reason}"
    assert node.status == expected_status, assertion


def check_blocking_status(fixture, node_name, expected_blocked, reason):
    """Generic function to check if a node is blocked."""
    node = fixture["nodes_by_name"][node_name]
    graph = fixture["graph"]
    is_blocked = node.is_blocked(graph)
    assertion = (
        f"Node '{shorten_text(node_name)}' is {'blocked' if is_blocked else 'unblocked'} "
        f"but should be {'blocked' if expected_blocked else 'unblocked'} because {reason}"
    )
    assert is_blocked == expected_blocked, assertion


def with_markdown(markdown):
    """Decorator to add a markdown fixture to a test class."""

    def decorator(cls):
        @pytest.fixture(scope="class")
        def graph_fixture(self):
            return create_graph_fixture(textwrap.dedent(markdown))

        cls.graph_fixture = graph_fixture
        return cls

    return decorator
