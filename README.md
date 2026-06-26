# MHcom - 多功能串口助手

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-5.15+-green.svg)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

一款基于 PyQt5 开发的专业级串口调试助手，专为嵌入式开发者设计。集成了实时波形可视化、Modbus RTU 协议调试、数据记录等强大功能，帮助您更高效地进行串口通信调试。

---

## 功能特性

### 串口通信核心

| 功能 | 说明 |
|------|------|
| 多串口支持 | 同时连接和管理多个串口设备 |
| 灵活配置 | 支持波特率 300~921600、数据位 5/6/7/8、停止位 1/1.5/2、校验位 None/Odd/Even/Mark/Space |
| 收发模式 | HEX / ASCII 文本模式自由切换 |
| 定时发送 | 自定义发送间隔，支持循环发送 |
| 文件传输 | 直接从文件发送二进制或文本数据 |
| 历史记录 | 自动保存发送历史，支持快速重发 |

### 实时波形图

- **多通道显示**：同时显示多路数据波形，支持通道颜色自定义
- **数据协议**：内置 FireWater 协议解析，支持自定义协议格式
- **频谱分析**：内置 FFT 功能，实时查看信号频域特征
- **游标测量**：添加测量游标，精确读取任意时刻的数据值
- **数据导出**：波形数据可导出为 CSV 文件，便于后续分析

### Modbus RTU 调试

- **主站模式**：图形化构造读写请求（功能码 01/02/03/04/05/06/15/16）
- **从站模拟**：模拟 Modbus 从站设备响应
- **响应解析**：自动解析从站返回数据并高亮显示
- **批量测试**：支持连续读取多个寄存器地址

### 实用工具集

| 工具 | 用途 |
|------|------|
| CRC 计算器 | 支持 CRC-8/16/32 及 Modbus 校验 |
| 十六进制转换器 | HEX/DEC/BIN/OCT 多进制互转 |
| 数据记录器 | 实时记录串口数据，支持自动保存和时间戳 |
| 协议解析器 | 自定义协议格式，解析二进制数据流 |
| 宏编辑器 | 编辑和管理常用发送命令宏 |
| 自动回复器 | 设置触发条件，自动发送预设响应 |
| 颜色拾取器 | 快速获取颜色值，便于界面定制 |
| 正则表达式工具 | 测试和调试正则表达式 |
| 终端工具 | 类命令行界面，支持脚本执行 |
| 数据统计 | 实时统计收发字节数、帧数、错误率 |
| 监控工具 | 监控串口数据流量和状态 |
| 设置面板 | 全局参数配置和个性化设置 |

### 界面与体验

- **主题切换**：深色 / 浅色主题一键切换，保护眼睛
- **可定制布局**：自由调整面板大小和位置
- **独立窗口**：工具面板可独立浮动，支持多显示器
- **全局数据总线**：各模块数据实时同步，无需重复读取

---

## 快速开始

### 环境要求

- **操作系统**：Windows 7/10/11
- **Python**：3.8 或更高版本
- **依赖库**：PyQt5、pyserial、pyqtgraph 等

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/thewnz/MHcom.git

# 2. 进入项目目录
cd MHcom

# 3. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行程序
python main.py
```

### 依赖列表

```
pyqt5>=5.15.0
pyserial>=3.5
pyqtgraph>=0.12.0
numpy>=1.20.0
```

---

## 打包分发

### 使用 PyInstaller

```bash
# 打包为单个可执行文件（推荐）
pyinstaller --onefile --windowed --name MHcom main.py

