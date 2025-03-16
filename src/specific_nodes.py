from typing import Optional, List, Dict, Any, Set, Union, ClassVar, Type
from datetime import datetime

from base_classes import Node, Element, Thought
from state_nodes import StateProducerNode, StateDerivedNode, NodeState
from node_categories import (
    WorkNode, BlockingNode, InformationNode, 
    DecisionNode, MetaNode, SpontaneousNode
)


class Task(WorkNode):
    """Represents a task or work item in the system.
    
    Tasks have explicit states (open, in progress, done, cancelled) and
    can have dependencies on other nodes.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 state: NodeState = NodeState.OPEN):
        """Initialize a new Task.
        
        Args:
            text: The task description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            state: Initial state of the task
        """
        # Determine the node type based on the state
        if state == NodeState.OPEN:
            node_type = "task"
        elif state == NodeState.IN_PROGRESS:
            node_type = "task_in_progress"
        elif state == NodeState.DONE:
            node_type = "task_done"
        elif state == NodeState.CANCELLED:
            node_type = "task_cancelled"
        else:
            node_type = "task"
            
        super().__init__(text, node_type, parent, id, ref_marker, metadata, state)
    
    def set_state(self, state: NodeState) -> None:
        """Set the state of this task.
        
        Also updates the node_type to match the state.
        
        Args:
            state: The new state
        """
        super().set_state(state)
        
        # Update the node type and marker based on the new state
        if state == NodeState.OPEN:
            self.node_type = "task"
            self.marker = self.NODE_TYPES["task"]
        elif state == NodeState.IN_PROGRESS:
            self.node_type = "task_in_progress"
            self.marker = self.NODE_TYPES["task_in_progress"]
        elif state == NodeState.DONE:
            self.node_type = "task_done"
            self.marker = self.NODE_TYPES["task_done"]
        elif state == NodeState.CANCELLED:
            self.node_type = "task_cancelled"
            self.marker = self.NODE_TYPES["task_cancelled"]


class Question(BlockingNode):
    """Represents a question or uncertainty in the system.
    
    Questions are blocking nodes that need to be answered before
    dependent nodes can proceed.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Question.
        
        Args:
            text: The question text
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "question", parent, id, ref_marker, metadata)
    
    def has_valid_resolution(self) -> bool:
        """Determine if this question has a valid resolution.
        
        A question is considered resolved if it has at least one Decision node
        as a direct child, and if the Decision references an Alternative, that
        Alternative must not contain any unresolved Problem nodes.
        
        Returns:
            bool: True if this question has a valid resolution, False otherwise
        """
        # Get all direct Decision children
        from specific_nodes import Decision, Problem, Alternative
        decisions = [child for child in self.children 
                    if isinstance(child, Decision)]
        
        if not decisions:
            # Get all direct Knowledge or Observation children
            from specific_nodes import Knowledge, Observation
            info_nodes = [child for child in self.children 
                         if isinstance(child, Knowledge) or 
                            isinstance(child, Observation)]
            
            # Question can be resolved by direct information nodes
            if info_nodes:
                return True
            return False
        
        # Check if any Decision has a valid resolution
        for decision in decisions:
            # If the Decision doesn't reference an Alternative, it's valid
            if not decision.selected_alternative_ref:
                return True
                
            # If the Decision references an Alternative, check if it's valid
            if decision.is_alternative_valid():
                return True
                
        return False
    
    def get_resolution_nodes(self) -> List[Node]:
        """Get nodes that contribute to resolving this question.
        
        Returns:
            List[Node]: Decision, Knowledge, or Observation nodes that resolve this question
        """
        from specific_nodes import Decision, Knowledge, Observation
        
        resolution_nodes = []
        
        # Add Decision nodes
        resolution_nodes.extend([child for child in self.children 
                                if isinstance(child, Decision)])
        
        # Add Knowledge and Observation nodes
        resolution_nodes.extend([child for child in self.children 
                                if isinstance(child, Knowledge) or 
                                   isinstance(child, Observation)])
        
        return resolution_nodes
    
    def get_alternatives(self) -> List[Node]:
        """Get all Alternative nodes that are direct children of this Question.
        
        Returns:
            List[Node]: List of Alternative nodes
        """
        from specific_nodes import Alternative
        return [child for child in self.children if isinstance(child, Alternative)]


