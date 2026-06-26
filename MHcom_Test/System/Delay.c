#include "stm32f10x.h"
#include "Delay.h"

static volatile uint32_t sys_tick_count = 0;

void SysTick_Init(void)
{
	SysTick_Config(SystemCoreClock / 1000);
}

void SysTick_Handler(void)
{
	sys_tick_count++;
}

uint32_t GetSysTick(void)
{
	return sys_tick_count;
}

void Delay_us(uint32_t xus)
{
	uint32_t start = SysTick->VAL;
	uint32_t ticks = xus * (SystemCoreClock / 1000000);
	uint32_t current;
	
	if (ticks > SysTick->LOAD)
	{
		ticks = SysTick->LOAD;
	}
	
	if (start >= ticks)
	{
		while (SysTick->VAL > start - ticks);
	}
	else
	{
		while (SysTick->VAL > start || SysTick->VAL <= start + SysTick->LOAD - ticks + 1);
	}
}

void Delay_ms(uint32_t xms)
{
	uint32_t start = sys_tick_count;
	while (sys_tick_count - start < xms);
}

void Delay_s(uint32_t xs)
{
	while (xs--)
	{
		Delay_ms(1000);
	}
}
