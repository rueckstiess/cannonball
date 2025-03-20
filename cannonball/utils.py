from marko.block import ListItem
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
from typing import Optional, Callable, Tuple, Type
import re
import networkx as nx
from enum import Enum

renderer = MarkdownRenderer()


class EdgeType(Enum):
    REQUIRES = "requires"
    REFERENCES = "references"


def get_subgraph(
    graph: nx.DiGraph,
    root_node: Optional[str] = None,
    node_filter: Optional[Type | Callable] = None,
    edge_filter: Optional[EdgeType | Callable] = None,
) -> nx.DiGraph:
    """Get a subgraph based on root node and/or edge type.

    Args:
        root_node: Optional root node ID. If provided, only include descendants of this node.
        node_filter: Optional filter function or type to include only specific node types. If a type is provided,
            only nodes of that type will be included. The node_filter function is passed the node object (not the data
            associated with the node)
        edge_filter: Optional filter function or EdgeType to include only specific edge types. If an EdgeType is provided,
            only edges of that type will be included. The edge_filter function is passed the data associated with the edge.

    Returns:
        A directed graph representing the requested subgraph.
    """
    # Start with the full graph

    if not graph.nodes:
        return graph

    # Filter by edge type if specified
    if edge_filter is not None:
        if isinstance(edge_filter, EdgeType):
            # convert to filtering function
            edge_type_fn = lambda data: data.get("type") == edge_filter.value
        else:
            # Use the provided function directly
            edge_type_fn = edge_filter
        # Create a subgraph with only the edges of the specified type
        edges = [(u, v) for u, v, data in graph.edges(data=True) if edge_type_fn(data)]
        graph = graph.edge_subgraph(edges)

    # Filter by node type if specified
    if node_filter is not None:
        if isinstance(node_filter, type):
            # convert to filtering function
            node_type_fn = lambda n: isinstance(n, node_filter)
        else:
            # Use the provided function directly
            node_type_fn = node_filter
        # Create a subgraph with only the nodes of the specified type
        nodes = [n for n in graph if node_type_fn(n)]
        graph = graph.subgraph(nodes)

    if root_node is not None:
        if root_node in graph:
            # Get all descendants of the root node using the filtered graph
            # This ensures we only include descendants reachable via the specified edge type
            descendants = list(nx.descendants(graph, root_node))
            # Include the root node itself
            nodes = [root_node] + descendants
            # Create a subgraph with only these nodes
            graph = graph.subgraph(nodes)
        else:
            # If the root node is not in the graph, return an empty graph
            return nx.DiGraph()

    return graph


def get_raw_text_from_listtem(li: ListItem) -> Optional[str]:
    """Get the raw text from a ListItem.

    Args:
        li (ListItem): The ListItem object.
    Returns:
        Optional[str]: The raw text from the ListItem, or empty string if no text found.
    """

    assert isinstance(li, ListItem), "Expected a ListItem"
    text = renderer.render_children(li).split("\n", 1)
    if len(text) > 0:
        return text[0]
    else:
        return ""
    # return text
    # # remove dash, dash+space, or dash+space+[content] from start of text
    # text = re.sub(r"^-\s*(?:\[.*?]\s*)?", "", text)
    # return text


def walk_list_items(node: Element, parent=None, level=0, apply_fn: Optional[Callable] = None):
    """Recursively walk the AST and yield all list items with parent and nesting level.

    Args:
        node: The current node in the abstract syntax tree (AST).
        parent: The parent node of the current node.
        level: The current nesting level of the node.
        apply_fn: Optional function to apply to each list item.

    Yields:
        tuple: A tuple containing the current node, its parent, and its nesting level.
            If apply_fn is provided, yields the result of apply_fn(node, parent, level).
    """
    if isinstance(node, ListItem):
        if apply_fn is not None:
            yield apply_fn(node, parent, level)
        else:
            yield node, parent, level
        parent = node
        level += 1

    if hasattr(node, "children"):
        for child in node.children:
            yield from walk_list_items(child, parent, level, apply_fn=apply_fn)


def print_ast(ast: Element) -> None:
    """Print the abstract syntax tree (AST) of a document.

    Args:
        ast (Element): The root node of the AST.
    """
    for item, _, level in walk_list_items(ast):
        print("\t" * level + "- " + get_raw_text_from_listtem(item))


def extract_node_marker_and_refs(text: str) -> Tuple[Optional[str], str, list]:
    """Extract node type, content, and reference ID from text.

    Args:
        text (str): The text to extract from, e.g. "[?] Content ^ref_id".

    Returns:
        tuple: A tuple containing the node type (None for regular Thoughts), reference ID (if any),
               and a list of reference links (if any).

    """
    # Initialize default values
    node_marker = None
    ref = None
    ref_links = []

    # Extract node marker with a regex that supports multi-character markers
    # Use a non-greedy quantifier (.+?) to match multiple characters but stop at the first closing bracket
    node_marker_match = re.match(r"^\s*\[(.+?)]\s*", text)
    if node_marker_match:
        node_marker = node_marker_match.group(1)

    ref_links = re.findall(r"\[\[#\^(\w+)]]", text)

    # Extract first reference ID (^ref)
    ref_match = re.search(r"(?:^|\s+)\^(\w+)", text)
    if ref_match:
        ref = ref_match.group(1)

    return node_marker, ref, ref_links


def extract_str_content(node: str) -> str:
    """Get the content without markers or references.

    Args:
        node: A string representing a node in markdown format

    Returns:
        The cleaned content without markers or references

    Examples:
        get_content("- Task 1") returns "Task 1"
        get_content("  - [ ] Task 2") returns "Task 2"
        get_content("      - [x] Task 3") returns "Task 3"
        get_content("- [D] Task 4 [[#^ref]]") returns "Task 4"
        get_content("- [a] Task 5 ^ref") returns "Task 5"
    """
    # Remove leading whitespace and bullet points
    text = re.sub(r"^\s*-\s*", "", node)

    # Extract marker and references
    marker, ref, ref_links = extract_node_marker_and_refs(text)

    # Remove marker if present
    if marker is not None:
        text = re.sub(r"^\s*\[" + re.escape(marker) + r"\]\s*", "", text)

    # Remove references (^ref)
    if ref is not None:
        text = re.sub(r"\s*\^" + re.escape(ref) + r"\b", "", text)

    # Remove reference links ([[#^ref]])
    text = re.sub(r"\[\[#\^[^\]]+\]\]", "", text)

    # Trim any extra whitespace
    text = text.strip()

    return text
