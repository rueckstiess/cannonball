from cannonball.nodes import (
    Task,
    Decision,
    Bullet,
    parse_markdown,
    NodeState,
)
import pytest


@pytest.fixture()
def bullet():
    return parse_markdown("""
        - Bullet
        """)


@pytest.fixture()
def bullet_with_child():
    return parse_markdown("""
        - Bullet
            - Nested bullet
        """)


@pytest.fixture()
def bullet_with_task():
    return parse_markdown("""
        - Bullet
            - [ ] Task
        """)


@pytest.fixture()
def bullet_with_decision():
    return parse_markdown("""
        - Bullet
            - [D] Decision
        """)


@pytest.fixture()
def deep_bullet_with_task():
    return parse_markdown("""
        - Bullet 1
            - Bullet 2
                - Bullet 3
                    - [ ] Task
        """)


class TestBullet:
    def test_single_bullet(self, bullet):
        assert isinstance(bullet, Bullet)
        assert bullet.name == "Bullet"
        # leaf bullets are completed
        assert bullet.state == NodeState.COMPLETED

        # leaf bullets cannot be set to other states
        with pytest.raises(ValueError, match="Bullet state cannot be changed manually"):
            bullet.state = NodeState.IN_PROGRESS
        with pytest.raises(ValueError, match="Bullet state cannot be changed manually"):
            bullet.state = NodeState.OPEN
        with pytest.raises(ValueError, match="Bullet state cannot be changed manually"):
            bullet.state = NodeState.CANCELLED
        with pytest.raises(ValueError, match="Bullet state cannot be changed manually"):
            bullet.state = NodeState.BLOCKED

    def test_nested_bullet(self, bullet_with_child):
        parent = bullet_with_child
        child = parent.find_by_name("Nested bullet")

        assert isinstance(parent, Bullet)
        assert isinstance(child, Bullet)

        assert parent.state == NodeState.COMPLETED
        assert child.state == NodeState.COMPLETED

    def test_bullet_with_task(self, bullet_with_task):
        bullet = bullet_with_task
        task = bullet.find_by_name("Task")

        assert isinstance(bullet, Bullet)
        assert isinstance(task, Task)

        # bullet inherits state from child
        assert bullet.state == NodeState.OPEN
        # child task is open
        assert task.state == NodeState.OPEN

        # now change task state
        task.state = NodeState.COMPLETED
        assert bullet.state == NodeState.COMPLETED

        task.state = NodeState.CANCELLED
        assert bullet.state == NodeState.CANCELLED

        task.state = NodeState.BLOCKED
        assert bullet.state == NodeState.BLOCKED

        task.state = NodeState.IN_PROGRESS
        assert bullet.state == NodeState.IN_PROGRESS

    def test_remove_task_from_bullet(self, bullet_with_task):
        bullet = bullet_with_task
        task = bullet.find_by_name("Task")

        assert bullet.state == NodeState.OPEN
        assert task.state == NodeState.OPEN

        # remove task from bullet
        bullet.remove_child(task)
        assert bullet.state == NodeState.COMPLETED

    def test_bullet_with_decision(self, bullet_with_decision):
        bullet = bullet_with_decision
        decision = bullet.find_by_name("Decision")

        assert isinstance(bullet, Bullet)
        assert isinstance(decision, Decision)

        # bullet inherits state from child
        assert bullet.state == NodeState.OPEN
        # child decision is open
        assert decision.state == NodeState.OPEN

        # now change decision state
        decision.state = NodeState.COMPLETED
        assert bullet.state == NodeState.COMPLETED

        with pytest.raises(ValueError):
            decision.state = NodeState.CANCELLED
        assert bullet.state == NodeState.COMPLETED

        decision.state = NodeState.BLOCKED
        assert bullet.state == NodeState.BLOCKED

        with pytest.raises(ValueError):
            decision.state = NodeState.IN_PROGRESS
        assert bullet.state == NodeState.BLOCKED

    def test_deeply_nested_bullet(self, deep_bullet_with_task):
        bullet = deep_bullet_with_task
        task = bullet.find_by_name("Task")

        assert bullet.state == NodeState.OPEN
        assert task.state == NodeState.OPEN

        task.state = NodeState.COMPLETED
        assert bullet.state == NodeState.COMPLETED
        task.state = NodeState.CANCELLED
        assert bullet.state == NodeState.CANCELLED
        task.state = NodeState.BLOCKED
        assert bullet.state == NodeState.BLOCKED
        task.state = NodeState.IN_PROGRESS
        assert bullet.state == NodeState.IN_PROGRESS