class Problem(BlockingNode):
    """Represents a problem or issue in the system.
    
    Problems are blocking nodes that need to be resolved before
    dependent nodes can proceed.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Problem.
        
        Args:
            text: The problem description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "problem", parent, id, ref_marker, metadata)
    
    def has_valid_resolution(self) -> bool:
        """Determine if this problem has a valid resolution.
        
        A problem is considered resolved through the same rules as a Question:
        if it has a Decision, Knowledge, or Observation node as a direct child.
        
        Returns:
            bool: True if this problem has a valid resolution, False otherwise
        """
        # Sharing the same resolution logic as Question
        from specific_nodes import Decision, Knowledge, Observation
        
        # Check for Decision nodes
        decisions = [child for child in self.children 
                    if isinstance(child, Decision)]
        
        if decisions:
            # Check if any Decision has a valid resolution
            for decision in decisions:
                if not decision.selected_alternative_ref or decision.is_alternative_valid():
                    return True
        
        # Check for Knowledge or Observation nodes
        info_nodes = [child for child in self.children 
                     if isinstance(child, Knowledge) or 
                        isinstance(child, Observation)]
        
        return len(info_nodes) > 0
    
    def get_resolution_nodes(self) -> List[Node]:
        """Get nodes that contribute to resolving this problem.
        
        Returns:
            List[Node]: Decision, Knowledge, or Observation nodes that resolve this problem
        """
        from specific_nodes import Decision, Knowledge, Observation
        
        resolution_nodes = []
        
        # Add Decision nodes
        resolution_nodes.extend([child for child in self.children 
                                if isinstance(child, Decision)])
        
        # Add Knowledge and Observation nodes
        resolution_nodes.extend([child for child in self.children 
                                if isinstance(child, Knowledge) or 
                                   isinstance(child, Observation)])
        
        return resolution_nodes


class Alternative(Node):
    """Represents an alternative or option being considered.
    
    Alternatives are options that can be selected by Decision nodes
    to resolve Questions or Problems.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Alternative.
        
        Args:
            text: The alternative description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "alternative", parent, id, ref_marker, metadata)
    
    def has_problems(self) -> bool:
        """Check if this alternative has any unresolved problems.
        
        Returns:
            bool: True if this alternative has unresolved problems, False otherwise
        """
        from specific_nodes import Problem
        for child in self.children:
            if isinstance(child, Problem) and child.is_blocking():
                return True
        return False
    
    def get_problems(self) -> List[Node]:
        """Get all Problem nodes that are direct children of this Alternative.
        
        Returns:
            List[Node]: List of Problem nodes
        """
        from specific_nodes import Problem
        return [child for child in self.children if isinstance(child, Problem)]
    
    def is_blocking(self) -> bool:
        """Determine if this node is blocking.
        
        Alternatives themselves don't block.
        
        Returns:
            bool: False, as alternatives don't block
        """
        return False
    
    def can_block(self) -> bool:
        """Determine if this node type can block.
        
        Returns:
            bool: False, as alternatives don't block
        """
        return False


class Decision(DecisionNode):
    """Represents a decision or choice in the system.
    
    Decisions are used to resolve Questions or Problems, often by
    selecting from among Alternative nodes.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 selected_alternative_ref: Optional[str] = None):
        """Initialize a new Decision.
        
        Args:
            text: The decision description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            selected_alternative_ref: Optional reference to the selected alternative
        """
        super().__init__(text, "decision", parent, id, ref_marker, metadata, NodeState.DONE)
        
        if selected_alternative_ref:
            self.select_alternative(selected_alternative_ref)
    
    def is_blocking(self) -> bool:
        """Determine if this decision is blocking.
        
        A decision is blocking if it references an alternative that has problems.
        
        Returns:
            bool: True if blocking, False otherwise
        """
        if not self.selected_alternative_ref:
            return False
            
        alternative = self.get_selected_alternative()
        if not alternative:
            return False
            
        return isinstance(alternative, Alternative) and alternative.has_problems()


class Observation(InformationNode):
    """Represents an empirical observation or data point.
    
    Observations are factual information derived from direct experience
    or measurement.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 source: Optional[str] = None):
        """Initialize a new Observation.
        
        Args:
            text: The observation text
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            source: Optional source of the observation
        """
        super().__init__(text, "observation", parent, id, ref_marker, metadata, source)


