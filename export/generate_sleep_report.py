

"""
ScoringHero Sleep Report Generator — standalone script

Generates the same PDF as File → Export Report → Sleep Report.
No ScoringHero installation needed; only the libraries below are required.

Dependencies (all included in ScoringHero's uv environment):
    numpy, scipy, edfio, matplotlib, reportlab, Pillow

Run:
    uv run export/generate_sleep_report.py
    python generate_sleep_report.py      # if dependencies are installed globally
"""

import argparse
import glob as _glob
import io
import json
import os
import tempfile

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.signal import welch
from edfio import read_edf
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image

# =============================================================================
#  OPTIONS  — set these before running
# =============================================================================

# Folder paths (used in batch mode and to derive paths from a single --json arg)
EDF_DIR    = r'\\vs03.herseninstituut.knaw.nl\VS03-SandD-4\PM\Data_BIDS\derivatives\scoring\EDF\Filtered'
JSON_DIR   = r'\\vs03.herseninstituut.knaw.nl\VS03-SandD-4\PM\Data_BIDS\derivatives\scoring\scores\Manual_Checked'
OUTPUT_DIR = r'\\vs03.herseninstituut.knaw.nl\VS03-SandD-4\PM\Data_BIDS\derivatives\scoring\scores\sleep_reports'
### --> Logic of how files are retrieved can be found in the function _paths_from_json

EPOCH_LENGTH_S = 30
SCALE_TO_UV    = False             # True if EDF signals are in Volts

# --- Spectrogram ---
SPEC_CHANNEL   = 0                 # 0-based channel index for spectrogram

# --- EEG trace ---
INCLUDE_TRACE   = True
TRACE_EPOCHS    = [50]              # 1-based epoch numbers, e.g. [5] or [3, 4, 5]
TRACE_CHANNELS  = [0,1,2,3,4,5,6,7,8,9,10,11]              # 0-based channel indices

# --- Report sections ---
SHOW_HYPNOGRAM        = True
HYP_SHOW_LINE         = False      # overlay a stage-connecting line on the hypnogram
HYP_COLORS            = 'all'     # 'all' | 'rem' | 'none'
HYP_MARK_AWAKENINGS   = True      # mark awakenings (last channel, duration >1 s) with magenta asterisks
HYP_MARK_STIMULI      = True      # mark auditory stimuli (last channel, duration ≤1 s) with magenta triangles
SHOW_SPECTROGRAM = True
SHOW_SLEEP_STATS = True            # TST, TRT, sleep efficiency
SHOW_STAGE_DIST  = True            # stage distribution table
SHOW_LATENCIES   = True            # N2 / N3 / REM latency
SHOW_AWAKENINGS  = True            # N2/N3/REM → Wake transitions
SHOW_AROUSALS    = True            # N2/N3/REM → N1 transitions

# =============================================================================
#  LAYOUT CONSTANTS  (match export_sleep_report.py exactly)
# =============================================================================

_FIG_SIZE   = (12, 2.5)
_DPI        = 300
_PLT_LEFT   = 0.10
_PLT_RIGHT  = 0.87
_PLT_BOTTOM = 0.22
_CBAR_W     = 0.025

_CH_COLORS = {
    'Black':   (0/255,   0/255,   0/255),
    'Blue':    (100/255, 149/255, 237/255),
    'Magenta': (233/255,  30/255,  99/255),
    'Green':   (0/255,  128/255,  64/255),
    'Orange':  (255/255, 140/255,   0/255),
    'Cyan':    (0/255,  200/255, 200/255),
}

