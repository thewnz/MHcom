# -*- coding: utf-8 -*-
"""
3D 调试舵机云台串口助手 — v6 Photorealistic
gimbal_3d_v3.py

基于真实 MG996R 舵机尺寸 (40.7×19.7×39.5mm) 和标准云台支架结构
参考: TowerPro MG996R 官方规格 / 标准2自由度云台支架

层级结构:
  固定层:
    底座圆盘 (铝制阳极氧化)
      4 橡胶脚垫
      中心 Pan 轴承座 + 滚珠轴承
        4 轴承座固定螺丝
  Pan 旋转层:
    Pan 舵机 (MG996R, 立式安装)
    法兰盘 (连接舵机输出轴与U型支架)
    U 型支架 (铝合金折弯)
    Tilt 舵机 (MG996R, 横置右侧)
    Tilt 旋转层:
      L 型安装板 (黑色阳极氧化铝)
      摄像头模块 (外壳 + 镜头 + LED)
"""
import sys
import os
import math

from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QSurfaceFormat, QFont, QColor, QDoubleValidator
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QOpenGLWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSplitter, QGroupBox, QLabel, QComboBox, QPushButton,
    QSlider, QSpinBox, QCheckBox, QPlainTextEdit, QScrollArea, QWidget,
    QSizePolicy, QGraphicsOpacityEffect, QStyleFactory, QFileDialog, QLineEdit,
    QMessageBox
)
from OpenGL.GL import *
from OpenGL.GLU import *


def hex2rgb(h, a=1.0):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [a]


