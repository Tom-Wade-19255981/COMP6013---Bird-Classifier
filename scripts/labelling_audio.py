import os

import numpy as np
import pandas as pd

import csv
import glob

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkwidgets import Table

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import RectangleSelector

import librosa
import librosa.display
import soundfile as sf

import sounddevice as sd


#from src import WavController
from src.config import SPECTROGRAMS, FULL_WAV, WAV_CHUNKS, LABELS, SPLIT_CSV, LABELS, SPECTROGRAMS


#TODO:
#1) add export

# Config constants:
CHUNK_SECONDS = 3.0
N_FFT = 512
HOP = N_FFT//4
N_MELS = 64
MIN_FREQ = 150
MAX_FREQ = 15000

CLASSES = ["Eurasian_Skylark", "Yellowhammer", "European Goldfinch", 
        "Eurasian Linnet", "European Robin", "Spotted Flycatcher", "Dunnock", 
        "Eurasian Magpie", "Unknown Bird"]
DEFAULT_CLASS = CLASSES[-1]

os.makedirs(LABELS, exist_ok=True)
os.makedirs(SPECTROGRAMS, exist_ok=True)
os.makedirs(FULL_WAV, exist_ok=True)
os.makedirs(WAV_CHUNKS, exist_ok=True)

#Rectangle Select requires parameters (eclick, erelease), cannot be used as method inside class
def on_select_box(eclick, erelease):
    labelling.draw_box(eclick, erelease)

