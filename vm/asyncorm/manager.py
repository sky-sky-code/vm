import asyncio

import asyncpg


class PoolManager:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._pool = None
        self._connection = None

    async def __aenter__(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(*self.args, **self.kwargs)

        self._connection = await self._pool.acquire()
        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._pool.release(self._connection)
        self._connection = None
