from cannonball.nodes import (
    NodeType,
    NodeState,
    Node,
    Bullet,
    Answer,
    Question,
    Decision,
    Task,
    StatefulNode,
    parse_markdown,
)
import pytest


class TestNodeType:
    def test_str_representation(self):
        """Test string representation of NodeType enum."""
        assert str(NodeType.TASK) == "task"
        assert str(NodeType.QUESTION) == "question"
        assert str(NodeType.GOAL) == "goal"
        assert str(NodeType.ALTERNATIVE) == "alternative"
        assert str(NodeType.DECISION) == "decision"


class TestNodeState:
    def test_repr_representation(self):
        """Test repr of NodeState enum."""
        assert repr(NodeState.OPEN) == "OPEN"
        assert repr(NodeState.IN_PROGRESS) == "IN_PROGRESS"
        assert repr(NodeState.BLOCKED) == "BLOCKED"
        assert repr(NodeState.COMPLETED) == "COMPLETED"
        assert repr(NodeState.CANCELLED) == "CANCELLED"

    def test_resolved_states(self):
        """Test the resolved_states class method."""
        resolved = NodeState.resolved_states()
        assert NodeState.COMPLETED in resolved
        assert NodeState.CANCELLED in resolved
        assert NodeState.OPEN not in resolved
        assert NodeState.IN_PROGRESS not in resolved
        assert NodeState.BLOCKED not in resolved


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
        assert repr(node) == "Node(Test Node)"

    def test_from_contents_bullet(self):
        """Test creating a Bullet node from contents."""
        node = Node.from_contents(id="123", content="Test content", marker=None)
        assert isinstance(node, Bullet)
        assert node.name == "Test content"
        assert node.id == "123"

    def test_from_contents_task_open(self):
        """Test creating an open Task from contents."""
        node = Node.from_contents(id="123", content="Test task", marker=" ")
        assert isinstance(node, Task)
        assert node.state == NodeState.OPEN

    def test_from_contents_task_in_progress(self):
        """Test creating an in-progress Task from contents."""
        node = Node.from_contents(id="123", content="Test task", marker="/")
        assert isinstance(node, Task)
        assert node.state == NodeState.IN_PROGRESS

    def test_from_contents_task_blocked(self):
        """Test creating a blocked Task from contents."""
        node = Node.from_contents(id="123", content="Test task", marker="!")
        assert isinstance(node, Task)
        assert node.state == NodeState.BLOCKED

    def test_from_contents_task_completed(self):
        """Test creating a completed Task from contents."""
        node = Node.from_contents(id="123", content="Test task", marker="x")
        assert isinstance(node, Task)
        assert node.state == NodeState.COMPLETED

    def test_from_contents_task_cancelled(self):
        """Test creating a cancelled Task from contents."""
        node = Node.from_contents(id="123", content="Test task", marker="-")
        assert isinstance(node, Task)
        assert node.state == NodeState.CANCELLED

    def test_from_contents_question(self):
        """Test creating a Question from contents."""
        node = Node.from_contents(id="123", content="Test question", marker="?")
        assert isinstance(node, Question)
        assert node.state == NodeState.OPEN

    def test_from_contents_decision(self):
        """Test creating a Decision from contents."""
        node = Node.from_contents(id="123", content="Test decision", marker="D")
        assert isinstance(node, Decision)
        assert node.state == NodeState.OPEN

    def test_from_contents_answer(self):
        """Test creating an Answer from contents."""
        node = Node.from_contents(id="123", content="Test answer", marker="A")
        assert isinstance(node, Answer)
        assert node.state == NodeState.COMPLETED

    def test_from_contents_unknown_marker(self):
        """Test creating a node with an unknown marker."""
        node = Node.from_contents(id="123", content="Test unknown", marker="Z")
        assert isinstance(node, StatefulNode)
        assert node.state == NodeState.OPEN

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
        assert bullet.state == NodeState.COMPLETED

    def test_bullet_repr(self):
        """Test Bullet node representation."""
        bullet = Bullet("Test Bullet")
        assert repr(bullet) == "Bullet(Test Bullet)"

    def test_bullet_str(self):
        """Test Bullet node string."""
        bullet = Bullet("Test Bullet")
        assert str(bullet) == "Test Bullet"


