import logging as log
from lxml import html
import os
import scrape
import shutil
import toc

# Creates a full qualified name based on prefix and name
def make_fqn(prefix, name):
    return "%s::%s" % (prefix, name)


def cp_file(ctx):
    shutil.copy2(ctx['src_path'], ctx['dest_path'])


def patch_file(patch_func):
    def closure(ctx):
        contents = patch_func(open(ctx['src_path'], 'rt').read())
        with open(ctx['dest_path'], 'wt') as f:
            f.write(contents)

    return closure


def update_toc(ctx, tree, ty):
    ctx['html_modified'] = ctx['html_modified'] or toc.insert_toc_into_tree(tree, ty)


# FIXME: so far caching isn't actually used fully
# but it might be useful later on with more atomic
# actions
def cached_html(f):
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


@cached_html
def add_guide(ctx, tree):
    titles = scrape.scrape(tree, [scrape.GUIDE_TITLE_FILTER])
    if len(titles) > 0:
        ctx['idx'].add(titles[0][0], "gd", ctx['rel_path'])

@cached_html
def add_module(ctx, tree):
    fqn_prefix = os.path.dirname(ctx['rel_path']).replace(os.sep, "::")
    ctx['idx'].add(fqn_prefix, "mod", ctx['rel_path'])
    update_toc(ctx, tree, "mod")

@cached_html
def add_decl_html(ctx, tree):
    idx = ctx['idx']

    rel_path = ctx['rel_path']
    name, _ = os.path.splitext(os.path.basename(rel_path))
    dirname = os.path.dirname(rel_path)

    fqn_prefix = dirname.replace(os.sep, "::")
    ty, name = name.split(".")
    fqn = make_fqn(fqn_prefix, name)

    # Process children before, as it allows to
    # distinguish between types and enums
    childs = scrape.child_decls(tree, ty)

    # Type declaration will have no children at all
    # It's a bit hacky but allows to avoid additional
    # search for exact type
    if len(childs) > 0 and ty == "type":
        ty = "enum"

    # And now we know for sure type
    idx.add(fqn, ty, rel_path)

    for decl_info in childs:
        (child_name, child_ty, ref) = decl_info
        if ref:
            ref = rel_path + "#" + ref
        else:
            ref = rel_path
        idx.add(make_fqn(fqn, child_name), child_ty, ref)

    update_toc(ctx, tree, ty)
