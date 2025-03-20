import unittest
import networkx as nx
from cannonball.nodes import Task, BlockingNode, TaskType
from cannonball.utils import EdgeType


class BlockingNodeForTesting(BlockingNode):
    """A simple BlockingNode implementation for testing that can be configured to block or not."""

    def __init__(self, id, name, blocks=False, **kwargs):
        super().__init__(id=id, name=name, **kwargs)
        self._blocks = blocks

    def is_blocked(self, graph):
        return self._blocks


class TestTask(unittest.TestCase):
    def test_task_initialization(self):
        """Test that a Task is initialized with the correct default values."""
        task = Task(id="task1", name="Task 1")
        self.assertEqual(task.id, "task1")
        self.assertEqual(task.name, "Task 1")
        self.assertEqual(task._status, TaskType.OPEN)
        self.assertEqual(task.marker, " ")
        self.assertIsNone(task.ref)

    def test_task_custom_initialization(self):
        """Test that a Task can be initialized with custom values."""
        task = Task(
            id="task2", name="Task 2", ref="REF123", status=TaskType.IN_PROGRESS
        )
        self.assertEqual(task.id, "task2")
        self.assertEqual(task.name, "Task 2")
        self.assertEqual(task._status, TaskType.IN_PROGRESS)
        self.assertEqual(task.marker, "/")
        self.assertEqual(task.ref, "REF123")

    def test_marker_inference_from_status(self):
        """Test that all task statuses correctly infer their respective markers."""
        open_task = Task(id="open", name="Open Task", status=TaskType.OPEN)
        in_progress_task = Task(
            id="progress", name="In Progress Task", status=TaskType.IN_PROGRESS
        )
        completed_task = Task(
            id="done", name="Completed Task", status=TaskType.COMPLETED
        )
        cancelled_task = Task(
            id="cancelled", name="Cancelled Task", status=TaskType.CANCELLED
        )

        self.assertEqual(open_task.marker, " ")
        self.assertEqual(in_progress_task.marker, "/")
        self.assertEqual(completed_task.marker, "x")
        self.assertEqual(cancelled_task.marker, "-")

    def test_marker_updates_with_status_change(self):
        """Test that changing the task status also updates its marker."""
        task = Task(id="task", name="Task", status=TaskType.OPEN)
        self.assertEqual(task.marker, " ")

        # Change status and verify marker updates
        task.status = TaskType.IN_PROGRESS
        self.assertEqual(task.marker, "/")
        task.status = TaskType.COMPLETED
        self.assertEqual(task.marker, "x")
        task.status = TaskType.CANCELLED
        self.assertEqual(task.marker, "-")

    def test_is_finished_for_different_statuses(self):
        """Test is_finished() returns correct result for different task statuses."""
        open_task = Task(id="open", name="Open Task", status=TaskType.OPEN)
        in_progress_task = Task(
            id="progress", name="In Progress Task", status=TaskType.IN_PROGRESS
        )
        completed_task = Task(
            id="done", name="Completed Task", status=TaskType.COMPLETED
        )
        cancelled_task = Task(
            id="cancelled", name="Cancelled Task", status=TaskType.CANCELLED
        )

        self.assertFalse(open_task.is_finished())
        self.assertFalse(in_progress_task.is_finished())
        self.assertTrue(completed_task.is_finished())
        self.assertTrue(cancelled_task.is_finished())

    def test_is_blocked_for_different_statuses(self):
        """Test is_blocked() returns correct result for different task statuses."""
        graph = nx.DiGraph()

        open_task = Task(id="open", name="Open Task", status=TaskType.OPEN)
        in_progress_task = Task(
            id="progress", name="In Progress Task", status=TaskType.IN_PROGRESS
        )
        completed_task = Task(
            id="done", name="Completed Task", status=TaskType.COMPLETED
        )
        cancelled_task = Task(
            id="cancelled", name="Cancelled Task", status=TaskType.CANCELLED
        )

        graph.add_nodes_from(
            [open_task, in_progress_task, completed_task, cancelled_task]
        )

        self.assertTrue(open_task.is_blocked(graph))
        self.assertTrue(in_progress_task.is_blocked(graph))
        self.assertFalse(completed_task.is_blocked(graph))
        self.assertFalse(cancelled_task.is_blocked(graph))

    def test_task_blocking_with_children(self):
        """Test that a task is blocked if any of its children are blocked."""
        graph = nx.DiGraph()

        parent_task = Task(id="parent", name="Parent Task", status=TaskType.COMPLETED)
        child_task_blocked = Task(
            id="child1", name="Child Task 1", status=TaskType.OPEN
        )
        child_task_unblocked = Task(
            id="child2", name="Child Task 2", status=TaskType.COMPLETED
        )

        graph.add_nodes_from([parent_task, child_task_blocked, child_task_unblocked])
        graph.add_edge(parent_task, child_task_blocked, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_task, child_task_unblocked, type=EdgeType.REQUIRES.value)

        # Even though parent_task is COMPLETED, it should be blocked because child_task_blocked is OPEN
        self.assertTrue(parent_task.is_blocked(graph))

    def test_task_blocking_with_unblocked_children(self):
        """Test that a task is not blocked if all its children are unblocked."""
        graph = nx.DiGraph()

        parent_task = Task(id="parent", name="Parent Task", status=TaskType.COMPLETED)
        child_task1 = Task(id="child1", name="Child Task 1", status=TaskType.COMPLETED)
        child_task2 = Task(id="child2", name="Child Task 2", status=TaskType.CANCELLED)

        graph.add_nodes_from([parent_task, child_task1, child_task2])
        graph.add_edge(parent_task, child_task1, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_task, child_task2, type=EdgeType.REQUIRES.value)

        # parent_task is COMPLETED and both children are finished, so it should not be blocked
        self.assertFalse(parent_task.is_blocked(graph))

    def test_task_blocking_with_deep_nesting(self):
        """Test blocking status propagation with multiple nesting levels."""
        graph = nx.DiGraph()

        root_task = Task(id="root", name="Root Task", status=TaskType.COMPLETED)
        level1_task = Task(id="level1", name="Level 1 Task", status=TaskType.COMPLETED)
        level2_task = Task(id="level2", name="Level 2 Task", status=TaskType.COMPLETED)
        level3_task_blocked = Task(
            id="level3", name="Level 3 Task", status=TaskType.OPEN
        )

        graph.add_nodes_from([root_task, level1_task, level2_task, level3_task_blocked])
        graph.add_edge(root_task, level1_task, type=EdgeType.REQUIRES.value)
        graph.add_edge(level1_task, level2_task, type=EdgeType.REQUIRES.value)
        graph.add_edge(level2_task, level3_task_blocked, type=EdgeType.REQUIRES.value)

        # The blocking status should propagate up through all levels
        self.assertTrue(level2_task.is_blocked(graph))
        self.assertTrue(level1_task.is_blocked(graph))
        self.assertTrue(root_task.is_blocked(graph))

    def test_task_blocking_with_reference_edge_type(self):
        """Test that blocking doesn't propagate through REFERENCES edge type."""
        graph = nx.DiGraph()

        parent_task = Task(id="parent", name="Parent Task", status=TaskType.COMPLETED)
        child_task_blocked = Task(id="child", name="Child Task", status=TaskType.OPEN)

        graph.add_nodes_from([parent_task, child_task_blocked])
        graph.add_edge(parent_task, child_task_blocked, type=EdgeType.REFERENCES)

        # parent_task is COMPLETED and the child is only referenced (not required),
        # so parent_task should not be blocked
        self.assertFalse(parent_task.is_blocked(graph))

    def test_task_blocking_with_mixed_edge_types(self):
        """Test blocking behavior with mixed edge types."""
        graph = nx.DiGraph()

        parent_task = Task(id="parent", name="Parent Task", status=TaskType.COMPLETED)
        required_child = Task(
            id="required", name="Required Child", status=TaskType.OPEN
        )
        referenced_child = Task(
            id="referenced", name="Referenced Child", status=TaskType.OPEN
        )

        graph.add_nodes_from([parent_task, required_child, referenced_child])
        graph.add_edge(parent_task, required_child, type=EdgeType.REQUIRES.value)
        graph.add_edge(parent_task, referenced_child, type=EdgeType.REFERENCES)

        # parent_task should be blocked because required_child is blocked
        self.assertTrue(parent_task.is_blocked(graph))

    def test_task_blocking_with_custom_blocking_nodes(self):
        """Test interaction with other BlockingNode types."""
        graph = nx.DiGraph()

        task = Task(id="task", name="Task", status=TaskType.COMPLETED)
        blocking_node = BlockingNodeForTesting(
            id="blocker", name="Blocker", blocks=True
        )
        non_blocking_node = BlockingNodeForTesting(
            id="non_blocker", name="Non-Blocker", blocks=False
        )

        graph.add_nodes_from([task, blocking_node, non_blocking_node])
        graph.add_edge(task, blocking_node, type=EdgeType.REQUIRES.value)
        graph.add_edge(task, non_blocking_node, type=EdgeType.REQUIRES.value)

        # task should be blocked because one of its children (blocking_node) is blocked
        self.assertTrue(task.is_blocked(graph))

    def test_changing_task_status_affects_blocking(self):
        """Test that changing the task status affects its blocking status."""
        graph = nx.DiGraph()

        task = Task(id="task", name="Task", status=TaskType.OPEN)
        graph.add_node(task)

        self.assertTrue(task.is_blocked(graph))

        # Change status to COMPLETED
        task._status = TaskType.COMPLETED
        self.assertFalse(task.is_blocked(graph))

        # Change back to IN_PROGRESS
        task._status = TaskType.IN_PROGRESS
        self.assertTrue(task.is_blocked(graph))

    def test_completed_task_blocked_by_child(self):
        """Test that a completed task is still blocked if its children are blocked."""
        graph = nx.DiGraph()

        parent_task = Task(id="parent", name="Parent Task", status=TaskType.COMPLETED)
        child_task = Task(id="child", name="Child Task", status=TaskType.OPEN)

        graph.add_nodes_from([parent_task, child_task])
        graph.add_edge(parent_task, child_task, type=EdgeType.REQUIRES.value)

        # Even though parent_task is COMPLETED, it should be blocked because child_task is blocked
        self.assertTrue(parent_task.is_blocked(graph))


if __name__ == "__main__":
    unittest.main()
