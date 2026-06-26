# -*- coding: utf-8 -*-
"""自动应答工具 - 收到指定内容后自动回复"""
import fnmatch
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QLineEdit, QListWidget, QListWidgetItem,
    QComboBox, QSpinBox, QGroupBox, QDialog, QDialogButtonBox
)
from core.data_bus import DataBus
from core.serial_link import SerialLink
from config.settings import AppConfig


class RuleEditDialog(QDialog):
    """规则编辑对话框"""

    def __init__(self, rule=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('编辑规则')
        self.resize(420, 260)
        self._build_ui()
        if rule:
            self.ed_match.setText(rule.get('match', ''))
            self.ed_reply.setText(rule.get('reply', ''))
            self.cb_mode.setCurrentText(rule.get('mode', '精确匹配'))
            self.sp_delay.setValue(rule.get('delay', 0))
            self.chk_enabled.setChecked(rule.get('enabled', True))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel('匹配内容:'))
        self.ed_match = QLineEdit()
        layout.addWidget(self.ed_match)

        layout.addWidget(QLabel('回复内容:'))
        self.ed_reply = QLineEdit()
        layout.addWidget(self.ed_reply)

        form_row = QHBoxLayout()
        form_row.addWidget(QLabel('匹配模式:'))
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(['精确匹配', '包含匹配', '通配符'])
        form_row.addWidget(self.cb_mode, 1)
        form_row.addWidget(QLabel('延迟(ms):'))
        self.sp_delay = QSpinBox()
        self.sp_delay.setRange(0, 60000)
        self.sp_delay.setSuffix(' ms')
        form_row.addWidget(self.sp_delay)
        layout.addLayout(form_row)

        self.chk_enabled = QCheckBox('启用该规则')
        self.chk_enabled.setChecked(True)
        layout.addWidget(self.chk_enabled)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_rule(self) -> dict:
        return {
            'match': self.ed_match.text(),
            'reply': self.ed_reply.text(),
            'mode': self.cb_mode.currentText(),
            'delay': self.sp_delay.value(),
            'enabled': self.chk_enabled.isChecked(),
        }


