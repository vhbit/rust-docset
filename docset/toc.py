from dash import to_dash_type
from lxml.html.builder import A, CLASS

def inject_toc(tree, rules):
    modified = False

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
            modified = True
            place_node.addprevious(toc_node)

    return modified
