from pathlib import Path
import os

PROJECT_ROOT = os.path.abspath(os.curdir) #[2]
DATA_PATH = PROJECT_ROOT + "\\data\\"

WAV_CHUNKS = DATA_PATH + "wav_chunks\\"
SPECTROGRAMS = DATA_PATH + "spectrograms\\"
PREPROCESSED = DATA_PATH + "preprocessed_wav\\"