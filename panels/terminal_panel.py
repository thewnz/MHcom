# -*- coding: utf-8 -*-
"""
高级串口助手面板（模式B）
- 完整的串口配置（含流控、自定义波特率）
- 收发分色显示、行号、暂停显示、查找
- 发送增强：自增、校验附加、换行模式、定时发送
- 快捷命令、发送历史
- 文件发送/保存
"""
import os
from collections import deque
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QLabel, QComboBox, QPushButton, QPlainTextEdit, QCheckBox,
    QSpinBox, QLineEdit, QListWidget, QFileDialog, QMessageBox,
    QGridLayout, QTabWidget, QInputDialog, QShortcut
)
from PyQt5.QtGui import QKeySequence

from core.serial_link import SerialLink, SerialOpenWorker
from core.data_bus import DataBus
from core.tool_manager import ToolManager
from config.settings import AppConfig


class TerminalPanel(QWidget):
    """高级串口助手主面板"""

    request_tool = pyqtSignal(str)

    MAX_RX_LINES = 5000
    MAX_HISTORY = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.slink = SerialLink.instance()
        self.bus = DataBus.instance()
        self.config = AppConfig()

        self._rx_lines = deque(maxlen=self.MAX_RX_LINES)
        self._send_history = []
        self._auto_timer = None
        self._cycle_idx = 0
        self._cycle_timer = None
        self._increment_counter = 0
        self._pause_display = False
        self._open_thread = None
        self._open_worker = None
        self._send_file_thread = None
        self._send_file_abort = False

        self._build_ui()
        self._wire_signals()
        self._refresh_ports()
        self._load_macros()
        self._load_history()
        self._sync_ui_from_serial()

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # 顶部：串口配置栏
        cfg = self._build_config_bar()
        root.addWidget(cfg)

        # 主体：左右分割
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧：接收 + 发送 + Tab
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)

        # 接收区
        rx_box = QGroupBox(' 接收区 ')
        rx_lay = QVBoxLayout(rx_box)
        rx_lay.setContentsMargins(8, 6, 8, 8)
        rx_lay.setSpacing(4)

        rx_tools = QHBoxLayout()
        rx_tools.setSpacing(6)
        self.chk_pause = QCheckBox('暂停显示')
        self.chk_pause.stateChanged.connect(self._on_pause_toggle)
        rx_tools.addWidget(self.chk_pause)

        self.chk_show_tx = QCheckBox('显示发送')
        self.chk_show_tx.setChecked(True)
        rx_tools.addWidget(self.chk_show_tx)

        self.chk_linenum = QCheckBox('行号')
        rx_tools.addWidget(self.chk_linenum)

        self.chk_timestamp = QCheckBox('时间戳')
        rx_tools.addWidget(self.chk_timestamp)

        rx_tools.addWidget(QLabel('编码:'))
        self.cmb_encoding = QComboBox()
        self.cmb_encoding.addItems(['UTF-8', 'GBK', 'GB2312', 'GB18030', 'ASCII', 'ISO-8859-1', 'Big5'])
        self.cmb_encoding.setMaximumWidth(90)
        self.cmb_encoding.setCurrentText('UTF-8')
        rx_tools.addWidget(self.cmb_encoding)

        self.edt_find = QLineEdit()
        self.edt_find.setPlaceholderText('查找...')
        self.edt_find.setMaximumWidth(140)
        self.edt_find.returnPressed.connect(self._find_text)
        rx_tools.addWidget(self.edt_find)

        btn_find = QPushButton('查找')
        btn_find.setMaximumWidth(60)
        btn_find.clicked.connect(self._find_text)
        rx_tools.addWidget(btn_find)

        rx_tools.addStretch()

        btn_clear_rx = QPushButton('清空')
        btn_clear_rx.setMaximumWidth(60)
        btn_clear_rx.clicked.connect(self._clear_rx)
        rx_tools.addWidget(btn_clear_rx)

        btn_save = QPushButton('保存')
        btn_save.setMaximumWidth(60)
        btn_save.clicked.connect(self._save_rx)
        rx_tools.addWidget(btn_save)

        rx_lay.addLayout(rx_tools)

        self.txt_rx = QPlainTextEdit()
        self.txt_rx.setReadOnly(True)
        self.txt_rx.setMaximumBlockCount(self.MAX_RX_LINES)
        font = QFont('Consolas', 10)
        font.setStyleHint(QFont.Monospace)
        self.txt_rx.setFont(font)
        rx_lay.addWidget(self.txt_rx)

        left_lay.addWidget(rx_box, 3)

        # 发送区 + 快捷命令 Tab
        self.tab_bottom = QTabWidget()
        self.tab_bottom.addTab(self._build_send_tab(), '发送')
        self.tab_bottom.addTab(self._build_macro_tab(), '快捷命令')
        self.tab_bottom.addTab(self._build_history_tab(), '发送历史')
        left_lay.addWidget(self.tab_bottom, 2)
        root.addWidget(left, 1)

        # 状态栏
        status = QHBoxLayout()
        status.setSpacing(12)
        self.lbl_port_status = QLabel('● 未连接')
        self.lbl_port_status.setStyleSheet('color:#EF4444; font-weight:600;')
        status.addWidget(self.lbl_port_status)

        self.lbl_rx_cnt = QLabel('RX: 0')
        status.addWidget(self.lbl_rx_cnt)

        self.lbl_tx_cnt = QLabel('TX: 0')
        status.addWidget(self.lbl_tx_cnt)

        status.addStretch()
        root.addLayout(status)

    def _build_config_bar(self) -> QWidget:
        bar = QGroupBox(' 串口配置 ')
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 6, 10, 8)
        lay.setSpacing(8)

        lay.addWidget(QLabel('端口:'))
        self.cmb_port = QComboBox()
        self.cmb_port.setMinimumWidth(100)
        lay.addWidget(self.cmb_port)

        btn_refresh = QPushButton('刷新')
        btn_refresh.setMaximumWidth(55)
        btn_refresh.clicked.connect(self._refresh_ports)
        lay.addWidget(btn_refresh)

        lay.addWidget(QLabel('波特率:'))
        self.cmb_baud = QComboBox()
        self.cmb_baud.setEditable(True)
        self.cmb_baud.addItems([
            '9600', '19200', '38400', '57600', '115200',
            '230400', '460800', '921600'
        ])
        self.cmb_baud.setCurrentText('115200')
        self.cmb_baud.setMinimumWidth(100)
        lay.addWidget(self.cmb_baud)

        lay.addWidget(QLabel('数据位:'))
        self.cmb_data = QComboBox()
        self.cmb_data.addItems(['8', '7', '6', '5'])
        self.cmb_data.setCurrentIndex(0)
        self.cmb_data.setMaximumWidth(60)
        lay.addWidget(self.cmb_data)

        lay.addWidget(QLabel('校验:'))
        self.cmb_parity = QComboBox()
        self.cmb_parity.addItems(['无', '奇', '偶', 'Mark', 'Space'])
        self.cmb_parity.setMaximumWidth(70)
        lay.addWidget(self.cmb_parity)

        lay.addWidget(QLabel('停止位:'))
        self.cmb_stop = QComboBox()
        self.cmb_stop.addItems(['1', '1.5', '2'])
        self.cmb_stop.setMaximumWidth(60)
        lay.addWidget(self.cmb_stop)

        lay.addWidget(QLabel('流控:'))
        self.cmb_flow = QComboBox()
        self.cmb_flow.addItems(['无', 'RTS/CTS', 'XON/XOFF', 'DSR/DTR'])
        self.cmb_flow.setMaximumWidth(90)
        lay.addWidget(self.cmb_flow)

        lay.addSpacing(8)
        self.btn_toggle = QPushButton('打开串口')
        self.btn_toggle.setMinimumWidth(90)
        self.btn_toggle.setStyleSheet(
            'background:#10B981; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        self.btn_toggle.clicked.connect(self._toggle_port)
        lay.addWidget(self.btn_toggle)

        lay.addStretch()
        return bar

    def _build_send_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        # 发送输入
        self.txt_tx = QPlainTextEdit()
        self.txt_tx.setPlaceholderText('输入发送内容...')
        self.txt_tx.setMaximumHeight(80)
        font = QFont('Consolas', 10)
        font.setStyleHint(QFont.Monospace)
        self.txt_tx.setFont(font)
        lay.addWidget(self.txt_tx)

        # 发送选项
        opt = QHBoxLayout()
        opt.setSpacing(8)

        self.chk_hex_send = QCheckBox('HEX发送')
        opt.addWidget(self.chk_hex_send)

        self.chk_newline = QCheckBox('追加换行')
        self.cmb_newline = QComboBox()
        self.cmb_newline.addItems(['\\r\\n', '\\n', '\\r', '无'])
        self.cmb_newline.setMaximumWidth(70)
        opt.addWidget(self.chk_newline)
        opt.addWidget(self.cmb_newline)

        self.chk_crc = QCheckBox('附加校验')
        self.cmb_crc = QComboBox()
        self.cmb_crc.addItems(['CRC16 Modbus', 'CRC16 CCITT', 'Sum8', 'XOR8'])
        self.cmb_crc.setMaximumWidth(110)
        opt.addWidget(self.chk_crc)
        opt.addWidget(self.cmb_crc)

        opt.addStretch()
        lay.addLayout(opt)

        # 自增 + 定时发送
        opt2 = QHBoxLayout()
        opt2.setSpacing(8)

        self.chk_increment = QCheckBox('自增')
        opt2.addWidget(self.chk_increment)

        self.spn_inc_val = QSpinBox()
        self.spn_inc_val.setRange(0, 999999)
        self.spn_inc_val.setValue(1)
        self.spn_inc_val.setMaximumWidth(80)
        opt2.addWidget(QLabel('步长:'))
        opt2.addWidget(self.spn_inc_val)

        self.chk_auto = QCheckBox('定时发送')
        opt2.addWidget(self.chk_auto)

        self.spn_interval = QSpinBox()
        self.spn_interval.setRange(1, 60000)
        self.spn_interval.setValue(1000)
        self.spn_interval.setSuffix(' ms')
        self.spn_interval.setMaximumWidth(90)
        opt2.addWidget(self.spn_interval)

        opt2.addStretch()
        lay.addLayout(opt2)

        # 发送按钮
        btn_row = QHBoxLayout()
        btn_send = QPushButton('发送 (Ctrl+Enter)')
        btn_send.setStyleSheet(
            'background:#3B82F6; color:white; font-weight:600;'
            'padding:6px 20px; border-radius:4px;'
        )
        btn_send.clicked.connect(self._do_send)
        btn_row.addWidget(btn_send)

        btn_send_file = QPushButton('发送文件')
        btn_send_file.clicked.connect(self._send_file)
        btn_row.addWidget(btn_send_file)

        btn_send_file_hex = QPushButton('HEX发送文件')
        btn_send_file_hex.clicked.connect(lambda: self._send_file(hex_mode=True))
        btn_row.addWidget(btn_send_file_hex)

        btn_cycle = QPushButton('循环发送列表')
        btn_cycle.setCheckable(True)
        btn_cycle.clicked.connect(self._toggle_cycle)
        btn_row.addWidget(btn_cycle)

        btn_row.addStretch()

        self.lbl_send_stat = QLabel('')
        self.lbl_send_stat.setStyleSheet('color:#64748B;')
        btn_row.addWidget(self.lbl_send_stat)

        lay.addLayout(btn_row)

        # 快捷键
        sc = QShortcut(QKeySequence('Ctrl+Return'), self)
        sc.activated.connect(self._do_send)

        return w

    def _build_macro_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        self.lst_macros = QListWidget()
        self.lst_macros.itemDoubleClicked.connect(self._on_macro_doubleclick)
        lay.addWidget(self.lst_macros, 1)

        btn_row = QHBoxLayout()
        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self._add_macro)
        btn_row.addWidget(btn_add)

        btn_edit = QPushButton('编辑')
        btn_edit.clicked.connect(self._edit_macro)
        btn_row.addWidget(btn_edit)

        btn_del = QPushButton('删除')
        btn_del.clicked.connect(self._del_macro)
        btn_row.addWidget(btn_del)

        btn_mgr = QPushButton('管理器')
        btn_mgr.clicked.connect(lambda: self.request_tool.emit('macro_editor'))
        btn_row.addWidget(btn_mgr)

        lay.addLayout(btn_row)
        return w

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        self.lst_history = QListWidget()
        self.lst_history.itemDoubleClicked.connect(self._on_history_doubleclick)
        lay.addWidget(self.lst_history, 1)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton('清空历史')
        btn_clear.clicked.connect(self._clear_history)
        btn_row.addWidget(btn_clear)

        btn_mgr = QPushButton('历史工具')
        btn_mgr.clicked.connect(lambda: self.request_tool.emit('history'))
        btn_row.addWidget(btn_mgr)

        btn_row.addStretch()
        lay.addLayout(btn_row)
        return w

    # ------------------------------------------------------------- 信号
    def _wire_signals(self):
        self.slink.received.connect(self._on_rx_data)
        self.slink.sent.connect(self._on_tx_done)
        self.slink.state_changed.connect(self._on_state_changed)
        self.slink.rx_count_changed.connect(self._on_rx_count)
        self.slink.tx_count_changed.connect(self._on_tx_count)
        self.slink.err_count_changed.connect(self._on_err_count)

        self.chk_auto.stateChanged.connect(self._on_auto_changed)
        self.chk_pause.stateChanged.connect(self._on_pause_toggle)

    def _sync_ui_from_serial(self):
        """根据当前串口状态同步UI"""
        if self.slink.is_open:
            self._update_ui_opened(self.slink.port_name, self.slink.baudrate)
            self.lbl_rx_cnt.setText(f'RX: {self.slink.rx_count}')
            self.lbl_tx_cnt.setText(f'TX: {self.slink.tx_count}')
        else:
            self._update_ui_closed()

    # -------------------------------------------------------- 串口操作
    def _refresh_ports(self):
        self.cmb_port.clear()
        ports = SerialLink.list_ports()
        self.cmb_port.addItems(ports)

    def _toggle_port(self):
        if self.slink.is_open:
            self.slink.close()
            self.bus.publish_serial_closed()
        else:
            port = self.cmb_port.currentText().strip()
            if not port:
                QMessageBox.warning(self, '提示', '请选择串口')
                return
            try:
                baud = int(self.cmb_baud.currentText())
            except ValueError:
                QMessageBox.warning(self, '提示', '波特率无效')
                return

            dbits = int(self.cmb_data.currentText())
            sbits = self.cmb_stop.currentText()
            parity = self.cmb_parity.currentText()
            flow = self.cmb_flow.currentText()

            rtscts = (flow == 'RTS/CTS')
            xonxoff = (flow == 'XON/XOFF')
            dsrdtr = (flow == 'DSR/DTR')

            self.btn_toggle.setEnabled(False)
            self.btn_toggle.setText('打开中...')

            self._open_thread = QThread()
            self._open_worker = SerialOpenWorker(
                port=port, baud=baud, dbits=dbits, sbits=sbits,
                parity=parity, rtscts=rtscts, xonxoff=xonxoff,
                dsrdtr=dsrdtr
            )
            self._open_worker.moveToThread(self._open_thread)
            self._open_thread.started.connect(self._open_worker.run)
            self._open_worker.ok.connect(
                lambda ser: self._on_open_ok(ser, port, baud, parity, dbits, sbits, flow)
            )
            self._open_worker.fail.connect(self._on_open_fail)
            self._open_worker.ok.connect(self._open_thread.quit)
            self._open_worker.fail.connect(self._open_thread.quit)
            self._open_thread.finished.connect(self._open_worker.deleteLater)
            self._open_thread.finished.connect(self._open_thread.deleteLater)
            self._open_thread.start()

    def _on_open_ok(self, ser, port, baud, parity, dbits, sbits, flow):
        self.slink.set_serial(ser, port, baud, parity, dbits, sbits, flow)
        self.bus.publish_serial_opened(port, baud)
        self._update_ui_opened(port, baud)

    def _on_open_fail(self, msg: str):
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText('打开串口')
        self.btn_toggle.setStyleSheet(
            'background:#10B981; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        QMessageBox.critical(self, '打开失败', msg)

    def _update_ui_opened(self, port: str, baud: int):
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText('关闭串口')
        self.btn_toggle.setStyleSheet(
            'background:#EF4444; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        self.lbl_port_status.setText(f'● {port} @ {baud}')
        self.lbl_port_status.setStyleSheet('color:#10B981; font-weight:600;')

    def _update_ui_closed(self):
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText('打开串口')
        self.btn_toggle.setStyleSheet(
            'background:#10B981; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        self.lbl_port_status.setText('● 未连接')
        self.lbl_port_status.setStyleSheet('color:#EF4444; font-weight:600;')

    def _on_state_changed(self, opened: bool):
        if not opened:
            self._update_ui_closed()

    def _on_rx_count(self, n: int):
        self.lbl_rx_cnt.setText(f'RX: {n}')

    def _on_tx_count(self, n: int):
        self.lbl_tx_cnt.setText(f'TX: {n}')

    def _on_err_count(self, n: int):
        pass

    # -------------------------------------------------------- 接收处理
    def _on_rx_data(self, data: bytes):
        self.bus.publish_serial_rx(data)
        if self._pause_display:
            return
        encoding = self.cmb_encoding.currentText()
        try:
            text = data.decode(encoding, errors='replace')
        except Exception:
            text = ' '.join(f'{b:02X}' for b in data)

        ts = ''
        if self.chk_timestamp.isChecked():
            from datetime import datetime
            ts = datetime.now().strftime('%H:%M:%S.%f')[:-3] + ' '

        prefix = ''
        if self.chk_linenum.isChecked():
            self._line_num = getattr(self, '_line_num', 0) + 1
            prefix = f'[{self._line_num:5d}] '

        self._append_colored(ts + prefix + text, QColor('#059669'))

        if self.txt_rx.blockCount() > self.MAX_RX_LINES:
            cursor = self.txt_rx.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()

    def _on_tx_done(self, n: int):
        self.lbl_send_stat.setText(f'已发送 {n} 字节')

    def _append_colored(self, text: str, color: QColor):
        cursor = self.txt_rx.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.txt_rx.setTextCursor(cursor)
        self.txt_rx.ensureCursorVisible()

    def _on_pause_toggle(self, state):
        self._pause_display = (state == Qt.Checked)

    def _clear_rx(self):
        self.txt_rx.clear()
        self._line_num = 0

    def _save_rx(self):
        text = self.txt_rx.toPlainText()
        if not text:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, '保存接收数据', '', '文本文件 (*.txt);;所有文件 (*.*)'
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, '成功', f'已保存到:\n{path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'保存失败: {e}')

    def _find_text(self):
        text = self.edt_find.text().strip()
        if not text:
            return
        if not self.txt_rx.find(text):
            self.txt_rx.moveCursor(QTextCursor.Start)
            self.txt_rx.find(text)

    # -------------------------------------------------------- 发送处理
    def _do_send(self):
        if not self.slink.is_open:
            QMessageBox.warning(self, '提示', '请先打开串口')
            return

        content = self.txt_tx.toPlainText()
        if not content:
            return

        is_hex = self.chk_hex_send.isChecked()
        encoding = self.cmb_encoding.currentText()
        data = b''
        try:
            if is_hex:
                parts = content.replace(',', ' ').replace('\n', ' ').split()
                data = bytes(int(p, 16) for p in parts if p)
            else:
                data = content.encode(encoding, errors='replace')
        except ValueError as e:
            QMessageBox.warning(self, '错误', f'数据格式错误: {e}')
            return

        if self.chk_newline.isChecked() and not is_hex:
            nl_map = {'\\r\\n': '\r\n', '\\n': '\n', '\\r': '\r', '无': ''}
            nl = nl_map.get(self.cmb_newline.currentText(), '')
            data += nl.encode('ascii')

        if self.chk_crc.isChecked():
            data = self._append_crc(data)

        if self.chk_increment.isChecked() and not is_hex:
            try:
                counter_str = str(self._increment_counter)
                data = data + counter_str.encode(encoding, errors='replace')
                self._increment_counter += self.spn_inc_val.value()
            except Exception:
                pass

        if data:
            ok = self.slink.send(data)
            if ok:
                self.bus.publish_serial_tx(data)
                self._add_to_history(content, is_hex)
                if self.chk_show_tx.isChecked():
                    try:
                        tx_text = data.decode('utf-8', errors='replace')
                    except Exception:
                        tx_text = ' '.join(f'{b:02X}' for b in data)
                    self._append_colored(f'\n→ {tx_text}\n', QColor('#3B82F6'))
            else:
                QMessageBox.warning(self, '错误', '发送失败')

    def _append_crc(self, data: bytes) -> bytes:
        alg = self.cmb_crc.currentText()
        try:
            if 'Modbus' in alg:
                from core.crc_calculator import crc16_modbus
                crc = crc16_modbus(data)
                return data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
            elif 'CCITT' in alg:
                from core.crc_calculator import crc16_ccitt
                crc = crc16_ccitt(data)
                return data + bytes([(crc >> 8) & 0xFF, crc & 0xFF])
            elif 'Sum8' in alg:
                from core.crc_calculator import sum8
                s = sum8(data)
                return data + bytes([s & 0xFF])
            elif 'XOR8' in alg:
                from core.crc_calculator import xor8
                x = xor8(data)
                return data + bytes([x & 0xFF])
        except Exception:
            pass
        return data

    def _send_file(self, hex_mode=False):
        if not self.slink.is_open:
            QMessageBox.warning(self, '提示', '请先打开串口')
            return
        
        path, _ = QFileDialog.getOpenFileName(
            self, '选择发送文件', '', '所有文件 (*.*)'
        )
        if not path:
            return
        
        try:
            with open(path, 'rb') as f:
                raw_data = f.read()
            if not raw_data:
                QMessageBox.warning(self, '提示', '文件为空')
                return
        except Exception as e:
            QMessageBox.critical(self, '错误', f'读取文件失败: {e}')
            return
        
        if hex_mode:
            hex_str = ' '.join(f'{b:02X}' for b in raw_data)
            encoding = self.cmb_encoding.currentText()
            try:
                parts = hex_str.replace(',', ' ').replace('\n', ' ').split()
                send_data = bytes(int(p, 16) for p in parts if p)
            except ValueError:
                QMessageBox.warning(self, '错误', 'HEX格式转换失败')
                return
        else:
            send_data = raw_data
        
        total_size = len(send_data)
        chunk_size = 1024
        chunks = (total_size + chunk_size - 1) // chunk_size
        
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog('正在发送文件...', '取消', 0, chunks, self)
        progress.setWindowTitle('发送文件')
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        
        self._send_file_abort = False
        
        for i in range(chunks):
            if self._send_file_abort or progress.wasCanceled():
                self._send_file_abort = True
                QMessageBox.information(self, '取消', '发送已取消')
                return
            
            start = i * chunk_size
            end = min(start + chunk_size, total_size)
            chunk = send_data[start:end]
            
            if not self.slink.is_open:
                QMessageBox.warning(self, '提示', '串口已关闭')
                return
            
            ok = self.slink.send(chunk)
            if ok:
                self.bus.publish_serial_tx(chunk)
            else:
                QMessageBox.warning(self, '错误', f'第 {i+1} 块发送失败')
                return
            
            progress.setValue(i + 1)
            progress.setLabelText(f'发送中... {end}/{total_size} 字节 ({(end/total_size)*100:.1f}%)')
            
            import time
            time.sleep(0.001)
        
        progress.close()
        QMessageBox.information(self, '完成', f'已发送 {total_size} 字节')

    # 定时发送
    def _on_auto_changed(self, state):
        if self._auto_timer is None:
            self._auto_timer = QTimer(self)
            self._auto_timer.timeout.connect(self._do_send)
        if state == Qt.Checked:
            self._auto_timer.start(self.spn_interval.value())
        else:
            self._auto_timer.stop()

    def _toggle_cycle(self, checked: bool):
        macros = self.config.get_macros()
        if checked:
            if not macros:
                QMessageBox.information(self, '提示', '快捷命令列表为空')
                self.sender().setChecked(False)
                return
            self._cycle_idx = 0
            if self._cycle_timer is None:
                self._cycle_timer = QTimer(self)
                self._cycle_timer.timeout.connect(self._cycle_send_next)
            self._cycle_timer.start(self.spn_interval.value())
        else:
            if self._cycle_timer:
                self._cycle_timer.stop()

    def _cycle_send_next(self):
        if not self.slink.is_open:
            return
        macros = self.config.get_macros()
        if not macros:
            return
        item = macros[self._cycle_idx % len(macros)]
        self._cycle_idx += 1
        text = item.get('content', '')
        if text:
            self._send_macro_text(text)

    # -------------------------------------------------------- 快捷命令
    def _load_macros(self):
        self.lst_macros.clear()
        for m in self.config.get_macros():
            self.lst_macros.addItem(m.get('name', ''))

    def _add_macro(self):
        name, ok = QInputDialog.getText(self, '添加命令', '名称:')
        if not ok or not name:
            return
        content, ok = QInputDialog.getMultiLineText(self, '添加命令', '内容:', '')
        if not ok:
            return
        macros = self.config.get_macros()
        macros.append({'name': name, 'content': content})
        self.config.set_macros(macros)
        self._load_macros()

    def _edit_macro(self):
        row = self.lst_macros.currentRow()
        if row < 0:
            return
        macros = self.config.get_macros()
        if row >= len(macros):
            return
        item = macros[row]
        new_name, ok = QInputDialog.getText(self, '编辑', '名称:', text=item.get('name', ''))
        if not ok:
            return
        new_content, ok = QInputDialog.getMultiLineText(
            self, '编辑', '内容:', item.get('content', '')
        )
        if not ok:
            return
        macros[row] = {'name': new_name, 'content': new_content}
        self.config.set_macros(macros)
        self._load_macros()

    def _del_macro(self):
        row = self.lst_macros.currentRow()
        if row < 0:
            return
        macros = self.config.get_macros()
        if row < len(macros):
            macros.pop(row)
            self.config.set_macros(macros)
            self._load_macros()

    def _on_macro_doubleclick(self, item):
        row = self.lst_macros.row(item)
        macros = self.config.get_macros()
        if row < len(macros):
            text = macros[row].get('content', '')
            if text:
                self._send_macro_text(text)

    def _send_macro_text(self, text: str):
        if not self.slink.is_open:
            QMessageBox.warning(self, '提示', '请先打开串口')
            return
        try:
            encoding = self.cmb_encoding.currentText()
            data = text.encode(encoding, errors='replace')
            if self.chk_newline.isChecked():
                nl_map = {'\\r\\n': '\r\n', '\\n': '\n', '\\r': '\r', '无': ''}
                nl = nl_map.get(self.cmb_newline.currentText(), '')
                data += nl.encode('ascii')
            self.slink.send(data)
            self.bus.publish_serial_tx(data)
            if self.chk_show_tx.isChecked():
                self._append_colored(f'\n→ {text}\n', QColor('#3B82F6'))
        except Exception as e:
            QMessageBox.warning(self, '错误', str(e))

    # -------------------------------------------------------- 发送历史
    def _add_to_history(self, content: str, is_hex: bool):
        prefix = '[HEX] ' if is_hex else ''
        line = content.split('\n')[0][:80]
        entry = prefix + line
        self._send_history.insert(0, entry)
        if len(self._send_history) > self.MAX_HISTORY:
            self._send_history = self._send_history[:self.MAX_HISTORY]
        self._refresh_history_list()

    def _load_history(self):
        try:
            h = self.config.get('send_history', '').split('|||')
            self._send_history = [x for x in h if x][:self.MAX_HISTORY]
        except Exception:
            self._send_history = []
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.lst_history.clear()
        for h in self._send_history:
            self.lst_history.addItem(h)

    def _on_history_doubleclick(self, item):
        text = item.text()
        if text.startswith('[HEX] '):
            self.chk_hex_send.setChecked(True)
            text = text[6:]
        else:
            self.chk_hex_send.setChecked(False)
        self.txt_tx.setPlainText(text)
        self.tab_bottom.setCurrentIndex(0)

    def _clear_history(self):
        self._send_history = []
        self._refresh_history_list()
        self.config.set('send_history', '')

    # ------------------------------------------------------------- 其它
    def closeEvent(self, e):
        if self._auto_timer:
            self._auto_timer.stop()
        if self._cycle_timer:
            self._cycle_timer.stop()
        super().closeEvent(e)
