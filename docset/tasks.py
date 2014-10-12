from __future__ import print_function

from datetime import datetime
import hashlib
from invoke import run, task
import importlib
from jinja2 import Template
import os
from pkg_resources import resource_filename
import shutil
import sys
import tarfile
import toml

from .builder import build_docset


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

    parts = ds['type'].split(":")
    if len(parts) == 1:
        parts.append("default")

    ty_mod = mod_with_name(parts[0], "Failed to import docset type specs: %(name)s")
    rules = ty_mod.__getattribute__(parts[1])
    templates = ty_mod.templates

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
        icon_path = ds['icon']
        res_prefix = "res://"
        if icon_path.startswith(res_prefix):
            ds['icon'] = resource_filename(__name__, icon_path[len(res_prefix):])
        else:
            ds['icon'] = ensure_abs(ds['icon'], root_dir)

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
