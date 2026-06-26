# -*- coding: utf-8 -*-
"""
CRC/鏍￠獙鍜岃绠?
鏀寔: Sum8, Sum16, CRC8, CRC16-CCITT, CRC16-MODBUS, CRC32
"""


def sum8(data: bytes) -> int:
    """8浣嶇疮鍔犲拰"""
    return sum(data) & 0xFF


def sum16(data: bytes) -> int:
    """16浣嶇疮鍔犲拰"""
    s = sum(data)
    return s & 0xFFFF


def xor8(data: bytes) -> int:
    """8浣嶅紓鎴栧拰"""
    r = 0
    for b in data:
        r ^= b
    return r & 0xFF


def crc8(data: bytes, poly=0x07, init=0x00) -> int:
    """CRC-8 (澶氶」寮?0x07)"""
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def crc16_ccitt(data: bytes, init=0xFFFF) -> int:
    """CRC-16 CCITT (澶氶」寮?0x1021)"""
    crc = init
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def crc16_modbus(data: bytes) -> int:
    """CRC-16 MODBUS (澶氶」寮?0xA001)"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def crc32(data: bytes) -> int:
    """CRC-32"""
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF


# 瀛楄妭搴忓父閲?
LE = 'LE'
BE = 'BE'


def parse_value(data: bytes, offset: int, length: int, endian: str = BE,
                signed: bool = False, scale: float = 1.0) -> float:
    """浠庡瓧鑺傛祦瑙ｆ瀽鍊?
    length: 1/2/4
    endian: 'LE' or 'BE'
    signed: 鏄惁涓烘湁绗﹀彿鏁?
    scale: 缂╂斁鍥犲瓙
    """
    if offset + length > len(data):
        raise ValueError("鏁版嵁闀垮害涓嶈冻")
    chunk = data[offset:offset + length]
    if endian == LE:
        chunk = chunk[::-1]
    val = int.from_bytes(chunk, byteorder='big', signed=signed)
    return val * scale


ALGORITHMS = {
    'Sum8': lambda d: sum8(d),
    'Sum16': lambda d: sum16(d),
    'XOR8': lambda d: xor8(d),
    'CRC8': lambda d: crc8(d),
    'CRC16-CCITT': lambda d: crc16_ccitt(d),
    'CRC16-MODBUS': lambda d: crc16_modbus(d),
    'CRC32': lambda d: crc32(d),
}
