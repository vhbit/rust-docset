import os
import shutil

from docset import rules
from docset.index import Index


def build_docset(info, ds_rules, src_dir, out_dir):
    root_dir = os.path.join(out_dir, info['name'] + '.docset')
    content_dir = os.path.join(root_dir, 'Contents')
    resources_dir = os.path.join(content_dir, 'Resources')
    doc_dir = os.path.join(resources_dir, 'Documents')
    index_path = os.path.join(resources_dir, 'docSet.dsidx')

    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)

    with open(os.path.join(content_dir, "Info.plist"), "w+t") as f:
        f.write(info['plist'])

    if 'icon' in info and os.path.exists(info['icon']):
        shutil.copy2(info['icon'], root_dir)

    idx = Index(index_path)

    for root, dirnames, filenames in os.walk(src_dir):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, src_dir)
            dest_path = os.path.join(doc_dir, rel_path)

            ctx = {
                'src_path': full_path,
                'dest_path': dest_path,
                'rel_path': rel_path,
                'idx': idx
            }

            rules.process_file_rules(ds_rules, ctx)

    idx.flush()
