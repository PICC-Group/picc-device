import asyncio
import random


class SimulateData:
    def __init__(self, data_queue, verbose):
        self.data_queue = data_queue
        self.verbose = verbose

    async def generate_start_data(self):
        for i in range(5):
            s11_data = self.generate_complex_data()
            s21_data = self.generate_complex_data()
            await self.data_queue.put((s11_data, s21_data))

    async def generate_data_continuously(self):
        while True:
            s11_data = self.generate_complex_data()
            s21_data = self.generate_complex_data()
            await self.data_queue.put((s11_data, s21_data))
            if self.verbose:
                print(f"Generated data: S11={s11_data}, S21={s21_data}")
                print(f"Queue length: {self.data_queue.qsize()}")
            await asyncio.sleep(2)  # Added sleep to simulate time delay

    def generate_complex_data(self):
        real_part = random.uniform(-1, 1)
        imag_part = random.uniform(-1, 1)
        return complex(real_part, imag_part)

    async def consume_data(self):
        while True:
            s11_data, s21_data = await self.data_queue.get()
            print(f"Consumed data: S11={s11_data}, S21={s21_data}")
            self.data_queue.task_done()
