from docset.index import Index
from docset import rules
import os
import shutil


def build_docset(settings, src_dir, out_dir):
    root_dir = os.path.join(out_dir, settings.DOCSET_NAME + '.docset')
    content_dir = os.path.join(root_dir, 'Contents')
    resources_dir = os.path.join(content_dir, 'Resources')
    doc_dir = os.path.join(resources_dir, 'Documents')
    index_path = os.path.join(resources_dir, 'docSet.dsidx')

    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)

    shutil.copy2(settings.TEMPLATE_PLIST, content_dir)
    if os.path.exists(settings.TEMPLATE_ICON):
        shutil.copy2(settings.TEMPLATE_ICON, root_dir)

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

            rules.process_file_rules(settings.RULES, ctx)

    idx.flush()
