import importlib
import yaml
from typing import Optional, Union, List, Dict

from starlette.applications import Starlette
from google.cloud import firestore
from google.cloud.firestore import CollectionReference

from vocaptcha.plugins import VoCaptchaPlugin
from vocaptcha.cache import ResponseCache

from pydantic import BaseModel


class Plugin(BaseModel):
    module: str
    cls: str
    parameters: Optional[Dict[str, str]]


class VoCaptchaConfig(BaseModel):
    class Config:
        arbitrary_types_allowed = True
    
    collection: Union[str, CollectionReference]
    plugins: List[Plugin]
    pluginFolder: str
    
class VoCaptchaManager:

    def __init__(self, path = "vocaptcha.yaml"):
        with open(path) as src:
            config = yaml.load(src, Loader=yaml.Loader)
        self.config = VoCaptchaConfig(**config)
        self.client = firestore.Client()
        self.config.collection = self.client.collection(self.config.collection)



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
        for plugin in self.plugins:
            module_path = f'{self.plugin_folder}.{plugin.module}'
            module = importlib.import_module(module_path)
            plugin = getattr(module, plugin.cls)
            instance = plugin(
                cache=self.cache
            )
            plugin_routes = instance()
            routes.append(plugin_routes)
        return Starlette(routes=routes)

