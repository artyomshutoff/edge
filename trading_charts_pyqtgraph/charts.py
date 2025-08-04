from decimal import Decimal

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QGraphicsItem
from pyqtgraph import QtCore, QtGui

import utility


def sma(*, values, period):
    sma_values = []

    for i in range(period - 1, len(values)):
        gap = 0
        for j in range(i, i - period, -1):
            gap += values[j]
        sma_values.append(gap / period)

    return sma_values


class LowHigh(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.start_time = kwargs["start_time"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(None))
        p.setBrush(pg.mkBrush(color="#cccccc"))

        for i in range(len(self.start_time)):
            width = (self.start_time[1] - self.start_time[0]) / 3
            x = self.start_time[i] - width
            y = self.high_price[i]
            height = self.low_price[i] - self.high_price[i]
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())



class Candlestick(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)

        for i in range(len(self.time)):
            width = (self.time[1] - self.time[0]) / 3
            color = "#51977f"
            if self.open_price[i] > self.close_price[i]:
                color = "#de7095"

            p.setBrush(pg.mkBrush(color=color))
            p.setPen(pg.mkPen(color=color))

            x = self.time[i]
            y = self.low_price[i]
            y1 = self.high_price[i]

            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y1))
            p.setPen(pg.mkPen(None))
            x -= width
            y = self.close_price[i]
            height = self.open_price[i] - self.close_price[i]
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class Bar(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.time[1] - self.time[0]) / 3

        for i in range(len(self.time)):
            color = "#51977f"
            if self.open_price[i] > self.close_price[i]:
                color = "#de7095"
            p.setBrush(pg.mkBrush(None))
            p.setPen(pg.mkPen(color=color, width=2))

            x = self.time[i]
            y = self.low_price[i]
            y1 = self.high_price[i]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y1))

            y = self.close_price[i]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x + width, y))

            y = self.open_price[i]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x - width, y))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class Bionic(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.time[1] - self.time[0]) / 3

        for i in range(len(self.time)):
            p.setPen(pg.mkPen(None))
            p.setBrush(pg.mkBrush(color="#0CF50D"))

            x = self.time[i] - width
            y = self.close_price[i]
            height = -(self.close_price[i] - self.low_price[i])
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

            y = self.high_price[i]
            p.setBrush(pg.mkBrush(color="#F70606"))
            height = -(self.high_price[i] - self.close_price[i])
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

            p.setPen(pg.mkPen(color="#000"))
            p.setBrush(pg.mkBrush(None))
            height = self.high_price[i] - self.low_price[i]
            p.drawRect(QtCore.QRectF(x, y, width * 2, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class HeikinAshi(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        values = [kwargs["open_price"][0], kwargs["close_price"][0]]
        self.open_price = [np.mean(values)]
        self.high_price = [kwargs["high_price"]]
        self.low_price = [kwargs["low_price"]]
        values = [kwargs["open_price"][0],
                  kwargs["high_price"][0],
                  kwargs["low_price"][0],
                  kwargs["close_price"][0]]
        self.close_price = [np.mean(values)]

        for i in range(1, len(self.time)):
            values = [self.open_price[-1], self.close_price[-1]]
            self.open_price.append(np.mean(values))
            values = [kwargs["high_price"][i],
                      self.open_price[-1],
                      self.close_price[-1]]
            self.high_price.append(np.amax(values))
            values = [kwargs["low_price"][i],
                      self.open_price[-1],
                      self.close_price[-1]]
            self.low_price.append(np.amin(values))
            values = [kwargs["open_price"][i],
                      kwargs["high_price"][i],
                      kwargs["low_price"][i],
                      kwargs["close_price"][i]]
            self.close_price.append(np.mean(values))

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        width = (self.time[1] - self.time[0]) / 3

        for i in range(len(self.time)):
            color = "#0CF50D"
            if self.open_price[i] > self.close_price[i]:
                color = "#F70606"
            p.setBrush(pg.mkBrush(color=color))
            p.setPen(pg.mkPen(color=color))

            point = QtCore.QPointF(self.time[i], self.low_price[i])
            point2 = QtCore.QPointF(self.time[i], self.high_price[i])
            p.drawLine(point, point2)
            p.setPen(pg.mkPen(color="#000"))

            x = self.time[i] - width
            y = self.close_price[i]
            width *= 2
            height = self.open_price[i] - self.close_price[i]
            p.drawRect(QtCore.QRectF(x, y, width, height))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class Kagi(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        self.atr = kwargs["atr"]
        self.atr_period = kwargs["atr_period"]
        if self.atr:
            self.time = self.t[self.atr_period + 1:]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.percent = kwargs["percent"]
        self.reversal_value = kwargs["reversal_value"]
        self.value_type = kwargs["value_type"]
        self.timespan = self.time[1] - self.time[0]
        self.kagi = np.zeros(len(self.time))
        self.generate_values()

    def atr_calculation(self):
        atr_values = []
        for i in range(1, len(self.high_price)):
            first = self.high_price[i] - self.low_price[i]
            second = abs(self.high_price[i] - self.close_price[i - 1])
            third = abs(self.low_price[i] - self.close_price[i - 1])
            element = np.amax([first, second, third])
            atr_values.append(element)
        return sma(values=atr_values, period=self.atr_period)

    def generate_values(self):
        if self.atr:
            atr_filter = self.atr_calculation()

        high_values = self.high_price
        low_values = self.low_price

        if self.value_type != "HighLow":
            price_values = np.zeros(len(self.time))
            high_values = price_values
            low_values = price_values

        for i in range(len(self.time)):
            if self.value_type == "OHLC4":
                price_values[i] = np.mean(
                    [self.open_price[i],
                     self.high_price[i],
                     self.low_price[i],
                     self.close_price[i]]
                )
            elif self.value_type == "HLC3":
                price_values[i] = np.mean(
                    [self.high_price[i],
                     self.low_price[i],
                     self.close_price[i]]
                )
            elif self.value_type == "Open":
                price_values = self.open_price[i]
            elif self.value_type == "High":
                price_values[i] = self.high_price[i]
            elif self.value_type == "Low":
                price_values[i] = self.low_price[i]
            elif self.value_type == "Close":
                price_values[i] = self.close_price[i]
        
        trend = 0
        last_high = 0
        last_low = 0

        for i in range(len(self.time)):
            price_change = self.reversal_value
            if trend == 0:
                if self.percent:
                    price_change *= low_values[0]
                if self.atr:
                    price_change = atr_filter[0]

                if high_values[i] >= low_values[0] + price_change:
                    trend = 1
                    last_high = i
                    self.kagi[0] = -1
                    continue

                if self.percent:
                    price_change *= high_values[0]
                if self.atr:
                    price_change = atr_filter[0]

                if low_values[i] <= high_values[0] - price_change:
                    trend = -1
                    last_low = i
                    self.kagi[0] = 1

            if trend == 1:
                if self.percent:
                    price_change *= high_values[last_high]
                if self.atr:
                    price_change = atr_filter[last_high]
                
                high_pivot = high_values[last_high] - price_change
                term = low_values[i] <= high_pivot
                if term and high_values[i] < high_values[last_high]:
                    trend = -1
                    self.kagi[last_high] = 1
                    last_low = i
                if high_values[i] > high_values[last_high]:
                    last_high = i

            if trend == -1:
                if self.percent:
                    price_change *= low_values[last_low]
                if self.atr:
                    price_change = atr_filter[last_low]
                
                low_pivot = low_values[last_low] + price_change
                term = high_values[i] >= low_pivot
                if term and low_values[i] > low_values[last_low]:
                    trend = 1
                    self.kagi[last_low] = -1
                    last_high = i
                if low_values[i] < low_values[last_low]:
                    last_low = i

        last_trend = 0
        last_trend_index = 0

        for i in range(len(self.kagi) - 1, -1, -1):
            if self.kagi[i] != 0:
                last_trend = self.kagi[i]
                last_trend_index = i
                break

        determinant = 0
        high_determinant = high_values[last_trend_index]
        low_determinant = low_values[last_trend_index]

        for i in range(last_trend_index + 1, len(self.kagi)):
            if last_trend == 1 and low_values[i] < low_determinant:
                low_determinant = low_values[i]
                determinant = i
            if last_trend == -1 and high_values[i] > high_determinant:
                high_determinant = high_values[i]
                determinant = i

        self.kagi[determinant] = -1 if last_trend == 1 else 1
        self.out = []

        for i in range(len(self.time)):
            if self.kagi[i] not in (1, -1):
                continue
            self.out.append([self.time[i], 0])
            self.out[-1][1] = low_values[i]
            if self.kagi[i] == 1:
                self.out[-1][1] = high_values[i]

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setBrush(pg.mkBrush(None))

        for i in range(1, len(self.out)):
            self.out[i][0] = self.out[0][0] + self.timespan * i

        for i in range(1, len(self.out)):
            term = self.out[i][1] > self.out[i - 1][1]
            color = "#0CF50D" if term else "#F70606"
            p.setPen(pg.mkPen(color=color, width=4))

            x = self.out[i][0]
            y = self.out[i][1]
            y1 = self.out[i-1][1]
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x, y1))

            color = "#F70606" if term else "#0CF50D"
            p.setPen(pg.mkPen(color=color, width=4))
            x1 = self.out[i-1][0]
            p.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x, y1))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class Renko(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        self.atr = kwargs["atr"]
        self.atr_period = kwargs["atr_period"]
        if self.atr:
            self.time = self.time[self.atr_period + 1:]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.percent = kwargs["percent"]
        self.reversal_value = kwargs["reversal_value"]
        self.value_type = kwargs["value_type"]
        self.timespan = self.time[1] - self.time[0]
        self.renko = np.zeros(len(self.time))
        self.generate_values()

    def atr_calculation(self):
        atr_values = []
        for i in range(1, len(self.high_price)):
            first = self.high_price[i] - self.low_price[i]
            second = abs(self.high_price[i] - self.close_price[i - 1])
            third = abs(self.low_price[i] - self.close_price[i - 1])
            element = np.amax([first, second, third])
            atr_values.append(element)
        return sma(values=atr_values, period=self.atr_period)

    def generate_values(self):
        if self.atr:
            atr_filter = self.atr_calculation()

        high_values = self.high_price
        low_values = self.low_price

        if self.value_type != "HighLow":
            price_values = np.zeros(len(self.time))
            high_values = price_values
            low_values = price_values
        
        for i in range(len(self.time)):
            if self.value_type == "OHLC4":
                price_values[i] = np.mean(
                    [self.open_price[i],
                     self.high_price[i],
                     self.low_price[i],
                     self.close_price[i]]
                )
            elif self.value_type == "HLC3":
                price_values[i] = np.mean(
                    [self.high_price[i],
                     self.low_price[i],
                     self.close_price[i]]
                )
            elif self.value_type == "Open":
                price_values = self.open_price[i]
            elif self.value_type == "High":
                price_values[i] = self.high_price[i]
            elif self.value_type == "Low":
                price_values[i] = self.low_price[i]
            elif self.value_type == "Close":
                price_values[i] = self.close_price[i]

        trend = 0
        last_high = 0
        last_low = 0

        for i in range(len(self.time)):
            price_change = self.reversal_value
            if trend == 0:
                if self.percent:
                    price_change *= low_values[0]
                if self.atr:
                    price_change = atr_filter[0]

                if high_values[i] >= low_values[0] + price_change:
                    trend = 1
                    last_high = i
                    self.renko[0] = -1

                if self.percent:
                    price_change *= high_values[0]
                if self.atr:
                    price_change = atr_filter[0]

                if low_values[i] <= high_values[0] - price_change:
                    trend = -1
                    last_low = i
                    self.renko[0] = 1

            if trend == 1:
                if self.percent:
                    price_change *= high_values[last_high]
                if self.atr:
                    price_change = atr_filter[last_high]

                high_pivot = high_values[last_high] - price_change
                term = low_values[i] <= high_pivot
                if term and high_values[i] < high_values[last_high]:
                    trend = -1
                    self.renko[last_high] = 1
                    last_low = i
                if high_values[i] > high_values[last_high]:
                    last_high = i

            if trend == -1:
                if self.percent:
                    price_change *= low_values[last_low]
                if self.atr:
                    price_change = atr_filter[last_low]

                low_pivot = low_values[last_low] + price_change
                term = high_values[i] >= low_pivot
                if term and low_values[i] > low_values[last_low]:
                    trend = 1
                    self.renko[last_low] = -1
                    last_high = i
                if low_values[i] < low_values[last_low]:
                    last_low = i

        last_trend = 0
        last_trend_index = 0

        for i in range(len(self.renko) - 1, -1, -1):
            if self.renko[i] != 0:
                last_trend = self.renko[i]
                last_trend_index = i
                break

        determinant = 0
        high_determinant = high_values[last_trend_index]
        low_determinant = low_values[last_trend_index]

        for i in range(last_trend_index + 1, len(self.renko)):
            if last_trend == 1 and low_values[i] < low_determinant:
                low_determinant = low_values[i]
                determinant = i

            if last_trend == -1 and high_values[i] > high_determinant:
                high_determinant = high_values[i]
                determinant = i

        self.renko[determinant] = -1 if last_trend == 1 else 1
        self.out = []

        for i in range(len(self.time)):
            if self.renko[i] not in (1, -1):
                continue
            self.out.append([self.time[i], 0])
            self.out[-1][1] = low_values[i]
            if self.renko[i] == 1:
                self.out[-1][1] = high_values[i]

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(color="#000000"))
        j = 0

        for i in range(1, len(self.out)):
            if self.out[i][1] > self.out[i - 1][1]:
                p.setBrush(pg.mkBrush(color="#0CF50D"))
                current_high = utility.format_value(
                    self.out[i][1],
                    self.reversal_value
                )
                current_low = utility.format_value(
                    self.out[i - 1][1],
                    self.reversal_value
                )
                price = current_low
                while price < current_high:
                    x = self.out[1][0] + self.timespan * j
                    y = price + self.reversal_value
                    width = self.timespan
                    height = self.reversal_value
                    p.drawRect(QtCore.QRectF(x, y, width, height))
                    price += self.reversal_value
                    j += 1

            if self.out[i][1] < self.out[i - 1][1]:
                p.setBrush(pg.mkBrush(color="#F70606"))
                current_high = utility.format_value(
                    self.out[i - 1][1],
                    self.reversal_value
                )
                current_low = utility.format_value(
                    self.out[i][1],
                    self.reversal_value
                )
                price = current_high
                while price > current_low:
                    x = self.out[1][0] + self.timespan * j
                    y = price + self.reversal_value
                    width = self.timespan
                    height = self.reversal_value
                    p.drawRect(QtCore.QRectF(x, y, width, height))
                    price -= self.reversal_value
                    j += 1

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class PointFigure(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.time = kwargs["start_time"]
        self.atr = kwargs["atr"]
        self.atr_period = kwargs["atr_period"]
        if self.atr:
            self.time = self.start_time[self.atr_period + 1:]
        self.open_price = kwargs["open_price"]
        self.high_price = kwargs["high_price"]
        self.low_price = kwargs["low_price"]
        self.close_price = kwargs["close_price"]
        self.percent = kwargs["percent"]
        self.reversal_value = kwargs["reversal_value"]
        self.value_type = kwargs["value_type"]
        self.timespan = self.time[1] - self.time[0]
        self.point_and_figure = np.zeros(len(self.time))
        self.generate_values()

    def atr_calculation(self):
        atr_values = []
        for i in range(1, len(self.high_price)):
            first = self.high_price[i] - self.low_price[i]
            second = abs(self.high_price[i] - self.close_price[i - 1])
            third = abs(self.low_price[i] - self.close_price[i - 1])
            element = np.amax([first, second, third])
            atr_values.append(element)
        return sma(values=atr_values, period=self.atr_period)
    
    def generate_values(self):
        if self.atr:
            atr_filter = self.atr_calculation()

        high_values = self.high_price
        low_values = self.low_price

        if self.value_type != "HighLow":
            price_values = np.zeros(len(self.start_time))
            high_values = price_values
            low_values = price_values

        for i in range(len(self.time)):
            if self.value_type == "OHLC4":
                price_values[i] = np.mean(
                    [self.open_price[i],
                     self.high_price[i],
                     self.low_price[i],
                     self.close_price[i]]
                )
            elif self.value_type == "HLC3":
                price_values[i] = np.mean(
                    [self.high_price[i],
                     self.low_price[i],
                     self.close_price[i]]
                )
            elif self.value_type == "Open":
                price_values = self.open_price[i]
            elif self.value_type == "High":
                price_values[i] = self.high_price[i]
            elif self.value_type == "Low":
                price_values[i] = self.low_price[i]
            elif self.value_type == "Close":
                price_values[i] = self.close_price[i]

        trend = 0
        last_high = 0
        last_low = 0

        for i in range(len(self.time)):
            price_change = self.reversal_value
            if trend == 0:
                if self.percent:
                    price_change *= low_values[0]
                if self.atr:
                    price_change = atr_filter[0]

                if high_values[i] >= low_values[0] + price_change:
                    trend = 1
                    last_high = i
                    self.point_and_figure[0] = -1

                if self.percent:
                    price_change *= high_values[0]
                if self.atr:
                    price_change = atr_filter[0]

                if low_values[i] <= high_values[0] - price_change:
                    trend = -1
                    last_low = i
                    self.point_and_figure[0] = 1

            if trend == 1:
                if self.percent:
                    price_change *= high_values[last_high]
                if self.atr:
                    price_change = atr_filter[last_high]

                high_pivot = high_values[last_high] - price_change
                term = low_values[i] <= high_pivot
                if term and high_values[i] < high_values[last_high]:
                    trend = -1
                    self.point_and_figure[last_high] = 1
                    last_low = i
                if high_values[i] > high_values[last_high]:
                    last_high = i

            if trend == -1:
                if self.percent:
                    price_change *= low_values[last_low]
                if self.atr:
                    price_change = atr_filter[last_low]

                low_pivot = low_values[last_low] + price_change
                term = high_values[i] >= low_pivot
                if term and low_values[i] > low_values[last_low]:
                    trend = 1
                    self.point_and_figure[last_low] = -1
                    last_high = i
                if low_values[i] < low_values[last_low]:
                    last_low = i

        last_trend = 0
        last_trend_index = 0

        for i in range(len(self.point_and_figure) - 1, -1, -1):
            if self.point_and_figure[i] != 0:
                last_trend = self.point_and_figure[i]
                last_trend_index = i
                break

        determinant = 0
        high_determinant = high_values[last_trend_index]
        low_determinant = low_values[last_trend_index]

        for i in range(last_trend_index + 1, len(self.point_and_figure)):
            if last_trend == 1 and low_values[i] < low_determinant:
                low_determinant = low_values[i]
                determinant = i

            if last_trend == -1 and high_values[i] > high_determinant:
                high_determinant = high_values[i]
                determinant = i

        self.point_and_figure[determinant] = -1 if last_trend == 1 else 1

        self.out = []

        for i in range(len(self.time)):
            if self.point_and_figure[i] not in (1, -1):
                continue
            self.out.append([self.time[i], 0])
            self.out[-1][1] = low_values[i]
            if self.point_and_figure[i] == 1:
                self.out[-1][1] = high_values[i]

        self.generate_picture()


    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setBrush(pg.mkBrush(None))
        j = 0

        for i in range(1, len(self.out)):

            if self.out[i][1] > self.out[i - 1][1]:
                p.setPen(pg.mkPen(color="#0CF50D", width=1))
                current_high = utility.format_value(
                    self.out[i][1], 
                    self.reversal_value,
                )
                current_low = utility.format_value(
                    self.out[i - 1][1], 
                    self.reversal_value,
                )
                price = current_low

                while price < current_high:
                    x = self.out[1][0] + \
                        self.timespan * j + \
                        self.timespan * 0.1
                    y = price + self.reversal_value * 0.9
                    x2 = self.out[1][0] + \
                         self.timespan * j + \
                         self.timespan * 0.9
                    y2 = price + self.reversal_value * 0.1
                    p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x2, y2))
                    p.drawLine(QtCore.QPointF(x, y2), QtCore.QPointF(x2, y))
                    price += self.reversal_value

                j += 1

            if self.out[i][1] < self.out[i - 1][1]:
                p.setPen(pg.mkPen("#F70606", width=1))
                current_high = utility.format_value(
                    self.out[i - 1][1], 
                    self.reversal_value,
                )
                current_low = utility.format_value(
                    self.out[i][1], 
                    self.reversal_value,
                )
                price = current_high

                while price > current_low:
                    x = self.out[1][0] + self.timespan * (j + 0.1)
                    y = price + self.reversal_value * 0.9
                    width = self.timespan * 0.8
                    height = -self.reversal_value * 0.8
                    p.drawEllipse(QtCore.QRectF(x, y, width, height))
                    price -= self.reversal_value

                j += 1

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class LineBreak(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.start_time = kwargs["start_time"]
        self.close_price = kwargs["close_price"]
        self.check = kwargs["check"]
        self.timespan = self.start_time[1] - self.start_time[0]
        self.start_time = self.start_time[0]
        self.linebreak = [[self.close_price[0], self.close_price[1]]]
        self.generate_values()

    def generate_values(self):
        for i in range(2, len(self.close_price)):
            if len(self.linebreak) < self.check:
                term = self.linebreak[-1][1] - self.linebreak[-1][0] > 0
                term2 = self.linebreak[-1][1] < self.close_price[i]
                term3 = self.linebreak[-1][0] > self.close_price[i]
                coef = 1 if term == term2 else 0 if term == term3 else -1
                if coef < 0:
                    continue
                value = [self.linebreak[-1][coef], self.close_price[i]]
                self.linebreak.append(value)
                continue

            strength = 0
            for j in range(-1, -self.check, -1):
                term = self.linebreak[j][1] - self.linebreak[j][0] > 0
                term2 = self.linebreak[j-1][1] - self.linebreak[j-1][0] < 0
                if term == term2:
                    break
                if j - 1 == -self.check:
                    strength = 1

            term = self.linebreak[-1][1] - self.linebreak[-1][0] > 0
            term2 = self.linebreak[-1][1] < self.close_price[i]
            index = -self.check if strength else -1
            term3 = self.linebreak[index][0] > self.close_price[i]
            coef = 1 if term == term2 else 0 if term == term3 else -1
            if coef < 0:
                continue
            value = [self.linebreak[-1][coef], self.close_price[i]]
            self.linebreak.append(value)

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(None))
        for i in range(len(self.linebreak)):
            color = "#51977f"
            if self.linebreak[i][1] - self.linebreak[i][0] > 0:
                color = "#de7095"
            p.setBrush(pg.mkBrush(color=color))
            x = self.start_time + self.timespan * i
            y = self.linebreak[i][0]
            width = self.timespan
            height = self.linebreak[i][1] - self.linebreak[i][0]
            p.drawRect(QtCore.QRectF(x, y, width, height))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


def VAMA(dates, highs, lows, tick_size, period):
    VA = {}
    PVV = []

    for i in range(period - 1, len(dates)):
        for n in range(i, i - period, -1):
            current_high = utility.format_value(highs[n], tick_size)
            current_low = utility.format_value(lows[n], tick_size)
            price = current_high

            while price >= current_low:
                if str(price) in VA:
                    VA[str(price)] += 1
                else:
                    VA[str(price)] = 1
                price = float(Decimal(str(price)) - Decimal(str(tick_size)))

        VA = [[float(k), VA[k]] for k in VA]
        PVV.append([utility.distribution_elements(VA), dates[i]])
        VA = {}

    return PVV
