# -*- coding: utf-8 -*-
"""
模式A: 3D 舵机云台调试
- 3D 舵机云台渲染
- 串口通信（单例模式）
- 角度控制 (Pan/Tilt)
- 3D 模型导入 + 自动调整舵机范围
- 快捷预设
- 工具按钮区域
- 状态栏信息
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QComboBox, QPushButton, QSlider, QSpinBox, QCheckBox, QPlainTextEdit,
    QFileDialog, QMessageBox, QSplitter, QScrollArea, QSizePolicy
)

from widgets.gimbal_gl_widget import GimbalGLWidget
from model.model_loader import ModelLoader
from model.model_analyzer import ModelAnalyzer
from core.serial_link import SerialLink, SerialOpenWorker
from core.data_bus import DataBus


class GimbalPanel(QWidget):
    """3D 舵机云台调试面板"""
    request_tool = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.slink = SerialLink.instance()
        self.bus = DataBus.instance()
        self._pending_pan = 0
        self._pending_tilt = 0
        self._servo_pending = False
        self._recv_buf = b''
        self._last_send_time = 0
        self._open_thread = None
        self._open_worker = None
        # 舵机指令防抖计时器：拖动滑块时延迟 60ms 发送，避免高频指令洪泛
        self._servo_send_timer = QTimer(self)
        self._servo_send_timer.setSingleShot(True)
        self._servo_send_timer.setInterval(60)
        self._servo_send_timer.timeout.connect(self._send_servo_impl)
        self._build_ui()
        self._connect_signals()
        self._refresh_ports()
        self._sync_ui_from_serial()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        cfg_bar = self._build_config_bar()
        root.addWidget(cfg_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = self._build_left()
        right = self._build_right()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([700, 480])
        root.addWidget(splitter, 1)

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
            '4800', '9600', '19200', '38400', '57600', '115200',
            '230400', '460800', '921600'
        ])
        self.cmb_baud.setCurrentText('115200')
        self.cmb_baud.setMinimumWidth(100)
        lay.addWidget(self.cmb_baud)

        lay.addWidget(QLabel('数据位:'))
        self.cmb_dbits = QComboBox()
        self.cmb_dbits.addItems(['8', '7', '6', '5'])
        self.cmb_dbits.setCurrentIndex(0)
        self.cmb_dbits.setMaximumWidth(60)
        lay.addWidget(self.cmb_dbits)

        lay.addWidget(QLabel('校验:'))
        self.cmb_parity = QComboBox()
        self.cmb_parity.addItems(['无', '奇', '偶', 'Mark', 'Space'])
        self.cmb_parity.setMaximumWidth(70)
        lay.addWidget(self.cmb_parity)

        lay.addWidget(QLabel('停止位:'))
        self.cmb_sbits = QComboBox()
        self.cmb_sbits.addItems(['1', '1.5', '2'])
        self.cmb_sbits.setMaximumWidth(60)
        lay.addWidget(self.cmb_sbits)

        lay.addWidget(QLabel('流控:'))
        self.cmb_flow = QComboBox()
        self.cmb_flow.addItems(['无', 'RTS/CTS', 'XON/XOFF', 'DSR/DTR'])
        self.cmb_flow.setMaximumWidth(90)
        lay.addWidget(self.cmb_flow)

        lay.addSpacing(8)
        self.btn_open = QPushButton('打开串口')
        self.btn_open.setMinimumWidth(90)
        self.btn_open.setStyleSheet(
            'background:#10B981; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        self.btn_open.clicked.connect(self._toggle_port)
        lay.addWidget(self.btn_open)

        lay.addStretch()
        return bar

    def _build_left(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self._gb_3d(), 3)
        lay.addWidget(self._gb_serial_io(), 2)
        return w

    def _gb_3d(self):
        gb = QGroupBox('  3D VIEW')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(8, 6, 8, 8)
        lay.setSpacing(4)

        self.gl = GimbalGLWidget()
        self.gl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self.gl, 1)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        bar.addStretch()
        self.chk_demo = QCheckBox('动画演示')
        self.chk_demo.stateChanged.connect(self._toggle_demo)
        bar.addWidget(self.chk_demo)
        tip = QLabel('左键旋转  |  右键平移  |  滚轮缩放')
        tip.setStyleSheet('color:#6B7280; font-size:12px;')
        bar.addWidget(tip)
        bar.addStretch()
        lay.addLayout(bar)
        return gb

    def _gb_serial_io(self):
        gb = QGroupBox('  串口收发')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(8, 6, 8, 8)
        lay.setSpacing(6)

        cfg_row = QHBoxLayout()
        cfg_row.addWidget(QLabel('发送:'))
        self.cmb_smode = QComboBox()
        self.cmb_smode.addItems(['文本', 'HEX'])
        self.cmb_smode.setMaximumWidth(70)
        cfg_row.addWidget(self.cmb_smode)
        self.cmb_senc = QComboBox()
        self.cmb_senc.addItems(['UTF-8', 'GBK', 'GB2312', 'GB18030', 'ASCII', 'ISO-8859-1', 'Big5'])
        self.cmb_senc.setMaximumWidth(80)
        cfg_row.addWidget(self.cmb_senc)
        cfg_row.addSpacing(10)
        cfg_row.addWidget(QLabel('接收:'))
        self.cmb_rmode = QComboBox()
        self.cmb_rmode.addItems(['文本', 'HEX'])
        self.cmb_rmode.setMaximumWidth(70)
        cfg_row.addWidget(self.cmb_rmode)
        cfg_row.addStretch()
        self.chk_hexd = QCheckBox('HEX显示')
        cfg_row.addWidget(self.chk_hexd)
        lay.addLayout(cfg_row)

        self.txt_send = QPlainTextEdit()
        self.txt_send.setPlaceholderText('输入要发送的文本或 HEX 数据...')
        self.txt_send.setMaximumHeight(64)
        lay.addWidget(self.txt_send)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        bclr = QPushButton('清空')
        bclr.clicked.connect(lambda: self.txt_send.clear())
        btn_row.addWidget(bclr)
        bsend = QPushButton('发送')
        bsend.clicked.connect(self._do_send)
        btn_row.addWidget(bsend)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self.txt_recv = QPlainTextEdit()
        self.txt_recv.setReadOnly(True)
        self.txt_recv.setPlaceholderText('等待接收数据...')
        self.txt_recv.setMaximumHeight(100)
        lay.addWidget(self.txt_recv)

        bar2 = QHBoxLayout()
        bar2.addStretch()
        bclr2 = QPushButton('清空接收')
        bclr2.clicked.connect(lambda: self.txt_recv.clear())
        bar2.addWidget(bclr2)
        lay.addLayout(bar2)
        return gb

    def _build_right(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setMinimumWidth(420)
        w = QWidget()
        w.setMinimumWidth(420)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 6)
        lay.setSpacing(6)
        lay.addWidget(self._gb_model_import())
        lay.addWidget(self._gb_servo())
        lay.addWidget(self._gb_preset())
        lay.addStretch()
        sa.setWidget(w)
        return sa

    def _gb_model_import(self):
        gb = QGroupBox('  3D模型导入')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(8)

        self.lbl_model_path = QLabel('未选择模型文件')
        self.lbl_model_path.setStyleSheet('color:#6B7280; font-size:13px;')
        lay.addWidget(self.lbl_model_path)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_import = QPushButton('导入模型')
        btn_import.clicked.connect(self._import_model)
        btn_row.addWidget(btn_import)
        btn_clear = QPushButton('清除模型')
        btn_clear.clicked.connect(self._clear_model)
        btn_row.addWidget(btn_clear)
        lay.addLayout(btn_row)

        self.chk_auto_adjust = QCheckBox('根据模型自动调整舵机范围')
        self.chk_auto_adjust.setChecked(True)
        lay.addWidget(self.chk_auto_adjust)

        info_rows = [
            ('顶点数:', 'lbl_verts'),
            ('面数:', 'lbl_faces'),
            ('尺寸 X:', 'lbl_dim_x'),
            ('尺寸 Y:', 'lbl_dim_y'),
            ('尺寸 Z:', 'lbl_dim_z'),
            ('Pan 范围:', 'lbl_pan_range'),
            ('Tilt 范围:', 'lbl_tilt_range'),
        ]
        info_group = QGroupBox('模型信息')
        info_grid = QGridLayout(info_group)
        info_grid.setContentsMargins(8, 6, 8, 6)
        info_grid.setSpacing(6)

        self.model_info_labels = []
        for i, (label, attr) in enumerate(info_rows):
            lbl = QLabel(label)
            lbl.setStyleSheet('color:#6B7280; font-size:13px;')
            info_grid.addWidget(lbl, i, 0)
            val = QLabel('-')
            val.setStyleSheet('color:#2563EB; font-size:13px; font-family: monospace;')
            setattr(self, attr, val)
            info_grid.addWidget(val, i, 1)
            self.model_info_labels.append(val)

        lay.addWidget(info_group)
        return gb

    def _gb_servo(self):
        gb = QGroupBox('  舵机控制 (Pan / Tilt)')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(8)

        pan_row = QHBoxLayout()
        pan_row.addWidget(QLabel('Pan:'))
        self.sld_pan = QSlider(Qt.Horizontal)
        self.sld_pan.setRange(-135, 135)
        self.sld_pan.setValue(0)
        self.sld_pan.valueChanged.connect(self._on_pan_changed)
        pan_row.addWidget(self.sld_pan, 1)
        self.spn_pan = QSpinBox()
        self.spn_pan.setRange(-135, 135)
        self.spn_pan.setValue(0)
        self.spn_pan.valueChanged.connect(self._on_pan_changed)
        self.spn_pan.setMaximumWidth(80)
        pan_row.addWidget(self.spn_pan)
        self.lbl_pan = QLabel('0°')
        self.lbl_pan.setStyleSheet('color:#2563EB; font-weight:600; min-width:40px;')
        pan_row.addWidget(self.lbl_pan)
        lay.addLayout(pan_row)

        tilt_row = QHBoxLayout()
        tilt_row.addWidget(QLabel('Tilt:'))
        self.sld_tilt = QSlider(Qt.Horizontal)
        self.sld_tilt.setRange(-30, 180)
        self.sld_tilt.setValue(90)
        self.sld_tilt.valueChanged.connect(self._on_tilt_changed)
        tilt_row.addWidget(self.sld_tilt, 1)
        self.spn_tilt = QSpinBox()
        self.spn_tilt.setRange(-30, 180)
        self.spn_tilt.setValue(90)
        self.spn_tilt.valueChanged.connect(self._on_tilt_changed)
        self.spn_tilt.setMaximumWidth(80)
        tilt_row.addWidget(self.spn_tilt)
        self.lbl_tilt = QLabel('90°')
        self.lbl_tilt.setStyleSheet('color:#2563EB; font-weight:600; min-width:40px;')
        tilt_row.addWidget(self.lbl_tilt)
        lay.addLayout(tilt_row)

        proto_row = QHBoxLayout()
        proto_row.addWidget(QLabel('协议:'))
        self.cmb_proto = QComboBox()
        self.cmb_proto.addItems([
            '#PAN,TILT\\r\\n',
            'P{p} T{t}\\r\\n',
            'pan={p},tilt={t}\\r\\n',
            '自定义 HEX (预留)',
        ])
        self.cmb_proto.setToolTip('选择舵机指令协议格式。"自定义 HEX"为预留选项，暂不支持')
        proto_row.addWidget(self.cmb_proto, 1)
        lay.addLayout(proto_row)

        step_row = QHBoxLayout()
        step_row.addWidget(QLabel('步进:'))
        for v in (1, 5, 10, 30):
            b = QPushButton(f'±{v}°')
            b.clicked.connect(lambda _, val=v: self._step(val))
            step_row.addWidget(b)
        step_row.addStretch()
        lay.addLayout(step_row)

        # 范围设置（可展开）
        self.btn_range_toggle = QPushButton('▼ 范围设置')
        self.btn_range_toggle.setCheckable(True)
        self.btn_range_toggle.setStyleSheet('text-align:left; padding:4px 8px;')
        self.btn_range_toggle.toggled.connect(self._toggle_range_settings)
        lay.addWidget(self.btn_range_toggle)

        self.range_widget = QWidget()
        rlay = QGridLayout(self.range_widget)
        rlay.setContentsMargins(8, 4, 8, 8)
        rlay.setSpacing(6)

        rlay.addWidget(QLabel('Pan 最小:'), 0, 0)
        self.spn_pan_min = QSpinBox()
        self.spn_pan_min.setRange(-180, 180)
        self.spn_pan_min.setValue(-135)
        self.spn_pan_min.setMaximumWidth(90)
        rlay.addWidget(self.spn_pan_min, 0, 1)

        rlay.addWidget(QLabel('Pan 最大:'), 0, 2)
        self.spn_pan_max = QSpinBox()
        self.spn_pan_max.setRange(-180, 180)
        self.spn_pan_max.setValue(135)
        self.spn_pan_max.setMaximumWidth(90)
        rlay.addWidget(self.spn_pan_max, 0, 3)

        rlay.addWidget(QLabel('Tilt 最小:'), 1, 0)
        self.spn_tilt_min = QSpinBox()
        self.spn_tilt_min.setRange(-90, 270)
        self.spn_tilt_min.setValue(-30)
        self.spn_tilt_min.setMaximumWidth(90)
        rlay.addWidget(self.spn_tilt_min, 1, 1)

        rlay.addWidget(QLabel('Tilt 最大:'), 1, 2)
        self.spn_tilt_max = QSpinBox()
        self.spn_tilt_max.setRange(-90, 270)
        self.spn_tilt_max.setValue(180)
        self.spn_tilt_max.setMaximumWidth(90)
        rlay.addWidget(self.spn_tilt_max, 1, 3)

        btn_apply_range = QPushButton('应用范围')
        btn_apply_range.setStyleSheet('background:#2563EB; color:white; padding:4px 12px;')
        btn_apply_range.clicked.connect(self._apply_custom_range)
        rlay.addWidget(btn_apply_range, 2, 0, 1, 2)

        btn_reset_range = QPushButton('重置默认')
        btn_reset_range.clicked.connect(self._reset_default_range)
        rlay.addWidget(btn_reset_range, 2, 2, 1, 2)

        self.range_widget.hide()
        lay.addWidget(self.range_widget)

        zero_row = QHBoxLayout()
        b_zero = QPushButton('归零 (中心)')
        b_zero.setStyleSheet('background:#EA580C; color:white; font-weight:600;')
        b_zero.clicked.connect(self._zero)
        zero_row.addWidget(b_zero)
        zero_row.addStretch()
        lay.addLayout(zero_row)

        return gb

    def _gb_preset(self):
        gb = QGroupBox('  快捷预设')
        lay = QGridLayout(gb)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(6)
        presets = [
            ('中心', 0, 90, 'Pan: 0°, Tilt: 90°'),
            ('左看', -90, 90, 'Pan: -90°, Tilt: 90°'),
            ('右看', 90, 90, 'Pan: 90°, Tilt: 90°'),
            ('上看', 0, 150, 'Pan: 0°, Tilt: 150°'),
            ('下看', 0, 30, 'Pan: 0°, Tilt: 30°'),
            ('左上看', -45, 135, 'Pan: -45°, Tilt: 135°'),
            ('右上看', 45, 135, 'Pan: 45°, Tilt: 135°'),
            ('扫地模式', 0, 30, 'Pan: 0°, Tilt: 30°'),
        ]
        for i, (name, p, t, tip) in enumerate(presets):
            b = QPushButton(name)
            b.setToolTip(tip)
            b.clicked.connect(lambda _, pp=p, tt=t: self._set_angles(pp, tt))
            lay.addWidget(b, i // 4, i % 4)
        return gb

    def _connect_signals(self):
        self.slink.received.connect(self._on_received)
        self.slink.sent.connect(self._on_sent)
        self.slink.state_changed.connect(self._on_state_changed)
        self.slink.rx_count_changed.connect(self._on_rx_count)
        self.slink.tx_count_changed.connect(self._on_tx_count)

    def _sync_ui_from_serial(self):
        if self.slink.is_open:
            self._update_ui_opened(self.slink.port_name, self.slink.baudrate)
            self.lbl_rx_cnt.setText(f'RX: {self.slink.rx_count}')
            self.lbl_tx_cnt.setText(f'TX: {self.slink.tx_count}')
        else:
            self._update_ui_closed()

    def _refresh_ports(self):
        ports = SerialLink.list_ports()
        self.cmb_port.clear()
        self.cmb_port.addItems(ports if ports else ['COM1'])
        # 自动选中第一个可用端口（优先 COM3，这是最常见的 USB 转串口）
        if ports:
            if 'COM3' in ports:
                self.cmb_port.setCurrentText('COM3')
            else:
                self.cmb_port.setCurrentIndex(0)

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

            dbits = int(self.cmb_dbits.currentText())
            sbits = self.cmb_sbits.currentText()
            parity = self.cmb_parity.currentText()
            flow = self.cmb_flow.currentText()

            rtscts = (flow == 'RTS/CTS')
            xonxoff = (flow == 'XON/XOFF')
            dsrdtr = (flow == 'DSR/DTR')

            self.btn_open.setEnabled(False)
            self.btn_open.setText('打开中...')

            # 清理上一次可能残留的线程，防止泄漏
            if self._open_thread and self._open_thread.isRunning():
                self._open_thread.quit()
                self._open_thread.wait(1000)

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
        self.btn_open.setEnabled(True)
        self.btn_open.setText('打开串口')
        self.btn_open.setStyleSheet(
            'background:#10B981; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        QMessageBox.critical(self, '打开失败', msg)

    def _update_ui_opened(self, port: str, baud: int):
        self.btn_open.setEnabled(True)
        self.btn_open.setText('关闭串口')
        self.btn_open.setStyleSheet(
            'background:#EF4444; color:white; font-weight:600;'
            'padding:5px 12px; border-radius:4px;'
        )
        self.lbl_port_status.setText(f'● {port} @ {baud}')
        self.lbl_port_status.setStyleSheet('color:#10B981; font-weight:600;')

    def _update_ui_closed(self):
        self.btn_open.setEnabled(True)
        self.btn_open.setText('打开串口')
        self.btn_open.setStyleSheet(
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

    def _do_send(self):
        if not self.slink.is_open:
            QMessageBox.warning(self, '提示', '请先打开串口')
            return
        text = self.txt_send.toPlainText()
        if not text:
            return
        try:
            if self.cmb_smode.currentText() == 'HEX':
                data = bytes(int(p, 16) for p in text.split() if p)
            else:
                enc = self.cmb_senc.currentText().lower()
                data = text.encode(enc, errors='replace')
            self.slink.send(data)
            self.bus.publish_serial_tx(data)
        except Exception as e:
            QMessageBox.warning(self, '发送失败', str(e))

    def _on_received(self, data: bytes):
        if self.cmb_rmode.currentText() == 'HEX':
            text = ' '.join(f'{b:02X}' for b in data)
        else:
            try:
                enc = self.cmb_senc.currentText().lower()
                text = data.decode(enc, errors='replace')
            except Exception:
                text = ' '.join(f'{b:02X}' for b in data)
        self.txt_recv.appendPlainText(text)
        self.bus.publish_serial_rx(data)

    def _on_sent(self, n: int):
        pass

    def _on_pan_changed(self, v):
        self.sld_pan.blockSignals(True)
        self.spn_pan.blockSignals(True)
        sender = self.sender()
        if sender is self.sld_pan:
            self.spn_pan.setValue(v)
        elif sender is self.spn_pan:
            self.sld_pan.setValue(v)
        self.sld_pan.blockSignals(False)
        self.spn_pan.blockSignals(False)
        self.lbl_pan.setText(f'{v}°')
        self.gl.set_angles(self.sld_pan.value(), self.sld_tilt.value())
        self._send_servo()

    def _on_tilt_changed(self, v):
        self.sld_tilt.blockSignals(True)
        self.spn_tilt.blockSignals(True)
        sender = self.sender()
        if sender is self.sld_tilt:
            self.spn_tilt.setValue(v)
        elif sender is self.spn_tilt:
            self.sld_tilt.setValue(v)
        self.sld_tilt.blockSignals(False)
        self.spn_tilt.blockSignals(False)
        self.lbl_tilt.setText(f'{v}°')
        self.gl.set_angles(self.sld_pan.value(), self.sld_tilt.value())
        self._send_servo()

    def _set_angles(self, pan: int, tilt: int):
        self.sld_pan.setValue(pan)
        self.sld_tilt.setValue(tilt)
        self._send_servo()

    def _step(self, val: int):
        self.spn_pan.setValue(self.spn_pan.value() + val)

    def _zero(self):
        self._set_angles(0, 90)

    def _toggle_demo(self, state):
        self.gl.set_demo(bool(state))

    def _send_servo(self):
        """舵机指令发送入口（防抖版）：每次调用重置计时器，60ms 内无新调用才实际发送"""
        self._servo_send_timer.start()

    def _send_servo_impl(self):
        """实际执行舵机指令发送"""
        if not self.slink.is_open:
            return
        pan = self.sld_pan.value()
        tilt = self.sld_tilt.value()
        proto = self.cmb_proto.currentText()
        if proto == '自定义 HEX':
            return
        try:
            if proto.startswith('#'):
                cmd = f'#PAN,{pan}\r\n#TILT,{tilt}\r\n'.encode('utf-8')
            else:
                cmd = proto.format(p=pan, t=tilt).encode('utf-8')
            self.slink.send(cmd)
        except Exception:
            pass

    def _import_model(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, '选择3D模型文件', '',
            '3D模型文件 (*.obj *.stl);;OBJ文件 (*.obj);;STL文件 (*.stl)'
        )
        if not filepath:
            return
        try:
            model = ModelLoader.load_model(filepath)
            analysis = ModelAnalyzer.analyze(model)
            if analysis:
                limits = ModelAnalyzer.calculate_servo_limits(analysis)
                self.lbl_model_path.setText(os.path.basename(filepath))
                self.lbl_verts.setText(str(analysis['vertex_count']))
                self.lbl_faces.setText(str(analysis['face_count']))
                self.lbl_dim_x.setText(f"{analysis['dimensions'][0]:.3f}")
                self.lbl_dim_y.setText(f"{analysis['dimensions'][1]:.3f}")
                self.lbl_dim_z.setText(f"{analysis['dimensions'][2]:.3f}")
                self.lbl_pan_range.setText(f"{limits['pan_min']}° ~ {limits['pan_max']}°")
                self.lbl_tilt_range.setText(f"{limits['tilt_min']}° ~ {limits['tilt_max']}°")

                if analysis['max_dim'] > 0:
                    scale_factor = 0.3 / analysis['max_dim']
                else:
                    scale_factor = 1.0
                offset = [0, limits['recommended_height'] + 0.1, 0]
                self.gl.set_external_model(model, offset, scale_factor)

                if self.chk_auto_adjust.isChecked():
                    self._adjust_servo_limits(limits)
                QMessageBox.information(self, '导入成功',
                    f'模型导入成功！\n顶点数: {analysis["vertex_count"]}\n面数: {analysis["face_count"]}')
            else:
                QMessageBox.warning(self, '导入失败', '无法分析模型文件')
        except Exception as e:
            QMessageBox.critical(self, '导入失败', f'加载模型时出错: {e}')

    def _clear_model(self):
        self.gl.clear_external_model()
        self.lbl_model_path.setText('未选择模型文件')
        for lbl in self.model_info_labels:
            lbl.setText('-')

    def _adjust_servo_limits(self, limits):
        pan_min, pan_max = limits['pan_min'], limits['pan_max']
        tilt_min, tilt_max = limits['tilt_min'], limits['tilt_max']
        self.spn_pan_min.setValue(pan_min)
        self.spn_pan_max.setValue(pan_max)
        self.spn_tilt_min.setValue(tilt_min)
        self.spn_tilt_max.setValue(tilt_max)
        self._apply_range(pan_min, pan_max, tilt_min, tilt_max)

    def _toggle_range_settings(self, checked: bool):
        self.range_widget.setVisible(checked)
        self.btn_range_toggle.setText('▲ 范围设置' if checked else '▼ 范围设置')

    def _apply_custom_range(self):
        pan_min = self.spn_pan_min.value()
        pan_max = self.spn_pan_max.value()
        tilt_min = self.spn_tilt_min.value()
        tilt_max = self.spn_tilt_max.value()
        if pan_min >= pan_max:
            QMessageBox.warning(self, '提示', 'Pan 最小值必须小于最大值')
            return
        if tilt_min >= tilt_max:
            QMessageBox.warning(self, '提示', 'Tilt 最小值必须小于最大值')
            return
        self._apply_range(pan_min, pan_max, tilt_min, tilt_max)

    def _reset_default_range(self):
        self.spn_pan_min.setValue(-135)
        self.spn_pan_max.setValue(135)
        self.spn_tilt_min.setValue(-30)
        self.spn_tilt_max.setValue(180)
        self._apply_range(-135, 135, -30, 180)

    def _apply_range(self, pan_min, pan_max, tilt_min, tilt_max):
        for w in (self.sld_pan, self.spn_pan):
            w.blockSignals(True)
            w.setRange(pan_min, pan_max)
            w.setValue(max(pan_min, min(pan_max, w.value())))
            w.blockSignals(False)
        for w in (self.sld_tilt, self.spn_tilt):
            w.blockSignals(True)
            w.setRange(tilt_min, tilt_max)
            w.setValue(max(tilt_min, min(tilt_max, w.value())))
            w.blockSignals(False)
        self.lbl_pan.setText(f'{self.sld_pan.value()}°')
        self.lbl_tilt.setText(f'{self.sld_tilt.value()}°')
        self.gl.set_angles(self.sld_pan.value(), self.sld_tilt.value())

    def closeEvent(self, e):
        super().closeEvent(e)
