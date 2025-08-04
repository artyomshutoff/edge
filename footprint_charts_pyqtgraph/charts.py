import sqlite3
import time
import datetime

import numpy as np
import pyqtgraph as pg
from PyQt5.QtGui import QBrush, QPen, QLinearGradient, QColor
from PyQt5.QtWidgets import QGraphicsItem
from pyqtgraph import QtCore, QtGui

import utility


class CandlestickItem(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.start_time = kwargs["start_time"]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.start_time[1] - self.start_time[0]) / 3

        for i in range(len(self.start_time)):
            color = "#0CF50D"
            if self.open_price[i] > self.close_price[i]:
                color = "#F70606"
            p.setBrush(pg.mkBrush(color=color))
            p.setPen(pg.mkPen(color=color))
            x = self.start_time[i]
            y = self.low_price[i]
            y2 = self.high_price[i]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y2))
            p.setPen(pg.mkPen(color="#000"))
            x = self.start_time[i] - width
            y = self.close_price[i]
            width *= 2
            height = self.open_price[i] - self.close_price[i]
            p.drawRect(QtCore.QRectF(x, y, width, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class VolumeItem(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.start_time = kwargs["start_time"]
        self.volume = kwargs["volume"]
        self.close_price = kwargs["close_price"]
        self.open_price = kwargs["open_price"]
        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.start_time[1] - self.start_time[0]) / 3
        p.setPen(pg.mkPen(color="#000"))

        for i in range(len(self.start_time)):
            color = "#C5FF48"
            if self.open_price[i] > self.close_price[i]:
                color = "#FF3B64"
            brush = pg.mkBrush((pg.mkColor(color)))
            p.setBrush(brush)
            x = self.start_time[i] - width
            height = self.volume[i]
            p.drawRect(QtCore.QRectF(x, 0, width * 2, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class PriceLevel:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask
        self.volume = bid + ask


class Footprint:
    def __init__(self, open_time, prices, tick_size):
        self.open_time = open_time
        self.prices = prices
        self.tick_size = tick_size
        self.min_vol = 0
        self.max_vol = 0
        self.min_delta = 0
        self.max_delta = 0

        self.min_bid = 0
        self.max_bid = 0
        self.min_ask = 0
        self.max_ask = 0
        self.min_bid_ask = 0
        self.max_bid_ask = 0

    def add(self, price, bid, ask):
        if price in self.prices:
            self.prices[price].bid += bid
            self.prices[price].ask += ask
            return
        self.prices[price] = PriceLevel(bid, ask)

    def format_prices(self):
        formatted_prices = []
        for i in self.prices:
            element = [i, self.prices[i].bid, self.prices[i].ask]
            formatted_prices.append(element)
        formatted_prices.sort(key=lambda x: x[0])
        self.prices = formatted_prices.copy()

    def vol_limits(self):
        if not isinstance(self.prices, list):
            self.format_prices()
        self.min_vol = float("inf")
        self.max_vol = -float("inf")

        for i in range(len(self.prices)):
            vol = self.prices[i][1] + self.prices[i][2]
            if vol < self.min_vol:
                self.min_vol = vol
            if vol > self.max_vol:
                self.max_vol = vol

    def delta_calc(self):
        if not isinstance(self.prices, list):
            self.format_prices()
        self.min_delta = float("inf")
        self.max_delta = -float("inf")

        for i in range(len(self.prices)):
            delta = abs(self.prices[i][1] - self.prices[i][2])
            if delta < self.min_delta:
                self.min_delta = delta
            if delta > self.max_delta:
                self.max_delta = delta

    def bid_ask_limits(self):
        if not isinstance(self.prices, list):
            self.format_prices()
        self.min_bid = float("inf")
        self.max_bid = -float("inf")

        self.min_ask = float("inf")
        self.max_ask = -float("inf")

        for i in range(len(self.prices)):
            bid = self.prices[i][1]
            if bid < self.min_bid:
                self.min_bid = bid
            if bid > self.max_bid:
                self.max_bid = bid

            ask = self.prices[i][2]
            if ask < self.min_ask:
                self.min_ask = ask
            if ask > self.max_ask:
                self.max_ask = ask

        self.min_bid_ask = self.min_ask
        if self.min_bid <= self.min_ask:
            self.min_bid_ask = self.min_bid

        self.max_bid_ask = self.max_ask
        if self.max_bid >= self.max_ask:
            self.max_bid_ask = self.max_bid


class FootprintItem(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.start_time = kwargs["start_time"]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.pair = kwargs["pair"]
        self.interval = utility.interval_to_unix(kwargs["interval"], False)
        self.marker_show = kwargs["marker_show"]
        self.candle_show = kwargs["candle_show"]
        self.VA_show = kwargs["VA_show"]
        self.POC_show = kwargs["POC_show"]
        self.one_side_show = kwargs["one_side_show"]
        self.imbalance_show = kwargs["imbalance_show"]
        self.imbalance_ratio = kwargs["imbalance_ratio"]
        self.footprint_type = kwargs["footprint_type"]
        self.footprint_type = self.footprint_type.replace(" ", "_").lower()
        self.grouping = kwargs["grouping"]

        self.picture = QtGui.QPicture()
        self.p = QtGui.QPainter(self.picture)

        self.footprint_fetch()

        if self.candle_show:
            self.candle()

        if self.marker_show:
            self.marker()

        self.p.end()

    def footprint_fetch(self):
        con = sqlite3.connect("footprint.db")
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {self.pair}")
        values = cur.fetchall()

        for i in range(len(values)):
            time = values[i][0] // 1000
            tick_size = utility.exact_mult(self.grouping, values[i][4])
            price = utility.format_value(values[i][1], tick_size)
            values[i] = [
                time,
                price,
                values[i][2],
                values[i][3],
                values[i][4],
                values[i][5],
            ]

        footprint = []

        for i in range(len(values)):
            cluster_time = values[i][0] - values[i][0] % self.interval
            if not i or cluster_time != footprint[-1].open_time:
                new_value = Footprint(
                    cluster_time,
                    {values[i][1]: PriceLevel(values[i][2], values[i][3])},
                    values[i][4]
                )
                footprint.append(new_value)
                continue

            footprint[-1].add(values[i][1], values[i][2], values[i][3])

        for i in range(len(footprint)):
            footprint[i].format_prices()

        types = [
            "volume",
            "delta_colored_volume",
            "volume_delta",
            "bid_ask",
            "delta"
        ]

        self.footprint = footprint

        if self.footprint_type not in types:
            e = f"{self.footprint_type}: this footprint type dont exist!"
            raise Exception(e)

        getattr(self, self.footprint_type)()

    def candle(self):
        for i in range(len(self.start_time)):
            self.p.setBrush(pg.mkBrush(None))
            term = self.open_price[i] > self.close_price[i]
            color = "#FF3B64" if term else "#C5FF48"
            self.p.setPen(pg.mkPen(color=color, width=1))

            x = self.start_time[i]
            x += self.interval * (0.55 if self.marker_show else 0.5)

            y = self.close_price[i] if term else self.open_price[i]
            y2 = self.low_price[i]
            self.p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y2))

            y = self.high_price[i]
            y2 = self.open_price[i] if term else self.close_price[i]
            self.p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y2))

            x = self.start_time[i]
            width = self.interval
            if self.marker_show:
                x += self.interval / 10
                width *= 0.9
            y = self.close_price[i]
            height = self.open_price[i] - self.close_price[i]
            self.p.drawRect(QtCore.QRectF(x + 1, y, width - 2, height))

    def marker(self):
        self.p.setPen(pg.mkPen(color="#000"))
        for i in range(len(self.start_time)):
            color = "#C5FF48"
            if self.open_price[i] > self.close_price[i]:
                color = "#FF3B64"
            self.p.setBrush(pg.mkBrush(color=color))
            x = self.start_time[i]
            y = self.close_price[i]
            width = self.interval / 10
            height = self.open_price[i] - self.close_price[i]
            self.p.drawRect(QtCore.QRectF(x, y, width, height))

    def value_area(self, x, prices, height):
        unpack = utility.distribution_elements(prices)
        point_of_control, value_area_high, value_area_low = unpack

        pen = pg.mkPen(
            color=pg.mkColor("#fff9"),
            style=QtCore.Qt.DotLine,
            width=2
        )
        self.p.setPen(pen)
        x += self.interval * (0.1 if self.marker_show else 0)
        x2 = x + self.interval * (0.9 if self.marker_show else 1)
        x += self.interval * 0.025
        x2 -= self.interval * 0.025
        y = value_area_high
        self.p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x2, y))
        y = value_area_low - abs(height)
        self.p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x2, y))

    def volume(self):
        for i in range(len(self.footprint)):
            self.footprint[i].vol_limits()
            max_vol = self.footprint[i].max_vol
            min_vol = self.footprint[i].min_vol
            cluster = self.footprint[i].prices
            open_time = self.footprint[i].open_time
            tick_size = self.footprint[i].tick_size
            height = -utility.exact_mult(tick_size, self.grouping)

            unpack = utility.distribution_elements(cluster)
            point_of_control, value_area_high, value_area_low = unpack

            for j in range(len(cluster)):
                price, bid, ask = cluster[j]
                vol = bid + ask

                color = "#000"
                if self.imbalance_show and j != len(cluster) - 1:
                    if bid >= cluster[j + 1][2] * self.imbalance_ratio:
                        color = "#FF00F7"
                    if (ask >= cluster[j - 1][1] * self.imbalance_ratio
                            and j >= 1):
                        color = "#00F2F2"
                self.p.setPen(pg.mkPen(color=color))

                colormap = [[0, "#262626"], [1, "#bfbdbd"]]
                if self.VA_show and value_area_low <= price <= value_area_high:
                    colormap = [[0, "#12415c"], [1, "#33b1ff"]]
                color = utility.heatmap(
                    value=vol,
                    start_value=min_vol,
                    finish_value=max_vol,
                    colormap=colormap,
                    to_hex=True,
                )
                if self.one_side_show:
                    if not bid:
                        color = "#ffea00"
                    if not ask:
                        color = "#ffa200"
                if self.POC_show and price == point_of_control:
                    color = "#ff3333"
                self.p.setBrush(pg.mkBrush(color=color))

                x = open_time
                width = self.interval * (vol / max_vol)
                if self.marker_show:
                    x += self.interval / 10
                    width *= 0.9

                self.p.drawRect(QtCore.QRectF(x, price, width, height))

    def delta_colored_volume(self):
        for i in range(len(self.footprint)):
            self.footprint[i].vol_limits()
            max_vol = self.footprint[i].max_vol
            min_vol = self.footprint[i].min_vol
            cluster = self.footprint[i].prices
            open_time = self.footprint[i].open_time
            tick_size = self.footprint[i].tick_size
            height = -utility.exact_mult(tick_size, self.grouping)

            if self.VA_show and self.POC_show:
                unpack = utility.distribution_elements(cluster)
                point_of_control, value_area_high, value_area_low = unpack

            for j in range(len(cluster)):
                price, bid, ask = cluster[j]
                vol = bid + ask

                color = "#000"
                if self.imbalance_show and j != len(cluster) - 1:
                    if bid >= cluster[j + 1][2] * self.imbalance_ratio:
                        color = "#FF00F7"
                    if (ask >= cluster[j - 1][1] * self.imbalance_ratio
                            and j >= 1):
                        color = "#00F2F2"
                if self.POC_show and price == point_of_control:
                    color = "#ffffff"
                self.p.setPen(pg.mkPen(color=color))
                
                start_color = "#005413"
                end_color = "#0dff0d"
                if bid < ask:
                    start_color = "#550E18"
                    end_color = "#ff0d0d"
                colormap = [[0, start_color], [1, end_color]]
                color = utility.heatmap(
                    value=vol,
                    start_value=min_vol,
                    finish_value=max_vol,
                    colormap=colormap,
                    to_hex=True,
                )
                if self.one_side_show:
                    if not bid:
                        color = "#ffea00"
                    if not ask:
                        color = "#ffa200"
                self.p.setBrush(pg.mkBrush(color=color))

                x = open_time
                width = self.interval * (vol / max_vol)
                if self.marker_show:
                    x += self.interval * 0.1
                    width *= 0.9

                self.p.drawRect(QtCore.QRectF(x, price, width, height))

            if self.VA_show:
                self.value_area(open_time, cluster, height)

    def volume_delta(self):
        for i in range(len(self.footprint)):
            max_vol, min_vol, max_delta, min_delta = 0, 0, 0, 0
            self.footprint[i].vol_limits()
            max_vol = self.footprint[i].max_vol
            min_vol = self.footprint[i].min_vol
            self.footprint[i].delta_calc()
            max_delta = self.footprint[i].max_delta
            min_delta = self.footprint[i].min_delta
            cluster = self.footprint[i].prices
            open_time = self.footprint[i].open_time
            tick_size = self.footprint[i].tick_size
            height = -utility.exact_mult(tick_size, self.grouping)

            unpack = utility.distribution_elements(cluster)
            point_of_control, value_area_high, value_area_low = unpack

            for j in range(len(cluster)):
                price, bid, ask = cluster[j]
                vol = bid + ask
                delta = abs(bid - ask)
                shift = self.interval * (0.55 if self.marker_show else 0.5)
                x = open_time + shift

                colormap = [[0, "#262626"], [1, "#bfbdbd"]]
                if self.VA_show and value_area_low <= price <= value_area_high:
                    colormap = [[0, "#12415c"], [1, "#33b1ff"]]
                color = utility.heatmap(
                    value=vol,
                    start_value=min_vol,
                    finish_value=max_vol,
                    colormap=colormap,
                    to_hex=True
                )
                if self.POC_show and price == point_of_control:
                    color = "#ff3333"
                self.p.setBrush(pg.mkBrush(color=color))
                self.p.setPen(pg.mkPen(color="#000"))

                width = (-self.interval *
                         (0.45 if self.marker_show else 0.5) *
                         (vol / max_vol))
                self.p.drawRect(QtCore.QRectF(x, price, width, height))

                if j < len(cluster) - 1 and self.imbalance_show:
                    if bid >= cluster[j + 1][2] * self.imbalance_ratio:
                        self.p.setPen(pg.mkPen(color="#FF00F7"))
                    if (j >= 1 and
                            ask >= cluster[j - 1][1] * self.imbalance_ratio):
                        self.p.setPen(pg.mkPen(color="#00F2F2"))

                start_color = "#005413"
                end_color = "#0dff0d"
                if bid < ask:
                    start_color = "#550E18"
                    end_color = "#ff0d0d"
                colormap = [[0, start_color], [1, end_color]]
                color = utility.heatmap(
                    value=delta,
                    start_value=min_delta,
                    finish_value=max_delta,
                    colormap=colormap,
                    to_hex=True,
                )
                if self.one_side_show:
                    if not bid:
                        color = "#ffea00"
                    if not ask:
                        color = "#ffa200"
                self.p.setBrush(pg.mkBrush(color=color))

                width = (self.interval *
                         (0.45 if self.marker_show else 0.5) *
                         (delta / max_delta))
                self.p.drawRect(QtCore.QRectF(x, price, width, height))

            if self.VA_show:
                self.value_area(open_time, cluster, height)

    def bid_ask(self):
        for i in range(len(self.footprint)):
            self.footprint[i].bid_ask_limits()
            min_bid_ask = self.footprint[i].min_bid_ask
            max_bid_ask = self.footprint[i].max_bid_ask
            cluster = self.footprint[i].prices
            open_time = self.footprint[i].open_time
            tick_size = self.footprint[i].tick_size
            height = -utility.exact_mult(tick_size, self.grouping)

            for j in range(len(cluster)):
                price, bid, ask = cluster[j]
                shift = self.interval * (0.55 if self.marker_show else 0.5)
                x = open_time + shift
                x += self.interval * 0.025
                width = self.interval * (0.45 if self.marker_show else 0.5)
                width -= self.interval * 0.05

                color = "#000"
                if (self.imbalance_show and j < len(cluster) - 1 and
                        bid >= cluster[j + 1][2] * self.imbalance_ratio):
                    color = "#00F2F2"
                self.p.setPen(pg.mkPen(color=color))

                colormap = [[0, "#94bf36"], [1, "#C5FF48"]]
                color = utility.heatmap(
                    value=bid,
                    start_value=min_bid_ask,
                    finish_value=max_bid_ask,
                    colormap=colormap,
                    to_hex=False
                )

                # gradient = QLinearGradient(x, 0, x - width, 0)
                # gradient.setColorAt(0, QColor("#71C9AF"))
                # gradient.setColorAt(1, QColor("#2954EB"))
                # pen = QPen(gradient, 1)
                # pen.setCosmetic(True)
                # self.p.setPen(pen)
                
                # gradient = QLinearGradient(x, 0, x - width, 0)
                # gradient.setColorAt(0, QColor("#41755E"))
                # gradient.setColorAt(1, QColor("#173389"))
                # self.p.setBrush(QBrush(gradient))

                if self.one_side_show and not ask:
                    color = "#ffea00"
                self.p.setBrush(pg.mkBrush(color=color))

                width2 = -width * (bid / max_bid_ask)
                self.p.drawRect(QtCore.QRectF(x, price, width2, height))

                color = "#000"
                if (self.imbalance_show and j >= 1 and
                        ask >= cluster[j - 1][1] * self.imbalance_ratio):
                    color = "#FF00F7"
                self.p.setPen(pg.mkPen(color=color))

                colormap = [[0, "#bf2c4c"], [1, "#FF3B64"]]
                color = utility.heatmap(
                    value=ask,
                    start_value=min_bid_ask,
                    finish_value=max_bid_ask,
                    colormap=colormap,
                    to_hex=False
                )

                # gradient = QLinearGradient(x, 0, x + width, 0)
                # gradient.setColorAt(0, QColor("#CF38BE"))
                # gradient.setColorAt(1, QColor("#B9973F"))
                # pen = QPen(gradient, 1)
                # pen.setCosmetic(True)
                # self.p.setPen(pen)

                # gradient = QLinearGradient(x, 0, x + width, 0)
                # gradient.setColorAt(0, QColor("#721874"))
                # gradient.setColorAt(1, QColor("#6A5926"))
                # self.p.setBrush(QBrush(gradient))

                if self.one_side_show and not bid:
                    color = "#ffa200"
                self.p.setBrush(pg.mkBrush(color=color))

                width2 = width * (ask / max_bid_ask) 
                self.p.drawRect(QtCore.QRectF(x, price, width2, height))

            if self.POC_show:
                x = open_time + (self.interval / 10 if self.marker_show else 0)
                x += self.interval * 0.025
                width = self.interval * (0.9 if self.marker_show else 1)
                width -= self.interval * 0.05
                unpack = utility.distribution_elements(cluster)
                y, *_ = unpack
                self.p.setBrush(pg.mkBrush(None))
                self.p.setPen(pg.mkPen("#fff"))
                self.p.drawRect(QtCore.QRectF(x, y, width, height))

            if self.VA_show:
                self.value_area(open_time, cluster, height)

    def delta(self):
        for i in range(len(self.footprint)):
            cluster = self.footprint[i].prices
            open_time = self.footprint[i].open_time
            tick_size = self.footprint[i].tick_size
            self.footprint[i].delta_calc()
            max_delta = self.footprint[i].max_delta
            min_delta = self.footprint[i].min_delta
            x = open_time + (self.interval / 10 if self.marker_show else 0)
            x2 = x + self.interval * (0.9 if self.marker_show else 1)
            height = -utility.exact_mult(tick_size, self.grouping)

            unpack = utility.distribution_elements(cluster)
            point_of_control, value_area_high, value_area_low = unpack

            for j in range(len(cluster)):
                price, bid, ask = cluster[j]
                delta = abs(bid - ask)
                width = self.interval * (delta / max_delta)
                if self.marker_show:
                    width *= 0.9

                color = "#000"
                if self.imbalance_show and j != len(cluster) - 1:
                    if bid >= cluster[j + 1][2] * self.imbalance_ratio:
                        color = "#FF00F7"
                    if (ask >= cluster[j - 1][1] * self.imbalance_ratio
                            and j >= 1):
                        color = "#00F2F2"
                self.p.setPen(pg.mkPen(color=color))

                start_color = "#005413"
                end_color = "#0dff0d"
                if bid < ask:
                    start_color = "#550E18"
                    end_color = "#ff0d0d"
                colormap = [[0, start_color], [1, end_color]]
                color = utility.heatmap(
                    value=delta,
                    start_value=min_delta,
                    finish_value=max_delta,
                    colormap=colormap,
                    to_hex=True
                )
                if self.one_side_show:
                    if not bid:
                        color = "#ffea00"
                    if not ask:
                        color = "#ffa200"
                self.p.setBrush(pg.mkBrush(color=color))

                self.p.drawRect(QtCore.QRectF(x, price, width, height))

            if self.POC_show:
                self.p.setPen(pg.mkPen(color="#ffffff", width=2))
                y = utility.exact_mult(tick_size, self.grouping) / 2
                y2 = point_of_control - y
                self.p.drawLine(QtCore.QPointF(x, y2), QtCore.QPointF(x2, y2))

            if self.VA_show:
                self.value_area(open_time, cluster, height)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class DeltaItem(QGraphicsItem):
    def __init__(self, *, pair, interval):
        super().__init__()
        self.setCacheMode(2)
        self.pair = pair
        con = sqlite3.connect("delta.db")
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {pair}")
        delta = cur.fetchall()
        self.open_price = [0]
        self.high_price = [delta[0][1]]
        self.low_price = [delta[0][2]]
        self.close_price = [delta[0][3]]
        self.interval = utility.interval_to_unix(interval, False)

        for i in range(len(delta)):
            delta[i] = [
                delta[i][0] / 1000,
                delta[i][1],
                delta[i][2],
                delta[i][3],
                delta[i][4]
            ]

        delta_time = delta[0][0] - delta[0][0] % self.interval
        self.start_time = [delta_time]

        for i in range(1, len(delta)):
            open_time = delta[i][0]
            high = delta[i][1]
            low = delta[i][2]
            close = delta[i][3]

            delta_time = open_time - open_time % self.interval

            if delta_time != self.start_time[-1]:
                self.start_time.append(delta_time)
                self.open_price.append(0)
                self.high_price.append(high)
                self.low_price.append(low)
                self.close_price.append(close)
                continue

            if high + self.close_price[-1] > self.high_price[-1]:
                self.high_price[-1] = high + self.close_price[-1]
            if low + self.close_price[-1] < self.low_price[-1]:
                self.low_price[-1] = low + self.close_price[-1]
            self.close_price[-1] += close

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.start_time[1] - self.start_time[0]) / 3

        for i in range(len(self.start_time)):
            color = "#C5FF48"
            if self.open_price[i] > self.close_price[i]:
                color = "#FF3B64"
            p.setBrush(pg.mkBrush(color=color))
            p.setPen(pg.mkPen(color=color))
            x = self.start_time[i]
            y = self.low_price[i]
            y2 = self.high_price[i]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y2))
            p.setPen(pg.mkPen(color="#000000"))
            x = self.start_time[i] - width
            y = self.close_price[i]
            height = self.open_price[i] - self.close_price[i]
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class CumulitiveDeltaItem(QGraphicsItem):
    def __init__(self, *, pair, interval):
        super().__init__()
        self.setCacheMode(2)
        self.pair = pair
        con = sqlite3.connect("delta.db")
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {pair}")
        delta = cur.fetchall()
        self.open_price = [0]
        self.high_price = [delta[0][1]]
        self.low_price = [delta[0][2]]
        self.close_price = [delta[0][3]]
        self.interval = utility.interval_to_unix(interval, False)

        for i in range(len(delta)):
            delta[i] = [
                delta[i][0] / 1000,
                delta[i][1],
                delta[i][2],
                delta[i][3],
                delta[i][4]
            ]

        delta_time = delta[0][0] - delta[0][0] % self.interval
        self.start_time = [delta_time]

        for i in range(1, len(delta)):
            open_time = delta[i][0]
            high = delta[i][1]
            low = delta[i][2]
            close = delta[i][3]

            delta_time = open_time - open_time % self.interval

            if delta_time != self.start_time[-1]:
                self.start_time.append(delta_time)
                self.open_price.append(0)
                self.high_price.append(high)
                self.low_price.append(low)
                self.close_price.append(close)
                continue

            if high + self.close_price[-1] > self.high_price[-1]:
                self.high_price[-1] = high + self.close_price[-1]
            if low + self.close_price[-1] < self.low_price[-1]:
                self.low_price[-1] = low + self.close_price[-1]
            self.close_price[-1] += close

        for i in range(1, len(self.start_time)):
            self.open_price[i] = self.close_price[i - 1]
            self.high_price[i] += self.open_price[i]
            self.low_price[i] += self.open_price[i]
            self.close_price[i] += self.open_price[i]

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.start_time[1] - self.start_time[0]) / 3
        for i in range(len(self.start_time)):
            color = "#C5FF48"
            if self.open_price[i] > self.close_price[i]:
                color = "#FF3B64"
            p.setBrush(pg.mkBrush(color=color))
            p.setPen(pg.mkPen(color=color))
            x = self.start_time[i]
            y = self.low_price[i]
            y2 = self.high_price[i]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y2))
            p.setPen(pg.mkPen(color="#000000"))
            x = self.start_time[i] - width
            y = self.close_price[i]
            height = self.open_price[i] - self.close_price[i]
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class HorizontalVolumeItem(QGraphicsItem):
    def __init__(self, *, pair, grouping, VA_show, POC_show):
        super().__init__()
        self.setCacheMode(2)
        self.pair = pair
        self.grouping = grouping
        self.VA_show = VA_show
        self.POC_show = POC_show

        con = sqlite3.connect("footprint.db")
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {pair}")
        volume = {}
        c = cur.fetchall()
        now = datetime.datetime.now()
        monday = now - datetime.timedelta(days=now.weekday())
        monday = datetime.datetime.combine(monday, datetime.time.min)
        monday = monday.timestamp() * 1000

        for i in range(len(c)):
            if c[i][0] < monday:
                continue
            self.height = -utility.exact_mult(grouping, c[i][4])
            break

        for i in range(len(c)):
            if c[i][0] < monday:
                continue
            price_level = utility.format_value(
                c[i][1], utility.exact_mult(grouping, c[i][4])
            )
            if price_level not in volume:
                volume[price_level] = [c[i][2], c[i][3]]
                continue
            volume[price_level][0] = utility.exact_add(
                volume[price_level][0], c[i][2]
            )
            volume[price_level][1] = utility.exact_add(
                volume[price_level][1], c[i][3]
            )

        volume = [[float(i), volume[i][0], volume[i][1]] for i in volume]
        volume.sort(key=lambda x: x[0])
        self.volume = volume

        self.max_volume = -np.inf
        for i in self.volume:
            if np.sum(i[1:]) > self.max_volume:
                self.max_volume = np.sum(i[1:])

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen("#000000"))
        sum_volume = []
        for i in range(len(self.volume)):
            sum_volume.append(self.volume[i][1] + self.volume[i][2])
        max_vol = np.amax(sum_volume)
        min_vol = np.amin(sum_volume)

        if self.VA_show or self.POC_show:
            unpack = utility.distribution_elements(self.volume)
            point_of_control, value_area_high, value_area_low = unpack

        for i in range(len(self.volume)):
            colormap = [[0, "#262626"], [1, "#bfbdbd"]]
            if (value_area_low <= self.volume[i][0] <= value_area_high and
                self.VA_show):
                colormap = [[0, "#1a587f"], [1, "#47b9ff"]]
            color = utility.heatmap(
                value=self.volume[i][1] + self.volume[i][2],
                start_value=min_vol,
                finish_value=max_vol,
                colormap=colormap,
                to_hex=True
            )
            gradient = QLinearGradient(min_vol, 0, max_vol, 0)
            gradient.setColorAt(0, QColor(colormap[0][1]))
            gradient.setColorAt(1, QColor(colormap[1][1]))
            p.setBrush(QBrush(gradient))
            if self.POC_show and self.volume[i][0] == point_of_control:
                color = "#ff3333"
            p.setBrush(pg.mkBrush(color=color))
            y = self.volume[i][0]
            width = self.volume[i][1] + self.volume[i][2]
            p.drawRect(QtCore.QRectF(0, y, width, self.height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
