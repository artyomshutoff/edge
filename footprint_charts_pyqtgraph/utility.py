import time
from datetime import datetime, timedelta
from decimal import Decimal
from time import mktime

import numpy as np
import pyqtgraph as pg
from pyqtgraph import AxisItem, QtCore

MS_SPACING = 1 / 1000
SECOND_SPACING = 1
MINUTE_SPACING = 60
HOUR_SPACING = 3600
DAY_SPACING = 24 * HOUR_SPACING
WEEK_SPACING = 7 * DAY_SPACING
MONTH_SPACING = 30 * DAY_SPACING
YEAR_SPACING = 365 * DAY_SPACING


def exact_diff(val, val2):
    val, val2 = str(val), str(val2)
    return float(Decimal(val) - Decimal(val2))


def exact_add(val, val2):
    val, val2 = str(val), str(val2)
    return float(Decimal(val) + Decimal(val2))


def exact_mult(val, val2):
    val, val2 = str(val), str(val2)
    return float(Decimal(val) * Decimal(val2))


def format_value(val, step_size):
    val, step_size = str(val), str(step_size)
    value = Decimal(val) - Decimal(val) % Decimal(step_size)
    return int(value) if not value % int(value) else float(value)


def interval_to_unix(interval, ms=True):
    intervals = {
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "8h": 28800,
        "12h": 43200,
        "1d": 86400,
        "3d": 259200,
        "1w": 604800,
        "1M": 2592000,
    }

    return intervals[interval] * (1000 if ms else 1)


def heatmap(**kwargs):
    value = kwargs["value"]
    start_value = kwargs["start_value"]
    finish_value = kwargs["finish_value"]
    colormap = kwargs["colormap"]
    to_hex = kwargs["to_hex"]
    if value < start_value:
        return colormap[0][1]
    elif value > finish_value:
        return colormap[-1][1]

    for i in range(len(colormap) - 1):
        ratio = (value - start_value) / (finish_value - start_value)
        if not (colormap[i][0] <= ratio <= colormap[i + 1][0]):
            continue
        h = colormap[i][1]
        rgb_1 = tuple(int(h.lstrip("#")[i: i + 2], 16) for i in (0, 2, 4))
        h_2 = colormap[i + 1][1]
        rgb_2 = tuple(int(h_2.lstrip("#")[i: i + 2], 16) for i in (0, 2, 4))
        numerator = ratio - colormap[i][0]
        denominator = colormap[i + 1][0] - colormap[i][0]
        change = numerator / denominator
        rgb = [0, 0, 0]

        for i in range(3):
            rgb[i] = rgb_1[i]
            diff = abs(rgb_1[i] - rgb_2[i]) * change
            if rgb_1[i] > rgb_2[i]:
                diff *= -1
            rgb[i] += diff

        rgb = list(map(int, rgb))

        return "#%02x%02x%02x" % tuple(rgb) if to_hex else tuple(rgb)


def distribution_elements(volume):
    volume = [(float(i[0]), exact_add(i[1], i[2])) for i in volume]
    volume.sort(key=lambda x: x[0])
    volume = np.array(volume)
    point_of_control = np.amax(volume[:, 1])
    point_of_control_index = 0
    total_volume = 0
    value_area = point_of_control

    for i in range(len(volume)):
        total_volume += volume[i][1]
        if point_of_control == volume[i][1]:
            point_of_control_index = i

    value_area_high = point_of_control_index
    value_area_low = point_of_control_index
    if point_of_control_index < len(volume) - 1:
        value_area_high = point_of_control_index + 1
    if point_of_control_index > 0:
        value_area_low = point_of_control_index - 1
    value_area += volume[value_area_high][1] + volume[value_area_low][1]

    while value_area / total_volume < 0.68:
        if value_area_high < len(volume) - 1:
            value_area_high += 1
            value_area += volume[value_area_high][1]
        if value_area_low > 0:
            value_area_low -= 1
            value_area += volume[value_area_low][1]

    point_of_control = volume[point_of_control_index][0]
    value_area_high = volume[value_area_high][0]
    value_area_low = volume[value_area_low][0]

    return point_of_control, value_area_high, value_area_low


class Crosshair:
    def __init__(self):
        self.__pen = pg.mkPen(
            color=pg.mkColor("#ffffff80"),
            style=QtCore.Qt.DotLine,
        )
        self.v_line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=self.__pen,
        )
        self.h_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=self.__pen,
        )


