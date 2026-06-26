# MHcom Test Firmware

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![STM32](https://img.shields.io/badge/MCU-STM32F103C8-blue.svg)](https://www.st.com/en/microcontrollers-microprocessors/stm32f103c8.html)
[![Keil](https://img.shields.io/badge/Toolchain-Keil%20uVision5-blue.svg)](https://www.keil.com/)

基于 STM32F103C8T6 的 **MHcom 串口助手**全功能测试固件，用于验证 MHcom 的各项功能，包括波形图、Modbus、文件发送、数据记录等。

---

## ✨ 功能特性

### 📊 波形图测试
- **8通道波形输出**: 支持正弦波、方波、三角波、锯齿波、直流、噪声
- **可调参数**: 幅值、频率、相位、偏移
- **可调采样率**: 1Hz ~ 1000Hz
- **CSV格式输出**: 与 MHcom 波形图工具完美兼容

### 🔌 Modbus RTU 测试
- **从站地址**: 1
- **支持8种功能码**:
  - 0x01: 读线圈状态
  - 0x02: 读离散输入
  - 0x03: 读保持寄存器
  - 0x04: 读输入寄存器
  - 0x05: 写单个线圈
  - 0x06: 写单个寄存器
  - 0x0F: 写多个线圈
  - 0x10: 写多个寄存器
- **32个保持寄存器** (0x0000~0x001F)
- **16个输入寄存器** (0x0000~0x000F)

### 💬 命令控制系统
- **5种工作模式**: 菜单、波形图、Modbus、回显、计数器
- **简洁命令语法**: `#command [parameters]`
- **实时反馈**: OLED显示当前状态

### 📡 串口通信
- **115200波特率**: 高速数据传输
- **环形缓冲区**: 防止数据丢失
- **接收中断**: 实时响应

---

## 🚀 快速开始

### 硬件要求

| 组件 | 型号 | 连接引脚 |
|------|------|----------|
| 微控制器 | STM32F103C8T6 | - |
| 显示屏 | OLED (SSD1306) | PB6(SCL), PB7(SDA) |
| LED | 发光二极管 | PC13 |
| 按键 | 轻触开关 | PA0 |
| 串口 | USB转TTL | PA9(TX), PA10(RX) |

### 软件环境

- **Keil uVision5** 或更高版本
- **STM32F1xx标准外设库**

### 编译与下载

1. 打开 `MHcom_Test.uvprojx`
2. 点击 **Build** (F7) 编译工程
3. 点击 **Download** (F8) 下载到开发板

### 串口配置

- **波特率**: 115200
- **数据位**: 8
- **停止位**: 1
- **校验位**: 无

---

## 📖 使用指南

### 进入命令模式

打开 MHcom 串口助手，发送 `#help` 查看所有命令：

```bash
#help
```

### 切换工作模式

```bash
#mode menu      # 菜单模式（默认）
#mode wave      # 波形图测试模式
#mode modbus    # Modbus RTU从站模式
#mode echo      # 回显模式
#mode counter   # 计数器模式
```

### 波形控制

```bash
#wave ch1 sine 50 1 0 0     # 通道1: 正弦波, 幅值50, 频率1Hz
#wave ch2 square 40 2 0 10  # 通道2: 方波, 幅值40, 频率2Hz
#wave count 4               # 设置4通道
#wave rate 100              # 设置采样率100Hz
```

### LED控制

```bash
#led on        # 点亮LED
#led off       # 熄灭LED
#led toggle    # 翻转LED状态
```

### 测试命令

```bash
#test crc      # CRC测试数据
#test hex      # HEX数据测试
#test text     # 文本数据测试
#test long     # 长包测试（100行）
```

---

## 🏗 项目结构

```
MHcom_Test/
├── MHcom_Test.uvprojx        # Keil工程文件
├── README.md                 # 项目说明文档
├── .gitignore                # Git忽略配置
├── Hardware/                 # 硬件驱动模块
│   ├── Serial.c/h            # 串口通信（增强版）
│   ├── WaveformGen.c/h       # 波形数据生成器
│   ├── Modbus_Slave.c/h      # Modbus RTU从站
│   ├── CommandParser.c/h     # 命令解析器
│   ├── OLED.c/h              # OLED显示驱动
│   ├── LED.c/h               # LED控制
│   └── Key.c/h               # 按键输入
├── System/                   # 系统模块
│   └── Delay.c/h             # 延时函数
├── Start/                    # STM32启动文件
│   ├── core_cm3.c/h          # Cortex-M3核心
│   ├── startup_stm32f10x_md.s # 启动汇编
│   └── system_stm32f10x.c/h  # 系统初始化
├── Library/                  # STM32标准外设库
│   ├── stm32f10x_gpio.c/h    # GPIO驱动
│   ├── stm32f10x_usart.c/h   # USART驱动
│   ├── stm32f10x_i2c.c/h     # I2C驱动
│   └── ...                   # 其他外设驱动
└── User/                     # 用户应用代码
    ├── main.c                # 主程序入口
    ├── stm32f10x_conf.h      # 库配置
    └── stm32f10x_it.c/h      # 中断服务
```

---

## 🧪 MHcom 测试场景

### 场景1: 测试实时波形图

```bash
#mode wave
```

在 MHcom 中打开波形图工具，设置4通道，观察实时波形显示。

### 场景2: 测试 Modbus RTU

```bash
#mode modbus
```

在 MHcom 中打开 Modbus 工具：
- 从站地址: 1
- 功能码: 03 (读保持寄存器)
- 起始地址: 0
- 数量: 10

### 场景3: 测试文件发送

```bash
#mode echo
```

使用 MHcom 的发送文件功能，验证文件传输完整性。

### 场景4: 测试数据记录

```bash
#mode counter
```

打开数据记录器工具，记录计数器数据并保存为CSV文件。

---

## 🛠 技术栈

- **MCU**: STM32F103C8T6 (Cortex-M3, 72MHz)
- **RTOS**: 无 (裸机)
- **编译工具**: Keil uVision5 (ARMCC v5)
- **通信协议**: UART, I2C, Modbus RTU
- **显示**: OLED (SSD1306, 128x64)

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 👤 作者

**Mouse**
- 安徽农业大学 电子信息工程
- GitHub: [@thewnz](https://github.com/thewnz)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 提交规范

- **Bug修复**: `fix: 修复XXX问题`
- **功能新增**: `feat: 添加XXX功能`
- **文档更新**: `docs: 更新XXX文档`
- **代码优化**: `refactor: 优化XXX代码`

---

## 📧 联系方式

如有问题或建议，请提交 Issue 或发送邮件至 m2627898738@163.com
