from cannonball.nodes import (
    Task,
    Bullet,
    parse_markdown,
    NodeState,
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
    return parse_markdown("""
        - [ ] Task 1
            - [ ] Task 2
                - Bullet 1
                - Bullet 2
            - [x] Task 3
        """)


class TestMarkdown:
    def test_basic_markdown_parsing(self, task_with_2_subtasks):
        """Test basic markdown parsing."""
        task1 = task_with_2_subtasks

        assert isinstance(task1, Task)
        assert len(task1.children) == 2
        assert task1.state == NodeState.IN_PROGRESS

        task2 = task1.find_by_name("Task 2")
        assert isinstance(task2, Task)
        assert task2.state == NodeState.OPEN

        task3 = task1.find_by_name("Task 3")
        assert isinstance(task3, Task)
        assert task3.state == NodeState.COMPLETED

    def test_nested_task_with_bullets(self, nested_task_with_bullets):
        """Test nested task with bullets."""
        task1 = nested_task_with_bullets

        assert isinstance(task1, Task)
        assert len(task1.children) == 2
        assert task1.state == NodeState.IN_PROGRESS

        task2 = task1.find_by_name("Task 2")
        assert isinstance(task2, Task)
        assert len(task2.children) == 2
        assert task2.state == NodeState.OPEN

        bullet1 = task2.find_by_name("Bullet 1")
        assert isinstance(bullet1, Bullet)
        assert bullet1.state == NodeState.OPEN

        bullet2 = task2.find_by_name("Bullet 2")
        assert isinstance(bullet2, Bullet)
        assert bullet2.state == NodeState.OPEN
