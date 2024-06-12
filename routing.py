from typing import Optional, List
from request import Request
from response import JSONResponse


def request_response(func):
    async def app(scope, body, sock):
        request = Request(scope, body)

        async def app(sock):
            response = await func(request)
            await response(sock)

        await app(sock)

    return app


class Route:
    def __init__(self, path, endpoint):
        self.path = path
        self.endpoint = endpoint
        self.app = request_response(endpoint)

    async def handle(self, scope, body, sock):
        await self.app(scope, body, sock)


class Router:

    def __init__(self, routes=None):
        self.routes = [] if routes is None else list(routes)
        self.middleware_stack = self.app

    async def __call__(self, scope, body, sock):
        return await self.middleware_stack(scope, body, sock)

    async def app(self, scope, body, sock):
        if "router" not in scope:
            scope["router"] = self

        for route in self.routes:
            if route.path == scope['path']:
                await route.handle(scope, body, sock)

    def add_route(self, path, func, **kwargs):
        route = Route(path, func)
        self.routes.append(route)
