#include "stm32f10x.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "CommandParser.h"
#include "Serial.h"
#include "WaveformGen.h"
#include "Modbus_Slave.h"
#include "LED.h"
#include "OLED.h"

static TestMode current_mode = MODE_MENU;
static uint32_t counter = 0;
static uint32_t last_wave_time = 0;
static uint16_t wave_interval_ms = 10;

static int str_startswith(const char *str, const char *prefix)
{
	while (*prefix)
	{
		if (*str != *prefix) return 0;
		str++;
		prefix++;
	}
	return 1;
}

static void cmd_help(char *cmd)
{
	CommandParser_ShowHelp();
}

static void cmd_mode(char *cmd)
{
	char *p = cmd + 5;
	while (*p == ' ') p++;
	
	if (strcmp(p, "wave") == 0 || strcmp(p, "waveform") == 0)
	{
		current_mode = MODE_WAVEFORM;
		Serial_Printf("切换到波形图模式\r\n");
		OLED_ShowString(1, 1, "Mode: Waveform    ");
	}
	else if (strcmp(p, "modbus") == 0)
	{
		current_mode = MODE_MODBUS;
		Serial_Printf("切换到Modbus模式\r\n");
		OLED_ShowString(1, 1, "Mode: Modbus      ");
	}
	else if (strcmp(p, "echo") == 0)
	{
		current_mode = MODE_ECHO;
		Serial_Printf("切换到回显模式\r\n");
		OLED_ShowString(1, 1, "Mode: Echo        ");
	}
	else if (strcmp(p, "counter") == 0)
	{
		current_mode = MODE_COUNTER;
		counter = 0;
		Serial_Printf("切换到计数器模式\r\n");
		OLED_ShowString(1, 1, "Mode: Counter     ");
	}
	else if (strcmp(p, "menu") == 0 || strcmp(p, "idle") == 0)
	{
		current_mode = MODE_MENU;
		Serial_Printf("切换到菜单模式\r\n");
		OLED_ShowString(1, 1, "Mode: Menu        ");
	}
	else
	{
		Serial_Printf("未知模式: %s\r\n", p);
	}
}

static void cmd_wave(char *cmd)
{
	char *p = cmd + 5;
	while (*p == ' ') p++;
	
	if (str_startswith(p, "ch"))
	{
		uint8_t ch;
		float amp, freq, phase, offset;
		int type = 0;
		char type_str[16];
		
		p += 2;
		while (*p == ' ') p++;
		ch = atoi(p) - 1;
		
		while (*p != ' ' && *p != '\0') p++;
		while (*p == ' ') p++;
		strncpy(type_str, p, 15);
		type_str[15] = '\0';
		
		if (strcmp(type_str, "sine") == 0) type = 0;
		else if (strcmp(type_str, "square") == 0) type = 1;
		else if (strcmp(type_str, "triangle") == 0) type = 2;
		else if (strcmp(type_str, "sawtooth") == 0) type = 3;
		else if (strcmp(type_str, "dc") == 0) type = 4;
		else if (strcmp(type_str, "noise") == 0) type = 5;
		else
		{
			Serial_Printf("未知波形类型: %s\r\n", type_str);
			return;
		}
		
		while (*p != ' ' && *p != '\0') p++;
		while (*p == ' ') p++;
		amp = atof(p);
		
		while (*p != ' ' && *p != '\0') p++;
		while (*p == ' ') p++;
		freq = atof(p);
		
		while (*p != ' ' && *p != '\0') p++;
		while (*p == ' ') p++;
		phase = atof(p);
		
		while (*p != ' ' && *p != '\0') p++;
		while (*p == ' ') p++;
		offset = atof(p);
		
		WaveformGen_SetChannel(ch, (WaveformType)type, amp, freq, phase, offset);
		Serial_Printf("通道%d设置: 类型=%s, 幅值=%.1f, 频率=%.2fHz\r\n", 
			ch + 1, type_str, amp, freq);
	}
	else if (str_startswith(p, "count"))
	{
		p += 5;
		while (*p == ' ') p++;
		uint8_t count = atoi(p);
		WaveformGen_SetChannelCount(count);
		Serial_Printf("波形通道数: %d\r\n", count);
	}
	else if (str_startswith(p, "rate"))
	{
		p += 4;
		while (*p == ' ') p++;
		uint16_t rate = atoi(p);
		if (rate > 0 && rate <= 1000)
		{
			WaveformGen_SetSampleRate(rate);
			Serial_Printf("波形输出速率: %d Hz\r\n", rate);
		}
	}
	else if (strcmp(p, "start") == 0)
	{
		current_mode = MODE_WAVEFORM;
		Serial_Printf("波形输出已启动\r\n");
	}
	else if (strcmp(p, "stop") == 0)
	{
		current_mode = MODE_MENU;
		Serial_Printf("波形输出已停止\r\n");
	}
	else
	{
		Serial_Printf("波形命令: wave ch<N> <type> <amp> <freq> <phase> <offset>\r\n");
		Serial_Printf("           wave count <N>  - 设置通道数\r\n");
		Serial_Printf("           wave rate <Hz>  - 设置输出速率\r\n");
		Serial_Printf("           wave start/stop - 启动/停止\r\n");
	}
}

