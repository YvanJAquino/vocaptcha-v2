from secrets import SystemRandom

from fuzzywuzzy import fuzz

from cxwebhooks import WebhookRequest, WebhookResponse
from service.vocaptcha.plugins import VoCaptchaPlugin



class SentencesPlugin(VoCaptchaPlugin):

    MOUNT = "/sentences"
    TYPE = "sentence-repetition"
    DOC = "sentences"
    PARAMS = {
        "fuzz_threshold": 70
    }

    def challenge(self):
        picker = SystemRandom()
        sentences = self.get_challenges()
        return picker.choice(sentences)

    async def generate(
        self, 
        webhook: WebhookRequest, 
        templates=...,
        response=...
    ):
        sentence = self.challenge()
        text = templates['generate']['text'].format(sentence=sentence)
        ssml = templates['generate']['ssml'].format(sentence=sentence)
        response.add_text_response(text)
        response.add_audio_text_response(ssml)
        response.add_session_params({
            "challenge": sentence,
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
        ratio = fuzz.ratio(challenge, challenge_response)
        print(f"{self.TYPE} - FUZZ RATIO: ", ratio)
        print(f"challenge: {challenge} - response: {challenge_response}")
        match = 'match' if ratio > self.PARAMS['fuzz_threshold'] else "don't match"
        is_match = True if match == 'match' else False
        text = templates['verify']['text'].format(
            challenge=challenge,
            challenge_response=challenge_response,
            match=match
        )
        response.add_text_response(text)
        response.add_audio_text_response(text)
        response.add_session_params({
            "challenge-response": challenge_response,
            "challenge-passed": is_match
        })
        return response
