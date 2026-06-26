# -*- coding: utf-8 -*-
"""
深色主题 QSS - 深空玻璃
"""

DARK_QSS = """
/* === 全局 === */
QMainWindow, QWidget {
    background: #07080B;
    color: #E5E7EB;
    font-family: "Microsoft YaHei UI", "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* === 工具�?=== */
QToolBar {
    background: #0E1014;
    border: none;
    border-bottom: 1px solid #1F2329;
    padding: 4px 8px;
    spacing: 4px;
}
QToolBar::separator {
    background: #1F2329;
    width: 1px;
    margin: 4px 4px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    color: #9CA3AF;
}
QToolButton:hover {
    background: #161A21;
    color: #E5E7EB;
}
QToolButton:checked {
    background: rgba(59, 130, 246, 0.15);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.4);
    font-weight: 600;
}

/* === 菜单�?=== */
QMenuBar {
    background: #0E1014;
    border-bottom: 1px solid #1F2329;
    color: #E5E7EB;
    padding: 2px;
}
QMenuBar::item {
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #161A21;
}
QMenu {
    background: #0E1014;
    border: 1px solid #1F2329;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: rgba(59, 130, 246, 0.2);
    color: #60A5FA;
}
QMenu::separator {
    height: 1px;
    background: #1F2329;
    margin: 4px 8px;
}

/* === 状态栏 === */
QStatusBar {
    background: #0E1014;
    border-top: 1px solid #1F2329;
    color: #9CA3AF;
    font-size: 12px;
}

/* === GroupBox === */
QGroupBox {
    background: #0E1014;
    border: 1px solid #1F2329;
    border-radius: 10px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
    color: #E5E7EB;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #9CA3AF;
    background: #0E1014;
}

/* === 按钮 === */
QPushButton {
    background: #161A21;
    border: 1px solid #1F2329;
    border-radius: 6px;
    padding: 6px 14px;
    color: #E5E7EB;
    font-size: 13px;
}
QPushButton:hover {
    background: #1F2329;
    border: 1px solid #2D3340;
}
QPushButton:pressed {
    background: #0E1014;
}
QPushButton:disabled {
    background: #0E1014;
    color: #6B7280;
    border: 1px solid #1F2329;
}

QPushButton[cssClass="default"] {
    background: #2563EB;
    color: white;
    border: 1px solid #2563EB;
    font-weight: 600;
}
QPushButton[cssClass="default"]:hover {
    background: #3B82F6;
    border: 1px solid #3B82F6;
}
QPushButton[cssClass="default"]:pressed {
    background: #1D4ED8;
}
QPushButton[cssClass="success"] {
    background: #10B981;
    color: white;
    border: 1px solid #10B981;
}
QPushButton[cssClass="danger"] {
    background: #EF4444;
    color: white;
    border: 1px solid #EF4444;
}
QPushButton[cssClass="warning"] {
    background: #F59E0B;
    color: white;
    border: 1px solid #F59E0B;
}

/* === 输入�?=== */
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #07080B;
    border: 1px solid #1F2329;
    border-radius: 6px;
    padding: 6px 8px;
    color: #E5E7EB;
    selection-background-color: #1E40AF;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #3B82F6;
}

/* === 下拉�?=== */
QComboBox {
    background: #07080B;
    border: 1px solid #1F2329;
    border-radius: 6px;
    padding: 5px 10px;
    color: #E5E7EB;
    min-height: 18px;
}
QComboBox:hover {
    border: 1px solid #2D3340;
}
QComboBox:focus {
    border: 1px solid #3B82F6;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #9CA3AF;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #0E1014;
    border: 1px solid #1F2329;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: rgba(59, 130, 246, 0.25);
    selection-color: #60A5FA;
    outline: 0;
}

/* === SpinBox === */
QSpinBox, QDoubleSpinBox {
    background: #07080B;
    border: 1px solid #1F2329;
    border-radius: 6px;
    padding: 4px 6px;
    color: #E5E7EB;
    min-height: 18px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3B82F6;
}

/* === 滑块 === */
QSlider::groove:horizontal {
    background: #1F2329;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #3B82F6;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
    border: 2px solid #0E1014;
}
QSlider::handle:horizontal:hover {
    background: #60A5FA;
}
QSlider::sub-page:horizontal {
    background: #3B82F6;
    border-radius: 3px;
}

/* === 复选框 === */
QCheckBox {
    color: #9CA3AF;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #2D3340;
    background: #07080B;
}
QCheckBox::indicator:hover {
    border: 1px solid #3B82F6;
}
QCheckBox::indicator:checked {
    background: #3B82F6;
    border: 1px solid #3B82F6;
}

/* === 标签 === */
QLabel {
    color: #9CA3AF;
    background: transparent;
}
QLabel[cssClass="title"] {
    color: #E5E7EB;
    font-size: 14px;
    font-weight: 600;
}
QLabel[cssClass="muted"] {
    color: #6B7280;
    font-size: 12px;
}
QLabel[cssClass="mono"] {
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    color: #60A5FA;
}
QLabel[cssClass="success"] { color: #10B981; font-weight: 600; }
QLabel[cssClass="danger"] { color: #EF4444; font-weight: 600; }
QLabel[cssClass="warning"] { color: #F59E0B; font-weight: 600; }

/* === 滚动�?=== */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2D3340;
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2D3340;
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #475569;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: none;
    width: 0;
}

/* === 表格 === */
QTableWidget, QTableView {
    background: #0E1014;
    border: 1px solid #1F2329;
    border-radius: 6px;
    gridline-color: #1F2329;
    color: #E5E7EB;
    selection-background-color: rgba(59, 130, 246, 0.25);
    selection-color: #60A5FA;
}
QHeaderView::section {
    background: #07080B;
    border: none;
    border-right: 1px solid #1F2329;
    border-bottom: 1px solid #1F2329;
    padding: 6px 8px;
    color: #9CA3AF;
    font-weight: 600;
}

/* === 选项�?=== */
QTabWidget::pane {
    border: 1px solid #1F2329;
    border-radius: 8px;
    background: #0E1014;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    padding: 8px 16px;
    color: #6B7280;
}
QTabBar::tab:hover {
    color: #E5E7EB;
}
QTabBar::tab:selected {
    color: #60A5FA;
    border-bottom: 2px solid #3B82F6;
    font-weight: 600;
}

/* === 进度�?=== */
QProgressBar {
    background: #161A21;
    border: 1px solid #1F2329;
    border-radius: 6px;
    text-align: center;
    color: #E5E7EB;
}
QProgressBar::chunk {
    background: #3B82F6;
    border-radius: 5px;
}

/* === 分割�?=== */
QSplitter::handle {
    background: #1F2329;
}

/* === 工具提示 === */
QToolTip {
    background: #1F2937;
    color: #E5E7EB;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* === QStackedWidget === */
QStackedWidget {
    background: #07080B;
}

/* === 滚动区域 === */
QScrollArea {
    background: transparent;
    border: none;
}
"""
