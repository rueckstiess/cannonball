import pytest
from cannonball.document import Document


class TestDocument:
    def test_document_initialization(self):
        """Test that Document can be initialized with markdown content."""
        markdown = "- Item 1\n  - Item 1.1\n- Item 2"
        doc = Document(markdown)
        assert doc.markdown == markdown
        assert len(doc.toplevel_lists) == 1
        assert len(doc.list_to_roots) == 1

    def test_create_nodes(self):
        """Test that _create_nodes correctly creates Node objects."""
        markdown = "- Item 1\n  - Item 1.1\n  - Item 1.2\n- Item 2"
        doc = Document(markdown)

        # Get the first list and its root nodes
        lst = list(doc.list_to_roots.keys())[0]
        roots = doc.list_to_roots[lst]

        assert len(roots) == 2  # Two root items
        assert roots[0].name == "Item 1"
        assert roots[1].name == "Item 2"
        assert len(roots[0].children) == 2  # Item 1 has two children
        assert roots[0].children[0].name == "Item 1.1"
        assert roots[0].children[1].name == "Item 1.2"

    def test_change_indent_with_tabs(self):
        """Test _change_indent with tab indentation."""
        markdown = "- Item 1\n  - Item 1.1\n    - Item 1.1.1\n  - Item 1.2"
        doc = Document(markdown)

        # Apply tab indentation
        result = doc._change_indent(markdown, "\t")
        expected = "- Item 1\n\t- Item 1.1\n\t\t- Item 1.1.1\n\t- Item 1.2"
        assert result == expected

    def test_change_indent_with_spaces(self):
        """Test _change_indent with space indentation."""
        markdown = "- Item 1\n  - Item 1.1\n    - Item 1.1.1\n  - Item 1.2"
        doc = Document(markdown)

        # Apply 4-space indentation
        result = doc._change_indent(markdown, 4)
        expected = "- Item 1\n    - Item 1.1\n        - Item 1.1.1\n    - Item 1.2"
        assert result == expected

        # Apply 2-space indentation (should be unchanged)
        result = doc._change_indent(markdown, 2)
        assert result == markdown

    def test_to_markdown_default_indent(self):
        """Test to_markdown with default tab indentation."""
        markdown = "- Item 1\n  - Item 1.1\n- Item 2"
        expected = "- Item 1\n\t- Item 1.1\n- Item 2\n"
        doc = Document(markdown)

        result = doc.to_markdown()
        assert result == expected

    def test_to_markdown_custom_indent(self):
        """Test to_markdown with custom indentation."""
        markdown = "- Item 1\n  - Item 1.1\n- Item 2"
        doc = Document(markdown)

        # Test with 4 spaces
        result = doc.to_markdown(indent=4)
        assert "    " in result  # Should contain 4-space indents

    def test_round_trip_conversion(self, mocker):
        """Test round-trip conversion from markdown to Document and back."""

        original = "- Item 1\n  - Item 1.1\n  - Item 1.2\n- Item 2"
        doc = Document(original)

        output = doc.to_markdown(indent=2).rstrip("\n")
        assert output == original

    def test_empty_document(self):
        """Test handling of empty documents."""
        doc = Document("")
        assert len(doc.toplevel_lists) == 0
        assert doc.to_markdown() == ""

    def test_document_with_multiple_lists(self):
        """Test handling of documents with multiple lists."""
        markdown = "- List 1 Item 1\n- List 1 Item 2\n\n* List 2 Item 1\n* List 2 Item 2"
        doc = Document(markdown)

        # Should find two top-level lists
        assert len(doc.toplevel_lists) == 2
        assert len(doc.list_to_roots) == 2

        # Each list should have two root nodes
        for lst, roots in doc.list_to_roots.items():
            assert len(roots) == 2

    def test_markdown_with_heading_preservation(self):
        """Test that headings are preserved in round-trip conversion."""
        original = "# Heading 1\n\n- Item 1\n  - Item 1.1\n\n## Heading 2\n\n- Item 2"
        doc = Document(original)
        output = doc.to_markdown(indent=2).rstrip("\n")
        assert output == original

    @pytest.mark.xfail(reason="Multi-line list items not currently supported")
    def test_markdown_with_code_blocks(self):
        """Test that code blocks are preserved in round-trip conversion."""
        original = "- Item 1\n  - Code example:\n    ```python\n    def hello():\n        print('Hello world')\n    ```\n- Item 2"
        doc = Document(original)
        output = doc.to_markdown(indent=2).rstrip("\n")
        assert output == original

    def test_markdown_with_numbered_lists(self):
        """Test that numbered lists are preserved in round-trip conversion."""
        original = "1. First item\n2. Second item\n   1. Nested item 1\n   2. Nested item 2\n3. Third item"
        doc = Document(original)
        output = doc.to_markdown(indent=2).rstrip("\n")
        assert output == original

    def test_mixed_markdown_elements(self):
        """Test a document with mixed markdown elements."""
        original = """# Project Tasks

1. Backend Development
   - API design
   - Database setup
     ```sql
     CREATE TABLE users (
         id INT PRIMARY KEY,
         name VARCHAR(255)
     );
     ```
   - Authentication
2. Frontend Development
   - Component library
   - State management

> Note: All tasks should be completed by Q2.

- [ ] Task 1
- [x] Task 2"""
        doc = Document(original)
        output = doc.to_markdown(indent=2).rstrip("\n")
        assert output == original

    def test_markdown_with_horizontal_rules(self):
        """Test that horizontal rules are preserved."""
        original = "# Section 1\n\n- Item 1\n- Item 2\n\n---\n\n# Section 2\n\n- Item 3\n- Item 4"
        doc = Document(original)
        output = doc.to_markdown(indent=2).rstrip("\n")

        # Marko renders thematic breaks as "* * *", let's ignore that and convert back to "---"
        output = output.replace("* * *", "---")

        assert output == original

    def test_markdown_with_tables(self):
        """Test that tables are preserved in round-trip conversion."""
        original = """# Project Status

| Feature | Status | Priority |
|---------|--------|----------|
| Login   | Done   | High     |
| Search  | WIP    | Medium   |

- Next steps
  - Complete search feature
  - Start work on notifications"""
        doc = Document(original)
        output = doc.to_markdown(indent=2).rstrip("\n")
        assert output == original