# 打包为文件夹（启动更快）
pyinstaller --onedir --windowed --name MHcom main.py
```

打包完成后，可执行文件位于 `dist/` 目录下。

---

## 项目结构

```
MHcom/
│
├── main.py                     # 程序入口，启动应用
├── gimbal_3d_v3.py             # 主窗口界面
├── requirements.txt            # Python 依赖列表
├── LICENSE                     # MIT 开源许可证
├── README.md                   # 项目说明文档
│
├── config/                     # 配置管理模块
│   ├── __init__.py
│   ├── settings.py             # 应用设置管理
│   └── user_config.json        # 用户自定义配置
│
├── core/                       # 核心功能模块
│   ├── __init__.py
│   ├── serial_link.py          # 串口通信封装
│   ├── data_bus.py             # 全局数据总线
│   ├── data_parser.py          # 数据解析器
│   ├── modbus_rtu.py           # Modbus RTU 协议实现
│   ├── crc_calculator.py       # CRC 校验计算
│   ├── statistics.py           # 数据统计
│   └── tool_manager.py         # 工具管理器
│
├── tools/                      # 功能工具模块
│   ├── __init__.py
│   ├── waveform_tool.py        # 实时波形图
│   ├── modbus_tool.py          # Modbus 调试工具
│   ├── terminal_tool.py        # 终端工具
│   ├── crc_tool.py             # CRC 计算器
│   ├── hex_converter_tool.py   # 进制转换器
│   ├── data_logger_tool.py     # 数据记录器
│   ├── protocol_parser_tool.py # 协议解析器
│   ├── macro_editor_tool.py    # 宏编辑器
│   ├── auto_reply_tool.py      # 自动回复器
│   ├── color_picker_tool.py    # 颜色拾取器
│   ├── regex_tool.py           # 正则表达式工具
│   ├── statistics_tool.py      # 数据统计面板
│   ├── monitor_tool.py         # 监控工具
│   ├── control_panel_tool.py   # 控制面板
│   ├── settings_dialog.py      # 设置对话框
│   ├── history_tool.py         # 历史记录
│   └── help_dialog.py          # 帮助文档
│
├── themes/                     # 界面主题模块
│   ├── __init__.py
│   ├── dark_theme.py           # 深色主题
│   └── light_theme.py          # 浅色主题
│
├── widgets/                    # 自定义控件
│   ├── __init__.py
│   ├── common.py               # 通用控件
│   └── gimbal_gl_widget.py     # OpenGL 3D 控件
│
├── panels/                     # 面板模块
│   ├── __init__.py
│   ├── gimbal_panel.py         # 云台控制面板
│   └── terminal_panel.py       # 终端面板
│
├── model/                      # 3D 模型模块
│   ├── __init__.py
│   ├── model_loader.py         # 模型加载器
│   └── model_analyzer.py       # 模型分析器
│
└── utils/                      # 工具函数
    └── __init__.py
```

---

## 配置说明

配置文件 `config/user_config.json` 包含以下主要配置项：

```json
{
  "serial": {
    "default_port": "COM1",
    "default_baudrate": 115200,
    "default_data_bits": 8,
    "default_stop_bits": 1,
    "default_parity": "None"
  },
  "display": {
    "theme": "dark",
    "font_size": 12,
    "auto_scroll": true,
    "timestamp": true
  },
  "waveform": {
    "max_points": 1000,
    "update_interval": 50,
    "channels": 4
  }
}
```

---

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 更新日志

### v1.0.0 (2024-01)
- 初始发布
- 实现基础串口通信功能
- 添加实时波形图显示
- 集成 Modbus RTU 调试工具
- 支持深色/浅色主题切换

---

## 常见问题

### Q: 无法打开串口？
A: 请检查：
- 串口设备是否已正确连接
- 串口驱动是否已安装
- 是否有其他程序占用该串口
- 尝试以管理员身份运行

### Q: 波形图不显示数据？
A: 请检查：
- 串口是否已成功打开
- 发送的数据格式是否正确
- 波形通道配置是否匹配

### Q: Modbus 通信无响应？
A: 请检查：
- 从站地址是否正确
- 波特率和数据格式是否匹配
- CRC 校验是否正确

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 作者

**Mouse**
- 安徽农业大学 · 电子信息工程
- GitHub: [@thewnz](https://github.com/thewnz)
- Email: m2627898738@163.com

---

## 致谢

感谢所有为本项目提供帮助和建议的开发者！

如果这个项目对您有帮助，请给个 Star 支持一下！
