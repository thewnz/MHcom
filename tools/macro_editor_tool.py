# -*- coding: utf-8 -*-
"""快捷命令管理器 - 支持分组管理、导入导出"""
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QListWidget, QListWidgetItem, QToolBar, QAction,
    QInputDialog, QMessageBox, QComboBox, QFileDialog, QSplitter
)
from config.settings import AppConfig


class MacroEditorTool(QWidget):
    """快捷命令管理器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('快捷命令管理器 - MHcom')
        self.resize(800, 550)
        self.config = AppConfig()
        self.macros = []
        self.current_group = '默认'
        self._load_macros()
        self._build_ui()
        self._refresh_groups()
        self._refresh_macros()

    def _load_macros(self):
        raw = self.config.get('macros', [])
        self.macros = []
        for m in raw:
            item = {
                'name': m.get('name', ''),
                'content': m.get('content', m.get('data', '')),
                'group': m.get('group', '默认'),
            }
            self.macros.append(item)

    def _save_macros(self):
        self.config.set('macros', self.macros)
        self.config.save()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QToolBar()
        toolbar.setStyleSheet('QToolBar{padding:4px;}')
        layout.addWidget(toolbar)

        act_import = QAction('导入', self)
        act_import.triggered.connect(self._import_json)
        toolbar.addAction(act_import)

        act_export = QAction('导出', self)
        act_export.triggered.connect(self._export_json)
        toolbar.addAction(act_export)

        toolbar.addSeparator()

        act_add_group = QAction('添加分组', self)
        act_add_group.triggered.connect(self._add_group)
        toolbar.addAction(act_add_group)

        act_rename_group = QAction('重命名分组', self)
        act_rename_group.triggered.connect(self._rename_group)
        toolbar.addAction(act_rename_group)

        act_del_group = QAction('删除分组', self)
        act_del_group.triggered.connect(self._delete_group)
        toolbar.addAction(act_del_group)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(12, 12, 6, 12)
        left_lay.setSpacing(6)
        left_lay.addWidget(QLabel('分组'))
        self.group_list = QListWidget()
        self.group_list.itemClicked.connect(self._on_group_select)
        left_lay.addWidget(self.group_list, 1)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(6, 12, 12, 12)
        right_lay.setSpacing(8)

        right_lay.addWidget(QLabel('命令列表（双击编辑名称）'))
        self.macro_list = QListWidget()
        self.macro_list.setEditTriggers(QListWidget.DoubleClicked | QListWidget.EditKeyPressed)
        self.macro_list.itemDoubleClicked.connect(self._on_macro_double_click)
        self.macro_list.itemChanged.connect(self._on_macro_rename)
        self.macro_list.itemSelectionChanged.connect(self._on_macro_select)
        right_lay.addWidget(self.macro_list, 1)

        btn_row1 = QHBoxLayout()
        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self._add_macro)
        btn_row1.addWidget(btn_add)
        btn_del = QPushButton('删除')
        btn_del.clicked.connect(self._delete_macro)
        btn_row1.addWidget(btn_del)
        btn_row1.addStretch()
        right_lay.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_up = QPushButton('上移')
        btn_up.clicked.connect(self._move_up)
        btn_row2.addWidget(btn_up)
        btn_down = QPushButton('下移')
        btn_down.clicked.connect(self._move_down)
        btn_row2.addWidget(btn_down)
        btn_row2.addStretch()
        right_lay.addLayout(btn_row2)

        btn_row3 = QHBoxLayout()
        btn_row3.addWidget(QLabel('移动到分组:'))
        self.group_combo = QComboBox()
        btn_row3.addWidget(self.group_combo, 1)
        btn_move = QPushButton('移动')
        btn_move.clicked.connect(self._move_to_group)
        btn_row3.addWidget(btn_move)
        right_lay.addLayout(btn_row3)

        right_lay.addWidget(QLabel('命令内容:'))
        self.ed_content = QPlainTextEdit()
        self.ed_content.setMaximumHeight(120)
        right_lay.addWidget(self.ed_content)

        btn_save = QPushButton('保存内容')
        btn_save.clicked.connect(self._save_content)
        right_lay.addWidget(btn_save)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([200, 500])

    def _get_groups(self):
        groups = set()
        for m in self.macros:
            groups.add(m.get('group', '默认'))
        if not groups:
            groups.add('默认')
        return sorted(groups)

    def _refresh_groups(self):
        groups = self._get_groups()
        self.group_list.clear()
        for g in groups:
            item = QListWidgetItem(g)
            self.group_list.addItem(item)
            if g == self.current_group:
                self.group_list.setCurrentItem(item)

        self.group_combo.clear()
        self.group_combo.addItems(groups)
        idx = self.group_combo.findText(self.current_group)
        if idx >= 0:
            self.group_combo.setCurrentIndex(idx)

    def _refresh_macros(self):
        self.macro_list.blockSignals(True)
        self.macro_list.clear()
        for i, m in enumerate(self.macros):
            if m.get('group', '默认') == self.current_group:
                item = QListWidgetItem(m.get('name', ''))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setData(Qt.UserRole, i)
                self.macro_list.addItem(item)
        self.macro_list.blockSignals(False)
        self.ed_content.clear()

    def _on_group_select(self, item):
        self.current_group = item.text()
        self._refresh_macros()
        idx = self.group_combo.findText(self.current_group)
        if idx >= 0:
            self.group_combo.setCurrentIndex(idx)

    def _on_macro_select(self):
        items = self.macro_list.selectedItems()
        if not items:
            return
        idx = items[0].data(Qt.UserRole)
        if 0 <= idx < len(self.macros):
            self.ed_content.setPlainText(self.macros[idx].get('content', ''))

    def _on_macro_double_click(self, item):
        self.macro_list.editItem(item)

    def _on_macro_rename(self, item):
        idx = item.data(Qt.UserRole)
        if 0 <= idx < len(self.macros):
            new_name = item.text().strip()
            if new_name:
                self.macros[idx]['name'] = new_name
                self._save_macros()
            else:
                item.setText(self.macros[idx].get('name', ''))

    def _add_group(self):
        name, ok = QInputDialog.getText(self, '添加分组', '分组名称:')
        if ok and name.strip():
            name = name.strip()
            if name in self._get_groups():
                QMessageBox.warning(self, '提示', '分组已存在')
                return
            self.current_group = name
            self._refresh_groups()

    def _rename_group(self):
        items = self.group_list.selectedItems()
        if not items:
            return
        old_name = items[0].text()
        if old_name == '默认':
            QMessageBox.warning(self, '提示', '默认分组不能重命名')
            return
        name, ok = QInputDialog.getText(self, '重命名分组', '新名称:', text=old_name)
        if ok and name.strip() and name.strip() != old_name:
            name = name.strip()
            if name in self._get_groups():
                QMessageBox.warning(self, '提示', '分组已存在')
                return
            for m in self.macros:
                if m.get('group', '默认') == old_name:
                    m['group'] = name
            self.current_group = name
            self._save_macros()
            self._refresh_groups()
            self._refresh_macros()

    def _delete_group(self):
        items = self.group_list.selectedItems()
        if not items:
            return
        name = items[0].text()
        if name == '默认':
            QMessageBox.warning(self, '提示', '默认分组不能删除')
            return
        reply = QMessageBox.question(self, '确认', f'删除分组"{name}"？\n该分组下的命令将移动到"默认"分组。')
        if reply != QMessageBox.Yes:
            return
        for m in self.macros:
            if m.get('group', '默认') == name:
                m['group'] = '默认'
        self.current_group = '默认'
        self._save_macros()
        self._refresh_groups()
        self._refresh_macros()

    def _add_macro(self):
        name, ok = QInputDialog.getText(self, '添加命令', '命令名称:')
        if ok and name.strip():
            self.macros.append({
                'name': name.strip(),
                'content': '',
                'group': self.current_group,
            })
            self._save_macros()
            self._refresh_macros()

    def _delete_macro(self):
        items = self.macro_list.selectedItems()
        if not items:
            return
        idx = items[0].data(Qt.UserRole)
        if 0 <= idx < len(self.macros):
            reply = QMessageBox.question(self, '确认', '删除该命令？')
            if reply == QMessageBox.Yes:
                del self.macros[idx]
                self._save_macros()
                self._refresh_macros()

    def _move_up(self):
        items = self.macro_list.selectedItems()
        if not items:
            return
        idx = items[0].data(Qt.UserRole)
        group_macros = [i for i, m in enumerate(self.macros) if m.get('group', '默认') == self.current_group]
        pos = group_macros.index(idx) if idx in group_macros else -1
        if pos <= 0:
            return
        prev_idx = group_macros[pos - 1]
        self.macros[idx], self.macros[prev_idx] = self.macros[prev_idx], self.macros[idx]
        self._save_macros()
        self._refresh_macros()
        self._select_macro_by_original_idx(prev_idx)

    def _move_down(self):
        items = self.macro_list.selectedItems()
        if not items:
            return
        idx = items[0].data(Qt.UserRole)
        group_macros = [i for i, m in enumerate(self.macros) if m.get('group', '默认') == self.current_group]
        pos = group_macros.index(idx) if idx in group_macros else -1
        if pos < 0 or pos >= len(group_macros) - 1:
            return
        next_idx = group_macros[pos + 1]
        self.macros[idx], self.macros[next_idx] = self.macros[next_idx], self.macros[idx]
        self._save_macros()
        self._refresh_macros()
        self._select_macro_by_original_idx(next_idx)

    def _select_macro_by_original_idx(self, original_idx):
        for i in range(self.macro_list.count()):
            item = self.macro_list.item(i)
            if item.data(Qt.UserRole) == original_idx:
                self.macro_list.setCurrentRow(i)
                break

    def _move_to_group(self):
        items = self.macro_list.selectedItems()
        if not items:
            return
        target_group = self.group_combo.currentText()
        if not target_group or target_group == self.current_group:
            return
        idx = items[0].data(Qt.UserRole)
        if 0 <= idx < len(self.macros):
            self.macros[idx]['group'] = target_group
            self._save_macros()
            self._refresh_macros()

    def _save_content(self):
        items = self.macro_list.selectedItems()
        if not items:
            return
        idx = items[0].data(Qt.UserRole)
        if 0 <= idx < len(self.macros):
            self.macros[idx]['content'] = self.ed_content.toPlainText()
            self._save_macros()

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, '导入 JSON', '', 'JSON文件 (*.json)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                    raise ValueError('格式错误')
            imported = []
            for m in data:
                if isinstance(m, dict) and 'name' in m:
                    imported.append({
                        'name': m.get('name', ''),
                        'content': m.get('content', m.get('data', '')),
                        'group': m.get('group', '默认'),
                    })
            if not imported:
                QMessageBox.warning(self, '提示', '没有有效的命令数据')
                return
            reply = QMessageBox.question(self, '确认', f'导入 {len(imported)} 条命令？\n是: 追加  否: 替换')
            if reply == QMessageBox.Yes:
                self.macros.extend(imported)
            elif reply == QMessageBox.No:
                self.macros = imported
            else:
                return
            self._save_macros()
            groups = self._get_groups()
            if self.current_group not in groups:
                self.current_group = groups[0] if groups else '默认'
            self._refresh_groups()
            self._refresh_macros()
            QMessageBox.information(self, '成功', '导入成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导入失败: {e}')

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, '导出 JSON', 'macros.json', 'JSON文件 (*.json)')
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.macros, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, '成功', '导出成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出失败: {e}')