class AutoReplyTool(QWidget):
    """自动应答工具"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('自动应答 - MHcom')
        self.resize(520, 560)
        self.config = AppConfig()
        self.rules = self.config.get('auto_reply_rules', [])
        self._build_ui()
        self._refresh_list()
        DataBus.instance().line_received.connect(self._on_line_received)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 顶部：启用开关 + 添加规则按钮
        top_row = QHBoxLayout()
        self.chk_enable = QCheckBox('启用自动应答')
        self.chk_enable.setChecked(self.config.get('auto_reply_enabled', False))
        top_row.addWidget(self.chk_enable)
        top_row.addStretch()
        btn_add = QPushButton('添加规则')
        btn_add.clicked.connect(self._add_rule)
        top_row.addWidget(btn_add)
        layout.addLayout(top_row)

        # 中间：规则列表
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        # 底部按钮：编辑/删除/上移/下移
        btn_row = QHBoxLayout()
        btn_edit = QPushButton('编辑')
        btn_edit.clicked.connect(self._edit_rule)
        btn_row.addWidget(btn_edit)
        btn_del = QPushButton('删除')
        btn_del.clicked.connect(self._delete_rule)
        btn_row.addWidget(btn_del)
        btn_up = QPushButton('上移')
        btn_up.clicked.connect(self._move_up)
        btn_row.addWidget(btn_up)
        btn_down = QPushButton('下移')
        btn_down.clicked.connect(self._move_down)
        btn_row.addWidget(btn_down)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 选项组
        opt_group = QGroupBox('选项')
        opt_lay = QHBoxLayout(opt_group)
        opt_lay.addWidget(QLabel('默认匹配模式:'))
        self.cb_default_mode = QComboBox()
        self.cb_default_mode.addItems(['精确匹配', '包含匹配', '通配符'])
        self.cb_default_mode.setCurrentText(
            self.config.get('auto_reply_default_mode', '包含匹配')
        )
        opt_lay.addWidget(self.cb_default_mode, 1)
        opt_lay.addWidget(QLabel('默认延迟:'))
        self.sp_default_delay = QSpinBox()
        self.sp_default_delay.setRange(0, 60000)
        self.sp_default_delay.setSuffix(' ms')
        self.sp_default_delay.setValue(
            self.config.get('auto_reply_default_delay', 0)
        )
        opt_lay.addWidget(self.sp_default_delay)
        layout.addWidget(opt_group)

        # 保存选项变更
        self.cb_default_mode.currentTextChanged.connect(self._save_options)
        self.sp_default_delay.valueChanged.connect(self._save_options)
        self.chk_enable.stateChanged.connect(self._save_options)

    def _refresh_list(self):
        self.list_widget.clear()
        for idx, rule in enumerate(self.rules):
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            row = self._create_rule_widget(rule, idx)
            item.setSizeHint(row.sizeHint())
            self.list_widget.setItemWidget(item, row)

    def _create_rule_widget(self, rule: dict, index: int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        chk = QCheckBox()
        chk.setChecked(rule.get('enabled', True))
        chk.stateChanged.connect(
            lambda state, i=index: self._toggle_rule(i, state == Qt.Checked)
        )
        layout.addWidget(chk)

        status = '✓' if rule.get('enabled', True) else '✗'
        match_text = rule.get('match', '')
        reply_text = rule.get('reply', '')
        mode_text = rule.get('mode', '')
        label = QLabel(f'{status} [{mode_text}] {match_text} → {reply_text}')
        if not rule.get('enabled', True):
            label.setStyleSheet('color: #94A3B8;')
        layout.addWidget(label, 1)

        return widget

    def _toggle_rule(self, index: int, enabled: bool):
        if 0 <= index < len(self.rules):
            self.rules[index]['enabled'] = enabled
            self._save_rules()
            self._refresh_list()

    def _add_rule(self):
        dlg = RuleEditDialog(parent=self)
        dlg.ed_match.setPlaceholderText('输入要匹配的内容')
        dlg.ed_reply.setPlaceholderText('输入自动回复的内容')
        dlg.cb_mode.setCurrentText(self.cb_default_mode.currentText())
        dlg.sp_delay.setValue(self.sp_default_delay.value())
        if dlg.exec_() == QDialog.Accepted:
            self.rules.append(dlg.get_rule())
            self._save_rules()
            self._refresh_list()

    def _edit_rule(self):
        current = self.list_widget.currentRow()
        if current < 0 or current >= len(self.rules):
            return
        dlg = RuleEditDialog(self.rules[current], parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.rules[current] = dlg.get_rule()
            self._save_rules()
            self._refresh_list()
            self.list_widget.setCurrentRow(current)

    def _delete_rule(self):
        current = self.list_widget.currentRow()
        if current < 0 or current >= len(self.rules):
            return
        del self.rules[current]
        self._save_rules()
        self._refresh_list()

    def _move_up(self):
        current = self.list_widget.currentRow()
        if current <= 0 or current >= len(self.rules):
            return
        self.rules[current - 1], self.rules[current] = (
            self.rules[current], self.rules[current - 1]
        )
        self._save_rules()
        self._refresh_list()
        self.list_widget.setCurrentRow(current - 1)

    def _move_down(self):
        current = self.list_widget.currentRow()
        if current < 0 or current >= len(self.rules) - 1:
            return
        self.rules[current + 1], self.rules[current] = (
            self.rules[current], self.rules[current + 1]
        )
        self._save_rules()
        self._refresh_list()
        self.list_widget.setCurrentRow(current + 1)

    def _save_rules(self):
        self.config.set('auto_reply_rules', self.rules)
        self.config.save()

    def _save_options(self):
        self.config.set('auto_reply_enabled', self.chk_enable.isChecked())
        self.config.set('auto_reply_default_mode', self.cb_default_mode.currentText())
        self.config.set('auto_reply_default_delay', self.sp_default_delay.value())
        self.config.save()

    def _on_line_received(self, line: str):
        if not self.chk_enable.isChecked():
            return
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
            if self._match_rule(line, rule):
                delay = rule.get('delay', 0)
                reply = rule.get('reply', '')
                if delay > 0:
                    QTimer.singleShot(
                        delay, lambda r=reply: self._send_reply(r)
                    )
                else:
                    self._send_reply(reply)
                break

    def _match_rule(self, line: str, rule: dict) -> bool:
        match_text = rule.get('match', '')
        mode = rule.get('mode', '精确匹配')
        if mode == '精确匹配':
            return line == match_text
        elif mode == '包含匹配':
            return match_text in line
        elif mode == '通配符':
            return fnmatch.fnmatch(line, match_text)
        return False

    def _send_reply(self, text: str):
        if not text:
            return
        SerialLink.instance().send_text(text, newline='\r\n')

