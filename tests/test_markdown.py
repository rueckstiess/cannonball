from cannonball import Node, Task, Bullet, Decision, Question, Artefact
import pytest


@pytest.fixture(scope="class")
def task_with_2_subtasks():
    return Node.from_markdown("""
        - [ ] Task 1
            - [ ] Task 2
            - [x] Task 3
        """)


@pytest.fixture(scope="class")
def nested_task_with_bullets():
    return Node.from_markdown(
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
        result = Node.from_markdown("")
        assert result is None

    def test_no_list_markdown(self):
        """Test parsing markdown with no list items."""
        result = Node.from_markdown("This is just text")
        assert result is None

    def test_from_markdown_converts_node_correctly(self):
        """Test that Node.from_markdown converts list items to nodes correctly and handles multiple references."""
        markdown = """
        - [!] Blocked task with refs ^123 [[#^ref1]] [[#^ref2]]
        """
        root = Node.from_markdown(markdown)
        assert isinstance(root, Task)
        assert root.name == "Blocked task with refs ^123 [[#^ref1]] [[#^ref2]]"
        assert root.is_blocked

    def test_multiple_roots(self):
        """Test parsing markdown with multiple root lists to force common root creation."""
        markdown = """
        - Root 1
        
        - Root 2
        """
        roots = Node.from_markdown(markdown)
        assert len(roots) == 2
        assert roots[0].name == "Root 1"
        assert roots[1].name == "Root 2"

    def test_simple_bullet_list(self):
        """Test parsing a simple bullet list."""
        markdown = """
        - Item 1
        - Item 2
        """
        roots = Node.from_markdown(markdown)

        assert isinstance(roots, list)
        assert roots
        assert len(roots) == 2

    def test_mixed_node_types(self):
        """Test parsing mixed node types."""
        markdown = """
        - [ ] Task
            - Bullet
            - [?] Question
                - [D] Decision
                - [A] Artefact
        """
        root = Node.from_markdown(markdown)

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

        artefact = question.children[1]
        assert isinstance(artefact, Artefact)
        assert artefact.name == "Artefact"


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
