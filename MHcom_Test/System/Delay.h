#ifndef __DELAY_H
#define __DELAY_H

#include <stdint.h>

void SysTick_Init(void);
uint32_t GetSysTick(void);

void Delay_us(uint32_t us);
void Delay_ms(uint32_t ms);
void Delay_s(uint32_t s);

#endif
