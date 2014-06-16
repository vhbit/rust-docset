#!/usr/bin/env python

from fnmatch import fnmatch
import logging as log
from lxml import html
from lxml.html.builder import A, CLASS
import os
from path_helper import DocsetPathHelper
import re
import shutil
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
    "static": "Constant",
    "macro": "Macro",
    "primitive": "Type",
    "ffi": "Function",
    "method": "Method",
    "field": "Field",
    "variant": "Variant",
    "enum": "Enum",
    "ffs": "Constant",
    "tymethod": "Method"
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
            log.error("Unknown type: %s, path %s", ty, path)
        else:
            (_, cursor) = idx
            cursor.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?);", (name, dash_ty, path,))


def scrape(tree, flt_list):
    def apply_filter(flt):
        return map(flt["fn"], tree.xpath(flt["xpath"]))

    return reduce(lambda a, b: a + b, map(apply_filter, flt_list), [])


def node_with_id_ref(node):
    id_attrib = node.attrib["id"]
    parts = id_attrib.split(".")
    return (parts[1], parts[0], id_attrib,)


def node_with_id_noref(node):
    parts = node.attrib["id"].split(".")
    return (parts[1], parts[0], None,)

METHOD_FILTER = {"xpath": '//*[@class="method"]',
                 "fn": node_with_id_ref}

VARIANT_FILTER = {"xpath": '//*[@class="variants"]/following-sibling::table[1]/tr/td[1]',
                  "fn": node_with_id_noref}

FIELD_FILTER = {"xpath": '//*[@class="fields"]/following-sibling::table/tr/td[1]',
                "fn": node_with_id_noref}

GUIDE_TITLE_FILTER = {"xpath": '//h1[@class="title"]',
                      "fn": lambda node: (node.text, None, None,)}

# Trait implementers filter
#{"type": "trait_impls",
# "xpath": '//h3[@class="impl"]/code/a[@class="struct"]/preceding-sibling::a[1]/text()'}

TO_SCRAPE_FILTERS = {
    "struct": [METHOD_FILTER, FIELD_FILTER],
    "trait": [METHOD_FILTER],
    "primitive": [METHOD_FILTER],
    "type": [METHOD_FILTER, VARIANT_FILTER],
}


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


def toc_node_classifier(node):
    (name, ty, _) = node_with_id_noref(node)
    return (name, ty)


def placement_child_code(node):
    return node.xpath('./code')[0]


METHOD_TOC_FILTER = {'xpath': '//*[@class="method"]',
                     'fn': toc_node_classifier}

FIELDS_TOC_FILTER = {'xpath': '//*[@class="fields"]/following-sibling::table/tr/td[1]',
                     'fn': toc_node_classifier,
                     'place_fn': placement_child_code}

VARIANTS_TOC_FILTER = {'xpath': '//*[@class="variants"]/following-sibling::table[1]/tr/td[1]',
                       'fn': toc_node_classifier,
                       'place_fn': placement_child_code}


def simple_a_class_toc(klass):
    return { 'xpath': '//a[@class="%s"]' % klass,
             'fn': lambda node: (node.text, klass,)}

FUNCTIONS_TOC_FILTER = simple_a_class_toc("fn")

IDENT_RE = re.compile(" ([a-zA-Z0-9_]+):")
def static_from_text(text):
    m = IDENT_RE.search(text)
    if m:
        return m.group(1)
    return ""

STATIC_TOC_FILTER = {'xpath': '//*[@id="statics"]/following-sibling::table[1]/tr/td/code[1]',
                      'fn': lambda node: (static_from_text(node.text), "static", )}

MODULES_TOC_FILTER = {'xpath': '//*[@id="modules"]/following-sibling::table[1]/tr/td/a[@class="mod"]',
                      'fn': lambda node: (node.text, "mod", )}

PRIMITIVE_TOC_FILTER = {'xpath': '//*[@id="primitives"]/following-sibling::table[1]/tr/td/a[@class="primitive"]',
                      'fn': lambda node: (node.text, "primitive", )}

STRUCT_TOC_FILTER = simple_a_class_toc("struct")

TRAIT_TOC_FILTER = simple_a_class_toc("trait")

