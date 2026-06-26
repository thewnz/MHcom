# -*- coding: utf-8 -*-
"""HEX / 文本 转换工具"""
import base64
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox, QComboBox
)


class HexConverterTool(QWidget):
    """HEX / 文本 / Base64 转换工具"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('HEX转换 - MHcom')
        self.resize(720, 560)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('HEX / 文本 转换工具')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        cfg = QGroupBox('  转换设置')
        cfg_lay = QVBoxLayout(cfg)
        cfg_lay.setContentsMargins(12, 10, 12, 12)
        cfg_lay.setSpacing(8)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel('转换方向:'))
        self.cmb_dir = QComboBox()
        self.cmb_dir.addItems(['文本 → HEX', 'HEX → 文本', '文本 → Base64', 'Base64 → 文本'])
        self.cmb_dir.currentIndexChanged.connect(self._on_dir_changed)
        dir_row.addWidget(self.cmb_dir, 1)
        cfg_lay.addLayout(dir_row)

        enc_row = QHBoxLayout()
        enc_row.addWidget(QLabel('字符编码:'))
        self.cmb_enc = QComboBox()
        self.cmb_enc.addItems(['UTF-8', 'GBK', 'ASCII', 'GB2312', 'ISO-8859-1'])
        enc_row.addWidget(self.cmb_enc, 1)
        cfg_lay.addLayout(enc_row)

        layout.addWidget(cfg)

        io_layout = QHBoxLayout()
        io_layout.setSpacing(12)

        left_box = QGroupBox('  输入')
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(10, 8, 10, 10)
        self.txt_in = QPlainTextEdit()
        self.txt_in.setPlaceholderText('在此输入要转换的内容...')
        self.txt_in.setMinimumHeight(200)
        left_lay.addWidget(self.txt_in)
        io_layout.addWidget(left_box, 1)

        right_box = QGroupBox('  输出')
        right_lay = QVBoxLayout(right_box)
        right_lay.setContentsMargins(10, 8, 10, 10)
        self.txt_out = QPlainTextEdit()
        self.txt_out.setReadOnly(True)
        self.txt_out.setPlaceholderText('转换结果将显示在这里...')
        self.txt_out.setMinimumHeight(200)
        right_lay.addWidget(self.txt_out)
        io_layout.addWidget(right_box, 1)

        layout.addLayout(io_layout, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_swap = QPushButton('⇄ 交换输入输出')
        btn_swap.setStyleSheet(
            'padding:6px 16px; border-radius:4px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_swap.clicked.connect(self._swap)
        btn_row.addWidget(btn_swap)

        btn_clear = QPushButton('清空')
        btn_clear.setStyleSheet(
            'padding:6px 16px; border-radius:4px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(btn_clear)

        btn_convert = QPushButton('转换')
        btn_convert.setStyleSheet(
            'padding:6px 20px; border-radius:4px;'
            'background:#3B82F6; color:white; font-weight:600; border:none;'
        )
        btn_convert.clicked.connect(self._convert)
        btn_row.addWidget(btn_convert)

        layout.addLayout(btn_row)

    def _on_dir_changed(self, idx):
        dir_map = {
            0: '在此输入文本...',
            1: '在此输入HEX (如: 48 65 6C 6C 6F)...',
            2: '在此输入文本...',
            3: '在此输入Base64编码...'
        }
        self.txt_in.setPlaceholderText(dir_map.get(idx, ''))

    def _convert(self):
        text = self.txt_in.toPlainText()
        enc_map = {
            'UTF-8': 'utf-8', 'GBK': 'gbk', 'ASCII': 'ascii',
            'GB2312': 'gb2312', 'ISO-8859-1': 'latin-1'
        }
        enc = enc_map.get(self.cmb_enc.currentText(), 'utf-8')
        direction = self.cmb_dir.currentIndex()

        try:
            if direction == 0:
                data = text.encode(enc, errors='replace')
                self.txt_out.setPlainText(' '.join(f'{b:02X}' for b in data))
            elif direction == 1:
                hex_str = text.replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '')
                if len(hex_str) % 2 != 0:
                    hex_str = hex_str[:-1]
                data = bytes.fromhex(hex_str)
                self.txt_out.setPlainText(data.decode(enc, errors='replace'))
            elif direction == 2:
                data = text.encode(enc, errors='replace')
                self.txt_out.setPlainText(base64.b64encode(data).decode('ascii'))
            elif direction == 3:
                data = base64.b64decode(text.strip())
                self.txt_out.setPlainText(data.decode(enc, errors='replace'))
        except Exception as e:
            self.txt_out.setPlainText(f'转换错误: {e}')

    def _swap(self):
        out_text = self.txt_out.toPlainText()
        self.txt_in.setPlainText(out_text)
        self.txt_out.clear()
        current = self.cmb_dir.currentIndex()
        swap_map = {0: 1, 1: 0, 2: 3, 3: 2}
        self.cmb_dir.setCurrentIndex(swap_map.get(current, 0))

    def _clear(self):
        self.txt_in.clear()
        self.txt_out.clear()

    def closeEvent(self, event):
        super().closeEvent(event)

