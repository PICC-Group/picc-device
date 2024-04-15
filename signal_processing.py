from numpy import angle
import math
import asyncio


class SignalProcessing:
    def __init__(self, data_queue, verbose=False):
        self.data_queue = data_queue  # The queue from which to consume data
        self.verbose = verbose

    async def process_data_continuously(self):
        while True:
            s11_data, s21_data = await self.data_queue.get()
            # Process the data using existing 
            wave_length = 0.10  # Should be configured somewhere else. Needs to be changed. 
            phase = self.process_throttle_phase(s11_data, wave_length)
            direction = self.process_direction(s11_data, s21_data)
            if self.verbose:
                print(f"Processed phase: {phase}, direction: {direction}")
            self.data_queue.task_done()
            await asyncio.sleep(2)

    @staticmethod
    def process_throttle_phase(s11_data, wave_length):
        # Calculates the the S11 phase and uses the wave length to calculte the distance to the antenna in meters. 
        phase = angle(s11_data)
        distance = phase / (2 * math.pi) * wave_length
        return distance

    @staticmethod
    def process_direction(s11_data, s21_data):
        # S11 and S21 added.
        return s11_data + s21_data
