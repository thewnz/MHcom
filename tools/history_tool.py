# -*- coding: utf-8 -*-
"""发送历史工具"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QLineEdit, QComboBox
)
from core.data_bus import DataBus
from core.serial_link import SerialLink
from config.settings import AppConfig


class HistoryTool(QWidget):
    """发送历史工具"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('发送历史 - MHcom')
        self.resize(720, 560)
        self._tx_count = 0
        self.config = AppConfig()
        self._build_ui()
        self._load_persisted_history()
        DataBus.instance().raw_sent.connect(self._on_tx)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('发送历史记录')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        filter_box = QGroupBox('  筛选')
        filter_lay = QHBoxLayout(filter_box)
        filter_lay.setContentsMargins(12, 10, 12, 12)

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText('搜索历史记录...')
        self.txt_filter.textChanged.connect(self._filter)
        filter_lay.addWidget(self.txt_filter, 1)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(['文本显示', 'HEX显示'])
        self.cmb_mode.currentIndexChanged.connect(self._refresh_list)
        filter_lay.addWidget(self.cmb_mode)

        layout.addWidget(filter_box)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            'QListWidget { border: 1px solid #E2E8F0; border-radius: 6px; padding: 4px; }'
            'QListWidget::item { padding: 6px 8px; border-bottom: 1px solid #F1F5F9; }'
            'QListWidget::item:selected { background: #DBEAFE; color: #1E40AF; }'
        )
        layout.addWidget(self.list_widget, 1)

        info_row = QHBoxLayout()
        self.lbl_count = QLabel('共 0 条记录')
        self.lbl_count.setStyleSheet('color:#64748B; font-size:13px;')
        info_row.addWidget(self.lbl_count)
        info_row.addStretch()
        layout.addLayout(info_row)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton('清空历史')
        btn_clear.setStyleSheet(
            'padding:6px 16px; border-radius:4px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(btn_clear)

        btn_row.addStretch()

        btn_replay = QPushButton('重新发送选中项')
        btn_replay.setStyleSheet(
            'padding:6px 20px; border-radius:4px;'
            'background:#3B82F6; color:white; font-weight:600; border:none;'
        )
        btn_replay.clicked.connect(self._replay)
        btn_row.addWidget(btn_replay)

        layout.addLayout(btn_row)

    def _on_tx(self, data):
        self._tx_count += 1
        try:
            text = data.decode('utf-8', errors='replace')
        except Exception:
            text = repr(data)

        if self.cmb_mode.currentIndex() == 1:
            display_text = ' '.join(f'{b:02X}' for b in data)
        else:
            display_text = text[:120]

        item = QListWidgetItem(f"[{self._tx_count}] {display_text}")
        item.setData(Qt.UserRole, data)
        item.setToolTip(f'完整数据: {text}')

        self.list_widget.insertItem(0, item)
        if self.list_widget.count() > 500:
            self.list_widget.takeItem(500)

        self._update_count()

    def _refresh_list(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.UserRole)
            if data:
                try:
                    text = data.decode('utf-8', errors='replace')
                except Exception:
                    text = repr(data)
                if self.cmb_mode.currentIndex() == 1:
                    display_text = ' '.join(f'{b:02X}' for b in data)
                else:
                    display_text = text[:120]
                item.setText(f"[{self._tx_count - i}] {display_text}")

    def _filter(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not text:
                item.setHidden(False)
            else:
                item.setHidden(text.lower() not in item.text().lower())

    def _clear(self):
        self.list_widget.clear()
        self._tx_count = 0
        self._update_count()

    def _replay(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        data = items[0].data(Qt.UserRole)
        if data:
            SerialLink.instance().send(data)
            DataBus.instance().publish_serial_tx(data)

    def _update_count(self):
        self.lbl_count.setText(f'共 {self.list_widget.count()} 条记录')

    def closeEvent(self, event):
        self._save_persisted_history()
        try:
            DataBus.instance().raw_sent.disconnect(self._on_tx)
        except Exception:
            pass
        super().closeEvent(event)

    def _load_persisted_history(self):
        """从配置加载持久化的发送历史"""
        try:
            hist = self.config.get('send_history', [])
            for item_data in reversed(hist):  # 恢复顺序
                if isinstance(item_data, str):
                    try:
                        data = bytes.fromhex(item_data)
                    except ValueError:
                        continue
                elif isinstance(item_data, list):
                    data = bytes(item_data)
                else:
                    continue
                self._tx_count += 1
                text = data.decode('utf-8', errors='replace')
                item = QListWidgetItem(f"[{self._tx_count}] {text[:120]}")
                item.setData(Qt.UserRole, data)
                self.list_widget.addItem(item)
            self._update_count()
        except Exception:
            pass

    def _save_persisted_history(self):
        """持久化发送历史到配置"""
        try:
            hist = []
            for i in range(min(self.list_widget.count(), 50)):
                item = self.list_widget.item(i)
                if item:
                    data = item.data(Qt.UserRole)
                    if data:
                        hist.append(data.hex())
            self.config.set('send_history', hist)
            self.config.save()
        except Exception:
            pass

