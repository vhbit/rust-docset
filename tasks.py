from docset import build_docset
from invoke import run, task
import importlib
import os
import requests
import shutil
import tarfile
from tempfile import TemporaryFile, mkdtemp

NIGHTLY_URL = "http://static.rust-lang.org/dist/rust-nightly-x86_64-unknown-linux-gnu.tar.gz"
#NIGHTLY_DEST = "nightly.tar.gz"
#NIGHTLY_DOC = "nightly_preparation"
TAG_FILE = ".last-tag"
DOC_PREFIX = "rust-nightly-x86_64-unknown-linux-gnu/doc"


def tag_from_response(req):
    """Generates a uniq tag from a response"""
    return req.headers['etag']


def has_nightly_update():
    """Checks if tag was changed"""
    if not os.path.exists(TAG_FILE):
        return True
    else:
        with open(TAG_FILE, "rt") as f:
            last_tag = f.read().strip()

    r = requests.head(NIGHTLY_URL)
    new_tag = tag_from_response(r)
    return new_tag != last_tag


def extract_docs(tar, dest_dir):
    """Extracts only documentation files from nightly archive"""
    for info in tar.getmembers():
        if info.name.startswith(DOC_PREFIX):
            rel_path = os.path.relpath(info.name, DOC_PREFIX)
            dest_path = os.path.join(dest_dir, rel_path)
            if info.isdir():
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
            else:
                in_file = tar.extractfile(info)
                with open(dest_path, "wb") as out_file:
                    out_file.write(in_file.read())


@task
def update_nightly(force=False, out_dir="nightly_out"):
    """Checks for update and re-builds doc if required. Stores new tag"""
    if not force:
        if not has_nightly_update():
            print "No updates available yet"
            return

    r = requests.get(NIGHTLY_URL, stream=True)
    with TemporaryFile("w+b") as temp_file:
        print "Downloading"
        for chunk in r.iter_content(1024*1024*10):
            temp_file.write(chunk)

        temp_dir = mkdtemp()
        try:
            print "Extracting to", temp_dir
            temp_file.seek(0)
            with tarfile.open(fileobj=temp_file, mode='r:gz', bufsize=1024*1024*10) as tar:
                extract_docs(tar, temp_dir)

            print "Building docset"
            build(doc_dir = temp_dir, out_dir = out_dir, settings = "nightly_settings")

            with open(TAG_FILE, "w+t") as f:
                f.write(tag_from_response(r))
        except:
            import traceback
            traceback.print_exc()
            shutil.rmtree(temp_dir)


@task
def build(doc_dir, out_dir=".", settings="nightly_settings"):
    """Builds a docset from doc_dir using settings.
Warning: out dir is cleaned before"""

    doc_dir = os.path.abspath(doc_dir)
    out_dir = os.path.abspath(out_dir)

    if os.path.exists(out_dir):
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        else:
            sys.stderr.write("Output dir points to a file!\n")
            sys.exit(1)

    os.makedirs(out_dir)

    try:
        mod = importlib.import_module(settings)
    except ImportError as e:
        raise ImportError("Failed to import settings from %s", settings)

    build_docset(mod, doc_dir, out_dir)
