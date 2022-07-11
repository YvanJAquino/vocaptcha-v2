import importlib
from typing import List, Dict

from starlette.applications import Starlette
from google.cloud import firestore
from vocaptcha.plugins import VoCaptchaPlugin
from vocaptcha.cache import ResponseCache


class VoCaptchaServer:

    def __init__(
        self, 
        plugins: Dict[str, str], 
        collection = None,
        plugin_folder = None
    ):
        self.plugins = plugins
        self.collection = collection
        self.cache = ResponseCache()
        self.cache.watch(collection)
        self.plugin_folder = plugin_folder
        
    def __call__(self):
        routes = []
        for module_name, plugin_class in self.plugins.items():
            module_path = f'{self.plugin_folder}.{module_name}'
            module = importlib.import_module(module_path)
            plugin = getattr(module, plugin_class)
            plugin_instance = plugin(
                cache=self.cache
            )
            plugin_routes = plugin_instance()
            routes.append(plugin_routes)
        return Starlette(routes=routes)

