#!/usr/bin/env python
"""A library to interact with a yaml encoded tag hierachy and files using those tags."""
# This file is part of productivity.py
# Copyright © 2021 Jonas Muehlmann
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import os
import re
from collections import UserList
from pathlib import Path
from typing import Dict, List, Optional, Union

import pyaoi
import yaml

TagHierachyNode = Union[List, Dict, str]


def is_tag(tag: str) -> bool:
    """Check whether a given str is a valid Tag."""
    # Example: foo-bar::baz_123

    return re.match(r"^\s*[a-zA-Z0-9_-]+(?:::[a-zA-Z_0-9_-]+)*\s*$", tag)


class Tag(UserList):
    """A list wrapper with additional methods to represent a Tags components."""

    def __init__(self, tag: Union[str, List[str]]) -> None:  # noqa W0231
        """Construct a Tag object from components specified as a list or string.

        Args:
            tag: A list of tag components(e.go ["foo", "bar"]) or
                 a string representation of a tag(e.g. "foo::bar")


        Raises:
            ValueError: If tag is not a list or
                        is a string that does satisfy is_tag()
        """

        if isinstance(tag, str):
            if is_tag(tag):
                self.data = tag.strip().split("::")
            else:
                raise ValueError("Tag does not have correct format")

        elif isinstance(tag, list):
            self.data = tag
        else:
            raise ValueError("Invalid type of parameter tag")

    def __str__(self) -> str:
        """Format the tag components like foo::bar::baz."""

        return "::".join(self.data)

    def __repr__(self) -> str:
        """Format the tag components like foo::bar::baz."""

        return self.__str__()

    # Parentheses used because Tag is not defined since we are inside it
    def get_parents(self) -> List["Tag"]:
        """Get a list of parent tag components."""

        return self.data[:-1]

    def get_direct_parent(self) -> Optional[str]:
        """Get the name of the direct parent tag."""

        if len(self.data) == 1:
            return None

        return self.data[-2]

    def get_leaf(self) -> str:
        """Get the leaf tag(tag at end of 'chain')."""

        return self.data[-1]

    def get_root_tag(self) -> str:
        """Get the root tag(tag at beginning of 'chain')."""

        return self.data[0]

    def remove_root_tag(self) -> None:
        """Remove the root tag(tag at beginning of 'chain')."""
        self.data.pop(0)