class CrosshairItem:
    fill_color = "#0B1925"
    text_color = pg.mkColor("#ffffff80")
    crosshair_list = []

    def __init__(self, *, main_plot, plots, win, interval, tick_size):
        self.main_plot = main_plot
        self.plots = plots
        self.win = win
        self.interval = interval
        self.tick_size = tick_size
        self.price_text = pg.TextItem(
            anchor=(1, 0.5),
            fill=self.fill_color,
            color=self.text_color,
        )

        self.time_text = pg.TextItem(
            anchor=(0.5, 1),
            fill=self.fill_color,
            color=self.text_color,
        )
        self.add()

    def add(self):
        self.main_plot.vb.scene().addItem(self.price_text)
        self.main_plot.vb.scene().addItem(self.time_text)

        self.crshr = Crosshair()
        self.main_plot.vb.addItem(
            self.crshr.v_line,
            ignoreBounds=True,
        )
        self.main_plot.vb.addItem(
            self.crshr.h_line,
            ignoreBounds=True,
        )

        for i in range(len(self.plots)):
            self.crosshair_list.append(Crosshair())

        for i in range(len(self.plots)):
            self.plots[i].addItem(
                self.crosshair_list[i].v_line,
                ignoreBounds=True
            )
            self.plots[i].addItem(
                self.crosshair_list[i].h_line,
                ignoreBounds=True
            )

    def mouse_moved(self, evt):
        pos = evt[0]
        if not self.main_plot.sceneBoundingRect().contains(pos):
            return
        mouse_point = self.main_plot.vb.mapSceneToView(pos)
        x_mouse = mouse_point.x()
        y_mouse = mouse_point.y()
        self.price_text.setText(str(format_value(y_mouse, self.tick_size)))
        self.price_text.setPos(self.win.width(), pos.y())
        span_sec = interval_to_unix(interval=self.interval, ms=False)
        x = x_mouse - x_mouse % span_sec
        if x_mouse >= x + span_sec / 2:
            x += span_sec
        time = datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
        self.time_text.setText(time)
        self.crshr.v_line.setPos(x)
        self.crshr.h_line.setPos(y_mouse)
        for i in self.crosshair_list:
            i.v_line.setPos(x)
            i.h_line.setPos(y_mouse)
        x = self.main_plot.vb.mapViewToScene(QtCore.QPointF(x, y_mouse)).x()
        y = self.win.height()
        self.time_text.setPos(x, y)


