#!/usr/bin/env python
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
"""Usage:
    tags.py                       list_documents_with_tag <tag> <path>
    tags.py            -t  <file> is_leaf_tag_ambiguous   <tag>
    tags.py            -t  <file> try_shorten_tag_path    <tag>
    tags.py            -t  <file> list_child_tags         <tag>
    tags.py [-D]       -t  <file> lint
    tags.py [-D] (-d | -t) <file> rename_tag              <old_name> <new_name>
    tags.py [-D] (-d | -t) <file> add_tag                 <tag>
    tags.py [-D] (-d | -t) <file> remove_tag              <tag>
    tags.py      (-d | -t) <file> list_tags               [--fully_qualified]
    tags.py (-h | --help)
    tags.py (-v | --version)

    Options:
        -t --tag_file  the tags file to work with.
        -d --document  the document to work with.
        -h --help      show this screen.
        -v --version   show version.
        -D --dry_run   instead of changing files, print their new content

"""
from os.path import exists

# Uses docopt-ng, not original docopt
from docopt import docopt
from schema import And, Optional, Or, Schema, SchemaError

from lib.libtags import DocumentTagHandler, Tag, TagHierachy, is_tag

if __name__ == "__main__":
    args = docopt(version="productivity.nvim 0.1.0")

    schema = Schema(
        {
            # Commands
            "lint": bool,
            "add_tag": bool,
            "remove_tag": bool,
            "rename_tag": bool,
            "list_tags": bool,
            "list_child_tags": bool,
            "list_documents_with_tag": bool,
            "is_leaf_tag_ambiguous": bool,
            "try_shorten_tag_path": bool,
            # Flags
            "--fully_qualified": bool,
            "--dry_run": bool,
            "--tag_file": bool,
            "--document": bool,
            "--help": bool,
            "--version": bool,
            # Arguments
            Optional("<file>"): Or(
                None, And(str, open), error="<file> should be accessible"
            ),
            Optional("<path>"): Or(
                None, And(str, exists), error="<path> should be accessible"
            ),
            Optional("<tag>"): Or(
                None,
                And(str, is_tag),
                error="<tag> does not match the pattern for a tag",
            ),
            Optional("<old_name>"): Or(
                None,
                And(str, is_tag),
                error="<tag> does not match the pattern for a tag",
            ),
            Optional("<new_name>"): Or(
                None,
                And(str, is_tag),
                error="<tag> does not match the pattern for a tag",
            ),
        }
    )

    try:
        args = schema.validate(args)
    except SchemaError as e:
        exit(e)

    # Passed arguments are made available as members after being stripped of
    # leading - and --,
    # surrounding < and >
    # and - in the middle get converted to _

    # Read only operations, do not alter files

    if args.tag_file:
        tag_hierachy = TagHierachy(args.file)

    if args.list_tags:
        if args.fully_qualified:
            print(tag_hierachy.list_tags())
        else:
            print(tag_hierachy.list_tags_short_paths())

    if args.list_documents_with_tag:
        print(
            DocumentTagHandler.list_documents_with_tag(
                args.path, Tag(args.tag), args.dry_run
            )
        )

    if args.list_child_tags:
        print(tag_hierachy.list_child_tags(Tag(args.tag)))

    if args.is_leaf_tag_ambiguous:
        print(tag_hierachy.is_leaf_tag_ambiguous(Tag(args.tag)))

    if args.try_shorten_tag_path:
        print(tag_hierachy.try_shorten_tag_path(Tag(args.tag)))

    # Read/write operations, can safe file changes if --dry_run is not specified

    if args.lint:
        tag_hierachy.lint()

    if args.add_tag:
        if args.document:
            DocumentTagHandler.add_tag(args.file, Tag(args.tag), args.dry_run)
        else:
            tag_hierachy.add_tag(Tag(args.tag))

    if args.remove_tag:
        if args.document:
            DocumentTagHandler.remove_tag(args.file, Tag(args.tag), args.dry_run)
        else:
            tag_hierachy.remove_tag(Tag(args.tag))

    if args.rename_tag:
        if args.document:
            DocumentTagHandler.rename_tag(
                args.file, Tag(args.old_name), Tag(args.new_name), args.dry_run
            )
        else:
            tag_hierachy.rename_tag(Tag(args.old_name), Tag(args.new_name))

    if not args.dry_run:
        tag_hierachy.safe_tags()
    else:
        print(tag_hierachy.tags_file)
