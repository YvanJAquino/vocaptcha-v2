from threading import Lock


class ResponseCache:

    def __init__(
        self,
        collection = None
    ):
        self.cache = {}
        self.lock = Lock()
        self.watcher = None
        self.collection = collection

    def callback(self, snaps, changes, read_time):
        for doc in snaps:
            id, data = doc.id, doc.to_dict()
            if id not in self.cache or self.cache.get(id) != data:
                with self.lock:
                    self.cache[doc.id] = data

    def watch(self, query=None):
        if not query:
            query = self.collection
        self.watcher = query.on_snapshot(self.callback)

    def get(self, key):
        with self.lock:
            value = self.cache.get(key)
        if not value:
            raise KeyError(f"Key {key} doesn't exist in the cache.")
        else:
            return value
