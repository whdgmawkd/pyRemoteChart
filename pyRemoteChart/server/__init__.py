import asyncio
from typing import Any, Awaitable, Callable, Union
import zmq
import zmq.asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import time


class DataCollector:

    def __init__(self, data_collect_function: Callable[[], dict[str, float]], data_collect_interval: float):
        """DataCollector

        Paramaeters
        ---
        * data_collect_function `() -> dict[str, float]`: data collect funtion

        * data_collect_interval `float`: data collect function call interval
        """
        self.data: list[dict[str, float]] = []
        self._queue: asyncio.Queue[Union[dict[str, float], None]] = asyncio.Queue()
        self._queue_puller: Optional[asyncio.Task] = None
        self._data_collect_task: Optional[asyncio.Future] = None
        self._executor = ThreadPoolExecutor(thread_name_prefix='DataCollector_')
        self._data_collect_func = data_collect_function
        self._data_collect_interval = data_collect_interval
        self._is_running = False

    def __data_collect_wrapper(self):
        try:
            while self._is_running:
                t = time.time()
                data = self._data_collect_func()
                self._queue.put_nowait(data)
                e = time.time() - t
                r = self._data_collect_interval - e
                if r < 0:
                    print(f'WARNING: Data Collect Function takes {e:.2f}seconds. which is longer than interval ({self._data_collect_interval:.2f}s). please increase data collect interval.')
                if r > 0:
                    time.sleep(r)
        except asyncio.CancelledError:
            return
        except Exception:
            return

    async def __queue_pull(self):
        while True:
            data = await self._queue.get()
            if data is None:
                break
            self.data.append(data)

    async def __aenter__(self) -> 'DataCollector':
        self._is_running = True
        self._queue_puller = asyncio.create_task(self.__queue_pull())
        self._data_collect_task = asyncio.get_event_loop().run_in_executor(self._executor, self.__data_collect_wrapper)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._is_running = False
        await self._data_collect_task
        await self._queue.put(None)
        await self._queue_puller

    async def get_data(self, at: int) -> dict[str, float]:
        """return data of given index.

        if data is not ready, function wait until data is ready.

        Parameter
        ---
        * at `int`: data index
        """
        while len(self.data) <= at:
            await asyncio.sleep(0)
        return self.data[at]


class ZmqJsonServer:

    def __init__(self, request_handler: Callable[[dict[str, Any]], Awaitable[Optional[dict[str, Any]]]], host: str = '*', port: int = 60001):
        """ZmqJsonServer

        Parameters
        ---
        * request_handler `(dict[str,Any]) -> Coroutine[dict[str,Any] | None]`: callback function to create response data

        * host `str`: Listening Address

        * post `int`: Listeneing Port
        """
        self._request_handler = request_handler
        self._ctx = zmq.asyncio.Context()
        self._sock = self._ctx.socket(zmq.REP)
        self._sock.bind(f'tcp://{host}:{port}')
        self._is_running = False

    async def __aenter__(self) -> 'ZmqJsonServer':
        self._is_running = True
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._is_running = False
        pass

    async def serve_forever(self):
        """run server until cancelled"""
        try:
            while True:
                request = await self._sock.recv_json()
                response = await self._request_handler(request)
                if response is None:
                    await self._sock.send_json(None)
                    break
                await self._sock.send_json(response)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            pass
