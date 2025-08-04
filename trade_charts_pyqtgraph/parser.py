import json
import logging
import sqlite3
import sys
import threading
import time
import datetime

from binance.spot import Spot
from binance.websocket.spot.websocket_stream import (
    SpotWebsocketStreamClient as WebsocketClient
)

class Parser:
    def __init__(self, pairs):
        logger.info("parser started")
        self.client = Spot()
        self.websocket_init()
        if self.client.ping():
            logger.error("binance maintenance")
            raise "binance maintenance"
        self.start()

    def websocket_init(self):
        self.client_websocket = WebsocketClient(
            on_message=self.handle_msg,
            on_pong=self.handle_pong
        )

    def start(self):
        self.book_ticker_db = sqlite3.connect("book_ticker.db")
        self.book_ticker_cursor = self.book_ticker_db.cursor()

        self.pairs = [i.upper() for i in pairs]
        self.best_bid = {}
        self.best_ask = {}
        self.first_commit = {}
        self.pong = 1

        self.sockets = []
        self.event = threading.Event()

        watchdog_thread = threading.Thread(target=self.watchdog)
        watchdog_thread.start()

        for pair in self.pairs:
            self.first_commit[pair] = True
            self.sockets.append(f"{pair.lower()}@bookTicker")
            self.db_prepare(pair)

        self.client_websocket.subscribe(self.sockets)
        logger.info("sockets started")

    def db_prepare(self, pair):
        self.book_ticker_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {pair} \
            (time INT(20), best_bid_price FLOAT, best_ask_price FLOAT)"
        )
        logger.info(f"{pair} table created")

        now = datetime.datetime.now()
        monday = now - datetime.timedelta(days=now.weekday())
        monday = datetime.datetime.combine(monday, datetime.time.min)
        monday -= datetime.timedelta(days=28)
        cut_date = monday.timestamp() * 1000
        sql = f"DELETE FROM {pair} WHERE time < {cut_date}"

        self.book_ticker_cursor.execute(sql)
        self.book_ticker_db.commit()

        logger.info(f"{pair} old info cleared")

    def handle_msg(self, _, msg):
        msg = json.loads(msg)
        if "e" in msg and msg["e"] == "error":
            logger.error(msg)
            self.websocket_check()
            return
        try:
            pair = msg["s"]
        except:
            return
        sql = f"INSERT INTO {pair} VALUES(?, ?, ?)"
        bid = float(msg["b"])
        ask = float(msg["a"])
        values = (int(time.time() * 1000), bid, ask)

        if self.first_commit[pair]:
            self.best_bid[pair] = float(msg["b"])
            self.best_ask[pair] = float(msg["a"])
            self.first_commit[pair] = False
    
        if (self.best_bid[pair] != bid or self.best_ask[pair] != ask):
            book_ticker_db = sqlite3.connect("book_ticker.db")
            book_ticker_cursor = book_ticker_db.cursor()
            book_ticker_cursor.execute(sql, values)
            book_ticker_db.commit()
        
        self.best_bid[pair] = bid
        self.best_ask[pair] = ask

    def handle_pong(self, _):
        self.pong = 1
    
    def websocket_stop(self):
        try:
            self.client_websocket.unsubscribe(self.sockets)
            logger.info("websocket unsubscribe succeeded")
        except:
            logger.warning("websocket unsubscribe failed ")
            pass
        try:
            self.client_websocket.stop()
            logger.info("websocket stop succeeded")
        except:
            logger.warning("websocket stop failed")
            pass
    
    def websocket_check(self):
        self.pong = 0
        try:
            self.client_websocket.ping()
            current_time = int(time.time())
            while True:
                if self.pong:
                    return
        except:
            pass
        logger.warning("websocket connection lost")
        self.websocket_stop()
        self.websocket_init()
        self.client_websocket.subscribe(self.sockets)
        logger.info("sockets restarted")
        time.sleep(1)
    
    def maintenance_check(self):
        try:
            if not self.client.system_status()["status"]:
                time.sleep(1)
                return
        except:
            self.client = Spot()
            if not self.client.system_status()["status"]:
                time.sleep(1)
                return

        logger.warning("binance maintenance")
        logger.info("closing websocket")
        self.websocket_stop()

        while getattr(self.watchdog_t, "on", True):
            if self.client.system_status()["status"]:
                continue
                time.sleep(60)
            logger.info("binance end of maintenance")
            self.websocket_init()
            self.client_websocket.subscribe(self.sockets)
            return

    def watchdog(self):
        logger.info("watchdog on")
        self.watchdog_t = threading.current_thread()
        while getattr(self.watchdog_t, "on", True):
            current_time = int(time.time())
            if not current_time % 180:
                self.websocket_check()
            if not current_time % 600:
                self.maintenance_check()

        logger.info("watchdog off")

    def stop(self):
        logger.debug("try to stop")
        self.client_websocket.unsubscribe(self.sockets)
        self.client_websocket.stop()
        self.watchdog_t.on = False
        self.event.set()

if __name__ == "__main__":
    time_file = datetime.datetime.now().strftime("%d.%m.%Y %H_%M_%S")
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
