import logging as log
from lxml import html
import os
import scrape
import shutil
import toc

# Creates a full qualified name based on prefix and name
def make_fqn(prefix, name):
    return "%s::%s" % (prefix, name)


def cp_file(src_path):
    def closure(dest_path):
        shutil.copy2(src_path, dest_path)

    return closure


def patch_file(src_path, patch_func):
    def closure(dest_path):
        contents = patch_func(open(src_path, 'rt').read())
        with open(dest_path, 'wt') as f:
            f.write(contents)

    return closure


def write_with_toc(tree, ty):
    def closure(dest_path):
        toc.insert_toc_into_tree(tree, ty)
        tree.write(dest_path)

    return closure


def process_html(ctx, full_path):
    prefix = ctx['prefix']
    idx = ctx['idx']

    rel_path = os.path.relpath(full_path, prefix)
    name, _ = os.path.splitext(os.path.basename(rel_path))
    dirname = os.path.dirname(rel_path)
    fqn_prefix = ""

    if dirname == "":
        tree = html.parse(full_path)
        titles = scrape.scrape(tree, [scrape.GUIDE_TITLE_FILTER])
        if len(titles) > 0:
            idx.add(titles[0][0], "gd", rel_path)
            return cp_file(full_path)
    elif not dirname.startswith("src"):
        tree = html.parse(full_path)

        if tree.getroot():
            fqn_prefix = dirname.replace(os.sep, "::")
            if name in ["index", "lib", "mod"]:
                idx.add(fqn_prefix, "mod", rel_path)
                return write_with_toc(tree, "mod")
            else:
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

                return write_with_toc(tree, ty)

    return cp_file(full_path)