TO_TOC_RULES = {
    "struct": [METHOD_TOC_FILTER, FIELDS_TOC_FILTER],
    "mod": [FUNCTIONS_TOC_FILTER, STATIC_TOC_FILTER, MODULES_TOC_FILTER, STRUCT_TOC_FILTER, TRAIT_TOC_FILTER, PRIMITIVE_TOC_FILTER],
    "trait": [METHOD_TOC_FILTER],
    "enum": [METHOD_TOC_FILTER, VARIANTS_TOC_FILTER],
    "type": [METHOD_TOC_FILTER, VARIANTS_TOC_FILTER],
    "primitive": [METHOD_TOC_FILTER]
}

def gen_toc(tree, ty):
    def closure(dest_path):
        rules = TO_TOC_RULES.get(ty, [])
        for rule in rules:
            nodes = tree.xpath(rule["xpath"])
            for node in nodes:
                (name, child_ty) = rule["fn"](node)
                toc_node = A(CLASS('dashAnchor'))
                toc_node.attrib["name"] = "//apple_ref/cpp/%s/%s" % (TO_DASH_TYPE.get(child_ty, child_ty), name)
                place_fn = rule.get('place_fn', None)
                if place_fn:
                    place_node = place_fn(node)
                else:
                    place_node = node
                place_node.addprevious(toc_node)

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
        titles = scrape(tree, [GUIDE_TITLE_FILTER])
        if len(titles) > 0:
            add_to_index(idx, titles[0][0], "gd", rel_path)
            return cp_file(full_path)
    elif not dirname.startswith("src"):
        tree = html.parse(full_path)

        if tree.getroot():
            fqn_prefix = dirname.replace(os.sep, "::")
            if name in ["index", "lib", "mod"]:
                add_to_index(idx, fqn_prefix, "mod", rel_path)
                return gen_toc(tree, "mod")
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

                    childs = scrape(tree, flts)
                    # Type declaration will have no children at all
                    # It's a bit hacky but allows to avoid additional
                    # search for exact type
                    if len(childs) > 0 and ty == "type":
                        ty = "enum"
                    map(add_child_node, childs)

                # And now we know for sure type
                add_to_index(idx, fqn, ty, rel_path)
                return gen_toc(tree, ty)

    return None


def print_usage():
    print """Usage:

   gen.py <doc root> [<out dir>]

Example:

  indexer.py projects/rust/doc
  indexer.py projects/rust/doc out-2014-jul-08
"""

DOCSET_NAME = "RustNightly"

CSS_PATCH = """
/* Dash DocSet overrides */

.sidebar, .sub { display: none; }
.content { margin-left: 0; }
"""

FILE_RULES = [
    [re.compile('main.css'), lambda ctx, fp: patch_file(fp, lambda x: x + CSS_PATCH)],
    [re.compile('.*\\.(epub|tex|pdf)$'), None],
    [re.compile('not_found\\.html$'), None],
    [re.compile('complement-bugreport\\.html$'), None],
    [re.compile('.*\\.html$'), lambda ctx, fp: process_html(ctx, fp)],
    [lambda _, fp: cp_file(fp)]
]


def matches(path, patterns):
    if len(patterns) == 0:
        return True
    else:
        for pattern in patterns:
            if re.search(pattern, path):
                return True

    return False


def rule_for_file(src_path):
    for rule in FILE_RULES:
        patterns = rule[:-1]
        if matches(src_path, patterns):
            return rule[-1]

    return None


def process_file_rules(ctx, src_path, dest_path):
    fn = rule_for_file(src_path)
    if fn:
        dest_fn = fn(ctx, src_path)
        if dest_fn:
            dest_dir = os.path.dirname(dest_path)

            if not os.path.exists(dest_dir):
                log.info("Creating %s", dest_dir)
                os.makedirs(dest_dir)

            dest_fn(dest_path)


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

        idx = prepare_index(docset.index_path)

        ctx = {
            'prefix': prefix,
            'idx': idx
        }

        for root, dirnames, filenames in os.walk(prefix):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, prefix)
                dest_path = os.path.join(docset.doc_dir, rel_path)

                process_file_rules(ctx, full_path, dest_path)

        flush_index(idx)
