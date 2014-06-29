from docset.actions import cached_html, update_toc
from docset.scrape import scrape
from rust_doc import guide_title
import index_rules
import os
import toc_rules
from types import to_dash_type


# Creates a full qualified name based on prefix and name
def make_fqn(prefix, name):
    return "%s::%s" % (prefix, name)


# Appends #ref to path if not None
def path_with_ref(path, ref):
    if ref:
        return path + "#" + ref
    else:
        return path


@cached_html
def add_guide(ctx, tree):
    titles = scrape(tree, index_rules.guide_titles())
    if len(titles) > 0:
        ctx['idx'].add(guide_title(titles[0][0]),
                       "gd", ctx['rel_path'])


@cached_html
def add_module(ctx, tree):
    fqn_prefix = os.path.dirname(ctx['rel_path']).replace(os.sep, "::")
    ctx['idx'].add(fqn_prefix, "mod", ctx['rel_path'])
    update_toc(ctx, tree, toc_rules.by_type("mod"), lambda x: to_dash_type(x, x))


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
    childs = scrape(tree, index_rules.by_type(ty))

    # Type declaration will have no children at all
    # It's a bit hacky but allows to avoid additional
    # search for exact type
    if len(childs) > 0 and ty == "type":
        ty = "enum"

    # And now we know for sure type
    idx.add(fqn, ty, rel_path)

    for decl_info in childs:
        (child_name, child_ty, ref) = decl_info
        idx.add(make_fqn(fqn, child_name), child_ty,
                path_with_ref(rel_path, ref))

    update_toc(ctx, tree, toc_rules.by_type(ty), lambda x: to_dash_type(x, x))
