# -*- coding: utf-8 -*-
"""
Modbus RTU 工具 - 支持串口直连读写
"""
import struct
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox, QComboBox, QSpinBox, QCheckBox,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt5.QtGui import QColor

from core.serial_link import SerialLink
from core.data_bus import DataBus
from core.modbus_rtu import (
    FUNC_READ_COILS, FUNC_READ_DISCRETE, FUNC_READ_HOLDING, FUNC_READ_INPUT,
    FUNC_WRITE_SINGLE_REG,
    build_read_holding_registers, build_read_input_registers,
    build_read_coils, build_write_single_register,
    parse_read_registers_response, parse_write_single_response,
    parse_exception, verify_crc
)


EXCEPTION_CODE_MAP = {
    0x01: '非法功能码',
    0x02: '非法数据地址',
    0x03: '非法数据值',
    0x04: '从站设备故障',
    0x05: '确认',
    0x06: '从站设备忙',
    0x07: '否定确认',
    0x08: '存储器奇偶校验错误',
}


FUNC_MAP = {
    '0x03 读保持寄存器': FUNC_READ_HOLDING,
    '0x04 读输入寄存器': FUNC_READ_INPUT,
    '0x01 读线圈': FUNC_READ_COILS,
    '0x02 读离散输入': FUNC_READ_DISCRETE,
    '0x06 写单寄存器': FUNC_WRITE_SINGLE_REG,
}


