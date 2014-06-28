import logging as log
import os
import re


def matches(ctx, predicates):
    for fn in predicates:
        if not fn(ctx):
            return False

    return True


def rule_for_file(rules, ctx):
    for rule in rules:
        if matches(ctx, rule[:-1]):
            return rule[-1]

    return None


def process_file_rules(rules, ctx):
    """Rules are checked until first match.
       If there are no patterns - it is a default rule,
       which will be executed anyway"""
    fn = rule_for_file(rules, ctx)
    if fn:
        dest_dir = os.path.dirname(ctx['dest_path'])

        if not os.path.exists(dest_dir):
            log.info("Creating %s", dest_dir)
            os.makedirs(dest_dir)

        fn(ctx)