def makeMSStepper(stepSize):
    def stepper(val, n):
        val *= 1000
        f = stepSize * 1000
        return (val // (n * f) + 1) * (n * f) / 1000

    return stepper


def makeSStepper(stepSize):
    def stepper(val, n):
        return (val // (n * stepSize) + 1) * (n * stepSize)

    return stepper


def makeMStepper(stepSize):
    def stepper(val, n):
        d = datetime.utcfromtimestamp(val)
        base0m = d.month + n * stepSize - 1
        d = datetime(d.year + base0m // 12, base0m % 12 + 1, 1)
        return (d - datetime(1970, 1, 1)).total_seconds()

    return stepper


def makeYStepper(stepSize):
    def stepper(val, n):
        d = datetime.utcfromtimestamp(val)
        next_date = datetime(
            (d.year // (n * stepSize) + 1) * (n * stepSize), 1, 1
        )
        return (next_date - datetime(1970, 1, 1)).total_seconds()

    return stepper


class TickSpec:
    def __init__(self, spacing, stepper, format, autoSkip=None):
        self.spacing = spacing
        self.step = stepper
        self.format = format
        self.autoSkip = autoSkip

    def makeTicks(self, minVal, maxVal, minSpc):
        ticks = []
        n = self.skipFactor(minSpc)
        x = self.step(minVal, n)
        while x <= maxVal:
            ticks.append(x)
            x = self.step(x, n)
        return (np.array(ticks), n)

    def skipFactor(self, minSpc):
        if self.autoSkip is None or minSpc < self.spacing:
            return 1
        factors = np.array(self.autoSkip)
        while True:
            for f in factors:
                spc = self.spacing * f
                if spc > minSpc:
                    return f
            factors *= 10


class ZoomLevel:
    def __init__(self, tickSpecs):
        self.tickSpecs = tickSpecs
        self.utcOffset = 0

    def tickValues(self, minVal, maxVal, minSpc):
        allTicks = []
        valueSpecs = []
        utcMin = minVal - self.utcOffset
        utcMax = maxVal - self.utcOffset
        for spec in self.tickSpecs:
            ticks, skipFactor = spec.makeTicks(utcMin, utcMax, minSpc)
            ticks += self.utcOffset
            tick_list = [x for x in ticks.tolist() if x not in allTicks]
            allTicks.extend(tick_list)
            valueSpecs.append((spec.spacing, tick_list))
            if skipFactor > 1:
                break
        return valueSpecs


YEAR_MONTH_ZOOM_LEVEL = ZoomLevel(
    [
        TickSpec(YEAR_SPACING, makeYStepper(1), "%Y", autoSkip=[1, 5, 10, 25]),
        TickSpec(MONTH_SPACING, makeMStepper(1), "%b")
    ]
)
MONTH_DAY_ZOOM_LEVEL = ZoomLevel(
    [
        TickSpec(MONTH_SPACING, makeMStepper(1), "%b"),
        TickSpec(DAY_SPACING, makeSStepper(DAY_SPACING), "%d", autoSkip=[1, 5])
    ]
)
DAY_HOUR_ZOOM_LEVEL = ZoomLevel(
    [
        TickSpec(DAY_SPACING, makeSStepper(DAY_SPACING), "%a %d"),
        TickSpec(
            HOUR_SPACING, makeSStepper(HOUR_SPACING), "%H:%M", autoSkip=[1, 6]
        )
    ]
)
HOUR_MINUTE_ZOOM_LEVEL = ZoomLevel(
    [
        TickSpec(DAY_SPACING, makeSStepper(DAY_SPACING), "%a %d"),
        TickSpec(
            MINUTE_SPACING,
            makeSStepper(MINUTE_SPACING),
            "%H:%M",
            autoSkip=[1, 5, 15]
        )
    ]
)
HMS_ZOOM_LEVEL = ZoomLevel(
    [
        TickSpec(
            SECOND_SPACING,
            makeSStepper(SECOND_SPACING),
            "%H:%M:%S",
            autoSkip=[1, 5, 15, 30]
        )
    ]
)
MS_ZOOM_LEVEL = ZoomLevel(
    [
        TickSpec(MINUTE_SPACING, makeSStepper(MINUTE_SPACING), "%H:%M:%S"),
        TickSpec(
            MS_SPACING,
            makeMSStepper(MS_SPACING),
            "%S.%f",
            autoSkip=[1, 5, 10, 25]
        )
    ]
)


class VolumeAxisItem(AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [self.volume_format(v) for v in values]
    
    def volume_format(self, val):
        if val >= 1000000:
            val = str(val)[::-1]
            millions = val[6:][::-1]
            thousands = val[3:5][::-1]
            return f"{millions}.{thousands}m"
        if val >= 10000:
            thousands = str(int(val))[::-1][3:][::-1]
            hundreds = str(int(val))[::-1][2:3][::-1]
            return f"{thousands}.{hundreds}k"
        return str(int(val))

class DateAxisItem(AxisItem):
    def __init__(self, orientation, utcOffset=None, **kvargs):
        super(DateAxisItem, self).__init__(orientation, **kvargs)
        if utcOffset is None:
            self.utcOffset = time.timezone
        else:
            self.utcOffset = utcOffset
        self.zoomLevel = YEAR_MONTH_ZOOM_LEVEL
        self.maxTicksPerPt = 1 / 60.0
        self.zoomLevels = {
            self.maxTicksPerPt: MS_ZOOM_LEVEL,
            30 * self.maxTicksPerPt: HMS_ZOOM_LEVEL,
            15 * 60 * self.maxTicksPerPt: HOUR_MINUTE_ZOOM_LEVEL,
            6 * 3600 * self.maxTicksPerPt: DAY_HOUR_ZOOM_LEVEL,
            5 * 3600 * 24 * self.maxTicksPerPt: MONTH_DAY_ZOOM_LEVEL,
            3600 * 24 * 30 * self.maxTicksPerPt: YEAR_MONTH_ZOOM_LEVEL
        }

    def tickStrings(self, values, scale, spacing):
        tickSpecs = self.zoomLevel.tickSpecs
        tickSpec = next((s for s in tickSpecs if s.spacing == spacing), None)
        dates = [datetime.utcfromtimestamp(v - self.utcOffset) for v in values]
        formatStrings = []
        for x in dates:
            try:
                value = x.strftime(tickSpec.format)
                if "%f" in tickSpec.format:
                    value = value[:-3]
                formatStrings.append(value)
            except ValueError:  # Windows can't handle dates before 1970
                formatStrings.append("")
        return formatStrings

    def tickValues(self, minVal, maxVal, size):
        density = (maxVal - minVal) / size
        self.setZoomLevelForDensity(density)
        minSpacing = density / self.maxTicksPerPt
        values = self.zoomLevel.tickValues(minVal, maxVal, minSpc=minSpacing)
        return values

    def setZoomLevelForDensity(self, density):
        keys = sorted(self.zoomLevels.keys())
        key = next((k for k in keys if density < k), keys[-1])
        self.zoomLevel = self.zoomLevels[key]
        self.zoomLevel.utcOffset = self.utcOffset


class TimeAxisItem(pg.AxisItem):
    _pxLabelWidth = 80

    def __init__(self, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self._oldAxis = None

    def tickValues(self, minVal, maxVal, size):
        maxMajSteps = int(size / self._pxLabelWidth)

        dt1 = datetime.fromtimestamp(minVal)
        dt2 = datetime.fromtimestamp(maxVal)

        dx = maxVal - minVal
        majticks = []

        if dx > 63072001:  # 3600s*24*(365+366) = 2 years (count leap year)
            d = timedelta(days=366)
            for y in range(dt1.year + 1, dt2.year):
                dt = datetime(year=y, month=1, day=1)
                majticks.append(mktime(dt.timetuple()))

        elif dx > 5270400:  # 3600s*24*61 = 61 days
            d = timedelta(days=31)
            dt = (
                dt1.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                + d
            )
            while dt < dt2:
                # make sure that we are on day 1 (even if always sum 31 days)
                dt = dt.replace(day=1)
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 172800:  # 3600s24*2 = 2 days
            d = timedelta(days=1)
            dt = dt1.replace(hour=0, minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 7200:  # 3600s*2 = 2hours
            d = timedelta(hours=1)
            dt = dt1.replace(minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 1200:  # 60s*20 = 20 minutes
            d = timedelta(minutes=10)
            dt = (
                dt1.replace(
                    minute=(dt1.minute // 10) * 10, second=0, microsecond=0
                )
                + d
            )
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 120:  # 60s*2 = 2 minutes
            d = timedelta(minutes=1)
            dt = dt1.replace(second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 20:  # 20s
            d = timedelta(seconds=10)
            dt = dt1.replace(second=(dt1.second // 10) * 10, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 2:  # 2s
            d = timedelta(seconds=1)
            majticks = range(int(minVal), int(maxVal))

        else:  # <2s , use standard implementation from parent
            return pg.AxisItem.tickValues(self, minVal, maxVal, size)

        L = len(majticks)
        if L > maxMajSteps:
            majticks = majticks[:: int(np.ceil(float(L) / maxMajSteps))]

        return [(d.total_seconds(), majticks)]

    def tickStrings(self, values, scale, spacing):
        ret = []
        if not values:
            return []

        if spacing >= 31622400: # 366d
            fmt = "%Y"
        elif spacing >= 2678400: # 31d
            fmt = "%Y %b"
        elif spacing >= 86400: # = 1d
            fmt = "%b/%d"
        elif spacing >= 3600: # 1h
            fmt = "%b/%d-%Hh"
        elif spacing >= 60: # 1m
            fmt = "%H:%M"
        elif spacing >= 1: # 1s
            fmt = "%H:%M:%S"
        else:
            # less than 2s (show microseconds)
            # fmt = '%S.%f"'
            fmt = "[+%fms]"  # explicitly relative to last second

        for x in values:
            try:
                t = datetime.fromtimestamp(x)
                ret.append(t.strftime(fmt))
            except ValueError:  # Windows can't handle dates before 1970
                ret.append("")

        return ret

    def attachToPlotItem(self, plotItem):
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]["item"]
        self._oldAxis.hide()
        plotItem.axes[self.orientation]["item"] = self
        pos = plotItem.axes[self.orientation]["pos"]
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

    def detachFromPlotItem(self):
        raise NotImplementedError()
