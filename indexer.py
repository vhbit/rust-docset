#!/usr/bin/env python

from lxml import html
import os
import sqlite3
import sys

DEBUG = os.getenv("DOCSET_DEBUG")

TO_DASH_TYPE = {
    "gd": "Guide",
    "fn": "Function",
    "trait": "Trait",
    "struct": "Struct",
    "structfield": "Field",
    "mod": "Module",
    "type": "Type",
    "static": "Variable",
    "macro": "Macro",
    "primitive": "Type",
    "ffi": "Function",
    "method": "Method",
    "field": "Field",
    "variant": "Variant",
    "enum": "Enum"
}


# Creates a full qualified name based on prefix and name
def make_fqn(prefix, name):
    return "%s::%s" % (prefix, name)


# Creates sqlite db
def prepare_index(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
    cursor = conn.cursor()
    return (conn, cursor)


# Commits transaction and closes everything
def flush_index(idx):
    (conn, cursor) = idx
    cursor.close()
    conn.commit()
    conn.close()


# Adds an item to index
def add_to_index(idx, name, ty, path):
    if ty:
        dash_ty = TO_DASH_TYPE.get(ty, None)
        if not dash_ty:
            sys.stderr.write("Unknown type: %s, path %s" % (ty, path))
        else:
            (_, cursor) = idx
            cursor.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?);", (name, dash_ty, path,))


def scrape(html_path, flt_list):
    try:
        tree = html.parse(html_path)

        def apply_filter(flt):
            return map(flt["func"], tree.xpath(flt["xpath"]))

        return reduce(lambda a, b: a + b, map(apply_filter, flt_list), [])
    except Exception as e:
        if DEBUG:
            print "Failed to parse: %s, reason: %s" % (html_path, e)
        else:
            print "Failed to parse: ", html_path
        return []


def node_with_id_ref(node):
    id_attrib = node.attrib["id"]
    parts = id_attrib.split(".")
    return (parts[1], parts[0], id_attrib,)


def node_with_id_noref(node):
    parts = node.attrib["id"].split(".")
    return (parts[1], parts[0], None,)

METHOD_FILTER = {"xpath": '//h4[@class="method"]',
                 "func": node_with_id_ref}

VARIANT_FILTER = {"xpath": '//h2[@class="variants"]/following-sibling::table[1]/tr/td[1]',
                  "func": node_with_id_noref}

FIELD_FILTER = {"xpath": '//h2[@class="fields"]/following-sibling::table/tr/td[1]',
                "func": node_with_id_noref}

GUIDE_TITLE_FILTER = {
    "xpath": '//h1[@class="title"]',
    "func": lambda node: (node.text, None, None,)}

# Trait implementers filter
#{"type": "trait_impls",
# "xpath": '//h3[@class="impl"]/code/a[@class="struct"]/preceding-sibling::a[1]/text()'}

TO_SCRAPE_FILTERS = {
    "struct": [METHOD_FILTER, FIELD_FILTER],
    "trait": [METHOD_FILTER],
    "primitive": [METHOD_FILTER],
    "type": [METHOD_FILTER, VARIANT_FILTER],
}


def process_file(idx, full_path, prefix):
    rel_path = os.path.relpath(full_path, prefix)
    name, _ = os.path.splitext(os.path.basename(rel_path))
    dirname = os.path.dirname(rel_path)
    fqn_prefix = ""

    if dirname == "":
        titles = scrape(full_path, [GUIDE_TITLE_FILTER])
        if len(titles) > 0:
            add_to_index(idx, titles[0][0], "gd", rel_path)
    elif dirname.startswith("src"):
        pass
    else:
        fqn_prefix = dirname.replace(os.sep, "::")
        if name in ["index", "lib", "mod"]:
            add_to_index(idx, fqn_prefix, "mod", rel_path)
        else:
            ty, name = name.split(".")
            fqn = make_fqn(fqn_prefix, name)

            # Process children before, as it allows to
            # distinguish between types and enums
            flts = TO_SCRAPE_FILTERS.get(ty, None)
            if flts:
                def add_child_node(node_info):
                    (name, ty, ref) = node_info
                    if ref:
                        ref = rel_path + "#" + ref
                    else:
                        ref = rel_path
                    add_to_index(idx, make_fqn(fqn, name), ty, ref)
                childs = scrape(full_path, flts)
                # Type declaration will have no children at all
                # It's a bit hacky but allows to avoid additional
                # search for exact type
                if len(childs) > 0 and ty == "type":
                    ty = "enum"
                map(add_child_node, childs)

            # And now we know for sure type
            add_to_index(idx, fqn, ty, rel_path)


def print_usage():
    print """Usage:

   gen.py <doc root> [<out dir>]

Example:

  indexer.py projects/rust/doc
  indexer.py projects/rust/doc out-2014-jul-08
"""

IDX_NAME = "docSet.dsidx"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
    else:
        prefix = os.path.abspath(sys.argv[1])
        if len(sys.argv) >= 3:
            out_dir = os.path.abspath(sys.argv[2])
            if not os.path.exists(out_dir) or not os.path.isdir(out_dir):
                print "Output directory either doesn't exist or is not directory"
                sys.exit(1)
            out_path = os.path.join(out_dir, IDX_NAME)
        else:
            out_path = os.path.abspath(IDX_NAME)

        idx = prepare_index(out_path)
        for l in sys.stdin:
            full_path = os.path.abspath(l.strip())
            process_file(idx, full_path, prefix)
        flush_index(idx)
