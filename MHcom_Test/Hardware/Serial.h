#ifndef __SERIAL_H
#define __SERIAL_H

#include <stdio.h>
#include <stdint.h>

#define SERIAL_RX_BUF_SIZE    256
#define SERIAL_TX_BUF_SIZE    256

void Serial_Init(void);
void Serial_SendByte(uint8_t Byte);
void Serial_SendArray(uint8_t *Array, uint16_t Length);
void Serial_SendString(char *String);
void Serial_SendNumber(uint32_t Number, uint8_t Length);
void Serial_Printf(char *format, ...);

uint16_t Serial_GetRxDataLen(void);
uint8_t Serial_ReadRxByte(void);
void Serial_ClearRxBuffer(void);
uint8_t Serial_GetRxFlag(void);
void Serial_ClearRxFlag(void);

extern uint8_t Serial_RxPacket[];
extern uint8_t Serial_RxFlag;

#endif
