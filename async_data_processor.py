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
    "../oscars_cal.cal" #"./test_cali.s2p"  # "Calibration_file_2024-04-12 12:23:02.604314.s2p"
)


class AsyncDataProcessor:
    def __init__(self, simulate: bool=False, datafile: str=None, producer_sleep_time: float=0.1, process_sleep_time: float= 0.0001, verbose: bool=False):
        """Initialize a AsyncDataProcessor object.

        Args:
            simulate (bool): Uses and instance of the SimulateData class for simulated data as data source if true, otherwise uses an istance of the NanoVNAData class for streaming or playback of data. 
            datafile (str): File for playback mode when simulate is false. If simulate is false and datafile none, then streaming from nanoVNA is used.
            producer_sleep_time (float): Sleep time after generating/producing data function is called.
            process_sleep_time (foat): Sleep time after processing data function is called. 
            verbose (bool): Prints information if true. 
        """
        self.simulate = simulate  # True if we are simulating data, false if we are streaming from the nanoVNA or using Data file
        self.producer_sleep_time = producer_sleep_time
        self.process_sleep_time = process_sleep_time
        self.verbose = verbose
        self.datafile = datafile
        self.data_queue = asyncio.Queue()  # Queue for inter-class communication
        if self.simulate:  # Runs on simulated data.
            self.data_source = SimulateData(data_queue=self.data_queue, producer_sleep_time=self.producer_sleep_time, verbose=self.verbose)
        else:  # Runs on streamed data from the vna.
            self.data_source = NanoVNAData(data_queue=self.data_queue, producer_sleep_time=self.producer_sleep_time, verbose=self.verbose)

        self.signal_processing = SignalProcessing(
            data_queue=self.data_queue, process_sleep_time=self.process_sleep_time, verbose=self.verbose
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
