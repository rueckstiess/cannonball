# __init__.py

# Base classes
from base_classes import Element, Thought, Node

# State management
from state_nodes import StateProducerNode, StateDerivedNode, NodeState

# Node categories
from node_categories import (
    WorkNode, BlockingNode, InformationNode, 
    DecisionNode, MetaNode, SpontaneousNode
)

# Specific node implementations
from specific_nodes import (
    Task, Question, Problem, Alternative, Decision,
    Observation, Knowledge, Goal, Experiment,
    Idea, Artifact
)

# Meta node implementations
from meta_nodes import MetaComment, Example, LocationMarker

# Graph management
# (to be implemented)
