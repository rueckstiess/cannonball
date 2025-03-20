import unittest
import networkx as nx
from cannonball.nodes import Question, BlockingNode
from cannonball.utils import EdgeType


class BlockingNodeForTesting(BlockingNode):
    """A simple BlockingNode implementation for testing that can be configured to block or not."""

    def __init__(self, id, name, blocks=False, **kwargs):
        super().__init__(id=id, name=name, **kwargs)
        self._blocks = blocks

    def is_blocked(self, graph):
        return self._blocks


class TestQuestion(unittest.TestCase):
    def test_question_initialization(self):
        """Test that a Question is initialized with the correct default values."""
        question = Question(id="q1", name="Question 1")
        self.assertEqual(question.id, "q1")
        self.assertEqual(question.name, "Question 1")
        self.assertIsNone(question.marker)
        self.assertIsNone(question.ref)
        self.assertFalse(question.is_resolved)

    def test_question_custom_initialization(self):
        """Test that a Question can be initialized with custom values."""
        question = Question(id="q2", name="Question 2", marker="?", ref="REF123", is_resolved=True)
        self.assertEqual(question.id, "q2")
        self.assertEqual(question.name, "Question 2")
        self.assertEqual(question.marker, "?")
        self.assertEqual(question.ref, "REF123")
        self.assertTrue(question.is_resolved)

    def test_is_blocked_when_unresolved(self):
        """Test that an unresolved question is blocked."""
        graph = nx.DiGraph()
        question = Question(id="q", name="Question", is_resolved=False)
        graph.add_node(question)

        self.assertTrue(question.is_blocked(graph))

    def test_is_blocked_when_resolved(self):
        """Test that a resolved question is not blocked."""
        graph = nx.DiGraph()
        question = Question(id="q", name="Question", is_resolved=True)
        graph.add_node(question)

        self.assertFalse(question.is_blocked(graph))

    def test_question_with_blocked_children(self):
        """Test that a question is blocked if any of its children are blocked."""
        graph = nx.DiGraph()

        parent_question = Question(id="parent", name="Parent Question", is_resolved=True)
        child_node_blocked = BlockingNodeForTesting(id="child1", name="Child Node 1", blocks=True)
        child_node_unblocked = BlockingNodeForTesting(id="child2", name="Child Node 2", blocks=False)

        graph.add_nodes_from([parent_question, child_node_blocked, child_node_unblocked])
        graph.add_edge(parent_question, child_node_blocked, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_question, child_node_unblocked, type=EdgeType.REQUIRES.value)

        # Even though parent_question is resolved, it should be blocked because child_node_blocked is blocked
        self.assertTrue(parent_question.is_blocked(graph))

    def test_question_with_unblocked_children(self):
        """Test that a question is not blocked if all its children are unblocked."""
        graph = nx.DiGraph()

        parent_question = Question(id="parent", name="Parent Question", is_resolved=True)
        child_node1 = BlockingNodeForTesting(id="child1", name="Child Node 1", blocks=False)
        child_node2 = BlockingNodeForTesting(id="child2", name="Child Node 2", blocks=False)

        graph.add_nodes_from([parent_question, child_node1, child_node2])
        graph.add_edge(parent_question, child_node1, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_question, child_node2, type=EdgeType.REQUIRES.value)

        # parent_question is resolved and both children are unblocked
        self.assertFalse(parent_question.is_blocked(graph))

    def test_question_blocking_with_deep_nesting(self):
        """Test blocking status propagation with multiple nesting levels."""
        graph = nx.DiGraph()

        root_question = Question(id="root", name="Root Question", is_resolved=True)
        level1_question = Question(id="level1", name="Level 1 Question", is_resolved=True)
        level2_question = Question(id="level2", name="Level 2 Question", is_resolved=True)
        level3_question_blocked = Question(id="level3", name="Level 3 Question", is_resolved=False)

        graph.add_nodes_from([root_question, level1_question, level2_question, level3_question_blocked])
        graph.add_edge(root_question, level1_question, type=EdgeType.REQUIRES.value)
        graph.add_edge(level1_question, level2_question, type=EdgeType.REQUIRES.value)
        graph.add_edge(level2_question, level3_question_blocked, type=EdgeType.REQUIRES.value)

        # The blocking status should propagate up through all levels
        self.assertTrue(level2_question.is_blocked(graph))
        self.assertTrue(level1_question.is_blocked(graph))
        self.assertTrue(root_question.is_blocked(graph))

    def test_question_blocking_with_reference_edge_type(self):
        """Test that blocking doesn't propagate through REFERENCES edge type."""
        graph = nx.DiGraph()

        parent_question = Question(id="parent", name="Parent Question", is_resolved=True)
        child_question_blocked = Question(id="child", name="Child Question", is_resolved=False)

        graph.add_nodes_from([parent_question, child_question_blocked])
        graph.add_edge(parent_question, child_question_blocked, type=EdgeType.REFERENCES)

        # parent_question is resolved and the child is only referenced (not required),
        # so parent_question should not be blocked
        self.assertFalse(parent_question.is_blocked(graph))

    def test_question_blocking_with_mixed_edge_types(self):
        """Test blocking behavior with mixed edge types."""
        graph = nx.DiGraph()

        parent_question = Question(id="parent", name="Parent Question", is_resolved=True)
        required_child = Question(id="required", name="Required Child", is_resolved=False)
        referenced_child = Question(id="referenced", name="Referenced Child", is_resolved=False)

        graph.add_nodes_from([parent_question, required_child, referenced_child])
        graph.add_edge(parent_question, required_child, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_question, referenced_child, type=EdgeType.REFERENCES)

        # parent_question should be blocked because required_child is blocked
        self.assertTrue(parent_question.is_blocked(graph))

    def test_changing_resolved_status_affects_blocking(self):
        """Test that changing the resolved status affects blocking status."""
        graph = nx.DiGraph()

        question = Question(id="q", name="Question", is_resolved=False)
        graph.add_node(question)

        self.assertTrue(question.is_blocked(graph))

        # Change resolved status
        question.is_resolved = True
        self.assertFalse(question.is_blocked(graph))

        # Change back
        question.is_resolved = False
        self.assertTrue(question.is_blocked(graph))

    def test_resolved_question_blocked_by_child(self):
        """Test that a resolved question is still blocked if its children are blocked."""
        graph = nx.DiGraph()

        parent_question = Question(id="parent", name="Parent Question", is_resolved=True)
        child_question = Question(id="child", name="Child Question", is_resolved=False)

        graph.add_nodes_from([parent_question, child_question])
        graph.add_edge(parent_question, child_question, type=EdgeType.REQUIRES.value)

        # Even though parent_question is resolved, it should be blocked because child_question is blocked
        self.assertTrue(parent_question.is_blocked(graph))

    def test_question_with_mixed_child_types(self):
        """Test question with different types of child nodes."""
        graph = nx.DiGraph()

        parent_question = Question(id="parent", name="Parent Question", is_resolved=True)
        blocking_node = BlockingNodeForTesting(id="blocker", name="Blocker", blocks=True)
        non_blocking_node = BlockingNodeForTesting(id="non_blocker", name="Non-Blocker", blocks=False)

        graph.add_nodes_from([parent_question, blocking_node, non_blocking_node])
        graph.add_edge(parent_question, blocking_node, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_question, non_blocking_node, type=EdgeType.REQUIRES.value)

        # parent_question should be blocked because one of its children (blocking_node) is blocked
        self.assertTrue(parent_question.is_blocked(graph))

    def test_empty_graph_for_question(self):
        """Test that a question in an empty graph is blocked only by its resolution status."""
        empty_graph = nx.DiGraph()  # Graph with no edges

        resolved_question = Question(id="resolved", name="Resolved Question", is_resolved=True)
        unresolved_question = Question(id="unresolved", name="Unresolved Question", is_resolved=False)

        empty_graph.add_nodes_from([resolved_question, unresolved_question])

        self.assertFalse(resolved_question.is_blocked(empty_graph))
        self.assertTrue(unresolved_question.is_blocked(empty_graph))


if __name__ == "__main__":
    unittest.main()
