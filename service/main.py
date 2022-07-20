import yaml

from vocaptcha.server import VoCaptchaServer, VoCaptchaManager

manager = VoCaptchaManager()
config = manager.config

app = VoCaptchaServer(
    plugins=config.plugins,
    collection=config.collection,
    plugin_folder=config.pluginFolder,
    agent_name=config.agentName,
    flow_name=config.flowName
)

# print(app.current_pages.keys())
# print(app.plugin_pages.keys())
# print(app.plugin_webhooks.keys())
print(app.inject_pages())