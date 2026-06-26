# -*- coding: utf-8 -*-
"""
帮助对话框 - 完整功能说明文档
左侧导航树 + 右侧内容显示
"""

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QTextCursor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextBrowser,
    QPushButton, QLabel, QLineEdit, QFrame
)


HELP_CONTENT = {
    'overview': {
        'title': '软件概述',
        'content': '''
<h2>MHcom - 多功能高级串口助手 v2.0</h2>
<p>一款集成 <b>3D舵机云台调试</b> 与 <b>高级串口助手</b> 的双模专业工具软件。</p>

<h3>核心特性</h3>
<ul>
<li><b>双模切换</b>：3D云台调试 / 高级串口助手，一键切换</li>
<li><b>3D模型导入</b>：支持 OBJ / STL 格式，自动分析并调整舵机范围</li>
<li><b>16+ 独立工具</b>：波形图、Modbus、CRC、HEX转换、协议解析等</li>
<li><b>双主题</b>：浅色（工程师明亮）/ 深色（深空玻璃）随心切换</li>
<li><b>模块化架构</b>：工具窗口独立运行，互不干扰</li>
<li><b>全局数据总线</b>：主窗口与工具窗口实时数据共享</li>
</ul>

<h3>系统要求</h3>
<ul>
<li>操作系统：Windows 7 / 10 / 11</li>
<li>Python 3.8+（开发环境）</li>
<li>PyQt5、PySerial、NumPy、PyOpenGL</li>
</ul>

<h3>技术架构</h3>
<ul>
<li>UI框架：PyQt5</li>
<li>3D渲染：OpenGL</li>
<li>串口通信：PySerial 异步模式</li>
<li>数据总线：单例模式 DataBus</li>
<li>配置持久化：JSON 文件</li>
</ul>
        '''
    },
    'quickstart': {
        'title': '快速开始',
        'content': '''
<h2>快速开始指南</h2>

<h3>第一步：连接串口</h3>
<ol>
<li>将设备通过 USB 转串口线连接到电脑</li>
<li>在工具栏或串口配置区点击「刷新」扫描串口</li>
<li>选择正确的串口号和波特率</li>
<li>点击「打开串口」按钮</li>
<li>状态栏显示绿色连接状态即为成功</li>
</ol>

<h3>第二步：切换工作模式</h3>
<p>软件提供两种工作模式，可随时切换：</p>
<ul>
<li><b>🎮 3D云台模式</b>：用于舵机云台的可视化调试</li>
<li><b>📡 串口助手模式</b>：通用串口数据收发与分析</li>
</ul>
<p>切换方式：工具栏点击模式按钮 / 菜单「视图」/ 快捷键 Ctrl+1、Ctrl+2</p>

<h3>第三步：使用工具</h3>
<p>点击顶部「工具」菜单，或工具栏快捷按钮，打开所需工具窗口。</p>
<p>所有工具窗口均为独立非模态窗口，可同时打开多个，自由拖动排列。</p>

<h3>常用快捷键</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>功能</b></td><td><b>快捷键</b></td></tr>
<tr><td>切换3D云台模式</td><td>Ctrl + 1</td></tr>
<tr><td>切换串口助手模式</td><td>Ctrl + 2</td></tr>
<tr><td>打开波形图</td><td>Ctrl + W</td></tr>
<tr><td>打开Modbus</td><td>Ctrl + M</td></tr>
<tr><td>打开CRC计算</td><td>Ctrl + Shift + C</td></tr>
<tr><td>打开HEX转换</td><td>Ctrl + H</td></tr>
<tr><td>打开协议解析</td><td>Ctrl + P</td></tr>
<tr><td>打开快捷命令</td><td>Ctrl + K</td></tr>
<tr><td>打开发送历史</td><td>Ctrl + L</td></tr>
<tr><td>打开数据统计</td><td>Ctrl + T</td></tr>
<tr><td>打开设置</td><td>Ctrl + ,</td></tr>
<tr><td>退出程序</td><td>Ctrl + Q</td></tr>
</table>
        '''
    },
    'gimbal': {
        'title': '3D云台调试模式',
        'content': '''
<h2>3D舵机云台调试模式</h2>
<p>提供可视化的双轴舵机云台调试界面，支持3D模型导入与自动分析。</p>

<h3>串口配置区</h3>
<ul>
<li><b>端口选择</b>：下拉选择可用串口，支持手动刷新</li>
<li><b>波特率</b>：支持标准波特率及自定义输入</li>
<li><b>数据位 / 停止位 / 校验位</b>：标准串口参数配置</li>
<li><b>流控</b>：RTS/CTS、DTR/DSR 硬件流控</li>
<li><b>发送模式</b>：文本 / HEX 两种发送格式</li>
<li><b>编码选择</b>：UTF-8 / GBK / GB2312 / GB18030 / ASCII 等</li>
<li><b>接收模式</b>：文本 / HEX 两种显示格式</li>
</ul>

<h3>3D视图区</h3>
<ul>
<li>实时显示云台3D模型</li>
<li>鼠标拖动可旋转视角</li>
<li>滚轮缩放视图</li>
<li>Pan / Tilt 角度实时联动</li>
</ul>

<h3>舵机控制区</h3>
<ul>
<li><b>Pan 轴控制</b>：水平旋转，滑块 + 数字输入框联动</li>
<li><b>Tilt 轴控制</b>：俯仰旋转，滑块 + 数字输入框联动</li>
<li><b>协议选择</b>：
  <ul>
  <li>#PAN,TILT\\r\\n - 标准逗号分隔格式</li>
  <li>P{p} T{t}\\r\\n - 前缀式格式</li>
  <li>pan={p},tilt={t}\\r\\n - 键值对格式</li>
  <li>自定义 HEX - 自由定义十六进制协议</li>
  </ul>
</li>
<li><b>步进按钮</b>：±1° / ±5° / ±10° / ±30° 快速微调</li>
<li><b>范围设置</b>（可展开）：
  <ul>
  <li>自定义 Pan / Tilt 的最小和最大角度</li>
  <li>点击「应用范围」生效</li>
  <li>点击「重置默认」恢复出厂范围</li>
  <li>导入3D模型时可自动调整范围</li>
  </ul>
</li>
<li><b>归零按钮</b>：一键回到中心位置（Pan=0°, Tilt=90°）</li>
</ul>

<h3>快捷预设</h3>
<p>提供 8 个常用视角预设按钮，一键跳转：</p>
<ul>
<li>中心、左看、右看、上看、下看</li>
<li>左上看、右上看、扫地模式</li>
</ul>

<h3>3D模型导入</h3>
<ul>
<li><b>支持格式</b>：OBJ、STL（二进制/ASCII）</li>
<li><b>导入步骤</b>：
  <ol>
  <li>点击「导入模型」选择文件</li>
  <li>软件自动分析模型尺寸、顶点数、面数</li>
  <li>自动计算推荐的舵机运动范围</li>
  <li>勾选「自动调整舵机范围」可一键应用</li>
  <li>3D视图中显示导入的模型</li>
  </ol>
</li>
<li><b>模型信息</b>：显示顶点数、面数、XYZ尺寸、推荐高度</li>
<li><b>清除模型</b>：一键移除导入的外部模型</li>
</ul>

<h3>数据收发区</h3>
<ul>
<li>实时显示串口收发数据</li>
<li>支持文本/HEX 切换显示</li>
<li>手动发送命令测试</li>
<li>TX/RX 字节计数</li>
</ul>
        '''
    },
    'terminal': {
        'title': '高级串口助手模式',
        'content': '''
<h2>高级串口助手模式</h2>
<p>功能丰富的通用串口调试工具，适用于各种串口设备调试场景。</p>

<h3>串口配置</h3>
<ul>
<li><b>端口</b>：自动扫描，支持刷新</li>
<li><b>波特率</b>：300 ~ 921600，支持自定义</li>
<li><b>数据位</b>：5 / 6 / 7 / 8</li>
<li><b>停止位</b>：1 / 1.5 / 2</li>
<li><b>校验位</b>：无 / 奇 / 偶 / 标记 / 空格</li>
<li><b>流控</b>：无 / 硬件 RTS/CTS / 软件 XON/XOFF</li>
<li><b>DTR / RTS</b>：独立控制电平输出</li>
</ul>

<h3>接收区功能</h3>
<ul>
<li><b>暂停显示</b>：暂停屏幕刷新，数据仍后台接收</li>
<li><b>显示发送</b>：在接收区同时显示发送的数据</li>
<li><b>行号显示</b>：每行数据前显示序号</li>
<li><b>时间戳</b>：每行数据前显示精确到毫秒的时间戳</li>
<li><b>编码选择</b>：UTF-8 / GBK / GB2312 / GB18030 / ASCII / ISO-8859-1 / Big5</li>
<li><b>查找功能</b>：在接收数据中搜索关键词</li>
<li><b>清空</b>：一键清空接收缓冲区显示</li>
<li><b>保存</b>：将接收数据保存为文本文件</li>
<li><b>自动滚动</b>：新数据到达时自动滚动到底部</li>
<li><b>最大行数限制</b>：防止内存溢出，默认 5000 行</li>
</ul>

<h3>发送区功能</h3>
<ul>
<li><b>文本 / HEX 切换</b>：两种发送输入模式</li>
<li><b>换行符</b>：\\r\\n / \\n / \\r / 无 可选</li>
<li><b>定时发送</b>：按设定周期自动重复发送</li>
<li><b>递增发送</b>：每次发送自动追加递增的数字</li>
<li><b>CRC 校验</b>：自动追加 CRC 校验码（支持多种算法）</li>
<li><b>发送按钮</b>：手动触发发送</li>
</ul>

<h3>快捷命令（Macros）</h3>
<ul>
<li>管理常用命令，一键快速发送</li>
<li>支持分组管理</li>
<li>可配置发送前是否追加换行符</li>
<li>双击即可发送</li>
<li>详细编辑请打开「快捷命令管理」工具</li>
</ul>

<h3>发送历史</h3>
<ul>
<li>自动记录已发送的命令</li>
<li>可快速重发历史命令</li>
<li>支持清空历史记录</li>
</ul>

<h3>状态栏信息</h3>
<ul>
<li>串口连接状态实时显示</li>
<li>RX / TX 字节计数（自动单位换算）</li>
<li>当前工作模式显示</li>
<li>软件版本号</li>
</ul>
        '''
    },
    'tools': {
        'title': '工具大全',
        'content': '''
<h2>独立工具窗口大全</h2>
<p>软件提供 16 个独立工具窗口，均可从「工具」菜单或工具栏打开。</p>
<p>所有工具均为非模态窗口，可同时打开多个，自由排列。</p>

<h3>数据可视化类</h3>
<ul>
<li><b>📊 实时波形图</b> - 多通道数据实时波形显示</li>
<li><b>📈 数据统计</b> - 收发数据量、速率等统计</li>
<li><b>👁 串口监听器</b> - 监听串口总线数据</li>
</ul>

<h3>协议分析类</h3>
<ul>
<li><b>🔌 Modbus RTU 模拟器</b> - Modbus 主站/从站模拟</li>
<li><b>📋 协议解析器</b> - 自定义协议格式解析</li>
<li><b>🧮 CRC / 校验计算器</b> - 多种校验算法计算</li>
</ul>

<h3>数据转换类</h3>
<ul>
<li><b>🔄 HEX / 文本 转换</b> - 十六进制与文本互转</li>
<li><b>🔍 正则测试器</b> - 正则表达式调试工具</li>
<li><b>🎨 颜色拾取器</b> - 颜色值获取与转换</li>
</ul>

<h3>命令管理类</h3>
<ul>
<li><b>⚡ 快捷命令管理</b> - 宏命令编辑与分组管理</li>
<li><b>📜 发送历史</b> - 历史发送记录浏览与重发</li>
<li><b>🤖 自动回复</b> - 收到指定数据自动回复</li>
</ul>

<h3>系统工具类</h3>
<ul>
<li><b>💻 终端模式</b> - 纯终端交互界面</li>
<li><b>💾 数据记录器</b> - 数据持久化记录</li>
<li><b>🎛 控制面板</b> - 高级串口参数控制</li>
<li><b>⚙ 设置</b> - 全局参数配置</li>
</ul>

<p>详细说明请查看左侧各工具的独立文档页。</p>
        '''
    },
    'tool_waveform': {
        'title': '📊 实时波形图',
        'content': '''
<h2>实时波形图工具</h2>
<p>基于纯 QPainter 绘制的专业级示波器工具，支持多通道数据实时显示、FFT 频谱分析、触发模式、游标测量等功能。</p>

<h3>功能特性</h3>
<ul>
<li><b>多通道支持</b>：最多 8 通道同时显示，可独立开关每个通道</li>
<li><b>自动数据解析</b>：自动识别逗号、空格、Tab、分号分隔的数值数据</li>
<li><b>双模式输入</b>：支持文本行模式和二进制字节模式</li>
<li><b>FFT 频谱分析</b>：实时频域分析，显示峰值频率（需 numpy 库）</li>
<li><b>游标测量</b>：双通道游标，测量采样点数差和时间差</li>
<li><b>触发模式</b>：支持自动、上升沿、下降沿三种触发方式</li>
<li><b>自动量程</b>：Y轴自动适应数据范围，也可手动锁定</li>
<li><b>数据导出</b>：一键导出波形数据为 CSV 格式</li>
<li><b>波形暂停</b>：冻结波形便于观察分析</li>
<li><b>实时采样率</b>：自动计算并显示当前采样率</li>
</ul>

<h3>界面说明</h3>
<ul>
<li><b>顶部工具栏</b>：通道数设置、缓冲区大小、暂停/清除/导出、游标/FFT开关、触发模式、自动量程</li>
<li><b>通道选择栏</b>：CH1-CH8 复选框，可独立控制每个通道的显示开关，不同颜色区分</li>
<li><b>波形显示区</b>：主波形绘制区域，带网格、坐标轴、图例</li>
<li><b>状态栏</b>：显示当前采样率及各通道实时数值</li>
</ul>

<h3>使用方法</h3>
<ol>
<li>确保串口已连接且设备正在输出数值数据</li>
<li>打开波形图工具（菜单: 工具 → 实时波形图，或快捷键 Ctrl+W）</li>
<li>在顶部工具栏设置通道数量（1-8路）</li>
<li>设置缓冲区大小（采样点数，默认1000）</li>
<li>数据到达后波形将自动显示</li>
<li>勾选「游标」开启测量游标，用鼠标拖动游标线测量</li>
<li>勾选「FFT」切换到频谱分析模式</li>
<li>选择触发模式：自动/上升沿/下降沿</li>
<li>点击「导出CSV」保存当前波形数据</li>
</ol>

<h3>通道颜色</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>通道</b></td><td><b>颜色</b></td><td><b>通道</b></td><td><b>颜色</b></td></tr>
<tr><td>CH1</td><td style="color:#3B82F6;">蓝色</td><td>CH5</td><td style="color:#8B5CF6;">紫色</td></tr>
<tr><td>CH2</td><td style="color:#EF4444;">红色</td><td>CH6</td><td style="color:#EC4899;">粉色</td></tr>
<tr><td>CH3</td><td style="color:#22C55E;">绿色</td><td>CH7</td><td style="color:#0EA5E9;">天蓝</td></tr>
<tr><td>CH4</td><td style="color:#F97316;">橙色</td><td>CH8</td><td style="color:#EAB308;">黄色</td></tr>
</table>

<h3>数据格式要求</h3>
<ul>
<li><b>文本模式</b>：每行一帧数据，数值之间用逗号、空格、Tab或分号分隔</li>
<li><b>示例</b>：<code>12.5 34.2 -8.7 102.3</code> 或 <code>1.23,4.56,7.89</code></li>
<li><b>二进制模式</b>：每个字节作为一个通道的数值（0-255）</li>
</ul>
        '''
    },
    'tool_modbus': {
        'title': '🔌 Modbus RTU 工具',
        'content': '''
<h2>Modbus RTU 工具</h2>
<p>基于串口的 Modbus RTU 主站调试工具，支持寄存器读写、轮询监控、日志记录等功能。</p>

<h3>功能特性</h3>
<ul>
<li><b>主站功能</b>：主动发送 Modbus RTU 请求，解析从站响应</li>
<li><b>5种功能码支持</b>：
  <ul>
  <li>0x01 - 读线圈状态 (Read Coils)</li>
  <li>0x02 - 读离散输入 (Read Discrete Inputs)</li>
  <li>0x03 - 读保持寄存器 (Read Holding Registers)</li>
  <li>0x04 - 读输入寄存器 (Read Input Registers)</li>
  <li>0x06 - 写单个寄存器 (Write Single Register)</li>
  </ul>
</li>
<li><b>轮询模式</b>：可设置间隔时间自动循环读取</li>
<li><b>结果表格</b>：以表格形式显示寄存器地址、十进制值、十六进制值</li>
<li><b>实时日志</b>：带时间戳的通信日志，彩色区分不同级别信息</li>
<li><b>CRC16 校验</b>：自动计算和验证 Modbus CRC16</li>
<li><b>异常码解析</b>：自动识别并显示 Modbus 异常码含义</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>顶部工具栏</b>：读取/写入按钮、轮询开关、轮询间隔设置</li>
<li><b>左侧配置区</b>：从机地址、功能码选择、寄存器地址、数量/写入值</li>
<li><b>右侧结果区</b>：三列表格（地址 / 十进制 / 十六进制）显示读取结果</li>
<li><b>底部日志区</b>：显示通信过程、发送数据、接收数据、错误信息</li>
</ul>

<h3>使用方法 - 读取寄存器</h3>
<ol>
<li>确保串口已连接（主窗口中打开串口）</li>
<li>打开 Modbus RTU 工具（Ctrl+M）</li>
<li>设置从机地址（1-247，默认1）</li>
<li>在功能码下拉框选择读取类型（0x03读保持寄存器等）</li>
<li>输入起始寄存器地址（0-65535）</li>
<li>输入读取数量（1-125）</li>
<li>点击「读取」按钮发送请求</li>
<li>右侧结果表格显示解析后的寄存器值</li>
<li>底部日志区显示详细通信过程</li>
</ol>

<h3>使用方法 - 写入寄存器</h3>
<ol>
<li>功能码选择「0x06 写单寄存器」</li>
<li>设置从机地址和寄存器地址</li>
<li>在「写入值」输入框输入要写入的数值（0-65535）</li>
<li>点击「写入」按钮</li>
<li>日志区显示写入结果</li>
</ol>

<h3>使用方法 - 轮询模式</h3>
<ol>
<li>配置好读取参数（从机地址、功能码、地址、数量）</li>
<li>勾选「轮询」复选框</li>
<li>设置轮询间隔（100ms - 60000ms）</li>
<li>工具将按设定周期自动发送读取请求</li>
<li>结果表格实时更新最新数据</li>
<li>再次勾选「轮询」即可停止</li>
</ol>

<h3>异常码说明</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>异常码</b></td><td><b>含义</b></td></tr>
<tr><td>0x01</td><td>非法功能码</td></tr>
<tr><td>0x02</td><td>非法数据地址</td></tr>
<tr><td>0x03</td><td>非法数据值</td></tr>
<tr><td>0x04</td><td>从站设备故障</td></tr>
<tr><td>0x05</td><td>确认</td></tr>
<tr><td>0x06</td><td>从站设备忙</td></tr>
<tr><td>0x07</td><td>否定确认</td></tr>
<tr><td>0x08</td><td>存储器奇偶校验错误</td></tr>
</table>
        '''
    },
    'tool_crc': {
        'title': '🧮 CRC / 校验计算器',
        'content': '''
<h2>CRC / 校验计算器</h2>
<p>专业的校验码计算工具，支持多种 CRC 算法和校验和计算，提供校验验证功能。</p>

<h3>功能特性</h3>
<ul>
<li><b>多种校验算法</b>：支持 CRC8、CRC16-CCITT、CRC16-MODBUS、CRC32、Sum8、Sum16、XOR8 等</li>
<li><b>HEX 输入</b>：支持空格分隔的十六进制数据输入</li>
<li><b>详细结果输出</b>：显示十六进制、十进制、高低字节、字节序等多种格式</li>
<li><b>结果追加</b>：一键将校验值追加到原始数据末尾</li>
<li><b>一键复制</b>：支持复制 HEX、复制十进制、复制全部结果</li>
<li><b>校验验证</b>：验证带校验值的数据是否正确</li>
<li><b>常用预设</b>：内置 Modbus 常用命令等预设数据</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>左侧输入区</b>：HEX 数据输入框、算法选择、计算/追加/清空按钮</li>
<li><b>左侧预设区</b>：常用数据预设按钮，一键填入</li>
<li><b>右侧结果区</b>：计算结果显示、三种复制按钮</li>
<li><b>底部验证区</b>：数据+校验值的验证功能</li>
</ul>

<h3>使用方法 - 计算校验</h3>
<ol>
<li>打开 CRC/校验计算器（Ctrl+Shift+C）</li>
<li>在「输入」框中输入 HEX 数据（空格分隔，如: 01 03 00 00 00 0A）</li>
<li>在「算法」下拉框选择校验算法</li>
<li>点击「计算」按钮</li>
<li>右侧「计算结果」区显示详细结果</li>
<li>点击「复制 HEX」/「复制十进制」/「复制全部」复制结果</li>
</ol>

<h3>使用方法 - 追加校验值</h3>
<ol>
<li>输入待发送的数据并计算校验值</li>
<li>点击「追加结果」按钮</li>
<li>输入框中会自动追加校验字节</li>
<li>自动重新计算（可直接复制完整帧数据）</li>
</ol>

<h3>使用方法 - 校验验证</h3>
<ol>
<li>在底部「校验验证」区输入完整数据（含校验值）</li>
<li>选择对应的校验算法</li>
<li>点击「验证」按钮</li>
<li>显示「✓ 校验正确」或「✗ 错误」及期望/实际值对比</li>
</ol>

<h3>支持的算法</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>算法</b></td><td><b>长度</b></td><td><b>说明</b></td></tr>
<tr><td>CRC8</td><td>8位</td><td>8位循环冗余校验</td></tr>
<tr><td>CRC16-CCITT</td><td>16位</td><td>CCITT 标准 CRC16</td></tr>
<tr><td>CRC16-MODBUS</td><td>16位</td><td>Modbus 标准 CRC16</td></tr>
<tr><td>CRC32</td><td>32位</td><td>32位循环冗余校验</td></tr>
<tr><td>Sum8</td><td>8位</td><td>8位累加和</td></tr>
<tr><td>Sum16</td><td>16位</td><td>16位累加和</td></tr>
<tr><td>XOR8</td><td>8位</td><td>8位异或校验（BCC）</td></tr>
</table>

<h3>常用预设数据</h3>
<ul>
<li>Modbus 读保持寄存器 (01 03 00 00 00 0A)</li>
<li>Modbus 读输入寄存器 (02 04 00 00 00 04)</li>
<li>简单测试 (01 02 03 04 05 06 07 08)</li>
<li>全零测试 / 全FF测试</li>
</ul>
        '''
    },
    'tool_hex': {
        'title': '🔄 HEX / 文本 转换',
        'content': '''
<h2>HEX / 文本 / Base64 转换工具</h2>
<p>多功能数据格式转换工具，支持十六进制与文本互转、Base64 编解码，支持多种字符编码。</p>

<h3>功能特性</h3>
<ul>
<li><b>文本 → HEX</b>：字符串转换为十六进制表示，空格分隔字节</li>
<li><b>HEX → 文本</b>：十六进制数据转换为可读文本</li>
<li><b>文本 → Base64</b>：文本字符串 Base64 编码</li>
<li><b>Base64 → 文本</b>：Base64 字符串解码为文本</li>
<li><b>多编码支持</b>：UTF-8、GBK、ASCII、GB2312、ISO-8859-1</li>
<li><b>一键交换</b>：快速交换输入输出内容并反转转换方向</li>
<li><b>单例模式</b>：全局唯一实例，数据不丢失</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>顶部设置区</b>：转换方向选择、字符编码选择</li>
<li><b>左侧输入区</b>：待转换的源数据输入框</li>
<li><b>右侧输出区</b>：转换结果显示（只读）</li>
<li><b>底部按钮区</b>：交换输入输出、清空、转换按钮</li>
</ul>

<h3>使用方法</h3>
<ol>
<li>打开 HEX 转换工具（Ctrl+H）</li>
<li>在「转换方向」下拉框选择转换类型：
  <ul>
  <li>文本 → HEX</li>
  <li>HEX → 文本</li>
  <li>文本 → Base64</li>
  <li>Base64 → 文本</li>
  </ul>
</li>
<li>在「字符编码」下拉框选择编码格式</li>
<li>在左侧「输入」框输入源数据</li>
<li>点击「转换」按钮</li>
<li>右侧「输出」框显示转换结果</li>
<li>点击「⇄ 交换输入输出」可快速反向转换</li>
</ol>

<h3>支持的 HEX 输入格式</h3>
<ul>
<li>纯十六进制字符：<code>48656C6C6F</code></li>
<li>空格分隔：<code>48 65 6C 6C 6F</code></li>
<li>换行分隔的多行数据</li>
<li>注意：奇数长度会自动截断最后一个字符</li>
</ul>

<h3>字符编码说明</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>编码</b></td><td><b>适用场景</b></td></tr>
<tr><td>UTF-8</td><td>通用 Unicode，支持中英文及各国文字</td></tr>
<tr><td>GBK</td><td>简体中文 Windows 系统常用编码</td></tr>
<tr><td>GB2312</td><td>早期简体中文编码</td></tr>
<tr><td>ASCII</td><td>纯英文/数字场景</td></tr>
<tr><td>ISO-8859-1</td><td>西欧字符，单字节全覆盖</td></tr>
</table>
        '''
    },
    'tool_protocol': {
        'title': '📋 协议解析器',
        'content': '''
<h2>协议解析器工具</h2>
<p>自定义协议格式解析工具，支持帧头+长度+数据+校验的自定义协议，可实时监听串口数据并自动解析。</p>

<h3>功能特性</h3>
<ul>
<li><b>可视化协议编辑</b>：图形化界面定义协议帧格式</li>
<li><b>7种字段类型</b>：u8、i8、u16、i16、u32、i32、float</li>
<li><b>双字节序</b>：支持大端（BE）和小端（LE）</li>
<li><b>4种长度模式</b>：
  <ul>
  <li>长度 = 数据域长度</li>
  <li>长度 = 数据域 + 校验</li>
  <li>长度 = 整帧长度</li>
  <li>长度 = 从长度字段后到帧尾</li>
  </ul>
</li>
<li><b>5种校验算法</b>：CRC16 Modbus、CRC16 CCITT、Sum8、XOR8、无校验</li>
<li><b>实时监听模式</b>：自动监听串口数据，实时解析并显示</li>
<li><b>离线解析模式</b>：手动输入 HEX 数据进行解析</li>
<li><b>协议模板管理</b>：保存/加载多个协议配置模板</li>
<li><b>原始数据日志</b>：记录所有接收的原始数据</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>顶部工具栏</b>：模板选择/保存/删除、实时监听开关、清空结果、重置缓冲区</li>
<li><b>左侧配置区</b>：
  <ul>
  <li>帧头配置：设置帧头字节（HEX格式）</li>
  <li>长度字段：偏移位置、字节数、长度含义</li>
  <li>校验配置：校验算法、字节序</li>
  <li>数据字段：字段名、偏移、类型表格，支持增删改排序</li>
  <li>「应用配置」按钮</li>
  </ul>
</li>
<li><b>右侧结果区</b>：
  <ul>
  <li>「实时结果」Tab：显示最新解析的一帧数据</li>
  <li>「离线解析」Tab：手动输入 HEX 数据进行解析</li>
  </ul>
</li>
<li><b>底部日志区</b>：原始数据接收日志，支持HEX显示、自动滚动</li>
</ul>

<h3>使用方法 - 配置协议</h3>
<ol>
<li>打开协议解析器（Ctrl+P）</li>
<li>在左侧「帧头配置」输入帧头字节（如: AA 55）</li>
<li>在「长度字段」设置：
  <ul>
  <li>偏移位置：长度字段在帧中的起始位置（从0开始）</li>
  <li>字节数：长度字段占用的字节数（1-4）</li>
  <li>长度含义：长度字段表示的数据范围</li>
  </ul>
</li>
<li>在「校验配置」选择校验算法和字节序</li>
<li>在「数据字段」表格添加字段：
  <ul>
  <li>点击「添加」按钮新增一行</li>
  <li>填写字段名、偏移（相对数据域起始）、类型</li>
  <li>使用「上移/下移」调整顺序</li>
  </ul>
</li>
<li>点击「应用配置」按钮使配置生效</li>
</ol>

<h3>使用方法 - 实时监听解析</h3>
<ol>
<li>确保主窗口已打开串口</li>
<li>配置好协议格式并应用</li>
<li>勾选顶部工具栏的「实时监听」复选框</li>
<li>串口收到的数据将自动送入解析器</li>
<li>解析成功的帧显示在「实时结果」表格中</li>
<li>底部日志区显示所有接收到的原始数据</li>
<li>取消勾选「实时监听」即可停止</li>
</ol>

<h3>使用方法 - 离线解析</h3>
<ol>
<li>切换到右侧「离线解析」Tab</li>
<li>配置好协议格式</li>
<li>在输入框中粘贴 HEX 数据（空格分隔）</li>
<li>点击「解析」按钮</li>
<li>下方表格显示解析结果</li>
<li>解析成功/失败状态显示在信息栏</li>
</ol>

<h3>使用方法 - 协议模板</h3>
<ol>
<li>配置好协议后，点击工具栏「保存模板」</li>
<li>输入模板名称，确定保存</li>
<li>以后可在模板下拉框直接选择加载</li>
<li>点击「删除模板」删除当前选中的模板</li>
</ol>

<h3>字段类型说明</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>类型</b></td><td><b>字节数</b></td><td><b>说明</b></td></tr>
<tr><td>u8</td><td>1</td><td>无符号8位整数 (0-255)</td></tr>
<tr><td>i8</td><td>1</td><td>有符号8位整数 (-128~127)</td></tr>
<tr><td>u16</td><td>2</td><td>无符号16位整数 (0-65535)</td></tr>
<tr><td>i16</td><td>2</td><td>有符号16位整数</td></tr>
<tr><td>u32</td><td>4</td><td>无符号32位整数</td></tr>
<tr><td>i32</td><td>4</td><td>有符号32位整数</td></tr>
<tr><td>float</td><td>4</td><td>单精度浮点数 (IEEE754)</td></tr>
</table>
        '''
    },
    'tool_macro': {
        'title': '⚡ 快捷命令管理',
        'content': '''
<h2>快捷命令管理器</h2>
<p>快速发送常用命令的管理工具，支持分组管理、批量导入导出，双击即可发送。</p>

<h3>功能特性</h3>
<ul>
<li><b>分组管理</b>：可创建多个分组，分类管理不同用途的命令</li>
<li><b>HEX/文本双模式</b>：每个命令独立设置发送格式</li>
<li><b>快捷键</b>：F1-F12 可绑定常用命令一键发送</li>
<li><b>双击发送</b>：在列表中双击命令立即发送到串口</li>
<li><b>增删改操作</b>：添加、编辑、删除命令</li>
<li><b>分组管理</b>：添加、重命名、删除分组</li>
<li><b>导入导出</b>：JSON 格式导入导出配置，方便备份共享</li>
<li><b>自动计数</b>：显示当前分组命令数量和总数量</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>左侧分组列表</b>：显示所有分组，点击切换</li>
<li><b>右侧命令列表</b>：当前分组的命令，显示名称、内容、格式</li>
<li><b>底部操作区</b>：添加/编辑/删除命令、导入导出按钮</li>
</ul>

<h3>使用方法 - 添加命令</h3>
<ol>
<li>打开快捷命令管理器（Ctrl+G）</li>
<li>选择要添加命令的分组</li>
<li>点击「添加」按钮</li>
<li>在对话框中填写：
  <ul>
  <li>命令名称：便于识别的描述</li>
  <li>命令内容：要发送的数据</li>
  <li>格式：HEX 或 文本</li>
  <li>快捷键：可选 F1-F12</li>
  </ul>
</li>
<li>点击「确定」保存</li>
</ol>

<h3>使用方法 - 发送命令</h3>
<ol>
<li>确保串口已打开</li>
<li>在列表中找到要发送的命令</li>
<li>双击该命令行立即发送</li>
<li>或选中后按发送快捷键</li>
<li>也可在主界面快捷键按钮区点击发送</li>
</ol>

<h3>使用方法 - 分组管理</h3>
<ol>
<li>右键点击左侧分组列表空白处</li>
<li>选择「添加分组」，输入分组名称</li>
<li>右键点击某个分组可重命名或删除</li>
<li>删除分组会同时删除组内所有命令</li>
</ol>

<h3>使用方法 - 导入导出</h3>
<ol>
<li>点击「导出」按钮</li>
<li>选择保存位置和文件名（JSON 格式）</li>
<li>所有分组和命令将被保存</li>
<li>点击「导入」按钮选择 JSON 文件</li>
<li>确认后导入所有配置</li>
</ol>

<h3>HEX 格式说明</h3>
<ul>
<li>空格分隔的十六进制字节：<code>01 03 00 00 00 0A C5 CD</code></li>
<li>支持大小写混合</li>
<li>非 HEX 字符会被自动忽略</li>
</ul>
        '''
    },
    'tool_history': {
        'title': '📜 发送历史',
        'content': '''
<h2>发送历史记录工具</h2>
<p>记录所有通过串口发送的数据，支持快速重发、搜索过滤、清空管理。</p>

<h3>功能特性</h3>
<ul>
<li><b>自动记录</b>：所有发送的数据自动记录到历史列表</li>
<li><b>实时显示</b>：按时间倒序排列，最新发送的在最上方</li>
<li><b>双击重发</b>：双击历史记录立即重新发送</li>
<li><b>发送格式</b>：显示每条记录的发送方式（文本/HEX）</li>
<li><b>时间戳</b>：显示每条记录的发送时间</li>
<li><b>搜索过滤</b>：按内容关键词搜索历史记录</li>
<li><b>清空历史</b>：一键清除所有历史记录</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>顶部工具栏</b>：搜索框、清空按钮</li>
<li><b>主列表区</b>：历史记录列表，显示序号、时间、格式、内容</li>
</ul>

<h3>使用方法</h3>
<ol>
<li>打开发送历史工具（Ctrl+L）</li>
<li>列表显示所有已发送的命令，最新的在最上方</li>
<li>在搜索框输入关键词可过滤显示</li>
<li>双击任一条目可立即重新发送</li>
<li>点击「清空」按钮清除所有记录</li>
</ol>

<h3>使用场景</h3>
<ul>
<li>快速重发最近使用过的命令</li>
<li>查看发送记录核对调试过程</li>
<li>搜索历史命令进行复用</li>
</ul>
        '''
    },
    'tool_datalogger': {
        'title': '💾 数据记录器',
        'content': '''
<h2>数据记录仪工具</h2>
<p>将串口接收的数据持久化记录到文件，支持二进制和文本格式，方便后续分析与回放。</p>

<h3>功能特性</h3>
<ul>
<li><b>多种记录格式</b>：
  <ul>
  <li>纯文本格式 (.txt) - 原始文本数据</li>
  <li>带时间戳文本 - 每行前缀时间戳</li>
  <li>HEX 格式 (.txt) - 十六进制字节记录</li>
  <li>CSV 表格格式 (.csv) - 可直接用 Excel 打开</li>
  <li>二进制格式 (.bin) - 原始二进制数据</li>
  </ul>
</li>
<li><b>数据回放</b>：从文件回放记录的数据到串口，支持速度调节</li>
<li><b>自动文件命名</b>：按日期时间自动生成文件名</li>
<li><b>实时统计</b>：显示已记录字节数、行数、运行时间</li>
<li><b>一键启停</b>：开始/停止记录简单直观</li>
<li><b>文件路径选择</b>：自定义记录文件保存位置</li>
<li><b>接收/发送选择</b>：可选择记录接收、发送或全部数据</li>
</ul>

<h3>界面布局</h3>
<ul>
<li><b>记录设置区</b>：文件格式选择、记录内容选择、文件路径、开始/停止按钮</li>
<li><b>状态统计区</b>：运行状态、记录字节数、记录行数、运行时间</li>
<li><b>回放控制区</b>：文件选择、速度调节、播放/暂停/停止按钮</li>
</ul>

<h3>使用方法 - 记录数据</h3>
<ol>
<li>打开数据记录仪工具</li>
<li>在「文件格式」下拉框选择记录格式</li>
<li>选择记录内容：仅接收、仅发送、全部</li>
<li>点击「浏览」选择保存路径和文件名</li>
<li>点击「开始记录」按钮启动记录</li>
<li>按钮变为「停止记录」，状态显示为「● 正在记录」</li>
<li>数据到达时自动写入文件</li>
<li>点击「停止记录」结束记录</li>
</ol>

<h3>使用方法 - 回放数据</h3>
<ol>
<li>切换到「回放」Tab</li>
<li>点击「打开文件」选择要回放的记录文件</li>
<li>选择回放速度（0.25x ~ 8x）</li>
<li>点击「播放」按钮开始回放</li>
<li>数据将按原始时间间隔发送到串口</li>
<li>可随时暂停或停止回放</li>
</ol>

<h3>记录格式说明</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>格式</b></td><td><b>扩展名</b></td><td><b>说明</b></td></tr>
<tr><td>纯文本</td><td>.txt</td><td>直接保存原始数据，每行一个数据包</td></tr>
<tr><td>带时间戳</td><td>.txt</td><td>每行前缀 [HH:MM:SS.mmm] 时间戳</td></tr>
<tr><td>HEX 格式</td><td>.txt</td><td>每个字节以两位十六进制表示，空格分隔</td></tr>
<tr><td>CSV 格式</td><td>.csv</td><td>表格形式，包含时间、方向、长度、内容</td></tr>
<tr><td>二进制</td><td>.bin</td><td>原始二进制流，体积最小，便于程序处理</td></tr>
</table>

<h3>使用场景</h3>
<ul>
<li>长时间测试数据记录</li>
<li>设备运行日志保存</li>
<li>实验数据采集与分析</li>
<li>故障诊断数据捕获</li>
<li>数据回放与复现</li>
</ul>
        '''
    },
    'tool_settings': {
        'title': '⚙ 设置',
        'content': '''
<h2>系统设置</h2>
<p>全局参数配置中心，包含界面主题、串口参数、显示设置等多项配置。</p>

<h3>功能特性</h3>
<ul>
<li><b>双主题切换</b>：浅色主题（工程师明亮）/ 深色主题（深空玻璃）</li>
<li><b>语言设置</b>：简体中文 / English</li>
<li><b>串口默认参数</b>：波特率、数据位、停止位、校验位默认值</li>
<li><b>显示设置</b>：接收区最大行数、字体、自动滚动等</li>
<li><b>发送设置</b>：默认发送格式、定时发送间隔等</li>
<li><b>配置导入导出</b>：JSON 格式备份和恢复配置</li>
</ul>

<h3>设置分类</h3>
<ul>
<li><b>通用设置</b>：主题、语言、启动行为</li>
<li><b>串口设置</b>：默认波特率、默认编码、缓冲区大小</li>
<li><b>显示设置</b>：字体、最大行数、时间戳格式、颜色方案</li>
<li><b>发送设置</b>：默认格式、回车符、历史记录数量</li>
<li><b>高级设置</b>：自动重连、数据保存路径等</li>
</ul>

<h3>使用方法</h3>
<ol>
<li>打开系统设置（菜单: 设置 → 系统设置，或 Ctrl+, ）</li>
<li>左侧选择设置分类</li>
<li>右侧修改对应参数</li>
<li>点击「应用」保存当前设置</li>
<li>点击「确定」保存并关闭</li>
<li>点击「取消」放弃修改</li>
<li>部分设置（如主题）立即生效，部分需重启生效</li>
</ol>

<h3>主题切换</h3>
<ul>
<li><b>工程师明亮</b>：浅色主题，适合白天使用，清晰明亮</li>
<li><b>深空玻璃</b>：深色主题，适合夜间使用，护眼舒适</li>
<li>切换后界面立即更新，无需重启</li>
</ul>

<h3>配置管理</h3>
<ol>
<li>点击「导出配置」按钮</li>
<li>选择保存位置，配置保存为 JSON 文件</li>
<li>点击「导入配置」按钮</li>
<li>选择之前导出的 JSON 文件</li>
<li>确认后所有设置恢复到导出时状态</li>
<li>点击「恢复默认」可重置所有设置为出厂默认</li>
</ol>

<h3>主要设置项说明</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr><td><b>设置项</b></td><td><b>说明</b></td><td><b>默认值</b></td></tr>
<tr><td>主题</td><td>界面外观主题</td><td>工程师明亮</td></tr>
<tr><td>语言</td><td>界面显示语言</td><td>简体中文</td></tr>
<tr><td>默认波特率</td><td>新串口连接的波特率</td><td>115200</td></tr>
<tr><td>默认编码</td><td>文本数据的字符编码</td><td>UTF-8</td></tr>
<tr><td>最大显示行数</td><td>接收区保留的最大行数</td><td>5000</td></tr>
<tr><td>自动滚动</td><td>新数据是否自动滚到底部</td><td>开启</td></tr>
<tr><td>时间戳</td><td>是否显示每行数据的时间</td><td>关闭</td></tr>
</table>
        '''
    },
    'about_author': {
        'title': '👤 作者介绍',
        'content': '''
<h2>关于作者</h2>

<div style="background:#F0F9FF; border-radius:12px; padding:20px; margin:10px 0;">
<h3 style="color:#1E40AF; margin-top:0;">👨‍💻 开发者：Mouse</h3>
<p style="color:#374151; font-size:15px;">
    <b>安徽农业大学</b> · 电子信息工程专业在读
</p>
</div>

<h3>个人简介</h3>
<p>专注于单片机软件开发，熟练掌握 C 语言及 STM32、ESP32 等主流嵌入式平台开发。具备从代码编写、错误分析到简单 PCB 设计的完整项目落地能力。</p>
<p>同时，热衷于探索 AI 辅助编程，能熟练运用 Trae IDE、Claude Code 等前沿 Agent 工具进行 Vibe Coding，实现高效开发。</p>

<h3>🛠️ 技术栈</h3>
<table border="0" cellpadding="8" cellspacing="0" style="width:100%;">
<tr>
<td style="background:#ECFDF5; border-radius:8px; padding:12px; width:50%; vertical-align:top;">
<b style="color:#065F46;">🔧 嵌入式开发</b>
<ul style="margin:8px 0 0 0; padding-left:20px; color:#374151;">
<li>STM32 / 51 单片机</li>
<li>ESP32 / ESP32-S3</li>
<li>MSPM0 / RTOS</li>
<li>基础 PCB 设计</li>
</ul>
</td>
<td style="background:#FEF3C7; border-radius:8px; padding:12px; width:50%; vertical-align:top;">
<b style="color:#92400E;">💻 编程能力</b>
<ul style="margin:8px 0 0 0; padding-left:20px; color:#374151;">
<li>C 语言</li>
<li>代码调试与错误分析</li>
<li>Python 脚本开发</li>
<li>Qt/嵌入式 GUI</li>
</ul>
</td>
</tr>
<tr>
<td colspan="2" style="background:#EDE9FE; border-radius:8px; padding:12px; vertical-align:top;">
<b style="color:#5B21B6;">🤖 AI 赋能开发</b>
<ul style="margin:8px 0 0 0; padding-left:20px; color:#374151;">
<li>熟练使用 Trae IDE / Claude Code / Codex 等 Vibe Coding 工具</li>
<li>探索 AI 辅助编程，提升开发效率</li>
</ul>
</td>
</tr>
</table>

<h3>🚀 项目实战</h3>
<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-top:10px;">
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:14px;">
<b style="color:#2563EB;">🌱 智能大棚控制系统</b>
<p style="color:#64748B; font-size:13px; margin:6px 0 0 0;">基于 STM32 开发</p>
</div>
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:14px;">
<b style="color:#059669;">📷 简易相机开发</b>
<p style="color:#64748B; font-size:13px; margin:6px 0 0 0;">基于 ESP32-S3</p>
</div>
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:14px;">
<b style="color:#DC2626;">🚗 电赛智能小车</b>
<p style="color:#64748B; font-size:13px; margin:6px 0 0 0;">基于 MSPM0-G3507</p>
</div>
</div>

<h3>📬 联系方式</h3>
<div style="background:#F8FAFC; border-radius:8px; padding:16px; margin-top:10px;">
<table border="0" cellpadding="8">
<tr>
<td style="width:100px;"><b>📧 邮箱：</b></td>
<td><a href="mailto:m2627898738@163.com" style="color:#2563EB;">m2627898738@163.com</a></td>
</tr>
<tr>
<td><b>💬 QQ：</b></td>
<td style="color:#374151;">1073197606</td>
</tr>
</table>
</div>

<div style="background:linear-gradient(135deg, #667EEA 0%, #764BA2 100%); color:white; border-radius:8px; padding:16px; margin-top:16px; text-align:center;">
<p style="margin:0; font-size:14px;">
    🎉 <b>用 AI 工具独立开发出多功能高级串口助手</b><br>
    <span style="font-size:12px; opacity:0.9;">充分体现「AI + 嵌入式」的复合能力</span>
</p>
</div>
        '''
    },
    'faq': {
        'title': '常见问题',
        'content': '''
<h2>常见问题 FAQ</h2>

<h3>Q: 为什么找不到串口？</h3>
<p><b>A:</b> 请检查：</p>
<ol>
<li>USB 转串口驱动是否正确安装</li>
<li>设备管理器中是否有 COM 端口</li>
<li>USB 线是否完好、连接是否牢固</li>
<li>点击「刷新」按钮重新扫描</li>
<li>尝试更换 USB 接口或数据线</li>
</ol>

<h3>Q: 串口打开失败怎么办？</h3>
<p><b>A:</b> 常见原因：</p>
<ol>
<li>串口被其他软件占用（关闭其他串口工具）</li>
<li>端口号不存在（确认设备管理器中的端口号）</li>
<li>驱动程序异常（重装驱动）</li>
<li>权限不足（以管理员身份运行）</li>
</ol>

<h3>Q: 接收数据显示乱码？</h3>
<p><b>A:</b> 这是编码不匹配问题：</p>
<ol>
<li>在接收区工具栏的「编码」下拉框中切换</li>
<li>常见设备使用 GBK 编码，可尝试切换到 GBK</li>
<li>如果是二进制数据，请切换到 HEX 显示模式</li>
</ol>

<h3>Q: 3D模型导入后显示不正常？</h3>
<p><b>A:</b> 请确认：</p>
<ol>
<li>文件格式是否为 OBJ 或 STL</li>
<li>STL 文件是否为二进制格式（推荐）</li>
<li>模型文件是否损坏（尝试用其他软件打开验证）</li>
<li>模型尺寸是否过大或过小（自动缩放可能异常）</li>
</ol>

<h3>Q: 工具窗口打开后看不到？</h3>
<p><b>A:</b> 工具窗口为独立窗口，可能：</p>
<ol>
<li>被主窗口遮挡了，移动主窗口看看</li>
<li>在任务栏中可以找到对应窗口</li>
<li>所有工具窗口均为非模态，可自由拖动</li>
</ol>

<h3>Q: 定时发送不生效？</h3>
<p><b>A:</b> 请检查：</p>
<ol>
<li>是否勾选了「定时发送」复选框</li>
<li>时间间隔设置是否合理（建议 ≥ 10ms）</li>
<li>发送内容是否为空</li>
<li>串口是否正常连接</li>
</ol>

<h3>Q: Modbus 通信无响应？</h3>
<p><b>A:</b> 排查步骤：</p>
<ol>
<li>确认从站地址是否正确</li>
<li>确认波特率、数据位、停止位、校验位设置一致</li>
<li>确认接线正确（A-A, B-B，注意 485 信号方向）</li>
<li>用示波器或逻辑分析仪查看总线信号</li>
</ol>

<h3>Q: 如何保存接收的数据？</h3>
<p><b>A:</b> 两种方式：</p>
<ol>
<li>点击接收区「保存」按钮，保存当前显示的内容</li>
<li>使用「数据记录器」工具，边接收边写入文件（推荐）</li>
</ol>

<h3>Q: 配置会丢失吗？</h3>
<p><b>A:</b> 不会。所有配置自动保存在本地 JSON 文件中，下次启动自动恢复。也可以手动导出配置备份。</p>

<h3>Q: 舵机范围如何调整？</h3>
<p><b>A:</b> 在3D云台模式的舵机控制区：</p>
<ol>
<li>点击「▼ 范围设置」展开面板</li>
<li>输入 Pan / Tilt 的最小和最大角度</li>
<li>点击「应用范围」按钮生效</li>
<li>导入3D模型时也可自动调整范围</li>
</ol>
        '''
    },
    'shortcuts': {
        'title': '快捷键大全',
        'content': '''
<h2>快捷键大全</h2>

<h3>模式切换</h3>
<table border="1" cellpadding="8" cellspacing="0">
<tr><td><b>功能</b></td><td><b>快捷键</b></td></tr>
<tr><td>切换到 3D 云台调试模式</td><td>Ctrl + 1</td></tr>
<tr><td>切换到 高级串口助手模式</td><td>Ctrl + 2</td></tr>
</table>

<h3>工具窗口</h3>
<table border="1" cellpadding="8" cellspacing="0">
<tr><td><b>功能</b></td><td><b>快捷键</b></td></tr>
<tr><td>实时波形图</td><td>Ctrl + W</td></tr>
<tr><td>Modbus RTU 模拟器</td><td>Ctrl + M</td></tr>
<tr><td>CRC / 校验计算器</td><td>Ctrl + Shift + C</td></tr>
<tr><td>HEX / 文本 转换</td><td>Ctrl + H</td></tr>
<tr><td>协议解析器</td><td>Ctrl + P</td></tr>
<tr><td>快捷命令管理</td><td>Ctrl + K</td></tr>
<tr><td>发送历史</td><td>Ctrl + L</td></tr>
<tr><td>数据统计</td><td>Ctrl + T</td></tr>
<tr><td>串口监听器</td><td>Ctrl + I</td></tr>
<tr><td>终端模式</td><td>Ctrl + `</td></tr>
<tr><td>正则测试器</td><td>Ctrl + R</td></tr>
<tr><td>设置</td><td>Ctrl + ,</td></tr>
</table>

<h3>通用操作</h3>
<table border="1" cellpadding="8" cellspacing="0">
<tr><td><b>功能</b></td><td><b>快捷键</b></td></tr>
<tr><td>退出程序</td><td>Ctrl + Q</td></tr>
<tr><td>清空接收区</td><td>Ctrl + Shift + X</td></tr>
<tr><td>查找内容</td><td>Ctrl + F</td></tr>
<tr><td>发送数据</td><td>Enter (发送输入框)</td></tr>
</table>

<h3>3D视图操作</h3>
<table border="1" cellpadding="8" cellspacing="0">
<tr><td><b>功能</b></td><td><b>操作</b></td></tr>
<tr><td>旋转视角</td><td>鼠标左键拖动</td></tr>
<tr><td>缩放视图</td><td>鼠标滚轮</td></tr>
<tr><td>平移视图</td><td>鼠标右键拖动 / 中键拖动</td></tr>
<tr><td>重置视角</td><td>双击视图</td></tr>
</table>
        '''
    },
    'about': {
        'title': '关于软件',
        'content': '''
<h2>关于 MHcom v2.0</h2>

<h3>软件信息</h3>
<table border="0" cellpadding="6">
<tr><td><b>软件名称</b></td><td>MHcom - 多功能高级串口助手</td></tr>
<tr><td><b>版本号</b></td><td>v2.0</td></tr>
<tr><td><b>开发语言</b></td><td>Python + PyQt5</td></tr>
<tr><td><b>运行平台</b></td><td>Windows 7 / 10 / 11</td></tr>
</table>

<h3>核心技术栈</h3>
<ul>
<li>UI 框架：PyQt5</li>
<li>3D 渲染：OpenGL / PyOpenGL</li>
<li>串口通信：PySerial</li>
<li>数值计算：NumPy</li>
<li>配置存储：JSON</li>
</ul>

<h3>开源许可</h3>
<p>本软件仅供学习和研发使用。</p>

<h3>反馈与支持</h3>
<p>如遇到问题或有改进建议，欢迎反馈。</p>

<h3>更新日志</h3>
<p><b>v2.0</b></p>
<ul>
<li>全新双模架构：3D云台调试 + 高级串口助手</li>
<li>新增 16+ 独立工具窗口</li>
<li>支持 OBJ / STL 3D模型导入与自动分析</li>
<li>全局数据总线：主窗口与工具实时联动</li>
<li>双主题支持：浅色/深色自由切换</li>
<li>舵机范围可自定义调节</li>
<li>多编码支持：UTF-8 / GBK / GB2312 等</li>
<li>模块化重构：代码结构清晰，便于扩展</li>
</ul>
        '''
    },
}