class TestAnswer:
    def test_answer_init(self):
        """Test Answer node initialization."""
        answer = Answer("Test Answer", id="a123")
        assert answer.name == "Test Answer"
        assert answer.id == "a123"
        assert answer.state == NodeState.COMPLETED

    def test_answer_str(self):
        """Test Answer node string."""
        answer = Answer("Test Answer")
        assert str(answer) == "[A] Test Answer"


@pytest.fixture
def question_with_tasks():
    """Create a question with tasks in various states."""
    question = Question("Test Question")
    Task("Task 1", parent=question, state=NodeState.OPEN)
    Task("Task 2", parent=question, state=NodeState.IN_PROGRESS)
    Task("Task 3", parent=question, state=NodeState.COMPLETED)
    Task("Task 4", parent=question, state=NodeState.BLOCKED)
    Task("Task 5", parent=question, state=NodeState.CANCELLED)

    # Force a recomputation of the state
    question._recompute_state()
    return question


@pytest.fixture
def question_with_decision():
    """Create a question with a decision."""
    return parse_markdown("""
        - [ ] Question
            - [D] Decision
                - [ ] Option 1
                - [x] Option 2
        """)


@pytest.fixture
def question_with_answer():
    """Create a question with an answer."""
    question = Question("Test Question")
    Answer("Answer", parent=question)
    return question


class TestQuestion:
    def test_question_initialization(self, question_with_tasks):
        """Test Question node initialization."""
        question = question_with_tasks
        assert isinstance(question, Question)
        assert question.name == "Test Question"
        assert len(question.children) == 5
        # Should be BLOCKED because there's a blocked task
        assert question.state == NodeState.BLOCKED

    def test_question_blocked(self, question_with_tasks):
        """Test Question node state with blocked tasks."""
        question = question_with_tasks
        # First make sure it's blocked due to the existing blocked task
        assert question.state == NodeState.BLOCKED

        # Remove the blocked state from the blocking task
        blocked_task = [child for child in question.children if child.state == NodeState.BLOCKED][0]
        blocked_task.state = NodeState.OPEN

        # Question should now be IN_PROGRESS because there are mixed states
        assert question.state == NodeState.IN_PROGRESS

    @pytest.mark.xfail(reason="Question logic not fully implemented")
    def test_question_completed_with_decision(self, question_with_decision):
        """Test Question completion with a completed Decision."""
        question = question_with_decision
        decision = question.find_by_name("Decision")
        open_option = question.find_by_name("Option 1")
        completed_option = question.find_by_name("Option 2")

        # Initially question should be OPEN because decision is OPEN (and not transparent)
        assert decision.state == NodeState.OPEN
        assert question.state == NodeState.OPEN

        # Complete the decision by deciding on open option
        decision.decide(open_option)
        assert decision.state == NodeState.COMPLETED
        # Question should be open because now decision is transparent
        assert question.state == NodeState.OPEN

        # Complete the decision by deciding on completed option
        decision.decide(completed_option)
        assert decision.state == NodeState.COMPLETED
        # Question should be open because now decision is transparent
        assert question.state == NodeState.COMPLETED

    def test_question_completed_with_answer(self, question_with_answer):
        """Test Question completion with a completed Answer."""
        question = question_with_answer
        answer = question.children[0]
        assert isinstance(answer, Answer)
        assert answer.state == NodeState.COMPLETED

        # Question should be completed due to the Answer
        assert question.state == NodeState.COMPLETED

    def test_question_with_no_children(self):
        """Test Question state with no children."""
        question = Question("Empty Question")
        assert question.state == NodeState.OPEN
