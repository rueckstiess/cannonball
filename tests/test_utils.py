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
    EdgeType,
    get_subgraph,
    extract_str_content,
)
from cannonball.nodes import AlternativeContainer

import networkx as nx
import unittest

from utils import with_markdown


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


class TestGetSubgraph(unittest.TestCase):
    def setUp(self):
        # Create a test graph for all tests
        graph = nx.DiGraph()
        graph.add_nodes_from(["n1", "n2", "n3", "n4", "n5", "n6"])
        graph.add_edges_from(
            [
                ("n1", "n2", {"type": "requires"}),
                ("n2", "n3", {"type": "requires"}),
                ("n3", "n4", {"type": "requires"}),
            ]
        )
        graph.add_edges_from(
            [
                ("n1", "n3", {"type": "references"}),
                ("n2", "n5", {"type": "references"}),
                ("n3", "n6", {"type": "references"}),
            ]
        )
        self.graph = graph

    def test_get_full_subgraph(self):
        # Test with no filters (should return the full graph)
        subgraph = get_subgraph(self.graph)
        self.assertEqual(len(subgraph.nodes), 6)
        self.assertEqual(len(subgraph.edges), 6)

    def test_get_subgraph_by_root(self):
        # Test with just a root node filter
        subgraph = get_subgraph(self.graph, root_node="n1")
        # n1 + all descendants considering all edge types
        self.assertEqual(len(subgraph.nodes), 6)
        self.assertTrue("n1" in subgraph.nodes)
        self.assertTrue("n2" in subgraph.nodes)
        self.assertTrue("n3" in subgraph.nodes)
        self.assertTrue("n4" in subgraph.nodes)
        self.assertTrue("n5" in subgraph.nodes)
        self.assertTrue("n6" in subgraph.nodes)

        # Test with a different root node
        subgraph = get_subgraph(self.graph, root_node="n2")
        # n2 + its descendants (n3,n4,n5,n6)
        self.assertEqual(len(subgraph.nodes), 5)
        self.assertTrue("n1" not in subgraph.nodes)
        self.assertTrue("n2" in subgraph.nodes)
        self.assertTrue("n3" in subgraph.nodes)
        self.assertTrue("n4" in subgraph.nodes)
        self.assertTrue("n5" in subgraph.nodes)
        self.assertTrue("n6" in subgraph.nodes)

        # Test with a leaf node
        subgraph = get_subgraph(self.graph, root_node="n6")
        self.assertEqual(len(subgraph.nodes), 1)  # Just n6
        self.assertTrue("n6" in subgraph.nodes)

    def test_get_subgraph_by_edge_type(self):
        # Test filtering by REQUIRES edges
        subgraph = get_subgraph(self.graph, edge_filter=EdgeType.REQUIRES)
        self.assertEqual(len(subgraph.nodes), 4)  # n1, n2, n3, n4
        self.assertEqual(len(subgraph.edges), 3)  # n1->n2, n2->n3, n3->n4

        # Test filtering by REFERENCES edges
        subgraph = get_subgraph(self.graph, edge_filter=EdgeType.REFERENCES)
        self.assertEqual(len(subgraph.nodes), 5)  # n1, n2, n3, n5, n6
        self.assertEqual(len(subgraph.edges), 3)  # n1->n3, n2->n5, n3->n6

    def test_get_subgraph_combined_filters(self):
        # Test with both root node and edge type filters
        subgraph = get_subgraph(self.graph, root_node="n2", edge_filter=EdgeType.REQUIRES)
        # When we filter by REQUIRES from n2, we should only get n2->n3->n4
        self.assertEqual(len(subgraph.nodes), 3)  # n2, n3, n4
        self.assertEqual(len(subgraph.edges), 2)  # n2->n3, n3->n4

        # Another combined test - n1 with REFERENCES edges only includes n1->n3
        subgraph = get_subgraph(self.graph, root_node="n1", edge_filter=EdgeType.REFERENCES)
        self.assertEqual(len(subgraph.nodes), 3)  # n1, n3, n6
        self.assertEqual(len(subgraph.edges), 2)  # n1->n3->n6

        # Test with n3 as root and REFERENCES edges
        subgraph = get_subgraph(self.graph, root_node="n3", edge_filter=EdgeType.REFERENCES)
        self.assertEqual(len(subgraph.nodes), 2)  # n3, n6
        self.assertEqual(len(subgraph.edges), 1)  # n3->n6

    def test_edge_cases(self):
        # Test with non-existent root node
        subgraph = get_subgraph(self.graph, root_node="non_existent")
        self.assertEqual(len(subgraph.nodes), 0)

        # Test with empty graph
        graph = nx.DiGraph()
        subgraph = get_subgraph(graph, root_node="n1")
        self.assertEqual(len(subgraph.nodes), 0)

        # Test with graph containing cycles (needs allow_cycles=True)
        cyclic_graph = nx.DiGraph()
        cyclic_graph.add_nodes_from(["c1", "c2", "c3"])
        cyclic_graph.add_edges_from([("c1", "c2"), ("c2", "c3"), ("c3", "c1")])

        subgraph = get_subgraph(cyclic_graph, root_node="c1")
        self.assertEqual(len(subgraph.nodes), 3)
        self.assertEqual(len(subgraph.edges), 3)

    def test_disconnected_components(self):
        # Create a graph with disconnected components

        disconn_graph = nx.DiGraph()
        disconn_graph.add_nodes_from(["d1", "d2", "e1", "e2"])
        disconn_graph.add_edges_from([("d1", "d2", {"type": "requires"})])
        disconn_graph.add_edges_from([("e1", "e2", {"type": "requires"})])

        # Test getting subgraph from one component
        subgraph = get_subgraph(disconn_graph, root_node="d1")
        self.assertEqual(len(subgraph.nodes), 2)
        self.assertTrue("d1" in subgraph.nodes)
        self.assertTrue("d2" in subgraph.nodes)
        self.assertTrue("e1" not in subgraph.nodes)
        self.assertTrue("e2" not in subgraph.nodes)

    def test_edge_type_as_function(self):
        # Test edge_type as a filtering function
        # Only include edges where the type contains the letter 'e'
        edge_filter = lambda data: "ref" in data.get("type", "")
        subgraph = get_subgraph(self.graph, edge_filter=edge_filter)

        # This should include only "references" edges
        self.assertEqual(len(subgraph.edges), 3)
        for u, v, attr in subgraph.edges(data=True):
            self.assertEqual(attr["type"], "references")

        # Test another custom filter - edges where type starts with 'r'
        starts_with_r = lambda data: data.get("type", "").startswith("r")
        subgraph = get_subgraph(self.graph, edge_filter=starts_with_r)

        self.assertEqual(len(subgraph.edges), 6)  # All edges in our test graph start with 'r'

        # Test filter that matches nothing
        no_match = lambda data: data.get("type", "") == "nonexistent"
        subgraph = get_subgraph(self.graph, edge_filter=no_match)

        self.assertEqual(len(subgraph.edges), 0)

    def test_node_type_as_type(self):
        # Create a new graph with node types
        typed_graph = nx.DiGraph()

        # Add nodes with different types
        typed_graph.add_node("n1")
        typed_graph.add_node("n2")
        typed_graph.add_node(3)
        typed_graph.add_node(4)

        # Add edges between them
        typed_graph.add_edge("n1", "n2")
        typed_graph.add_edge("n1", 3)
        typed_graph.add_edge("n2", 4)
        typed_graph.add_edge(3, 4)

        # Test filtering by node type
        subgraph = get_subgraph(typed_graph, node_filter=str)

        self.assertEqual(len(subgraph), 2)
        for node in subgraph.nodes:
            self.assertIsInstance(node, str)

        # Test with the other type
        subgraph = get_subgraph(typed_graph, node_filter=int)

        self.assertEqual(len(subgraph.nodes), 2)
        for node in subgraph.nodes:
            self.assertIsInstance(node, int)

    def test_node_type_as_function(self):
        # Create a graph with various node attributes
        attr_graph = nx.DiGraph()

        # Add nodes with different attributes
        attr_graph.add_node(False)
        attr_graph.add_node(True)
        attr_graph.add_node(12.4)
        attr_graph.add_node("foo")

        # Add edges between them
        attr_graph.add_edge(False, True)
        attr_graph.add_edge(False, 12.4)
        attr_graph.add_edge(True, "foo")
        attr_graph.add_edge(12.4, "foo")

        # Test filtering by a function that checks node attributes
        filter_bool = lambda node: isinstance(node, bool)
        subgraph = get_subgraph(attr_graph, node_filter=filter_bool)

        self.assertEqual(len(subgraph.nodes), 2)
        for node in subgraph.nodes:
            self.assertIsInstance(node, bool)

    def test_combined_node_and_edge_filters(self):
        # Create a graph with both node and edge attributes
        combined_graph = nx.DiGraph()

        # Add nodes with attributes
        combined_graph.add_node("n1")
        combined_graph.add_node("n2")
        combined_graph.add_node(3)
        combined_graph.add_node(4.4)

        # Add edges with attributes
        combined_graph.add_edge("n1", "n2", relation="strong")
        combined_graph.add_edge("n1", 3, relation="weak")
        combined_graph.add_edge("n2", 4.4, relation="medium")
        combined_graph.add_edge(3, 4.4, relation="strong")

        # Define filters
        string_nodes = lambda node: isinstance(node, str)
        strong_relation = lambda edge: edge.get("relation") == "strong"

        # Test combining node and edge filters
        subgraph = get_subgraph(combined_graph, node_filter=string_nodes, edge_filter=strong_relation)

        # This should only include n1 and n2 nodes with the strong relation between them
        self.assertEqual(len(subgraph.nodes), 2)
        self.assertEqual(len(subgraph.edges), 1)
        self.assertTrue(("n1", "n2") in subgraph.edges())

        # Test with root_node as well
        subgraph = get_subgraph(
            combined_graph,
            root_node="n1",
            node_filter=lambda node: isinstance(node, (str, float)),
            edge_filter=lambda edge: edge.get("relation") != "weak",
        )

        # Should include n1 -> n2 -> n4 path (but not n3 which is reachable via weak relation)
        self.assertEqual(len(subgraph.nodes), 3)
        self.assertTrue("n1" in subgraph.nodes)
        self.assertTrue("n2" in subgraph.nodes)
        self.assertTrue(4.4 in subgraph.nodes)
        self.assertFalse(3 in subgraph.nodes)
        self.assertEqual(len(subgraph.edges), 2)  # n1->n2 and n2->n4


class TestExtractStrContent(unittest.TestCase):
    def test_extract_str_content(self):
        """Test the get_content function."""
        test_cases = [
            ("- [x] Task 1", "Task 1"),
            ("- [ ] Task 2", "Task 2"),
            ("  - [D] Task 3 [[#^ref]]", "Task 3"),
            ("- [a] Task 4 ^ref", "Task 4"),
            ("      - Task 5", "Task 5"),
        ]
        for input_str, expected_output in test_cases:
            assert extract_str_content(input_str) == expected_output, f"Failed for input: {input_str}"


@with_markdown("""\
- [?] Question
    - [a] Alternative
""")
class TestSubGraphFromMarkdown:
    def test_get_alternatives_subgraph(self, graph_fixture):
        graph = graph_fixture["graph"]
        nodes = graph_fixture["nodes_by_name"]
        assert len(graph) == 2
        assert len(graph.edges) == 1

        subgraph = get_subgraph(
            graph, root_node=nodes["Question"], node_filter=lambda n: not isinstance(n, AlternativeContainer)
        )
        if len(subgraph) == 0:
            return False

        alternatives = list(nx.dfs_preorder_nodes(subgraph, source=nodes["Question"]))
        assert len(alternatives) > 0
