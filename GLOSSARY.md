# ScoringHero

Desktop tool for visually scoring sleep stages and events in EEG/PSG recordings.

## Language

### Signals

**Recording**:
An EEG/PSG file opened for scoring; contains one or more signals.
_Avoid_: EEG file, dataset

**Signal**:
One data series stored in the recording file (EEG, EOG, EMG, accelerometer, ...). Signals may have different native sampling rates.
_Avoid_: trace, lead

**Channel**:
A displayed row on the signal panel; either a signal from the file or a derived channel.

**Derived channel**:
A channel computed from other channels (e.g. re-referenced), not stored in the recording file. Starts with the channel settings of its source channel.

**Overlay signal**:
A second recording with the same channels shown on top of the primary recording for comparison.
_Avoid_: overlay (alone; ambiguous with busy indicator)

**Busy indicator**:
A visible notice that the app is working (importing or filtering) and that input is paused.
_Avoid_: overlay, spinner

### Display

**Scaling factor**:
Per-channel amplification of the trace on screen, in percent.
_Avoid_: gain, zoom

**Default scaling**:
The scaling factor given to channels of a newly opened recording, based on how many signals the file contains; a saved channel template entry for that channel name takes precedence.

**Channel settings**:
All per-channel settings of one channel in a recording: scaling factor, vertical shift, re-reference, filters, polarity flip and display options. Saved with the recording.
_Avoid_: channel config

**Channel template**:
Saved per-channel-name settings reused when opening new recordings.

**Vertical shift**:
Per-channel offset of the trace from its row position, in µV; may be negative.

### Filtering

**Cutoff frequency**:
For high-pass and low-pass filters, the frequency at which the displayed signal is attenuated by 3 dB.
_Avoid_: corner frequency, stopband edge

**Notch frequency**:
The frequency the notch filter attenuates most.
_Avoid_: notch cutoff

**Filter order**:
How steeply a filter rolls off beyond its cutoff; higher is steeper.

### Events

**Event**:
A scored time span of a given type (e.g. arousal, artefact) shown on the signal panel and the hypnogram.
_Avoid_: annotation, label
