import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class setSlowmode(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(
        name="set_slowmode", description="sets the slowmode for a channel in the server."
    )
    @app_commands.describe(delay="The slowmode time in seconds, max is 21600, default is 5")
    async def set_slowmode(self, interaction: discord.Interaction, delay: int = 5) -> None:
        # make a variable for the channel after null-checking and type-checking so the linter won't blow on me
        if interaction.channel and interaction.channel.type == discord.ChannelType.text:
            # global channel
            channel: discord.TextChannel = interaction.channel

            logger.info(
                f"{interaction.user} used the set_slowmode command in {channel.name} to change slowmode for channel."
            )

            # discord supports slowmode delay to be no more than 21600 and no less than 0 (disables slowmode)
            if delay > 21600:
                embed = discord.Embed(
                    color=discord.Colour.red(),
                    title="Error",
                    description="The slowmode delay cant be more than 21600 or less than 0",
                    timestamp=interaction.created_at,
                )
                embed.set_footer(
                    text=f"Requested by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar,
                )
                await interaction.response.send_message(embed=embed)
                return

            try:
                await channel.edit(slowmode_delay=delay)
                if delay > 0:
                    embed = discord.Embed(
                        color=discord.Colour.green(),
                        title="Success!",
                        description=f"slowmode delay has been set to {delay} for <#{channel.id}>",
                        timestamp=interaction.created_at,
                    )
                    embed.set_footer(
                        text=f"Requested by {interaction.user.display_name}",
                        icon_url=interaction.user.display_avatar,
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = discord.Embed(
                        color=discord.Colour.green(),
                        title="Success!",
                        description=f"slowmode delay has disabled for <#{channel.id}> successfully",
                        timestamp=interaction.created_at,
                    )
                    embed.set_footer(
                        text=f"Requested by {interaction.user.display_name}",
                        icon_url=interaction.user.display_avatar,
                    )
                    await interaction.response.send_message(embed=embed)

            # You don't have permission
            except discord.errors.Forbidden as e:
                embed_error = discord.Embed(
                    colour=discord.Colour.red(),
                    title=f"Failed to change slowmode for {channel.name}",
                    description=f"tldr: You don't have permission\n`Error info: {e}`",
                    timestamp=interaction.created_at,
                )
                embed_error.set_footer(
                    text=f"Requested by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar,
                )
                await interaction.response.send_message(embed=embed_error)
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(setSlowmode(bot))
