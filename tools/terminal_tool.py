# -*- coding: utf-8 -*-
"""
终端模式工具
- 类Linux终端
- 支持AT指令快捷
- 命令历史记录
"""

from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QPlainTextEdit, QLineEdit, QComboBox
)
from core.data_bus import DataBus
from core.serial_link import SerialLink


class TerminalCmdTool(QWidget):
    """终端模式工具 - 单例模式"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        self.setWindowTitle('终端模式 - MHcom')
        self.resize(820, 560)
        self._history = []
        self._history_idx = -1
        self._build_ui()
        DataBus.instance().raw_received.connect(self._on_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('终端模式')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        cfg_box = QGroupBox('  配置')
        cfg_lay = QHBoxLayout(cfg_box)
        cfg_lay.setContentsMargins(12, 10, 12, 12)
        cfg_lay.setSpacing(12)

        cfg_lay.addWidget(QLabel('换行符:'))
        self.cmb_newline = QComboBox()
        self.cmb_newline.addItems(['\\r\\n (CRLF)', '\\n (LF)', '\\r (CR)', '无'])
        self.cmb_newline.setCurrentIndex(0)
        cfg_lay.addWidget(self.cmb_newline)

        cfg_lay.addWidget(QLabel('编码:'))
        self.cmb_encoding = QComboBox()
        self.cmb_encoding.addItems(['UTF-8', 'GBK', 'ASCII'])
        cfg_lay.addWidget(self.cmb_encoding)

        cfg_lay.addStretch()

        self.lbl_status = QLabel('● 未连接')
        self.lbl_status.setStyleSheet('color:#EF4444; font-weight:600;')
        cfg_lay.addWidget(self.lbl_status)

        layout.addWidget(cfg_box)

        self.txt_term = QPlainTextEdit()
        self.txt_term.setReadOnly(True)
        f = QFont('Consolas')
        f.setStyleHint(QFont.Monospace)
        f.setPointSize(11)
        self.txt_term.setFont(f)
        self.txt_term.setStyleSheet(
            'QPlainTextEdit { background: #0F172A; color: #10B981; '
            'border: 1px solid #1E293B; border-radius: 6px; padding: 8px; }'
        )
        layout.addWidget(self.txt_term, 1)

        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self.lbl_prompt = QLabel('$')
        self.lbl_prompt.setStyleSheet(
            'color: #10B981; font-weight: 600; font-family: Consolas; font-size: 14px;'
        )
        in_row.addWidget(self.lbl_prompt)
        self.txt_input = QLineEdit()
        self.txt_input.setStyleSheet(
            'QLineEdit { background: #1E293B; color: #E5E7EB; '
            'border: 1px solid #334155; border-radius: 6px; '
            'padding: 8px; font-family: Consolas; font-size: 13px; }'
            'QLineEdit:focus { border: 1px solid #3B82F6; }'
        )
        self.txt_input.setPlaceholderText('输入命令，按回车发送（输入 help 查看内置命令）...')
        self.txt_input.returnPressed.connect(self._on_enter)
        self.txt_input.installEventFilter(self)
        in_row.addWidget(self.txt_input, 1)

        btn_clear = QPushButton('清屏')
        btn_clear.setStyleSheet(
            'padding:6px 14px; border-radius:4px;'
            'background:#334155; color:#E5E7EB; border:none;'
        )
        btn_clear.clicked.connect(self.txt_term.clear)
        in_row.addWidget(btn_clear)

        btn_send = QPushButton('发送')
        btn_send.setStyleSheet(
            'padding:6px 18px; border-radius:4px;'
            'background:#3B82F6; color:white; font-weight:600; border:none;'
        )
        btn_send.clicked.connect(self._on_enter)
        in_row.addWidget(btn_send)

        layout.addLayout(in_row)

        self._append('终端模式已启动。输入命令按回车发送。\n', '#94A3B8')
        self._append('可用命令: help, cls, ping, status\n', '#60A5FA')
        self._append('提示: 按 ↑↓ 键浏览历史命令\n\n', '#64748B')

        DataBus.instance().connection_status.connect(self._on_connection)

    def eventFilter(self, obj, event):
        if obj == self.txt_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Up:
                self._history_prev()
                return True
            elif event.key() == Qt.Key_Down:
                self._history_next()
                return True
        return super().eventFilter(obj, event)

    def _history_prev(self):
        if not self._history:
            return
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self.txt_input.setText(self._history[self._history_idx])

    def _history_next(self):
        if self._history_idx > 0:
            self._history_idx -= 1
            self.txt_input.setText(self._history[self._history_idx])
        elif self._history_idx == 0:
            self._history_idx = -1
            self.txt_input.clear()

    def _append(self, text, color='#10B981'):
        self.txt_term.moveCursor(QTextCursor.End)
        fmt = self.txt_term.currentCharFormat()
        fmt.setForeground(QColor(color))
        self.txt_term.setCurrentCharFormat(fmt)
        self.txt_term.insertPlainText(text)
        self.txt_term.moveCursor(QTextCursor.End)

    def _on_enter(self):
        cmd = self.txt_input.text().strip()
        if not cmd:
            return

        if cmd not in self._history or self._history[0] != cmd:
            self._history.insert(0, cmd)
            if len(self._history) > 100:
                self._history = self._history[:100]
        self._history_idx = -1

        if cmd == 'cls' or cmd == 'clear':
            self.txt_term.clear()
            self.txt_input.clear()
            return

        if cmd == 'help':
            self._append('可用命令:\n', '#60A5FA')
            self._append('  help    - 显示帮助信息\n', '#94A3B8')
            self._append('  cls     - 清屏\n', '#94A3B8')
            self._append('  ping    - 测试连接\n', '#94A3B8')
            self._append('  status  - 查看连接状态\n', '#94A3B8')
            self._append('  其他    - 直接发送到串口\n\n', '#94A3B8')
            self.txt_input.clear()
            return

        if cmd == 'ping':
            if SerialLink.instance().is_open:
                self._append('pong - 串口连接正常\n', '#10B981')
            else:
                self._append('未连接到串口\n', '#EF4444')
            self.txt_input.clear()
            return

        if cmd == 'status':
            link = SerialLink.instance()
            if link.is_open:
                self._append(f'串口: {link.port_name} @ {link.baudrate}\n', '#10B981')
                self._append(f'发送: {link.tx_count} 字节\n', '#94A3B8')
                self._append(f'接收: {link.rx_count} 字节\n', '#94A3B8')
                self._append(f'错误: {link.err_count} 次\n\n', '#94A3B8')
            else:
                self._append('未连接到串口\n\n', '#EF4444')
            self.txt_input.clear()
            return

        ts = datetime.now().strftime('%H:%M:%S')
        self._append(f'[{ts}] $ {cmd}\n', '#E5E7EB')

        newline_map = {0: '\r\n', 1: '\n', 2: '\r', 3: ''}
        newline = newline_map.get(self.cmb_newline.currentIndex(), '\r\n')
        enc_map = {'UTF-8': 'utf-8', 'GBK': 'gbk', 'ASCII': 'ascii'}
        enc = enc_map.get(self.cmb_encoding.currentText(), 'utf-8')

        try:
            data = (cmd + newline).encode(enc)
            if not SerialLink.instance().send(data):
                self._append('[发送失败: 串口未连接]\n', '#EF4444')
            else:
                DataBus.instance().publish_serial_tx(data)
        except Exception as e:
            self._append(f'[发送错误: {e}]\n', '#EF4444')

        self.txt_input.clear()

    def _on_data(self, data: bytes):
        try:
            enc_map = {'UTF-8': 'utf-8', 'GBK': 'gbk', 'ASCII': 'ascii'}
            enc = enc_map.get(self.cmb_encoding.currentText(), 'utf-8')
            text = data.decode(enc, errors='replace')
        except Exception:
            text = repr(data)
        self._append(text, '#10B981')

    def _on_connection(self, connected, info):
        if connected:
            self.lbl_status.setText(f'● {info}')
            self.lbl_status.setStyleSheet('color:#10B981; font-weight:600;')
        else:
            self.lbl_status.setText('● 未连接')
            self.lbl_status.setStyleSheet('color:#EF4444; font-weight:600;')

    def closeEvent(self, e):
        try:
            DataBus.instance().raw_received.disconnect(self._on_data)
            DataBus.instance().connection_status.disconnect(self._on_connection)
        except Exception:
            pass
        super().closeEvent(e)

