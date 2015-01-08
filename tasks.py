from __future__ import print_function

from datetime import datetime
from docset import build_docset
from docset.rust import templates
import hashlib
from invoke import run, task
import importlib
from jinja2 import Template
import os
import requests
import shutil
import sys
import tarfile
from tempfile import TemporaryFile, mkdtemp
import toml


def nightly_url(platform):
    return "http://static.rust-lang.org/dist/rust-docs-nightly-%s.tar.gz" % platform


def doc_prefix(platform):
    return "rust-docs-nightly-%s/share/doc/rust/html" % platform


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


@task
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
            build(doc_dir=temp_dir, out_dir=out_dir, conf="nightly.toml")

            with open(tag_file, "w+t") as f:
                f.write(tag_from_response(r))
        except:
            import traceback
            traceback.print_exc()
            exit_with(1, "Internal error")
        finally:
            shutil.rmtree(temp_dir)


def mod_with_name(name, error_fmt):
    try:
        return importlib.import_module(name)
    except ImportError as e:
        print(error_fmt % {'name': name})
        sys.exit(2)


def ensure_abs(path, prefix):
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(prefix, path)


def not_empty(key):
    def __closure__(section, data):
        if (key not in data) or (not data[key]):
            return "[%s.%s] should have a value" % (section, key,)
        return None

    return __closure__


def flatten(lst_of_lst):
    def concat(a, b):
        a.extend(b)
        return a
    return reduce(lambda a, b: concat(a, b), lst_of_lst, [])


def validate_section(cfg, section_name, rules):
    if not section_name in cfg:
        return ["Section [%s] must be presented" % section_name]
    else:
        data = cfg[section_name]
        return filter(lambda x: x != None,
                      map(lambda r: r(section_name, data), rules))


def validate_config(cfg):
    sections = {
        'docset': [not_empty('name'), not_empty('type'), not_empty('bundle_id')],
    }

    # feed is optional section
    if 'feed' in cfg:
        sections['feed'] = [not_empty('base_url')]

    return flatten(map(lambda (s, r): validate_section(cfg, s, r),
                       sections.items()))


def template_from(info, key, prefix_path, default):
    if not key in info:
        data = default
    else:
        path = ensure_abs(info[key], prefix_path)
        with open(template_path, "rt") as f:
            data = f.read()
    return Template(data)


def exit_with(code, message):
    if code != 0:
        out = sys.stderr
    else:
        out = sys.stdout
    if isinstance(message, str):
        print(message, file=out)
    elif isinstance(message, list):
        for l in message:
            print(message, file=out)
    out.flush()
    sys.exit(code)


def warn(message):
    sys.stdout.write(message)
    sys.stdout.write("\n")
    sys.stdout.flush()


def build_in_dir(root_dir, config, doc_dir = None, out_dir = None):
    ds = config['docset']
    if not 'version' in ds:
        def_version = "0.1"
        warn("No [docset.version] found, defaulting to %s" % def_version)
        ds['version'] = def_version

    plist_template = template_from(ds, 'plist', root_dir, templates.INFO_PLIST)
    ds['plist'] = plist_template.render({
        'time': datetime.now(),
        'name': ds['name'],
        'version': ds['version'],
        'info': ds,
        'bundle_id': ds['bundle_id'],
        'index_file': ds.get('index_file', "index.html")
    })

    if 'icon' in ds:
        ds['icon'] = ensure_abs(ds['icon'], root_dir)

    parts = ds['type'].split(":")
    if len(parts) == 1:
        parts.append("default")

    ty_mod = mod_with_name(parts[0], "Failed to import docset type specs: %(name)s")
    rules = ty_mod.__getattribute__(parts[1])

    warns = {}
    if not doc_dir:
        if 'doc_dir' in ds:
            doc_dir = ensure_abs(ds['doc_dir'], root_dir)
        else:
            warns['doc_dir'] = True
            doc_dir = '.'

    if not out_dir:
        if 'out_dir' in ds:
            out_dir = ensure_abs(ds['out_dir'], root_dir)
        else:
            warns['out_dir'] = True
            out_dir = 'ds_out'

    doc_dir = os.path.abspath(doc_dir)
    out_dir = os.path.abspath(out_dir)

    # Have to delay to get full path
    if 'doc_dir' in warns:
        warn("doc_dir wasn't specified, defaulting to %s" % doc_dir)

    if 'out_dir' in warns:
        warn("out_dir wasn't specified, defaulting to %s" % out_dir)

    if os.path.exists(out_dir):
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        else:
            exit_with(1, "Output dir points to a file!\n")

    os.makedirs(out_dir)

    build_docset(ds, rules, doc_dir, out_dir)

    if 'feed' in config:
        feed = config['feed']
        template = template_from(ds, 'template', root_dir, templates.FEED_XML)

        TGZ_TEMP = os.path.join(out_dir, "%s.tar.gz" % ds['name'])
        DOCSET_DIR = "%s.docset" % ds['name']
        DOC_DIR = os.path.join(out_dir, DOCSET_DIR)

        with tarfile.open(TGZ_TEMP, "w:gz", bufsize=1024*1024*10) as tar:
            tar.add(DOC_DIR, arcname = DOCSET_DIR)

        hash = hashlib.sha1()
        with open(TGZ_TEMP) as f:
            while True:
                chunk = f.read(1024*1024*5)
                if not chunk:
                    break
                else:
                    hash.update(chunk)
        
        sha = hash.hexdigest()
        TGZ_NAME = "%s-%s.tgz" % (ds['name'], sha[:8],)
        TGZ = os.path.join(out_dir, TGZ_NAME)

        xml = template.render({
            'sha': sha,
            'time': datetime.now(),
            'name': ds['name'],
            'file_name': TGZ_NAME,
            'version': ds['version'],
            'info': ds,
            'base_url': feed['base_url']
        })
        feed_xml_path = os.path.join(out_dir, "%s.xml" % ds['name'])

        with open(feed_xml_path, "w+t") as f:
            f.write(xml)

        os.rename(TGZ_TEMP, TGZ)

        if 'upload_cmd' in feed:
            run('"%s" "%s" "%s"' % (feed['upload_cmd'], TGZ, feed_xml_path,))


@task
def build(doc_dir=None, out_dir=None, conf="docset.toml"):
    """Builds a docset from doc_dir using settings.
Command line arguments to doc_dir and out_dir override \
corresponding conf values.

Warning: out dir is cleaned before"""
    conf = os.path.abspath(conf)

    if not os.path.exists(conf):
        exit_with(1, "There is no configuration at path %s" % conf)

    with open(conf) as cf:
        config = toml.loads(cf.read())

    errors = validate_config(config)
    if errors:
        exit_with(1, errors)

    build_in_dir(os.path.dirname(conf), config, doc_dir, out_dir)


def cargo_result(args):
    import json
    from subprocess import check_output, CalledProcessError, STDOUT 
    try:
        output = check_output(["cargo"] + args, stderr = STDOUT)
        decoded = json.loads(output)
        return decoded
    except CalledProcessError as e:
        exit_with(1, "Cargo error: %s" % e.output)
    except ValueError as e:
        exit_with(1, "Failed to parse cargo output: %s" % e)


@task 
def cargo_doc(feed_base_url = None):
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
        "index_file": os.path.join(manifest["name"], "index.html")
    }

    config = {"docset": ds}

    if feed_base_url:
        config["feed"] = {"base_url": feed_base_url}

    build_in_dir(proj_root, config)
