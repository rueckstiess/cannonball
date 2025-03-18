import pytest
from unittest.mock import patch, MagicMock
import io
from marko.block import ListItem
from marko.element import Element
from cannonball.utils import (
    extract_node_marker_and_refs,
    get_raw_text_from_listtem,
    walk_list_items,
    print_ast,
)


class TestExtractNodeMarkerAndRef:
    def test_complete_extraction(self):
        """Test extraction of node marker, reference, and reference links."""
        text = "[?] This is a question ^ref123"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "?"
        assert ref == "ref123"
        assert ref_links == []

    def test_without_reference(self):
        """Test extraction with no reference."""
        text = "[!] Important note"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "!"
        assert ref is None
        assert ref_links == []

    def test_multi_character_node_marker(self):
        """Test extraction with multi-character markers."""
        # Simple two-character marker
        text = "[ai] Passing off to AI"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "ai"
        assert ref is None
        assert ref_links == []

        # Longer marker
        text = "[todo] Remember to fix this later"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "todo"
        assert ref is None
        assert ref_links == []

        # Marker with non-alphanumeric characters
        text = "[high-priority] Critical task ^important"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "high-priority"
        assert ref == "important"
        assert ref_links == []

        # Marker with reference
        text = "[api] Implement new endpoint ^endpoint123"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "api"
        assert ref == "endpoint123"
        assert ref_links == []

    def test_without_node_marker(self):
        """Test extraction with no node marker."""
        text = "Just some content ^ref456"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker is None
        assert ref == "ref456"
        assert ref_links == []

    def test_content_only(self):
        """Test extraction with only content."""
        text = "Plain text without markers or refs"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker is None
        assert ref is None
        assert ref_links == []

    def test_empty_checkbox(self):
        """Test extraction with only content."""
        text = "[ ] An open Task checkbox"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == " "
        assert ref is None
        assert ref_links == []

    def test_empty_string(self):
        """Test with empty string input."""
        text = ""
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker is None
        assert ref is None
        assert ref_links == []

    def test_multiple_references(self):
        """Test with multiple reference-like patterns, should extract only the first."""
        text = "[T] Test with ^ref1 and another ^ref2"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "T"
        assert ref == "ref1"
        assert ref_links == []

    def test_multiline_content(self):
        """Test with multiline content."""
        text = "[M] Line 1\nLine 2\nLine 3 ^multiref"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "M"
        assert ref == "multiref"
        assert ref_links == []

    def test_special_characters(self):
        """Test with special characters in marker and reference."""
        text = "[*] Content with special chars ^ref_123"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "*"
        assert ref == "ref_123"
        assert ref_links == []

    def test_whitespace_handling(self):
        """Test proper whitespace handling."""
        text = "[X]    Content with extra spaces    ^ref789    "
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "X"
        assert ref == "ref789"
        assert ref_links == []

    def test_reference_at_beginning(self):
        """Test with reference at the beginning of content."""
        text = "[R] ^ref123 Content after reference"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "R"
        assert ref == "ref123"
        assert ref_links == []

    def test_with_reference_links(self):
        """Test extraction with reference links."""
        text = "[?] Question with links to [[#^q1]] and [[#^q2]] ^q3"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "?"
        assert ref == "q3"
        assert ref_links == ["q1", "q2"]

    def test_with_only_reference_links(self):
        """Test extraction with only reference links."""
        text = "See questions [[#^q1]] and [[#^q2]]"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker is None
        assert ref is None
        assert ref_links == ["q1", "q2"]

    def test_with_reference_and_links(self):
        """Test extraction with both reference and reference links."""
        text = "[!] Important note related to [[#^item1]] ^note1"
        node_marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert node_marker == "!"
        assert ref == "note1"
        assert ref_links == ["item1"]


