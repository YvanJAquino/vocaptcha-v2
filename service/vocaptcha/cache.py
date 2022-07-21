from threading import Lock, Event


class ResponseCache:

    def __init__(
        self,
        collection = None
    ):
        self.cache = {}
        self.lock = Lock()
        self.watcher = None
        self.collection = collection
        self.ready = Event()

    def callback(self, snaps, changes, read_time):
        for doc in snaps:
            _id, data = doc.id, doc.to_dict()
            if _id not in self.cache or self.cache.get(_id) != data:
                with self.lock:
                    self.cache[doc.id] = data
        self.ready.set()

    def watch(self, query=None):
        if not query:
            query = self.collection
        self.watcher = query.on_snapshot(self.callback)
    
        if not self.ready.is_set():
            self.ready.wait()

    def get(self, key):
        with self.lock:
            value = self.cache.get(key)
        if not value:
            raise KeyError(f"Key {key} doesn't exist in the cache.")
        else:
            return value
