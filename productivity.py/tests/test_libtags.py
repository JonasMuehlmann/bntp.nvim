#!/usr/bin/env python3
from pathlib import Path

import pytest
import yaml
from src.lib import libtags

from tests.util import create_test_file

# Ignores:
#   method could be function
#   too few public methods
# pylint: disable=R0201,R0903


# NOTE: Top level classes represent classes in the tested library,
# nested classes group tests for each class method


class TestHelpers:
    class TestIsTag:
        def test_single_component(self):
            assert libtags.is_tag("foo")

        def test_double_component(self):
            assert libtags.is_tag("foo::bar")

        def test_alnum_plus_underscore_and_dash(self):
            assert libtags.is_tag("foo_bar::baz-123")

        def test_non_alnum_plus_underscore_and_dash(self):
            assert not libtags.is_tag("foo+bar::baz")

        def test_empty(self):
            assert not libtags.is_tag("")

        def test_single_component_separator_prefix(self):
            assert not libtags.is_tag("::foo")

        def test_single_component_separator_postfix(self):
            assert not libtags.is_tag("foo::")


class TestTag:
    class TestInit:
        def test_empty(self):
            with pytest.raises(ValueError):
                assert libtags.Tag("")

        def test_correct_tag_from_string_one_component(self):
            assert libtags.Tag("foo_bar") == ["foo_bar"]

        def test_correct_tag_from_string(self):
            assert libtags.Tag("foo_bar::baz-123") == ["foo_bar", "baz-123"]

        def test_incorrect_tag_from_string(self):
            with pytest.raises(ValueError):
                libtags.Tag("foo_bar::baz+123")

        def test_correct_tag_from_list(self):
            assert libtags.Tag(["foo_bar", "baz-123"]) == ["foo_bar", "baz-123"]

    class TestStr:
        def test_single_component(self):
            assert str(libtags.Tag("foo_bar")) == "foo_bar"

        def test_multiple_components(self):
            assert str(libtags.Tag("foo::bar")) == "foo::bar"

    class TestGetParents:
        def test_single_component(self):
            assert libtags.Tag("foo").get_parents() == []

        def test_two_components(self):
            assert libtags.Tag("foo::bar").get_parents() == ["foo"]

        def test_three_components(self):
            assert libtags.Tag("foo::bar::baz").get_parents() == ["foo", "bar"]

    class TestGetDirectParent:
        def test_single_component(self):
            assert libtags.Tag("foo").get_direct_parent() is None

        def test_two_components(self):
            assert libtags.Tag("foo::bar").get_direct_parent() == "foo"

        def test_three_components(self):
            assert libtags.Tag("foo::bar::baz").get_direct_parent() == "bar"

    class TestGetLeaf:
        def test_single_component(self):
            assert libtags.Tag("foo").get_leaf() == "foo"

        def test_two_components(self):
            assert libtags.Tag("foo::bar").get_leaf() == "bar"

        def test_three_components(self):
            assert libtags.Tag("foo::bar::baz").get_leaf() == "baz"

    class TestRemoveRootTag:
        def test_single_component(self):
            tag = libtags.Tag("foo")
            tag.remove_root_tag()
            assert str(tag) == ""

        def test_two_components(self):
            tag = libtags.Tag("foo::bar")
            tag.remove_root_tag()
            assert str(tag) == "bar"

        def test_three_components(self):
            tag = libtags.Tag("foo::bar::baz")
            tag.remove_root_tag()
            assert str(tag) == "bar::baz"


