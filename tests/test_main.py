import os
import json
from starlette.testclient import TestClient

from service.vocaptcha.server import VoCaptchaServer, VoCaptchaManager

manager = VoCaptchaManager(
    # Have to patch-in the config.
    path="service/vocaptcha.yaml"
)

config = manager.config

factory = VoCaptchaServer(
    plugins=config.plugins,
    collection=config.collection,
    plugin_folder=config.pluginFolder,
    agent_name=config.agentName,
    flow_name=config.flowName
)

service = TestClient(app)

def test_working_directory():
    cwd = os.getcwd()
    print(f"CURRENT WORKING DIR: {cwd}")

def test_cache():
    collection = config.collection
    for doc in collection.stream():
        print(doc.to_dict())
    print(factory.cache.cache)

def test_generate_add_two_numbers():
    with open("tests/cases/generate_add_two_numbers.json") as src:
        payload = json.load(src)
    response = service.post("/add-two-numbers/generate", json=payload)
    assert response.status_code == 200
    print(response.json())
    