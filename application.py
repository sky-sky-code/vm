from typing import Optional, List, Callable, Sequence
from middleware import Middleware
from routing import Router


class WebApp:

    def __init__(
            self,
            middleware: Sequence = None
    ):
        self.user_connects = []
        self.user_middleware = middleware
        self.middleware_stack: Optional = None
        self.router = Router()

    def build_middleware_stak(self):
        app = self.router
        if self.user_middleware:
            for cls, args, kwargs in reversed(self.user_middleware):
                app = cls(app=app, *args, **kwargs)
        return app

    async def __call__(self, scope, body, sock):
        scope['app'] = self
        if self.middleware_stack is None:
            self.middleware_stack = self.build_middleware_stak()
        await self.middleware_stack(scope, body, sock)

    def route(self, path, **kwargs):
        def decorator(func):
            self.router.add_route(path, func, **kwargs)
            return func

        return decorator
