from google.cloud import firestore

from vocaptcha.server import VoCaptchaServer

plugins = {
    'nato_alpha': 'NATOAlphaPlugin',
    'sentences': 'SentencesPlugin',
    'add_numbers': 'AddTwoNumbersPlugin'
}
fs = firestore.Client()
collection = fs.collection('vocaptcha-v3-plugins')
plugin_folder = 'plugins'

app = VoCaptchaServer(
    plugins=plugins,
    collection=collection,
    plugin_folder=plugin_folder
)

