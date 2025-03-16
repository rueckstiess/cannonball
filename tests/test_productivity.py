import unittest
from graph_manager import GraphManager
from base_classes import Element, Thought, Node
from state_nodes import NodeState
from specific_nodes import Task, Question, Problem, Alternative, Decision, Observation


class ProductivitySystemTest(unittest.TestCase):
    """Test cases for the productivity system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph_manager = GraphManager()
        
        # Simple test markdown
        self.test_markdown = """- [g] Test Goal
	- [?] Test Question ^q1
		- [a] Alternative 1 ^alt1
			- [o] Observation for Alt 1
		- [a] Alternative 2 ^alt2
			- [o] Observation for Alt 2
		- [D] Selected ^alt1
	- [ ] Task 1
		- [ ] Subtask 1.1
		- [x] Subtask 1.2
	- [P] Test Problem
		- [o] Problem Observation
	- [I] Test Idea
"""
        self.graph_manager.load_from_markdown(self.test_markdown)
    
    def test_node_creation(self):
        """Test that nodes are created correctly from markdown."""
        # Check that we have the expected number of nodes
        self.assertGreater(len(self.graph_manager.graph.nodes), 0)
        
        # Check that we can find nodes by reference
        question = self.graph_manager.get_node_by_ref("q1")
        self.assertIsNotNone(question)
        self.assertEqual(question.text, "Test Question")
        self.assertEqual(question.node_type, "question")
        
        # Check alternatives
        alt1 = self.graph_manager.get_node_by_ref("alt1")
        self.assertIsNotNone(alt1)
        self.assertEqual(alt1.text, "Alternative 1")
        
        alt2 = self.graph_manager.get_node_by_ref("alt2")
        self.assertIsNotNone(alt2)
        self.assertEqual(alt2.text, "Alternative 2")
    
    def test_node_relationships(self):
        """Test that node relationships are established correctly."""
        question = self.graph_manager.get_node_by_ref("q1")
        self.assertIsNotNone(question)
        
        # Check that alternatives are children of the question
        alternatives = question.get_alternatives()
        self.assertEqual(len(alternatives), 2)
        
        # Check that there's a decision node
        decisions = [child for child in question.children if isinstance(child, Decision)]
        self.assertEqual(len(decisions), 1)
        
        # Check that the decision references the right alternative
        decision = decisions[0]
        self.assertEqual(decision.selected_alternative_ref, "alt1")
        self.assertEqual(decision.get_selected_alternative().text, "Alternative 1")
    
    def test_question_resolution(self):
        """Test that questions are resolved correctly."""
        question = self.graph_manager.get_node_by_ref("q1")
        self.assertIsNotNone(question)
        
        # Question should be resolved due to the decision
        self.assertTrue(question.is_resolved())
        
        # Check resolution nodes
        resolution_nodes = question.get_resolution_nodes()
        self.assertEqual(len(resolution_nodes), 1)
        self.assertIsInstance(resolution_nodes[0], Decision)
    
    def test_task_state(self):
        """Test task state management."""
        # Find Task 1
        task = None
        for node in self.graph_manager.graph.nodes:
            node_data = self.graph_manager.graph.nodes[node]
            if node_data.get('text') == "Task 1":
                task = self.graph_manager.get_node_by_id(node)
                break
        
        self.assertIsNotNone(task)
        self.assertEqual(task.get_state(), NodeState.OPEN)
        
        # Mark as in progress
        self.graph_manager.update_task_state(task.id, "in_progress")
        self.assertEqual(task.get_state(), NodeState.IN_PROGRESS)
        
        # Check subtasks
        subtasks = [child for child in task.children if isinstance(child, Task)]
        self.assertEqual(len(subtasks), 2)
        
        # One subtask should be done, one open
        done_subtasks = [task for task in subtasks if task.get_state() == NodeState.DONE]
        self.assertEqual(len(done_subtasks), 1)
    
    def test_problem_resolution(self):
        """Test problem resolution."""
        # Find the Problem node
        problem = None
        for node in self.graph_manager.graph.nodes:
            node_data = self.graph_manager.graph.nodes[node]
            if node_data.get('type') == "problem":
                problem = self.graph_manager.get_node_by_id(node)
                break
        
        self.assertIsNotNone(problem)
        
        # Problem should be resolved due to observation
        self.assertTrue(problem.is_resolved())
        
        # The observation should be a child of the problem
        observations = [child for child in problem.children if isinstance(child, Observation)]
        self.assertEqual(len(observations), 1)
    
    def test_markdown_roundtrip(self):
        """Test that markdown can be converted to a graph and back."""
        # Export to markdown
        exported_markdown = self.graph_manager.to_markdown()
        
        # Create a new graph manager and load the exported markdown
        new_manager = GraphManager()
        new_manager.load_from_markdown(exported_markdown)
        
        # Check that the nodes are the same
        self.assertEqual(len(self.graph_manager.graph.nodes), len(new_manager.graph.nodes))
        
        # Check that references are preserved
        q1_original = self.graph_manager.get_node_by_ref("q1")
        q1_new = new_manager.get_node_by_ref("q1")
        
        self.assertIsNotNone(q1_original)
        self.assertIsNotNone(q1_new)
        self.assertEqual(q1_original.text, q1_new.text)
    
    def test_node_modification(self):
        """Test node modification."""
        question = self.graph_manager.get_node_by_ref("q1")
        self.assertIsNotNone(question)
        
        # Update text
        new_text = "Modified Question"
        self.graph_manager.update_node_text(question.id, new_text)
        self.assertEqual(question.text, new_text)
        
        # Add a new alternative
        alt3 = self.graph_manager.add_node(
            "alternative", 
            "Alternative 3", 
            question.id, 
            "alt3"
        )
        self.assertIsNotNone(alt3)
        self.assertIn(alt3, question.children)
        
        # Change decision
        decision = [child for child in question.children if isinstance(child, Decision)][0]
        self.graph_manager.make_decision(decision.id, "alt3")
        self.assertEqual(decision.selected_alternative_ref, "alt3")
        self.assertEqual(decision.get_selected_alternative().text, "Alternative 3")
    
    def test_blocking_state(self):
        """Test blocking state propagation."""
        # Initially, the question is resolved
        question = self.graph_manager.get_node_by_ref("q1")
        self.assertIsNotNone(question)
        self.assertTrue(question.is_resolved())
        
        # Add a problem to the selected alternative
        alt1 = self.graph_manager.get_node_by_ref("alt1")
        self.assertIsNotNone(alt1)
        
        problem = self.graph_manager.add_node(
            "problem", 
            "New Problem with Alternative 1", 
            alt1.id
        )
        self.assertIsNotNone(problem)
        
        # Now the question should not be resolved
        self.assertFalse(question.is_resolved())
        
        # Resolve the problem
        observation = self.graph_manager.add_node(
            "observation", 
            "Problem solved", 
            problem.id
        )
        self.assertIsNotNone(observation)
        
        # Question should be resolved again
        self.assertTrue(question.is_resolved())


if __name__ == "__main__":
    unittest.main()
