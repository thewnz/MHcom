# -*- coding: utf-8 -*-
"""
数据记录仪工具
- 记录串口数据到文件（二进制/文本）
- 从文件回放数据，支持速度调节
"""
import os
import time
import struct
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QFileDialog, QComboBox, QProgressBar, QMessageBox
)
from core.serial_link import SerialLink
from core.data_bus import DataBus


class DataLoggerTool(QWidget):
    """数据记录仪工具"""

    SPEED_OPTIONS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    BINARY_MAGIC = b'DLOG'
    BINARY_VERSION = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('数据记录仪 - MHcom')
        self.resize(720, 480)

        self.serial = SerialLink.instance()
        self.bus = DataBus.instance()

        self._recording = False
        self._record_start_time = 0
        self._record_bytes = 0
        self._record_file = None
        self._record_format = 'text'
        self._text_encoding = 'utf-8'

        self._playing = False
        self._paused = False
        self._playback_data = []
        self._playback_index = 0
        self._playback_speed = 1.0
        self._playback_timer = QTimer(self)
        self._playback_timer.timeout.connect(self._on_playback_tick)
        self._playback_start_time = 0
        self._playback_elapsed = 0
        self._total_duration = 0

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel('数据记录仪')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        rec_box = QGroupBox('  记录控制')
        rec_lay = QVBoxLayout(rec_box)
        rec_lay.setContentsMargins(10, 8, 10, 10)
        rec_lay.setSpacing(8)

        path_row = QHBoxLayout()
        self.lbl_rec_path = QLabel('未选择文件')
        self.lbl_rec_path.setStyleSheet('color:#64748B;')
        self.lbl_rec_path.setWordWrap(True)
        path_row.addWidget(self.lbl_rec_path, 1)
        btn_browse = QPushButton('浏览...')
        btn_browse.clicked.connect(self._choose_record_file)
        path_row.addWidget(btn_browse)
        rec_lay.addLayout(path_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel('记录格式:'))
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(['文本格式 (.txt)', '二进制格式 (.bin)'])
        self.cmb_format.currentIndexChanged.connect(self._on_format_changed)
        fmt_row.addWidget(self.cmb_format)
        fmt_row.addStretch()
        rec_lay.addLayout(fmt_row)

        btn_row = QHBoxLayout()
        self.btn_start_rec = QPushButton('开始记录')
        self.btn_start_rec.setStyleSheet(
            'background:#10B981; color:white; padding:8px 20px;'
            'border-radius:4px; font-weight:600;'
        )
        self.btn_start_rec.clicked.connect(self._toggle_record)
        btn_row.addWidget(self.btn_start_rec)
        btn_row.addStretch()
        rec_lay.addLayout(btn_row)

        layout.addWidget(rec_box)

        play_box = QGroupBox('  回放控制')
        play_lay = QVBoxLayout(play_box)
        play_lay.setContentsMargins(10, 8, 10, 10)
        play_lay.setSpacing(8)

        file_row = QHBoxLayout()
        self.lbl_play_file = QLabel('未打开文件')
        self.lbl_play_file.setStyleSheet('color:#64748B;')
        self.lbl_play_file.setWordWrap(True)
        file_row.addWidget(self.lbl_play_file, 1)
        btn_open = QPushButton('打开文件')
        btn_open.clicked.connect(self._open_playback_file)
        file_row.addWidget(btn_open)
        play_lay.addLayout(file_row)

        ctrl_row = QHBoxLayout()
        self.btn_play = QPushButton('播放')
        self.btn_play.setStyleSheet(
            'background:#3B82F6; color:white; padding:6px 18px;'
            'border-radius:4px; font-weight:600;'
        )
        self.btn_play.clicked.connect(self._toggle_playback)
        self.btn_play.setEnabled(False)
        ctrl_row.addWidget(self.btn_play)

        self.btn_pause = QPushButton('暂停')
        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_pause.setEnabled(False)
        ctrl_row.addWidget(self.btn_pause)

        btn_stop = QPushButton('停止')
        btn_stop.clicked.connect(self._stop_playback)
        ctrl_row.addWidget(btn_stop)

        ctrl_row.addStretch()
        ctrl_row.addWidget(QLabel('速度:'))
        self.cmb_speed = QComboBox()
        for s in self.SPEED_OPTIONS:
            self.cmb_speed.addItem(f'{s}x', s)
        self.cmb_speed.setCurrentIndex(2)
        self.cmb_speed.currentIndexChanged.connect(self._on_speed_changed)
        ctrl_row.addWidget(self.cmb_speed)
        play_lay.addLayout(ctrl_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat('%p%')
        self.progress_bar.setValue(0)
        play_lay.addWidget(self.progress_bar)

        time_row = QHBoxLayout()
        self.lbl_cur_time = QLabel('00:00.000')
        self.lbl_cur_time.setStyleSheet('font-family: Consolas; color:#475569;')
        time_row.addWidget(self.lbl_cur_time)
        time_row.addStretch()
        self.lbl_total_time = QLabel('00:00.000')
        self.lbl_total_time.setStyleSheet('font-family: Consolas; color:#475569;')
        time_row.addWidget(self.lbl_total_time)
        play_lay.addLayout(time_row)

        layout.addWidget(play_box)

        stat_box = QGroupBox('  统计信息')
        stat_lay = QVBoxLayout(stat_box)
        stat_lay.setContentsMargins(10, 8, 10, 10)
        stat_lay.setSpacing(6)

        self.lbl_stat_bytes = QLabel('已记录字节数: 0 B')
        self.lbl_stat_bytes.setStyleSheet('font-family: Consolas; color:#334155;')
        stat_lay.addWidget(self.lbl_stat_bytes)

        self.lbl_stat_duration = QLabel('记录时长: 00:00.000')
        self.lbl_stat_duration.setStyleSheet('font-family: Consolas; color:#334155;')
        stat_lay.addWidget(self.lbl_stat_duration)

        self.lbl_stat_packets = QLabel('数据块数: 0')
        self.lbl_stat_packets.setStyleSheet('font-family: Consolas; color:#334155;')
        stat_lay.addWidget(self.lbl_stat_packets)

        self.lbl_stat_filesize = QLabel('文件大小: 0 B')
        self.lbl_stat_filesize.setStyleSheet('font-family: Consolas; color:#334155;')
        stat_lay.addWidget(self.lbl_stat_filesize)

        layout.addWidget(stat_box)

        self._stat_timer = QTimer(self)
        self._stat_timer.timeout.connect(self._update_stats)
        self._stat_timer.start(500)

    def _connect_signals(self):
        self.serial.received.connect(self._on_serial_data)

    def _choose_record_file(self):
        if self._recording:
            QMessageBox.warning(self, '提示', '请先停止当前记录')
            return

        fmt = self.cmb_format.currentIndex()
        if fmt == 0:
            filter_str = '文本文件 (*.txt);;所有文件 (*.*)'
            default_ext = '.txt'
        else:
            filter_str = '二进制文件 (*.bin);;所有文件 (*.*)'
            default_ext = '.bin'

        default_name = f'log_{time.strftime("%Y%m%d_%H%M%S")}{default_ext}'
        path, _ = QFileDialog.getSaveFileName(
            self, '选择记录文件', default_name, filter_str
        )
        if path:
            self._record_path = path
            self.lbl_rec_path.setText(path)
            self._update_file_size()

    def _on_format_changed(self, index):
        self._record_format = 'text' if index == 0 else 'binary'

    def _toggle_record(self):
        if self._recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        if not hasattr(self, '_record_path') or not self._record_path:
            QMessageBox.warning(self, '提示', '请先选择记录文件')
            return

        try:
            if self._record_format == 'text':
                self._record_file = open(self._record_path, 'w', encoding=self._text_encoding)
            else:
                self._record_file = open(self._record_path, 'wb')
                self._record_file.write(self.BINARY_MAGIC)
                self._record_file.write(struct.pack('<I', self.BINARY_VERSION))
                self._record_file.write(struct.pack('<Q', 0))
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开文件: {e}')
            return

        self._recording = True
        self._record_start_time = time.time()
        self._record_bytes = 0
        self._record_packets = 0

        self.btn_start_rec.setText('停止记录')
        self.btn_start_rec.setStyleSheet(
            'background:#EF4444; color:white; padding:8px 20px;'
            'border-radius:4px; font-weight:600;'
        )
        self.lbl_rec_path.setStyleSheet('color:#10B981;')

    def _stop_record(self):
        self._recording = False

        if self._record_file:
            try:
                self._record_file.close()
            except Exception:
                pass
            self._record_file = None

        self.btn_start_rec.setText('开始记录')
        self.btn_start_rec.setStyleSheet(
            'background:#10B981; color:white; padding:8px 20px;'
            'border-radius:4px; font-weight:600;'
        )
        self.lbl_rec_path.setStyleSheet('color:#64748B;')
        self._update_file_size()

    def _on_serial_data(self, data: bytes):
        if not self._recording or not self._record_file:
            return

        ts = time.time() - self._record_start_time
        self._record_bytes += len(data)
        self._record_packets += 1

        try:
            if self._record_format == 'text':
                hex_str = data.hex(' ').upper()
                self._record_file.write(f'[{ts:.3f}] {hex_str}\n')
                self._record_file.flush()
            else:
                ts_ms = int(ts * 1000)
                length = len(data)
                self._record_file.write(struct.pack('<I', ts_ms))
                self._record_file.write(struct.pack('<I', length))
                self._record_file.write(data)
                self._record_file.flush()
        except Exception as e:
            self._stop_record()
            QMessageBox.critical(self, '记录错误',
                f'写入文件时出错，记录已停止：\n{e}')

    def _open_playback_file(self):
        if self._playing:
            self._stop_playback()

        path, _ = QFileDialog.getOpenFileName(
            self, '选择回放文件', '',
            '数据日志文件 (*.txt *.bin);;所有文件 (*.*)'
        )
        if not path:
            return

        try:
            self._playback_data = []
            ext = os.path.splitext(path)[1].lower()

            file_size = os.path.getsize(path)
            if file_size > 20 * 1024 * 1024:  # 超过 20MB 提示
                QMessageBox.warning(self, '大文件警告',
                    f'文件大小 {file_size / (1024*1024):.1f} MB，回放可能占用较多内存。\n建议使用较小的记录文件。')

            if ext == '.bin':
                self._load_binary_file(path)
            else:
                self._load_text_file(path)

            if not self._playback_data:
                QMessageBox.warning(self, '提示', '文件中没有可回放的数据')
                return

            self._playback_path = path
            self.lbl_play_file.setText(path)
            self.btn_play.setEnabled(True)
            self._playback_index = 0
            self._playback_elapsed = 0

            if self._playback_data:
                self._total_duration = self._playback_data[-1][0]
            else:
                self._total_duration = 0

            self.lbl_total_time.setText(self._format_time(self._total_duration))
            self.lbl_cur_time.setText('00:00.000')
            self.progress_bar.setValue(0)

            self._update_playback_file_info(path)

        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法加载文件: {e}')

    def _load_text_file(self, path):
        with open(path, 'r', encoding=self._text_encoding, errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('[') and ']' in line:
                    end = line.index(']')
                    try:
                        ts = float(line[1:end])
                        hex_part = line[end + 1:].strip()
                        if hex_part:
                            data = bytes.fromhex(hex_part.replace(' ', ''))
                            self._playback_data.append((ts, data))
                    except (ValueError, IndexError):
                        continue

    def _load_binary_file(self, path):
        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic != self.BINARY_MAGIC:
                raise ValueError('不是有效的二进制日志文件')
            version = struct.unpack('<I', f.read(4))[0]
            if version != self.BINARY_VERSION:
                raise ValueError(f'不支持的版本: {version}')
            _ = f.read(8)

            while True:
                header = f.read(8)
                if len(header) < 8:
                    break
                ts_ms, length = struct.unpack('<II', header)
                data = f.read(length)
                if len(data) < length:
                    break
                ts = ts_ms / 1000.0
                self._playback_data.append((ts, data))

    def _toggle_playback(self):
        if self._playing:
            self._pause_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        if not self._playback_data:
            return

        if self._playback_index >= len(self._playback_data):
            self._playback_index = 0
            self._playback_elapsed = 0

        self._playing = True
        self._paused = False
        self._playback_start_time = time.time() - (self._playback_elapsed / self._playback_speed)

        self.btn_play.setText('播放中')
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)

        self._playback_timer.start(10)

    def _pause_playback(self):
        self._playing = False
        self._paused = True
        self._playback_timer.stop()

        self.btn_play.setText('继续')
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)

    def _toggle_pause(self):
        if self._playing:
            self._pause_playback()

    def _stop_playback(self):
        self._playing = False
        self._paused = False
        self._playback_timer.stop()
        self._playback_index = 0
        self._playback_elapsed = 0

        self.btn_play.setText('播放')
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_cur_time.setText('00:00.000')

    def _on_playback_tick(self):
        if not self._playing or not self._playback_data:
            return

        current_time = time.time()
        elapsed = (current_time - self._playback_start_time) * self._playback_speed
        self._playback_elapsed = elapsed

        while self._playback_index < len(self._playback_data):
            ts, data = self._playback_data[self._playback_index]
            if ts <= elapsed:
                self.bus.publish_serial_rx(data)
                self._playback_index += 1
            else:
                break

        if self._total_duration > 0:
            progress = min(100, int(elapsed / self._total_duration * 100))
            self.progress_bar.setValue(progress)
        self.lbl_cur_time.setText(self._format_time(elapsed))

        if self._playback_index >= len(self._playback_data):
            self._stop_playback()
            self.btn_play.setText('播放')
            self.btn_play.setEnabled(True)

    def _on_speed_changed(self, index):
        new_speed = self.SPEED_OPTIONS[index]
        if self._playing:
            self._playback_start_time = time.time() - (self._playback_elapsed / new_speed)
        self._playback_speed = new_speed

    def _update_stats(self):
        if self._recording:
            self.lbl_stat_bytes.setText(f'已记录字节数: {self._format_size(self._record_bytes)}')
            elapsed = time.time() - self._record_start_time
            self.lbl_stat_duration.setText(f'记录时长: {self._format_time(elapsed)}')
            self.lbl_stat_packets.setText(f'数据块数: {self._record_packets}')
            self._update_file_size()

    def _update_file_size(self):
        if hasattr(self, '_record_path') and self._record_path and os.path.exists(self._record_path):
            try:
                size = os.path.getsize(self._record_path)
                self.lbl_stat_filesize.setText(f'文件大小: {self._format_size(size)}')
            except Exception:
                pass

    def _update_playback_file_info(self, path):
        try:
            size = os.path.getsize(path)
            self.lbl_stat_filesize.setText(f'文件大小: {self._format_size(size)}')
            self.lbl_stat_bytes.setText(f'数据块数: {len(self._playback_data)}')
            total_bytes = sum(len(d[1]) for d in self._playback_data)
            self.lbl_stat_packets.setText(f'总字节数: {self._format_size(total_bytes)}')
            self.lbl_stat_duration.setText(f'总时长: {self._format_time(self._total_duration)}')
        except Exception:
            pass

    @staticmethod
    def _format_size(size_bytes):
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.2f} KB'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.2f} MB'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'

    @staticmethod
    def _format_time(seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f'{mins:02d}:{secs:02d}.{ms:03d}'

    def closeEvent(self, e):
        if self._recording:
            self._stop_record()
        if self._playing:
            self._stop_playback()
        try:
            self.serial.received.disconnect(self._on_serial_data)
        except Exception:
            pass
        super().closeEvent(e)

