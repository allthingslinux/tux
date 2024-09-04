import discord
from discord.ext import commands

from prisma.models import AFKModel
from tux.bot import Tux
from tux.database.controllers import AfkController


class AFK(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = AfkController()

    @commands.hybrid_command(
        name="afk",
        usage="afk [reason]",
    )
    @commands.guild_only()
    async def afk(self, ctx: commands.Context[Tux], *, reason: str = "No reason."):
        if not ctx.guild:
            return await ctx.send("This command cannot be used in direct messages.")

        target = ctx.author
        assert isinstance(target, discord.Member)  # only hit if inside a guild

        if await self.db.is_afk(target.id, guild_id=ctx.guild.id):
            return await ctx.send("You are already afk!", ephemeral=True)

        max_name_limit = 32 - 6  # accounts for "[AFK] "
        if len(target.display_name) >= max_name_limit:
            return await ctx.send("Your name is too long!", ephemeral=True)

        await self.db.insert_afk(target.id, target.display_name, reason, ctx.guild.id)
        await target.edit(nick=f"[AFK] {target.display_name}")
        return await ctx.send(
            content="\N{SLEEPING SYMBOL} || You are now afk! " + f"Reason: `{reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )

    @commands.Cog.listener("on_message")
    async def remove_afk(self, message: discord.Message):
        if not message.guild:
            return

        if message.author.bot:
            return

        entry = await self.db.get_afk_member(message.author.id, guild_id=message.guild.id)
        if not entry:
            return

        assert isinstance(message.author, discord.Member)

        await self.db.remove_afk(message.author.id)
        await message.reply("Welcome back!", delete_after=5)
        await message.author.edit(nick=entry.nickname)

    @commands.Cog.listener("on_message")
    async def check_afk(self, message: discord.Message):
        if not message.guild:
            return

        if message.author.bot:
            return

        afks_mentioned: list[AFKModel] = []
        for mentioned in message.mentions:
            entry = await self.db.get_afk_member(mentioned.id, guild_id=message.guild.id)
            if entry:
                afks_mentioned.append(entry)

        if not afks_mentioned:
            return

        msgs: list[str] = []
        for mentioned, afk in zip(message.mentions, afks_mentioned, strict=False):
            msgs.append(f"{mentioned.mention} is currently AFK: `{afk.reason}` (<t:{int(afk.since.timestamp())}:R>)")

        await message.reply(
            content="\n".join(msgs),
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )


async def setup(bot: Tux):
    await bot.add_cog(AFK(bot))
