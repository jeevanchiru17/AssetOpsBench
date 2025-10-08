import logging
import random
import string
import time

from litestar import Litestar, Request
from litestar.middleware import DefineMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send
from scenario_server.endpoints import (
    OPENAPI_CONFIG,
    fetch_scenario,
    grade_submission,
    register_scenario_handlers,
    scenario_types,
    set_tracking_uri,
)

logger: logging.Logger = logging.getLogger("scenario-server")


class RequestTimingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if "http" == scope["type"]:
            request = Request(scope)

            bag: str = string.ascii_lowercase + string.digits
            rid: str = "".join(random.choices(bag, k=12))
            request.state["rid"] = rid

            logger.info(f"[{rid}] > request: {request.url.path} {request.client}")
            t1: float = time.perf_counter()

            await self.app(scope, receive, send)

            logger.info(
                f"[{rid}] < response: {request.url.path}  {time.perf_counter() - t1:0.5f}"
            )
        else:
            await self.app(scope, receive, send)


def get_app(
    handlers: list = [], include_default_handlers: bool = True, tracking_uri: str = ""
) -> Litestar:
    if tracking_uri != "":
        set_tracking_uri(tracking_uri=tracking_uri)

    if len(handlers) > 0:
        register_scenario_handlers(handlers=handlers)

    if include_default_handlers:
        register_scenario_handlers(handlers=[])

    app = Litestar(
        debug=True,
        middleware=[DefineMiddleware(RequestTimingMiddleware)],
        route_handlers=[scenario_types, fetch_scenario, grade_submission],
        openapi_config=OPENAPI_CONFIG,
    )

    return app
