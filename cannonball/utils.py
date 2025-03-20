from marko.block import ListItem
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
from typing import Optional, Callable, Tuple
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
    edge_type: Optional[EdgeType] = None,
) -> nx.DiGraph:
    """Get a subgraph based on root node and/or edge type.

    Args:
        root_node: Optional root node ID. If provided, only include descendants of this node.
        edge_type: Optional edge type. If provided, only include edges of this type.

    Returns:
        A directed graph representing the requested subgraph.
    """
    # Start with the full graph

    if not graph.nodes:
        return graph

    # Filter by edge type if specified
    if edge_type is not None:
        # Create a subgraph with only the edges of the specified type
        edges = [(u, v) for u, v, data in graph.edges(data=True) if data.get("type") == edge_type.value]
        graph = graph.edge_subgraph(edges)

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