class ModelLoader:
    @staticmethod
    def load_obj(filepath):
        vertices = []
        faces = []
        texcoords = []
        normals = []
        
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split()
                    if not parts:
                        continue
                    
                    cmd = parts[0]
                    if cmd == 'v':
                        vertices.append([float(p) for p in parts[1:4]])
                    elif cmd == 'vt':
                        texcoords.append([float(p) for p in parts[1:3]])
                    elif cmd == 'vn':
                        normals.append([float(p) for p in parts[1:4]])
                    elif cmd == 'f':
                        face = []
                        for part in parts[1:]:
                            indices = part.split('/')
                            vi = int(indices[0]) - 1 if indices[0] else -1
                            ti = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                            ni = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                            face.append((vi, ti, ni))
                        faces.append(face)
        except Exception as e:
            raise ValueError(f"Failed to load OBJ file: {str(e)}")
        
        return {'vertices': vertices, 'faces': faces, 'texcoords': texcoords, 'normals': normals}

    @staticmethod
    def load_stl(filepath):
        vertices = []
        faces = []
        
        try:
            with open(filepath, 'rb') as f:
                header = f.read(80)
                if header[:5] == b'solid':
                    return ModelLoader._load_stl_ascii(f, header)
                else:
                    return ModelLoader._load_stl_binary(f)
        except Exception as e:
            raise ValueError(f"Failed to load STL file: {str(e)}")

    @staticmethod
    def _load_stl_ascii(f, header):
        vertices = []
        faces = []
        import re
        
        content = header.decode('ascii', errors='ignore') + f.read().decode('ascii', errors='ignore')
        lines = content.split('\n')
        
        current_face = []
        for line in lines:
            line = line.strip()
            if line.startswith('vertex'):
                parts = re.split(r'\s+', line)
                if len(parts) >= 4:
                    current_face.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith('endloop') and current_face:
                if len(current_face) >= 3:
                    faces.append([(len(vertices) + i, -1, -1) for i in range(len(current_face))])
                    vertices.extend(current_face)
                current_face = []
        
        return {'vertices': vertices, 'faces': faces, 'texcoords': [], 'normals': []}

    @staticmethod
    def _load_stl_binary(f):
        vertices = []
        faces = []
        
        f.seek(80)
        num_faces = int.from_bytes(f.read(4), 'little')
        
        for _ in range(num_faces):
            normal = [float.fromhex(f'{int.from_bytes(f.read(4), "little"):08x}') for _ in range(3)]
            face_verts = []
            for _ in range(3):
                vert = [float.fromhex(f'{int.from_bytes(f.read(4), "little"):08x}') for _ in range(3)]
                face_verts.append(vert)
                vertices.append(vert)
            faces.append([(len(vertices) - 3 + i, -1, -1) for i in range(3)])
            f.read(2)
        
        return {'vertices': vertices, 'faces': faces, 'texcoords': [], 'normals': []}

    @staticmethod
    def load_model(filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.obj':
            return ModelLoader.load_obj(filepath)
        elif ext in ('.stl', '.stla', '.stlb'):
            return ModelLoader.load_stl(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")


class ModelAnalyzer:
    @staticmethod
    def analyze(model):
        vertices = model['vertices']
        if not vertices:
            return None
        
        min_x = min(v[0] for v in vertices)
        max_x = max(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_y = max(v[1] for v in vertices)
        min_z = min(v[2] for v in vertices)
        max_z = max(v[2] for v in vertices)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        
        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z
        
        max_dim = max(size_x, size_y, size_z)
        min_dim = min(size_x, size_y, size_z)
        
        return {
            'bounding_box': {
                'min': [min_x, min_y, min_z],
                'max': [max_x, max_y, max_z]
            },
            'center': [center_x, center_y, center_z],
            'dimensions': [size_x, size_y, size_z],
            'max_dim': max_dim,
            'min_dim': min_dim,
            'volume': size_x * size_y * size_z,
            'vertex_count': len(vertices),
            'face_count': len(model['faces'])
        }

    @staticmethod
    def calculate_servo_limits(analysis, gimbal_height=0.3):
        max_dim = analysis['max_dim']
        center = analysis['center']
        
        max_reach = math.sqrt((max_dim / 2) ** 2 + (gimbal_height + center[1]) ** 2)
        
        tilt_min = -30
        tilt_max = 180
        pan_min = -135
        pan_max = 135
        
        if max_dim > 0.5:
            tilt_max = 150
            pan_min = -120
            pan_max = 120
        
        if max_dim > 0.8:
            tilt_max = 120
            pan_min = -90
            pan_max = 90
        
        return {
            'pan_min': pan_min,
            'pan_max': pan_max,
            'tilt_min': tilt_min,
            'tilt_max': tilt_max,
            'recommended_height': gimbal_height + center[1]
        }


class GimbalGLWidget(QOpenGLWidget):
    """双轴云台 3D 渲染控件 — v7 Photorealistic
    基于 TowerPro 官方 MG996R 尺寸 (40.7×19.7×42.9mm) 和标准2mm铝板云台支架
    参考: TowerPro MG996R 官方规格书 / SCCCLTD 2DOF 标准云台支架
    单位: 1 GL单位 = 10mm (即 0.407 = 40.7mm)
    """

    # ===== MG996R 官方真实尺寸 (GL单位) =====
    # 来源: TowerPro 官方规格 - 40.7×19.7×42.9mm (宽×高×长)
    MG996R_W = 0.407    # 宽度 (X) 40.7mm
    MG996R_H = 0.429    # 长度/高度 (Y) 42.9mm (不含输出轴)
    MG996R_D = 0.197    # 厚度/深度 (Z) 19.7mm
    SHAFT_R = 0.024     # 输出轴半径 2.4mm (铝6061-T6)
    SPLINE_R = 0.026    # 花键半径 2.6mm (25齿)
    SPLINE_TEETH = 25   # 花键齿数
    EAR_W = 0.075       # 安装耳宽度 7.5mm
    EAR_H = 0.025       # 安装耳厚度 2.5mm
    EAR_D = 0.100       # 安装耳深度 10.0mm
    EAR_HOLE_R = 0.015  # 安装孔半径 M3 1.5mm
    MOUNT_HOLE_SPACING_X = 0.330  # 安装孔横向间距 33mm
    MOUNT_HOLE_SPACING_Y = 0.405  # 安装孔纵向间距 40.5mm

    # ===== 标准云台支架尺寸 (2mm 磨砂黑色阳极氧化铝) =====
    # 来源: SCCCLTD 标准2DOF短款云台支架
    BRACKET_THICK = 0.020   # 铝板厚度 2mm
    BASE_PLATE_W = 0.580     # 多功能支架宽度 58mm
    BASE_PLATE_D = 0.370     # 多功能支架深度 37mm
    U_BRACKET_H = 0.420     # U型支架高度 42mm
    U_BRACKET_INNER_W = 0.460  # U型支架内宽 46mm

    # ===== 材质配色 (PBR风格 Photorealistic Palette) =====
    # 金属 - 阳极氧化铝
    C_ALU_BLACK    = '#1E2026'      # 黑色阳极氧化 主色
    C_ALU_BLACK_M  = '#2A2D34'      # 黑色阳极氧化 中灰
    C_ALU_BLACK_L  = '#383C44'      # 黑色阳极氧化 亮面
    C_ALU_SILVER   = '#9AA0AA'      # 银色氧化铝
    C_ALU_SILVER_E = '#C8CDD6'      # 银色氧化 边缘高光
    C_ALU_6061     = '#B8BEC8'      # 6061铝本色
    # 金属 - 钢材
    C_STEEL        = '#7A808A'        # 碳钢
    C_STEEL_BRIGHT = '#A0A6B0'      # 抛光钢
    C_CHROME       = '#E8ECF2'        # 镀铬
    C_BRASS        = '#B8862E'        # 黄铜
    C_TI           = '#8A8F99'        # 钛合金
    # 塑料 - PBT工程塑料
    C_PBT_BLACK    = '#14161A'      # PBT黑色 主色
    C_PBT_DARK     = '#1C1F25'      # PBT深灰
    C_PBT_MID      = '#262A32'      # PBT中灰
    C_PBT_TEXT     = '#5A6270'      # PBT文字色
    # 橡胶
    C_RUBBER       = '#1E2026'      # 丁腈橡胶
    C_RUBBER_SOFT  = '#2A2D34'      # 软橡胶
    # 光学
    C_LENS_GLASS   = '#0E1218'      # 光学玻璃
    C_LENS_COAT_B  = '#2A5FA8'      # 蓝色镀膜
    C_LENS_COAT_M  = '#5A8FD8'      # 蓝紫色镀膜
    C_LENS_COAT_G  = '#8AB8F0'      # 淡蓝镀膜
    C_LED_IR       = '#FF6B1A'      # 红外LED
    C_LED_GLOW     = '#FFA35A'      # LED光晕
    # 线缆 - 标准JR配色
    C_WIRE_SIG     = '#E6A80E'      # 信号 - 橙黄色
    C_WIRE_VCC     = '#B81818'      # 电源 - 红色
    C_WIRE_GND     = '#3A2818'      # 地线 - 棕色
    # 环境
    C_GROUND       = '#0D0F13'
    C_GRID_LINE    = '#1A1D22'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 150)
        self.setCursor(Qt.OpenHandCursor)

        self.pan = 0.0
        self.tilt = 0.0
        self.target_pan = 0.0
        self.target_tilt = 0.0

        self.view_rx = -18.0
        self.view_ry = 38.0
        self.view_zm = 2.8
        self.view_tx = 0.0
        self.view_ty = -0.04

        self._last = None
        self.demo = False
        self._t = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        self.q = None
        
        self.external_model = None
        self.model_offset = [0, 0, 0]
        self.model_scale = 1.0
        self.model_visible = False

    def initializeGL(self):
        if self.q is not None:
            gluDeleteQuadric(self.q)
        self.q = gluNewQuadric()
        gluQuadricNormals(self.q, GLU_SMOOTH)
        
        glClearColor(0.047, 0.055, 0.071, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glShadeModel(GL_SMOOTH)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.10, 0.10, 0.12, 1.0])

        # 主光源 (摄影棚风格 - 暖白, 右上方45度)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [6, 9, 5, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.10, 0.10, 0.12, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.92, 0.88, 0.82, 1])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.85, 0.85, 0.90, 1])
        
        # 补光 (冷白, 左下方 - 模拟环境反射)
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, [-5, 3, -4, 1])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.04, 0.04, 0.06, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.30, 0.33, 0.40, 1])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.15, 0.15, 0.20, 1])
        
        # 顶光 (柔和漫射 - 模拟天花板反光)
        glEnable(GL_LIGHT2)
        glLightfv(GL_LIGHT2, GL_POSITION, [0, 15, 2, 1])
        glLightfv(GL_LIGHT2, GL_AMBIENT, [0.02, 0.02, 0.03, 1])
        glLightfv(GL_LIGHT2, GL_DIFFUSE, [0.22, 0.22, 0.25, 1])
        glLightfv(GL_LIGHT2, GL_SPECULAR, [0, 0, 0, 1])
        
        # 轮廓光 (背光 - 增强金属边缘)
        glEnable(GL_LIGHT3)
        glLightfv(GL_LIGHT3, GL_POSITION, [0, 5, -8, 1])
        glLightfv(GL_LIGHT3, GL_AMBIENT, [0, 0, 0, 1])
        glLightfv(GL_LIGHT3, GL_DIFFUSE, [0.25, 0.28, 0.35, 1])
        glLightfv(GL_LIGHT3, GL_SPECULAR, [0.35, 0.38, 0.45, 1])

    def resizeGL(self, w, h):
        if h == 0: h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(38.0, w / float(h), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        if self.q is None: return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0, 0.50, self.view_zm, 0, 0.45, 0, 0, 1, 0)
        glRotatef(self.view_rx, 1, 0, 0)
        glRotatef(self.view_ry, 0, 1, 0)
        glTranslatef(self.view_tx, self.view_ty, 0)
        
        self._draw_ground()
        self._draw_gimbal()

    # ==================== 材质系统 (PBR风格) ====================
    def _mat(self, color, shin=42, spec=0.45, a=1.0, emit=False, amb=0.30):
        c = hex2rgb(color, a)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [c[0]*amb, c[1]*amb, c[2]*amb, a])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, c)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [spec]*3 + [a])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shin)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, c if emit else [0]*4)

    # 阳极氧化铝 - 磨砂黑色
    def _alu_black(self):   self._mat(self.C_ALU_BLACK, 38, 0.35, amb=0.28)
    def _alu_black_m(self): self._mat(self.C_ALU_BLACK_M, 45, 0.42, amb=0.26)
    def _alu_black_l(self): self._mat(self.C_ALU_BLACK_L, 55, 0.50, amb=0.22)
    # 阳极氧化铝 - 银色
    def _alu_silver(self):  self._mat(self.C_ALU_SILVER, 68, 0.65, amb=0.24)
    def _alu_edge(self):    self._mat(self.C_ALU_SILVER_E, 96, 0.92, amb=0.12)
    def _alu_6061(self):    self._mat(self.C_ALU_6061, 60, 0.58, amb=0.25)
    # 钢材
    def _steel(self):       self._mat(self.C_STEEL, 58, 0.55, amb=0.26)
    def _steel_bright(self):self._mat(self.C_STEEL_BRIGHT, 80, 0.78, amb=0.18)
    def _chrome(self):      self._mat(self.C_CHROME, 110, 1.0, amb=0.10)
    def _brass(self):       self._mat(self.C_BRASS, 52, 0.50, amb=0.28)
    def _titanium(self):    self._mat(self.C_TI, 65, 0.60, amb=0.24)
    # PBT工程塑料
    def _plastic(self):     self._mat(self.C_PBT_BLACK, 14, 0.12, amb=0.38)
    def _plastic_d(self):   self._mat(self.C_PBT_DARK, 18, 0.16, amb=0.36)
    def _plastic_m(self):   self._mat(self.C_PBT_MID, 22, 0.20, amb=0.34)
    # 橡胶
    def _rubber(self):      self._mat(self.C_RUBBER, 6, 0.06, amb=0.42)
    def _rubber_soft(self): self._mat(self.C_RUBBER_SOFT, 10, 0.10, amb=0.40)

    # ==================== 几何图元 ====================
    def _box(self, w, h, d):
        hw, hh, hd = w/2.0, h/2.0, d/2.0
        faces = [
            ((0,0,1), [(-hw,-hh,hd),(hw,-hh,hd),(hw,hh,hd),(-hw,hh,hd)]),
            ((0,0,-1), [(hw,-hh,-hd),(-hw,-hh,-hd),(-hw,hh,-hd),(hw,hh,-hd)]),
            ((0,1,0), [(-hw,hh,hd),(hw,hh,hd),(hw,hh,-hd),(-hw,hh,-hd)]),
            ((0,-1,0), [(-hw,-hh,-hd),(hw,-hh,-hd),(hw,-hh,hd),(-hw,-hh,hd)]),
            ((1,0,0), [(hw,-hh,hd),(hw,-hh,-hd),(hw,hh,-hd),(hw,hh,hd)]),
            ((-1,0,0),[(-hw,-hh,-hd),(-hw,-hh,hd),(-hw,hh,hd),(-hw,hh,-hd)]),
        ]
        for normal, vts in faces:
            glBegin(GL_QUADS)
            glNormal3f(normal[0], normal[1], normal[2])
            for p in vts:
                glVertex3f(p[0], p[1], p[2])
            glEnd()

    def _cyl(self, r, h, s=40):
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(self.q, r, r, h, s, 1)
        glPopMatrix()

    def _dring(self, ri, ro, s=40):
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluDisk(self.q, ri, ro, s, 1)
        glPopMatrix()

    def _sdisk(self, r, h, s=44):
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(self.q, r, r, h, s, 1)
        gluDisk(self.q, 0, r, s, 1)
        glTranslatef(0, 0, h)
        gluDisk(self.q, 0, r, s, 1)
        glPopMatrix()

    def _sphere(self, r, s=24, t=18):
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluSphere(self.q, r, s, t)
        glPopMatrix()

    def _screw_cap(self, r=0.018, h=0.022):
        """内六角圆柱头螺丝"""
        glPushMatrix()
        self._steel()
        self._cyl(r, h * 0.7)
        glTranslatef(0, h * 0.7, 0)
        self._mat(self.C_STEEL_BRIGHT, 82, 0.82)
        self._dring(0, r)
        # 内六角
        self._mat(self.C_RUBBER, 5, 0.05)
        glPushMatrix()
        glTranslatef(0, 0.001, 0)
        glRotatef(30, 0, 1, 0)
        glBegin(GL_POLYGON)
        for i in range(6):
            a = math.radians(i * 60)
            glVertex3f(math.cos(a) * r * 0.55, 0, math.sin(a) * r * 0.55)
        glEnd()
        glPopMatrix()
        glPopMatrix()

    def _hex_nut(self, r=0.028, h=0.016):
        """六角螺母"""
        glPushMatrix()
        self._steel()
        glRotatef(30, 0, 1, 0)
        # 侧面
        for i in range(6):
            a1 = math.radians(i * 60)
            a2 = math.radians((i+1) * 60)
            x1, z1 = math.cos(a1) * r, math.sin(a1) * r
            x2, z2 = math.cos(a2) * r, math.sin(a2) * r
            nx = math.cos(a1 + math.pi/6)
            nz = math.sin(a1 + math.pi/6)
            glBegin(GL_QUADS)
            glNormal3f(nx, 0, nz)
            glVertex3f(x1, -h/2, z1)
            glVertex3f(x2, -h/2, z2)
            glVertex3f(x2, h/2, z2)
            glVertex3f(x1, h/2, z1)
            glEnd()
        # 顶面/底面
        for ys in (1, -1):
            glBegin(GL_POLYGON)
            glNormal3f(0, ys, 0)
            for i in range(6):
                a = math.radians(i * 60)
                glVertex3f(math.cos(a) * r, ys * h/2, math.sin(a) * r)
            glEnd()
        glPopMatrix()

    def _hex_screw(self, r=0.022, h=0.020):
        """外六角螺丝头"""
        glPushMatrix()
        self._steel_bright()
        # 六角头
        glRotatef(30, 0, 1, 0)
        for i in range(6):
            a1 = math.radians(i * 60)
            a2 = math.radians((i+1) * 60)
            x1, z1 = math.cos(a1) * r, math.sin(a1) * r
            x2, z2 = math.cos(a2) * r, math.sin(a2) * r
            nx = math.cos(a1 + math.pi/6)
            nz = math.sin(a1 + math.pi/6)
            glBegin(GL_QUADS)
            glNormal3f(nx, 0, nz)
            glVertex3f(x1, 0, z1)
            glVertex3f(x2, 0, z2)
            glVertex3f(x2, h * 0.7, z2)
            glVertex3f(x1, h * 0.7, z1)
            glEnd()
        # 顶面
        glBegin(GL_POLYGON)
        glNormal3f(0, 1, 0)
        for i in range(6):
            a = math.radians(i * 60)
            glVertex3f(math.cos(a) * r, h * 0.7, math.sin(a) * r)
        glEnd()
        # 十字槽
        glTranslatef(0, h * 0.72, 0)
        self._mat(self.C_RUBBER, 4, 0.04)
        glPushMatrix()
        self._box(r * 1.2, 0.004, r * 0.3)
        glPopMatrix()
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        self._box(r * 1.2, 0.004, r * 0.3)
        glPopMatrix()
        glPopMatrix()

    def _ball_bearing(self, r_outer=0.055, r_inner=0.030, h=0.020):
        """滚珠轴承"""
        glPushMatrix()
        # 外圈
        self._chrome()
        self._cyl(r_outer, h)
        glTranslatef(0, h, 0)
        self._dring(r_outer * 0.76, r_outer)
        glTranslatef(0, -h, 0)
        # 内圈
        self._steel()
        self._cyl(r_inner, h * 0.92)
        glTranslatef(0, h * 0.04, 0)
        self._dring(0, r_inner)
        # 滚珠
        ball_r = (r_outer * 0.76 - r_inner) / 2
        r_mid = (r_outer * 0.76 + r_inner) / 2
        self._chrome()
        for i in range(8):
            a = math.radians(i * 45)
            glPushMatrix()
            glTranslatef(math.cos(a) * r_mid, h/2, math.sin(a) * r_mid)
            self._sphere(ball_r * 0.85, 10, 8)
            glPopMatrix()
        glPopMatrix()

    # ==================== 地面 ====================
    def _draw_ground(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.07, 0.08, 0.10)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-3, -0.001, -3)
        glVertex3f(3, -0.001, -3)
        glVertex3f(3, -0.001, 3)
        glVertex3f(-3, -0.001, 3)
        glEnd()
        
        # 网格
        glColor3f(0.12, 0.14, 0.17)
        glLineWidth(1.0)
        size = 2.0
        step = 0.2
        n = int(size / step)
        glBegin(GL_LINES)
        for i in range(-n, n + 1):
            p = i * step
            glVertex3f(p, 0, -size); glVertex3f(p, 0, size)
            glVertex3f(-size, 0, p); glVertex3f(size, 0, p)
        glEnd()
        
        # 中心十字
        glColor3f(0.20, 0.25, 0.32)
        glBegin(GL_LINES)
        glVertex3f(0, 0.001, -size); glVertex3f(0, 0.001, size)
        glVertex3f(-size, 0.001, 0); glVertex3f(size, 0.001, 0)
        glEnd()
        
        glEnable(GL_LIGHTING)

    # ==================== MG996R 舵机 (官方精确尺寸) ====================
    def _mg996r(self, label=True, wires=True):
        """MG996R 舵机 - 输出轴沿 +Y 方向
        基于 TowerPro 官方规格: 40.7×19.7×42.9mm (宽×厚×长)
        25齿花键输出轴, 铝6061-T6材质升级
        """
        w = self.MG996R_W   # 40.7mm 宽度
        h = self.MG996R_H   # 42.9mm 长度(高度)
        d = self.MG996R_D   # 19.7mm 厚度
        
        # ===== 主体外壳 (PBT工程塑料) =====
        self._plastic()
        self._box(w, h, d)
        
        # ===== 上下端盖 (深色PBT) =====
        glPushMatrix()
        glTranslatef(0, h/2 + 0.003, 0)
        self._plastic_d()
        self._box(w * 0.92, 0.010, d * 0.92)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, -h/2 - 0.003, 0)
        self._plastic_d()
        self._box(w * 0.92, 0.010, d * 0.92)
        glPopMatrix()
        
        # ===== 侧面加强筋和纹理 =====
        for sz in (-d/2 - 0.001, d/2 + 0.001):
            glPushMatrix()
            glTranslatef(0, 0, sz)
            self._plastic_m()
            for i in range(5):
                y_off = -h * 0.38 + i * h * 0.19
                self._box(w * 0.82, 0.008, 0.002)
                glTranslatef(0, y_off, 0)
            glPopMatrix()
        
        # ===== 输出轴组件 =====
        glPushMatrix()
        glTranslatef(0, h/2 + 0.032, 0)
        
        # 轴座塑料凸台
        self._plastic_d()
        self._cyl(0.078, 0.024)
        
        # 轴承钢环 (防尘盖)
        glTranslatef(0, 0.024, 0)
        self._chrome()
        self._dring(0.050, 0.076)
        
        # 输出轴主体 (铝6061-T6)
        self._alu_6061()
        self._cyl(self.SHAFT_R, 0.042)
        
        # 25齿花键
        glTranslatef(0, 0.018, 0)
        self._alu_6061()
        n_teeth = self.SPLINE_TEETH
        for k in range(n_teeth):
            a = math.radians(k * 360.0 / n_teeth)
            glPushMatrix()
            glTranslatef(math.cos(a) * self.SPLINE_R, 0, math.sin(a) * self.SPLINE_R)
            glRotatef(k * 360.0 / n_teeth, 0, 1, 0)
            tooth_w = 2 * math.pi * self.SPLINE_R / n_teeth * 0.45
            self._box(tooth_w, 0.024, 0.005)
            glPopMatrix()
        
        # 轴端面 + 中心M2.5螺丝孔
        glTranslatef(0, 0.030, 0)
        self._alu_6061()
        self._dring(0, self.SHAFT_R * 0.92)
        self._mat(self.C_RUBBER, 4, 0.04)
        self._dring(0, 0.012)
        
        glPopMatrix()
        
        # ===== 标签区域 (正面 +Z) =====
        if label:
            glPushMatrix()
            glTranslatef(0, 0, d/2 + 0.002)
            self._mat(self.C_PBT_TEXT, 7, 0.06)
            self._box(w * 0.60, h * 0.40, 0.003)
            # 模拟产品标签文字
            glTranslatef(0, 0, 0.002)
            self._plastic()
            for i in range(5):
                glPushMatrix()
                glTranslatef(0, h * 0.15 - i * h * 0.085, 0)
                lw = w * (0.50 - i * 0.06)
                self._box(lw, 0.005, 0.001)
                glPopMatrix()
            glPopMatrix()
        
        # ===== 线缆 (底部侧面引出) =====
        if wires:
            glPushMatrix()
            glTranslatef(0, -h * 0.32, -d/2 - 0.005)
            # 出线座
            self._plastic_d()
            self._cyl(0.030, 0.020)
            # 橡胶护套
            glTranslatef(0, -0.010, -0.025)
            self._rubber_soft()
            glRotatef(20, 1, 0, 0)
            self._cyl(0.018, 0.30)
            # 三根分线 (标准JR配色: 橙-红-棕)
            glPushMatrix()
            glTranslatef(0, -0.015, -0.025)
            glDisable(GL_LIGHTING)
            wire_colors = [
                (self.C_WIRE_SIG, -0.007, -0.28, -0.28),
                (self.C_WIRE_VCC,  0.000, -0.28, -0.27),
                (self.C_WIRE_GND,  0.007, -0.28, -0.28),
            ]
            for color, ex, ey, ez in wire_colors:
                glColor4f(*hex2rgb(color))
                glLineWidth(2.0)
                glBegin(GL_LINES)
                glVertex3f(0, 0, 0)
                glVertex3f(ex, ey, ez)
                glEnd()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)
            glPopMatrix()
            glPopMatrix()
        
        # ===== 安装耳 (双侧) =====
        ear_offset = w/2 + self.EAR_W/2 - 0.005
        for sx in (-ear_offset, ear_offset):
            glPushMatrix()
            glTranslatef(sx, -h/2 + self.EAR_H/2 + 0.005, 0)
            self._plastic_d()
            self._box(self.EAR_W, self.EAR_H, self.EAR_D)
            # 安装孔 (M3)
            glTranslatef(0, self.EAR_H/2, 0)
            self._mat(self.C_RUBBER, 4, 0.04)
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            gluDisk(self.q, 0, self.EAR_HOLE_R, 18, 1)
            glPopMatrix()
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            gluCylinder(self.q, self.EAR_HOLE_R, self.EAR_HOLE_R, self.EAR_H, 18, 1)
            glPopMatrix()
            glPopMatrix()
        
        # ===== 固定螺丝孔位标记 (4个安装孔) =====
        for sy in (-h * 0.38, h * 0.38):
            for sx in (-w * 0.36, w * 0.36):
                glPushMatrix()
                glTranslatef(sx, sy, d/2 + 0.001)
                self._plastic_d()
                self._cyl(0.008, 0.002)
                glPopMatrix()

    # ==================== 主绘制 ====================
    def _draw_gimbal(self):
        self._draw_base()
        glPushMatrix()
        glRotatef(self.pan, 0, 1, 0)
        self._draw_pan_assembly()
        self._draw_external_model()
        glPopMatrix()

    # ==================== 底座 (固定层 - 三层同心圆结构) ====================
    def _draw_base(self):
        # 真实云台三层结构：底层底座 + 中层固定环 + 上层轴承座
        
        # ===== 第一层: 底层大圆盘底座 =====
        glPushMatrix()
        self._alu_silver()
        self._sdisk(0.68, 0.035)
        
        # 边缘高光倒角
        glTranslatef(0, 0.035, 0)
        self._alu_edge()
        self._dring(0.62, 0.68)
        glPopMatrix()
        
        # ===== 4 个底座安装螺丝 (外六角) =====
        for i in range(4):
            a = math.radians(i * 90)
            glPushMatrix()
            glTranslatef(math.cos(a) * 0.58, 0.038, math.sin(a) * 0.58)
            self._hex_screw(0.022, 0.020)
            glPopMatrix()
        
        # ===== 第二层: 中间固定环 =====
        glPushMatrix()
        glTranslatef(0, 0.035, 0)
        self._alu_silver()
        self._sdisk(0.52, 0.045)
        
        # 中心凹陷
        glTranslatef(0, 0.045, 0)
        self._alu_black_m()
        self._sdisk(0.38, 0.010)
        glPopMatrix()
        
        # ===== 4 个贯穿螺丝 (连接三层) =====
        for i in range(4):
            a = math.radians(45 + i * 90)
            glPushMatrix()
            glTranslatef(math.cos(a) * 0.45, 0.080, math.sin(a) * 0.45)
            self._hex_screw(0.018, 0.016)
            glPopMatrix()
        
        # ===== 第三层: 轴承座 (带滚珠轴承) =====
        glPushMatrix()
        glTranslatef(0, 0.080, 0)
        
        # 轴承座底座
        self._alu_silver()
        self._sdisk(0.42, 0.050)
        
        # 轴承安装凹槽
        glTranslatef(0, 0.050, 0)
        self._alu_black()
        self._sdisk(0.34, 0.015)
        
        # 滚珠轴承
        glTranslatef(0, 0.003, 0)
        self._ball_bearing(0.120, 0.060, 0.030)
        
        glPopMatrix()
        
        # ===== 中心通孔 =====
        glPushMatrix()
        glTranslatef(0, 0, 0)
        self._mat(self.C_RUBBER, 5, 0.05)
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        gluCylinder(self.q, 0.055, 0.055, 0.200, 24, 1)
        glPopMatrix()
        glPopMatrix()

    # ==================== Pan 旋转层 ====================
    def _draw_pan_assembly(self):
        base_h = 0.080 + 0.050 + 0.030  # 底座高度
        
        # ===== 旋转环 (连接轴承与舵机) =====
        glPushMatrix()
        glTranslatef(0, base_h, 0)
        
        # 旋转环主体
        self._alu_silver()
        self._sdisk(0.46, 0.060)
        
        # 顶部边缘
        glTranslatef(0, 0.060, 0)
        self._alu_edge()
        self._dring(0.38, 0.46)
        
        # 中心平台
        self._alu_black()
        self._sdisk(0.30, 0.020)
        
        glPopMatrix()
        
        # ===== 旋转环固定螺丝 (4个) =====
        for i in range(4):
            a = math.radians(45 + i * 90)
            glPushMatrix()
            glTranslatef(math.cos(a) * 0.40, base_h + 0.062, math.sin(a) * 0.40)
            self._hex_screw(0.016, 0.014)
            glPopMatrix()
        
        # ===== Pan 舵机 (立式安装在旋转环上) =====
        sw, sh, sd = self.MG996R_W, self.MG996R_H, self.MG996R_D
        scy = base_h + 0.080 + sh / 2
        glPushMatrix()
        glTranslatef(0, scy, 0)
        self._mg996r()
        glPopMatrix()
        
        # ===== 舵机固定螺丝 (外六角, 穿过安装耳) =====
        ear_offset = sw/2 + self.EAR_W/2 - 0.005
        for sx in (-ear_offset, ear_offset):
            glPushMatrix()
            glTranslatef(sx, base_h + 0.062, 0)
            self._hex_screw(0.014, 0.016)
            glPopMatrix()
        
        # ===== 舵机线缆 (弯曲状) =====
        glPushMatrix()
        glTranslatef(0, scy - sh * 0.35, -sd/2 - 0.008)
        glDisable(GL_LIGHTING)
        # 线缆护套
        self._rubber()
        glRotatef(-15, 1, 0, 0)
        self._cyl(0.018, 0.35)
        # 三根分线
        wire_colors = [
            (self.C_WIRE_SIG, -0.007, -0.32, 0),
            (self.C_WIRE_VCC,  0.000, -0.33, 0),
            (self.C_WIRE_GND,  0.007, -0.32, 0),
        ]
        glPushMatrix()
        glTranslatef(0, -0.015, 0)
        for color, ex, ey, ez in wire_colors:
            glColor4f(*hex2rgb(color))
            glLineWidth(2.5)
            glBegin(GL_LINE_STRIP)
            glVertex3f(0, 0, 0)
            glVertex3f(ex * 0.5, ey * 0.5, ez)
            glVertex3f(ex, ey, ez)
            glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glPopMatrix()
        
        # ===== U 型支架 (黑色塑料) =====
        ub_y = scy + sh / 2 + 0.040
        self._draw_u_bracket(ub_y)
        
        # ===== Tilt 轴中心高度 =====
        tilt_y = ub_y + 0.020 + 0.26
        
        # ===== Tilt 舵机 (右侧横置) =====
        self._draw_tilt_servo(tilt_y)
        
        # ===== Tilt 旋转层 (黑色塑料安装板) =====
        glPushMatrix()
        glTranslatef(0, tilt_y, 0)
        glRotatef(self.tilt - 90, 1, 0, 0)
        glTranslatef(0, -tilt_y, 0)
        self._draw_tilt_layer(tilt_y)
        glPopMatrix()

    # ==================== U 型支架 (黑色塑料) ====================
    def _draw_u_bracket(self, by):
        tw = 0.030                # 3mm 塑料厚度
        th = 0.52                 # 侧板高度
        ts = 0.48                 # 内宽
        td = 0.44                 # 深度
        scx = ts / 2 + tw / 2
        
        # ===== 底板 =====
        glPushMatrix()
        glTranslatef(0, by + tw/2, 0)
        self._plastic()
        self._box(ts + tw*2, tw, td)
        glPopMatrix()
        
        # ===== 左右侧板 =====
        for sx in (-scx, scx):
            glPushMatrix()
            glTranslatef(sx, by + tw + th/2, 0)
            self._plastic()
            self._box(tw, th, td)
            
            # 侧板上的安装孔
            for i in range(3):
                sy = -th * 0.35 + i * th * 0.25
                glPushMatrix()
                glTranslatef(0, sy, 0)
                self._mat(self.C_RUBBER, 4, 0.04)
                glPushMatrix()
                glRotatef(90, 0, 1, 0)
                gluDisk(self.q, 0, 0.016, 16, 1)
                glPopMatrix()
                glPopMatrix()
            
            glPopMatrix()
        
        # ===== 顶部横梁 =====
        ttop = by + tw + th
        glPushMatrix()
        glTranslatef(0, ttop - tw/2, 0)
        self._plastic()
        self._box(ts + tw * 2, tw, tw * 1.5)
        glPopMatrix()
        
        # ===== 6 个固定螺丝 (外六角) =====
        for sx in (-ts * 0.35, 0, ts * 0.35):
            for sz in (-td * 0.35, td * 0.35):
                glPushMatrix()
                glTranslatef(sx, by + tw + 0.005, sz)
                self._hex_screw(0.014, 0.014)
                glPopMatrix()
        
        # ===== 右侧板 tilt 轴孔 =====
        glPushMatrix()
        glTranslatef(scx + 0.002, by + tw + th/2, 0)
        self._ball_bearing(0.055, 0.030, 0.022)
        glPopMatrix()
        
        # ===== 左侧板从动轴孔 =====
        glPushMatrix()
        glTranslatef(-scx - 0.002, by + tw + th/2, 0)
        self._brass()
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        gluCylinder(self.q, 0.022, 0.022, tw, 18, 1)
        glPopMatrix()
        self._mat(self.C_RUBBER, 4, 0.04)
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        gluDisk(self.q, 0, 0.020, 18, 1)
        glPopMatrix()
        glPopMatrix()

    # ==================== Tilt 舵机 (右侧横置) ====================
    def _draw_tilt_servo(self, cy):
        tw = self.BRACKET_THICK
        ts = self.U_BRACKET_INNER_W
        scx = ts / 2 + tw / 2
        sp = scx
        sw, sh, sd = self.MG996R_W, self.MG996R_H, self.MG996R_D
        
        # 舵机主体 (绕Z轴旋转 -90度，输出轴沿 -X 方向)
        glPushMatrix()
        glTranslatef(sp + sh/2 + 0.010, cy, 0)
        glRotatef(-90, 0, 0, 1)
        self._mg996r()
        glPopMatrix()
        
        # 输出轴 (伸入支架内，铝6061-T6)
        glPushMatrix()
        glTranslatef(sp, cy, 0)
        glRotatef(-90, 0, 1, 0)
        self._alu_6061()
        self._cyl(0.038, 0.14)
        # 25齿花键段
        glTranslatef(0, 0, -0.120)
        self._alu_6061()
        n_teeth = self.SPLINE_TEETH
        for k in range(n_teeth):
            a = math.radians(k * 360.0 / n_teeth)
            r = self.SPLINE_R
            glPushMatrix()
            glTranslatef(math.cos(a) * r, math.sin(a) * r, 0)
            glRotatef(k * 360.0 / n_teeth, 0, 0, 1)
            tooth_w = 2 * math.pi * r / n_teeth * 0.45
            self._box(tooth_w, tooth_w, 0.050)
            glPopMatrix()
        glPopMatrix()
        
        # 左侧从动轴 (铝制)
        glPushMatrix()
        glTranslatef(-sp, cy, 0)
        glRotatef(90, 0, 1, 0)
        self._alu_6061()
        self._cyl(0.024, 0.12)
        glPopMatrix()

    # ==================== Tilt 旋转层 (黑色塑料多孔安装板) ====================
    def _draw_tilt_layer(self, pivot_y):
        tw = 0.030  # 塑料厚度
        
        # ===== 垂直安装板 (黑色塑料) =====
        glPushMatrix()
        glTranslatef(tw/2, pivot_y, 0)
        self._plastic()
        self._box(tw, 0.40, 0.48)
        
        # 多孔设计
        for i in range(3):
            for j in range(4):
                sx = -0.18 + i * 0.12
                sz = -0.20 + j * 0.13
                glPushMatrix()
                glTranslatef(sx, sz, 0)
                self._mat(self.C_RUBBER, 4, 0.04)
                glPushMatrix()
                glRotatef(90, 0, 1, 0)
                gluDisk(self.q, 0, 0.018, 16, 1)
                glPopMatrix()
                glPopMatrix()
        
        glPopMatrix()
        
        # ===== 花键连接座 + 锁紧螺母 =====
        glPushMatrix()
        glTranslatef(0, pivot_y, 0)
        self._alu_black()
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        gluDisk(self.q, 0.018, 0.056, 24, 1)
        glPopMatrix()
        self._hex_nut(0.026, 0.018)
        glPopMatrix()
        
        # ===== 6 个固定螺丝 (外六角) =====
        for sx in (-tw/2 - 0.005, tw/2 + 0.005):
            for sy in (-0.16, 0, 0.16):
                glPushMatrix()
                glTranslatef(sx, pivot_y + sy, 0)
                self._hex_screw(0.014, 0.014)
                glPopMatrix()
        
        # ===== 水平安装板 (黑色塑料多孔) =====
        hp = pivot_y + 0.18
        glPushMatrix()
        glTranslatef(tw/2 - 0.08, hp, 0)
        self._plastic()
        self._box(0.32, tw, 0.48)
        
        # 多孔设计
        for i in range(3):
            for j in range(3):
                sx = -0.12 + i * 0.12
                sz = -0.20 + j * 0.20
                glPushMatrix()
                glTranslatef(sx, sz, 0)
                self._mat(self.C_RUBBER, 4, 0.04)
                glPushMatrix()
                glRotatef(90, 0, 1, 0)
                gluDisk(self.q, 0, 0.020, 16, 1)
                glPopMatrix()
                glPopMatrix()
        
        glPopMatrix()
        
        # ===== 摄像头模块 (标准模组尺寸) =====
        ccx = tw/2 - 0.08
        ccy = hp + tw + 0.080
        
        # 摄像头外壳 (方形模组)
        glPushMatrix()
        glTranslatef(ccx, ccy, 0)
        self._plastic()
        self._box(0.30, 0.26, 0.36)
        # 外壳散热槽纹理
        for i in range(4):
            glPushMatrix()
            glTranslatef(0, -0.09 + i * 0.065, 0)
            self._plastic_d()
            self._box(0.28, 0.004, 0.34)
            glPopMatrix()
        glPopMatrix()
        
        # 前面板
        glPushMatrix()
        glTranslatef(ccx, ccy, 0.182)
        self._plastic_d()
        self._box(0.28, 0.24, 0.004)
        glPopMatrix()
        
        # 镜头筒 (M12 镜头座)
        glPushMatrix()
        glTranslatef(ccx, ccy, 0.185)
        self._alu_black()
        self._cyl(0.076, 0.115)
        
        glTranslatef(0, 0, 0.113)
        # 镜头外环 (黑色)
        self._alu_black_m()
        self._dring(0.040, 0.082)
        
        # 多层镀膜效果 (渐变蓝紫色)
        glPushMatrix()
        glTranslatef(0, 0, 0.003)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        # 外圈镀膜
        glColor4f(0.18, 0.42, 0.72, 0.85)
        gluDisk(self.q, 0.005, 0.068, 32, 1)
        # 中圈
        glColor4f(0.42, 0.68, 0.92, 0.88)
        gluDisk(self.q, 0.005, 0.045, 32, 1)
        # 中心光圈暗部
        glColor4f(0.03, 0.05, 0.08, 1.0)
        gluDisk(self.q, 0, 0.018, 20, 1)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        
        glPopMatrix()  # /镜头筒
        
        # ===== LED 指示灯 (红外LED + 光晕) =====
        glPushMatrix()
        glTranslatef(ccx + 0.10, ccy + 0.07, 0.175)
        
        # 多层光晕
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        for i in range(4):
            r = 0.030 + i * 0.018
            alpha = 0.35 - i * 0.09
            glColor4f(1.0, 0.52, 0.10, alpha)
            gluDisk(self.q, 0, r, 20, 1)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        
        # LED 本体 (发光)
        self._mat(self.C_LED_IR, 96, 0.96, emit=True)
        self._sphere(0.020, 14, 10)
        
        # LED 外圈 (塑料座
        self._plastic()
        self._dring(0.020, 0.032)
        glPopMatrix()

    # ==================== 动画 ====================
    def _tick(self):
        if self.demo:
            self._t += .016
            self.target_pan  = 135 + 120 * math.sin(self._t * .8)
            self.target_tilt = 90 + 70 * math.sin(self._t * .6 + 1.)
        self.pan  += (self.target_pan  - self.pan ) * .12
        self.tilt += (self.target_tilt - self.tilt) * .12
        self.update()

    def set_angles(self, p, t):
        self.target_pan = p
        self.target_tilt = t

    def set_demo(self, on):
        self.demo = bool(on)
        self._t = 0.

    # ==================== 鼠标交互 ====================
    def mousePressEvent(self, e):
        self._last = e.pos()
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if not self._last: return
        dx = e.x() - self._last.x()
        dy = e.y() - self._last.y()
        if e.buttons() & Qt.LeftButton:
            self.view_ry += dx * .5
            self.view_rx = max(-89, min(89, self.view_rx + dy * .5))
        elif e.buttons() & Qt.RightButton:
            self.view_tx += dx * .005
            self.view_ty -= dy * .005
        self._last = e.pos()
        self.update()

    def mouseReleaseEvent(self, e):
        self._last = None
        self.setCursor(Qt.OpenHandCursor)

    def wheelEvent(self, e):
        d = e.angleDelta().y() / 120.
        self.view_zm = max(1.6, min(12., self.view_zm * (.9 ** d)))
        self.update()

    def set_external_model(self, model, offset=[0, 0, 0], scale=1.0):
        self.external_model = model
        self.model_offset = offset
        self.model_scale = scale
        self.model_visible = True
        self.update()

    def clear_external_model(self):
        self.external_model = None
        self.model_visible = False
        self.update()

    def _draw_external_model(self):
        if not self.external_model or not self.model_visible:
            return
        
        glPushMatrix()
        glTranslatef(self.model_offset[0], self.model_offset[1], self.model_offset[2])
        glScalef(self.model_scale, self.model_scale, self.model_scale)
        
        self._mat('#4A90D9', 50, 0.50, amb=0.25)
        
        vertices = self.external_model['vertices']
        faces = self.external_model['faces']
        
        for face in faces:
            glBegin(GL_POLYGON)
            for vi, ti, ni in face:
                if vi >= 0 and vi < len(vertices):
                    glVertex3f(vertices[vi][0], vertices[vi][1], vertices[vi][2])
            glEnd()
        
        glPopMatrix()


