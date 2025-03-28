from .bullet import Bullet
from .problem import Problem
from .question import Question
from .decision import Decision
from .task import Task
from .node import Node
from .artefact import Artefact
from .goal import Goal
from .experiment import Experiment

# --- Register all node types and markers with the base class

# Bullet
Node.register(None, Bullet, True, False)

# Task
Node.register(" ", Task, False, False)
Node.register("!", Task, False, True)
Node.register("x", Task, True, False)

# Decision
Node.register("d", Decision, False, False)
Node.register("D", Decision, True, False)
Node.register("$", Decision, False, True)

# Question
Node.register("q", Question, False, False)
Node.register("Q", Question, True, False)
Node.register("?", Question, False, True)

# Artefact
Node.register("a", Artefact, False, False)
Node.register("A", Artefact, True, False)

# Problem
Node.register("P", Problem, False, True)

# Goal
Node.register("g", Goal, False, False)
Node.register("G", Goal, True, False)
Node.register("~", Goal, False, True)

# Experiment
Node.register("e", Experiment, False, False)
Node.register("E", Experiment, True, False)
Node.register("%", Experiment, False, True)

