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
    def __init__(self, data_queue, process_sleep_time=0.0001, verbose=False):
        self.data_queue = data_queue  # The queue from which to consume data
        self.process_sleep_time = process_sleep_time
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
