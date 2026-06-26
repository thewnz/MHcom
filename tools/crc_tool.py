# -*- coding: utf-8 -*-
"""CRC / 校验和计算器 - 增强版"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox, QComboBox, QGridLayout, QApplication
)
from core.crc_calculator import ALGORITHMS


PRESETS = {
    'Modbus 读保持寄存器 (01 03 00 00 00 0A)': '01 03 00 00 00 0A',
    'Modbus 读输入寄存器 (02 04 00 00 00 04)': '02 04 00 00 00 04',
    '简单测试 (01 02 03 04 05 06 07 08)': '01 02 03 04 05 06 07 08',
    '全零测试 (00 00 00 00)': '00 00 00 00',
    '全FF测试 (FF FF FF FF)': 'FF FF FF FF',
}


def _hex_to_bytes(text: str) -> bytes:
    return bytes(int(p, 16) for p in text.split() if p)


def _bytes_to_hex(data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in data)


class CrcTool(QWidget):
    """CRC / 校验计算器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('CRC/校验计算器 - MHcom')
        self.resize(820, 580)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(10)
        right = QVBoxLayout()
        right.setSpacing(10)

        self._build_input(left)
        self._build_presets(left)
        self._build_result(right)

        top.addLayout(left, 1)
        top.addLayout(right, 1)

        outer.addLayout(top, 1)
        outer.addWidget(self._build_verify())

    def _build_input(self, parent):
        box = QGroupBox('  输入')
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(6)

        lay.addWidget(QLabel('HEX 数据 (空格分隔):'))
        self.txt_in = QPlainTextEdit()
        self.txt_in.setMaximumHeight(90)
        self.txt_in.setPlaceholderText('例如: 01 03 00 00 00 0A')
        lay.addWidget(self.txt_in)

        row = QHBoxLayout()
        row.addWidget(QLabel('算法:'))
        self.cmb_alg = QComboBox()
        self.cmb_alg.addItems(list(ALGORITHMS.keys()))
        row.addWidget(self.cmb_alg, 1)
        lay.addLayout(row)

        btn_row = QHBoxLayout()
        btn_calc = QPushButton('计算')
        btn_calc.setStyleSheet(
            'background:#3B82F6; color:white; padding:6px 14px;'
            'border-radius:4px; font-weight:600;'
        )
        btn_calc.clicked.connect(self._calc)
        btn_row.addWidget(btn_calc)

        btn_append = QPushButton('追加结果')
        btn_append.clicked.connect(self._append_result)
        btn_row.addWidget(btn_append)

        btn_clear = QPushButton('清空')
        btn_clear.clicked.connect(lambda: self.txt_in.clear())
        btn_row.addWidget(btn_clear)

        lay.addLayout(btn_row)
        parent.addWidget(box)

    def _build_result(self, parent):
        box = QGroupBox('  计算结果')
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(6)

        self.txt_out = QPlainTextEdit()
        self.txt_out.setReadOnly(True)
        self.txt_out.setStyleSheet(
            'background:#F8FAFC; font-family:Consolas; font-size:13px;'
        )
        lay.addWidget(self.txt_out, 1)

        btn_row = QHBoxLayout()
        btn_copy_hex = QPushButton('复制 HEX')
        btn_copy_hex.clicked.connect(lambda: self._copy('hex'))
        btn_row.addWidget(btn_copy_hex)

        btn_copy_dec = QPushButton('复制十进制')
        btn_copy_dec.clicked.connect(lambda: self._copy('dec'))
        btn_row.addWidget(btn_copy_dec)

        btn_copy_all = QPushButton('复制全部')
        btn_copy_all.clicked.connect(lambda: self._copy('all'))
        btn_row.addWidget(btn_copy_all)

        lay.addLayout(btn_row)
        parent.addWidget(box)

    def _build_presets(self, parent):
        box = QGroupBox('  常用预设')
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(4)

        for name, data in PRESETS.items():
            btn = QPushButton(name)
            btn.setStyleSheet('text-align:left; padding:5px 10px;')
            btn.clicked.connect(lambda checked, d=data: self.txt_in.setPlainText(d))
            lay.addWidget(btn)

        parent.addWidget(box)

    def _build_verify(self):
        box = QGroupBox('  校验验证')
        lay = QGridLayout(box)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(6)

        lay.addWidget(QLabel('数据 + 校验值 (HEX):'), 0, 0)
        self.txt_verify = QPlainTextEdit()
        self.txt_verify.setMaximumHeight(55)
        self.txt_verify.setPlaceholderText('例如: 01 03 00 00 00 0A C5 CD')
        lay.addWidget(self.txt_verify, 0, 1, 1, 3)

        lay.addWidget(QLabel('算法:'), 1, 0)
        self.cmb_verify_alg = QComboBox()
        self.cmb_verify_alg.addItems(list(ALGORITHMS.keys()))
        lay.addWidget(self.cmb_verify_alg, 1, 1)

        btn_verify = QPushButton('验证')
        btn_verify.setStyleSheet(
            'background:#10B981; color:white; padding:5px 14px;'
            'border-radius:4px; font-weight:600;'
        )
        btn_verify.clicked.connect(self._verify)
        lay.addWidget(btn_verify, 1, 2)

        self.lbl_verify_result = QLabel('')
        self.lbl_verify_result.setStyleSheet('font-weight:600;')
        lay.addWidget(self.lbl_verify_result, 1, 3)

        lay.setColumnStretch(1, 1)
        return box

    def _calc(self):
        text = self.txt_in.toPlainText().strip()
        if not text:
            self.txt_out.setPlainText('请输入 HEX 数据')
            return
        try:
            data = _hex_to_bytes(text)
        except ValueError as e:
            self.txt_out.setPlainText(f'HEX 格式错误: {e}')
            return

        alg_name = self.cmb_alg.currentText()
        func = ALGORITHMS.get(alg_name)
        if not func:
            self.txt_out.setPlainText('未知算法')
            return

        try:
            result = func(data)
        except Exception as e:
            self.txt_out.setPlainText(f'计算错误: {e}')
            return

        self._last_result = result
        self._last_alg = alg_name

        width = self._result_width(alg_name)
        lines = [
            f'算法: {alg_name}',
            f'输入长度: {len(data)} 字节',
            f'输入 HEX: {_bytes_to_hex(data)}',
            '',
            f'十六进制: 0x{result:0{width}X}',
            f'十进制: {result}',
        ]

        if width >= 4:
            lines.append(f'高字节: 0x{(result >> 8) & 0xFF:02X}')
            lines.append(f'低字节: 0x{result & 0xFF:02X}')
        if width >= 8:
            lines.append('')
            lines.append(f'字16位高: 0x{(result >> 16) & 0xFFFF:04X}')
            lines.append(f'字16位低: 0x{result & 0xFFFF:04X}')
            lines.append(f'字节序BE: {(result >> 24) & 0xFF:02X} {(result >> 16) & 0xFF:02X} {(result >> 8) & 0xFF:02X} {result & 0xFF:02X}')
            lines.append(f'字节序LE: {result & 0xFF:02X} {(result >> 8) & 0xFF:02X} {(result >> 16) & 0xFF:02X} {(result >> 24) & 0xFF:02X}')

        self.txt_out.setPlainText('\n'.join(lines))

    def _result_width(self, alg_name: str) -> int:
        if alg_name in ('Sum8', 'XOR8', 'CRC8'):
            return 2
        if alg_name in ('Sum16', 'CRC16-CCITT', 'CRC16-MODBUS'):
            return 4
        if alg_name == 'CRC32':
            return 8
        return 4

    def _append_result(self):
        if not hasattr(self, '_last_result'):
            return
        text = self.txt_in.toPlainText().strip()
        if not text:
            return
        width = self._result_width(self._last_alg)
        hex_str = f'{self._last_result:0{width}X}'
        hex_bytes = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        self.txt_in.setPlainText(text + ' ' + hex_bytes)
        self._calc()

    def _copy(self, mode: str):
        if not hasattr(self, '_last_result'):
            return
        width = self._result_width(self._last_alg)
        cb = QApplication.clipboard()
        if mode == 'hex':
            cb.setText(f'{self._last_result:0{width}X}')
        elif mode == 'dec':
            cb.setText(str(self._last_result))
        else:
            cb.setText(self.txt_out.toPlainText())

    def _verify(self):
        text = self.txt_verify.toPlainText().strip()
        if not text:
            self.lbl_verify_result.setText('请输入数据')
            self.lbl_verify_result.setStyleSheet('color:#EF4444; font-weight:600;')
            return
        try:
            data = _hex_to_bytes(text)
        except ValueError:
            self.lbl_verify_result.setText('格式错误')
            self.lbl_verify_result.setStyleSheet('color:#EF4444; font-weight:600;')
            return

        alg_name = self.cmb_verify_alg.currentText()
        func = ALGORITHMS.get(alg_name)
        if not func:
            return

        width = self._result_width(alg_name)
        n_bytes = width // 2

        if len(data) <= n_bytes:
            self.lbl_verify_result.setText('数据太短')
            self.lbl_verify_result.setStyleSheet('color:#EF4444; font-weight:600;')
            return

        payload = data[:-n_bytes]
        expected = int.from_bytes(data[-n_bytes:], byteorder='big')
        actual = func(payload)

        if expected == actual:
            self.lbl_verify_result.setText('✓ 校验正确')
            self.lbl_verify_result.setStyleSheet('color:#10B981; font-weight:600;')
        else:
            self.lbl_verify_result.setText(
                f'✗ 错误 (期望: {expected:0{width}X}, 实际: {actual:0{width}X})'
            )
            self.lbl_verify_result.setStyleSheet('color:#EF4444; font-weight:600;')

