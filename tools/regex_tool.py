# -*- coding: utf-8 -*-
"""
正则表达式测试器
实时高亮匹配，支持多种模式
"""

import re
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QCheckBox, QComboBox
)


class RegexHighlighter(QSyntaxHighlighter):
    def __init__(self, pattern_str, parent):
        super().__init__(parent)
        self.pattern = None
        if pattern_str:
            try:
                self.pattern = re.compile(pattern_str)
            except re.error:
                self.pattern = None

    def set_pattern(self, pattern_str, flags=0):
        if pattern_str:
            try:
                self.pattern = re.compile(pattern_str, flags)
            except re.error:
                self.pattern = None
        else:
            self.pattern = None
        self.rehighlight()

    def highlightBlock(self, text):
        if not self.pattern:
            return
        for m in self.pattern.finditer(text):
            fmt = QTextCharFormat()
            fmt.setBackground(QColor('#FEF3C7'))
            fmt.setForeground(QColor('#92400E'))
            self.setFormat(m.start(), m.end() - m.start(), fmt)


class RegexTool(QWidget):
    """正则表达式测试工具 - 单例模式"""

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
        self.setWindowTitle('正则表达式测试器 - MHcom')
        self.resize(820, 620)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('正则表达式测试器')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        box = QGroupBox('  正则表达式')
        bl = QHBoxLayout(box)
        bl.setContentsMargins(12, 10, 12, 12)
        bl.setSpacing(10)

        bl.addWidget(QLabel('/'))
        self.txt_pattern = QLineEdit()
        self.txt_pattern.setPlaceholderText(r'输入正则表达式，如: \d+')
        self.txt_pattern.setStyleSheet(
            'QLineEdit { padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px;'
            'font-family: Consolas; font-size: 14px; }'
            'QLineEdit:focus { border: 1px solid #3B82F6; }'
        )
        self.txt_pattern.textChanged.connect(self._update)
        bl.addWidget(self.txt_pattern, 1)
        bl.addWidget(QLabel('/'))

        flags_box = QHBoxLayout()
        flags_box.setSpacing(8)
        self.chk_ignore = QCheckBox('i')
        self.chk_ignore.setToolTip('忽略大小写')
        self.chk_ignore.toggled.connect(self._update)
        flags_box.addWidget(self.chk_ignore)

        self.chk_multi = QCheckBox('m')
        self.chk_multi.setToolTip('多行模式')
        self.chk_multi.toggled.connect(self._update)
        flags_box.addWidget(self.chk_multi)

        self.chk_dotall = QCheckBox('s')
        self.chk_dotall.setToolTip('点匹配全部')
        self.chk_dotall.toggled.connect(self._update)
        flags_box.addWidget(self.chk_dotall)
        bl.addLayout(flags_box)

        layout.addWidget(box)

        preset_box = QHBoxLayout()
        preset_box.addWidget(QLabel('常用正则:'))
        self.cmb_preset = QComboBox()
        self.cmb_preset.addItems([
            '选择预设...',
            '数字: \\d+',
            '字母: [a-zA-Z]+',
            '邮箱: \\w+@\\w+\\.\\w+',
            '手机号: 1[3-9]\\d{9}',
            'IP地址: \\d+\\.\\d+\\.\\d+\\.\\d+',
            '中文字符: [\\u4e00-\\u9fa5]+',
            'URL: https?://\\S+',
        ])
        self.cmb_preset.currentIndexChanged.connect(self._apply_preset)
        preset_box.addWidget(self.cmb_preset)
        preset_box.addStretch()
        layout.addLayout(preset_box)

        self.lbl_status = QLabel('等待输入...')
        self.lbl_status.setStyleSheet(
            'color:#64748B; font-size:13px; padding: 4px 8px;'
        )
        layout.addWidget(self.lbl_status)

        box2 = QGroupBox('  测试文本')
        v2 = QVBoxLayout(box2)
        v2.setContentsMargins(12, 10, 12, 12)
        self.txt_test = QPlainTextEdit()
        self.txt_test.setPlaceholderText('输入测试文本，匹配结果将自动高亮...')
        f = QFont('Consolas')
        f.setStyleHint(QFont.Monospace)
        f.setPointSize(11)
        self.txt_test.setFont(f)
        self.txt_test.setStyleSheet(
            'QPlainTextEdit { border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px; }'
        )
        self.txt_test.setMinimumHeight(180)
        v2.addWidget(self.txt_test)
        layout.addWidget(box2, 1)

        box3 = QGroupBox('  匹配结果')
        v3 = QVBoxLayout(box3)
        v3.setContentsMargins(12, 10, 12, 12)

        result_header = QHBoxLayout()
        result_header.addWidget(QLabel('匹配详情:'))
        result_header.addStretch()
        btn_copy = QPushButton('复制结果')
        btn_copy.setStyleSheet(
            'padding:4px 12px; border-radius:4px; font-size:12px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_copy.clicked.connect(self._copy_result)
        result_header.addWidget(btn_copy)
        v3.addLayout(result_header)

        self.txt_result = QPlainTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setMaximumHeight(140)
        self.txt_result.setFont(f)
        self.txt_result.setStyleSheet(
            'QPlainTextEdit { background:#F8FAFC; border: 1px solid #E2E8F0;'
            'border-radius: 6px; padding: 8px; }'
        )
        v3.addWidget(self.txt_result)
        layout.addWidget(box3)

        self.highlighter = RegexHighlighter('', self.txt_test.document())
        self.txt_test.textChanged.connect(self._update)

    def _apply_preset(self, idx):
        if idx == 0:
            return
        text = self.cmb_preset.currentText()
        if ': ' in text:
            pattern = text.split(': ', 1)[1]
            self.txt_pattern.setText(pattern)
        self.cmb_preset.setCurrentIndex(0)

    def _update(self):
        pattern = self.txt_pattern.text()
        flags = 0
        if self.chk_ignore.isChecked():
            flags |= re.IGNORECASE
        if self.chk_multi.isChecked():
            flags |= re.MULTILINE
        if self.chk_dotall.isChecked():
            flags |= re.DOTALL

        self.highlighter.set_pattern(pattern, flags)

        if not pattern:
            self.lbl_status.setText('等待输入...')
            self.lbl_status.setStyleSheet('color:#64748B; font-size:13px; padding: 4px 8px;')
            self.txt_result.clear()
            return

        try:
            p = re.compile(pattern, flags)
            text = self.txt_test.toPlainText()
            matches = list(p.finditer(text))
            if matches:
                self.lbl_status.setText(f'✓ 找到 {len(matches)} 个匹配')
                self.lbl_status.setStyleSheet(
                    'color:#059669; font-size:13px; font-weight:600;'
                    'padding: 4px 8px; background:#ECFDF5; border-radius:4px;'
                )
                lines = []
                for i, m in enumerate(matches[:100]):
                    groups = ''
                    if m.groups():
                        groups = f'  groups={m.groups()}'
                    lines.append(f'[{i}] pos={m.start()}-{m.end()}  match="{m.group()}"{groups}')
                if len(matches) > 100:
                    lines.append(f'... 共 {len(matches)} 个，仅显示前 100 个')
                self.txt_result.setPlainText('\n'.join(lines))
            else:
                self.lbl_status.setText('无匹配')
                self.lbl_status.setStyleSheet(
                    'color:#DC2626; font-size:13px; font-weight:600;'
                    'padding: 4px 8px;'
                )
                self.txt_result.clear()
        except re.error as e:
            self.lbl_status.setText(f'✗ 正则语法错误: {e}')
            self.lbl_status.setStyleSheet(
                'color:#DC2626; font-size:13px; font-weight:600;'
                'padding: 4px 8px; background:#FEF2F2; border-radius:4px;'
            )
            self.txt_result.clear()

    def _copy_result(self):
        text = self.txt_result.toPlainText()
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)

    def closeEvent(self, event):
        super().closeEvent(event)

