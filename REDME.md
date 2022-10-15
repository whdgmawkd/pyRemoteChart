# pyRemoteChart

Client - Server 기반 실시간 데이터 Chart 표시 라이브러리

## Concept

JSON 형태로 요청 및 응답 형태를 사용자가 구현

Server - Client 구조를 통해 원격 환경에서 실행 가능

## Examples

### Server

`generate_data` 함수를 수정하여 원하는 데이터를 보낼 수 있음

```python
from pyRemoteChart.server import ZmqJsonServer, DataCollector
import asyncio
import time

def generate_data():
    return {'a': time.time() % 10, 'b': 1}

async def main():
    collector = DataCollector(generate_data, 0.1)
    async with collector:
        async def request_handler(request_json):
            requested_index = request_json['index']
            response_data = await collector.get_data(requested_index)
            return response_data
        server=ZmqJsonServer(request_handler)
        async with server:
            await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
```

### Client

`client.request`의 요청 데이터 형식을 수정하여 원하는 형태로 변경 가능

```python
from pyRemoteChart.client import ZmqJsonClient, DataDrawer

if __name__ == '__main__':
    index=0
    drawer=DataDrawer()
    client = ZmqJsonClient('127.0.0.1', 60001)
    with client, drawer:
        while True:
            response = client.request({'index': index})
            if response is None:
                break
            index+=1
            drawer.add_data(response)
            drawer.update()
```
