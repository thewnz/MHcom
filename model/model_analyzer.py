# -*- coding: utf-8 -*-
"""
3D模型分析器
- 边界框、中心点、尺寸计算
- 舵机安全范围自动推荐
"""

import math


class ModelAnalyzer:
    """3D模型分析器"""

    @staticmethod
    def analyze(model: dict) -> dict:
        """分析3D模型
        返回: {
            'bounding_box': {'min': [x,y,z], 'max': [x,y,z]},
            'center': [x, y, z],
            'dimensions': [w, h, d],
            'max_dim': float,
            'min_dim': float,
            'volume': float,
            'vertex_count': int,
            'face_count': int
        }
        """
        vertices = model.get('vertices', [])
        if not vertices:
            return None

        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2

        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z

        return {
            'bounding_box': {
                'min': [min_x, min_y, min_z],
                'max': [max_x, max_y, max_z]
            },
            'center': [center_x, center_y, center_z],
            'dimensions': [size_x, size_y, size_z],
            'max_dim': max(size_x, size_y, size_z),
            'min_dim': min(size_x, size_y, size_z),
            'volume': size_x * size_y * size_z,
            'vertex_count': len(vertices),
            'face_count': len(model.get('faces', []))
        }

    @staticmethod
    def calculate_servo_limits(analysis: dict, gimbal_height: float = 0.3) -> dict:
        """根据模型分析结果计算推荐舵机范围
        Args:
            analysis: analyze()的返回值
            gimbal_height: 云台基座高度
        """
        max_dim = analysis['max_dim']
        center = analysis['center']

        # 默认安全范围
        tilt_min, tilt_max = -30, 180
        pan_min, pan_max = -135, 135

        # 根据模型尺寸动态调整
        if max_dim > 0.5:
            tilt_max = 150
            pan_min, pan_max = -120, 120
        if max_dim > 0.8:
            tilt_max = 120
            pan_min, pan_max = -90, 90

        max_reach = math.sqrt((max_dim / 2) ** 2 + (gimbal_height + center[1]) ** 2)

        return {
            'pan_min': pan_min,
            'pan_max': pan_max,
            'tilt_min': tilt_min,
            'tilt_max': tilt_max,
            'recommended_height': gimbal_height + center[1],
            'max_reach': max_reach
        }
