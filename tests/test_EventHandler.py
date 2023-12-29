import unittest
from unittest.mock import MagicMock

from tux.tux_events.event_handler import EventHandler


class TestEventHandler(unittest.TestCase):
    def setUp(self):
        # Create a mock bot instance
        self.mock_bot = MagicMock()
        # Create an EventHandler instance with debug mode disabled
        self.event_handler = EventHandler(self.mock_bot, debug=False)

    def test_setup_logging(self):
        # Ensure the logging level is correctly set based on the debug flag
        self.assertEqual(self.event_handler.debug, False)
        self.assertEqual(self.event_handler.setup_logging(), None)

        # Test the case when debug mode is enabled
        self.event_handler.debug = True
        self.assertEqual(self.event_handler.setup_logging(), None)

    def test_load_events(self):
        # Mock the os.listdir function to return a list of mock file names
        with unittest.mock.patch(
            "os.listdir",
            return_value=["on_leave.py", "on_join.py"],
        ):
            self.assertEqual(self.event_handler.load_events(), None)

        # Ensure that self.bot.load_extension is called for each event module
        self.mock_bot.load_extension.assert_called_with(
            "tux.tux_events.events.on_leave",
        )
        self.mock_bot.load_extension.assert_called_with("tux.tux_events.events.on_join")

    def test_on_ready(self):
        # Mock the logging.info function to track its calls
        with unittest.mock.patch("logging.info") as mock_info:
            self.assertEqual(
                self.event_handler.on_ready(),
                None,
            )  # It should return None

        # Ensure that logging.info is called with the correct message
        mock_info.assert_called_with(f"{self.mock_bot.user} has connected to Discord!")

    def test_setup(self):
        # Ensure that the EventHandler is added to the bot using bot.add_cog
        with unittest.mock.patch.object(self.mock_bot, "add_cog") as mock_add_cog:
            self.assertEqual(self.event_handler.setup(self.mock_bot, debug=True), None)

        # Ensure that bot.add_cog is called with the correct arguments
        mock_add_cog.assert_called_with(EventHandler(self.mock_bot, debug=True))


if __name__ == "__main__":
    unittest.main()
