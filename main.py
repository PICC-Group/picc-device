import asyncio
from nano_vna import NanoVNA


async def main():
    nanoVNA = NanoVNA(simulate=True, verbose=True)
    await nanoVNA.run()  # Changed to use the new run method that handles both production and consumption


if __name__ == "__main__":
    asyncio.run(main())
