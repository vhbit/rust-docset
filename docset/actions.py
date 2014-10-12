import logging as log
from lxml import html
import os
import scrape
import shutil

from .toc import inject_toc


def cp_file(ctx):
    """Copies file"""
    shutil.copy2(ctx['src_path'], ctx['dest_path'])


def patch_file(patch_func):
    """Applies patch_func to file context and stores new content"""
    def closure(ctx):
        contents = patch_func(open(ctx['src_path'], 'rt').read())
        with open(ctx['dest_path'], 'wt') as f:
            f.write(contents)

    return closure


def update_toc(ctx, tree, rules, ty_map_fn = None):
    """Runs TOC rules over tree, updates html_modification flag"""
    ctx['html_modified'] = ctx['html_modified'] or inject_toc(tree, rules, ty_map_fn)


# FIXME: so far caching isn't actually used fully
# but it might be useful later on with more atomic
# actions
def cached_html(f):
    """Wraps a function f(ctx, tree) to process a cached
    version of HTML. If tree is modified - new tree is saved,
    Otherwise it simply copies file"""
    def closure(ctx):
        has_html = ctx.get('has_html', False)
        if not has_html:
            tree = html.parse(ctx['src_path'])
            ctx['has_html'] = True
            ctx['html'] = tree
            ctx['html_modified'] = False
        if tree.getroot() is not None:
            f(ctx, tree)

        if ctx['html_modified']:
            tree.write(ctx['dest_path'])
        else:
            cp_file(ctx) # FIXME: should it actually be copied?

    return closure
