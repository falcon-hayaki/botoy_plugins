from botoy import bot
from bg_tasks import start_bg

bot.set_url('127.0.0.1:8086')

bot.load_plugins()
bot.print_receivers()

start_bg()

bot.run()
