from pathlib import Path
import os

PROJECT_ROOT = os.path.abspath(os.curdir) + "\\" #[2]
DATA_PATH = PROJECT_ROOT + "data\\"

WAV_PATH = DATA_PATH + "wav_files\\"
WAV_CHUNKS = WAV_PATH + "wav_chunks\\"
FULL_WAV = WAV_PATH + "full_wav\\"

LABELS = DATA_PATH + "labels\\"
SPECTROGRAMS = DATA_PATH + "spectrograms\\"
PREPROCESSED = DATA_PATH + "preprocessed_wav\\"

#We should review this closer to end time, probably bad to require external file structure
# CSV_DATA = PROJECT_ROOT + "..\\csv_bird_data\\"

CSV_DATA = DATA_PATH + "csv_files\\"
FULL_CSV = CSV_DATA + "full_csv\\"
SPLIT_CSV = CSV_DATA + "split_csv\\"