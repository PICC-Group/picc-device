import asyncio

from signal_processing import (
    SignalProcessing,
)
from simulate_data import (
    SimulateData,
)
from nanovna_saver_headless.src.NanoVNASaverHeadless import NanoVNASaverHeadless

# File used for calibratin the vna. 
CALIBRATION_FILE = (
    "./test_cali.s2p"  # "Calibration_file_2024-04-12 12:23:02.604314.s2p"
)


class AsyncDataProcessor:
    def __init__(self, simulate=False, verbose=False):
        self.simulate = simulate  # True if we are simulating data, false if we are streaming from the nanoVNA
        self.verbose = verbose
        self.data_queue = asyncio.Queue()  # Queue for inter-class communication
        if self.simulate:  # Runs on simulated data.
            self.data_source = SimulateData(self.data_queue, verbose=self.verbose)
        else:  # Runs on streamed data from the vna.
            # TODO: Put nanoVNA data into a async Queue that is refered to as self.data_source. 
            self.data_source = NanoVNASaverHeadless(vna_index=0, verbose=self.verbose)
            self.data_source.calibrate(None, CALIBRATION_FILE)  # Calibrates the vna
            self.data_source.set_sweep(2.9e9, 3.1e9, 1, 101)  # Sets the sweep.

        self.signal_processing = SignalProcessing(
            self.data_queue, verbose=self.verbose
        )  # Pass queue to SignalProcessing
        self.running = True

    async def run(self):
        if self.simulate:
            start_buffer_data = asyncio.create_task(
                self.data_source.generate_start_data()
            )  # Reads a few data points before the processing starts, to avoid empty queue
            producer = asyncio.create_task(
                self.data_source.generate_data_continuously()
            )
        else:
            # TODO: Make sure that 'self.data_source' is a async Queue with functions for handeling continuous data streaming. 
            start_buffer_data = ...
            producer = ...

        consumer = asyncio.create_task(
            self.signal_processing.process_data_continuously()
        )
        try:
            await asyncio.gather(start_buffer_data)
            await asyncio.gather(producer, consumer)
        except asyncio.CancelledError:
            pass  # Handle cleanup if necessary

    def stop(self):
        # Stops the continuous reading and processing of data
        self.running = False
