#!/usr/bin/env python

import actions
from index import Index
import logging as log
import os
from path_helper import DocsetPathHelper
import re
import rules
import shutil
import sys

DEBUG = os.getenv("DOCSET_DEBUG")

DOCSET_NAME = "RustNightly"

CSS_PATCH = """
/* Dash DocSet overrides */

.sidebar, .sub { display: none; }
.content { margin-left: 0; }
"""

"""Rules are in form:
 [pattern1, pattern2, pattern3, ... , patternn, action]
 action is fn(ctx, full_path_to_source_file) -> fn(dest_path),
 i.e it is a function which takes ctx and path to source file
 and returns a function, which knows how to write to dest_path.
 So it allows to write directly to dest without prior copying.

 Notes:
 1. Rules are checked until first match
 2. If there are no patterns, just action - it is a default
    action, which matches anything
"""
FILE_RULES = [
    [re.compile('main.css'), lambda ctx, fp: actions.patch_file(fp, lambda x: x + CSS_PATCH)],
    [re.compile('.*\\.(epub|tex|pdf)$'), None],
    [re.compile('not_found\\.html$'), None],
    [re.compile('complement-bugreport\\.html$'), None],
    [re.compile('.*\\.html$'), lambda ctx, fp: actions.process_html(ctx, fp)],
    [lambda _, fp: actions.cp_file(fp)]
]

def print_usage():
    print """Usage:

   gen.py <doc root> [<out dir>]

Example:

  indexer.py projects/rust/doc
  indexer.py projects/rust/doc out-2014-jul-08
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
    else:
        prefix = os.path.abspath(sys.argv[1])
        if len(sys.argv) >= 3:
            out_dir = os.path.abspath(sys.argv[2])
        else:
            out_dir = os.cwd()

        if not os.path.exists(out_dir) or not os.path.isdir(out_dir):
            log.error("Output directory either doesn't exist or is not directory")
            sys.exit(1)

        docset = DocsetPathHelper(DOCSET_NAME, out_dir)
        if not os.path.exists(docset.doc_dir):
            os.makedirs(docset.doc_dir)

        shutil.copy2('Info.plist', docset.content_dir)
        shutil.copy2('icon.png', docset.root_dir)

        idx = Index(docset.index_path)

        ctx = {
            'prefix': prefix,
            'idx': idx
        }

        for root, dirnames, filenames in os.walk(prefix):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, prefix)
                dest_path = os.path.join(docset.doc_dir, rel_path)

                rules.process_file_rules(FILE_RULES, ctx, full_path, dest_path)

        idx.flush()
