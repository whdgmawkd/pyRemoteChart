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