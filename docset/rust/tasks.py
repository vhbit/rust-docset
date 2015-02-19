from __future__ import print_function

import hashlib
from invoke import run, task
import os
from pkg_resources import resource_filename
import requests
import shutil
import sys
import tarfile
from tempfile import TemporaryFile, mkdtemp

from docset.rust import templates
from docset.tasks import build, build_in_dir, exit_with


def nightly_url(platform):
    return "http://static.rust-lang.org/dist/rust-docs-nightly-%s.tar.gz" % platform


def doc_prefix(platform):
    return "rust-docs-nightly-%s/rust-docs/share/doc/rust/html" % platform


def tag_file_name(platform):
    return ".last-tag-%s" % platform


def tag_from_response(req):
    """Generates a uniq tag from a response"""
    return req.headers['etag']


def has_update(url, tag_file):
    """Checks if tag was changed"""
    if not os.path.exists(tag_file):
        return True
    else:
        with open(tag_file, "rt") as f:
            last_tag = f.read().strip()

    r = requests.head(url)
    new_tag = tag_from_response(r)
    return new_tag != last_tag


def extract_docs(tar, dest_dir, doc_prefix):
    """Extracts only documentation files from nightly archive"""
    for info in tar.getmembers():
        if info.name.startswith(doc_prefix):
            rel_path = os.path.relpath(info.name, doc_prefix)
            dest_path = os.path.join(dest_dir, rel_path)
            if info.isdir():
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
            else:
                in_file = tar.extractfile(info)
                with open(dest_path, "wb") as out_file:
                    out_file.write(in_file.read())


@task(name="up_nightly", aliases=["update_nightly"])
def update_nightly(force=False, out_dir="nightly_out", platform = "x86_64-unknown-linux-gnu"):
    """Checks for update and re-builds doc if required. Stores new tag"""
    url = nightly_url(platform)
    tag_file = tag_file_name(platform)

    if not force:
        if not has_update(url, tag_file):
            print("No updates available yet")
            return

    r = requests.get(url, stream=True)
    with TemporaryFile("w+b") as temp_file:
        print("Downloading")
        for chunk in r.iter_content(1024*1024*10):
            temp_file.write(chunk)

        temp_dir = mkdtemp()
        try:
            print("Extracting to", temp_dir)
            temp_file.seek(0)
            with tarfile.open(fileobj=temp_file, mode='r:gz',
                              bufsize=1024*1024*10) as tar:
                extract_docs(tar, temp_dir, doc_prefix(platform))

            print("Building docset")
            build(doc_dir=temp_dir, out_dir=out_dir, conf=resource_filename(__name__, "data/nightly.toml"))

            with open(tag_file, "w+t") as f:
                f.write(tag_from_response(r))
        except:
            import traceback
            traceback.print_exc()
            exit_with(1, "Internal error")
        finally:
            shutil.rmtree(temp_dir)


def cargo_result(args):
    import json
    from subprocess import check_output, CalledProcessError, STDOUT
    try:
        output = check_output(["cargo"] + args, stderr=STDOUT, universal_newlines=True)
        decoded = json.loads(output)
        return decoded
    except CalledProcessError as e:
        exit_with(1, "Cargo error: %s" % e.output)
    except ValueError as e:
        exit_with(1, "Failed to parse cargo output: %s" % e)


@task
def cargo(feed_base_url = None):
    """Builds docset for cargo project

If feed base url is present also generates a feed file. \
Base url isn't checked, so it could be a marker, which will be \
processed later by other tools like sed."""
    proj_loc = cargo_result(["locate-project"])
    proj_root = os.path.dirname(proj_loc["root"])
    manifest = cargo_result(["read-manifest", "--manifest-path=%s" % proj_root])

    docset_dir = os.path.join(proj_root, "target", "docset")
    shutil.rmtree(docset_dir, True)

    ds = {
        "name": manifest["name"],
        "version": manifest["version"],
        "bundle_id": manifest["name"],
        "type": "docset.rust",
        "doc_dir": os.path.join(proj_root, "target", "doc"),
        "out_dir": docset_dir,
        "index_file": os.path.join(manifest["name"], "index.html"),
        "icon": resource_filename(__name__, "data/template/icon.png")
    }

    config = {"docset": ds}

    if feed_base_url:
        config["feed"] = {"base_url": feed_base_url}

    build_in_dir(proj_root, config)
