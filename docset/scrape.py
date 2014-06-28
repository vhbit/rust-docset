def scrape(tree, flt_list):
    """Returns a list of tuples (name, type, reference,) based on rules"""
    def apply_filter(flt):
        return map(flt["fn"], tree.xpath(flt["xpath"]))

    return reduce(lambda a, b: a + b, map(apply_filter, flt_list), [])
