from cannonball.nodes import (
    Node,
    Task,
    Decision,
    Bullet,
    parse_markdown,
)
import pytest


class TestDecision:
    def test_decision_init(self):
        decision = Decision("Decision")
        assert isinstance(decision, Decision)
        assert decision.auto_decide is False
        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.name == "Decision"
        assert decision.parent is None

    def test_decision_init_blocked(self):
        decision = Decision("Decision", blocked=True)
        assert decision.auto_decide is False
        assert decision.is_completed is False
        assert decision.is_blocked is True

    def test_decision_init_completed(self):
        decision = Decision("Decision", completed=True)
        assert decision.auto_decide is False
        assert decision.is_completed is True
        assert decision.is_blocked is False

    def test_decision_init_auto_decide(self):
        decision = Decision("Decision", auto_decide=True)
        assert decision.auto_decide is True
        assert decision.is_completed is False
        # a decision with no options is blocked
        assert decision.is_blocked is True

    def test_decision_init_auto_decide_with_options(self):
        option1 = Bullet("Option 1")
        option2 = Bullet("Option 2")
        decision = Decision("Decision", auto_decide=True, children=[option1, option2])

        assert decision.auto_decide is True
        assert decision.is_completed is False
        # a decision with multiple options is blocked
        assert decision.is_blocked is False

    def test_decision_init_auto_decide_with_one_option(self):
        decision = Decision("Decision", auto_decide=True)
        option1 = Bullet("Option 1", parent=decision)
        assert decision.auto_decide is True
        assert decision.is_completed is True
        assert decision.is_blocked is False
        assert decision.decision == option1
        assert decision.is_decided is True

    def test_decision_init_with_blocked_options(self):
        decision = Decision("Decision", auto_decide=True)
        option1 = Task("Option 1", blocked=True, parent=decision)
        Task("Option 2", blocked=True, parent=decision)
        assert decision.auto_decide is True
        assert decision.is_completed is False
        assert decision.is_blocked is True
        assert decision.decision is None
        assert decision.is_decided is False

        # unblock one option
        assert option1.unblock() is True
        assert decision.is_decided is True
        assert decision.is_completed is True
        assert decision.is_blocked is False
        assert decision.decision == option1


@pytest.fixture()
def decision():
    return parse_markdown("""
        - [D] Decision
        """)


