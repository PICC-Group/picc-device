import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random
import pynanovna
import numpy as np
from scipy.fft import ifft

def plot_fourier(stream, start=2.9e9, stop=3.1e9, x_lim=False):
    plt.ion()
    fig, ax = plt.subplots(2, 1)
    fig.tight_layout(pad=4.0)

    # Initialize lines for each subplot, assuming no label is needed now
    line3, = ax[0].plot([], [])
    line4, = ax[1].plot([], [])

    if not x_lim:
        ax[0].set_xlim(start, stop)  # Set x limits
        ax[1].set_xlim(start, stop)  # Set x limits
    else:
        ax[0].set_xlim(x_lim[0], x_lim[1])
        ax[1].set_xlim(x_lim[0], x_lim[1])
    

    # Assuming the data stream yields tuples with two lists: s11 and s21
    for s11, s21 in stream:
        N = len(s11)
        M = 2 ** np.ceil(np.log2(N)).astype(int)  # Next power of two for FFT padding

        c1 = np.pad([p.phase for p in s11], (0, M - N), 'constant')  # Pad signal
        c1 = ifft(c1)  # Compute inverse FFT

        c2 = np.pad([p.phase for p in s21], (0, M - N), 'constant')  # Pad signal
        c2 = ifft(c2)  # Compute inverse FFT

        x = np.linspace(0, (stop-start), num=len(c1))  # x-axis as time, based on frequency range

        # Update data for each line
        line3.set_data(x, np.abs(c1))
        line4.set_data(x, np.abs(c2))

        if not x_lim:
            ax[0].set_xlim(min(x), max(x))  # Set x limits
            ax[1].set_xlim(min(x), max(x))  # Set x limits
        else:
            ax[0].set_xlim(x_lim[0], x_lim[1])
            ax[1].set_xlim(x_lim[0], x_lim[1])

        # Set limits
        ax[0].set_ylim(min(np.abs(c1)), max(np.abs(c1)))
        ax[1].set_ylim(min(np.abs(c2)), max(np.abs(c2)))

        # Redraw the figure
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)


start = 2.0e9
stop = 4.0e9

worker = pynanovna.NanoVNAWorker(verbose=False)
worker.set_sweep(start, stop, 1, 1001)
worker.calibrate(load_file="../oscars_cal.cal")

stream = worker.stream_data()

plot_fourier(stream, start=start, stop=stop)#, x_lim=(0, 0.25))