class TestTagHierarchy:
    class TestInit:
        def test_file_path_no_yaml(self):
            FILE_PATH: Path = create_test_file(self, "test_file_path_no_yaml", "foo")
            with pytest.raises(ValueError):
                libtags.TagHierachy(FILE_PATH)

        def test_file_path_empty(self):
            with pytest.raises(ValueError):
                libtags.TagHierachy("")

        def test_file_path_yaml(self):
            FILE_PATH: Path = create_test_file(self, "test_file_path_yaml", "yaml")
            libtags.TagHierachy(FILE_PATH)

        def test_file_path_yml(self):
            FILE_PATH: Path = create_test_file(self, "test_file_path_yml.yml", "yml")
            libtags.TagHierachy(FILE_PATH)

        def test_read_file(self):
            FILE_PATH: Path = create_test_file(self, "test_read_file", "yaml")
            FILE_CONTENT: str = "tags:\n- foo\n- bar\n"

            with open(FILE_PATH, "w") as f:
                f.write(FILE_CONTENT)

            hierarchy = libtags.TagHierachy(FILE_PATH)
            assert hierarchy.tags == {"tags": ["foo", "bar"]}
            assert hierarchy.tags_file == FILE_CONTENT

    class TestLoadTags:
        def test_read_file(self):
            FILE_PATH: Path = create_test_file(self, "test_read_file", "yaml")
            FILE_CONTENT: str = "tags:\n- foo\n- bar\n"

            with open(FILE_PATH, "w") as f:
                f.write(FILE_CONTENT)

            hierarchy = libtags.TagHierachy(FILE_PATH)
            assert hierarchy.tags == {"tags": ["foo", "bar"]}
            assert hierarchy.tags_file == FILE_CONTENT

    class TestSafeTags:
        def test_write_file(self):
            FILE_PATH: Path = create_test_file(self, "test_write_file", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags_file = "tags:\n- foo\n- bar\n- baz\n"
            hierarchy.safe_tags()

            hierarchy.load_tags()
            assert hierarchy.tags == {"tags": ["foo", "bar", "baz"]}
            assert hierarchy.tags_file == "tags:\n- foo\n- bar\n- baz\n"

    class TestReorderListItems:
        def test_no_changes_only_scalar(self):
            FILE_PATH: Path = create_test_file(
                self, "test_no_changes_only_scalar", "yaml"
            )

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {"tags": ["foo", "bar", "baz"]}
            hierarchy.reorder_list_items()

            assert hierarchy.tags == {"tags": ["foo", "bar", "baz"]}

        def test_no_changes_only_mapping(self):
            FILE_PATH: Path = create_test_file(
                self, "test_no_changes_only_mapping", "yaml"
            )

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {
                "tags": [{"foo": "foo2"}, {"bar": "bar2"}, {"baz": "baz2"}]
            }
            hierarchy.reorder_list_items()
            assert hierarchy.tags == {
                "tags": [{"foo": "foo2"}, {"bar": "bar2"}, {"baz": "baz2"}]
            }

        def test_mixed(self):
            FILE_PATH: Path = create_test_file(self, "test_mixed", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {"tags": [{"foo": "foo2"}, {"bar": "bar2"}, "baz"]}
            hierarchy.reorder_list_items()
            assert hierarchy.tags == {"tags": ["baz", {"foo": "foo2"}, {"bar": "bar2"}]}

        def test_mixed_nested(self):
            FILE_PATH: Path = create_test_file(self, "test_mixed", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {
                "tags": [
                    {
                        "foo": [
                            {
                                "foo2": [
                                    {"bar3": "bar3"},
                                    {"bar3": "bar4"},
                                ]
                            },
                            "foo3",
                        ],
                    },
                    {"bar": "bar2"},
                    "baz",
                ],
            }
            hierarchy.reorder_list_items()
            assert hierarchy.tags == {
                "tags": [
                    "baz",
                    {
                        "foo": [
                            "foo3",
                            {
                                "foo2": [
                                    {"bar3": "bar3"},
                                    {"bar3": "bar4"},
                                ]
                            },
                        ],
                    },
                    {"bar": "bar2"},
                ],
            }

    class TestAddBlankLines:
        def test_no_changes(self):
            FILE_PATH: Path = create_test_file(self, "test_no_changes", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            _yml: str = """tags:
    - foo2
    - foo3
    - foo:
        - bar
        - baz"""
            hierarchy.tags_file = _yml
            hierarchy.add_blank_lines()
            assert hierarchy.tags_file == _yml

        def test_nested(self):
            FILE_PATH: Path = create_test_file(self, "test_nested", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            _yml_old: str = """tags:
    - foo:
        - bar:
            - bar2
        - baz
    - foo2
    - foo3"""

            _yml_new: str = """tags:
    - foo:
        - bar:
            - bar2

        - baz

    - foo2
    - foo3"""
            hierarchy.tags_file = _yml_old
            hierarchy.add_blank_lines()
            print(hierarchy.tags_file)
            assert hierarchy.tags_file == _yml_new

    class TestRenameTag:
        # TODO: Add tests to make sure only first occurence of tag is renamed
        def test_rename_top_level(self):
            FILE_PATH: Path = create_test_file(self, "test_rename_top_level", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {"tags": ["foo", "bar"]}
            hierarchy.rename_tag(libtags.Tag("foo"), libtags.Tag("bar2"))

            assert hierarchy.tags == {"tags": ["bar2", "bar"]}

        def test_nested_leaf_only_child(self):
            FILE_PATH: Path = create_test_file(
                self, "test_nested_non_leaf_only_child", "yaml"
            )

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {"tags": [{"foo": "foobar"}, "bar"]}
            hierarchy.rename_tag(libtags.Tag("foo::foobar"), libtags.Tag("bar2"))

            assert hierarchy.tags == {"tags": [{"foo": "bar2"}, "bar"]}

        def test_nested_leaf(self):
            FILE_PATH: Path = create_test_file(self, "test_nested_non_leaf", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {"tags": [{"foo": ["foobar", "barbaz"]}, "bar"]}
            hierarchy.rename_tag(libtags.Tag("foo::foobar"), libtags.Tag("bar2"))

            assert hierarchy.tags == {"tags": [{"foo": ["bar2", "barbaz"]}, "bar"]}

        def test_nested_non_leaf(self):
            FILE_PATH: Path = create_test_file(self, "test_nested_leaf", "yaml")

            hierarchy = libtags.TagHierachy(FILE_PATH)
            hierarchy.tags = {"tags": [{"foo": ["foobar"]}, "bar"]}
            hierarchy.rename_tag(libtags.Tag("foo"), libtags.Tag("bar2"))

            assert hierarchy.tags == {"tags": [{"bar2": ["foobar"]}, "bar"]}

    class TestAddTag:
        pass

    class TestRemoveTag:
        pass

    class TestListTags:
        pass

    class TestListChildTags:
        pass

    class TestIsLeafTagAmbiguous:
        pass

    class TestTryShortenTagPath:
        pass

    class TestListTagsShortPaths:
        pass


class TestDocumentTagHandler:
    class TestListTagsInDocument:
        pass

    class TestFindTagsLine:
        pass

    class TestListDocumentsWithTag:
        pass

    class TestRemoveTag:
        pass

    class TestRenameTag:
        pass

    class TestAddTag:
        pass
