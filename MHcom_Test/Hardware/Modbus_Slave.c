#include "stm32f10x.h"
#include <string.h>
#include "Modbus_Slave.h"
#include "Serial.h"
#include "Delay.h"

static uint16_t holding_regs[MODBUS_REG_COUNT];
static uint16_t input_regs[MODBUS_INPUT_REG_COUNT];
static uint8_t coils[MODBUS_COIL_COUNT / 8 + 1];
static uint8_t discrete_inputs[MODBUS_DISCRETE_COUNT / 8 + 1];

static uint16_t crc16_modbus(uint8_t *data, uint16_t len)
{
	uint16_t crc = 0xFFFF;
	uint16_t i, j;
	
	for (i = 0; i < len; i++)
	{
		crc ^= data[i];
		for (j = 0; j < 8; j++)
		{
			if (crc & 0x0001)
			{
				crc >>= 1;
				crc ^= 0xA001;
			}
			else
			{
				crc >>= 1;
			}
		}
	}
	return crc;
}

static void Modbus_SendResponse(uint8_t *data, uint16_t len)
{
	uint16_t crc;
	crc = crc16_modbus(data, len);
	data[len++] = crc & 0xFF;
	data[len++] = (crc >> 8) & 0xFF;
	Serial_SendArray(data, len);
}

static void Modbus_SendException(uint8_t slave_addr, uint8_t func, uint8_t exc_code)
{
	uint8_t resp[5];
	resp[0] = slave_addr;
	resp[1] = func | 0x80;
	resp[2] = exc_code;
	Modbus_SendResponse(resp, 3);
}

void ModbusSlave_Init(void)
{
	uint16_t i;
	memset(holding_regs, 0, sizeof(holding_regs));
	memset(input_regs, 0, sizeof(input_regs));
	memset(coils, 0, sizeof(coils));
	memset(discrete_inputs, 0, sizeof(discrete_inputs));
	
	for (i = 0; i < MODBUS_REG_COUNT; i++)
	{
		holding_regs[i] = i * 10;
	}
	
	for (i = 0; i < MODBUS_INPUT_REG_COUNT; i++)
	{
		input_regs[i] = i * 20 + 100;
	}
	
	for (i = 0; i < MODBUS_COIL_COUNT; i++)
	{
		if (i % 2 == 0)
		{
			coils[i / 8] |= (1 << (i % 8));
		}
	}
	
	for (i = 0; i < MODBUS_DISCRETE_COUNT; i++)
	{
		if (i % 3 == 0)
		{
			discrete_inputs[i / 8] |= (1 << (i % 8));
		}
	}
}

static void Modbus_HandleReadCoils(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t start_addr, coil_count;
	uint16_t byte_count;
	uint16_t i, j;
	uint8_t resp[256];
	uint8_t coil_val;
	
	if (len < 6)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_COILS, 0x03);
		return;
	}
	
	start_addr = (data[2] << 8) | data[3];
	coil_count = (data[4] << 8) | data[5];
	
	if (start_addr + coil_count > MODBUS_COIL_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_COILS, 0x02);
		return;
	}
	
	byte_count = (coil_count + 7) / 8;
	
	resp[0] = slave_addr;
	resp[1] = MODBUS_FUNC_READ_COILS;
	resp[2] = byte_count;
	
	for (i = 0; i < byte_count; i++)
	{
		resp[3 + i] = 0;
		for (j = 0; j < 8 && i * 8 + j < coil_count; j++)
		{
			uint16_t coil_idx = start_addr + i * 8 + j;
			coil_val = (coils[coil_idx / 8] >> (coil_idx % 8)) & 0x01;
			if (coil_val)
			{
				resp[3 + i] |= (1 << j);
			}
		}
	}
	
	Modbus_SendResponse(resp, 3 + byte_count);
}

static void Modbus_HandleReadDiscrete(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t start_addr, input_count;
	uint16_t byte_count;
	uint16_t i, j;
	uint8_t resp[256];
	uint8_t input_val;
	
	if (len < 6)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_DISCRETE, 0x03);
		return;
	}
	
	start_addr = (data[2] << 8) | data[3];
	input_count = (data[4] << 8) | data[5];
	
	if (start_addr + input_count > MODBUS_DISCRETE_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_DISCRETE, 0x02);
		return;
	}
	
	byte_count = (input_count + 7) / 8;
	
	resp[0] = slave_addr;
	resp[1] = MODBUS_FUNC_READ_DISCRETE;
	resp[2] = byte_count;
	
	for (i = 0; i < byte_count; i++)
	{
		resp[3 + i] = 0;
		for (j = 0; j < 8 && i * 8 + j < input_count; j++)
		{
			uint16_t input_idx = start_addr + i * 8 + j;
			input_val = (discrete_inputs[input_idx / 8] >> (input_idx % 8)) & 0x01;
			if (input_val)
			{
				resp[3 + i] |= (1 << j);
			}
		}
	}
	
	Modbus_SendResponse(resp, 3 + byte_count);
}

