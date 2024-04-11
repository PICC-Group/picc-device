import asyncio

from signal_processing import SignalProcessing

class NanoVNA:
    def __init__(self, batch_size=3, simulate=True, verbose=False):
        self.batch_size = batch_size
        self.simulate = simulate
        self.signal_processing = SignalProcessing()
        self.verbose = verbose
        if self.simulate:
            from simulate_data import SimulateData
            self.data_source = SimulateData(batch_size=batch_size)
        else: 
            # Using real data. Import functionality from nanovna-saver-headless repo.
            pass
        self.running = True

    async def process_data(self):
        try:
            while self.running:
                if self.simulate:
                    s11_batch, s21_batch = await self.data_source.generate_batch()
                    result1 = self.signal_processing.process_gas_phase(s21_batch)
                    result2 = self.signal_processing.process_direction(s11_batch, s21_batch)
                    if self.verbose:
                        print(f"Result 1: {result1}")
                        print(f"Result 2: {result2}")

                    await asyncio.sleep(1)  # Adapt this.
                else:
                    # Using the real data from the nanoVNA. 
                    pass
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Stopping rading and processing of data.")
            self.stop()

    def stop(self):
        # Stops the continuous reding and processing of data. 
        self.running = False
