import random

from discord.ext import commands

from tux.utils.embeds import EmbedCreator


class Random(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="random",
        aliases=["rand"],
        usage="$random <subcommand>",
    )
    @commands.guild_only()
    async def random(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Random generation commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("random")

    @random.command(
        name="coinflip",
        aliases=["cf"],
        usage="$random coinflip",
    )
    @commands.guild_only()
    async def coinflip(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Flip a coin.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        """

        await ctx.send(
            content="You got heads!" if random.choice([True, False]) else "You got tails!",
        )

    @random.command(
        name="8ball",
        aliases=["eightball", "8b"],
        usage="$random 8ball [question]",
    )
    @commands.guild_only()
    async def eight_ball(self, ctx: commands.Context[commands.Bot], *, question: str, cow: bool = False) -> None:
        """
        Ask the magic 8ball a question.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        question : str
            The question to ask the 8ball.
        cow : bool, optional
            Whether to use the cow ASCII art, by default False.
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
            "Probably",
            "Outlook not so good",
            "Very doubtful",
            "Why the hell are you asking me lmao",
            "What???",
            "Hell yeah",
            "Hell no",
            "When pigs fly",
            "Ask someone else for once, I'm sick and tired of answering your questions you absolute buffoon.",
            "I dont know, ask me later",
            "I'm not sure",
            "Ask your mom",
            "Ask Puffy or Beastie",
            "Absolutely",
            "Absolutely not",
            "You're joking right?",
            "Ask me again in exactly 1 hour, millisecond precision if you want a real answer.",
            "Ask a real person.",
            "I may be a robot but some questions are just too stupid to answer.",
        ]

        choice = random.choice(responses)

        if cow:
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
        else:
            response = f"""Response to "{question}":
  {"_" * len(choice)}
< {choice} >
  {"-" * len(choice)}
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
        await ctx.send(content=f"```{response}```")

    @random.command(
        name="dice",
        aliases=["d"],
        usage="$random dice <sides>",
    )
    @commands.guild_only()
    async def dice(self, ctx: commands.Context[commands.Bot], sides: int = 6) -> None:
        """
        Roll a dice.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        sides : int, optional
            The number of sides on the dice, by default 6.
        """

        if sides < 2:
            await ctx.send(content="The dice must have at least 2 sides.", ephemeral=True, delete_after=30)
            return

        embed = EmbedCreator.create_info_embed(
            title=f"Dice Roll (D{sides})",
            description=f"You rolled a {random.randint(1, sides)}!",
            ctx=ctx,
        )

        await ctx.send(embed=embed)

    @random.command(
        name="number",
        aliases=["n"],
        usage="$random number <min> <max>",
    )
    @commands.guild_only()
    async def random_number(
        self,
        ctx: commands.Context[commands.Bot],
        minimum: int = 0,
        maximum: int = 100,
    ) -> None:
        """
        Generate a random number between two values.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        minimum : int, optional
            The minimum value of the random number, by default 0.
        maximum : int, optional
            The maximum value of the random number, by default 100.
        """

        if minimum > maximum:
            await ctx.send(
                content="The minimum value must be less than the maximum value.",
                ephemeral=True,
                delete_after=30,
            )
            return

        await ctx.send(content=f"Your random number is: {random.randint(minimum, maximum)}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Random(bot))
