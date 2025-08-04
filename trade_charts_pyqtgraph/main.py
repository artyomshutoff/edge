import ctypes
import sqlite3

import numpy as np
import pyqtgraph as pg
from binance.spot import Spot
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

import utility

pg.setConfigOption("useOpenGL", True)
pg.setConfigOption("useCupy", True)
pg.setConfigOption("useNumba", True)
pg.setConfigOption("enableExperimental", True)

client = Spot()

pair = "BTCUSDT"
win_size = (1280, 720)

trades_con = sqlite3.connect("tape.db")
trades_cur = trades_con.cursor()
sql = f"SELECT * FROM {pair} LIMIT 1"
trades_cur.execute(sql)
trades_start_time = trades_cur.fetchall()[0][0]

book_ticker_con = sqlite3.connect("book_ticker.db")
book_ticker_cur = book_ticker_con.cursor()
book_ticker_cur.execute(sql)
book_ticker_start_time = book_ticker_cur.fetchall()[0][0]

start_time = np.amax([trades_start_time, book_ticker_start_time])

sql = f"SELECT * FROM {pair} WHERE time >= {start_time}"

trades_cur.execute(sql)
trades = trades_cur.fetchall()
trades_time = [i / 1000 for i in np.array(trades, dtype=np.uint64)[:, 0]]
# book_ticker_cur.execute(sql)
# book_ticker = book_ticker_cur.fetchall()
# spread = [utility.exact_diff(i[2], i[1]) for i in book_ticker]
# spread_time = [i / 1000 for i in np.array(book_ticker, dtype=np.uint64)[:, 0]]

pair_info = client.exchange_info(pair)
tick_size = float(pair_info["symbols"][0]["filters"][0]["tickSize"])

app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(
    title=f"Squeeze Chart: {pair}",
    size=win_size
)
bg_color = "#2D2D2D"
win.setBackground(background=bg_color)

layout = pg.GraphicsLayout()
win.setCentralWidget(item=layout)
date_axis = utility.DateAxisItem(orientation="bottom")
p1 = pg.PlotItem(axisItems={"bottom": date_axis})
p1.setClipToView(clip=True)
p1.setDownsampling(ds=True, auto=True, mode="subsample")
p1.showAxis(axis="right")
p1.hideAxis(axis="left")
p1.showGrid(x=True, y=True, alpha=0.5)

layout.addItem(item=p1)

for key in p1.axes:
    ax = p1.getAxis(key)
    ax.setZValue(-1)

# spread_count = {}

# for i in spread:
#     if i not in spread_count:
#         spread_count[i] = 1
#         continue
#     spread_count[i] += 1



# spread_item = pg.BarGraphItem(
#     height=list(spread_count.keys()),
#     x=list(spread_count.values()),
#     width=0.5
# )

# p1.addItem(spread_item)

# bid_price = np.array(book_ticker, dtype=np.uint64)[:, 1]
# ask_price = np.array(book_ticker, dtype=np.uint64)[:, 2]

# bid_item = pg.PlotCurveItem(spread_time, bid_price, stepMode="left")
# bid_item.setSegmentedLineMode("on")
# ask_item = pg.PlotCurveItem(spread_time, ask_price, stepMode="left")
# ask_item.setSegmentedLineMode("on")

# p1.addItem(bid_item)
# p1.addItem(ask_item)

bids = []
asks = []

for i in range(len(trades)):
    if trades[i][3]:
        bids.append((trades_time[i], trades[i][1], trades[i][2]))
        continue
    asks.append((trades_time[i], trades[i][1], trades[i][2]))

bids = np.array(bids)
asks = np.array(asks)

pxs = []

min_bid = np.amin(bids[:, 2])
max_bid = np.amax(bids[:, 2])
diff = max_bid - min_bid

for i in bids[:, 2]:
    ratio = (i - min_bid) / diff
    pxs.append(int(1 + 24 * ratio))
    

bid_bubbles = pg.ScatterPlotItem(
    x=bids[:, 0],
    y=bids[:, 1],
    size=pxs,
    pxMode=True,
    pen=pg.mkPen(None),
    brush=pg.mkBrush("#d88f30")
)

p1.addItem(bid_bubbles)

pxs = []

min_ask = np.amin(asks[:, 2])
max_ask = np.amax(asks[:, 2])
diff = max_ask - min_ask

for i in asks[:, 2]:
    ratio = (i - min_ask) / diff
    pxs.append(int(1 + 24 * ratio))
    

ask_bubbles = pg.ScatterPlotItem(
    x=asks[:, 0],
    y=asks[:, 1],
    size=pxs,
    pxMode=True,
    pen=pg.mkPen(None),
    brush=pg.mkBrush("#0086d2")
)

p1.addItem(ask_bubbles)

# price_item = pg.PlotCurveItem(trades_time, np.array(trades)[:, 1])
# price_item.setSegmentedLineMode("on")

# p1.addItem(price_item)

# crosshair = utility.CrosshairItem(
#     main_plot=p1,
#     win=win,
#     tick_size=tick_size
# )

# proxy = pg.SignalProxy(
#     signal=p1.scene().sigMouseMoved,
#     rateLimit=100,
#     slot=crosshair.mouse_moved
# )

win.show()
