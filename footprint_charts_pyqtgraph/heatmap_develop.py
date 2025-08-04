
# class Heatmap:
#     def __init__(self, open_time, blocks, close_time):
#         self.open_time = open_time
#         self.blocks = blocks
#         self.close_time = close_time

#     def format_blocks(self):
#         for i in list(self.blocks.keys()):


class HeatmapItem(QGraphicsItem):
    def __init__(self, pair, tick_size_mult, interval):
        super().__init__()
        self.setCacheMode(2)
        self.pair = pair
        self.interval = interval
        self.tick_size_mult = tick_size_mult

        c = self.heatmap_fetch()

        heatmap = []

        for i in range(len(c)):
            block_time = c[i][0] - c[i][0] % self.interval

        self.generatePicture()

    def heatmap_fetch(self):
        con = sqlite3.connect("heatmap.db")
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {self.pair}")
        c = cur.fetchall()

        for i in range(len(c)):
            c[i] = [
                c[i][0] / 1000,
                format_value(
                    c[i][1],
                    Decimal(str(self.tick_size_mult)) * Decimal(str(c[i][6])),
                ),
                c[i][2],
                c[i][3],
                c[i][4],
                c[i][5],
                c[i][6],
                c[i][7],
            ]

        return c

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)

        p.setPen(pg.mkPen(None))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class VolumeHeatmapItem(QGraphicsItem):
    def __init__(self, pair, period, interval, ticksize, fetch_time):
        super().__init__()
        self.setCacheMode(2)
        self.pair = pair
        self.period = interval_to_unix(period)
        self.interval = interval_to_unix(interval)
        self.ticksize = ticksize
        self.fetch_time = fetch_time

        self.klines = interval
        self.dates = np.array(self.klines, dtype=float)[:, 0]  # open time
        self.highs = np.array(self.klines, dtype=float)[:, 2]  # high
        self.lows = np.array(self.klines, dtype=float)[:, 3]  # low

        volumeheatmap = []

        for i in range(len(self.dates)):
            if len(volumeheatmap) != 0:
                if not self.dates[i] % self.period:
                    volumeheatmap.append([self.dates[i], {}])
                    current_high = format_value(self.highs[i], self.ticksize)
                    current_low = format_value(self.lows[i], self.ticksize)
                    price = current_high
                    while price >= current_low:
                        if price in volumeheatmap[-1][1]:
                            volumeheatmap[-1][1][price] += 1
                        else:
                            volumeheatmap[-1][1][price] = 1
                        price = float(Decimal(price) - Decimal(self.ticksize))
                    for k in volumeheatmap[-2][1]:
                        if k in volumeheatmap[-1][1]:
                            volumeheatmap[-1][1][k] += volumeheatmap[-2][1][k]
                        else:
                            volumeheatmap[-1][1][k] = volumeheatmap[-2][1][k]
                    if not self.att:
                        for k in volumeheatmap[-1][1]:
                            if volumeheatmap[-1][1][k] > 0:
                                volumeheatmap[-1][1][k] -= 1
                        self.att = 10
                    self.att -= 1

                else:
                    current_high = format_value(self.highs[i], self.ticksize)
                    current_low = format_value(self.lows[i], self.ticksize)
                    price = current_high
                    while price >= current_low:
                        if price in volumeheatmap[-1][1]:
                            volumeheatmap[-1][1][price] += 1
                        else:
                            volumeheatmap[-1][1][price] = 1
                        price = exact_diff(price, self.ticksize)
            else:
                if not self.dates[i] % self.interval:
                    volumeheatmap.append([self.dates[i], {}])
                    currentHigh = format_value(self.highs[i], self.ticksize)
                    currentLow = format_value(self.lows[i], self.ticksize)
                    price = currentHigh
                    while price >= currentLow:
                        if str(price) in volumeheatmap[-1][1]:
                            volumeheatmap[-1][1][str(price)] += 1
                        else:
                            volumeheatmap[-1][1][str(price)] = 1
                        price = float(
                            Decimal(str(price)) - Decimal(str(self.ticksize))
                        )
                    self.att = 10

        for i in range(len(volumeheatmap)):
            volumeheatmap[i][1] = [
                [float(k), volumeheatmap[i][1][k]] for k in volumeheatmap[i][1]
            ]
        self.volumeheatmap = volumeheatmap

        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)

        p.setPen(pg.mkPen(None))
        self.vol = []
        for i in range(len(self.volumeheatmap)):
            for j in range(len(self.volumeheatmap[i][1])):
                if self.volumeheatmap[i][1][j][1] not in self.vol:
                    self.vol.append(self.volumeheatmap[i][1][j][1])
        self.vol.sort()
        median = np.mean(self.vol)
        self.maxVol = int(np.mean([i for i in self.vol if i > median]))
        self.minVol = int(np.mean([i for i in self.vol if i < median]))
        if len([i for i in self.vol if i < self.minVol]) != 0:
            self.minVol = int(
                np.mean([i for i in self.vol if i < self.minVol])
            )
        self.PriceVolumeHeatmap = {}
        for i in range(len(self.volumeheatmap)):
            for j in range(len(self.volumeheatmap[i][1])):
                if (
                    str(self.volumeheatmap[i][1][j][0])
                    in self.PriceVolumeHeatmap
                ):
                    if (
                        self.volumeheatmap[i][1][j][1]
                        != self.PriceVolumeHeatmap[
                            str(self.volumeheatmap[i][1][j][0])
                        ][-1][1]
                    ):
                        self.PriceVolumeHeatmap[
                            str(self.volumeheatmap[i][1][j][0])
                        ].append(
                            [
                                self.volumeheatmap[i][0],
                                self.volumeheatmap[i][1][j][1],
                            ]
                        )
                else:
                    self.PriceVolumeHeatmap[
                        str(self.volumeheatmap[i][1][j][0])
                    ] = [
                        [
                            self.volumeheatmap[i][0],
                            self.volumeheatmap[i][1][j][1],
                        ]
                    ]
        for k in self.PriceVolumeHeatmap:
            for i in range(len(self.PriceVolumeHeatmap[k]) - 1):
                if (
                    self.PriceVolumeHeatmap[k][i][1] != 0
                    and self.PriceVolumeHeatmap[k][i][0] >= self.dates[0]
                    and self.PriceVolumeHeatmap[k][i][1] >= self.minVol
                ):
                    exp = (self.PriceVolumeHeatmap[k][i][1] - self.minVol) / (
                        self.maxVol - self.minVol
                    )
                    if exp >= 0:
                        c = "#11022D"
                    if exp >= 0.1:
                        c = "#1F032B"
                    if exp >= 0.2:
                        c = "#380621"
                    if exp >= 0.3:
                        c = "#5D0E14"
                    if exp >= 0.4:
                        c = "#881A0D"
                    if exp >= 0.5:
                        c = "#A53E1B"
                    if exp >= 0.6:
                        c = "#C37C2E"
                    if exp >= 0.7:
                        c = "#D6BA3F"
                    if exp >= 0.8:
                        c = "#E5DE74"
                    if exp >= 1:
                        c = "#FEFDDF"
                    p.setBrush(pg.mkBrush(c))
                    p.drawRect(
                        QtCore.QRectF(
                            self.PriceVolumeHeatmap[k][i][0] / 1000,
                            float(k),
                            (
                                (
                                    self.PriceVolumeHeatmap[k][i + 1][0]
                                    if (i + 1)
                                    != (len(self.PriceVolumeHeatmap[k]) - 1)
                                    else self.dates[-1]
                                )
                                - self.PriceVolumeHeatmap[k][i][0]
                            )
                            / 1000
                            - 1,
                            self.ticksize,
                        )
                    )

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())