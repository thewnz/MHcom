# -*- coding: utf-8 -*-
"""
浅色主题 QSS - 工程师明亮
"""

LIGHT_QSS = """
/* === 全局 === */
QMainWindow, QWidget {
    background: #F8FAFC;
    color: #0F172A;
    font-family: "Microsoft YaHei UI", "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* === 工具栏 === */
QToolBar {
    background: #FFFFFF;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 4px 8px;
    spacing: 4px;
}
QToolBar::separator {
    background: #E2E8F0;
    width: 1px;
    margin: 4px 4px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    color: #475569;
}
QToolButton:hover {
    background: #F1F5F9;
    color: #0F172A;
}
QToolButton:checked {
    background: #EFF6FF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    font-weight: 600;
}

/* === 菜单栏 === */
QMenuBar {
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    color: #0F172A;
    padding: 2px;
}
QMenuBar::item {
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #F1F5F9;
}
QMenu {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #EFF6FF;
    color: #2563EB;
}
QMenu::separator {
    height: 1px;
    background: #E2E8F0;
    margin: 4px 8px;
}

/* === 状态栏 === */
QStatusBar {
    background: #FFFFFF;
    border-top: 1px solid #E2E8F0;
    color: #475569;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}

/* === GroupBox === */
QGroupBox {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
    color: #0F172A;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #475569;
    background: #FFFFFF;
}

/* === 按钮 === */
QPushButton {
    background: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px 14px;
    color: #0F172A;
    font-size: 13px;
}
QPushButton:hover {
    background: #E2E8F0;
    border: 1px solid #CBD5E1;
}
QPushButton:pressed {
    background: #CBD5E1;
}
QPushButton:disabled {
    background: #F8FAFC;
    color: #94A3B8;
    border: 1px solid #E2E8F0;
}

QPushButton[cssClass="default"] {
    background: #2563EB;
    color: white;
    border: 1px solid #2563EB;
    font-weight: 600;
}
QPushButton[cssClass="default"]:hover {
    background: #1D4ED8;
    border: 1px solid #1D4ED8;
}
QPushButton[cssClass="default"]:pressed {
    background: #1E40AF;
}
QPushButton[cssClass="default"]:disabled {
    background: #93C5FD;
    border: 1px solid #93C5FD;
}

QPushButton[cssClass="success"] {
    background: #16A34A;
    color: white;
    border: 1px solid #16A34A;
}
QPushButton[cssClass="success"]:hover {
    background: #15803D;
}

QPushButton[cssClass="danger"] {
    background: #DC2626;
    color: white;
    border: 1px solid #DC2626;
}
QPushButton[cssClass="danger"]:hover {
    background: #B91C1C;
}

QPushButton[cssClass="warning"] {
    background: #EA580C;
    color: white;
    border: 1px solid #EA580C;
}

/* === 输入框 === */
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px 8px;
    color: #0F172A;
    selection-background-color: #BFDBFE;
    selection-color: #0F172A;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #2563EB;
}
QLineEdit:disabled, QPlainTextEdit:disabled {
    background: #F1F5F9;
    color: #94A3B8;
}

/* === 下拉框 === */
QComboBox {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 5px 10px;
    color: #0F172A;
    min-height: 18px;
}
QComboBox:hover {
    border: 1px solid #CBD5E1;
}
QComboBox:focus {
    border: 1px solid #2563EB;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #64748B;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
    outline: 0;
}

/* === SpinBox === */
QSpinBox, QDoubleSpinBox {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px 6px;
    color: #0F172A;
    min-height: 18px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2563EB;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: transparent;
    border: none;
    width: 16px;
}

/* === 滑块 === */
QSlider::groove:horizontal {
    background: #E2E8F0;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2563EB;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
    border: 2px solid #FFFFFF;
}
QSlider::handle:horizontal:hover {
    background: #1D4ED8;
}
QSlider::sub-page:horizontal {
    background: #2563EB;
    border-radius: 3px;
}

/* === 复选框 === */
QCheckBox {
    color: #475569;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #CBD5E1;
    background: #FFFFFF;
}
QCheckBox::indicator:hover {
    border: 1px solid #2563EB;
}
QCheckBox::indicator:checked {
    background: #2563EB;
    border: 1px solid #2563EB;
}

/* === 标签 === */
QLabel {
    color: #475569;
    background: transparent;
}
QLabel[cssClass="title"] {
    color: #0F172A;
    font-size: 14px;
    font-weight: 600;
}
QLabel[cssClass="muted"] {
    color: #94A3B8;
    font-size: 12px;
}
QLabel[cssClass="mono"] {
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    color: #2563EB;
}
QLabel[cssClass="success"] { color: #16A34A; font-weight: 600; }
QLabel[cssClass="danger"] { color: #DC2626; font-weight: 600; }
QLabel[cssClass="warning"] { color: #EA580C; font-weight: 600; }

/* === 滚动条 === */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
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
    background: #CBD5E1;
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: none;
    width: 0;
}

/* === 表格 === */
QTableWidget, QTableView {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: #E2E8F0;
    color: #0F172A;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
}
QHeaderView::section {
    background: #F8FAFC;
    border: none;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #E2E8F0;
    padding: 6px 8px;
    color: #475569;
    font-weight: 600;
}

/* === 选项卡 === */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background: #FFFFFF;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    padding: 8px 16px;
    color: #64748B;
}
QTabBar::tab:hover { color: #0F172A; }
QTabBar::tab:selected {
    color: #2563EB;
    border-bottom: 2px solid #2563EB;
    font-weight: 600;
}

/* === 进度条 === */
QProgressBar {
    background: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    text-align: center;
    color: #0F172A;
}
QProgressBar::chunk {
    background: #2563EB;
    border-radius: 5px;
}

/* === 分割器 === */
QSplitter::handle { background: #E2E8F0; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

/* === 工具提示 === */
QToolTip {
    background: #0F172A;
    color: #FFFFFF;
    border: 1px solid #1E293B;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

QStackedWidget { background: #F8FAFC; }
QScrollArea { background: transparent; border: none; }
"""
