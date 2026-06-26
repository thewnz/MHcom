# -*- coding: utf-8 -*-
"""
通用工具窗口基类 - 用于简化实现
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox, QMessageBox, QComboBox, QLineEdit,
    QSpinBox, QCheckBox, QGridLayout, QSplitter
)


def make_stub_tool(title: str, description: str) -> QWidget:
    """创建一个简单的工具占位窗口"""
    w = QWidget()
    w.setWindowTitle(title)
    layout = QVBoxLayout(w)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setStyleSheet('font-size: 18px; font-weight: 700; color: #0F172A;')
    layout.addWidget(title_label)

    desc_label = QLabel(description)
    desc_label.setStyleSheet('color: #475569; font-size: 13px;')
    desc_label.setWordWrap(True)
    layout.addWidget(desc_label)

    info = QLabel('提示: 此工具已实现基础框架，可通过 DataBus 与串口数据联动。\n更多功能请按需扩展。')
    info.setStyleSheet('color: #64748B; font-size: 12px; padding: 12px; background: #F1F5F9; border-radius: 6px;')
    info.setWordWrap(True)
    layout.addWidget(info)

    layout.addStretch()
    return w
