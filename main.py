import asyncio
from async_data_processor import AsyncDataProcessor

DATA_FILE = False  # "../nanovna-saver-headless/testData/0grader3cm.csv"


async def main():
    async_data_stream = AsyncDataProcessor(
        datafile=False,
        producer_sleep_time=0.1,
        process_sleep_time=0.0001,
        verbose=False,
    )
    await async_data_stream.run()  # Runs both streaming and continuous processing of data.


if __name__ == "__main__":
    asyncio.run(main())
