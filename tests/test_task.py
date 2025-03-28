from cannonball import Task


# @pytest.fixture()
# def single_task():
#     return Node.from_markdown("""
#         - [ ] Task
#         """)


# class TestSingleTask:
#     def test_task_init(self, single_task):
#         assert isinstance(single_task, Task)
#         assert single_task.state == NodeState.OPEN
#         assert single_task.name == "Task"
#         assert single_task.parent is None


# @pytest.fixture()
# def task_with_decision():
#     return Node.from_markdown("""
#         - [ ] Task
#             - [D] Decision
#         """)


# @pytest.fixture()
# def task_with_decision_and_subtasks():
#     return Node.from_markdown("""
#         - [ ] Task
#             - [D] Decision
#                 - [ ] Option 1
#                 - [x] Option 2
#         """)


# class TestTaskWithDecision:
#     def test_task_with_decision(self, task_with_decision):
#         task = task_with_decision

#         assert isinstance(task, Task)
#         assert task.state == NodeState.OPEN
#         assert task.name == "Task"
#         assert task.parent is None

#         # Task cannot be completed because of open decision
#         assert task.complete() is False
#         assert task.state == NodeState.OPEN

#         # Check the child is a Decision
#         decision = task.find_by_name("Decision")
#         assert isinstance(decision, Decision)
#         assert decision.state == NodeState.OPEN
#         assert decision.parent == task_with_decision

#         # set decision to COMPLETED, should propagate to task
#         decision.state = NodeState.COMPLETED
#         assert task.state == NodeState.COMPLETED

#         # set decision to BLOCKED, should propagate to task
#         decision.state = NodeState.BLOCKED
#         assert task.state == NodeState.BLOCKED

#     def test_task_with_decision_and_subtasks(self, task_with_decision_and_subtasks):
#         task = task_with_decision_and_subtasks
#         decision = task.find_by_name("Decision")
#         option_1 = task.find_by_name("Option 1")
#         option_2 = task.find_by_name("Option 2")

#         assert task.state == NodeState.OPEN
#         assert decision.state == NodeState.OPEN

#         # make decision for option 1
#         decision.decide(option_1)
#         assert decision.state == NodeState.COMPLETED
#         # the decision was completed, but the subtask is still open
#         assert task.state == NodeState.OPEN

#         # make decision for option 2
#         decision.decide(option_2)
#         assert decision.state == NodeState.COMPLETED
#         # the decision was completed, and the subtask is also complete
#         assert task.state == NodeState.COMPLETED

#         # recompute decision state should be a no-op
#         decision._recompute_state()
#         # decision should remain the same
#         assert decision.decision == option_2
#         assert decision.state == NodeState.COMPLETED

#         # now reopen option_2
#         assert option_2.reopen() is True
#         assert option_2.state == NodeState.OPEN
#         # decision should remain the same
#         assert decision.decision == option_2
#         assert decision.state == NodeState.COMPLETED
#         # but the task should now be open, inherited from option_2
#         assert task.state == NodeState.OPEN


# @pytest.fixture()
# def task_with_bullet():
#     return Node.from_markdown("""
#         - [ ] Task
#             - Bullet
#         """)


# class TestTaskWithBullet:
#     def test_task_with_bullet(self, task_with_bullet):
#         task = task_with_bullet
#         bullet = task.find_by_name("Bullet")

#         assert isinstance(task, Task)
#         assert task.state == NodeState.OPEN
#         assert task.name == "Task"
#         assert task.parent is None

#         # Task can be completed as leaf bullet has COMPLETED state
#         assert bullet.state == NodeState.COMPLETED
#         assert task.complete() is True
#         assert task.state == NodeState.COMPLETED


