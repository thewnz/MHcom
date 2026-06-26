# -*- coding: utf-8 -*-
"""串口监听器工具"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox, QCheckBox, QSpinBox, QComboBox
)
from core.data_bus import DataBus


class MonitorTool(QWidget):
    """串口监听器 - 单例模式"""

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
        self.setWindowTitle('串口监听器 - MHcom')
        self.resize(780, 600)
        self.monitoring = False
        self._rx_count = 0
        self._build_ui()
        DataBus.instance().raw_received.connect(self._on_rx)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('串口数据监听器')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        cfg = QGroupBox('  监听配置')
        cfg_lay = QHBoxLayout(cfg)
        cfg_lay.setContentsMargins(12, 10, 12, 12)
        cfg_lay.setSpacing(12)

        self.cmb_display = QComboBox()
        self.cmb_display.addItems(['文本显示', 'HEX显示', '混合显示'])
        cfg_lay.addWidget(QLabel('显示模式:'))
        cfg_lay.addWidget(self.cmb_display)

        self.chk_pause = QCheckBox('暂停显示')
        cfg_lay.addWidget(self.chk_pause)

        cfg_lay.addWidget(QLabel('最大行数:'))
        self.spn_max = QSpinBox()
        self.spn_max.setRange(100, 100000)
        self.spn_max.setValue(2000)
        cfg_lay.addWidget(self.spn_max)

        cfg_lay.addStretch()

        self.btn_toggle = QPushButton('开始监听')
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setStyleSheet(
            'padding:6px 20px; border-radius:4px; font-weight:600;'
            'background:#10B981; color:white; border:none;'
        )
        self.btn_toggle.clicked.connect(self._toggle)
        cfg_lay.addWidget(self.btn_toggle)

        layout.addWidget(cfg)

        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText('点击"开始监听"按钮开始接收数据...')
        self.txt_log.setStyleSheet(
            'QPlainTextEdit { background:#0F172A; color:#10B981; font-family: Consolas;'
            'font-size:13px; border: 1px solid #1E293B; border-radius: 6px; padding: 8px; }'
        )
        layout.addWidget(self.txt_log, 1)

        status_row = QHBoxLayout()
        self.lbl_status = QLabel('状态: 未监听')
        self.lbl_status.setStyleSheet('color:#64748B; font-size:13px;')
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        self.lbl_count = QLabel('接收: 0 字节')
        self.lbl_count.setStyleSheet('color:#64748B; font-size:13px;')
        status_row.addWidget(self.lbl_count)
        layout.addLayout(status_row)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton('清空日志')
        btn_clear.setStyleSheet(
            'padding:6px 16px; border-radius:4px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_clear.clicked.connect(self.txt_log.clear)
        btn_row.addWidget(btn_clear)

        btn_save = QPushButton('保存日志')
        btn_save.setStyleSheet(
            'padding:6px 16px; border-radius:4px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_save.clicked.connect(self._save_log)
        btn_row.addWidget(btn_save)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _toggle(self, on):
        self.monitoring = on
        if on:
            self.btn_toggle.setText('停止监听')
            self.btn_toggle.setStyleSheet(
                'padding:6px 20px; border-radius:4px; font-weight:600;'
                'background:#EF4444; color:white; border:none;'
            )
            self.txt_log.setPlaceholderText('')
            self.lbl_status.setText('状态: 监听中')
            self.lbl_status.setStyleSheet('color:#10B981; font-size:13px; font-weight:600;')
        else:
            self.btn_toggle.setText('开始监听')
            self.btn_toggle.setStyleSheet(
                'padding:6px 20px; border-radius:4px; font-weight:600;'
                'background:#10B981; color:white; border:none;'
            )
            self.txt_log.setPlaceholderText('监听已停止')
            self.lbl_status.setText('状态: 已停止')
            self.lbl_status.setStyleSheet('color:#F59E0B; font-size:13px; font-weight:600;')

    def _on_rx(self, data):
        if not self.monitoring or self.chk_pause.isChecked():
            return

        self._rx_count += len(data)
        self.lbl_count.setText(f'接收: {self._rx_count} 字节')

        mode = self.cmb_display.currentIndex()
        try:
            text = data.decode('utf-8', errors='replace')
        except Exception:
            text = repr(data)

        if mode == 0:
            display = text
        elif mode == 1:
            display = ' '.join(f'{b:02X}' for b in data)
        else:
            hex_str = ' '.join(f'{b:02X}' for b in data)
            display = f'[{hex_str}] {text}'

        self.txt_log.appendPlainText(display)

        max_lines = self.spn_max.value()
        if self.txt_log.blockCount() > max_lines:
            cursor = self.txt_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, self.txt_log.blockCount() - max_lines)
            cursor.removeSelectedText()

    def _save_log(self):
        from PyQt5.QtWidgets import QFileDialog
        text = self.txt_log.toPlainText()
        if not text:
            return
        fname, _ = QFileDialog.getSaveFileName(
            self, '保存日志', 'serial_log.txt', '文本文件 (*.txt);;所有文件 (*)'
        )
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(text)
            except Exception as e:
                self.txt_log.appendPlainText(f'\n[保存失败: {e}]')

    def closeEvent(self, event):
        try:
            DataBus.instance().raw_received.disconnect(self._on_rx)
        except Exception:
            pass
        super().closeEvent(event)