class Knowledge(InformationNode):
    """Represents knowledge or information from external sources.
    
    Knowledge nodes contain information acquired from research, documentation,
    papers, books, or other external sources.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 source: Optional[str] = None):
        """Initialize a new Knowledge node.
        
        Args:
            text: The knowledge text
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            source: Optional citation or source reference
        """
        super().__init__(text, "knowledge", parent, id, ref_marker, metadata, source)


class Goal(StateDerivedNode):
    """Represents a goal or objective in the system.
    
    Goals define desired outcomes and provide direction for the work.
    They are typically at the root of a graph or sub-graph.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Goal.
        
        Args:
            text: The goal description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "goal", parent, id, ref_marker, metadata)
    
    def has_valid_resolution(self) -> bool:
        """Determine if this goal has been achieved.
        
        A goal is achieved when all its required sub-nodes are complete or resolved.
        If a Goal contains unresolved Problem or Question nodes, it cannot be
        considered achieved. If it contains incomplete Task nodes, it is still
        in progress.
        
        Returns:
            bool: True if this goal has been achieved, False otherwise
        """
        # Check if there are any blocking nodes
        if self.get_blocking_children():
            return False
            
        # Check if there are any incomplete tasks
        from specific_nodes import Task
        tasks = [child for child in self.get_recursive_nodes() 
                if isinstance(child, Task) and child is not self]
        
        if any(task.get_state() != NodeState.DONE and 
               task.get_state() != NodeState.CANCELLED 
               for task in tasks):
            return False
            
        return True


class Experiment(StateDerivedNode):
    """Represents an experiment or structured investigation.
    
    Experiments are systematic approaches to gathering information through
    direct testing or measurement.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Experiment.
        
        Args:
            text: The experiment description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "experiment", parent, id, ref_marker, metadata)
    
    def has_valid_resolution(self) -> bool:
        """Determine if this experiment has been completed.
        
        An experiment is completed when it has Observation nodes capturing results,
        regardless of whether those results are positive or negative.
        
        Returns:
            bool: True if this experiment has been completed, False otherwise
        """
        # Check if there are any observation nodes
        from specific_nodes import Observation
        observations = [child for child in self.children 
                       if isinstance(child, Observation)]
        
        return len(observations) > 0
    
    def get_protocol_tasks(self) -> List[Node]:
        """Get all Task nodes that describe the experiment protocol.
        
        Returns:
            List[Node]: List of protocol Task nodes
        """
        from specific_nodes import Task
        # Look for tasks that have "protocol" in their metadata
        return [child for child in self.children 
               if isinstance(child, Task) and 
                  child.metadata.get("role") == "protocol"]
    
    def get_execution_tasks(self) -> List[Node]:
        """Get all Task nodes for running the experiment.
        
        Returns:
            List[Node]: List of execution Task nodes
        """
        from specific_nodes import Task
        # Look for tasks that have "execution" in their metadata
        return [child for child in self.children 
               if isinstance(child, Task) and 
                  child.metadata.get("role") == "execution"]
    
    def get_results(self) -> List[Node]:
        """Get all Observation nodes capturing experiment results.
        
        Returns:
            List[Node]: List of result Observation nodes
        """
        from specific_nodes import Observation
        return [child for child in self.children 
               if isinstance(child, Observation)]


class Idea(SpontaneousNode):
    """Represents a spontaneous idea or insight.
    
    Ideas are creative thoughts that emerge during the work process
    without explicit dependencies.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new Idea.
        
        Args:
            text: The idea description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
        """
        super().__init__(text, "idea", parent, id, ref_marker, metadata)


class Artifact(InformationNode):
    """Represents a tangible output or deliverable.
    
    Artifacts are concrete products of work, such as documents, code,
    or other deliverables.
    """
    
    def __init__(self, 
                 text: str, 
                 parent: Optional[Element] = None, 
                 id: Optional[str] = None,
                 ref_marker: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 artifact_type: Optional[str] = None,
                 location: Optional[str] = None):
        """Initialize a new Artifact.
        
        Args:
            text: The artifact description
            parent: The parent element, if any
            id: Optional unique identifier
            ref_marker: Optional reference marker (without the ^ symbol)
            metadata: Optional metadata dictionary
            artifact_type: Optional type of artifact (code, document, etc.)
            location: Optional location or path to the artifact
        """
        super().__init__(text, "artifact", parent, id, ref_marker, metadata)
        self.artifact_type = artifact_type
        self.location = location
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this artifact to a dictionary for storage in MongoDB.
        
        Returns:
            dict: The dictionary representation of this artifact
        """
        artifact_dict = super().to_dict()
        artifact_dict.update({
            "artifact_type": self.artifact_type,
            "location": self.location
        })
        return artifact_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], elements_map: Dict[str, Element]) -> 'Artifact':
        """Create an artifact from a dictionary representation.
        
        Args:
            data: The dictionary data
            elements_map: A map of element IDs to element objects
            
        Returns:
            Artifact: The created artifact
        """
        artifact = super().from_dict(data, elements_map)
        artifact.artifact_type = data.get("artifact_type")
        artifact.location = data.get("location")
        return artifact