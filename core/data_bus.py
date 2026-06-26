# -*- coding: utf-8 -*-
"""
全局数据总线 - 单例模式
跨窗口共享串口数据、状态、计数等
"""
from PyQt5.QtCore import QObject, pyqtSignal


class DataBus(QObject):
    """全局数据总线 - 所有窗口共享同一个实例"""

    _instance = None

    raw_received = pyqtSignal(bytes)
    raw_sent = pyqtSignal(bytes)
    text_received = pyqtSignal(str)
    text_sent = pyqtSignal(str)
    line_received = pyqtSignal(str)

    serial_opened = pyqtSignal(str, int)
    serial_closed = pyqtSignal()
    connection_status = pyqtSignal(bool, str)

    rx_count = pyqtSignal(int)
    tx_count = pyqtSignal(int)
    err_count = pyqtSignal(int)

    tool_opened = pyqtSignal(str)
    tool_closed = pyqtSignal(str)

    app_config_changed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_buffer = ''
        self._rx_total = 0
        self._tx_total = 0
        self._err_total = 0

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = DataBus()
        return cls._instance

    def publish_serial_rx(self, data: bytes):
        self.raw_received.emit(data)
        self._rx_total += len(data)
        self.rx_count.emit(self._rx_total)
        try:
            text = data.decode('utf-8', errors='replace')
            self.text_received.emit(text)
            self._line_buffer += text
            while '\n' in self._line_buffer:
                idx = self._line_buffer.index('\n')
                line = self._line_buffer[:idx].rstrip('\r')
                self._line_buffer = self._line_buffer[idx + 1:]
                if line:
                    self.line_received.emit(line)
        except Exception:
            pass

    def publish_serial_tx(self, data: bytes):
        self.raw_sent.emit(data)
        self._tx_total += len(data)
        self.tx_count.emit(self._tx_total)
        try:
            text = data.decode('utf-8', errors='replace')
            self.text_sent.emit(text)
        except Exception:
            pass

    def publish_serial_opened(self, port: str, baud: int):
        self.serial_opened.emit(port, baud)
        self.connection_status.emit(True, f'{port} @ {baud}')

    def publish_serial_closed(self):
        self.serial_closed.emit()
        self.connection_status.emit(False, '未连接')

    def publish_err(self):
        self._err_total += 1
        self.err_count.emit(self._err_total)

    def reset_counts(self):
        self._rx_total = 0
        self._tx_total = 0
        self._err_total = 0
        self.rx_count.emit(0)
        self.tx_count.emit(0)
        self.err_count.emit(0)

    @property
    def rx_total(self) -> int:
        return self._rx_total

    @property
    def tx_total(self) -> int:
        return self._tx_total

    @property
    def err_total(self) -> int:
        return self._err_total
