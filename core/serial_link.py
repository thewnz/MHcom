# -*- coding: utf-8 -*-
"""
串口核心模块
- SerialOpenWorker: 异步打开串口（支持全部参数）
- SerialLink: 串口通信主类（单例模式，全局共享）
"""
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer


class SerialOpenWorker(QObject):
    """异步打开串口的 Worker - 支持完整串口参数"""
    ok = pyqtSignal(object)
    fail = pyqtSignal(str)

    def __init__(self, port: str, baud: int, dbits: int = 8,
                 sbits: float = 1, parity: str = 'N',
                 rtscts: bool = False, xonxoff: bool = False,
                 dsrdtr: bool = False, timeout: float = 0.05,
                 parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self.dbits = dbits
        self.sbits = sbits
        self.parity = parity
        self.rtscts = rtscts
        self.xonxoff = xonxoff
        self.dsrdtr = dsrdtr
        self.timeout = timeout

    def run(self):
        import serial
        pmap = {'无': 'N', 'N': 'N', '奇': 'O', 'O': 'O', '偶': 'E', 'E': 'E',
                'Mark': 'M', 'M': 'M', 'Space': 'S', 'S': 'S'}
        sbm = {
            1: serial.STOPBITS_ONE,
            '1': serial.STOPBITS_ONE,
            '1.5': serial.STOPBITS_ONE_POINT_FIVE,
            1.5: serial.STOPBITS_ONE_POINT_FIVE,
            '2': serial.STOPBITS_TWO,
            2: serial.STOPBITS_TWO,
        }
        try:
            ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                bytesize=int(self.dbits),
                stopbits=sbm.get(self.sbits, serial.STOPBITS_ONE),
                parity=pmap.get(self.parity, 'N'),
                rtscts=self.rtscts,
                xonxoff=self.xonxoff,
                dsrdtr=self.dsrdtr,
                timeout=self.timeout
            )
            self.ok.emit(ser)
        except Exception as e:
            self.fail.emit(str(e))


class SerialLink(QObject):
    """串口通信主类 - 单例模式，异步读取 + 信号推送

    全局唯一实例，所有面板/工具共享同一个串口连接。
    """

    _instance = None

    received = pyqtSignal(bytes)
    sent = pyqtSignal(int)
    err_count_changed = pyqtSignal(int)
    tx_count_changed = pyqtSignal(int)
    rx_count_changed = pyqtSignal(int)
    state_changed = pyqtSignal(bool)
    port_info_changed = pyqtSignal(str, int, str, int, float, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ser = None
        self._rx_bytes = 0
        self._tx_bytes = 0
        self._err_count = 0
        self._timer = None
        self._port_name = ''
        self._baudrate = 0
        self._parity = 'N'
        self._dbits = 8
        self._sbits = 1
        self._flow_ctrl = '无'

    @classmethod
    def instance(cls):
        """获取单例"""
        if cls._instance is None:
            cls._instance = SerialLink()
        return cls._instance

    def set_serial(self, ser, port_name='', baudrate=0, parity='N',
                   dbits=8, sbits=1, flow_ctrl='无'):
        """设置已打开的串口对象（替换前先关闭旧串口，防止资源泄漏）"""
        # 关闭前一个串口连接
        if self.ser is not None and self.ser.is_open:
            try:
                self._stop_polling()
                self.ser.close()
            except Exception:
                pass
        self.ser = ser
        self._port_name = port_name
        self._baudrate = int(baudrate)
        self._parity = parity
        self._dbits = int(dbits)
        self._sbits = float(sbits)
        self._flow_ctrl = flow_ctrl
        self._start_polling()
        self.state_changed.emit(self.is_open)
        self.port_info_changed.emit(
            port_name, self._baudrate, parity, self._dbits, self._sbits, flow_ctrl
        )

    def _start_polling(self):
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._poll)
        self._timer.start(20)

    def _stop_polling(self):
        if self._timer:
            self._timer.stop()

    def _poll(self):
        if not self.ser or not self.ser.is_open:
            return
        try:
            n = getattr(self.ser, 'in_waiting', 0)
            if n > 0:
                data = self.ser.read(n)
                if data:
                    self._rx_bytes += len(data)
                    self.received.emit(data)
                    self.rx_count_changed.emit(self._rx_bytes)
        except Exception:
            self._err_count += 1
            self.err_count_changed.emit(self._err_count)

    @staticmethod
    def list_ports() -> list:
        """列出可用串口"""
        try:
            import serial.tools.list_ports
            return [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            return []

    @staticmethod
    def list_ports_detail() -> list:
        """列出可用串口（带描述）"""
        try:
            import serial.tools.list_ports
            return [(p.device, p.description) for p in serial.tools.list_ports.comports()]
        except Exception:
            return []

    def close(self):
        """关闭串口"""
        self._stop_polling()
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
        self._port_name = ''
        self._baudrate = 0
        self.state_changed.emit(False)

    def send(self, data: bytes) -> bool:
        """发送数据"""
        if not self.ser or not self.ser.is_open:
            return False
        try:
            n = self.ser.write(data)
            self._tx_bytes += n
            self.sent.emit(n)
            self.tx_count_changed.emit(self._tx_bytes)
            return True
        except Exception:
            self._err_count += 1
            self.err_count_changed.emit(self._err_count)
            return False

    def send_text(self, text: str, encoding: str = 'utf-8',
                  newline: str = '') -> bool:
        """发送文本

        Args:
            text: 文本内容
            encoding: 编码
            newline: 追加换行符 ('', '\\n', '\\r\\n', '\\r')
        """
        data = text.encode(encoding, errors='ignore')
        if newline:
            data += newline.encode('ascii')
        return self.send(data)

    def reset_counts(self):
        self._rx_bytes = 0
        self._tx_bytes = 0
        self._err_count = 0
        self.rx_count_changed.emit(0)
        self.tx_count_changed.emit(0)
        self.err_count_changed.emit(0)

    def set_dtr(self, level: bool):
        """设置 DTR 电平"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.dtr = level
            except Exception:
                pass

    def set_rts(self, level: bool):
        """设置 RTS 电平"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.rts = level
            except Exception:
                pass

    @property
    def is_open(self) -> bool:
        return self.ser is not None and self.ser.is_open

    @property
    def port_name(self) -> str:
        return self._port_name

    @property
    def baudrate(self) -> int:
        return self._baudrate

    @property
    def rx_count(self) -> int:
        return self._rx_bytes

    @property
    def tx_count(self) -> int:
        return self._tx_bytes

    @property
    def err_count(self) -> int:
        return self._err_count

    @property
    def port_info(self) -> dict:
        return {
            'port': self._port_name,
            'baudrate': self._baudrate,
            'parity': self._parity,
            'dbits': self._dbits,
            'sbits': self._sbits,
            'flow_ctrl': self._flow_ctrl,
        }
