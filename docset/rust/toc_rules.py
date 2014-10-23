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


def trait_impl(node):
    if " for " in node.getparent().xpath("string()"):
        fqn_parts = node.attrib["title"].split("::")
        return (fqn_parts[-1], "trait",)
    else:
        return None

FUNCTIONS_TOC_FILTER = simple_a_class_toc("fn")

STRUCT_TOC_FILTER = simple_a_class_toc("struct")

TRAIT_TOC_FILTER = {'xpath': '//h3[@class="impl"]/code/a[@class="trait"][last()]',
                    'fn': trait_impl}

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

BY_TYPE = {
    "struct": [METHOD_TOC_FILTER, FIELDS_TOC_FILTER, TRAIT_TOC_FILTER],
    "mod": [FUNCTIONS_TOC_FILTER, STATIC_TOC_FILTER, MODULES_TOC_FILTER, STRUCT_TOC_FILTER, TRAIT_TOC_FILTER, PRIMITIVE_TOC_FILTER],
    "trait": [METHOD_TOC_FILTER],
    "enum": [METHOD_TOC_FILTER, VARIANTS_TOC_FILTER, TRAIT_TOC_FILTER],
    "type": [METHOD_TOC_FILTER, VARIANTS_TOC_FILTER],
    "primitive": [METHOD_TOC_FILTER]
}


def by_type(ty):
    return BY_TYPE.get(ty, [])