static void cmd_led(char *cmd)
{
	char *p = cmd + 4;
	while (*p == ' ') p++;
	
	if (strcmp(p, "on") == 0)
	{
		LED1_ON();
		Serial_Printf("LED 已点亮\r\n");
	}
	else if (strcmp(p, "off") == 0)
	{
		LED1_OFF();
		Serial_Printf("LED 已熄灭\r\n");
	}
	else if (strcmp(p, "toggle") == 0)
	{
		LED1_Turn();
		Serial_Printf("LED 已翻转\r\n");
	}
	else
	{
		Serial_Printf("LED命令: led on/off/toggle\r\n");
	}
}

static void cmd_info(char *cmd)
{
	Serial_Printf("========================================\r\n");
	Serial_Printf("  MHcom Test Firmware v1.0\r\n");
	Serial_Printf("  STM32F103C8T6 Test Board\r\n");
	Serial_Printf("========================================\r\n");
	Serial_Printf("  波特率: 115200\r\n");
	Serial_Printf("  数据位: 8\r\n");
	Serial_Printf("  停止位: 1\r\n");
	Serial_Printf("  校验位: 无\r\n");
	Serial_Printf("========================================\r\n");
	Serial_Printf("  当前模式: ");
	switch (current_mode)
	{
		case MODE_MENU: Serial_Printf("菜单模式\r\n"); break;
		case MODE_WAVEFORM: Serial_Printf("波形图模式\r\n"); break;
		case MODE_MODBUS: Serial_Printf("Modbus模式\r\n"); break;
		case MODE_ECHO: Serial_Printf("回显模式\r\n"); break;
		case MODE_COUNTER: Serial_Printf("计数器模式\r\n"); break;
		default: Serial_Printf("未知\r\n"); break;
	}
	Serial_Printf("========================================\r\n");
}

static void cmd_test(char *cmd)
{
	char *p = cmd + 5;
	while (*p == ' ') p++;
	
	if (strcmp(p, "crc") == 0)
	{
		Serial_Printf("CRC测试数据 (Modbus RTU):\r\n");
		Serial_Printf("  读保持寄存器 0x0000~0x0009:\r\n");
		Serial_Printf("  01 03 00 00 00 0A C5 CD\r\n");
		Serial_Printf("  写单寄存器 0x0000 = 0x1234:\r\n");
		Serial_Printf("  01 06 00 00 12 34 49 E6\r\n");
	}
	else if (strcmp(p, "hex") == 0)
	{
		uint8_t data[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
		                  0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F};
		Serial_SendArray(data, 16);
		Serial_Printf("\r\n已发送16字节HEX数据 00~0F\r\n");
	}
	else if (strcmp(p, "text") == 0)
	{
		Serial_Printf("Hello, MHcom!\r\n");
		Serial_Printf("这是一段中文测试文本\r\n");
		Serial_Printf("1234567890\r\n");
		Serial_Printf("!@#$%%^&*()_+\r\n");
	}
	else if (strcmp(p, "long") == 0)
	{
		uint16_t i;
		for (i = 0; i < 100; i++)
		{
			Serial_Printf("长包测试 - 第%03d行 - 数据长度测试 ABCDEFGHIJKLMNOPQRSTUVWXYZ\r\n", i + 1);
		}
		Serial_Printf("长包测试完成，共100行\r\n");
	}
	else
	{
		Serial_Printf("测试命令: test crc/hex/text/long\r\n");
	}
}

typedef struct {
	const char *cmd;
	void (*handler)(char *);
	const char *desc;
} CommandItem;

static const CommandItem cmd_table[] = {
	{"help", cmd_help, "显示帮助信息"},
	{"?", cmd_help, "显示帮助信息"},
	{"mode", cmd_mode, "切换模式 (wave/modbus/echo/counter/menu)"},
	{"wave", cmd_wave, "波形控制"},
	{"led", cmd_led, "LED控制 (on/off/toggle)"},
	{"info", cmd_info, "显示设备信息"},
	{"test", cmd_test, "测试命令 (crc/hex/text/long)"},
	{NULL, NULL, NULL}
};

void CommandParser_Init(void)
{
	current_mode = MODE_MENU;
	counter = 0;
}

