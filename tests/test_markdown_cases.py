from cannonball.nodes import Task, TaskType, Question, Alternative, Goal
from cannonball.utils import extract_str_content
from cannonball.graph_mgr import GraphMgr
import pytest


class TestBasicMarkdownParsing:
    @pytest.fixture
    def graph_fixture(self):
        """Fixture that creates a graph from markdown for testing."""
        input_md = """\
- [x] Task 1
  - [ ] Task 2
    - [x] Task 3
"""
        mgr = GraphMgr.from_markdown(input_md)
        graph = mgr.nxgraph
        nodes = list(graph)
        nodes_by_name = {extract_str_content(node.name): node for node in nodes}

        return {"graph": graph, "nodes": nodes, "nodes_by_name": nodes_by_name}

    @pytest.mark.parametrize(
        "node_name,expected_status,description",
        [
            ("Task 1", TaskType.COMPLETED, "Task 1 should be completed"),
            ("Task 2", TaskType.OPEN, "Task 2 should be open"),
        ],
    )
    def test_task_status(self, graph_fixture, node_name, expected_status, description):
        """Test task status parsing."""
        node = graph_fixture["nodes_by_name"][node_name]
        assert node.status == expected_status, description

    @pytest.mark.parametrize(
        "node_name,expected_type,description",
        [
            ("Task 1", Task, "Task 1 should be a Task node"),
            ("Task 2", Task, "Task 2 should be a Task node"),
        ],
    )
    def test_node_types(self, graph_fixture, node_name, expected_type, description):
        """Test node type parsing."""
        node = graph_fixture["nodes_by_name"][node_name]
        assert isinstance(node, expected_type), description

    @pytest.mark.parametrize(
        "node_name,expected_blocked,description",
        [
            ("Task 1", True, "Task 1 should be blocked"),
            ("Task 2", True, "Task 2 should be blocked"),
            ("Task 3", False, "Task 3 should not be blocked"),
        ],
    )
    def test_blocking_status(self, graph_fixture, node_name, expected_blocked, description):
        """Test node blocking status."""
        node = graph_fixture["nodes_by_name"][node_name]
        graph = graph_fixture["graph"]
        assert node.is_blocked(graph) == expected_blocked, description


class TestAlternativeContainers:
    @pytest.fixture
    def graph_fixture(self):
        """Fixture that creates a graph from markdown for testing."""
        input_md = """\
- [?] Question
    - [a] Alternative 1
    - [a] Alternative 2 
"""
        mgr = GraphMgr.from_markdown(input_md)
        graph = mgr.nxgraph
        nodes = list(graph)
        nodes_by_name = {extract_str_content(node.name): node for node in nodes}

        return {"graph": graph, "nodes": nodes, "nodes_by_name": nodes_by_name}

    @pytest.mark.parametrize(
        "node_name,expected_type,description",
        [
            ("Question", Question, "should be a Question"),
            ("Alternative 1", Alternative, "should be an Alternative"),
            ("Alternative 2", Alternative, "should be an Alternative"),
        ],
    )
    def test_node_types(self, graph_fixture, node_name, expected_type, description):
        """Test task status parsing."""
        node = graph_fixture["nodes_by_name"][node_name]
        assert isinstance(node, expected_type), description
