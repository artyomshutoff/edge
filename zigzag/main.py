from binance.spot import Spot
from ZigZag import zigzag

client = Spot()
klines = client.klines(symbol="BTCUSDT", interval="4h", limit=100)

r = zigzag(klines=klines, min_size=0.025, percent=True)