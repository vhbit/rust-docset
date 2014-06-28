import logging as log
import os
import sqlite3


class Index(object):
    def __init__(self, path, map_fn):
        self._path = path
        if os.path.exists(path):
            os.remove(path)
        self._conn = sqlite3.connect(path)
        self._conn.execute("CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
        self._cursor = self._conn.cursor()
        self._type_map_fn = map_fn

    def flush(self):
        self._cursor.close()
        self._conn.commit()
        self._conn.close()

    def add(self, name, ty, path):
        if ty:
            if self._type_map_fn:
                dash_ty = self._type_map_fn(ty)
            else:
                dash_ty = ty

            if not dash_ty:
                log.error("Unknown type: %s, path %s", ty, path)
            else:
                self._cursor.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?);", (name, dash_ty, path,))
