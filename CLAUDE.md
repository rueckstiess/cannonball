# CLAUDE.md - Coding Assistant Guide

## Commands
```bash
# Installation
pip install -e .

# Testing
pytest                                          # Run all tests
pytest tests/test_utils.py                      # Run specific test file 
pytest tests/test_utils.py::TestClassName       # Run specific test class
pytest tests/test_utils.py::TestClassName::test_method_name  # Run specific test

# Jupyter notebooks
jupyter notebook                                # Start notebook server
```

## Code Style
- **Imports**: stdlib first, third-party second, project imports last
- **Types**: Use type hints (e.g., `def func(text: str) -> Optional[Dict[str, Any]]`)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Google-style docstrings with Args/Returns sections
- **Error handling**: Use assertions for validation, return None for missing values
- **Project structure**: Core code in cannonball/, tests in tests/, notebooks for exploration

## Libraries
- Core: networkx, pymongo, regraph, marko
- Testing: pytest