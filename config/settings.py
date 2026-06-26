# -*- coding: utf-8 -*-
"""
用户配置管理 - JSON持久化
"""

import json
import os
from typing import Any, Dict, List


class AppConfig:
    """应用配置 - 持久化到JSON文件"""

    DEFAULT = {
        "theme": "light",                  # light / dark
        "mode": "gimbal",                  # gimbal / terminal
        "serial": {
            "port": "COM3",
            "baud": 115200,
            "bytesize": 8,
            "stopbits": 1,
            "parity": "N",
            "encoding": "utf-8",
            "auto_send": False,
            "auto_send_interval": 1000,
            "show_timestamp": True,
            "hex_display": False,
            "auto_scroll": True,
        },
        "macros": [                        # 快捷命令
            {"name": "查询版本", "data": "AT+VER?\r\n", "encoding": "text"},
            {"name": "获取状态", "data": "AT+STAT?\r\n", "encoding": "text"},
            {"name": "重启设备", "data": "AT+RST\r\n", "encoding": "text"},
        ],
        "waveform": {
            "channels": [
                {"name": "CH1", "color": "#3B82F6", "offset": 0, "scale": 1.0, "visible": True},
                {"name": "CH2", "color": "#10B981", "offset": 0, "scale": 1.0, "visible": True},
                {"name": "CH3", "color": "#F59E0B", "offset": 0, "scale": 1.0, "visible": False},
                {"name": "CH4", "color": "#EF4444", "offset": 0, "scale": 1.0, "visible": False},
            ],
            "buffer_size": 1000,
            "update_interval": 50,
        },
        "modbus": {
            "slave_id": 1,
            "timeout": 1000,
            "poll_interval": 500,
            "start_address": 0,
            "register_count": 10,
        },
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base, 'config', 'user_config.json')
        self.path = config_path
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if not isinstance(loaded, dict):
                    raise ValueError('配置文件根类型不是对象')
                return self._merge_defaults(loaded)
            except json.JSONDecodeError as e:
                import sys
                print(f'[Config] 配置文件 JSON 格式错误 ({self.path}): {e}，使用默认配置', file=sys.stderr)
                return json.loads(json.dumps(self.DEFAULT))
            except Exception as e:
                import sys
                print(f'[Config] 加载配置文件失败 ({self.path}): {e}，使用默认配置', file=sys.stderr)
                return json.loads(json.dumps(self.DEFAULT))
        return json.loads(json.dumps(self.DEFAULT))

    def _merge_defaults(self, data: dict) -> dict:
        """合并默认值，保留用户设置"""
        import copy
        merged = copy.deepcopy(self.DEFAULT)
        for k, v in data.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k].update(v)
            else:
                merged[k] = v
        return merged

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None) -> Any:
        keys = key.split('.')
        v = self.data
        for k in keys:
            if isinstance(v, dict) and k in v:
                v = v[k]
            else:
                return default
        return v

    def set(self, key: str, value: Any):
        keys = key.split('.')
        d = self.data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    def get_macros(self) -> List[dict]:
        macros = self.data.get('macros', [])
        result = []
        for m in macros:
            item = dict(m)
            # 统一字段名：旧版 'content' → 新版 'data'（向后兼容）
            if 'data' not in item and 'content' in item:
                item['data'] = item['content']
            if 'content' not in item and 'data' in item:
                item['content'] = item['data']
            if 'group' not in item:
                item['group'] = '默认'
            result.append(item)
        return result

    def set_macros(self, macros: List[dict]):
        normalized = []
        for m in macros:
            item = dict(m)
            # 统一以 'data' 为主字段存储，'content' 仅作读取时别名
            if 'content' in item and 'data' not in item:
                item['data'] = item['content']
            if 'data' in item and 'content' not in item:
                item['content'] = item['data']
            normalized.append(item)
        self.data['macros'] = normalized

    def add_macro(self, name: str, data: str, encoding: str = 'text'):
        self.data['macros'].append({"name": name, "data": data, "encoding": encoding})

    def remove_macro(self, index: int):
        if 0 <= index < len(self.data['macros']):
            del self.data['macros'][index]
