import numpy as np
import math
import asyncio
from scipy.special import comb

# S11 phase throttle parameters
UPPER_PHASE_LIM = 0.8 * math.pi
LOWER_PHASE_LIM = 0.1 * math.pi
K = 1 / (LOWER_PHASE_LIM - UPPER_PHASE_LIM)
M = 1 - (LOWER_PHASE_LIM) / (LOWER_PHASE_LIM - UPPER_PHASE_LIM)
UPPER_VAL_LIM = 2.0  # Needs to be calibrated
# Direction parameters


class SignalProcessing:
    def __init__(self, data_stream, process_sleep_time=0.0001, smoothing_points: int=5,  verbose=False):
        self.data_stream = data_stream  # The stream from which to process data
        self.process_sleep_time = process_sleep_time
        self.smoothing_points = smoothing_points
        self.verbose = verbose

    async def process_data_continuously(self):
        for s11, s21 in self.data_stream:
            phase = self.get_angle(s11, s21)
            direction = self.get_throttle(s11, s21)
            if self.verbose:
                print(f"Processed phase: {phase}, direction: {direction}")
            await asyncio.sleep(self.process_sleep_time)

    def get_angle(self, s11, s21, ref_angle_data=None, ref_throttle_data=None, alpha=3.0):
        ## Calculate angle from s11 and s21 data, ref_angle_data and ref_throttle_data is returned from setup
        ns11, ns21 = self._normalize(s11, s21)
        ang = (np.average(np.abs(ns21)))/np.power((np.average(np.abs(ns11))),0.5)

        if ref_angle_data is not None and ref_throttle_data is not None:
            h = self.get_throttle(s11,s21, ref_throttle_data, alpha)
            minval = h*ref_angle_data[0]+(1-h)*ref_angle_data[2] # value at minangle interpolated between min distance and max distance based on current throttle
            maxval = h*ref_angle_data[1]+(1-h)*ref_angle_data[3] # value at maxangle interpolated between min distance and max distance based on current throttle
            return self.smoothstep(ang,minval,maxval, 0) # Clamp the value between minval and maxval using a smoothstep function https://en.wikipedia.org/wiki/Smoothstep
        return ang

    def get_throttle(self, s11, s21, ref_throttle_data=None, alpha=3.0):
        ## Calculate throttle value from s11 and s21 data, ref_throttle_data is returned from setup
        ns11, ns21 = self._normalize(s11, s21)
        h = np.square(np.average(np.abs(ns11))) + np.square(alpha*np.average(np.abs(ns21)))
        if ref_throttle_data is None:
            return np.sqrt(h)
        else:
            return self.smoothstep(np.sqrt(h),ref_throttle_data[1],ref_throttle_data[0],0) # Clamp value between minimum throttle and maximum throttle (N=0 in smoothstep corresponds to normal clamp)

    def fourier_filtering(self, s11, s21):
        # TEOS MAGIC
        pass
    
    def _normalize(self, s11, s21, norm) -> tuple:
        return (s11 - norm[0], s21 - norm[1])
    
    def smoothstep(self, x, x_min=0, x_max=1, N=1):
        ## Smoothstep function https://en.wikipedia.org/wiki/Smoothstep, used for limiting data between a maximum and minimum in a 'smooth' way.
        x = np.clip((x - x_min) / (x_max - x_min), 0, 1)

        result = 0
        for n in range(0, N + 1):
            result += comb(N + n, n) * comb(2 * N + 1, N - n) * (-x) ** n

        result *= x ** (N + 1)

        return result

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
                self.queue._queue.appendleft(item)  # Directly manipulating the internal deque
            
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
            s11_values = [item[0] * weight for item, weight in zip(temp_storage, weights)]
            s21_values = [item[1] * weight for item, weight in zip(temp_storage, weights)]
            total_weight = sum(weights)
            mean_s11 = sum(s11_values) / total_weight
            mean_s21 = sum(s21_values) / total_weight
            
            # Puts all items back into their original order in the queue. 
            for item in reversed(temp_storage):
                self.queue._queue.appendleft(item)
            
            # Reomoves the firs item.
            #for item in reversed(temp_storage[1:]):  # Skip the first item
             #    self.queue._queue.appendleft(item)
            
            return [mean_s11, mean_s21]

        except Exception as e:
            print(f"An error occurred: {e}")
            return None, None
