from botoy import bot
from bg_tasks import start_scheduler, get_scheduler_jobs

bot.set_url('127.0.0.1:8086')

bot.load_plugins()
bot.print_receivers()

print(get_scheduler_jobs())
start_scheduler()

bot.run()