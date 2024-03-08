from botoy import bot
import time

bot.load_plugins()
bot.print_receivers()

while True:
    bot.run()
    time.sleep(5)
