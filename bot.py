from botoy import bot

bot.set_url('127.0.0.1:8086')

bot.load_plugins()
bot.print_receivers()

from bg_tasks import start_bg
start_bg()

bot.run()