class TagHierachy:
    """A yaml encoded tag hierarchy."""

    def __init__(self, file_path: Path) -> None:
        """Deserialize a yaml encoded tag hierarchy.

        Args:
            file_path: The file containing the tag hierarchy to work with

        Raises:
            ValueError: If file_path does not end in .yml or .yaml
        """

        if file_path is None or (
            not file_path.lower().endswith(".yml")
            and not file_path.lower().endswith(".yaml")
        ):
            raise ValueError("No valid YAML file provided")

        self.tags_file_path: Path = file_path
        # To be populated by load_tags()
        self.tags: Dict = {}
        self.tags_file: str = ""
        self.load_tags()

    def load_tags(self) -> None:
        """Reload the tag hierarchy from disk."""
        with open(self.tags_file_path, "r") as f:
            self.tags: Dict = yaml.safe_load(f)
            f.seek(0)
            self.tags_file: str = f.read()

    def safe_tags(self) -> None:
        """Safe the tag hierarchy to disk."""
        with open(self.tags_file_path, "w") as f:
            f.write(self.tags_file)

    def reorder_list_items(self, node: Union[Dict, List] = None) -> None:  # noqa: R1710
        """Reorder the tag hierarchy to put leaf tags before mappings of sub-tags.

        Does not write to disk.

        Args:
            node: the tag hierarchy node processed at the current iteration
                  this parameter is only needed for recursion

        """
        # First call, set initial node and start recursing

        if node is None:
            self.reorder_list_items(self.tags)
            self.tags_file = yaml.dump(self.tags)

        # Keep recursing...

        if isinstance(node, dict) and isinstance(list(node.values())[0], list):

            for key, val in node.items():  # noqa VNE002
                self.reorder_list_items(val)
                node[key] = val

        # Base case, reorder list and unwind

        if isinstance(node, dict) and isinstance(list(node.values())[0], str):
            return node

        if isinstance(node, list):
            pyaoi.for_each(
                node,
                lambda item: self.reorder_list_items(item)
                if isinstance(item, dict)
                else item,
            )
            node.sort(key=lambda item: isinstance(item, dict))

    def add_blank_lines(self) -> None:
        """Add blank lines before unindeted lines in the tag hierarchy file.

        Does not write to disk.
        """
        lines: List[str] = self.tags_file.split("\n")
        new_lines: List[str] = []
        print(lines)

        for i, line in enumerate(lines):
            indentation_level_cur = pyaoi.find(line, "-")
            indentation_level_prev = pyaoi.find(lines[i - 1], "-")

            if (
                indentation_level_cur != -1
                and indentation_level_prev != -1
                and indentation_level_cur < indentation_level_prev
            ):
                new_lines.append("")
            new_lines.append(line)

        self.tags_file = "\n".join(new_lines)

    def lint(self) -> None:
        """Add blank lines and reorder nodes."""

        self.reorder_list_items()
        self.add_blank_lines()

    def rename_tag(  # noqa: C901
        self, old_tag: Tag, new_tag: Tag, node: TagHierachyNode = None
    ) -> None:
        """Rename a tag in the tag hierarchy.

        Args:
            old_tag: the tag to rename
            new_tag: the tag replacement
            node: the tag hierarchy node processed at the current iteration
                  this parameter is only needed for recursion
        """
        # First call, set root node and start traversing

        if node is None:
            node = self.tags["tags"]
            self.rename_tag(old_tag, new_tag, node)

        # Direct parent reached, append new node

        elif not old_tag.get_parents():
            i_tag: int = pyaoi.find_if(
                node,
                lambda list_item: list_item == str(old_tag)
                or str(old_tag) in list_item,
            )

            # TODO: Clean up this mess of a function
            # Not sure how robust this is...
            # Narrator: "Turns out it isn't robust at all."

            if isinstance(node[i_tag], str):
                node[i_tag] = str(new_tag)

            elif isinstance(node[i_tag], dict):
                node[i_tag][str(new_tag)] = node[i_tag].pop(str(old_tag))

            self.tags_file = yaml.dump(self.tags)

        # Recurse to new tag's direct parent
        else:
            if isinstance(node, dict):
                parent = old_tag.get_root_tag()
                node = node[parent]
                old_tag.remove_root_tag()

            elif isinstance(node, list):
                parent = old_tag.get_root_tag()
                old_tag.remove_root_tag()

                for i, list_item in enumerate(node):
                    if isinstance(list_item, dict) and parent in list_item:
                        if isinstance(list(list_item.values())[0], str):
                            list_item[parent] = str(new_tag)
                            # This is a bit of a hacky workaround!
                            self.tags_file = yaml.dump(self.tags)

                            return
                        node = list_item[parent]

                        break
                    # A node in parents is turned from a string to a
                    # dictionary and gets it's first child

                    if list_item == parent:
                        node[i] = {parent: []}
                        node = node[i][parent]

                        break

            self.rename_tag(old_tag, new_tag, node)

    def add_tag(self, tag: Tag, node: TagHierachyNode = None) -> None:  # noqa: C901
        """Add a tag to the tag hierarchy.

        The parent components of the provided tag decide where it is inserted.

        Args:
            tag: the tag to add
            node: the tag hierarchy node processed at the current iteration
                  this parameter is only needed for recursion
        """
        # First call, set root node and start traversing

        if node is None:
            node = self.tags["tags"]
            self.add_tag(tag, node)

        # Direct parent reached, append new node

        elif not tag.get_parents():
            node.append(str(tag))
            self.tags_file = yaml.dump(self.tags)

        # Recurse to new tag's direct parent
        else:
            if isinstance(node, dict):
                tag.remove_root_tag()
                parent = tag.get_direct_parent()
                node = node[parent]

            elif isinstance(node, list):
                parent = tag.get_direct_parent()
                tag.remove_root_tag()

                for i, list_item in enumerate(node):
                    if isinstance(list_item, dict) and parent in list_item:
                        if isinstance(list_item[parent], str):
                            existing_tag: str = list_item[parent]
                            list_item[parent] = [existing_tag]
                        node = list_item[parent]
                    # A node in parents is turned from a string to a
                    # dictionary and gets it's first child
                    elif list_item == parent:
                        node[i] = {parent: str(tag)}
                        self.tags_file = yaml.dump(self.tags)

                        return

            self.add_tag(tag, node)

    def remove_tag(self, tag: Tag, node: TagHierachyNode = None) -> None:  # noqa: C901
        """Remove a tag from the tag hierarchy.

        The parent components of the provided tag decide where it is inserted

        Args:
            tag: The tag to remove
            node: the tag hierarchy node processed at the current iteration
                  this parameter is only needed for recursion
        """
        # First call, set root node and start traversing

        if node is None:
            node = self.tags["tags"]
            self.remove_tag(tag, node)

        # Direct parent reached, remove list item representig tag and write new hierachy

        elif not tag.get_parents():
            for i, list_item in enumerate(node):
                if (isinstance(list_item, dict) and tag in list_item) or (
                    isinstance(list_item, str) and list_item == tag
                ):
                    node.pop(i)

            self.tags_file = yaml.dump(self.tags)

        # Recurse to new tag's direct parent list
        else:
            parent: str = tag.get_direct_parent()

            if isinstance(node, dict):
                tag.remove_root_tag()
                node = node[parent]

            elif isinstance(node, list):
                tag.remove_root_tag()

                for list_item in enumerate(node):
                    if isinstance(list_item, dict) and parent in list_item:
                        node = list_item[parent]

            self.remove_tag(tag, node)

    def list_tags(  # noqa: C901
        self,
        paths: List[Tag] = None,
        cur_path: Tag = None,
        node: TagHierachyNode = None,
    ) -> List[Tag]:
        """List all tags in the tag hierarchy.

        Basically returns all root-leaf paths in the tag hierarchy.

        Args:
            paths: The list of all tags(aka paths through the tag hierarchy)
                  this parameter is only needed for recursion
            cur_path: The current path being explored
                  this parameter is only needed for recursion
            node: the tag hierarchy node processed at the current iteration
                  this parameter is only needed for recursion

        Returns:
            List[Tag]: All tags in the tag hierarchy
        """
        # First call, set root node and start traversing

        if node is None:
            paths = []
            self.list_tags(paths, [], self.tags)

            return paths

        # Leaf node reached(base case), add paths and unwind

        if isinstance(node, str):

            cur_path.append(node)

            for i in range(1, len(cur_path) + 1):
                if not cur_path[:i] in paths:
                    paths.append(cur_path[:i])

        # Recurse from non-leaf node
        elif isinstance(node, dict):
            cur_path.append(list(node.keys())[0])

            self.list_tags(paths, cur_path.copy(), list(node.values())[0])

        # Recurse from non-leaf nodes
        elif isinstance(node, list):

            for child in node:
                self.list_tags(paths, cur_path.copy(), child)

    def list_child_tags(  # noqa: C901
        self,
        parent_tag: Tag,
        child_tags: List[Tag] = None,
        cur_tag: Tag = None,
        node: TagHierachyNode = None,
    ) -> List[Tag]:
        """List all child tags of a specified tag.

        Basically lists all parent_tag-leaf paths.

        Args:
            parent_tag: The tag to list child tags of
            child_tags: The l
            cur_tag: The current path being explored
                  this parameter is only needed for recursion
            node: the tag hierarchy node processed at the current iteration
                  this parameter is only needed for recursion

        Returns:
            List[Tag]: A list of child tags of the provided parent_tag
        """

        if node is None:
            child_tags = []
            self.list_child_tags(parent_tag, child_tags, [], self.tags)

            return child_tags

        # Leaf node reached(base case), add child_tags and unwind

        if isinstance(node, str):

            cur_tag.append(node)

            for i in range(1, len(cur_tag) + 1):
                if not cur_tag[:i] in child_tags:
                    child_tags.append(cur_tag[:i])

        # Recurse from non-leaf node
        elif isinstance(node, dict):
            cur_tag.append(list(node.keys())[0])

            self.list_child_tags(
                parent_tag, child_tags, cur_tag.copy(), list(node.values())[0]
            )

        # Recurse from non-leaf nodes
        elif isinstance(node, list):

            for child in node:
                self.list_child_tags(parent_tag, child_tags, cur_tag.copy(), child)

    def is_leaf_tag_ambiguous(self, tag: Tag) -> bool:
        """Check whetever or not the leaf component of tag occurs in any other tag."""
        leaf_tag: str = tag.get_leaf()

        return any(
            (path != tag and pyaoi.mismatch(path, tag) is not None and leaf_tag in path)
            for path in self.list_tags()
        )

    def try_shorten_tag_path(self, tag: Tag) -> Tag:
        """If tag is not ambiguous, return it's leaf component."""

        if not self.is_leaf_tag_ambiguous(tag):
            return [tag.get_leaf()]

        return tag

    def list_tags_short_paths(self) -> List[Tag]:
        """List all tags, only resorting to fully qualified paths where necessary."""
        tags: List[Tag] = self.list_tags()

        pyaoi.transform(tags, self.try_shorten_tag_path)

        return tags


