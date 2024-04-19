import asyncio

from signal_processing import (
    SignalProcessing,
)
from simulate_data import (
    SimulateData,
)
from nanovna_data import (
    NanoVNAData
)

# File used for calibratin the vna. 
CALIBRATION_FILE = (
    "./test_cali.s2p"  # "Calibration_file_2024-04-12 12:23:02.604314.s2p"
)


class AsyncDataProcessor:
    def __init__(self, datafile=False, sleep_time=0.1, verbose=False):
        self.simulate = not datafile  # True if we are simulating data, false if we are streaming from the nanoVNA
        self.sleep_time = sleep_time
        self.verbose = verbose
        self.datafile = datafile
        self.data_queue = asyncio.Queue()  # Queue for inter-class communication
        if self.simulate:  # Runs on simulated data.
            self.data_source = SimulateData(data_queue=self.data_queue, sleep_time=self.sleep_time, verbose=self.verbose)
        else:  # Runs on streamed data from the vna.
            # TODO: Put nanoVNA data into a async Queue that is refered to as self.data_source. 
            self.data_source = NanoVNAData(data_queue=self.data_queue, sleep_time=self.sleep_time, verbose=self.verbose)

        self.signal_processing = SignalProcessing(
            data_queue=self.data_queue, sleep_time=self.sleep_time, verbose=self.verbose
        )  # Pass queue to SignalProcessing
        self.running = True

    async def run(self):
        producer = asyncio.create_task(
            self.data_source.generate_data_continuously(self.datafile)
        )

        consumer = asyncio.create_task(
            self.signal_processing.process_data_continuously()
        )
        try:
            await asyncio.gather(producer, consumer)
        except asyncio.CancelledError:
            pass  # Handle cleanup if necessary

    def stop(self):
        # Stops the continuous reading and processing of data
        self.running = False
