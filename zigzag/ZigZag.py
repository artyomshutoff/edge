import numpy as np

def zigzag(*, klines, min_size, percent):
    klines = np.array(object=klines, dtype=np.float64)
    time = klines[:, 0]
    high = klines[:, 2]
    low = klines[:, 3]
    length = len(klines)
    zigzag = np.zeros(length)
    trend, last_high, last_low = 0, 0, 0

    for i in range(length):
        price_change = min_size
        if trend == 0:
            if percent:
                price_change *= low[0]
            if high[i] >= low[0] + price_change:
                trend = 1
                last_high = i
                zigzag[0] = -1
                continue

            if percent:
                price_change *= high[0]
            if low[i] <= high[0] - price_change:
                trend = -1
                last_low = i
                zigzag[0] = 1

        if trend == 1:
            if percent:
                price_change *= high[last_high]
            term = low[i] <= high[last_high] - price_change
            if term and high[i] < high[last_high]:
                trend = -1
                zigzag[last_high] = 1
                last_low = i
            if high[i] > high[last_high]:
                last_high = i

        if trend == -1:
            if percent:
                price_change *= low[last_low]
            term = high[i] >= low[last_low] + price_change
            if term and low[i] > low[last_low]:
                trend = 1
                zigzag[last_low] = -1
                last_high = i
            if low[i] < low[last_low]:
                last_low = i

    last_trend = 0
    last_trend_index = 0

    for i in range(length - 1, -1, -1):
        if zigzag[i] != 0:
            last_trend = zigzag[i]
            last_trend_index = i
            break

    determinant = 0
    high_determinant = high[last_trend_index]
    low_determinant = low[last_trend_index]

    for i in range(last_trend_index + 1, length):
        if last_trend == 1 and low[i] < low_determinant:
            low_determinant = low[i]
            determinant = i

        if last_trend == -1 and high[i] > high_determinant:
            high_determinant = high[i]
            determinant = i

    zigzag[determinant] = -1 if last_trend == 1 else 1

    out = []

    for i in range(length):
        if zigzag[i] == 1:
            out.append([time[i], high[i]])
        if zigzag[i] == -1:
            out.append([time[i], low[i]])

    return np.array(object=out, dtype=np.float64)
