import json
import logging
import sqlite3
import sys
from datetime import datetime

from binance.spot import Spot
from binance.websocket.spot.websocket_stream import (
    SpotWebsocketStreamClient as WebsocketClient
)

class Parser:
    def __init__(self, pairs):
        logger.info("parser started")
        self.client = Spot()
        self.client_websocket = WebsocketClient(
            on_message=self.handle_msg
        )
        if self.client.ping():
            logger.error("binance maintenance")
            raise "Binance maintenance"
        self.start()
    
    def start(self):
        self.db = sqlite3.connect("tape.db")
        self.cursor = self.db.cursor()
        self.pairs = [i.upper() for i in pairs]
        self.sockets = []

        for pair in self.pairs:
            self.sockets.append(f"{pair.lower()}@trade")
            self.create_table(pair)

        self.client_websocket.subscribe(self.sockets)
        logger.info("sockets started")

    def create_table(self, pair):
        self.trades_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {pair} \
            (time INT(20), price FLOAT, size FLOAT, is_bid BIT)"
        )
        logger.info(f"{pair} table created")

    def handle_msg(self, _, msg):
        msg = json.loads(msg)
        if "e" in msg and msg["e"] == "error":
            logger.error(msg)
            self.handle_restart()
            return
        try:
            pair = msg["s"]
        except:
            return
        sql = f"INSERT INTO {pair} VALUES(?, ?, ?, ?)"
        is_bid = 1 if msg["m"] else 0
        values = (msg["T"], float(msg["p"]), float(msg["q"]), is_bid)
        trades_db = sqlite3.connect("tape.db")
        trades_cursor = trades_db.cursor()
        trades_cursor.execute(sql, values)
        trades_db.commit()
    
    def handle_restart(self):
        logger.warning("websocket connection error")
        try:
            self.client_websocket.unsubscribe(self.sockets)
            logger.info("websocket unsubscribe succeeded")
        except:
            logger.warning("websocket unsubscribe failed")
            pass
        try:
            self.client_websocket.stop()
            logger.info("websocket stop succeeded")
        except:
            logger.warning("websocket stop failed")
            pass
        self.client_websocket = WebsocketClient(
            on_message=self.handle_msg
        )
        self.client_websocket.subscribe(self.sockets)
        logger.info("sockets restarted")

    def stop(self):
        logger.debug("try to stop")
        self.client_websocket.unsubscribe(self.sockets)
        self.client_websocket.stop()
        self.event.set()

if __name__ == "__main__":
    time_file = datetime.now().strftime("%d.%m.%Y %H_%M_%S")
    log_filename = f"parser {time_file}.log"
    log_formatter = logging.Formatter(
        fmt="%(levelname)-8s %(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger("parser")
    logger.setLevel(level=logging.DEBUG)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(level=logging.DEBUG)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(filename=log_filename)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(level=logging.INFO)
    logger.addHandler(file_handler)

    pairs = ["btcusdt", "ethusdt", "ltcusdt", "bnbusdt"]
    parser = Parser(pairs)
