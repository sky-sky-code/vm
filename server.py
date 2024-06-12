import asyncio
import socket
import email
from typing import Optional
from request import Request

MAX_LINE = 64 * 1024
MAX_HEADERS = 100


class Server:
    def __init__(self, host, port, app: Optional = None):
        self.app = app
        self.host = host
        self.port = port

    def parse_request(self, req_str):
        body = req_str.split('\r\n\r\n', 1)[-1]
        first_line, headers = req_str.split('\r\n', 1)
        headers = dict(email.message_from_string(headers).items())
        method, path, proto = first_line.split()
        scope = {
            'method': method,
            "path": path,
            "proto": proto,
            "headers": headers
        }
        return scope, body

    async def serve_conn(self, sock, addr):
        loop = asyncio.get_event_loop()
        print("Connected by", addr)
        request_line = await loop.sock_recv(sock, MAX_LINE)
        if request_line == b'':
            sock.close()
            return
        scope, body = self.parse_request(request_line.decode('utf8'))
        await self.app(scope, body, sock)
        sock.close()

    async def run(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serv_sock.bind((self.host, self.port))
            serv_sock.listen()

            serv_sock.setblocking(False)
            print('Server started')

            loop = asyncio.get_event_loop()
            while True:
                print('Waiting for connection')
                sock, addr = await loop.sock_accept(serv_sock)
                loop.create_task(self.serve_conn(sock, addr))
        except Exception as e:
            print("Client serving failed", e)
        finally:
            serv_sock.close()
