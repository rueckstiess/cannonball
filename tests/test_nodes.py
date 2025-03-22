import pytest
from anytree import RenderTree
from cannonball.nodes import Task, TaskState, Node


class TestTaskBasics:
    """Test basic task creation and properties."""

    def test_create_task(self):
        """Test task creation and default state."""
        task = Task("Create test suite")
        assert task.state == TaskState.OPEN
        assert task.content == "Create test suite"

    def test_create_task_with_state(self):
        """Test creating a task with a specific state."""
        task = Task("In progress task", state=TaskState.IN_PROGRESS)
        assert task.state == TaskState.IN_PROGRESS


class TestLeafTaskStateChanges:
    """Test state changes for leaf tasks (no children)."""

    def test_start_leaf_task(self):
        """Test starting a leaf task."""
        task = Task("Leaf task")
        assert task.start() is True
        assert task.state == TaskState.IN_PROGRESS

    def test_block_leaf_task(self):
        """Test blocking a leaf task."""
        task = Task("Leaf task")
        assert task.block() is True
        assert task.state == TaskState.BLOCKED

    def test_complete_leaf_task(self):
        """Test completing a leaf task."""
        task = Task("Leaf task")
        assert task.complete() is True
        assert task.state == TaskState.COMPLETED

    def test_cancel_leaf_task(self):
        """Test cancelling a leaf task."""
        task = Task("Leaf task")
        assert task.cancel() is True
        assert task.state == TaskState.CANCELLED

    def test_reopen_completed_leaf_task(self):
        """Test reopening a completed leaf task."""
        task = Task("Leaf task", state=TaskState.COMPLETED)
        assert task.reopen() is True
        assert task.state == TaskState.OPEN

    def test_reopen_cancelled_leaf_task(self):
        """Test reopening a cancelled leaf task."""
        task = Task("Leaf task", state=TaskState.CANCELLED)
        assert task.reopen() is True
        assert task.state == TaskState.OPEN

    def test_repeated_state_change(self):
        """Test that changing to the same state returns False."""
        task = Task("Leaf task", state=TaskState.BLOCKED)
        assert task.block() is False  # Already blocked

        task.state = TaskState.COMPLETED
        assert task.complete() is False  # Already completed


class TestParentChildStateRelationship:
    """Test how parent task states are affected by child task states."""

    def test_parent_with_open_children(self):
        """Parent task with all open children should be open."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        assert parent.state == TaskState.OPEN

    def test_parent_with_in_progress_child(self):
        """Parent task with an in-progress child should be in-progress."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        child1.start()
        assert parent.state == TaskState.IN_PROGRESS

    def test_parent_with_blocked_child(self):
        """Parent task with a blocked child should be blocked."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        child1.start()
        assert parent.state == TaskState.IN_PROGRESS

        child2.block()
        assert parent.state == TaskState.BLOCKED

    def test_parent_with_all_completed_children(self):
        """Parent task with all completed children should be completed."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        child1.complete()
        # Parent not completed yet but in progress
        assert parent.state == TaskState.IN_PROGRESS

        child2.complete()
        # Now parent should be completed
        assert parent.state == TaskState.COMPLETED

    def test_parent_with_mixed_resolved_children(self):
        """Parent task with all children resolved (mix of completed and cancelled) should be completed."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        child1.complete()
        child2.cancel()

        assert parent.state == TaskState.COMPLETED

    def test_completing_parent_with_unresolved_children(self):
        """Attempting to complete a parent with unresolved children should fail."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        child1.complete()
        # child2 is still open

        assert parent.complete() is False
        assert parent.state == TaskState.IN_PROGRESS

    def test_nested_state_propagation(self):
        """Test state propagation through multiple levels."""
        grandparent = Task("Grandparent")
        parent1 = Task("Parent 1", parent=grandparent)
        parent2 = Task("Parent 2", parent=grandparent)
        child1 = Task("Child 1.1", parent=parent1)
        child2 = Task("Child 1.2", parent=parent1)
        child3 = Task("Child 2.1", parent=parent2)

        # Initial state
        assert grandparent.state == TaskState.OPEN

        # Start one task deep in the tree
        child1.start()
        assert parent1.state == TaskState.IN_PROGRESS
        assert grandparent.state == TaskState.IN_PROGRESS

        # Complete tasks in first branch
        child1.complete()
        child2.complete()
        assert parent1.state == TaskState.COMPLETED
        assert grandparent.state == TaskState.IN_PROGRESS  # parent2's child is still open

        # Complete last task
        child3.complete()
        assert parent2.state == TaskState.COMPLETED
        assert grandparent.state == TaskState.COMPLETED

    def test_mixed_node_types(self):
        """Test that non-Task children don't affect Task state calculations."""
        parent = Task("Parent")
        task_child = Task("Task Child", parent=parent)
        note_child = Node("Note", parent=parent)  # Not a Task

        assert parent.state == TaskState.OPEN

        task_child.complete()
        assert parent.state == TaskState.COMPLETED  # Only considers Task children


