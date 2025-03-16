# AI-Powered Productivity System

A productivity system based on directed acyclic graphs (DAGs) represented as hierarchical Markdown with custom node types. This system enables structured work management, knowledge representation, and AI-assisted decision making.

## Features

- **Directed Acyclic Graph (DAG)**: Represents projects as nodes and edges in a directed graph
- **Markdown Representation**: Stores projects as human-readable markdown files
- **Multiple Node Types**: Supports various node types for different purposes (tasks, questions, decisions, etc.)
- **State Propagation**: Automatically tracks dependencies and blocking relationships
- **MongoDB Integration**: Persistent storage with MongoDB
- **NetworkX Support**: Graph operations and analysis using NetworkX
- **ReactFlow Ready**: Designed for visualization with ReactFlow

## Node Types

The system supports the following node types:

- **Tasks `- [ ]`**: Work to be done with states (open, in-progress, done, cancelled)
- **Questions `- [?]`**: Uncertainties requiring resolution
- **Alternatives `- [a]`**: Options being considered
- **Observations `- [o]`**: Empirical data points
- **Decisions `- [D]`**: Active choices made
- **Goals `- [g]`**: Desired outcomes
- **Artifacts `- [A]`**: Tangible outputs produced
- **Problems `- [P]`**: Issues requiring resolution
- **Experiments `- [e]`**: Structured investigations
- **Meta Comments `- [m]`**: System feedback
- **Examples `- ["]`**: Illustrative content
- **Ideas `- [I]`**: Spontaneous insights
- **Knowledge `- [i]`**: External information
- **Location Markers `- [l]`**: Navigation aids

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/productivity-system.git
cd productivity-system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
productivity-system/
├── productivity/
│   ├── __init__.py             # Module initialization
│   ├── base_classes.py         # Base Element, Thought, and Node classes
│   ├── state_nodes.py          # State management classes
│   ├── node_categories.py      # Node category classes
│   ├── specific_nodes.py       # Specific node implementations
│   ├── meta_nodes.py           # Meta node implementations
│   ├── markdown_parser.py      # Markdown parsing utilities
│   └── graph_manager.py        # Graph management and operations
├── tests/
│   ├── __init__.py
│   └── test_productivity.py    # Integration tests
├── examples/
│   └── example.py              # Example usage
├── README.md                   # Project documentation
├── requirements.txt            # Dependencies
└── setup.py                    # Package configuration
```

## Usage

Basic example:

```python
from productivity.graph_manager import GraphManager

# Create a new graph manager
graph_manager = GraphManager()

# Load markdown
markdown = """- [g] Build a recommendation engine
	- [?] Which algorithm should we use? ^q1
		- [a] Collaborative filtering ^alt1
		- [a] Content-based filtering ^alt2
		- [D] Selected ^alt1
	- [ ] Implement algorithm
	- [ ] Test with users
"""
graph_manager.load_from_markdown(markdown)

# Get nodes by reference
question = graph_manager.get_node_by_ref("q1")
print(f"Question: {question.text}")
print(f"Is resolved: {question.is_resolved()}")

# Add a new node
graph_manager.add_node(
    "observation", 
    "Algorithm achieves 85% accuracy", 
    question.id
)

# Export to markdown
modified_markdown = graph_manager.to_markdown()
print(modified_markdown)
```

## Dependencies

- `networkx` for graph operations
- `pymongo` for MongoDB integration
- `pytest` for testing

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