# fmt: off
_SPECTRAL_RGB = np.array([
    0.3686,0.3098,0.6353, 0.3619,0.3186,0.6394, 0.3551,0.3273,0.6436, 0.3483,0.3361,0.6478, 0.3416,0.3449,0.6519, 0.3348,0.3536,0.6561,
    0.3280,0.3624,0.6602, 0.3213,0.3712,0.6644, 0.3145,0.3799,0.6685, 0.3077,0.3887,0.6727, 0.3010,0.3975,0.6768, 0.2942,0.4062,0.6810,
    0.2874,0.4150,0.6851, 0.2807,0.4238,0.6893, 0.2739,0.4325,0.6934, 0.2671,0.4413,0.6976, 0.2604,0.4501,0.7017, 0.2536,0.4588,0.7059,
    0.2468,0.4676,0.7100, 0.2401,0.4764,0.7142, 0.2333,0.4851,0.7183, 0.2265,0.4939,0.7225, 0.2198,0.5027,0.7266, 0.2130,0.5114,0.7308,
    0.2062,0.5202,0.7349, 0.1995,0.5290,0.7391, 0.2001,0.5378,0.7393, 0.2081,0.5467,0.7356, 0.2161,0.5556,0.7319, 0.2241,0.5646,0.7283,
    0.2321,0.5735,0.7246, 0.2401,0.5824,0.7209, 0.2481,0.5913,0.7172, 0.2561,0.6002,0.7135, 0.2641,0.6092,0.7098, 0.2720,0.6181,0.7061,
    0.2800,0.6270,0.7024, 0.2880,0.6359,0.6987, 0.2960,0.6448,0.6950, 0.3040,0.6537,0.6913, 0.3120,0.6627,0.6877, 0.3200,0.6716,0.6840,
    0.3280,0.6805,0.6803, 0.3360,0.6894,0.6766, 0.3440,0.6983,0.6729, 0.3520,0.7073,0.6692, 0.3600,0.7162,0.6655, 0.3680,0.7251,0.6618,
    0.3760,0.7340,0.6581, 0.3840,0.7429,0.6544, 0.3920,0.7519,0.6507, 0.4000,0.7608,0.6471, 0.4106,0.7649,0.6469, 0.4212,0.7691,0.6468,
    0.4318,0.7732,0.6466, 0.4424,0.7774,0.6464, 0.4531,0.7815,0.6463, 0.4637,0.7857,0.6461, 0.4743,0.7899,0.6460, 0.4849,0.7940,0.6458,
    0.4955,0.7982,0.6457, 0.5061,0.8023,0.6455, 0.5167,0.8065,0.6454, 0.5273,0.8106,0.6452, 0.5379,0.8148,0.6451, 0.5486,0.8189,0.6449,
    0.5592,0.8231,0.6448, 0.5698,0.8272,0.6446, 0.5804,0.8314,0.6444, 0.5910,0.8355,0.6443, 0.6016,0.8397,0.6441, 0.6122,0.8438,0.6440,
    0.6228,0.8480,0.6438, 0.6334,0.8521,0.6437, 0.6441,0.8563,0.6435, 0.6547,0.8604,0.6434, 0.6653,0.8646,0.6432, 0.6751,0.8685,0.6422,
    0.6842,0.8722,0.6404, 0.6933,0.8759,0.6385, 0.7023,0.8796,0.6367, 0.7114,0.8833,0.6348, 0.7205,0.8870,0.6330, 0.7296,0.8907,0.6311,
    0.7386,0.8943,0.6293, 0.7477,0.8980,0.6275, 0.7568,0.9017,0.6256, 0.7659,0.9054,0.6238, 0.7749,0.9091,0.6219, 0.7840,0.9128,0.6201,
    0.7931,0.9165,0.6182, 0.8022,0.9202,0.6164, 0.8112,0.9239,0.6145, 0.8203,0.9276,0.6127, 0.8294,0.9313,0.6108, 0.8384,0.9349,0.6090,
    0.8475,0.9386,0.6072, 0.8566,0.9423,0.6053, 0.8657,0.9460,0.6035, 0.8747,0.9497,0.6016, 0.8838,0.9534,0.5998, 0.8929,0.9571,0.5979,
    0.9020,0.9608,0.5961, 0.9058,0.9623,0.6021, 0.9097,0.9639,0.6081, 0.9135,0.9654,0.6141, 0.9173,0.9669,0.6201, 0.9212,0.9685,0.6261,
    0.9250,0.9700,0.6321, 0.9289,0.9715,0.6381, 0.9327,0.9731,0.6441, 0.9366,0.9746,0.6501, 0.9404,0.9762,0.6561, 0.9443,0.9777,0.6621,
    0.9481,0.9792,0.6681, 0.9519,0.9808,0.6740, 0.9558,0.9823,0.6800, 0.9596,0.9839,0.6860, 0.9635,0.9854,0.6920, 0.9673,0.9869,0.6980,
    0.9712,0.9885,0.7040, 0.9750,0.9900,0.7100, 0.9789,0.9915,0.7160, 0.9827,0.9931,0.7220, 0.9865,0.9946,0.7280, 0.9904,0.9962,0.7340,
    0.9942,0.9977,0.7400, 0.9981,0.9992,0.7460, 0.9999,0.9976,0.7450, 0.9998,0.9928,0.7370, 0.9996,0.9881,0.7290, 0.9995,0.9833,0.7210,
    0.9993,0.9785,0.7130, 0.9992,0.9738,0.7050, 0.9990,0.9690,0.6970, 0.9988,0.9642,0.6890, 0.9987,0.9595,0.6810, 0.9985,0.9547,0.6730,
    0.9984,0.9499,0.6651, 0.9982,0.9452,0.6571, 0.9981,0.9404,0.6491, 0.9979,0.9356,0.6411, 0.9978,0.9309,0.6331, 0.9976,0.9261,0.6251,
    0.9975,0.9213,0.6171, 0.9973,0.9166,0.6091, 0.9972,0.9118,0.6011, 0.9970,0.9070,0.5931, 0.9968,0.9023,0.5851, 0.9967,0.8975,0.5771,
    0.9965,0.8927,0.5691, 0.9964,0.8880,0.5611, 0.9962,0.8832,0.5531, 0.9961,0.8784,0.5451, 0.9959,0.8737,0.5371, 0.9958,0.8690,0.5291,
    0.9956,0.8642,0.5211, 0.9955,0.8595,0.5131, 0.9953,0.8547,0.5051, 0.9952,0.8500,0.4971, 0.9950,0.8452,0.4891, 0.9948,0.8405,0.4811,
    0.9947,0.8357,0.4731, 0.9945,0.8310,0.4651, 0.9944,0.8262,0.4571, 0.9942,0.8215,0.4491, 0.9941,0.8167,0.4411, 0.9939,0.8120,0.4331,
    0.9938,0.8072,0.4251, 0.9936,0.8025,0.4171, 0.9934,0.7977,0.4091, 0.9933,0.7930,0.4011, 0.9931,0.7882,0.3931, 0.9930,0.7835,0.3851,
    0.9928,0.7787,0.3771, 0.9927,0.7740,0.3691, 0.9925,0.7692,0.3611, 0.9924,0.7645,0.3531, 0.9922,0.7597,0.3451, 0.9921,0.7550,0.3371,
    0.9919,0.7502,0.3291, 0.9918,0.7455,0.3211, 0.9916,0.7407,0.3131, 0.9914,0.7360,0.3051, 0.9913,0.7312,0.2971, 0.9911,0.7265,0.2891,
    0.9910,0.7217,0.2811, 0.9908,0.7170,0.2731, 0.9907,0.7122,0.2651, 0.9905,0.7075,0.2571, 0.9904,0.7027,0.2491, 0.9902,0.6980,0.2411,
    0.9901,0.6932,0.2331, 0.9899,0.6885,0.2251, 0.9898,0.6837,0.2171, 0.9896,0.6790,0.2091, 0.9894,0.6742,0.2011, 0.9893,0.6695,0.1931,
    0.9891,0.6647,0.1851, 0.9890,0.6600,0.1771, 0.9888,0.6552,0.1691, 0.9887,0.6505,0.1611, 0.9885,0.6457,0.1531, 0.9883,0.6410,0.1451,
    0.9882,0.6362,0.1371, 0.9880,0.6315,0.1291, 0.9879,0.6267,0.1211, 0.9877,0.6220,0.1131, 0.9876,0.6172,0.1051, 0.9874,0.6125,0.0971,
    0.9873,0.6077,0.0891, 0.9871,0.6030,0.0811, 0.9870,0.5982,0.0731, 0.9868,0.5935,0.0651, 0.9867,0.5887,0.0571, 0.9865,0.5840,0.0491,
    0.9864,0.5792,0.0411, 0.9862,0.5745,0.0331, 0.9861,0.5697,0.0251, 0.9859,0.5650,0.0171, 0.9858,0.5602,0.0091, 0.9856,0.5555,0.0011,
    0.9854,0.5507,0.0000, 0.9853,0.5460,0.0000, 0.9851,0.5412,0.0000, 0.9850,0.5365,0.0000, 0.9848,0.5317,0.0000, 0.9847,0.5270,0.0000,
    0.9845,0.5222,0.0000, 0.9844,0.5175,0.0000, 0.9842,0.5127,0.0000, 0.9841,0.5080,0.0000, 0.9839,0.5032,0.0000, 0.9838,0.4985,0.0000,
    0.9836,0.4937,0.0000, 0.9835,0.4890,0.0000, 0.9833,0.4842,0.0000, 0.9832,0.4795,0.0000, 0.9830,0.4747,0.0000, 0.9829,0.4700,0.0000,
    0.9827,0.4652,0.0000, 0.9826,0.4605,0.0000, 0.9824,0.4557,0.0000, 0.9823,0.4510,0.0000, 0.9821,0.4462,0.0000, 0.9820,0.4415,0.0000,
    0.9818,0.4367,0.0000, 0.9817,0.4320,0.0000, 0.9815,0.4272,0.0000, 0.9814,0.4225,0.0000, 0.9812,0.4177,0.0000, 0.9811,0.4130,0.0000,
    0.9809,0.4082,0.0000, 0.9808,0.4035,0.0000, 0.9806,0.3987,0.0000, 0.9805,0.3940,0.0000, 0.9803,0.3892,0.0000, 0.9802,0.3845,0.0000,
    0.9800,0.3797,0.0000, 0.9799,0.3750,0.0000, 0.9797,0.3702,0.0000, 0.9796,0.3655,0.0000, 0.9794,0.3607,0.0000, 0.9793,0.3560,0.0000,
    0.9791,0.3512,0.0000, 0.9790,0.3465,0.0000, 0.9788,0.3417,0.0000, 0.9787,0.3370,0.0000, 0.9785,0.3322,0.0000, 0.9784,0.3275,0.0000,
    0.9782,0.3227,0.0000, 0.9781,0.3180,0.0000, 0.9779,0.3132,0.0000, 0.9778,0.3085,0.0000, 0.9776,0.3037,0.0000, 0.9775,0.2990,0.0000,
    0.9773,0.2942,0.0000, 0.9772,0.2895,0.0000, 0.9770,0.2847,0.0000, 0.9769,0.2800,0.0000, 0.9767,0.2752,0.0000, 0.9766,0.2705,0.0000,
    0.9764,0.2657,0.0000, 0.9763,0.2610,0.0000, 0.9761,0.2562,0.0000, 0.9760,0.2515,0.0000, 0.9758,0.2467,0.0000, 0.9757,0.2420,0.0000,
    0.9755,0.2372,0.0000, 0.9754,0.2325,0.0000, 0.9752,0.2277,0.0000, 0.9751,0.2230,0.0000, 0.9749,0.2182,0.0000, 0.9748,0.2135,0.0000,
    0.9746,0.2087,0.0000, 0.9745,0.2040,0.0000, 0.9743,0.1992,0.0000, 0.9742,0.1945,0.0000, 0.9740,0.1897,0.0000, 0.9739,0.1850,0.0000,
    0.9737,0.1802,0.0000, 0.9736,0.1755,0.0000, 0.9734,0.1707,0.0000, 0.9733,0.1660,0.0000, 0.9731,0.1612,0.0000, 0.9730,0.1565,0.0000,
    0.9728,0.1517,0.0000, 0.9727,0.1470,0.0000, 0.9725,0.1422,0.0000, 0.9724,0.1375,0.0000, 0.9722,0.1327,0.0000, 0.9721,0.1280,0.0000,
    0.9719,0.1232,0.0000, 0.9718,0.1185,0.0000, 0.9716,0.1137,0.0000, 0.9715,0.1090,0.0000, 0.9713,0.1042,0.0000, 0.9712,0.0995,0.0000,
    0.9710,0.0947,0.0000, 0.9709,0.0900,0.0000, 0.9707,0.0852,0.0000, 0.9706,0.0805,0.0000, 0.9704,0.0757,0.0000, 0.9703,0.0710,0.0000,
    0.9701,0.0662,0.0000, 0.9700,0.0615,0.0000, 0.9698,0.0567,0.0000, 0.9697,0.0520,0.0000, 0.9695,0.0472,0.0000, 0.9694,0.0425,0.0000,
    0.9692,0.0377,0.0000, 0.9691,0.0330,0.0000, 0.9689,0.0282,0.0000, 0.9688,0.0235,0.0000, 0.9686,0.0187,0.0000, 0.9685,0.0140,0.0000,
    0.9683,0.0092,0.0000, 0.9682,0.0045,0.0000, 0.9680,0.0000,0.0000,
]).reshape(-1, 3)
# fmt: on
_SPECTRAL_CMAP = LinearSegmentedColormap.from_list('spectral', _SPECTRAL_RGB)

