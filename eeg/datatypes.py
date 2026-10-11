from collections import namedtuple

from .load_bdf import load_bdf
from .load_edf import load_edf
from .load_eeglab import load_eeglab
from .load_r09 import load_r09

# One entry per supported EEG file type: the file dialog filter and a loader
# (filename_prefix -> (eeg_data, srate, channel_names, units)). Add a new type here.
Datatype = namedtuple("Datatype", "file_filter load")

DATATYPES = {
    "eeglab": Datatype("*.mat", load_eeglab),
    "r09": Datatype("*.r09", load_r09),
    "edf": Datatype("*.edf", load_edf),
    "edfvolt": Datatype("*.edf", lambda prefix: load_edf(prefix, scale_to_uv=True)),
    "bdf": Datatype("*.bdf", load_bdf),
}
