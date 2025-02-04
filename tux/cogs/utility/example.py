import discord
from discord import app_commands
from discord.ext import commands

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator

# This is a example cog file for Tux.


class Example(commands.Cog):  # Change the name of the class to match your file name.
    def __init__(self, bot: Tux) -> None:  # You can define variables here and access them with self.<variable>
        self.bot = bot

    @commands.hybrid_command(  # Lets you use both slash and prefix commands.
        name="example",  # This is the name of the command for both slash and prefix.
        aliases=["test"],  # Optional aliases for the command.
    )
    # @commands.command()  # This is a prefix command. Avoid this unless absolutely necessary.
    async def example_hybrid_or_prefix(self, ctx: commands.Context[Tux]) -> None:
        """
        Example command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """

        embed = EmbedCreator.create_embed(  # Here you can create an embed using the EmbedCreator class.
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Example Embed",
            description="This is an example embed.",
        )

        await ctx.send(embed=embed)

    @app_commands.command(name="example-app-command")  # This is a slash command.
    async def example_app_command(self, interaction: discord.Interaction) -> None:
        """
        Example slash command.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        embed = EmbedCreator.create_embed(  # Here you can create an embed using the EmbedCreator class.
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=interaction.user.name,
            user_display_avatar=interaction.user.display_avatar.url,
            title="Example Embed",
            description="This is an example embed.",
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Example(bot))  # Don't forget to change the name of the class to match your file name here too.
