#!/usr/bin/env python

from lxml import html
import re
import os
import sqlite3
import sys

TO_DASH_TYPE = {
    "gd": "Guide",
    "fn": "Function",
    "trait": "Trait",
    "struct": "Struct",
    "mod": "Module",
    "type": "Type",
    "static": "Variable",
    "macro": "Macro",
    "primitive": "Type",
    "ffi": "Function",
    "method": "Method",
    "field": "Field",
    "variant": "Variant"
}

def make_fqn(prefix, name):
    return "%s::%s" % (prefix, name)

def scrape(html_path, filters):
    try:
        tree = html.fromstring(open(os.path.join(PREFIX, html_path), "rt").read())

        res = {}
        for flt in filters:
            res[flt["type"]] = tree.xpath(flt["xpath"])
        return res
    except:
        print "Failed to parse", html_path
        return {}

TO_SCRAPE_FILTERS = {
    "struct": [{"type": "methods",
                "xpath": '//h4[@class="method"]/code/a[@class="fnname"]/text()'},
               #{"type": "trait_impls",
               # "xpath": '//h3[@class="impl"]/code/a[@class="struct"]/preceding-sibling::a[1]/text()'},
               {"type": "fields",
                "xpath": '//h2[@class="fields"]/following-sibling::table/tr/td[1]/code/text()'}],
    "trait": [{"type": "methods",
               "xpath": '//div[@class="methods"]/h3[@class="method"]/code/a[1]/text()'}],
    "primitive": [{"type": "methods",
                   "xpath": '//h4[@class="method"]/code/a[@class="fnname"]/text()'}],
    "type": [{"type": "methods",
              "xpath": '//h4[@class="method"]/code/a[@class="fnname"]/text()'},
             {"type": "variants",
              "xpath": '//h2[@class="variants"]/following-sibling::table[1]/tr/td[1]/code/text()'}],
}

IDX_FILE = "docSet.dsidx"

def prepare_index():
    if os.path.exists(IDX_FILE):
        os.remove(IDX_FILE)
    conn = sqlite3.connect(IDX_FILE)
    conn.execute("CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
    cursor = conn.cursor()
    return (conn, cursor)

def flush_index(idx):
    (conn, cursor) = idx
    cursor.close()
    conn.commit()
    conn.close()

def add_to_index(idx, name, ty, path):
    if ty:
        dash_ty = TO_DASH_TYPE.get(ty, None)
        if not dash_ty:
            sys.stderr.write("Unknown type: %s, path %s" % (ty, path))
        else:
            (_, cursor) = idx
            cursor.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?);", (name, dash_ty, path,))

def process_complex(idx, fqn_prefix, ty, path, sub_data):
    map(lambda name: add_to_index(idx, make_fqn(fqn_prefix, name), "method", path),
        sub_data.get("methods", []))
    #map(lambda name: add_to_index(idx, name, "impl", path),
    #    sub_data.get("trait_impls", []))
    map(lambda name: add_to_index(idx, make_fqn(fqn_prefix, name), "field", path),
        sub_data.get("fields", []))
    map(lambda name: add_to_index(idx, make_fqn(fqn_prefix, name), "variant", path),
        sub_data.get("variants", []))


def process_path(idx, path):
    name, _ = os.path.splitext(os.path.basename(path))
    dirname = os.path.dirname(path)
    fqn_prefix = ""

    if dirname == "":
        titles = scrape(path, [{"type": "title", "xpath": '//h1[@class="title"]/text()'}])["title"]
        if len(titles) > 0:
            add_to_index(idx, titles[0], "gd", path)
    elif dirname.startswith("src"):
        pass
    else:
        fqn_prefix = dirname.replace(os.sep, "::")
        if name in ["index", "lib", "mod"]:
            add_to_index(idx, fqn_prefix, "mod", path)
        else:
            ty, name = name.split(".")
            fqn = make_fqn(fqn_prefix, name)
            add_to_index(idx, fqn, ty, path)
            flts = TO_SCRAPE_FILTERS.get(ty, None)
            if flts:
                sub_data = scrape(path, flts)
                process_complex(idx, fqn, ty, path, sub_data)

def print_usage():
    print """Usage:
   gen.py <doc root>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2 :
        print_usage()
    else:
        global PREFIX
        PREFIX = os.path.abspath(sys.argv[1])
        idx = prepare_index()
        for l in sys.stdin:
            full_path = os.path.abspath(l.strip())
            rel_path = os.path.relpath(full_path, PREFIX)
            process_path(idx, rel_path)
        flush_index(idx)
