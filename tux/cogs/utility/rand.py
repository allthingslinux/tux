import random

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Random(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="coinflip", description="Flip a coin.")
    async def coinflip(self, interaction: discord.Interaction) -> None:
        """
        Flip a coin.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """
        await interaction.response.send_message(
            content="You got heads!" if random.choice([True, False]) else "You got tails!"
        )

        logger.info(f"{interaction.user} used the coinflip command in {interaction.channel}.")

    @app_commands.command(name="8ball", description="Ask the magic 8ball a question.")
    @app_commands.describe(question="The question to ask the 8ball.")
    async def eight_ball(self, interaction: discord.Interaction, question: str) -> None:
        """
        Ask the magic 8ball a question.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        question : str
            The question to ask the 8ball.
        """
        responses = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes definitely",
            "You may rely on it",
            "As I see it yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful",
        ]

        choice = random.choice(responses)

        response = f"""Response to "{question}":
  {"_" * len(choice)} 
< {choice} >
  {"-" * len(choice)}
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
"""

        await interaction.response.send_message(content=f"```{response}```")

        logger.info(f"{interaction.user} used the 8ball command in {interaction.channel}.")

    @app_commands.command(name="dice", description="Roll a dice.")
    @app_commands.describe(sides="The number of sides on the dice. (default: 6)")
    async def dice(self, interaction: discord.Interaction, sides: int = 6) -> None:
        """
        Roll a dice.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        sides : int, optional
            The number of sides on the dice, by default 6.
        """
        if sides < 2:
            await interaction.response.send_message(content="The dice must have at least 2 sides.")
            return

        embed = EmbedCreator.create_info_embed(
            title=f"Dice Roll (D{sides})",
            description=f"You rolled a {random.randint(1, sides)}!",
            interaction=interaction,
        )

        await interaction.response.send_message(embed=embed)

        logger.info(f"{interaction.user} used the dice command in {interaction.channel}.")

    @app_commands.command(name="randomnumber", description="Generate a random number.")
    @app_commands.describe(
        minimum="The minimum value of the random number. (default: 0)",
        maximum="The maximum value of the random number. (default: 100)",
    )
    async def random_number(
        self, interaction: discord.Interaction, minimum: int = 0, maximum: int = 100
    ) -> None:
        """
        Generate a random number.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        minimum : int, optional
            The minimum value of the random number, by default 0.
        maximum : int, optional
            The maximum value of the random number, by default 100.
        """
        if minimum > maximum:
            await interaction.response.send_message(
                content="The minimum value must be less than the maximum value."
            )
            return

        embed = EmbedCreator.create_info_embed(
            title="Random Number",
            description=f"Your random number is: {random.randint(minimum, maximum)}",
            interaction=interaction,
        )

        await interaction.response.send_message(embed=embed)

        logger.info(f"{interaction.user} used the randomnumber command in {interaction.channel}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Random(bot))
