import asyncio
import logging
import os
from logging import Formatter

from botoy import bot

# Ensure logs directory exists
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging to file and console
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = Formatter("%(asctime)s %(levelname)s:%(name)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(fmt)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(os.path.join(LOG_DIR, "botoy.log"), encoding="utf-8")
file_handler.setFormatter(fmt)
logger.addHandler(file_handler)

bot.load_plugins()
bot.print_receivers()


async def run_with_reconnect(bot):
    while True:
        try:
            await bot.run()
        except Exception as e:
            logger.error(f"bot.run() 失败: {e}")
            await asyncio.sleep(5)


def main():
    try:
        asyncio.run(run_with_reconnect(bot))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()