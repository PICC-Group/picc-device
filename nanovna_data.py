import asyncio
from nanovna_saver_headless.src.NanoVNASaverHeadless import NanoVNASaverHeadless


class NanoVNAData:
    def __init__(self, data_queue, verbose):
        self.data_queue = data_queue
        self.verbose = verbose
        self.vna = NanoVNASaverHeadless(0, self.verbose)

    async def generate_data_continuously(self, datafile=False):
        if self.vna.playback_mode and datafile:
            print("No VNA is connected, a playback file must be used. Quitting.")
            return
        data = self.vna.stream_data(datafile)
        for sweep in data:
            s11_re, s11_im, s21_re, s21_im, freq = sweep
            s11_data = complex(s11_re, s11_im)
            s21_data = complex(s21_re, s21_im)
            await self.data_queue.put((s11_data, s21_data))
            if self.verbose:
                print(f"Generated data: S11={s11_data}, S21={s21_data}")
                print(f"Queue length: {self.data_queue.qsize()}")
            await asyncio.sleep(2)  # Added sleep to simulate time delay

    async def consume_data(self):
        while True:
            s11_data, s21_data = await self.data_queue.get()
            print(f"Consumed data: S11={s11_data}, S21={s21_data}")
            self.data_queue.task_done()
