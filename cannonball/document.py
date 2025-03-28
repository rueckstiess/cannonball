from typing import Optional, Union

from marko import Markdown
from marko.element import Element
from marko.block import List, ListItem
from marko.md_renderer import MarkdownRenderer

from cannonball.node import Node
from cannonball.utils import (
    get_raw_text_from_listtem,
    extract_node_marker_and_refs,
    extract_str_content,
    walk_list_items,
)

import uuid


class Document:
    def __init__(self, markdown: str):
        self.markdown = markdown
        self.parser = Markdown()
        self.renderer = MarkdownRenderer()

        # parse markdown and get top-level List elements
        self.ast = self.parser.parse(markdown)
        self.toplevel_lists = [child for child in self.ast.children if isinstance(child, List)]

        # Settings
        self.auto_resolve = True
        self.auto_decide = True

        self.list_to_roots = self._create_nodes()

    def _convert_li_to_node(self, li: ListItem) -> Node:
        text = get_raw_text_from_listtem(li)
        marker, ref, ref_links = extract_node_marker_and_refs(text)
        content = extract_str_content(text)

        node_id = str(uuid.uuid4())[:8]
        return Node.from_contents(
            id=node_id,
            content=content,
            marker=marker,
            list_item=li,
            auto_resolve=self.auto_resolve,
            auto_decide=self.auto_decide,
        )

    def _create_nodes(self) -> dict[List, list[Node]]:
        """Converts the ListItems in each top-level List into Node objects.

        Returns:
            dict: A dictionary mapping each List to a list of Node objects.
        """

        list_to_roots = {}

        for lst in self.toplevel_lists:
            item_to_node = {}

            for li, parent_li, level in walk_list_items(lst):
                if li in item_to_node:
                    node = item_to_node[li]
                else:
                    node = self._convert_li_to_node(li)
                    item_to_node[li] = node

                # parent node must already exist since we're parsing a tree
                parent = item_to_node[parent_li] if parent_li else None

                if parent:
                    node.parent = parent

            roots = [node for node in item_to_node.values() if node.is_root]
            list_to_roots[lst] = roots

        return list_to_roots

    def _change_indent(self, markdown: str, indent: Union[str, int] = "\t") -> str:
        """Change the indentation in rendered markdown.

        Args:
            markdown: The markdown string to modify
            indent: The new indentation to use. If an integer, used as the number of spaces.
                If a string, used directly as the indentation.

        Returns:
            The markdown with modified indentation
        """
        # Convert integer indent to spaces
        if isinstance(indent, int):
            indent_str = " " * indent
        else:
            indent_str = indent

        # If using 2 spaces as indent, this is already the Marko default - no change needed
        if indent_str == "  ":
            return markdown

        lines = markdown.split("\n")
        result = []

        for line in lines:
            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip(" "))
            # Calculate indent level (integer division by 2)
            indent_level = leading_spaces // 2
            # Replace leading spaces with the new indent
            result.append(indent_str * indent_level + line[leading_spaces:])

        return "\n".join(result)

    def to_markdown(self, indent="\t") -> str:
        """Convert the document back to markdown."""

        for lst, roots in self.list_to_roots.items():
            for root in roots:
                root.update_list_items()

        markdown = self.renderer.render(self.ast)

        # Change the indentation of the rendered markdown
        markdown = self._change_indent(markdown, indent)
        return markdown
