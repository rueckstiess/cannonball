from cannonball.nodes import (
    Task,
    NodeState,
)


class TestTaskSpecificMethods:
    """Test Task-specific methods that aren't covered in other tests."""

    def test_start_non_leaf_task(self):
        """Test that attempting to start a non-leaf task returns False."""
        parent = Task("Parent")
        Task("Child", parent=parent)

        # Parent is not a leaf, so start should fail
        assert parent.start() is False
        assert parent.state == NodeState.OPEN  # State shouldn't change

    def test_start_resolved_task(self):
        """Test that attempting to start a resolved task returns False."""
        task = Task("Test Task", state=NodeState.COMPLETED)

        # Task is already completed, so start should fail
        assert task.start() is False
        assert task.state == NodeState.COMPLETED  # State shouldn't change

        task.state = NodeState.CANCELLED
        assert task.start() is False
        assert task.state == NodeState.CANCELLED  # State shouldn't change

    def test_cancel_already_cancelled(self):
        """Test that cancelling an already cancelled task returns False."""
        task = Task("Test Task", state=NodeState.CANCELLED)

        assert task.cancel() is False
        assert task.state == NodeState.CANCELLED  # State shouldn't change
