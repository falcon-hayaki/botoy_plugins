import asyncio
import logging
import time

from botoy import bot

bot.load_plugins()
bot.print_receivers()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_with_reconnect(bot):
    while True:
        try:
            await bot.run()
        except Exception as e:
            logger.error(f"bot.run() 失败: {e}")
            await asyncio.sleep(5)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_with_reconnect(bot))
    loop.close()

if __name__ == "__main__":
    main()