# =============================================================================
#  FUNCTIONS
# =============================================================================

def _channel_color_and_scale(ch_name):
    """Return (color_name, amplitude_scale) based on channel name keywords."""
    n = ch_name.upper()
    if 'ECG' in n:
        return ('Magenta', 0.10)
    if 'EOG' in n:
        return ('Blue', 1.0)
    if 'EMG' in n:
        return ('Green', 1.0)
    if 'CHEST' in n or 'ABDOMEN' in n:
        return ('Black', 0.10)
    return ('Black', 1.0)


def load_edf(filepath, scale_to_uv=False):
    edf       = read_edf(filepath)
    srate     = int(edf.signals[0].sampling_frequency)
    ch_names  = [s.label for s in edf.signals]
    signals   = [s.data for s in edf.signals]
    max_len   = max(len(s) for s in signals)
    eeg_data  = np.array([
        np.pad(s, (0, max_len - len(s))) if len(s) < max_len else s
        for s in signals
    ])
    if scale_to_uv:
        eeg_data = eeg_data * 1e6
    return eeg_data, srate, ch_names


def _fig_to_image(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=_DPI)
    buf.seek(0)
    img = Image.open(buf)
    img.load()
    buf.close()
    plt.close(fig)
    return img


def create_hypnogram(stages, n_epochs, epoch_length_s, options, awakening_times_h=None, stimuli_times_h=None):
    digits      = np.array([s.get('digit') for s in stages], dtype=object)
    times       = np.arange(n_epochs) * epoch_length_s / 3600
    epoch_dur_h = epoch_length_s / 3600
    total_hours = n_epochs * epoch_length_s / 3600

    stage_colors   = {1: '#8bbf56', 0: '#dc5050', -1: '#aabcce', -2: '#405c79', -3: '#0b1c2c'}
    stage_y        = {1: 4, 0: 3, -1: 2, -2: 1, -3: 0}
    hyp_colors     = options.get('hyp_colors', 'all')
    show_line      = options.get('hyp_line', False)

    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=_DPI)

    for i, d in enumerate(digits):
        if d is None:
            continue
        if hyp_colors == 'none':
            continue
        if hyp_colors == 'rem' and d != 0:
            continue
        color = stage_colors.get(d, '#cccccc')
        y     = stage_y.get(d, 2)
        ax.barh(y, epoch_dur_h, left=times[i], height=0.7, color=color, edgecolor='none')

    if show_line:
        lx, ly = [], []
        for i, d in enumerate(digits):
            if d is not None and d in stage_y:
                lx.append(times[i] + epoch_dur_h / 2)
                ly.append(stage_y[d])
        if lx:
            ax.plot(lx, ly, color='black', linewidth=1.5, zorder=5)

    if awakening_times_h:
        ax.scatter(awakening_times_h, [4.35] * len(awakening_times_h),
                   marker='*', color='magenta', s=80, zorder=10, linewidths=0)

    if stimuli_times_h:
        ax.scatter(stimuli_times_h, [0.5] * len(stimuli_times_h),
                   marker='^', color='magenta', s=50, zorder=10, linewidths=0)

    ax.set_ylim(-0.5, 4.5)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(['N3', 'N2', 'N1', 'REM', 'Wake'], fontsize=12)
    ax.set_xlim(0, total_hours)
    ax.set_xticks(range(int(total_hours) + 1))
    ax.set_xticklabels([f'{h}h' for h in range(int(total_hours) + 1)], fontsize=11)
    ax.set_xlabel('Time (0h = recording start)', fontsize=11)
    ax.grid(axis='x', alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_title('Hypnogram', loc='left', fontsize=11, fontweight='bold', pad=4)
    fig.subplots_adjust(left=_PLT_LEFT, right=_PLT_RIGHT, bottom=_PLT_BOTTOM, top=0.88)
    return _fig_to_image(fig)


def create_spectrogram(power_mat, freqs, n_epochs, epoch_length_s, channel_name):
    cmap  = _SPECTRAL_CMAP
    power = np.log10(np.maximum(power_mat, 1e-30))
    power = np.clip(power, -1, 3)
    times = np.arange(n_epochs) * epoch_length_s / 3600

    spec_top = 0.88
    fig      = plt.figure(figsize=_FIG_SIZE, dpi=_DPI)
    ax_w     = _PLT_RIGHT - _PLT_LEFT
    ax_h     = spec_top - _PLT_BOTTOM
    ax       = fig.add_axes([_PLT_LEFT, _PLT_BOTTOM, ax_w, ax_h])
    cbar_ax  = fig.add_axes([_PLT_RIGHT + 0.015, _PLT_BOTTOM, _CBAR_W, ax_h])

    im = ax.pcolormesh(times, freqs, power.T, cmap=cmap, shading='auto', vmin=-1, vmax=3)
    ax.set_xlabel('Time (0h = recording start)', fontsize=11)
    ax.set_ylabel('Frequency (Hz)', fontsize=11)
    ax.set_ylim(1, 30)
    total_hours = n_epochs * epoch_length_s / 3600
    ax.set_xticks(range(int(total_hours) + 1))
    ax.set_xticklabels([f'{h}h' for h in range(int(total_hours) + 1)], fontsize=11)
    ax.tick_params(axis='y', labelsize=11)
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.set_label('Power (dB)', fontsize=10)
    ax.set_title(f'Spectrogram ({channel_name})', loc='left', fontsize=11, fontweight='bold', pad=4)
    return _fig_to_image(fig)


def create_eeg_trace(eeg_data, srate, epoch_length_s, ch_names, ch_colors, ch_scales, stages, options):
    epoch_numbers   = options.get('trace_epochs', [])
    channel_indices = options.get('trace_channels', [])
    if not epoch_numbers or not channel_indices:
        return None

    epo_samp        = int(epoch_length_s * srate)
    n_total_samples = eeg_data.shape[1]
    ref_amp         = 100   # µV reference lines

    segments = []
    for ep_num in epoch_numbers:
        start = (ep_num - 1) * epo_samp
        end   = min(start + epo_samp, n_total_samples)
        segments.append(eeg_data[:, start:end])
    signal   = np.concatenate(segments, axis=1)
    t_sec    = np.arange(signal.shape[1]) / srate

    n_sel   = len(channel_indices)
    spacing = 200
    offsets = [(n_sel - 1 - pi) * spacing for pi in range(n_sel)]

    fig_height = max(2.5, 1.0 + 0.65 * n_sel)
    bottom_frac = 0.55 / fig_height
    top_frac    = 1.0 - 0.35 / fig_height

    fig, ax = plt.subplots(figsize=(12, fig_height), dpi=_DPI)

    scaled_refs = []
    for pi, ch_idx in enumerate(channel_indices):
        color_name = ch_colors[ch_idx] if ch_idx < len(ch_colors) else 'Black'
        ch_color   = _CH_COLORS.get(color_name, (0, 0, 0))
        scale      = ch_scales[ch_idx] if ch_idx < len(ch_scales) else 1.0
        scaled_refs.append(ref_amp * scale)
        ax.plot(t_sec, signal[ch_idx] * scale + offsets[pi], color=ch_color, linewidth=0.7)

    sel_names = [ch_names[i] for i in channel_indices if i < len(ch_names)]
    ax.set_yticks(offsets)
    ax.set_yticklabels(sel_names, fontsize=10)
    ax.set_ylim(-scaled_refs[-1] - 50, (n_sel - 1) * spacing + scaled_refs[0] + 50)
    ax.set_xlabel('Time (s)', fontsize=11)
    ax.set_xlim(0, t_sec[-1] if len(t_sec) else 1)
    ax.tick_params(axis='x', labelsize=11)
    ax.grid(axis='x', alpha=0.3)
    ax.set_axisbelow(True)

    for offset, sr in zip(offsets, scaled_refs):
        ax.axhline(offset - sr, color='gray', linewidth=0.3, linestyle='--', alpha=0.4)
        ax.axhline(offset + sr, color='gray', linewidth=0.3, linestyle='--', alpha=0.4)

    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    mid = 0 # n_sel - 1
    ref_ticks  = [offsets[mid] + scaled_refs[mid], offsets[mid], offsets[mid] - scaled_refs[mid]]
    ref_labels = [f'+{ref_amp:.0f} µV', '0 µV', f'-{ref_amp:.0f} µV']
    ax2.set_yticks(ref_ticks)
    ax2.set_yticklabels(ref_labels, fontsize=9)

    stage_name = 'Unscored'
    if epoch_numbers and stages:
        idx = epoch_numbers[0] - 1
        if 0 <= idx < len(stages):
            s = stages[idx].get('stage')
            if s:
                stage_name = s
    ax.set_title(f'Example traces of one epoch ({stage_name})', loc='left', fontsize=11, fontweight='bold', pad=4)
    fig.subplots_adjust(left=_PLT_LEFT, right=_PLT_RIGHT, bottom=bottom_frac, top=top_frac)
    return _fig_to_image(fig)


def calculate_sleep_statistics(stages, epoch_length_s, options):
    digits          = np.array([s.get('digit') for s in stages], dtype=object)
    epoch_length_min = epoch_length_s / 60

    scored_mask  = np.array([d is not None for d in digits])
    scored_epochs = np.sum(scored_mask)
    wake_epochs  = np.sum(digits == 1)
    n1_epochs    = np.sum(digits == -1)
    n2_epochs    = np.sum(digits == -2)
    n3_epochs    = np.sum(digits == -3)
    rem_epochs   = np.sum(digits == 0)
    sleep_epochs = scored_epochs - wake_epochs

    tst_min         = sleep_epochs * epoch_length_min
    trt_min         = scored_epochs * epoch_length_min
    sleep_efficiency = (tst_min / trt_min * 100) if trt_min > 0 else 0

    lines = []

    if options.get('sleep_stats'):
        lines += [
            'SLEEP STATISTICS',
            '-' * 50,
            f"{'Total Sleep Time (TST):':<31}{tst_min:.1f} min ({tst_min/60:.1f} h)",
            f"{'Total Recording Time (TRT):':<31}{trt_min:.1f} min ({trt_min/60:.1f} h)",
            f"{'Sleep Efficiency:':<31}{sleep_efficiency:.1f}%",
        ]

    if options.get('stage_distribution'):
        pct = lambda n: (n / scored_epochs * 100) if scored_epochs > 0 else 0
        if lines:
            lines.append('')
        lines += [
            'SLEEP STAGE DISTRIBUTION',
            '-' * 50,
            f"{'Wake:':<31}{wake_epochs*epoch_length_min:.1f} min ({wake_epochs*epoch_length_min/60:.1f} h) - {pct(wake_epochs):.1f}%",
            f"{'REM:':<31}{rem_epochs*epoch_length_min:.1f} min ({rem_epochs*epoch_length_min/60:.1f} h) - {pct(rem_epochs):.1f}%",
            f"{'N1:':<31}{n1_epochs*epoch_length_min:.1f} min ({n1_epochs*epoch_length_min/60:.1f} h) - {pct(n1_epochs):.1f}%",
            f"{'N2:':<31}{n2_epochs*epoch_length_min:.1f} min ({n2_epochs*epoch_length_min/60:.1f} h) - {pct(n2_epochs):.1f}%",
            f"{'N3:':<31}{n3_epochs*epoch_length_min:.1f} min ({n3_epochs*epoch_length_min/60:.1f} h) - {pct(n3_epochs):.1f}%",
        ]

    if options.get('latencies'):
        def latency(target):
            idx = np.where(digits == target)[0]
            return idx[0] * epoch_length_min if len(idx) > 0 else None
        n2_lat  = latency(-2)
        n3_lat  = latency(-3)
        rem_lat = latency(0)
        if lines:
            lines.append('')
        lines += [
            'LATENCIES',
            '-' * 50,
            f"{'N2 latency:':<31}{n2_lat:.1f} min"  if n2_lat  is not None else f"{'N2 latency:':<31}N/A",
            f"{'N3 latency:':<31}{n3_lat:.1f} min"  if n3_lat  is not None else f"{'N3 latency:':<31}N/A",
            f"{'REM latency:':<31}{rem_lat:.1f} min" if rem_lat is not None else f"{'REM latency:':<31}N/A",
        ]

    if options.get('awakenings') or options.get('arousals'):
        sleep_set   = {-3, -2, 0}
        scored_list = [d for d in digits.tolist() if d is not None]
        n           = len(scored_list)
        sleep_pos   = [i for i, d in enumerate(scored_list) if d in sleep_set]
        last_sleep  = sleep_pos[-1] if sleep_pos else None

    if options.get('awakenings'):
        n3w = n2w = remw = 0
        awk_durs = []
        if last_sleep is not None:
            i = 1
            while i < n:
                prev, curr = scored_list[i - 1], scored_list[i]
                if curr == 1 and prev in sleep_set and i < last_sleep:
                    if prev == -3: n3w += 1
                    elif prev == -2: n2w += 1
                    elif prev == 0:  remw += 1
                    j = i
                    while j < n and scored_list[j] == 1:
                        j += 1
                    awk_durs.append((j - i) * epoch_length_min)
                    i = j
                else:
                    i += 1
        total_awk = n3w + n2w + remw
        avg_awk   = f'{np.mean(awk_durs):.1f} min' if awk_durs else 'N/A'
        if lines:
            lines.append('')
        lines += [
            'AWAKENINGS',
            '-' * 50,
            f"{'N3 -> Wake:':<31}{n3w}",
            f"{'N2 -> Wake:':<31}{n2w}",
            f"{'REM -> Wake:':<31}{remw}",
            f"{'Total:':<31}{total_awk}",
            f"{'Avg. duration:':<31}{avg_awk}",
        ]

    if options.get('arousals'):
        if last_sleep is not None:
            n3n1  = sum(1 for i in range(1, n) if scored_list[i] == -1 and scored_list[i-1] == -3)
            n2n1  = sum(1 for i in range(1, n) if scored_list[i] == -1 and scored_list[i-1] == -2)
            remn1 = sum(1 for i in range(1, n) if scored_list[i] == -1 and scored_list[i-1] == 0)
        else:
            n3n1 = n2n1 = remn1 = 0
        total_arousals = n3n1 + n2n1 + remn1
        if lines:
            lines.append('')
        lines += [
            'STAGE TRANSITION DUE TO AROUSAL',
            '-' * 50,
            f"{'N3 -> N1:':<31}{n3n1}",
            f"{'N2 -> N1:':<31}{n2n1}",
            f"{'REM -> N1:':<31}{remn1}",
            f"{'Total:':<31}{total_arousals}",
        ]

    return '\n'.join(lines)


def create_pdf_report(filepath, hypnogram_img, spectrogram_img, trace_img, stats_text, report_name=None, stats_new_page=False, show_awakenings=False, show_stimuli=False):
    page_w, page_h = letter
    c = canvas.Canvas(filepath, pagesize=letter)

    left_x      = 0.5 * inch
    bottom_m    = 0.5 * inch
    plot_width  = page_w - 2 * left_x
    plot_height = plot_width * _FIG_SIZE[1] / _FIG_SIZE[0]
    current_y   = page_h - 0.75 * inch
    tmp_files   = []

    def new_page():
        nonlocal current_y
        c.showPage()
        current_y = page_h - bottom_m

    def save_img(img):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            tmp_files.append(f.name)
            return f.name

    try:
        c.setFont('Helvetica-Bold', 16)
        c.drawString(left_x, page_h - 0.55 * inch, 'Sleep Report')
        if report_name:
            c.setFont('Helvetica', 10)
            c.drawString(left_x, current_y, report_name)
            current_y -= 0.25 * inch
        current_y -= 0.1 * inch

        if hypnogram_img is not None:
            if current_y - plot_height < bottom_m:
                new_page()
            path = save_img(hypnogram_img)
            c.drawImage(path, left_x, current_y - plot_height, width=plot_width, height=plot_height)
            current_y -= plot_height
            show_awk  = show_awakenings
            show_stim = show_stimuli
            if show_awk or show_stim:
                from reportlab.lib.colors import magenta, black
                c.setFont('Helvetica', 8)
                caption_y = current_y - 0.14 * inch
                if show_awk:
                    c.setFillColor(magenta)
                    c.drawString(left_x, caption_y, '*')
                    c.setFillColor(black)
                    c.drawString(left_x + 0.10 * inch, caption_y, 'indicate alarm sounds, which were followed by a structured interview')
                    caption_y -= 0.13 * inch
                if show_stim:
                    c.setFillColor(magenta)
                    c.drawString(left_x, caption_y, '\u25b2')
                    c.setFillColor(black)
                    c.drawString(left_x + 0.12 * inch, caption_y, 'indicate auditory stimuli presented during sleep')
                    caption_y -= 0.13 * inch
                current_y = caption_y - 0.02 * inch
            else:
                current_y -= 0.15 * inch

        if spectrogram_img is not None:
            if current_y - plot_height < bottom_m:
                new_page()
            path = save_img(spectrogram_img)
            c.drawImage(path, left_x, current_y - plot_height, width=plot_width, height=plot_height)
            current_y -= plot_height + 0.15 * inch

        if trace_img is not None:
            trace_height = plot_width * (trace_img.height / trace_img.width)
            if current_y - trace_height < bottom_m:
                new_page()
            path = save_img(trace_img)
            c.drawImage(path, left_x, current_y - trace_height, width=plot_width, height=trace_height)
            current_y -= trace_height + 0.15 * inch

        if stats_text:
            if stats_new_page:
                new_page()
            c.setFont('Courier', 9)
            text_y = current_y - 0.25 * inch
            for line in stats_text.split('\n'):
                if text_y < bottom_m:
                    new_page()
                    c.setFont('Courier', 9)
                    text_y = current_y
                c.drawString(left_x, text_y, line)
                text_y -= 0.12 * inch

        c.save()
    finally:
        for path in tmp_files:
            try:
                os.unlink(path)
            except OSError:
                pass

# =============================================================================
#  PROCESS ONE FILE
# =============================================================================

def process_file(edf_file, scoring_file, output_pdf, report_name):
    # --- Load EDF ---
    print(f'Loading EDF: {edf_file}')
    eeg_data, srate, ch_names = load_edf(edf_file, scale_to_uv=SCALE_TO_UV)

    epo_samp = round(EPOCH_LENGTH_S * srate)
    n_epochs = eeg_data.shape[1] // epo_samp
    eeg_data = eeg_data[:, : n_epochs * epo_samp]
    print(f'  {eeg_data.shape[0]} channels  {srate:.0f} Hz  {n_epochs} epochs')

    # --- Load scoring JSON ---
    print(f'Loading scoring: {scoring_file}')
    with open(scoring_file) as f:
        raw = json.load(f)
    stages = raw[0]     # raw = [stages_array, annotations_array]

    for i in range(len(stages), n_epochs):
        stages.append({
            'epoch': i + 1, 'start': i * EPOCH_LENGTH_S, 'end': (i + 1) * EPOCH_LENGTH_S,
            'stage': None, 'digit': None, 'confidence': None,
            'channels': [], 'clean': 1, 'source': None,
        })

    # --- Compute spectrogram ---
    if SHOW_SPECTROGRAM:
        print('Computing spectrogram...')
        win_len   = int(4 * srate)
        hop_len   = int(2 * srate)
        ch_sig    = eeg_data[SPEC_CHANNEL]
        freqs, _  = welch(ch_sig[:epo_samp], srate, window='hann',
                          nperseg=win_len, noverlap=win_len - hop_len,
                          detrend='constant', scaling='density')
        power_mat = np.zeros((n_epochs, len(freqs)))
        for ep in range(n_epochs):
            seg = ch_sig[ep * epo_samp : (ep + 1) * epo_samp]
            _, pxx = welch(seg, srate, window='hann',
                           nperseg=win_len, noverlap=win_len - hop_len,
                           detrend='constant', scaling='density')
            power_mat[ep] = pxx
    else:
        freqs     = np.array([])
        power_mat = np.array([])

    # --- Generate PDF ---
    ch_cs     = [_channel_color_and_scale(n) for n in ch_names]
    ch_colors = [cs[0] for cs in ch_cs]
    ch_scales = [cs[1] for cs in ch_cs]

    options = {
        'hypnogram':            SHOW_HYPNOGRAM,
        'hyp_line':             HYP_SHOW_LINE,
        'hyp_colors':           HYP_COLORS,
        'hyp_mark_awakenings':  HYP_MARK_AWAKENINGS,
        'hyp_mark_stimuli':     HYP_MARK_STIMULI,
        'spectrogram':          SHOW_SPECTROGRAM,
        'sleep_stats':          SHOW_SLEEP_STATS,
        'stage_distribution':   SHOW_STAGE_DIST,
        'latencies':            SHOW_LATENCIES,
        'awakenings':           SHOW_AWAKENINGS,
        'arousals':             SHOW_AROUSALS,
        'trace':                INCLUDE_TRACE,
        'trace_epochs':         TRACE_EPOCHS if INCLUDE_TRACE else [],
        'trace_channels':       TRACE_CHANNELS if INCLUDE_TRACE else [],
    }

    print('Generating report...')
    any_stats = any(options[k] for k in ('sleep_stats', 'stage_distribution', 'latencies', 'awakenings', 'arousals'))

    awakening_times_h = []
    stimuli_times_h   = []
    if (options['hyp_mark_awakenings'] or options['hyp_mark_stimuli']) and options['hypnogram']:
        last_ch = eeg_data[-1]
        diff    = np.diff(last_ch)
        onsets  = np.where(diff > 50)[0]
        for onset in onsets:
            search  = diff[onset + 1:]
            offsets = np.where(search < -5)[0]
            if len(offsets) == 0:
                continue
            offset   = onset + 1 + offsets[0]
            duration = (offset - onset) / srate
            if duration > 1.0:
                if options['hyp_mark_awakenings']:
                    awakening_times_h.append(onset / srate / 3600)
            else:
                if options['hyp_mark_stimuli']:
                    stimuli_times_h.append(onset / srate / 3600)
        print(f'  Awakenings detected: {len(awakening_times_h)}')
        print(f'  Auditory stimuli detected: {len(stimuli_times_h)}')

    hypnogram_img   = create_hypnogram(stages, n_epochs, EPOCH_LENGTH_S, options, awakening_times_h, stimuli_times_h) if options['hypnogram']   else None
    spectrogram_img = create_spectrogram(power_mat, freqs, n_epochs, EPOCH_LENGTH_S,
                                         ch_names[SPEC_CHANNEL])                            if options['spectrogram'] else None
    trace_img       = create_eeg_trace(eeg_data, srate, EPOCH_LENGTH_S, ch_names,
                                       ch_colors, ch_scales, stages, options)               if options['trace']       else None
    stats_text      = calculate_sleep_statistics(stages, EPOCH_LENGTH_S, options)           if any_stats              else None

    stats_new_page = (INCLUDE_TRACE and SHOW_HYPNOGRAM and SHOW_SPECTROGRAM and len(TRACE_CHANNELS) > 3)
    create_pdf_report(output_pdf, hypnogram_img, spectrogram_img, trace_img, stats_text, report_name,
                      stats_new_page=stats_new_page,
                      show_awakenings=options['hyp_mark_awakenings'],
                      show_stimuli=options['hyp_mark_stimuli'])
    print(f'Report saved: {output_pdf}')


def _paths_from_json(json_path):
    """Derive EDF path, output PDF path, and report name from a JSON scoring file path."""
    stem = os.path.splitext(os.path.basename(json_path))[0]   # e.g. sub-hpmam003_ses-S1_..._Checked
    base = stem.replace('_Checked', '')                         # e.g. sub-hpmam003_ses-S1_...
    edf_path    = os.path.join(EDF_DIR,    base + '_filtered.edf')
    output_path = os.path.join(OUTPUT_DIR, base + '.pdf')
    report_name = '_'.join(base.split('_')[:2])                 # sub-hpmam003_ses-S1
    return edf_path, output_path, report_name


# =============================================================================
#  ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate sleep report PDF(s).')
    parser.add_argument('--json', metavar='FILE',
                        help='Path to a single scoring JSON file (single-file mode). '
                             'Omit to process all JSON files in JSON_DIR (batch mode).')
    parser.add_argument('--overwrite', action='store_true',
                        help='In batch mode, overwrite PDFs that already exist (default: skip).')
    args = parser.parse_args()

    if args.json:
        # Single-file mode
        edf_path, output_path, report_name = _paths_from_json(args.json)
        process_file(edf_path, args.json, output_path, report_name)
    else:
        # Batch mode — iterate over all JSON files in JSON_DIR
        json_files = sorted(_glob.glob(os.path.join(JSON_DIR, '*.json')))
        print(f'Found {len(json_files)} JSON file(s) in {JSON_DIR}')
        for json_path in json_files:
            edf_path, output_path, report_name = _paths_from_json(json_path)
            if not os.path.exists(edf_path):
                print(f'[SKIP] EDF not found: {edf_path}')
                continue
            if not args.overwrite and os.path.exists(output_path):
                print(f'[SKIP] PDF already exists: {output_path}')
                continue
            process_file(edf_path, json_path, output_path, report_name)
