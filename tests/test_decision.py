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


@pytest.fixture()
def nested_decisions():
    return parse_markdown("""
        - [D] Decision
            - [ ] Option A
            - [D] Nested Decision
                - [ ] Option B1
                - [ ] Option B2
        """)


@pytest.fixture()
def decision_with_sibling_options():
    return parse_markdown("""
    - Root
        - [D] Decision
        - Option 1
        - Option 2
    """)


class TestDecision:
    def test_decision_init(self, open_decision):
        assert isinstance(open_decision, Decision)
        assert open_decision.state == NodeState.OPEN
        assert open_decision.name == "Open Decision"
        assert open_decision.parent is None

    def test_valid_decision_states(self, open_decision):
        assert open_decision.state == NodeState.OPEN
        open_decision.state = NodeState.COMPLETED
        assert open_decision.state == NodeState.COMPLETED
        open_decision.state = NodeState.BLOCKED
        assert open_decision.state == NodeState.BLOCKED

        with pytest.raises(ValueError, match="Invalid Decision state 'IN_PROGRESS'"):
            open_decision.state = NodeState.IN_PROGRESS
        with pytest.raises(ValueError, match="Invalid Decision state 'CANCELLED'"):
            open_decision.state = NodeState.CANCELLED

    def test_decision_with_single_bullet(self, decision_with_bullet):
        decision = decision_with_bullet
        assert decision.state == NodeState.OPEN

        bullet = decision.find_by_name("I need to make a decision here")
        assert isinstance(bullet, Bullet)
        assert bullet.state == NodeState.COMPLETED
        assert bullet.parent == decision

    def test_decision_with_2_bullets(self, decision_with_2_bullets):
        decision = decision_with_2_bullets
        assert decision.state == NodeState.OPEN

        bullet_1 = decision.find_by_name("I need to make a decision here")
        assert isinstance(bullet_1, Bullet)
        assert bullet_1.state == NodeState.COMPLETED
        assert bullet_1.parent == decision

        bullet_2 = decision.find_by_name("Another bullet")
        assert isinstance(bullet_2, Bullet)
        assert bullet_2.state == NodeState.COMPLETED
        assert bullet_2.parent == decision

        # make manual decision (auto-decidable is False)
        decision.decide(bullet_1)
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == bullet_1
        assert decision.auto_decide is False

        # unset the decision
        decision.decide(None)
        assert decision.state == NodeState.OPEN
        assert decision.decision is None

    def test_auto_decision_with_2_bullets(self, decision_with_2_bullets):
        decision = decision_with_2_bullets
        decision.auto_decide = True
        assert decision.state == NodeState.OPEN

        bullet_1 = decision.find_by_name("I need to make a decision here")
        assert isinstance(bullet_1, Bullet)
        assert bullet_1.state == NodeState.COMPLETED
        assert bullet_1.parent == decision

        bullet_2 = decision.find_by_name("Another bullet")
        assert isinstance(bullet_2, Bullet)
        assert bullet_2.state == NodeState.COMPLETED
        assert bullet_2.parent == decision

        # make manual decision (disables auto_decide)
        decision.decide(bullet_1)
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == bullet_1
        assert decision.auto_decide is False

        # turn auto-decidable back on
        decision.auto_decide = True
        assert decision.state == NodeState.OPEN
        assert decision.decision is None
        assert decision.auto_decide is True

        # unset the decision
        decision.decide(None)
        assert decision.state == NodeState.OPEN
        assert decision.decision is None
        assert decision.auto_decide is False

    def test_auto_decision_with_task(self, decision_with_task):
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
        decision.auto_decide = True
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
        decision.auto_decide = False

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
        decision.auto_decide = True

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

    def test_nested_decisions(self, nested_decisions):
        decision = nested_decisions
        option_a = decision.find_by_name("Option A")
        nested_decision = decision.find_by_name("Nested Decision")
        option_b1 = decision.find_by_name("Option B1")
        option_b2 = decision.find_by_name("Option B2")

        # decisions and tasks are in open state
        assert decision.state == NodeState.OPEN
        assert nested_decision.state == NodeState.OPEN
        assert option_a.state == NodeState.OPEN
        assert option_b1.state == NodeState.OPEN
        assert option_b2.state == NodeState.OPEN

        # # make manual decision on the nested decision
        decision.decide(nested_decision)
        assert nested_decision.state == NodeState.OPEN
        assert decision.state == NodeState.COMPLETED

        # now block both nested options, decision should be open again
        option_b1.block()
        option_b2.block()
        assert nested_decision.state == NodeState.BLOCKED
        assert decision.state == NodeState.OPEN

    def test_auto_nested_decisions(self, nested_decisions):
        decision = nested_decisions
        decision.auto_decide = True
        option_a = decision.find_by_name("Option A")
        nested_decision = decision.find_by_name("Nested Decision")
        option_b1 = decision.find_by_name("Option B1")
        option_b2 = decision.find_by_name("Option B2")

        # decisions and tasks are in open state
        assert decision.state == NodeState.OPEN
        assert nested_decision.state == NodeState.OPEN
        assert option_a.state == NodeState.OPEN
        assert option_b1.state == NodeState.OPEN
        assert option_b2.state == NodeState.OPEN

        # now block both nested options, decision should be option A
        option_b1.block()
        option_b2.block()
        assert nested_decision.state == NodeState.BLOCKED
        assert decision.state == NodeState.COMPLETED
        assert decision.decision == option_a

        # unblock option B1, decision should be open again
        option_b1.state = NodeState.OPEN
        assert nested_decision.state == NodeState.OPEN
        assert decision.state == NodeState.OPEN

    def test_decision_with_sibling_options(self, decision_with_sibling_options):
        root = decision_with_sibling_options
        decision = root.find_by_name("Decision")
        option_1 = root.find_by_name("Option 1")
        option_2 = root.find_by_name("Option 2")

        assert decision.state == NodeState.OPEN
        assert option_1.state == NodeState.COMPLETED
        assert option_2.state == NodeState.COMPLETED

        # make manual decision on option 1 (should not change the state because option 1 is not a child of decision)
        assert decision.decide(option_1) is False
        assert decision.state == NodeState.OPEN
        assert decision.decision is None
