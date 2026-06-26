#ifndef __MODBUS_SLAVE_H
#define __MODBUS_SLAVE_H

#include <stdint.h>

#define MODBUS_SLAVE_ADDR        0x01
#define MODBUS_REG_COUNT         32
#define MODBUS_COIL_COUNT        32
#define MODBUS_INPUT_REG_COUNT   16
#define MODBUS_DISCRETE_COUNT    16

#define MODBUS_FUNC_READ_COILS           0x01
#define MODBUS_FUNC_READ_DISCRETE        0x02
#define MODBUS_FUNC_READ_HOLDING         0x03
#define MODBUS_FUNC_READ_INPUT           0x04
#define MODBUS_FUNC_WRITE_SINGLE_COIL    0x05
#define MODBUS_FUNC_WRITE_SINGLE_REG     0x06
#define MODBUS_FUNC_WRITE_MULTI_COILS    0x0F
#define MODBUS_FUNC_WRITE_MULTI_REGS     0x10

void ModbusSlave_Init(void);
void ModbusSlave_Process(void);
uint16_t ModbusSlave_GetHoldingReg(uint16_t addr);
void ModbusSlave_SetHoldingReg(uint16_t addr, uint16_t value);
uint16_t ModbusSlave_GetInputReg(uint16_t addr);
void ModbusSlave_SetInputReg(uint16_t addr, uint16_t value);
uint8_t ModbusSlave_GetCoil(uint16_t addr);
void ModbusSlave_SetCoil(uint16_t addr, uint8_t value);
uint8_t ModbusSlave_GetDiscrete(uint16_t addr);
void ModbusSlave_SetDiscrete(uint16_t addr, uint8_t value);

#endif
