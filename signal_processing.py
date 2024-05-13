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
    def __init__(self, data_stream, process_sleep_time=0.0001, smoothing_points: int=5,  verbose=False):
        self.data_stream = data_stream  # The stream from which to process data
        self.process_sleep_time = process_sleep_time
        self.smoothing_points = smoothing_points
        self.verbose = verbose

    async def process_data_continuously(self):
        for s11, s21 in self.data_stream:
            phase = self.calculate_angle(s11, s21)
            direction = self.calculate_throttle(s11, s21)
            if self.verbose:
                print(f"Processed phase: {phase}, direction: {direction}")
            await asyncio.sleep(self.process_sleep_time)

    @staticmethod
    def calculate_angle(s11_data, s21_data, norm):
        # OSCARS MAGIC
        pass

    @staticmethod
    def calculate_throttle(s11_data, s21_data):
        # OSCARS MAGIC
        pass

    def _fourier_filtering(self, s11, s21):
        # TEOS MAGIC
        pass

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
