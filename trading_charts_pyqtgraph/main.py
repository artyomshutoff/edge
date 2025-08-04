import numpy as np
import pyqtgraph as pg
from binance.spot import Spot
from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtGui

import charts
import utility

pg.setConfigOption("useOpenGL", True)
pg.setConfigOption("useCupy", True)
pg.setConfigOption("useNumba", True)
pg.setConfigOption("enableExperimental", True)

client = Spot()

pair = "BTCUSDT"
interval = "1h"
win_size = (1280, 720)

klines = np.array(
    client.klines(symbol=pair, interval=interval, limit=10000),
    dtype=np.float64
)

unpack = list(map(lambda x: x[0], np.split(np.transpose(klines), 12)))
time, open_price, high_price, low_price, close_price, volume, *_ = unpack
time = np.array([i / 1000 for i in time], dtype=np.uint32)
exchange_info = client.exchange_info(pair)
tick_size = float(exchange_info["symbols"][0]["filters"][0]["tickSize"])

app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget(
    title=f"{pair} {interval}",
    size=win_size
)

gradient = QtGui.QLinearGradient(0, 0, 0, win.height())
gradient.setColorAt(0, pg.mkColor("#242e49")) # start color
gradient.setColorAt(1, pg.mkColor("#141823")) # end color

win.setBackground(background=QtGui.QBrush(gradient))
win.show()

layout = pg.GraphicsLayout()
win.setCentralWidget(layout)
date_axis = utility.DateAxisItem(orientation="bottom")
p1 = pg.PlotItem(axisItems={"bottom": date_axis})
p1.setClipToView(clip=True)
p1.setDownsampling(ds=True, auto=True, mode="subsample")
p1.showGrid(x=True, y=True, alpha=0.5)
p1.showAxis(axis="right")
p1.hideAxis(axis="left")
for key in p1.axes:
    ax = p1.getAxis(key)
    ax.setZValue(-1)
layout.addItem(item=p1)

# item = charts.LowHigh(
#         start_time=time,
#         high_price=high_price,
#         low_price=low_price
# )

# item = charts.Candlestick(
#         start_time=time,
#         open_price=open_price,
#         high_price=high_price,
#         low_price=low_price,
#         close_price=close_price
# )

# item = charts.Bar(
#         start_time=time,
#         open_price=open_price,
#         high_price=high_price,
#         low_price=low_price,
#         close_price=close_price
# )

item = charts.LineBreak(
        start_time=time,
        close_price=close_price,
        check=3
)

# p1.addItem(item=charts.PointFigureItem(
#     start_time=time,
#     open_price=open_price,
#     high_price=high_price,
#     low_price=low_price,
#     close_price=close_price,
#     percent=False,
#     reversal_value=200,
#     value_type="HighLow",
#     atr=False,
#     atr_period=14,
#     )
# )

# p1.addItem(
#     item=charts.KagiItem(
#         start_time=time,
#         open_price=open_price,
#         high_price=high_price,
#         low_price=low_price,
#         close_price=close_price,
#         percent=True,
#         reversal_value=0.01,
#         value_type="HighLow",
#         atr=False,
#         atr_period=14
#     )
# )

# block = client.klines(symbol=pair, interval="30m", limit=10000)
# timespan = client.klines(symbol=pair, interval="1d", limit=10000)

# p1.addItem(item=charts.MarketProfileItem(
#         plot=p1,
#         block=block,
#         timespan=timespan,
#         tick_size=tick_size,
#         VA_show=True,
#         POC_show=True,
#         alphabet=False,
#         deployed=False,
#         heatmap_gradient=[
#             [0, "#ff0000"],
#             [0.25, "#ffff00"],
#             [0.5, "#00ff00"],
#             [0.75, "#00ffff"],
#             [1, "#0000ff"],
#         ],
#         heatmap_on=True,
#         open_close_show=True,
#         dynamic_VA=False,
#     )
# )

# renko = charts.RenkoItem(
#         start_time=time,
#         atr=False,
#         atr_period=14,
#         open_price=open_price,
#         high_price=high_price,
#         low_price=low_price,
#         close_price=close_price,
#         percent=False,
#         reversal_value=100,
#         value_type="Close",
#     )

p1.addItem(item=item)

crosshair = utility.CrosshairItem(
    main_plot=p1, 
    win=win, 
    interval=interval, 
    tick_size=tick_size
)
proxy = pg.SignalProxy(
    signal=p1.scene().sigMouseMoved,
    rateLimit=60,
    slot=crosshair.mouse_moved,
)
