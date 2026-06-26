# -*- coding: utf-8 -*-
"""
Modbus RTU 协议模块
- 主站请求构造
- 从站响应解析
- 常用功能码实现
"""
import struct
from .crc_calculator import crc16_modbus


# 功能码
FUNC_READ_COILS = 0x01
FUNC_READ_DISCRETE = 0x02
FUNC_READ_HOLDING = 0x03
FUNC_READ_INPUT = 0x04
FUNC_WRITE_SINGLE_COIL = 0x05
FUNC_WRITE_SINGLE_REG = 0x06
FUNC_WRITE_MULTI_COILS = 0x0F
FUNC_WRITE_MULTI_REGS = 0x10


def build_read_holding_registers(slave_id: int, address: int, count: int) -> bytes:
    """构造读保持寄存器 (0x03) 请求"""
    frame = struct.pack('>BBHH', slave_id, FUNC_READ_HOLDING, address, count)
    crc = crc16_modbus(frame)
    return frame + struct.pack('<H', crc)


def build_read_input_registers(slave_id: int, address: int, count: int) -> bytes:
    """构造读输入寄存器 (0x04) 请求"""
    frame = struct.pack('>BBHH', slave_id, FUNC_READ_INPUT, address, count)
    crc = crc16_modbus(frame)
    return frame + struct.pack('<H', crc)


def build_read_coils(slave_id: int, address: int, count: int) -> bytes:
    """构造读线圈 (0x01) 请求"""
    frame = struct.pack('>BBHH', slave_id, FUNC_READ_COILS, address, count)
    crc = crc16_modbus(frame)
    return frame + struct.pack('<H', crc)


def build_write_single_register(slave_id: int, address: int, value: int) -> bytes:
    """构造写单个寄存器 (0x06) 请求"""
    frame = struct.pack('>BBHH', slave_id, FUNC_WRITE_SINGLE_REG, address, value)
    crc = crc16_modbus(frame)
    return frame + struct.pack('<H', crc)


def build_write_multiple_registers(slave_id: int, address: int, values: list) -> bytes:
    """构造写多个寄存器 (0x10) 请求"""
    byte_count = len(values) * 2
    frame = struct.pack('>BBHHB', slave_id, FUNC_WRITE_MULTI_REGS, address, len(values), byte_count)
    for v in values:
        frame += struct.pack('>H', v)
    crc = crc16_modbus(frame)
    return frame + struct.pack('<H', crc)


def verify_crc(data: bytes) -> bool:
    """验证 Modbus RTU 帧的 CRC"""
    if len(data) < 4:
        return False
    body = data[:-2]
    crc_recv = struct.unpack('<H', data[-2:])[0]
    crc_calc = crc16_modbus(body)
    return crc_recv == crc_calc


def parse_read_registers_response(data: bytes) -> list:
    """解析读保持/输入寄存器的响应 (0x03/0x04)
    返回: 寄存器值列表
    """
    if len(data) < 3:
        raise ValueError("响应长度不足")
    if not verify_crc(data):
        raise ValueError("CRC校验失败")
    func = data[1]
    if func not in (FUNC_READ_HOLDING, FUNC_READ_INPUT):
        raise ValueError(f"非预期的功能码 0x{func:02X}")
    byte_count = data[2]
    registers = []
    for i in range(0, byte_count, 2):
        if 3 + i + 2 > len(data) - 2:
            break
        val = struct.unpack('>H', data[3 + i:5 + i])[0]
        registers.append(val)
    return registers


def parse_write_single_response(data: bytes) -> tuple:
    """解析写单寄存器响应 -> (address, value)"""
    if len(data) != 8:
        raise ValueError("响应长度错误")
    if not verify_crc(data):
        raise ValueError("CRC校验失败")
    if data[1] != FUNC_WRITE_SINGLE_REG:
        raise ValueError(f"非预期的功能码 0x{data[1]:02X}")
    address = struct.unpack('>H', data[2:4])[0]
    value = struct.unpack('>H', data[4:6])[0]
    return address, value


def parse_exception(data: bytes) -> int:
    """解析异常响应 (功能码最高位置1) -> 异常码"""
    if len(data) < 5:
        raise ValueError("异常响应长度不足")
    if not verify_crc(data):
        raise ValueError("CRC校验失败")
    func = data[1]
    if func & 0x80:
        return data[2]
    return 0