class TestTask:
    def test_task_init(self):
        task = Task("Task")
        assert isinstance(task, Task)
        assert task.is_blocked is False
        assert task.is_completed is False
        assert task.auto_resolve is True
        assert task.name == "Task"
        assert task.parent is None
        assert task.marker == " "

    def test_completed_task_init(self):
        task = Task("Task", completed=True)
        assert isinstance(task, Task)
        assert task.is_blocked is False
        assert task.is_completed is True
        assert task.marker == "x"

    def test_blocked_task_init(self):
        task = Task("Task", blocked=True)
        assert isinstance(task, Task)
        assert task.is_blocked is True
        assert task.is_completed is False
        assert task.marker == "!"

    def test_task_with_children(self):
        task = Task("Task")
        child1 = Task("Child 1", parent=task)
        child2 = Task("Child 2", parent=task)

        assert len(task.children) == 2
        assert task.children[0] == child1
        assert task.children[1] == child2

        assert task.is_blocked is False
        assert task.is_completed is False

    def test_task_with_completed_children(self):
        task = Task("Task")
        child1 = Task("Child 1", completed=True, parent=task)
        child2 = Task("Child 2", completed=True, parent=task)

        assert len(task.children) == 2
        assert task.children[0] == child1
        assert task.children[1] == child2

        assert task.is_blocked is False
        assert task.is_completed is True

        # mark child1 as incomplete
        child1.reopen()

        assert task.is_blocked is False
        assert task.is_completed is False

        # mark both children blocked
        child1.block()
        child2.block()
        assert task.is_blocked is True
        assert task.is_completed is False
        assert task.auto_resolve is True

    def test_auto_resolve_leaf_task(self):
        task = Task("Task")
        Task("Child 1", parent=task, completed=True)
        Task("Child 2", parent=task, completed=True)

        assert task.is_completed is True

        # removing children should auto-resolve to False
        task.children = []
        assert task.is_completed is False

    def test_disable_auto_resolve_leaf_task(self):
        task = Task("Task")
        assert task.complete() is True
        assert task.is_completed is True
        assert task.auto_resolve is False

        assert task.reopen() is True
        assert task.is_completed is False

        # adding children doesn't change state since auto-resolve is disabled
        child1 = Task("Child 1", parent=task, completed=True)
        child2 = Task("Child 2", parent=task, completed=True)
        assert task.is_completed is False

        # can't manually reopen now
        assert task.reopen() is False

        # removing children, task remains incomplete (no auto-resolve)
        task.children = []
        assert task.is_completed is False

        # adding children back
        task.children = [child1, child2]
        assert task.is_completed is False

        # enable auto-resolve again, now it should resolve
        task.auto_resolve = True
        assert task.is_completed is True

    def test_task_block_non_leaf(self):
        """Test blocking a non-leaf task."""
        parent = Task("Parent Task")
        Task("Child Task", parent=parent)
        result = parent.block()
        assert result is False

    def test_task_unblock_non_leaf(self):
        """Test unblocking a non-leaf task."""
        parent = Task("Parent Task", blocked=True)
        Task("Child Task", parent=parent)
        result = parent.unblock()
        assert result is False

    def test_task_complete_non_leaf(self):
        """Test completing a non-leaf task."""
        parent = Task("Parent Task")
        Task("Child Task", parent=parent)
        result = parent.complete()
        assert result is False

    def test_task_reopen_non_leaf(self):
        """Test reopening a non-leaf task."""
        parent = Task("Parent Task", completed=True)
        Task("Child Task", parent=parent)
        result = parent.reopen()
        assert result is False

    def test_task_block_already_blocked(self):
        """Test blocking an already blocked task."""
        task = Task("Test Task", blocked=True)
        result = task.block()
        assert result is False

    def test_task_unblock_already_unblocked(self):
        """Test unblocking an already unblocked task."""
        task = Task("Test Task")
        result = task.unblock()
        assert result is False

    def test_task_complete_already_completed(self):
        """Test completing an already completed task."""
        task = Task("Test Task", completed=True)
        result = task.complete()
        assert result is False

    def test_task_reopen_not_completed(self):
        """Test reopening a task that is not completed."""
        task = Task("Test Task")
        result = task.reopen()
        assert result is False

    def test_task_leaf_state(self):
        """Test the _leaf_state method of Task."""
        # Test with auto_resolve=True
        task1 = Task("Task 1", auto_resolve=True)
        completed, blocked = task1._leaf_state()
        assert completed is False
        assert blocked is False

        # Test with auto_resolve=False
        task2 = Task("Task 2", auto_resolve=False, completed=True, blocked=False)
        completed, blocked = task2._leaf_state()
        assert completed is True
        assert blocked is False
