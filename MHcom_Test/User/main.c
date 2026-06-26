#include "stm32f10x.h"
#include <string.h>
#include "Delay.h"
#include "OLED.h"
#include "Serial.h"
#include "LED.h"
#include "WaveformGen.h"
#include "Modbus_Slave.h"
#include "CommandParser.h"
#include "Key.h"

static uint32_t last_second = 0;
static uint32_t second_count = 0;

int main(void)
{
	uint32_t wave_timer = 0;
	uint32_t counter_timer = 0;
	uint32_t led_timer = 0;
	uint8_t key_num;
	
	SysTick_Init();
	OLED_Init();
	LED_Init();
	Key_Init();
	Serial_Init();
	WaveformGen_Init();
	ModbusSlave_Init();
	CommandParser_Init();
	
	OLED_ShowString(1, 1, "MHcom Test v1.0  ");
	OLED_ShowString(2, 1, "Baud:115200      ");
	OLED_ShowString(3, 1, "Mode: Menu       ");
	OLED_ShowString(4, 1, "Ready!           ");
	
	Delay_ms(500);
	
	CommandParser_ShowMenu();
	
	while (1)
	{
		CommandParser_Process();
		
		TestMode mode = CommandParser_GetMode();
		
		switch (mode)
		{
			case MODE_WAVEFORM:
				if (GetSysTick() - wave_timer >= WaveformGen_GetIntervalMs())
				{
					wave_timer = GetSysTick();
					WaveformGen_SendFrame();
				}
				break;
			
			case MODE_MODBUS:
				ModbusSlave_Process();
				break;
			
			case MODE_COUNTER:
				if (GetSysTick() - counter_timer >= 1000)
				{
					counter_timer = GetSysTick();
					second_count++;
					Serial_Printf("Counter: %lu\r\n", second_count);
				}
				break;
			
			case MODE_ECHO:
			case MODE_MENU:
			case MODE_IDLE:
			default:
				break;
		}
		
		key_num = Key_GetNum();
		if (key_num == 1)
		{
			LED1_Turn();
			Serial_Printf("KEY1 pressed, LED toggled\r\n");
		}
		
		if (GetSysTick() - led_timer >= 500)
		{
			led_timer = GetSysTick();
		}
		
		if (GetSysTick() - last_second >= 1000)
		{
			last_second = GetSysTick();
			
			char mode_str[16];
			switch (mode)
			{
				case MODE_WAVEFORM: strcpy(mode_str, "Waveform"); break;
				case MODE_MODBUS:   strcpy(mode_str, "Modbus  "); break;
				case MODE_ECHO:     strcpy(mode_str, "Echo    "); break;
				case MODE_COUNTER:  strcpy(mode_str, "Counter "); break;
				case MODE_MENU:
				default:            strcpy(mode_str, "Menu    "); break;
			}
			OLED_ShowString(3, 1, "Mode: ");
			OLED_ShowString(3, 7, mode_str);
			
			OLED_ShowString(4, 1, "Uptime: ");
			OLED_ShowNum(4, 9, second_count, 5);
			OLED_ShowString(4, 14, "s");
		}
	}
}
