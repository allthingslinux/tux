# # utils/audit_logger.py

# import discord
# from discord.ext import commands

# from tux.utils.tux_logger import TuxLogger

# logger = TuxLogger(__name__)


# MOD_CHANNEL_ID = 1191472088695980083


# class AuditLogger(commands.Cog):
#     def __init__(self, bot: commands.Bot):
#         self.bot = bot

#     async def send_audit_log(
#         self, title, description, color=0x7289DA, url=None, timestamp=None, fields=None
#     ):
#         channel = self.bot.get_channel(MOD_CHANNEL_ID)
#         embed = discord.Embed(
#             title=title,
#             description=description,
#             color=color,
#             url=url,
#             timestamp=timestamp,
#         )

#         if fields:
#             for name, value, inline in fields:
#                 embed.add_field(name=name, value=value, inline=inline)

#         if isinstance(channel, discord.TextChannel):
#             await channel.send(embed=embed)
#         else:
#             logger.error(
#                 f"Failed to send message: Channel '{channel}' is not a text channel."
#             )


# async def setup(bot: commands.Bot):
#     await bot.add_cog(AuditLogger(bot))
