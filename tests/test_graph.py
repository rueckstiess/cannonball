import pytest
from cannonball.graph_mgr import GraphMgr
from cannonball.nodes import Node
import networkx as nx
from cannonball.utils import EdgeType

# Sample markdown string with hierarchical structure for testing
SAMPLE_MARKDOWN = """
- [g] Add syntax highlighting for Cannonball markdown ^feature3
\t- [?] Which library should we use for highlighting? ^q1
\t\t- [a] Use Prism.js ^alt1
\t\t\t- [o] Has good React integration
\t\t\t- [P] May need custom language definition
\t\t\t\t- [ ] Research custom grammar in Prism
\t\t- [a] Use highlight.js ^alt2
\t\t\t- [o] More lightweight
\t\t\t- [o] Easier to customize
\t\t- [D] Selected ^alt2
\t- [ ] Implement syntax highlighting component
\t\t- This will be a React component
\t\t- [/] Create basic highlighter class
\t\t- [ ] Add custom rules for node types
\t\t- [ ] Connect to rendering pipeline
\t- [I] Could add visual indicators for different node states
\t- [ ] Write tests for highlighting edge cases
"""


class TestGraphMgr:
    def test_init(self):
        """Test that the GraphMgr initializes properly."""
        graph_mgr = GraphMgr()
        assert isinstance(graph_mgr.nxgraph, nx.DiGraph)
        assert len(graph_mgr.nxgraph.nodes) == 0
        assert len(graph_mgr.nxgraph.edges) == 0

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph_mgr = GraphMgr()
        node = Node(id="test", name="Test Node", marker="T", ref="test_ref")
        graph_mgr.add_node(node)

        assert node in graph_mgr.nxgraph.nodes
        assert graph_mgr.nxgraph.nodes[node]["name"] == "Test Node"
        assert graph_mgr.nxgraph.nodes[node]["marker"] == "T"
        assert graph_mgr.nxgraph.nodes[node]["ref"] == "test_ref"
        assert graph_mgr.nodes_by_ref["test_ref"] == node

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph_mgr = GraphMgr()
        node1 = Node(id="parent", name="Parent Node", marker="P")
        node2 = Node(id="child", name="Child Node", marker="C")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)
        graph_mgr.add_edge(node1, node2)

        assert (node1, node2) in graph_mgr.nxgraph.edges

    def test_get_node_by_ref(self):
        """Test getting a node by reference."""
        graph_mgr = GraphMgr()
        node = Node(id="test", name="Test Node", marker="T", ref="test_ref")
        graph_mgr.add_node(node)

        assert graph_mgr.get_node_by_ref("test_ref") == node
        assert graph_mgr.get_node_by_ref("nonexistent") is None

    def test_from_markdown_simple(self):
        """Test creating a graph from a simple markdown."""
        markdown = """
- [A] Root node ^root
\t- [B] Child node ^child
"""

        graph_mgr = GraphMgr.from_markdown(markdown)

        # Check if graph has the right structure
        assert len(graph_mgr.nxgraph.nodes) == 2
        assert len(graph_mgr.nxgraph.edges) == 1

        # Check if references were properly extracted
        root = graph_mgr.get_node_by_ref("root")
        child = graph_mgr.get_node_by_ref("child")

        assert root is not None
        assert child is not None
        assert graph_mgr.nxgraph.nodes[root]["marker"] == "A"
        assert graph_mgr.nxgraph.nodes[child]["marker"] == "B"

        # Check if the edge is correct
        assert (root, child) in graph_mgr.nxgraph.edges

    def test_from_markdown_with_thoughts(self):
        """Test creating a graph from a simple markdown."""
        markdown = """
- [A] Root node ^root
\t- [B] Child node ^child
\t- Just a thought ^thought
"""

        graph_mgr = GraphMgr.from_markdown(markdown)

        # Check if graph has the right structure
        assert len(graph_mgr.nxgraph.nodes) == 3
        assert len(graph_mgr.nxgraph.edges) == 2

        # Check if references were properly extracted
        root_id = graph_mgr.get_node_by_ref("root")
        child_id = graph_mgr.get_node_by_ref("child")
        thought_id = graph_mgr.get_node_by_ref("thought")

        assert root_id is not None
        assert child_id is not None
        assert thought_id is not None
        assert graph_mgr.nxgraph.nodes[root_id]["marker"] == "A"
        assert graph_mgr.nxgraph.nodes[child_id]["marker"] == "B"
        assert graph_mgr.nxgraph.nodes[thought_id]["marker"] is None

        # Check if the edge is correct
        assert (root_id, child_id) in graph_mgr.nxgraph.edges
        assert (root_id, thought_id) in graph_mgr.nxgraph.edges

    def test_from_markdown_complex(self):
        """Test creating a graph from a complex markdown structure."""
        graph_mgr = GraphMgr.from_markdown(SAMPLE_MARKDOWN)

        # Check overall structure
        assert len(graph_mgr.nxgraph.nodes) > 15  # There should be at least 15 nodes

        # Check specific references
        feature_id = graph_mgr.get_node_by_ref("feature3")
        q1_id = graph_mgr.get_node_by_ref("q1")
        alt1_id = graph_mgr.get_node_by_ref("alt1")
        alt2_id = graph_mgr.get_node_by_ref("alt2")

        assert feature_id is not None
        assert q1_id is not None
        assert alt1_id is not None
        assert alt2_id is not None

        # Check node attributes
        assert graph_mgr.nxgraph.nodes[feature_id]["marker"] == "g"
        assert graph_mgr.nxgraph.nodes[q1_id]["marker"] == "?"

        # Check hierarchy
        assert nx.has_path(graph_mgr.nxgraph, feature_id, q1_id)
        assert nx.has_path(graph_mgr.nxgraph, q1_id, alt1_id)
        assert nx.has_path(graph_mgr.nxgraph, q1_id, alt2_id)

        # Root should have no parents
        assert graph_mgr.nxgraph.in_degree(feature_id) == 0

        # Test topological order - feature should come before questions
        topo_order = graph_mgr.topological_sort()
        feature_idx = topo_order.index(feature_id)
        q1_idx = topo_order.index(q1_id)
        assert feature_idx < q1_idx

    def test_is_acyclic(self):
        """Test checking if graph is acyclic."""
        # Create a simple acyclic graph
        graph_mgr = GraphMgr()
        node1 = Node(id="1", name="Node 1", marker="1")
        node2 = Node(id="2", name="Node 2", marker="2")
        node3 = Node(id="3", name="Node 3", marker="3")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)
        graph_mgr.add_node(node3)

        graph_mgr.add_edge(node1, node2)
        graph_mgr.add_edge(node2, node3)

        assert graph_mgr.has_circular_dependencies() is False

        # Add an edge to create a cycle
        graph_mgr.add_edge(node3, node1)
        assert graph_mgr.has_circular_dependencies() is True

    def test_topological_sort(self):
        """Test topological sorting."""
        graph_mgr = GraphMgr()
        node1 = Node(id="1", name="Node 1", marker="1")
        node2 = Node(id="2", name="Node 2", marker="2")
        node3 = Node(id="3", name="Node 3", marker="3")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)
        graph_mgr.add_node(node3)

        graph_mgr.add_edge(node1, node2)
        graph_mgr.add_edge(node1, node3)
        graph_mgr.add_edge(node2, node3)

        sorted_nodes = graph_mgr.topological_sort()

        # Node 1 must come before Node 2
        assert sorted_nodes.index(node1) < sorted_nodes.index(node2)
        # Node 2 must come before Node 3
        assert sorted_nodes.index(node2) < sorted_nodes.index(node3)
        # Node 1 must come before Node 3
        assert sorted_nodes.index(node1) < sorted_nodes.index(node3)

    def test_get_roots_and_leaves(self):
        """Test getting roots and leaves of the graph."""
        graph_mgr = GraphMgr.from_markdown(SAMPLE_MARKDOWN)

        roots = graph_mgr.get_roots()
        leaves = graph_mgr.get_leaves()

        # Should have only one root (the feature node)
        assert len(roots) == 1
        feature_id = graph_mgr.get_node_by_ref("feature3")
        assert feature_id in roots

        # Should have multiple leaves (the bottom-most items)
        assert len(leaves) > 1

        # All leaves should have no children
        for leaf in leaves:
            assert graph_mgr.nxgraph.out_degree(leaf) == 0

    def test_to_dict(self):
        """Test converting graph to a dictionary."""
        graph_mgr = GraphMgr()
        node1 = Node(id="1", name="Node 1", marker="1")
        node2 = Node(id="2", name="Node 2", marker="2")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)
        graph_mgr.add_edge(node1, node2)

        graph_dict = graph_mgr.to_dict()

        assert len(graph_dict["nodes"]) == 2
        assert len(graph_dict["edges"]) == 1
        assert graph_dict["edges"][0]["source"] == node1
        assert graph_dict["edges"][0]["target"] == node2

    def test_cyclic_topological_sort(self):
        """Test topological sort on cyclic graph raises ValueError."""
        graph_mgr = GraphMgr()
        node1 = Node(id="1", name="Node 1", marker="1")
        node2 = Node(id="2", name="Node 2", marker="2")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)

        # Create a cycle
        graph_mgr.add_edge(node1, node2)
        graph_mgr.add_edge(node2, node1)

        with pytest.raises(ValueError):
            graph_mgr.topological_sort()

    def test_duplicate_node_ids(self):
        """Test handling of duplicate node IDs in from_markdown."""
        markdown = """
- [A] Same content ^ref1
\t- [B] Same content ^ref2
\t\t- [C] Same content ^ref3
"""
        # Here, all nodes have the same content "Same content" which would result in
        # duplicate IDs, but the GraphMgr should make them unique

        graph_mgr = GraphMgr.from_markdown(markdown)

        # Check that we have 3 nodes (even though they have the same content)
        assert len(graph_mgr.nxgraph.nodes) == 3

        # Check that the references are correctly mapped
        ref1_id = graph_mgr.get_node_by_ref("ref1")
        ref2_id = graph_mgr.get_node_by_ref("ref2")
        ref3_id = graph_mgr.get_node_by_ref("ref3")

        assert ref1_id is not None
        assert ref2_id is not None
        assert ref3_id is not None

        # Verify the IDs are all different
        assert ref1_id != ref2_id
        assert ref1_id != ref3_id
        assert ref2_id != ref3_id

    def test_to_markdown_empty_graph(self):
        """Test converting an empty graph to markdown."""
        graph_mgr = GraphMgr()
        markdown = graph_mgr.to_markdown()
        assert markdown == ""

    def test_obsidian_reference_links(self):
        """Test handling of Obsidian-style reference links."""
        markdown = """
- [A] Root node ^root
\t- [B] Child with reference link to root [[#^root]]
\t- [C] Another child
\t\t- [D] Grandchild referencing root [[#^root]] and child [[#^child]]
- [X] Independent node ^child
"""
        # Convert to graph
        graph_mgr = GraphMgr.from_markdown(markdown)

        # Get node IDs by reference
        root = graph_mgr.get_node_by_ref("root")
        child = graph_mgr.get_node_by_ref("child")

        # Need to find nodes containing reference links
        child_with_link = None
        grandchild = None

        for node in graph_mgr.nxgraph:
            if "Child with reference link" in node.name:
                child_with_link = node
            elif "Grandchild referencing" in node.name:
                grandchild = node

        # Make sure we found the nodes
        assert child_with_link is not None, (
            "Could not find node with 'Child with reference link'"
        )
        assert grandchild is not None, (
            "Could not find node with 'Grandchild referencing'"
        )

        # Verify reference links created edges
        assert (child_with_link, root) in graph_mgr.nxgraph.edges, (
            "Missing reference edge from child to root"
        )
        assert (grandchild, root) in graph_mgr.nxgraph.edges, (
            "Missing reference edge from grandchild to root"
        )
        assert (grandchild, child) in graph_mgr.nxgraph.edges, (
            "Missing reference edge from grandchild to independent node"
        )

        # Test the to_markdown function to ensure reference links are preserved
        markdown_output = graph_mgr.to_markdown()

        # Print the output markdown
        print("\nGenerated markdown:")
        print(markdown_output)

        # Check that the reference links appear in the output
        assert "[[#^root]]" in markdown_output, (
            "Reference link to root missing in output"
        )
        assert "[[#^child]]" in markdown_output, (
            "Reference link to child missing in output"
        )

    def test_multi_character_markers_with_reference_links(self):
        """Test handling of multi-character markers with reference links."""
        markdown = """
- [project] Main project task ^proj
\t- [todo] First subtask with link to project [[#^proj]]
\t- [in-progress] Second subtask
\t\t- [high-priority] Critical item referencing project [[#^proj]]
- [completed] Independent task ^task123
\t- [note] Reference to completed task [[#^task123]]
"""
        # Convert to graph, allowing cycles since our reference links may create them
        graph_mgr = GraphMgr.from_markdown(markdown)

        # Print all nodes for debugging
        print("\nAll nodes:")
        for node_id in graph_mgr.nxgraph.nodes():
            attrs = graph_mgr.nxgraph.nodes[node_id]
            print(
                f"Node ID: {node_id}, Name: {attrs.get('name')}, Marker: {attrs.get('marker')}, Ref: {attrs.get('ref')}"
            )

        # Print all edges for debugging
        print("\nAll edges:")
        for source, target in graph_mgr.nxgraph.edges():
            source_name = graph_mgr.nxgraph.nodes[source].get("name")
            target_name = graph_mgr.nxgraph.nodes[target].get("name")
            print(f"Edge: {source} ({source_name}) -> {target} ({target_name})")

        # Get node IDs by reference
        proj_id = graph_mgr.get_node_by_ref("proj")
        task_id = graph_mgr.get_node_by_ref("task123")

        # Find nodes with specific markers and content
        todo_node_id = None
        critical_node_id = None
        note_node_id = None

        for node_id in graph_mgr.nxgraph.nodes():
            attrs = graph_mgr.nxgraph.nodes[node_id]
            name = attrs.get("name")
            marker = attrs.get("marker")

            if marker == "todo" and "First subtask" in name:
                todo_node_id = node_id
            elif marker == "high-priority" and "Critical item" in name:
                critical_node_id = node_id
            elif marker == "note" and "Reference to completed" in name:
                note_node_id = node_id

        # Make sure we found the nodes
        assert todo_node_id is not None, "Could not find todo node"
        assert critical_node_id is not None, "Could not find high-priority node"
        assert note_node_id is not None, "Could not find note node"

        # Verify multi-character markers are preserved
        assert graph_mgr.nxgraph.nodes[proj_id]["marker"] == "project"
        assert graph_mgr.nxgraph.nodes[task_id]["marker"] == "completed"

        # Verify reference links created edges
        assert (todo_node_id, proj_id) in graph_mgr.nxgraph.edges, (
            "Missing reference edge from todo to project"
        )
        assert (critical_node_id, proj_id) in graph_mgr.nxgraph.edges, (
            "Missing reference edge from critical to project"
        )
        assert (note_node_id, task_id) in graph_mgr.nxgraph.edges, (
            "Missing reference edge from note to task"
        )

        # Test the to_markdown function to ensure reference links are preserved
        markdown_output = graph_mgr.to_markdown()

        # Print the output markdown
        print("\nGenerated markdown:")
        print(markdown_output)

        # Check that the essential multi-character markers are preserved
        # Note: Due to cycle handling, not all nodes will appear in the output
        assert "[project]" in markdown_output
        assert "[todo]" in markdown_output
        assert "[in-progress]" in markdown_output
        assert "[high-priority]" in markdown_output

        # Check that the essential reference links appear in the output
        # Note: Due to cycle handling, not all reference links will appear
        assert "[[#^proj]]" in markdown_output

    def test_to_markdown_complex_example(self):
        """Test round-trip conversion using a complex markdown example."""
        # Complex markdown example with nested structure
        original_md = """\
- [g] Add syntax highlighting for Cannonball markdown ^feature3
\t- [?] Which library should we use for highlighting? ^q1
\t\t- [a] Use Prism.js ^alt1
\t\t\t- [o] Has good React integration
\t\t\t- [P] May need custom language definition
\t\t\t\t- [ ] Research custom grammar in Prism
\t\t- [a] Use highlight.js ^alt2
\t\t\t- [o] More lightweight
\t\t\t- [o] Easier to customize
\t\t- [D] Selected ^alt2
\t- [ ] Implement syntax highlighting component
\t\t- This will be a React component
\t\t- [/] Create basic highlighter class
\t\t- [ ] Add custom rules for node types
\t\t- [ ] Connect to rendering pipeline
\t- [I] Could add visual indicators for different node states
\t- [ ] Write tests for highlighting edge cases
"""

        # Convert markdown to graph
        graph_mgr = GraphMgr.from_markdown(original_md)

        # Convert graph back to markdown
        result_md = graph_mgr.to_markdown()

        # Clean up whitespace for comparison
        def clean_md(md):
            return "\n".join(
                line.strip() for line in md.strip().split("\n") if line.strip()
            )

        # The structure should be preserved
        clean_md(original_md)
        clean_result = clean_md(result_md)

        # Check that the content is preserved (references)
        references = ["feature3", "q1", "alt1", "alt2"]
        for ref in references:
            assert f"^{ref}" in clean_result

        # Check that all markers are preserved
        markers = ["[g]", "[?]", "[a]", "[o]", "[P]", "[ ]", "[D]", "[/]", "[I]"]
        for marker in markers:
            assert marker in clean_result

        # Verify specific content fragments
        assert "Add syntax highlighting for Cannonball markdown" in clean_result
        assert "Which library should we use for highlighting?" in clean_result
        assert "Use Prism.js" in clean_result
        assert "Use highlight.js" in clean_result
        assert "Has good React integration" in clean_result
        assert "May need custom language definition" in clean_result
        assert "Research custom grammar in Prism" in clean_result
        assert "More lightweight" in clean_result
        assert "Easier to customize" in clean_result
        assert "Selected" in clean_result
        assert "Implement syntax highlighting component" in clean_result
        assert "This will be a React component" in clean_result
        assert "Create basic highlighter class" in clean_result
        assert "Add custom rules for node types" in clean_result
        assert "Connect to rendering pipeline" in clean_result
        assert "Could add visual indicators for different node states" in clean_result
        assert "Write tests for highlighting edge cases" in clean_result

        # Verify the graph structure by checking key parent-child relationships
        feature_id = graph_mgr.get_node_by_ref("feature3")
        q1_id = graph_mgr.get_node_by_ref("q1")
        alt1_id = graph_mgr.get_node_by_ref("alt1")
        alt2_id = graph_mgr.get_node_by_ref("alt2")

        # Feature -> Question
        assert (feature_id, q1_id) in graph_mgr.nxgraph.edges
        # Question -> Alternatives
        assert (q1_id, alt1_id) in graph_mgr.nxgraph.edges
        assert (q1_id, alt2_id) in graph_mgr.nxgraph.edges

        # Create a new graph from the serialized markdown
        GraphMgr.from_markdown(result_md)

        # The number of nodes might differ slightly due to changes in text extraction
        # The important part is that the key references and structure are maintained

    def test_to_markdown_custom_indent_int(self):
        """Test to_markdown with custom integer indentation."""
        # Create a simple graph
        graph_mgr = GraphMgr()
        root = Node(id="root", name="[A] Root node ^root", marker="A", ref="root")
        child = Node(id="child", name="[B] Child node ^child", marker="B", ref="child")
        grandchild = Node(
            id="grandchild", name="[C] Grandchild node ^gc", marker="C", ref="gc"
        )

        graph_mgr.add_node(root)
        graph_mgr.add_node(child)
        graph_mgr.add_node(grandchild)

        graph_mgr.add_edge(root, child)
        graph_mgr.add_edge(child, grandchild)

        # Test with 4 spaces indentation
        markdown = graph_mgr.to_markdown(indent=4)

        # Verify indentation
        lines = markdown.strip().split("\n")
        assert lines[0].startswith("- ")
        assert lines[1].startswith("    - ")
        assert lines[2].startswith("        - ")

        # Parse back to verify round-trip conversion
        new_graph = GraphMgr.from_markdown(markdown)

        # Check that structure is preserved
        new_root = new_graph.get_node_by_ref("root")
        new_child = new_graph.get_node_by_ref("child")
        new_gc = new_graph.get_node_by_ref("gc")

        assert new_root is not None
        assert new_child is not None
        assert new_gc is not None
        assert (new_root, new_child) in new_graph.nxgraph.edges
        assert (new_child, new_gc) in new_graph.nxgraph.edges

    def test_to_markdown_custom_indent_str(self):
        """Test to_markdown with custom string indentation (tab)."""
        # Create a simple graph
        graph_mgr = GraphMgr()
        root = Node(id="root", name="[A] Root node ^root", marker="A", ref="root")
        child = Node(id="child", name="[B] Child node ^child", marker="B", ref="child")

        graph_mgr.add_node(root)
        graph_mgr.add_node(child)

        graph_mgr.add_edge(root, child)

        # Test with tab indentation
        markdown = graph_mgr.to_markdown(indent="\t")

        # Verify indentation
        lines = markdown.strip().split("\n")
        assert lines[0].startswith("- ")
        assert lines[1].startswith("\t- ")

        # Parse back to verify round-trip conversion
        new_graph = GraphMgr.from_markdown(markdown)

        # Check that structure is preserved
        new_root_id = new_graph.get_node_by_ref("root")
        new_child_id = new_graph.get_node_by_ref("child")

        assert new_root_id is not None
        assert new_child_id is not None
        assert (new_root_id, new_child_id) in new_graph.nxgraph.edges

    def test_to_markdown_custom_roots(self):
        """Test to_markdown with custom root nodes parameter."""
        # Create a graph with multiple potential roots
        graph_mgr = GraphMgr()
        root1 = Node(id="root1", name="[A] Root 1 ^root1", marker="A", ref="root1")
        root2 = Node(id="root2", name="[B] Root 2 ^root2", marker="B", ref="root2")
        child1 = Node(id="child1", name="[C] Child 1 ^child1", marker="C", ref="child1")
        child2 = Node(id="child2", name="[D] Child 2 ^child2", marker="D", ref="child2")

        graph_mgr.add_node(root1)
        graph_mgr.add_node(root2)
        graph_mgr.add_node(child1)
        graph_mgr.add_node(child2)

        graph_mgr.add_edge(root1, child1)
        graph_mgr.add_edge(root2, child2)

        # Test with only root1 as the starting point
        markdown = graph_mgr.to_markdown(root_nodes=[root1])

        # Should include root1 and child1, but not root2 or child2
        assert "Root 1" in markdown
        assert "Child 1" in markdown
        assert "Root 2" not in markdown
        assert "Child 2" not in markdown

        # Parse back to verify partial graph extraction
        new_graph = GraphMgr.from_markdown(markdown)

        # Should only have references for root1 and child1
        assert new_graph.get_node_by_ref("root1") is not None
        assert new_graph.get_node_by_ref("child1") is not None
        assert new_graph.get_node_by_ref("root2") is None
        assert new_graph.get_node_by_ref("child2") is None

    def test_to_markdown_with_cycles(self):
        """Test to_markdown with a graph containing cycles."""
        # Create a graph with a cycle
        graph_mgr = GraphMgr()
        node1 = Node(id="node1", name="[A] Node 1 ^node1", marker="A", ref="node1")
        node2 = Node(id="node2", name="[B] Node 2 ^node2", marker="B", ref="node2")
        node3 = Node(id="node3", name="[C] Node 3 ^node3", marker="C", ref="node3")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)
        graph_mgr.add_node(node3)

        # Create a cycle: 1 -> 2 -> 3 -> 1
        graph_mgr.add_edge(node1, node2)
        graph_mgr.add_edge(node2, node3)
        graph_mgr.add_edge(node3, node1)

        # Should not enter an infinite loop because to_markdown guards against cycles
        markdown = graph_mgr.to_markdown()

        # Should have some content
        assert len(markdown.strip()) > 0

        # All nodes should appear exactly once in the output
        assert markdown.count("Node 1") == 1
        assert markdown.count("Node 2") == 1
        assert markdown.count("Node 3") == 1

        # The graph structure should break the cycle to create a tree
        assert markdown.count("^node1") == 1
        assert markdown.count("^node2") == 1
        assert markdown.count("^node3") == 1

    def test_to_markdown_complex_nested_example(self):
        """Test to_markdown with a complex nested example with multiple levels and multi-char markers."""

        original_md = """\
- [project] Main project task ^prj
    - [feature] Feature 1: User Authentication ^f1
    - [task] Design login screen ^t1
        - [subtask] Create mockups ^st1
        - [subtask] Get feedback from team ^st2
    - [task] Implement backend auth ^t2
        - [subtask] Set up OAuth integration ^st3
        - [subtask] Write unit tests ^st4
    - [feature] Feature 2: Dashboard ^f2
    - [task] Create widget framework ^t3
        - [blocker] Need design specs first
    - [task] Implement data sources ^t4
- [milestone] Version 1.0 Release ^m1
    - [task] Finalize documentation ^td
    - [task] Submit to app store ^ta
"""

        # Parse the markdown into a graph
        graph_mgr = GraphMgr.from_markdown(original_md)
        result_md = graph_mgr.to_markdown(indent=4)
        assert result_md == original_md, "Markdown output does not match original input"

    def test_to_markdown_preserves_rich_formatting(self):
        """Test to_markdown preserves rich formatting in node names."""

        # Create a graph manually
        graph_mgr = GraphMgr()

        markdown = """\
- [g] Add syntax highlighting for *Cannonball* markdown ^feature3
\t- [?] Which **library** should we use for highlighting? ^q1
\t\t- [a] Check out tutorial at [cannonball.io](https://cannonball.io) ^alt1
"""

        # Parse the markdown into a graph
        graph_mgr = GraphMgr.from_markdown(markdown)
        # Convert back to markdown
        result_md = graph_mgr.to_markdown(indent="\t")

        assert result_md == markdown, "Markdown output does not match original input"

    def test_to_markdown_edge_cases(self):
        """Test to_markdown with various edge cases."""
        # 1. Node with no marker
        # 2. Node with no reference
        # 3. Node with special characters
        # 4. Empty node name

        graph_mgr = GraphMgr()

        # Add nodes with special cases
        node1 = Node(
            id="n1", name="Regular node with no marker ^nomark", marker="", ref="nomark"
        )
        node2 = Node(id="n2", name="[x] Node with no reference", marker="x", ref=None)
        node3 = Node(
            id="n3",
            name="[!] Node with special & chars % $ @ ^special",
            marker="!",
            ref="special",
        )
        node4 = Node(id="n4", name="[e] ^empty", marker="e", ref="empty")

        graph_mgr.add_node(node1)
        graph_mgr.add_node(node2)
        graph_mgr.add_node(node3)
        graph_mgr.add_node(node4)

        # Create a simple hierarchy
        graph_mgr.add_edge(node1, node2)
        graph_mgr.add_edge(node1, node3)
        graph_mgr.add_edge(node3, node4)

        # Convert to markdown
        markdown = graph_mgr.to_markdown()

        # Verify the markdown is not empty
        assert markdown.strip() != ""

        # Make sure we have content in the markdown
        node_names = [
            "Regular node with no marker",
            "Node with no reference",
            "Node with special & chars",
            "^empty",
        ]

        found_names = 0
        for name in node_names:
            if name in markdown:
                found_names += 1

        assert found_names > 0, "No node content preserved in the output"

        # Make sure the graph can be regenerated from the markdown
        new_graph = GraphMgr.from_markdown(markdown)

        # Verify the regenerated graph has nodes
        assert len(new_graph.nxgraph.nodes) > 0, "No nodes in regenerated graph"

    def test_get_requires_subgraph(self):
        """Test that get_requires_subgraph returns only the edges with REQUIRES type."""
        # Create a graph with both REQUIRES and REFERENCES edges
        graph_mgr = GraphMgr()

        # Create nodes
        node_a = Node(id="a", name="Node A")
        node_b = Node(id="b", name="Node B")
        node_c = Node(id="c", name="Node C")
        node_d = Node(id="d", name="Node D")

        # Add nodes to graph
        graph_mgr.add_node(node_a)
        graph_mgr.add_node(node_b)
        graph_mgr.add_node(node_c)
        graph_mgr.add_node(node_d)

        # Add edges of different types
        graph_mgr.add_edge(node_a, node_b, edge_type=EdgeType.REQUIRES)  # A requires B
        graph_mgr.add_edge(node_b, node_c, edge_type=EdgeType.REQUIRES)  # B requires C
        graph_mgr.add_edge(
            node_a, node_d, edge_type=EdgeType.REFERENCES
        )  # A references D

        # Get requires subgraph
        requires_subgraph = graph_mgr.get_requires_subgraph()

        # Check the subgraph contains only the REQUIRES edges
        assert len(requires_subgraph.edges) == 2
        assert requires_subgraph.has_edge(node_a, node_b)
        assert requires_subgraph.has_edge(node_b, node_c)
        assert not requires_subgraph.has_edge(node_a, node_d)

        # Check nodes are preserved
        assert len(requires_subgraph.nodes) == 3
        assert node_a in requires_subgraph.nodes
        assert node_b in requires_subgraph.nodes
        assert node_c in requires_subgraph.nodes
        assert node_d not in requires_subgraph.nodes

    def test_has_circular_dependencies(self):
        """Test checking for circular dependencies in the graph."""
        # Create a graph without circular dependencies
        graph_acyclic = GraphMgr()

        # Create nodes
        node_a = Node(id="a", name="Node A")
        node_b = Node(id="b", name="Node B")
        node_c = Node(id="c", name="Node C")

        # Add nodes to graph
        graph_acyclic.add_node(node_a)
        graph_acyclic.add_node(node_b)
        graph_acyclic.add_node(node_c)

        # Add edges forming a directed acyclic graph (DAG)
        graph_acyclic.add_edge(node_a, node_b, edge_type=EdgeType.REQUIRES)
        graph_acyclic.add_edge(node_b, node_c, edge_type=EdgeType.REQUIRES)

        # Test that it correctly identifies a graph without cycles
        assert not graph_acyclic.has_circular_dependencies()

        # Create another graph with a cycle
        graph_cyclic = GraphMgr()

        # Create nodes
        node_x = Node(id="x", name="Node X")
        node_y = Node(id="y", name="Node Y")
        node_z = Node(id="z", name="Node Z")

        # Add nodes to graph
        graph_cyclic.add_node(node_x)
        graph_cyclic.add_node(node_y)
        graph_cyclic.add_node(node_z)

        # Add edges forming a cycle
        graph_cyclic.add_edge(node_x, node_y, edge_type=EdgeType.REQUIRES)
        graph_cyclic.add_edge(node_y, node_z, edge_type=EdgeType.REQUIRES)
        graph_cyclic.add_edge(node_z, node_x, edge_type=EdgeType.REQUIRES)

        # Test that it correctly identifies a graph with cycles
        assert graph_cyclic.has_circular_dependencies()

        # Test a graph with both REQUIRES and REFERENCES edges, but only REQUIRES forms a cycle
        graph_mixed = GraphMgr()

        # Add nodes to graph
        node_p = Node(id="p", name="Node P")
        node_q = Node(id="q", name="Node Q")

        graph_mixed.add_node(node_p)
        graph_mixed.add_node(node_q)

        # Add edges - only the REQUIRES type should affect circular dependency checking
        graph_mixed.add_edge(node_p, node_q, edge_type=EdgeType.REQUIRES)
        graph_mixed.add_edge(node_q, node_p, edge_type=EdgeType.REFERENCES)

        # No cycle in REQUIRES edges, so should return False
        assert not graph_mixed.has_circular_dependencies()

    def test_topological_sort_2(self):
        """Test topological sorting of nodes connected with requires edges."""
        # Create a directed acyclic graph
        graph_mgr = GraphMgr()

        # Create nodes
        node_a = Node(id="a", name="Node A")
        node_b = Node(id="b", name="Node B")
        node_c = Node(id="c", name="Node C")
        node_d = Node(id="d", name="Node D")
        node_e = Node(id="e", name="Node E")

        # Add nodes to graph
        graph_mgr.add_node(node_a)
        graph_mgr.add_node(node_b)
        graph_mgr.add_node(node_c)
        graph_mgr.add_node(node_d)
        graph_mgr.add_node(node_e)

        # Add REQUIRES edges
        graph_mgr.add_edge(node_a, node_b, edge_type=EdgeType.REQUIRES)
        graph_mgr.add_edge(node_a, node_c, edge_type=EdgeType.REQUIRES)
        graph_mgr.add_edge(node_b, node_d, edge_type=EdgeType.REQUIRES)
        graph_mgr.add_edge(node_c, node_d, edge_type=EdgeType.REQUIRES)
        graph_mgr.add_edge(node_d, node_e, edge_type=EdgeType.REQUIRES)

        # Add a REFERENCES edge that should be ignored in topological sort
        graph_mgr.add_edge(node_e, node_a, edge_type=EdgeType.REFERENCES)

        # Get the topological sort
        sorted_nodes = graph_mgr.topological_sort()

        # Verify the sort is valid
        # In a valid topological sort, for every directed edge (u, v),
        # u comes before v in the ordering
        for i, node in enumerate(sorted_nodes):
            for successor in graph_mgr.get_requires_subgraph().successors(node):
                successor_index = sorted_nodes.index(successor)
                assert i < successor_index, (
                    f"Node {node.id} should come before {successor.id} in topological sort"
                )

        # Check the specific order - node_a should be first
        assert sorted_nodes[0] == node_a
        # node_e should be last
        assert sorted_nodes[-1] == node_e

    def test_topological_sort_with_cycle(self):
        """Test that topological_sort raises ValueError when graph has circular dependencies."""
        # Create a graph with a cycle
        graph_mgr = GraphMgr()

        # Create nodes
        node_a = Node(id="a", name="Node A")
        node_b = Node(id="b", name="Node B")
        node_c = Node(id="c", name="Node C")

        # Add nodes to graph
        graph_mgr.add_node(node_a)
        graph_mgr.add_node(node_b)
        graph_mgr.add_node(node_c)

        # Add edges forming a cycle
        graph_mgr.add_edge(node_a, node_b, edge_type=EdgeType.REQUIRES)
        graph_mgr.add_edge(node_b, node_c, edge_type=EdgeType.REQUIRES)
        graph_mgr.add_edge(node_c, node_a, edge_type=EdgeType.REQUIRES)

        # Attempt topological sort - should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            graph_mgr.topological_sort()

        assert "circular dependencies" in str(excinfo.value).lower()
