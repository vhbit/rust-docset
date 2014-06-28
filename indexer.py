#!/usr/bin/env python

from docset import build_docset
import importlib
import logging as log
import os
import sys


def print_usage():
    print """Usage:

   indexer.py <doc root> [<out dir>]

Example:

  indexer.py projects/rust/doc
  indexer.py projects/rust/doc out-2014-jul-08
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
    else:
        src_dir = os.path.abspath(sys.argv[1])
        if len(sys.argv) >= 3:
            out_dir = os.path.abspath(sys.argv[2])
        else:
            out_dir = os.cwd()

        if not os.path.exists(out_dir) or not os.path.isdir(out_dir):
            log.error("Output directory either doesn't exist or is not directory")
            sys.exit(1)

        try:
            settings = importlib.import_module("nightly_settings")
        except ImportError as e:
            raise ImportError("Please specify settings!")

        build_docset(settings, src_dir, out_dir)
