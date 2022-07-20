from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Callable
from functools import partial

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from pydantic import ValidationError

from google.cloud import dialogflowcx_v3 as cx
from google.protobuf.duration_pb2 import Duration

from cxwebhooks import WebhookRequest, WebhookResponse

CHALLENGES = 'challenges'
TEMPLATES = 'templates'

class EntityTypes:
    sys_any = "projects/-/locations/-/agents/-/entityTypes/sys.any"

@dataclass
class Pages:
    generate: cx.Page
    verify: cx.Page

    def yield_pair(self):
        return self.generate, self.verify

@dataclass
class Webhooks:
    generate: cx.Webhook
    verify: cx.Webhook

    def yield_pair(self):
        return self.generate, self.verify


class VoCaptchaPlugin(ABC):

    MOUNT = None
    TYPE = None
    DOC = None
    FIELD = None
    PARAMS = None



    def __init__(
        self, 
        cache,
        mount=None,
        type=None,
        doc=None,
        field=None,
        params=None
    ):
        self.cache = cache
        self.mount = mount or self.MOUNT
        self.type = type or self.TYPE
        self.doc = doc or self.DOC
        self.field = field or self.FIELD
        self.params = params or self.PARAMS

    def __call__(self):
        return self.generate_routes()

    @abstractmethod
    async def generate(self, webhook: WebhookRequest, templates: dict = ..., response = ...):
        ...
    
    @abstractmethod
    async def verify(self, webhook: WebhookRequest, templates: dict = ..., response = ...):
        ...

    def get_challenges(self):
        document = self.cache.get(self.doc)
        challenges = document.get(CHALLENGES)
        if not challenges:
            raise NotImplementedError("No challenges found!  Please review.")
        return challenges

    def get_templates(self):
        document = self.cache.get(self.doc)
        templates = document.get(TEMPLATES)
        if not templates:
            raise NotImplementedError("No templates found!  Please review.")
        return templates

    def generate_routes(self):
        """
            need to test and see if partial is working as desired.
        """
        mount_name = self.MOUNT.replace("/", "")
        generate = partial(self.adapt, endpoint=self.generate)
        verify = partial(self.adapt, endpoint=self.verify)
        mount = Mount(self.mount, name=mount_name, routes=[
            Route("/generate", generate, methods=["GET", "POST"], name="generate"),
            Route("/verify", verify, methods=["GET", "POST"], name="verify")
        ])
        return mount

    async def adapt(self, request: Request, endpoint: Callable):
        if request.method == "POST":
            try:
                body = await request.json()
                webhook = WebhookRequest(**body)
            except ValidationError as e:
                return JSONResponse({
                    "message": "Request body does not conform to WebhookRequest specification.",
                    "status_code": "422 UNPROCESSABLE ENTITY"
                }, status_code=422)
        else:
            webhook = None
        model_response = await endpoint(
            webhook, 
            templates=self.get_templates(), 
            response=WebhookResponse()
        )
        response = JSONResponse(model_response.dict(exclude_none=True))
        return response

    @property
    def pages(self):
        generate_page = cx.Page()
        generate_page.display_name = "generate-" + self.mount[1:]


        verify_page = cx.Page()
        verify_page.display_name = "verify-" + self.mount[1:]
        return Pages(
            generate=generate_page,
            verify=verify_page
        )

    @property
    def webhooks(self):
        generate_webhook = cx.Webhook()
        generate_webhook.display_name = "generate-" + self.mount[1:]
        generate_webhook.timeout = Duration(seconds=7)
        generate_webhook.generic_web_service.uri = "https://replace.me"

        verify_webhook = cx.Webhook()
        verify_webhook.display_name = "verify-" + self.mount[1:]
        verify_webhook.timeout = Duration(seconds=7)
        verify_webhook.generic_web_service.uri = "https://replace.me"
        return Webhooks(
            generate=generate_webhook,
            verify=verify_webhook
        )