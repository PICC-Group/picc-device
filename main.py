import asyncio

from nano_vna import NanoVNA

async def main():
    nanoVNA = NanoVNA(batch_size=2, verbose=True)
    await nanoVNA.process_data()

if __name__ == "__main__":
    asyncio.run(main())