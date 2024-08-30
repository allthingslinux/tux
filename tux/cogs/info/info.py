from collections.abc import Generator, Iterable, Iterator

import discord
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="info",
        aliases=["i"],
        usage="info <subcommand>",
    )
    async def info(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Information commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("info")

    @info.command(
        name="server",
        aliases=["s"],
        usage="info server",
    )
    async def server(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Show information about the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        """

        if not ctx.guild:
            return
        guild = ctx.guild

        embed = discord.Embed(
            title=ctx.guild.name,
            description=guild.description or "No description available.",
            color=discord.Color.blurple(),
        )

        embed.set_author(name="Server Information", icon_url=guild.icon)
        embed.add_field(name="Owner", value=str(guild.owner.mention) if guild.owner else "Unknown")
        embed.add_field(name="Vanity URL", value=guild.vanity_url_code or "None")
        embed.add_field(name="Boosts", value=guild.premium_subscription_count)
        embed.add_field(name="Text Channels", value=len(guild.text_channels))
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels))
        embed.add_field(name="Forum Channels", value=len(guild.forums))
        embed.add_field(name="Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}")
        embed.add_field(name="Stickers", value=f"{len(guild.stickers)}/{guild.sticker_limit}")
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Humans", value=sum(not member.bot for member in guild.members))
        embed.add_field(name="Bots", value=sum(member.bot for member in guild.members))
        embed.add_field(name="Bans", value=len([entry async for entry in guild.bans(limit=2000)]))
        embed.set_footer(text=f"ID: {guild.id} | Created: {guild.created_at.strftime('%B %d, %Y')}")

        await ctx.send(embed=embed)

    @info.command(
        name="member",
        aliases=["m", "user", "u"],
        usage="info member [member]",
    )
    async def member(self, ctx: commands.Context[commands.Bot], member: discord.Member) -> None:
        """
        Show information about a member.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        member : discord.Member
            The member to get information about.
        """

        bot_status = "✅" if member.bot else "❌"
        joined = discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Unknown"
        created = discord.utils.format_dt(member.created_at, "R") if member.created_at else "Unknown"
        roles = ", ".join(role.mention for role in member.roles[1:]) if member.roles[1:] else "No roles"
        fetched_member = await self.bot.fetch_user(member.id)

        embed = discord.Embed(
            title=member.display_name,
            description="Here is some information about the member.",
            color=discord.Color.blurple(),
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=fetched_member.banner)
        embed.add_field(name="Bot?", value=bot_status, inline=False)
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="ID", value=str(member.id), inline=False)
        embed.add_field(name="Joined", value=joined, inline=False)
        embed.add_field(name="Registered", value=created, inline=False)
        embed.add_field(name="Roles", value=roles, inline=False)

        await ctx.send(embed=embed)

    @info.command(
        name="roles",
        aliases=["r"],
        usage="info roles",
    )
    async def roles(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        List all roles in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        """
        if not ctx.guild:
            return

        guild = ctx.guild
        roles = [role.mention for role in guild.roles]

        embed = discord.Embed(
            title="Server Roles",
            color=discord.Color.blurple(),
        )

        chunk_size = 32
        if not len(roles) > chunk_size:
            embed.description = self._create_embed_desc("roles", guild.name, roles)
            await ctx.send(embed=embed)
            return

        chunks = self._chunks(iter(roles), chunk_size)
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        for chunk in chunks:
            embed = embed.copy()

            embed.description = self._create_embed_desc("roles", guild.name, chunk)
            menu.add_page(embed)

        menu = self._add_buttons_to_menu(menu)
        await menu.start()

    @info.command(
        name="emotes",
        aliases=["e"],
        usage="info emotes",
    )
    async def emotes(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        List all emotes in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        """
        if not ctx.guild:
            return

        guild = ctx.guild
        emotes: list[str] = [str(emote) for emote in guild.emojis]

        embed = discord.Embed(
            title="Server Emotes",
            color=discord.Color.blurple(),
        )

        chunk_size = 128
        if not len(emotes) > chunk_size:
            embed.description = self._create_embed_desc("emotes", guild.name, emotes)
            await ctx.send(embed=embed)
            return

        chunks = self._chunks(iter(emotes), chunk_size)
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        for chunk in chunks:
            embed = embed.copy()

            embed.description = self._create_embed_desc("emotes", guild.name, chunk)
            menu.add_page(embed)

        menu = self._add_buttons_to_menu(menu)
        await menu.start()

    def _chunks[T](self, it: Iterator[T], size: int) -> Generator[list[T], None, None]:
        """
        Split an iterator into chunks of a specified size.

        This function takes an iterator and divides it into chunks of a given size.
        Any remaining elements that do not fill a complete chunk are included in the
        final chunk, which may be smaller than the specified size.

        Parameters
        ----------
        it : Iterator[T]
            The input iterator to be split into chunks.
        size : int
            The size of each chunk.

        Yields
        -------
        list[T]
            A list containing a chunk of elements from the input iterator. The last
            list may contain fewer elements if there are not enough remaining to fill
            a complete chunk.
        """
        chunk: list[T] = []
        for item in it:
            chunk.append(item)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:  # if last chunk has any items
            yield chunk

    def _create_embed_desc(self, list_type: str, guild_name: str, items: Iterable[str]) -> str:
        return (
            f"{list_type.capitalize()} list for {guild_name}:\n {" ".join(items) if items else "No items available."}"
        )

    def _add_buttons_to_menu[T: ViewMenu](self, menu: T) -> T:
        menu.add_button(ViewButton.go_to_first_page())
        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        menu.add_button(ViewButton.go_to_last_page())
        menu.add_button(ViewButton.end_session())
        return menu


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))
