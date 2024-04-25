import asyncio
from async_data_processor import AsyncDataProcessor

DATA_FILE = "data/0grader3cm.csv"
DATA_FILE = None#"../nanovna-saver-headless/testData/0grader3cm.csv"

# 3 different data sources can be used. If simulate=True, then simulated data is used. If simulate=False, then the NanoVNAData class is used. 
# Then depending on if DATA_FILE is none, either playback mode is used or streaming directly from the nanoVNA. 
async def main():
    # Using simulated data
    #async_data_stream = AsyncDataProcessor(simulate=True, datafile=DATA_FILE, producer_sleep_time=0.1, process_sleep_time=0.0001, verbose=True)
    # Using playback mode
    #async_data_stream = AsyncDataProcessor(simulate=False, datafile=DATA_FILE, producer_sleep_time=0.1, process_sleep_time=0.0001, verbose=True)
    # Streaming data live from nanoVNA
    async_data_stream = AsyncDataProcessor(simulate=False, datafile=None, producer_sleep_time=0.1, process_sleep_time=0.0001, verbose=False)
    await async_data_stream.run()  # Runs both streaming and continuous processing of data. 


if __name__ == "__main__":
    asyncio.run(main())
