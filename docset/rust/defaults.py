from actions import add_guide, add_module, add_decl_html
from docset.actions import cp_file, patch_file

from docset.predicate import rel_path

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

"""Rules for building docs for Rust itself"""
RUST_STD_RULES = [
    [rel_path(matches='main.css'), patch_file(lambda text: text + CSS_PATCH)],
    [rel_path(matches='.*\\.(epub|tex|pdf)$'), None],
    [rel_path(matches='not_found\\.html$'), None],
    [rel_path(matches='complement-bugreport\\.html$'), None],

    # deprecated guides
    [rel_path(matches='rust\\.html$'), None],
    [rel_path(matches='tutorial\\.html$'), None],

    [rel_path(startswith="src"), cp_file],
    [rel_path(dirname=""), rel_path(matches='.*\\.html$'), add_guide],
    [rel_path(dirname="book"), rel_path(matches='index\\.html$'), add_guide],
    [rel_path(matches=r'stability\.html'), cp_file],
    [rel_path(matches=r'^(index|mod)\.html$'), add_module],
    [rel_path(matches='.*\\.html$'), add_decl_html],
    [cp_file]
]

"""Rules which should work for any Rust package"""
RUST_RULES = [
    [rel_path(matches='main.css'), patch_file(lambda text: text + CSS_PATCH)],
    [rel_path(matches='.*\\.(epub|tex|pdf)$'), None],
    [rel_path(startswith="src"), cp_file],
    [rel_path(dirname=""), rel_path(matches='.*\\.html$'), add_guide],
    [rel_path(matches=r'stability\.html'), cp_file],
    [rel_path(matches=r'^(index|mod)\.html$'), add_module],
    [rel_path(matches=r'/(index|mod)\.html$'), add_module],
    [rel_path(matches='.*\\.html$'), add_decl_html],
    [cp_file]
]
