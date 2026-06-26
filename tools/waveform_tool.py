# -*- coding: utf-8 -*-
"""
实时波形图工具 - 专业级示波器功能
基于 PyQt5 + QPainter 纯绘制，无需 pyqtgraph
支持 FireWater 协议、FFT 频谱、触发模式、游标测量等
"""
import time
import csv
from collections import deque
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QPolygon, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSpinBox, QCheckBox, QComboBox, QGridLayout,
    QFileDialog, QMessageBox, QSlider
)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from core.data_bus import DataBus


CHANNEL_COLORS = [
    QColor(59, 130, 246),
    QColor(239, 68, 68),
    QColor(34, 197, 94),
    QColor(249, 115, 22),
    QColor(139, 92, 246),
    QColor(236, 72, 153),
    QColor(14, 165, 233),
    QColor(234, 179, 8),
]

TRIGGER_AUTO = 0
TRIGGER_RISING = 1
TRIGGER_FALLING = 2


class WaveformWidget(QWidget):
    """波形绘制控件 - 纯 QPainter 实现"""

    cursor_moved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setMouseTracking(True)

        self.channels = []
        self.channel_names = []
        self.channel_visible = []
        self.max_points = 1000
        self.sample_rate = 0.0

        self.y_min = -100.0
        self.y_max = 100.0
        self.auto_scale = True

        self.paused = False
        self.show_cursors = False
        self.cursor1_pos = 0.2
        self.cursor2_pos = 0.8
        self._dragging_cursor = 0

        self.show_fft = False
        self.fft_data = None

        self._bg_color = QColor('#F8FAFC')
        self._plot_bg = QColor('#FFFFFF')
        self._grid_color = QColor('#E2E8F0')
        self._grid_major = QColor('#CBD5E1')
        self._text_color = QColor('#475569')
        self._axis_color = QColor('#334155')

        self._pad_left = 60
        self._pad_right = 15
        self._pad_top = 30
        self._pad_bottom = 35

        self.setAutoFillBackground(False)

    def set_channel_count(self, n):
        n = max(1, min(n, 8))
        while len(self.channels) < n:
            self.channels.append(deque(maxlen=self.max_points))
            self.channel_names.append(f'CH{len(self.channels) + 1}')
            self.channel_visible.append(True)
        while len(self.channels) > n:
            self.channels.pop()
            self.channel_names.pop()
            self.channel_visible.pop()
        self.update()

    def set_max_points(self, n):
        self.max_points = n
        new_channels = []
        for ch in self.channels:
            new_ch = deque(ch, maxlen=n)
            new_channels.append(new_ch)
        self.channels = new_channels
        self.update()

    def add_frame(self, values):
        if self.paused:
            return
        for i, v in enumerate(values):
            if i < len(self.channels):
                self.channels[i].append(float(v))
        if self.auto_scale:
            self._auto_range()
        self.update()

    def clear(self):
        for ch in self.channels:
            ch.clear()
        self.fft_data = None
        self.update()

    def _auto_range(self):
        all_vals = []
        for i, ch in enumerate(self.channels):
            if self.channel_visible[i] and len(ch) > 0:
                all_vals.extend(ch)
        if all_vals:
            vmin = min(all_vals)
            vmax = max(all_vals)
            if vmin == vmax:
                vmin -= 1.0
                vmax += 1.0
            margin = (vmax - vmin) * 0.1
            self.y_min = vmin - margin
            self.y_max = vmax + margin

    def set_manual_range(self, y_min, y_max):
        self.auto_scale = False
        self.y_min = y_min
        self.y_max = y_max
        self.update()

    def compute_fft(self, channel_idx=0):
        if not NUMPY_AVAILABLE or channel_idx >= len(self.channels):
            return None
        ch = self.channels[channel_idx]
        if len(ch) < 16:
            return None
        data = np.array(list(ch))
        data = data - np.mean(data)
        n = len(data)
        fft_vals = np.abs(np.fft.rfft(data)) / n
        freqs = np.fft.rfftfreq(n, d=1.0 / max(self.sample_rate, 1.0))
        return freqs, fft_vals

    def _plot_area(self):
        w = self.width()
        h = self.height()
        return (
            self._pad_left,
            self._pad_top,
            w - self._pad_left - self._pad_right,
            h - self._pad_top - self._pad_bottom
        )

    def _value_to_y(self, val, plot_h):
        y_range = self.y_max - self.y_min
        if y_range == 0:
            y_range = 1.0
        return self._pad_top + plot_h * (1.0 - (val - self.y_min) / y_range)

    def _x_to_index(self, x, plot_x, plot_w):
        n_pts = self.max_points
        if plot_w <= 0:
            return 0
        ratio = (x - plot_x) / plot_w
        return int(max(0, min(n_pts - 1, ratio * (n_pts - 1))))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w = self.width()
        h = self.height()
        plot_x, plot_y, plot_w, plot_h = self._plot_area()

        p.fillRect(self.rect(), self._bg_color)

        grad = QLinearGradient(0, plot_y, 0, plot_y + plot_h)
        grad.setColorAt(0, QColor('#FFFFFF'))
        grad.setColorAt(1, QColor('#F1F5F9'))
        p.fillRect(plot_x, plot_y, plot_w, plot_h, grad)

        self._draw_grid(p, plot_x, plot_y, plot_w, plot_h)

        if self.show_fft and NUMPY_AVAILABLE:
            self._draw_fft(p, plot_x, plot_y, plot_w, plot_h)
        else:
            self._draw_waveforms(p, plot_x, plot_y, plot_w, plot_h)

        self._draw_axes(p, plot_x, plot_y, plot_w, plot_h)

        if self.show_cursors and not self.show_fft:
            self._draw_cursors(p, plot_x, plot_y, plot_w, plot_h)

        self._draw_legend(p, plot_x, plot_y, plot_w)

        p.end()

    def _draw_grid(self, p, px, py, pw, ph):
        p.setPen(QPen(self._grid_color, 1))
        n_y = 5
        for i in range(n_y + 1):
            y = py + ph * i / n_y
            p.drawLine(px, int(y), px + pw, int(y))

        n_x = 8
        for i in range(n_x + 1):
            x = px + pw * i / n_x
            p.drawLine(int(x), py, int(x), py + ph)

    def _draw_axes(self, p, px, py, pw, ph):
        p.setPen(QPen(self._axis_color, 1))
        p.drawLine(px, py + ph, px + pw, py + ph)
        p.drawLine(px, py, px, py + ph)

        p.setPen(QPen(self._text_color))
        p.setFont(QFont('Consolas', 9))

        n_y = 5
        for i in range(n_y + 1):
            y = py + ph * i / n_y
            val = self.y_max - (self.y_max - self.y_min) * i / n_y
            p.drawText(2, int(y) + 4, f'{val:7.2f}')

        if self.show_fft:
            n_x = 6
            for i in range(n_x + 1):
                x = px + pw * i / n_x
                if self.sample_rate > 0:
                    freq = (self.sample_rate / 2.0) * i / n_x
                    label = f'{freq:.1f}Hz'
                else:
                    label = f'{i}/{n_x}'
                p.drawText(int(x) - 20, py + ph + 18, label)
        else:
            n_x = 8
            n_pts = max((len(ch) for ch in self.channels), default=0)
            for i in range(n_x + 1):
                x = px + pw * i / n_x
                idx = int(n_pts * i / n_x) if n_pts > 0 else 0
                p.drawText(int(x) - 15, py + ph + 18, f'{idx}')

    def _draw_waveforms(self, p, px, py, pw, ph):
        step_x = pw / max(self.max_points - 1, 1)

        for ch_idx, ch in enumerate(self.channels):
            if not self.channel_visible[ch_idx] or len(ch) < 2:
                continue

            color = CHANNEL_COLORS[ch_idx % len(CHANNEL_COLORS)]
            pen = QPen(color, 1.4)
            p.setPen(pen)

            n_pts = len(ch)
            start_x = px + max(0, (self.max_points - n_pts) * step_x)

            y_range = self.y_max - self.y_min
            if y_range == 0:
                y_range = 1.0

            points = QPolygon()
            for i, val in enumerate(ch):
                x = start_x + i * step_x
                y = py + ph * (1.0 - (val - self.y_min) / y_range)
                points.append(QPoint(int(x), int(y)))

            p.drawPolyline(points)

    def _draw_fft(self, p, px, py, pw, ph):
        if not NUMPY_AVAILABLE:
            return

        fft_result = None
        for i, visible in enumerate(self.channel_visible):
            if visible and i < len(self.channels):
                fft_result = self.compute_fft(i)
                if fft_result is not None:
                    break

        if fft_result is None:
            return

        freqs, fft_vals = fft_result
        if len(freqs) < 2:
            return

        max_val = max(fft_vals) if len(fft_vals) > 0 else 1.0
        if max_val == 0:
            max_val = 1.0

        color = CHANNEL_COLORS[0]
        pen = QPen(color, 1.2)
        p.setPen(pen)

        points = QPolygon()
        n = len(freqs)
        max_freq = freqs[-1] if freqs[-1] > 0 else 1.0

        for i in range(n):
            x = px + pw * (freqs[i] / max_freq)
            y = py + ph * (1.0 - fft_vals[i] / max_val)
            points.append(QPoint(int(x), int(y)))

        p.drawPolyline(points)

        p.setPen(QPen(self._text_color))
        p.setFont(QFont('Consolas', 9))
        peak_idx = int(np.argmax(fft_vals))
        peak_freq = freqs[peak_idx]
        p.drawText(px + 10, py + 40, f'峰值: {peak_freq:.2f} Hz')

    def _draw_cursors(self, p, px, py, pw, ph):
        x1 = px + pw * self.cursor1_pos
        x2 = px + pw * self.cursor2_pos

        pen1 = QPen(QColor(239, 68, 68), 1, Qt.DashLine)
        pen2 = QPen(QColor(34, 197, 94), 1, Qt.DashLine)

        p.setPen(pen1)
        p.drawLine(int(x1), py, int(x1), py + ph)

        p.setPen(pen2)
        p.drawLine(int(x2), py, int(x2), py + ph)

        p.setPen(QPen(self._text_color))
        p.setFont(QFont('Consolas', 9))

        idx1 = self._x_to_index(x1, px, pw)
        idx2 = self._x_to_index(x2, px, pw)
        delta = abs(idx2 - idx1)

        info = f'ΔIdx: {delta}'
        if self.sample_rate > 0:
            delta_t = delta / self.sample_rate
            info += f'  ΔT: {delta_t*1000:.2f}ms'

        p.drawText(px + 10, py + ph - 10, info)

    def _draw_legend(self, p, px, py, pw):
        legend_x = px + 8
        legend_y = py + 8
        p.setFont(QFont('Microsoft YaHei', 9))

        for ch_idx in range(len(self.channels)):
            if not self.channel_visible[ch_idx]:
                continue

            color = CHANNEL_COLORS[ch_idx % len(CHANNEL_COLORS)]
            p.fillRect(legend_x, legend_y, 12, 12, color)
            p.setPen(QPen(self._text_color))
            p.drawText(legend_x + 16, legend_y + 11, self.channel_names[ch_idx])

            legend_x += 90
            if legend_x > px + pw - 90:
                legend_x = px + 8
                legend_y += 20

    def mousePressEvent(self, e: QMouseEvent):
        if not self.show_cursors or self.show_fft:
            return
        px, py, pw, ph = self._plot_area()
        x = e.x()
        if px <= x <= px + pw:
            dist1 = abs(x - (px + pw * self.cursor1_pos))
            dist2 = abs(x - (px + pw * self.cursor2_pos))
            if dist1 < dist2 and dist1 < 10:
                self._dragging_cursor = 1
            elif dist2 < 10:
                self._dragging_cursor = 2
            else:
                self._dragging_cursor = 0

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._dragging_cursor == 0:
            return
        px, py, pw, ph = self._plot_area()
        if pw <= 0:
            return
        ratio = max(0.0, min(1.0, (e.x() - px) / pw))
        if self._dragging_cursor == 1:
            self.cursor1_pos = ratio
        elif self._dragging_cursor == 2:
            self.cursor2_pos = ratio
        self.cursor_moved.emit()
        self.update()

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._dragging_cursor = 0