# ==================== SerialLink 串口核心 ====================
class SerialOpenWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, port, baud, dbits, sbits, parity, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self.dbits = dbits
        self.sbits = sbits
        self.parity = parity
        self.ser = None

    def run(self):
        import serial
        pmap = {'无': 'N', '奇': 'O', '偶': 'E'}
        sbm = {
            '1': serial.STOPBITS_ONE,
            '1.5': serial.STOPBITS_ONE_POINT_FIVE,
            '2': serial.STOPBITS_TWO
        }
        try:
            self.ser = serial.Serial(
                port=self.port, baudrate=self.baud,
                bytesize=int(self.dbits), stopbits=sbm.get(self.sbits, serial.STOPBITS_ONE),
                parity=pmap.get(self.parity, 'N'), timeout=0.05
            )
            self.finished.emit(True, '')
        except Exception as e:
            self.finished.emit(False, str(e))


class SerialLink:
    def __init__(self):
        self.ser = None

    def set_serial(self, ser):
        self.ser = ser

    @staticmethod
    def list_ports():
        import serial.tools.list_ports
        return [p.device for p in serial.tools.list_ports.comports()]

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    def send(self, data: bytes):
        if self.ser and self.ser.is_open:
            self.ser.write(data)

    def read_all(self):
        if not self.ser or not self.ser.is_open:
            return b''
        try:
            n = self.ser.in_waiting
            return self.ser.read(n) if n > 0 else b''
        except Exception:
            return b''

    @property
    def is_open(self):
        return self.ser is not None and self.ser.is_open


