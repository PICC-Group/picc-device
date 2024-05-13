import asyncio
import pynanovna

from signal_processing import (
    SignalProcessing,
)


# File used for calibratin the vna.
CALIBRATION_FILE = "../oscars_cal.cal"


class AsyncDataProcessor:
    def __init__(
        self,
        datafile: str = False,
        calibration_file: str = False,
        producer_sleep_time: float = 0.1,
        process_sleep_time: float = 0.0001,
        verbose: bool = False,
    ):
        """Initialize a AsyncDataProcessor object.

        Args:
            simulate (bool): Uses and instance of the SimulateData class for simulated data as data source if true, otherwise uses an istance of the NanoVNAData class for streaming or playback of data.
            datafile (str): File for playback mode when simulate is false. If simulate is false and datafile false, then streaming from nanoVNA is used.
            producer_sleep_time (float): Sleep time after generating/producing data function is called.
            process_sleep_time (foat): Sleep time after processing data function is called.
            verbose (bool): Prints information if true.
        """
        self.producer_sleep_time = producer_sleep_time
        self.process_sleep_time = process_sleep_time
        self.verbose = verbose
        self.datafile = datafile

        self.data_source = pynanovna.NanoVNAWorker(verbose=verbose)
        self.data_source.calibrate(
            calibration_file
        )  #  This needs to be done through a terminal atm.
        self.data_source.set_sweep(2.9e9, 3.1e9, 1, 101)
        self.data_stream = self.data_source.stream_data(datafile)

        self.signal_processing = SignalProcessing(
            self.data_stream,
            process_sleep_time=self.process_sleep_time,
            verbose=self.verbose,
        )
        self.running = True

    async def run(self):
        consumer = asyncio.create_task(
            self.signal_processing.process_data_continuously(self.data_stream)
        )
        try:
            await asyncio.gather(consumer)
        except asyncio.CancelledError:
            pass  # Handle cleanup if necessary

    def stop(self):
        # Stops the continuous reading and processing of data
        self.running = False
