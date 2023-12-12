from discord.ext import commands
import os
import logging


class EventHandler(commands.Cog):
    def __init__(self, bot, debug=False):
        self.bot = bot
        self.debug = debug
        self.setup_logging()
        self.load_events()

    def setup_logging(self):
        logging_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(level=logging_level,
                            format='%(asctime)s [%(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def load_events(self):
        events_dir = os.path.join(os.path.dirname(__file__), 'events')

        for filename in os.listdir(events_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                event_name = filename[:-3]  # Remove the '.py' extension
                module = f'src.events.{event_name}'

                try:
                    self.bot.load_extension(module)
                    logging.debug(f'Successfully loaded event: {module}')
                except Exception as e:
                    logging.error(f'Failed to load event {module}. Error: {e}')

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'{self.bot.user} has connected to Discord!')


def setup(bot, debug=False):
    bot.add_cog(EventHandler(bot, debug))