class SpectrogramLabeller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spectrogram Labeller")
        self.geometry("1200x720")

        #State vars
        self.wav_path = None
        self.csv_path = None
        self.sample_rate = None
        self.audio = None
        self.t_start = 0.0
        self.audio_chunk = None
        self.duration = None

        self.current_class = DEFAULT_CLASS
        self.labels = []
        self.boundaries = []

        # --- Layout ---
        self._build_ui_()

        # --- Put matplotlib figure in tk ---
        self.fig, self.ax = plt.subplots(1,1,figsize=(7.5,4.5))
        self.color_bar = None
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.spec_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Rectangle selector for labelling ---
        self.boundary_selector = RectangleSelector(
            self.ax,
            on_select_box,
            useblit=True,
            button=[1], #left click
            interactive=True,
            spancoords="data",
            drag_from_anywhere=True
        )

        self.keybinds={"deselect":"Escape"}
        self.bind("<Key>", self.on_key_press)

        self._refresh_status()

    # ---------- TTK Window Actions ----------
    def _build_ui_(self):
        """Builds the UI for the program, called at instantiation."""


        # ------ Top panel buttons ------

        # ------ Row 0 ------
        top_panel = ttk.Frame(self)
        top_panel.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        ttk.Button(top_panel, text="Select .wav", command=self.select_wav).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_panel, text="Select .csv", command=self.select_csv).pack(side=tk.LEFT, padx=4)

        ttk.Label(top_panel, text="Start (s): ").pack(side=tk.LEFT, padx=(16,4))
        self.start_var = tk.StringVar(value="0.0")
        start_entry = ttk.Entry(top_panel, textvariable=self.start_var, width=10)
        start_entry.pack(side=tk.LEFT)
        ttk.Button(top_panel, text="Load chunk", command=self.load_chunk_from_entry).pack(side=tk.LEFT, padx=6)

        ttk.Button(top_panel, text="Play chunk", command=self.play_chunk).pack(side=tk.LEFT, padx=(16,4))
        ttk.Button(top_panel, text="Stop", command=self.stop_playback).pack(side=tk.LEFT, padx=4)

        ttk.Button(top_panel, text="Save export", command=self.export_current_chunk).pack(side=tk.RIGHT, padx=4)

        # ------ Row 1 ------
        class_frame = ttk.Frame(self)
        class_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0,8))
        ttk.Label(class_frame, text="Class:").pack(side=tk.LEFT, padx=(0,6))

        self.class_var = tk.StringVar(value=self.current_class)
        class_menu = ttk.OptionMenu(class_frame, self.class_var, self.current_class, *CLASSES, command=self.on_class_change)
        class_menu.pack(side=tk.LEFT)

        ttk.Button(class_frame, text="Delete last box", command=self.delete_last_box).pack(side=tk.LEFT, padx=10)
        ttk.Button(class_frame, text="Clear boxes", command=self.clear_boxes).pack(side=tk.LEFT)

        
        # ------ Main frame: spectrogram + labels || CSV table ------
        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # ------ Spectrogram + labels frame ------
        spec_and_boundary_labels = ttk.PanedWindow(main, orient=tk.VERTICAL)
        spec_and_boundary_labels.pack(fill=tk.Y, expand=True)
        main.add(spec_and_boundary_labels, weight=4)


        self.spec_frame = ttk.Frame(spec_and_boundary_labels)
        spec_and_boundary_labels.add(self.spec_frame, weight=9)


        self.boundary_cols = ("label","t0","t1","f0","f1")
        self.boundary_table = Table(spec_and_boundary_labels, columns=self.boundary_cols, sortable=False, drag_cols=False, drag_rows=False)

        for col in self.boundary_cols:
            self.boundary_table.heading(col, text=col)
            self.boundary_table.column(col, width=125, stretch=False)
            if len(col) == 2: self.boundary_table.column(col, type=float)


        spec_and_boundary_labels.add(self.boundary_table, weight=1)

        #print(dir(self.boundary_table))


        # ------ BirdNET Csv ------

        self.table_frame = ttk.Frame(main)
        main.add(self.table_frame, weight=2)

        cols = ("Start (s)", "End (s)", "Location", "SciName", "CommonName", "Confidence")
        ttk.Label(self.table_frame, text="BirdNet Labels").pack(side=tk.TOP, anchor="w")
        self.label_table = Table(self.table_frame, columns=cols, sortable=False, drag_cols=False, drag_rows=False)


        for col in cols:
            self.label_table.heading(col, text=col)
            self.label_table.column(col, width=90)
        self.label_table.pack(fill=tk.BOTH, expand=True, pady=(6,0))


        self.status_label = tk.StringVar()
        self.status_label.set("none")

        self.status = ttk.Label(self, text=self.status_label, relief=tk.SUNKEN, anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _refresh_status(self):
        """Refreshes the contents shown to user, called upon update of variables"""

        wav = os.path.basename(self.wav_path) if self.wav_path else "(none)"
        csv = os.path.basename(self.csv_path) if self.csv_path else "(none)"
        self.status_label.set(f"Wav: {wav} | CSV: {csv} | Start: {self.t_start:.3f}s | Chunk: {CHUNK_SECONDS:.1f}s | Class: {self.current_class}")

    def on_key_press(self, event):
        if event.keysym == self.keybinds["deselect"]:
            toggle = True if self.boundary_selector.get_active else False
            self.boundary_selector.set_active(toggle)

        
    

    # ---------- File Selection ----------
    def select_wav(self):
        """Prompts the user for a wav file"""


        path = filedialog.askopenfilename(
            title="Select .wav",
            filetypes=[("WAV Files", "*.wav"), ("All Files", "*.*")],
            initialdir=FULL_WAV
        )    
        if not path:
            return
        
        self.wav_path = path
        self.load_wav()
        self._refresh_status()
    
    def select_csv(self):
        """Prompts user for a csv file"""


        path = filedialog.askopenfilename(
            title="Select csv file",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=SPLIT_CSV
        )
        if not path:
            return

        self.csv_path = path
        self.load_csv_table()
        self._refresh_status()
    
    # ---------- Load wav + chunks ----------

    def load_wav(self):
        """Loads audio from the contained wav_path, requires wav_path to be defined."""


        try:
            audio, sample_rate = librosa.load(self.wav_path, mono=True, dtype=float)
        except Exception as e:
            messagebox.showerror("Load wav failed.", str(e))

        self.audio = audio
        self.sample_rate = sample_rate
        self.duration = len(audio)/sample_rate
        self.t_start=0.0
        self.start_var.set("0.0")

        self.load_chunk(0.0)

    def load_chunk_from_entry(self):
        """Loads an audio chunk from the full audio file, requires a wav file to be loaded."""


        if self.audio is None:
            messagebox.showwarning("No wav!", "Select wav first")
            return

        try:
            t = float(self.start_var.get())
        except ValueError:
            messagebox.showwarning("Invalid start time", "Start time must be a number")
            return
        self.load_chunk(t)

    def load_chunk(self, t_start: float):
        

        t_start = max(0.0, min(t_start,max(0.0, self.duration - CHUNK_SECONDS)))
        self.t_start = t_start

        i0 = int(round(t_start*self.sample_rate))
        i1 = int(round(t_start+CHUNK_SECONDS)*self.sample_rate)

        self.audio_chunk = self.audio[i0:i1].copy()

        self.clear_boxes()

        self.draw_spectrogram()

        self._refresh_status()

    # ---------- Spectrogram + labelling ----------

    def compute_spec(self):
        mel_spec = librosa.feature.melspectrogram(
            y=self.audio_chunk,
            sr=self.sample_rate,
            n_fft=N_FFT,
            n_mels=N_MELS,
            hop_length=HOP,
            fmin = MIN_FREQ,
            #Removes black box from top of spectrogram, sample rate of AudioMoth not high enough for 150khz
            fmax = min(self.sample_rate/2, 150000) 
        )
        return librosa.power_to_db(mel_spec, ref=np.max)

    def draw_spectrogram(self):

        if self.audio_chunk is None or self.sample_rate is None:
            return

        if self.color_bar is not None:
            try:
                self.color_bar.remove()
                self.color_bar = None
            except Exception as e:
                messagebox.showerror("Old colorbar couldn't be removed", str(e))

        self.ax.clear()
        spec_db = self.compute_spec()

        self.img = librosa.display.specshow(
            spec_db,
            sr=self.sample_rate,
            hop_length=HOP,
            x_axis="time",
            y_axis="mel",
            ax=self.ax
        )

        self.ax.set_title(f"{os.path.basename(self.wav_path)}: ({self.t_start:.2f})s -> ({self.t_start+CHUNK_SECONDS:.2f})s")
        self.color_bar = self.fig.colorbar(self.img, ax=self.ax, format="%+2.0f dB")

        self.ax.set_xlim(0, CHUNK_SECONDS)

        self.canvas.draw_idle()

    def draw_box(self, eclick, erelease):
        click_valid = eclick.xdata is not None and eclick.ydata is not None
        release_valid = erelease.xdata is not None and erelease.ydata is not None

        if not click_valid or not release_valid:
            print(f"Eclick or release not valid: \n{eclick} \n {erelease}")
            return
        
        #Get the xydata values from clicks in order to draw rectangle
        rec_x0 = float(min(eclick.xdata, erelease.xdata))
        rec_x1 = float(max(eclick.xdata, erelease.xdata))
        rec_y0 = float(min(eclick.ydata, erelease.ydata))
        rec_y1 = float(max(eclick.ydata, erelease.ydata))

        #Boundary information for matplotlib.patches.Rectangle
        boundary = {"label":self.current_class, "x":rec_x0,"y":rec_y0, "height":rec_y1-rec_y0,"width":rec_x1-rec_x0}
        

        #Get the xy values from clicks (relative to window) for YOLO label
        label_x0 = float(min(eclick.x, erelease.x))
        label_x1 = float(max(eclick.x, erelease.x))
        label_y0 = float(min(eclick.y, erelease.y))
        label_y1 = float(max(eclick.y, erelease.y))

        spec_bounding_box = self.ax.get_window_extent()

        #YOLO wants labels in the form: class, centre_x, centre_y, width, height
        #Each variable needs to be in range from 0-1
        spec_width = spec_bounding_box.width
        spec_height = spec_bounding_box.height
        spec_left = spec_bounding_box.x0
        spec_bottom = spec_bounding_box.y0

        #Get position of rectangle corners relative to window size
        t0_rel = (label_x0 - spec_left) / spec_width
        t1_rel = (label_x1 - spec_left) / spec_width

        f0_rel = (label_y0 - spec_bottom) / spec_height
        f1_rel = (label_y1 - spec_bottom) / spec_height

        #YOLO origin in top left, matplotlib in bottom left
        f0_rel = 1 - f0_rel
        f1_rel = 1 - f1_rel

        centre_x = (t0_rel+t1_rel)/2
        centre_y = (f0_rel+f1_rel)/2

        boundary_width = t1_rel-t0_rel
        boundary_height = f0_rel-f1_rel #Again, these need to be flipped because YOLO origin in top left

        print(f"YOLO: ({centre_x},{centre_y},{boundary_width},{boundary_height})")

        label = {"label": self.current_class, "cx":centre_x, "cy":centre_y, "w":boundary_width, "h":boundary_height}


        self._draw_boundary(boundary)
        self.canvas.draw_idle()

        self.labels.append(label)

        self.boundary_table.insert("","end",values=list(label.values()))


    def _draw_boundary(self, boundary):
        x = boundary["x"]
        y = boundary["y"]
        h = boundary["height"]
        w = boundary["width"]

        rect = Rectangle((x,y),w,h,fill=False,linewidth=2)
        self.ax.add_patch(rect)
        txt = self.ax.text(x,y+h,boundary["label"],fontsize=10,va="bottom")

        self.boundaries.append((rect, txt))

    def delete_last_box(self):
        if self.boundaries:
            rect, txt = self.boundaries.pop()
            rect.remove()
            txt.remove()

        self.boundary_table.delete(self.boundary_table.get_children()[-1])

        self.canvas.draw_idle()

    def clear_boxes(self):
        for boundary in self.boundary_table.get_children():
            self.boundary_table.delete(boundary)

        for rect, txt in self.boundaries:
            rect.remove()
            txt.remove()
        self.boundaries = []

        if hasattr(self,"canvas"):
            self.canvas.draw_idle()

    def on_class_change(self, _):
        self.current_class = self.class_var.get()
        self._refresh_status()


    # ---------- CSV display ----------


    def load_csv_table(self):
        for item in self.label_table.get_children():
            self.label_table.delete(item)

        if not self.csv_path:
            return

        try:
            # df = pd.read_csv(self.csv_path, header=0)
            with open(self.csv_path, newline='', encoding="utf-8-sig") as csv_file:
                label_reader = csv.reader(csv_file)

                info_line = ",".join(next(label_reader))

                for i,bird in enumerate(label_reader):
                    self.label_table.insert("","end",values=bird)

        except Exception as e:
            messagebox.showerror("Load csv failed", str(e))


    # ---------- Playback ----------

    def play_chunk(self):
        if self.audio_chunk is None or self.sample_rate is None:
            messagebox.showerror("No audio", "Load a wav file first")
            return

        try:
            sd.stop()
            sd.play(self.audio_chunk, self.sample_rate)
        except Exception as e:
            messagebox.showerror("Playback failed", str(e))

    def stop_playback(self):
        try:
            sd.stop()
        except Exception as e:
            messagebox.showerror("Playback couldn't be stopped", str(e))


    # ---------- Export ----------
    def export_current_chunk(self):
        if self.audio_chunk is None or self.sample_rate is None or not self.wav_path:
            messagebox.showinfo("Nothing to export", "Load a wav first")
            return
        
        if len(self.boundaries)<1:
            messagebox.showinfo("Nothing to export", "Label a feature first")


        label_num = len(glob.glob(LABELS+"*.csv"))
        file_path = LABELS + str(label_num) + ".csv"

        print(file_path)

        with file_path.open("w",newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(self.label)
            for label in self.boundary_table.get_children():
                print("CHange this")
                # centre_x = (label[1]+label[2])/2
                # centre_y = (label[3]+label[4])/2
                # width = label[2]-label[1]
                # height = label[4]-label[3]
                # print(centre_x, centre_y, width, height)

            

            #writer.writerows(self.boundary_table.get_children())


        
        



if __name__ == "__main__":
    global labelling
    labelling = SpectrogramLabeller()
    labelling.mainloop()