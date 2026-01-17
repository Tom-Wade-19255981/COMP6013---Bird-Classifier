import sys, os
from scipy.io import wavfile
from librosa.filters import mel
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

from src.config import WAV_CHUNKS, SPECTROGRAMS, PREPROCESSED

class WavController:
    def __init__(self, file_path, chunk_length=3):
        self.chunk_length = chunk_length
        self.file_path = file_path
        #self.sample_rate, self.audio_data = wavfile.read(file_path)
        self.audio_data, self.sample_rate = librosa.load(file_path)
        self.file_name = os.path.basename(file_path).split(".")[0] #[1]


    def make_chunks(self):
        """
        Splits the wav file into chunks, overlapping each clip as to not miss start/end of a bird call.

        Returns
            numpy array of audio chunks
        """
        chunk_size = int(self.chunk_length * self.sample_rate)
        overlap_size = chunk_size//3 #1 second of overlap between chunks

        chunks = [
            self.audio_data[chunk:chunk+chunk_size]
            for chunk in range(0, len(self.audio_data) - chunk_size + 1, overlap_size)
        ]

        return chunks

    def create_spectrogram(self, chunk, save=False):
        filter_banks = mel(n_fft=512, n_mels=64, sr=self.sample_rate)

        mel_spectrogram = librosa.feature.melspectrogram(y=chunk, sr=self.sample_rate, n_fft=512, n_mels=64, hop_length=128)

        plt.figure(figsize=(50,20))
        librosa.display.specshow(mel_spectrogram, sr=self.sample_rate)
        plt.show()

        if save:
            pass
            #TODO: save specs

    def save_chunks(self, chunks):
        if not os.path.exists(WAV_CHUNKS / self.file_name):
            os.makedirs(WAV_CHUNKS / self.file_name)

        #TODO: probably not

wav_controller = WavController(PREPROCESSED + "Weaveley_BIRD_HedgerowNorth_20240605_184000.WAV")
chunks = wav_controller.make_chunks()

wav_controller.create_spectrogram(chunks[102])

# plt.figure(figsize=(20,5))
# librosa.display.waveshow(wav_controller.audio_data, sr=wav_controller.sample_rate)
# plt.title('Waveplot')
# plt.xlabel('Time')
# plt.ylabel('Amplitude')
# plt.show()