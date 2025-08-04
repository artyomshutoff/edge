class MarketProfileItem(QGraphicsItem):
    def __init__(self, **kwargs):
        super().__init__()
        self.setCacheMode(2)
        self.plot = kwargs["plot"]
        self.block = np.array(kwargs["block"], dtype=np.float64)
        self.timespan = np.array(kwargs["timespan"], dtype=np.float64)
        self.tick_size = kwargs["tick_size"]
        self.VA_show = kwargs["VA_show"]
        self.POC_show = kwargs["POC_show"]
        self.alphabet = kwargs["alphabet"]
        self.deployed = kwargs["deployed"]
        self.heatmap_gradient = kwargs["heatmap_gradient"]
        self.heatmap_on = kwargs["heatmap_gradient"]
        self.open_close_show = kwargs["open_close_show"]
        self.dynamic_VA = kwargs["dynamic_VA"]
        self.generate_values()

    def generate_values(self):
        if self.open_close_show:
            self.timespan_open_close = []
            for i in range(len(self.timespan)):
                o = utility.format_value(self.timespan[i][1], self.tick_size)
                c = utility.format_value(self.timespan[i][4], self.tick_size)
                self.timespan_open_close.append([o, c])

        self.timespan = list(map(lambda x: x / 1000, self.timespan[:, 0]))
        diff = self.timespan[1] - self.timespan[0]
        diff2 = self.block[:, 0][1] - self.block[:, 0][0]
        self.num_letters = int(diff / diff2)
        self.market_profile = []

        if self.heatmap_on:
            self.intervals_period = 0
            period_start = self.timespan[0]
            interval_time = self.interval[:, 0]
            for j in range(len(self.interval)):
                if interval_time[j] >= period_start + diff:
                    break
                if interval_time[j] < self.period[0]:
                    continue
                self.intervals_period += 1

        for i in range(len(self.period)):
            self.TPO.append([self.period[i], {}])

            if self.open_close_show:
                self.TPO[-1].append(self.period_open_close[i])

            n = 0

            for j in range(len(self.interval)):
                if interval_time[j] >= self.period[i] + diff:
                    break
                if self.interval[:, 0][j] < self.period[i]:
                    continue

                current_high = utility.format_value(
                    self.interval[:, 2][j],
                    self.tick_size,
                )
                current_low = utility.format_value(
                    self.interval[:, 3][j],
                    self.tick_size,
                )
                price = current_high
                if n <= 25:
                    char = string.ascii_uppercase[n]
                else:
                    char = string.ascii_lowercase[n]

                while price >= current_low:
                    if price in self.TPO[-1][1]:
                        self.TPO[-1][1][price][0] += 1
                        self.TPO[-1][1][price][1] += char
                    else:
                        self.TPO[-1][1][price] = [1, char]
                    price = float(Decimal(price) - Decimal(self.tick_size))

                n += 1

        for i in range(len(self.TPO)):
            self.TPO[i][1] = [[k, self.TPO[i][1][k]] for k in self.TPO[i][1]]

        self.generate_picture()

    def generate_picture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        w = (self.interval[:, 0][1] - self.interval[:, 0][0]) / 3
        p.setPen(pg.mkPen(color=None))

        for i in range(len(self.TPO)):
            square_start = self.TPO[i][0]
            z = 0
            POC, VAH, VAL = utility.distribution_elements(
                [
                    [self.TPO[i][1][n][0], self.TPO[i][1][n][1][0]]
                    for n in range(len(self.TPO[i][1]))
                ]
            )

            if self.deployed:
                for j in range(len(self.interval)):
                    if self.interval[:, 0][j] >= self.TPO[i][0] + (
                        self.TPO[1][0] - self.TPO[0][0]
                    ):
                        break

                    if self.interval[:, 0][j] >= self.TPO[i][0]:
                        current_high = utility.format_value(
                            self.interval[:, 2][j], self.tick_size
                        )
                        current_low = utility.format_value(
                            self.interval[:, 3][j], self.tick_size
                        )
                        price = current_high

                        while price >= current_low:
                            if self.heatmap_on:
                                color = utility.heatmap(
                                    value=z,
                                    start_value=0,
                                    finish_value=self.intervals_period,
                                    colormap=self.heatmap_gradient,
                                    to_hex=False,
                                )
                                p.setBrush(
                                    pg.mkBrush((color[0], color[1], color[2], 85))
                                )
                                color = (color[0], color[1], color[2], 85)

                                if self.VA_sho and VAL <= price <= VAH:
                                    p.setBrush(pg.mkBrush((color[0], color[1], color[2], 255))
                                    )
                                    color = (color[0], color[1], color[2], 255)

                            else:
                                p.setBrush(pg.mkBrush("#cccccc"))
                                color = "#cccccc"

                                if self.VA_show and VAL <= price <= VAH:
                                    c = "#0080C0"
                                    p.setBrush(pg.mkBrush(color=c))

                                if self.POC_show and price == POC:
                                    c = "#ff3333"
                                    p.setBrush(pg.mkBrush(color=c))

                            if self.alphabet:
                                char = string.ascii_lowercase[z]
                                if z <= 25:
                                    char = string.ascii_uppercase[z]
                                text = pg.TextItem(
                                    text=char,
                                    anchor=(0.5, 0.5),
                                    color=pg.mkColor(color=c),
                                )
                                self.plot.addItem(text)
                                text.setPos(self.interval[:, 0][j], price)
                                text.setFont(
                                    QFont("Bahnschrift", 10, weight=QtGui.QFont.Bold)
                                )

                            else:
                                p.drawRect(
                                    QtCore.QRectF(
                                        self.interval[:, 0][j] - w,
                                        price
                                        + self.tick_size * 0.5
                                        - self.tick_size * 0.1,
                                        w * 2,
                                        -self.tick_size * 0.8,
                                    )
                                )

                            price = float(Decimal(price) - Decimal(self.tick_size))

                        z += 1

            else:
                for j in range(len(self.TPO[i][1])):
                    square_start = self.TPO[i][0]

                    for n in range(len(self.TPO[i][1][j][1][1])):
                        if self.heatmap_on:
                            color = utility.heatmap(
                                string.ascii_uppercase.index(
                                    self.TPO[i][1][j][1][1][n]
                                ),
                                0,
                                self.intervals_period,
                                self.heatmap_gradient,
                                False,
                            )

                            if (
                                self.TPO[i][1][j][1][1][n] == "A"
                                and self.TPO[i][1][j][0] == self.TPO[i][2][0]
                            ):
                                color = (255, 128, 0)

                            if (
                                self.TPO[i][1][j][1][1][n]
                                == string.ascii_uppercase[self.max_letter - 1]
                                and self.TPO[i][1][j][0] == self.TPO[i][2][1]
                            ):
                                color = (255, 255, 0)

                            p.setBrush(pg.mkBrush((color[0], color[1], color[2], 85)))
                            color = (color[0], color[1], color[2], 85)

                            if self.VA_show:
                                if VAL <= self.TPO[i][1][j][0] <= VAH:
                                    p.setBrush(
                                        pg.mkBrush((color[0], color[1], color[2], 255))
                                    )
                                    color = (color[0], color[1], color[2], 255)

                        else:
                            c = "#cccccc"
                            p.setBrush(pg.mkBrush(color=c))

                            exp = VAL <= self.TPO[i][1][j][0] <= VAH
                            if self.VA_show and exp:
                                c = "#0080C0"
                                p.setBrush(pg.mkBrush(color=c))

                            exp = self.TPO[i][1][j][0] == POC
                            if self.POC_show and exp:
                                c = "#ff3333"
                                p.setBrush(pg.mkBrush(color=c))

                        if self.alphabet:
                            text = pg.TextItem(
                                text=self.TPO[i][1][j][1][1][n],
                                anchor=(0.5, 0.5),
                                color=pg.mkColor(color=с),
                            )
                            self.plot.addItem(text)
                            text.setPos(
                                (
                                    square_start
                                    + (
                                        self.interval[:, 0][1] / 1000
                                        - self.interval[:, 0][0] / 1000
                                    )
                                    * (n + 1)
                                ),
                                self.TPO[i][1][j][0],
                            )
                            text.setFont(
                                QFont("Bahnschrift", 10, weight=QtGui.QFont.Bold)
                            )

                        else:
                            time = (self.interval[:, 0][1] - self.interval[:, 0][0]) * n
                            x = square_start + time - w
                            y = self.TPO[i][1][j][0] + self.tick_size * 0.4
                            width = w * 2
                            height = -self.tick_size * 0.8
                            p.drawRect(QtCore.QRectF(x, y, width, height))

            if self.heatmap_on and self.POC_show:
                p.setBrush(pg.mkBrush(color=None))
                p.setPen(pg.mkPen(color="#ffffff"))
                p.drawRect(
                    QtCore.QRectF(
                        square_start
                        - (self.interval[:, 0][1] - self.interval[:, 0][0]) / 2,
                        POC + self.tick_size * 0.5,
                        self.TPO[1][0] - self.TPO[0][0],
                        -self.tick_size,
                    )
                )
                p.setPen(pg.mkPen(None))

        p.end()

    def dynamic_value_area(self):
        self.values = []
        self.TPO = []

        for i in range(len(self.period)):
            self.TPO.append([self.period[i], {}])

            n = 0

            for j in range(len(self.interval)):
                if self.interval[:, 0][j] >= self.period[i] + diff:
                    break
                if self.interval[:, 0][j] < self.period[i]:
                    continue

                current_high = utility.format_value(self.interval[:, 2][j], self.tick_size)

                current_low = utility.format_value(self.interval[:, 3][j], self.tick_size)
                price = current_high

                while price >= current_low:
                    if price in self.TPO[-1][1]:
                        self.TPO[-1][1][price] += 1
                    else:
                        self.TPO[-1][1][price] = 1
                    price = float(Decimal(price) - Decimal(self.tick_size))

                n += 1

                self.dynamic_VP.append(
                    [
                        self.interval[:, 0][j],
                        utility.distribution_elements([[k, self.TPO[-1][1][k]] for k in self.TPO[-1][1]]),
                    ]
                )

        self.plot.addItem(
            pg.PlotDataItem(
                [self.dynamic_VP[i][0] for i in range(len(self.dynamic_VP))],
                [self.dynamic_VP[i][1][0] for i in range(len(self.dynamic_VP))],
                pen=pg.mkPen(color=pg.mkColor("#27a9e6"), width=1),
            )
        )

        self.plot.addItem(
            pg.PlotDataItem(
                [self.dynamic_VP[i][0] for i in range(len(self.dynamic_VP))],
                [self.dynamic_VP[i][1][1] for i in range(len(self.dynamic_VP))],
                pen=pg.mkPen(color=pg.mkColor("#c9814d"), width=1),
            )
        )

        self.plot.addItem(
            pg.PlotDataItem(
                [self.dynamic_VP[i][0] for i in range(len(self.dynamic_VP))],
                [self.dynamic_VP[i][1][2] for i in range(len(self.dynamic_VP))],
                pen=pg.mkPen(color=pg.mkColor("#c9814d"), width=1),
            )
        )

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())