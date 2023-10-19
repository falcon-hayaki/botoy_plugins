from botoy import bot

bot.set_url('127.0.0.1:8086')

bot.load_plugins()
bot.print_receivers()
bot.run()