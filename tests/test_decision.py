from cannonball.nodes import (
    Task,
    Decision,
    Bullet,
    parse_markdown,
    NodeState,
)
import pytest


@pytest.fixture(scope="class")
def open_decision():
    return parse_markdown("""
        - [D] Open Decision
        """)


@pytest.fixture(scope="class")
def decision_with_bullet():
    return parse_markdown("""
        - [D] Decision
            - I need to make a decision here
        """)


@pytest.fixture(scope="class")
def decision_with_2_bullets():
    return parse_markdown("""
        - [D] Decision
            - I need to make a decision here
            - Another bullet
        """)


@pytest.fixture(scope="class")
def decision_with_task():
    return parse_markdown("""
        - [D] Decision
            - [ ] Task
        """)


@pytest.fixture(scope="class")
def decision_with_tasks():
    return parse_markdown("""
        - [D] Decision
            - [ ] Task 1
            - [ ] Task 2
            - [ ] Task 3
        """)


class TestDecision:
    def test_decision_init(self, open_decision):
        assert isinstance(open_decision, Decision)
        assert open_decision.state == NodeState.OPEN
        assert open_decision.name == "Open Decision"
        assert open_decision.parent is None

    def test_decision_with_single_bullet(self, decision_with_bullet):
        decision = decision_with_bullet
        assert decision.state == NodeState.OPEN

        bullet = decision.find_by_name("I need to make a decision here")
        assert isinstance(bullet, Bullet)
        assert bullet.state == NodeState.OPEN
        assert bullet.parent == decision

    def test_decision_with_2_bullets(self, decision_with_2_bullets):
        decision = decision_with_2_bullets
        assert decision.state == NodeState.OPEN

        bullet_1 = decision.find_by_name("I need to make a decision here")

        assert isinstance(bullet_1, Bullet)
        assert bullet_1.state == NodeState.OPEN
        assert bullet_1.parent == decision

        bullet_2 = decision.find_by_name("Another bullet")
        assert isinstance(bullet_2, Bullet)
        assert bullet_2.state == NodeState.OPEN
        assert bullet_2.parent == decision

    def test_decision_with_task(self, decision_with_task):
        decision = decision_with_task
        assert decision.state == NodeState.OPEN

        task = decision.find_by_name("Task")
        assert isinstance(task, Task)
        assert task.state == NodeState.OPEN
        assert task.parent == decision

        # now complete the task
        task.complete()
        assert task.state == NodeState.COMPLETED

        # the decision now has exactly one completed child and should be completed
        assert decision.state == NodeState.COMPLETED

    def test_decision_with_tasks(self, decision_with_tasks):
        decision = decision_with_tasks
        task_1 = decision.find_by_name("Task 1")
        task_2 = decision.find_by_name("Task 2")
        task_3 = decision.find_by_name("Task 3")

        assert decision.state == NodeState.OPEN
        assert task_1.state == NodeState.OPEN
        assert task_2.state == NodeState.OPEN
        assert task_3.state == NodeState.OPEN

        task_1.complete()
        # the decision now has exactly one completed child and should be completed
        assert decision.state == NodeState.COMPLETED

        task_2.complete()
        # the decision now has two completed children and should be in progress
        assert decision.state == NodeState.IN_PROGRESS

        task_3.complete()
        # the decision now has three completed children and should be in progress
        assert decision.state == NodeState.IN_PROGRESS

        task_1.block()
        # even though task_1 is blocked, the decision should still be in progress
        assert decision.state == NodeState.IN_PROGRESS

        task_2.block()
        # now that task_2 is blocked, the decision should be completed because it has one completed child
        assert decision.state == NodeState.COMPLETED

        task_3.block()
        # now that task_3 is blocked, the decision should be blocked
        assert decision.state == NodeState.BLOCKED

        task_3.cancel()
        # now that task_3 is cancelled, the decision should be open as no children are in progress or done
        assert decision.state == NodeState.OPEN
