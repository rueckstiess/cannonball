from cannonball.nodes import (
    StatefulNode,
    Task,
    Bullet,
    Decision,
    Question,
    Answer,
    parse_markdown,
)
import pytest


@pytest.fixture(scope="class")
def task_with_2_subtasks():
    return parse_markdown("""
        - [ ] Task 1
            - [ ] Task 2
            - [x] Task 3
        """)


@pytest.fixture(scope="class")
def nested_task_with_bullets():
    return parse_markdown(
        """
        - [ ] Task 1
            - [ ] Task 2
                - Bullet 1
                - Bullet 2
            - [x] Task 3
        """,
        auto_resolve=False,  # to prevent auto-completing Task 2
    )


class TestParseMarkdown:
    def test_empty_markdown(self):
        """Test parsing empty markdown."""
        result = parse_markdown("")
        assert result is None

    def test_no_list_markdown(self):
        """Test parsing markdown with no list items."""
        result = parse_markdown("This is just text")
        assert result is None

    def test_parse_markdown_converts_node_correctly(self):
        """Test that parse_markdown converts list items to nodes correctly and handles multiple references."""
        markdown = """
        - [!] Blocked task with refs ^123 [[#^ref1]] [[#^ref2]]
        """
        root = parse_markdown(markdown)
        assert isinstance(root, Task)
        assert root.name == "Blocked task with refs"
        assert root.is_blocked

    def test_multiple_roots(self):
        """Test parsing markdown with multiple root lists to force common root creation."""
        markdown = """
        - Root 1
        
        - Root 2
        """
        root = parse_markdown(markdown)
        assert root.name == "Root"
        assert len(root.children) == 2
        assert root.children[0].name == "Root 1"
        assert root.children[1].name == "Root 2"

    def test_simple_bullet_list(self):
        """Test parsing a simple bullet list."""
        markdown = """
        - Item 1
        - Item 2
        """
        root = parse_markdown(markdown)

        assert isinstance(root, StatefulNode)
        # Root node was added
        assert root.name == "Root"
        assert len(root.children) == 2

    def test_mixed_node_types(self):
        """Test parsing mixed node types."""
        markdown = """
        - [ ] Task
            - Bullet
            - [?] Question
                - [D] Decision
                - [A] Answer
        """
        root = parse_markdown(markdown)

        # With the current implementation, we expect the root to be the Answer
        assert isinstance(root, Task)
        assert root.name == "Task"

        # Check the structure matches expected
        assert len(root.children) == 2

        bullet = root.children[0]
        assert isinstance(bullet, Bullet)
        assert bullet.name == "Bullet"

        question = root.children[1]
        assert isinstance(question, Question)
        assert question.name == "Question"

        assert len(question.children) == 2

        decision = question.children[0]
        assert isinstance(decision, Decision)
        assert decision.name == "Decision"

        answer = question.children[1]
        assert isinstance(answer, Answer)
        assert answer.name == "Answer"


class TestMarkdown:
    def test_basic_markdown_parsing(self, task_with_2_subtasks):
        """Test basic markdown parsing."""
        task1 = task_with_2_subtasks

        assert isinstance(task1, Task)
        assert len(task1.children) == 2
        assert task1.is_completed is False

        task2 = task1.find_by_name("Task 2")
        assert isinstance(task2, Task)
        assert task2.is_completed is False

        task3 = task1.find_by_name("Task 3")
        assert isinstance(task3, Task)
        assert task3.is_completed is True

    def test_nested_task_with_bullets(self, nested_task_with_bullets):
        """Test nested task with bullets."""
        task1 = nested_task_with_bullets

        assert isinstance(task1, Task)
        assert len(task1.children) == 2
        assert task1.is_completed is False

        task2 = task1.find_by_name("Task 2")
        assert isinstance(task2, Task)
        assert len(task2.children) == 2
        assert task2.is_completed is False

        bullet1 = task2.find_by_name("Bullet 1")
        assert isinstance(bullet1, Bullet)
        assert bullet1.is_completed is True

        bullet2 = task2.find_by_name("Bullet 2")
        assert isinstance(bullet2, Bullet)
        assert bullet2.is_completed is True
