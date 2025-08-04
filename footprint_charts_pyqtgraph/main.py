import ctypes
import sqlite3

import numpy as np
import pyqtgraph as pg
from binance.spot import Spot
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

import charts
import utility
import files

pg.setConfigOption("useOpenGL", True)
pg.setConfigOption("useCupy", True)
pg.setConfigOption("useNumba", True)
pg.setConfigOption("enableExperimental", True)

client = Spot()

pair = "BTCUSDT"
interval = "1h"
grouping = 100
win_size = (1280, 720)
imbalance_ratio = 5
footprint_type = "bid_ask"
display_type = "gradient"

files.get()

con = sqlite3.connect("footprint.db")
cur = con.cursor()
cur.execute(f"SELECT * FROM {pair} LIMIT 1")
values = cur.fetchall()
start_time = values[0][0] - values[0][0] % utility.interval_to_unix(interval)  

klines = np.array(
    client.klines(symbol=pair, interval=interval, startTime=start_time),
    dtype=np.float64
)

unpack = list(map(lambda x: x[0], np.split(np.transpose(klines), 12)))
time, open_price, high_price, low_price, close_price, volume, *_ = unpack
time = np.array([i // 1000 for i in time], dtype=np.uint32)
pair_info = client.exchange_info(pair)
tick_size = float(pair_info["symbols"][0]["filters"][0]["tickSize"])

a2 = utility.VolumeAxisItem(orientation="left")
p2 = pg.ViewBox()
p2.setOpacity(0.5)

a21 = pg.AxisItem(orientation="top")
p21 = pg.ViewBox(invertX=True)

app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(
    title=f"Footprint Chart: {pair} {interval}",
    size=win_size
)
bg_color = "#000" # "#0B1925"
win.setBackground(background=bg_color)

layout = pg.GraphicsLayout()
win.setCentralWidget(item=layout)
layout.addItem(item=a2, row=1, col=0, rowspan=1, colspan=1)
layout.addItem(item=a21, row=0, col=1, rowspan=1, colspan=1)
date_axis = utility.DateAxisItem(orientation="bottom")
p1 = pg.PlotItem(axisItems={"bottom": date_axis})
p1.setClipToView(clip=True)
p1.setDownsampling(ds=True, auto=True, mode="subsample")

ax0 = p1.getAxis("bottom")
ax0.setStyle(showValues=False)

layout.addItem(p1, row=1, col=1, rowspan=1, colspan=1)

layout.scene().addItem(p2)
a2.linkToView(p2)
p2.setXLink(p1.vb)

layout.scene().addItem(p21)
a21.linkToView(p21)
p21.setYLink(p1.vb)

p1.showAxis(axis="right")
p1.hideAxis(axis="left")
p1.showGrid(x=True, y=True, alpha=0.5)

for key in p1.axes:
    ax = p1.getAxis(key)
    ax.setZValue(-1)

date_axis2 = utility.DateAxisItem(orientation="bottom")
p3 = pg.PlotItem(axisItems={"bottom": date_axis2})
p3.setClipToView(clip=True)
p3.setDownsampling(ds=True, auto=True, mode="subsample")

p3.vb.setXLink(p1.vb)
p3.showAxis(axis="right")
p3.hideAxis(axis="left")
ax1 = p3.getAxis(name="bottom")
ax1.setStyle(showValues=False)

layout.addItem(item=p3, row=2, col=1, rowspan=1, colspan=1)

date_axis3 = utility.DateAxisItem(orientation="bottom")
p4 = pg.PlotItem(axisItems={"bottom": date_axis3})
p4.setClipToView(clip=True)
p4.setDownsampling(ds=True, auto=True, mode="subsample")

p4.vb.setXLink(view=p1.vb)
p4.showAxis(axis="right")
p4.hideAxis(axis="left")

p3.showGrid(x=True, y=True, alpha=0.5)
for key in p3.axes:
    ax = p3.getAxis(key)
    ax.setZValue(-1)
layout.layout.setSpacing(0)
layout.setContentsMargins(0, 0, 0, 0)

layout.addItem(item=p4, row=3, col=1, rowspan=1, colspan=1)
p4.showGrid(x=True, y=True, alpha=0.5)
for key in p4.axes:
    ax = p4.getAxis(key)
    ax.setZValue(-1)

layout.layout.setRowStretchFactor(1, 6)


def update_views():
    p2.setGeometry(p1.vb.sceneBoundingRect())
    p21.setGeometry(p1.vb.sceneBoundingRect())


footprint_item = charts.FootprintItem(
    start_time=time,
    open_price=open_price,
    high_price=high_price,
    low_price=low_price,
    close_price=close_price,
    pair=pair,
    interval=interval,
    marker_show=True,
    candle_show=False,
    VA_show=True,
    POC_show=True,
    one_side_show=True,
    imbalance_show=True,
    imbalance_ratio=imbalance_ratio,
    footprint_type=footprint_type,
    grouping=grouping,
    display_type=display_type
)

p1.addItem(item=footprint_item)

volume_item = charts.VolumeItem(
    start_time=time,
    volume=volume,
    close_price=close_price,
    open_price=open_price
)

p2.addItem(item=volume_item)

max_volume = np.amax(volume) * 10
p2.setLimits(
    yMin=0,
    yMax=max_volume,
    minYRange=0,
    maxYRange=max_volume
)
p2.setYRange(min=0, max=max_volume)

horizontal_volume_item = charts.HorizontalVolumeItem(
    pair=pair,
    grouping=grouping,
    VA_show=True,
    POC_show=True
)

p21.addItem(item=horizontal_volume_item)

max_horizontal_volume = horizontal_volume_item.max_volume * 10
p21.setLimits(
    xMin=0,
    xMax=max_horizontal_volume,
    minXRange=0,
    maxXRange=max_horizontal_volume
)
p21.setXRange(min=0, max=max_horizontal_volume)

p3.addItem(item=charts.DeltaItem(pair=pair, interval=interval))
p4.addItem(item=charts.CumulitiveDeltaItem(pair=pair, interval=interval))

p1.vb.sigResized.connect(update_views)
update_views()

crosshair = utility.CrosshairItem(
    main_plot=p1,
    plots=[p3, p4],
    win=win,
    interval=interval,
    tick_size=tick_size * grouping
)

proxy = pg.SignalProxy(
    signal=p1.scene().sigMouseMoved,
    rateLimit=100,
    slot=crosshair.mouse_moved
)

win.show()
