from discord.ext import commands
import os
import logging


class EventHandler(commands.Cog):
    def __init__(self, bot, debug=False):
        """
        Constructor for the EventHandler Cog.

        Parameters:
            bot (commands.Bot): The instance of the Discord bot.
            debug (bool): A flag indicating whether debug mode is enabled.
        """
        self.bot = bot
        self.debug = debug
        self._setup_logging()
        self.ignore_cogs = []

    def _setup_logging(self):
        """
        Configures logging settings based on the debug flag.
        """
        logging_level = logging.DEBUG if self.debug else logging.INFO

        logging.basicConfig(
            level=logging_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    async def _load_events(self):
        """
        Dynamically loads event modules from the 'events' directory.

        Each event module should be a Python file in the 'events' directory.
        The file name (excluding extension) is considered the event name.
        """
        events_dir = os.path.join(os.path.dirname(__file__), 'events')

        for filename in os.listdir(events_dir):
            event_name = filename[:-3]
            module = f'tux_events.events.{event_name}'

            if not filename.endswith('.py') or event_name in self.ignore_cogs \
                    or filename.startswith('__'):
                logging.info(f"Skipping {module}.")
                continue

            try:
                await self.bot.load_extension(module)
                logging.debug(f'Successfully loaded event: {module}')
            except Exception as e:
                logging.error(f'Failed to load event {module}. Error: {e}')

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Event handler for the bot being ready.

        This function is called when the bot successfully connects to Discord.
        """
        logging.info(f'{self.bot.user} has connected to Discord!')

    @classmethod
    async def setup(cls, bot, debug=False):
        """
        Sets up the EventHandler Cog and adds it to the bot.

        Parameters:
            bot (commands.Bot): The instance of the Discord bot.
            debug (bool): A flag indicating whether debug mode is enabled.
        """
        cog = cls(bot, debug)
        await cog._load_events()
        await bot.add_cog(cog)
