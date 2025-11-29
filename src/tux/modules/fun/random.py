"""
Random generation commands for entertainment and utility.

This module provides various random generation commands including coin flips,
dice rolls, magic 8-ball responses, and random number generation. All commands
are designed for fun and entertainment in Discord servers.
"""

import random
from textwrap import shorten, wrap

from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.constants import (
    EIGHT_BALL_QUESTION_LENGTH_LIMIT,
    EIGHT_BALL_RESPONSE_WRAP_WIDTH,
)
from tux.shared.functions import truncate
from tux.ui.embeds import EmbedCreator


class Random(BaseCog):
    """Discord cog for random generation commands.

    Provides various random generation commands including coin flips, dice rolls,
    magic 8-ball responses, and random number generation. All commands are
    designed to be fun and entertaining for Discord server members.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Random cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_group(
        name="random",
        aliases=["rand"],
    )
    @commands.guild_only()
    async def random(self, ctx: commands.Context[Tux]) -> None:
        """
        Random generation commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("random")

    @random.command(
        name="coinflip",
        aliases=["cf"],
    )
    @commands.guild_only()
    async def coinflip(self, ctx: commands.Context[Tux]) -> None:
        """
        Flip a coin.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        await ctx.reply(
            content="You got heads!"
            if random.choice([True, False])
            else "You got tails!",
        )

    @random.command(
        name="8ball",
        aliases=["eightball", "8b"],
    )
    @commands.guild_only()
    async def eight_ball(
        self,
        ctx: commands.Context[Tux],
        *,
        question: str,
        cow: bool = False,
    ) -> None:
        """
        Ask the magic 8ball a question.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        question : str
            The question to ask the 8ball.
        cow : bool, optional
            Whether to use the cow ASCII art, by default False.
        """
        yes_responses = [
            "Hell yeah",
            "Absolutely",
            "Totally",
            "Why not?",
            "100% chance",
            "My gut says yes",
            "Without a doubt",
            "Signs point to yes",
            "It is certain",
            "Only one way to find out",
        ]

        no_responses = [
            "Hell no",
            "When pigs fly",
            "Absolutely not",
            "No way",
            "Don't count on it",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful",
            "0% chance",
            "No",
        ]

        unsure_responses = [
            "Probably, Maybe, Possibly, Perhaps",
            "¯\\_(ツ)_/¯",
            "Why are you asking me?",
            "What???",
            "Ask someone else for once, I'm tired of answering your questions.",
            "?",
            "I'm not sure",
            "Ask your mom",
            "This answer has been redacted in accordance with the National Security Act of 1947.",
            "Don't ask a penguin for advice",
            "I may be a robot but some questions are just too stupid to answer.",
            "Reply hazy, try again",
            "Cannot predict now",
            "Ask again later",
        ]

        choice = random.choice(
            [
                random.choice(yes_responses),
                random.choice(no_responses),
                random.choice(unsure_responses),
            ],
        )

        width = min(EIGHT_BALL_RESPONSE_WRAP_WIDTH, len(choice))
        chunks = wrap(choice, width)

        if len(chunks) > 1:
            chunks = [chunk.ljust(width) for chunk in chunks]

        formatted_choice = (
            f"  {'_' * width}\n< {' >\n< '.join(chunks)} >\n  {'-' * width}"
        )

        shortened_question = shorten(
            question,
            width=EIGHT_BALL_QUESTION_LENGTH_LIMIT,
            placeholder="...",
        )

        response = f'Response to "{shortened_question}":\n{formatted_choice}'

        if cow:
            response += """
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
"""
        else:
            response += """
   \\
    \\
        .--.
       |o_o |
       |:_/ |
      //   \\ \\
     (|     | )
    /'\\_   _/`\\
    \\___)=(___/
"""
        await ctx.reply(content=f"```{response}```")

    @random.command(
        name="dice",
        aliases=["d"],
    )
    @commands.guild_only()
    async def dice(self, ctx: commands.Context[Tux], sides: int = 6) -> None:
        """
        Roll a dice.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        sides : int, optional
            The number of sides on the dice, by default 6.
        """
        if sides < 2:
            await ctx.reply(
                content="The dice must have at least 2 sides.",
                ephemeral=True,
            )
            return

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=f"Dice Roll (D{truncate(str(sides), 50)})",
            description=f"You rolled a {random.randint(1, sides)}!",
        )

        await ctx.reply(embed=embed)

    @random.command(
        name="number",
        aliases=["n"],
    )
    @commands.guild_only()
    async def random_number(
        self,
        ctx: commands.Context[Tux],
        minimum_str: str = "0",
        maximum_str: str = "100",
    ) -> None:
        """
        Generate a random number between two values.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        minimum_str : str, optional
            The minimum value of the random number, by default 0. Converted to int after removing certain characters.
        maximum_str : str, optional
            The maximum value of the random number, by default 100. Converted to int after removing certain characters.

        """
        try:
            minimum_int = int(minimum_str.replace(",", "").replace(".", ""))
            maximum_int = int(maximum_str.replace(",", "").replace(".", ""))

        except ValueError:
            await ctx.reply(
                content="Invalid input for minimum or maximum value. Please provide valid numbers.",
                ephemeral=True,
            )
            return

        if minimum_int > maximum_int:
            await ctx.reply(
                content="The minimum value must be less than the maximum value.",
                ephemeral=True,
            )
            return

        await ctx.reply(
            content=f"Your random number is: {random.randint(minimum_int, maximum_int)}",
        )


async def setup(bot: Tux) -> None:
    """Set up the Random cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Random(bot))
