from cannonball.nodes import Task, TaskType, Question, Alternative, Goal, Problem, BlockingNode
import pytest

from utils import with_markdown, check_blocking_status, check_node_type, check_task_status


@with_markdown("""\
    - [x] Task 1
      - [ ] Task 2
        - [x] Task 3
""")
class TestBasicTaskGraph:
    @pytest.mark.parametrize(
        "node_name,expected_type,reason",
        [
            ("Task 1", Task, "it's a task"),
            ("Task 2", Task, "it's a task"),
            ("Task 3", Task, "it's a task"),
        ],
    )
    def test_node_types(self, graph_fixture, node_name, expected_type, reason):
        check_node_type(graph_fixture, node_name, expected_type, reason)

    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Task 1", TaskType.COMPLETED, "its marker is x"),
            ("Task 2", TaskType.OPEN, "its marker is empty"),
            ("Task 3", TaskType.COMPLETED, "its marker is x"),
        ],
    )
    def test_task_status(self, graph_fixture, node_name, expected_status, reason):
        check_task_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative
""")
class TestOneAlternative:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "it starts unresolved"),
            ("Alternative", False, "has no blocking children"),
        ],
    )
    def test_blocking_status_before_resolution(self, graph_fixture, node_name, expected_status, reason):
        check_blocking_status(graph_fixture, node_name, expected_status, reason)

    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", False, "was manually resolved"),
            ("Alternative", False, "has no blocking children"),
        ],
    )
    def test_blocking_status_after_resolution(self, graph_fixture, node_name, expected_status, reason):
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True
        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
    - [a] Alternative 2 
""")
class TestSimpleAlternatives:
    @pytest.mark.parametrize(
        "node_name,expected_type,reason",
        [
            ("Question", Question, "it has '?' marker"),
            ("Alternative 1", Alternative, "it has 'a' marker"),
            ("Alternative 2", Alternative, "it has 'a' marker"),
            ("Alternative 2", BlockingNode, "it derives from BlockingNode"),
        ],
    )
    def test_node_types(self, graph_fixture, node_name, expected_type, reason):
        check_node_type(graph_fixture, node_name, expected_type, reason)

    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "it has more than one alternative"),
            ("Alternative 1", False, "it has no blocking children"),
            ("Alternative 2", False, "it has no blocking children"),
        ],
    )
    def test_blocking_status_resolved(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True
        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
    - [a] Alternative 2 
        - [P] Problem    
""")
class TestOneViableAlternative:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", False, "it has only one unblocked alternative"),
            ("Alternative 1", False, "it has no blocking children"),
            ("Alternative 2", True, "it contains a problem"),
            ("Problem", True, "problems are always blocked"),
        ],
    )
    def test_blocking_status_resolved(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True

        # double-check that this updates the graph too, not a copy of the node
        graph = graph_fixture["graph"]
        assert question in graph
        # get question from the graph
        question = [n for n in graph if isinstance(n, Question)][0]
        assert question.is_resolved

        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
        - [P] Problem 1
    - [a] Alternative 2 
        - [P] Problem 2  
""")
class TestNoViableAlternative:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "Should block, has Alternatives but none viable"),
            ("Alternative 1", True, "should be blocked, because of Problem 1"),
            ("Alternative 2", True, "should be blocked, because of the Problem 2"),
            ("Problem 1", True, "should be blocked"),
            ("Problem 2", True, "should be blocked"),
        ],
    )
    def test_blocking_status(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True

        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
        - [P] Problem 1
    - [a] Alternative 2 
        - [P] Problem 2  
""")
class TestMultipleBlockedAlternatives:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "Should block, has Alternatives but none viable"),
            ("Alternative 1", True, "should be blocked, because of Problem 1"),
            ("Alternative 2", True, "should be blocked, because of the Problem 2"),
            ("Problem 1", True, "should be blocked"),
            ("Problem 2", True, "should be blocked"),
        ],
    )
    def test_blocking_status(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True

        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
        - [a] Alternative 1.1
        - [a] Alternative 1.2
    - [a] Alternative 2 
        - [a] Alternative 2.1
        - [a] Alternative 2.2
""")
class TestMultipleNestedAlternatives:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "it has unresolved alternatives"),
            ("Alternative 1", False, "it has no blocking children"),
            ("Alternative 2", False, "it has no blocking children"),
            ("Alternative 1.1", False, "it has no blocking children"),
            ("Alternative 1.2", False, "it has no blocking children"),
            ("Alternative 2.1", False, "it has no blocking children"),
            ("Alternative 2.2", False, "it has no blocking children"),
        ],
    )
    def test_blocking_status(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True

        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
        - [a] Alternative 1.1
        - [a] Alternative 1.2
    - [a] Alternative 2 
        - [P] Problem
""")
class TestNestedAlternativesOneProblem:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "it has unresolved alternatives A1.1 and A1.2"),
            ("Alternative 1", False, "it has no blocking children"),
            ("Alternative 2", True, "it has a problem"),
            ("Alternative 1.1", False, "it has no blocking children"),
            ("Alternative 1.2", False, "it has no blocking children"),
            ("Problem", True, "problems always block"),
        ],
    )
    def test_blocking_status(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True

        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Question
    - [a] Alternative 1
        - [a] Alternative 1.1
        - [a] Alternative 1.2
            - [P] Problem 1.2
    - [a] Alternative 2 
        - [P] Problem 2
""")
class TestNestedAlternativesTwoProblems:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Question", True, "it has unresolved alternatives A1.1 and A1.2"),
            ("Alternative 1", True, "it has a unblocked alternative"),
            ("Alternative 2", True, "it has a problem"),
            ("Alternative 1.1", False, "it has no blocking children"),
            ("Alternative 1.2", True, "it has a problem"),
            ("Problem 1.2", True, "problems always block"),
            ("Problem 2", True, "problems always block"),
        ],
    )
    def test_blocking_status(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Question"]
        question.is_resolved = True

        check_blocking_status(graph_fixture, node_name, expected_status, reason)


@with_markdown("""\
- [?] Do Questions automatically resolve when they are unblocked, or do they have a dedicated `is_resolved` status and toggle (`.resolve()`)?
	- [a] Their blocked status does not depend on `is_resolved`
	    - This requires manually triggering a graph.resolve() method, which updates all nodes and automatically resolves (unblocks) questions. While this is not called, the node remains in its current status
	    - [c] The downside is that I can't call any other graph checks because they see the current graph and the question would already be resolved
	- [a] Their blocked status also depends on `is_resolved`  ^alt-toggle
		- initially `is_resolved` is False and the node is blocked
		- a `graph.resolve()` method can now switch all switchable nodes (Goal, Question, Task) explicitly
		- [p] This maintains the graph state until `graph.resolve()` is called
		- It would be better if all switchable nodes had the same interface
			- Instead of `is_achieved`, `is_resolved`, ... we use `is_done` and create a `.done(b: bool)` attribute or method.
			- This is different from the status of a Task
			- [_] refers to [[#^switch-idea]]
	- [D] Use separate toggles but unify Goals, Nodes (at least) [[#^alt-toggle]] or go further [[#^switch-idea]]
""")
class TestToggleExample:
    @pytest.mark.parametrize(
        "node_name,expected_status,reason",
        [
            ("Do Questions...", False, "Should be unblocked, has Decision referencing Alternative"),
            # ("Alternative 1", False, "should not be blocked, no blocked children"),
            # ("Alternative 2", False, "should not be blocked, no blocked children"),
            # ("Problem 1", False, "should not be blocked"),
            # ("Problem 2", False, "should not be blocked"),
        ],
    )
    @pytest.mark.skip(reason="Decision not yet implemented")
    def test_blocking_status_resolved(self, graph_fixture, node_name, expected_status, reason):
        # Set the question to resolved, we only want to test the alternative blocking mechanism
        nodes = graph_fixture["nodes_by_name"]
        question = nodes["Do Questions..."]
        question.is_resolved = True

        check_blocking_status(graph_fixture, node_name, expected_status, reason)
