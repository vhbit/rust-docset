from docset import build_docset
from invoke import run, task
import importlib
import os
import requests
import shutil
import sys
import tarfile
from tempfile import TemporaryFile, mkdtemp
import toml

NIGHTLY_URL = "http://static.rust-lang.org/dist/rust-nightly-x86_64-unknown-linux-gnu.tar.gz"
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
            build(doc_dir = temp_dir, out_dir = out_dir, conf = "nightly.toml")

            with open(TAG_FILE, "w+t") as f:
                f.write(tag_from_response(r))
        except:
            import traceback
            traceback.print_exc()
            shutil.rmtree(temp_dir)


def mod_with_name(name, error_fmt):
    try:
        return importlib.import_module(name)
    except ImportError as e:
        print error_fmt % {'name': name}
        sys.exit(2)


def ensure_abs(path, prefix):
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(prefix, path)


def validate_docset(ds):
    result = []
    for key in ['name', 'plist', 'type']:
        value = ds[key]
        if not value:
            result.append("Docset attribute '%s' couldn't be empty", key)

    return result


@task
def build(doc_dir = None, out_dir=None, conf="rust_ds.toml"):
    """Builds a docset from doc_dir using settings.
Command line arguments to doc_dir and out_dir override
corresponding conf values.

Warning: out dir is cleaned before"""
    conf = os.path.abspath(conf)
    with open(conf) as cf:
        config = toml.loads(cf.read())

    ds = config['docset']
    errors = validate_docset(ds)
    if errors:
        for e in errors:
            print e, "\n"
        sys.exit(1)

    ds['plist'] = ensure_abs(ds['plist'], os.path.dirname(conf))
    if 'icon' in ds:
        ds['icon'] = ensure_abs(ds['icon'], os.path.dirname(conf))

    parts = ds['type'].split(":")
    if len(parts) == 1:
        parts.append("default")

    ty_mod = mod_with_name(parts[0], "Failed to import docset type specs: %(name)s")
    rules = ty_mod.__getattribute__(parts[1])

    if not doc_dir and 'doc_dir' in ds:
        doc_dir = ensure_abs(ds['doc_dir'], os.path.dirname(conf))

    if not out_dir and 'out_dir' in ds:
        out_dir = ensure_abs(ds['out_dir'], os.path.dirname(conf))

    if not doc_dir:
        doc_dir = "."

    doc_dir = os.path.abspath(doc_dir)
    out_dir = os.path.abspath(out_dir)

    if os.path.exists(out_dir):
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        else:
            sys.stderr.write("Output dir points to a file!\n")
            sys.exit(1)

    os.makedirs(out_dir)

    build_docset(ds, rules, doc_dir, out_dir)

    if 'feed' in config:
        feed = config['feed']
        #xml = feed['template']