# ==================== MainWindow ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('3D Gimbal Debug Terminal')
        self.setMinimumSize(1060, 680)
        self.resize(1400, 860)
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.slink = SerialLink()
        self._auto_send_timer = QTimer(self)
        self._auto_send_timer.timeout.connect(self._auto_send_tick)
        self._auto_interval_connected = False
        self._pending_pan = 0
        self._pending_tilt = 0
        self._servo_pending = False
        self._recv_buf = b''
        self._last_send_time = 0
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(200)

        # ===== QSS =====
        code_font = 'Cascadia Code, JetBrains Mono, Consolas, monospace'
        ui_font = 'Microsoft YaHei UI, Segoe UI, sans-serif'
        self.setStyleSheet(f'''
            * {{ font-family:"{ui_font}"; font-size:16px; color:#9CA3AF; outline:none; }}
            QMainWindow {{ background:#0A0C10; }}
            QSplitter {{ background:#0A0C10; border:none; }}
            QSplitter::handle {{ background:#1A1D24; width:2px; }}
            QSplitter::handle:hover {{ background:#1E40AF; }}
            QSplitter::handle:pressed {{ background:#2563EB; }}
            QGroupBox {{
                color:#D1D5DB; font-weight:600; font-size:16px; letter-spacing:0.5px;
                background:#111318; border:1px solid #1F2329;
                border-radius:6px; margin-top:18px; padding:16px 14px 12px 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; left:14px; top:1px;
                padding:2px 8px; background:#111318; border-radius:3px;
                color:#D1D5DB; font-size:15px; font-weight:700; letter-spacing:0.8px;
            }}
            QLabel {{ color:#9CA3AF; font-size:16px; background:transparent; }}
            QLabel[cssClass="title"] {{ color:#E5E7EB; font-size:16px; font-weight:700; }}
            QLabel[cssClass="value"] {{
                color:#60A5FA; font-size:18px; font-weight:700; min-width:50px;
                font-family:'Cascadia Code','JetBrains Mono','Consolas',monospace;
                background:#161920; border:1px solid #1F2329; border-radius:4px; padding:4px 10px;
            }}
            QLabel[cssClass="tip"] {{ color:#4B5563; font-size:15px; }}
            QLabel[cssClass="led"] {{
                min-width:10px; max-width:10px; min-height:10px; max-height:10px;
                background:#DC2626; border-radius:5px;
                border:1px solid rgba(255,255,255,0.08);
            }}
            QLabel[cssClass="led-on"] {{
                background:#16A34A; border-radius:5px;
                border:1px solid rgba(255,255,255,0.08);
            }}
            QComboBox {{
                background:#161920; color:#D1D5DB; border:1px solid #1F2329; border-radius:5px;
                padding:5px 12px; min-width:90px; min-height:36px;
                font-size:15px;
            }}
            QComboBox:hover {{ border-color:#2563EB; background:#1A1D24; }}
            QComboBox:focus {{ border-color:#3B82F6; }}
            QComboBox:disabled {{ background:#0F1115; color:#374151; border-color:#1A1D24; }}
            QComboBox::drop-down {{ subcontrol-origin:padding; subcontrol-position:right center; width:24px; border:none; border-left:1px solid #1F2329; }}
            QComboBox::down-arrow {{ width:8px; height:8px; }}
            QComboBox QAbstractItemView {{
                background:#161920; color:#D1D5DB; outline:none; border:1px solid #1F2329;
                border-radius:5px; padding:4px; selection-background-color:#1E40AF; selection-color:#F9FAFB;
                font-size:15px;
            }}
            QPushButton {{
                background:#1E40AF; color:#F9FAFB; border:none; border-radius:5px;
                padding:8px 22px; min-height:38px; font-weight:600; font-size:15px;
            }}
            QPushButton:hover {{ background:#2563EB; }}
            QPushButton:pressed {{ background:#1D4ED8; }}
            QPushButton:focus {{ border:1px solid #60A5FA; }}
            QPushButton:disabled {{ background:#111318; color:#374151; }}
            QPushButton[cssClass="danger"] {{ background:#DC2626; }}
            QPushButton[cssClass="danger"]:hover {{ background:#EF4444; }}
            QPushButton[cssClass="danger"]:focus {{ border:1px solid #FCA5A5; }}
            QPushButton[cssClass="default"] {{
                background:#161920; color:#9CA3AF; border:1px solid #1F2329; font-weight:400;
            }}
            QPushButton[cssClass="default"]:hover {{
                background:#1A1D24; color:#D1D5DB; border-color:#2563EB;
            }}
            QPushButton[cssClass="default"]:pressed {{
                background:#0F1115; color:#6B7280;
            }}
            QPushButton[cssClass="zero"] {{
                background:#D97706; color:#FFFBEB; border:none; border-radius:6px;
                padding:9px 22px; min-height:46px; font-size:17px; font-weight:700;
            }}
            QPushButton[cssClass="zero"]:hover {{ background:#F59E0B; }}
            QPushButton[cssClass="zero"]:pressed {{ background:#B45309; }}
            QPushButton#btn_open {{
                background:#16A34A; min-width:140px; min-height:42px; font-size:17px; font-weight:700; border-radius:6px;
            }}
            QPushButton#btn_open:hover {{ background:#22C55E; }}
            QPushButton#btn_open:pressed {{ background:#15803D; }}
            QPushButton#btn_open:checked {{ background:#DC2626; }}
            QPushButton#btn_send {{
                background:#1E40AF; min-width:76px; min-height:38px;
            }}
            QPushButton#btn_send:hover {{ background:#2563EB; }}
            QCheckBox {{ color:#9CA3AF; spacing:8px; font-size:15px; }}
            QCheckBox::indicator {{
                width:18px; height:18px; border:1.5px solid #374151;
                border-radius:4px; background:#111318;
            }}
            QCheckBox::indicator:hover {{ border-color:#2563EB; }}
            QCheckBox::indicator:checked {{ background:#1E40AF; border-color:#1E40AF; }}
            QPlainTextEdit {{
                background:#0D0F13; color:#D1D5DB; border:1px solid #1F2329;
                border-radius:6px; padding:8px 10px; font-family:{code_font}; font-size:14px;
                selection-background-color:#1E40AF; selection-color:#F9FAFB;
            }}
            QPlainTextEdit:focus {{ border-color:#2563EB; }}
            QScrollArea {{ background:#0A0C10; border:none; }}
            QScrollBar:vertical {{ background:transparent; width:6px; margin:2px; }}
            QScrollBar::handle:vertical {{ background:#282D36; border-radius:3px; min-height:28px; }}
            QScrollBar::handle:vertical:hover {{ background:#374151; }}
            QScrollBar::handle:vertical:pressed {{ background:#1E40AF; }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar:horizontal {{ background:transparent; height:6px; margin:2px; }}
            QScrollBar::handle:horizontal {{ background:#282D36; border-radius:3px; min-width:28px; }}
            QScrollBar::handle:horizontal:hover {{ background:#374151; }}
            QScrollBar::handle:horizontal:pressed {{ background:#1E40AF; }}
            QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal {{ width:0; }}
            QSpinBox {{
                background:#161920; color:#D1D5DB; border:1px solid #1F2329; border-radius:5px;
                padding:5px 10px; min-height:34px; font-size:14px;
                font-family:'Cascadia Code','JetBrains Mono','Consolas',monospace;
            }}
            QSpinBox:hover {{ border-color:#2563EB; }}
            QSpinBox:focus {{ border-color:#3B82F6; }}
            QSpinBox:disabled {{ background:#0F1115; color:#374151; }}
            QSpinBox::up-button {{ width:20px; border:none; border-left:1px solid #1F2329; border-bottom:1px solid #1F2329; border-top-right-radius:4px; background:#1A1D24; }}
            QSpinBox::down-button {{ width:20px; border:none; border-left:1px solid #1F2329; border-bottom-right-radius:4px; background:#1A1D24; }}
            QSlider::groove:horizontal {{ background:#1F2329; height:5px; border-radius:2px; }}
            QSlider::handle:horizontal {{
                background:#3B82F6; width:18px; height:18px; margin:-6px 0; border-radius:9px;
                border:2px solid #60A5FA;
            }}
            QSlider::handle:horizontal:hover {{ background:#60A5FA; border-color:#93C5FD; }}
            QSlider::handle:horizontal:pressed {{ background:#2563EB; border-color:#3B82F6; }}
            QSlider::sub-page:horizontal {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1E40AF,stop:1 #3B82F6); border-radius:2px; }}
            QSlider::add-page:horizontal {{ background:#1F2329; border-radius:2px; }}
        ''')

        # ===== 主分割器 =====
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(3)

        left = self._build_left()
        right = self._build_right()
        self._splitter.addWidget(left)
        self._splitter.addWidget(right)
        self._splitter.setStretchFactor(0, 5)
        self._splitter.setStretchFactor(1, 4)
        self.setCentralWidget(self._splitter)

        # 状态栏
        self.statusBar().setFixedHeight(34)
        self.statusBar().setStyleSheet('''
            QStatusBar {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0F1B3D,stop:0.5 #0E1218,stop:1 #0A0C10);
                border-top:1px solid #1A2332;
            }
            QStatusBar QLabel { color:#E5E7EB; font-size:14px; background:transparent; }
        ''')
        sbw = QWidget()
        sbl = QHBoxLayout(sbw)
        sbl.setContentsMargins(12, 0, 12, 0)
        sbl.setSpacing(0)

        left_zone = QWidget()
        left_zone.setFixedWidth(150)
        left_lay = QHBoxLayout(left_zone)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)
        self.led_conn = QLabel()
        self.led_conn.setProperty('cssClass', 'led')
        self.led_conn.setToolTip('串口连接状态')
        left_lay.addWidget(self.led_conn)
        self.status_conn = QLabel('未连接')
        self.status_conn.setStyleSheet('color:#60A5FA;font-size:13px;font-weight:600;')
        left_lay.addWidget(self.status_conn)
        left_lay.addStretch()
        sbl.addWidget(left_zone)

        sep1 = QLabel()
        sep1.setFixedWidth(1)
        sep1.setFixedHeight(18)
        sep1.setStyleSheet('background:#1A2332;')
        sbl.addWidget(sep1)

        mid_zone = QWidget()
        mid_lay = QHBoxLayout(mid_zone)
        mid_lay.setContentsMargins(12, 0, 12, 0)
        mid_lay.setSpacing(18)
        self.status_pan = QLabel('Pan: 0°')
        self.status_pan.setStyleSheet('color:#F9FAFB;font-size:15px;font-weight:700;font-family:"Cascadia Code","JetBrains Mono",monospace;')
        mid_lay.addWidget(self.status_pan)
        self.status_tilt = QLabel('Tilt: 0°')
        self.status_tilt.setStyleSheet('color:#F9FAFB;font-size:15px;font-weight:700;font-family:"Cascadia Code","JetBrains Mono",monospace;')
        mid_lay.addWidget(self.status_tilt)
        mid_lay.addStretch()
        sbl.addWidget(mid_zone)

        sep2 = QLabel()
        sep2.setFixedWidth(1)
        sep2.setFixedHeight(18)
        sep2.setStyleSheet('background:#1A2332;')
        sbl.addWidget(sep2)

        right_zone = QWidget()
        right_lay = QHBoxLayout(right_zone)
        right_lay.setContentsMargins(12, 0, 0, 0)
        right_lay.setSpacing(0)
        self.status_mode = QLabel('手动控制')
        self.status_mode.setStyleSheet('color:#6B7280;font-size:14px;')
        right_lay.addWidget(self.status_mode)
        right_lay.addStretch()
        self.status_error = QLabel('')
        self.status_error.setStyleSheet('color:#F87171;font-size:14px;font-weight:600;')
        self.status_error.hide()
        right_lay.addWidget(self.status_error)
        sbl.addWidget(right_zone)

        self.statusBar().addWidget(sbw, 1)

        QTimer.singleShot(100, self._refresh_ports)

    # ===== 左栏 =====
    def _build_left(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)
        lay.addWidget(self._gb_3d(), 3)
        lay.addWidget(self._gb_serial_io(), 2)
        return w

    def _gb_3d(self):
        gb = QGroupBox('  3D VIEW')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(2, 4, 2, 2)

        stack = QWidget()
        stack_lay = QGridLayout(stack)
        stack_lay.setContentsMargins(0, 0, 0, 0)
        stack_lay.setSpacing(0)

        self.gl = GimbalGLWidget()
        self.gl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stack_lay.addWidget(self.gl, 0, 0)

        self._empty_overlay = QLabel('等待连接串口...')
        self._empty_overlay.setAlignment(Qt.AlignCenter)
        self._empty_overlay.setStyleSheet('''
            QLabel {
                color:#5A6270; font-size:16px; font-weight:500;
                background:rgba(20,23,28,0.92); border:1px solid #1F2329;
                border-radius:10px; padding:18px 36px;
            }
        ''')
        self._empty_overlay.setVisible(True)
        self._empty_overlay.setFixedWidth(220)
        stack_lay.addWidget(self._empty_overlay, 0, 0, Qt.AlignCenter)
        lay.addWidget(stack, 1)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        bar.addStretch()
        self.chk_demo = QCheckBox('动画演示')
        self.chk_demo.stateChanged.connect(self._toggle_demo)
        bar.addWidget(self.chk_demo)
        tip = QLabel('左键旋转  |  右键平移  |  滚轮缩放')
        tip.setProperty('cssClass', 'tip')
        bar.addWidget(tip)
        bar.addStretch()
        lay.addLayout(bar)
        return gb

    def _gb_serial_io(self):
        gb = QGroupBox('  串口收发')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(8, 6, 8, 8)
        lay.setSpacing(6)

        cfg_row = QHBoxLayout()
        cfg_row.setSpacing(8)
        cfg_row.addWidget(QLabel('发送:'))
        self.cmb_smode = QComboBox()
        self.cmb_smode.addItems(['文本', 'HEX'])
        self.cmb_smode.setMaximumWidth(70)
        cfg_row.addWidget(self.cmb_smode)
        self.cmb_senc = QComboBox()
        self.cmb_senc.addItems(['UTF-8', 'GB2312', 'ASCII'])
        self.cmb_senc.setMaximumWidth(80)
        cfg_row.addWidget(self.cmb_senc)
        cfg_row.addSpacing(10)
        cfg_row.addWidget(QLabel('接收:'))
        self.cmb_rmode = QComboBox()
        self.cmb_rmode.addItems(['文本', 'HEX'])
        self.cmb_rmode.setMaximumWidth(70)
        cfg_row.addWidget(self.cmb_rmode)
        self.cmb_renc = QComboBox()
        self.cmb_renc.addItems(['UTF-8', 'GB2312', 'ASCII'])
        self.cmb_renc.setMaximumWidth(80)
        cfg_row.addWidget(self.cmb_renc)
        cfg_row.addSpacing(10)
        self.chk_hexd = QCheckBox('HEX显示')
        cfg_row.addWidget(self.chk_hexd)
        cfg_row.addStretch()
        lay.addLayout(cfg_row)

        self.txt_send = QPlainTextEdit()
        self.txt_send.setPlaceholderText('输入要发送的文本或 HEX 数据...')
        self.txt_send.setMinimumHeight(44)
        self.txt_send.setMaximumHeight(64)
        lay.addWidget(self.txt_send)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.chk_auto = QCheckBox('自动发送')
        self.chk_auto.stateChanged.connect(self._on_auto_changed)
        btn_row.addWidget(self.chk_auto)
        btn_row.addWidget(QLabel('间隔(ms):'))
        self.sp_interval = QSpinBox()
        self.sp_interval.setRange(100, 10000)
        self.sp_interval.setValue(1000)
        self.sp_interval.setMaximumWidth(78)
        btn_row.addWidget(self.sp_interval)
        btn_row.addStretch()
        bclr = QPushButton('清空')
        bclr.setProperty('cssClass', 'default')
        bclr.clicked.connect(lambda: self.txt_send.clear())
        btn_row.addWidget(bclr)
        bsend = QPushButton('发送')
        bsend.setObjectName('btn_send')
        bsend.clicked.connect(self._do_send)
        btn_row.addWidget(bsend)
        lay.addLayout(btn_row)

        self.txt_recv = QPlainTextEdit()
        self.txt_recv.setReadOnly(True)
        self.txt_recv.setPlaceholderText('等待接收数据...')
        self.txt_recv.setMinimumHeight(60)
        self.txt_recv.setMaximumHeight(100)
        lay.addWidget(self.txt_recv)

        bar2 = QHBoxLayout()
        bar2.addStretch()
        bclr2 = QPushButton('清空接收')
        bclr2.setProperty('cssClass', 'default')
        bclr2.clicked.connect(lambda: self.txt_recv.clear())
        bar2.addWidget(bclr2)
        lay.addLayout(bar2)
        return gb

    def _toggle_demo(self, state):
        self.gl.demo = bool(state)
        if state:
            self.gl._t = 0.0
        self._update_status()

    # ===== 右栏 =====
    def _build_right(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFixedWidth(440)
        w = QWidget()
        w.setStyleSheet('background:#0F1115;')
        w.setMinimumWidth(440)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 6)
        lay.setSpacing(6)
        lay.addWidget(self._gb_model_import())
        lay.addWidget(self._gb_port())
        lay.addWidget(self._gb_servo())
        lay.addWidget(self._gb_preset())
        lay.addStretch()
        sa.setWidget(w)
        return sa

    def _gb_model_import(self):
        gb = QGroupBox('  3D模型导入')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(8)

        self.lbl_model_path = QLabel('未选择模型文件')
        self.lbl_model_path.setStyleSheet('color:#6B7280;font-size:14px;font-family:monospace;')
        lay.addWidget(self.lbl_model_path)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_import = QPushButton('导入模型')
        btn_import.setProperty('cssClass', 'default')
        btn_import.clicked.connect(self._import_model)
        btn_row.addWidget(btn_import)
        btn_clear = QPushButton('清除模型')
        btn_clear.setProperty('cssClass', 'danger')
        btn_clear.clicked.connect(self._clear_model)
        btn_row.addWidget(btn_clear)
        lay.addLayout(btn_row)

        self.chk_auto_adjust = QCheckBox('根据模型自动调整舵机范围')
        self.chk_auto_adjust.setChecked(True)
        lay.addWidget(self.chk_auto_adjust)

        info_group = QGroupBox('模型信息')
        info_grid = QGridLayout(info_group)
        info_grid.setContentsMargins(8, 6, 8, 6)
        info_grid.setSpacing(6)

        self.model_info_labels = []
        info_rows = [
            ('顶点数:', 'lbl_verts'),
            ('面数:', 'lbl_faces'),
            ('尺寸(X):', 'lbl_dim_x'),
            ('尺寸(Y):', 'lbl_dim_y'),
            ('尺寸(Z):', 'lbl_dim_z'),
            ('Pan范围:', 'lbl_pan_range'),
            ('Tilt范围:', 'lbl_tilt_range'),
        ]
        
        for i, (label, attr) in enumerate(info_rows):
            lbl = QLabel(label)
            lbl.setStyleSheet('color:#6B7280;font-size:13px;')
            info_grid.addWidget(lbl, i, 0)
            val = QLabel('-')
            val.setStyleSheet('color:#60A5FA;font-size:13px;font-family:monospace;')
            setattr(self, attr, val)
            info_grid.addWidget(val, i, 1)
            self.model_info_labels.append(val)

        lay.addWidget(info_group)

        return gb

    def _import_model(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, '选择3D模型文件', '',
            '3D模型文件 (*.obj *.stl);;OBJ文件 (*.obj);;STL文件 (*.stl)'
        )
        if not filepath:
            return

        try:
            model = ModelLoader.load_model(filepath)
            analysis = ModelAnalyzer.analyze(model)
            
            if analysis:
                limits = ModelAnalyzer.calculate_servo_limits(analysis)
                
                self.lbl_model_path.setText(os.path.basename(filepath))
                self.lbl_verts.setText(str(analysis['vertex_count']))
                self.lbl_faces.setText(str(analysis['face_count']))
                self.lbl_dim_x.setText(f"{analysis['dimensions'][0]:.3f}")
                self.lbl_dim_y.setText(f"{analysis['dimensions'][1]:.3f}")
                self.lbl_dim_z.setText(f"{analysis['dimensions'][2]:.3f}")
                self.lbl_pan_range.setText(f"{limits['pan_min']}° ~ {limits['pan_max']}°")
                self.lbl_tilt_range.setText(f"{limits['tilt_min']}° ~ {limits['tilt_max']}°")

                scale_factor = 0.3 / analysis['max_dim']
                offset = [0, limits['recommended_height'] + 0.1, 0]
                
                self.gl.set_external_model(model, offset, scale_factor)

                if self.chk_auto_adjust.isChecked():
                    self._adjust_servo_limits(limits)

                QMessageBox.information(self, '导入成功', 
                    f'模型导入成功！\n顶点数: {analysis["vertex_count"]}\n面数: {analysis["face_count"]}\n最大尺寸: {analysis["max_dim"]:.3f}')
            else:
                QMessageBox.warning(self, '导入失败', '无法分析模型文件')
                
        except Exception as e:
            QMessageBox.critical(self, '导入失败', f'加载模型时出错: {str(e)}')

    def _clear_model(self):
        self.gl.clear_external_model()
        self.lbl_model_path.setText('未选择模型文件')
        for lbl in self.model_info_labels:
            lbl.setText('-')

    def _adjust_servo_limits(self, limits):
        pan_min, pan_max = limits['pan_min'], limits['pan_max']
        tilt_min, tilt_max = limits['tilt_min'], limits['tilt_max']

        self.sld_pan.blockSignals(True)
        self.sld_pan.setRange(pan_min, pan_max)
        self.sld_pan.setValue(max(pan_min, min(pan_max, self.sld_pan.value())))
        self.sld_pan.blockSignals(False)

        self.spn_pan.blockSignals(True)
        self.spn_pan.setRange(pan_min, pan_max)
        self.spn_pan.setValue(max(pan_min, min(pan_max, self.spn_pan.value())))
        self.spn_pan.blockSignals(False)

        self.sld_tilt.blockSignals(True)
        self.sld_tilt.setRange(tilt_min, tilt_max)
        self.sld_tilt.setValue(max(tilt_min, min(tilt_max, self.sld_tilt.value())))
        self.sld_tilt.blockSignals(False)

        self.spn_tilt.blockSignals(True)
        self.spn_tilt.setRange(tilt_min, tilt_max)
        self.spn_tilt.setValue(max(tilt_min, min(tilt_max, self.spn_tilt.value())))
        self.spn_tilt.blockSignals(False)

        self.lbl_pan.setText(f'{self.sld_pan.value()}°')
        self.lbl_tilt.setText(f'{self.sld_tilt.value()}°')

    def _gb_port(self):
        gb = QGroupBox('  串口配置')
        grid = QGridLayout(gb)
        grid.setContentsMargins(10, 8, 10, 10)
        grid.setSpacing(7)
        labels = ['串口号:', '波特率:', '数据位:', '停止位:', '校验位:']
        for i, lb in enumerate(labels):
            lbl = QLabel(lb)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, i, 0)
        self.cmb_port = QComboBox()
        grid.addWidget(self.cmb_port, 0, 1)
        self.cmb_baud = QComboBox()
        self.cmb_baud.addItems(['4800', '9600', '38400', '115200'])
        self.cmb_baud.setCurrentText('9600')
        grid.addWidget(self.cmb_baud, 1, 1)
        self.cmb_dbits = QComboBox()
        self.cmb_dbits.addItems(['5', '6', '7', '8'])
        self.cmb_dbits.setCurrentText('8')
        grid.addWidget(self.cmb_dbits, 2, 1)
        self.cmb_sbits = QComboBox()
        self.cmb_sbits.addItems(['1', '1.5', '2'])
        self.cmb_sbits.setCurrentText('1')
        grid.addWidget(self.cmb_sbits, 3, 1)
        self.cmb_parity = QComboBox()
        self.cmb_parity.addItems(['无', '奇', '偶'])
        self.cmb_parity.setCurrentText('无')
        grid.addWidget(self.cmb_parity, 4, 1)
        self.btn_open = QPushButton('打开串口')
        self.btn_open.setObjectName('btn_open')
        self.btn_open.setCheckable(True)
        self.btn_open.setToolTip('打开/关闭串口连接')
        self.btn_open.clicked.connect(self._toggle_port)
        grid.addWidget(self.btn_open, 5, 0, 1, 2, Qt.AlignHCenter)
        btn_refresh = QPushButton('刷新')
        btn_refresh.setProperty('cssClass', 'default')
        btn_refresh.setMaximumWidth(60)
        btn_refresh.clicked.connect(self._refresh_ports)
        grid.addWidget(btn_refresh, 0, 2)
        return gb

    def _gb_servo(self):
        gb = QGroupBox('  舵机控制')
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(12)
        for axis, label, min_v, max_v, default_v in [
            ('pan', 'Pan', 0, 270, 0),
            ('tilt', 'Tilt', 0, 180, 0)
        ]:
            lbl = QLabel(label)
            lbl.setProperty('cssClass', 'title')
            lbl.setStyleSheet('font-size:16px;')
            lay.addWidget(lbl)
            row = QHBoxLayout()
            row.setSpacing(10)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(min_v, max_v)
            sld.setValue(default_v)
            sld.setMinimumHeight(28)
            setattr(self, f'sld_{axis}', sld)
            row.addWidget(sld, 1)
            val = QLabel(f'{default_v}\u00b0')
            val.setProperty('cssClass', 'value')
            val.setAlignment(Qt.AlignCenter)
            val.setFixedWidth(68)
            val.setFixedHeight(34)
            setattr(self, f'lbl_{axis}', val)
            row.addWidget(val)
            spn = QSpinBox()
            spn.setRange(min_v, max_v)
            spn.setValue(default_v)
            spn.setFixedWidth(66)
            setattr(self, f'spn_{axis}', spn)
            row.addWidget(spn)
            lay.addLayout(row)
        for a in ('pan', 'tilt'):
            getattr(self, f'sld_{a}').valueChanged.connect(
                lambda v, ax=a: self._on_angle(ax, v, 'sld'))
            getattr(self, f'spn_{a}').valueChanged.connect(
                lambda v, ax=a: self._on_angle(ax, v, 'spn'))
        return gb

    def _on_angle(self, axis, v, src):
        if src == 'sld':
            getattr(self, f'spn_{axis}').blockSignals(True)
            getattr(self, f'spn_{axis}').setValue(v)
            getattr(self, f'spn_{axis}').blockSignals(False)
        else:
            getattr(self, f'sld_{axis}').blockSignals(True)
            getattr(self, f'sld_{axis}').setValue(v)
            getattr(self, f'sld_{axis}').blockSignals(False)
        getattr(self, f'lbl_{axis}').setText(f'{v}°')
        p = v if axis == 'pan' else self.gl.target_pan
        t = v if axis == 'tilt' else self.gl.target_tilt
        self.gl.set_angles(p, t)
        if self.chk_demo.isChecked():
            self.chk_demo.setChecked(False)
        self._pending_pan = int(p)
        self._pending_tilt = int(t)
        if not self._servo_pending:
            self._servo_pending = True
            QTimer.singleShot(80, self._send_servo_angles)
        self._update_status()

    def set_angles_external(self, pan, tilt):
        pan = int(max(0, min(270, pan)))
        tilt = int(max(0, min(180, tilt)))
        self.gl.set_angles(pan, tilt)
        self.sld_pan.blockSignals(True)
        self.sld_pan.setValue(pan)
        self.sld_pan.blockSignals(False)
        self.sld_tilt.blockSignals(True)
        self.sld_tilt.setValue(tilt)
        self.sld_tilt.blockSignals(False)
        self.spn_pan.blockSignals(True)
        self.spn_pan.setValue(pan)
        self.spn_pan.blockSignals(False)
        self.spn_tilt.blockSignals(True)
        self.spn_tilt.setValue(tilt)
        self.spn_tilt.blockSignals(False)
        self.lbl_pan.setText(f'{pan}°')
        self.lbl_tilt.setText(f'{tilt}°')
        if self.chk_demo.isChecked():
            self.chk_demo.setChecked(False)
        self._pending_pan = pan
        self._pending_tilt = tilt
        if not self._servo_pending:
            self._servo_pending = True
            QTimer.singleShot(80, self._send_servo_angles)
        self._update_status()

    def _update_status(self):
        p = int(self.gl.pan)
        t = int(self.gl.tilt)
        conn = '已连接' if self.slink.is_open else '未连接'
        demo = 'Demo 运行中' if self.gl.demo else '手动控制'
        self.status_pan.setText(f'Pan: {p}°')
        self.status_tilt.setText(f'Tilt: {t}°')
        self.status_conn.setText(conn)
        self.status_mode.setText(demo)
        if self.slink.is_open:
            self.led_conn.setProperty('cssClass', 'led-on')
            self.status_conn.setStyleSheet('color:#4ADE80;font-size:14px;font-weight:600;')
            self._empty_overlay.setVisible(False)
            self._start_led_pulse()
        else:
            self.led_conn.setProperty('cssClass', 'led')
            self.status_conn.setStyleSheet('color:#60A5FA;font-size:14px;font-weight:600;')
            self._empty_overlay.setVisible(True)
            self._stop_led_pulse()
        self.led_conn.style().unpolish(self.led_conn)
        self.led_conn.style().polish(self.led_conn)

    def _start_led_pulse(self):
        if not hasattr(self, '_led_fx'):
            self._led_fx = QGraphicsOpacityEffect(self.led_conn)
            self._led_fx.setOpacity(1.0)
            self.led_conn.setGraphicsEffect(self._led_fx)
            self._led_pulse = QPropertyAnimation(self._led_fx, b"opacity")
            self._led_pulse.setDuration(1400)
            self._led_pulse.setStartValue(1.0)
            self._led_pulse.setKeyValueAt(0.5, 0.45)
            self._led_pulse.setEndValue(1.0)
            self._led_pulse.setEasingCurve(QEasingCurve.InOutSine)
            self._led_pulse.setLoopCount(-1)
            self._led_pulse.start()

    def _stop_led_pulse(self):
        if hasattr(self, '_led_pulse'):
            self._led_pulse.stop()
            self.led_conn.setGraphicsEffect(None)
            del self._led_pulse
            del self._led_fx

    # ===== 预设位 =====
    def _gb_preset(self):
        gb = QGroupBox('  预设位')
        outer = QHBoxLayout(gb)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(10)

        btn_zero = QPushButton('归零\n0\u00b0, 0\u00b0')
        btn_zero.setProperty('cssClass', 'zero')
        btn_zero.setMinimumHeight(72)
        btn_zero.setMinimumWidth(90)
        btn_zero.setToolTip('将 Pan/Tilt 归零到 0\u00b0')
        btn_zero.clicked.connect(lambda: self._preset(0, 0))
        outer.addWidget(btn_zero)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        presets = [
            ('左上\n0\u00b0, 90\u00b0', 0, 90, 0, 0),
            ('右上\n270\u00b0, 90\u00b0', 270, 90, 0, 1),
            ('左下\n0\u00b0, 180\u00b0', 0, 180, 1, 0),
            ('右下\n270\u00b0, 180\u00b0', 270, 180, 1, 1),
        ]
        for txt, p, t, r, c in presets:
            btn = QPushButton(txt)
            btn.setProperty('cssClass', 'default')
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(80)
            btn.setToolTip(f'设置舵机到 Pan:{p}\u00b0 Tilt:{t}\u00b0')
            btn.clicked.connect(lambda _, pp=p, tt=t: self._preset(pp, tt))
            grid.addWidget(btn, r, c)
        btn_query = QPushButton('查询当前角度')
        btn_query.setProperty('cssClass', 'default')
        btn_query.setMinimumHeight(36)
        btn_query.setToolTip('查询当前舵机角度')
        btn_query.clicked.connect(lambda: self._preset(-1, -1))
        grid.addWidget(btn_query, 2, 0, 1, 2)
        outer.addLayout(grid)
        return gb

    def _preset(self, p, t):
        if p == -1:
            if self.slink.is_open:
                self.slink.send(b'S\r\n')
            return
        self.sld_pan.setValue(p)
        self.sld_tilt.setValue(t)

    # ===== 串口操作 =====
    def _refresh_ports(self):
        self.cmb_port.clear()
        ports = self.slink.list_ports()
        if not ports:
            self.cmb_port.addItem('(未发现串口)')
        else:
            self.cmb_port.addItems(ports)

    def _toggle_port(self):
        if self.slink.is_open:
            self.slink.close()
            self.btn_open.setChecked(False)
            self.btn_open.setText('打开串口')
            self._auto_interval_connected = False
            self._auto_send_timer.stop()
            self.status_error.hide()
        else:
            port = self.cmb_port.currentText()
            if port.startswith('('):
                self.status_error.setText('没有可用串口')
                self.status_error.show()
                QTimer.singleShot(3000, self.status_error.hide)
                self.btn_open.setChecked(False)
                return
            baud = int(self.cmb_baud.currentText())
            dbits = self.cmb_dbits.currentText()
            sbits = self.cmb_sbits.currentText()
            parity = self.cmb_parity.currentText()
            self.btn_open.setEnabled(False)
            self.btn_open.setText('连接中...')
            self._open_worker = SerialOpenWorker(port, baud, dbits, sbits, parity)
            self._open_worker.finished.connect(self._on_port_opened)
            self._open_worker.start()

    def _on_port_opened(self, success, msg):
        self.btn_open.setEnabled(True)
        if success:
            self.slink.set_serial(self._open_worker.ser)
            self.btn_open.setChecked(True)
            self.btn_open.setText('关闭串口')
            self.status_error.hide()
            self._recv_buf = b''
            if self.chk_auto.isChecked():
                self._auto_interval_connected = True
                self._auto_send_timer.start(self.sp_interval.value())
            self._recv_timer = QTimer(self)
            self._recv_timer.timeout.connect(self._poll_recv)
            self._recv_timer.start(30)
        else:
            self.btn_open.setChecked(False)
            self.btn_open.setText('打开串口')
            self.status_error.setText(msg[:80])
            self.status_error.show()
            QTimer.singleShot(5000, self.status_error.hide)

    def _do_send(self):
        if not self.slink.is_open:
            return
        txt = self.txt_send.toPlainText()
        if not txt:
            return
        try:
            if self.cmb_smode.currentText() == 'HEX':
                clean = txt.replace(' ', '').replace('\n', '')
                data = bytes.fromhex(clean)
            else:
                enc = self.cmb_senc.currentText()
                data = txt.encode(enc)
            self.slink.send(data)
        except Exception as e:
            self.status_error.setText(f'发送错误: {e}')
            self.status_error.show()
            QTimer.singleShot(3000, self.status_error.hide)

    def _on_auto_changed(self, state):
        if state and self.slink.is_open:
            self._auto_interval_connected = True
            self._auto_send_timer.start(self.sp_interval.value())
        else:
            self._auto_interval_connected = False
            self._auto_send_timer.stop()

    def _auto_send_tick(self):
        if not self.slink.is_open:
            return
        txt = self.txt_send.toPlainText()
        if not txt:
            return
        try:
            if self.cmb_smode.currentText() == 'HEX':
                clean = txt.replace(' ', '').replace('\n', '')
                data = bytes.fromhex(clean)
            else:
                enc = self.cmb_senc.currentText()
                data = txt.encode(enc)
            self.slink.send(data)
        except Exception:
            pass

    def _send_servo_angles(self):
        self._servo_pending = False
        if self.slink.is_open:
            cmd = f'B:{self._pending_pan},{self._pending_tilt}\r\n'.encode()
            self.slink.send(cmd)

    def _poll_recv(self):
        if not self.slink.is_open:
            return
        data = self.slink.read_all()
        if not data:
            return
        self._recv_buf += data
        while b'\n' in self._recv_buf:
            line, _, self._recv_buf = self._recv_buf.partition(b'\n')
            line = line.replace(b'\r', b'')
            try:
                text = line.decode(self.cmb_renc.currentText(), errors='replace')
            except Exception:
                text = line.decode('utf-8', errors='replace')
            if self.chk_hexd.isChecked():
                hex_str = ' '.join(f'{b:02X}' for b in line)
                self.txt_recv.appendPlainText(f'[HEX] {hex_str}')
            else:
                self.txt_recv.appendPlainText(text)
            self._parse_rx_line(text)

    def _parse_rx_line(self, line):
        try:
            line = line.strip()
            if line.startswith('A1:') and 'A2:' in line:
                a1 = float(line.split('A1:')[1].split(',')[0])
                a2 = float(line.split('A2:')[1].split(',')[0])
                self.set_angles_external(a1, a2)
        except Exception:
            pass

    def closeEvent(self, ev):
        self.slink.close()
        super().closeEvent(ev)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
