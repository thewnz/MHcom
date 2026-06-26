# -*- coding: utf-8 -*-
"""
协议解析器工具 - 自定义帧格式解析 + 实时监听
支持: 帧头+长度+数据+校验 的自定义协议，实时监听串口数据
"""
import struct
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QCheckBox, QSpinBox,
    QToolBar, QAction, QInputDialog, QMessageBox,
    QTabWidget, QFormLayout
)
from PyQt5.QtGui import QColor, QBrush
from core.data_bus import DataBus
from core.crc_calculator import crc16_modbus, crc16_ccitt, sum8, xor8
from config.settings import AppConfig


# ==================== 协议解析核心类 ====================

class FieldDef:
    """字段定义"""
    TYPES = ['u8', 'u16', 'u32', 'i8', 'i16', 'i32', 'float']

    def __init__(self, name='', offset=0, ftype='u8'):
        self.name = name
        self.offset = offset
        self.ftype = ftype

    def size(self):
        """返回字段字节数"""
        if self.ftype in ('u8', 'i8'):
            return 1
        elif self.ftype in ('u16', 'i16'):
            return 2
        elif self.ftype in ('u32', 'i32', 'float'):
            return 4
        return 1

    def to_dict(self):
        return {'name': self.name, 'offset': self.offset, 'type': self.ftype}

    @classmethod
    def from_dict(cls, d):
        return cls(name=d.get('name', ''), offset=d.get('offset', 0), ftype=d.get('type', 'u8'))


class ProtocolConfig:
    """协议帧格式配置"""

    CHECKSUM_ALGS = ['CRC16 Modbus', 'CRC16 CCITT', 'Sum8', 'XOR8', '无校验']
    ENDIAN_OPTIONS = ['大端 (BE)', '小端 (LE)']
    LEN_MODE_OPTIONS = [
        '长度 = 数据域长度',
        '长度 = 数据域 + 校验',
        '长度 = 整帧长度',
        '长度 = 从长度字段后到帧尾',
    ]

    def __init__(self):
        self.frame_header = 'AA 55'          # 帧头 HEX
        self.len_offset = 2                   # 长度字段偏移（从帧头开始算）
        self.len_bytes = 1                    # 长度字段字节数
        self.len_mode = '长度 = 数据域长度'    # 长度字段含义
        self.checksum_alg = 'CRC16 Modbus'    # 校验算法
        self.checksum_at_end = True           # 校验在帧末尾
        self.endian = '大端 (BE)'             # 字节序
        self.fields = []                      # 字段列表

    def header_bytes(self):
        """获取帧头字节"""
        try:
            parts = self.frame_header.strip().split()
            return bytes(int(p, 16) for p in parts if p)
        except Exception:
            return b''

    def is_little_endian(self):
        return 'LE' in self.endian

    def checksum_size(self):
        """校验字段字节数"""
        if self.checksum_alg == '无校验':
            return 0
        elif self.checksum_alg in ('Sum8', 'XOR8'):
            return 1
        else:
            return 2

    def calc_checksum(self, data: bytes) -> int:
        """计算校验值"""
        if self.checksum_alg == 'CRC16 Modbus':
            return crc16_modbus(data)
        elif self.checksum_alg == 'CRC16 CCITT':
            return crc16_ccitt(data)
        elif self.checksum_alg == 'Sum8':
            return sum8(data)
        elif self.checksum_alg == 'XOR8':
            return xor8(data)
        return 0

    def parse_value(self, data: bytes, offset: int, ftype: str):
        """从数据中解析指定类型的值"""
        endian = '<' if self.is_little_endian() else '>'
        try:
            if ftype == 'u8':
                return data[offset]
            elif ftype == 'i8':
                return struct.unpack('b', data[offset:offset+1])[0]
            elif ftype == 'u16':
                return struct.unpack(endian + 'H', data[offset:offset+2])[0]
            elif ftype == 'i16':
                return struct.unpack(endian + 'h', data[offset:offset+2])[0]
            elif ftype == 'u32':
                return struct.unpack(endian + 'I', data[offset:offset+4])[0]
            elif ftype == 'i32':
                return struct.unpack(endian + 'i', data[offset:offset+4])[0]
            elif ftype == 'float':
                return struct.unpack(endian + 'f', data[offset:offset+4])[0]
        except Exception:
            return None
        return None

    def field_hex(self, data: bytes, offset: int, ftype: str) -> str:
        """获取字段的十六进制表示"""
        size = 1
        if ftype in ('u16', 'i16'):
            size = 2
        elif ftype in ('u32', 'i32', 'float'):
            size = 4
        if offset + size <= len(data):
            return ' '.join(f'{b:02X}' for b in data[offset:offset+size])
        return ''

    def to_dict(self):
        return {
            'frame_header': self.frame_header,
            'len_offset': self.len_offset,
            'len_bytes': self.len_bytes,
            'len_mode': self.len_mode,
            'checksum_alg': self.checksum_alg,
            'checksum_at_end': self.checksum_at_end,
            'endian': self.endian,
            'fields': [f.to_dict() for f in self.fields],
        }

    @classmethod
    def from_dict(cls, d):
        cfg = cls()
        cfg.frame_header = d.get('frame_header', 'AA 55')
        cfg.len_offset = d.get('len_offset', 2)
        cfg.len_bytes = d.get('len_bytes', 1)
        cfg.len_mode = d.get('len_mode', '长度 = 数据域长度')
        cfg.checksum_alg = d.get('checksum_alg', 'CRC16 Modbus')
        cfg.checksum_at_end = d.get('checksum_at_end', True)
        cfg.endian = d.get('endian', '大端 (BE)')
        cfg.fields = [FieldDef.from_dict(f) for f in d.get('fields', [])]
        return cfg


