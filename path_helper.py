import os


class DocsetPathHelper(object):
    def __init__(self, name, out_path):
        self._name = name
        self._root_dir = os.path.join(out_path, name+'.docset')


    @property
    def root_dir(self):
        return self._root_dir


    @property
    def content_dir(self):
        return os.path.join(self.root_dir, 'Contents')


    @property
    def resources_dir(self):
        return os.path.join(self.content_dir, 'Resources')


    @property
    def doc_dir(self):
        return os.path.join(self.resources_dir, 'Documents')


    @property
    def index_path(self):
        return os.path.join(self.resources_dir, 'docSet.dsidx')
