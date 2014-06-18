#!/usr/bin/env python

import actions
from index import Index
import logging as log
import os
from path_helper import DocsetPathHelper
from predicate import rel_path
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
 [predicate1, predicate2, predicate3, ... , predicateN, action]

 action is fn(ctx), i.e. it decides how to write file
 to destination, it might be copy, it might be patching
 or might be injecting toc

 predicate is fn(ctx) -> bool, i.e. it returns true if current
 context fits. rel_path wraps corresponding functions

 Notes:
 1. Rules are checked until first match
 2. If there are no patterns, just action - it is a default
    action, which matches anything
"""
FILE_RULES = [
    [rel_path(matches='main.css'), actions.patch_file(lambda text: text + CSS_PATCH)],
    [rel_path(matches='.*\\.(epub|tex|pdf)$'), None],
    [rel_path(matches='not_found\\.html$'), None],
    [rel_path(matches='complement-bugreport\\.html$'), None],
    [rel_path(startswith="src"), actions.cp_file],
    [rel_path(dirname=""), rel_path(matches='.*\\.html$'), actions.add_guide],
    [rel_path(matches=r'(index|mod|lib)\.html$'), actions.add_module],
    [rel_path(matches='.*\\.html$'), actions.add_decl_html],
    [actions.cp_file]
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


        for root, dirnames, filenames in os.walk(prefix):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, prefix)
                dest_path = os.path.join(docset.doc_dir, rel_path)

                ctx = {
                    'src_path': full_path,
                    'dest_path': dest_path,
                    'rel_path': rel_path,
                    'idx': idx
                }

                rules.process_file_rules(FILE_RULES, ctx)

        idx.flush()
