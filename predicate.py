import logging as log
import re
import os


def predicate_fn(pair):
    key, value = pair
    if key == "matches":
        r = re.compile(value)
        return lambda x: (r.search(x) != None)
    elif key == "startswith":
        return lambda x: x.startswith(value)
    elif key == "dirname":
        return lambda x: (os.path.dirname(x) == value)

    log.warn("Unknown predicate: %s", key)
    return None


def construct_predicate(**kwargs):
    fn_list = filter(lambda x: x != None, map(predicate_fn, kwargs.items()))
    if len(fn_list) == 0:
        print "Invalid predicate"
        log.warn("Check rules, one of predicates has no arguments, will always fail")

    def closure(data):
        for fn in fn_list:
            if not fn(data):
                break
        else:
            return True
        return False

    return closure


def rel_path(**kwargs):
    f = construct_predicate(**kwargs)
    def closure(ctx):
        data = ctx['rel_path']
        return f(data)

    return closure
