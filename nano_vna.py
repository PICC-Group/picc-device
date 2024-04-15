import asyncio

from signal_processing import (
    SignalProcessing,
)  # Ensure SignalProcessing class is adapted for async queue use
from simulate_data import (
    SimulateData,
)  # Ensure SimulateData class is adapted for continuous data generation


class NanoVNA:
    def __init__(self, simulate=True, verbose=False):
        self.simulate = simulate
        self.verbose = verbose
        self.data_queue = asyncio.Queue()  # Queue for inter-class communication
        self.data_source = SimulateData(
            self.data_queue, verbose=self.verbose
        )  # SimulateData now handles continuous data generation
        self.signal_processing = SignalProcessing(
            self.data_queue, verbose=self.verbose
        )  # Pass queue to SignalProcessing
        self.running = True

    async def run(self):
        start_data = asyncio.create_task(self.data_source.generate_start_data())  # Reads a few data points before the processing starts, to avoid empty queue
        producer = asyncio.create_task(self.data_source.generate_data_continuously())
        consumer = asyncio.create_task(
            self.signal_processing.process_data_continuously()
        )
        try:
            await asyncio.gather(start_data)
            await asyncio.gather(start_data, producer, consumer)
        except asyncio.CancelledError:
            pass  # Handle cleanup if necessary

    def stop(self):
        # Stops the continuous reading and processing of data
        self.running = False
