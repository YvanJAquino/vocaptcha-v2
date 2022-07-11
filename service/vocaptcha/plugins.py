from abc import ABC, abstractmethod
from typing import List, Callable
from functools import partial

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from pydantic import ValidationError

from cxwebhooks import WebhookRequest, WebhookResponse

CHALLENGES = 'challenges'
TEMPLATES = 'templates'

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
        generate = partial(self.adapt, endpoint=self.generate)
        verify = partial(self.adapt, endpoint=self.verify)
        mount = Mount(self.mount, routes=[
            Route("/generate", generate, methods=["GET", "POST"]),
            Route("/verify", verify, methods=["GET", "POST"])
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
