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