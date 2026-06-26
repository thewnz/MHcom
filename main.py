# -*- coding: utf-8 -*-
"""
PC Tool - 多功能高级串口助手 v2.0
主入口 - 3D云台调试 + 高级串口助手 双模切换
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QStackedWidget,
    QToolBar, QStatusBar, QLabel, QWidget, QHBoxLayout, QMessageBox,
    QActionGroup
)

from themes.light_theme import LIGHT_QSS
from themes.dark_theme import DARK_QSS
from config.settings import AppConfig
from core.serial_link import SerialLink
from core.data_bus import DataBus
from core.tool_manager import ToolManager
from panels.gimbal_panel import GimbalPanel
from panels.terminal_panel import TerminalPanel

from tools.waveform_tool import WaveformTool
from tools.crc_tool import CrcTool
from tools.hex_converter_tool import HexConverterTool
from tools.protocol_parser_tool import ProtocolParserTool
from tools.macro_editor_tool import MacroEditorTool
from tools.history_tool import HistoryTool
from tools.modbus_tool import ModbusTool
from tools.data_logger_tool import DataLoggerTool
from tools.settings_dialog import SettingsDialog
from tools.help_dialog import HelpDialog


APP_VERSION = 'v2.0'


class MainWindow(QMainWindow):
    """主窗口 - 3D云台调试 + 高级串口助手 双模切换"""

    TOOL_MENU_ITEMS = [
        ('waveform',       '📊 实时波形图', 'Ctrl+W'),
        ('modbus',         '🔌 Modbus RTU 模拟器', 'Ctrl+M'),
        ('crc',            '🧮 CRC / 校验计算器', 'Ctrl+Shift+C'),
        ('hex_converter',  '🔄 HEX / 文本 转换', 'Ctrl+H'),
        ('protocol_parser','📋 协议解析器', 'Ctrl+P'),
        ('macro_editor',   '⚡ 快捷命令管理', 'Ctrl+K'),
        ('history',        '📜 发送历史', 'Ctrl+L'),
        ('data_logger',    '💾 数据记录器', None),
        ('settings',       '⚙ 设置', 'Ctrl+,'),
    ]

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        self.slink = SerialLink.instance()
        self.bus = DataBus.instance()

        self.setWindowTitle('MHcom - 多功能高级串口助手 v2.0')
        self.resize(1400, 850)

        self._setup_fonts()
        self._init_panels()
        self._build_central()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._connect_signals()
        self._apply_theme(self.config.get('theme', 'light'))
        self._restore_mode()

    # ------------------------------------------------------------------ init

    def _setup_fonts(self):
        f = QFont('Microsoft YaHei UI', 10)
        f.setStyleStrategy(QFont.PreferAntialias)
        QApplication.setFont(f)

    def _init_panels(self):
        self.gimbal_panel = GimbalPanel()
        self.terminal_panel = TerminalPanel()
        if hasattr(self.gimbal_panel, 'request_tool'):
            self.gimbal_panel.request_tool.connect(self._open_tool)
        if hasattr(self.terminal_panel, 'request_tool'):
            self.terminal_panel.request_tool.connect(self._open_tool)

    def _build_central(self):
        self.stack = QStackedWidget()
        self.stack.addWidget(self.gimbal_panel)
        self.stack.addWidget(self.terminal_panel)
        self.setCentralWidget(self.stack)

    # ------------------------------------------------------------------ menu

    def _build_menu(self):
        mb = self.menuBar()
        self._build_menu_file(mb.addMenu('文件(&F)'))
        self._build_menu_view(mb.addMenu('视图(&V)'))
        self._build_menu_tools(mb.addMenu('工具(&T)'))
        self._build_menu_settings(mb.addMenu('设置(&S)'))
        self._build_menu_help(mb.addMenu('帮助(&H)'))

    def _build_menu_file(self, m):
        a_export = QAction('导出配置...', self)
        a_export.triggered.connect(self._export_config)
        m.addAction(a_export)

        a_import = QAction('导入配置...', self)
        a_import.triggered.connect(self._import_config)
        m.addAction(a_import)

        m.addSeparator()

        a_exit = QAction('退出(&Q)', self)
        a_exit.setShortcut('Ctrl+Q')
        a_exit.triggered.connect(self.close)
        m.addAction(a_exit)

    def _build_menu_view(self, m):
        self.action_gimbal = QAction('3D云台调试', self, checkable=True)
        self.action_gimbal.setShortcut('Ctrl+1')
        self.action_gimbal.triggered.connect(lambda: self._set_mode(0))
        m.addAction(self.action_gimbal)

        self.action_terminal = QAction('高级串口助手', self, checkable=True)
        self.action_terminal.setShortcut('Ctrl+2')
        self.action_terminal.triggered.connect(lambda: self._set_mode(1))
        m.addAction(self.action_terminal)

        mode_group = QActionGroup(self)
        mode_group.addAction(self.action_gimbal)
        mode_group.addAction(self.action_terminal)
        mode_group.setExclusive(True)

        m.addSeparator()

        m_theme = m.addMenu('主题')
        self.action_theme_light = QAction('浅色 (工程师明亮)', self, checkable=True)
        self.action_theme_light.triggered.connect(lambda: self._apply_theme('light'))
        m_theme.addAction(self.action_theme_light)

        self.action_theme_dark = QAction('深色 (深空玻璃)', self, checkable=True)
        self.action_theme_dark.triggered.connect(lambda: self._apply_theme('dark'))
        m_theme.addAction(self.action_theme_dark)

        theme_group = QActionGroup(self)
        theme_group.addAction(self.action_theme_light)
        theme_group.addAction(self.action_theme_dark)
        theme_group.setExclusive(True)

    def _build_menu_tools(self, m):
        for tool_id, label, shortcut in self.TOOL_MENU_ITEMS:
            act = QAction(label, self)
            if shortcut:
                act.setShortcut(shortcut)
            act.triggered.connect(lambda _, t=tool_id: self._open_tool(t))
            m.addAction(act)

    def _build_menu_settings(self, m):
        a_serial = QAction('串口设置...', self)
        a_serial.triggered.connect(lambda: self._open_tool('settings'))
        m.addAction(a_serial)

        m.addSeparator()

        a_theme_light = QAction('浅色主题', self)
        a_theme_light.triggered.connect(lambda: self._apply_theme('light'))
        m.addAction(a_theme_light)

        a_theme_dark = QAction('深色主题', self)
        a_theme_dark.triggered.connect(lambda: self._apply_theme('dark'))
        m.addAction(a_theme_dark)

    def _build_menu_help(self, m):
        a_help = QAction('使用帮助', self)
        a_help.setShortcut('F1')
        a_help.triggered.connect(lambda: self._open_help('overview'))
        m.addAction(a_help)

        a_quickstart = QAction('快速开始', self)
        a_quickstart.triggered.connect(lambda: self._open_help('quickstart'))
        m.addAction(a_quickstart)

        m.addSeparator()

        m_gimbal_help = QAction('3D云台调试说明', self)
        m_gimbal_help.triggered.connect(lambda: self._open_help('gimbal'))
        m.addAction(m_gimbal_help)

        m_terminal_help = QAction('高级串口助手说明', self)
        m_terminal_help.triggered.connect(lambda: self._open_help('terminal'))
        m.addAction(m_terminal_help)

        m_tools_help = QAction('工具大全', self)
        m_tools_help.triggered.connect(lambda: self._open_help('tools'))
        m.addAction(m_tools_help)

        m.addSeparator()

        a_shortcuts = QAction('快捷键大全', self)
        a_shortcuts.triggered.connect(lambda: self._open_help('shortcuts'))
        m.addAction(a_shortcuts)

        a_faq = QAction('常见问题', self)
        a_faq.triggered.connect(lambda: self._open_help('faq'))
        m.addAction(a_faq)

        m.addSeparator()

        a_about = QAction('关于', self)
        a_about.triggered.connect(self._show_about)
        m.addAction(a_about)

    # ---------------------------------------------------------------- toolbar

    def _build_toolbar(self):
        tb = QToolBar('主工具栏')
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addWidget(QLabel(' 模式: '))
        self.tb_gimbal = QAction('🎮 3D云台', self, checkable=True)
        self.tb_gimbal.triggered.connect(lambda: self._set_mode(0))
        tb.addAction(self.tb_gimbal)

        self.tb_terminal = QAction('📡 串口助手', self, checkable=True)
        self.tb_terminal.triggered.connect(lambda: self._set_mode(1))
        tb.addAction(self.tb_terminal)

        tb_mode_group = QActionGroup(self)
        tb_mode_group.addAction(self.tb_gimbal)
        tb_mode_group.addAction(self.tb_terminal)
        tb_mode_group.setExclusive(True)

        tb.addSeparator()

        self.lbl_conn_status = QLabel(' 🔴 未连接 ')
        self.lbl_conn_status.setStyleSheet(
            'padding: 2px 8px; border-radius: 4px; '
            'background: #FEE2E2; color: #DC2626; font-weight: 500;'
        )
        tb.addWidget(self.lbl_conn_status)

        tb.addSeparator()

        tb.addAction('📊 波形').triggered.connect(lambda: self._open_tool('waveform'))
        tb.addAction('🔌 Modbus').triggered.connect(lambda: self._open_tool('modbus'))
        tb.addAction('🧮 CRC').triggered.connect(lambda: self._open_tool('crc'))
        tb.addAction('🔄 HEX').triggered.connect(lambda: self._open_tool('hex_converter'))
        tb.addAction('📋 解析').triggered.connect(lambda: self._open_tool('protocol_parser'))

        tb.addSeparator()

        tb.addAction('⚙ 设置').triggered.connect(lambda: self._open_tool('settings'))

    # ---------------------------------------------------------------- statusbar

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)

        self.lbl_serial_status = QLabel('串口: 未连接')
        sb.addWidget(self.lbl_serial_status, 1)

        self.lbl_rx = QLabel('RX: 0')
        sb.addPermanentWidget(self.lbl_rx)

        self.lbl_tx = QLabel('TX: 0')
        sb.addPermanentWidget(self.lbl_tx)

        self.lbl_mode = QLabel('模式: 3D云台调试')
        sb.addPermanentWidget(self.lbl_mode)

        self.lbl_version = QLabel(APP_VERSION)
        sb.addPermanentWidget(self.lbl_version)

    # ---------------------------------------------------------------- signals

    def _connect_signals(self):
        self.slink.state_changed.connect(self._on_serial_state_changed)
        self.slink.rx_count_changed.connect(self._on_rx_count_changed)
        self.slink.tx_count_changed.connect(self._on_tx_count_changed)

    # ---------------------------------------------------------------- mode

    def _set_mode(self, idx: int):
        self.stack.setCurrentIndex(idx)
        mode = 'gimbal' if idx == 0 else 'terminal'
        self.config.set('mode', mode)
        self.config.save()

        self.action_gimbal.setChecked(idx == 0)
        self.action_terminal.setChecked(idx == 1)
        self.tb_gimbal.setChecked(idx == 0)
        self.tb_terminal.setChecked(idx == 1)

        mode_text = '3D云台调试' if idx == 0 else '高级串口助手'
        self.lbl_mode.setText(f'模式: {mode_text}')

    def _restore_mode(self):
        mode = self.config.get('mode', 'gimbal')
        idx = 0 if mode == 'gimbal' else 1
        self.stack.setCurrentIndex(idx)
        # 仅更新 UI 选中状态，不触发 config.save（config 值已正确）
        self.action_gimbal.setChecked(idx == 0)
        self.action_terminal.setChecked(idx == 1)
        self.tb_gimbal.setChecked(idx == 0)
        self.tb_terminal.setChecked(idx == 1)
        mode_text = '3D云台调试' if idx == 0 else '高级串口助手'
        self.lbl_mode.setText(f'模式: {mode_text}')

    # ---------------------------------------------------------------- theme

    def _apply_theme(self, name: str):
        app = QApplication.instance()
        if name == 'dark':
            app.setStyleSheet(DARK_QSS)
            self.action_theme_dark.setChecked(True)
            self.action_theme_light.setChecked(False)
        else:
            app.setStyleSheet(LIGHT_QSS)
            self.action_theme_light.setChecked(True)
            self.action_theme_dark.setChecked(False)
        self.config.set('theme', name)
        self.config.save()

    # ---------------------------------------------------------------- tools

    def _open_help(self, page: str = 'overview'):
        try:
            from tools.help_dialog import HelpDialog
            widget = ToolManager.show_tool('help', HelpDialog, self)
            if widget and hasattr(widget, 'show_page'):
                widget.show_page(page)
        except Exception as e:
            QMessageBox.warning(self, '帮助打开失败', str(e))

    def _open_tool(self, tool_id: str):
        """打开工具窗口（所有工具类已在模块头部静态导入）"""
        tool_classes = {
            'waveform': WaveformTool, 'crc': CrcTool,
            'hex_converter': HexConverterTool, 'protocol_parser': ProtocolParserTool,
            'macro_editor': MacroEditorTool, 'history': HistoryTool,
            'modbus': ModbusTool, 'data_logger': DataLoggerTool,
            'settings': SettingsDialog, 'help': HelpDialog,
        }
        tool_class = tool_classes.get(tool_id)
        if tool_class is None:
            QMessageBox.warning(self, '工具不存在', f'未知工具: {tool_id}')
            return
        try:
            ToolManager.show_tool(tool_id, tool_class, self)
        except Exception as e:
            QMessageBox.warning(self, '工具加载失败', str(e))

    # ---------------------------------------------------------------- serial

    def _on_serial_state_changed(self, opened: bool):
        if opened:
            port = self.slink.port_name
            baud = self.slink.baudrate
            self.lbl_conn_status.setText(f' 🟢 {port} @ {baud} ')
            self.lbl_conn_status.setStyleSheet(
                'padding: 2px 8px; border-radius: 4px; '
                'background: #D1FAE5; color: #059669; font-weight: 500;'
            )
            self.lbl_serial_status.setText(f'串口: {port} @ {baud}')
        else:
            self.lbl_conn_status.setText(' 🔴 未连接 ')
            self.lbl_conn_status.setStyleSheet(
                'padding: 2px 8px; border-radius: 4px; '
                'background: #FEE2E2; color: #DC2626; font-weight: 500;'
            )
            self.lbl_serial_status.setText('串口: 未连接')

    def _on_rx_count_changed(self, count: int):
        self.lbl_rx.setText(f'RX: {self._format_bytes(count)}')

    def _on_tx_count_changed(self, count: int):
        self.lbl_tx.setText(f'TX: {self._format_bytes(count)}')

    @staticmethod
    def _format_bytes(n: int) -> str:
        if n < 1024:
            return f'{n} B'
        elif n < 1024 * 1024:
            return f'{n / 1024:.1f} KB'
        else:
            return f'{n / (1024 * 1024):.1f} MB'

    # ---------------------------------------------------------------- config

    def _export_config(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, '导出配置', 'config.json', 'JSON (*.json)')
        if not path:
            return
        import json
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config.data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, '导出成功', f'已导出到: {path}')
        except Exception as e:
            QMessageBox.critical(self, '导出失败', str(e))

    def _import_config(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, '导入配置', '', 'JSON (*.json)')
        if not path:
            return
        import json
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.config.data = self.config._merge_defaults(data)
            self.config.save()
            QMessageBox.information(self, '导入成功', '配置已加载, 部分设置需重启生效')
        except Exception as e:
            QMessageBox.critical(self, '导入失败', str(e))

    # ---------------------------------------------------------------- about

    def _show_about(self):
        QMessageBox.about(self, '关于 PC Tool',
            f'<h3>PC Tool - 多功能高级串口助手 {APP_VERSION}</h3>'
            '<p>🎮 模式A: 3D 舵机云台调试</p>'
            '<p>📡 模式B: 高级串口助手</p>'
            '<p>🛠 独立工具: 波形图 / Modbus / CRC / HEX / 协议解析 等 10 项</p>'
            '<p>支持 OBJ/STL 3D模型导入与自动分析</p>'
            '<p>设计: 多文件模块化 + 浅色/深色双主题</p>'
        )

    # ---------------------------------------------------------------- close

    def closeEvent(self, e):
        ToolManager.close_all()
        try:
            self.slink.close()
        except Exception:
            pass
        self.config.save()
        super().closeEvent(e)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName('PC Tool')

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