void CommandParser_Process(void)
{
	char *packet;
	char cmd[100];
	uint8_t i;
	uint8_t found = 0;
	
	if (Serial_RxFlag)
	{
		packet = (char *)Serial_RxPacket;
		
		if (current_mode == MODE_ECHO)
		{
			Serial_SendString("ECHO: ");
			Serial_SendString(packet);
			Serial_SendString("\r\n");
			Serial_ClearRxFlag();
			return;
		}
		
		if (packet[0] == '#' || packet[0] == '$' || packet[0] == '@')
		{
			strcpy(cmd, packet + 1);
		}
		else
		{
			strcpy(cmd, packet);
		}
		
		char *nl = strchr(cmd, '\r');
		if (nl) *nl = '\0';
		nl = strchr(cmd, '\n');
		if (nl) *nl = '\0';
		
		if (strlen(cmd) == 0)
		{
			Serial_ClearRxFlag();
			return;
		}
		
		for (i = 0; cmd_table[i].cmd != NULL; i++)
		{
			if (str_startswith(cmd, cmd_table[i].cmd))
			{
				cmd_table[i].handler(cmd);
				found = 1;
				break;
			}
		}
		
		if (!found)
		{
			Serial_Printf("未知命令: %s\r\n", cmd);
			Serial_Printf("输入 #help 查看帮助\r\n");
		}
		
		Serial_ClearRxFlag();
	}
}

TestMode CommandParser_GetMode(void)
{
	return current_mode;
}

void CommandParser_SetMode(TestMode mode)
{
	current_mode = mode;
}

void CommandParser_ShowHelp(void)
{
	uint8_t i;
	Serial_Printf("\r\n========================================\r\n");
	Serial_Printf("  MHcom 测试固件 - 命令列表\r\n");
	Serial_Printf("========================================\r\n");
	Serial_Printf("  命令前缀: # 或 $ 或 @\r\n");
	Serial_Printf("  示例: #help, $mode wave\r\n");
	Serial_Printf("----------------------------------------\r\n");
	for (i = 0; cmd_table[i].cmd != NULL; i++)
	{
		Serial_Printf("  %-10s - %s\r\n", cmd_table[i].cmd, cmd_table[i].desc);
	}
	Serial_Printf("----------------------------------------\r\n");
	Serial_Printf("  模式说明:\r\n");
	Serial_Printf("    menu     - 菜单模式(默认)\r\n");
	Serial_Printf("    wave     - 波形图模式(自动发送波形)\r\n");
	Serial_Printf("    modbus   - Modbus RTU从站模式\r\n");
	Serial_Printf("    echo     - 回显模式(回显所有接收)\r\n");
	Serial_Printf("    counter  - 计数器模式(每秒计数)\r\n");
	Serial_Printf("========================================\r\n");
}

void CommandParser_ShowMenu(void)
{
	Serial_Printf("\r\n");
	Serial_Printf("  __  __ _   _                       _    _____\r\n");
	Serial_Printf(" |  \\/  | | | |                     / |  / ____|\r\n");
	Serial_Printf(" | \\  / | |_| | ___ ___  _ __ ___   | | | |     ___  ___ _ ____   _____ _ __\r\n");
	Serial_Printf(" | |\\/| |  _  |/ __/ _ \\| '_ ` _ \\  | | | |    / _ \\/ _ \\ '__\\ \\ / / _ \\ '__|\r\n");
	Serial_Printf(" | |  | | | | | (_| (_) | | | | | |_| |_| |___|  __/  __/ |   \\ V /  __/ |\r\n");
	Serial_Printf(" |_|  |_|_| |_|\\___\\___/|_| |_| |_\\___/ \\_____\\___|\\___|_|    \\_/ \\___|_|\r\n");
	Serial_Printf("\r\n");
	Serial_Printf("  MHcom 多功能串口测试固件 v1.0\r\n");
	Serial_Printf("  ========================================\r\n");
	Serial_Printf("  波特率: 115200  数据位: 8  停止位: 1\r\n");
	Serial_Printf("  ========================================\r\n");
	Serial_Printf("\r\n");
	Serial_Printf("  可用测试模式:\r\n");
	Serial_Printf("  [1] 波形图测试  - 发送 #mode wave\r\n");
	Serial_Printf("  [2] Modbus测试  - 发送 #mode modbus\r\n");
	Serial_Printf("  [3] 回显测试    - 发送 #mode echo\r\n");
	Serial_Printf("  [4] 计数器测试  - 发送 #mode counter\r\n");
	Serial_Printf("\r\n");
	Serial_Printf("  输入 #help 查看完整命令列表\r\n");
	Serial_Printf("\r\n");
}