@pytest.fixture()
def decision_with_bullet():
    return parse_markdown("""
        - [D] Decision
            - I'm the only option
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


class TestDecisionFixtures:
    def test_decision_with_single_bullet(self, decision_with_bullet: Node):
        decision = decision_with_bullet
        bullet = decision.find_by_name("I'm the only option")

        assert decision.auto_decide is False
        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.decision is None

        decision.auto_decide = True
        assert decision.is_completed is True
        assert decision.is_blocked is False
        assert decision.decision is bullet

    def test_decision_with_2_bullets(self, decision_with_2_bullets: Node):
        decision = decision_with_2_bullets
        assert len(decision.get_options()) == 2

        bullet_1 = decision.find_by_name("I need to make a decision here")
        decision.find_by_name("Another bullet")

        # make manual decision (auto-decidable is False)
        decision.decide(bullet_1)
        assert decision.is_completed is True
        assert decision.decision == bullet_1
        assert decision.auto_decide is False

        # unset the decision
        decision.decide(None)
        assert decision.is_completed is False
        assert decision.decision is None

    def test_auto_decision_with_2_bullets(self, decision_with_2_bullets: Node):
        decision = decision_with_2_bullets
        decision.auto_decide = True
        assert decision.is_decided is False
        assert decision.is_completed is False
        assert decision.is_blocked is False

        bullet_1 = decision.find_by_name("I need to make a decision here")
        decision.find_by_name("Another bullet")

        # make manual decision (disables auto_decide)
        decision.decide(bullet_1)
        assert decision.is_decided is True
        assert decision.is_completed is True
        assert decision.decision == bullet_1
        assert decision.auto_decide is False

        # turn auto-decidable back on
        decision.auto_decide = True
        assert decision.is_decided is False
        assert decision.is_completed is False
        assert decision.decision is None
        assert decision.auto_decide is True

        # unset the decision
        decision.decide(None)
        assert decision.is_decided is False
        assert decision.is_completed is False
        assert decision.decision is None
        assert decision.auto_decide is False

    def test_auto_decision_with_task(self, decision_with_task: Node):
        decision = decision_with_task
        assert decision.is_decided is False

        task = decision.find_by_name("Task")
        assert isinstance(task, Task)
        assert task.is_completed is False
        assert task.parent == decision

        # decision has one viable option but cannot be auto-decided
        assert decision.decision is None
        assert decision.is_completed is False

        # decision is now auto-decidable and has one viable option
        decision.auto_decide = True
        assert decision.is_completed is True
        assert decision.decision == task

        # now block the task
        task.block()
        assert decision.is_blocked is True
        assert decision.is_completed is False
        assert decision.decision is None

    def test_decision_with_tasks(self, decision_with_tasks: Node):
        decision = decision_with_tasks
        decision.auto_decide = False

        task_1 = decision.find_by_name("Task 1")
        task_2 = decision.find_by_name("Task 2")
        task_3 = decision.find_by_name("Task 3")

        assert decision.is_completed is False
        assert task_1.is_completed is False
        assert task_2.is_completed is False
        assert task_3.is_completed is False

        task_1.block()
        # the decision still has 2 viable options and remains open
        assert decision.is_completed is False
        assert decision.is_blocked is False

        task_2.block()
        # the decision now has exactly one viable option but is not auto-decidable
        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.decision is None

        task_3.block()
        # the decision now has three blocked children and should be blocked
        assert decision.is_blocked is True
        assert decision.decision is None

        task_1.unblock()
        # now the decision has one viable option but is not auto-decidable
        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.decision is None

        task_2.unblock()
        # the decision has two viable options
        assert decision.is_completed is False
        assert decision.decision is None

        # decide manually
        decision.decide(task_1)
        assert decision.is_completed is True
        assert decision.decision == task_1

        # shouldn't be able to decide on a cancelled or blocked task
        assert decision.decide(task_3) is False
        assert decision.decision == task_1
        assert decision.is_completed is True

    def test_auto_decision_with_tasks(self, decision_with_tasks):
        decision = decision_with_tasks
        decision.auto_decide = True

        task_1 = decision.find_by_name("Task 1")
        task_2 = decision.find_by_name("Task 2")
        task_3 = decision.find_by_name("Task 3")

        assert decision.is_completed is False
        assert task_1.is_completed is False
        assert task_2.is_completed is False
        assert task_3.is_completed is False

        task_1.block()
        # the decision still has 2 viable options and remains open
        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.decision is None

        task_2.block()
        # the decision now has exactly one viable option and should be completed
        assert decision.is_completed is True
        assert decision.decision == task_3

        task_3.block()
        # the decision now has three blocked children and should be blocked
        assert decision.is_completed is False
        assert decision.is_blocked is True
        assert decision.decision is None

        task_1.unblock()
        # now the decision has one viable option and should be completed
        assert decision.is_completed is True
        assert decision.is_blocked is False
        assert decision.decision == task_1

        task_2.unblock()
        # since the decision auto-decides and we have 2 options again, it is OPEN
        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.decision is None

        task_1.parent = None
        # now that task_1 is removed, the decision should be complete again
        assert decision.is_completed is True
        assert decision.decision == task_2

        task_2.parent = None
        # now the decision has 1 blocked option (option 3) and is blocked
        assert decision.is_blocked is True
        assert decision.is_completed is False
        assert decision.decision is None

        task_3.unblock()
        # now the decision has 1 viable option (option 2) and is completed
        assert decision.is_completed is True
        assert decision.is_blocked is False
        assert decision.decision == task_3

    def test_nested_decisions(self, nested_decisions):
        decision = nested_decisions
        option_a = decision.find_by_name("Option A")
        nested_decision = decision.find_by_name("Nested Decision")
        option_b1 = decision.find_by_name("Option B1")
        option_b2 = decision.find_by_name("Option B2")

        # decisions and tasks are in open state
        assert decision.is_completed is False
        assert nested_decision.is_completed is False
        assert option_a.is_completed is False
        assert option_b1.is_completed is False
        assert option_b2.is_completed is False

        # make manual decision on the nested decision
        decision.decide(nested_decision)
        assert nested_decision.is_completed is False
        assert decision.is_completed is True

        # now block both nested options, decision should be open again
        option_b1.block()
        option_b2.block()
        assert nested_decision.is_blocked is True
        assert decision.is_completed is False
        assert decision.decision is None

    def test_auto_nested_decisions(self, nested_decisions):
        decision = nested_decisions
        decision.auto_decide = True
        option_a = decision.find_by_name("Option A")
        nested_decision = decision.find_by_name("Nested Decision")
        option_b1 = decision.find_by_name("Option B1")
        option_b2 = decision.find_by_name("Option B2")

        # decisions and tasks are in open state
        assert decision.is_completed is False
        assert nested_decision.is_completed is False
        assert option_a.is_completed is False
        assert option_b1.is_completed is False
        assert option_b2.is_completed is False

        # now block both nested options, decision should be option A
        option_b1.block()
        option_b2.block()
        assert nested_decision.is_blocked is True
        assert decision.is_completed is True
        assert decision.decision == option_a

        # unblock option B1, decision should be open again
        option_b1.unblock()
        assert nested_decision.is_completed is False
        assert decision.is_completed is False


class TestDecisionWithOtherOptions:
    def test_decision_with_task(self, decision_with_task):
        decision = decision_with_task
        task = decision.find_by_name("Task")

        # auto-decidable decision with one viable option
        decision.auto_decide = True
        assert decision.is_completed is True
        assert decision.is_blocked is False
        assert decision.decision == task

        # now change to different options
        bullet_with_options = parse_markdown("""
            - Bullet
                - [ ] Option 1
                - [ ] Option 2
            """)

        decision.set_options(bullet_with_options.children)

        assert decision.is_completed is False
        assert decision.is_blocked is False
        assert decision.decision is None
        assert decision.get_options() == list(bullet_with_options.children)