class HelpDialog(QDialog):
    """帮助对话框 - 左侧导航 + 右侧内容"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('帮助文档 - MHcom v2.0')
        self.resize(1000, 650)
        self.setMinimumSize(QSize(800, 500))

        self._build_ui()
        self._populate_tree()
        self._connect_signals()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel('🔍 搜索:'))
        self.edt_search = QLineEdit()
        self.edt_search.setPlaceholderText('输入关键词搜索帮助内容...')
        self.edt_search.setMaximumWidth(300)
        top_row.addWidget(self.edt_search)
        top_row.addStretch()
        btn_close = QPushButton('关闭')
        btn_close.setMaximumWidth(80)
        btn_close.clicked.connect(self.accept)
        top_row.addWidget(btn_close)
        root.addLayout(top_row)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel('帮助目录')
        self.tree.setMinimumWidth(240)
        self.tree.setMaximumWidth(320)
        splitter.addWidget(self.tree)

        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.StyledPanel)
        cl = QVBoxLayout(content_frame)
        cl.setContentsMargins(12, 8, 12, 8)
        cl.setSpacing(6)

        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet('font-size: 16px; font-weight: 600; color: #1E40AF;')
        cl.addWidget(self.lbl_title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('color: #E5E7EB;')
        cl.addWidget(line)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        font = QFont('Microsoft YaHei UI', 10)
        self.browser.setFont(font)
        cl.addWidget(self.browser, 1)

        splitter.addWidget(content_frame)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

    def _populate_tree(self):
        top_items = [
            ('overview', '📖 软件概述'),
            ('quickstart', '🚀 快速开始'),
            ('gimbal', '🎮 3D云台调试模式'),
            ('terminal', '📡 高级串口助手模式'),
        ]

        tools_parent = QTreeWidgetItem(['🛠 工具大全'])
        tools_parent.setData(0, Qt.UserRole, 'tools')
        tools_children = [
            ('tool_waveform', '📊 实时波形图'),
            ('tool_modbus', '🔌 Modbus RTU 模拟器'),
            ('tool_crc', '🧮 CRC / 校验计算器'),
            ('tool_hex', '🔄 HEX / 文本 转换'),
            ('tool_protocol', '📋 协议解析器'),
            ('tool_macro', '⚡ 快捷命令管理'),
            ('tool_history', '📜 发送历史'),
            ('tool_datalogger', '💾 数据记录器'),
            ('tool_settings', '⚙ 设置'),
        ]

        bottom_items = [
            ('shortcuts', '⌨ 快捷键大全'),
            ('about_author', '👤 作者介绍'),
            ('faq', '❓ 常见问题'),
            ('about', 'ℹ 关于软件'),
        ]

        for key, title in top_items:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.UserRole, key)
            self.tree.addTopLevelItem(item)

        self.tree.addTopLevelItem(tools_parent)
        for key, title in tools_children:
            child = QTreeWidgetItem([title])
            child.setData(0, Qt.UserRole, key)
            tools_parent.addChild(child)

        for key, title in bottom_items:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.UserRole, key)
            self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def _connect_signals(self):
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.edt_search.textChanged.connect(self._on_search)

    def _on_item_clicked(self, item, column):
        key = item.data(0, Qt.UserRole)
        if key and key in HELP_CONTENT:
            self._show_content(key)

    def _show_content(self, key: str):
        doc = HELP_CONTENT.get(key)
        if not doc:
            return
        self.lbl_title.setText(doc['title'])
        self.browser.setHtml(doc['content'])
        self.browser.moveCursor(QTextCursor.Start)

    def _on_search(self, text: str):
        if not text.strip():
            for i in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(i).setHidden(False)
                for j in range(self.tree.topLevelItem(i).childCount()):
                    self.tree.topLevelItem(i).child(j).setHidden(False)
            return

        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            top_match = False
            top_text = top.text(0).lower()
            top_key = top.data(0, Qt.UserRole)
            if text in top_text:
                top_match = True
            elif top_key and top_key in HELP_CONTENT:
                content = HELP_CONTENT[top_key]['content'].lower()
                if text in content:
                    top_match = True

            child_visible = 0
            for j in range(top.childCount()):
                child = top.child(j)
                child_text = child.text(0).lower()
                child_key = child.data(0, Qt.UserRole)
                found = text in child_text
                if not found and child_key and child_key in HELP_CONTENT:
                    content = HELP_CONTENT[child_key]['content'].lower()
                    found = text in content
                child.setHidden(not found)
                if found:
                    child_visible += 1

            top.setHidden(not (top_match or child_visible > 0))
            if child_visible > 0:
                top.setExpanded(True)

    def show_page(self, key: str):
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            if top.data(0, Qt.UserRole) == key:
                self.tree.setCurrentItem(top)
                self._show_content(key)
                return
            for j in range(top.childCount()):
                child = top.child(j)
                if child.data(0, Qt.UserRole) == key:
                    self.tree.setCurrentItem(child)
                    self._show_content(key)
                    top.setExpanded(True)
                    return

    def showEvent(self, e):
        super().showEvent(e)
        if not self.browser.toHtml():
            self._show_content('overview')

