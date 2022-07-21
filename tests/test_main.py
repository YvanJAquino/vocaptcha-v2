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

app = factory()

service = TestClient(app)

def test_generate_add_two_numbers():
    with open("tests/cases/generate_add_two_numbers.json") as src:
        payload = json.load(src)
    response = service.post("/add-two-numbers/generate", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])

def test_generate_nato_passphrase():
    with open("tests/cases/generate_nato_passphrase.json") as src:
        payload = json.load(src)
    response = service.post("/nato-alphabet/generate", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])

def test_generate_sentences():
    with open("tests/cases/generate_sentences.json") as src:
        payload = json.load(src)
    response = service.post("/sentences/generate", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])

# #  Skipping /add-two-numbers/verify - Works better in DFCX
# def test_verify_add_two_numbers():
#     with open("tests/cases/verify_add_two_numbers.json") as src:
#         payload = json.load(src)
#     response = service.post("/add-two-numbers/verify", json=payload)
#     assert response.status_code == 200
#     print(response.json()['sessionInfo']['parameters'])

def test_verify_nato_passphrase_strict():
    with open("tests/cases/verify_nato_passphrase_strict.json") as src:
        payload = json.load(src)
    response = service.post("/nato-alphabet/verify", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])

def test_verify_nato_passphrase_loose():
    with open("tests/cases/verify_nato_passphrase_loose.json") as src:
        payload = json.load(src)
    response = service.post("/nato-alphabet/verify", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])

def test_verify_sentences_strict():
    with open("tests/cases/verify_sentences_strict.json") as src:
        payload = json.load(src)
    response = service.post("/sentences/verify", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])

def test_verify_sentences_loose():
    with open("tests/cases/verify_sentences_loose.json") as src:
        payload = json.load(src)
    response = service.post("/sentences/verify", json=payload)
    assert response.status_code == 200
    print(response.json()['sessionInfo']['parameters'])