static void Modbus_HandleReadHolding(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t start_addr, reg_count;
	uint16_t byte_count;
	uint16_t i;
	uint8_t resp[256];
	
	if (len < 6)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_HOLDING, 0x03);
		return;
	}
	
	start_addr = (data[2] << 8) | data[3];
	reg_count = (data[4] << 8) | data[5];
	
	if (start_addr + reg_count > MODBUS_REG_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_HOLDING, 0x02);
		return;
	}
	
	byte_count = reg_count * 2;
	
	resp[0] = slave_addr;
	resp[1] = MODBUS_FUNC_READ_HOLDING;
	resp[2] = byte_count;
	
	for (i = 0; i < reg_count; i++)
	{
		resp[3 + i * 2] = (holding_regs[start_addr + i] >> 8) & 0xFF;
		resp[4 + i * 2] = holding_regs[start_addr + i] & 0xFF;
	}
	
	Modbus_SendResponse(resp, 3 + byte_count);
}

static void Modbus_HandleReadInput(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t start_addr, reg_count;
	uint16_t byte_count;
	uint16_t i;
	uint8_t resp[256];
	
	if (len < 6)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_INPUT, 0x03);
		return;
	}
	
	start_addr = (data[2] << 8) | data[3];
	reg_count = (data[4] << 8) | data[5];
	
	if (start_addr + reg_count > MODBUS_INPUT_REG_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_READ_INPUT, 0x02);
		return;
	}
	
	byte_count = reg_count * 2;
	
	resp[0] = slave_addr;
	resp[1] = MODBUS_FUNC_READ_INPUT;
	resp[2] = byte_count;
	
	for (i = 0; i < reg_count; i++)
	{
		resp[3 + i * 2] = (input_regs[start_addr + i] >> 8) & 0xFF;
		resp[4 + i * 2] = input_regs[start_addr + i] & 0xFF;
	}
	
	Modbus_SendResponse(resp, 3 + byte_count);
}

static void Modbus_HandleWriteSingleCoil(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t coil_addr;
	uint16_t coil_val;
	
	if (len < 6)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_SINGLE_COIL, 0x03);
		return;
	}
	
	coil_addr = (data[2] << 8) | data[3];
	coil_val = (data[4] << 8) | data[5];
	
	if (coil_addr >= MODBUS_COIL_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_SINGLE_COIL, 0x02);
		return;
	}
	
	if (coil_val == 0xFF00)
	{
		coils[coil_addr / 8] |= (1 << (coil_addr % 8));
	}
	else if (coil_val == 0x0000)
	{
		coils[coil_addr / 8] &= ~(1 << (coil_addr % 8));
	}
	else
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_SINGLE_COIL, 0x03);
		return;
	}
	
	Modbus_SendResponse(data, 6);
}

static void Modbus_HandleWriteSingleReg(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t reg_addr;
	uint16_t reg_val;
	
	if (len < 6)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_SINGLE_REG, 0x03);
		return;
	}
	
	reg_addr = (data[2] << 8) | data[3];
	reg_val = (data[4] << 8) | data[5];
	
	if (reg_addr >= MODBUS_REG_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_SINGLE_REG, 0x02);
		return;
	}
	
	holding_regs[reg_addr] = reg_val;
	
	Modbus_SendResponse(data, 6);
}

static void Modbus_HandleWriteMultiCoils(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t start_addr, coil_count;
	uint16_t byte_count;
	uint16_t i, j;
	uint8_t coil_val;
	uint8_t resp[8];
	
	if (len < 7)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_MULTI_COILS, 0x03);
		return;
	}
	
	start_addr = (data[2] << 8) | data[3];
	coil_count = (data[4] << 8) | data[5];
	byte_count = data[6];
	
	if (start_addr + coil_count > MODBUS_COIL_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_MULTI_COILS, 0x02);
		return;
	}
	
	for (i = 0; i < coil_count; i++)
	{
		uint16_t byte_idx = i / 8;
		uint8_t bit_idx = i % 8;
		coil_val = (data[7 + byte_idx] >> bit_idx) & 0x01;
		
		uint16_t coil_idx = start_addr + i;
		if (coil_val)
		{
			coils[coil_idx / 8] |= (1 << (coil_idx % 8));
		}
		else
		{
			coils[coil_idx / 8] &= ~(1 << (coil_idx % 8));
		}
	}
	
	resp[0] = slave_addr;
	resp[1] = MODBUS_FUNC_WRITE_MULTI_COILS;
	resp[2] = (start_addr >> 8) & 0xFF;
	resp[3] = start_addr & 0xFF;
	resp[4] = (coil_count >> 8) & 0xFF;
	resp[5] = coil_count & 0xFF;
	
	Modbus_SendResponse(resp, 6);
}

