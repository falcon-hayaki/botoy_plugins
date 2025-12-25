import asyncio
import logging
import os
import time
import inspect
from logging import Formatter
from logging.handlers import RotatingFileHandler

from botoy import bot

# Ensure logs directory exists
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging to file and console
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fmt = Formatter("%(asctime)s %(levelname)s:%(name)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(fmt)
logger.addHandler(console_handler)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "botoy.log"),
    maxBytes=500 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(fmt)
logger.addHandler(file_handler)

# Reduce noisy library loggers to INFO (suppress DEBUG spam)
for noisy in ("websockets", "websockets.client", "httpx", "urllib3", "googleapiclient", "asyncio"):
    logging.getLogger(noisy).setLevel(logging.INFO)

bot.load_plugins()
bot.print_receivers()


async def _async_run_with_reconnect(bot):
    while True:
        try:
            await bot.run()
        except Exception as e:
            logger.error(f"bot.run() 失败: {e}")
            await asyncio.sleep(5)


def _sync_run_with_reconnect(bot):
    while True:
        try:
            bot.run()
        except Exception as e:
            logger.error(f"bot.run() 失败: {e}")
            time.sleep(5)


def main():
    try:
        if inspect.iscoroutinefunction(bot.run):
            asyncio.run(_async_run_with_reconnect(bot))
        else:
            _sync_run_with_reconnect(bot)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()