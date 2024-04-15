import asyncio
from async_data_processor import AsyncDataProcessor


async def main():
    nanoVNA = AsyncDataProcessor(simulate=True, verbose=True)
    await nanoVNA.run()  # Runs both streaming and continuous processing of data. 


if __name__ == "__main__":
    asyncio.run(main())