class WaveformTool(QWidget):
    """实时波形图工具 - 专业级示波器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('实时波形图 - MHcom')
        self.resize(1000, 650)

        self.bus = DataBus.instance()
        self._frame_times = deque(maxlen=100)
        self._trigger_mode = TRIGGER_AUTO
        self._trigger_channel = 0
        self._trigger_level = 0.0
        self._trigger_armed = True
        self._hex_mode = False

        self._build_ui()
        self._connect_bus()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_refresh)
        self._refresh_timer.start(40)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        toolbar = QGroupBox()
        toolbar.setStyleSheet('QGroupBox { border: 1px solid #E2E8F0; border-radius: 6px; }')
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 6, 8, 6)
        tb_layout.setSpacing(10)

        tb_layout.addWidget(QLabel('通道:'))
        self.spn_ch = QSpinBox()
        self.spn_ch.setRange(1, 8)
        self.spn_ch.setValue(4)
        self.spn_ch.valueChanged.connect(self._on_channels_changed)
        tb_layout.addWidget(self.spn_ch)

        tb_layout.addWidget(QLabel('缓冲:'))
        self.spn_buf = QSpinBox()
        self.spn_buf.setRange(100, 10000)
        self.spn_buf.setValue(1000)
        self.spn_buf.setSingleStep(100)
        self.spn_buf.valueChanged.connect(self._on_buf_changed)
        tb_layout.addWidget(self.spn_buf)

        tb_layout.addSpacing(10)

        self.chk_pause = QCheckBox('暂停')
        self.chk_pause.stateChanged.connect(self._on_pause_changed)
        tb_layout.addWidget(self.chk_pause)

        btn_clear = QPushButton('清除')
        btn_clear.clicked.connect(self._on_clear)
        tb_layout.addWidget(btn_clear)

        btn_export = QPushButton('导出CSV')
        btn_export.clicked.connect(self._on_export_csv)
        tb_layout.addWidget(btn_export)

        tb_layout.addSpacing(10)

        self.chk_cursor = QCheckBox('游标')
        self.chk_cursor.stateChanged.connect(self._on_cursor_toggled)
        tb_layout.addWidget(self.chk_cursor)

        self.chk_fft = QCheckBox('FFT')
        self.chk_fft.setEnabled(NUMPY_AVAILABLE)
        self.chk_fft.stateChanged.connect(self._on_fft_toggled)
        tb_layout.addWidget(self.chk_fft)

        if not NUMPY_AVAILABLE:
            self.chk_fft.setToolTip('需要 numpy 库支持')

        tb_layout.addSpacing(10)

        tb_layout.addWidget(QLabel('触发:'))
        self.cmb_trigger = QComboBox()
        self.cmb_trigger.addItems(['自动', '上升沿', '下降沿'])
        self.cmb_trigger.currentIndexChanged.connect(self._on_trigger_changed)
        tb_layout.addWidget(self.cmb_trigger)

        self.chk_auto_scale = QCheckBox('自动量程')
        self.chk_auto_scale.setChecked(True)
        self.chk_auto_scale.stateChanged.connect(self._on_auto_scale)
        tb_layout.addWidget(self.chk_auto_scale)

        tb_layout.addStretch(1)

        main_layout.addWidget(toolbar)

        channel_bar = QGroupBox()
        ch_layout = QHBoxLayout(channel_bar)
        ch_layout.setContentsMargins(8, 4, 8, 4)
        ch_layout.setSpacing(8)

        self.channel_checks = []
        for i in range(8):
            chk = QCheckBox(f'CH{i+1}')
            chk.setChecked(i < 4)
            chk.setStyleSheet(f'QCheckBox {{ color: {CHANNEL_COLORS[i].name()}; font-weight: bold; }}')
            chk.stateChanged.connect(lambda state, idx=i: self._on_channel_toggled(idx, state))
            self.channel_checks.append(chk)
            ch_layout.addWidget(chk)

        ch_layout.addStretch(1)
        main_layout.addWidget(channel_bar)

        self.wave = WaveformWidget()
        self.wave.set_channel_count(self.spn_ch.value())
        self.wave.set_max_points(self.spn_buf.value())
        main_layout.addWidget(self.wave, 1)

        self.status_bar = QLabel('等待数据...')
        self.status_bar.setStyleSheet(
            'color: #64748B; font-size: 12px; '
            'padding: 4px 8px; background: #F1F5F9; border-radius: 4px;'
        )
        main_layout.addWidget(self.status_bar)

    def _connect_bus(self):
        self.bus.line_received.connect(self._on_line_received)
        self.bus.raw_received.connect(self._on_raw_received)

    def _on_line_received(self, line: str):
        if self.chk_pause.isChecked() or self._hex_mode:
            return

        try:
            parts = line.replace(',', ' ').replace('\t', ' ').replace(';', ' ').split()
            vals = []
            for p in parts:
                try:
                    vals.append(float(p))
                except ValueError:
                    continue

            if vals:
                self._feed_frame(vals)
        except Exception:
            pass

    def _on_raw_received(self, data: bytes):
        if self.chk_pause.isChecked() or not self._hex_mode:
            return
        try:
            vals = [float(b) for b in data]
            if vals:
                self._feed_frame(vals)
        except Exception:
            pass

    def _feed_frame(self, vals):
        now = time.time()
        self._frame_times.append(now)

        if len(self._frame_times) >= 2:
            dt = self._frame_times[-1] - self._frame_times[0]
            if dt > 0:
                self.wave.sample_rate = len(self._frame_times) / dt

        if self._trigger_mode == TRIGGER_AUTO:
            self._add_frame(vals)
        else:
            self._check_trigger(vals)

    def _check_trigger(self, vals):
        if self._trigger_channel >= len(vals) or self._trigger_channel >= len(self.wave.channels):
            self._add_frame(vals)
            return

        current_val = vals[self._trigger_channel]
        ch = self.wave.channels[self._trigger_channel]

        if len(ch) == 0:
            self._add_frame(vals)
            return

        last_val = ch[-1]

        triggered = False
        if self._trigger_mode == TRIGGER_RISING:
            if last_val < self._trigger_level <= current_val:
                triggered = True
        elif self._trigger_mode == TRIGGER_FALLING:
            if last_val > self._trigger_level >= current_val:
                triggered = True

        if triggered:
            self._trigger_armed = True

        if self._trigger_armed:
            self._add_frame(vals)
            if len(self.wave.channels[0]) >= self.wave.max_points:
                self._trigger_armed = False

    def _add_frame(self, vals):
        n_ch = self.spn_ch.value()
        frame = list(vals[:n_ch])
        while len(frame) < n_ch:
            frame.append(0.0)
        self.wave.add_frame(frame)

    def _on_refresh(self):
        parts = []

        if self.wave.sample_rate > 0:
            parts.append(f'采样率: {self.wave.sample_rate:.1f} Hz')

        for i in range(min(self.spn_ch.value(), len(self.wave.channels))):
            if not self.wave.channel_visible[i]:
                continue
            ch = self.wave.channels[i]
            if ch:
                val = ch[-1]
                color = CHANNEL_COLORS[i].name()
                parts.append(f'<span style="color:{color}; font-weight:bold;">CH{i+1}: {val:.3f}</span>')

        if parts:
            self.status_bar.setText(' | '.join(parts))
        else:
            self.status_bar.setText('等待数据...')

    def _on_channels_changed(self, n):
        self.wave.set_channel_count(n)
        for i in range(8):
            self.channel_checks[i].setChecked(i < n and self.wave.channel_visible[i] if i < len(self.wave.channel_visible) else i < n)

    def _on_buf_changed(self, n):
        self.wave.set_max_points(n)

    def _on_pause_changed(self, state):
        self.wave.paused = (state == Qt.Checked)

    def _on_clear(self):
        self.wave.clear()
        self._frame_times.clear()
        self.status_bar.setText('已清空')

    def _on_export_csv(self):
        if not self.wave.channels or all(len(ch) == 0 for ch in self.wave.channels):
            QMessageBox.information(self, '导出CSV', '没有可导出的数据')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出CSV数据', 'waveform_data.csv', 'CSV 文件 (*.csv)'
        )
        if not file_path:
            return

        try:
            n_pts = max(len(ch) for ch in self.wave.channels)
            n_ch = len(self.wave.channels)

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                header = ['Index'] + [f'CH{i+1}' for i in range(n_ch)]
                writer.writerow(header)

                for i in range(n_pts):
                    row = [i]
                    for ch in self.wave.channels:
                        if i < len(ch):
                            row.append(ch[i])
                        else:
                            row.append('')
                    writer.writerow(row)

            QMessageBox.information(self, '导出CSV', f'导出成功！\n文件: {file_path}\n共 {n_pts} 个采样点')
        except Exception as e:
            QMessageBox.critical(self, '导出CSV', f'导出失败: {str(e)}')

    def _on_cursor_toggled(self, state):
        self.wave.show_cursors = (state == Qt.Checked)
        self.wave.update()

    def _on_fft_toggled(self, state):
        self.wave.show_fft = (state == Qt.Checked)
        self.wave.update()

    def _on_trigger_changed(self, idx):
        self._trigger_mode = idx
        self._trigger_armed = True

    def _on_auto_scale(self, state):
        self.wave.auto_scale = (state == Qt.Checked)
        if self.wave.auto_scale:
            self.wave._auto_range()
        self.wave.update()

    def _on_channel_toggled(self, idx, state):
        if idx < len(self.wave.channel_visible):
            self.wave.channel_visible[idx] = (state == Qt.Checked)
            if self.wave.auto_scale:
                self.wave._auto_range()
            self.wave.update()

    def closeEvent(self, e):
        try:
            self._refresh_timer.stop()
            self.bus.line_received.disconnect(self._on_line_received)
            self.bus.raw_received.disconnect(self._on_raw_received)
        except Exception:
            pass
        super().closeEvent(e)