static void Modbus_HandleWriteMultiRegs(uint8_t slave_addr, uint8_t *data, uint16_t len)
{
	uint16_t start_addr, reg_count;
	uint16_t byte_count;
	uint16_t i;
	uint8_t resp[8];
	
	if (len < 7)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_MULTI_REGS, 0x03);
		return;
	}
	
	start_addr = (data[2] << 8) | data[3];
	reg_count = (data[4] << 8) | data[5];
	byte_count = data[6];
	
	if (start_addr + reg_count > MODBUS_REG_COUNT)
	{
		Modbus_SendException(slave_addr, MODBUS_FUNC_WRITE_MULTI_REGS, 0x02);
		return;
	}
	
	for (i = 0; i < reg_count; i++)
	{
		holding_regs[start_addr + i] = (data[7 + i * 2] << 8) | data[8 + i * 2];
	}
	
	resp[0] = slave_addr;
	resp[1] = MODBUS_FUNC_WRITE_MULTI_REGS;
	resp[2] = (start_addr >> 8) & 0xFF;
	resp[3] = start_addr & 0xFF;
	resp[4] = (reg_count >> 8) & 0xFF;
	resp[5] = reg_count & 0xFF;
	
	Modbus_SendResponse(resp, 6);
}

void ModbusSlave_Process(void)
{
	static uint8_t rx_buf[256];
	static uint16_t rx_idx = 0;
	static uint32_t last_rx_tick = 0;
	uint8_t slave_addr;
	uint8_t func_code;
	uint16_t crc_recv, crc_calc;
	uint32_t now = GetSysTick();
	
	while (Serial_GetRxDataLen() > 0)
	{
		uint8_t byte = Serial_ReadRxByte();
		if (rx_idx < sizeof(rx_buf))
		{
			rx_buf[rx_idx++] = byte;
		}
		last_rx_tick = now;
	}
	
	if (rx_idx >= 4 && (now - last_rx_tick) > 5)
	{
		slave_addr = rx_buf[0];
		
		if (slave_addr == MODBUS_SLAVE_ADDR || slave_addr == 0)
		{
			crc_recv = rx_buf[rx_idx - 2] | (rx_buf[rx_idx - 1] << 8);
			crc_calc = crc16_modbus(rx_buf, rx_idx - 2);
			
			if (crc_recv == crc_calc)
			{
				func_code = rx_buf[1];
				
				switch (func_code)
				{
					case MODBUS_FUNC_READ_COILS:
						Modbus_HandleReadCoils(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_READ_DISCRETE:
						Modbus_HandleReadDiscrete(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_READ_HOLDING:
						Modbus_HandleReadHolding(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_READ_INPUT:
						Modbus_HandleReadInput(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_WRITE_SINGLE_COIL:
						Modbus_HandleWriteSingleCoil(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_WRITE_SINGLE_REG:
						Modbus_HandleWriteSingleReg(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_WRITE_MULTI_COILS:
						Modbus_HandleWriteMultiCoils(slave_addr, rx_buf, rx_idx);
						break;
					
					case MODBUS_FUNC_WRITE_MULTI_REGS:
						Modbus_HandleWriteMultiRegs(slave_addr, rx_buf, rx_idx);
						break;
					
					default:
						Modbus_SendException(slave_addr, func_code, 0x01);
						break;
				}
			}
		}
		
		rx_idx = 0;
	}
}

uint16_t ModbusSlave_GetHoldingReg(uint16_t addr)
{
	if (addr >= MODBUS_REG_COUNT) return 0;
	return holding_regs[addr];
}

void ModbusSlave_SetHoldingReg(uint16_t addr, uint16_t value)
{
	if (addr >= MODBUS_REG_COUNT) return;
	holding_regs[addr] = value;
}

uint16_t ModbusSlave_GetInputReg(uint16_t addr)
{
	if (addr >= MODBUS_INPUT_REG_COUNT) return 0;
	return input_regs[addr];
}

void ModbusSlave_SetInputReg(uint16_t addr, uint16_t value)
{
	if (addr >= MODBUS_INPUT_REG_COUNT) return;
	input_regs[addr] = value;
}

uint8_t ModbusSlave_GetCoil(uint16_t addr)
{
	if (addr >= MODBUS_COIL_COUNT) return 0;
	return (coils[addr / 8] >> (addr % 8)) & 0x01;
}

void ModbusSlave_SetCoil(uint16_t addr, uint8_t value)
{
	if (addr >= MODBUS_COIL_COUNT) return;
	if (value)
		coils[addr / 8] |= (1 << (addr % 8));
	else
		coils[addr / 8] &= ~(1 << (addr % 8));
}

uint8_t ModbusSlave_GetDiscrete(uint16_t addr)
{
	if (addr >= MODBUS_DISCRETE_COUNT) return 0;
	return (discrete_inputs[addr / 8] >> (addr % 8)) & 0x01;
}

void ModbusSlave_SetDiscrete(uint16_t addr, uint8_t value)
{
	if (addr >= MODBUS_DISCRETE_COUNT) return;
	if (value)
		discrete_inputs[addr / 8] |= (1 << (addr % 8));
	else
		discrete_inputs[addr / 8] &= ~(1 << (addr % 8));
}
