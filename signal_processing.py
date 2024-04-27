from numpy import angle
import numpy as np
import math
import asyncio

# S11 phase throttle parameters
UPPER_PHASE_LIM = 0.8 * math.pi
LOWER_PHASE_LIM = 0.1 * math.pi
K = 1 / (LOWER_PHASE_LIM - UPPER_PHASE_LIM)
M = 1 - (LOWER_PHASE_LIM) / (LOWER_PHASE_LIM - UPPER_PHASE_LIM)
UPPER_VAL_LIM = 2.0  # Needs to be calibrated
# Direction parameters


class SignalProcessing:
    def __init__(self, data_queue, process_sleep_time=0.0001, smoothing_points: int=5,  verbose=False):
        self.data_queue = data_queue  # The queue from which to consume data
        self.process_sleep_time = process_sleep_time
        self.smoothing_points = smoothing_points
        self.norm = []
        self.verbose = verbose

    async def process_data_continuously(self):
        counter = 0
        while True:
            s11_data, s21_data = await self.data_queue.get()
            if counter < 20:
                self.set_norm(s11_data, s21_data)
            elif counter <= 10:
                counter += 1
                continue
            counter += 1
            # Process the data using existing 
            phase = self.process_throttle_phase(s11_data, s21_data, self.norm)
            direction = self.process_direction(s11_data, s21_data)
            if self.verbose:
                print(f"Processed phase: {phase}, direction: {direction}")
            self.data_queue.task_done()
            await asyncio.sleep(self.process_sleep_time)

    async def _mean_smoothing(self):
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
            # In case of an error, ensure all items are put back
            while temp_storage:
                item = temp_storage.pop()
                await self.queue.put(item)
            return None, None

    def set_norm(self, s11, s12):
        self.norm = [s11, s12]

    @staticmethod
    def process_throttle_phase(s11_data, s21_data, norm):
        norm_mag_sum_s11 = 0
        norm_mag_sum_s21 = 0
        res = 0
        alpha = 0.25
        beta = 1

        for i in range(0, len(s11_data)):
            norm_mag_sum_s11 += alpha * np.square(np.abs(s11_data[i] - norm[0][i]))
            norm_mag_sum_s21 += beta * np.square(np.abs(s21_data[i] - norm[1][i]))
            res += np.sqrt(norm_mag_sum_s11/ len(s11_data) + norm_mag_sum_s21/ len(s21_data))
        res *= 1000
        # TODO: Handle faulty input and output data. 
        # Calculates the the S11 phase and uses that to determine the throttle. 
        #phase = angle(s11_data)
        #output = K * phase + M
        #val = abs(s11_data)

        #if phase < LOWER_PHASE_LIM:
        #    output = 1
        #elif (phase > UPPER_PHASE_LIM) or (val < UPPER_VAL_LIM):
        #    output = 0
        print(norm_mag_sum_s11, norm_mag_sum_s21)
        print(res)
        return res
        #return output

    @staticmethod
    def process_direction(s11_data, s21_data):
        # TODO: Handle faulty input and output data. 
        # S11 and S21 added.
        #s11_val = abs(s11_data)
        #s21_val = abs(s21_data)
        s11_val = np.abs(s11_data)
        s21_val = np.abs(s21_data)

        output = s11_val / s21_val
        # Need to look at data to do more.

        return output
