#include "stm32f10x.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "Serial.h"

static uint8_t Rx_Buf[SERIAL_RX_BUF_SIZE];
static volatile uint16_t Rx_Write_Idx = 0;
static volatile uint16_t Rx_Read_Idx = 0;

static uint8_t Tx_Buf[SERIAL_TX_BUF_SIZE];
static volatile uint16_t Tx_Write_Idx = 0;
static volatile uint16_t Tx_Read_Idx = 0;

uint8_t Serial_RxPacket[100];
uint8_t Serial_RxFlag = 0;

void Serial_Init(void)
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	
	USART_InitTypeDef USART_InitStructure;
	USART_InitStructure.USART_BaudRate = 115200;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_Init(USART1, &USART_InitStructure);
	
	NVIC_InitTypeDef NVIC_InitStructure;
	NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
	NVIC_Init(&NVIC_InitStructure);
	
	USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
	USART_Cmd(USART1, ENABLE);
}

void Serial_SendByte(uint8_t Byte)
{
	USART_SendData(USART1, Byte);
	while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
}

void Serial_SendArray(uint8_t *Array, uint16_t Length)
{
	uint16_t i;
	for (i = 0; i < Length; i ++)
	{
		Serial_SendByte(Array[i]);
	}
}

void Serial_SendString(char *String)
{
	uint8_t i;
	for (i = 0; String[i] != '\0'; i ++)
	{
		Serial_SendByte(String[i]);
	}
}

uint32_t Serial_Pow(uint32_t X, uint32_t Y)
{
	uint32_t Result = 1;
	while (Y --)
	{
		Result *= X;
	}
	return Result;
}

void Serial_SendNumber(uint32_t Number, uint8_t Length)
{
	uint8_t i;
	for (i = 0; i < Length; i ++)
	{
		Serial_SendByte(Number / Serial_Pow(10, Length - i - 1) % 10 + '0');
	}
}

int fputc(int ch, FILE *f)
{
	Serial_SendByte(ch);
	return ch;
}

void Serial_Printf(char *format, ...)
{
	char String[200];
	va_list arg;
	va_start(arg, format);
	vsprintf(String, format, arg);
	va_end(arg);
	Serial_SendString(String);
}

uint16_t Serial_GetRxDataLen(void)
{
	return (Rx_Write_Idx - Rx_Read_Idx + SERIAL_RX_BUF_SIZE) % SERIAL_RX_BUF_SIZE;
}

uint8_t Serial_ReadRxByte(void)
{
	uint8_t data;
	if (Rx_Read_Idx == Rx_Write_Idx)
	{
		return 0;
	}
	data = Rx_Buf[Rx_Read_Idx];
	Rx_Read_Idx = (Rx_Read_Idx + 1) % SERIAL_RX_BUF_SIZE;
	return data;
}

void Serial_ClearRxBuffer(void)
{
	Rx_Read_Idx = Rx_Write_Idx;
}

uint8_t Serial_GetRxFlag(void)
{
	return Serial_RxFlag;
}

void Serial_ClearRxFlag(void)
{
	Serial_RxFlag = 0;
}

void USART1_IRQHandler(void)
{
	uint8_t rx_byte;
	static uint8_t rx_state = 0;
	static uint8_t rx_pkt_idx = 0;
	
	if (USART_GetITStatus(USART1, USART_IT_RXNE) == SET)
	{
		rx_byte = USART_ReceiveData(USART1);
		
		uint16_t next_idx = (Rx_Write_Idx + 1) % SERIAL_RX_BUF_SIZE;
		if (next_idx != Rx_Read_Idx)
		{
			Rx_Buf[Rx_Write_Idx] = rx_byte;
			Rx_Write_Idx = next_idx;
		}
		
		if (rx_state == 0)
		{
			if (rx_byte == '#' || rx_byte == '$' || rx_byte == '@')
			{
				rx_state = 1;
				rx_pkt_idx = 0;
				Serial_RxPacket[rx_pkt_idx++] = rx_byte;
			}
		}
		else if (rx_state == 1)
		{
			Serial_RxPacket[rx_pkt_idx++] = rx_byte;
			if (rx_byte == '\n' || rx_byte == '\r' || rx_pkt_idx >= 99)
			{
				Serial_RxPacket[rx_pkt_idx] = '\0';
				Serial_RxFlag = 1;
				rx_state = 0;
			}
		}
		
		USART_ClearITPendingBit(USART1, USART_IT_RXNE);
	}
}
