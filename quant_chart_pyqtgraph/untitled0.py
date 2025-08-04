import json
import time
from collections import deque
from decimal import Decimal

import numpy as np
import pyqtgraph as pg
from binance import ThreadedDepthCacheManager
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon


class RightAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [str(format_value(value, 1)) for value in values]


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [
            QtCore.QTime().currentTime().addMSecs(int(value / 1000)).toString("mm:ss")
            for value in values
        ]


def format_value(val, step_size):
    return float(Decimal(str(val)) - (Decimal(str(val)) % Decimal(str(step_size))))

class MyWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Quant Chart")
        self.useOpenGL(True)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.tick_size = 1
        self.lvls = {}
        self.lvl = 0
        self.ms_history = 10000
        self.fps = 100
        self.interval = 1000 // self.fps

        dcm = ThreadedDepthCacheManager()
        dcm.start()
        dcm_name = dcm.start_depth_cache(self.handle_depth_cache, symbol="BTCUSDT")

        self.client = SpotWebsocketStreamClient(on_message=self.handle_socket_message)
        self.client.kline(symbol="btcusdt", interval="1s")

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(self.interval)  # in milliseconds
        self.timer.start()
        self.timer.timeout.connect(self.handle_depth_plot)

        self.plotItem = self.addPlot(
            axisItems={
                "bottom": TimeAxisItem(orientation="bottom"),
                "right": RightAxisItem(orientation="right"),
            }
        )

        self.grid = pg.GridItem(pen=pg.mkPen("#ffffff", width=2))
        self.grid.setTickSpacing(x=[self.ms_history], y=[self.tick_size])
        self.grid.setPen(pg.mkPen("#ffffff", width=2))
        self.grid.setTextPen(None)
        self.plotItem.addItem(self.grid)
        
        self.plotDataItem2 = pg.PlotCurveItem(
            [],
            pen=pg.mkPen("#ffffff", width=2),
        )
        
        self.plotDataItem2.setSegmentedLineMode(mode='on')
        self.plotItem.addItem(self.plotDataItem2)

        self.plotItem.showAxis("right")
        self.plotItem.hideAxis("left")
        self.plotItem.showGrid(False, True, 1)
        ax = self.plotItem.getAxis("right")
        ticks = [0]
        for i in range(1, 100000):
            ticks.append(ticks[i - 1] + self.tick_size)
        ax.setTicks([[(v, str(v)) for v in ticks]])
        ax.setGrid(True)
        
        self.price_text = pg.TextItem(
            anchor=(1, 0.5), 
            fill= '#000000', 
            color="#ffffff"
        )
        self.p1 = self.plotItem.vb
        self.p1.scene().addItem(self.price_text)

        self.price_x = deque([], maxlen=self.ms_history // self.interval)
        self.price = deque([], maxlen=self.ms_history // self.interval)
        self.vol = 10
        self.volume = deque([], maxlen=self.ms_history)
        self.last_price = 0

    def handle_socket_message(self, _, msg):
        msg = json.loads(msg)
        if "e" in msg and msg["e"] == "error":
            self.client.stop()
            self.client.kline(symbol="btcusdt", interval="1s")
            return
        if "e" in msg and msg["e"] == "kline":
            self.last_price = float(msg["k"]["c"])

    def handle_depth_cache(self, depth_cache):
        bid = depth_cache.get_bids()[:100]
        ask = depth_cache.get_asks()[:100]
        self.lvl = bid + ask
        self.update_time = depth_cache.update_time
        self.handle_depth_update()

    def handle_depth_update(self):
        while True:
            if not self.lvl:
                time.sleep(1)
                continue
            break
        
        lvl = self.lvl.copy()
        
        for i in np.array(lvl)[:, 0]:
            price = format_value(i, self.tick_size)
            if price in self.lvls:
                self.lvls[price][0] = 0
        
        for i in range(len(lvl)):
            price = format_value(lvl[i][0], self.tick_size)
            volume = lvl[i][1]
            if price in self.lvls:
                self.lvls[price][0] += volume
                continue
            self.lvls[price] = [
                volume,
                self.update_time,
                pg.PlotCurveItem(pen=pg.mkPen("#ffffff", width=1)),
                deque([], maxlen=self.ms_history // self.interval),
                deque([], maxlen=self.ms_history // self.interval)
            ]
            self.lvls[price][2].setSegmentedLineMode('on')
            self.plotItem.addItem(self.lvls[price][2])
            
        for i in np.array(lvl)[:, 0]:
            price = format_value(i, self.tick_size)
            if price in self.lvls:
                self.volume.append(self.lvls[price][0])

        self.vol = np.median(self.volume)

    def handle_depth_plot(self):
        plot_time = int(time.time() * 1000)
        self.price_text.setText(text=str(self.last_price))
        y = self.p1.mapViewToScene(QtCore.QPointF(0, self.last_price)).y()
        self.price_text.setPos(self.width(), y)
        
        y_min=self.last_price - 10 * self.tick_size
        y_max=self.last_price + 10 * self.tick_size

        for p in list(self.lvls.keys()):
            if (time.time() * 1000 - self.lvls[p][1] > self.ms_history * 2 
                and (p < y_min or p >  y_max)):
                self.plotItem.removeItem(self.lvls[p][2])
                del self.lvls[p]
                continue
            volume = self.lvls[p][0]
            factor = volume / self.vol if (volume / self.vol) < 1 else 1
            y = p + self.tick_size * factor
            self.lvls[p][3].append(plot_time)
            self.lvls[p][4].append(y)
            xs = []
            ys = []
            for i in range(-1, -len(list(self.lvls[p][3])), -1):
                if plot_time - self.lvls[p][3][i] > self.ms_history:
                    break
                xs.append(self.lvls[p][3][i])
                ys.append(self.lvls[p][4][i])
            color = "#0000FF" if self.last_price > p else "#FF0000"
            self.lvls[p][2].setData(xs, ys, pen=pg.mkPen(color, width=1))
            

        if self.last_price:
            self.price.append(self.last_price)
            self.price_x.append(plot_time)

        self.plotItem.enableAutoRange(axis="x", enable=True)
        self.plotItem.setYRange(y_min, y_max, padding=0)
        y_min = self.last_price - 50 * self.tick_size
        y_max = self.last_price + 50 * self.tick_size
        self.plotItem.vb.setLimits(yMin=y_min, yMax=y_max)

        price_plot = []
        price_x_plot = []
        for i in range(len(self.price)):
            if plot_time - self.price_x[i] < self.ms_history:
                price_plot.append(self.price[i])
                price_x_plot.append(self.price_x[i])

        self.plotDataItem2.setData(price_x_plot, price_plot)


def main():
    app = QtWidgets.QApplication([])
    app.setWindowIcon(QIcon("icon.ico"))
    pg.setConfigOptions(antialias=False)
    win = MyWidget()
    win.setBackground("#000000")
    win.show()
    win.resize(1280, 720)
    win.raise_()
    app.exec_()


if __name__ == "__main__":
    main()