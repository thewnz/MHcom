# -*- coding: utf-8 -*-
"""
3D 模型加载与解析
支持: OBJ (Wavefront), STL (ASCII/Binary)
"""
import os
import re


class ModelLoader:
    """3D 模型加载器"""

    @staticmethod
    def load_obj(filepath: str) -> dict:
        """加载 OBJ 格式模型"""
        vertices = []
        faces = []
        texcoords = []
        normals = []

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    cmd = parts[0]
                    if cmd == 'v' and len(parts) >= 4:
                        try:
                            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                        except ValueError:
                            continue
                    elif cmd == 'vt' and len(parts) >= 3:
                        try:
                            texcoords.append([float(parts[1]), float(parts[2])])
                        except ValueError:
                            continue
                    elif cmd == 'vn' and len(parts) >= 4:
                        try:
                            normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                        except ValueError:
                            continue
                    elif cmd == 'f' and len(parts) >= 4:
                        face = []
                        for part in parts[1:]:
                            indices = part.split('/')
                            vi = int(indices[0]) - 1 if indices[0] else -1
                            ti = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                            ni = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                            face.append((vi, ti, ni))
                        faces.append(face)
        except Exception as e:
            raise ValueError(f"加载 OBJ 文件失败: {e}")

        return {
            'vertices': vertices,
            'faces': faces,
            'texcoords': texcoords,
            'normals': normals,
        }

    @staticmethod
    def load_stl(filepath: str) -> dict:
        """加载 STL 格式模型 (自动识别 ASCII/Binary)"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(80)
                if header[:5] == b'solid':
                    return ModelLoader._load_stl_ascii(f, header)
                else:
                    return ModelLoader._load_stl_binary(f)
        except Exception as e:
            raise ValueError(f"加载 STL 文件失败: {e}")

    @staticmethod
    def _load_stl_ascii(f, header: bytes) -> dict:
        """加载 ASCII 格式 STL"""
        vertices = []
        faces = []
        content = header.decode('ascii', errors='ignore') + f.read().decode('ascii', errors='ignore')
        lines = content.split('\n')
        current_face = []
        for line in lines:
            line = line.strip()
            if line.startswith('vertex'):
                parts = re.split(r'\s+', line)
                if len(parts) >= 4:
                    try:
                        current_face.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    except ValueError:
                        continue
            elif line.startswith('endloop') and current_face:
                if len(current_face) >= 3:
                    start_idx = len(vertices)
                    faces.append([(start_idx + i, -1, -1) for i in range(len(current_face))])
                    vertices.extend(current_face)
                current_face = []
        return {'vertices': vertices, 'faces': faces, 'texcoords': [], 'normals': []}

    @staticmethod
    def _load_stl_binary(f) -> dict:
        """加载 Binary 格式 STL"""
        import struct
        vertices = []
        faces = []
        f.seek(80)
        num_faces_bytes = f.read(4)
        if len(num_faces_bytes) < 4:
            return {'vertices': [], 'faces': [], 'texcoords': [], 'normals': []}
        num_faces = struct.unpack('<I', num_faces_bytes)[0]
        # 防止读取过大的文件
        if num_faces > 5_000_000:
            raise ValueError("STL 文件面数过多")
        for _ in range(num_faces):
            # normal (3 floats) + 3 vertices (9 floats) + attribute (2 bytes) = 50 bytes
            data = f.read(50)
            if len(data) < 50:
                break
            values = struct.unpack('<12fH', data)
            face_verts = []
            for j in range(3):
                vert = [values[3 + j*3], values[3 + j*3 + 1], values[3 + j*3 + 2]]
                face_verts.append(vert)
                vertices.append(vert)
            start = len(vertices) - 3
            faces.append([(start, -1, -1), (start + 1, -1, -1), (start + 2, -1, -1)])
        return {'vertices': vertices, 'faces': faces, 'texcoords': [], 'normals': []}

    @staticmethod
    def load_model(filepath: str) -> dict:
        """根据文件扩展名自动选择加载器"""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.obj':
            return ModelLoader.load_obj(filepath)
        elif ext in ('.stl', '.stla', '.stlb'):
            return ModelLoader.load_stl(filepath)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