class DocumentTagHandler:
    """A class containing static methods to interact with documents containing tags."""

    @staticmethod
    def list_tags_in_document(file_path: Path) -> List[Tag]:
        """List all tags in the specified document.

        Args:
            file_path: The path to the document to list tags of

        Returns:
            List[Tag]: The list of tags the document contains
        """

        # Warning! Possibly ugly code ahead! Maybe this could work with regex only?!
        tags_line: str = DocumentTagHandler.find_tags_line(file_path)

        if not tags_line:
            return []

        # Could we use regex split here?
        tag_candidates = tags_line.strip().split(",")

        return [candidate for candidate in tag_candidates if is_tag(candidate)]

    @staticmethod
    def find_tags_line(file_path: Path) -> int:
        """Find the file's tag line(# Tags) number.

        Args:
            file_path: The path to the document to find the tag line of

        Returns:
            int: The line number of the tag line or -1 if not present
        """
        with open(file_path, "r") as f:
            try:
                document: List[str] = f.read().splitlines()
            except UnicodeError:
                return -1

            i_tags_list: int = pyaoi.find(document, "# Tags")

            # Tags list either does not exist or ist empty

            if i_tags_list in (-1, len(document) - 1):
                return -1

            return i_tags_list + 1

    @staticmethod
    def list_documents_with_tag(path: Path, tag: Tag) -> List[Path]:
        """Recursively search path for documents containing the tag tag.

        Args:
            path: The directory to start searching in
            tag:  The tag to search for in the found documents

        Returns:
            List[Path]: Paths to all documents containing the specified tag
        """
        file_paths: List[Path] = []

        for root, _, file_paths in os.walk(path):
            for file_path in file_paths:
                file_paths.append(os.path.join(root, file_path))

        return [
            path
            for path in file_paths
            if tag in DocumentTagHandler.list_tags_in_document(path)
        ]

    @staticmethod
    def remove_tag(file_path: Path, tag: Tag, dry_run: bool) -> None:
        """Remove a specified tag from a specified document at file_path.

        Args:
            file_path: The path of the document to modify
            tag: The tag to remove from the document
            dry_run: If True, print the new content instead of writing changes to disk
        """
        i_tags_line: int = DocumentTagHandler.find_tags_line(file_path)

        document: List[str] = []

        with open(file_path, "r+") as f:
            document = f.readlines()

            if i_tags_line == -1:
                return

            new_tags_line: str = re.sub(
                fr"(?:(?<=^)|(?<=,))\s*{str(tag)},?", "", document[i_tags_line]
            )

            document[i_tags_line] = new_tags_line

            if dry_run:
                print(document)
            else:
                # You might think opening the file twice is stupid,
                # and you would be right indeed, but even more stupid is
                # what happens if you actually try to reuse the file handle
                with open(file_path, "w") as f:
                    f.writelines(document)

    @staticmethod
    def rename_tag(
        file_path: Path, old_name: Tag, new_name: Tag, dry_run: bool
    ) -> None:
        """Rename a specified tag in a document at file_path.

        Args:
            file_path: The path of the document to modify
            old_name: The tag to rename
            new_name: The replacement tag
            dry_run: If True, print the new content instead of writing changes to disk
        """
        i_tags_line: int = DocumentTagHandler.find_tags_line(file_path)

        document: List[str] = []

        with open(file_path, "r") as f:
            document = f.readlines()

            if i_tags_line == -1:
                return

            new_tags_line = re.sub(
                fr"(?:(?<=^)|(?<=,))\s*{str(old_name)}",
                str(new_name),
                document[i_tags_line],
            )

            document[i_tags_line] = new_tags_line

            if dry_run:
                print(document)
            else:
                # You might think opening the file twice is stupid,
                # and you would be right indeed, but even more stupid is
                # what happens if you actually try to reuse the file handle
                with open(file_path, "w") as f:
                    f.writelines(document)

    @staticmethod
    def add_tag(file_path: Path, tag: Tag, dry_run: bool) -> None:
        """Add a specified tag to a specified document at file_path.

        Args:
            file_path: The path of the document to modify
            tag: The tag to add to the document
            dry_run: If True, print the new content instead of writing changes to disk
        """
        i_tags_line: int = DocumentTagHandler.find_tags_line(file_path)

        document: List[str] = []

        with open(file_path, "r") as f:
            document = f.readlines()

            if i_tags_line == -1:
                return

            document[i_tags_line] += f",{tag}"

            if dry_run:
                print(document)
            else:
                # You might think opening the file twice is stupid, and you would be
                # right indeed, but even more stupid is what happens if you actually try
                # to reuse the file handle
                with open(file_path, "w") as f:
                    f.writelines(document)
