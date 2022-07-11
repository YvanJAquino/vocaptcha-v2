from secrets import SystemRandom
from string import ascii_lowercase
from cxwebhooks import WebhookRequest, WebhookResponse

from vocaptcha.plugins import VoCaptchaPlugin


class NATOAlphaPlugin(VoCaptchaPlugin):

    MOUNT = "/nato-alphabet"
    TYPE = "nato-alphabet-passphrase"
    DOC = "nato-alphabet"
    PARAMS = {
        "num_words": 3
    }

    def challenge(self):
        words = self.get_challenges()
        picker = SystemRandom()
        letters = set()
        while len(letters) < self.params.get('num_words'):
            letter = picker.choice(ascii_lowercase)
            letters.add(letter)

        passphrase = []
        for letter in letters:
            word = words[letter]
            passphrase.append(word)

        return ', '.join(passphrase), iter(passphrase)

    async def generate(
        self, 
        webhook: WebhookRequest, 
        templates=...,
        response=...
    ):
        phrase, words = self.challenge()
        text = templates['generate']['text'].format(phrase=phrase)
        ssml = templates['generate']['ssml'].format(phrase=phrase)
        response.add_text_response(text)
        response.add_audio_text_response(ssml)
        response.add_session_params({
            "challenge": " ".join(words),
            "challenge-type": self.TYPE
        })
        return response

    async def verify(
        self, 
        webhook: WebhookRequest, 
        templates=...,
        response=...
    ):
        parameters = webhook.sessionInfo.parameters
        challenge = parameters.get('challenge')
        challenge_type = parameters.get('challenge-type')
        if challenge_type != self.TYPE or challenge is None:
            response.add_text_response("Something went wrong.  Please reach out!")
            return response
        challenge_response = parameters.get('challenge-response')
        match = 'match' if challenge == challenge_response else "don't match"
        text = templates['generate']['text'].format(
            challenge=challenge,
            challenge_response=challenge_response,
            match=match
        )
        response.add_text_response(text)
        response.add_audio_text_response(text)
        response.add_session_params({
            "challenge-response": challenge_response
        })
        return response
