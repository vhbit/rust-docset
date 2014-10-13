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

BY_TYPE = {
    "struct": [METHOD_FILTER, FIELD_FILTER],
    "trait": [METHOD_FILTER],
    "primitive": [METHOD_FILTER],
    "type": [METHOD_FILTER, VARIANT_FILTER],
    "enum": [METHOD_FILTER, VARIANT_FILTER],
}

def by_type(ty):
    return BY_TYPE.get(ty, [])


def guide_titles():
    return [GUIDE_TITLE_FILTER]
