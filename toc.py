from dash import to_dash_type
from lxml.html.builder import A, CLASS
import re

IDENT_RE = re.compile(" ([a-zA-Z0-9_]+):")


def toc_node_classifier(node):
    parts = node.attrib["id"].split(".")
    return (parts[1], parts[0])


def placement_child_code(node):
    return node.xpath('./code')[0]


def static_from_text(text):
    m = IDENT_RE.search(text)
    if m:
        return m.group(1)
    return ""


def simple_a_class_toc(klass):
    return { 'xpath': '//a[@class="%s"]' % klass,
             'fn': lambda node: (node.text, klass,)}

FUNCTIONS_TOC_FILTER = simple_a_class_toc("fn")

STRUCT_TOC_FILTER = simple_a_class_toc("struct")

TRAIT_TOC_FILTER = simple_a_class_toc("trait")


METHOD_TOC_FILTER = {'xpath': '//*[@class="method"]',
                     'fn': toc_node_classifier}

FIELDS_TOC_FILTER = {'xpath': '//*[@class="fields"]/following-sibling::table/tr/td[1]',
                     'fn': toc_node_classifier,
                     'place_fn': placement_child_code}

VARIANTS_TOC_FILTER = {'xpath': '//*[@class="variants"]/following-sibling::table[1]/tr/td[1]',
                       'fn': toc_node_classifier,
                       'place_fn': placement_child_code}

STATIC_TOC_FILTER = {'xpath': '//*[@id="statics"]/following-sibling::table[1]/tr/td/code[1]',
                      'fn': lambda node: (static_from_text(node.text), "static", )}

MODULES_TOC_FILTER = {'xpath': '//*[@id="modules"]/following-sibling::table[1]/tr/td/a[@class="mod"]',
                      'fn': lambda node: (node.text, "mod", )}

PRIMITIVE_TOC_FILTER = {'xpath': '//*[@id="primitives"]/following-sibling::table[1]/tr/td/a[@class="primitive"]',
                      'fn': lambda node: (node.text, "primitive", )}

TO_TOC_RULES = {
    "struct": [METHOD_TOC_FILTER, FIELDS_TOC_FILTER],
    "mod": [FUNCTIONS_TOC_FILTER, STATIC_TOC_FILTER, MODULES_TOC_FILTER, STRUCT_TOC_FILTER, TRAIT_TOC_FILTER, PRIMITIVE_TOC_FILTER],
    "trait": [METHOD_TOC_FILTER],
    "enum": [METHOD_TOC_FILTER, VARIANTS_TOC_FILTER],
    "type": [METHOD_TOC_FILTER, VARIANTS_TOC_FILTER],
    "primitive": [METHOD_TOC_FILTER]
}


def insert_toc_into_tree(tree, ty):
    rules = TO_TOC_RULES.get(ty, [])
    for rule in rules:
        nodes = tree.xpath(rule["xpath"])
        for node in nodes:
            (name, child_ty) = rule["fn"](node)
            toc_node = A(CLASS('dashAnchor'))
            toc_node.attrib["name"] = "//apple_ref/cpp/%s/%s" % (to_dash_type(child_ty, child_ty), name)
            place_fn = rule.get('place_fn', None)
            if place_fn:
                place_node = place_fn(node)
            else:
                place_node = node
            place_node.addprevious(toc_node)