class TestGetRawTextFromListItem:
    def test_valid_list_item_with_paragraph(self):
        """Test extraction of text from a valid ListItem with a Paragraph."""
        from marko import Markdown
        from marko.inline import RawText, StrongEmphasis

        # Create a simple markdown parser
        md = Markdown()

        # Create real ListItem with plain text
        list_md = "- Sample text"
        ast = md.parse(list_md)
        list_item = ast.children[0].children[0]  # Get the ListItem inside the List

        result = get_raw_text_from_listtem(list_item)
        assert result == "Sample text"

        # Test with formatted text (bold)
        list_md_bold = "- Sample **bold** text"
        ast_bold = md.parse(list_md_bold)
        list_item_bold = ast_bold.children[0].children[0]  # Get the ListItem inside the List

        result_bold = get_raw_text_from_listtem(list_item_bold)
        assert result_bold == "Sample **bold** text"

    def test_empty_list_item(self):
        """Test with an empty ListItem (no children)."""
        from marko import Markdown

        # Create a real empty list item using the parser
        md = Markdown()
        # This creates a list item with an empty paragraph
        list_md = "- "
        ast = md.parse(list_md)
        list_item = ast.children[0].children[0]  # Get the ListItem inside the List

        result = get_raw_text_from_listtem(list_item)
        assert result == ""

    def test_list_item_without_paragraph(self):
        """Test with a ListItem whose first child is not a Paragraph."""
        from marko import Markdown

        # Create a real list item with a fenced code block
        md = Markdown()
        # Creating a list with a fenced code block
        list_md = "- ```\ncode block\n```"
        ast = md.parse(list_md)
        list_item = ast.children[0].children[0]  # Get the ListItem inside the List

        result = get_raw_text_from_listtem(list_item)
        # Check if we get a non-empty result - we don't assert specific content
        # because the rendered output might vary based on the implementation
        assert result.strip() != ""
        assert "```" in result

    def test_paragraph_without_text(self):
        """Test with a Paragraph that has no children."""
        # Parse a list item with empty paragraph
        from marko import Markdown

        md = Markdown()
        list_md = "- "
        ast = md.parse(list_md)
        list_item = ast.children[0].children[0]  # Get the ListItem inside the List

        result = get_raw_text_from_listtem(list_item)
        assert result == ""

    def test_non_list_item_input(self):
        """Test that assertion error is raised when input is not a ListItem."""
        # Use Element as non-ListItem
        mock_non_list_item = MagicMock(spec=Element)

        with pytest.raises(AssertionError):
            get_raw_text_from_listtem(mock_non_list_item)


class TestWalkListItems:
    def test_simple_walk(self):
        """Test walking a simple AST with one level of list items."""
        # Create a mock for the root element
        root = MagicMock(spec=Element)

        # Create list items
        list_item1 = MagicMock(spec=ListItem)
        list_item2 = MagicMock(spec=ListItem)

        # Set up the tree structure
        root.children = [list_item1, list_item2]
        list_item1.children = []
        list_item2.children = []

        # Walk the tree
        result = list(walk_list_items(root))

        # Check results
        assert len(result) == 2
        assert result[0][0] == list_item1  # First item
        assert result[0][1] is None  # No parent for first item
        assert result[0][2] == 0  # Level 0 for first item
        assert result[1][0] == list_item2  # Second item
        assert result[1][1] is None  # No parent for second item
        assert result[1][2] == 0  # Level 0 for second item

    def test_nested_walk(self):
        """Test walking an AST with nested list items."""
        # Create a mock for the root element
        root = MagicMock(spec=Element)

        # Create list items
        list_item1 = MagicMock(spec=ListItem)
        list_item2 = MagicMock(spec=ListItem)
        nested_item = MagicMock(spec=ListItem)

        # Set up the tree structure
        root.children = [list_item1, list_item2]
        list_item1.children = [nested_item]
        list_item2.children = []
        nested_item.children = []

        # Walk the tree
        result = list(walk_list_items(root))

        # Check results
        assert len(result) == 3
        assert result[0][0] == list_item1  # First item
        assert result[0][2] == 0  # Level 0 for first item
        assert result[1][0] == nested_item  # Nested item
        assert result[1][1] == list_item1  # Parent is first item
        assert result[1][2] == 1  # Level 1 for nested item
        assert result[2][0] == list_item2  # Second item
        assert result[2][2] == 0  # Level 0 for second item

    def test_with_apply_function(self):
        """Test walking an AST with an apply function."""
        # Create a mock for the root element
        root = MagicMock(spec=Element)

        # Create list items
        list_item = MagicMock(spec=ListItem)

        # Set up the tree structure
        root.children = [list_item]
        list_item.children = []

        # Define apply function
        def apply_fn(node, parent, level):
            return f"Item: {id(node)}, Parent: {id(parent) if parent else None}, Level: {level}"

        # Walk the tree with apply function
        result = list(walk_list_items(root, apply_fn=apply_fn))

        # Check results
        assert len(result) == 1
        assert isinstance(result[0], str)
        assert result[0].startswith("Item:")
        assert "Parent: None" in result[0]
        assert "Level: 0" in result[0]


class TestPrintAst:
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_print_ast(self, mock_stdout):
        """Test printing an AST with nested list items."""
        # Create a mock for the root element
        root = MagicMock(spec=Element)

        # Create list items
        list_item1 = MagicMock(spec=ListItem)
        list_item2 = MagicMock(spec=ListItem)
        nested_item = MagicMock(spec=ListItem)

        # Set up the tree structure
        root.children = [list_item1, list_item2]
        list_item1.children = [nested_item]
        list_item2.children = []
        nested_item.children = []

        # Mock get_raw_text_from_listtem function to return predictable text
        with patch("cannonball.utils.get_raw_text_from_listtem") as mock_get_text:
            mock_get_text.side_effect = (
                lambda item: "Item 1" if item == list_item1 else ("Nested Item" if item == nested_item else "Item 2")
            )

            # Print the AST
            print_ast(root)

            # Check output
            output = mock_stdout.getvalue().strip().split("\n")
            assert len(output) == 3
            assert output[0] == "- Item 1"
            assert output[1] == "\t- Nested Item"
            assert output[2] == "- Item 2"
