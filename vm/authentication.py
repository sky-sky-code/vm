from vm.db.models import VM
from response import JSONResponse


class AuthMiddleware:

    def __init__(self, app, *args, **kwargs):
        self.app = app
        self.args = args
        self.kwargs = kwargs

    async def __call__(self, scope, body, sock):
        auth = scope['headers'].get('Authorization', None)
        if auth is not None:
            scheme, credentials = auth.split()
            if scheme.lower() == 'bearer':
                data_vm = await VM.get(token=credentials)
                if data_vm is not None:
                    scope['vm'] = VM(**data_vm)
        return await self.app(scope, body, sock)
