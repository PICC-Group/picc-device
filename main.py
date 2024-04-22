import asyncio
from async_data_processor import AsyncDataProcessor

DATA_FILE = None#"../nanovna-saver-headless/testData/0grader3cm.csv"
async def main():
    nanoVNA = AsyncDataProcessor(datafile=DATA_FILE, sleep_time=0.01, verbose=True)
    await nanoVNA.run()  # Runs both streaming and continuous processing of data. 


if __name__ == "__main__":
    asyncio.run(main())
