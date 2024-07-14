import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator

meta_fields = [
    "<#1172252854371749958>",
    "<#1172343581495795752>",
    "<#1172259762893754480>",
    "<#1193304492226129971>",
]

support_fields = ["<#1172312602181902357>", "<#1172312653797007461>", "<#1172312674298761216>"]

resources_fields = [
    "<#1221117147091304548>",
    "<#1221115462549504060>",
    "<#1174251004586381323>",
    "<#1174742125036961863>",
    "<#1220004498789896253>",
]


class Guide(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="guide", description="See useful channels for the server.")
    async def guide(self, interaction: discord.Interaction) -> None:
        """
        Send a guide to the server with useful channels and resources.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        guild = interaction.guild

        if not guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        embed = EmbedCreator.create_info_embed(
            title="Server Guide",
            description=f"Welcome to {guild.name}!",
            interaction=interaction,
        )

        embed.add_field(name="Meta", value="\n".join(meta_fields), inline=False)
        embed.add_field(name="Support", value="\n".join(support_fields), inline=False)
        embed.add_field(name="Resources", value="\n".join(resources_fields), inline=False)

        embed.set_thumbnail(url=guild.icon)

        await interaction.response.send_message(embed=embed)

        logger.info(f"{interaction.user} used the guide command in {interaction.channel}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Guide(bot))
