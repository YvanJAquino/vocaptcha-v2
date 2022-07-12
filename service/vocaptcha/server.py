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

    """
    Pydantic definitions for the Plugin object.
    """

    module: str
    cls: str
    parameters: Optional[Dict[str, str]]


class VoCaptchaConfig(BaseModel):

    """
    Pydantic definitions for the VoCaptcha Config.
    """

    class Config:
        arbitrary_types_allowed = True
    
    collection: Union[str, CollectionReference]
    plugins: List[Plugin]
    pluginFolder: str
    
class VoCaptchaManager:

    """
    The VoCaptcha Server Manager.  A light wrapper over the VoCaptchaConfig
    itself.  

    In the next iteration, we'll implement a Pydantic validator to circumvent
    the need to replace the "collection" which comes in as a string but
    needs to be converted into a Firestore Reference object for use with
    the firestore.*Reference.on_snapshot method.  
    """

    def __init__(self, path = "vocaptcha.yaml"):
        with open(path) as src:
            config = yaml.load(src, Loader=yaml.Loader)
        self.config = VoCaptchaConfig(**config)
        self.client = firestore.Client()
        self.config.collection = self.client.collection(self.config.collection)



class VoCaptchaServer:

    """
    The VoCaptcha Server process. VoCaptcha Server is an ASGI Factory that creates
    API routes based off the provided plugins.  

    Recommended usage:
    `
    from vocaptcha.server import VoCaptchaServer, VoCaptchaManager

    manager = VoCaptchaManager()
    config = manager.config

    app = VoCaptchaServer(
        plugins=config.plugins,
        collection=config.collection,
        plugin_folder=config.pluginFolder
    )
    `

    """

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
        """
        Creates an instance of the plugins, creates routes for those plugins,
        mounts them to their path(s), and returns an instance of Starlette that
        uvicorn will accept.  
        """
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

