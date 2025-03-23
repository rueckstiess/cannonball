from cannonball.nodes import Node, Task, Question, Bullet, parse_markdown, NodeState
import pytest


@pytest.fixture(scope="class")
def root():
    return parse_markdown("""
        - [ ] Task 1
            - [ ] Task 2
            - [x] Task 3
        """)


class TestMarkdown:
    def test_basic_markdown_parsing(self, root):
        """Test basic markdown parsing."""

        assert isinstance(root, Task)
        assert len(root.children) == 2
        assert root.state == NodeState.IN_PROGRESS

        task2 = root.find_by_name("Task 2")
        assert isinstance(task2, Task)
        assert task2.state == NodeState.OPEN

        task3 = root.find_by_name("Task 3")
        assert isinstance(task3, Task)
        assert task3.state == NodeState.COMPLETED
