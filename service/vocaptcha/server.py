import time
import importlib
import yaml
from typing import Optional, Union, List, Dict


from starlette.applications import Starlette
from google.cloud import firestore
from google.cloud.firestore import CollectionReference
from google.cloud import dialogflowcx_v3 as cx

from vocaptcha.plugins import VoCaptchaPlugin, Webhooks
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
    
    collection: Union[str, CollectionReference] # implement validator
    plugins: List[Plugin]
    pluginFolder: str
    agentName: str
    flowName: str
    
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
        self.agent_name = self.config.agentName
        self.flow_name = self.config.flowName



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

    webhooks_client = cx.WebhooksClient()
    pages_client = cx.PagesClient()
    flows_client = cx.FlowsClient()

    def __init__(
        self, 
        plugins: Dict[str, str], 
        collection = None,
        plugin_folder = None,
        agent_name = None,
        flow_name = None
    ):
        self.plugins = plugins
        self.collection = collection
        self.cache = ResponseCache()
        self.cache.watch(collection)
        self.plugin_folder = plugin_folder
        self.agent_name = agent_name
        self.flow_name = self.agent_name + f'/flows/{flow_name}'
        
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

    @property
    def current_webhooks(self):
        list_webhooks = self.webhooks_client.list_webhooks(parent=self.agent_name)
        time.sleep(1)
        return {
            webhook.display_name: webhook
            for webhook in list(list_webhooks)
        }

    @property
    def plugin_webhooks(self):
        plugin_webhooks = []
        for plugin in self.plugins:
            module_path = f'{self.plugin_folder}.{plugin.module}'
            module = importlib.import_module(module_path)
            plugin = getattr(module, plugin.cls)
            instance = plugin(
                cache=self.cache
            )
            plugin_webhooks.append(instance.webhooks)

        return {
            webhook.display_name: webhook
            for _webhook in plugin_webhooks
            for webhook in _webhook.yield_pair() 
        }

    def inject_webhooks(self):
        print("Proposed webhooks:\n\t - - - - -")
        for hook in self.plugin_webhooks:
            print(hook)

        for _display_name, webhook in self.plugin_webhooks.items():
            if _display_name not in self.current_webhooks:
                result = self.webhooks_client.create_webhook(
                    webhook = webhook,
                    parent = self.agent_name
                )
                assert result.display_name == _display_name
                print(f"Created webhook: {_display_name}")
            else:
                current_webhook = self.current_webhooks[_display_name]
                webhook.name = current_webhook.name
                result = self.webhooks_client.update_webhook(
                    webhook = webhook
                )
                assert result.display_name == _display_name
                print(f"Updated webhook: {_display_name}")
            time.sleep(1)     

    @property
    def current_pages(self):
        list_pages = self.pages_client.list_pages(parent=self.flow_name)
        time.sleep(1)
        return {
            page.display_name: page
            for page in list(list_pages)
        }

    @property
    def plugin_pages(self):
        plugin_pages = []
        for plugin in self.plugins:
            module_path = f'{self.plugin_folder}.{plugin.module}'
            module = importlib.import_module(module_path)
            plugin = getattr(module, plugin.cls)
            instance = plugin(
                cache=self.cache
            )
            plugin_pages.append(instance.pages)

        return {
            page.display_name: page
            for _page in plugin_pages
            for page in _page.yield_pair() 
        }

    def inject_pages(self):
        print("Proposed pages:\n\t - - - - -")
        for page in self.plugin_pages:
            print(page)

        for _display_name, page in self.plugin_pages.items():
            if _display_name not in self.current_pages:
                result = self.pages_client.create_page(
                    page = page,
                    parent = self.flow_name
                )
                assert result.display_name == _display_name
                print(f"Created page: {_display_name}")
            else:
                current_page = self.current_pages[_display_name]
                page.name = current_page.name
                result = self.pages_client.update_page(
                    page = page
                )
                assert result.display_name == _display_name
                print(f"Updated page: {_display_name}")
            time.sleep(1)
        
        router_page = cx.Page()
        router_page.display_name = "router"
        if "router" not in self.current_pages:
            result = self.pages_client.create_page(
                page = router_page,
                parent = self.flow_name
            )
            assert result.display_name == router_page.display_name   
            time.sleep(1)        

    def patch_router_page(self):
        router_page = self.current_pages.get('router')
        time.sleep(1)
        print(router_page)
        plugin_count = len(self.plugins)
        router_ranges = [(
            round(n /plugin_count, ndigits=2),
            round((n+1) /plugin_count, ndigits=2)
        ) for n in range(plugin_count)]        
        conditions = [(
            f"$session.params.which-challenge > {lower} "
            f"AND $session.params.which-challenge <= {upper}"
        ) for lower, upper in router_ranges]
        generate_pages = [
            page
            for display_name, page in self.current_pages.items()
            if display_name.startswith("generate")
        ]
        transition_routes = [
            {
                "condition": condition,
                "target_page": page.name,
                "trigger_fulfillment": {}  
            } for condition, page in zip(conditions, generate_pages)
        ]
        router_page.transition_routes = transition_routes
        result = self.pages_client.update_page(
            page = router_page
        )
    
    def patch_start_flow(self):
        start_flow = self.flows_client.get_flow(
            name = self.flow_name
        )
        transition_route = start_flow.transition_routes[0]
        trigger_fulfillment = transition_route.trigger_fulfillment
        spas = trigger_fulfillment.set_parameter_actions
        spa_which_challenge = {
            "parameter": "which-challenge",
            "value": {
                "string_value":"$sys.func.RAND()"
            }
        }
        if not spas:
            spas.append(spa_which_challenge)
        else:
            spa_names = [
                spa.parameter 
                for spa in spas
            ]
            if "which-challenge" not in spa_names:
                spas.append(spa_which_challenge)
        
        router_page = self.current_pages.get('router')
        start_flow.transition_routes[0].target_page = router_page.name
        result = self.flows_client.update_flow(
            flow=start_flow
        )
        assert "which-challenge" in [
            spa.parameter for 
            spa in result.transition_routes[0].trigger_fulfillment.set_parameter_actions
        ]
