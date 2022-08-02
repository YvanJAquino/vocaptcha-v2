import copy
import argparse
import json
import importlib

from google.cloud import firestore

from service.vocaptcha.server import VoCaptchaManager, VoCaptchaConfig


class VoCaptchaDataManager:

    def __init__(self, config: VoCaptchaConfig):
        self.plugins = config.plugins
        self.collection = config.collection
        self.plugin_folder = config.pluginFolder

        self.plugin_classes = self.load_plugins_classes()
        

    def load_plugins_classes(self):
        plugin_classes = []
        for plugin in self.plugins:
            module_path = f'service.{self.plugin_folder}.{plugin.module}'
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, plugin.cls)
            plugin_classes.append(plugin_class)
        return plugin_classes

    def _make_plugin_documents(self):
        for plugin in self.plugin_classes:
            plugin_module = plugin.__module__
            root, folder, module_name = plugin_module.split('.')
            path = '/'.join((folder, module_name + '.json'))
            ref = self.collection.document(plugin.DOC)
            doc = ref.get()
            with open(path, 'w') as dest:
                doc_dict = doc.to_dict()
                json.dump(doc_dict, dest, indent=2)

    def load_plugin_documents(
        self, 
        coll: firestore.CollectionReference=None
    ):
        if coll:
            self.collection = coll
        self.backup_plugin_documents()
        for plugin in self.plugin_classes:
            plugin_module = plugin.__module__
            root, folder, module_name = plugin_module.split('.')
            path = '/'.join((folder, module_name + '.json'))
            ref = self.collection.document(plugin.DOC)
            with open(path, 'r') as src:
                doc_dict = json.load(src)
                ref.set(doc_dict)

    def backup_plugin_documents(self):
        backup_coll = copy.copy(self.collection)        
        backup_coll_name = backup_coll._path[0] + "-backup"
        backup_coll._path = (backup_coll_name,)
        for plugin in self.plugin_classes:
            plugin_module = plugin.__module__
            root, folder, module_name = plugin_module.split('.')
            path = '/'.join((folder, module_name + '.json'))
            source_doc_ref = self.collection.document(plugin.DOC)
            target_doc_ref = backup_coll.document(plugin.DOC)
            source_doc = source_doc_ref.get()
            target_doc_ref.set(source_doc.to_dict())



class VoCaptchaCommander:

    LOAD = "load"
    DEFAULT = "default"

    def __init__(self):
        self.manager = VoCaptchaManager()
        self.data = VoCaptchaDataManager(self.manager.config)

        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(dest="subparser")
        self.load_parser = self.subparsers.add_parser(self.LOAD)
        self.load_parser.add_argument("collection_name", nargs="?", default=self.DEFAULT)
        self.args = self.parser.parse_args()
        print(self.args)
        self.route_command()

    def route_command(self):
        if self.args.subparser == self.LOAD:
            self.load()
        elif self.args.subparser == self.CHECK:
            self.check()
        else:
            raise KeyError("Oops, that's not a recognized command")

    def load(self):
        if self.args.collection_name == self.DEFAULT:
            self.data.load_plugin_documents()
        else:
            fs = firestore.Client()
            coll = fs.collection(self.args.collection_name)
            self.data.load_plugin_documents(coll=coll)

    def check(self):
        print("check not implemented yet..!")
        NotImplemented

if __name__ == "__main__":
    cli = VoCaptchaCommander()
