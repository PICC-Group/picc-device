from pynanovna import NanoVNAWorker
from pynanovna import RFTools
import matplotlib
matplotlib.use("tkagg")
from matplotlib import pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.special import comb
import time

# Setup real-time plotting in matplotlib
plt.ion()

fig, ax = plt.subplots(2)
ax[0].set_ylim(0,1)
ax[0].set_xlim(0,1)
ax[1].set_ylim(0,1)
ax[1].set_xlim(0,1)
xs = []
ys = []
x2s = []
y2s = []
ax[0].title.set_text('Throttle')
ax[1].title.set_text('Angle')
line1, = ax[0].plot(xs, ys)
line2, = ax[1].plot(x2s, y2s)

# Setup nanovna
worker = NanoVNAWorker(verbose=False)
worker.set_sweep(2.95e9,3.05e9,1,11)
worker.calibrate(load_file="signal-processing/oscars_cal.cal")
datafile = False #  Set this to a path if you want to play a previously recorded file.



norm = np.zeros(10) # Reference sweep is stored here as a global variable

## Update graph with new data
def animate():
    global ys, y2s
    # Limit x and y lists to 20 items
    ys = ys[-20:]
    y2s = y2s[-20:]
    x = np.linspace(0,1,len(ys))

    # Set the x and y data
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

## Make list of datapoints into a numpy array of complex values
def to_complex(s: list[RFTools.Datapoint]) -> np.array:
    news = np.zeros(len(s), complex)
    for i in range(len(s)):
        news[i] = complex(s[i].re, s[i].im)
    return news

## Make data (i.e tuple of list of datapoints) into a tuple of numpy arrays of complex values
def data_to_np(data) -> tuple[np.array]:
    return (to_complex(data[0]), to_complex(data[1]))

## Smoothstep function https://en.wikipedia.org/wiki/Smoothstep, used for limiting data between a maximum and minimum in a 'smooth' way.
def smoothstep(x, x_min=0, x_max=1, N=1):
    x = np.clip((x - x_min) / (x_max - x_min), 0, 1)

    result = 0
    for n in range(0, N + 1):
         result += comb(N + n, n) * comb(2 * N + 1, N - n) * (-x) ** n

    result *= x ** (N + 1)

    return result

## (S11-refS11, S21-refS21)
def normalize(s11, s21) -> tuple:
    return (s11-norm[0], s21-norm[1])

## Calculate throttle value from s11 and s21 data, ref_throttle_data is returned from setup
def get_throttle(s11, s21, ref_throttle_data=None, alpha=3.0):
    ns11, ns21 = normalize(s11, s21)
    h = np.square(np.average(np.abs(ns11))) + np.square(alpha*np.average(np.abs(ns21)))
    if ref_throttle_data==None:
        return np.sqrt(h)
    else:
        return smoothstep(np.sqrt(h),ref_throttle_data[1],ref_throttle_data[0],0) # Clamp value between minimum throttle and maximum throttle (N=0 in smoothstep corresponds to normal clamp)
    #return np.sqrt(h)

## Calculate angle from s11 and s21 data, ref_angle_data and ref_throttle_data is returned from setup
def get_angle(s11, s21, ref_angle_data=None, ref_throttle_data=None, alpha=3.0):
    ns11, ns21 = normalize(s11, s21)
    ang = (np.average(np.abs(ns21)))/np.power((np.average(np.abs(ns11))),0.5)
    if ref_angle_data!=None and ref_throttle_data!=None:
        h = get_throttle(s11,s21, ref_throttle_data, alpha)
        minval = h*ref_angle_data[0]+(1-h)*ref_angle_data[2] # value at minangle interpolated between min distance and max distance based on current throttle
        maxval = h*ref_angle_data[1]+(1-h)*ref_angle_data[3] # value at maxangle interpolated between min distance and max distance based on current throttle
        return smoothstep(ang,minval,maxval) # Clamp the value between minval and maxval using a smoothstep function https://en.wikipedia.org/wiki/Smoothstep
    else:
        return ang
    #return smoothstep(ang,0.05,0.20)

def get_new_data():
    data = worker.single_sweep()
    return (data[0].copy(), data[1].copy())

## Setup function to determine reference values for accurate calculation of throttle and angle
def setup():
    global norm

    r_data, mindist_minangle, mindist_maxangle, maxdist_minangle, maxdist_maxangle = [], [], [], [], []
    data_old = [[RFTools.Datapoint(1, 1.0, 1.0)]]
    data = data_old
    i = 0
    while True:
        match i:
            case 0:
                input("Taking empty refernce, make sure the space infront of the antenna is clear. Press Enter to continue.")
                r_data = get_new_data()
                norm = data_to_np(r_data)
            case 1:
                input("Put strip grid at 2cm distance at minimum angle. Press Enter to continue.")
                mindist_minangle = get_new_data()
            case 2:
                input("Put strip grid at 2cm distance at maximum angle (45 degrees). Press Enter to continue.")
                mindist_maxangle = get_new_data()
            case 3:
                input("Put strip grid at 10cm distance at minimum angle. Press Enter to continue.")
                maxdist_minangle = get_new_data()
            case 4:
                input("Put strip grid at 10cm distance at maximum angle (45 degrees). Press Enter to continue.")
                maxdist_maxangle = get_new_data()
                print(mindist_maxangle==mindist_minangle)
        if i > 5:
            break
        i+=1
    
    s21max1 = np.average(np.abs(data_to_np(mindist_maxangle)[1]))
    s21max2 = np.average(np.abs(data_to_np(maxdist_maxangle)[1]))
    s11max1 = np.average(np.abs(data_to_np(mindist_minangle)[0]))
    s11max2 = np.average(np.abs(data_to_np(maxdist_minangle)[0]))
    print(s11max1, s11max2)
    alpha = np.sqrt((s11max1/s21max1 + s11max2/s21max2)/2) # Determine how much larger s11 is than s21
    print(alpha)

    # [anlge min at min distance, angle max at min distance, anlge min at max distance, angle max at max distance]
    ref_angle_data =  [get_angle(*data_to_np(mindist_minangle)), get_angle(*data_to_np(mindist_maxangle)),
                    get_angle(*data_to_np(maxdist_minangle)), get_angle(*data_to_np(maxdist_maxangle))]
    
    # [average throttle at min distance, average throttle at max distance]
    ref_throttle_data = [(get_throttle(*data_to_np(mindist_minangle))+get_throttle(*data_to_np(mindist_minangle)))/2,
                        (get_throttle(*data_to_np(maxdist_minangle))+get_throttle(*data_to_np(maxdist_maxangle)))/2]
    
    print(ref_angle_data, ref_throttle_data, alpha)
    return [ref_angle_data, ref_throttle_data, alpha]


data_old = [] # Keep track of last sweep
i = 0 # Loop idx
t0 = time.time() # Start time


refs = setup() # Setup ref values

stream = worker.stream_data(datafile)

for data in stream:
    if (data == data_old):
        continue
    
    N = len(data[0])
    s11 = to_complex(data[0])
    s21 = to_complex(data[1])
    
    #if (i==0):
    #    norm = (s11, s21)

    h = get_throttle(s11, s21, refs[1])
    ang = get_angle(s11,s21,refs[0], refs[1])
    
    print("throttle: ", h, " ang: ", ang)
    ys.append(h)
    y2s.append(ang)
    animate()
    data_old = (data[0].copy(), data[1].copy())
    i += 1
    t1 = time.time()

worker.kill()

