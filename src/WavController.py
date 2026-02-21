import os
from librosa.filters import mel
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

from src.config import WAV_CHUNKS, SPECTROGRAMS, PREPROCESSED

class WavController():


    def __init__(self, file_path=None, chunk_length=3):
        self.chunk_length = chunk_length
        self.file_path = file_path
        #self.sample_rate, self.audio_data = wavfile.read(file_path)
        if file_path is not None: self.load_audio(file_path)
        else: self.audio_data, self.sample_rate = None, None

        self.file_name = os.path.basename(file_path).split(".")[0] #[1]

        #Spectrogram parameters, advised by Kahl, C. M. Wood, et al 2021
        self.window_length = 512
        self.num_mel_bands = 64
        self.overlap = self.window_length//4
        self.max_freq = 15000
        self.min_freq = 150

    def load_audio(self, file_path):
        self.audio_data, self.sample_rate = librosa.load(file_path, mono=True, dtype=float)

    def make_chunks(self, overlap=False):
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
        

        mel_spectrogram = librosa.feature.melspectrogram(
            y=chunk, 
            sr=self.sample_rate, 
            n_fft=self.window_length, 
            n_mels=self.num_mel_bands, 
            hop_length=self.overlap,
            fmin = self.min_freq,
            fmax = self.max_freq
        )


        if save:
            pass
            #TODO: save specs

        return mel_spectrogram

    def save_chunks(self, chunks):
        if not os.path.exists(WAV_CHUNKS / self.file_name):
            os.makedirs(WAV_CHUNKS / self.file_name)

        #TODO: probably not


if __name__ == "__main__":
    wav_controller = WavController(PREPROCESSED + "Weaveley_BIRD_HedgerowNorth_20240605_184000.WAV")
    chunks = wav_controller.make_chunks()

    y = chunks[100]

    mel_spec = wav_controller.create_spectrogram(y)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    fig, ax = plt.subplots(3, 1, figsize=(25,20), constrained_layout=True)

    librosa.display.waveshow(y, sr=wav_controller.sample_rate, ax=ax[0])
    ax[0].set(title="Audio Waveform")
    ax[0].set_ylabel("Amplitude")
    ax[0].set_xlim(0,3)

    ax[1].sharex(ax[2])
    img = librosa.display.specshow(mel_spec, sr=wav_controller.sample_rate, x_axis="time", y_axis="mel", ax=ax[1])
    ax[1].set(title="Mel Spectrogram (Linear)")
    fig.colorbar(img, ax=ax[1])

    img = librosa.display.specshow(mel_spec_db, sr=wav_controller.sample_rate, x_axis="time", y_axis="mel", ax=ax[2])
    ax[2].set(title="Mel Spectrogram (Log dB)")

    fig.colorbar(img, ax=ax[2], format="%+2.0f dB")

    #plt.tight_layout()
    plt.show()