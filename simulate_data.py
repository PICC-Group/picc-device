import asyncio
import random

class SimulateData:
    def __init__(self, batch_size=3) -> None:
        self.batch_size = batch_size

    async def generate_batch(self):
        s11_batch = [self.generete_complex_data() for _ in range(self.batch_size)]
        s21_batch = [self.generete_complex_data() for _ in range(self.batch_size)]
        return s11_batch, s21_batch
    
    def generete_complex_data(self):
        real_part = random.uniform(-1, 1)
        imag_part = random.uniform(-1, 1)
        return complex(real_part, imag_part)
    
