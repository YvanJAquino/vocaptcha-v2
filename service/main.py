import yaml

from vocaptcha.server import VoCaptchaServer, VoCaptchaManager

manager = VoCaptchaManager()
config = manager.config

app = VoCaptchaServer(
    plugins=config.plugins,
    collection=config.collection,
    plugin_folder=config.pluginFolder
)

