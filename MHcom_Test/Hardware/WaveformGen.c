#include "stm32f10x.h"
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include "WaveformGen.h"
#include "Serial.h"

#ifndef M_PI
#define M_PI    3.14159265358979323846
#endif

static WaveformChannel channels[WAVEFORM_MAX_CHANNELS];
static uint8_t channel_count = 4;
static uint32_t sample_count = 0;
static float time_accum = 0.0f;
static float sample_rate = 100.0f;
static uint16_t sample_interval_ms = 10;

static const uint16_t sin_table[256] = {
	0, 1608, 3212, 4808, 6393, 7962, 9512, 11039,
	12540, 14010, 15447, 16846, 18205, 19519, 20788, 22006,
	23170, 24279, 25330, 26319, 27245, 28106, 28899, 29622,
	30273, 30852, 31357, 31786, 32138, 32413, 32610, 32728,
	32768, 32728, 32610, 32413, 32138, 31786, 31357, 30852,
	30273, 29622, 28899, 28106, 27245, 26319, 25330, 24279,
	23170, 22006, 20788, 19519, 18205, 16846, 15447, 14010,
	12540, 11039, 9512, 7962, 6393, 4808, 3212, 1608,
	0, 63928, 62324, 60728, 59143, 57574, 56024, 54497,
	52996, 51526, 50089, 48690, 47331, 46017, 44748, 43530,
	42366, 41257, 40206, 39217, 38291, 37430, 36637, 35914,
	35263, 34684, 34179, 33750, 33398, 33123, 32926, 32808,
	32768, 32808, 32926, 33123, 33398, 33750, 34179, 34684,
	35263, 35914, 36637, 37430, 38291, 39217, 40206, 41257,
	42366, 43530, 44748, 46017, 47331, 48690, 50089, 51526,
	52996, 54497, 56024, 57574, 59143, 60728, 62324, 63928
};

static float fast_sin(float angle)
{
	float norm = angle / (2.0f * (float)M_PI);
	norm = norm - (float)((int)norm);
	if (norm < 0.0f) norm += 1.0f;
	uint16_t idx = (uint16_t)(norm * 256.0f) & 0xFF;
	return ((float)sin_table[idx] / 32768.0f) * 2.0f - 1.0f;
}

void WaveformGen_Init(void)
{
	uint8_t i;
	for (i = 0; i < WAVEFORM_MAX_CHANNELS; i++)
	{
		channels[i].type = WAVE_SINE;
		channels[i].amplitude = 50.0f;
		channels[i].frequency = 1.0f;
		channels[i].phase = 0.0f;
		channels[i].offset = 0.0f;
	}
	
	channels[0].type = WAVE_SINE;
	channels[0].amplitude = 50.0f;
	channels[0].frequency = 1.0f;
	channels[0].phase = 0.0f;
	channels[0].offset = 0.0f;
	
	channels[1].type = WAVE_SQUARE;
	channels[1].amplitude = 40.0f;
	channels[1].frequency = 2.0f;
	channels[1].phase = 0.0f;
	channels[1].offset = 10.0f;
	
	channels[2].type = WAVE_TRIANGLE;
	channels[2].amplitude = 45.0f;
	channels[2].frequency = 0.5f;
	channels[2].phase = 0.0f;
	channels[2].offset = -20.0f;
	
	channels[3].type = WAVE_SAWTOOTH;
	channels[3].amplitude = 60.0f;
	channels[3].frequency = 1.5f;
	channels[3].phase = 0.0f;
	channels[3].offset = 30.0f;
	
	channel_count = 4;
	sample_count = 0;
	time_accum = 0.0f;
}

void WaveformGen_SetChannel(uint8_t ch, WaveformType type, float amp, float freq, float phase, float offset)
{
	if (ch >= WAVEFORM_MAX_CHANNELS) return;
	channels[ch].type = type;
	channels[ch].amplitude = amp;
	channels[ch].frequency = freq;
	channels[ch].phase = phase;
	channels[ch].offset = offset;
}

void WaveformGen_SetChannelCount(uint8_t count)
{
	if (count > WAVEFORM_MAX_CHANNELS) count = WAVEFORM_MAX_CHANNELS;
	if (count < 1) count = 1;
	channel_count = count;
}

uint8_t WaveformGen_GetChannelCount(void)
{
	return channel_count;
}

void WaveformGen_Generate(float *values, uint8_t count)
{
	uint8_t i;
	float t;
	float angle;
	float frac;
	
	t = time_accum;
	
	for (i = 0; i < count && i < channel_count; i++)
	{
		angle = 2.0f * (float)M_PI * channels[i].frequency * t + channels[i].phase;
		
		switch (channels[i].type)
		{
			case WAVE_SINE:
				values[i] = channels[i].amplitude * fast_sin(angle) + channels[i].offset;
				break;
			
			case WAVE_SQUARE:
				if (fast_sin(angle) >= 0.0f)
					values[i] = channels[i].amplitude + channels[i].offset;
				else
					values[i] = -channels[i].amplitude + channels[i].offset;
				break;
			
			case WAVE_TRIANGLE:
				frac = (angle / (2.0f * (float)M_PI));
				frac = frac - (float)((int)frac);
				if (frac < 0.0f) frac += 1.0f;
				if (frac < 0.25f)
					values[i] = channels[i].amplitude * (4.0f * frac) + channels[i].offset;
				else if (frac < 0.75f)
					values[i] = channels[i].amplitude * (2.0f - 4.0f * frac) + channels[i].offset;
				else
					values[i] = channels[i].amplitude * (4.0f * frac - 4.0f) + channels[i].offset;
				break;
			
			case WAVE_SAWTOOTH:
				frac = (angle / (2.0f * (float)M_PI));
				frac = frac - (float)((int)frac);
				if (frac < 0.0f) frac += 1.0f;
				values[i] = channels[i].amplitude * (2.0f * frac - 1.0f) + channels[i].offset;
				break;
			
			case WAVE_DC:
				values[i] = channels[i].offset;
				break;
			
			case WAVE_NOISE:
				values[i] = channels[i].amplitude * ((float)rand() / (float)RAND_MAX * 2.0f - 1.0f) + channels[i].offset;
				break;
			
			default:
				values[i] = 0.0f;
				break;
		}
	}
	
	time_accum += 1.0f / sample_rate;
	sample_count++;
}

void WaveformGen_SendFrame(void)
{
	float values[WAVEFORM_MAX_CHANNELS];
	uint8_t i;
	char buf[32];
	
	WaveformGen_Generate(values, channel_count);
	
	for (i = 0; i < channel_count; i++)
	{
		sprintf(buf, "%.2f", values[i]);
		Serial_SendString(buf);
		if (i < channel_count - 1)
		{
			Serial_SendString(",");
		}
	}
	Serial_SendString("\r\n");
}

float WaveformGen_GetSampleRate(void)
{
	return sample_rate;
}

void WaveformGen_SetSampleRate(uint16_t rate_hz)
{
	if (rate_hz == 0) rate_hz = 1;
	if (rate_hz > 1000) rate_hz = 1000;
	sample_rate = (float)rate_hz;
	sample_interval_ms = 1000 / rate_hz;
	if (sample_interval_ms == 0) sample_interval_ms = 1;
}

uint16_t WaveformGen_GetIntervalMs(void)
{
	return sample_interval_ms;
}
