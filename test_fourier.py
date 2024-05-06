import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random
import pynanovna
import numpy as np
from scipy.fft import ifft
from time import sleep

def plot_fourier(stream, start=2.9e9, stop=3.1e9, x_lim=False):
    plt.ion()
    fig, ax = plt.subplots(2, 1)
    fig.tight_layout(pad=4.0)

    line3, = ax[0].plot([], [])
    line4, = ax[1].plot([], [])
    vertical_line3 = ax[0].axvline(color='r', linestyle='--')  # Vertical line for center of gravity on subplot 1
    vertical_line4 = ax[1].axvline(color='r', linestyle='--')  # Vertical line for center of gravity on subplot 2

    if not x_lim:
        ax[0].set_xlim(start, stop)  # Set x limits
        ax[1].set_xlim(start, stop)  # Set x limits
    else:
        ax[0].set_xlim(x_lim[0], x_lim[1])
        ax[1].set_xlim(x_lim[0], x_lim[1])
    
    normalized = False
    counter = 0
    noise_tresh1 = 0#0.001
    noise_tresh2 = 0#0.000008

    for s11, s21 in stream:
        if counter < 6:
            counter += 1
            sleep(0.1)
            continue
        if not normalized:
            n1 = np.array([p.z for p in s11])
            n2 = np.array([p.z for p in s21])
            normalized = True

        N = len(s11)
        M = 2 ** np.ceil(np.log2(N)).astype(int)
        window = np.blackman(N + M - N)

        c1 = [p.z for p in s11]
        c1 = np.array(c1) - n1
        c1 = np.pad([p for p in c1], (0, M - N), 'constant')
        c1 = ifft(c1)
        c2 = [p if p > noise_tresh1 else 0 for p in c1]
        c1 = c1 * window

        c2 = [p.z for p in s21]
        c2 = np.array(c2) - n2
        c2 = np.pad([p for p in c2], (0, M - N), 'constant')
        c2 = ifft(c2)
        c2 = [p if p > noise_tresh2 else 0 for p in c2]
        c2 = c2 * window

        x = np.linspace(0, 1 / (stop * 2), num=len(c1))

        # Update data for each line
        line3.set_data(x, [np.log(abs(p.real) + 1) for p in c1])
        line4.set_data(x, [np.log(abs(p.real) + 1) for p in c2])

        # Calculate center of gravity
        center_of_gravity_c1 = np.sum(x * np.abs(c1)) / np.sum(np.abs(c1))
        center_of_gravity_c2 = np.sum(x * np.abs(c2)) / np.sum(np.abs(c2))

        # Update the position of the vertical line
        vertical_line3.set_xdata(center_of_gravity_c1)
        vertical_line4.set_xdata(center_of_gravity_c2)

        # Set limits
        ax[0].set_ylim(min(np.abs(c1)), max(np.abs(c1)))
        ax[1].set_ylim(min(np.abs(c2)), max(np.abs(c2)))

        # Redraw the figure
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)



start = 50e3
stop = 6.0e9

worker = pynanovna.NanoVNAWorker(verbose=False)
worker.set_sweep(start, stop, 1, 1001)
worker.calibrate(load_file="./Calibration_file_2024-05-05 18:18:48.477944.cal")

stream = worker.stream_data("./save_plate.csv")

plot_fourier(stream, start=start, stop=stop, x_lim=(0, 1e-10))
