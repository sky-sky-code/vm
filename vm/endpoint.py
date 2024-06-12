import string
import random
import uuid

from application import WebApp
from server import Server
from response import JSONResponse
from request import Request
from middleware import Middleware

from authentication import AuthMiddleware
from db.models import VM, HardDisk

import asyncio

app = WebApp(
    middleware=[
        Middleware(AuthMiddleware)
    ]
)


@app.route("/")
async def index(request: Request):
    result = await VM.all()
    return JSONResponse(result, 200, request.headers)


@app.route('/add/')
async def add_vm(request: Request):
    info_hard_disk = request.body.pop('hard_disk')
    token = ''.join(random.choice(string.ascii_letters) for x in range(8))
    vm = await VM(**request.body | {"uid": uuid.uuid4(), "token": token}).create()
    hard_disk = await HardDisk(**info_hard_disk | {"uid": uuid.uuid4(), "vm": str(vm['uid'])}).create()
    return JSONResponse(vm, 200, request.headers)


@app.route('/update/')
async def update_vm(request: Request):
    if request.scope.get('vm', None) is None:
        return JSONResponse({'msg': 'You don`t have permissions to request'}, 403, request.headers)
    await request.scope['vm'].save(**request.body)
    upd_vm = await VM.filter(uid=str(request.scope['vm'].uid))
    return JSONResponse(upd_vm, 201, request.headers)


@app.route('/logout/')
async def logout(request: Request):
    pass


@app.route('/hardisk/')
async def info_hard(request: Request):
    result = await VM.join()
    return JSONResponse(result, 200, request.headers)


if __name__ == '__main__':
    server = Server('localhost', 8000, app)
    asyncio.run(server.run())