class ModbusTool(QWidget):
    """Modbus RTU 工具"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Modbus RTU 工具 - MHcom')
        self.resize(900, 650)

        self._serial = SerialLink.instance()
        self._bus = DataBus.instance()
        self._rx_buffer = b''
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._on_poll)
        # 轮询请求超时计时器：防止设备不响应导致轮询永久停滞
        self._poll_timeout_timer = QTimer(self)
        self._poll_timeout_timer.setSingleShot(True)
        self._poll_timeout_timer.timeout.connect(self._on_poll_timeout)
        self._pending_func = 0
        self._pending_slave = 0
        self._pending_addr = 0
        self._pending_count = 0
        self._rx_buffer_max = 4096  # 接收缓冲区上限，防止噪声数据导致内存泄漏

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(8)

        top = QHBoxLayout()
        self.btn_read = QPushButton('读取')
        self.btn_read.setFixedWidth(80)
        self.btn_read.clicked.connect(self._on_read)
        top.addWidget(self.btn_read)

        self.btn_write = QPushButton('写入')
        self.btn_write.setFixedWidth(80)
        self.btn_write.clicked.connect(self._on_write)
        top.addWidget(self.btn_write)

        top.addSpacing(20)

        self.chk_poll = QCheckBox('轮询')
        top.addWidget(self.chk_poll)
        self.chk_poll.stateChanged.connect(self._on_poll_toggled)

        top.addWidget(QLabel('间隔(ms):'))
        self.spn_interval = QSpinBox()
        self.spn_interval.setRange(100, 60000)
        self.spn_interval.setValue(1000)
        self.spn_interval.setSuffix(' ms')
        self.spn_interval.setFixedWidth(100)
        top.addWidget(self.spn_interval)

        top.addStretch()
        main.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(8)

        cfg = QGroupBox('配置')
        grid = QGridLayout(cfg)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel('从机地址:'), 0, 0)
        self.spn_slave = QSpinBox()
        self.spn_slave.setRange(1, 247)
        self.spn_slave.setValue(1)
        grid.addWidget(self.spn_slave, 0, 1)

        grid.addWidget(QLabel('功能码:'), 1, 0)
        self.cmb_func = QComboBox()
        self.cmb_func.addItems(list(FUNC_MAP.keys()))
        self.cmb_func.currentIndexChanged.connect(self._on_func_changed)
        grid.addWidget(self.cmb_func, 1, 1)

        grid.addWidget(QLabel('寄存器地址:'), 2, 0)
        self.spn_addr = QSpinBox()
        self.spn_addr.setRange(0, 65535)
        self.spn_addr.setValue(0)
        grid.addWidget(self.spn_addr, 2, 1)

        grid.addWidget(QLabel('数量:'), 3, 0)
        self.spn_count = QSpinBox()
        self.spn_count.setRange(1, 125)
        self.spn_count.setValue(10)
        grid.addWidget(self.spn_count, 3, 1)

        self.lbl_value = QLabel('写入值:')
        grid.addWidget(self.lbl_value, 4, 0)
        self.spn_value = QSpinBox()
        self.spn_value.setRange(0, 65535)
        self.spn_value.setValue(0)
        grid.addWidget(self.spn_value, 4, 1)

        left_lay.addWidget(cfg)
        left_lay.addStretch()

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)

        result_box = QGroupBox('结果')
        result_lay = QVBoxLayout(result_box)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['地址', '十进制', '十六进制'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        result_lay.addWidget(self.table)
        right_lay.addWidget(result_box, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 600])
        main.addWidget(splitter, 1)

        log_box = QGroupBox('日志')
        log_lay = QVBoxLayout(log_box)
        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumBlockCount(500)
        self.txt_log.setStyleSheet('font-family: Consolas, monospace; font-size: 12px;')
        log_lay.addWidget(self.txt_log)
        main.addWidget(log_box)

        self._on_func_changed()

    def _connect_signals(self):
        self._serial.received.connect(self._on_serial_rx)
        self._serial.state_changed.connect(self._on_serial_state)

    def _on_func_changed(self):
        func_text = self.cmb_func.currentText()
        is_write = '0x06' in func_text
        self.lbl_value.setVisible(is_write)
        self.spn_value.setVisible(is_write)
        self.spn_count.setVisible(not is_write)
        if is_write:
            self.spn_count.setValue(1)

    def _on_serial_state(self, opened: bool):
        self.btn_read.setEnabled(opened)
        self.btn_write.setEnabled(opened)
        self.chk_poll.setEnabled(opened)
        if not opened:
            self.chk_poll.setChecked(False)

    def _on_serial_rx(self, data: bytes):
        self._rx_buffer += data
        # 缓冲区上限保护：防止噪声数据导致内存无限增长
        if len(self._rx_buffer) > self._rx_buffer_max:
            self._log(f'接收缓冲区超限 ({self._rx_buffer_max}B)，已清空残留数据', 'warn')
            self._rx_buffer = b''
            self._pending_func = 0
            self._poll_timeout_timer.stop()
            return
        self._try_parse_response()

    def _try_parse_response(self):
        if len(self._rx_buffer) < 5:
            return
        slave = self._rx_buffer[0]
        func = self._rx_buffer[1]
        if func & 0x80:
            if len(self._rx_buffer) >= 5:
                if verify_crc(self._rx_buffer[:5]):
                    ex_code = self._rx_buffer[2]
                    self._log(f'异常响应: 从站{slave}, 错误码 0x{ex_code:02X} - {EXCEPTION_CODE_MAP.get(ex_code, "未知错误")}', 'error')
                    self._rx_buffer = self._rx_buffer[5:]
                    self._pending_func = 0
                    return
            return
        if func in (FUNC_READ_HOLDING, FUNC_READ_INPUT):
            if len(self._rx_buffer) >= 3:
                byte_count = self._rx_buffer[2]
                total_len = 3 + byte_count + 2
                if len(self._rx_buffer) >= total_len:
                    frame = self._rx_buffer[:total_len]
                    self._rx_buffer = self._rx_buffer[total_len:]
                    self._handle_read_registers_response(frame)
                    return
        elif func in (FUNC_READ_COILS, FUNC_READ_DISCRETE):
            if len(self._rx_buffer) >= 3:
                byte_count = self._rx_buffer[2]
                total_len = 3 + byte_count + 2
                if len(self._rx_buffer) >= total_len:
                    frame = self._rx_buffer[:total_len]
                    self._rx_buffer = self._rx_buffer[total_len:]
                    self._handle_read_coils_response(frame)
                    return
        elif func == FUNC_WRITE_SINGLE_REG:
            if len(self._rx_buffer) >= 8:
                frame = self._rx_buffer[:8]
                self._rx_buffer = self._rx_buffer[8:]
                self._handle_write_response(frame)
                return

    def _handle_read_registers_response(self, frame: bytes):
        try:
            registers = parse_read_registers_response(frame)
            self._update_table(registers)
            self._log(f'读取成功: {len(registers)} 个寄存器', 'ok')
        except Exception as e:
            self._log(f'解析失败: {e}', 'error')
        self._pending_func = 0
        self._poll_timeout_timer.stop()

    def _handle_read_coils_response(self, frame: bytes):
        try:
            if not verify_crc(frame):
                raise ValueError('CRC校验失败')
            byte_count = frame[2]
            bits = []
            for i in range(byte_count):
                byte = frame[3 + i]
                for bit in range(8):
                    bits.append((byte >> bit) & 1)
            count = self._pending_count
            if count > len(bits):
                count = len(bits)
            self._update_table(bits[:count], is_bits=True)
            self._log(f'读取成功: {count} 个位', 'ok')
        except Exception as e:
            self._log(f'解析失败: {e}', 'error')
        self._pending_func = 0
        self._poll_timeout_timer.stop()

    def _handle_write_response(self, frame: bytes):
        try:
            addr, value = parse_write_single_response(frame)
            self._log(f'写入成功: 地址 {addr}, 值 {value} (0x{value:04X})', 'ok')
        except Exception as e:
            self._log(f'解析失败: {e}', 'error')
        self._pending_func = 0
        self._poll_timeout_timer.stop()

    def _update_table(self, values: list, is_bits: bool = False):
        self.table.setRowCount(len(values))
        base_addr = self._pending_addr
        for i, val in enumerate(values):
            addr_item = QTableWidgetItem(str(base_addr + i))
            addr_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, addr_item)

            dec_item = QTableWidgetItem(str(val))
            dec_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, dec_item)

            if is_bits:
                hex_text = 'ON' if val else 'OFF'
            else:
                hex_text = f'0x{val:04X}'
            hex_item = QTableWidgetItem(hex_text)
            hex_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, hex_item)

    def _on_read(self):
        if not self._serial.is_open:
            self._log('串口未连接', 'error')
            return
        func_text = self.cmb_func.currentText()
        func_code = FUNC_MAP.get(func_text, 0)
        slave = self.spn_slave.value()
        addr = self.spn_addr.value()
        count = self.spn_count.value()

        if func_code in (FUNC_READ_HOLDING, FUNC_READ_INPUT, FUNC_READ_COILS, FUNC_READ_DISCRETE):
            self._send_read_request(slave, func_code, addr, count)
        else:
            self._log('当前功能码不支持读取操作', 'warn')

    def _on_write(self):
        if not self._serial.is_open:
            self._log('串口未连接', 'error')
            return
        func_text = self.cmb_func.currentText()
        func_code = FUNC_MAP.get(func_text, 0)
        slave = self.spn_slave.value()
        addr = self.spn_addr.value()
        value = self.spn_value.value()

        if func_code == FUNC_WRITE_SINGLE_REG:
            req = build_write_single_register(slave, addr, value)
            self._pending_func = func_code
            self._pending_slave = slave
            self._pending_addr = addr
            self._pending_count = 1
            self._rx_buffer = b''
            self._serial.send(req)
            self._poll_timeout_timer.start(2000)  # 2 秒超时保护
            self._log(f'发送写请求: 从站{slave}, 地址{addr}, 值{value} (0x{value:04X})')
            self._log_hex(req)
        else:
            self._log('当前功能码不支持写入操作', 'warn')

    def _send_read_request(self, slave: int, func_code: int, addr: int, count: int):
        if func_code == FUNC_READ_HOLDING:
            req = build_read_holding_registers(slave, addr, count)
        elif func_code == FUNC_READ_INPUT:
            req = build_read_input_registers(slave, addr, count)
        elif func_code == FUNC_READ_COILS:
            req = build_read_coils(slave, addr, count)
        elif func_code == FUNC_READ_DISCRETE:
            req = self._build_read_discrete(slave, addr, count)
        else:
            return

        self._pending_func = func_code
        self._pending_slave = slave
        self._pending_addr = addr
        self._pending_count = count
        self._rx_buffer = b''
        self._serial.send(req)
        self._poll_timeout_timer.start(2000)  # 2 秒超时保护
        func_name = self.cmb_func.currentText()
        self._log(f'发送读请求: {func_name}, 从站{slave}, 地址{addr}, 数量{count}')
        self._log_hex(req)

    def _build_read_discrete(self, slave_id: int, address: int, count: int) -> bytes:
        from core.crc_calculator import crc16_modbus
        frame = struct.pack('>BBHH', slave_id, FUNC_READ_DISCRETE, address, count)
        crc = crc16_modbus(frame)
        return frame + struct.pack('<H', crc)

    def _on_poll_toggled(self, state):
        if state == Qt.Checked:
            interval = self.spn_interval.value()
            self._poll_timer.start(interval)
            self._log(f'轮询已开启, 间隔 {interval}ms', 'ok')
        else:
            self._poll_timer.stop()
            self._log('轮询已关闭', 'warn')

    def _on_poll(self):
        if not self._serial.is_open:
            self.chk_poll.setChecked(False)
            return
        if self._pending_func != 0:
            return
        self._on_read()

    def _on_poll_timeout(self):
        """轮询请求超时处理：清除等待状态，恢复轮询"""
        self._log(f'请求超时（从站 {self._pending_slave}，功能码 0x{self._pending_func:02X}），已放弃等待', 'warn')
        self._rx_buffer = b''
        self._pending_func = 0

    def _log(self, msg: str, level: str = 'info'):
        color_map = {
            'info': '#334155',
            'ok': '#16A34A',
            'warn': '#D97706',
            'error': '#DC2626',
        }
        color = color_map.get(level, '#334155')
        from datetime import datetime
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self.txt_log.appendHtml(f'<span style="color:#94A3B8;">[{ts}]</span> <span style="color:{color};">{msg}</span>')

    def _log_hex(self, data: bytes):
        hex_str = ' '.join(f'{b:02X}' for b in data)
        self._log(f'  TX: {hex_str}', 'info')

    def closeEvent(self, event):
        self._poll_timer.stop()
        self._poll_timeout_timer.stop()
        self._serial.received.disconnect(self._on_serial_rx)
        self._serial.state_changed.disconnect(self._on_serial_state)
        super().closeEvent(event)

