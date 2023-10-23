from botoy import bot
from bg_tasks import scheduler
import asyncio

bot.set_url('127.0.0.1:8086')

bot.load_plugins()
bot.print_receivers()

async def main():
    scheduler.start()
    bot.run()
    
asyncio.run(main)