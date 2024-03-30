import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class unban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="unban", description="unbans a user from the server.")
    @app_commands.guild_only()
    @app_commands.describe(username="Memeber's username to unban", reason="Reason to unban member")
    async def unban(
        self,
        interaction: discord.Interaction,
        username: str,
        reason: str | None = None,
    ) -> None:
        # get a list  of banned users in the server
        banned_users: list[discord.User] = []
        user_to_unban: discord.User | None = None
        if interaction.guild:
            # the list is asyncIterator so I converted it to a normal list
            banned_users = [ban.user async for ban in interaction.guild.bans()]

        # now check if the provided username *exactly* matches a username in the list
        for banned_user in banned_users:
            user_to_unban = banned_user if username == banned_user.name else None

        if interaction.guild and user_to_unban:
            logger.info(
                f"{interaction.user} used the unban command in {interaction.channel} to unban user {user_to_unban.display_name}."
            )
            try:
                await interaction.guild.unban(user_to_unban, reason=reason)
                embed: discord.Embed = discord.Embed(
                    title=f"unbanned {user_to_unban.display_name}!",
                    color=discord.Colour.red(),
                    timestamp=interaction.created_at,
                    type="rich",
                )

                embed.add_field(
                    name="Reason",
                    value="`none provided`" if not reason else f"`{reason}`",
                    inline=True,
                )
                embed.add_field(
                    name="User",
                    value=f"<@{user_to_unban.id}>",
                    inline=True,
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
                    title=f"Failed to unban {user_to_unban.display_name}",
                    description=f"tldr: You don't have permission\n`Error info: {e}`",
                    timestamp=interaction.created_at,
                )
                embed_error.set_footer(
                    text=f"Requested by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar,
                )
                await interaction.response.send_message(embed=embed_error)

            # user_to_unban does not exist
            except discord.errors.NotFound as e:
                embed_error = discord.Embed(
                    colour=discord.Colour.red(),
                    title=f"Failed to unban {user_to_unban.display_name}",
                    description=f"tldr: No banned user matches the provided username\n`Error info: {e}`",
                    timestamp=interaction.created_at,
                )
                embed_error.set_footer(
                    text=f"Requested by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar,
                )
                await interaction.response.send_message(embed=embed_error)
                return

        return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(unban(bot))
