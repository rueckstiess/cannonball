import unittest
import networkx as nx
from cannonball.nodes import Node, BlockingNode, Question, Problem, Goal
from cannonball.utils import EdgeType

# Import the classes to test using relative import


class TestBlockingNode(unittest.TestCase):
    """Tests for the BlockingNode class."""

    def setUp(self):
        """Set up common test fixtures."""
        self.graph = nx.DiGraph()

    def create_simple_graph(self):
        """Create a simple graph with parent and child nodes."""
        # Create a blocking parent node
        parent = BlockingNode(id="parent", name="Parent Node")

        # Create a child node that is blocking
        blocking_child = BlockingNode(id="blocking_child", name="Blocking Child")
        blocking_child.is_blocked = lambda g: True  # Override is_blocked to always return True

        # Create a child node that is not blocking
        non_blocking_child = BlockingNode(id="non_blocking_child", name="Non-Blocking Child")
        non_blocking_child.is_blocked = lambda g: False  # Override is_blocked to always return False

        # Add nodes to the graph
        for node in [parent, blocking_child, non_blocking_child]:
            self.graph.add_node(node, **node.__dict__)

        # Connect parent to children with REQUIRES edge type
        self.graph.add_edge(parent, blocking_child, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(parent, non_blocking_child, type=EdgeType.REQUIRES.value)

        return parent, blocking_child, non_blocking_child

    def create_nested_graph(self):
        """Create a nested graph with multiple levels of nodes."""
        # Create a root node
        root = BlockingNode(id="root", name="Root Node")

        # Create level 1 nodes
        level1_a = BlockingNode(id="level1_a", name="Level 1A")
        level1_b = BlockingNode(id="level1_b", name="Level 1B")

        # Create level 2 nodes under level1_a
        level2_a1 = BlockingNode(id="level2_a1", name="Level 2A1")
        level2_a1.is_blocked = lambda g: True  # This node is always blocked
        level2_a2 = BlockingNode(id="level2_a2", name="Level 2A2")

        # Create level 2 nodes under level1_b
        level2_b1 = BlockingNode(id="level2_b1", name="Level 2B1")

        # Create level 3 node under level2_b1
        level3_b1 = BlockingNode(id="level3_b1", name="Level 3B1")
        level3_b1.is_blocked = lambda g: True  # This node is always blocked

        # Add all nodes to the graph
        nodes = [root, level1_a, level1_b, level2_a1, level2_a2, level2_b1, level3_b1]
        for node in nodes:
            self.graph.add_node(node, **node.__dict__)

        # Connect nodes with REQUIRES edges
        self.graph.add_edge(root, level1_a, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(root, level1_b, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(level1_a, level2_a1, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(level1_a, level2_a2, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(level1_b, level2_b1, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(level2_b1, level3_b1, type=EdgeType.REQUIRES.value)

        return {
            "root": root,
            "level1_a": level1_a,
            "level1_b": level1_b,
            "level2_a1": level2_a1,
            "level2_a2": level2_a2,
            "level2_b1": level2_b1,
            "level3_b1": level3_b1,
        }

    def create_mixed_edge_types_graph(self):
        """Create a graph with both REQUIRES and REFERENCES edge types."""
        # Create nodes
        root = BlockingNode(id="root", name="Root Node")

        # Nodes connected with REQUIRES edges
        req_child1 = BlockingNode(id="req_child1", name="Required Child 1")
        req_child1.is_blocked = lambda g: True  # This node is blocking
        req_child2 = BlockingNode(id="req_child2", name="Required Child 2")

        # Nodes connected with REFERENCES edges
        ref_child1 = BlockingNode(id="ref_child1", name="Reference Child 1")
        ref_child1.is_blocked = lambda g: True  # This is blocking but shouldn't affect parent

        ref_child2 = BlockingNode(id="ref_child2", name="Reference Child 2")

        # Add nodes to the graph
        nodes = [root, req_child1, req_child2, ref_child1, ref_child2]
        for node in nodes:
            self.graph.add_node(node, **node.__dict__)

        # Connect with different edge types
        self.graph.add_edge(root, req_child1, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(root, req_child2, type=EdgeType.REQUIRES.value)
        self.graph.add_edge(root, ref_child1, type=EdgeType.REFERENCES.value)
        self.graph.add_edge(root, ref_child2, type=EdgeType.REFERENCES.value)

        return {
            "root": root,
            "req_child1": req_child1,
            "req_child2": req_child2,
            "ref_child1": ref_child1,
            "ref_child2": ref_child2,
        }

    def test_default_is_blocked(self):
        """Test the default implementation of is_blocked."""
        node = BlockingNode(id="test", name="Test Node")
        self.assertFalse(
            node.is_blocked(self.graph),
            "BlockingNode.is_blocked should return False by default",
        )

    def test_is_blocked_simple(self):
        """Test is_blocked with a simple hierarchy."""
        parent, blocking_child, non_blocking_child = self.create_simple_graph()

        # Parent should be blocked since one of its children is blocking
        self.assertTrue(
            parent.is_blocked(self.graph),
            "Parent should be blocked when it has a blocking child",
        )

    def test_is_blocked_no_blocking_children(self):
        """Test is_blocked when there are no blocking children."""
        parent, blocking_child, non_blocking_child = self.create_simple_graph()

        # Modify blocking_child to be non-blocking
        blocking_child.is_blocked = lambda g: False

        # Now parent should not be blocked
        self.assertFalse(
            parent.is_blocked(self.graph),
            "Parent should not be blocked when it has no blocking children",
        )

    def test_is_blocked_nested(self):
        """Test is_blocked with a nested graph structure."""
        nodes = self.create_nested_graph()

        # level1_a should be blocked because level2_a1 is blocking
        self.assertTrue(
            nodes["level1_a"].is_blocked(self.graph),
            "level1_a should be blocked by level2_a1",
        )

        # level1_b should be blocked because level3_b1 is blocking (transitive)
        self.assertTrue(
            nodes["level1_b"].is_blocked(self.graph),
            "level1_b should be blocked by level3_b1 (transitive)",
        )

        # Root should be blocked because both child paths have blocking nodes
        self.assertTrue(
            nodes["root"].is_blocked(self.graph),
            "Root should be blocked when all paths have blocking nodes",
        )

    def test_is_blocked_mixed_blocking_states(self):
        """Test is_blocked with mixed blocking states in descendants."""
        nodes = self.create_nested_graph()

        # Make level2_a1 non-blocking
        nodes["level2_a1"].is_blocked = lambda g: False

        # level1_a should now be unblocked
        self.assertFalse(
            nodes["level1_a"].is_blocked(self.graph),
            "level1_a should not be blocked when all children are non-blocking",
        )

        # Root should still be blocked because level3_b1 is still blocking
        self.assertTrue(
            nodes["root"].is_blocked(self.graph),
            "Root should still be blocked because level3_b1 is blocking",
        )

        # Now make level3_b1 non-blocking
        nodes["level3_b1"].is_blocked = lambda g: False

        # Root should now be unblocked
        self.assertFalse(
            nodes["root"].is_blocked(self.graph),
            "Root should be unblocked when all descendants are non-blocking",
        )

    def test_is_blocked_with_reference_edges(self):
        """Test is_blocked with a mix of REQUIRES and REFERENCES edge types."""
        nodes = self.create_mixed_edge_types_graph()

        # Root should be blocked because req_child1 is blocking
        self.assertTrue(
            nodes["root"].is_blocked(self.graph),
            "Root should be blocked by required children",
        )

        # Make req_child1 non-blocking
        nodes["req_child1"].is_blocked = lambda g: False

        # Root should now be unblocked, even though ref_child1 is blocking
        self.assertFalse(
            nodes["root"].is_blocked(self.graph),
            "Root should not be blocked by reference edges, only by required edges",
        )

    def test_is_blocked_with_no_children(self):
        """Test is_blocked for a node with no children."""
        node = BlockingNode(id="lonely", name="Lonely Node")
        self.graph.add_node(node, **node.__dict__)

        # A node with no children should not be blocked
        self.assertFalse(node.is_blocked(self.graph), "Node with no children should not be blocked")

    def test_is_blocked_with_empty_graph(self):
        """Test is_blocked with an empty graph."""
        empty_graph = nx.DiGraph()
        node = BlockingNode(id="test", name="Test Node")

        # A node in an empty graph should not be blocked
        self.assertFalse(node.is_blocked(empty_graph), "Node in empty graph should not be blocked")

    def test_cyclic_graph(self):
        """Test is_blocked with a cyclic graph."""
        # Create nodes
        node_a = BlockingNode(id="A", name="Node A")
        node_b = BlockingNode(id="B", name="Node B")
        node_b.is_blocked = lambda g: True  # Node B is blocking

        # Add nodes to the graph
        graph = nx.DiGraph()
        graph.add_node(node_a, **node_a.__dict__)
        graph.add_node(node_b, **node_b.__dict__)

        # Create a cycle: A -> B -> A
        graph.add_edge(node_a, node_b, type=EdgeType.REQUIRES.value)
        graph.add_edge(node_b, node_a, type=EdgeType.REQUIRES.value)

        # Node A should be blocked because Node B is blocking
        # This also tests that is_blocked doesn't get stuck in an infinite loop
        self.assertTrue(
            node_a.is_blocked(graph),
            "Node A should be blocked by Node B in a cyclic graph",
        )

    def test_concrete_blocking_node_implementations(self):
        """Test concrete implementations of BlockingNode."""
        # Set up a graph
        graph = nx.DiGraph()

        # Test QuestionNode
        question_resolved = Question(id="q1", name="Resolved Question", is_resolved=True)
        question_unresolved = Question(id="q2", name="Unresolved Question", is_resolved=False)

        self.assertFalse(question_resolved.is_blocked(graph), "Resolved question should not block")
        self.assertTrue(question_unresolved.is_blocked(graph), "Unresolved question should block")

        # Test ProblemNode
        problem = Problem(id="p1", name="Problem")
        self.assertTrue(problem.is_blocked(graph), "Problem should always block")

        # Test GoalNode
        goal_achieved = Goal(id="g1", name="Achieved Goal", is_achieved=True)
        goal_unachieved = Goal(id="g2", name="Unachieved Goal", is_achieved=False)

        self.assertFalse(goal_achieved.is_blocked(graph), "Achieved goal should not block")
        self.assertTrue(goal_unachieved.is_blocked(graph), "Unachieved goal should block")

    def test_propagation_multiple_levels(self):
        """Test blocking propagation through multiple levels of nodes."""
        # Create a deeper graph structure
        deep_graph = nx.DiGraph()

        # Create a chain of nodes: root -> A -> B -> C -> D
        # Where D is blocking
        nodes = {
            "root": BlockingNode(id="root", name="Root"),
            "A": BlockingNode(id="A", name="Level A"),
            "B": BlockingNode(id="B", name="Level B"),
            "C": BlockingNode(id="C", name="Level C"),
            "D": BlockingNode(id="D", name="Level D"),
        }

        # Make node D blocking
        nodes["D"].is_blocked = lambda g: True

        # Add nodes to graph
        for node in nodes.values():
            deep_graph.add_node(node, **node.__dict__)

        # Connect nodes with REQUIRES edges
        deep_graph.add_edge(nodes["root"], nodes["A"], type=EdgeType.REQUIRES.value)
        deep_graph.add_edge(nodes["A"], nodes["B"], type=EdgeType.REQUIRES.value)
        deep_graph.add_edge(nodes["B"], nodes["C"], type=EdgeType.REQUIRES.value)
        deep_graph.add_edge(nodes["C"], nodes["D"], type=EdgeType.REQUIRES.value)

        # Blocking should propagate all the way up to root
        self.assertTrue(
            nodes["root"].is_blocked(deep_graph),
            "Root should be blocked by node D (4 levels deep)",
        )
        self.assertTrue(
            nodes["A"].is_blocked(deep_graph),
            "Node A should be blocked by node D (3 levels deep)",
        )
        self.assertTrue(
            nodes["B"].is_blocked(deep_graph),
            "Node B should be blocked by node D (2 levels deep)",
        )
        self.assertTrue(
            nodes["C"].is_blocked(deep_graph),
            "Node C should be blocked by node D (1 level deep)",
        )

        # Node D itself should be blocked (per definition)
        self.assertTrue(
            nodes["D"].is_blocked(deep_graph),
            "Node D should not be blocked as it has no children",
        )


if __name__ == "__main__":
    unittest.main()
