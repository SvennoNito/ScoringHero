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
A displayed row on the signal panel; either a signal from the file or a derived channel. Identified by its channel name.

**Channel name**:
The name of a channel, unique within a recording; a channel cannot be renamed to a name another channel already has.

**Derived channel**:
A channel computed from other channels (e.g. re-referenced), not stored in the recording file. Starts with the channel settings of its source channel, under the source channel's name followed by `*` (`**`, ... if that name is taken).

**Overlay signal**:
A second recording with the same channels shown on top of the primary recording for comparison.
_Avoid_: overlay (alone; ambiguous with busy indicator)

**Displayed signal**:
A channel's signal as shown: re-referenced, filtered and polarity-flipped according to its channel settings. Derived from the recording, never stored in it.
_Avoid_: display data, processed signal

**Busy indicator**:
A visible notice that the app is working (importing or filtering) and that input is paused.
_Avoid_: overlay, spinner

**Welcome banner**:
The greeting printed in the console window when the app starts; thanks the user and points to the issue tracker for bug reports and feature requests.
_Avoid_: splash screen, startup message

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

### Scoring

**Primary scoring**:
The scoring of the recording that is being viewed and edited.
_Avoid_: you, my scoring, own scoring

**Comparison scoring**:
A second scoring of the same recording, loaded read-only to compare against the primary scoring. Labelled by its file name.
_Avoid_: you, reference scoring, ref

**Epoch**:
A fixed-length time slice of a recording that receives one stage.

**Stage**:
One of Wake, N1, N2, N3, REM or Inconclusive, assigned to an epoch. An epoch without a stage is unscored.

**Hypnogram digit**:
The number a stage has on the hypnogram: Wake 1, N1 -1, N2 -2, N3 -3, REM 0, Inconclusive 2. Derived from the stage name, never stored in memory; written next to the stage in the scoring file and ignored on load. Not the same as a format's own stage codes (e.g. GSSC `4` = REM), which stay inside that format's loader and writer.
_Avoid_: digit (alone; ambiguous with format codes)

**Disagreement**:
An epoch where the primary scoring and the comparison scoring have different stages. Always computed from the current primary scoring.

**Scoring**:
The stage of every epoch of a recording; events are not part of it. The scoring file stores a scoring together with the events.
