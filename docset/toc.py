from lxml.html.builder import A, CLASS

def inject_toc(tree, rules, ty_map_fn = None):
    modified = False

    for rule in rules:
        nodes = tree.xpath(rule["xpath"])
        for node in nodes:
            (name, child_ty) = rule["fn"](node)
            toc_node = A(CLASS('dashAnchor'))

            if ty_map_fn:
                ty = ty_map_fn(child_ty)
            else:
                ty = child_ty

            toc_node.attrib["name"] = "//apple_ref/cpp/%s/%s" % (ty, name)
            place_fn = rule.get('place_fn', None)
            if place_fn:
                place_node = place_fn(node)
            else:
                place_node = node
            modified = True
            place_node.addprevious(toc_node)

    return modified
