# -*- coding: utf-8 -*-
"""
控件交互面板工具 - 类 VOFA+ 的控件面板
通过图形控件向下位机发送指令
"""
import re
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QGroupBox, QSlider, QDial, QCheckBox, QComboBox, QSpinBox, QLineEdit,
    QDialog, QDialogButtonBox, QMenu, QAction, QMessageBox, QFrame
)
from core.serial_link import SerialLink
from core.data_bus import DataBus
from config.settings import AppConfig


WIDGET_TYPES = ['按钮', '滑块', '旋钮', '仪表盘', '开关']


class GaugeWidget(QWidget):
    """仪表盘控件 - 自定义绘制"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 140)
        self._value = 0.0
        self._min_val = 0.0
        self._max_val = 100.0
        self._title = '仪表盘'
        self._unit = ''

    def set_range(self, min_val: float, max_val: float):
        self._min_val = min_val
        self._max_val = max_val
        self.update()

    def set_value(self, value: float):
        self._value = max(self._min_val, min(self._max_val, value))
        self.update()

    def set_title(self, title: str):
        self._title = title
        self.update()

    def set_unit(self, unit: str):
        self._unit = unit
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2 + 10
        radius = min(w, h) / 2 - 20

        # 背景圆
        gradient = QRadialGradient(cx, cy, radius)
        gradient.setColorAt(0, QColor('#FAFAFA'))
        gradient.setColorAt(1, QColor('#E5E7EB'))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor('#CBD5E1'), 2))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # 刻度弧线
        start_angle = 210
        span_angle = -240
        painter.setPen(QPen(QColor('#94A3B8'), 3))
        from PyQt5.QtCore import QRectF, Qt as QtCore
        rect = QRectF(cx - radius + 8, cy - radius + 8,
                      (radius - 8) * 2, (radius - 8) * 2)
        painter.drawArc(rect, start_angle * 16, span_angle * 16)

        # 刻度线
        painter.setPen(QPen(QColor('#64748B'), 1.5))
        import math
        for i in range(11):
            angle = math.radians(210 + i * (-240) / 10)
            x1 = cx + (radius - 12) * math.cos(angle)
            y1 = cy - (radius - 12) * math.sin(angle)
            x2 = cx + (radius - 20) * math.cos(angle)
            y2 = cy - (radius - 20) * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 值范围文本
        painter.setPen(QColor('#475569'))
        painter.setFont(QFont('Arial', 8))
        painter.drawText(int(cx - radius + 5), int(cy + 8),
                         int(radius / 2), 20, Qt.AlignLeft,
                         f'{self._min_val:g}')
        painter.drawText(int(cx + radius / 2 - 5), int(cy + 8),
                         int(radius / 2), 20, Qt.AlignRight,
                         f'{self._max_val:g}')

        # 指针
        ratio = 0.0
        if self._max_val != self._min_val:
            ratio = (self._value - self._min_val) / (self._max_val - self._min_val)
        pointer_angle = math.radians(210 + ratio * (-240))
        painter.setPen(QPen(QColor('#EF4444'), 3, Qt.SolidLine, Qt.RoundCap))
        px = cx + (radius - 30) * math.cos(pointer_angle)
        py = cy - (radius - 30) * math.sin(pointer_angle)
        painter.drawLine(int(cx), int(cy), int(px), int(py))

        # 中心圆
        painter.setBrush(QColor('#374151'))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - 6), int(cy - 6), 12, 12)

        # 数值显示
        painter.setPen(QColor('#1F2937'))
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        val_text = f'{self._value:.2f}' if isinstance(self._value, float) else str(self._value)
        if self._unit:
            val_text += f' {self._unit}'
        painter.drawText(int(cx - radius), int(cy + 25),
                         int(radius * 2), 20, Qt.AlignCenter, val_text)

        # 标题
        painter.setPen(QColor('#64748B'))
        painter.setFont(QFont('Arial', 9))
        painter.drawText(0, 2, w, 20, Qt.AlignCenter, self._title)


class WidgetConfigDialog(QDialog):
    """控件属性编辑对话框"""

    def __init__(self, widget_type: str, config: dict = None, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.setWindowTitle(f'编辑{widget_type}控件')
        self.resize(380, 320)
        self._build_ui()
        if config:
            self._load_config(config)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 名称
        layout.addWidget(QLabel('控件名称:'))
        self.ed_name = QLineEdit()
        self.ed_name.setPlaceholderText('显示在控件上方的名称')
        layout.addWidget(self.ed_name)

        # 类型特定配置
        self._build_type_ui(layout)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_type_ui(self, layout):
        if self.widget_type == '按钮':
            layout.addWidget(QLabel('按钮文本:'))
            self.ed_btn_text = QLineEdit('发送')
            layout.addWidget(self.ed_btn_text)

            layout.addWidget(QLabel('发送内容:'))
            self.ed_btn_cmd = QLineEdit()
            self.ed_btn_cmd.setPlaceholderText('例如: AT+VER?\\r\\n')
            layout.addWidget(self.ed_btn_cmd)

        elif self.widget_type == '滑块':
            form_row = QHBoxLayout()
            form_row.addWidget(QLabel('最小值:'))
            self.sp_min = QSpinBox()
            self.sp_min.setRange(-100000, 100000)
            self.sp_min.setValue(0)
            form_row.addWidget(self.sp_min)
            form_row.addWidget(QLabel('最大值:'))
            self.sp_max = QSpinBox()
            self.sp_max.setRange(-100000, 100000)
            self.sp_max.setValue(100)
            form_row.addWidget(self.sp_max)
            layout.addLayout(form_row)

            layout.addWidget(QLabel('格式字符串 (用 {val} 表示数值):'))
            self.ed_format = QLineEdit('SET:CH1={val}\\r\\n')
            layout.addWidget(self.ed_format)

            layout.addWidget(QLabel('实时发送(拖动时发送):'))
            self.chk_realtime = QCheckBox('启用实时发送')
            self.chk_realtime.setChecked(True)
            layout.addWidget(self.chk_realtime)

        elif self.widget_type == '旋钮':
            form_row = QHBoxLayout()
            form_row.addWidget(QLabel('最小值:'))
            self.sp_min = QSpinBox()
            self.sp_min.setRange(-100000, 100000)
            self.sp_min.setValue(0)
            form_row.addWidget(self.sp_min)
            form_row.addWidget(QLabel('最大值:'))
            self.sp_max = QSpinBox()
            self.sp_max.setRange(-100000, 100000)
            self.sp_max.setValue(100)
            form_row.addWidget(self.sp_max)
            layout.addLayout(form_row)

            layout.addWidget(QLabel('格式字符串 (用 {val} 表示数值):'))
            self.ed_format = QLineEdit('SET:SPD={val}\\r\\n')
            layout.addWidget(self.ed_format)

        elif self.widget_type == '仪表盘':
            form_row = QHBoxLayout()
            form_row.addWidget(QLabel('最小值:'))
            self.sp_min = QSpinBox()
            self.sp_min.setRange(-100000, 100000)
            self.sp_min.setValue(0)
            form_row.addWidget(self.sp_min)
            form_row.addWidget(QLabel('最大值:'))
            self.sp_max = QSpinBox()
            self.sp_max.setRange(-100000, 100000)
            self.sp_max.setValue(100)
            form_row.addWidget(self.sp_max)
            layout.addLayout(form_row)

            layout.addWidget(QLabel('单位:'))
            self.ed_unit = QLineEdit()
            self.ed_unit.setPlaceholderText('例如: °C, rpm, V')
            layout.addWidget(self.ed_unit)

            layout.addWidget(QLabel('数据匹配正则 (从接收数据中提取数值):'))
            self.ed_regex = QLineEdit()
            self.ed_regex.setPlaceholderText('例如: TEMP:([\\d.]+)')
            layout.addWidget(self.ed_regex)

        elif self.widget_type == '开关':
            layout.addWidget(QLabel('开 (ON) 发送内容:'))
            self.ed_on_cmd = QLineEdit('ON\\r\\n')
            layout.addWidget(self.ed_on_cmd)

            layout.addWidget(QLabel('关 (OFF) 发送内容:'))
            self.ed_off_cmd = QLineEdit('OFF\\r\\n')
            layout.addWidget(self.ed_off_cmd)

    def _load_config(self, config: dict):
        self.ed_name.setText(config.get('name', ''))

        if self.widget_type == '按钮':
            self.ed_btn_text.setText(config.get('btn_text', '发送'))
            self.ed_btn_cmd.setText(config.get('cmd', ''))

        elif self.widget_type in ('滑块', '旋钮'):
            self.sp_min.setValue(config.get('min_val', 0))
            self.sp_max.setValue(config.get('max_val', 100))
            self.ed_format.setText(config.get('format', '{val}'))
            if hasattr(self, 'chk_realtime'):
                self.chk_realtime.setChecked(config.get('realtime', True))

        elif self.widget_type == '仪表盘':
            self.sp_min.setValue(config.get('min_val', 0))
            self.sp_max.setValue(config.get('max_val', 100))
            self.ed_unit.setText(config.get('unit', ''))
            self.ed_regex.setText(config.get('regex', ''))

        elif self.widget_type == '开关':
            self.ed_on_cmd.setText(config.get('on_cmd', 'ON\\r\\n'))
            self.ed_off_cmd.setText(config.get('off_cmd', 'OFF\\r\\n'))

    def get_config(self) -> dict:
        cfg = {
            'type': self.widget_type,
            'name': self.ed_name.text(),
        }

        if self.widget_type == '按钮':
            cfg['btn_text'] = self.ed_btn_text.text()
            cfg['cmd'] = self.ed_btn_cmd.text()

        elif self.widget_type in ('滑块', '旋钮'):
            cfg['min_val'] = self.sp_min.value()
            cfg['max_val'] = self.sp_max.value()
            cfg['format'] = self.ed_format.text()
            if hasattr(self, 'chk_realtime'):
                cfg['realtime'] = self.chk_realtime.isChecked()

        elif self.widget_type == '仪表盘':
            cfg['min_val'] = self.sp_min.value()
            cfg['max_val'] = self.sp_max.value()
            cfg['unit'] = self.ed_unit.text()
            cfg['regex'] = self.ed_regex.text()

        elif self.widget_type == '开关':
            cfg['on_cmd'] = self.ed_on_cmd.text()
            cfg['off_cmd'] = self.ed_off_cmd.text()

        return cfg


class ControlWidgetWrapper(QFrame):
    """控件包装器 - 带标题栏和右键菜单"""

    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, index: int, config: dict, parent=None):
        super().__init__(parent)
        self.index = index
        self.config = config
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            QFrame { border: 1px solid #E5E7EB; border-radius: 6px;
                     background: #FFFFFF; }
            QFrame:hover { border-color: #93C5FD; }
        ''')
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(4)

        # 标题栏
        title_row = QHBoxLayout()
        self.lbl_title = QLabel(self.config.get('name', self.config.get('type', '')))
        self.lbl_title.setStyleSheet('color: #475569; font-weight: 500; font-size: 11px;')
        title_row.addWidget(self.lbl_title)
        title_row.addStretch()

        btn_edit = QPushButton('⋯')
        btn_edit.setFixedSize(22, 20)
        btn_edit.setStyleSheet('QPushButton { border: none; color: #64748B; }'
                               'QPushButton:hover { color: #3B82F6; }')
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.index))
        title_row.addWidget(btn_edit)

        layout.addLayout(title_row)

        # 控件主体
        self._build_widget(layout)

    def _build_widget(self, layout):
        wtype = self.config.get('type', '')

        if wtype == '按钮':
            self.btn = QPushButton(self.config.get('btn_text', '发送'))
            self.btn.setMinimumHeight(32)
            self.btn.setStyleSheet('''
                QPushButton { background: #3B82F6; color: white;
                              border: none; border-radius: 4px; padding: 6px 12px; }
                QPushButton:hover { background: #2563EB; }
                QPushButton:pressed { background: #1D4ED8; }
            ''')
            self.btn.clicked.connect(self._on_button_click)
            layout.addWidget(self.btn)

        elif wtype == '滑块':
            slider_row = QHBoxLayout()
            self.slider = QSlider(Qt.Horizontal)
            self.slider.setMinimum(self.config.get('min_val', 0))
            self.slider.setMaximum(self.config.get('max_val', 100))
            self.slider.setValue((self.config.get('min_val', 0) +
                                  self.config.get('max_val', 100)) // 2)
            self.lbl_slider_val = QLabel(str(self.slider.value()))
            self.lbl_slider_val.setFixedWidth(50)
            self.lbl_slider_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lbl_slider_val.setStyleSheet('color: #1F2937; font-family: Consolas;')
            slider_row.addWidget(self.slider, 1)
            slider_row.addWidget(self.lbl_slider_val)
            layout.addLayout(slider_row)

            if self.config.get('realtime', True):
                self.slider.valueChanged.connect(self._on_slider_changed)
            else:
                self.slider.sliderReleased.connect(self._on_slider_released)
            self.slider.valueChanged.connect(
                lambda v: self.lbl_slider_val.setText(str(v))
            )

        elif wtype == '旋钮':
            dial_row = QHBoxLayout()
            dial_row.addStretch()
            self.dial = QDial()
            self.dial.setMinimum(self.config.get('min_val', 0))
            self.dial.setMaximum(self.config.get('max_val', 100))
            self.dial.setValue((self.config.get('min_val', 0) +
                                self.config.get('max_val', 100)) // 2)
            self.dial.setNotchesVisible(True)
            self.dial.setWrapping(False)
            self.dial.setFixedSize(100, 100)
            dial_row.addWidget(self.dial)
            dial_row.addStretch()
            layout.addLayout(dial_row)

            self.lbl_dial_val = QLabel(str(self.dial.value()))
            self.lbl_dial_val.setAlignment(Qt.AlignCenter)
            self.lbl_dial_val.setStyleSheet(
                'color: #1F2937; font-family: Consolas; font-size: 13px; font-weight: bold;'
            )
            layout.addWidget(self.lbl_dial_val)

            self.dial.valueChanged.connect(self._on_dial_changed)
            self.dial.valueChanged.connect(
                lambda v: self.lbl_dial_val.setText(str(v))
            )

        elif wtype == '仪表盘':
            self.gauge = GaugeWidget()
            self.gauge.set_range(self.config.get('min_val', 0),
                                 self.config.get('max_val', 100))
            self.gauge.set_title('')
            self.gauge.set_unit(self.config.get('unit', ''))
            layout.addWidget(self.gauge)

        elif wtype == '开关':
            switch_row = QHBoxLayout()
            switch_row.addStretch()
            self.chk_switch = QCheckBox('OFF')
            self.chk_switch.setStyleSheet('''
                QCheckBox { font-size: 14px; font-weight: 600;
                            color: #64748B; padding: 8px; }
                QCheckBox:checked { color: #059669; }
                QCheckBox::indicator { width: 48px; height: 24px; border-radius: 12px;
                                       background: #CBD5E1; }
                QCheckBox::indicator:checked { background: #10B981; }
            ''')
            self.chk_switch.toggled.connect(self._on_switch_toggled)
            switch_row.addWidget(self.chk_switch)
            switch_row.addStretch()
            layout.addLayout(switch_row)

    def _on_button_click(self):
        cmd = self.config.get('cmd', '')
        if cmd:
            SerialLink.instance().send_text(cmd)

    def _on_slider_changed(self, value: int):
        fmt = self.config.get('format', '{val}')
        text = fmt.replace('{val}', str(value))
        text = text.replace('\\r', '\r').replace('\\n', '\n')
        SerialLink.instance().send(text.encode('utf-8', errors='ignore'))

    def _on_slider_released(self):
        self._on_slider_changed(self.slider.value())

    def _on_dial_changed(self, value: int):
        fmt = self.config.get('format', '{val}')
        text = fmt.replace('{val}', str(value))
        text = text.replace('\\r', '\r').replace('\\n', '\n')
        SerialLink.instance().send(text.encode('utf-8', errors='ignore'))

    def _on_switch_toggled(self, checked: bool):
        self.chk_switch.setText('ON' if checked else 'OFF')
        cmd = self.config.get('on_cmd', '') if checked else self.config.get('off_cmd', '')
        if cmd:
            cmd = cmd.replace('\\r', '\r').replace('\\n', '\n')
            SerialLink.instance().send(cmd.encode('utf-8', errors='ignore'))

    def _show_menu(self, pos):
        menu = QMenu(self)
        act_edit = QAction('编辑', self)
        act_edit.triggered.connect(lambda: self.edit_requested.emit(self.index))
        menu.addAction(act_edit)

        act_delete = QAction('删除', self)
        act_delete.triggered.connect(lambda: self.delete_requested.emit(self.index))
        menu.addAction(act_delete)

        menu.exec_(self.mapToGlobal(pos))

    def update_config(self, config: dict):
        self.config = config
        self.lbl_title.setText(config.get('name', config.get('type', '')))
        if hasattr(self, 'gauge'):
            self.gauge.set_range(config.get('min_val', 0),
                                 config.get('max_val', 100))
            self.gauge.set_unit(config.get('unit', ''))

    def update_gauge_value(self, value: float):
        if hasattr(self, 'gauge'):
            self.gauge.set_value(value)


class ControlPanelTool(QWidget):
    """控件交互面板工具"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('控件交互面板 - MHcom')
        self.resize(720, 520)
        self.config = AppConfig()
        self.widgets_config = self.config.get('control_panel_widgets', [])
        self.widget_wrappers = []
        self._build_ui()
        self._load_widgets()
        DataBus.instance().line_received.connect(self._on_line_received)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 顶部工具栏
        top_row = QHBoxLayout()

        self.lbl_title = QLabel('控件交互面板')
        self.lbl_title.setStyleSheet('font-size: 15px; font-weight: 600; color: #1F2937;')
        top_row.addWidget(self.lbl_title)

        top_row.addStretch()

        top_row.addWidget(QLabel('网格列数:'))
        self.sp_cols = QSpinBox()
        self.sp_cols.setRange(1, 8)
        self.sp_cols.setValue(self.config.get('control_panel_cols', 3))
        self.sp_cols.valueChanged.connect(self._on_cols_changed)
        top_row.addWidget(self.sp_cols)

        self.cb_add_type = QComboBox()
        self.cb_add_type.addItems(WIDGET_TYPES)
        top_row.addWidget(self.cb_add_type)

        btn_add = QPushButton('+ 添加控件')
        btn_add.setStyleSheet('''
            QPushButton { background: #10B981; color: white; border: none;
                          border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background: #059669; }
        ''')
        btn_add.clicked.connect(self._add_widget)
        top_row.addWidget(btn_add)

        layout.addLayout(top_row)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('color: #E5E7EB;')
        layout.addWidget(line)

        # 网格区域
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(10)
        layout.addWidget(self.grid_widget, 1)

        # 底部提示
        self.lbl_hint = QLabel('提示: 右键控件可编辑/删除 | 拖拽值控件自动发送')
        self.lbl_hint.setStyleSheet('color: #94A3B8; font-size: 11px;')
        layout.addWidget(self.lbl_hint)

    def _load_widgets(self):
        for wrapper in self.widget_wrappers:
            wrapper.setParent(None)
        self.widget_wrappers.clear()

        cols = self.config.get('control_panel_cols', 3)
        for i, cfg in enumerate(self.widgets_config):
            row = i // cols
            col = i % cols
            wrapper = ControlWidgetWrapper(i, cfg)
            wrapper.edit_requested.connect(self._edit_widget)
            wrapper.delete_requested.connect(self._delete_widget)
            self.grid_layout.addWidget(wrapper, row, col)
            self.widget_wrappers.append(wrapper)

        # 填充空白行
        for i in range(len(self.widget_wrappers), cols * 2):
            pass

    def _refresh_grid(self):
        cols = self.config.get('control_panel_cols', 3)
        for i, wrapper in enumerate(self.widget_wrappers):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(wrapper, row, col)

    def _add_widget(self):
        wtype = self.cb_add_type.currentText()
        dlg = WidgetConfigDialog(wtype, parent=self)
        dlg.ed_name.setText(f'{wtype}{len(self.widget_wrappers) + 1}')
        if dlg.exec_() == QDialog.Accepted:
            cfg = dlg.get_config()
            self.widgets_config.append(cfg)
            self._save_config()
            self._load_widgets()

    def _edit_widget(self, index: int):
        if 0 <= index < len(self.widgets_config):
            cfg = self.widgets_config[index]
            dlg = WidgetConfigDialog(cfg['type'], cfg, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.widgets_config[index] = dlg.get_config()
                self._save_config()
                if index < len(self.widget_wrappers):
                    self.widget_wrappers[index].update_config(
                        self.widgets_config[index]
                    )

    def _delete_widget(self, index: int):
        if 0 <= index < len(self.widgets_config):
            reply = QMessageBox.question(
                self, '确认删除', '确定要删除该控件吗？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.widgets_config[index]
                self._save_config()
                self._load_widgets()

    def _on_cols_changed(self, value: int):
        self.config.set('control_panel_cols', value)
        self.config.save()
        self._refresh_grid()

    def _save_config(self):
        self.config.set('control_panel_widgets', self.widgets_config)
        self.config.save()

    def _on_line_received(self, line: str):
        for wrapper in self.widget_wrappers:
            cfg = wrapper.config
            if cfg.get('type') == '仪表盘':
                regex = cfg.get('regex', '')
                if regex:
                    try:
                        m = re.search(regex, line)
                        if m:
                            val = float(m.group(1))
                            wrapper.update_gauge_value(val)
                    except Exception:
                        pass

    def closeEvent(self, e):
        try:
            DataBus.instance().line_received.disconnect(self._on_line_received)
        except Exception:
            pass
        super().closeEvent(e)

