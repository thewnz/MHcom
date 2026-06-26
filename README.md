# MHcom - 多功能串口助手

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-5.15+-blue.svg)](https://www.qt.io/)

基于 PyQt5 的专业级串口助手，支持波形图、Modbus、数据记录等多种功能。

---

## ✨ 功能特性

### 📡 串口通信
- 支持多串口同时连接
- 支持多种波特率、数据位、停止位、校验位配置
- HEX/文本模式切换
- 定时发送功能
- 文件发送功能
- 发送历史记录

### 📊 实时波形图
- 多通道数据可视化
- 支持 FireWater 协议
- FFT 频谱分析
- 游标测量功能
- 数据导出为 CSV

### 🔌 Modbus RTU
- 主站请求构造
- 响应解析
- 寄存器读写测试
- 支持常用功能码

### 🛠 实用工具
- CRC 计算器
- 十六进制转换器
- 协议解析器
- 数据记录器
- 宏编辑器
- 自动回复器

### 🎨 界面特性
- 深色/浅色主题切换
- 可定制布局
- 独立工具窗口
- 全局数据总线

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **Qt**: 5.15 或更高版本

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

---

## 📦 打包

### 使用 PyInstaller

```bash
# 打包为单文件
pyinstaller --onefile --windowed --name MHcom main.py

# 打包为文件夹
pyinstaller --onedir --windowed --name MHcom main.py
```

---

## 🏗 项目结构

```
MHcom/
├── main.py                  # 程序入口
├── gimbal_3d_v3.py          # 主窗口
├── requirements.txt         # 依赖列表
├── config/                  # 配置模块
│   ├── settings.py          # 设置管理
│   └── user_config.json     # 用户配置
├── core/                    # 核心模块
│   ├── serial_link.py       # 串口通信
│   ├── data_bus.py          # 数据总线
│   ├── modbus_rtu.py        # Modbus协议
│   └── tool_manager.py      # 工具管理
├── tools/                   # 工具模块
│   ├── waveform_tool.py     # 波形图工具
│   ├── modbus_tool.py       # Modbus工具
│   ├── terminal_tool.py     # 终端工具
│   └── ...                  # 其他工具
├── themes/                  # 主题模块
│   ├── dark_theme.py        # 深色主题
│   └── light_theme.py       # 浅色主题
└── utils/                   # 工具函数
```

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 👤 作者

**Mouse**
- 安徽农业大学 电子信息工程
- GitHub: [@thewnz](https://github.com/thewnz)

---

## 📧 联系方式

如有问题或建议，请提交 Issue 或发送邮件至 m2627898738@163.com
