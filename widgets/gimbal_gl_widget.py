# -*- coding: utf-8 -*-
"""
3D 云台显示控件
- 双轴云台 3D 渲染
- 鼠标交互 (旋转/缩放/平移)
- 支持导入外部 3D 模型
- 完整 MG996R 舵机 + 标准云台支架 + 摄像头
"""
import math
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


def hex2rgb(h, a=1.0):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [a]


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
        try:
            if self.demo:
                self._t += .016
                self.target_pan  = 135 + 120 * math.sin(self._t * .8)
                self.target_tilt = 90 + 70 * math.sin(self._t * .6 + 1.)
            self.pan  += (self.target_pan  - self.pan ) * .12
            self.tilt += (self.target_tilt - self.tilt) * .12
            self.update()
        except Exception:
            pass

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
            # 计算面法线：对三角形用叉积，多边形用 Newell 法
            face_verts = []
            for vi, ti, ni in face:
                if vi >= 0 and vi < len(vertices):
                    v = vertices[vi]
                    face_verts.append((v[0], v[1], v[2]))
            if len(face_verts) >= 3:
                # Newell's method for polygon normal
                nx = ny = nz = 0.0
                n = len(face_verts)
                for i in range(n):
                    x1, y1, z1 = face_verts[i]
                    x2, y2, z2 = face_verts[(i + 1) % n]
                    nx += (y1 - y2) * (z1 + z2)
                    ny += (z1 - z2) * (x1 + x2)
                    nz += (x1 - x2) * (y1 + y2)
                length = (nx * nx + ny * ny + nz * nz) ** 0.5
                if length > 1e-10:
                    glNormal3f(nx / length, ny / length, nz / length)
            for vi, ti, ni in face:
                if vi >= 0 and vi < len(vertices):
                    glVertex3f(vertices[vi][0], vertices[vi][1], vertices[vi][2])
            glEnd()
        
        glPopMatrix()


# ==================== SerialLink 串口核心 ====================