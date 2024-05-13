import asyncio
from async_data_processor import AsyncDataProcessor

DATA_FILE = "../save_plate.csv"


async def main():
    async_data_stream = AsyncDataProcessor(
        datafile=DATA_FILE,
        producer_sleep_time=0.1,
        process_sleep_time=0.0001,
        verbose=True,
    )
    await async_data_stream.run()  # Runs both streaming and continuous processing of data.


if __name__ == "__main__":
    asyncio.run(main())
