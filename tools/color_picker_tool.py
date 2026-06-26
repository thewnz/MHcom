# -*- coding: utf-8 -*-
"""
颜色拾取器
HEX/RGB/HSL 转换，预设颜色，复制到剪贴板
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QGuiApplication
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QLineEdit, QSpinBox, QApplication, QSlider
)


class ColorPickerTool(QWidget):
    """颜色拾取工具 - 单例模式"""

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
        self.setWindowTitle('颜色拾取器 - MHcom')
        self.resize(540, 520)
        self._color = QColor('#3B82F6')
        self._updating = False
        self._build_ui()
        self._update_display()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('颜色拾取器')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        cur_box = QGroupBox('  当前颜色')
        cl = QVBoxLayout(cur_box)
        cl.setContentsMargins(12, 10, 12, 12)
        self.preview = QLabel()
        self.preview.setMinimumHeight(90)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet(
            'border: 1px solid #E2E8F0; border-radius: 8px;'
            'font-size: 16px; font-weight: 600;'
        )
        cl.addWidget(self.preview)
        layout.addWidget(cur_box)

        slider_box = QGroupBox('  RGB 滑块')
        sl = QVBoxLayout(slider_box)
        sl.setContentsMargins(12, 10, 12, 12)
        sl.setSpacing(8)

        r_row = QHBoxLayout()
        r_row.addWidget(QLabel('R'))
        self.slider_r = QSlider(Qt.Horizontal)
        self.slider_r.setRange(0, 255)
        self.slider_r.setValue(59)
        self.slider_r.valueChanged.connect(self._on_slider)
        r_row.addWidget(self.slider_r, 1)
        self.lbl_r = QLabel('59')
        self.lbl_r.setMinimumWidth(40)
        self.lbl_r.setAlignment(Qt.AlignCenter)
        r_row.addWidget(self.lbl_r)
        sl.addLayout(r_row)

        g_row = QHBoxLayout()
        g_row.addWidget(QLabel('G'))
        self.slider_g = QSlider(Qt.Horizontal)
        self.slider_g.setRange(0, 255)
        self.slider_g.setValue(130)
        self.slider_g.valueChanged.connect(self._on_slider)
        g_row.addWidget(self.slider_g, 1)
        self.lbl_g = QLabel('130')
        self.lbl_g.setMinimumWidth(40)
        self.lbl_g.setAlignment(Qt.AlignCenter)
        g_row.addWidget(self.lbl_g)
        sl.addLayout(g_row)

        b_row = QHBoxLayout()
        b_row.addWidget(QLabel('B'))
        self.slider_b = QSlider(Qt.Horizontal)
        self.slider_b.setRange(0, 255)
        self.slider_b.setValue(246)
        self.slider_b.valueChanged.connect(self._on_slider)
        b_row.addWidget(self.slider_b, 1)
        self.lbl_b = QLabel('246')
        self.lbl_b.setMinimumWidth(40)
        self.lbl_b.setAlignment(Qt.AlignCenter)
        b_row.addWidget(self.lbl_b)
        sl.addLayout(b_row)

        layout.addWidget(slider_box)

        val_box = QGroupBox('  颜色值')
        vg = QGridLayout(val_box)
        vg.setContentsMargins(12, 10, 12, 12)
        vg.setSpacing(8)

        vg.addWidget(QLabel('HEX:'), 0, 0)
        self.txt_hex = QLineEdit()
        self.txt_hex.setText('#3B82F6')
        self.txt_hex.setStyleSheet(
            'QLineEdit { padding: 6px; border: 1px solid #CBD5E1; border-radius: 6px;'
            'font-family: Consolas; }'
        )
        self.txt_hex.textChanged.connect(self._on_hex)
        vg.addWidget(self.txt_hex, 0, 1)

        vg.addWidget(QLabel('RGB:'), 1, 0)
        rgb_row = QHBoxLayout()
        rgb_row.setSpacing(4)
        self.spn_r = QSpinBox()
        self.spn_r.setRange(0, 255)
        self.spn_r.valueChanged.connect(self._on_rgb)
        self.spn_g = QSpinBox()
        self.spn_g.setRange(0, 255)
        self.spn_g.valueChanged.connect(self._on_rgb)
        self.spn_b = QSpinBox()
        self.spn_b.setRange(0, 255)
        self.spn_b.valueChanged.connect(self._on_rgb)
        rgb_row.addWidget(QLabel('R'))
        rgb_row.addWidget(self.spn_r, 1)
        rgb_row.addWidget(QLabel('G'))
        rgb_row.addWidget(self.spn_g, 1)
        rgb_row.addWidget(QLabel('B'))
        rgb_row.addWidget(self.spn_b, 1)
        vg.addLayout(rgb_row, 1, 1)

        layout.addWidget(val_box)

        preset_box = QGroupBox('  预设颜色')
        pg = QGridLayout(preset_box)
        pg.setContentsMargins(12, 10, 12, 12)
        pg.setSpacing(6)

        colors = [
            ('#EF4444', '红'), ('#F59E0B', '橙'), ('#FBBF24', '黄'),
            ('#84CC16', '黄绿'), ('#10B981', '绿'), ('#06B6D4', '青'),
            ('#3B82F6', '蓝'), ('#6366F1', '靛'), ('#8B5CF6', '紫'),
            ('#EC4899', '粉'), ('#64748B', '灰'), ('#0F172A', '深蓝'),
        ]
        for i, (color, name) in enumerate(colors):
            row, col = divmod(i, 6)
            btn = QPushButton(name)
            text_color = 'white' if self._is_dark(color) else '#1E293B'
            btn.setStyleSheet(
                f'QPushButton {{ background: {color}; color: {text_color};'
                f'border: none; padding: 10px 6px; border-radius: 6px;'
                f'font-size: 12px; font-weight: 500; }}'
                f'QPushButton:hover {{ opacity: 0.9; }}'
            )
            btn.clicked.connect(lambda _, c=color: self._set_hex(c))
            pg.addWidget(btn, row, col)

        layout.addWidget(preset_box)

        ops = QHBoxLayout()
        ops.setSpacing(8)

        btn_copy_hex = QPushButton('📋 复制 HEX')
        btn_copy_hex.setStyleSheet(
            'padding:8px 16px; border-radius:6px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
            'font-weight: 500;'
        )
        btn_copy_hex.clicked.connect(self._copy_hex)
        ops.addWidget(btn_copy_hex)

        btn_copy_rgb = QPushButton('📋 复制 RGB')
        btn_copy_rgb.setStyleSheet(
            'padding:8px 16px; border-radius:6px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
            'font-weight: 500;'
        )
        btn_copy_rgb.clicked.connect(self._copy_rgb)
        ops.addWidget(btn_copy_rgb)

        ops.addStretch()
        layout.addLayout(ops)

    def _is_dark(self, hex_color):
        c = QColor(hex_color)
        luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
        return luminance < 0.5

    def _set_hex(self, h):
        self.txt_hex.setText(h)

    def _on_hex(self, h):
        if self._updating:
            return
        if not h:
            return
        if not h.startswith('#'):
            h = '#' + h
        c = QColor(h)
        if c.isValid():
            self._color = c
            self._update_display()
            self._updating = True
            try:
                self.spn_r.setValue(c.red())
                self.spn_g.setValue(c.green())
                self.spn_b.setValue(c.blue())
                self.slider_r.setValue(c.red())
                self.slider_g.setValue(c.green())
                self.slider_b.setValue(c.blue())
                self.lbl_r.setText(str(c.red()))
                self.lbl_g.setText(str(c.green()))
                self.lbl_b.setText(str(c.blue()))
            finally:
                self._updating = False

    def _on_rgb(self):
        if self._updating:
            return
        c = QColor(self.spn_r.value(), self.spn_g.value(), self.spn_b.value())
        self._color = c
        self._update_display()
        self._updating = True
        self.txt_hex.setText(c.name().upper())
        self.slider_r.setValue(c.red())
        self.slider_g.setValue(c.green())
        self.slider_b.setValue(c.blue())
        self.lbl_r.setText(str(c.red()))
        self.lbl_g.setText(str(c.green()))
        self.lbl_b.setText(str(c.blue()))
        self._updating = False

    def _on_slider(self):
        if self._updating:
            return
        r = self.slider_r.value()
        g = self.slider_g.value()
        b = self.slider_b.value()
        c = QColor(r, g, b)
        self._color = c
        self._update_display()
        self._updating = True
        self.txt_hex.setText(c.name().upper())
        self.spn_r.setValue(r)
        self.spn_g.setValue(g)
        self.spn_b.setValue(b)
        self.lbl_r.setText(str(r))
        self.lbl_g.setText(str(g))
        self.lbl_b.setText(str(b))
        self._updating = False

    def _update_display(self):
        name = self._color.name().upper()
        text_color = 'white' if self._is_dark(name) else '#1E293B'
        self.preview.setStyleSheet(
            f'background: {name}; color: {text_color};'
            f'border: 1px solid #E2E8F0; border-radius: 8px;'
            f'font-size: 16px; font-weight: 600;'
        )
        self.preview.setText(
            f'{name}  |  RGB({self._color.red()}, {self._color.green()}, {self._color.blue()})'
        )

    def _copy_hex(self):
        QApplication.clipboard().setText(self._color.name().upper())

    def _copy_rgb(self):
        s = f'rgb({self._color.red()}, {self._color.green()}, {self._color.blue()})'
        QApplication.clipboard().setText(s)

    def closeEvent(self, event):
        super().closeEvent(event)

