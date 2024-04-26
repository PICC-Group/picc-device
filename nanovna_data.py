import asyncio
import pynanovna


class NanoVNAData:
    def __init__(self, data_queue, producer_sleep_time=0.1, verbose=False):
        self.data_queue = data_queue
        self.producer_sleep_time = producer_sleep_time
        self.verbose = verbose
        self.vna = pynanovna.NanoVNAWorker(0, self.verbose)

    async def generate_data_continuously(self, datafile=False):  
        if self.vna.playback_mode and not datafile:  # No VNA is connected and no play back file is given. 
            print("No VNA is connected, a playback file must be used. Quitting.")
            return
        # Uses the playback file 'datafile'. 
        data = self.vna.stream_data(data_file=datafile)
        for sweep in data:
            s11_re, s11_im, s21_re, s21_im, freq = sweep
            s11_data = [complex(s11_re[i], s11_im[i]) for i in range(len(s11_re))]
            s21_data = [complex(s21_re[j], s21_im[j]) for j in range(len(s21_re))]
            await self.data_queue.put((s11_data, s21_data))
            if self.verbose:
                print(f"Generated data: S11={s11_data}, S21={s21_data}")
                print(f"Queue length: {self.data_queue.qsize()}")
            await asyncio.sleep(self.producer_sleep_time)  # Added sleep to simulate time delay

    async def consume_data(self):
        while True:
            s11_data, s21_data = await self.data_queue.get()
            if self.verbose: 
                print(f"Consumed data: S11={s11_data}, S21={s21_data}")
            self.data_queue.task_done()
