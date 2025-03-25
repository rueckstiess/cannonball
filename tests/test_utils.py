from cannonball.utils import (
    get_raw_text_from_listtem,
    walk_list_items,
    extract_node_marker_and_refs,
    extract_str_content,
    print_ast,
)
from marko import Markdown
from marko.block import ListItem
from textwrap import dedent
import io
import sys


class TestGetRawTextFromListItem:
    def test_get_raw_text_valid_listitem(self):
        """Test extracting text from a valid ListItem."""
        parser = Markdown()
        markdown = "- This is a list item"
        ast = parser.parse(markdown)
        list_item = ast.children[0].children[0]

        assert isinstance(list_item, ListItem)
        result = get_raw_text_from_listtem(list_item)
        assert result == "This is a list item"

    def test_get_raw_text_empty_listitem(self):
        """Test extracting text from an empty ListItem."""
        parser = Markdown()
        markdown = "- "
        ast = parser.parse(markdown)
        list_item = ast.children[0].children[0]

        assert isinstance(list_item, ListItem)
        result = get_raw_text_from_listtem(list_item)
        assert result == ""

    def test_get_raw_text_empty_line_break_listitem(self):
        """Test extracting text from a ListItem with empty text and line break."""
        parser = Markdown()
        markdown = "- \n"
        ast = parser.parse(markdown)
        list_item = ast.children[0].children[0]

        assert isinstance(list_item, ListItem)
        result = get_raw_text_from_listtem(list_item)
        assert result == ""


class TestWalkListItems:
    def test_walk_list_items_simple(self):
        """Test walking a simple list with no nesting."""
        parser = Markdown()
        markdown = dedent("""\
        - Item 1
        - Item 2
        - Item 3
        """)
        ast = parser.parse(markdown)

        items = list(walk_list_items(ast))
        assert len(items) == 3

        # Check that all are top-level (parent is None)
        for item, parent, level in items:
            assert parent is None
            assert level == 0

    def test_walk_list_items_nested(self):
        """Test walking a nested list."""
        parser = Markdown()
        markdown = dedent("""\
        - Item 1
            - Nested 1.1
                - Nested 1.1.1
            - Nested 1.2
            - Nested 1.3
                - Nested 1.3.1
        """)
        ast = parser.parse(markdown)

        items = list(walk_list_items(ast))
        assert len(items) == 6

        # Check specific nesting relationships
        # First item should have no parent
        assert items[0][1] is None
        assert items[0][2] == 0

        # Second item should have first item as parent
        assert items[1][1] == items[0][0]
        assert items[1][2] == 1

        # Third item should have second item as parent
        assert items[2][1] == items[1][0]
        assert items[2][2] == 2

    def test_walk_list_items_with_apply_function(self):
        """Test walking a list with an apply function."""
        parser = Markdown()
        markdown = dedent("""\
        - Item 1
            - Nested 1.1
        """)
        ast = parser.parse(markdown)

        # Define a simple apply function that returns a ID
        def apply_fn(node):
            if node is None:
                return None
            return id(node)

        items = list(walk_list_items(ast, apply_fn=apply_fn))
        assert len(items) == 2

        # Check that the apply function was used
        assert isinstance(items[0][0], int)  # Should be a ID now
        assert items[0][1] is None  # Root has no parent

        assert isinstance(items[1][0], int)
        assert isinstance(items[1][1], int)  # Parent should also be a ID


class TestExtractNodeMarkerAndRefs:
    def test_extract_node_marker_basic(self):
        """Test extracting a basic node marker."""
        text = "[ ] Task 1"
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert marker == " "
        assert ref is None
        assert ref_links == []

    def test_extract_node_marker_with_ref(self):
        """Test extracting a node marker with a reference."""
        text = "[x] Task 1 ^ref123"
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert marker == "x"
        assert ref == "ref123"
        assert ref_links == []

    def test_extract_node_marker_with_ref_links(self):
        """Test extracting a node marker with reference links."""
        text = "[!] Task 1 [[#^ref123]]"
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert marker == "!"
        assert ref is None
        assert ref_links == ["ref123"]

    def test_extract_node_marker_with_multiple_ref_links(self):
        """Test extracting a node marker with multiple reference links."""
        text = "[D] Decision [[#^ref1]] and [[#^ref2]]"
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert marker == "D"
        assert ref is None
        assert ref_links == ["ref1", "ref2"]

    def test_extract_node_marker_with_ref_and_links(self):
        """Test extracting a node marker with both ref and links."""
        text = "[?] Question [[#^link1]] ^myref"
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert marker == "?"
        assert ref == "myref"
        assert ref_links == ["link1"]

    def test_extract_node_marker_no_marker(self):
        """Test extracting with no marker."""
        text = "Plain text"
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        assert marker is None
        assert ref is None
        assert ref_links == []


class TestExtractStrContent:
    def test_extract_str_content_basic(self):
        """Test extracting content from simple text."""
        text = "- Task 1"
        content = extract_str_content(text)
        assert content == "Task 1"

    def test_extract_str_content_with_marker(self):
        """Test extracting content with a marker."""
        text = "- [x] Task 2"
        content = extract_str_content(text)
        assert content == "Task 2"

    def test_extract_str_content_with_ref(self):
        """Test extracting content with a reference."""
        text = "- Task 3 ^ref123"
        content = extract_str_content(text)
        assert content == "Task 3"

    def test_extract_str_content_with_marker_and_ref(self):
        """Test extracting content with both marker and reference."""
        text = "- [D] Task 4 ^ref123"
        content = extract_str_content(text)
        assert content == "Task 4"

    def test_extract_str_content_with_ref_links(self):
        """Test extracting content with reference links."""
        text = "- [?] Task 5 [[#^ref123]]"
        content = extract_str_content(text)
        assert content == "Task 5"


class TestPrintAst:
    def test_print_ast(self, monkeypatch):
        """Test print_ast function."""
        # Create a simple markdown string
        markdown = dedent("""\
        - Item 1
            - Nested 1.1
        """)

        # Parse the markdown to get an AST
        parser = Markdown()
        ast = parser.parse(markdown)

        # Redirect stdout to capture print output
        captured_output = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured_output)

        # Call the print_ast function
        print_ast(ast)

        # Get the captured output
        output = captured_output.getvalue()

        # Check that the output contains the expected text
        assert "Item 1" in output
        assert "- Nested 1.1" in output
