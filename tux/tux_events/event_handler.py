from discord.ext import commands
import os
import logging


class EventHandler(commands.Cog):
    def __init__(self, bot, debug=False):
        '''
        Constructor for the EventHandler Cog.

        :param bot: The Discord bot instance.
        :param debug: A flag indicating whether debug mode is enabled.
        '''
        self.bot = bot
        self.debug = debug
        self.setup_logging()
        self.load_events()

    def setup_logging(self):
        '''
        Configures the logging settings based on the debug flag.
        '''
        logging_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(level=logging_level,
                            format='%(asctime)s [%(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def load_events(self):
        '''
        Dynamically loads event modules from the 'events' directory.

        Each event module should be a Python file in the 'events' directory.
        The file name (excluding extension) is considered the event name.
        '''
        events_dir = os.path.join(os.path.dirname(__file__), 'events')

        for filename in os.listdir(events_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                # Remove the '.py' extension to get the event name
                event_name = filename[:-3]
                # Construct the full module path
                module = f'src.events.{event_name}'

                try:
                    # Load the event module
                    self.bot.load_extension(module)
                    logging.debug(f'Successfully loaded event: {module}')
                except Exception as e:
                    # Log an error message if loading fails
                    logging.error(f'Failed to load event {module}. Error: {e}')

    @commands.Cog.listener()
    async def on_ready(self):
        '''
        Event handler for the bot being ready.

        This function is called when the bot successfully connects to Discord.
        '''
        logging.info(f'{self.bot.user} has connected to Discord!')


def setup(bot, debug=False):
    '''
    Sets up the EventHandler Cog and adds it to the bot.

    :param bot: The Discord bot instance.
    :param debug: A flag indicating whether debug mode is enabled.
    '''
    bot.add_cog(EventHandler(bot, debug))