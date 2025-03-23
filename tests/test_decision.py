from cannonball.nodes import (
    Task,
    Decision,
    Bullet,
    parse_markdown,
    NodeState,
)
import pytest


@pytest.fixture()
def open_decision():
    return parse_markdown("""
        - [D] Open Decision
        """)


@pytest.fixture()
def decision_with_bullet():
    return parse_markdown("""
        - [D] Decision
            - I need to make a decision here
        """)


@pytest.fixture()
def decision_with_2_bullets():
    return parse_markdown("""
        - [D] Decision
            - I need to make a decision here
            - Another bullet
        """)


@pytest.fixture()
def decision_with_task():
    return parse_markdown("""
        - [D] Decision
            - [ ] Task
        """)


@pytest.fixture()
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

    def test_aut_decision_with_task(self, decision_with_task):
        decision = decision_with_task
        assert decision.state == NodeState.OPEN

        task = decision.find_by_name("Task")
        assert isinstance(task, Task)
        assert task.state == NodeState.OPEN
        assert task.parent == decision

        # decision has one viable option but cannot be auto-decided
        assert decision.decision is None
        assert decision.state == NodeState.OPEN

        # decision is now auto-decidable and has one viable option
        decision.auto_decidable = True
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == task

        # now block the task
        task.block()
        assert decision.state == NodeState.BLOCKED
        assert decision.decision is None

        # now cancel the task
        task.cancel()
        assert decision.state == NodeState.BLOCKED
        assert decision.decision is None

    def test_decision_with_tasks(self, decision_with_tasks):
        decision = decision_with_tasks
        decision.auto_decidable = False

        task_1 = decision.find_by_name("Task 1")
        task_2 = decision.find_by_name("Task 2")
        task_3 = decision.find_by_name("Task 3")

        assert decision.state == NodeState.OPEN
        assert task_1.state == NodeState.OPEN
        assert task_2.state == NodeState.OPEN
        assert task_3.state == NodeState.OPEN

        task_1.block()
        # the decision still has 2 viable options and remains open
        assert decision.state == NodeState.OPEN

        task_2.block()
        # the decision now has exactly one viable option but is not auto-decidable
        assert decision.state == NodeState.OPEN
        assert decision.decision is None

        task_3.block()
        # the decision now has three blocked children and should be blocked
        assert decision.state == NodeState.BLOCKED
        assert decision.decision is None

        task_1.state = NodeState.OPEN
        # now the decision has one viable option but is not auto-decidable
        assert decision.state == NodeState.OPEN
        assert decision.decision is None

        task_2.state = NodeState.OPEN
        # the decision has two viable options
        assert decision.state == NodeState.OPEN
        assert decision.decision is None

        # decide manually
        decision.decide(task_1)
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == task_1

        # now cancel the task
        task_1.cancel()
        assert decision.state == NodeState.OPEN
        assert decision.decision is None

        # shouldn't be able to decide on a cancelled or blocked task
        assert decision.decide(task_1) is False
        assert decision.decide(task_3) is False
        assert decision.decision is None
        assert decision.state == NodeState.OPEN

        # decide on the only remaining task
        decision.decide(task_2)
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == task_2

    def test_auto_decision_with_tasks(self, decision_with_tasks):
        decision = decision_with_tasks
        decision.auto_decidable = True

        task_1 = decision.find_by_name("Task 1")
        task_2 = decision.find_by_name("Task 2")
        task_3 = decision.find_by_name("Task 3")

        assert decision.state == NodeState.OPEN
        assert task_1.state == NodeState.OPEN
        assert task_2.state == NodeState.OPEN
        assert task_3.state == NodeState.OPEN

        task_1.block()
        # the decision still has 2 viable options and remains open
        assert decision.state == NodeState.OPEN

        task_2.block()
        # the decision now has exactly one viable option and should be completed
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == task_3

        task_3.block()
        # the decision now has three blocked children and should be blocked
        assert decision.state == NodeState.BLOCKED
        assert decision.decision is None

        task_1.complete()
        # now the decision has one viable option and should be completed
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == task_1

        task_2.complete()
        # since the decision auto-decides and we have 2 options again, it is OPEN
        assert decision.state == NodeState.OPEN
        assert decision.decision is None

        task_1.cancel()
        # now that task_1 is cancelled, the decision should be complete again
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == task_2

        task_2.cancel()
        # now the decision has 2 cancelled and 1 blocked option and is blocked
        assert decision.state == NodeState.BLOCKED
        assert decision.decision is None
