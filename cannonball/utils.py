from marko.block import ListItem
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
from typing import Optional, Callable, Tuple
import re

renderer = MarkdownRenderer()


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


def walk_list_items(node: Element, parent=None, level=0, apply_fn: Optional[Callable] = None):
    """Recursively walk the AST and yield all list items with parent and nesting level.

    Args:
        node: The current node in the abstract syntax tree (AST).
        parent: The parent node of the current node.
        level: The current nesting level of the node.
        apply_fn: Optional function to apply to each list item.

    Yields:
        tuple: A tuple containing the current node, its parent, and its nesting level.
            If apply_fn is provided, yields (apply_fn(node), apply_fn(parent), level).
    """
    if isinstance(node, ListItem):
        if apply_fn is not None:
            yield (apply_fn(node), apply_fn(parent), level)
        else:
            yield node, parent, level
        parent = node
        level += 1

    if hasattr(node, "children"):
        for child in node.children:
            yield from walk_list_items(child, parent, level, apply_fn=apply_fn)


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


def extract_str_content(text: str) -> str:
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
    text = re.sub(r"^\s*-\s*", "", text)

    # Extract marker and references
    marker, ref, ref_links = extract_node_marker_and_refs(text)

    # Remove marker if present
    if marker is not None:
        text = re.sub(r"^\s*\[" + re.escape(marker) + r"\]\s*", "", text)

    # Remove references (^ref)
    # if ref is not None:
    #     text = re.sub(r"\s*\^" + re.escape(ref) + r"\b", "", text)

    # Remove reference links ([[#^ref]])
    # text = re.sub(r"\[\[#\^[^\]]+\]\]", "", text)

    # Trim any extra whitespace
    text = text.strip()

    return text
