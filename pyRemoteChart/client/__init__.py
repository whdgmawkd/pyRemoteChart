import asyncio
from typing import Any
from matplotlib.lines import Line2D
import zmq
import zmq.asyncio
from concurrent.futures import ThreadPoolExecutor
from matplotlib import artist, pyplot as plt
import numpy as np
import pandas as pd
import math


class DataDrawer:

    def __init__(self, data_size: int = 100):
        """DataDrawer

        Parameters
        ---

        * data_size `int`: Data count to draw in chart
        """
        self._data_size = data_size
        self._fig, self._ax = plt.subplots()
        self._ax.set_xlim(0, 100)
        self._artists: dict[str, Line2D] = dict()
        self._bg = None
        self._canvas = self._fig.canvas
        self._data = pd.DataFrame()
        self._cid = self._canvas.mpl_connect("draw_event", self.on_draw)
        self._is_resized = False
        self._ylim = (0, 1)

    def _round_lim(self, val: float):
        sign = 1
        if val < 0:
            sign = -1
            val *= -1
        if val < 1:
            return 0
        log_value = math.log10(val)
        exp = int(log_value)
        mul = int(10**(log_value-exp)) + 1
        return sign * (10**exp) * mul

    def __enter__(self):
        plt.show(block=False)
        plt.pause(0.05)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def on_draw(self, event):
        cv = self._canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def _draw_animated(self):
        fig = self._canvas.figure
        for name, artist in self._artists.items():
            fig.draw_artist(artist)

    def update(self):
        """update chart with updated data"""
        cv = self._canvas
        fig = cv.figure
        if self._bg is None:
            self.on_draw(None)
        else:
            cv.restore_region(self._bg)
            self._draw_animated()
            cv.blit(fig.bbox)
        if self._is_resized:
            cv.resize_event()
            self._is_resized = False
        cv.flush_events()

    def add_data(self, json_data: dict[str, float]):
        """add new data row"""
        self._data = pd.concat([self._data, pd.DataFrame([json_data])], ignore_index=True, sort=False)
        for colname in self._data.columns:
            data_list = self._data[colname].to_list()
            if len(data_list) < self._data_size:
                data_list = [0 for x in range(self._data_size - len(data_list))] + data_list
            data_list = data_list[-self._data_size:]
            if colname not in self._artists:
                (self._artists[colname],) = self._ax.plot(data_list, animated=True)
                self._artists[colname].set_animated(True)
            self._artists[colname].set_ydata(data_list)
            new_ylim = (self._round_lim(self._data.min().min()), self._round_lim(self._data.max().max()))
            if (self._ylim != new_ylim):
                self._is_resized = True
                self._ax.set_ylim(*new_ylim)
                self._ylim = new_ylim


class ZmqJsonClient:

    def __init__(self, host: str, port: int):
        """ZmqJsonClient

        Parameters
        ---
        * host `str`: Server Address

        * port `int`: Server Listening Port
        """
        self._host = host
        self._port = port
        self._ctx = zmq.Context()
        self._sock: zmq.Socket = self._ctx.socket(zmq.REQ)
        self._sock.connect(f'tcp://{self._host}:{self._port}')
        self._is_running = False

    def __enter__(self):
        self._is_running = True
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self._is_running = False

    def request(self, json_body: dict[str, Any]) -> dict[str, Any]:
        """request to server with given data

        Parameter
        ---
        * json_body `dict[str,Any]`: data to send to server
        """
        self._sock.send_json(json_body)
        response_data = self._sock.recv_json()
        return response_data
