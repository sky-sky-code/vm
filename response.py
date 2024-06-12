import json
import asyncio
import uuid


class JSONEncoderSupportUUID(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class JSONResponse:
    media_type = 'application/json'

    def __init__(self, content, status_code, headers):
        self.content = content
        self.status_code = status_code
        self.headers = self.init_headers(headers)
        self.body = self.render(content)

    def init_headers(self, headers):
        headers['Content-type'] = self.media_type
        return headers

    def render(self, content):
        return json.dumps(
            content,
            cls=JSONEncoderSupportUUID,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        )

    async def __call__(self, sock):
        loop = asyncio.get_event_loop()
        http_headers = '\r\n'.join([f'{key}: {value}' for key, value in self.headers.items()])
        await loop.sock_sendall(sock, bytes(f'HTTP/1.1 {self.status_code} ОК\r\n{http_headers}\r\n\r\n{self.body}',
                                            encoding='utf8'))
