from collections.abc import Generator, Iterable, Iterator

import discord
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu

from tux.bot import Tux


class Info(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @commands.hybrid_group(name="info", aliases=["i"], usage="info <subcommand>")
    async def info(self, ctx: commands.Context[Tux]) -> None:
        """
        Information commands.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help("info")

    @info.command(name="server", aliases=["s"], usage="info server")
    async def server(self, ctx: commands.Context[Tux]) -> None:
        """
        Show information about the server.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """
        guild = ctx.guild
        if not guild:
            return

        embed: discord.Embed = (
            discord.Embed(
                title=guild.name,
                description=guild.description or "No description available.",
                color=discord.Color.blurple(),
            )
            .set_author(name="Server Information", icon_url=guild.icon)
            .add_field(name="Owner", value=str(guild.owner.mention) if guild.owner else "Unknown")
            .add_field(name="Vanity URL", value=guild.vanity_url_code or "None")
            .add_field(name="Boosts", value=guild.premium_subscription_count)
            .add_field(name="Text Channels", value=len(guild.text_channels))
            .add_field(name="Voice Channels", value=len(guild.voice_channels))
            .add_field(name="Forum Channels", value=len(guild.forums))
            .add_field(name="Emojis", value=f"{len(guild.emojis)}/{2*guild.emoji_limit}")
            .add_field(name="Stickers", value=f"{len(guild.stickers)}/{guild.sticker_limit}")
            .add_field(name="Roles", value=len(guild.roles))
            .add_field(name="Humans", value=sum(not member.bot for member in guild.members))
            .add_field(name="Bots", value=sum(member.bot for member in guild.members))
            .add_field(name="Bans", value=len([entry async for entry in guild.bans(limit=2000)]))
            .set_footer(text=f"ID: {guild.id} | Created: {guild.created_at.strftime('%B %d, %Y')}")
        )

        await ctx.send(embed=embed)

    @info.command(name="member", aliases=["m", "user", "u"], usage="info member [member]")
    async def member(self, ctx: commands.Context[Tux], member: discord.Member) -> None:
        """
        Show information about a member.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        member : discord.Member
            The member to get information about.
        """
        embed: discord.Embed = (
            discord.Embed(
                title=member.display_name,
                description="Here is some information about the member.",
                color=discord.Color.blurple(),
            )
            .set_thumbnail(url=member.display_avatar.url)
            .set_image(
                url=(await self.bot.fetch_user(member.id)).banner,  # Fetched member's banner
            )
            .add_field(name="Bot?", value="✅" if member.bot else "❌", inline=False)
            .add_field(name="Username", value=member.name, inline=False)
            .add_field(name="ID", value=str(member.id), inline=False)
            .add_field(
                name="Joined",
                value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Unknown",
                inline=False,
            )
            .add_field(
                name="Registered",
                value=discord.utils.format_dt(member.created_at, "R") if member.created_at else "Unknown",
                inline=False,
            )
            .add_field(
                name="Roles",
                value=", ".join(role.mention for role in member.roles[1:]) if member.roles[1:] else "No roles",
                inline=False,
            )
        )

        await ctx.send(embed=embed)

    @info.command(name="roles", aliases=["r"], usage="info roles")
    async def roles(self, ctx: commands.Context[Tux]) -> None:
        """
        List all roles in the server.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """
        guild = ctx.guild
        if not guild:
            return

        roles: list[str] = [role.mention for role in guild.roles]

        await self.paginated_embed(ctx, "Server Roles", "roles", guild.name, roles, 32)

    @info.command(name="emotes", aliases=["e"], usage="info emotes")
    async def emotes(self, ctx: commands.Context[Tux]) -> None:
        """
        List all emotes in the server.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """
        guild = ctx.guild
        if not guild:
            return

        emotes: list[str] = [str(emote) for emote in guild.emojis]
        await self.paginated_embed(ctx, "Server Emotes", "emotes", guild.name, emotes, 128)

    async def paginated_embed(
        self,
        ctx: commands.Context[Tux],
        title: str,
        list_type: str,
        guild_name: str,
        items: Iterable[str],
        chunk_size: int,
    ) -> None:
        """
        Send a paginated embed.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        title : str
            The title of the embed.
        list_type : str
            The type of list (e.g., roles, emotes).
        guild_name : str
            The name of the guild.
        items : Iterable[str]
            The items to display in the embed.
        chunk_size : int
            The size of each chunk for pagination.
        """
        embed: discord.Embed = discord.Embed(title=title, color=discord.Color.blurple())
        chunks: list[list[str]] = list(self._chunks(iter(items), chunk_size))

        if not chunks:
            embed.description = "No items available."
            await ctx.send(embed=embed)
            return

        menu: ViewMenu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
        for chunk in chunks:
            page_embed: discord.Embed = embed.copy()
            page_embed.description = f"{list_type.capitalize()} list for {guild_name}:\n{' '.join(chunk)}"
            menu.add_page(page_embed)

        self._add_buttons_to_menu(menu)
        await menu.start()

    def _chunks(self, it: Iterator[str], size: int) -> Generator[list[str], None, None]:
        """
        Split an iterator into chunks of a specified size.

        Parameters
        ----------
        it : Iterator[str]
            The input iterator to be split into chunks.
        size : int
            The size of each chunk.

        Yields
        ------
        List[str]
            A list containing a chunk of elements from the input iterator. The last
            list may contain fewer elements if there are not enough remaining to fill
            a complete chunk.
        """
        chunk: list[str] = []
        for item in it:
            chunk.append(item)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    def _add_buttons_to_menu(self, menu: ViewMenu) -> ViewMenu:
        """
        Add buttons to the menu.

        Parameters
        ----------
        menu : ViewMenu
            The menu to add buttons to.

        Returns
        -------
        ViewMenu
            The menu with buttons added.
        """
        buttons = [
            ViewButton.go_to_first_page(),
            ViewButton.back(),
            ViewButton.next(),
            ViewButton.go_to_last_page(),
            ViewButton.end_session(),
        ]

        for button in buttons:
            menu.add_button(button)
        return menu


async def setup(bot: Tux) -> None:
    await bot.add_cog(Info(bot))
