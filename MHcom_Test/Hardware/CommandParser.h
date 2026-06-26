#ifndef __COMMAND_PARSER_H
#define __COMMAND_PARSER_H

#include <stdint.h>

typedef enum {
	MODE_IDLE = 0,
	MODE_WAVEFORM,
	MODE_MODBUS,
	MODE_ECHO,
	MODE_COUNTER,
	MODE_MENU
} TestMode;

void CommandParser_Init(void);
void CommandParser_Process(void);
TestMode CommandParser_GetMode(void);
void CommandParser_SetMode(TestMode mode);
void CommandParser_ShowHelp(void);
void CommandParser_ShowMenu(void);

#endif
