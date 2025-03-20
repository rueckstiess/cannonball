import unittest
import networkx as nx
from cannonball.nodes import Goal, BlockingNode
from cannonball.utils import EdgeType


class BlockingNodeForTesting(BlockingNode):
    """A simple BlockingNode implementation for testing that can be configured to block or not."""

    def __init__(self, id, name, blocks=False, **kwargs):
        super().__init__(id=id, name=name, **kwargs)
        self._blocks = blocks

    def is_blocked(self, graph):
        return self._blocks


class TestGoal(unittest.TestCase):
    def test_goal_initialization(self):
        """Test that a Goal is initialized with the correct default values."""
        goal = Goal(id="g1", name="Goal 1")
        self.assertEqual(goal.id, "g1")
        self.assertEqual(goal.name, "Goal 1")
        self.assertIsNone(goal.marker)
        self.assertIsNone(goal.ref)
        self.assertFalse(goal.is_achieved)

    def test_goal_custom_initialization(self):
        """Test that a Goal can be initialized with custom values."""
        goal = Goal(id="g2", name="Goal 2", marker="*", ref="REF123", is_achieved=True)
        self.assertEqual(goal.id, "g2")
        self.assertEqual(goal.name, "Goal 2")
        self.assertEqual(goal.marker, "*")
        self.assertEqual(goal.ref, "REF123")
        self.assertTrue(goal.is_achieved)

    def test_is_blocked_when_not_achieved(self):
        """Test that an unachieved goal is blocked."""
        graph = nx.DiGraph()
        goal = Goal(id="g", name="Goal", is_achieved=False)
        graph.add_node(goal)

        self.assertTrue(goal.is_blocked(graph))

    def test_is_blocked_when_achieved(self):
        """Test that an achieved goal is not blocked."""
        graph = nx.DiGraph()
        goal = Goal(id="g", name="Goal", is_achieved=True)
        graph.add_node(goal)

        self.assertFalse(goal.is_blocked(graph))

    def test_goal_with_blocked_children(self):
        """Test that a goal is blocked if any of its children are blocked."""
        graph = nx.DiGraph()

        parent_goal = Goal(id="parent", name="Parent Goal", is_achieved=True)
        child_node_blocked = BlockingNodeForTesting(
            id="child1", name="Child Node 1", blocks=True
        )
        child_node_unblocked = BlockingNodeForTesting(
            id="child2", name="Child Node 2", blocks=False
        )

        graph.add_nodes_from([parent_goal, child_node_blocked, child_node_unblocked])
        graph.add_edge(parent_goal, child_node_blocked, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_goal, child_node_unblocked, type=EdgeType.REQUIRES.value)

        # Even though parent_goal is achieved, it should be blocked because child_node_blocked is blocked
        self.assertTrue(parent_goal.is_blocked(graph))

    def test_goal_with_unblocked_children(self):
        """Test that a goal is not blocked if all its children are unblocked."""
        graph = nx.DiGraph()

        parent_goal = Goal(id="parent", name="Parent Goal", is_achieved=True)
        child_node1 = BlockingNodeForTesting(
            id="child1", name="Child Node 1", blocks=False
        )
        child_node2 = BlockingNodeForTesting(
            id="child2", name="Child Node 2", blocks=False
        )

        graph.add_nodes_from([parent_goal, child_node1, child_node2])
        graph.add_edge(parent_goal, child_node1, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_goal, child_node2, type=EdgeType.REQUIRES.value)

        # parent_goal is achieved and both children are unblocked
        self.assertFalse(parent_goal.is_blocked(graph))

    def test_goal_blocking_with_deep_nesting(self):
        """Test blocking status propagation with multiple nesting levels."""
        graph = nx.DiGraph()

        root_goal = Goal(id="root", name="Root Goal", is_achieved=True)
        level1_goal = Goal(id="level1", name="Level 1 Goal", is_achieved=True)
        level2_goal = Goal(id="level2", name="Level 2 Goal", is_achieved=True)
        level3_goal_blocked = Goal(id="level3", name="Level 3 Goal", is_achieved=False)

        graph.add_nodes_from([root_goal, level1_goal, level2_goal, level3_goal_blocked])
        graph.add_edge(root_goal, level1_goal, type=EdgeType.REQUIRES.value)
        graph.add_edge(level1_goal, level2_goal, type=EdgeType.REQUIRES.value)
        graph.add_edge(level2_goal, level3_goal_blocked, type=EdgeType.REQUIRES.value)

        # The blocking status should propagate up through all levels
        self.assertTrue(level2_goal.is_blocked(graph))
        self.assertTrue(level1_goal.is_blocked(graph))
        self.assertTrue(root_goal.is_blocked(graph))

    def test_goal_blocking_with_reference_edge_type(self):
        """Test that blocking doesn't propagate through REFERENCES edge type."""
        graph = nx.DiGraph()

        parent_goal = Goal(id="parent", name="Parent Goal", is_achieved=True)
        child_goal_blocked = Goal(id="child", name="Child Goal", is_achieved=False)

        graph.add_nodes_from([parent_goal, child_goal_blocked])
        graph.add_edge(parent_goal, child_goal_blocked, type=EdgeType.REFERENCES.value)

        # parent_goal is achieved and the child is only referenced (not required),
        # so parent_goal should not be blocked
        self.assertFalse(parent_goal.is_blocked(graph))

    def test_goal_blocking_with_mixed_edge_types(self):
        """Test blocking behavior with mixed edge types."""
        graph = nx.DiGraph()

        parent_goal = Goal(id="parent", name="Parent Goal", is_achieved=True)
        required_child = Goal(id="required", name="Required Child", is_achieved=False)
        referenced_child = Goal(
            id="referenced", name="Referenced Child", is_achieved=False
        )

        graph.add_nodes_from([parent_goal, required_child, referenced_child])
        graph.add_edge(parent_goal, required_child, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_goal, referenced_child, type=EdgeType.REFERENCES.value)

        # parent_goal should be blocked because required_child is blocked
        self.assertTrue(parent_goal.is_blocked(graph))

    def test_changing_achieved_status_affects_blocking(self):
        """Test that changing the achieved status affects blocking status."""
        graph = nx.DiGraph()

        goal = Goal(id="g", name="Goal", is_achieved=False)
        graph.add_node(goal)

        self.assertTrue(goal.is_blocked(graph))

        # Change achieved status
        goal.is_achieved = True
        self.assertFalse(goal.is_blocked(graph))

        # Change back
        goal.is_achieved = False
        self.assertTrue(goal.is_blocked(graph))

    def test_achieved_goal_blocked_by_child(self):
        """Test that an achieved goal is still blocked if its children are blocked."""
        graph = nx.DiGraph()

        parent_goal = Goal(id="parent", name="Parent Goal", is_achieved=True)
        child_goal = Goal(id="child", name="Child Goal", is_achieved=False)

        graph.add_nodes_from([parent_goal, child_goal])
        graph.add_edge(parent_goal, child_goal, type=EdgeType.REQUIRES.value)

        # Even though parent_goal is achieved, it should be blocked because child_goal is blocked
        self.assertTrue(parent_goal.is_blocked(graph))

    def test_goal_with_mixed_child_types(self):
        """Test goal with different types of child nodes."""
        graph = nx.DiGraph()

        parent_goal = Goal(id="parent", name="Parent Goal", is_achieved=True)
        blocking_node = BlockingNodeForTesting(
            id="blocker", name="Blocker", blocks=True
        )
        non_blocking_node = BlockingNodeForTesting(
            id="non_blocker", name="Non-Blocker", blocks=False
        )

        graph.add_nodes_from([parent_goal, blocking_node, non_blocking_node])
        graph.add_edge(parent_goal, blocking_node, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_goal, non_blocking_node, type=EdgeType.REQUIRES.value)

        # parent_goal should be blocked because one of its children (blocking_node) is blocked
        self.assertTrue(parent_goal.is_blocked(graph))

    def test_empty_graph_for_goal(self):
        """Test that a goal in an empty graph is blocked only by its achievement status."""
        empty_graph = nx.DiGraph()  # Graph with no edges

        achieved_goal = Goal(id="achieved", name="Achieved Goal", is_achieved=True)
        unachieved_goal = Goal(
            id="unachieved", name="Unachieved Goal", is_achieved=False
        )

        empty_graph.add_nodes_from([achieved_goal, unachieved_goal])

        self.assertFalse(achieved_goal.is_blocked(empty_graph))
        self.assertTrue(unachieved_goal.is_blocked(empty_graph))


if __name__ == "__main__":
    unittest.main()