class FrameParser:
    """帧解析器 - 从数据流中查找并解析帧"""

    def __init__(self, config: ProtocolConfig):
        self.config = config
        self._buffer = b''
        self._buffer_max = 65536  # 缓冲区上限，防止无限增长

    def reset(self):
        self._buffer = b''

    def feed(self, data: bytes):
        """追加数据，超出上限时清空旧数据"""
        self._buffer += data
        if len(self._buffer) > self._buffer_max:
            self._buffer = self._buffer[-self._buffer_max:]

    def try_parse_frame(self):
        """
        尝试从缓冲区解析一帧
        返回: (frame_data, parsed_fields) 或 None
        parsed_fields: [(name, value, hex_str)]
        """
        header = self.config.header_bytes()
        if not header:
            return None

        # 查找帧头
        idx = self._buffer.find(header)
        if idx < 0:
            # 保留最后几个字节，防止帧头被截断
            if len(self._buffer) > len(header) * 2:
                self._buffer = self._buffer[-(len(header) - 1):]
            return None

        # 移除帧头之前的数据
        if idx > 0:
            self._buffer = self._buffer[idx:]

        header_len = len(header)
        len_end_offset = self.config.len_offset + self.config.len_bytes
        min_len = len_end_offset
        if len(self._buffer) < min_len:
            return None

        # 解析长度字段
        len_start = self.config.len_offset
        len_end = len_start + self.config.len_bytes
        len_bytes_data = self._buffer[len_start:len_end]
        if self.config.is_little_endian():
            frame_len = int.from_bytes(len_bytes_data, 'little')
        else:
            frame_len = int.from_bytes(len_bytes_data, 'big')

        # 根据长度模式计算总帧长
        mode = self.config.len_mode
        cs_size = self.config.checksum_size()

        if mode == '长度 = 数据域长度':
            # 总帧长 = 长度字段结束位置 + 数据域长度 + 校验长度
            total_len = len_end_offset + frame_len + cs_size
        elif mode == '长度 = 数据域 + 校验':
            # 总帧长 = 长度字段结束位置 + frame_len
            total_len = len_end_offset + frame_len
        elif mode == '长度 = 整帧长度':
            # 总帧长就是 frame_len
            total_len = frame_len
        elif mode == '长度 = 从长度字段后到帧尾':
            # 总帧长 = 长度字段起始位置 + frame_len
            total_len = self.config.len_offset + frame_len
        else:
            total_len = len_end_offset + frame_len + cs_size

        if total_len < min_len or total_len > 65536:
            # 长度不合理，跳过当前帧头
            self._buffer = self._buffer[1:]
            return None

        if len(self._buffer) < total_len:
            return None

        # 取出完整一帧
        frame = self._buffer[:total_len]
        self._buffer = self._buffer[total_len:]

        # 校验
        if self.config.checksum_alg != '无校验' and self.config.checksum_at_end and cs_size > 0:
            data_for_check = frame[:-cs_size]
            expected_cs = self.config.calc_checksum(data_for_check)
            actual_cs_bytes = frame[-cs_size:]
            if self.config.is_little_endian():
                actual_cs = int.from_bytes(actual_cs_bytes, 'little')
            else:
                actual_cs = int.from_bytes(actual_cs_bytes, 'big')
            if expected_cs != actual_cs:
                return None

        # 解析字段（数据域从长度字段之后开始，偏移相对数据域起始）
        data_start = len_end_offset
        data_end = total_len - cs_size if self.config.checksum_at_end else total_len
        data_area = frame[data_start:data_end]

        parsed = []
        for field in self.config.fields:
            if field.offset + self._field_size(field.ftype) <= len(data_area):
                val = self.config.parse_value(data_area, field.offset, field.ftype)
                hex_str = self.config.field_hex(data_area, field.offset, field.ftype)
                parsed.append((field.name if field.name else f'字段@{field.offset}', val, hex_str))
            else:
                parsed.append((field.name if field.name else f'字段@{field.offset}', None, ''))

        return frame, parsed

    def _field_size(self, ftype):
        if ftype in ('u8', 'i8'):
            return 1
        elif ftype in ('u16', 'i16'):
            return 2
        elif ftype in ('u32', 'i32', 'float'):
            return 4
        return 1


