# -*- coding: utf-8 -*-
"""
鏁版嵁缁熻妯″潡
- 鏀跺彂瀛楄妭鏁?
- 瀹炴椂閫熺巼
- 閿欒璁℃暟
"""

import time
from collections import deque
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class DataStatistics(QObject):
    """鏁版嵁缁熻 - 璁＄畻瀹炴椂閫熺巼"""
    rate_updated = pyqtSignal(float)         # 鎺ユ敹閫熺巼 (B/s)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total_rx = 0
        self._total_tx = 0
        self._err_count = 0
        self._rx_samples = deque(maxlen=100)  # (timestamp, byte_count)
        self._tx_samples = deque(maxlen=100)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_rate)
        self._timer.start(500)

    def add_rx(self, n: int):
        self._total_rx += n
        self._rx_samples.append((time.time(), n))

    def add_tx(self, n: int):
        self._total_tx += n
        self._tx_samples.append((time.time(), n))

    def add_error(self):
        self._err_count += 1

    def reset(self):
        self._total_rx = 0
        self._total_tx = 0
        self._err_count = 0
        self._rx_samples.clear()
        self._tx_samples.clear()

    def _update_rate(self):
        rx_rate = self._calc_rate(self._rx_samples)
        tx_rate = self._calc_rate(self._tx_samples)
        self.rate_updated.emit(rx_rate)

    def _calc_rate(self, samples):
        if len(samples) < 2:
            return 0.0
        now = time.time()
        # 鍙粺璁℃渶杩?绉掔殑鏁版嵁
        recent = [s for s in samples if now - s[0] < 2.0]
        if not recent:
            return 0.0
        total_bytes = sum(s[1] for s in recent)
        if len(recent) < 2:
            return float(total_bytes)
        duration = recent[-1][0] - recent[0][0]
        if duration <= 0:
            return 0.0
        return total_bytes / duration

    @property
    def rx_total(self): return self._total_rx
    @property
    def tx_total(self): return self._total_tx
    @property
    def errors(self): return self._err_count

    def rate_string(self) -> str:
        rx = self._calc_rate(self._rx_samples)
        if rx < 1024:
            return f"{rx:.0f} B/s"
        elif rx < 1024 * 1024:
            return f"{rx/1024:.1f} KB/s"
        else:
            return f"{rx/1024/1024:.2f} MB/s"
