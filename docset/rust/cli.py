from invoke.cli import dispatch
import sys


def main():
	dispatch([sys.argv[0], "-c", "docset.rust.tasks"] + sys.argv[1:])