# ==================== 主窗口类 ====================

class ProtocolParserTool(QWidget):
    """协议解析器工具"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('协议解析器 - MHcom')
        self.resize(1100, 700)

        self.data_bus = DataBus.instance()
        self.config = AppConfig()
        self.proto_cfg = ProtocolConfig()
        self.parser = FrameParser(self.proto_cfg)
        self.monitoring = False
        self.templates = []

        self._load_templates()
        self._build_ui()
        self._refresh_template_combo()

    # -------------------- UI 构建 --------------------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部工具栏
        self._build_toolbar(main_layout)

        # 主区域分割
        main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(main_splitter, 1)

        # 上半部分：左侧配置 + 右侧结果
        top_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(top_splitter)

        # 左侧：帧格式配置
        self._build_config_panel(top_splitter)

        # 右侧：解析结果 + 离线解析
        self._build_result_panel(top_splitter)

        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 2)
        top_splitter.setSizes([380, 720])

        # 底部：原始数据日志
        self._build_log_panel(main_splitter)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setSizes([500, 200])

    def _build_toolbar(self, parent_layout):
        toolbar = QToolBar()
        toolbar.setStyleSheet('QToolBar{padding:4px; spacing:6px;}')
        parent_layout.addWidget(toolbar)

        # 模板选择
        toolbar.addWidget(QLabel('  模板: '))
        self.cmb_template = QComboBox()
        self.cmb_template.setMinimumWidth(160)
        self.cmb_template.currentIndexChanged.connect(self._on_template_selected)
        toolbar.addWidget(self.cmb_template)

        btn_save_tpl = QPushButton('保存模板')
        btn_save_tpl.clicked.connect(self._save_template)
        toolbar.addWidget(btn_save_tpl)

        btn_del_tpl = QPushButton('删除模板')
        btn_del_tpl.clicked.connect(self._delete_template)
        toolbar.addWidget(btn_del_tpl)

        toolbar.addSeparator()

        # 实时监听开关
        self.chk_monitor = QCheckBox('实时监听')
        self.chk_monitor.setStyleSheet('font-weight:600; padding:4px 8px;')
        self.chk_monitor.toggled.connect(self._toggle_monitor)
        toolbar.addWidget(self.chk_monitor)

        toolbar.addSeparator()

        act_clear = QAction('清空结果', self)
        act_clear.triggered.connect(self._clear_results)
        toolbar.addAction(act_clear)

        act_reset_buf = QAction('重置缓冲区', self)
        act_reset_buf.triggered.connect(self._reset_buffer)
        toolbar.addAction(act_reset_buf)

    def _build_config_panel(self, parent_splitter):
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(10, 10, 5, 10)
        left_lay.setSpacing(8)

        # 帧头配置
        gb_header = QGroupBox('帧头配置')
        hl = QFormLayout(gb_header)
        hl.setContentsMargins(10, 15, 10, 10)
        hl.setSpacing(6)

        self.ed_header = QLineEdit('AA 55')
        self.ed_header.setPlaceholderText('如: AA 55 或 01 02 03')
        hl.addRow('帧头 (HEX):', self.ed_header)

        left_lay.addWidget(gb_header)

        # 长度配置
        gb_len = QGroupBox('长度字段')
        ll = QFormLayout(gb_len)
        ll.setContentsMargins(10, 15, 10, 10)
        ll.setSpacing(6)

        self.spin_len_offset = QSpinBox()
        self.spin_len_offset.setRange(0, 255)
        self.spin_len_offset.setValue(2)
        ll.addRow('偏移位置:', self.spin_len_offset)

        self.spin_len_bytes = QSpinBox()
        self.spin_len_bytes.setRange(1, 4)
        self.spin_len_bytes.setValue(1)
        ll.addRow('字节数:', self.spin_len_bytes)

        self.cmb_len_mode = QComboBox()
        self.cmb_len_mode.addItems(ProtocolConfig.LEN_MODE_OPTIONS)
        ll.addRow('长度含义:', self.cmb_len_mode)

        left_lay.addWidget(gb_len)

        # 校验配置
        gb_cs = QGroupBox('校验配置')
        cl = QFormLayout(gb_cs)
        cl.setContentsMargins(10, 15, 10, 10)
        cl.setSpacing(6)

        self.cmb_checksum = QComboBox()
        self.cmb_checksum.addItems(ProtocolConfig.CHECKSUM_ALGS)
        cl.addRow('校验算法:', self.cmb_checksum)

        self.cmb_endian = QComboBox()
        self.cmb_endian.addItems(ProtocolConfig.ENDIAN_OPTIONS)
        cl.addRow('字节序:', self.cmb_endian)

        left_lay.addWidget(gb_cs)

        # 字段配置
        gb_fields = QGroupBox('数据字段 (相对数据域偏移)')
        fl = QVBoxLayout(gb_fields)
        fl.setContentsMargins(10, 15, 10, 10)
        fl.setSpacing(6)

        self.tbl_fields = QTableWidget(0, 3)
        self.tbl_fields.setHorizontalHeaderLabels(['字段名', '偏移', '类型'])
        self.tbl_fields.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_fields.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_fields.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_fields.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_fields.setStyleSheet('QTableWidget{font-size:12px;}')
        fl.addWidget(self.tbl_fields, 1)

        btn_row = QHBoxLayout()
        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self._add_field)
        btn_row.addWidget(btn_add)

        btn_del = QPushButton('删除')
        btn_del.clicked.connect(self._delete_field)
        btn_row.addWidget(btn_del)

        btn_up = QPushButton('上移')
        btn_up.clicked.connect(self._move_field_up)
        btn_row.addWidget(btn_up)

        btn_down = QPushButton('下移')
        btn_down.clicked.connect(self._move_field_down)
        btn_row.addWidget(btn_down)

        fl.addLayout(btn_row)

        left_lay.addWidget(gb_fields, 1)

        # 应用配置按钮
        btn_apply = QPushButton('应用配置')
        btn_apply.setStyleSheet(
            'background:#3B82F6; color:white; padding:8px; '
            'border-radius:4px; font-weight:600;'
        )
        btn_apply.clicked.connect(self._apply_config)
        left_lay.addWidget(btn_apply)

        parent_splitter.addWidget(left)

    def _build_result_panel(self, parent_splitter):
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(5, 10, 10, 10)
        right_lay.setSpacing(8)

        tab_widget = QTabWidget()
        right_lay.addWidget(tab_widget, 1)

        # --- 解析结果 Tab ---
        result_widget = QWidget()
        rl = QVBoxLayout(result_widget)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        rl.addWidget(QLabel('解析结果:'))
        self.tbl_result = QTableWidget(0, 3)
        self.tbl_result.setHorizontalHeaderLabels(['字段名', '值', '十六进制'])
        self.tbl_result.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_result.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_result.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_result.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_result.setStyleSheet('QTableWidget{font-family:Consolas; font-size:12px;}')
        rl.addWidget(self.tbl_result, 1)

        # 帧信息标签
        self.lbl_frame_info = QLabel('暂无帧')
        self.lbl_frame_info.setStyleSheet(
            'padding:6px 10px; background:#F1F5F9; border-radius:4px; '
            'color:#475569; font-size:12px;'
        )
        rl.addWidget(self.lbl_frame_info)

        tab_widget.addTab(result_widget, '实时结果')

        # --- 离线解析 Tab ---
        offline_widget = QWidget()
        ol = QVBoxLayout(offline_widget)
        ol.setContentsMargins(10, 10, 10, 10)
        ol.setSpacing(8)

        ol.addWidget(QLabel('HEX 数据输入:'))
        self.txt_offline_input = QPlainTextEdit()
        self.txt_offline_input.setMaximumHeight(120)
        self.txt_offline_input.setPlaceholderText('输入 HEX 数据，空格分隔，如: AA 55 05 01 02 03 04 05')
        ol.addWidget(self.txt_offline_input)

        btn_row = QHBoxLayout()
        btn_parse = QPushButton('解析')
        btn_parse.setStyleSheet(
            'background:#10B981; color:white; padding:6px 16px; '
            'border-radius:4px; font-weight:600;'
        )
        btn_parse.clicked.connect(self._offline_parse)
        btn_row.addWidget(btn_parse)

        btn_clear = QPushButton('清空')
        btn_clear.clicked.connect(lambda: self.txt_offline_input.clear())
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        ol.addLayout(btn_row)

        ol.addWidget(QLabel('解析结果:'))
        self.tbl_offline_result = QTableWidget(0, 3)
        self.tbl_offline_result.setHorizontalHeaderLabels(['字段名', '值', '十六进制'])
        self.tbl_offline_result.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_offline_result.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_offline_result.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_offline_result.setStyleSheet('QTableWidget{font-family:Consolas; font-size:12px;}')
        ol.addWidget(self.tbl_offline_result, 1)

        self.lbl_offline_info = QLabel('')
        self.lbl_offline_info.setStyleSheet(
            'padding:6px 10px; background:#F1F5F9; border-radius:4px; '
            'color:#475569; font-size:12px;'
        )
        ol.addWidget(self.lbl_offline_info)

        tab_widget.addTab(offline_widget, '离线解析')

        parent_splitter.addWidget(right)

    def _build_log_panel(self, parent_splitter):
        bottom = QGroupBox('原始数据日志')
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(10, 15, 10, 10)
        bl.setSpacing(6)

        log_ctrl = QHBoxLayout()
        self.chk_log_hex = QCheckBox('HEX 显示')
        self.chk_log_hex.setChecked(True)
        log_ctrl.addWidget(self.chk_log_hex)

        self.chk_log_auto_scroll = QCheckBox('自动滚动')
        self.chk_log_auto_scroll.setChecked(True)
        log_ctrl.addWidget(self.chk_log_auto_scroll)

        btn_clear_log = QPushButton('清空日志')
        btn_clear_log.clicked.connect(self._clear_log)
        log_ctrl.addStretch()
        log_ctrl.addWidget(btn_clear_log)

        bl.addLayout(log_ctrl)

        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumBlockCount(5000)
        self.txt_log.setStyleSheet(
            'QPlainTextEdit{background:#F8FAFC; font-family:Consolas; font-size:12px;}'
        )
        bl.addWidget(self.txt_log, 1)

        parent_splitter.addWidget(bottom)

    # -------------------- 配置应用 --------------------

    def _apply_config(self):
        """从UI读取配置并应用"""
        self.proto_cfg.frame_header = self.ed_header.text().strip()
        self.proto_cfg.len_offset = self.spin_len_offset.value()
        self.proto_cfg.len_bytes = self.spin_len_bytes.value()
        self.proto_cfg.len_mode = self.cmb_len_mode.currentText()
        self.proto_cfg.checksum_alg = self.cmb_checksum.currentText()
        self.proto_cfg.endian = self.cmb_endian.currentText()

        # 读取字段表格
        self.proto_cfg.fields = []
        for row in range(self.tbl_fields.rowCount()):
            name_item = self.tbl_fields.item(row, 0)
            offset_item = self.tbl_fields.item(row, 1)
            type_combo = self.tbl_fields.cellWidget(row, 2)
            if name_item and offset_item and type_combo:
                try:
                    name = name_item.text().strip()
                    offset = int(offset_item.text())
                    ftype = type_combo.currentText().strip()
                    if ftype in FieldDef.TYPES:
                        self.proto_cfg.fields.append(FieldDef(name, offset, ftype))
                except ValueError:
                    pass

        self.parser = FrameParser(self.proto_cfg)
        self._append_log('配置已应用')

    def _load_config_to_ui(self, cfg: ProtocolConfig):
        """将配置加载到UI"""
        self.ed_header.setText(cfg.frame_header)
        self.spin_len_offset.setValue(cfg.len_offset)
        self.spin_len_bytes.setValue(cfg.len_bytes)
        idx = self.cmb_len_mode.findText(cfg.len_mode)
        if idx >= 0:
            self.cmb_len_mode.setCurrentIndex(idx)
        idx = self.cmb_checksum.findText(cfg.checksum_alg)
        if idx >= 0:
            self.cmb_checksum.setCurrentIndex(idx)
        idx = self.cmb_endian.findText(cfg.endian)
        if idx >= 0:
            self.cmb_endian.setCurrentIndex(idx)

        # 加载字段
        self.tbl_fields.setRowCount(0)
        for field in cfg.fields:
            self._add_field_row(field.name, str(field.offset), field.ftype)

    # -------------------- 字段表格操作 --------------------

    def _add_field(self):
        self._add_field_row('新字段', '0', 'u8')

    def _add_field_row(self, name, offset, ftype):
        row = self.tbl_fields.rowCount()
        self.tbl_fields.insertRow(row)
        self.tbl_fields.setItem(row, 0, QTableWidgetItem(name))
        self.tbl_fields.setItem(row, 1, QTableWidgetItem(offset))

        combo = QComboBox()
        combo.addItems(FieldDef.TYPES)
        idx = combo.findText(ftype)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        self.tbl_fields.setCellWidget(row, 2, combo)

    def _delete_field(self):
        rows = set()
        for item in self.tbl_fields.selectedItems():
            rows.add(item.row())
        for row in sorted(rows, reverse=True):
            self.tbl_fields.removeRow(row)

    def _move_field_up(self):
        row = self.tbl_fields.currentRow()
        if row <= 0:
            return
        self._swap_rows(row, row - 1)
        self.tbl_fields.setCurrentRow(row - 1)

    def _move_field_down(self):
        row = self.tbl_fields.currentRow()
        if row < 0 or row >= self.tbl_fields.rowCount() - 1:
            return
        self._swap_rows(row, row + 1)
        self.tbl_fields.setCurrentRow(row + 1)

    def _swap_rows(self, r1, r2):
        for col in range(self.tbl_fields.columnCount()):
            if col == 2:
                w1 = self.tbl_fields.cellWidget(r1, col)
                w2 = self.tbl_fields.cellWidget(r2, col)
                t1, t2 = w1.currentText(), w2.currentText()
                w1.setCurrentText(t2)
                w2.setCurrentText(t1)
            else:
                i1 = self.tbl_fields.item(r1, col)
                i2 = self.tbl_fields.item(r2, col)
                t1 = i1.text() if i1 else ''
                t2 = i2.text() if i2 else ''
                if not i1:
                    self.tbl_fields.setItem(r1, col, QTableWidgetItem(t2))
                else:
                    i1.setText(t2)
                if not i2:
                    self.tbl_fields.setItem(r2, col, QTableWidgetItem(t1))
                else:
                    i2.setText(t1)

    # -------------------- 实时监听 --------------------

    def _toggle_monitor(self, checked):
        self.monitoring = checked
        if checked:
            self._apply_config()
            self.data_bus.raw_received.connect(self._on_serial_data)
            self._append_log('实时监听已开启')
        else:
            try:
                self.data_bus.raw_received.disconnect(self._on_serial_data)
            except Exception:
                pass
            self._append_log('实时监听已关闭')

    def _on_serial_data(self, data: bytes):
        if not self.monitoring:
            return

        self._append_log(f'RX ({len(data)}B): {" ".join(f"{b:02X}" for b in data)}', is_rx=True)

        self.parser.feed(data)

        # 尝试解析帧
        while True:
            result = self.parser.try_parse_frame()
            if result is None:
                break
            frame, parsed = result
            self._show_parsed_frame(frame, parsed)

    def _show_parsed_frame(self, frame: bytes, parsed: list):
        """显示解析结果"""
        self.tbl_result.setRowCount(0)
        for i, (name, value, hex_str) in enumerate(parsed):
            row = self.tbl_result.rowCount()
            self.tbl_result.insertRow(row)
            self.tbl_result.setItem(row, 0, QTableWidgetItem(name))

            val_str = str(value) if value is not None else '-'
            val_item = QTableWidgetItem(val_str)
            if value is None:
                val_item.setForeground(QBrush(QColor('#94A3B8')))
            self.tbl_result.setItem(row, 1, val_item)

            self.tbl_result.setItem(row, 2, QTableWidgetItem(hex_str))

        self.lbl_frame_info.setText(
            f'帧长度: {len(frame)} 字节 | '
            f'HEX: {" ".join(f"{b:02X}" for b in frame[:20])}'
            f'{"..." if len(frame) > 20 else ""}'
        )

    # -------------------- 离线解析 --------------------

    def _offline_parse(self):
        text = self.txt_offline_input.toPlainText().strip()
        if not text:
            self.lbl_offline_info.setText('请输入 HEX 数据')
            return

        try:
            parts = text.split()
            data = bytes(int(p, 16) for p in parts if p)
        except ValueError as e:
            self.lbl_offline_info.setText(f'HEX 格式错误: {e}')
            return

        self._apply_config()

        # 尝试解析
        parser = FrameParser(self.proto_cfg)
        parser.feed(data)
        result = parser.try_parse_frame()

        if result is None:
            self.lbl_offline_info.setText(
                f'解析失败: 未找到有效帧 (输入 {len(data)} 字节)\n'
                f'提示: 请检查帧头、长度配置是否正确'
            )
            self.tbl_offline_result.setRowCount(0)
            return

        frame, parsed = result
        self.tbl_offline_result.setRowCount(0)
        for name, value, hex_str in parsed:
            row = self.tbl_offline_result.rowCount()
            self.tbl_offline_result.insertRow(row)
            self.tbl_offline_result.setItem(row, 0, QTableWidgetItem(name))

            val_str = str(value) if value is not None else '-'
            val_item = QTableWidgetItem(val_str)
            if value is None:
                val_item.setForeground(QBrush(QColor('#94A3B8')))
            self.tbl_offline_result.setItem(row, 1, val_item)

            self.tbl_offline_result.setItem(row, 2, QTableWidgetItem(hex_str))

        self.lbl_offline_info.setText(
            f'解析成功! 帧长度: {len(frame)} 字节 | '
            f'HEX: {" ".join(f"{b:02X}" for b in frame[:30])}'
            f'{"..." if len(frame) > 30 else ""}'
        )

    # -------------------- 模板管理 --------------------

    def _load_templates(self):
        raw = self.config.get('protocol_templates', [])
        self.templates = []
        for t in raw:
            if isinstance(t, dict) and 'name' in t:
                self.templates.append({
                    'name': t['name'],
                    'config': ProtocolConfig.from_dict(t.get('config', {})),
                })

        # 默认模板
        if not self.templates:
            default_cfg = ProtocolConfig()
            default_cfg.fields = [
                FieldDef('设备地址', 0, 'u8'),
                FieldDef('功能码', 1, 'u8'),
                FieldDef('数据长度', 2, 'u8'),
            ]
            self.templates.append({'name': '默认模板', 'config': default_cfg})

    def _save_templates(self):
        data = []
        for t in self.templates:
            data.append({
                'name': t['name'],
                'config': t['config'].to_dict(),
            })
        self.config.set('protocol_templates', data)
        self.config.save()

    def _refresh_template_combo(self):
        self.cmb_template.blockSignals(True)
        self.cmb_template.clear()
        for t in self.templates:
            self.cmb_template.addItem(t['name'])
        self.cmb_template.blockSignals(False)

        if self.templates:
            self._load_config_to_ui(self.templates[0]['config'])

    def _on_template_selected(self, index):
        if 0 <= index < len(self.templates):
            self._load_config_to_ui(self.templates[index]['config'])
            self._append_log(f'加载模板: {self.templates[index]["name"]}')

    def _save_template(self):
        name, ok = QInputDialog.getText(self, '保存模板', '模板名称:')
        if not ok or not name.strip():
            return
        name = name.strip()

        self._apply_config()

        # 检查是否已存在
        for i, t in enumerate(self.templates):
            if t['name'] == name:
                reply = QMessageBox.question(self, '确认', f'模板"{name}"已存在，是否覆盖？')
                if reply != QMessageBox.Yes:
                    return
                self.templates[i] = {'name': name, 'config': self.proto_cfg}
                break
        else:
            self.templates.append({'name': name, 'config': self.proto_cfg})

        self._save_templates()
        self._refresh_template_combo()
        idx = self.cmb_template.findText(name)
        if idx >= 0:
            self.cmb_template.setCurrentIndex(idx)
        QMessageBox.information(self, '成功', f'模板"{name}"已保存')

    def _delete_template(self):
        idx = self.cmb_template.currentIndex()
        if idx < 0:
            return
        name = self.templates[idx]['name']
        reply = QMessageBox.question(self, '确认', f'删除模板"{name}"？')
        if reply != QMessageBox.Yes:
            return
        del self.templates[idx]
        self._save_templates()
        self._refresh_template_combo()

    # -------------------- 日志 --------------------

    def _append_log(self, msg, is_rx=False, is_tx=False):
        from datetime import datetime
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        prefix = ''
        if is_rx:
            prefix = '[RX] '
        elif is_tx:
            prefix = '[TX] '
        line = f'[{ts}] {prefix}{msg}'
        self.txt_log.appendPlainText(line)
        if self.chk_log_auto_scroll.isChecked():
            sb = self.txt_log.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _clear_log(self):
        self.txt_log.clear()

    def _clear_results(self):
        self.tbl_result.setRowCount(0)
        self.lbl_frame_info.setText('暂无帧')

    def _reset_buffer(self):
        self.parser.reset()
        self._append_log('缓冲区已重置')

    # -------------------- 关闭处理 --------------------

    def closeEvent(self, event):
        if self.monitoring:
            try:
                self.data_bus.raw_received.disconnect(self._on_serial_data)
            except Exception:
                pass
        super().closeEvent(event)

