from collections.abc import Generator, Iterable, Iterator

import discord
from bot import Tux
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from ui.embeds import EmbedCreator, EmbedType
from utils.functions import generate_usage


class Info(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.info.usage = generate_usage(self.info)
        self.server.usage = generate_usage(self.server)
        self.member.usage = generate_usage(self.member)
        self.roles.usage = generate_usage(self.roles)
        self.emotes.usage = generate_usage(self.emotes)

    @commands.hybrid_group(
        name="info",
        aliases=["i"],
    )
    @commands.guild_only()
    async def info(
        self,
        ctx: commands.Context[Tux],
    ) -> None:
        """
        Information commands.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help("info")

    @info.command(
        name="server",
        aliases=["s"],
    )
    @commands.guild_only()
    async def server(self, ctx: commands.Context[Tux]) -> None:
        """
        Show information about the server.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """
        guild = ctx.guild
        assert guild
        assert guild.icon

        embed: discord.Embed = (
            EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title=guild.name,
                description=guild.description or "No description available.",
                custom_color=discord.Color.blurple(),
                custom_author_text="Server Information",
                custom_author_icon_url=guild.icon.url,
                custom_footer_text=f"ID: {guild.id} | Created: {guild.created_at.strftime('%B %d, %Y')}",
            )
            .add_field(name="Owner", value=str(guild.owner.mention) if guild.owner else "Unknown")
            .add_field(name="Vanity URL", value=guild.vanity_url_code or "None")
            .add_field(name="Boosts", value=guild.premium_subscription_count)
            .add_field(name="Text Channels", value=len(guild.text_channels))
            .add_field(name="Voice Channels", value=len(guild.voice_channels))
            .add_field(name="Forum Channels", value=len(guild.forums))
            .add_field(name="Emojis", value=f"{len(guild.emojis)}/{2 * guild.emoji_limit}")
            .add_field(name="Stickers", value=f"{len(guild.stickers)}/{guild.sticker_limit}")
            .add_field(name="Roles", value=len(guild.roles))
            .add_field(name="Humans", value=sum(not member.bot for member in guild.members))
            .add_field(name="Bots", value=sum(member.bot for member in guild.members))
            .add_field(name="Bans", value=len([entry async for entry in guild.bans(limit=2000)]))
        )

        await ctx.send(embed=embed)

    @info.command(
        name="member",
        aliases=["m", "user", "u"],
    )
    @commands.guild_only()
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
        user = await self.bot.fetch_user(member.id)
        embed: discord.Embed = (
            EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title=member.display_name,
                custom_color=discord.Color.blurple(),
                description="Here is some information about the member.",
                thumbnail_url=member.display_avatar.url,
                image_url=user.banner.url if user.banner else None,
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

    @info.command(
        name="roles",
        aliases=["r"],
    )
    @commands.guild_only()
    async def roles(self, ctx: commands.Context[Tux]) -> None:
        """
        List all roles in the server.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """
        guild = ctx.guild
        assert guild

        roles: list[str] = [role.mention for role in guild.roles]

        await self.paginated_embed(ctx, "Server Roles", "roles", guild.name, roles, 32)

    @info.command(
        name="emotes",
        aliases=["e"],
    )
    async def emotes(self, ctx: commands.Context[Tux]) -> None:
        """
        List all emotes in the server.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        """
        guild = ctx.guild
        assert guild

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
        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=title,
            custom_color=discord.Color.blurple(),
        )
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

        buttons = [
            ViewButton.go_to_first_page(),
            ViewButton.back(),
            ViewButton.next(),
            ViewButton.go_to_last_page(),
            ViewButton.end_session(),
        ]

        for button in buttons:
            menu.add_button(button)

        await menu.start()

    @staticmethod
    def _chunks(it: Iterator[str], size: int) -> Generator[list[str]]:
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


async def setup(bot: Tux) -> None:
    await bot.add_cog(Info(bot))
