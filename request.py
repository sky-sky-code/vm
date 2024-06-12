import json

class Request:
    def __init__(self, scope, receive):
        self.scope = scope
        self.receive = receive

    @property
    def path(self):
        return self.scope['path']

    @property
    def headers(self):
        return self.scope['headers']

    @property
    def body(self):
        return json.loads(self.receive)
