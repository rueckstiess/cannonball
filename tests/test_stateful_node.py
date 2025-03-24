from cannonball.nodes import (
    NodeState,
    StatefulNode,
    Task,
)


class TestStatefulNodeBasics:
    """Test basic stateful node creation and properties."""

    def test_create_stateful_node(self):
        """Test stateful node creation and default state."""
        node = StatefulNode("Test Node")
        assert node.state == NodeState.OPEN
        assert node.name == "Test Node"

    def test_create_stateful_node_with_state(self):
        """Test creating a stateful node with a specific state."""
        node = StatefulNode("Test Node", state=NodeState.IN_PROGRESS)
        assert node.state == NodeState.IN_PROGRESS

    def test_repr(self):
        """Test the repr of a stateful node includes the state."""
        node = StatefulNode("Test Node", state=NodeState.BLOCKED)
        # The actual format includes the full NodeState.BLOCKED rather than just BLOCKED
        assert "StatefulNode(Test Node, state=NodeState.BLOCKED)" in repr(node)

    def test_str(self):
        """Test the string representation of a stateful node."""
        node = StatefulNode("Test Node", state=NodeState.OPEN)
        assert str(node) == "[ ] Test Node"

        node.state = NodeState.IN_PROGRESS
        assert str(node) == "[/] Test Node"

        node.state = NodeState.BLOCKED
        assert str(node) == "[!] Test Node"

        node.state = NodeState.COMPLETED
        assert str(node) == "[✓] Test Node"

        node.state = NodeState.CANCELLED
        assert str(node) == "[-] Test Node"


class TestStatefulNodeStateChanges:
    """Test state changes for stateful nodes."""

    def test_state_setter(self):
        """Test that the state setter properly updates the state."""
        node = StatefulNode("Test Node")
        assert node.state == NodeState.OPEN

        node.state = NodeState.IN_PROGRESS
        assert node.state == NodeState.IN_PROGRESS

        node.state = NodeState.COMPLETED
        assert node.state == NodeState.COMPLETED

    def test_state_propagation_to_parent(self):
        """Test that state changes propagate to parent."""
        parent = StatefulNode("Parent")
        child = Task("Child", parent=parent)

        # Both should start OPEN
        assert parent.state == NodeState.OPEN
        assert child.state == NodeState.OPEN

        # Change child state and verify parent updates
        child.state = NodeState.IN_PROGRESS
        assert parent.state == NodeState.IN_PROGRESS

    def test_cancellation_propagation(self):
        """Test that setting to CANCELLED propagates to children."""
        parent = StatefulNode("Parent")
        child1 = Task("Child 1", parent=parent)
        child2 = Task("Child 2", parent=parent)

        # Initially all OPEN
        assert parent.state == NodeState.OPEN
        assert child1.state == NodeState.OPEN
        assert child2.state == NodeState.OPEN

        # Cancel the parent
        parent.state = NodeState.CANCELLED

        # All children should be cancelled
        assert child1.state == NodeState.CANCELLED
        assert child2.state == NodeState.CANCELLED

    def test_is_resolved(self):
        """Test the is_resolved helper method."""
        node = StatefulNode("Test Node")

        # Open node is not resolved
        assert node.is_resolved() is False

        # Blocked node is not resolved
        node.state = NodeState.BLOCKED
        assert node.is_resolved() is False

        # In-progress node is not resolved
        node.state = NodeState.IN_PROGRESS
        assert node.is_resolved() is False

        # Completed node is resolved
        node.state = NodeState.COMPLETED
        assert node.is_resolved() is True

        # Cancelled node is resolved
        node.state = NodeState.CANCELLED
        assert node.is_resolved() is True

    def test_can_complete_leaf(self):
        """Test can_complete for leaf nodes."""
        node = StatefulNode("Leaf Node")

        # Open node can be completed
        assert node.state == NodeState.OPEN
        assert node.can_complete() is True

        # In-progress node can be completed
        node.state = NodeState.IN_PROGRESS
        assert node.can_complete() is True

        # Blocked node can be completed
        node.state = NodeState.BLOCKED
        assert node.can_complete() is True

        # Completed node cannot be completed again
        node.state = NodeState.COMPLETED
        assert node.can_complete() is False

        # Cancelled node cannot be completed
        node.state = NodeState.CANCELLED
        assert node.can_complete() is False

    def test_can_complete_parent(self):
        """Test can_complete for parent nodes with Task children."""
        parent = StatefulNode("Parent")
        Task("Child 1", parent=parent, state=NodeState.OPEN)
        Task("Child 2", parent=parent, state=NodeState.IN_PROGRESS)

        # Force parent state recomputation
        parent._recompute_state()

        # Parent with unresolved children cannot be completed
        assert parent.can_complete() is False

        # Modify children to be resolved
        for child in parent.children:
            if isinstance(child, Task):
                child.state = NodeState.COMPLETED

        # Now parent should be completable
        assert parent.can_complete() is True

    def test_add_and_remove_child(self):
        """Test adding and removing children with state recomputation."""
        parent = StatefulNode("Parent")
        child1 = Task("Child 1", state=NodeState.BLOCKED)

        # Initially parent is OPEN
        assert parent.state == NodeState.OPEN

        # Add child and verify state propagation
        parent.add_child(child1)
        assert parent.state == NodeState.BLOCKED

        # Currently the parent is still BLOCKED because it became a leaf and leaves don't calculate their state
        parent.remove_child(child1)
        assert parent.state == NodeState.BLOCKED

    def test_leaf_vs_parent_recomputation(self):
        """Test that leaf nodes don't recompute state."""
        # Create a stateful node
        node = StatefulNode("Test Node")

        # Should be a leaf node
        assert node.is_leaf is True

        # Manually set the state
        node._state = NodeState.IN_PROGRESS

        # Call _recompute_state - should not change anything for leaf nodes
        node._recompute_state()
        assert node.state == NodeState.IN_PROGRESS
