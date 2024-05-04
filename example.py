from pynanovna import NanoVNAWorker
from pynanovna import RFTools
import matplotlib
matplotlib.use("tkagg")
from matplotlib import pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.special import comb

plt.ion()

fig, ax = plt.subplots(2)
ax[0].set_ylim(0,0.5)
ax[0].set_xlim(0,1)
ax[1].set_ylim(0,1)
ax[1].set_xlim(0,1)
xs = []
ys = []
x2s = []
y2s = []
ax[0].title.set_text('Height')
ax[1].title.set_text('Angle')
line1, = ax[0].plot(xs, ys)
line2, = ax[1].plot(x2s, y2s)

def animate():
    global ys, y2s
    # Limit x and y lists to 20 items
    
    ys = ys[-20:]
    y2s = y2s[-20:]
    x = np.linspace(0,1,len(ys))
    line1.set_xdata(x)
    line1.set_ydata(ys)
    line2.set_xdata(x)
    line2.set_ydata(y2s)

    # Draw
    fig.canvas.draw()

    # This will run the GUI event
    # loop until all UI events
    # currently waiting have been processed
    fig.canvas.flush_events()

worker = NanoVNAWorker(verbose=False)
worker.set_sweep(2.9e9,3.1e9,1,51)
datafile = False #  Set this to a path if you want to play a previously recorded file.
stream = worker.stream_data(datafile)

def to_complex(s: list[RFTools.Datapoint]) -> np.array:
    news = np.zeros(len(s), complex)
    for i in range(len(s)):
        news[i] = complex(s[i].re, s[i].im)
    return news

norm = np.zeros(10)

def smoothstep(x, x_min=0, x_max=1, N=1):
    x = np.clip((x - x_min) / (x_max - x_min), 0, 1)

    result = 0
    for n in range(0, N + 1):
         result += comb(N + n, n) * comb(2 * N + 1, N - n) * (-x) ** n

    result *= x ** (N + 1)

    return result

def normalize(s11, s21) -> tuple:
    return (s11-norm[0], s21-norm[1])

def get_h(s11, s21):
    alpha = 3.0
    ns11, ns21 = normalize(s11, s21)
    h = np.square(np.average(np.abs(ns11))) + np.square(alpha*np.average(np.abs(ns21)))
    return np.sqrt(h)

def get_angle(s11, s21):
    ns11, ns21 = normalize(s11, s21)
    ang = (np.average(np.abs(ns21)))/np.sqrt(get_h(s11,s21))
    return smoothstep(ang,0.02,0.13)

data_old = []
i = 0
for data in stream:
    if (data == data_old):
        continue
    
    N = len(data[0])
    s11 = to_complex(data[0])
    s21 = to_complex(data[1])
    
    if (i==0):
        norm = (s11, s21)
    
    print("h: ", get_h(s11, s21), " ang: ", get_angle(s11,s21))
    ys.append(get_h(s11, s21))
    y2s.append(get_angle(s11, s21))
    animate()
    data_old = (data[0].copy(), data[1].copy())
    i += 1

