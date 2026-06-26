# -*- coding: utf-8 -*-
"""
通用数据解析�?
- 按字段定义解析字节流
- 支持多种数据类型和字节序
"""

from .crc_calculator import parse_value, LE, BE


DATA_TYPES = {
    'uint8':  {'length': 1, 'signed': False, 'scale': 1.0},
    'int8':   {'length': 1, 'signed': True,  'scale': 1.0},
    'uint16': {'length': 2, 'signed': False, 'scale': 1.0},
    'int16':  {'length': 2, 'signed': True,  'scale': 1.0},
    'uint32': {'length': 4, 'signed': False, 'scale': 1.0},
    'int32':  {'length': 4, 'signed': True,  'scale': 1.0},
    'float':  {'length': 4, 'signed': True,  'scale': 1.0, 'is_float': True},
}


class FieldDef:
    """字段定义"""
    def __init__(self, name: str, offset: int, dtype: str = 'uint16',
                 endian: str = BE, scale: float = 1.0, unit: str = ''):
        self.name = name
        self.offset = offset
        self.dtype = dtype
        self.endian = endian
        self.scale = scale
        self.unit = unit
        if dtype not in DATA_TYPES:
            raise ValueError(f"未知类型: {dtype}")

    def parse(self, data: bytes) -> float:
        info = DATA_TYPES[self.dtype]
        length = info['length']
        if info.get('is_float'):
            # IEEE 754 float
            if self.offset + length > len(data):
                raise ValueError("数据不足")
            chunk = data[self.offset:self.offset + length]
            if self.endian == LE:
                chunk = chunk[::-1]
            import struct
            return struct.unpack('>f' if self.endian == BE else '<f', chunk)[0]
        return parse_value(data, self.offset, length, self.endian,
                          info['signed'], self.scale)


def parse_frame(data: bytes, fields: list) -> list:
    """按字段定义解析一帧数�?
    fields: [FieldDef, ...]
    返回: [(name, value, unit), ...]
    """
    result = []
    for f in fields:
        try:
            v = f.parse(data)
            result.append((f.name, v, f.unit))
        except Exception as e:
            result.append((f.name, None, f.unit))
    return result


def detect_frame(data: bytes, header: bytes, min_length: int = 4) -> int:
    """检测帧边界 - 找到header第一次出现的位置
    返回: header的位�? 未找到返�?-1
    """
    return data.find(header)
