import numpy as np
import math
from time import sleep
from scipy.special import comb
from scipy.fft import ifft
from scipy.fft import fft


# S11 phase throttle parameters
UPPER_PHASE_LIM = 0.8 * math.pi
LOWER_PHASE_LIM = 0.1 * math.pi
K = 1 / (LOWER_PHASE_LIM - UPPER_PHASE_LIM)
M = 1 - (LOWER_PHASE_LIM) / (LOWER_PHASE_LIM - UPPER_PHASE_LIM)
UPPER_VAL_LIM = 2.0  # Needs to be calibrated
# Direction parameters


class SignalProcessing:
    def __init__(
        self,
        data_stream,
        process_sleep_time=0.0001,
        smoothing_points: int = 5,
        verbose=False,
    ):
        self.stream = data_stream  # The stream from which to process data
        self.process_sleep_time = process_sleep_time
        self.smoothing_points = smoothing_points
        self.verbose = verbose
        self.norm = None
        self.ref_angle_data = None
        self.ref_throttle_data = None
        self.alpha = None
        self.setup()

    def process_data_continuously(self):
        for s11, s21 in self.stream:
            angle = self.get_angle(s11, s21, self.ref_angle_data, self.ref_throttle_data, self.alpha) * 90 - 45
            throttle = self.get_throttle(s11, s21, self.ref_throttle_data, self.alpha)
            print(angle)
            if self.verbose:
                print(f"Processed phase: {angle}, direction: {throttle}")
            sleep(self.process_sleep_time)
            yield angle, throttle

    def get_angle(
        self, s11, s21, ref_angle_data=None, ref_throttle_data=None, alpha=3.0
    ):
        ## Calculate angle from s11 and s21 data, ref_angle_data and ref_throttle_data is returned from setup
        if type(s11[0]) != np.complex128:
            s11, s21 = self.data_to_np([s11, s21])
        ns11, ns21 = self._normalize(s11, s21)
        ang = (np.average(np.abs(ns21))) / np.power((np.average(np.abs(ns11))), 0.5)

        if ref_angle_data is not None and ref_throttle_data is not None:
            h = self.get_throttle(s11, s21, ref_throttle_data, alpha)
            minval = (
                h * ref_angle_data[0] + (1 - h) * ref_angle_data[2]
            )  # value at minangle interpolated between min distance and max distance based on current throttle
            maxval = (
                h * ref_angle_data[1] + (1 - h) * ref_angle_data[3]
            )  # value at maxangle interpolated between min distance and max distance based on current throttle
            return self.smoothstep(
                ang, minval, maxval, 0
            )  # Clamp the value between minval and maxval using a smoothstep function https://en.wikipedia.org/wiki/Smoothstep
        return ang

    def get_throttle(self, s11, s21, ref_throttle_data=None, alpha=3.0):
        ## Calculate throttle value from s11 and s21 data, ref_throttle_data is returned from setup
        if type(s11[0]) != np.complex128:
            s11, s21 = self.data_to_np([s11, s21])
        ns11, ns21 = self._normalize(s11, s21)
        h = np.square(np.average(np.abs(ns11))) + np.square(
            alpha * np.average(np.abs(ns21))
        )
        if ref_throttle_data is None:
            return np.sqrt(h)
        else:
            return self.smoothstep(
                np.sqrt(h), 0, ref_throttle_data[0], 0 # This should be possible to control.
            )  # Clamp value between minimum throttle and maximum throttle (N=0 in smoothstep corresponds to normal clamp)

    def fourier_filtering(self, s11, s21):
        #Filtering the signal using FFT
        ######### Returns complex values ############
        c1 = [p.z for p in s11]
        c1 = np.array(c1)
        c2 = [p.z for p in s21]
        c2 = np.array(c2)
        c1_filtered = self._fft_hanning(c1)
        c2_filtered = self._fft_hanning(c2)
        
        return c1_filtered, c2_filtered
    
    def _fft_hanning(self, c):
        #Using ifft, then a hanning window and finally fft
        pad_size = 16384-len(c)
        c = np.pad([p for p in c], (int(pad_size/2), int(pad_size/2)), 'constant')
        c = ifft(c)
        index_of_peak = 0
        if np.max(c) > 0:
            index_of_peak = np.argmax(np.abs(c))
            window_size = 750
            if index_of_peak - window_size // 2 < 0 or index_of_peak + window_size // 2 > len(c):
                window_size = 0
            start_index = index_of_peak-window_size/2
            hanning_window = np.concatenate((np.zeros(int(start_index)), np.hanning(window_size), np.zeros(len(c) - (index_of_peak + window_size//2))))
            c_modified = np.copy(c)
            c_modified = c_modified.astype(hanning_window.dtype)
            c_modified *= hanning_window
        else:
            c_modified = np.copy(c)
        #Zero padding before fft again gives weird results
        c_modified = np.pad([p for p in c_modified], (int(pad_size/2), int(pad_size/2)), 'constant')
        return fft(c_modified)

    def _normalize(self, s11, s21) -> tuple:
        return (s11 - self.norm[0], s21 - self.norm[1])

    def smoothstep(self, x, x_min=0, x_max=1, N=1):
        ## Smoothstep function https://en.wikipedia.org/wiki/Smoothstep, used for limiting data between a maximum and minimum in a 'smooth' way.
        x = np.clip((x - x_min) / (x_max - x_min), 0, 1)

        result = 0
        for n in range(0, N + 1):
            result += comb(N + n, n) * comb(2 * N + 1, N - n) * (-x) ** n

        result *= x ** (N + 1)

        return result

    def get_new_data(self):
        for data in self.stream:
            return (
                data[0].copy(),
                data[1].copy(),
            )  # This is not good practice. Might change later.

    def data_to_np(self, data) -> tuple[np.array]:
        ## Make data (i.e tuple of list of datapoints) into a tuple of numpy arrays of complex values
        return np.array([[p.z for p in data[0]], [p.z for p in data[1]]])

    def setup(self):
        i = 0
        while True:
            match i:
                case 0:
                    input(
                        "Taking empty refernce, make sure the space infront of the antenna is clear. Press Enter to continue."
                    )
                    r_data = self.get_new_data()
                    self.norm = self.data_to_np(r_data)
                case 1:
                    input(
                        "Put strip grid at 2cm distance at minimum angle. Press Enter to continue."
                    )
                    mindist_minangle = self.get_new_data()
                case 2:
                    input(
                        "Put strip grid at 2cm distance at maximum angle (45 degrees). Press Enter to continue."
                    )
                    mindist_maxangle = self.get_new_data()
                case 3:
                    input(
                        "Put strip grid at 10cm distance at minimum angle. Press Enter to continue."
                    )
                    maxdist_minangle = self.get_new_data()
                case 4:
                    input(
                        "Put strip grid at 10cm distance at maximum angle (45 degrees). Press Enter to continue."
                    )
                    maxdist_maxangle = self.get_new_data()
                    print(mindist_maxangle == mindist_minangle)
            if i > 5:
                break
            i += 1

        s21max1 = np.average(np.abs(self.data_to_np(mindist_maxangle)[1]))
        s21max2 = np.average(np.abs(self.data_to_np(maxdist_maxangle)[1]))
        s11max1 = np.average(np.abs(self.data_to_np(mindist_minangle)[0]))
        s11max2 = np.average(np.abs(self.data_to_np(maxdist_minangle)[0]))
        if self.verbose:
            print(s11max1, s11max2)

        self.alpha = np.sqrt(
            (s11max1 / s21max1 + s11max2 / s21max2) / 2
        )  # Determine how much larger s11 is than s21
        if self.verbose:
            print(self.alpha)

        # [angle min at min distance, angle max at min distance, anlge min at max distance, angle max at max distance]
        self.ref_angle_data = [
            self.get_angle(*self.data_to_np(mindist_minangle)),
            self.get_angle(*self.data_to_np(mindist_maxangle)),
            self.get_angle(*self.data_to_np(maxdist_minangle)),
            self.get_angle(*self.data_to_np(maxdist_maxangle)),
        ]

        # [average throttle at min distance, average throttle at max distance]
        self.ref_throttle_data = [
            (
                self.get_throttle(*self.data_to_np(mindist_minangle))
                + self.get_throttle(*self.data_to_np(mindist_minangle))
            )
            / 2,
            (
                self.get_throttle(*self.data_to_np(maxdist_minangle))
                + self.get_throttle(*self.data_to_np(maxdist_maxangle))
            )
            / 2,
        ]

        if self.verbose:
            print(self.ref_angle_data, self.ref_throttle_data, self.alpha)

    async def _mean_smoothing(self):
        ########### THIS NEEDS TO BE REWRITTEN TO NOT USE QUEUE ######################
        """Calculates the mean value of n number of S11 and S21 values.
        No value is removed.

        Returns:
            list[complex]: mean S11 and S21 values
        """
        n = self.smoothing_points
        temp_storage = []
        try:
            # Check if the queue has enough items
            if self.queue.qsize() < n:
                print("Not enough items in the queue to calculate the mean.")
                return None, None

            # Temporarily remove n items to peek
            for _ in range(n):
                item = await self.queue.get()
                temp_storage.append(item)

            # Calculate mean for S11 and S21
            s11_values = [item[0] for item in temp_storage]
            s21_values = [item[1] for item in temp_storage]
            mean_s11 = np.mean(s11_values)
            mean_s21 = np.mean(s21_values)

            # Put the items back in the queue
            for item in reversed(temp_storage):
                self.queue._queue.appendleft(
                    item
                )  # Directly manipulating the internal deque

            return [mean_s11, mean_s21]

        except Exception as e:
            print(f"An error occurred: {e}")
            # In case of an error, ensure all items are put back
            while temp_storage:
                item = temp_storage.pop()
                await self.queue.put(item)
            return None, None

    async def _weighted_mean_smoothing(self, n):
        ########### THIS NEEDS TO BE REWRITTEN TO NOT USE QUEUE ######################
        """Calculates the mean value of n number of S11 and S21 values.
        No value is removed.

        Returns:
            list[complex]: mean S11 and S21 values
        """
        temp_storage = []
        n = self.smoothing_points
        try:
            # Check if the queue has enough items
            if self.queue.qsize() < n:
                print("Not enough items in the queue to calculate the mean.")
                return None, None

            # Temporarily remove n items to peek
            for _ in range(n):
                item = await self.queue.get()
                temp_storage.append(item)

            # Calculate weights based on n. w1 = 1, w_(n+1) = 0
            weights = [1 - (0.5 / (n - 1)) * i if n > 1 else 1 for i in range(n)]

            # Calculate mean for S11 and S21
            s11_values = [
                item[0] * weight for item, weight in zip(temp_storage, weights)
            ]
            s21_values = [
                item[1] * weight for item, weight in zip(temp_storage, weights)
            ]
            total_weight = sum(weights)
            mean_s11 = sum(s11_values) / total_weight
            mean_s21 = sum(s21_values) / total_weight

            # Puts all items back into their original order in the queue.
            for item in reversed(temp_storage):
                self.queue._queue.appendleft(item)

            # Reomoves the firs item.
            # for item in reversed(temp_storage[1:]):  # Skip the first item
            #    self.queue._queue.appendleft(item)

            return [mean_s11, mean_s21]

        except Exception as e:
            print(f"An error occurred: {e}")
            return None, None