class TestTaskCancellation:
    """Test cancellation propagation behavior."""

    def test_cancel_propagates_to_children(self):
        """Cancelling a parent should cancel all child tasks."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)
        grandchild = Task("Grandchild", parent=child1)

        # Start some tasks
        child2.start()
        grandchild.start()

        # Cancel parent
        parent.cancel()

        # All should be cancelled
        assert parent.state == TaskState.CANCELLED
        assert child1.state == TaskState.CANCELLED
        assert child2.state == TaskState.CANCELLED
        assert grandchild.state == TaskState.CANCELLED

    def test_cancel_subtree(self):
        """Cancelling a subtree should not affect siblings or parents."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)
        grandchild1 = Task("Grandchild 1", parent=child1)
        grandchild2 = Task("Grandchild 2", parent=child1)

        # Cancel one subtree
        child1.cancel()

        # Check cancellation propagation
        assert child1.state == TaskState.CANCELLED
        assert grandchild1.state == TaskState.CANCELLED
        assert grandchild2.state == TaskState.CANCELLED

        # Sibling and parent should be unaffected
        assert child2.state == TaskState.OPEN
        assert parent.state == TaskState.OPEN


class TestTaskReopening:
    """Test reopening completed or cancelled tasks."""

    def test_reopen_leaf_task(self):
        """Test reopening a leaf task."""
        task = Task("Leaf", state=TaskState.COMPLETED)
        task.reopen()
        assert task.state == TaskState.OPEN

    def test_reopen_parent_task(self):
        """Reopening a parent task should not be possible."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        # Complete all tasks
        child1.complete()
        child2.complete()
        assert parent.state == TaskState.COMPLETED

        # Attempt to reopen parent
        assert parent.reopen() is False

        # Reopen one child
        child1.reopen()

        # Parent should derive new state
        assert parent.state == TaskState.IN_PROGRESS
        assert child1.state == TaskState.OPEN

        # Start the reopened child
        child1.start()
        assert parent.state == TaskState.IN_PROGRESS


class TestEdgeCases:
    """Test various edge cases and complex scenarios."""

    def test_add_child_recomputes_state(self):
        """Adding a child should recompute parent state."""
        parent = Task("Parent")
        assert parent.state == TaskState.OPEN

        # Add a blocked child
        child = Task("Child", state=TaskState.BLOCKED)
        parent.add_child(child)

        # Parent should become blocked
        assert parent.state == TaskState.BLOCKED

    def test_remove_child_recomputes_state(self):
        """Removing a child should recompute parent state."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent, state=TaskState.COMPLETED)

        # Parent should be completed
        assert parent.state == TaskState.COMPLETED

        # Add a blocked child
        child2 = Task("Child 2", parent=parent, state=TaskState.BLOCKED)

        # Parent should be blocked due to child2
        assert parent.state == TaskState.BLOCKED

        # Remove blocked child
        parent.remove_child(child2)

        # Parent should now be completed
        assert parent.state == TaskState.COMPLETED

    def test_can_complete_checks(self):
        """Test the can_complete helper method."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        # Initially can't complete
        assert parent.can_complete() is False

        # Complete one child
        child1.complete()
        assert parent.can_complete() is False

        # Complete all children
        child2.complete()
        assert parent.can_complete() is True

    def test_empty_parent_completion(self):
        """A parent with no children should be directly completable."""
        parent = Task("Empty Parent")  # No children

        assert parent.is_leaf is True
        assert parent.complete() is True
        assert parent.state == TaskState.COMPLETED

    def test_parent_with_non_task_children_only(self):
        """A parent with only non-Task children should behave like a leaf."""
        parent = Task("Parent")
        note1 = Node("Note 1", parent=parent)
        note2 = Node("Note 2", parent=parent)

        # Should be treated as a leaf for task state purposes
        assert parent.complete() is True
        assert parent.state == TaskState.COMPLETED


def visualize_tree(root):
    """Helper function to print a tree for debugging."""
    result = ""
    for pre, _, node in RenderTree(root):
        if isinstance(node, Task):
            result += f"{pre}{node.content} ({node.state})\n"
        else:
            result += f"{pre}{node.content}\n"
    return result


class TestVisualization:
    """Test tree visualization for debugging."""

    def test_tree_visualization(self):
        """Simple test to verify visualization helper."""
        parent = Task("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent, state=TaskState.IN_PROGRESS)

        vis = visualize_tree(parent)
        print("\nTree visualization:")
        print(vis)

        assert "Parent (in_progress)" in vis
        assert "├── Child 1 (open)" in vis
        assert "└── Child 2 (in_progress)" in vis
