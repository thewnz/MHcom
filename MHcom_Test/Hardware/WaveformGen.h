#ifndef __WAVEFORM_GEN_H
#define __WAVEFORM_GEN_H

#include <stdint.h>

#define WAVEFORM_MAX_CHANNELS    8

typedef enum {
	WAVE_SINE = 0,
	WAVE_SQUARE,
	WAVE_TRIANGLE,
	WAVE_SAWTOOTH,
	WAVE_DC,
	WAVE_NOISE
} WaveformType;

typedef struct {
	WaveformType type;
	float amplitude;
	float frequency;
	float phase;
	float offset;
} WaveformChannel;

void WaveformGen_Init(void);
void WaveformGen_SetChannel(uint8_t ch, WaveformType type, float amp, float freq, float phase, float offset);
void WaveformGen_SetChannelCount(uint8_t count);
uint8_t WaveformGen_GetChannelCount(void);
void WaveformGen_Generate(float *values, uint8_t count);
void WaveformGen_SendFrame(void);
float WaveformGen_GetSampleRate(void);
void WaveformGen_SetSampleRate(uint16_t rate_hz);
uint16_t WaveformGen_GetIntervalMs(void);

#endif
