import unittest
import networkx as nx
from cannonball.nodes import Thought, Task, Question, Goal, Problem, TaskType
from cannonball.utils import EdgeType


class TestMixedNodes(unittest.TestCase):
    def test_different_node_types_basic_interaction(self):
        """Test basic interaction between different node types."""
        graph = nx.DiGraph()

        thought = Thought(id="thought", name="A thought")
        task = Task(id="task", name="A task", status=TaskType.OPEN)
        question = Question(id="question", name="A question", is_resolved=False)
        goal = Goal(id="goal", name="A goal", is_achieved=False)
        problem = Problem(id="problem", name="A problem")

        graph.add_nodes_from([thought, task, question, goal, problem])

        # Test initial blocking states
        self.assertFalse(thought.is_blocked(graph))  # Thoughts are never blocked
        self.assertTrue(task.is_blocked(graph))  # Unfinished tasks are blocked
        self.assertTrue(question.is_blocked(graph))  # Unresolved questions are blocked
        self.assertTrue(goal.is_blocked(graph))  # Unachieved goals are blocked
        self.assertTrue(problem.is_blocked(graph))  # Problems are always blocked

    def test_simple_dependency_chain(self):
        """Test a simple dependency chain with different node types."""
        graph = nx.DiGraph()

        # Create a simple dependency chain: task -> question -> goal -> problem
        task = Task(id="task", name="Task", status=TaskType.COMPLETED)
        question = Question(id="question", name="Question", is_resolved=True)
        goal = Goal(id="goal", name="Goal", is_achieved=True)
        problem = Problem(id="problem", name="Problem")

        graph.add_nodes_from([task, question, goal, problem])
        graph.add_edge(task, question, type=EdgeType.REQUIRES.value)
        graph.add_edge(question, goal, type=EdgeType.REQUIRES.value)
        graph.add_edge(goal, problem, type=EdgeType.REQUIRES.value)

        # Problem always blocks, and this should propagate up the chain
        self.assertTrue(problem.is_blocked(graph))
        self.assertTrue(goal.is_blocked(graph))
        self.assertTrue(question.is_blocked(graph))
        self.assertTrue(task.is_blocked(graph))

        # Test with REFERENCES edge type which doesn't propagate blocking
        new_graph = nx.DiGraph()
        new_graph.add_nodes_from([task, question, goal, problem])
        new_graph.add_edge(task, question, type=EdgeType.REQUIRES.value)
        new_graph.add_edge(question, goal, type=EdgeType.REQUIRES.value)
        new_graph.add_edge(goal, problem, type=EdgeType.REFERENCES.value)

        # Now the problem shouldn't block goal and above
        self.assertTrue(problem.is_blocked(new_graph))
        self.assertFalse(goal.is_blocked(new_graph))
        self.assertFalse(question.is_blocked(new_graph))
        self.assertFalse(task.is_blocked(new_graph))

    def test_tree_structure_with_mixed_nodes(self):
        """Test a tree structure with different node types."""
        graph = nx.DiGraph()

        # Root task with multiple children of different types
        root_task = Task(id="root", name="Root Task", status=TaskType.COMPLETED)

        # First branch - unblocked
        branch1_question = Question(
            id="b1_q", name="Branch 1 Question", is_resolved=True
        )
        branch1_task = Task(id="b1_t", name="Branch 1 Task", status=TaskType.COMPLETED)

        # Second branch - blocked
        branch2_goal = Goal(id="b2_g", name="Branch 2 Goal", is_achieved=True)
        branch2_problem = Problem(id="b2_p", name="Branch 2 Problem")

        # Third branch - includes a Thought (never blocked)
        branch3_thought = Thought(id="b3_th", name="Branch 3 Thought")

        # Build the graph
        graph.add_nodes_from(
            [
                root_task,
                branch1_question,
                branch1_task,
                branch2_goal,
                branch2_problem,
                branch3_thought,
            ]
        )

        # Add edges
        graph.add_edge(root_task, branch1_question, type=EdgeType.REQUIRES.value)
        graph.add_edge(branch1_question, branch1_task, type=EdgeType.REQUIRES.value)
        graph.add_edge(root_task, branch2_goal, type=EdgeType.REQUIRES.value)
        graph.add_edge(branch2_goal, branch2_problem, type=EdgeType.REQUIRES.value)
        graph.add_edge(root_task, branch3_thought, type=EdgeType.REQUIRES.value)

        # Check blocking status
        self.assertFalse(branch1_task.is_blocked(graph))
        self.assertFalse(branch1_question.is_blocked(graph))
        self.assertTrue(branch2_problem.is_blocked(graph))
        self.assertTrue(branch2_goal.is_blocked(graph))
        self.assertFalse(branch3_thought.is_blocked(graph))

        # Root task should be blocked because of branch2
        self.assertTrue(root_task.is_blocked(graph))

    def test_complex_dependency_network(self):
        """Test a complex network of dependencies between different node types."""
        graph = nx.DiGraph()

        # Create nodes of different types
        task1 = Task(id="task1", name="Task 1", status=TaskType.COMPLETED)
        task2 = Task(id="task2", name="Task 2", status=TaskType.OPEN)
        question1 = Question(id="q1", name="Question 1", is_resolved=True)
        question2 = Question(id="q2", name="Question 2", is_resolved=False)
        goal1 = Goal(id="goal1", name="Goal 1", is_achieved=True)
        goal2 = Goal(id="goal2", name="Goal 2", is_achieved=False)
        thought1 = Thought(id="thought1", name="Thought 1")
        problem1 = Problem(id="problem1", name="Problem 1")

        # Add nodes to graph
        graph.add_nodes_from(
            [task1, task2, question1, question2, goal1, goal2, thought1, problem1]
        )

        # Create a more complex dependency structure
        graph.add_edge(task1, question1, type=EdgeType.REQUIRES.value)
        graph.add_edge(task1, question2, type=EdgeType.REQUIRES.value)
        graph.add_edge(question1, goal1, type=EdgeType.REQUIRES.value)
        graph.add_edge(question2, goal2, type=EdgeType.REQUIRES.value)
        graph.add_edge(goal1, thought1, type=EdgeType.REQUIRES.value)
        graph.add_edge(
            goal2, problem1, type=EdgeType.REFERENCES.value
        )  # Using REFERENCES to not propagate blocking
        graph.add_edge(task2, problem1, type=EdgeType.REQUIRES.value)

        # Check blocking states
        self.assertFalse(thought1.is_blocked(graph))
        self.assertFalse(goal1.is_blocked(graph))
        self.assertTrue(goal2.is_blocked(graph))  # blocked because it's not achieved
        self.assertTrue(
            question2.is_blocked(graph)
        )  # blocked because it's not resolved and has a blocked child
        self.assertTrue(problem1.is_blocked(graph))  # problems are always blocked
        self.assertTrue(
            task2.is_blocked(graph)
        )  # blocked because it's not completed and has a blocked child

        # task1 should be blocked because question2 is blocked
        self.assertTrue(task1.is_blocked(graph))

    def test_deep_nesting_with_mixed_nodes(self):
        """Test deep nesting with many levels of different node types."""
        graph = nx.DiGraph()

        # Create a deep nested structure
        level1 = Task(id="l1", name="Level 1 Task", status=TaskType.COMPLETED)
        level2 = Question(id="l2", name="Level 2 Question", is_resolved=True)
        level3 = Goal(id="l3", name="Level 3 Goal", is_achieved=True)
        level4 = Thought(id="l4", name="Level 4 Thought")
        level5 = Task(id="l5", name="Level 5 Task", status=TaskType.COMPLETED)
        level6 = Question(id="l6", name="Level 6 Question", is_resolved=True)
        level7 = Goal(
            id="l7", name="Level 7 Goal", is_achieved=False
        )  # This one is blocked

        # Add nodes to graph
        graph.add_nodes_from([level1, level2, level3, level4, level5, level6, level7])

        # Create connections
        graph.add_edge(level1, level2, type=EdgeType.REQUIRES.value)
        graph.add_edge(level2, level3, type=EdgeType.REQUIRES.value)
        graph.add_edge(level3, level4, type=EdgeType.REQUIRES.value)
        graph.add_edge(level4, level5, type=EdgeType.REQUIRES.value)
        graph.add_edge(level5, level6, type=EdgeType.REQUIRES.value)
        graph.add_edge(level6, level7, type=EdgeType.REQUIRES.value)

        # Check how blocking propagates up the chain
        self.assertTrue(level7.is_blocked(graph))  # Blocked because it's not achieved
        self.assertTrue(level6.is_blocked(graph))
        self.assertTrue(level5.is_blocked(graph))
        self.assertTrue(
            level4.is_blocked(graph)
        )  # Even Thoughts propagate blocking from their children
        self.assertTrue(level3.is_blocked(graph))
        self.assertTrue(level2.is_blocked(graph))
        self.assertTrue(level1.is_blocked(graph))

    def test_mixed_edge_types(self):
        """Test mixed edge types with different node types."""
        graph = nx.DiGraph()

        # Create nodes
        root = Task(id="root", name="Root Task", status=TaskType.COMPLETED)

        req_task = Task(id="req_task", name="Required Task", status=TaskType.OPEN)
        req_question = Question(id="req_q", name="Required Question", is_resolved=False)

        ref_task = Task(id="ref_task", name="Referenced Task", status=TaskType.OPEN)
        ref_question = Question(
            id="ref_q", name="Referenced Question", is_resolved=False
        )

        # Add nodes
        graph.add_nodes_from([root, req_task, req_question, ref_task, ref_question])

        # Add edges with different types
        graph.add_edge(root, req_task, type=EdgeType.REQUIRES.value)
        graph.add_edge(root, req_question, type=EdgeType.REQUIRES.value)
        graph.add_edge(root, ref_task, type=EdgeType.REFERENCES.value)
        graph.add_edge(root, ref_question, type=EdgeType.REFERENCES.value)

        # Check that only REQUIRES edges propagate blocking
        self.assertTrue(req_task.is_blocked(graph))
        self.assertTrue(req_question.is_blocked(graph))
        self.assertTrue(ref_task.is_blocked(graph))
        self.assertTrue(ref_question.is_blocked(graph))

        # Root should be blocked because of required children
        self.assertTrue(root.is_blocked(graph))

        # Create a new graph with only REFERENCES edges
        ref_only_graph = nx.DiGraph()
        ref_only_graph.add_nodes_from([root, ref_task, ref_question])
        ref_only_graph.add_edge(root, ref_task, type=EdgeType.REFERENCES.value)
        ref_only_graph.add_edge(root, ref_question, type=EdgeType.REFERENCES.value)

        # Root should not be blocked now
        self.assertFalse(root.is_blocked(ref_only_graph))

    # def test_circular_dependencies(self):
    #     """Test circular dependencies between different node types."""
    #     graph = nx.DiGraph()

    #     # Create nodes
    #     task = Task(id="task", name="Task", status=TaskType.COMPLETED)
    #     question = Question(id="question", name="Question", is_resolved=True)
    #     goal = Goal(id="goal", name="Goal", is_achieved=True)

    #     # Add nodes to graph
    #     graph.add_nodes_from([task, question, goal])

    #     # Create a circular dependency (task → question → goal → task)
    #     graph.add_edge(task, question, type=EdgeType.REQUIRES.value)
    #     graph.add_edge(question, goal, type=EdgeType.REQUIRES.value)
    #     graph.add_edge(goal, task, type=EdgeType.REQUIRES.value)

    #     # None of these should be blocked by themselves, and the cycle shouldn't cause issues
    #     self.assertFalse(task.is_blocked(graph))
    #     self.assertFalse(question.is_blocked(graph))
    #     self.assertFalse(goal.is_blocked(graph))

    #     # Now add a problem that blocks one of them
    #     problem = Problem(id="problem", name="Problem")
    #     graph.add_node(problem)
    #     graph.add_edge(goal, problem, type=EdgeType.REQUIRES.value)

    #     # The problem should block the entire cycle
    #     self.assertTrue(problem.is_blocked(graph))
    #     self.assertTrue(goal.is_blocked(graph))
    #     self.assertTrue(question.is_blocked(graph))
    #     self.assertTrue(task.is_blocked(graph))

    def test_resolving_nodes_affects_blocking(self):
        """Test that resolving nodes properly affects blocking status through a complex graph."""
        graph = nx.DiGraph()

        # Create a structure with multiple dependencies
        root = Task(id="root", name="Root", status=TaskType.COMPLETED)
        branch1 = Question(id="branch1", name="Branch 1", is_resolved=False)
        branch2 = Task(id="branch2", name="Branch 2", status=TaskType.IN_PROGRESS)
        leaf1 = Goal(id="leaf1", name="Leaf 1", is_achieved=False)
        leaf2 = Problem(id="leaf2", name="Leaf 2")

        # Add nodes and edges
        graph.add_nodes_from([root, branch1, branch2, leaf1, leaf2])
        graph.add_edge(root, branch1, type=EdgeType.REQUIRES.value)
        graph.add_edge(root, branch2, type=EdgeType.REQUIRES.value)
        graph.add_edge(branch1, leaf1, type=EdgeType.REQUIRES.value)
        graph.add_edge(branch2, leaf2, type=EdgeType.REQUIRES.value)

        # Initially everything is blocked
        self.assertTrue(root.is_blocked(graph))
        self.assertTrue(branch1.is_blocked(graph))
        self.assertTrue(branch2.is_blocked(graph))
        self.assertTrue(leaf1.is_blocked(graph))
        self.assertTrue(leaf2.is_blocked(graph))

        # Resolve branch1 and leaf1
        branch1.is_resolved = True
        leaf1.is_achieved = True

        # Branch1 and leaf1 should now be unblocked
        self.assertFalse(leaf1.is_blocked(graph))
        self.assertFalse(branch1.is_blocked(graph))

        # But root is still blocked because of branch2 and leaf2
        self.assertTrue(root.is_blocked(graph))

        # Complete branch2
        branch2.status = TaskType.COMPLETED

        # branch2 is still blocked because of leaf2 (Problem)
        self.assertTrue(branch2.is_blocked(graph))

        # Root is still blocked
        self.assertTrue(root.is_blocked(graph))

        # If we change the edge to leaf2 to be a REFERENCES edge
        graph.remove_edge(branch2, leaf2)
        graph.add_edge(branch2, leaf2, type=EdgeType.REFERENCES.value)

        # Now branch2 should be unblocked
        self.assertFalse(branch2.is_blocked(graph))

        # And root should now be unblocked
        self.assertFalse(root.is_blocked(graph))

    def test_thought_node_special_behavior(self):
        """Test the special behavior of Thought nodes, which never block themselves."""
        graph = nx.DiGraph()

        # Create a chain: task → thought → problem
        task = Task(id="task", name="Task", status=TaskType.COMPLETED)
        thought = Thought(id="thought", name="Thought")
        problem = Problem(id="problem", name="Problem")

        # Add nodes and edges
        graph.add_nodes_from([task, thought, problem])
        graph.add_edge(task, thought, type=EdgeType.REQUIRES.value)
        graph.add_edge(thought, problem, type=EdgeType.REQUIRES.value)

        # The problem blocks the thought, which blocks the task
        self.assertTrue(problem.is_blocked(graph))
        self.assertTrue(
            thought.is_blocked(graph)
        )  # Thought still propagates blocking from its children
        self.assertTrue(task.is_blocked(graph))

        # Create a new graph with just the thought
        thought_graph = nx.DiGraph()
        thought_graph.add_node(thought)

        # On its own, a thought is never blocked
        self.assertFalse(thought.is_blocked(thought_graph))

    def test_problem_node_special_behavior(self):
        """Test the special behavior of Problem nodes, which are always blocked."""
        graph = nx.DiGraph()

        # Even in complex scenarios, problems always block
        problem1 = Problem(id="p1", name="Problem 1")
        problem2 = Problem(id="p2", name="Problem 2")

        graph.add_nodes_from([problem1, problem2])
        graph.add_edge(
            problem1, problem2, type=EdgeType.REFERENCES.value
        )  # Even with REFERENCES

        self.assertTrue(problem1.is_blocked(graph))
        self.assertTrue(problem2.is_blocked(graph))

        # Even with achieved goals as children
        problem_with_child = Problem(id="pwc", name="Problem with Child")
        achieved_goal = Goal(id="ag", name="Achieved Goal", is_achieved=True)

        graph.add_nodes_from([problem_with_child, achieved_goal])
        graph.add_edge(problem_with_child, achieved_goal, type=EdgeType.REQUIRES.value)

        self.assertTrue(problem_with_child.is_blocked(graph))


if __name__ == "__main__":
    unittest.main()
