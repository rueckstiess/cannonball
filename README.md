# Cannonball

A productivity system based on dependency trees represented as hierarchical Markdown with custom node types. This system enables structured work management, knowledge representation, and AI-assisted decision making.

![Teaser](./assets/teaser.png)

## Features

- **Markdown Representation**: Stores projects as human-readable markdown files
- **Multiple Node Types**: Supports various node types for different purposes (tasks, questions, decisions, etc.)
- **State Propagation**: Automatically tracks dependencies and blocking relationships

## Node Types

The system currently supports the following node types:

- **Bullet `- `**: For neutral comments or grouping mechanism
- **Tasks `- [ ]`**: Work to be done with states (open, in-progress, done, cancelled)
- **Decisions `- [D]`**: Active choices to be made
- **Answers `- [a]`**: An Answer to a question



Future nodes planned: 

- **Questions `- [?]`**: Uncertainties requiring resolution
- **Observations `- [o]`**: Empirical data points
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
|   └── nodes.py                # Node definitions and logic
├── tests/
│   ├── __init__.py
│   └── test_*.py               # Test files, starting with `test_`
├── notebooks/
│   └── *.ipynb                 # Example usage in Jupyter notebooks
├── README.md                   # Project documentation
├── CLAUDE.md                   # Instructions for Claude Code
├── requirements.txt            # Dependencies
└── setup.py                    # Package configuration
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
