# Cannonball

A productivity system based on directed acyclic graphs (DAGs) represented as hierarchical Markdown with custom node types. This system enables structured work management, knowledge representation, and AI-assisted decision making.

![Teaser](./assets/teaser.png)

## Features

- **Directed Acyclic Graph (DAG)**: Represents projects as nodes and edges in a directed graph
- **Markdown Representation**: Stores projects as human-readable markdown files
- **Multiple Node Types**: Supports various node types for different purposes (tasks, questions, decisions, etc.)
- **State Propagation**: Automatically tracks dependencies and blocking relationships
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
git clone https://github.com/rueckstiess/cannonball.git
cd cannonball
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
cannonball/
├── cannonball/
│   ├── __init__.py             # Module initialization
│   ├── utils.py                # Common utility functions
├── tests/
│   ├── __init__.py
│   └── test_*.py               # Test files, starting with `test_`
├── examples/
│   └── example.py              # Example usage
├── README.md                   # Project documentation
├── requirements.txt            # Dependencies
└── setup.py                    # Package configuration
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
