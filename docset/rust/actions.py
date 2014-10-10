from docset.actions import cached_html, update_toc
from docset.scrape import scrape
import index_rules
import logging
import os
from rust_doc import guide_title
import toc_rules
from types import to_dash_type

log = logging.getLogger('docset.rust')


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
    """
    This one should work only for nigthly builds

    Special case, main index "index.html" and "rustdoc.html"
    have the same title "Rust Documentation", which is rather
    confusing.
    """
    if ctx['rel_path'] == 'index.html':
        titles = ["Overview"]
    else:
        titles = scrape(tree, index_rules.guide_titles())

    if len(titles) > 0:
        ctx['idx'].add(guide_title(titles[0][0]),
                       "gd", ctx['rel_path'], to_dash_type)


@cached_html
def add_module(ctx, tree):
    fqn_prefix = os.path.dirname(ctx['rel_path']).replace(os.sep, "::")
    ctx['idx'].add(fqn_prefix, "mod", ctx['rel_path'], to_dash_type)
    update_toc(ctx, tree, toc_rules.by_type("mod"),
               lambda x: to_dash_type(x, x))


@cached_html
def add_decl_html(ctx, tree):
    idx = ctx['idx']

    rel_path = ctx['rel_path']
    name, _ = os.path.splitext(os.path.basename(rel_path))
    dirname = os.path.dirname(rel_path)

    fqn_prefix = dirname.replace(os.sep, "::")
    name_parts = name.split('.')
    if len(name_parts) < 2:
        log.error("Unexpected HTML file: %s" % rel_path)
        return
    ty, name = name_parts
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
    idx.add(fqn, ty, rel_path, to_dash_type)

    for decl_info in childs:
        (child_name, child_ty, ref) = decl_info
        idx.add(make_fqn(fqn, child_name), child_ty,
                path_with_ref(rel_path, ref), to_dash_type)

    update_toc(ctx, tree, toc_rules.by_type(ty), lambda x: to_dash_type(x, x))
