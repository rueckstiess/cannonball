from cannonball import Node
import pytest


class TestStatefulNode:
    def test_stateful_node_init(self):
        """Test initializing a stateful node with different states."""
        node = Node("Test Node")
        assert not node.is_completed
        assert not node.is_blocked

        completed_node = Node("Completed Node", completed=True)
        assert completed_node.is_completed
        assert not completed_node.is_blocked

        blocked_node = Node("Blocked Node", blocked=True)
        assert not blocked_node.is_completed
        assert blocked_node.is_blocked

        with pytest.raises(ValueError):
            # Cannot have both completed and blocked states
            Node("Invalid Node", completed=True, blocked=True)

    def test_init_with_marker(self):
        """Test initializing a stateful node with a marker."""
        node = Node("Test Node", marker="F")
        assert node.marker == "F"
        assert node.to_markdown() == "- [F] Test Node"

    def test_init_without_marker(self):
        """Test initializing a stateful node with a marker."""
        node = Node("Test Node", marker=None)
        assert node.marker is None
        assert node.to_markdown() == "- Test Node"

    def test_add_parent_in_init(self):
        """Test adding a parent during initialization."""
        parent = Node("Parent Node")
        child = Node("Child Node", parent=parent)

        assert child.parent == parent
        assert child in parent.children

    def test_add_children_in_init(self):
        """Test adding a parent during initialization."""
        child = Node("Child Node")

        parent = Node("Parent Node", children=[child])

        assert child.parent == parent
        assert child in parent.children

    def test_repr_method(self):
        """Test the __repr__ method of StatefulNode."""
        node = Node("Test Node", completed=True, blocked=False)
        repr_str = repr(node)
        expected = "Node(Test Node, completed=True, blocked=False)"
        assert repr_str == expected

    def test_recompute_stated_not_called_without_parent_children(self, mocker):
        """Test that recompute_state is not called on initialization if there are no children."""

        spy = mocker.spy(Node, "_recompute_state")
        Node("Test Node")
        assert spy.call_count == 0

    def test_recompute_state_called_with_children(self, mocker):
        """Test that recompute_state is called on initialization if there are children."""

        class ChildNode(Node):
            pass

        class ParentNode(Node):
            pass

        child_spy = mocker.spy(ChildNode, "_recompute_state")
        child = ChildNode("Child Node")
        assert child_spy.call_count == 0

        parent_spy = mocker.spy(ParentNode, "_recompute_state")
        ParentNode("Parent Node", children=[child])
        # called twice, but hard to avoid
        parent_spy.assert_called()

    def test_recompute_state_called_with_parent(self, mocker):
        """Test that recompute_state is called on initialization if there are children."""

        class ParentNode(Node):
            pass

        class ChildNode(Node):
            pass

        parent_spy = mocker.spy(ParentNode, "_recompute_state")
        parent = ParentNode("Parent Node")
        assert parent_spy.call_count == 0

        child_spy = mocker.spy(ChildNode, "_recompute_state")
        ChildNode("Child Node", parent=parent)

        assert child_spy.call_count == 0
        parent_spy.assert_called()

    def test_parent_child_relationship(self):
        """Test parent-child relationship creation."""
        parent = Node("Parent")
        child = Node("Child", parent=parent)

        assert child.parent == parent
        assert child in parent.children

    def test_state_propagation_to_parent(self):
        """Test that state changes in children propagate to parents."""
        parent = Node("Parent")
        child1 = Node("Child 1", parent=parent)
        child2 = Node("Child 2", parent=parent)

        # Initially all nodes are incomplete
        assert not parent.is_completed

        # Complete all children
        child1._completed = True
        child1._notify_parent()
        assert not parent.is_completed  # Not all children completed yet

        child2._completed = True
        child2._notify_parent()
        assert parent.is_completed  # All children completed now

    def test_blocked_propagation(self):
        """Test that blocked state correctly propagates to parent."""
        parent = Node("Parent")
        child1 = Node("Child 1", parent=parent)
        Node("Child 2", parent=parent)

        # Block one child
        child1._blocked = True
        child1._notify_parent()

        # Parent should be blocked if any child is blocked
        assert parent.is_blocked

        # Unblock the child
        child1._blocked = False
        child1._notify_parent()
        assert not parent.is_blocked

    def test_post_attach_recomputation_completed(self):
        """Test state recomputation after attaching/detaching children."""
        parent = Node("Parent")
        child1 = Node("Child 1", completed=True)
        child2 = Node("Child 2", completed=True)

        assert not parent.is_completed

        # Attach completed children
        parent.children = [child1, child2]
        assert parent.is_completed

    def test_post_detach_recomputation_blocked(self, mocker):
        """Test state recomputation after attaching/detaching children."""

        class ParentNode(Node):
            pass

        spy = mocker.spy(ParentNode, "_recompute_state")

        parent = ParentNode("Parent")
        assert spy.call_count == 0
        assert not parent.is_completed
        assert not parent.is_blocked

        child = Node("Child 1", parent=parent, blocked=True)
        assert spy.call_count == 1
        assert not parent.is_completed
        assert parent.is_blocked

        # Detach child
        child.parent = None
        assert spy.call_count > 1
        assert not parent.is_completed

        # parent is a leaf, but StatefulNode does not change its state, it remains blocked
        assert parent.is_blocked

    def test_complex_state_propagation(self):
        """Test state propagation in a complex tree."""
        root = Node("Root")
        branch1 = Node("Branch 1", parent=root)
        branch2 = Node("Branch 2", parent=root)

        leaf1 = Node("Leaf 1", parent=branch1)
        leaf2 = Node("Leaf 2", parent=branch1)
        leaf3 = Node("Leaf 3", parent=branch2)

        # Initially nothing is completed
        assert not root.is_completed

        # Complete leaves in branch1
        leaf1._completed = True
        leaf1._notify_parent()
        leaf2._completed = True
        leaf2._notify_parent()

        # Branch1 should now be completed but not root
        assert branch1.is_completed
        assert not root.is_completed

        # Complete leaf in branch2
        leaf3._completed = True
        leaf3._notify_parent()

        # Now root should be completed
        assert root.is_completed

        # Block one leaf
        leaf2._blocked = True
        leaf2._notify_parent()

        # Branch1 and root should be blocked and not completed
        assert branch1.is_blocked
        assert not branch1.is_completed
        assert root.is_blocked
        assert not root.is_completed
