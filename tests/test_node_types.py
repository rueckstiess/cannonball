from cannonball import Node, Bullet, Artefact, Question, Decision, Task


class TestNode:
    def test_base_node_creation(self):
        """Test creation of a base Node."""
        node = Node("Test Node", id="test123")
        assert node.name == "Test Node"
        assert node.id == "test123"
        assert node.parent is None
        assert len(node.children) == 0

    def test_node_with_children(self):
        """Test creating a Node with children."""
        child1 = Node("Child 1")
        child2 = Node("Child 2")
        parent = Node("Parent", children=[child1, child2])

        assert len(parent.children) == 2
        assert child1.parent == parent
        assert child2.parent == parent

    def test_node_repr(self):
        """Test the string representation of a Node."""
        node = Node("Test Node")
        assert repr(node) == "Node(Test Node, completed=False, blocked=False)"

    def test_from_contents_bullet(self):
        """Test creating a Bullet node from contents."""
        node = Node.from_contents(node_id="123", content="Test content", marker=None)
        assert isinstance(node, Bullet)
        assert node.name == "Test content"
        assert node.id == "123"

    def test_from_contents_task_open(self):
        """Test creating an open Task from contents."""
        node = Node.from_contents(node_id="123", content="Test task", marker=" ")
        assert isinstance(node, Task)
        assert node.is_completed is False

    def test_from_contents_task_blocked(self):
        """Test creating a blocked Task from contents."""
        node = Node.from_contents(node_id="123", content="Test task", marker="!")
        assert isinstance(node, Task)
        assert node.is_blocked is True

    def test_from_contents_task_completed(self):
        """Test creating a completed Task from contents."""
        node = Node.from_contents(node_id="123", content="Test task", marker="x")
        assert isinstance(node, Task)
        assert node.is_completed is True

    def test_from_contents_question(self):
        """Test creating a Question from contents."""
        node = Node.from_contents(node_id="123", content="Test question", marker="?")
        assert isinstance(node, Question)
        assert node.is_completed is False

    def test_from_contents_decision(self):
        """Test creating a Decision from contents."""
        node = Node.from_contents(node_id="123", content="Test decision", marker="D")
        assert isinstance(node, Decision)
        assert node.is_completed is False

    def test_from_contents_answer(self):
        """Test creating an Answer from contents."""
        node = Node.from_contents(node_id="123", content="Test artefact", marker="A")
        assert isinstance(node, Artefact)
        assert node.is_completed is True

    def test_from_contents_unknown_marker(self):
        """Test creating a node with an unknown marker."""
        node = Node.from_contents(node_id="123", content="Test unknown", marker="Z")
        assert isinstance(node, Node)
        assert node.is_completed is False

    def test_find_by_name(self):
        """Test finding a node by name."""
        child1 = Node("Child One")
        child2 = Node("Child Two")
        parent = Node("Parent", children=[child1, child2])

        found = parent.find_by_name("Child O")
        assert found == child1

        found = parent.find_by_name("Child T")
        assert found == child2

        found = parent.find_by_name("Nonexistent")
        assert found is None


class TestBullet:
    def test_bullet_init(self):
        """Test Bullet node initialization."""
        bullet = Bullet("Test Bullet", id="b123")
        assert bullet.name == "Test Bullet"
        assert bullet.id == "b123"
        assert bullet.is_completed is True

    def test_bullet_repr(self):
        """Test Bullet node representation."""
        bullet = Bullet("Test Bullet")
        assert repr(bullet) == "Bullet(Test Bullet, completed=True, blocked=False)"

    def test_bullet_str(self):
        """Test Bullet node string."""
        bullet = Bullet("Test Bullet")
        assert str(bullet) == "- Test Bullet"
