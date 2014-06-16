import logging as log
import os
import re

def matches(path, patterns):
    if len(patterns) == 0:
        return True
    else:
        for pattern in patterns:
            if re.search(pattern, path):
                return True

    return False


def rule_for_file(rules, src_path):
    for rule in rules:
        patterns = rule[:-1]
        if matches(src_path, patterns):
            return rule[-1]

    return None


def process_file_rules(rules, ctx, src_path, dest_path):
    """Rules are checked until first match.
       If there are no patterns - it is a default rule,
       which will be executed anyway"""
    fn = rule_for_file(rules, src_path)
    if fn:
        dest_fn = fn(ctx, src_path)
        if dest_fn:
            dest_dir = os.path.dirname(dest_path)

            if not os.path.exists(dest_dir):
                log.info("Creating %s", dest_dir)
                os.makedirs(dest_dir)

            dest_fn(dest_path)
