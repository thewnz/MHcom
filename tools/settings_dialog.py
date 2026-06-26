# -*- coding: utf-8 -*-
"""系统设置对话框 - 统一配置中心"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLabel, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox
)
from config.settings import AppConfig


class SettingsDialog(QDialog):
    """系统设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = AppConfig()
        self.setWindowTitle('系统设置 - MHcom')
        self.resize(560, 520)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_general_tab(), '通用设置')
        self.tabs.addTab(self._build_send_tab(), '发送设置')
        self.tabs.addTab(self._build_ui_tab(), '界面设置')
        self.tabs.addTab(self._build_shortcut_tab(), '快捷键')
        layout.addWidget(self.tabs, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_reset = QPushButton('恢复默认')
        btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(btn_reset)

        btn_apply = QPushButton('应用')
        btn_apply.clicked.connect(self._apply)
        btn_layout.addWidget(btn_apply)

        btn_cancel = QPushButton('取消')
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton('确定')
        btn_ok.setStyleSheet(
            'background:#3B82F6; color:white; padding:6px 18px;'
            'border-radius:4px; font-weight:600;'
        )
        btn_ok.clicked.connect(self._on_ok)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.cmb_baud = QComboBox()
        self.cmb_baud.setEditable(True)
        self.cmb_baud.addItems([
            '9600', '19200', '38400', '57600', '115200',
            '230400', '460800', '921600'
        ])
        form.addRow('默认波特率:', self.cmb_baud)

        self.cmb_bytesize = QComboBox()
        self.cmb_bytesize.addItems(['8', '7', '6', '5'])
        form.addRow('数据位:', self.cmb_bytesize)

        self.cmb_parity = QComboBox()
        self.cmb_parity.addItems(['无', '奇', '偶', 'Mark', 'Space'])
        form.addRow('校验:', self.cmb_parity)

        self.cmb_stopbits = QComboBox()
        self.cmb_stopbits.addItems(['1', '1.5', '2'])
        form.addRow('停止位:', self.cmb_stopbits)

        self.cmb_flowctrl = QComboBox()
        self.cmb_flowctrl.addItems(['无', 'RTS/CTS', 'XON/XOFF', 'DSR/DTR'])
        form.addRow('流控:', self.cmb_flowctrl)

        self.spn_max_lines = QSpinBox()
        self.spn_max_lines.setRange(100, 100000)
        self.spn_max_lines.setSingleStep(100)
        self.spn_max_lines.setSuffix(' 行')
        form.addRow('接收区最大行数:', self.spn_max_lines)

        self.spn_font_size = QSpinBox()
        self.spn_font_size.setRange(8, 32)
        self.spn_font_size.setSuffix(' px')
        form.addRow('显示字体大小:', self.spn_font_size)

        self.chk_window_top = QCheckBox('窗口置顶')
        form.addRow('', self.chk_window_top)

        self.chk_remember_geometry = QCheckBox('记住窗口位置大小')
        form.addRow('', self.chk_remember_geometry)

        return w

    def _build_send_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.cmb_newline = QComboBox()
        self.cmb_newline.addItems(['\\r\\n', '\\n', '\\r', '无'])
        form.addRow('默认换行符:', self.cmb_newline)

        self.spn_history_count = QSpinBox()
        self.spn_history_count.setRange(10, 500)
        self.spn_history_count.setSuffix(' 条')
        form.addRow('发送历史记录数:', self.spn_history_count)

        self.cmb_crc_alg = QComboBox()
        self.cmb_crc_alg.addItems([
            'CRC16 Modbus', 'CRC16 CCITT', 'CRC8',
            'CRC32', 'Sum8', 'Sum16', 'XOR8'
        ])
        form.addRow('默认校验算法:', self.cmb_crc_alg)

        return w

    def _build_ui_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(['浅色', '深色'])
        form.addRow('主题:', self.cmb_theme)

        self.spn_icon_size = QSpinBox()
        self.spn_icon_size.setRange(16, 64)
        self.spn_icon_size.setSingleStep(2)
        self.spn_icon_size.setSuffix(' px')
        self.spn_icon_size.setEnabled(False)
        self.spn_icon_size.setToolTip('当前工具栏为纯文字模式，此设置暂无效果')
        form.addRow('工具栏图标大小:', self.spn_icon_size)

        self.cmb_language = QComboBox()
        self.cmb_language.addItems(['中文', 'English (开发中)'])
        self.cmb_language.setEnabled(False)
        self.cmb_language.setToolTip('国际化功能尚未实现，敬请期待')
        form.addRow('语言:', self.cmb_language)

        return w

    def _build_shortcut_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        tip = QLabel('快捷键列表 (只读)')
        tip.setStyleSheet('color:#64748B; font-size:12px;')
        layout.addWidget(tip)

        self.list_shortcuts = QListWidget()
        shortcuts = [
            ('Ctrl+1', '切换到 3D云台调试 模式'),
            ('Ctrl+2', '切换到 高级串口助手 模式'),
            ('Ctrl+Q', '退出程序'),
            ('Ctrl+W', '打开实时波形图'),
            ('Ctrl+M', '打开 Modbus RTU 模拟器'),
            ('Ctrl+Shift+C', '打开 CRC / 校验计算器'),
            ('Ctrl+H', '打开 HEX / 文本转换'),
            ('Ctrl+P', '打开协议解析器'),
            ('Ctrl+K', '打开快捷命令管理'),
            ('Ctrl+L', '打开发送历史'),
            ('Ctrl+T', '打开数据统计'),
            ('Ctrl+I', '打开串口监听器'),
            ('Ctrl+`', '打开终端模式'),
            ('Ctrl+R', '打开正则测试器'),
            ('Ctrl+,', '打开系统设置'),
            ('Ctrl+Enter', '发送数据'),
        ]
        for key, desc in shortcuts:
            item = QListWidgetItem(f'{key:18s}  {desc}')
            self.list_shortcuts.addItem(item)
        layout.addWidget(self.list_shortcuts, 1)

        return w

    def _load_settings(self):
        baud = self.config.get('serial.baud', 115200)
        self.cmb_baud.setCurrentText(str(baud))

        bytesize = self.config.get('serial.bytesize', 8)
        idx = self.cmb_bytesize.findText(str(bytesize))
        if idx >= 0:
            self.cmb_bytesize.setCurrentIndex(idx)

        parity = self.config.get('serial.parity', 'N')
        parity_map = {'N': '无', 'O': '奇', 'E': '偶', 'M': 'Mark', 'S': 'Space'}
        idx = self.cmb_parity.findText(parity_map.get(parity, '无'))
        if idx >= 0:
            self.cmb_parity.setCurrentIndex(idx)

        stopbits = self.config.get('serial.stopbits', 1)
        idx = self.cmb_stopbits.findText(str(stopbits))
        if idx >= 0:
            self.cmb_stopbits.setCurrentIndex(idx)

        max_lines = self.config.get('ui.max_rx_lines', 5000)
        self.spn_max_lines.setValue(max_lines)

        font_size = self.config.get('ui.font_size', 10)
        self.spn_font_size.setValue(font_size)

        window_top = self.config.get('ui.window_top', False)
        self.chk_window_top.setChecked(window_top)

        remember_geo = self.config.get('ui.remember_geometry', True)
        self.chk_remember_geometry.setChecked(remember_geo)

        newline = self.config.get('send.newline', '\\r\\n')
        idx = self.cmb_newline.findText(newline)
        if idx >= 0:
            self.cmb_newline.setCurrentIndex(idx)

        history_count = self.config.get('send.history_count', 50)
        self.spn_history_count.setValue(history_count)

        crc_alg = self.config.get('send.crc_algorithm', 'CRC16 Modbus')
        idx = self.cmb_crc_alg.findText(crc_alg)
        if idx >= 0:
            self.cmb_crc_alg.setCurrentIndex(idx)

        theme = self.config.get('theme', 'light')
        self.cmb_theme.setCurrentIndex(0 if theme == 'light' else 1)

        icon_size = self.config.get('ui.toolbar_icon_size', 24)
        self.spn_icon_size.setValue(icon_size)

        language = self.config.get('ui.language', 'zh')
        self.cmb_language.setCurrentIndex(0 if language == 'zh' else 1)

    def _save_settings(self):
        try:
            baud = int(self.cmb_baud.currentText())
            self.config.set('serial.baud', baud)
        except ValueError:
            pass

        self.config.set('serial.bytesize', int(self.cmb_bytesize.currentText()))

        parity_map = {'无': 'N', '奇': 'O', '偶': 'E', 'Mark': 'M', 'Space': 'S'}
        self.config.set('serial.parity', parity_map.get(self.cmb_parity.currentText(), 'N'))

        self.config.set('serial.stopbits', float(self.cmb_stopbits.currentText()))

        self.config.set('ui.max_rx_lines', self.spn_max_lines.value())
        self.config.set('ui.font_size', self.spn_font_size.value())
        self.config.set('ui.window_top', self.chk_window_top.isChecked())
        self.config.set('ui.remember_geometry', self.chk_remember_geometry.isChecked())

        self.config.set('send.newline', self.cmb_newline.currentText())
        self.config.set('send.history_count', self.spn_history_count.value())
        self.config.set('send.crc_algorithm', self.cmb_crc_alg.currentText())

        theme = 'light' if self.cmb_theme.currentIndex() == 0 else 'dark'
        self.config.set('theme', theme)

        self.config.set('ui.toolbar_icon_size', self.spn_icon_size.value())

        language = 'zh' if self.cmb_language.currentIndex() == 0 else 'en'
        self.config.set('ui.language', language)

        self.config.save()

    def _apply(self):
        self._save_settings()

    def _on_ok(self):
        self._save_settings()
        self.accept()

    def _reset_defaults(self):
        defaults = self.config.DEFAULT
        self.config.set('serial.baud', defaults.get('serial', {}).get('baud', 115200))
        self.config.set('serial.bytesize', defaults.get('serial', {}).get('bytesize', 8))
        self.config.set('serial.parity', defaults.get('serial', {}).get('parity', 'N'))
        self.config.set('serial.stopbits', defaults.get('serial', {}).get('stopbits', 1))
        self.config.set('theme', defaults.get('theme', 'light'))
        self.config.save()
        self._load_settings()

