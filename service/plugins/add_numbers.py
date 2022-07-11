from random import randint
from string import ascii_lowercase
from cxwebhooks import WebhookRequest, WebhookResponse

from vocaptcha.plugins import VoCaptchaPlugin


class AddTwoNumbersPlugin(VoCaptchaPlugin):

    MOUNT = "/add-two-numbers"
    TYPE = "add-two-numbers"
    DOC = "add-two-numbers"
    PARAMS = {
        "min": 1,
        "max": 10
    }

    def challenge(self):
        MIN = self.PARAMS.get('min')
        MAX = self.PARAMS.get('max')
        num1 = randint(MIN, MAX)
        num2 = randint(MIN, MAX)
        return num1, num2

    async def generate(
        self, 
        webhook: WebhookRequest, 
        templates=...,
        response=...
    ):
        num1, num2 = self.challenge()
        text = templates['generate']['text'].format(num1=num1, num2=num2)
        ssml = templates['generate']['ssml'].format(num1=num1, num2=num2)
        response.add_text_response(text)
        response.add_audio_text_response(ssml)
        response.add_session_params({
            "challenge": num1 + num2,
            "challenge-type": self.TYPE
        })
        return response

    async def verify(
        self, 
        webhook: WebhookRequest, 
        templates=...,
        response=...
    ):
        ...