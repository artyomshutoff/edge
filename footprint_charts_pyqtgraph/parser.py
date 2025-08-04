import json
import logging
import sqlite3
import sys
import threading
import time
from datetime import datetime
from decimal import Decimal

from binance.spot import Spot
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

from utility import format_value, interval_to_unix, exact_add


class Parser:
    class TempInfo:
        def __init__(self, pair, tick_size):
            self.footprint = {}
            self.delta = [0, 0, 0, 0]
            self.tick_size = tick_size
            self.sync = 0

    def __init__(self, pairs, interval):
        logger.info("Parser started")
        self.client = Spot()
        self.client_websocket = SpotWebsocketStreamClient(
            on_message=self.handle_msg)
        if self.client.ping():
            logger.error("Binance maintenance")
            raise "Binance maintenance"

        self.footprint_db = sqlite3.connect("footprint.db")
        self.delta_db = sqlite3.connect("delta.db")
        self.heatmap_db = sqlite3.connect("heatmap.db")

        self.footprint_cursor = self.footprint_db.cursor()
        self.delta_cursor = self.delta_db.cursor()
        self.heatmap_cursor = self.heatmap_db.cursor()

        self.interval = interval
        self.pairs = [i.upper() for i in pairs]
        self.tick_size = self.get_tick_size(self.pairs)

        self.sockets = []
        self.push_threads = []
        self.pair_obj = {}
        self.event = threading.Event()

        watchdog_thread = threading.Thread(target=self.watchdog)
        watchdog_thread.start()

        for pair in self.pairs:
            self.sockets.append(f"{pair.lower()}@trade")
            self.create_tables(pair)
            self.delete_old_info(pair)
            self.pair_obj[pair] = self.TempInfo(pair, self.tick_size[pair])
        
        thread = threading.Thread(target=self.push, args=(self.event,))
        thread.start()

        self.client_websocket.subscribe(self.sockets)
        logger.info("Sockets started")

    def delete_old_info(self, pair):
        current_time = int(time.time())
        monday_time = current_time - current_time % 604800
        if current_time % 604800 <= 345600:
            monday_time -= 259200
        else:
            monday_time += 345600
        cut_date = (monday_time - 604800 * 4) * 1000
        sql = f"DELETE FROM {pair} WHERE close_time < {cut_date}"

        self.footprint_cursor.execute(sql)
        self.footprint_db.commit()

        self.delta_cursor.execute(sql)
        self.delta_db.commit()

        self.heatmap_cursor.execute(sql)
        self.heatmap_db.commit()

        logger.info(f"{pair} old info deleted")

    def create_tables(self, pair):
        self.delta_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {pair} \
            (open_time INT(20), high FLOAT, low FLOAT, \
            close FLOAT, close_time INT(20))"
        )
        self.footprint_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {pair} \
            (open_time INT(20), price FLOAT, bid FLOAT, \
            ask FLOAT, tick_size FLOAT, close_time INT(20))"
        )
        self.heatmap_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {pair} \
            (open_time INT(20), price FLOAT, volume FLOAT, \
            bid FLOAT, ask FLOAT, tick_size FLOAT, close_time INT(20))"
        )
        logger.info(f"{pair} tables created")

    def handle_msg(self, _, msg):
        msg = json.loads(msg)
        if "e" in msg and msg["e"] == "error":
            logger.error(msg)
            self.client_websocket.unsubscribe(self.sockets)
            self.client_websocket.stop()
            self.client_websocket = SpotWebsocketStreamClient(
                on_message=self.handle_msg
            )
            return
        try:
            pair = msg["s"]
        except BaseException:
            return
        while True:
            if self.pair_obj[pair].sync:
                continue
            self.pair_obj[pair].sync = 1
            price = float(msg["p"])
            quantity = Decimal(msg["q"])
            tmp_delta_close = Decimal(self.pair_obj[pair].delta[3])
            side = 0 if msg["m"] else 1
            var = 1 if msg["m"] else -1
            if price in self.pair_obj[pair].footprint:
                value = exact_add(
                    self.pair_obj[pair].footprint[price][side], quantity)
                self.pair_obj[pair].footprint[price][side] = value
            else:
                value = [float(quantity), 0][::var]
                self.pair_obj[pair].footprint[price] = value
            value = float(tmp_delta_close - quantity * var)
            self.pair_obj[pair].delta[3] = value
            obj_delta = self.pair_obj[pair].delta
            if obj_delta[3] > obj_delta[1]:
                self.pair_obj[pair].delta[1] = obj_delta[3]
            if obj_delta[3] < obj_delta[2]:
                self.pair_obj[pair].delta[2] = obj_delta[3]
            self.pair_obj[pair].sync = 0
            break

    def watchdog(self):
        logger.info("Watchdog on")
        self.watchdog_t = threading.current_thread()
        while getattr(self.watchdog_t, "on", True):
            if not int(time.time()) % 5:
                if not self.client_websocket.ping():
                    time.sleep(1)
                    continue
                logger.warning("websocket connection lost")
                try:
                    self.client_websocket.unsubscribe(self.sockets)
                except:
                    pass
                try:
                    self.client_websocket.stop()
                except:
                    pass
                self.client_websocket = SpotWebsocketStreamClient(
                    on_message=self.handle_msg
                )
                self.client_websocket.subscribe(self.sockets)
                logger.info("sockets restarted")
                time.sleep(1)

            if int(time.time()) % 600:
                continue
            if not self.client.ping():
                logger.debug("Binance online")
                time.sleep(1)
                continue
            logger.info("Closing multiplex socket")
            self.client_websocket.unsubscribe(self.sockets)
            self.client_websocket.stop()
            logger.warning("Binance maintenance")

            while getattr(self.watchdog_t, "on", True):
                if self.client.ping():
                    continue
                    time.sleep(60)
                logger.info("Binance end of maintenance")
                try:
                    self.client_websocket.unsubscribe(self.sockets)
                except:
                    pass
                try:
                    self.client_websocket.stop()
                except:
                    pass
                self.client = Spot()
                self.client_websocket = SpotWebsocketStreamClient(
                    on_message=self.handle_msg
                )
                self.client_websocket.subscribe(self.sockets)
                break

        logger.info("Watchdog off")

    def get_tick_size(self, pairs):
        symbols_info = self.client.exchange_info(symbols=pairs)["symbols"]
        res = {}
        for info in symbols_info:
            res[info["symbol"]] = float(info["filters"][0]["tickSize"])
        logger.info(f'{", ".join(pairs)} ticks received')
        return res

    def stop(self):
        logger.debug("try to stop")
        self.client_websocket.unsubscribe(self.sockets)
        self.client_websocket.stop()
        self.watchdog_t.on = False
        self.event.set()

    def push(self, event):
        footprint_db = sqlite3.connect("footprint.db")
        delta_db = sqlite3.connect("delta.db")
        heatmap_db = sqlite3.connect("heatmap.db")

        footprint_cursor = footprint_db.cursor()
        delta_cursor = delta_db.cursor()
        heatmap_cursor = heatmap_db.cursor()

        logger.info("Push thread started")

        while True:
            if event.is_set():
                logger.info("push thread stopped")
                break
            current_time = int(time.time())
            if (current_time + 1) % 60:
                continue

            for pair in self.pairs:
                tmp_footprint = self.pair_obj[pair].footprint
                tmp_delta = self.pair_obj[pair].delta
                tick_size = self.pair_obj[pair].tick_size

                open_time = current_time - current_time % 60
                open_time *= 1000
                close_time = open_time - 1
                close_time += interval_to_unix(self.interval, True)
                self.pair_obj[pair].sync = 1

                footprint_push = []
                for price in tmp_footprint:
                    bid = tmp_footprint[price][0]
                    ask = tmp_footprint[price][1]
                    push_value = (
                        open_time,
                        price,
                        bid,
                        ask,
                        tick_size,
                        close_time
                    )
                    footprint_push.append(push_value)

                delta_push = [
                    open_time,
                    tmp_delta[1],
                    tmp_delta[2],
                    tmp_delta[3],
                    close_time
                ]

                heatmap = {}

                while True:
                    try:
                        orderbook = self.client.depth(symbol=pair, limit=1000)
                        break
                    except BaseException:
                        self.client = Spot()
                        logger.error("receiving depth error")

                for i in orderbook["bids"]:
                    price = format_value(i[0], tick_size * 100)
                    if price not in heatmap:
                        heatmap[price] = [float(i[1]), 0]
                        continue
                    heatmap[price][0] = exact_add(heatmap[price][0], i[1])
                for i in orderbook["asks"]:
                    price = format_value(i[0], tick_size * 100)
                    if price not in heatmap:
                        heatmap[price] = [0, float(i[1])]
                        continue
                    heatmap[price][1] = exact_add(heatmap[price][1], i[1])

                heatmap_push = []
                for price in heatmap:
                    volume = sum(heatmap[price])
                    push_value = (
                        open_time,
                        price,
                        volume,
                        heatmap[price][0],
                        heatmap[price][1],
                        tick_size * 100,
                        close_time
                    )
                    heatmap_push.append(push_value)

                self.pair_obj[pair].footprint = {}
                self.pair_obj[pair].delta = [0, 0, 0, 0]
                self.pair_obj[pair].sync = 0

                sql = f"INSERT INTO {pair} VALUES(?, ?, ?, ?, ?, ?)"
                footprint_cursor.executemany(sql, footprint_push)
                footprint_db.commit()

                sql = f"INSERT INTO {pair} VALUES(?, ?, ?, ?, ?)"
                delta_cursor.execute(sql, delta_push)
                delta_db.commit()

                sql = f"INSERT INTO {pair} VALUES(?, ?, ?, ?, ?, ?, ?)"
                heatmap_cursor.executemany(sql, heatmap_push)
                heatmap_db.commit()

                logger.info(f"{pair} commit")

            time.sleep(1)


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
    interval = "1m"
    parser = Parser(pairs, interval)
